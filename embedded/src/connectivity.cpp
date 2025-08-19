#include "connectivity.h"
#include <Arduino.h>

char server_ip[16] = "192.168.1.20"; //Default
char server_port[6] = "5001";
char device_id[4] = "1";

void connectivitySetup()
{
    WiFiManager wm;

    WiFiManagerParameter custom_server_ip("server_ip", "IP du serveur", server_ip, 16);
    WiFiManagerParameter custom_server_port("server_port", "Port du serveur", server_port, 6);
    WiFiManagerParameter custom_device_id("device_id", "ID de l'appareil", device_id, 4);

    wm.addParameter(&custom_server_ip);
    wm.addParameter(&custom_server_port);
    wm.addParameter(&custom_device_id);

    wm.setConfigPortalTimeout(180);

    bool res = wm.autoConnect("LarkWeatherStationAP");

    if(!res)
    {
        Serial.println("Echec de la connexion. Redemarrage...");
        ESP.restart();
    }
    else
    {
        Serial.println("Wi-Fi connecte !");

        strcpy(server_ip, custom_server_ip.getValue());
        strcpy(server_port, custom_server_port.getValue());
        strcpy(device_id, custom_device_id.getValue());

        Serial.println("Parametres configurés :");
        Serial.print("IP du Serveur: "); Serial.println(server_ip);
        Serial.print("Port du Serveur: "); Serial.println(server_port);
        Serial.print("ID de l'appareil: "); Serial.println(device_id);
    }
}