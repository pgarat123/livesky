import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

db_url = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Table `Location`
class Location(db.Model):
    __tablename__ = 'location'
    location_id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(45), nullable=False, unique=True)
    devices = db.relationship('Device', backref='location', lazy=True)

# Table `Device`
class Device(db.Model):
    __tablename__ = 'device'
    device_id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(45), nullable=False, unique=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.location_id'), nullable=False)
    readings = db.relationship('SensorReading', backref='device', lazy=True)

class SensorReading(db.Model):
    __tablename__ = 'sensor_reading'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    device_id = db.Column(db.Integer, db.ForeignKey('device.device_id'), nullable=False)

    temperature = db.Column(db.Float, nullable=True)
    humidity = db.Column(db.Float, nullable=True)
    pressure = db.Column(db.Float, nullable=True)
    wind_speed = db.Column(db.Float, nullable=True)
    wind_direction = db.Column(db.String(3), nullable=True)

with app.app_context():
    db.create_all()

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
    wind_speed_kmh = wind_speed_ms * 3.6 if wind_speed_ms is not None else None

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
            "wind_chill": wind_chill
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
    
    # Optionnel : Gérer le changement de lieu
    if 'location_name' in data:
        location = Location.query.filter_by(location_name=data['location_name']).first()
        if not location:
            # Créer le lieu s'il n'existe pas
            location = Location(location_name=data['location_name'])
            db.session.add(location)
        device.location = location

    db.session.commit()
    return jsonify({"message": f"Appareil '{device.device_name}' mis à jour."})

@app.route('/api/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    device = Device.query.get_or_404(device_id)
    
    # Supprimer d'abord toutes les lectures de capteurs associées
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
        "data": [getattr(reading, sensor_type) for reading in history]
    }

    return jsonify(response_data)


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
    app.run(host='0.0.0.0', port=5000, debug=True)
