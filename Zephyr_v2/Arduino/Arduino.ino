#include <PID_v1.h>

// SETUP VARIABLES ----------------------------------------
// Ensure all defined variables are utilised for arduino functionality, and not for data processing.
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
double ptStepSize = 2.55;

// Solenoid Valve Setup: Digital Pins
const int solenoidValvePins[2] = {12, 13};
double svOutputs[2] = {0, 0};

// PWM Proportional Valve Setup: Digital PWM Pins
const int proportionalValvePins[2] = {9, 10};
double pvSetpoints[2] = {0, 0};
double pvOutputs[2] = {0, 0};
const double pvFuelMaxdP = 120;
const double pvOxMaxdP = 700;
const double pvMaxOpP = 1000;

// PID Setup (Kp, Ki, Kd to be tuned)
double kFuelPv[3] = {0.01, 0.005, 5.0};
double kOxPv[3] = {0.01, 0.005, 5.0};
PID pidFuel(&ptOutputsP[1], &pvOutputs[0], &pvSetpoints[0], kFuelPv[0], kFuelPv[1], kFuelPv[2], P_ON_M, DIRECT);
PID pidOx(&ptOutputsP[3], &pvOutputs[1], &pvSetpoints[1], kOxPv[0], kOxPv[1], kOxPv[2], P_ON_M, DIRECT);

// Timing and Data Transmission
unsigned long stateStartTime ;
unsigned long lastTransmitTime = 0;
const unsigned long transmitInterval = 200;  
unsigned long dataPointCount = 0;

// Rocket Operation Constants
const double oxidiserSetpointOxTest = 40;
const double oxidiserSetpointIgnition = 0;
const double fuelSetpointThrust = 20;
const double oxidiserSetpointThrust = 300;
const double fuelSetpointCooling = 0;
const double oxidiserSetpointCooling = 300;


// Test Timing Setup
const unsigned long testConnectionDuration = 5000;
const unsigned long pidDuration = 10000;
const unsigned long oxTestDuration = 25000;
const unsigned long ignitionDuration = 5000;
const unsigned long thrustDuration = 10000;
const unsigned long coolingDuration = 10000;
unsigned long lastPidUpdateTime = 0;
const unsigned long pidUpdateInterval = 200;


// State Machine -----------------------------------------

enum SystemState { 
  IDLE, 
  IDLEOX,
  TESTINGCONNECTION, 
  UPDATEKVALUES,
  PIDTUNETEST, 
  OXTEST,
  IGNITION,
  THRUSTING,
  COOLING
  };

SystemState currentState = IDLE;
SystemState lastState = IDLE;
// Helper Functions ------------------------------------------
// mode 0 = full test dataset
// mode 1 = air test dataset
void readPressures(int mode = 0) {
  static double ptOutputsV_avg[6] = {0};
  const int numReadings = 5;
  static double readings[6][numReadings] = {{0}};
  static int readIndex[6] = {0};
  static double totals[6] = {0};

  if (mode == 0) {
    for (int i = 0; i < 6; i++) {
      totals[i] -= readings[i][readIndex[i]];
      readings[i][readIndex[i]] = (analogRead(pressurePins[i]) / 1023.0) * ptRefV;
      totals[i] += readings[i][readIndex[i]];
      readIndex[i] = (readIndex[i] + 1) % numReadings;
      ptOutputsV_avg[i] = totals[i] / numReadings;
      ptOutputsV[i] = ptOutputsV_avg[i];
      ptOutputsP[i] = ptMinP + (ptOutputsV[i] - ptMinV) * (ptMaxP - ptMinP) / (ptMaxV - ptMinV);
      if (ptOutputsP[i] < ptMinP) ptOutputsP[i] = ptMinP;
    }
    ptdP[0] = ptOutputsP[0] - ptOutputsP[1];
    ptdP[1] = ptOutputsP[2] - ptOutputsP[3];
  }
  if (mode == 1) {
    for (int i = 2; i < 4; i++) {
      totals[i] -= readings[i][readIndex[i]];
      readings[i][readIndex[i]] = (analogRead(pressurePins[i]) / 1023.0) * ptRefV;
      totals[i] += readings[i][readIndex[i]];
      readIndex[i] = (readIndex[i] + 1) % numReadings;
      ptOutputsV_avg[i] = totals[i] / numReadings;
      ptOutputsV[i] = ptOutputsV_avg[i];
      ptOutputsP[i] = ptMinP + (ptOutputsV[i] - ptMinV) * (ptMaxP - ptMinP) / (ptMaxV - ptMinV);
      if (ptOutputsP[i] < ptMinP) ptOutputsP[i] = ptMinP;
    }
    ptdP[1] = ptOutputsP[2] - ptOutputsP[3];
  }
}

void checkPressureLimits(int mode = 0) {
  if (mode == 0) { // Full data: Check all differentials and operating pressures
    if (abs(ptdP[0]) > pvFuelMaxdP) {
      Serial.println("MAXdP_EXCEEDED");
      currentState = IDLE;
    } else if (abs(ptdP[1]) > pvOxMaxdP) {
      Serial.println("MAXdP_EXCEEDED");
      currentState = IDLE;
    }
    for (int i = 0; i < 2; i++) {
      if (ptOutputsP[i * 2 + 1] > ptMaxP) { // Check pressures[1] and pressures[3]
        Serial.println("MAXP_EXCEEDED " + String(i + 1));
        currentState = IDLE;
        break;
      }
    }
  }
  if (mode == 1) { // OX_TEST: Only check oxidizer differential (ptdP[1]) and relevant pressure
    struct FaultCheck {
      bool (*cond)();
      const char* msg;
    };

    FaultCheck checks[] = {
      { [](){ return abs(ptdP[1]) > pvOxMaxdP; }, "MAXdP_EXCEEDED" },
      { [](){ return ptOutputsP[3] > ptMaxP; }, "MAXP_EXCEEDED" },
    };
    const size_t numChecks = sizeof (checks) / sizeof(checks[0]);

    for (size_t i = 0; i < numChecks; ++i) {
      if (checks[i].cond()) {
        Serial.println(checks[i].msg);
        currentState = IDLE;
        return;
      }
    }
  }
}


void sendData(int mode = 0, bool forceSend = false) {
  unsigned long currentTime = millis();

  if (forceSend || (currentTime - lastTransmitTime >= transmitInterval)) {
    String data = String(dataPointCount++) + ",";

    if (mode == 0) {
      for (int i = 0; i < 6; i++) data += String(ptOutputsV[i], 2) + ",";
      for (int i = 0; i < 6; i++) data += String(ptOutputsP[i], 2) + ",";
      for (int i = 0; i < 2; i++) data += String(ptdP[i], 2) + ",";
      for (int i = 0; i < 2; i++) data += String(svOutputs[i]) + ",";
      for (int i = 0; i < 2; i++) data += String(pvSetpoints[i]) + ",";
      for (int i = 0; i < 2; i++) data += String(pvOutputs[i]) + ",";
    }
    if (mode == 1) {
      for (int i = 0; i < 2; i++) data += "0.00,";
      for (int i = 2; i < 4; i++) data += String(ptOutputsV[i], 2) + ",";
      for (int i = 4; i < 6; i++) data += "0.00,";
      for (int i = 0; i < 2; i++) data += "0.00,";
      for (int i = 2; i < 4; i++) data += String(ptOutputsP[i], 2) + ",";
      for (int i = 4; i < 6; i++) data += "0.00,";
      data += "0.00,";
      data += String(ptdP[1], 2) + ",";
      data += "0,";
      data += String(svOutputs[1]) + ",";
      data += "0.00,";
      data += String(pvSetpoints[1], 2) + ",";
      data += "0,";
      data += String(pvOutputs[1]) + ",";
    }
    data += String(currentTime - stateStartTime);
    Serial.println(data);
    lastTransmitTime = currentTime;
  }
}

void computePID(int mode = 0) {
  unsigned long currentTime = millis();
  if (currentTime - lastPidUpdateTime < pidUpdateInterval) return;
  lastPidUpdateTime = currentTime;

  if (mode == 0) {
    pidFuel.Compute();
    pidOx.Compute();
    analogWrite(proportionalValvePins[0], pvOutputs[0]);
    analogWrite(proportionalValvePins[1], pvOutputs[1]);
    Serial.print("PID Fuel Output: ");
    Serial.println(pvOutputs[0]);
    Serial.print("PID Ox Output: ");
    Serial.println(pvOutputs[1]);
  }
  if (mode == 1) {
    double error = pvSetpoints[1] - ptOutputsP[3];  // Error = setpoint - measured value
    double deadband = 15.0;  // Deadband of ±15 kPa

    // Determine the proportional mode based on the error
    if (abs(error) < deadband) {
        // Inside deadband: Use P_ON_E for fine-tuning
        pidOx.SetTunings(pidOx.GetKp(), pidOx.GetKi(), pidOx.GetKd(), P_ON_E);
    } else {
        // Outside deadband: Use P_ON_M to prevent overshooting
        pidOx.SetTunings(pidOx.GetKp(), pidOx.GetKi(), pidOx.GetKd(), P_ON_M);
    }

    // Compute PID regardless of deadband (but with different modes)
    pidOx.Compute();

    // Anti-windup: If output is saturated, stop accumulating integral term
    if (pvOutputs[1] >= 255 && (ptOutputsP[3] < pvSetpoints[1])) {
        pidOx.SetMode(MANUAL);  
        pidOx.SetMode(AUTOMATIC);
    }

    // Apply the new PWM value
    analogWrite(proportionalValvePins[1], pvOutputs[1]);
  }
}

void closeValvesSafetly(int mode = 0) {
  if (mode == 0) {
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
  if (mode == 1) {
    digitalWrite(solenoidValvePins[1], LOW);
    svOutputs[1] = 0;
    delay(100);
    pvOutputs[1] = 0;
    analogWrite(proportionalValvePins[1], 0);
  }
}

void openSolenoidValves(int mode = 0) {
  if (mode == 0) {
    for (int i = 0; i < 2; i++) {
      digitalWrite(solenoidValvePins[i], HIGH);
      svOutputs[i] = 1;
    }
  }
  if (mode == 1) {
    digitalWrite(solenoidValvePins[1], HIGH);
    svOutputs[1] = 1;
  }
}

void checkActiveCommands() {
  if (Serial.available()) {
    Serial.println("Serial data available, reading...");
  }
  while (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    Serial.print("Received command: '");
    Serial.print(input);
    Serial.println("'");
    Serial.print("Command length: ");
    Serial.println(input.length());
    if (input == "IDLE") {
      currentState = IDLE;
      Serial.println("State changed to IDLE");
    }
    else if (input == "IDLEOX") {
      currentState = IDLEOX;
      Serial.println("State changed to IDLEOX");
    }
    else if (input == "TEST_CONNECTION") {
      currentState = TESTINGCONNECTION;
      stateStartTime = millis();
      Serial.println("TEST_CONNECTION started");
    }
    else if (input == "OX_TEST") {
      currentState = OXTEST;
      stateStartTime = millis();
      pvSetpoints[1] = 0;
      Serial.println("OX_TEST started, ox setpoint reset to 0");
    }
    else {
      Serial.print("Uknown command: ");
      Serial.print(input);
    }
  }
}

// Void Loop ------------------------------------------------

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for Serial to initialize
  }
  Serial.flush();  // Clear any leftover data in the buffer
  pinMode(solenoidValvePins[0], OUTPUT);
  pinMode(solenoidValvePins[1], OUTPUT);
  pinMode(proportionalValvePins[0], OUTPUT);
  pinMode(proportionalValvePins[1], OUTPUT);
  pidFuel.SetMode(AUTOMATIC);
  pidOx.SetMode(AUTOMATIC);
  pidFuel.SetOutputLimits(180, 255);
  pidOx.SetOutputLimits(180, 255);
  pidFuel.SetSampleTime(10);
  pidOx.SetSampleTime(10);
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
  if (input == "IDLE") currentState = IDLE;
  if (input == "IDLEOX") currentState = IDLEOX;
  if (input == "TEST_CONNECTION") {
    currentState = TESTINGCONNECTION;
    stateStartTime = millis();
    Serial.println("TEST_CONNECTION started");
  }
  else if (input == "UPDATE_K_VALUES") {
    currentState = UPDATEKVALUES;
    Serial.println("Ready to configure K values...");
  }
  else if (input == "PID_TUNE_TEST") {
    currentState = PIDTUNETEST;
    stateStartTime = millis(); 
    Serial.println("PID_TUNE_TEST started");
  }
  else if (input == "OX_TEST") {
    currentState = OXTEST;
    stateStartTime = millis(); 
    Serial.println("OX_TEST started");
  }
  else if (input == "IGNITION") {
    currentState = IGNITION;
    stateStartTime = millis();
    pvSetpoints[1] = 0;
    Serial.println("IGNITION started");
  }
}

// Execute State Logic -----------------------------------------------

void executeStateLogic() {
  if (currentState != lastState && (currentState == IDLE || currentState == IDLEOX)) {
    Serial.println("IDLE");
    closeValvesSafetly(currentState == IDLE ? 0 : 1);
  }
  lastState = currentState;

  switch (currentState) {

    case IDLE:
      closeValvesSafetly(0);
      break;
    
    case IDLEOX:
      closeValvesSafetly(1);
      break;  

    case TESTINGCONNECTION:
      if (millis() - stateStartTime < testConnectionDuration) {
        readPressures(1);
        checkPressureLimits(1); 
        sendData(1); 
      } else {
        currentState = IDLEOX;
      }
      break;
    
    case UPDATEKVALUES:
      if (Serial.available()) {
        char buffer[64];
        int bytesRead = Serial.readBytesUntil('\n', buffer, sizeof(buffer) - 1);
        buffer[bytesRead] = '\0';
        double k_values[6];
        int parsed = sscanf(buffer, "%lf,%lf,%lf,%lf,%lf,%lf",
                            &k_values[0], &k_values[1], &k_values[2],
                            &k_values[3], &k_values[4], &k_values[5]);
        if (parsed == 6) {
          Serial.println("Updated K[P1,I1,D1,P2,I2,D2] Values: " +
                         String(k_values[0]) + "," + String(k_values[1]) + "," +
                         String(k_values[2]) + "," + String(k_values[3]) + "," +
                         String(k_values[4]) + "," + String(k_values[5]));
          Serial.println("K values updated successfully.");
        } else {
          Serial.println("Error: Expected 6 comma-separated double values.");
        }
      }
      currentState = IDLE;
      break;

    case PIDTUNETEST:
      openSolenoidValves(0);
      if (millis() - stateStartTime < pidDuration) {
        checkActiveCommands();
        readPressures(0);
        checkPressureLimits(0);
        pvSetpoints[0] = 10;
        pvSetpoints[1] = 300;
        computePID(0);
        sendData(0);
      } else {
        Serial.println("PID_DONE");
        currentState = IDLE;
      }
      break;
    
    case OXTEST:
      if (millis() - stateStartTime < oxTestDuration) {
        pvSetpoints[1] = oxidiserSetpointOxTest;
        openSolenoidValves(1);
        checkActiveCommands();
        readPressures(1);
        checkPressureLimits(1);
        computePID(1);
        sendData(1);
      } else {
        Serial.println("OX_TEST completed");
        currentState = IDLEOX;
      }
      break;
      
    case IGNITION:
      openSolenoidValves(0);
      if (millis() - stateStartTime < ignitionDuration) {
        checkActiveCommands();
        readPressures(0);
        checkPressureLimits(0);
        int steps = (millis() - stateStartTime) / (ignitionDuration / 6);
        pvSetpoints[0] = steps * ptStepSize;
        pvSetpoints[1] = oxidiserSetpointCooling;
        computePID(0);
        sendData(0);
      } else {
        pvSetpoints[0] = fuelSetpointThrust;
        pvSetpoints[1] = oxidiserSetpointThrust;
        currentState = THRUSTING;
        Serial.println("THRUSTING started");
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
        pvSetpoints[0] = fuelSetpointCooling;  
        pvSetpoints[1] = oxidiserSetpointCooling; 
        currentState = COOLING;
      }
    
      break;

    case COOLING:
      if (millis() - stateStartTime < coolingDuration) {
        checkActiveCommands();
        readPressures(0);
        checkPressureLimits(0);
        computePID(0);
        sendData(0);
      } else {
        Serial.println("Test Complete...");
        currentState = IDLE;
      }
      break;
  }
}



