# -*- coding: utf-8 -*-
"""把窗口每个区域编号命名，出一张“区域地图”供指认"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

cfg = souti.load_config()
cfg["theme"] = "qianli"
w = souti.FloatWindow(cfg)
w.show()
app.processEvents()
w._present_answer(
    "### 题目\n求 $\\int_0^1 x^2\\,dx$\n\n### 答案\n$\\dfrac{1}{3}$\n\n"
    "### 解析\n由 $\\int x^2dx=\\frac{x^3}{3}$ 得 $\\left.\\frac{x^3}{3}\\right|_0^1=\\frac13$。\n\n"
    "### 考点\n定积分 · 牛顿-莱布尼茨公式")
app.processEvents()

shot = w.grab()
W, H = shot.width(), shot.height()
MARGIN_R, MARGIN_T = 300, 40
canvas = QImage(W + MARGIN_R, H + MARGIN_T * 2, QImage.Format_RGB32)
canvas.fill(QColor(238, 240, 242))
p = QPainter(canvas)
p.setRenderHint(QPainter.Antialiasing, True)
p.drawPixmap(0, MARGIN_T, shot)

bar = w.bar.geometry()
view = w.view.geometry()
inp = w.input.geometry()

regions = [
    ("1", "标题栏（可拖动）", QRect(bar.x() + 4, bar.y() + 6, bar.width() - 8, bar.height() - 12)),
    ("2", "栏底线", QRect(2, bar.bottom() - 2, W - 4, 4)),
    ("3", "正文区（滚动区）", QRect(view.x() + 2, view.y() + 60, view.width() - 4, view.height() - 70)),
    ("4", "答案块", QRect(view.x() + 8, view.y() + 6, view.width() - 16, 96)),
    ("5", "分区标题（题目/解析/考点）", QRect(view.x() + 10, view.y() + 108, 190, 26)),
    ("6", "输入框", QRect(inp.x(), inp.y(), inp.width(), inp.height())),
    ("7", "发送按钮", QRect(inp.right() + 4, inp.y(), 74, inp.height())),
    ("8", "卡片外框/圆角", QRect(2, 2, W - 4, H - 4)),
]

font = QFont("Microsoft YaHei", 10, QFont.Bold)
p.setFont(font)
accent = QColor(214, 48, 72)
for tag, name, rect in regions:
    p.setPen(QPen(accent, 2, Qt.DashLine))
    p.setBrush(Qt.NoBrush)
    p.drawRect(rect.adjusted(0, MARGIN_T, 0, MARGIN_T))
    # 编号圆点放在区域右侧
    cx, cy = W - 26, rect.center().y() + MARGIN_T
    p.setPen(Qt.NoPen)
    p.setBrush(accent)
    p.drawEllipse(QPoint(cx, cy), 13, 13)
    p.setPen(QColor(255, 255, 255))
    p.drawText(QRect(cx - 13, cy - 13, 26, 26), Qt.AlignCenter, tag)
    # 右侧文字
    p.setPen(accent)
    p.drawText(QPoint(cx + 22, cy + 5), f"{tag}  {name}")

p.end()
canvas.save("dev/shots/regions.png")
print("saved dev/shots/regions.png", canvas.width(), canvas.height())
w.ball.hide()
w.tray.hide()
w.close()
