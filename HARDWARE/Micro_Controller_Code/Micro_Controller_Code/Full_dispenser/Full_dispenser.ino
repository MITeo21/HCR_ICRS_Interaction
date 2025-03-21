#include <ArduinoJson.h>
// #include <ArduinoSTL.h>
#include "Arduino.h"
// #include <vector>
#include <Adafruit_NeoPixel.h>
#ifdef __AVR__
#include <avr/power.h> // Required for 16 MHz Adafruit Trinket
#endif

#include <Servo.h>
Servo myservo;

#include <string.h>
#define PIN_WS2812B 12  // Arduino pin that connects to WS2812B
#define NUM_PIXELS 60  // The number of LEDs (pixels) on WS2812B
#define DELAY_INTERVAL 1000
Adafruit_NeoPixel WS2812B(NUM_PIXELS, PIN_WS2812B, NEO_GRB + NEO_KHZ800);
JsonDocument doc;

void setup() {
  // Initialize serial port
  Serial.begin(115200);
  WS2812B.begin();
  myservo.attach(13);
  // pinMode(dirVert, OUTPUT);
  // pinMode(dirHoriz, OUTPUT);
  // pinMode(stepVert, OUTPUT);
  // pinMode(stepHoriz, OUTPUT);
  // pinMode(enVert, OUTPUT);
  // pinMode(enHoriz, OUTPUT);
  int current_position = 0;
  // digitalWrite(enVert, HIGH);
  // digitalWrite(enHoriz, HIGH);
  while (!Serial)
    continue;

  // Allocate the JSON document

  // Deserialize the JSON document
  
}

void loop(){
  DeserializationError error = deserializeJson(doc, Serial);
  // Test if parsing succeeds
  if (error) {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.f_str());
    return;
  }
  String type = doc["Type"];
  if (type=="Dispenser"){
    JsonArray numbers = doc["Locations"];
    FlashingLED(numbers);
  }
  else{
    Serial.println("Unknown command");
  }
  return;
}

void FlashingLED(JsonArray numbers){
  myservo.write(30);
  for (int i =0; i<10; i++){
    for (size_t i = 0; i < numbers.size(); i++) {
      WS2812B.setPixelColor(numbers[i], WS2812B.Color(255, 255, 255));
    }
      WS2812B.show();
      delay(DELAY_INTERVAL);
      WS2812B.clear();
      WS2812B.show();
      delay(DELAY_INTERVAL);
  }
  myservo.write(120); 
}