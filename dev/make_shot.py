# -*- coding: utf-8 -*-
"""真实屏幕预览：灰底 + 液态玻璃窗 + 答案态，抓屏导出（给用户看效果）"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import Qt, QRect

app = QApplication(sys.argv)
import souti

SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
os.makedirs(SHOTS, exist_ok=True)
W, H = 1280, 800
POS = (300, 60)

TEXT = """### 题目
**3.**【单选题】（2分）哪一年 8 月 15 日，时任浙江省委书记的习近平在安吉考察时首次提出“绿水青山就是金山银山”？

A. 2007　B. 2008　C. 2004　D. 2005

### 答案
**D. 2005**

### 解析
2005 年 8 月 15 日，习近平在浙江安吉县天荒坪镇余村考察时首次提出该论断；其余年份均不符。

### 考点
考查该理念的提出时间与地点；易错点是与 2003 年“八八战略”混淆。"""


class Page(QWidget):
    """模拟一张真实网页：白底 + 稀疏文字"""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setGeometry(0, 0, W, H)

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#f7f8fa"))
        p.fillRect(QRect(0, 0, W, 56), QColor("#ffffff"))
        p.setPen(QColor("#8a94a6"))
        p.setFont(QFont("Noto Sans SC", 9))
        p.drawText(24, 34, "智慧树 · 在线学堂")
        p.setPen(QColor("#1f2430"))
        p.setFont(QFont("Noto Sans SC", 11))
        y = 120
        for i in range(6):
            p.drawText(40, y, "第一章 极限与连续 课堂笔记：函数在某点连续，当且仅当左右极限存在且相等。")
            p.drawText(40, y + 30, "（示例页面文字，与右侧浮窗内容无关）")
            y += 110


def grab():
    for _ in range(8):
        app.processEvents()
    time.sleep(0.35)
    for _ in range(8):
        app.processEvents()
    return app.primaryScreen().grabWindow(0).toImage()


page = Page()
page.show(); page.raise_()

cfg = souti.load_config()
for theme, tag in (("morandi", "liquid"), ("laser", "laser")):
    cfg["theme"] = theme
    w = souti.FloatWindow(cfg)
    w.move(*POS); w.resize(440, 620)
    w.show(); page.raise_(); w.raise_()
    for _ in range(10):
        app.processEvents()
    w.current_answer = TEXT
    w._present_answer(TEXT)
    w.status.setText("✓ 完成 · 5s · tokens 1933")
    for _ in range(12):
        app.processEvents()
    time.sleep(0.5)
    img = grab()
    dpr = app.primaryScreen().devicePixelRatio()
    out = os.path.join(SHOTS, f"shot_{tag}.png")
    img.copy(QRect(int((POS[0] - 12) * dpr), int((POS[1] - 12) * dpr),
                   int(464 * dpr), int(644 * dpr))).save(out)
    print("saved", out)
    w.ball.hide(); w.tray.hide(); w.close()
    for _ in range(6):
        app.processEvents()
page.close()
