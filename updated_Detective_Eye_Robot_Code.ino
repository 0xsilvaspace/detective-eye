#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();



const int TOP_LEFT_PIN  = 12;
const int TOP_RIGHT_PIN = 15;
const int BOT_LEFT_PIN  = 2;
const int BOT_RIGHT_PIN = 1;
const int PAN_PIN       = 8;
const int TILT_PIN      = 9;


const bool INV_TOP_L = false; 
const bool INV_TOP_R = true;  
const bool INV_BOT_L = true;  
const bool INV_BOT_R = false; 
const bool INV_PAN   = false;
const bool INV_TILT  = false;  

const int PAN_TRIM   = 25;    
const int PAN_MIN    = 20;   
const int PAN_MAX    = 160;  

const int TILT_MIN   = 10;    
const int TILT_MAX   = 40; 
const int LID_CLOSED = 0;   
const int LID_OPEN   = 90;  

const int SERVOMIN = 150; 
const int SERVOMAX = 600; 
const int BLINK_SPEED = 3;   

unsigned long lastBlinkTime = 0;
long blinkInterval = 4000;   

String inputString = ""; 
bool stringComplete = false;

void setup() {
  Serial.begin(115200);
  pwm.begin();
  pwm.setPWMFreq(60);

  
  moveServo(PAN_PIN, 90, INV_PAN);
  moveServo(TILT_PIN, 25, INV_TILT); 
  setEyelids(LID_OPEN); 
}

void loop() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') stringComplete = true;
    else inputString += inChar;
  }

  if (stringComplete) {
    parseAndMove(inputString);
    inputString = "";
    stringComplete = false;
  }

  unsigned long currentMillis = millis();
  if (currentMillis - lastBlinkTime >= blinkInterval) {
    if (random(0, 100) > 70) performDoubleBlink();
    else performSingleBlink();
    lastBlinkTime = currentMillis;
    blinkInterval = random(3000, 7000); 
  }
}

void parseAndMove(String data) {
  int xIndex = data.indexOf('X');
  int yIndex = data.indexOf('Y');
  
  if (xIndex != -1 && yIndex != -1) {
    String xVal = data.substring(xIndex + 1, yIndex);
    String yVal = data.substring(yIndex + 1);
    
    int panAngle = xVal.toInt() + PAN_TRIM; 
    int inputTilt = yVal.toInt(); // This is what Python sends (10 to 40)

    int tiltAngle = map(inputTilt, TILT_MIN, TILT_MAX, TILT_MAX, TILT_MIN);

    panAngle = constrain(panAngle, PAN_MIN, PAN_MAX);
    tiltAngle = constrain(tiltAngle, TILT_MIN, TILT_MAX);
    
    moveServo(PAN_PIN, panAngle, INV_PAN);
    moveServo(TILT_PIN, tiltAngle, INV_TILT);
  }
}

void performSingleBlink() { closeEyelids(); delay(50); openEyelids(); }
void performDoubleBlink() { closeEyelids(); delay(50); openEyelids(); delay(100); closeEyelids(); delay(50); openEyelids(); }
void closeEyelids() { for (int i = LID_OPEN; i >= LID_CLOSED; i -= 8) { setEyelids(i); delay(BLINK_SPEED); } setEyelids(LID_CLOSED); }
void openEyelids() { for (int i = LID_CLOSED; i <= LID_OPEN; i += 8) { setEyelids(i); delay(BLINK_SPEED); } setEyelids(LID_OPEN); }

void setEyelids(int angle) {
  moveServo(TOP_LEFT_PIN,  angle, INV_TOP_L);
  moveServo(TOP_RIGHT_PIN, angle, INV_TOP_R);
  moveServo(BOT_LEFT_PIN,  angle, INV_BOT_L);
  moveServo(BOT_RIGHT_PIN, angle, INV_BOT_R);
}

void moveServo(int channel, int angle, bool invert) {
  int target = angle;
  if (invert) target = 180 - angle;
  if (target < 0) target = 0;
  if (target > 180) target = 180;
  pwm.setPWM(channel, 0, map(target, 0, 180, SERVOMIN, SERVOMAX));
}