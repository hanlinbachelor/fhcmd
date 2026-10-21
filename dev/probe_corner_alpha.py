# -*- coding: utf-8 -*-
"""诊断：卡片自绘的圆角是否真的留出透明角"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage

app = QApplication(sys.argv)
import souti

cfg = souti.load_config()
cfg["theme"] = "morandi"
w = souti.FloatWindow(cfg)
w.resize(440, 620)
w.show()
for _ in range(10):
    app.processEvents()

pm = w.grab()
im = pm.toImage().convertToFormat(QImage.Format_ARGB32)
dpr = im.width() / max(1, w.width())
print("grab:", im.width(), im.height(), "dpr", dpr, "| acrylic:", w._acrylic_ok)
for lx, ly in [(0, 0), (1, 1), (4, 4), (8, 8), (14, 14), (24, 24), (220, 300)]:
    c = im.pixelColor(int(lx * dpr), int(ly * dpr))
    print(f"  逻辑({lx:3d},{ly:3d}) -> rgba({c.red():3d},{c.green():3d},{c.blue():3d},{c.alpha():3d})")
w.ball.hide(); w.tray.hide(); w.close()
