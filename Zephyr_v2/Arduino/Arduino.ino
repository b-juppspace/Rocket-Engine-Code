#include <PID_v1.h>

// Pressure Transducer Inputs
const int pressurePins[6] = {A0, A1, A2, A3, A4, A5};
double pressures[6];

// PWM Proportional Valve Outputs
const int valvePins[2] = {9, 6};
double setpoints[2] = {0, 0};  // Updated by GUI
double outputs[2] = {0, 0};

// PID Setup (Kp, Ki, Kd to be tuned)
double Kp = 2.0, Ki = 5.0, Kd = 1.0;
PID pid1(&pressures[0], &outputs[0], &setpoints[0], Kp, Ki, Kd, DIRECT);
PID pid2(&pressures[1], &outputs[1], &setpoints[1], Kp, Ki, Kd, DIRECT);

// State Machine
enum SystemState { IDLE, TESTING, IGNITION, PID_CONTROL, SHUTDOWN };
SystemState currentState = IDLE;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);  
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "INIT_SERIAL") {
      Serial.begin(9600);
      digitalWrite(LED_BUILTIN, HIGH);
      delay(500);
      digitalWrite(LED_BUILTIN, LOW);
      Serial.println("Serial Initialized");
    } else if (command.startsWith("SETPOINTS,")) {
      updateSetpoints(command);
    } else {
      handleSerialCommands(command);
    }
  }

  readPressures();
  executeStateLogic();
  sendData();
}

void readPressures() {
  for (int i = 0; i < 6; i++) {
    pressures[i] = analogRead(pressurePins[i]) * (5.0 / 1023.0);
  }
}

void handleSerialCommands(String command) {
  if (command == "BEGIN_TEST") currentState = TESTING;
  else if (command == "START_IGNITION") currentState = IGNITION;
  else if (command == "SHUTDOWN") currentState = SHUTDOWN;
}

void executeStateLogic() {
  switch (currentState) {
    case TESTING:
      break;
    case IGNITION:
      ignitionSequence();
      currentState = PID_CONTROL;
      break;
    case PID_CONTROL:
      pid1.Compute();
      pid2.Compute();
      analogWrite(valvePins[0], outputs[0]);
      analogWrite(valvePins[1], outputs[1]);
      break;
    case SHUTDOWN:
      analogWrite(valvePins[0], 0);
      analogWrite(valvePins[1], 0);
      currentState = IDLE;
      break;
    default:
      break;
  }
}

void ignitionSequence() {
  analogWrite(valvePins[0], 255);
  delay(2000);
  analogWrite(valvePins[0], 0);
}

void sendData() {
  Serial.print("Pressure Data:");
  for (int i = 0; i < 6; i++) {
    Serial.print(pressures[i]);
    Serial.print(",");
  }
  Serial.print("PWM Data:");
  Serial.print(outputs[0]);
  Serial.print(",");
  Serial.println(outputs[1]);
}

void updateSetpoints(String command) {
  int firstComma = command.indexOf(',');
  int secondComma = command.indexOf(',', firstComma + 1);
  
  if (firstComma > 0 && secondComma > firstComma) {
    setpoints[0] = command.substring(firstComma + 1, secondComma).toFloat();
    setpoints[1] = command.substring(secondComma + 1).toFloat();
  }
}
