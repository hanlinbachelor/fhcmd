# -*- coding: utf-8 -*-
"""把莫兰迪玻璃窗摆在真实桌面上（白底网页上方）抓屏，检验可读性与玻璃感"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRect

app = QApplication(sys.argv)
import souti

SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
os.makedirs(SHOTS, exist_ok=True)

DEMO = """### 题目
**3.**【单选题】（2分）哪一年 8 月 15 日，时任浙江省委书记的习近平在安吉考察时首次提出“绿水青山就是金山银山”？

A. 2007　B. 2008　C. 2004　D. 2005

### 答案
**D. 2005**

### 解析
2005 年 8 月 15 日，习近平在浙江安吉县天荒坪镇余村考察时首次提出该论断。其余年份不符。

### 考点
考查该理念的提出时间与地点；易错点是与 2003 年“八八战略”混淆。"""

pos = (520, 40)
cfg = souti.load_config()
cfg["theme"] = "morandi"
w = souti.FloatWindow(cfg)
w.move(*pos)
w.resize(440, 620)
w.show()
for _ in range(10):
    app.processEvents()
print("亚克力生效:", getattr(w, "_acrylic_ok", None), "| 主题:", w.theme_name)
w.view.setMarkdown(DEMO)
w.status.setText("✓ 完成 · 5s · tokens 1933")
for _ in range(10):
    app.processEvents()
time.sleep(0.4)
for _ in range(10):
    app.processEvents()

img = app.primaryScreen().grabWindow(0).toImage()
dpr = app.primaryScreen().devicePixelRatio()
crop = img.copy(QRect(int((pos[0] - 12) * dpr), int((pos[1] - 12) * dpr),
                      int(464 * dpr), int(644 * dpr)))
out = os.path.join(SHOTS, "real_morandi_over_webpage.png")
crop.save(out)
print("saved", out, crop.width(), "x", crop.height())

# 也存一张镭射做对照
w.apply_theme("laser")
for _ in range(10):
    app.processEvents()
time.sleep(0.3)
for _ in range(10):
    app.processEvents()
img2 = app.primaryScreen().grabWindow(0).toImage()
out2 = os.path.join(SHOTS, "real_laser_over_webpage.png")
img2.copy(QRect(int((pos[0] - 12) * dpr), int((pos[1] - 12) * dpr),
                    int(464 * dpr), int(644 * dpr))).save(out2)
print("saved", out2)

w.ball.hide()
w.tray.hide()
w.close()
