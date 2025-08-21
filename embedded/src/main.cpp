#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "DFRobot_LarkWeatherStation.h"
#include "connectivity.h"

#define DEVICE_ADDR 0x42
#define uS_TO_S_FACTOR 1000000ULL  // Conversion factor for micro seconds to seconds
#define TIME_TO_SLEEP  300        // Time ESP32 will go to sleep (in seconds)

DFRobot_LarkWeatherStation_I2C lark(DEVICE_ADDR, &Wire);

// from connectivity.cpp
extern char server_ip[16];
extern char server_port[6];
extern char device_id[4];

void sendData();
bool ensureWiFiConnection();
void print_wakeup_reason();

void setup(void) {
    Serial.begin(9600);
    delay(1000); // Wait for serial to initialize

    Serial.println("\nBooting...");
    print_wakeup_reason();

    // Initialize sensor
    if (lark.begin() != 0) {
        Serial.println("Sensor initialization failed. Going to sleep.");
        esp_deep_sleep_start();
    }
    Serial.println("Sensor initialized successfully.");

    // Connect to WiFi
    if (ensureWiFiConnection()) {
        sendData();
    } else {
        Serial.println("Failed to connect to WiFi after several attempts.");
    }

    Serial.println("Going to sleep for " + String(TIME_TO_SLEEP) + " seconds");
    esp_sleep_enable_timer_wakeup(TIME_TO_SLEEP * uS_TO_S_FACTOR);
    
    Serial.flush(); // Ensure all serial messages are sent before sleeping
    esp_deep_sleep_start();
}

void loop(void) {
    // This will not be called, as the ESP32 will be in deep sleep.
}

void print_wakeup_reason(){
  esp_sleep_wakeup_cause_t wakeup_reason;
  wakeup_reason = esp_sleep_get_wakeup_cause();
  switch(wakeup_reason)
  {
    case ESP_SLEEP_WAKEUP_TIMER : Serial.println("Wakeup caused by timer"); break;
    default : Serial.printf("Wakeup was not caused by deep sleep (reason: %d)\n", wakeup_reason); break;
  }
}

bool ensureWiFiConnection() {
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("Already connected to WiFi.");
        return true;
    }

    Serial.println("Connecting to WiFi...");
    connectivitySetup(); // This will block until connected or timeout

    // Check status after attempting connection
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("WiFi connected.");
        return true;
    }

    Serial.println("WiFi connection failed.");
    return false;
}

void sendData() {
    Serial.println("----------------------------");
    Serial.println("Reading sensor data...");

    float temp = lark.getValue("Temp").toFloat();
    float humi = lark.getValue("Humi").toFloat();
    float pressure = lark.getValue("Pressure").toFloat();
    float speed = lark.getValue("Speed").toFloat();
    String dir = lark.getValue("Dir");

    // Basic check for invalid sensor readings
    if (temp == 0.0 && humi == 0.0 && pressure == 0.0) {
        Serial.println("Invalid sensor data. Skipping send.");
        return;
    }

    Serial.printf("Temp: %.2f, Hum: %.2f, Pres: %.2f, Wind Spd: %.2f, Wind Dir: %s\n",
                  temp, humi, pressure, speed, dir.c_str());

    StaticJsonDocument<256> doc;
    doc["device_id"] = atoi(device_id);
    doc["temperature"] = temp;
    doc["humidity"] = humi;
    doc["pressure"] = pressure;
    doc["wind_speed"] = speed;
    doc["wind_direction"] = dir;

    String jsonBuffer;
    serializeJson(doc, jsonBuffer);
    Serial.println("JSON created: " + jsonBuffer);

    HTTPClient http;
    String serverPath = "http://" + String(server_ip) + ":" + String(server_port) + "/api/data";
    Serial.println("Sending data to: " + serverPath);

    http.begin(serverPath.c_str());
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.POST(jsonBuffer);

    if (httpResponseCode > 0) {
        Serial.printf("HTTP Response code: %d\n", httpResponseCode);
        String payload = http.getString();
        Serial.println("Server response: " + payload);
    } else {
        Serial.printf("Error on sending POST: %d\n", httpResponseCode);
    }

    http.end();
}