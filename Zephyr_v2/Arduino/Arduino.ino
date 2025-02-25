#include <PID_v1.h>

// SETUP VARIABLES ----------------------------------------

// Pressure Transducer Inputs
const int pressurePins[6] = {A0, A1, A2, A3, A4, A5};
double pressures[6];

// PWM Proportional Valve Outputs
const int valvePins[2] = {9, 6};
double setpoints[2] = {0, 0};  // Updated by GUI
double outputs[2] = {0, 0};

// PID Setup (Kp, Ki, Kd to be tuned)
double k_values[3] = {0, 0, 0}; //Updated by GUI
PID pid1(&pressures[1], &outputs[0], &setpoints[0], k_values[0], k_values[1], k_values[2], DIRECT);
PID pid2(&pressures[3], &outputs[1], &setpoints[1], k_values[0], k_values[1], k_values[2], DIRECT);

// Setup timing sequence and data point counter for data transmission
unsigned long stateStartTime ;
unsigned long lastTransmitTime = 0;
const unsigned long transmitInterval = 100;  // Send data every 100 ms
unsigned long dataPointCount = 0;

// State Machine -----------------------------------------

enum SystemState { 
  IDLE, 
  TESTINGCONNECTION, 
  UPDATEKVALUES,
  PIDTUNETEST, 
  IGNITION,
  THRUSTING
  };

SystemState currentState = IDLE;

// Void Loop ------------------------------------------------

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  // Check if data is available and process it
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');  // Read data until newline character
    handleSerialCommands(command);  // Directly pass the input to the function
  }

  // Execute state logic based on the current state
  executeStateLogic();
}

// Handle Serial Commands ---------------------------------------

void handleSerialCommands(String command) {
  if (command == "TEST_CONNECTION") {
    currentState = TESTINGCONNECTION;
    stateStartTime = millis();
    // Serial.println("Entering TEST_CONNECTION...")
  }

  else if (command == "UPDATE_K_VALUES") {
    currentState = UPDATEKVALUES;
    stateStartTime = millis();
    Serial.println("State set to UPDATEKVALUES");
    // Serial.println("Entering UPDATE_K_VALUES...")
  }

  else if (command == "PID_TUNE_TEST") {
    currentState = PIDTUNETEST;
    stateStartTime = millis(); 
    // Serial.println("Entering PIDTUNETEST...");
  }

  else if (command == "IGNITION") {
    currentState = IGNITION;
    stateStartTime = millis();
  }

}

// Execute State Logic -----------------------------------------------

void executeStateLogic() {
  switch (currentState) {

    case IDLE:
      Serial.println("IDLE");
      // Ensure valves are fully closed
      outputs[0] = 0;
      outputs[1] = 0;
      analogWrite(valvePins[0], 0);
      analogWrite(valvePins[1], 0);
      break;

    case TESTINGCONNECTION:
      // Only send data at the specified interval
      if (millis() - lastTransmitTime >= transmitInterval) {
        // UPDATE PRESSURES!!
        for (int i = 0; i < 6; i++) {
          pressures[i] = analogRead(pressurePins[i]); // Read each analog pin and update pressures[]
        }

        // Format data as a comma-separated string
        String data = "";

        // Append data point count
        data += "DataPointCount:" + String(dataPointCount++) + ",";

        // Append pressure values
        for (int i = 0; i < 6; i++) {
          data += String(pressures[i]);
          if (i < 5) data += ",";  
        }

        // Append setpoints
        for (int i = 0; i < 2; i++) {
          data += "," + String(setpoints[i]);
        }

        // Append outputs
        for (int i = 0; i < 2; i++) {
          data += "," + String(outputs[i]);
        }

        // Append time
        data += "," + String(millis() - stateStartTime);

        // Send the data string via Serial
        Serial.println(data);

        // Update the last transmit time
        lastTransmitTime = millis();
      }

      // Check if 0.5 seconds have passed
      if (millis() - stateStartTime >= 500) {
        Serial.println("TESTINGCONNECTION complete. Returning to IDLE.");
        currentState = IDLE;
      }
      break;
    
    case UPDATEKVALUES:
      // Check for new command and parse it if available
      if (Serial.available()) {
        String input = Serial.readStringUntil('\n');  // Read the incoming string until newline
        
        // Check if the input matches the expected format
        int firstComma = input.indexOf(',');
        int secondComma = input.indexOf(',', firstComma + 1);
        
        // Ensure there are two commas, meaning we have three values
        if (firstComma > 0 && secondComma != -1) {
          k_values[0] = input.substring(0, firstComma).toFloat();  // Extract the first value
          k_values[1] = input.substring(firstComma + 1, secondComma).toFloat();  // Extract the second value
          k_values[2] = input.substring(secondComma + 1).toFloat();  // Extract the third value

          // Print the updated values to the serial monitor for verification
          Serial.println("Updated K[P,I,D] Values: " + String(k_values[0]) + ", " + String(k_values[1]) + ", " + String(k_values[2]));

          // Optionally send a confirmation to the GUI
          Serial.println("K values updated successfully.");
        } 
        else {
          // If the format is incorrect, send an error message
          Serial.println("Error in UPDATEKVALUES command format");
        }
      }

      // Transition back to IDLE state after processing
      currentState = IDLE;
      break;

    case PIDTUNETEST:
      // Run continuously until 1 second has passed
      if (millis() - stateStartTime < 1000) {  
        // Update pressure readings
        for (int i = 0; i < 6; i++) {
          pressures[i] = analogRead(pressurePins[i]); // Read each analog pin and update pressures[]
        }
    
        // Set setpoints for PID controllers
        setpoints[0] = 2.31;
        setpoints[1] = 45.21;
    
        // Compute PID outputs
        pid1.Compute();
        pid2.Compute();
    
        // Constrain outputs within the valid PWM range (0-255)
        outputs[0] = constrain(outputs[0], 0, 255);
        outputs[1] = constrain(outputs[1], 0, 255);

        // Control the valves using the computed PID outputs
        analogWrite(valvePins[0], outputs[0]);
        analogWrite(valvePins[1], outputs[1]);
    
        // Create the data string to send via Serial
        String data = "";
        data += "DataPointCount:" + String(dataPointCount++) + ",";  // Include data point count
        for (int i = 0; i < 6; i++) {
          data += String(pressures[i]);
          if (i < 5) data += ",";
        }
        for (int i = 0; i < 2; i++) {
          data += "," + String(setpoints[i]);
        }
        for (int i = 0; i < 2; i++) {
          data += "," + String(outputs[i]);
        }
        data += "," + String(millis() - stateStartTime);  // Send elapsed time
        Serial.println(data);  // Send data via Serial
    
      } else {
        // After 1 second, transition to IDLE state
        Serial.println("PIDTUNETEST complete. Returning to IDLE.");
        currentState = IDLE;
      }
    
      break;


    case IGNITION:
      // Run continuously until 1 second has passed
      if (millis() - stateStartTime < 5000) {  
        // Calculate the number of steps (each step corresponds to an increase of 0.33)
        int steps = (millis() - stateStartTime) / (5000 / 7);  // 7 steps over 5 seconds
        setpoints[0] = steps * 0.33;  // Increase fuel setpoint by 0.33 at each step
        setpoints[1] = 0;  // Oxidizer remains closed during ignition
        
        // Update pressure readings
        for (int i = 0; i < 6; i++) {
          pressures[i] = analogRead(pressurePins[i]); // Read each analog pin and update pressures[]
        }
    
        // Check for new commands from Serial
        if (Serial.available()) {
          String input = Serial.readStringUntil('\n');

          if (input == "IDLE") {
            currentState = IDLE;
          }
        }

        // Compute PID outputs
        pid1.Compute();
        pid2.Compute();
    
        // Constrain outputs within the valid PWM range (0-255)
        outputs[0] = constrain(outputs[0], 0, 255);
        outputs[1] = constrain(outputs[1], 0, 255);

        // Control the valves using the computed PID outputs
        analogWrite(valvePins[0], outputs[0]);
        analogWrite(valvePins[1], outputs[1]);
    
        // Create the data string to send via Serial
        String data = "";
        data += "DataPointCount:" + String(dataPointCount++) + ",";  // Include data point count
        for (int i = 0; i < 6; i++) {
          data += String(pressures[i]);
          if (i < 5) data += ",";
        }
        for (int i = 0; i < 2; i++) {
          data += "," + String(setpoints[i]);
        }
        for (int i = 0; i < 2; i++) {
          data += "," + String(outputs[i]);
        }
        data += "," + String(millis() - stateStartTime);  // Send elapsed time
        Serial.println(data);  // Send data via Serial
    
      } else {
        // After 5 seconds, transition to THRUSTING state
        currentState = THRUSTING;
      }
    
      break;

    case THRUSTING:
      // Run continuously until 1 second has passed
      if (millis() - stateStartTime < 10000) {  
        // Update pressure readings
        for (int i = 0; i < 6; i++) {
          pressures[i] = analogRead(pressurePins[i]); // Read each analog pin and update pressures[]
        }
    
        // Check for new setpoints from Serial
        if (Serial.available()) {
          String input = Serial.readStringUntil('\n');

          if (input == "IDLE") {
            currentState = IDLE;
          }
          else if (input.startsWith("UPDATESETPOINTS,")) {
            // Parse the received setpoints
            int commaIndex1 = input.indexOf(',', 10);  // Find first comma after "SETPOINTS,"
            if (commaIndex1 != -1) {
              setpoints[0] = input.substring(10, commaIndex1).toFloat();
              setpoints[1] = input.substring(commaIndex1 + 1).toFloat();
            }
          }
        }

        // Compute PID outputs
        pid1.Compute();
        pid2.Compute();
    
        // Constrain outputs within the valid PWM range (0-255)
        outputs[0] = constrain(outputs[0], 0, 255);
        outputs[1] = constrain(outputs[1], 0, 255);

        // Control the valves using the computed PID outputs
        analogWrite(valvePins[0], outputs[0]);
        analogWrite(valvePins[1], outputs[1]);
    
        // Create the data string to send via Serial
        String data = "";
        data += "DataPointCount:" + String(dataPointCount++) + ",";  // Include data point count
        for (int i = 0; i < 6; i++) {
          data += String(pressures[i]);
          if (i < 5) data += ",";
        }
        for (int i = 0; i < 2; i++) {
          data += "," + String(setpoints[i]);
        }
        for (int i = 0; i < 2; i++) {
          data += "," + String(outputs[i]);
        }
        data += "," + String(millis() - stateStartTime);  // Send elapsed time
        Serial.println(data);  // Send data via Serial
    
      } else {
        // After 1 second, transition to IDLE state
        currentState = IDLE;
      }
    
      break;

    default:
      break;

    
  }
}



