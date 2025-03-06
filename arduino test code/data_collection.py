import serial
import time

# Ensure to replace the port with your actual device port
ser = serial.Serial('/dev/cu.usbmodem1101', 9600)  # For Mac, replace with your correct port
time.sleep(2)  # Give Arduino time to reset

def start_data_collection():
    # Send 'start' to Arduino to begin collecting data
    ser.write(b"start\n")
    print("Started data collection.")

def stop_data_collection():
    # Send 'stop' to Arduino to stop collecting data
    ser.write(b"stop\n")
    print("Stopped data collection.")

def save_data_to_file():
    # Get the current timestamp to create a unique filename
    current_time = time.strftime("%Y%m%d_%H%M%S")
    filename = f"data_{current_time}.csv"

    # Open the file to write data
    with open(filename, 'w') as file:
        # Write headers for the CSV file
        file.write("Timestamp (ms), PT0, PT1, PT2\n")
        
        # Continuously collect data until stopped
        while True:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').strip()  # Read a line
                if data:  # Ensure it's not an empty string
                    print(data)
                    file.write(data + "\n")
                
                # Check for the stop condition (you can use some timeout or manually stop the script)
                # (Optional) You can add a condition to break out of the loop after a certain amount of time
                # or by some user input to stop the data collection.

try:
    while True:
        # Ask the user for a command
        command = input("Enter command (start/stop/exit): ").strip().lower()

        if command == "start":
            start_data_collection()
            save_data_to_file()  # Start saving data after starting the test
        elif command == "stop":
            stop_data_collection()
        elif command == "exit":
            print("Exiting...")
            break
        else:
            print("Invalid command. Please enter 'start', 'stop', or 'exit'.")
except KeyboardInterrupt:
    print("Program interrupted. Exiting...")
finally:
    ser.close()  # Ensure serial connection is closed properly
