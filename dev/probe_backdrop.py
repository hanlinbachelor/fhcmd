# -*- coding: utf-8 -*-
"""最小用例：全屏彩色底能不能被抓屏"看见" """
import sys, time
sys.path.insert(0, "C:/Users/hanli/Desktop")
sys.path.insert(0, "D:/hermes/261020搜题浮窗")
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QImage, QPainter, QColor, QLinearGradient, QBrush
from PySide6.QtCore import Qt, QRect

app = QApplication(sys.argv)
W, H = 1280, 800

class B(QWidget):
    def __init__(self, striped):
        super().__init__()
        self.striped = striped
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setGeometry(0, 0, W, H)
    def paintEvent(self, _):
        p = QPainter(self)
        if self.striped:
            g = QLinearGradient(0, 0, W, H)
            g.setColorAt(0, QColor("#E86A5C")); g.setColorAt(1, QColor("#4C7FD6"))
            p.fillRect(self.rect(), QBrush(g))
        else:
            p.fillRect(self.rect(), QColor(128, 128, 128))

for striped in (True, False):
    b = B(striped)
    b.show(); b.raise_()
    for _ in range(10):
        app.processEvents()
    time.sleep(0.3)
    for _ in range(10):
        app.processEvents()
    img = app.primaryScreen().grabWindow(0).toImage()
    c1 = img.pixelColor(1000, 700)
    c2 = img.pixelColor(300, 500)
    print("striped=%s 抓屏像素 (1000,700)=(%d,%d,%d) (300,500)=(%d,%d,%d)"
          % (striped, c1.red(), c1.green(), c1.blue(), c2.red(), c2.green(), c2.blue()))
    b.close()
