#include <PID_v1.h>

// Pressure Transducer Inputs
const int pressurePins[6] = {A0, A1, A2, A3, A4, A5};
double pressures[6];

// PWM Proportional Valve Outputs
const int valvePins[2] = {9, 6};
double setpoints[2] = {0, 0};
double outputs[2] = {0, 0};

// PID Setup (Kp, Ki, Kd to be tuned)
double Kp = 2.0, Ki = 5.0, Kd = 1.0;
PID pid1(&pressures[0], &outputs[0], &setpoints[0], Kp, Ki, Kd, DIRECT);
PID pid2(&pressures[1], &outputs[1], &setpoints[1], Kp, Ki, Kd, DIRECT);

// State Machine
enum SystemState { IDLE, TESTING, IGNITION, PID_CONTROL, SHUTDOWN };
SystemState currentState = IDLE;

void setup() {
  // Start with no serial connection until we receive the command from Python
  pinMode(LED_BUILTIN, OUTPUT);  // Optional: use for visual feedback (e.g., blinking LED when ready)
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');  // Read command from Python

    // Check for initialization command
    if (command == "INIT_SERIAL") {
      Serial.begin(9600);  // Initialize serial connection at 9600 baud rate
      digitalWrite(LED_BUILTIN, HIGH);  // Optional: turn on LED to show serial is initialized
      delay(500);  // Wait for half a second
      digitalWrite(LED_BUILTIN, LOW);  // Turn off LED
      Serial.println("Serial Initialized");
    }

    // Handle other commands as needed (e.g., control valves, send sensor data)
    // For example:
    // if (command == "BEGIN_TEST") {
    //     // Start the test...
    // }
  }
}


void loop() {
    readPressures();
    handleSerialCommands();
    executeStateLogic();
    sendData();
}

void readPressures() {
    for (int i = 0; i < 6; i++) {
        pressures[i] = analogRead(pressurePins[i]) * (5.0 / 1023.0);  // Convert to voltage
    }
}

void handleSerialCommands() {
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        if (command == "BEGIN_TEST") currentState = TESTING;
        else if (command == "START_IGNITION") currentState = IGNITION;
        else if (command == "SHUTDOWN") currentState = SHUTDOWN;
    }
}

void executeStateLogic() {
    switch (currentState) {
        case TESTING:
            // Just relay sensor data, valves stay off
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
    // Example: Open valve for 2s, then close
    analogWrite(valvePins[0], 255);
    delay(2000);
    analogWrite(valvePins[0], 0);
}

void sendData() {
    Serial.print("Pressure Data: ");
    for (int i = 0; i < 6; i++) {
        Serial.print(pressures[i]);
        Serial.print(i < 5 ? "," : "\n");
    }
}
