#include "connectivity.h"
#include <Arduino.h>

// Define these as extern in main.cpp
char server_ip[16] = "192.168.1.20";
char server_port[6] = "5001";
char device_id[4] = "1";

void connectivitySetup()
{
    WiFiManager wm;

    // Set a shorter timeout for the portal to avoid long waits on failure
    wm.setConfigPortalTimeout(120); 

    WiFiManagerParameter custom_server_ip("server_ip", "IP du serveur", server_ip, 16);
    WiFiManagerParameter custom_server_port("server_port", "Port du serveur", server_port, 6);
    WiFiManagerParameter custom_device_id("device_id", "ID de l'appareil", device_id, 4);

    wm.addParameter(&custom_server_ip);
    wm.addParameter(&custom_server_port);
    wm.addParameter(&custom_device_id);

    // autoConnect is blocking, but with the timeout, it will eventually give up.
    // If it fails, it returns false, and the logic in main.cpp will handle it.
    if (!wm.autoConnect("LarkWeatherStationAP")) {
        Serial.println("Failed to connect and hit timeout");
        // We don't restart here anymore. main.cpp will put the device to sleep.
    } else {
        Serial.println("WiFi connected!");

        // Save the custom parameters
        strcpy(server_ip, custom_server_ip.getValue());
        strcpy(server_port, custom_server_port.getValue());
        strcpy(device_id, custom_device_id.getValue());

        Serial.println("Parametres configures :");
        Serial.print("IP du Serveur: "); Serial.println(server_ip);
        Serial.print("Port du Serveur: "); Serial.println(server_port);
        Serial.print("ID de l'appareil: "); Serial.println(device_id);
    }
}
