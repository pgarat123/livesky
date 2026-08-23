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


class NotificationSubscriber(db.Model):
    __tablename__ = 'notification_subscriber'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    ntfy_topic = db.Column(db.String(120), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('device.device_id'), nullable=False)

    frost_enabled = db.Column(db.Boolean, nullable=False, default=True)
    heatwave_enabled = db.Column(db.Boolean, nullable=False, default=True)
    high_wind_enabled = db.Column(db.Boolean, nullable=False, default=True)
    offline_enabled = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class AlertState(db.Model):
    """Suit si une alerte est actuellement 'active' pour un appareil, afin de
    n'envoyer une notification qu'au déclenchement (et à la fin), pas à
    chaque lecture tant que la condition reste vraie."""
    __tablename__ = 'alert_state'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.device_id'), nullable=False)
    alert_type = db.Column(db.String(20), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=False)
    since = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('device_id', 'alert_type', name='uq_alert_state_device_type'),
    )
