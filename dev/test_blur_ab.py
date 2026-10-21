# -*- coding: utf-8 -*-
"""决定性验证：同一窗口、同一位置，只把亚克力开/关做对比。
   窗内区域的高频能量（相邻像素差）在"开"时显著低于"关" => 背景真的被虚化了。"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRect

app = QApplication(sys.argv)
import souti

POS = (500, 40)
INSIDE_LOCAL = (24, 380, 380, 180)     # 窗口内：正文面板下方空白处（背后是网页正文）

cfg = souti.load_config()
cfg["theme"] = "morandi"
w = souti.FloatWindow(cfg)
w.move(*POS)
w.resize(440, 620)
w.show()
for _ in range(10):
    app.processEvents()
w.view.setHtml(w._welcome_html())
for _ in range(10):
    app.processEvents()
time.sleep(0.4)


def shot():
    for _ in range(10):
        app.processEvents()
    time.sleep(0.35)
    for _ in range(10):
        app.processEvents()
    return app.primaryScreen().grabWindow(0).toImage()


def hf_energy(img, rect):
    g = img.copy(rect)
    tot, n = 0, 0
    for y in range(0, g.height() - 2, 2):
        for x in range(0, g.width() - 2, 2):
            c = g.pixelColor(x, y).lightness()
            tot += abs(c - g.pixelColor(x + 2, y).lightness())
            tot += abs(c - g.pixelColor(x, y + 2).lightness())
            n += 2
    return tot / max(1, n)


dpr = app.primaryScreen().devicePixelRatio()
x, y, ww, hh = INSIDE_LOCAL
rect = QRect(int((POS[0] + x) * dpr), int((POS[1] + y) * dpr), int(ww * dpr), int(hh * dpr))

print("亚克力开关状态（apply_theme 后）:", w._acrylic_ok)
a = shot()
ea = hf_energy(a, rect)
a.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots", "blur_on.png"))

souti.enable_acrylic(w.winId(), (0, 0, 0), 0)      # 关掉亚克力
time.sleep(0.3)
b = shot()
eb = hf_energy(b, rect)
b.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots", "blur_off.png"))

print(f"窗内高频能量：亚克力开={ea:.2f}  关={eb:.2f}  下降={100*(1-ea/max(1e-6,eb)):.0f}%")
assert ea < eb * 0.7, "开亚克力后背景没有明显变糊，模糊没生效"
print("✅ 亚克力确实把背后内容虚化了（同等条件下高频能量显著下降）")
w.ball.hide()
w.tray.hide()
w.close()
