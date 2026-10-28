/*
  Thesis-informed REFERENCE IMPLEMENTATION, not the original experimental firmware.
  Hardware bench validation NOT performed. Inspect wiring, power ratings, voltage
  dividers and servo range before connecting live equipment.

  Reference wiring (Arduino UNO):
  A0   - voltage divider sensor (scale = 5.0)
  A1   - ACS712 current sensor (calibration required)
  D9   - IRLZ44N Gate (220 ohm series gate resistor, 10k pulldown to GND)
  A4/5 - PCA9685 I2C SDA/SCL, servo on PCA9685 channel 15

  Serial commands:
  MODE,0 or MODE,1 or MODE,2   (Basic, Adaptive, ANN-P&O)
  STATIC_SWEEP                (20,30,40,50,60,70 degrees and PWM 0..255 step 15)
  DYNAMIC_START               (moving 20..70 degrees)
  ANN_PWM,<integer 0..255>    (ANN recommended PWM supplied by Pi)
  STOP                        (disable load PWM)

  Serial output, one CSV row per sample:
  time_ms,angle_deg,pwm,voltage_v,current_a,estimated_power_w,mode,sweep_id

  NOTE: Wire protocol and thresholds are design choices for this reference code,
        not verbatim parameters from the thesis.
*/
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <math.h>

Adafruit_PWMServoDriver servoDriver(0x40);
constexpr int PIN_LOAD_PWM = 9;
constexpr int PIN_VOLTAGE = A0;
constexpr int PIN_CURRENT = A1;
constexpr int SERVO_CHANNEL = 15;
constexpr int SERVO_MIN = 120;
constexpr int SERVO_MAX = 600;
constexpr float ADC_REFERENCE_V = 5.0f;
constexpr float VOLTAGE_SCALE = 5.0f;
constexpr float LOAD_RESISTOR_OHM = 40.0f;
// ACS712-5A often uses 0.185V/A; VERIFY exact sensor variant and calibrate.
constexpr float ACS_SENSITIVITY_V_PER_A = 0.185f;
constexpr float CURRENT_NOISE_FLOOR_A = 0.020f;

int algorithmMode = 0;  // 0 Basic, 1 Adaptive, 2 ANN-P&O
bool dynamicRunning = false;
bool staticRunning = false;
int angleDeg = 20;
int angleDirection = 1;
int loadPwm = 0;
int direction = 1;
int staticAngleIndex = 0;
int sweepId = 0;
const int STATIC_ANGLES[] = {20, 30, 40, 50, 60, 70};
float acsZeroVoltage = 2.5f;
float previousEstimatedPower = -1.0f;
unsigned long lastSample = 0;
unsigned long lastServoStep = 0;
const unsigned long SAMPLE_INTERVAL_MS = 220;
const unsigned long SERVO_INTERVAL_MS = 420;

int clampPwm(int value) { return constrain(value, 0, 255); }

void setLoad(int value) {
  loadPwm = clampPwm(value);
  analogWrite(PIN_LOAD_PWM, loadPwm);
}

void moveServo(int angle) {
  int bounded = constrain(angle, 20, 70);
  int pulse = map(bounded, 0, 180, SERVO_MIN, SERVO_MAX);
  servoDriver.setPWM(SERVO_CHANNEL, 0, pulse);
  angleDeg = bounded;
}

float adcMean(int pin, int repeats = 12) {
  float sum = 0.0f;
  for (int i = 0; i < repeats; i++) {
    sum += analogRead(pin);
    delay(2);
  }
  return sum / repeats;
}

float sensorVoltage(int pin) {
  return adcMean(pin) * ADC_REFERENCE_V / 1023.0f;
}

float panelVoltage() {
  return sensorVoltage(PIN_VOLTAGE) * VOLTAGE_SCALE;
}

float loadCurrent() {
  float current = fabs(sensorVoltage(PIN_CURRENT) - acsZeroVoltage) / ACS_SENSITIVITY_V_PER_A;
  return current < CURRENT_NOISE_FLOOR_A ? 0.0f : current;
}

float powerEstimate(float voltage, int pwm) {
  return (pwm / 255.0f) * voltage * voltage / LOAD_RESISTOR_OHM;
}

void outputSample(float voltage, float current, float estimatedPower, int modeTag) {
  Serial.print(millis()); Serial.print(',');
  Serial.print(angleDeg); Serial.print(',');
  Serial.print(loadPwm); Serial.print(',');
  Serial.print(voltage, 5); Serial.print(',');
  Serial.print(current, 5); Serial.print(',');
  Serial.print(estimatedPower, 6); Serial.print(',');
  Serial.print(modeTag); Serial.print(',');
  Serial.println(sweepId);
}

int stepFromDelta(float absDelta) {
  // Example thresholds; thesis lists step magnitudes 12,7,4,2 but not thresholds.
  if (absDelta > 0.080f) return 12;
  if (absDelta > 0.035f) return 7;
  if (absDelta > 0.010f) return 4;
  return 2;
}

void poUpdate(float estimatedPower) {
  if (previousEstimatedPower >= 0.0f) {
    float delta = estimatedPower - previousEstimatedPower;
    if (delta < 0.0f) direction = -direction;
    int step = algorithmMode == 1 ? stepFromDelta(fabs(delta)) :
               algorithmMode == 2 ? 2 : 4;
    setLoad(loadPwm + direction * step);
  }
  previousEstimatedPower = estimatedPower;
}

void stopAll() {
  dynamicRunning = false;
  staticRunning = false;
  previousEstimatedPower = -1.0f;
  setLoad(0);
}

void handleCommand(String cmd) {
  cmd.trim();
  if (cmd == "STOP") { stopAll(); return; }
  if (cmd.startsWith("MODE,")) {
    int choice = cmd.substring(5).toInt();
    if (choice >= 0 && choice <= 2) algorithmMode = choice;
    return;
  }
  if (cmd == "STATIC_SWEEP") {
    stopAll();
    staticRunning = true;
    staticAngleIndex = 0;
    sweepId = 0;
    moveServo(STATIC_ANGLES[0]);
    setLoad(0);
    lastSample = millis();
    return;
  }
  if (cmd == "DYNAMIC_START") {
    stopAll();
    dynamicRunning = true;
    angleDirection = 1;
    moveServo(20);
    direction = 1;
    setLoad(80);
    lastSample = millis();
    lastServoStep = millis();
    return;
  }
  if (cmd.startsWith("ANN_PWM,") && dynamicRunning && algorithmMode == 2) {
    int recommended = cmd.substring(8).toInt();
    // Example: jump to ANN-suggested operating region, then P&O refines.
    setLoad(recommended);
    previousEstimatedPower = -1.0f;
  }
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(25);
  pinMode(PIN_LOAD_PWM, OUTPUT);
  setLoad(0);
  Wire.begin();
  servoDriver.begin();
  servoDriver.setPWMFreq(50);
  delay(300);
  moveServo(20);
  delay(200);
  // ACS712 zero current calibration with MOSFET switched OFF.
  acsZeroVoltage = sensorVoltage(PIN_CURRENT);
  stopAll();
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    handleCommand(command);
  }
  unsigned long now = millis();
  if (dynamicRunning && now - lastServoStep >= SERVO_INTERVAL_MS) {
    lastServoStep = now;
    int nextAngle = angleDeg + angleDirection * 2;
    if (nextAngle >= 70) { nextAngle = 70; angleDirection = -1; }
    if (nextAngle <= 20) { nextAngle = 20; angleDirection = 1; }
    moveServo(nextAngle);
  }
  if (now - lastSample < SAMPLE_INTERVAL_MS) return;
  lastSample = now;

  // Measurement is taken at current PWM; only AFTER logging do we change PWM.
  float voltage = panelVoltage();
  float current = loadCurrent();
  float estimatedPower = powerEstimate(voltage, loadPwm);
  int modeTag = staticRunning ? 3 : dynamicRunning ? algorithmMode : 4;
  outputSample(voltage, current, estimatedPower, modeTag);

  if (staticRunning) {
    if (loadPwm < 255) {
      setLoad(min(255, loadPwm + 15));
    } else {
      sweepId++;
      staticAngleIndex = (staticAngleIndex + 1) % 6;
      moveServo(STATIC_ANGLES[staticAngleIndex]);
      setLoad(0);
      delay(150); // settle mechanically after angle change
    }
  } else if (dynamicRunning) {
    poUpdate(estimatedPower);
  }
}
