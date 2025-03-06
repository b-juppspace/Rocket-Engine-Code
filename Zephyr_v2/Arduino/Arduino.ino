#include <PID_v1.h>

// SETUP VARIABLES ----------------------------------------
// Pressures given in kPa
// const = constant value, won't change
// int = 16 bit integer
// double = double-precision floating-point number, 32 bit, 6-7 decimal digits of precision
// unsigned long = 32-bit unsigned (can't be negative) integer
// Pressure Transducer Setup: Analogue Pins
const int pressurePins[6] = {A0, A1, A2, A3, A4, A5};
double ptOutputsV[6];
double ptOutputsP[6];
double ptdP[2];
double ptMinV = 0.5;
double ptMaxV = 4.5;
double ptRefV = 5.0;
double ptMinP = 0;
double ptMaxP = 2000;
double ptStepSize = 0.366;

// Solenoid Valve Setup: Digital Pins
const int solenoidValvePins[2] = {12, 13};
double svOutputs[2] = {0, 0};

// PWM Proportional Valve Setup: Digital PWM Pins
const int proportionalValvePins[2] = {9, 6};
double pvSetpoints[2] = {0, 0};
double pvOutputs[2] = {0, 0};
const double pvFuelMaxdP = 120;
const double pvOxMaxdP = 700;
const double pvMaxOpP = 1000;

// PID Setup (Kp, Ki, Kd to be tuned)
double kFuelPv[3] = {1.0, 5.0, 2.0};
double kOxPv[3] = {1.0, 5.0, 2.0};
PID pidFuel(&ptOutputsP[1], &pvOutputs[0], &pvSetpoints[0], kFuelPv[0], kFuelPv[1], kFuelPv[2], DIRECT);
PID pidOx(&ptOutputsP[3], &pvOutputs[1], &pvSetpoints[1], kOxPv[0], kOxPv[1], kOxPv[2], DIRECT);

// Timing and Data Transmission
unsigned long stateStartTime ;
unsigned long lastTransmitTime = 0;
const unsigned long transmitInterval = 100;  
unsigned long dataPointCount = 0;

// Rocket Operation Constants
const double fuelSetpointThrust = 2.31;
const double oxidiserSetpointThrust = 45.21;
const double ignitionFuelStep = 0.33;

// Test Timing Setup
const unsigned long testConnectionDuration = 500;
const unsigned long pidDuration = 1000;
const unsigned long ignitionDuration = 5000;
const unsigned long thrustDuration = 10000;
const unsigned long coolingDuration = 10000;



// State Machine -----------------------------------------

enum SystemState { 
  IDLE, 
  TESTINGCONNECTION, 
  UPDATEKVALUES,
  PIDTUNETEST, 
  IGNITION,
  THRUSTING,
  COOLING
  };

SystemState currentState = IDLE;

// Helper Functions ------------------------------------------
void readPressures() {
  for (int i = 0; i < 6; i++) {
    ptOutputsV[i] = (analogRead(pressurePins[i]) / 1023.0) * ptRefV;
    ptOutputsP[i] = ptMinP + (ptOutputsV[i] - ptMinV) * (ptMaxP - ptMinP) / (ptMaxV - ptMinV);
    if (ptOutputsP[i] < ptMinP) ptOutputsP[i] = ptMinP;
  }
  ptdP[0] = ptOutputsP[0] - ptOutputsP[1];
  ptdP[1] = ptOutputsP[2] - ptOutputsP[3];
}

void checkPressureLimits() {
  // Check differential pressure limits for fuel (dP[0]) and oxidizer (dP[1])
  if (abs(ptdP[0]) > pvFuelMaxdP) {
    Serial.println("Warning: Fuel dP exceeds 120 kPa, triggering shutdown");
    currentState = IDLE;
  } else if (abs(ptdP[1]) > pvOxMaxdP) {
    Serial.println("Warning: Oxidizer dP exceeds 700 kPa, triggering shutdown");
    currentState = IDLE;
  }

  // Check operating pressure limits for valve outputs (assuming outputs reflect pressure control)
  for (int i = 0; i < 2; i++) {
    if (ptOutputsP[i * 2 + 1] > ptMaxP) { // Check pressures[1] and pressures[3] (PID inputs)
      Serial.println("Warning: Operating pressure exceeds 2 MPa for valve " + String(i + 1));
      currentState = IDLE;
      break; // Exit loop on first violation
    }
  }
}

void sendData(bool forceSend = false) {
  static unsigned long lastTransmitTime = 0;
  unsigned long currentTime = millis();

  if (forceSend || (currentTime - lastTransmitTime >= transmitInterval)) {
    String data = String(dataPointCount++) + ",";
    for (int i = 0; i < 6; i++) {
      data += String(ptOutputsV[i], 2) + ",";
    }
    for (int i = 0; i < 6; i++) {
      data += String(ptOutputsP[i], 2) + ",";
    }
    data += String(ptdP[0], 2) + "," + String(ptdP[1], 2) + ",";
    for (int i = 0; i < 2; i++) {
      data += String(svOutputs[i]) + ",";
    }
    for (int i = 0; i < 2; i++) {
      data += String(pvSetpoints[i]) + ",";
    }
    for (int i = 0; i < 2; i++) {
      data += String(pvOutputs[i]) + ",";
    }
    data += String(currentTime - stateStartTime);
    Serial.println(data);
    lastTransmitTime = currentTime;
  }
}

void computePID() {
  // Compute PID outputs
  pidFuel.Compute();
  pidOx.Compute();

  // Constrain outputs within the valid PWM range (0-255)
  pvOutputs[0] = constrain(pvOutputs[0], 0, 255);
  pvOutputs[1] = constrain(pvOutputs[1], 0, 255);

  // Control the valves using the computed PID outputs
  analogWrite(valvePins[0], outputs[0]);
  analogWrite(valvePins[1], outputs[1]);
}

void closeAllValvesSafetly() {
  for (int i = 0; i < 2; i++) {
    digitalWrite(solenoidValvePins[i], LOW);
    svOutputs[i] = 0;
  }
  delay(100);
  pvOutputs[0] = 0;
  pvOutputs[1] = 0;
  analogWrite(proportionalValvePins[0], 0);
  analogWrite(proportionalValvePins[1], 0);
}

void openAllSolenoidValves() {
  for (int i = 0; i < 2; i++) {
    digitalWrite(solenoidValvePins[i], HIGH);
    svOutputs[i] = 1;
    Serial.Println("Solenoid Valves Open");
  }
}

void checkActiveCommands() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');

    if (input == "EMERGENCY_SHUTDOWN") {
      Serial.println("Emergency shutdown initiated...hope you're alive!");
      currentState = IDLE;
    }
    else if (input.startsWith("UPDATESETPOINTS,")) {
      // Parse the received setpoints
      int commaIndex1 = input.indexOf(',', 10);  // Find first comma after "SETPOINTS,"
      if (commaIndex1 != -1) {
        pvSetpoints[0] = input.substring(10, commaIndex1).todouble();
        pvSetpoints[1] = input.substring(commaIndex1 + 1).todouble();
      }
    }
  }
}

// Void Loop ------------------------------------------------

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  for (int i = 0; i < 2; i++) {
    pinMode(solenoidValvePins[i], OUTPUT);
    pinMode(proportionalValvePins[i], OUTPUT); 
  }
  pid1.SetMode(AUTOMATIC);
  pid2.SetMode(AUTOMATIC);
  pid1.SetOutputLimits(0, 255);
  pid2.SetOutputLimits(0, 255);
}

void loop() {
  // Check if data is available and process it
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');  
    handleSerialCommands(input);  
  }
  executeStateLogic();
}

// Handle Serial Commands ---------------------------------------

void handleSerialCommands(String input) {
  if (input == "IDLE") {
    currentState = IDLE;
  }
  if (input == "TEST_CONNECTION") {
    currentState = TESTINGCONNECTION;
    stateStartTime = millis();
  }

  else if (input == "UPDATE_K_VALUES") {
    currentState = UPDATEKVALUES;
    Serial.println("Ready to configure K values...");
  }

  else if (input == "PID_TUNE_TEST") {
    currentState = PIDTUNETEST;
    stateStartTime = millis(); 
  }

  else if (input == "IGNITION") {
    currentState = IGNITION;
    stateStartTime = millis();
  }

}

// Execute State Logic -----------------------------------------------

void executeStateLogic() {
  switch (currentState) {

    case IDLE:
      closeAllValvesSafetly();
      Serial.println("IDLE");
      break;

    case TESTINGCONNECTION:
      if (millis() - stateStartTime < testConnectionDuration) {
        readPressures();
              checkPressureLimits();
              sendData(); 
      } else {
        Serial.println("TESTINGCONNECTION complete. Returning to IDLE.");
        currentState = IDLE;
      }
      break;
    
    case UPDATEKVALUES:
      if (Serial.available()) {
          char buffer[64];  // Buffer for the incoming line (adjust size as needed)
          int bytesRead = Serial.readBytesUntil('\n', buffer, sizeof(buffer) - 1);
          buffer[bytesRead] = '\0';  // Null-terminate the string
  
          double k_values[6];  // Array for 6 values
          int parsed = sscanf(buffer, "%f,%f,%f,%f,%f,%f", 
                             &k_values[0], &k_values[1], &k_values[2],
                             &k_values[3], &k_values[4], &k_values[5]);
  
          if (parsed == 6) {  // Expect exactly 6 values
              Serial.println("Updated K[P1,I1,D1,P2,I2,D2] Values: " + 
                             String(k_values[0]) + ", " + String(k_values[1]) + ", " + 
                             String(k_values[2]) + ", " + String(k_values[3]) + ", " + 
                             String(k_values[4]) + ", " + String(k_values[5]));
              Serial.println("K values updated successfully.");
          } else {
              Serial.println("Error: Expected 6 comma-separated double values.");
          }
      }
  
      currentState = IDLE;
      break;

    case PIDTUNETEST:
      Serial.println("PID Test Initiated...");
      openAllSolenoidValves();
      if (millis() - stateStartTime < pidDuration) {  
        checkActiveCommands();
        readPressures();
        checkPressureLimits();

        // Set test setpoints for PID controllers
        pvSetpoints[0] = 10;
        pvSetpoints[1] = 300;
    
        computePID();
        sendData();
    
      } else {
        // After 1 second, transition to IDLE state
        Serial.println("PID_DONE");
        currentState = IDLE;
      }
    
      break;


    case IGNITION:
      Serial.println("Ignition...");
      openAllSolenoidValves();
      // Run continuously until 1 second has passed
      if (millis() - stateStartTime < ignitionDuration) {  
        checkActiveCommands();
        readPressures();
        checkPressureLimits();
        
        int steps = (millis() - stateStartTime) / (ignitionDuration / 10);  
        pvSetpoints[0] = steps * ptStepSize;  
        pvSetpoints[1] = 0;  
        
        computePID();
        sendData();
    
      } else {
        pvSetpoints[0] = 20;  
        pvSetpoints[1] = 300; 
        currentState = THRUSTING;
      }
    
      break;

    case THRUSTING:
      Serial.println("Thrusting...");
      if (millis() - stateStartTime < thrustDuration) {  
        checkActiveCommands();
        readPressures();
        checkPressureLimits();
        computePID();
        sendData();
    
      } else {
        pvSetpoints[0] = 0;  
        pvSetpoints[1] = 45.21; 
        currentState = COOLING;
      }
    
      break;

    case COOLING:
      Serial.println("Cooling...");
      
      if (millis() - stateStartTime < 10000) {  
        checkActiveCommands();
        readPressures();
        checkPressureLimits();
        computePID();
        sendData();
    
      } else {
        Serial.println("Test Complete...");
        currentState = IDLE;
      }
    
      break;
  }
}



