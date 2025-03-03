import sys
import serial
import threading
import pyqtgraph as pg
import time
import csv
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QSlider, QHBoxLayout, QTabWidget, QTextEdit, QLineEdit
from PyQt5.QtGui import QPalette, QColor, QFont, QPixmap, QFont
from PyQt5.QtCore import Qt
import os
from datetime import datetime

class PressureControlGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.serial_conn = None
        self.running = False
        # insert variable list here?
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Command Centre")
        self.setFixedSize(1400, 900)

        # Setup Variables -------------------------------------------------------
        font = QFont("Consolas", 10)
        small_font = QFont("Consolas", 8)
        header_font = QFont("Consolas", 12, QFont.Bold)
        title_font = QFont("Consolas", 16, QFont.Bold)
        self.setFont(font)
        graph_label = "<span style='font-size:10pt; font-weight:bold; color:white; font-family:Consolas;'>{}</span>"
         
        
        # Setup main layout -----------------------------------------------------

        main_layout = QHBoxLayout()
        image_path = os.path.join(os.getcwd(), "logosmall")
        
        # Tab setup -----------------------------------------------------

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget {
                background-color: #000000 !important;  /* Ensure tab widget background is black */
                color: #ffffff;
                border: none;
            }

            QTabWidget::pane {
                background-color: #000000 !important;  /* Ensure the content area background is also black */
                border: none;
            }

            QTabBar::tab {
                background-color: #ffffff;
                color: #000000;
                height: 30px;
                width: 140px;
                padding: 5px;
                border: 1px solid #1e1e2e; /* optional border around each tab */
            }
            
            QTabBar::tab:selected {
                background-color: #000000;
                color: #ffffff;
            }

            QTabBar::tab:hover {
                background-color: #e9e9e9;
                color: #000000;
            }
        """)                       
        self.tabs.setFont(font)
        
        # Menu layout ------------------------------------------------------
        self.menu_tab = QWidget()
        menu_layout = QVBoxLayout()
        self.menu_tab.setFont(font)
        self.menu_tab.setLayout(menu_layout)

        self.tabs.addTab(self.menu_tab, "Menu")

        # Load and display the image
        self.logo_label = QLabel()
        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            print("Error: Could not load logo.png")

        self.logo_label.setPixmap(pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)  # Center the image
        menu_layout.addWidget(self.logo_label)

        self.menu_title_label = QLabel("Juppspace Test GUI")
        self.menu_title_label.setFont(QFont(title_font))
        self.menu_title_label.setAlignment(Qt.AlignCenter)
        self.menu_title_label.setStyleSheet("color: white;")
        menu_layout.addWidget(self.menu_title_label)

        self.menu_text_label = QLabel("Script for rocket engine test purposes.")
        self.menu_text_label.setFont(QFont(font))
        self.menu_text_label.setAlignment(Qt.AlignCenter)
        self.menu_text_label.setStyleSheet("color: white;")
        menu_layout.addWidget(self.menu_text_label)

        # Settings layout ------------------------------------------------------
        self.connection_tab = QWidget()
        connection_layout = QVBoxLayout()
        self.connection_tab.setFont(font)
        self.connection_tab.setLayout(connection_layout)
        self.tabs.addTab(self.connection_tab, "Settings")

        self.connection_title_label = QLabel("Terminal")
        self.connection_title_label.setFont(QFont(header_font))
        self.connection_title_label.setStyleSheet("color: white;")
        connection_layout.addWidget(self.connection_title_label)

        self.connection_output = QTextEdit()
        self.connection_output.setReadOnly(True)
        self.connection_output.setStyleSheet("background-color: #000000; color: #ffffff;")
        self.connection_output.setFont(font)
        connection_layout.addWidget(self.connection_output)
        
        self.init_serial_button = QPushButton("Initialize Serial Port")
        self.init_serial_button.clicked.connect(self.init_serial)
        self.init_serial_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        self.init_serial_button.setFont(font)
        connection_layout.addWidget(self.init_serial_button)
        
        self.test_connection_button = QPushButton("Test Connection")
        self.test_connection_button.clicked.connect(self.test_connection)
        self.test_connection_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        self.test_connection_button.setFont(font)
        connection_layout.addWidget(self.test_connection_button)

        self.tune_label = QLabel("Tune PID K-Values")
        self.tune_label.setFont(header_font)
        self.tune_label.setStyleSheet("color: #ffffff;")
        connection_layout.addWidget(self.tune_label)
        
        # ------------------------------sliders---------------------------
        slider_layout = QHBoxLayout()
        slider_v1_section = QVBoxLayout()

        self.kp_label = QLabel("kp: 1.00")
        self.kp_label.setFont(font)
        self.kp_label.setStyleSheet("color: #ffffff;")
        slider_v1_section.addWidget(self.kp_label)

        self.kp_slider = QSlider(Qt.Horizontal)
        self.kp_slider.setRange(0, 80)
        self.kp_slider.setValue(10)
        self.kp_slider.valueChanged.connect(self.update_kp)
        self.kp_slider.setStyleSheet("""
            QSlider::handle:horizontal {
                background: #ffffff;
            }
        """)
        slider_v1_section.addWidget(self.kp_slider)
        
        self.ki_label = QLabel("ki: 5.00")
        self.ki_label.setFont(QFont(font))
        self.ki_label.setStyleSheet("color: #ffffff;")
        slider_v1_section.addWidget(self.ki_label)

        self.ki_slider = QSlider(Qt.Horizontal)
        self.ki_slider.setRange(0, 80)
        self.ki_slider.setValue(50)
        self.ki_slider.valueChanged.connect(self.update_ki)
        self.ki_slider.setStyleSheet("""
            QSlider::handle:horizontal {
                background: #ffffff;
            }
        """)
        slider_v1_section.addWidget(self.ki_slider)
        
        self.kd_label = QLabel("kd: 2.00")
        self.kd_label.setFont(QFont(font))
        self.kd_label.setStyleSheet("color: #ffffff;")
        slider_v1_section.addWidget(self.kd_label)

        self.kd_slider = QSlider(Qt.Horizontal)
        self.kd_slider.setRange(0, 80)
        self.kd_slider.setValue(20)
        self.kd_slider.valueChanged.connect(self.update_kd)
        self.kd_slider.setStyleSheet("""
            QSlider::handle:horizontal {
                background: #ffffff;
            }
        """)
        slider_v1_section.addWidget(self.kd_slider)


        slider_v2_section = QVBoxLayout()

        self.kp2_label = QLabel("kp: 1.00")
        self.kp2_label.setFont(font)
        self.kp2_label.setStyleSheet("color: #ffffff;")
        slider_v2_section.addWidget(self.kp2_label)

        self.kp2_slider = QSlider(Qt.Horizontal)
        self.kp2_slider.setRange(0, 80)
        self.kp2_slider.setValue(10)
        self.kp2_slider.valueChanged.connect(self.update_kp2)
        self.kp2_slider.setStyleSheet("""
            QSlider::handle:horizontal {
                background: #ffffff;
            }
        """)
        slider_v2_section.addWidget(self.kp2_slider)
        
        self.ki2_label = QLabel("ki: 5.00")
        self.ki2_label.setFont(QFont(font))
        self.ki2_label.setStyleSheet("color: #ffffff;")
        slider_v2_section.addWidget(self.ki2_label)

        self.ki2_slider = QSlider(Qt.Horizontal)
        self.ki2_slider.setRange(0, 80)
        self.ki2_slider.setValue(50)
        self.ki2_slider.valueChanged.connect(self.update_ki2)
        self.ki2_slider.setStyleSheet("""
            QSlider::handle:horizontal {
                background: #ffffff;
            }
        """)
        slider_v2_section.addWidget(self.ki2_slider)
        
        self.kd2_label = QLabel("kd: 2.00")
        self.kd2_label.setFont(QFont(font))
        self.kd2_label.setStyleSheet("color: #ffffff;")
        slider_v2_section.addWidget(self.kd2_label)

        self.kd2_slider = QSlider(Qt.Horizontal)
        self.kd2_slider.setRange(0, 80)
        self.kd2_slider.setValue(20)
        self.kd2_slider.valueChanged.connect(self.update_kd2)
        self.kd2_slider.setStyleSheet("""
            QSlider::handle:horizontal {
                background: #ffffff;
            }
        """)
        slider_v2_section.addWidget(self.kd2_slider)


        slider_layout.addLayout(slider_v1_section)
        slider_layout.addLayout(slider_v2_section)
        connection_layout.addLayout(slider_layout)


        self.send_k_button = QPushButton("Send K Values")
        self.send_k_button.clicked.connect(self.send_k_values_connection)
        self.send_k_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        self.send_k_button.setFont(font)
        connection_layout.addWidget(self.send_k_button)
        
        self.note_label = QLabel("Note: Open valves to complete PID tuning tests. Valve will open to provide pressure of 45psi for air and 2 psi for fuel, edit K values for tuning of response.")
        self.note_label.setWordWrap(True)  # Allows text wrapping for long messages
        self.note_label.setStyleSheet("background-color: #000000; color: #ffffff; ")
        self.note_label.setFont(small_font)
        connection_layout.addWidget(self.note_label)

        self.pid_tune_test_button = QPushButton("Begin PID Tune Test")
        self.pid_tune_test_button.clicked.connect(self.pid_tune_test_connection)
        self.pid_tune_test_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        self.pid_tune_test_button.setFont(font)
        connection_layout.addWidget(self.pid_tune_test_button)
        
        # PID Tune Test Graph Layout
        graph_layout = QHBoxLayout()
        
        self.graph_V1_PID = pg.PlotWidget()
        self.graph_V1_PID.setTitle(graph_label.format("Valve 1"))
        self.graph_V1_PID.setLabel('left', graph_label.format("P (psi)"))
        self.graph_V1_PID.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_V1_PID.getAxis('left').setStyle(tickFont=font)
        self.graph_V1_PID.getAxis('bottom').setStyle(tickFont=font)

        self.graph_V2_PID = pg.PlotWidget()
        self.graph_V2_PID.setTitle(graph_label.format("Valve 2"))
        self.graph_V2_PID.setLabel('left', graph_label.format("P (psi)"))
        self.graph_V2_PID.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_V2_PID.getAxis('left').setStyle(tickFont=font)
        self.graph_V2_PID.getAxis('bottom').setStyle(tickFont=font)

        graph_layout.addWidget(self.graph_V1_PID)
        graph_layout.addWidget(self.graph_V2_PID)
        
        connection_layout.addLayout(graph_layout)
        
        # PLay tab layout --------------------------------------------

        self.control_tab = QWidget()
        control_layout = QVBoxLayout()
        self.control_tab.setLayout(control_layout)
        self.tabs.addTab(self.control_tab, "Play")
        
        self.control_title_label2 = QLabel("Terminal")
        self.control_title_label2.setFont(QFont("Consolas", 12, QFont.Bold))
        self.control_title_label2.setStyleSheet("color: white;")
        control_layout.addWidget(self.control_title_label2)

        self.control_output = QTextEdit()
        self.control_output.setReadOnly(True)
        self.control_output.setStyleSheet("background-color: #000000; color: #ffffff;")
        self.control_output.setFont(font)
        control_layout.addWidget(self.control_output)

        self.valve1_label = QLabel("Valve 1: 2.31")
        self.valve1_label.setFont(QFont("Consolas", 10))
        self.valve1_label.setStyleSheet("color: #ffffff;")
        control_layout.addWidget(self.valve1_label)

        self.valve1_slider = QSlider(Qt.Horizontal)
        self.valve1_slider.setRange(0, 30)
        self.valve1_slider.setValue(7)
        self.valve1_slider.valueChanged.connect(self.update_valve1) # Live value change 
        self.valve1_slider.setStyleSheet("QSlider::handle:horizontal {background: #ffffff;}")
        control_layout.addWidget(self.valve1_slider)
        
        self.valve2_label = QLabel("Valve 2: 45.21")
        self.valve2_label.setFont(QFont("Consolas", 10))
        self.valve2_label.setStyleSheet("color: #ffffff;")
        control_layout.addWidget(self.valve2_label)

        self.valve2_slider = QSlider(Qt.Horizontal)
        self.valve2_slider.setRange(0, 240)
        self.valve2_slider.setValue(137)
        self.valve2_slider.valueChanged.connect(self.update_valve2)  
        self.valve2_slider.setStyleSheet("QSlider::handle:horizontal {background: #ffffff;}")
        control_layout.addWidget(self.valve2_slider)
        
        button_layout = QHBoxLayout()

        self.ignition_button = QPushButton("Ignition")
        self.ignition_button.clicked.connect(self.ignition)
        self.ignition_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        self.ignition_button.setFont(font)
        button_layout.addWidget(self.ignition_button)

        self.shutdown_button = QPushButton("Shutdown")
        self.shutdown_button.clicked.connect(self.shutdown)
        self.shutdown_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        self.shutdown_button.setFont(font)
        button_layout.addWidget(self.shutdown_button)

        control_layout.addLayout(button_layout)
        
        # Graph Layout 2
        graph_layout2 = QHBoxLayout()

        graph_column1 = QVBoxLayout()

        self.graph_A0A1 = pg.PlotWidget()
        self.graph_A0A1.setTitle(graph_label.format("A0/A1"))
        self.graph_A0A1.setLabel('left', graph_label.format("P (psi)"))
        self.graph_A0A1.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_A0A1.getAxis('left').setStyle(tickFont=font)
        self.graph_A0A1.getAxis('bottom').setStyle(tickFont=font)
        graph_column1.addWidget(self.graph_A0A1)

        self.graph_PWM1 = pg.PlotWidget()
        self.graph_PWM1.setTitle(graph_label.format("PWM1"))
        self.graph_PWM1.setLabel('left', graph_label.format("PWM(0-255)"))
        self.graph_PWM1.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_PWM1.getAxis('left').setStyle(tickFont=font)
        self.graph_PWM1.getAxis('bottom').setStyle(tickFont=font)
        graph_column1.addWidget(self.graph_PWM1)
        
        graph_column2 = QVBoxLayout()

        self.graph_A2A3 = pg.PlotWidget()
        self.graph_A2A3.setTitle(graph_label.format("A2/A3"))
        self.graph_A2A3.setLabel('left', graph_label.format("P (psi)"))
        self.graph_A2A3.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_A2A3.getAxis('left').setStyle(tickFont=font)
        self.graph_A2A3.getAxis('bottom').setStyle(tickFont=font)
        graph_column2.addWidget(self.graph_A2A3)

        self.graph_PWM2 = pg.PlotWidget()
        self.graph_PWM2.setTitle(graph_label.format("PWM2"))
        self.graph_PWM2.setLabel('left', graph_label.format("PWM(0-255)"))
        self.graph_PWM2.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_PWM2.getAxis('left').setStyle(tickFont=font)
        self.graph_PWM2.getAxis('bottom').setStyle(tickFont=font)
        graph_column2.addWidget(self.graph_PWM2)

        self.graph_A4A5 = pg.PlotWidget()
        self.graph_A4A5.setTitle(graph_label.format("A4/A5"))
        self.graph_A4A5.setLabel('left', graph_label.format("P (psi)"))
        self.graph_A4A5.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_A4A5.getAxis('left').setStyle(tickFont=font)
        self.graph_A4A5.getAxis('bottom').setStyle(tickFont=font)
        
        graph_layout2.addLayout(graph_column1)
        graph_layout2.addLayout(graph_column2)
        graph_layout2.addWidget(self.graph_A4A5)
        
        control_layout.addLayout(graph_layout2)

    # Health tab layout --------------------------------------------

        self.health_tab = QWidget()
        health_layout = QVBoxLayout()
        self.health_tab.setLayout(health_layout)
        self.tabs.addTab(self.health_tab, "Health")
        
        # Health Graph Layout
        graph_layout3 = QHBoxLayout()
        
        self.graph_delta_A0A1 = pg.PlotWidget()
        self.graph_delta_A0A1.setTitle(graph_label.format("delta A0/A1"))
        self.graph_delta_A0A1.setLabel('left', graph_label.format("P (psi)"))
        self.graph_delta_A0A1.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_delta_A0A1.getAxis('left').setStyle(tickFont=font)
        self.graph_delta_A0A1.getAxis('bottom').setStyle(tickFont=font)

        self.graph_delta_A2A3 = pg.PlotWidget()
        self.graph_delta_A2A3.setTitle(graph_label.format("delta A2/A3"))
        self.graph_delta_A2A3.setLabel('left', graph_label.format("P (psi)"))
        self.graph_delta_A2A3.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_delta_A2A3.getAxis('left').setStyle(tickFont=font)
        self.graph_delta_A2A3.getAxis('bottom').setStyle(tickFont=font)

        graph_layout3.addWidget(self.graph_delta_A0A1)
        graph_layout3.addWidget(self.graph_delta_A2A3)

        health_layout.addLayout(graph_layout3)


        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
    
    #--------------Stored Data Variables--------------
    def variables(self):    
        self.A0 = []
        self.A1 = []
        self.A2 = []
        self.A3 = []
        self.A4 = []
        self.A5 = []
        self.v1_setpoint = []
        self.v2_setpoint = []
        self.v1_output = []
        self.v2_output = []
        self.time = []
        self.delta_A0A1 = []
        self.delta_A2A3 = []
        self.v1_max_delta = 100                                
        self.v2_max_delta = 17                             
    #--------------General Definitions----------------

    def init_serial(self):
        """ Connects GUI to serial port. """
        try:
            self.serial_conn = serial.Serial("COM3", 115200, timeout=1)
            self.running = True
        except serial.SerialException as e:
            self.connection_output.append(f"Error: {e}")

    def send_command(self, command):
        """ Sends a command through the serial port. """
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.write((command + "\n").encode())

    def read_serial_data(self):
        """ Reads a single line from the serial port. """
        if self.serial_conn and self.serial_conn.in_waiting:
            return self.serial_conn.readline().decode().strip().split(",")
        return None
    
    def save_data(self):
        # Get current directory
        current_dir = os.getcwd()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%m-%d_%H-%M")
        file_name = os.path.join(current_dir, f"DATA_{timestamp}.csv")

        with open(file_name, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Time", "A0", "A1", "A2", "A3", "A4", "A5", "V1 Setpoint", "V2 Setpoint", "V1 Output", "V2 Output"])
            
            for i in range(len(self.time)):  # Use self.time instead of self.time_series
                writer.writerow([
                    self.time[i], self.A0[i], self.A1[i], self.A2[i], self.A3[i], self.A4[i], self.A5[i], 
                    self.v1_setpoint[i], self.v2_setpoint[i], self.v1_output[i], self.v2_output[i]
                ])

    #-------------K-Slider Definitions-----------------

    def update_kp(self):
        value = self.kp_slider.value() * 0.1
        self.kp_label.setText(f"kp: {value:.2f}")

    def update_ki(self):
        value = self.ki_slider.value() * 0.1
        self.ki_label.setText(f"ki: {value:.2f}")

    def update_kd(self):
        value = self.kd_slider.value() * 0.1
        self.kd_label.setText(f"kd: {value:.2f}")

    def update_kp2(self):
        value = self.kp2_slider.value() * 0.1
        self.kp2_label.setText(f"kp: {value:.2f}")

    def update_ki2(self):
        value = self.ki2_slider.value() * 0.1
        self.ki2_label.setText(f"ki: {value:.2f}")

    def update_kd2(self):
        value = self.kd2_slider.value() * 0.1
        self.kd2_label.setText(f"kd: {value:.2f}")

    def send_k_values_connection(self):
        self.send_command("UPDATE_K_VALUES")

        # Wait for Arduino to confirm it has entered the state
        while True:
            response = self.read_serial_data()
            if "State set to UPDATEKVALUES" in response:  # Arduino confirms state change
                self.connection_output.append(response)
                break  # Exit loop when confirmation is received
            time.sleep(0.05)  # Small delay to avoid busy-waiting
        
        kp_value = self.kp_slider.value() * 0.1
        ki_value = self.ki_slider.value() * 0.1
        kd_value = self.kd_slider.value() * 0.1
        kp2_value = self.kp2_slider.value() * 0.1
        ki2_value = self.ki2_slider.value() * 0.1
        kd2_value = self.kd2_slider.value() * 0.1
        self.send_command(f"{kp_value},{ki_value},{kd_value},{kp2_value}, {ki2_value}, {kd2_value}")

        response = self.read_serial_data()
        self.connection_output.append(response)
    
    #--------------Setpoint-Slider Definitions-----------

    def update_valve1(self):
        value = self.valve1_slider.value() * 0.33
        self.valve1_label.setText(f"Valve 1: {value:.2f}")
        self.send_setpoints()
    
    def update_valve2(self):
        value = self.valve2_slider.value() * 0.33
        self.valve2_label.setText(f"Valve 2: {value:.2f}")
        self.send_setpoints()
    
    def send_setpoints(self):
        if self.serial_conn and self.serial_conn.is_open:
            valve1_value = self.valve1_slider.value() * 0.33
            valve2_value = self.valve2_slider.value() * 0.33
            self.serial_conn.write(f"UPDATESETPOINTS,{valve1_value},{valve2_value}\n".encode())

    #--------------Test Definitions----------------

    def test_connection(self):
        """ Tests connection of serial port and receives data for 1 second. """
        self.send_command("TEST_CONNECTION")
        
        while True:
            response = self.read_serial_data()

            if response == "IDLE":
                                self.connection_output.append("Test completed. Returning to idle & saving data.")
                                self.save_data()
                                self.connection_output.append("Data saved to working directory.")
                                break

            else:
                self.connection_output.append(response)

            # Allow UI to update to prevent freezing
            QApplication.processEvents()
    
    def pid_tune_test_connection(self):
        """ Tests connection of serial port and receives data for 1 second. """
        self.send_command("PID_TUNE_TEST")

        while True:
            response = self.read_serial_data()

            if response == "IDLE":
                    self.connection_output.append("IDLE")
                    self.save_data()
                    self.connection_output.append("Data saved to working directory.")
                    break
            
            elif response == "PID_DONE":
                 self.connection_output.append("Test completed.")

            else:
                self.control_output.append(response)

                self.datapointcount.append(float(response[0]))
                self.A0.append(float(response[1]))
                self.A1.append(float(response[2]))
                self.A2.append(float(response[3]))
                self.A3.append(float(response[4]))
                self.A4.append(float(response[5]))
                self.A5.append(float(response[6]))
                self.v1_setpoint.append(float(response[7]))
                self.v2_setpoint.append(float(response[8]))
                self.v1_output.append(float(response[9]))
                self.v2_output.append(float(response[10]))
                self.time.append(float(response[11]))

                self.delta_A0A1.append(float(response[1]) - float(response[2]))  # A0 - A1
                self.delta_A2A3.append(float(response[3]) - float(response[4]))  # A2 - A3

                self.connection_output.append("Testing...")

                # Append the response to graphs
                # Plot for Valve 1: A1, v1_setpoint, v1_output vs. Time
                self.graph_V1_PID.plot(self.time, self.A1, pen=pg.mkPen(color="#ffffff"), name="A1")
                self.graph_V1_PID.plot(self.time, self.v1_setpoint, pen=pg.mkPen(color="#bfbfbf"), name="V1 Setpoint")
                self.graph_V1_PID.plot(self.time, self.v1_output, pen=pg.mkPen(color="#6d6d6d"), name="V1 Output")

                # Plot for Valve 2: A3, v2_setpoint, v2_output vs. Time
                self.graph_V2_PID.plot(self.time, self.A3, pen=pg.mkPen(color="#ffffff"), name="A3")
                self.graph_V2_PID.plot(self.time, self.v2_setpoint, pen=pg.mkPen(color="#bfbfbf"), name="V2 Setpoint")
                self.graph_V2_PID.plot(self.time, self.v2_output, pen=pg.mkPen(color="#6d6d6d"), name="V2 Output")

                # Plot for delta values for health checks: A0-A1, Max_delta vs Time
                self.graph_delta_A0A1.plot(self.time, self.delta_A0A1, pen=pg.mkPen(color="#ffffff"), name="Delta A0/A1")
                self.graph_delta_A0A1.plot(self.time, [self.v1_max_delta[0]] * len(self.time), pen=pg.mkPen(color="#bfbfbf"), name="MAX Delta A0/A1")
                
                # Plot for delta values for health checks: A2-A3, Max_delta vs Time
                self.graph_delta_A2A3.plot(self.time, self.delta_A2A3, pen=pg.mkPen(color="#ffffff"), name="Delta A2/A3")
                self.graph_delta_A2A3.plot(self.time, [self.v2_max_delta[0]] * len(self.time), pen=pg.mkPen(color="#bfbfbf"), name="Delta A0/A1")

            # Allow UI to update to prevent freezing
            QApplication.processEvents()

    def ignition(self):
        """Begins ignition of thruster and runs through thrusting sequence."""
        self.send_command("IGNITION")

        while True:
            response = self.read_serial_data()

            if response == "IDLE":
                    self.control_output.append("Test completed. Returning to idle & saving data.")
                    self.save_data()
                    self.control_output.append("Data saved to working directory.")
                    break
            
            elif response == "IGNITION":
                    self.control_output.append("Ignition state commenced.")

            elif response == "THRUSTING":
                    self.control_output.append("Thrusting state commenced.")

            elif response == "COOLING":
                    self.control_output.append("Cooling state commenced")

            else:
                self.datapointcount.append(float(response[0]))
                self.A0.append(float(response[1]))
                self.A1.append(float(response[2]))
                self.A2.append(float(response[3]))
                self.A3.append(float(response[4]))
                self.A4.append(float(response[5]))
                self.A5.append(float(response[6]))
                self.v1_setpoint.append(float(response[7]))
                self.v2_setpoint.append(float(response[8]))
                self.v1_output.append(float(response[9]))
                self.v2_output.append(float(response[10]))
                self.time.append(float(response[11]))

                
                self.delta_A0A1.append(float(response[1]) - float(response[2]))  # A0 - A1
                self.delta_A2A3.append(float(response[3]) - float(response[4]))  # A2 - A3

                # Valve deltaP limits safety check
                if self.delta_A0A1[-1] > self.v1_max_delta or self.delta_A2A3[-1] > self.v2_max_delta:
                    self.send_command("IDLE")

                self.control_output.append("Testing...")

                # Append the response to graphs
                # A0/A1
                self.graph_A0A1.plot(self.time, self.A0, pen=pg.mkPen(color="#ffffff"), name="A0")
                self.graph_A0A1.plot(self.time, self.A1, pen=pg.mkPen(color="#bfbfbf"), name="A1")
                self.graph_A0A1.plot(self.time, self.v1_setpoint, pen=pg.mkPen(color="#6d6d6d"), name="V1 Setpoint")

                # Plot for Valve 1: PWM vs. Time
                self.graph_PWM1.plot(self.time, self.v1_output, pen="g", name="V1 PWM Response")

                # A2/A3
                self.graph_A2A3.plot(self.time, self.A2, pen=pg.mkPen(color="#ffffff"), name="A0")
                self.graph_A2A3.plot(self.time, self.A3, pen=pg.mkPen(color="#bfbfbf"), name="A1")
                self.graph_A2A3.plot(self.time, self.v2_setpoint, pen=pg.mkPen(color="#6d6d6d"), name="V2 Setpoint")

                # Plot for Valve 2: PWM vs. Time
                self.graph_PWM2.plot(self.time, self.v2_output, pen=pg.mkPen(color="#ffffff"), name="V2 PWM Response")

                # Plot for delta values for health checks: A0-A1, Max_delta vs Time
                self.graph_delta_A0A1.plot(self.time, self.delta_A0A1, pen=pg.mkPen(color="#ffffff"), name="Delta A0/A1")
                self.graph_delta_A0A1.plot(self.time, [self.v1_max_delta[0]] * len(self.time), pen=pg.mkPen(color="#bfbfbf"), name="MAX Delta A0/A1")
                
                # Plot for delta values for health checks: A2-A3, Max_delta vs Time
                self.graph_delta_A2A3.plot(self.time, self.delta_A2A3, pen=pg.mkPen(color="#ffffff"), name="Delta A2/A3")
                self.graph_delta_A2A3.plot(self.time, [self.v2_max_delta[0]] * len(self.time), pen=pg.mkPen(color="#bfbfbf"), name="Delta A0/A1")

            # Allow UI to update to prevent freezing
            QApplication.processEvents()

    def shutdown(self):
        self.send_command("IDLE")
        self.control_output.append("Forced System Shutdown...")
        response = self.read_serial_data()
        self.control_output.append(response)
        self.save_data()
        self.control_output.append("Data saved to working directory.")

    def closeEvent(self, event):
        self.running = False
        if self.serial_conn:
            self.serial_conn.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = PressureControlGUI()
    gui.show()
    sys.exit(app.exec_())
