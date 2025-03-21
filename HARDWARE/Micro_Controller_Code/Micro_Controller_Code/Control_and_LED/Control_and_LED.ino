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
#define DELAY_INTERVAL 500
Adafruit_NeoPixel WS2812B(NUM_PIXELS, PIN_WS2812B, NEO_GRB + NEO_KHZ800);
JsonDocument doc;

const int dirVert = 7; //z
const int dirHoriz = 5; //x
const int stepVert = 4; //z
const int stepHoriz = 2; //x
const int enVert = 8;
const int enHoriz = 8;

int final_position;
int initial_position;
int current_position=0;
int32_t horizLim = 9000;

int iloc;
int eloc;
bool collect_from_shelf;

void setup() {
  // Initialize serial port
  Serial.begin(115200);
  WS2812B.begin();
  myservo.attach(13);
  pinMode(dirVert, OUTPUT);
  pinMode(dirHoriz, OUTPUT);
  pinMode(stepVert, OUTPUT);
  pinMode(stepHoriz, OUTPUT);
  pinMode(enVert, OUTPUT);
  pinMode(enHoriz, OUTPUT);
  int current_position = 0;
  digitalWrite(enVert, HIGH);
  // digitalWrite(enHoriz, HIGH);
  while (!Serial)
    continue;

  // Allocate the JSON document

  // Deserialize the JSON document
  
}
void moveVertical(int32_t current_pos, int32_t external_pos){
  int32_t movement = external_pos - current_pos;
  bool dir = (movement>0) ? HIGH : LOW;
  Serial.println("Gant go uppy downy");
  digitalWrite(enVert, LOW);
  digitalWrite(dirVert, dir);
  for (uint32_t i =0; i<abs(movement); i++){
    digitalWrite(stepVert, LOW);
    delayMicroseconds(70);
    digitalWrite(stepVert, HIGH);
    delayMicroseconds(70);
  }
  digitalWrite(stepVert, LOW);
  digitalWrite(enVert, HIGH);
}

void goOut() {
  Serial.println("Gant go outy outy");
  digitalWrite(enHoriz, LOW);
  digitalWrite(dirHoriz, LOW);
  for (uint32_t i =0; i<horizLim; i++){
    digitalWrite(stepHoriz, LOW);
    delayMicroseconds(100);
    digitalWrite(stepHoriz, HIGH);
    delayMicroseconds(100);
  }
  digitalWrite(stepHoriz, LOW);
  digitalWrite(enHoriz, HIGH);
}

void goIn() {
  Serial.println("Gant go inny inny");
  digitalWrite(enHoriz, LOW);
  digitalWrite(dirHoriz, HIGH);
  for (int i =0; i<horizLim; i++){
    digitalWrite(stepHoriz, LOW);
    delayMicroseconds(100);
    digitalWrite(stepHoriz, HIGH);
    delayMicroseconds(100);
  }
  digitalWrite(stepHoriz, LOW);
  digitalWrite(enHoriz, HIGH);
}

void gantry(int32_t iloc, int32_t eloc, bool collect_from_shelf){
  int32_t position1 = 40000;
  int32_t position2 = 240000;
  int32_t position3 = 375000;
  switch (iloc) {
  case 1:
    iloc = position1;
    break;
  case 2:
    iloc = position2;
    break;
  case 3:
    iloc = position3;
    break;
  default:
    iloc = position3;
    break;
  }
  switch (eloc) {
  case 1:
    eloc = 80000;
    break;
  case 2:
    eloc = 280000;
    break;
  case 3:
    eloc = position3;
    break;
  default:
    eloc = 0;
    break;
  }
  int32_t adjustment = 15000;
  // 

  initial_position = current_position;
  // use values to move
  if (collect_from_shelf){
    // moveVertical(0, eloc);
    // delay(5000);
    // moveVertical(position1, 0);

    moveVertical(initial_position, eloc-adjustment);
    delay(1000);
    goOut();
    delay(1000);
    moveVertical(eloc-adjustment, eloc+adjustment);
    delay(1000);
    moveVertical(eloc+adjustment, iloc);
    delay(1000);
    goIn();
    delay(1000);
    moveVertical(iloc,eloc-adjustment);
    moveVertical(eloc-adjustment,0);
    current_position = initial_position;
  }
  else{
    moveVertical(initial_position, iloc);
    delay(1000);
    // moveVertical(iloc, iloc+adjustment);
    // delay(1000);
    goOut();
    delay(1000);
    moveVertical(iloc, eloc-adjustment);
    // moveVertical(eloc+adjustment, eloc-adjustment);
    delay(1000);
    goIn();
    moveVertical(eloc-adjustment,0);
    current_position = eloc-adjustment;
  }
}

void FlashingLED(JsonArray numbers){
  myservo.write(30);
  for (int i =0; i<5; i++){
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

// break down the serialJSON and output a struct that contains all the possible variables along with a bool representing if it is a gant or not
void loop(){
  
  DeserializationError error = deserializeJson(doc, Serial);
  // Test if parsing succeeds
  
  if (error) {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.f_str());
    return;
  }
  myservo.write(30);
  String type = doc["Type"];
  if (type=="Gantry"){
    int eloc = doc["EBoxLocation"];
    int iloc = doc["IBoxLocation"];
    bool collect_from_shelf = doc["CollectBox"];
    gantry(iloc, eloc, collect_from_shelf);
  }
  else if (type=="Dispenser"){
    JsonArray numbers = doc["Locations"];
    FlashingLED(numbers);
  }
  else{
    Serial.println("Unknown command");
  }
  return;
}