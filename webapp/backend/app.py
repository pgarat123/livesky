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

    new_reading = SensorReading(
        device_id=data['device_id'],
        temperature=data.get('temperature'),
        humidity=data.get('humidity'),
        pressure=data.get('pressure'),
        wind_speed=data.get('wind_speed'),
        wind_direction=data.get('wind_direction')
    )

    db.session.add(new_reading)
    db.session.commit()
    return jsonify({"message": "Donnee ajoutee"}), 201

@app.route('/api/data', methods=['GET'])
def get_data():
    readings = SensorReading.query.join(Device).order_by(SensorReading.timestamp.desc()).all()
    data_list = [
        {
            "id": reading.id,
            "device_id": reading.device.device_id,
            "timestamp": reading.timestamp.isoformat() + 'Z',
            "device_name": reading.device.device_name,
            "location_name": reading.device.location.location_name,

            "temperature": reading.temperature,
            "humidity": reading.humidity,
            "pressure": reading.pressure,
            "wind_speed": reading.wind_speed,
            "wind_direction": reading.wind_direction
        } for reading in readings
    ]
    return jsonify(data_list)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)