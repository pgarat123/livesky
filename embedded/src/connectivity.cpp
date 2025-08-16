//
// Created by Pierre Garat on 16/08/2025.
//
#include "connectivity.h"

void connectivitySetup()
{
    WiFiManager wm;
    bool res;
    res = wm.autoConnect("AutoConnectAP"); // password protected ap

    if(!res)
    {
        Serial.println("Failed to connect");
        ESP.restart();
    }
    else
    {
        Serial.println("Wi-Fi connected !");
    }
}