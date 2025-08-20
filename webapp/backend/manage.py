import random
from datetime import datetime, timedelta
from app import app, db, Location, Device, SensorReading
import math
from sqlalchemy import text

def generate_realistic_data(start_time, end_time, interval_minutes=60):
    """Generates a list of realistic sensor readings."""
    readings = []
    current_time = start_time
    wind_directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']

    while current_time <= end_time:
        hour_of_day = current_time.hour + current_time.minute / 60
        temp_variation = math.sin((hour_of_day - 9) * (math.pi / 12))
        base_temp = 15
        temperature = round(base_temp + temp_variation * 8 + random.uniform(-1, 1), 2)

        humidity = round(max(0, min(100, 70 - temp_variation * 20 + random.uniform(-5, 5))), 2)

        pressure = round(1013 + random.uniform(-5, 5), 2)

        wind_speed = round(random.uniform(0, 25), 2)
        
        wind_direction = random.choice(wind_directions)

        readings.append({
            "timestamp": current_time,
            "temperature": temperature,
            "humidity": humidity,
            "pressure": pressure,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
        })
        current_time += timedelta(minutes=interval_minutes)
    return readings

def clear_data():
    """Clears all data from the database and resets primary key sequences."""
    with app.app_context():
        print("Clearing all data and resetting sequences...")
        db.session.execute(text('TRUNCATE TABLE sensor_reading, device, location RESTART IDENTITY CASCADE;'))
        db.session.commit()
        print("Data cleared.")

def seed_data():
    """Seeds the database with sample data."""
    with app.app_context():
        print("Seeding database...")
        
        location = Location(location_name='My Garden')
        db.session.add(location)
        db.session.commit()

        device = Device(device_id=1, device_name='Weather Station Pro', location_id=location.location_id)
        db.session.add(device)
        db.session.commit()
        
        now = datetime.utcnow()
        start_date = now - timedelta(days=7)
        
        data_points = generate_realistic_data(start_date, now, interval_minutes=15)
        
        for data in data_points:
            reading = SensorReading(
                device_id=device.device_id,
                timestamp=data['timestamp'],
                temperature=data['temperature'],
                humidity=data['humidity'],
                pressure=data['pressure'],
                wind_speed=data['wind_speed'],
                wind_direction=data['wind_direction']
            )
            db.session.add(reading)
            
        db.session.commit()
        print(f"Seeded {len(data_points)} sensor readings for device {device.device_id}.")
        print("Database seeded.")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'clear':
            clear_data()
        elif sys.argv[1] == 'seed':
            clear_data()
            seed_data()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Available commands: clear, seed")
    else:
        print("Please provide a command.")
        print("Available commands: clear, seed")