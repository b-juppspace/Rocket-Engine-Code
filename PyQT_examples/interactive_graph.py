import sys
import numpy as np
import os
import csv
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class InteractiveGraphApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window properties
        self.setWindowTitle("Interactive Graph with Live Data")
        self.setGeometry(100, 100, 800, 600)

        # Central widget and layout
        self.main_widget = QWidget(self)
        self.layout = QVBoxLayout(self.main_widget)

        # Add a label at the top
        self.label = QLabel("Interactive Graph Example", self)
        self.label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.layout.addWidget(self.label)

        # Create plot area (graph)
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Create a button to start streaming data
        self.start_button = QPushButton("Start Streaming Data", self)
        self.start_button.clicked.connect(self.start_streaming)
        self.layout.addWidget(self.start_button)

        # Create a button to stop streaming data and save to CSV
        self.stop_button = QPushButton("Stop Streaming and Save Data", self)
        self.stop_button.clicked.connect(self.stop_streaming)
        self.layout.addWidget(self.stop_button)

        # Set layout to central widget
        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)

        # Data storage for the graph
        self.x_data = np.linspace(0, 10, 100)  # X axis: time or sample index
        self.y_data = np.sin(self.x_data)  # Initial Y axis: sine wave
        self.line, = None,  # Initialize line plot

        # Set up the timer for updating the graph
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_graph)

        # Default save folder and filename (initially the working directory)
        self.save_folder = os.getcwd()  # Start with the current working directory
        self.csv_filename = os.path.join(self.save_folder, "data.csv")

        # To track streaming status
        self.streaming = False

    def select_folder(self):
            # Open folder dialog for user to select the folder
            folder = QFileDialog.getExistingDirectory(self, "Select Folder for Saving Data")
        
            if folder:
                self.save_folder = folder  # Update the save folder path
                self.csv_filename = os.path.join(self.save_folder, "data.csv")  # Update the file path
                print(f"Data will be saved to: {self.csv_filename}")

    def start_streaming(self):
        # When the button is clicked, start the data stream
        self.start_button.setEnabled(False)  # Disable the button once clicked
        self.streaming = True
        self.timer.start(1000)  # Update graph every second

        # Create an initial plot on the graph
        ax = self.figure.add_subplot(111)
        ax.set_title("Live Data Streaming")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Amplitude")
        ax.grid(True)
        self.line, = ax.plot(self.x_data, self.y_data, label="Sine Wave", color="blue")
        ax.legend()

        # Redraw the canvas
        self.canvas.draw()

    def stop_streaming(self):
        # Stop streaming data and save to CSV
        if self.streaming:
            self.timer.stop()  # Stop the timer from updating the graph
            self.start_button.setEnabled(True)  # Enable the start button again
            self.streaming = False

            # Write the data to a CSV file
            self.write_data_to_csv()
            print(f"Data saved to {self.csv_filename}")
        else:
            print("Streaming is not active.")

    def write_data_to_csv(self):
        # Write the X and Y data to a CSV file
        with open(self.csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Time (s)', 'Amplitude'])  # Header
            for x, y in zip(self.x_data, self.y_data):
                writer.writerow([x, y])  # Write data rows

    def update_graph(self):
        # Update the graph with new data (simulate live data streaming)
        self.x_data = np.linspace(0, 10, 100)
        self.y_data = np.sin(self.x_data + np.random.randn(100) * 0.1)  # Add some noise for realism

        # Update the data of the line plot
        self.line.set_ydata(self.y_data)

        # Redraw the canvas to reflect the new data
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InteractiveGraphApp()
    window.show()
    sys.exit(app.exec_())
