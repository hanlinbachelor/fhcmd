# -*- coding: utf-8 -*-
"""给窗口里每条可能的“边界”打上字母标注，方便用户指认"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

cfg = souti.load_config()
cfg["theme"] = "qianli"
w = souti.FloatWindow(cfg)
w.show()
app.processEvents()
w._present_answer("### 题目\n求 $\\int_0^1 x^2\\,dx$\n\n### 答案\n$\\dfrac{1}{3}$\n\n### 解析\n由 $\\int x^2 dx=\\frac{x^3}{3}$ 得。\n\n### 考点\n定积分")
app.processEvents()

base = w.grab()
img = QImage(base.width(), base.height(), QImage.Format_ARGB32)
img.fill(QColor(246, 244, 240))
p = QPainter(img)
p.drawPixmap(0, 0, base)

bar = w.bar.geometry()
view = w.view.geometry()

p.setPen(QPen(QColor(230, 40, 60), 2))
font = QFont("Noto Sans SC", 11, QFont.Bold)
p.setFont(font)


def label(text, x, y):
    pass
    p.setBrush(QColor(255, 255, 255, 235))
    p.setPen(QPen(QColor(230, 40, 60), 1))
    p.drawRoundedRect(x, y, 46, 26, 6, 6)
    p.setPen(QColor(180, 20, 40))
    p.drawText(x, y, 46, 26, Qt.AlignCenter, text)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor(230, 40, 60), 2))


# A 窗口外缘
p.drawRect(3, 3, img.width() - 7, img.height() - 7)
label("A", 14, 40)
# B 标题栏下那条线
p.drawLine(4, bar.bottom(), img.width() - 5, bar.bottom())
label("B", 14, bar.bottom() + 4)
# C 正文面板边缘
p.drawRect(view.x() + 2, view.y() + 2, view.width() - 5, view.height() - 5)
label("C", view.right() - 56, view.y() + 6)
# D 答案块边缘（正文顶部那块）
p.drawRect(view.x() + 8, view.y() + 8, view.width() - 17, 100)
label("D", view.right() - 56, view.y() + 112)

p.end()
img.save("dev/shots/boundaries.png")
print("saved dev/shots/boundaries.png", img.width(), img.height())
w.ball.hide()
w.tray.hide()
w.close()
