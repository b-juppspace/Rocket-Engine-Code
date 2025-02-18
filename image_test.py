from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
import sys

app = QApplication(sys.argv)

pixmap = QPixmap(":/qt-project.org/logos/qt-logo.png")  # Built-in Qt image

if pixmap.isNull():
    print("Fail")
else:
    print("Qt built-in image loaded successfully!")

sys.exit()
