from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Location(db.Model):
    __tablename__ = 'location'
    location_id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(45), nullable=False, unique=True)
    devices = db.relationship('Device', backref='location', lazy=True)


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
