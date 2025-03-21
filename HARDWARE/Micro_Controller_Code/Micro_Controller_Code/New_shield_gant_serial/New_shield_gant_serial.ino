const int dirVert = 7; //z
const int dirHoriz = 5; //x
const int stepVert = 4; //z
const int stepHoriz = 2; //x
const int enVert = 8;
const int enHoriz = 8;

const uint32_t vertLim = 375000;
const uint32_t horizLim = 9000; //11500

void setup() {
  Serial.begin(115200);
  pinMode(dirVert, OUTPUT);
  pinMode(dirHoriz, OUTPUT);
  pinMode(stepVert, OUTPUT);
  pinMode(stepHoriz, OUTPUT);
  pinMode(enVert, OUTPUT);
  pinMode(enHoriz, OUTPUT);
  digitalWrite(enVert, HIGH);
}


void loop() {
    if (Serial.available()) {
        char command = Serial.read(); // Read a single command
        processCommand(command); // Pass command to handler function
    }
}

// Function to process commands
void processCommand(char cmd) {
    switch (cmd) {
        case 'u':
            goUp();
            break;
        case 'd':
            goDown();
            break;
        case 'i':
            goIn();
            break;
        case 'o':
            goOut();
            break;
        default:
            Serial.println("Unknown command");
    }
}

// Functions for LED control
void goUp() {
  // int vertLim = 100;
  Serial.println("Gant go uppy uppy");
  digitalWrite(enVert, LOW);
  digitalWrite(dirVert, HIGH);
  for (uint32_t i=0; i<vertLim; i++){
    digitalWrite(stepVert, LOW);
    delayMicroseconds(70);
    digitalWrite(stepVert, HIGH);
    delayMicroseconds(70);
  }
  digitalWrite(stepVert, LOW);
  digitalWrite(enVert, HIGH);
  delay(1000);
}

void goDown() {
  Serial.println("Gant go downy downy");
  digitalWrite(enVert, LOW);
  digitalWrite(dirVert, LOW);
  for (uint32_t i =0; i<vertLim; i++){
    digitalWrite(stepVert, LOW);
    delayMicroseconds(70);
    digitalWrite(stepVert, HIGH);
    delayMicroseconds(70);
  }
  digitalWrite(stepVert, LOW);
  digitalWrite(enVert, HIGH);
}

// Functions for Motor control
void goIn() {
  Serial.println("Gant go inny inny");
  digitalWrite(enHoriz, LOW);
  digitalWrite(dirHoriz, HIGH);
  for (uint32_t i =0; i<horizLim; i++){
    digitalWrite(stepHoriz, LOW);
    delayMicroseconds(70);
    digitalWrite(stepHoriz, HIGH);
    delayMicroseconds(70);
  }
  digitalWrite(stepHoriz, LOW);
  digitalWrite(enHoriz, HIGH);
}

void goOut() {
  Serial.println("Gant go outy outy");
  digitalWrite(enHoriz, LOW);
  digitalWrite(dirHoriz, LOW);
  for (uint32_t i =0; i<horizLim; i++){
    digitalWrite(stepHoriz, LOW);
    delayMicroseconds(70);
    digitalWrite(stepHoriz, HIGH);
    delayMicroseconds(70);
  }
  digitalWrite(stepHoriz, LOW);
  digitalWrite(enHoriz, HIGH);
}
