import serial
import time

# Make sure to use the correct port here
ser = serial.Serial('/dev/cu.usbmodem1101', 9600)  # Adjust the port as needed

# Give time for Arduino to reset
time.sleep(2)

# Send 'start' command
ser.write(b"start\n")

# Read data from Arduino
while True:
    if ser.in_waiting > 0:
        data = ser.readline().decode('utf-8').strip()  # Read a line of data
        print(data)  # Print the data received
