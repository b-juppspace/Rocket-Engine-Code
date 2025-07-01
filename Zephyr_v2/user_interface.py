import sys
import serial
import threading
import pyqtgraph as pg
import time
import csv
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QSlider, QHBoxLayout, QTabWidget, QTextEdit, QLineEdit
from PyQt5.QtGui import QPalette, QColor, QFont, QPixmap, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
from datetime import datetime
import numpy as np
from scipy.optimize import curve_fit

class SerialThread(QThread):
    data_received = pyqtSignal(list)  # Signal to emit received data
    status_update = pyqtSignal(str)   # Signal for status messages

    def __init__(self, serial_conn):
        super().__init__()
        self.serial_conn = serial_conn
        self.running = False

    def run(self):
        self.running = True
        while self.running and self.serial_conn and self.serial_conn.is_open:
            try:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode().strip()
                    if line:
                        data = line.split(",")
                        self.data_received.emit(data)
            except Exception as e:
                self.status_update.emit(f"Serial error: {e}")
            time.sleep(0.01)  # Small delay to prevent CPU hogging

    def stop(self):
        self.running = False
        self.wait()

class PressureControlGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.serial_conn = None
        self.serial_thread = None
        self.running = False
        self.Q_REF = 90.0
        self.DP_REF = 500.0
        self.R_GAS = 259.8
        self.TEMP = 298.0
        self.initUI()
        self.variables()  
    
    def initUI(self):
        self.setWindowTitle("Command Centre")
        self.setFixedSize(1400, 900)

        # GUI Formatting
        font = QFont("Consolas", 10)
        small_font = QFont("Consolas", 8)
        header_font = QFont("Consolas", 12, QFont.Bold)
        title_font = QFont("Consolas", 16, QFont.Bold)
        self.setFont(font)
        graph_label = "<span style='font-size:10pt; font-weight:bold; color:white; font-family:Consolas;'>{}</span>"
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
        
        # Setup main layout -----------------------------------------------------
        main_layout = QHBoxLayout()
        image_path = os.path.join(os.getcwd(), "logosmall")

        # Label Setup and Formatting --------------------------------------------
        self.logo_label = QLabel()
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print("Error: Could not load logo.png")
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)

        self.menu_title_label = QLabel("Juppspace Test GUI")
        self.menu_title_label.setFont(QFont(title_font))
        self.menu_title_label.setAlignment(Qt.AlignCenter)
        self.menu_title_label.setStyleSheet("color: white;")

        self.menu_text_label = QLabel("Script for rocket engine test purposes.")
        self.menu_text_label.setFont(QFont(font))
        self.menu_text_label.setAlignment(Qt.AlignCenter)
        self.menu_text_label.setStyleSheet("color: white;")

        self.connection_title_label = QLabel("Terminal")
        self.connection_title_label.setFont(QFont(header_font))
        self.connection_title_label.setStyleSheet("color: white;")

        self.tune_label = QLabel("Tune PID K-Values")
        self.tune_label.setFont(header_font)
        self.tune_label.setStyleSheet("color: #ffffff;")

        self.kp_label = QLabel("kp: 1.00")
        self.kp_label.setFont(font)
        self.kp_label.setStyleSheet("color: #ffffff;")

        self.ki_label = QLabel("ki: 5.00")
        self.ki_label.setFont(QFont(font))
        self.ki_label.setStyleSheet("color: #ffffff;")

        self.kd_label = QLabel("kd: 2.00")
        self.kd_label.setFont(QFont(font))
        self.kd_label.setStyleSheet("color: #ffffff;")

        self.kp2_label = QLabel("kp: 1.00")
        self.kp2_label.setFont(font)
        self.kp2_label.setStyleSheet("color: #ffffff;")

        self.ki2_label = QLabel("ki: 5.00")
        self.ki2_label.setFont(QFont(font))
        self.ki2_label.setStyleSheet("color: #ffffff;")

        self.kd2_label = QLabel("kd: 2.00")
        self.kd2_label.setFont(QFont(font))
        self.kd2_label.setStyleSheet("color: #ffffff;")

        self.note_label = QLabel("Note: Open valves to complete PID tuning tests. Valve will open to provide pressure of 45psi for ox and 2 psi for fuel, edit K values for tuning of response.")
        self.note_label.setWordWrap(True)
        self.note_label.setStyleSheet("background-color: #000000; color: #ffffff;")
        self.note_label.setFont(small_font)

        self.oxtest_title_label = QLabel("Terminal")
        self.oxtest_title_label.setFont(QFont(header_font))
        self.oxtest_title_label.setStyleSheet("color: white;")

        self.control_title_label2 = QLabel("Terminal")
        self.control_title_label2.setFont(QFont(header_font))
        self.control_title_label2.setStyleSheet("color: white;")
        
        self.valve1_label = QLabel("Valve 1: 2.31 kPa")
        self.valve1_label.setFont(QFont("Consolas", 10))
        self.valve1_label.setStyleSheet("color: #ffffff;")

        self.valve2_label = QLabel("Valve 2: 45.21 kPa")
        self.valve2_label.setFont(QFont("Consolas", 10))
        self.valve2_label.setStyleSheet("color: #ffffff;")

        # Slider Setup and Formatting -------------------------------------------
        self.kp_slider = QSlider(Qt.Horizontal)
        self.kp_slider.setRange(0, 80)
        self.kp_slider.setValue(10)
        self.kp_slider.valueChanged.connect(self.update_kp)
        self.kp_slider.setStyleSheet("QSlider::handle:horizontal {background: #ffffff;}")

        self.ki_slider = QSlider(Qt.Horizontal)
        self.ki_slider.setRange(0, 80)
        self.ki_slider.setValue(50)
        self.ki_slider.valueChanged.connect(self.update_ki)
        self.ki_slider.setStyleSheet("QSlider::handle:horizontal {background: #ffffff;}")

        self.kd_slider = QSlider(Qt.Horizontal)
        self.kd_slider.setRange(0, 80)
        self.kd_slider.setValue(20)
        self.kd_slider.valueChanged.connect(self.update_kd)
        self.kd_slider.setStyleSheet("QSlider::handle:horizontal {background: #ffffff;}")

        self.kp2_slider = QSlider(Qt.Horizontal)
        self.kp2_slider.setRange(0, 80)
        self.kp2_slider.setValue(10)
        self.kp2_slider.valueChanged.connect(self.update_kp2)
        self.kp2_slider.setStyleSheet("QSlider::handle:horizontal {background: #ffffff;}")

        self.ki2_slider = QSlider(Qt.Horizontal)
        self.ki2_slider.setRange(0, 80)
        self.ki2_slider.setValue(50)
        self.ki2_slider.valueChanged.connect(self.update_ki2)
        self.ki2_slider.setStyleSheet("QSlider::handle:horizontal {background: #ffffff;}")

        self.kd2_slider = QSlider(Qt.Horizontal)
        self.kd2_slider.setRange(0, 80)
        self.kd2_slider.setValue(20)
        self.kd2_slider.valueChanged.connect(self.update_kd2)
        self.kd2_slider.setStyleSheet("QSlider::handle:horizontal {background: #ffffff;}")

        self.valve1_slider = QSlider(Qt.Horizontal)
        self.valve1_slider.setRange(0, 30)
        self.valve1_slider.setValue(7)
        self.valve1_slider.valueChanged.connect(self.update_fuel_PV)
        self.valve1_slider.setStyleSheet("QSlider::handle:horizontal {background: #ffffff;}")

        self.valve2_slider = QSlider(Qt.Horizontal)
        self.valve2_slider.setRange(0, 240)
        self.valve2_slider.setValue(137)
        self.valve2_slider.valueChanged.connect(self.update_ox_PV)
        self.valve2_slider.setStyleSheet("QSlider::handle:horizontal {background: #ffffff;}")

        # Button Setup and Formatting -------------------------------------------
        self.init_serial_button = QPushButton("Initialize Serial Port")
        self.init_serial_button.clicked.connect(self.init_serial)
        self.init_serial_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        self.init_serial_button.setFont(font)

        self.test_connection_button = QPushButton("Test Connection")
        self.test_connection_button.clicked.connect(self.test_connection)
        self.test_connection_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        self.test_connection_button.setFont(font)

        self.send_k_button = QPushButton("Send K Values")
        self.send_k_button.clicked.connect(self.send_k_values_connection)
        self.send_k_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        self.send_k_button.setFont(font)

        self.pid_tune_test_button = QPushButton("Begin PID Tune Test")
        self.pid_tune_test_button.clicked.connect(self.pid_tune_test_connection)
        self.pid_tune_test_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        self.pid_tune_test_button.setFont(font)

        self.ox_test_button = QPushButton("Begin Ox Test")
        self.ox_test_button.clicked.connect(self.pid_tune_test_connection)
        self.ox_test_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        self.ox_test_button.setFont(font)

        self.initialise_ox_test_button = QPushButton("Initialise Ox Test")
        self.initialise_ox_test_button.clicked.connect(self.oxtest)
        self.initialise_ox_test_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        self.initialise_ox_test_button.setFont(font)

        self.end_ox_test_button = QPushButton("Finish Ox Test")
        self.end_ox_test_button.clicked.connect(self.end_oxtest)
        self.end_ox_test_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        self.end_ox_test_button.setFont(font)

        self.ignition_button = QPushButton("Ignition")
        self.ignition_button.clicked.connect(self.ignition)
        self.ignition_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        self.ignition_button.setFont(font)

        self.shutdown_button = QPushButton("Forced Shutdown")
        self.shutdown_button.clicked.connect(self.shutdown)
        self.shutdown_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        self.shutdown_button.setFont(font)

        # Terminal -------------------------------------
        self.connection_output = QTextEdit()
        self.connection_output.setReadOnly(True)
        self.connection_output.setStyleSheet("background-color: #000000; color: #ffffff;")
        self.connection_output.setFont(font)

        self.oxtest_output = QTextEdit()
        self.oxtest_output.setReadOnly(True)
        self.oxtest_output.setStyleSheet("background-color: #000000; color: #ffffff;")
        self.oxtest_output.setFont(font)

        self.control_output = QTextEdit()
        self.control_output.setReadOnly(True)
        self.control_output.setStyleSheet("background-color: #000000; color: #ffffff;")
        self.control_output.setFont(font)

        # Graphs -------------------------------------

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

        self.graph_oxtest_voltage = pg.PlotWidget()
        self.graph_oxtest_voltage.setTitle(graph_label.format("Ox Feed-line Transducer Voltage"))
        self.graph_oxtest_voltage.setLabel('left', graph_label.format("V (volts)"))
        self.graph_oxtest_voltage.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_oxtest_voltage.getAxis('left').setStyle(tickFont=font)
        self.graph_oxtest_voltage.getAxis('bottom').setStyle(tickFont=font)

        self.graph_oxtest_pressure = pg.PlotWidget()
        self.graph_oxtest_pressure.setTitle(graph_label.format("Ox Feed-line Pressure"))
        self.graph_oxtest_pressure.setLabel('left', graph_label.format("P (kPa)"))
        self.graph_oxtest_pressure.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_oxtest_pressure.getAxis('left').setStyle(tickFont=font)
        self.graph_oxtest_pressure.getAxis('bottom').setStyle(tickFont=font)

        self.graph_oxtest_deltaP = pg.PlotWidget()
        self.graph_oxtest_deltaP.setTitle(graph_label.format("Ox Feed-line Delta Pressure"))
        self.graph_oxtest_deltaP.setLabel('left', graph_label.format("P (psi)"))
        self.graph_oxtest_deltaP.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_oxtest_deltaP.getAxis('left').setStyle(tickFont=font)
        self.graph_oxtest_deltaP.getAxis('bottom').setStyle(tickFont=font)

        self.graph_oxtest_sv = pg.PlotWidget()
        self.graph_oxtest_sv.setTitle(graph_label.format("Solenoid Valve (OFF=0 ON=1)"))
        self.graph_oxtest_sv.setLabel('left', graph_label.format("SV"))
        self.graph_oxtest_sv.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_oxtest_sv.getAxis('left').setStyle(tickFont=font)
        self.graph_oxtest_sv.getAxis('bottom').setStyle(tickFont=font) 

        self.graph_oxtest_PWM = pg.PlotWidget()
        self.graph_oxtest_PWM.setTitle(graph_label.format("Proportional Valve PWM Response"))
        self.graph_oxtest_PWM.setLabel('left', graph_label.format("PWM(0-255)"))
        self.graph_oxtest_PWM.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_oxtest_PWM.getAxis('left').setStyle(tickFont=font)
        self.graph_oxtest_PWM.getAxis('bottom').setStyle(tickFont=font) 

        self.graph_oxtest_mdot_air = pg.PlotWidget()
        self.graph_oxtest_mdot_air.setTitle(graph_label.format("Mass Flow Rate of Air"))
        self.graph_oxtest_mdot_air.setLabel('left', graph_label.format("mdot (g/s)"))
        self.graph_oxtest_mdot_air.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_oxtest_mdot_air.getAxis('left').setStyle(tickFont=font)
        self.graph_oxtest_mdot_air.getAxis('bottom').setStyle(tickFont=font) 

        self.graph_oxtest_mtotal_air = pg.PlotWidget()
        self.graph_oxtest_mtotal_air.setTitle(graph_label.format("Total Mass Flowed of Air"))
        self.graph_oxtest_mtotal_air.setLabel('left', graph_label.format("m (g)"))
        self.graph_oxtest_mtotal_air.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_oxtest_mtotal_air.getAxis('left').setStyle(tickFont=font)
        self.graph_oxtest_mtotal_air.getAxis('bottom').setStyle(tickFont=font) 

        self.graph_A0A1 = pg.PlotWidget()
        self.graph_A0A1.setTitle(graph_label.format("A0/A1"))
        self.graph_A0A1.setLabel('left', graph_label.format("P (psi)"))
        self.graph_A0A1.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_A0A1.getAxis('left').setStyle(tickFont=font)
        self.graph_A0A1.getAxis('bottom').setStyle(tickFont=font)

        self.graph_PWM1 = pg.PlotWidget()
        self.graph_PWM1.setTitle(graph_label.format("PWM1"))
        self.graph_PWM1.setLabel('left', graph_label.format("PWM(0-255)"))
        self.graph_PWM1.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_PWM1.getAxis('left').setStyle(tickFont=font)
        self.graph_PWM1.getAxis('bottom').setStyle(tickFont=font)

        self.graph_A2A3 = pg.PlotWidget()
        self.graph_A2A3.setTitle(graph_label.format("A2/A3"))
        self.graph_A2A3.setLabel('left', graph_label.format("P (psi)"))
        self.graph_A2A3.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_A2A3.getAxis('left').setStyle(tickFont=font)
        self.graph_A2A3.getAxis('bottom').setStyle(tickFont=font)

        self.graph_PWM2 = pg.PlotWidget()
        self.graph_PWM2.setTitle(graph_label.format("PWM2"))
        self.graph_PWM2.setLabel('left', graph_label.format("PWM(0-255)"))
        self.graph_PWM2.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_PWM2.getAxis('left').setStyle(tickFont=font)
        self.graph_PWM2.getAxis('bottom').setStyle(tickFont=font)

        self.graph_A4A5 = pg.PlotWidget()
        self.graph_A4A5.setTitle(graph_label.format("A4/A5"))
        self.graph_A4A5.setLabel('left', graph_label.format("P (psi)"))
        self.graph_A4A5.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_A4A5.getAxis('left').setStyle(tickFont=font)
        self.graph_A4A5.getAxis('bottom').setStyle(tickFont=font)

        self.graph_dP_fuel = pg.PlotWidget()
        self.graph_dP_fuel.setTitle(graph_label.format("delta A0/A1"))
        self.graph_dP_fuel.setLabel('left', graph_label.format("P (psi)"))
        self.graph_dP_fuel.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_dP_fuel.getAxis('left').setStyle(tickFont=font)
        self.graph_dP_fuel.getAxis('bottom').setStyle(tickFont=font)

        self.graph_dP_ox = pg.PlotWidget()
        self.graph_dP_ox.setTitle(graph_label.format("delta A2/A3"))
        self.graph_dP_ox.setLabel('left', graph_label.format("P (psi)"))
        self.graph_dP_ox.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_dP_ox.getAxis('left').setStyle(tickFont=font)
        self.graph_dP_ox.getAxis('bottom').setStyle(tickFont=font)

        # Layout Setup and Widget Placement -------------------------------------
        self.menu_tab = QWidget()
        menu_layout = QVBoxLayout()
        self.menu_tab.setFont(font)
        self.menu_tab.setLayout(menu_layout)
        self.tabs.addTab(self.menu_tab, "Menu")
        menu_layout.addWidget(self.logo_label)
        menu_layout.addWidget(self.menu_title_label)
        menu_layout.addWidget(self.menu_text_label)

        self.connection_tab = QWidget()
        connection_layout = QVBoxLayout()
        self.connection_tab.setFont(font)
        self.connection_tab.setLayout(connection_layout)
        self.tabs.addTab(self.connection_tab, "Settings")
        connection_layout.addWidget(self.connection_title_label)
        connection_layout.addWidget(self.connection_output)
        connection_layout.addWidget(self.init_serial_button)
        connection_layout.addWidget(self.test_connection_button)
        connection_layout.addWidget(self.tune_label)

        slider_layout = QHBoxLayout()
        slider_v1_section = QVBoxLayout()
        slider_v1_section.addWidget(self.kp_label)
        slider_v1_section.addWidget(self.kp_slider)
        slider_v1_section.addWidget(self.ki_label)
        slider_v1_section.addWidget(self.ki_slider)
        slider_v1_section.addWidget(self.kd_label)
        slider_v1_section.addWidget(self.kd_slider)

        slider_v2_section = QVBoxLayout()
        slider_v2_section.addWidget(self.kp2_label)
        slider_v2_section.addWidget(self.kp2_slider)
        slider_v2_section.addWidget(self.ki2_label)
        slider_v2_section.addWidget(self.ki2_slider)
        slider_v2_section.addWidget(self.kd2_label)
        slider_v2_section.addWidget(self.kd2_slider)

        slider_layout.addLayout(slider_v1_section)
        slider_layout.addLayout(slider_v2_section)
        connection_layout.addLayout(slider_layout)

        connection_layout.addWidget(self.send_k_button)
        connection_layout.addWidget(self.note_label)
        connection_layout.addWidget(self.pid_tune_test_button)

        graph_layout = QHBoxLayout()
        graph_layout.addWidget(self.graph_V1_PID)
        graph_layout.addWidget(self.graph_V2_PID)
        connection_layout.addLayout(graph_layout)

        self.oxtest_tab = QWidget()
        oxtest_layout = QVBoxLayout()
        self.oxtest_tab.setLayout(oxtest_layout)
        self.tabs.addTab(self.oxtest_tab, "Ox Test")
        oxtest_layout.addWidget(self.oxtest_title_label)
        oxtest_layout.addWidget(self.oxtest_output)
        oxtest_button_layout = QHBoxLayout()
        oxtest_button_layout.addWidget(self.initialise_ox_test_button)
        oxtest_button_layout.addWidget(self.end_ox_test_button)
        oxtest_layout.addLayout(oxtest_button_layout)
        oxtest_pressure_graph_layout = QHBoxLayout()
        oxtest_pressure_graph_layout.addWidget(self.graph_oxtest_voltage)
        oxtest_pressure_graph_layout.addWidget(self.graph_oxtest_pressure)
        oxtest_pressure_graph_layout.addWidget(self.graph_oxtest_deltaP)
        oxtest_layout.addLayout(oxtest_pressure_graph_layout)
        oxtest_valve_graph_layout = QHBoxLayout()
        oxtest_valve_graph_layout.addWidget(self.graph_oxtest_PWM)
        oxtest_valve_graph_layout.addWidget(self.graph_oxtest_sv)
        oxtest_layout.addLayout(oxtest_valve_graph_layout)
        oxtest_mass_graph_layout = QHBoxLayout()
        oxtest_mass_graph_layout.addWidget(self.graph_oxtest_mdot_air)
        oxtest_mass_graph_layout.addWidget(self.graph_oxtest_mtotal_air)
        oxtest_layout.addLayout(oxtest_mass_graph_layout)
        

        self.control_tab = QWidget()
        control_layout = QVBoxLayout()
        self.control_tab.setLayout(control_layout)
        self.tabs.addTab(self.control_tab, "Play")
        control_layout.addWidget(self.control_title_label2)
        control_layout.addWidget(self.control_output)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ignition_button)
        button_layout.addWidget(self.shutdown_button)
        control_layout.addLayout(button_layout)
        control_layout.addWidget(self.valve1_label)
        control_layout.addWidget(self.valve1_slider)
        control_layout.addWidget(self.valve2_label)
        control_layout.addWidget(self.valve2_slider)
        

        graph_layout2 = QHBoxLayout()
        graph_column1 = QVBoxLayout()
        graph_column1.addWidget(self.graph_A0A1)
        graph_column1.addWidget(self.graph_PWM1)
        graph_column2 = QVBoxLayout()
        graph_column2.addWidget(self.graph_A2A3)
        graph_column2.addWidget(self.graph_PWM2)
        graph_layout2.addLayout(graph_column1)
        graph_layout2.addLayout(graph_column2)
        graph_layout2.addWidget(self.graph_A4A5)
        control_layout.addLayout(graph_layout2)

        self.health_tab = QWidget()
        health_layout = QVBoxLayout()
        self.health_tab.setLayout(health_layout)
        self.tabs.addTab(self.health_tab, "Health")
        graph_layout3 = QHBoxLayout()
        graph_layout3.addWidget(self.graph_dP_fuel)
        graph_layout3.addWidget(self.graph_dP_ox)
        health_layout.addLayout(graph_layout3)


        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
    
    #--------------Stored Data Variables--------------
    def variables(self):   
        self.dataPointCount = []
        self.V0 = []
        self.V1 = []
        self.V2 = []
        self.V3 = []
        self.V4 = []
        self.V5 = []
        self.A0 = []
        self.A1 = []
        self.A2 = []
        self.A3 = []
        self.A4 = []
        self.A5 = []
        self.dP_fuel = []
        self.dP_ox = []
        self.sv_fuel_output = []
        self.sv_ox_output = []
        self.pv_fuel_setpoint = []
        self.pv_ox_setpoint = []
        self.pv_fuel_output = []
        self.pv_ox_output = []
        self.time = []
        self.pvMaxOpP = 1000
        self.fuel_max_delta = 120                                
        self.ox_max_delta = 700                
        self.mdot_air = []
        self.mtotal_air = []             
    #--------------General Definitions----------------

    def init_serial(self):
        try:
            self.serial_conn = serial.Serial("COM4", 115200, timeout=1)
            self.running = True
            self.serial_thread = SerialThread(self.serial_conn)
            self.serial_thread.data_received.connect(self.handle_serial_data)
            self.serial_thread.status_update.connect(self.connection_output.append)
            self.serial_thread.start()
            self.connection_output.append("Serial port initialized.")
        except serial.SerialException as e:
            self.connection_output.append(f"Error: {e}")

    def send_command(self, command):
        """Sends a command through the serial port."""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write((command + "\n").encode())
            except serial.SerialException as e:
                self.connection_output.append(f"Error sending command '{command}': {e}")
    
    def save_data(self):
        """Saves all data to a CSV file with a timestamp."""
        try:
            current_dir = os.getcwd()
            timestamp = datetime.now().strftime("%m-%d_%H-%M")
            file_name = os.path.join(current_dir, f"DATA_{timestamp}.csv")

            with open(file_name, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Data Point Count", "V0", "V1", "V2", "V3", "V4", "V5",
                    "A0", "A1", "A2", "A3", "A4", "A5",
                    "dP Fuel", "dP Ox",
                    "SV Fuel Output", "SV Ox Output",
                    "PV Fuel Setpoint", "PV Ox Setpoint",
                    "PV Fuel Output", "PV Ox Output",
                    "Time",
                    "Air Mass Flow Rate (g/s)", "Air Total Mass Flowed (g)"
                ])
                for i in range(len(self.time)):
                    writer.writerow([
                        self.dataPointCount[i] if i < len(self.dataPointCount) else "",
                        self.V0[i] if i < len(self.V0) else "",
                        self.V1[i] if i < len(self.V1) else "",
                        self.V2[i] if i < len(self.V2) else "",
                        self.V3[i] if i < len(self.V3) else "",
                        self.V4[i] if i < len(self.V4) else "",
                        self.V5[i] if i < len(self.V5) else "",
                        self.A0[i] if i < len(self.A0) else "",
                        self.A1[i] if i < len(self.A1) else "",
                        self.A2[i] if i < len(self.A2) else "",
                        self.A3[i] if i < len(self.A3) else "",
                        self.A4[i] if i < len(self.A4) else "",
                        self.A5[i] if i < len(self.A5) else "",
                        self.dP_fuel[i] if i < len(self.dP_fuel) else "",
                        self.dP_ox[i] if i < len(self.dP_ox) else "",
                        self.sv_fuel_output[i] if i < len(self.sv_fuel_output) else "",
                        self.sv_ox_output[i] if i < len(self.sv_ox_output) else "",
                        self.pv_fuel_setpoint[i] if i < len(self.pv_fuel_setpoint) else "",
                        self.pv_ox_setpoint[i] if i < len(self.pv_ox_setpoint) else "",
                        self.pv_fuel_output[i] if i < len(self.pv_fuel_output) else "",
                        self.pv_ox_output[i] if i < len(self.pv_ox_output) else "",
                        self.time[i],
                        self.mdot_air[i] if i < len(self.mdot_air) else "",
                        self.mtotal_air[i] if i < len(self.mtotal_air) else ""
                    ])
            self.connection_output.append(f"Data saved to {file_name}")
        except Exception as e:
            self.connection_output.append(f"Error saving data: {e}")

    #-------------DATA PROCESSING---------------------
    def calculate_mass_flow_rate_air(self, dp_ox, A2, A3):
        q = self.Q_REF * np.sqrt(dp_ox / self.DP_REF)
        avg_pressure = (A2 + A3) / 2 * 1000.0
        density = avg_pressure / (self.R_GAS * self.TEMP)
        q_m3_per_s = (q / 60.0) * 1e-3
        mass_flow_rate = density * q_m3_per_s * 1000.0
        return mass_flow_rate

    def calculate_time_constant_air(self):
        def exp_decay(t, p_final, p_delta, tau):
            return p_final + p_delta * np.exp(-t / tau)
        
        try:
            # Convert times to seconds and make relative to start
            t = np.array([time_val / 1000.0 for time_val in self.time])
            t = t - t[0]  # Make time relative to start
            p = np.array(self.A3)

            # Initial guesses: p_final = last value, p_delta = initial - final, tau = 20
            p0 = [p[-1], p[0] - p[-1], 20.0]
            popt, _ = curve_fit(exp_decay, t, p, p0=p0, maxfev=10000)
            time_constant = popt[2]  # τ in seconds

            # Update GUI
            self.time_constant_label.setText(f"Time Constant (τ): {time_constant:.2f} s")
            return time_constant

        except Exception as e:
            self.oxtest_output.append(f"Error calculating time constant: {e}")
            self.time_constant_label.setText("Time Constant (τ): N/A")
            return None

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
            response = self.handle_serial_data()
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

        response = self.handle_serial_data()
        self.connection_output.append(response)
    
    #--------------Setpoint-Slider Definitions-----------

    def update_fuel_PV(self):
        value = self.valve1_slider.value()
        self.valve1_label.setText(f"Valve 1: {value:.2f}")
        self.send_setpoints()
    
    def update_ox_PV(self):
        value = self.oxtest_valve_slider.value()
        self.oxtest_slider_label.setText(f"ox Valve: {value:.2f} kPa")
        self.oxtest_output.append(f"Slider moved to: {value} kPa")
        self.send_oxtest_setpoint()
    
    def send_setpoints(self):
        if self.serial_conn and self.serial_conn.is_open:
            valve1_value = self.valve1_slider.value() 
            valve2_value = self.valve2_slider.value() 
            self.serial_conn.write(f"UPDATESETPOINTS,{valve1_value},{valve2_value}\n".encode())

    #--------------Test Definitions----------------

    def handle_serial_data(self, data):
        """Default handler for serial data when no test is active."""
        if data:  # Check for valid data
            response_str = ",".join(data)
            self.connection_output.append(f"Received: {response_str}")
            
            # Highlight critical states for safety
            if "IDLE" in response_str:
                self.connection_output.append("System is in IDLE state.")
            elif "MAXdP_EXCEEDED" in response_str:
                self.connection_output.append("Warning: Maximum pressure differential exceeded.")
            elif "MAXP_EXCEEDED" in response_str:
                self.connection_output.append("Warning: Maximum pressure exceeded.")

    def test_connection(self):
        self.send_command("TEST_CONNECTION")
        self.connection_output.append("Starting TEST_CONNECTION...")
        self.serial_thread.data_received.disconnect()  # Clear previous handler
        self.serial_thread.data_received.connect(self.handle_test_connection_data)

    def handle_test_connection_data(self, response):
        try:
            response_str = ",".join(response)
            if "IDLE" in response_str:
                self.connection_output.append("Test completed. Returning to idle.")
                self.serial_thread.data_received.disconnect(self.handle_test_connection_data)
                self.serial_thread.data_received.connect(self.handle_serial_data)
            else:
                self.connection_output.append(response_str)
        except Exception as e:
            self.connection_output.append(f"Error in test_connection: {e}")
    
    def pid_tune_test_connection(self):
        """ Tests connection of serial port and receives data for 1 second. """
        self.send_command("PID_TUNE_TEST")

        while True:
            response = self.handle_serial_data()

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
                self.pv_fuel_setpoint.append(float(response[7]))
                self.pv_ox_setpoint.append(float(response[8]))
                self.pv_fuel_output.append(float(response[9]))
                self.pv_ox_output.append(float(response[10]))
                self.time.append(float(response[11]))

                self.dP_fuel.append(float(response[1]) - float(response[2]))  # A0 - A1
                self.dP_ox.append(float(response[3]) - float(response[4]))  # A2 - A3

                self.connection_output.append("Testing...")

                # Append the response to graphs
                # Plot for Valve 1: A1, pv_fuel_setpoint, pv_fuel_output vs. Time
                self.graph_V1_PID.plot(self.time, self.A1, pen=pg.mkPen(color="#ffffff"), name="A1")
                self.graph_V1_PID.plot(self.time, self.pv_fuel_setpoint, pen=pg.mkPen(color="#bfbfbf"), name="V1 Setpoint")
                self.graph_V1_PID.plot(self.time, self.pv_fuel_output, pen=pg.mkPen(color="#6d6d6d"), name="V1 Output")

                # Plot for Valve 2: A3, pv_ox_setpoint, pv_ox_output vs. Time
                self.graph_V2_PID.plot(self.time, self.A3, pen=pg.mkPen(color="#ffffff"), name="A3")
                self.graph_V2_PID.plot(self.time, self.pv_ox_setpoint, pen=pg.mkPen(color="#bfbfbf"), name="V2 Setpoint")
                self.graph_V2_PID.plot(self.time, self.pv_ox_output, pen=pg.mkPen(color="#6d6d6d"), name="V2 Output")

                # Plot for delta values for health checks: A0-A1, Max_delta vs Time
                self.graph_dP_fuel.plot(self.time, self.dP_fuel, pen=pg.mkPen(color="#ffffff"), name="Delta A0/A1")
                self.graph_dP_fuel.plot(self.time, [self.v1_max_delta[0]] * len(self.time), pen=pg.mkPen(color="#bfbfbf"), name="MAX Delta A0/A1")
                
                # Plot for delta values for health checks: A2-A3, Max_delta vs Time
                self.graph_dP_ox.plot(self.time, self.dP_ox, pen=pg.mkPen(color="#ffffff"), name="Delta A2/A3")
                self.graph_dP_ox.plot(self.time, [self.v2_max_delta[0]] * len(self.time), pen=pg.mkPen(color="#bfbfbf"), name="Delta A0/A1")

            # Allow UI to update to prevent freezing
            QApplication.processEvents()

    def oxtest(self):
        # Clear data lists
        self.dataPointCount.clear()
        self.time.clear()
        self.V2.clear()
        self.V3.clear()
        self.A2.clear()
        self.A3.clear()
        self.dP_ox.clear()
        self.sv_ox_output.clear()
        self.pv_ox_output.clear()
        self.pv_ox_setpoint.clear()
        self.mdot_air.clear()
        self.mtotal_air.clear()

        self.variables()  # Initialize plotting lists
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.flushInput()
            # Send a test command to ensure Arduino is ready
            self.serial_conn.write("TEST_CONNECTION\n".encode())
            self.oxtest_output.append("Sent: TEST_CONNECTION")
            # Wait for Arduino to respond
            start_time = time.time()
            while time.time() - start_time < 1.0:
                if self.serial_conn.in_waiting:
                    response = self.serial_conn.readline().decode().strip()
                    if response == "TEST_CONNECTION started":
                        self.oxtest_output.append("Arduino ready")
                        break
            # Start the test
            self.send_command("OX_TEST")
            self.oxtest_output.append("Starting OX_TEST...")
            time.sleep(1.0)  # Wait for Arduino to enter OXTEST
        self.ignore_idle_until = time.time() + 1.0
        try:
            self.serial_thread.data_received.disconnect()
        except TypeError:
            pass
        self.serial_thread.data_received.connect(self.handle_oxtest_data)

    def handle_oxtest_data(self, response):
        """Handles serial data received during Ox test."""
        try:
            response_str = ",".join(response)
            
            if "IDLE" in response_str:
                self.oxtest_output.append("IDLE")
                self.save_data()
                self.oxtest_output.append("Data saved to working directory.")
                self.serial_thread.data_received.disconnect(self.handle_oxtest_data)
                self.serial_thread.data_received.connect(self.handle_serial_data)
            
            elif "OX_DONE" in response_str:
                self.oxtest_output.append("Test completed.")
                self.serial_thread.data_received.disconnect(self.handle_oxtest_data)
                self.serial_thread.data_received.connect(self.handle_serial_data)
            
            elif "MAXdP_EXCEEDED" in response_str:
                self.oxtest_output.append("Maximum pressure differential exceeded, system shutdown.")
                self.serial_thread.data_received.disconnect(self.handle_oxtest_data)
                self.serial_thread.data_received.connect(self.handle_serial_data)
            
            elif "MAXP_EXCEEDED" in response_str:
                self.oxtest_output.append("Maximum pressure exceeded, system shutdown.")
                self.serial_thread.data_received.disconnect(self.handle_oxtest_data)
                self.serial_thread.data_received.connect(self.handle_serial_data)
            
            elif not response or len(response) < 22 or not response[0]:
                return  # Skip invalid data
            
            else:
                self.oxtest_output.append(response_str)

                # Populate data lists
                self.dataPointCount.append(float(response[0]))
                self.V0.append(float(response[1]))
                self.V1.append(float(response[2]))
                self.V2.append(float(response[3]))
                self.V3.append(float(response[4]))
                self.V4.append(float(response[5]))
                self.V5.append(float(response[6]))
                self.A0.append(float(response[7]))
                self.A1.append(float(response[8]))
                self.A2.append(float(response[9]))
                self.A3.append(float(response[10]))
                self.A4.append(float(response[11]))
                self.A5.append(float(response[12]))
                self.dP_fuel.append(float(response[13]))
                self.dP_ox.append(float(response[14]))
                self.sv_fuel_output.append(float(response[15]))
                self.sv_ox_output.append(float(response[16]))
                self.pv_fuel_setpoint.append(float(response[17]))
                self.pv_ox_setpoint.append(float(response[18]))
                self.pv_fuel_output.append(float(response[19]))
                self.pv_ox_output.append(float(response[20]))
                self.time.append(float(response[21]))

                massFlowRates = self.calculate_mass_flow_rate_air(
                    float(response[14]), # dpOX
                    float(response[9]), # A2
                    float(response[10]) # A3
                )
                self.mdot_air.append(massFlowRates)

                # Calculate total mass flowed (numerical integration using trapezoidal rule)
                if len(self.time) > 1:
                    dt = (self.time[-1] - self.time[-2]) / 1000.0  # Convert ms to s
                    avg_mass_flow = (self.mdot_air[-1] + self.mdot_air[-2]) / 2
                    delta_mass = avg_mass_flow * dt
                    if len(self.mtotal_air) == 0:
                        total_mass = delta_mass
                    else:
                        total_mass = self.mtotal_air[-1] + delta_mass
                else:
                    total_mass = 0.0
                self.mtotal_air.append(total_mass)

                # Calculate time constant for fully open test (PWM = 255)
                #if float(response[20]) == 255 and len(self.time) > 5:  # Need enough points to fit
                #    self.calculate_time_constant_air()

                # Optimize plotting 
                if len(self.time) > 1000:
                    self.time = self.time[-1000:]
                    self.V2 = self.V2[-1000:]
                    self.V3 = self.V3[-1000:]
                    self.A2 = self.A2[-1000:]
                    self.A3 = self.A3[-1000:]
                    self.pv_ox_setpoint = self.pv_ox_setpoint[-1000:]
                    self.dP_ox = self.dP_ox[-1000:]
                    self.pv_ox_output = self.pv_ox_output[-1000:]
                    self.sv_ox_output = self.sv_ox_output[-1000:]
                    self.mdot_air = self.mdot_air[-1000:]
                    self.mtotal_air = self.mtotal_air[-1000:]

                # Plotting with clearing
                self.graph_oxtest_voltage.clear()
                self.graph_oxtest_voltage.plot(self.time, self.V2, pen=pg.mkPen(color="#ffffff"), name="V2")
                self.graph_oxtest_voltage.plot(self.time, self.V3, pen=pg.mkPen(color="#bfbfbf"), name="V3")

                self.graph_oxtest_pressure.clear()
                self.graph_oxtest_pressure.plot(self.time, self.A2, pen=pg.mkPen(color="#ffffff"), name="A2")
                self.graph_oxtest_pressure.plot(self.time, self.A3, pen=pg.mkPen(color="#bfbfbf"), name="A3")
                self.graph_oxtest_pressure.plot(self.time, self.pv_ox_setpoint, pen=pg.mkPen(color="#bfbfbf"), name="Ox Setpoint")
                self.graph_oxtest_pressure.plot(self.time, [self.pvMaxOpP] * len(self.time), pen=pg.mkPen(color="#6d6d6d"), name="Max Op P")

                self.graph_oxtest_deltaP.clear()
                self.graph_oxtest_deltaP.plot(self.time, self.dP_ox, pen=pg.mkPen(color="#ffffff"), name="dPOx")
                self.graph_oxtest_deltaP.plot(self.time, [self.ox_max_delta] * len(self.time), pen=pg.mkPen(color="#bfbfbf"), name="Max dPOx")

                self.graph_oxtest_PWM.clear()
                self.graph_oxtest_PWM.plot(self.time, self.pv_ox_output, pen=pg.mkPen(color="#ffffff"), name="Ox PWM")

                self.graph_oxtest_sv.clear()
                self.graph_oxtest_sv.plot(self.time, self.sv_ox_output, pen=pg.mkPen(color="#ffffff"), name="Ox SV")

                self.graph_oxtest_mdot_air.clear()
                self.graph_oxtest_mdot_air.plot(self.time, self.mdot_air, pen=pg.mkPen(color="#ffffff"), name="Air mdot (g/s)")

                self.graph_oxtest_mtotal_air.clear()
                self.graph_oxtest_mtotal_air.plot(self.time, self.mtotal_air, pen=pg.mkPen(color="#ffffff"), name="Air mdot (g/s)")
        except Exception as e:
            self.oxtest_output.append(f"Error in oxtest: {e}")


    def ignition(self):
        """Begins ignition of thruster and runs through thrusting sequence."""
        self.send_command("IGNITION")

        while True:
            response = self.handle_serial_data()

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
                self.pv_fuel_setpoint.append(float(response[7]))
                self.pv_ox_setpoint.append(float(response[8]))
                self.pv_fuel_output.append(float(response[9]))
                self.pv_ox_output.append(float(response[10]))
                self.time.append(float(response[11]))

                
                self.dP_fuel.append(float(response[1]) - float(response[2]))  # A0 - A1
                self.dP_ox.append(float(response[3]) - float(response[4]))  # A2 - A3

                # Valve deltaP limits safety check
                if self.dP_fuel[-1] > self.v1_max_delta or self.dP_ox[-1] > self.v2_max_delta:
                    self.send_command("IDLE")

                self.control_output.append("Testing...")

                # Append the response to graphs
                # A0/A1
                self.graph_A0A1.plot(self.time, self.A0, pen=pg.mkPen(color="#ffffff"), name="A0")
                self.graph_A0A1.plot(self.time, self.A1, pen=pg.mkPen(color="#bfbfbf"), name="A1")
                self.graph_A0A1.plot(self.time, self.pv_fuel_setpoint, pen=pg.mkPen(color="#6d6d6d"), name="V1 Setpoint")

                # Plot for Valve 1: PWM vs. Time
                self.graph_PWM1.plot(self.time, self.pv_fuel_output, pen="g", name="V1 PWM Response")

                # A2/A3
                self.graph_A2A3.plot(self.time, self.A2, pen=pg.mkPen(color="#ffffff"), name="A0")
                self.graph_A2A3.plot(self.time, self.A3, pen=pg.mkPen(color="#bfbfbf"), name="A1")
                self.graph_A2A3.plot(self.time, self.pv_ox_setpoint, pen=pg.mkPen(color="#6d6d6d"), name="V2 Setpoint")

                # Plot for Valve 2: PWM vs. Time
                self.graph_PWM2.plot(self.time, self.pv_ox_output, pen=pg.mkPen(color="#ffffff"), name="V2 PWM Response")

                # Plot for delta values for health checks: A0-A1, Max_delta vs Time
                self.graph_dP_fuel.plot(self.time, self.dP_fuel, pen=pg.mkPen(color="#ffffff"), name="Delta A0/A1")
                self.graph_dP_fuel.plot(self.time, [self.v1_max_delta[0]] * len(self.time), pen=pg.mkPen(color="#bfbfbf"), name="MAX Delta A0/A1")
                
                # Plot for delta values for health checks: A2-A3, Max_delta vs Time
                self.graph_dP_ox.plot(self.time, self.dP_ox, pen=pg.mkPen(color="#ffffff"), name="Delta A2/A3")
                self.graph_dP_ox.plot(self.time, [self.v2_max_delta[0]] * len(self.time), pen=pg.mkPen(color="#bfbfbf"), name="Delta A0/A1")

            # Allow UI to update to prevent freezing
            QApplication.processEvents()

    def end_oxtest(self):
        self.send_command("IDLEOX")
        self.oxtest_output.append("Sending End Ox Test Command...")
        response = self.handle_serial_data()
        self.oxtest_output.append(response)
        self.save_data()
        self.oxtest_output.append("Data saved to working directory.")


    def shutdown(self):
        self.send_command("IDLE")
        self.control_output.append("Forced System Shutdown...")
        response = self.handle_serial_data()
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
