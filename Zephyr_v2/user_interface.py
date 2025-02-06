import sys
import serial
import numpy as np
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class PressurePIDGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pressure and PID Control")
        self.setGeometry(100, 100, 1200, 800)  # Adjust window size to accommodate the graphs

        # Setup UI
        self.main_widget = QWidget(self)
        self.layout = QVBoxLayout(self.main_widget)

        # Create plot area (6 subplots)
        self.figure = Figure(figsize=(12, 8))  # Increased figure size for 6 subplots
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Create buttons
        self.init_button = QPushButton('Initialize Serial')
        self.init_button.setFont(QFont("Arial", 14))
        self.layout.addWidget(self.init_button)
        self.init_button.clicked.connect(self.initialize_serial)

        self.start_button = QPushButton('Start Test')
        self.start_button.setFont(QFont("Arial", 14))
        self.layout.addWidget(self.start_button)
        self.start_button.clicked.connect(self.start_test)

        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)

        # Setup serial connection (not opened yet)
        self.ser = None

        # Initialize data containers
        self.pressure_data_A0_A1 = []
        self.pressure_data_A2_A3 = []
        self.valve_pwm_1 = []
        self.valve_pwm_2 = []
        self.pressure_data_A4 = []
        self.pressure_data_A5 = []

        # Setup timer to periodically update the graph and retrieve serial data
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(1000)  # Update every second

    def initialize_serial(self):
        if self.ser is None:
            try:
                # Open the serial connection (replace 'COM3' with your actual port)
                self.ser = serial.Serial('COM3', 9600, timeout=1)
                self.ser.write(b'INIT_SERIAL\n')  # Send the initialization command to Arduino
                print("Sent INIT_SERIAL to Arduino")
                self.init_button.setEnabled(False)  # Disable the init button after it's been clicked
            except Exception as e:
                print(f"Error opening serial port: {e}")

    def start_test(self):
        if self.ser is not None:
            print("Test Started")
            self.ser.write(b'BEGIN_TEST\n')  # Command to begin test
        else:
            print("Serial connection not initialized yet!")

    def update_graph(self):
        if self.ser is not None and self.ser.in_waiting > 0:
            # Read data from the Arduino, assuming it's sending comma-separated values
            data = self.ser.readline().decode('utf-8').strip()
            if data:
                try:
                    # Assuming Arduino sends data in the format: A0,A1,A2,A3,valve_pwm_1,valve_pwm_2,A4,A5
                    A0, A1, A2, A3, valve_pwm_1, valve_pwm_2, A4, A5 = map(float, data.split(','))
                    # Append the values to respective lists
                    self.pressure_data_A0_A1.append((A0, A1))
                    self.pressure_data_A2_A3.append((A2, A3))
                    self.valve_pwm_1.append(valve_pwm_1)
                    self.valve_pwm_2.append(valve_pwm_2)
                    self.pressure_data_A4.append(A4)
                    self.pressure_data_A5.append(A5)

                    # Keep only the latest 50 values for smooth plotting
                    self.pressure_data_A0_A1 = self.pressure_data_A0_A1[-50:]
                    self.pressure_data_A2_A3 = self.pressure_data_A2_A3[-50:]
                    self.valve_pwm_1 = self.valve_pwm_1[-50:]
                    self.valve_pwm_2 = self.valve_pwm_2[-50:]
                    self.pressure_data_A4 = self.pressure_data_A4[-50:]
                    self.pressure_data_A5 = self.pressure_data_A5[-50:]

                    # Update the graph
                    self.plot_data()
                except ValueError:
                    print("Error parsing data:", data)

    def plot_data(self):
        self.figure.clear()

        # Create subplots: 6 graphs
        ax1 = self.figure.add_subplot(231)  # Graph 1: A0 and A1 pressure signals
        ax2 = self.figure.add_subplot(232)  # Graph 2: A2 and A3 pressure signals
        ax3 = self.figure.add_subplot(233)  # Graph 3: Valve 1 PWM
        ax4 = self.figure.add_subplot(234)  # Graph 4: Valve 2 PWM
        ax5 = self.figure.add_subplot(235)  # Graph 5: A4 pressure signal
        ax6 = self.figure.add_subplot(236)  # Graph 6: A5 pressure signal

        # Plot A0 and A1 pressure signals
        ax1.plot([x[0] for x in self.pressure_data_A0_A1], label="A0 Pressure", color='blue')
        ax1.plot([x[1] for x in self.pressure_data_A0_A1], label="A1 Pressure", color='orange')
        ax1.set_ylabel("Pressure (Pa)")
        ax1.legend(loc="upper left")

        # Plot A2 and A3 pressure signals
        ax2.plot([x[0] for x in self.pressure_data_A2_A3], label="A2 Pressure", color='green')
        ax2.plot([x[1] for x in self.pressure_data_A2_A3], label="A3 Pressure", color='red')
        ax2.set_ylabel("Pressure (Pa)")
        ax2.legend(loc="upper left")

        # Plot Valve 1 PWM
        ax3.plot(self.valve_pwm_1, label="Valve 1 PWM", color='purple')
        ax3.set_ylabel("PWM (%)")
        ax3.legend(loc="upper left")

        # Plot Valve 2 PWM
        ax4.plot(self.valve_pwm_2, label="Valve 2 PWM", color='brown')
        ax4.set_ylabel("PWM (%)")
        ax4.legend(loc="upper left")

        # Plot A4 pressure signal
        ax5.plot(self.pressure_data_A4, label="A4 Pressure", color='cyan')
        ax5.set_ylabel("Pressure (Pa)")
        ax5.legend(loc="upper left")

        # Plot A5 pressure signal
        ax6.plot(self.pressure_data_A5, label="A5 Pressure", color='magenta')
        ax6.set_ylabel("Pressure (Pa)")
        ax6.legend(loc="upper left")

        # Redraw the canvas to update the figure
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PressurePIDGUI()
    window.show()
    sys.exit(app.exec_())
