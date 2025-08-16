#include <Arduino.h>
#include "DFRobot_LarkWeatherStation.h"
#include "connectivity.h"
#include "WiFiManager.h"
#define DEVICE_ADDR                  0x42
DFRobot_LarkWeatherStation_I2C lark(DEVICE_ADDR,&Wire);

void setup(void){
    Serial.begin(9600);
    delay(1000);
    while(lark.begin()!= 0){
        Serial.println("init error");
        delay(1000);
    }
    Serial.println("init success");
    lark.setTime(2023,3,1,17,20,0);
    connectivitySetup();

}

void loop(void){
    Serial.println(lark.getTimeStamp());
    Serial.print(lark.getValue("Speed").toFloat());
    Serial.println(lark.getUnit("Speed"));
    Serial.println(lark.getValue("Dir"));
    Serial.print(lark.getValue("Temp").toFloat());
    Serial.println(lark.getUnit("Temp"));
    Serial.print(lark.getValue("Humi").toFloat());
    Serial.println(lark.getUnit("Humi"));
    Serial.print(lark.getValue("Pressure").toFloat());
    Serial.println(lark.getUnit("Pressure"));
//    Serial.print(lark.getValue("Battery"));//Available when connected to a lithium battery
//    Serial.println(lark.getUnit("Battery")); //Available when connected to a lithium battery
//    Serial.print(lark.getValue("Lat"));//Available when connected to a GNSS module
//    Serial.print(lark.getValue("Lon"));//Available when connected to a GNSS module
    Serial.println("----------------------------");
//    Serial.println(lark.getInformation(true));
    delay(1000);
}
