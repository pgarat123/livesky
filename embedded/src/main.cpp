#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "DFRobot_LarkWeatherStation.h"
#include "connectivity.h"

#define DEVICE_ADDR 0x42
DFRobot_LarkWeatherStation_I2C lark(DEVICE_ADDR, &Wire);

// From connectivity.cpp
extern char server_ip[16];
extern char server_port[6];
extern char device_id[4];

const unsigned long POST_INTERVAL_MS = 300000; // 300,000 ms = 5 minutes
unsigned long lastPostTime = 0;

void sendData();

void setup(void) {
    Serial.begin(9600);
    delay(1000);

    connectivitySetup();

    while (lark.begin() != 0) {
        Serial.println("Erreur d'initialisation du capteur, nouvel essai dans 1s");
        delay(1000);
    }
    Serial.println("Capteur initialisé avec succès.");
}

void loop(void) {
    if (millis() - lastPostTime > POST_INTERVAL_MS) {
        lastPostTime = millis();
        sendData();
    }
}

void sendData() {
    Serial.println("----------------------------");
    Serial.println("Lecture des donnees du capteur...");

    // 1. Lecture de toutes les valeurs
    float temp = lark.getValue("Temp").toFloat();
    float humi = lark.getValue("Humi").toFloat();
    float pressure = lark.getValue("Pressure").toFloat();
    float speed = lark.getValue("Speed").toFloat();
    String dir = lark.getValue("Dir");

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
    Serial.println("JSON cree : " + jsonBuffer);

    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;

        String serverPath = "http://" + String(server_ip) + ":" + String(server_port) + "/api/data";
        Serial.println("Envoi des données vers : " + serverPath);

        http.begin(serverPath.c_str());
        http.addHeader("Content-Type", "application/json");

        int httpResponseCode = http.POST(jsonBuffer);

        if (httpResponseCode > 0) {
            Serial.print("Code de réponse HTTP : ");
            Serial.println(httpResponseCode);
            String payload = http.getString();
            Serial.print("Reponse du serveur : ");
            Serial.println(payload);
        } else {
            Serial.print("Erreur lors de l'envoi de la requête POST; code : ");
            Serial.println(httpResponseCode);
        }

        http.end();
    } else {
        Serial.println("WiFi non connecte. Impossible d'envoyer les données.");
    }
}