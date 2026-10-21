# -*- coding: utf-8 -*-
"""客观验证亚克力是否真的把背景糊掉了：
   同一张文字密集的网页上，比较窗口内部 vs 窗口外部的"相邻像素差均值"（越高越清晰）。
   窗口内部明显更低 => 背景被模糊 => 真玻璃，而不是透明叠加。"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRect
from PySide6.QtGui import QImage

app = QApplication(sys.argv)
import souti

SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
os.makedirs(SHOTS, exist_ok=True)

POS = (500, 40)
cfg = souti.load_config()


def sharpness(img, rect):
    """相邻像素差均值（灰度）—— 抹糊后这个值会显著下降"""
    g = img.copy(rect)
    w, h = g.width(), g.height()
    total, n = 0, 0
    for y in range(0, h, 3):
        for x in range(0, w - 3, 3):
            total += abs(g.pixelColor(x, y).lightness() - g.pixelColor(x + 3, y).lightness())
            n += 1
    return total / max(1, n)


for theme in ("morandi", "laser"):
    cfg["theme"] = theme
    w = souti.FloatWindow(cfg)
    w.move(*POS)
    w.resize(440, 620)
    w.show()
    for _ in range(10):
        app.processEvents()
    w.view.setHtml(w._welcome_html())      # 欢迎页中下部是空白，便于测"透过去的背景"
    for _ in range(10):
        app.processEvents()
    time.sleep(0.5)
    for _ in range(10):
        app.processEvents()
    img = app.primaryScreen().grabWindow(0).toImage()
    dpr = app.primaryScreen().devicePixelRatio()
    img.save(os.path.join(SHOTS, f"blur_{theme}.png"))

    inside = QRect(int((POS[0] + 24) * dpr), int((POS[1] + 400) * dpr),
                   int(360 * dpr), int(150 * dpr))
    outside = QRect(int((POS[0] + 500) * dpr), int((POS[1] + 400) * dpr),
                    int(360 * dpr), int(150 * dpr))
    si, so = sharpness(img, inside), sharpness(img, outside)
    print(f"{theme:<8} 亚克力={getattr(w, '_acrylic_ok', None)}  窗内清晰度={si:.2f}  窗外={so:.2f}  "
          f"衰减={100*(1-si/max(1e-6,so)):.0f}%")
    w.ball.hide()
    w.tray.hide()
    w.close()
