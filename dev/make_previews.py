# -*- coding: utf-8 -*-
"""生成给用户看的外观预览图：两种主题 + 外观菜单"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtCore import QRect, QPoint

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

POS = (500, 30)
cfg = souti.load_config()

for theme in ("morandi", "laser"):
    cfg["theme"] = theme
    w = souti.FloatWindow(cfg)
    w.move(*POS)
    w.resize(440, 620)
    w.show()
    for _ in range(10):
        app.processEvents()
    w.view.setMarkdown(DEMO)
    w.status.setText("✓ 完成 · 5s · tokens 1933")
    w.view.verticalScrollBar().setValue(0)
    for _ in range(10):
        app.processEvents()
    time.sleep(0.5)
    for _ in range(10):
        app.processEvents()
    img = app.primaryScreen().grabWindow(0).toImage()
    dpr = app.primaryScreen().devicePixelRatio()
    crop = img.copy(QRect(int((POS[0] - 14) * dpr), int((POS[1] - 14) * dpr),
                          int(468 * dpr), int(648 * dpr)))
    out = os.path.join(SHOTS, f"preview_{theme}.png")
    crop.save(out)
    print("saved", out, crop.width(), "x", crop.height(), "| 亚克力:", w._acrylic_ok)

    if theme == "morandi":
        # 外观菜单截图
        menu = w.theme_menu
        menu.popup(w.mapToGlobal(QPoint(10, 10)))
        for _ in range(8):
            app.processEvents()
        time.sleep(0.2)
        for _ in range(6):
            app.processEvents()
        pm = menu.grab()
        menu.close()
        bg = QImage(pm.width() + 40, pm.height() + 40, QImage.Format_RGB32)
        bg.fill(QColor(232, 234, 238))
        p = QPainter(bg)
        p.drawPixmap(20, 20, pm)
        p.end()
        bg.save(os.path.join(SHOTS, "preview_theme_menu.png"))
        print("saved preview_theme_menu.png", bg.width(), "x", bg.height())

    w.ball.hide()
    w.tray.hide()
    w.close()
