from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Artificak temp data
mock_sensor_data = [
    {"id": 1, "temperature": 23.5, "humidity": 45.2, "timestamp": "2025-08-16T16:10:00Z"},
    {"id": 2, "temperature": 23.7, "humidity": 45.8, "timestamp": "2025-08-16T16:11:00Z"},
    {"id": 3, "temperature": 23.6, "humidity": 46.1, "timestamp": "2025-08-16T16:12:00Z"}
]

@app.route('/')
def hello_world():
    return '<h1>Le backend fonctionne !</h1>'

@app.route('/api/data')
def get_data():
    return jsonify(mock_sensor_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
