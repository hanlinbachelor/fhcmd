import sys
from PySide6.QtWidgets import QApplication
app = QApplication(sys.argv)
for s in app.screens():
    g = s.geometry()
    print(s.name(), g.x(), g.y(), g.width(), g.height(), "dpr=", s.devicePixelRatio())
print("virtual:", app.primaryScreen().virtualGeometry())
