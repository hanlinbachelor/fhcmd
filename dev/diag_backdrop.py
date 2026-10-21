# -*- coding: utf-8 -*-
"""诊断玻璃底图：抓到的背景到底糊没糊、对齐没对齐"""
import os
import sys
import statistics
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import Qt, QRect

app = QApplication(sys.argv)
import souti

SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
W, H = 1280, 800


class Page(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setGeometry(0, 0, W, H)

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#f7f8fa"))
        p.setPen(QColor("#1f2430"))
        p.setFont(QFont("Noto Sans SC", 11))
        y = 100
        for i in range(6):
            p.drawText(40, y, "第一章 极限与连续 课堂笔记 函数连续的定义与判定")
            y += 60


page = Page(); page.show(); page.raise_()
for _ in range(8): app.processEvents()
time.sleep(0.3)

cfg = souti.load_config(); cfg["theme"] = "morandi"
w = souti.FloatWindow(cfg)
print("bg 图尺寸:", w.card.bg_img.width(), "x", w.card.bg_img.height(), "| k =", w.card.bg_k,
      "| origin =", w.card.bg_origin)
w.card.bg_img.save(os.path.join(SHOTS, "diag_backdrop.png"))
# 统计：背景图里文字区域应有明暗变化，但如果糊透，标准差应很小
vals = [w.card.bg_img.pixelColor(x, y).lightness()
        for y in range(0, w.card.bg_img.height(), 2) for x in range(0, w.card.bg_img.width(), 2)]
print("背景图亮度: min=%d max=%d std=%.1f" % (min(vals), max(vals), statistics.pstdev(vals)))

w.move(300, 60); w.resize(440, 620); w.show(); page.raise_(); w.raise_()
for _ in range(10): app.processEvents()
time.sleep(0.4)
for _ in range(8): app.processEvents()
img = app.primaryScreen().grabWindow(0).toImage()
img.copy(QRect(300 * 2 - 20, 60 * 2 - 20, 920, 1280)).save(os.path.join(SHOTS, "diag_window.png"))
w.ball.hide(); w.tray.hide(); w.close(); page.close()
print("saved diag images")
