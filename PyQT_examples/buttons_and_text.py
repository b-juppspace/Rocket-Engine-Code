import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit

class BasicPyQtInterface(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window properties
        self.setWindowTitle("Basic PyQt5 Interface")
        self.setGeometry(100, 100, 400, 300)  # Set window size

        # Central widget and layout
        self.main_widget = QWidget(self)
        self.layout = QVBoxLayout(self.main_widget)

        # Add a label
        self.label = QLabel("Welcome to PyQt5!", self)
        self.label.setStyleSheet("font-size: 20px; font-weight: bold;")  # Style the label
        self.layout.addWidget(self.label)

        # Add a text input field
        self.text_input = QLineEdit(self)
        self.text_input.setPlaceholderText("Type something here...")
        self.layout.addWidget(self.text_input)

        # Add a button to update the label with the input text
        self.update_button = QPushButton("Update Label", self)
        self.update_button.clicked.connect(self.update_label)  # Connect button to function
        self.layout.addWidget(self.update_button)

        # Add a button to clear the input and label
        self.clear_button = QPushButton("Clear", self)
        self.clear_button.clicked.connect(self.clear_input)  # Connect button to function
        self.layout.addWidget(self.clear_button)

        # Set layout to the central widget
        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)

    def update_label(self):
        # Update the label with the text input
        text = self.text_input.text()
        self.label.setText(f"You typed: {text}")

    def clear_input(self):
        # Clear the text input and the label
        self.text_input.clear()
        self.label.setText("Welcome to PyQt5!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BasicPyQtInterface()
    window.show()
    sys.exit(app.exec_())
