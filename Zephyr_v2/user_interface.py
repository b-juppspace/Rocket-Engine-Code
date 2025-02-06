import sys
import serial
import threading
import pyqtgraph as pg
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QDial

class PressureControlGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.serial_conn = None
        self.running = False
        self.start_time = None
        self.time_series = []
        self.pressure_data = []
        self.pwm_data = []
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        self.label = QLabel("Pressure Data: Waiting...")
        layout.addWidget(self.label)
        
        self.init_serial_button = QPushButton("Initialize Serial Port")
        self.init_serial_button.clicked.connect(self.init_serial)
        layout.addWidget(self.init_serial_button)
        
        self.valve1_label = QLabel("Valve 1: 0.00")
        layout.addWidget(self.valve1_label)
        self.valve1_dial = QDial()
        self.valve1_dial.setRange(0, 30)  # 0 to 10 with 0.33 increments
        self.valve1_dial.valueChanged.connect(self.update_valve1)
        layout.addWidget(self.valve1_dial)
        
        self.valve2_label = QLabel("Valve 2: 0.00")
        layout.addWidget(self.valve2_label)
        self.valve2_dial = QDial()
        self.valve2_dial.setRange(0, 240)  # 0 to 80 with 0.33 increments
        self.valve2_dial.valueChanged.connect(self.update_valve2)
        layout.addWidget(self.valve2_dial)
        
        self.start_button = QPushButton("Begin Test")
        self.start_button.clicked.connect(lambda: self.send_command("BEGIN_TEST"))
        layout.addWidget(self.start_button)
        
        self.ignition_button = QPushButton("Start Ignition Sequence")
        self.ignition_button.clicked.connect(lambda: self.send_command("START_IGNITION"))
        layout.addWidget(self.ignition_button)
        
        self.shutdown_button = QPushButton("System Shutdown")
        self.shutdown_button.clicked.connect(lambda: self.send_command("SHUTDOWN"))
        layout.addWidget(self.shutdown_button)
        
        self.save_button = QPushButton("Save Data")
        self.save_button.clicked.connect(self.save_data)
        layout.addWidget(self.save_button)
        
        self.plot_widgets = []
        self.plot_curves = []
        self.plot_data = []
        titles = ["A0 & A1", "PWM1", "A2 & A3", "PWM2", "A4 & A5"]
        for title in titles:
            plot_widget = pg.PlotWidget(title=title)
            plot_curve = plot_widget.plot()
            layout.addWidget(plot_widget)
            self.plot_widgets.append(plot_widget)
            self.plot_curves.append(plot_curve)
            self.plot_data.append([])
        
        self.setLayout(layout)
        self.setWindowTitle("Pressure Control GUI")
        self.resize(500, 600)
    
    def init_serial(self):
        try:
            self.serial_conn = serial.Serial("COM3", 115200, timeout=1)
            self.running = True
            self.start_time = time.time()
            self.start_serial_thread()
        except serial.SerialException as e:
            self.label.setText(f"Error: {e}")
    
    def send_command(self, command):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.write((command + "\n").encode())
    
    def update_valve1(self):
        value = self.valve1_dial.value() * 0.33
        self.valve1_label.setText(f"Valve 1: {value:.2f}")
        self.send_setpoints()
    
    def update_valve2(self):
        value = self.valve2_dial.value() * 0.33
        self.valve2_label.setText(f"Valve 2: {value:.2f}")
        self.send_setpoints()
    
    def send_setpoints(self):
        if self.serial_conn and self.serial_conn.is_open:
            valve1_value = self.valve1_dial.value() * 0.33
            valve2_value = self.valve2_dial.value() * 0.33
            self.serial_conn.write(f"SETPOINTS,{valve1_value},{valve2_value}\n".encode())
    
    def start_serial_thread(self):
        thread = threading.Thread(target=self.read_serial_data, daemon=True)
        thread.start()
    
    def read_serial_data(self):
        while self.running and self.serial_conn:
            try:
                data = self.serial_conn.readline().decode().strip()
                current_time = time.time() - self.start_time
                self.time_series.append(current_time)
                
                if data.startswith("Pressure Data:"):
                    values = list(map(float, data.split(":")[1].split(",")))
                    self.pressure_data.append(values)
                    self.plot_data[0].append(sum(values[0:2])/2)  # A0 & A1
                    self.plot_data[2].append(sum(values[2:4])/2)  # A2 & A3
                    self.plot_data[4].append(sum(values[4:6])/2)  # A4 & A5
                    self.update_gui()
                elif data.startswith("PWM Data:"):
                    values = list(map(float, data.split(":")[1].split(",")))
                    self.pwm_data.append(values)
                    self.plot_data[1].append(values[0])  # PWM1
                    self.plot_data[3].append(values[1])  # PWM2
                    self.update_gui()
            except Exception as e:
                print(f"Serial Read Error: {e}")
    
    def update_gui(self):
        if self.time_series:
            for i in range(5):
                self.plot_curves[i].setData(self.time_series, self.plot_data[i])
            self.label.setText(f"Pressure Data: {self.pressure_data[-1]}")
    
    def save_data(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Data", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            with open(file_name, "w") as file:
                file.write("Time,Pressure_A0,Pressure_A1,Pressure_A2,Pressure_A3,Pressure_A4,Pressure_A5,PWM1,PWM2\n")
                for i in range(len(self.time_series)):
                    row = [self.time_series[i]] + self.pressure_data[i] + self.pwm_data[i]
                    file.write(",".join(map(str, row)) + "\n")
    
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
