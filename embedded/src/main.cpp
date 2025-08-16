#include <Arduino.h>
#include "DFRobot_LarkWeatherStation.h"
#define DEVICE_ADDR                  0x42
DFRobot_LarkWeatherStation_I2C atm(DEVICE_ADDR,&Wire);

void setup(void){
    Serial.begin(9600);
    delay(1000);
    while(atm.begin()!= 0){
        Serial.println("init error");
        delay(1000);
    }
    Serial.println("init success");
    //atm.setTime(2023,3,1,17,20,0);
}

void loop(void){
    Serial.println(atm.getTimeStamp());
    Serial.print(atm.getValue("Speed").toFloat());
    Serial.println(atm.getUnit("Speed"));
    Serial.println(atm.getValue("Dir"));
    Serial.print(atm.getValue("Temp").toFloat());
    Serial.println(atm.getUnit("Temp"));
    Serial.print(atm.getValue("Humi").toFloat());
    Serial.println(atm.getUnit("Humi"));
    Serial.print(atm.getValue("Pressure").toFloat());
    Serial.println(atm.getUnit("Pressure"));
//    Serial.print(atm.getValue("Battery"));//Available when connected to a lithium battery
//    Serial.println(atm.getUnit("Battery")); //Available when connected to a lithium battery
//    Serial.print(atm.getValue("Lat"));//Available when connected to a GNSS module
//    Serial.print(atm.getValue("Lon"));//Available when connected to a GNSS module
    Serial.println("----------------------------");
//    Serial.println(atm.getInformation(true));
    delay(1000);
}
