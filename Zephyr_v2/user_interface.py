import sys
import serial
import threading
import pyqtgraph as pg
import time
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout,
    QTabWidget, QTextEdit, QLineEdit, QComboBox, QSlider
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from datetime import datetime
import serial.tools.list_ports
import os

class SerialThread(QThread):
    data_received = pyqtSignal(list)
    message_received = pyqtSignal(str)

    def __init__(self, serial_conn):
        super().__init__()
        self.serial_conn = serial_conn
        self.running = True

    def run(self):
        while self.running and self.serial_conn.is_open:
            if self.serial_conn.in_waiting:
                try:
                    line = self.serial_conn.readline().decode().strip()
                    if "," in line:
                        data = line.split(",")
                        self.data_received.emit(data)
                    else:
                        self.message_received.emit(line)
                except Exception as e:
                    self.message_received.emit(f"Serial Error: {e}")
            time.sleep(0.01)

    def stop(self):
        self.running = False

class PressureControlGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.serial_conn = None
        self.serial_thread = None
        self.data = {
            "dataPointCount": [], "V0": [], "V1": [], "V2": [], "V3": [], "V4": [], "V5": [],
            "P0": [], "P1": [], "P2": [], "P3": [], "P4": [], "P5": [],
            "dP0": [], "dP1": [], "SV0": [], "SV1": [], "SP0": [], "SP1": [], "OP0": [], "OP1": [], "time": []
        }
        self.plot_lines = {}
        self.initUI()
        self.setup_plots()

    def initUI(self):
        self.setWindowTitle("Command Centre")
        self.setFixedSize(1400, 900)

        font = QFont("Consolas", 10)
        small_font = QFont("Consolas", 8)
        header_font = QFont("Consolas", 12, QFont.Bold)
        title_font = QFont("Consolas", 16, QFont.Bold)
        self.setFont(font)
        graph_label = "<span style='font-size:10pt; font-weight:bold; color:white; font-family:Consolas;'>{}</span>"

        main_layout = QHBoxLayout()
        image_path = os.path.join(os.getcwd(), "logosmall")

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget {
                background-color: #000000 !important;
                color: #ffffff;
                border: none;
            }
            QTabWidget::pane {
                background-color: #000000 !important;
                border: none;
            }
            QTabBar::tab {
                background-color: #ffffff;
                color: #000000;
                height: 30px;
                width: 140px;
                padding: 5px;
                border: 1px solid #1e1e2e;
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

        # Menu Tab
        menu_tab = QWidget()
        menu_layout = QVBoxLayout(menu_tab)
        menu_tab.setFont(font)

        logo_label = QLabel()
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print("Error: Could not load logo.png")
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        menu_layout.addWidget(logo_label)

        menu_title_label = QLabel("Juppspace Test GUI")
        menu_title_label.setFont(title_font)
        menu_title_label.setAlignment(Qt.AlignCenter)
        menu_title_label.setStyleSheet("color: white;")
        menu_layout.addWidget(menu_title_label)

        menu_text_label = QLabel("Script for rocket engine test purposes.")
        menu_text_label.setFont(font)
        menu_text_label.setAlignment(Qt.AlignCenter)
        menu_text_label.setStyleSheet("color: white;")
        menu_layout.addWidget(menu_text_label)

        self.tabs.addTab(menu_tab, "Menu")

        # Settings Tab
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_tab.setFont(font)

        settings_title_label = QLabel("Terminal")
        settings_title_label.setFont(header_font)
        settings_title_label.setStyleSheet("color: white;")
        settings_layout.addWidget(settings_title_label)

        self.settings_output = QTextEdit()
        self.settings_output.setReadOnly(True)
        self.settings_output.setStyleSheet("background-color: #000000; color: #ffffff;")
        self.settings_output.setFont(font)
        settings_layout.addWidget(self.settings_output)

        # Serial Port Selection
        port_layout = QVBoxLayout()
        port_layout.addWidget(QLabel("Select Port:", styleSheet="color: #ffffff;"))
        self.port_combo = QComboBox()
        self.port_combo.currentTextChanged.connect(self.update_serial)
        port_layout.addWidget(self.port_combo)
        settings_layout.addLayout(port_layout)

        init_serial_button = QPushButton("Initialize Serial Port")
        init_serial_button.clicked.connect(self.init_serial)
        init_serial_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        init_serial_button.setFont(font)
        settings_layout.addWidget(init_serial_button)

        test_connection_button = QPushButton("Test Connection")
        test_connection_button.clicked.connect(self.test_connection)
        test_connection_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        test_connection_button.setFont(font)
        settings_layout.addWidget(test_connection_button)

        tune_label = QLabel("Tune PID K-Values")
        tune_label.setFont(header_font)
        tune_label.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(tune_label)

        slider_layout = QHBoxLayout()
        for prefix, max_dp in [("V1", 120), ("V2", 700)]:  # V1: Fuel, V2: Oxidizer
            slider_section = QVBoxLayout()
            for param in [("kp", "kp: 1.00"), ("ki", "ki: 5.00"), ("kd", "kd: 2.00")]:
                lbl = QLabel(param[1], styleSheet="color: #ffffff;")
                slider = QSlider(Qt.Horizontal, minimum=0, maximum=80, value=10 if param[0] == "kp" else 50 if param[0] == "ki" else 20)
                slider.valueChanged.connect(lambda v, p=param[0], l=lbl, pr=prefix: l.setText(f"{p}: {v * 0.1:.2f}"))
                slider.setStyleSheet("QSlider::handle:horizontal { background: #ffffff; }")
                setattr(self, f"{param[0]}{prefix}_label", lbl)
                setattr(self, f"{param[0]}{prefix}_slider", slider)
                slider_section.addWidget(lbl)
                slider_section.addWidget(slider)
            slider_layout.addLayout(slider_section)
        settings_layout.addLayout(slider_layout)

        send_k_button = QPushButton("Send K Values")
        send_k_button.clicked.connect(self.send_k_values)
        send_k_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        send_k_button.setFont(font)
        settings_layout.addWidget(send_k_button)

        note_label = QLabel("Note: Open valves to complete PID tuning tests. Valve 1 will target 10 kPa (fuel), Valve 2 will target 300 kPa (oxidizer). Edit K values for tuning response.")
        note_label.setWordWrap(True)
        note_label.setStyleSheet("background-color: #000000; color: #ffffff;")
        note_label.setFont(small_font)
        settings_layout.addWidget(note_label)

        pid_tune_test_button = QPushButton("Begin PID Tune Test")
        pid_tune_test_button.clicked.connect(self.pid_tune_test)
        pid_tune_test_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        pid_tune_test_button.setFont(font)
        settings_layout.addWidget(pid_tune_test_button)

        # Calibration Tab
        cal_tab = QWidget()
        cal_layout = QVBoxLayout(cal_tab)
        cal_tab.setFont(font)

        cal_title_label = QLabel("Calibration Settings", font=header_font, styleSheet="color: white;")
        cal_layout.addWidget(cal_title_label)

        cal_fields = [
            ("V_MIN (V at 0 kPa)", "0.5", "v_min_edit"),
            ("V_MAX (V at 2068 kPa)", "4.5", "v_max_edit"),
            ("P_MIN (kPa)", "0.0", "p_min_edit"),
            ("P_MAX (kPa)", "2068.0", "p_max_edit"),
            ("V_REF (Reference V)", "5.0", "v_ref_edit")
        ]
        for label, default, attr in cal_fields:
            h_layout = QHBoxLayout()
            h_layout.addWidget(QLabel(label, styleSheet="color: #ffffff;"))
            edit = QLineEdit(default, styleSheet="background-color: #ffffff; color: #000000;")
            setattr(self, attr, edit)
            h_layout.addWidget(edit)
            cal_layout.addLayout(h_layout)

        send_cal_button = QPushButton("Update Calibration", styleSheet="background-color: #ffffff; color: #000000;", clicked=self.send_calibration)
        send_cal_button.setFont(font)
        cal_layout.addWidget(send_cal_button)
        cal_layout.addStretch()
        self.tabs.addTab(cal_tab, "Calibration")

        graph_layout = QHBoxLayout()
        self.graph_V1_PID = pg.PlotWidget(title=graph_label.format("Valve 1"))
        self.graph_V1_PID.setLabel('left', graph_label.format("P (kPa)"))
        self.graph_V1_PID.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_V1_PID.getAxis('left').setStyle(tickFont=font)
        self.graph_V1_PID.getAxis('bottom').setStyle(tickFont=font)
        graph_layout.addWidget(self.graph_V1_PID)

        self.graph_V2_PID = pg.PlotWidget(title=graph_label.format("Valve 2"))
        self.graph_V2_PID.setLabel('left', graph_label.format("P (kPa)"))
        self.graph_V2_PID.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_V2_PID.getAxis('left').setStyle(tickFont=font)
        self.graph_V2_PID.getAxis('bottom').setStyle(tickFont=font)
        graph_layout.addWidget(self.graph_V2_PID)
        settings_layout.addLayout(graph_layout)

        self.tabs.addTab(settings_tab, "Settings")

        # Play Tab
        play_tab = QWidget()
        play_layout = QVBoxLayout(play_tab)
        play_tab.setFont(font)

        play_title_label = QLabel("Terminal")
        play_title_label.setFont(header_font)
        play_title_label.setStyleSheet("color: white;")
        play_layout.addWidget(play_title_label)

        self.play_output = QTextEdit()
        self.play_output.setReadOnly(True)
        self.play_output.setStyleSheet("background-color: #000000; color: #ffffff;")
        self.play_output.setFont(font)
        play_layout.addWidget(self.play_output)

        for i, (label_text, max_val, default) in enumerate([
            ("Valve 1 (Fuel): 15 kPa", 120, 15),  
            ("Valve 2 (Oxidizer): 300 kPa", 700, 300)  
        ]):
            lbl = QLabel(label_text, styleSheet="color: #ffffff;")
            slider = QSlider(Qt.Horizontal, minimum=0, maximum=int(max_val / 0.33), value=int(default / 0.33))
            slider.valueChanged.connect(lambda v, l=lbl, idx=i: self.update_valve(v, l, idx))
            slider.setStyleSheet("QSlider::handle:horizontal { background: #ffffff; }")
            setattr(self, f"valve{i+1}_label", lbl)
            setattr(self, f"valve{i+1}_slider", slider)
            play_layout.addWidget(lbl)
            play_layout.addWidget(slider)

        button_layout = QHBoxLayout()
        ignition_button = QPushButton("Ignition")
        ignition_button.clicked.connect(self.ignition)
        ignition_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        ignition_button.setFont(font)
        button_layout.addWidget(ignition_button)

        shutdown_button = QPushButton("Shutdown")
        shutdown_button.clicked.connect(self.shutdown)
        shutdown_button.setStyleSheet("background-color: #ffffff; color: #000000;")
        shutdown_button.setFont(font)
        button_layout.addWidget(shutdown_button)
        play_layout.addLayout(button_layout)

        graph_layout2 = QHBoxLayout()
        graph_column1 = QVBoxLayout()
        self.graph_A0A1 = pg.PlotWidget(title=graph_label.format("A0/A1"))
        self.graph_A0A1.setLabel('left', graph_label.format("P (kPa)"))
        self.graph_A0A1.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_A0A1.getAxis('left').setStyle(tickFont=font)
        self.graph_A0A1.getAxis('bottom').setStyle(tickFont=font)
        graph_column1.addWidget(self.graph_A0A1)

        self.graph_PWM1 = pg.PlotWidget(title=graph_label.format("PWM1"))
        self.graph_PWM1.setLabel('left', graph_label.format("PWM(0-255)"))
        self.graph_PWM1.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_PWM1.getAxis('left').setStyle(tickFont=font)
        self.graph_PWM1.getAxis('bottom').setStyle(tickFont=font)
        graph_column1.addWidget(self.graph_PWM1)

        graph_column2 = QVBoxLayout()
        self.graph_A2A3 = pg.PlotWidget(title=graph_label.format("A2/A3"))
        self.graph_A2A3.setLabel('left', graph_label.format("P (kPa)"))
        self.graph_A2A3.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_A2A3.getAxis('left').setStyle(tickFont=font)
        self.graph_A2A3.getAxis('bottom').setStyle(tickFont=font)
        graph_column2.addWidget(self.graph_A2A3)

        self.graph_PWM2 = pg.PlotWidget(title=graph_label.format("PWM2"))
        self.graph_PWM2.setLabel('left', graph_label.format("PWM(0-255)"))
        self.graph_PWM2.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_PWM2.getAxis('left').setStyle(tickFont=font)
        self.graph_PWM2.getAxis('bottom').setStyle(tickFont=font)
        graph_column2.addWidget(self.graph_PWM2)

        self.graph_A4A5 = pg.PlotWidget(title=graph_label.format("A4/A5"))
        self.graph_A4A5.setLabel('left', graph_label.format("P (kPa)"))
        self.graph_A4A5.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_A4A5.getAxis('left').setStyle(tickFont=font)
        self.graph_A4A5.getAxis('bottom').setStyle(tickFont=font)
        graph_layout2.addLayout(graph_column1)
        graph_layout2.addLayout(graph_column2)
        graph_layout2.addWidget(self.graph_A4A5)
        play_layout.addLayout(graph_layout2)

        self.tabs.addTab(play_tab, "Play")

        # Health Tab
        health_tab = QWidget()
        health_layout = QVBoxLayout(health_tab)
        health_tab.setFont(font)

        health_title_label = QLabel("Health Monitoring")
        health_title_label.setFont(header_font)
        health_title_label.setStyleSheet("color: white;")
        health_layout.addWidget(health_title_label)

        graph_layout3 = QHBoxLayout()
        self.graph_delta_A0A1 = pg.PlotWidget(title=graph_label.format("delta A0/A1"))
        self.graph_delta_A0A1.setLabel('left', graph_label.format("P (kPa)"))
        self.graph_delta_A0A1.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_delta_A0A1.getAxis('left').setStyle(tickFont=font)
        self.graph_delta_A0A1.getAxis('bottom').setStyle(tickFont=font)
        graph_layout3.addWidget(self.graph_delta_A0A1)

        self.graph_delta_A2A3 = pg.PlotWidget(title=graph_label.format("delta A2/A3"))
        self.graph_delta_A2A3.setLabel('left', graph_label.format("P (kPa)"))
        self.graph_delta_A2A3.setLabel('bottom', graph_label.format("t (ms)"))
        self.graph_delta_A2A3.getAxis('left').setStyle(tickFont=font)
        self.graph_delta_A2A3.getAxis('bottom').setStyle(tickFont=font)
        graph_layout3.addWidget(self.graph_delta_A2A3)
        health_layout.addLayout(graph_layout3)

        self.tabs.addTab(health_tab, "Health")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        self.update_port_list()
        self.setup_plots()

    def update_port_list(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.clear()
        self.port_combo.addItems(ports)

    def update_serial(self, port):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_thread.stop()
            self.serial_thread.wait()
            self.serial_conn.close()
        self.init_serial()

    def init_serial(self):
        try:
            port = self.port_combo.currentText()
            if port:
                self.serial_conn = serial.Serial(port, 115200, timeout=1)
                self.serial_thread = SerialThread(self.serial_conn)
                self.serial_thread.data_received.connect(self.handle_data)
                self.serial_thread.message_received.connect(self.handle_message)
                self.serial_thread.start()
                self.settings_output.append(f"Serial port {port} initialized.")
        except serial.SerialException as e:
            self.settings_output.append(f"Error: {e}")

    def send_command(self, command):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.write((command + "\n").encode())

    def read_serial_data(self):
        if self.serial_conn and self.serial_conn.in_waiting:
            return self.serial_conn.readline().decode().strip().split(",")
        return None

    def handle_data(self, data):
        try:
            if len(data) >= 19:  # Match new 19-field format
                self.data["dataPointCount"].append(float(data[0]))
                for i in range(6):
                    self.data[f"V{i}"].append(float(data[i + 1]))
                    self.data[f"P{i}"].append(float(data[i + 7]) )  
                self.data["dP0"].append(float(data[13]) )  
                self.data["dP1"].append(float(data[14]))  
                self.data["SV0"].append(float(data[15]))
                self.data["SV1"].append(float(data[16]))
                self.data["SP0"].append(float(data[17]))  
                self.data["SP1"].append(float(data[18]))  
                self.data["OP0"].append(float(data[19]))
                self.data["OP1"].append(float(data[20]))
                self.data["time"].append(float(data[21]))
                self.update_plots()
                if abs(self.data["dP0"][-1]) > 17.4 or abs(self.data["dP1"][-1]) > 101.5:
                    self.send_command("IDLE")
                    self.play_output.append("Differential pressure limit exceeded, shutting down.")
        except (ValueError, IndexError) as e:
            self.settings_output.append(f"Data parse error: {e}")

    def handle_message(self, msg):
        if "TESTINGCONNECTION complete" in msg or "PID_DONE" in msg:
            self.save_data()
            self.settings_output.append(f"{msg} - Data saved.")
        elif "EMERGENCY_SHUTDOWN" in msg:
            self.play_output.append("Emergency shutdown triggered.")
        elif "Calibration updated" in msg:
            self.settings_output.append(msg)
        elif "K values updated" in msg:
            self.settings_output.append(msg)
        else:
            self.play_output.append(msg)

    def setup_plots(self):
        colors = {"data": "#ffffff", "setpoint": "#bfbfbf", "output": "#6d6d6d", "max": "#ff0000"}
        self.plot_lines["V1_P"] = self.graph_V1_PID.plot(pen=colors["data"], name="P1 (kPa)")
        self.plot_lines["V1_SP"] = self.graph_V1_PID.plot(pen=colors["setpoint"], name="V1 Setpoint (kPa)")
        self.plot_lines["V1_OP"] = self.graph_V1_PID.plot(pen=colors["output"], name="V1 Output")

        self.plot_lines["V2_P"] = self.graph_V2_PID.plot(pen=colors["data"], name="P3 (kPa)")
        self.plot_lines["V2_SP"] = self.graph_V2_PID.plot(pen=colors["setpoint"], name="V2 Setpoint (kPa)")
        self.plot_lines["V2_OP"] = self.graph_V2_PID.plot(pen=colors["output"], name="V2 Output")

        self.plot_lines["A0"] = self.graph_A0A1.plot(pen=colors["data"], name="A0 (kPa)")
        self.plot_lines["A1"] = self.graph_A0A1.plot(pen=colors["setpoint"], name="A1 (kPa)")
        self.plot_lines["V1_SP_A0A1"] = self.graph_A0A1.plot(pen=colors["output"], name="V1 Setpoint (kPa)")
        self.plot_lines["V1_OP_PWM1"] = self.graph_PWM1.plot(pen=colors["data"], name="V1 PWM")

        self.plot_lines["A2"] = self.graph_A2A3.plot(pen=colors["data"], name="A2 (kPa)")
        self.plot_lines["A3"] = self.graph_A2A3.plot(pen=colors["setpoint"], name="A3 (kPa)")
        self.plot_lines["V2_SP_A2A3"] = self.graph_A2A3.plot(pen=colors["output"], name="V2 Setpoint (kPa)")
        self.plot_lines["V2_OP_PWM2"] = self.graph_PWM2.plot(pen=colors["data"], name="V2 PWM")

        self.plot_lines["A4"] = self.graph_A4A5.plot(pen=colors["data"], name="A4 (kPa)")
        self.plot_lines["A5"] = self.graph_A4A5.plot(pen=colors["setpoint"], name="A5 (kPa)")

        self.plot_lines["dP0"] = self.graph_delta_A0A1.plot(pen=colors["data"], name="Fuel dP (kPa)")
        self.plot_lines["dP0_max"] = self.graph_delta_A0A1.plot(pen=colors["max"], name="Max Delta (120 kPa)")
        self.plot_lines["dP1"] = self.graph_delta_A2A3.plot(pen=colors["data"], name="Ox dP (kPa)")
        self.plot_lines["dP1_max"] = self.graph_delta_A2A3.plot(pen=colors["max"], name="Max Delta (700 kPa)")

    def update_plots(self):
        t = self.data["time"]
        self.plot_lines["V1_P"].setData(t, self.data["P1"])
        self.plot_lines["V1_SP"].setData(t, self.data["SP0"])
        self.plot_lines["V1_OP"].setData(t, self.data["OP0"])

        self.plot_lines["V2_P"].setData(t, self.data["P3"])
        self.plot_lines["V2_SP"].setData(t, self.data["SP1"])
        self.plot_lines["V2_OP"].setData(t, self.data["OP1"])

        self.plot_lines["A0"].setData(t, self.data["P0"])
        self.plot_lines["A1"].setData(t, self.data["P1"])
        self.plot_lines["V1_SP_A0A1"].setData(t, self.data["SP0"])
        self.plot_lines["V1_OP_PWM1"].setData(t, self.data["OP0"])

        self.plot_lines["A2"].setData(t, self.data["P2"])
        self.plot_lines["A3"].setData(t, self.data["P3"])
        self.plot_lines["V2_SP_A2A3"].setData(t, self.data["SP1"])
        self.plot_lines["V2_OP_PWM2"].setData(t, self.data["OP1"])

        self.plot_lines["A4"].setData(t, self.data["P4"])
        self.plot_lines["A5"].setData(t, self.data["P5"])

        self.plot_lines["dP0"].setData(t, self.data["dP0"])
        self.plot_lines["dP0_max"].setData(t, [120] * len(t))
        self.plot_lines["dP1"].setData(t, self.data["dP1"])
        self.plot_lines["dP1_max"].setData(t, [700] * len(t))

    def save_data(self):
        timestamp = datetime.now().strftime("%m-%d_%H-%M")
        file_name = os.path.join(os.getcwd(), f"DATA_{timestamp}.csv")
        with open(file_name, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Time", "V0", "V1", "V2", "V3", "V4", "V5", "P0", "P1", "P2", "P3", "P4", "P5",
                "dP0", "dP1", "SV0", "SV1", "SP0", "SP1", "OP0", "OP1"
            ])
            for i in range(len(self.data["time"])):
                writer.writerow([
                    self.data["time"][i],
                    self.data["V0"][i], self.data["V1"][i], self.data["V2"][i], self.data["V3"][i],
                    self.data["V4"][i], self.data["V5"][i], self.data["P0"][i], self.data["P1"][i],
                    self.data["P2"][i], self.data["P3"][i], self.data["P4"][i], self.data["P5"][i],
                    self.data["dP0"][i], self.data["dP1"][i], self.data["SV0"][i], self.data["SV1"][i],
                    self.data["SP0"][i], self.data["SP1"][i], self.data["OP0"][i], self.data["OP1"][i]
                ])

    def update_valve(self, value, label, index):
        val = value * 0.33
        label.setText(f"Valve {index + 1} ({'Fuel' if index == 0 else 'Oxidizer'}): {val:.2f} kPa")
        self.send_setpoints()

    def send_setpoints(self):
        if self.serial_conn and self.serial_conn.is_open:
            v1_val = self.valve1_slider.value() * 0.33
            v2_val = self.valve2_slider.value() * 0.33
            self.send_command(f"UPDATESETPOINTS,{v1_val},{v2_val}")

    def send_k_values(self):
        self.send_command("UPDATE_K_VALUES")
        time.sleep(0.1)
        kp1 = self.kpV1_slider.value() * 0.1
        ki1 = self.kiV1_slider.value() * 0.1
        kd1 = self.kdV1_slider.value() * 0.1
        kp2 = self.kpV2_slider.value() * 0.1
        ki2 = self.kiV2_slider.value() * 0.1
        kd2 = self.kdV2_slider.value() * 0.1
        self.send_command(f"{kp1},{ki1},{kd1},{kp2},{ki2},{kd2}")
        self.settings_output.append(f"K values sent: {kp1},{ki1},{kd1},{kp2},{ki2},{kd2}")

    def send_calibration(self):
        v_min = self.v_min_edit.text()
        v_max = self.v_max_edit.text()
        p_min = self.p_min_edit.text()
        p_max = self.p_max_edit.text()
        v_ref = self.v_ref_edit.text()
        try:
            float(v_min), float(v_max), float(p_min), float(p_max), float(v_ref)
            self.send_command(f"UPDATE_CALIBRATION,{v_min},{v_max},{p_min},{p_max},{v_ref}")
        except ValueError:
            self.settings_output.append("Error: Calibration values must be numbers")

    def test_connection(self):
        self.send_command("TEST_CONNECTION")
        while True:
            response = self.read_serial_data()
            if response and "IDLE" in response:
                self.settings_output.append("Test completed. Returning to idle & saving data.")
                self.save_data()
                self.settings_output.append("Data saved to working directory.")
                break
            elif response:
                self.settings_output.append(",".join(response))
            QApplication.processEvents()

    def pid_tune_test(self):
        self.send_command("PID_TUNE_TEST")
        while True:
            response = self.read_serial_data()
            if response and "IDLE" in response:
                self.settings_output.append("Test completed. Returning to idle & saving data.")
                self.save_data()
                self.settings_output.append("Data saved to working directory.")
                break
            elif response and "PID_DONE" in response:
                self.settings_output.append("PID tuning test completed.")
            elif response:
                try:
                    self.data["dataPointCount"].append(float(response[0]))
                    for i in range(6):
                        self.data[f"V{i}"].append(float(response[i + 1]))
                        self.data[f"P{i}"].append(float(response[i + 7])) 
                    self.data["dP0"].append(float(response[13])) 
                    self.data["dP1"].append(float(response[14]))  
                    self.data["SV0"].append(float(response[15]))
                    self.data["SV1"].append(float(response[16]))
                    self.data["SP0"].append(float(response[17]))  
                    self.data["SP1"].append(float(response[18])) 
                    self.data["OP0"].append(float(response[19]))
                    self.data["OP1"].append(float(response[20]))
                    self.data["time"].append(float(response[21]))
                    self.update_plots()
                    self.settings_output.append("Testing...")
                except (ValueError, IndexError) as e:
                    self.settings_output.append(f"Data parse error: {e}")
            QApplication.processEvents()

    def ignition(self):
        self.send_command("IGNITION")
        while True:
            response = self.read_serial_data()
            if response and "IDLE" in response:
                self.play_output.append("Test completed. Returning to idle & saving data.")
                self.save_data()
                self.play_output.append("Data saved to working directory.")
                break
            elif response and any(state in response for state in ["IGNITION", "THRUSTING", "COOLING"]):
                self.play_output.append(f"{response.split(',')[0]} state commenced.")
            elif response:
                try:
                    self.data["dataPointCount"].append(float(response[0]))
                    for i in range(6):
                        self.data[f"V{i}"].append(float(response[i + 1]))
                        self.data[f"P{i}"].append(float(response[i + 7])) 
                    self.data["dP0"].append(float(response[13])) 
                    self.data["dP1"].append(float(response[14]))  
                    self.data["SV0"].append(float(response[15]))
                    self.data["SV1"].append(float(response[16]))
                    self.data["SP0"].append(float(response[17]))  
                    self.data["SP1"].append(float(response[18]))  
                    self.data["OP0"].append(float(response[19]))
                    self.data["OP1"].append(float(response[20]))
                    self.data["time"].append(float(response[21]))
                    self.update_plots()
                    if abs(self.data["dP0"][-1]) > 17.4 or abs(self.data["dP1"][-1]) > 101.5:
                        self.send_command("IDLE")
                        self.play_output.append("Differential pressure limit exceeded, shutting down.")
                    self.play_output.append("Testing...")
                except (ValueError, IndexError) as e:
                    self.play_output.append(f"Data parse error: {e}")
            QApplication.processEvents()

    def shutdown(self):
        self.send_command("IDLE")
        self.play_output.append("Forced System Shutdown...")
        response = self.read_serial_data()
        if response:
            self.play_output.append(response[0])
        self.save_data()
        self.play_output.append("Data saved to working directory.")

    def closeEvent(self, event):
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait()
        if self.serial_conn:
            self.serial_conn.close()
        event.accept()

    def update_kpV1(self):
        value = self.kpV1_slider.value() * 0.1
        self.kpV1_label.setText(f"kp: {value:.2f}")

    def update_kiV1(self):
        value = self.kiV1_slider.value() * 0.1
        self.kiV1_label.setText(f"ki: {value:.2f}")

    def update_kdV1(self):
        value = self.kdV1_slider.value() * 0.1
        self.kdV1_label.setText(f"kd: {value:.2f}")

    def update_kpV2(self):
        value = self.kpV2_slider.value() * 0.1
        self.kpV2_label.setText(f"kp: {value:.2f}")

    def update_kiV2(self):
        value = self.kiV2_slider.value() * 0.1
        self.kiV2_label.setText(f"ki: {value:.2f}")

    def update_kdV2(self):
        value = self.kdV2_slider.value() * 0.1
        self.kdV2_label.setText(f"kd: {value:.2f}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = PressureControlGUI()
    gui.show()
    sys.exit(app.exec_())