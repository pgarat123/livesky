"""Statistiques agrégées sur l'historique des relevés (records, climatologie).

Tout est calculé via des agrégats SQL (GROUP BY / MIN / MAX côté Postgres)
plutôt qu'en rapatriant les lignes en Python : ça reste rapide même avec
plusieurs années de données, sans dépendance supplémentaire (pandas, etc).
"""

from models import db, SensorReading
from sun import classify_exposure

RECORD_METRICS = {
    'temperature_max': (SensorReading.temperature, False),
    'temperature_min': (SensorReading.temperature, True),
    'humidity_max': (SensorReading.humidity, False),
    'humidity_min': (SensorReading.humidity, True),
    'pressure_max': (SensorReading.pressure, False),
    'pressure_min': (SensorReading.pressure, True),
    'wind_speed_max': (SensorReading.wind_speed, False),
}


def get_records(device_id=None):
    records = {}
    for key, (column, ascending) in RECORD_METRICS.items():
        query = SensorReading.query.filter(column.isnot(None))
        if device_id:
            query = query.filter(SensorReading.device_id == device_id)
        query = query.order_by(column.asc() if ascending else column.desc())
        reading = query.first()
        record = {
            "value": getattr(reading, column.key) if reading else None,
            "timestamp": (reading.timestamp.isoformat() + 'Z') if reading else None,
        }
        # Un record de température en plein soleil est probablement gonflé par le
        # biais radiatif du capteur (voir sun.py) : on le signale plutôt que de le
        # présenter comme une vraie température record.
        if key.startswith('temperature') and reading:
            risk, _ = classify_exposure(reading.timestamp)
            record["sun_exposure_risk"] = risk
        records[key] = record
    return records


def get_climatology(device_id=None):
    query = db.session.query(
        db.func.extract('month', SensorReading.timestamp).label('month'),
        db.func.avg(SensorReading.temperature).label('avg_temp'),
        db.func.min(SensorReading.temperature).label('min_temp'),
        db.func.max(SensorReading.temperature).label('max_temp'),
        db.func.avg(SensorReading.humidity).label('avg_humidity'),
        db.func.avg(SensorReading.pressure).label('avg_pressure'),
        db.func.count(SensorReading.id).label('sample_count'),
    )
    if device_id:
        query = query.filter(SensorReading.device_id == device_id)
    query = query.group_by('month').order_by('month')

    def r(value):
        return round(value, 1) if value is not None else None

    return [
        {
            "month": int(row.month),
            "avg_temp": r(row.avg_temp),
            "min_temp": r(row.min_temp),
            "max_temp": r(row.max_temp),
            "avg_humidity": r(row.avg_humidity),
            "avg_pressure": r(row.avg_pressure),
            "sample_count": row.sample_count,
        }
        for row in query.all()
    ]


def get_yearly_daily_averages(device_id=None):
    """Moyenne de température par jour-de-l'année et par année.

    Sert à superposer les courbes de plusieurs années sur le frontend pour
    une comparaison "cette année vs l'année dernière" — celle-ci ne sera
    pertinente qu'une fois plusieurs années de recul accumulées.
    """
    query = db.session.query(
        db.func.extract('year', SensorReading.timestamp).label('year'),
        db.func.extract('doy', SensorReading.timestamp).label('doy'),
        db.func.avg(SensorReading.temperature).label('avg_temp'),
    )
    if device_id:
        query = query.filter(SensorReading.device_id == device_id)
    query = query.group_by('year', 'doy').order_by('year', 'doy')

    return [
        {
            "year": int(row.year),
            "day_of_year": int(row.doy),
            "avg_temp": round(row.avg_temp, 1) if row.avg_temp is not None else None,
        }
        for row in query.all()
    ]
