
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle('GUI Test')
window.setGeometry(200, 200, 250, 150)
label = QLabel('<h1>Hello, World!</h1>', parent=window)
window.show()
print("Test GUI window should be visible now.")
sys.exit(app.exec())
