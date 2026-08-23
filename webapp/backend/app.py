import os
import threading
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta

import stats
import forecast
import notifications
from models import db, Location, Device, SensorReading, NotificationSubscriber
from sun import sun_bias_estimate, classify_exposure

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()


def _offline_check_loop():
    """Contrôle périodique, indépendant des requêtes HTTP : c'est l'ABSENCE de
    nouvelle mesure qu'on veut détecter, donc rien dans /api/data ne peut la
    déclencher. Tourne dans un thread daemon, pas de dépendance supplémentaire
    (pas de Celery/APScheduler pour un simple contrôle toutes les 10 min)."""
    while True:
        time.sleep(600)
        with app.app_context():
            try:
                notifications.check_offline_alerts()
            except Exception as e:
                print(f"Erreur lors de la vérification hors-ligne: {e}")


threading.Thread(target=_offline_check_loop, daemon=True).start()


@app.route('/')
def hello_world():
    return '<h1>Backend avec schéma de BDD avancé !</h1>'


@app.route('/api/devices', methods=['POST'])
def create_device():
    data = request.get_json()
    location = Location.query.filter_by(location_name=data['location_name']).first()
    if not location:
        location = Location(location_name=data['location_name'])
        db.session.add(location)
        db.session.commit()

    device = Device(device_name=data['device_name'], location_id=location.location_id)
    db.session.add(device)
    db.session.commit()
    return jsonify({"message": f"Appareil '{data['device_name']}' créé."}), 201


@app.route('/api/data', methods=['POST'])
def add_data():
    data = request.get_json()
    if not data or 'device_id' not in data:
        return jsonify({"error": "Données invalides, 'device_id' manquant"}), 400

    device = Device.query.get(data['device_id'])
    if not device:
        return jsonify({"error": "Appareil non trouvé"}), 404

    # Convert wind speed from m/s to km/h if present
    wind_speed_ms = data.get('wind_speed')
    wind_speed_kmh = round(wind_speed_ms * 3.6, 1) if wind_speed_ms is not None else None

    new_reading = SensorReading(
        device_id=data['device_id'],
        temperature=data.get('temperature'),
        humidity=data.get('humidity'),
        pressure=data.get('pressure'),
        wind_speed=wind_speed_kmh,
        wind_direction=data.get('wind_direction')
    )

    db.session.add(new_reading)
    db.session.commit()

    try:
        notifications.check_reading_alerts(new_reading)
    except Exception as e:
        # Une alerte ratée ne doit jamais faire échouer l'ingestion de la mesure.
        print(f"Erreur lors de la vérification des alertes: {e}")

    return jsonify({"message": "Donnee ajoutee"}), 201


def calculate_wind_chill(temperature, wind_speed):
    if temperature is None or wind_speed is None:
        return None
    # Wind chill formula is typically for temperatures <= 10°C and wind speed > 4.8 km/h
    # If wind speed is too low, wind chill is not significant or not applicable
    if temperature > 10 or wind_speed <= 4.8:
        return temperature # Return original temperature if wind chill not applicable

    # V in km/h
    wind_speed_kmh = wind_speed

    # Wind Chill Index formula (Environment Canada / NWS)
    wind_chill = 13.12 + (0.6215 * temperature) - (11.37 * (wind_speed_kmh**0.16)) + (0.3965 * temperature * (wind_speed_kmh**0.16))
    return round(wind_chill, 1)


def calculate_heat_index(temperature_celsius, humidity):
    if temperature_celsius is None or humidity is None:
        return None

    # Convert Celsius to Fahrenheit
    temperature_fahrenheit = (temperature_celsius * 9/5) + 32

    # Heat index formula is typically for temperatures >= 80°F (26.7°C) and humidity >= 40%
    if temperature_fahrenheit < 80 or humidity < 40:
        return temperature_celsius # Return original temperature if heat index not applicable

    T = temperature_fahrenheit
    RH = humidity

    # Steadman (1984) / NWS Heat Index formula
    heat_index_fahrenheit = -42.379 + 2.04901523*T + 10.14333127*RH - 0.22475541*T*RH - \
                            6.83783e-3*T**2 - 5.481717e-2*RH**2 + 1.22874e-3*T**2*RH + \
                            8.5282e-4*T*RH**2 - 1.99e-6*T**2*RH**2

    # Convert back to Celsius
    heat_index_celsius = (heat_index_fahrenheit - 32) * 5/9
    return round(heat_index_celsius, 1)


def calculate_trend(current_value, past_value):
    if current_value is None or past_value is None:
        return 'stable'
    # Using a small tolerance to avoid flagging minor fluctuations
    if current_value > past_value + 0.2:
        return 'rising'
    elif current_value < past_value - 0.2:
        return 'falling'
    else:
        return 'stable'


@app.route('/api/data', methods=['GET'])
def get_data():
    latest_readings_subquery = db.session.query(
        SensorReading.device_id,
        db.func.max(SensorReading.timestamp).label('max_timestamp')
    ).group_by(SensorReading.device_id).subquery()

    readings = db.session.query(SensorReading).join(
        latest_readings_subquery,
        db.and_(
            SensorReading.device_id == latest_readings_subquery.c.device_id,
            SensorReading.timestamp == latest_readings_subquery.c.max_timestamp
        )
    ).order_by(SensorReading.timestamp.desc()).all()

    data_list = []
    for reading in readings:
        past_time = reading.timestamp - timedelta(hours=1)
        past_reading = SensorReading.query.filter(
            SensorReading.device_id == reading.device_id,
            SensorReading.timestamp <= past_time
        ).order_by(SensorReading.timestamp.desc()).first()

        trends = {
            'temperature': calculate_trend(reading.temperature, past_reading.temperature if past_reading else None),
            'humidity': calculate_trend(reading.humidity, past_reading.humidity if past_reading else None),
            'pressure': calculate_trend(reading.pressure, past_reading.pressure if past_reading else None),
        }

        heat_index = calculate_heat_index(reading.temperature, reading.humidity)
        wind_chill = calculate_wind_chill(reading.temperature, reading.wind_speed)
        sun = sun_bias_estimate(reading.temperature, reading.timestamp)

        data_list.append({
            "id": reading.id,
            "device_id": reading.device.device_id,
            "temperature": reading.temperature,
            "humidity": reading.humidity,
            "pressure": reading.pressure,
            "wind_speed": reading.wind_speed,
            "wind_direction": reading.wind_direction,
            "timestamp": reading.timestamp.isoformat() + 'Z',
            "device_name": reading.device.device_name,
            "location_name": reading.device.location.location_name,
            "trends": trends,
            "heat_index": heat_index,
            "wind_chill": wind_chill,
            "sun": sun,
        })

    return jsonify(data_list)


@app.route('/api/devices', methods=['GET'])
def get_devices():
    devices = Device.query.order_by(Device.device_id).all()
    devices_list = [
        {
            "device_id": device.device_id,
            "device_name": device.device_name,
            "location_name": device.location.location_name
        } for device in devices
    ]
    return jsonify(devices_list)


@app.route('/api/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    device = Device.query.get_or_404(device_id)
    data = request.get_json()

    if 'device_name' in data:
        device.device_name = data['device_name']

    # Optional: Handle location change
    if 'location_name' in data:
        location = Location.query.filter_by(location_name=data['location_name']).first()
        if not location:
            # Create the location if it doesn't exist
            location = Location(location_name=data['location_name'])
            db.session.add(location)
        device.location = location

    db.session.commit()
    return jsonify({"message": f"Appareil '{device.device_name}' mis à jour."})


@app.route('/api/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    device = Device.query.get_or_404(device_id)

    # First, delete all associated sensor readings to maintain data integrity
    SensorReading.query.filter_by(device_id=device_id).delete()

    db.session.delete(device)
    db.session.commit()
    return jsonify({"message": f"Appareil ID {device_id} et ses données supprimés."})


@app.route('/api/devices/<int:device_id>/history', methods=['GET'])
def get_device_history(device_id):
    sensor_type = request.args.get('sensor', 'temperature', type=str)
    time_range_hours = request.args.get('range', 24, type=int)

    valid_sensors = ['temperature', 'humidity', 'pressure', 'wind_speed', 'wind_direction']
    if sensor_type not in valid_sensors:
        return jsonify({"error": "Type de capteur non valide"}), 400

    start_time = datetime.utcnow() - timedelta(hours=time_range_hours)

    history = SensorReading.query.filter(
        SensorReading.device_id == device_id,
        SensorReading.timestamp >= start_time,
        getattr(SensorReading, sensor_type).isnot(None)
    ).order_by(SensorReading.timestamp.asc()).all()

    response_data = {
        "labels": [reading.timestamp.isoformat() + 'Z' for reading in history],
        "data": [getattr(reading, sensor_type) for reading in history],
    }

    if sensor_type == 'temperature':
        response_data["sun_exposure"] = [classify_exposure(reading.timestamp)[0] for reading in history]

    return jsonify(response_data)


@app.route('/api/stats/records', methods=['GET'])
def get_records():
    device_id = request.args.get('device_id', type=int)
    return jsonify(stats.get_records(device_id))


@app.route('/api/stats/climatology', methods=['GET'])
def get_climatology():
    device_id = request.args.get('device_id', type=int)
    return jsonify(stats.get_climatology(device_id))


@app.route('/api/stats/yearly-comparison', methods=['GET'])
def get_yearly_comparison():
    device_id = request.args.get('device_id', type=int)
    return jsonify(stats.get_yearly_daily_averages(device_id))


@app.route('/api/forecast/<int:device_id>', methods=['GET'])
def get_forecast(device_id):
    Device.query.get_or_404(device_id)
    return jsonify(forecast.build_forecast(device_id, datetime.utcnow()))


def _subscriber_dict(sub):
    return {
        "id": sub.id,
        "name": sub.name,
        "ntfy_topic": sub.ntfy_topic,
        "device_id": sub.device_id,
        "frost_enabled": sub.frost_enabled,
        "heatwave_enabled": sub.heatwave_enabled,
        "high_wind_enabled": sub.high_wind_enabled,
        "offline_enabled": sub.offline_enabled,
    }


@app.route('/api/notifications/subscribers', methods=['GET'])
def get_subscribers():
    device_id = request.args.get('device_id', type=int)
    query = NotificationSubscriber.query
    if device_id:
        query = query.filter_by(device_id=device_id)
    subs = query.order_by(NotificationSubscriber.id).all()
    return jsonify([_subscriber_dict(s) for s in subs])


@app.route('/api/notifications/subscribers', methods=['POST'])
def create_subscriber():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('ntfy_topic') or not data.get('device_id'):
        return jsonify({"error": "Champs 'name', 'ntfy_topic' et 'device_id' requis"}), 400

    Device.query.get_or_404(data['device_id'])

    sub = NotificationSubscriber(
        name=data['name'],
        ntfy_topic=data['ntfy_topic'],
        device_id=data['device_id'],
        frost_enabled=data.get('frost_enabled', True),
        heatwave_enabled=data.get('heatwave_enabled', True),
        high_wind_enabled=data.get('high_wind_enabled', True),
        offline_enabled=data.get('offline_enabled', True),
    )
    db.session.add(sub)
    db.session.commit()
    return jsonify(_subscriber_dict(sub)), 201


@app.route('/api/notifications/subscribers/<int:sub_id>', methods=['PUT'])
def update_subscriber(sub_id):
    sub = NotificationSubscriber.query.get_or_404(sub_id)
    data = request.get_json() or {}
    for field in ['name', 'ntfy_topic', 'frost_enabled', 'heatwave_enabled', 'high_wind_enabled', 'offline_enabled']:
        if field in data:
            setattr(sub, field, data[field])
    db.session.commit()
    return jsonify(_subscriber_dict(sub))


@app.route('/api/notifications/subscribers/<int:sub_id>', methods=['DELETE'])
def delete_subscriber(sub_id):
    sub = NotificationSubscriber.query.get_or_404(sub_id)
    db.session.delete(sub)
    db.session.commit()
    return jsonify({"message": "Abonné supprimé."})


@app.route('/api/notifications/subscribers/<int:sub_id>/test', methods=['POST'])
def test_subscriber(sub_id):
    sub = NotificationSubscriber.query.get_or_404(sub_id)
    ok = notifications.send_ntfy(
        sub.ntfy_topic,
        "Test LiveSky",
        "Si tu reçois ce message, les notifications sont bien configurées !",
        tags=['white_check_mark'],
        priority=3,
    )
    if ok:
        return jsonify({"message": "Notification de test envoyée."})
    return jsonify({"error": "Échec de l'envoi. Vérifie le nom du topic ntfy."}), 502


@app.route('/api/admin/readings', methods=['GET'])
def get_all_readings():
    """
    Admin route to get all sensor readings from all devices.
    """
    limit = request.args.get('limit', 50, type=int)

    readings = SensorReading.query.order_by(SensorReading.timestamp.desc()).limit(limit).all()

    data_list = [
        {
            "id": reading.id,
            "device_id": reading.device.device_id,
            "device_name": reading.device.device_name,
            "temperature": reading.temperature,
            "humidity": reading.humidity,
            "pressure": reading.pressure,
            "wind_speed": reading.wind_speed,
            "wind_direction": reading.wind_direction,
            "timestamp": reading.timestamp.isoformat() + 'Z',
        } for reading in readings
    ]
    return jsonify(data_list)


@app.route('/api/admin/devices/<int:device_id>/readings', methods=['GET'])
def get_device_readings_for_admin(device_id):
    """
    Admin route to get all readings for a specific device.
    """
    limit = request.args.get('limit', 50, type=int)

    device = Device.query.get_or_404(device_id)
    readings = SensorReading.query.filter_by(device_id=device.device_id).order_by(SensorReading.timestamp.desc()).limit(limit).all()

    data_list = [
        {
            "id": reading.id,
            "timestamp": reading.timestamp.isoformat() + 'Z',
            "temperature": reading.temperature,
            "humidity": reading.humidity,
            "pressure": reading.pressure,
            "wind_speed": reading.wind_speed,
            "wind_direction": reading.wind_direction,
        } for reading in readings
    ]
    return jsonify(data_list)


@app.route('/api/admin/readings/<int:reading_id>', methods=['DELETE'])
def delete_reading(reading_id):
    """
    Admin route to delete a specific sensor reading.
    """
    reading = SensorReading.query.get_or_404(reading_id)
    db.session.delete(reading)
    db.session.commit()
    return jsonify({"message": f"Reading ID {reading_id} has been deleted."})


if __name__ == '__main__':
    # debug=False : le débogueur interactif de Werkzeug permet l'exécution de
    # code arbitraire depuis une page d'erreur, à éviter sur un site exposé
    # (duckdns/ngrok). Ça évite aussi que le reloader de debug=True ne
    # démarre le thread de fond ci-dessus deux fois (process parent + enfant).
    app.run(host='0.0.0.0', port=5000, debug=False)
