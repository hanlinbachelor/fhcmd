# -*- coding: utf-8 -*-
"""用真实原文走完整 UI，截图看公式到底显示成什么样"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

raw = io.open(r"D:\hermes\261020搜题浮窗\last_answer.txt", encoding="utf-8").read()
raw = raw.split("\n", 1)[1] if raw.startswith("=====") else raw

cfg = souti.load_config()
w = souti.FloatWindow(cfg)
w.show()
app.processEvents()
w._present_answer(raw)
app.processEvents()

img = w.view.grab().toImage()
# 统计“非背景”像素比例，粗略判断有没有内容（公式图会比纯文字密）
from collections import Counter
c = Counter()
for y in range(0, img.height(), 3):
    for x in range(0, img.width(), 3):
        q = img.pixelColor(x, y)
        c[(q.red() // 16, q.green() // 16, q.blue() // 16)] += 1
print("视图尺寸:", img.width(), img.height(), "颜色种类:", len(c))
w.grab().save("dev/shots/real_answer_ui.png")
print("saved dev/shots/real_answer_ui.png")
w.ball.hide()
w.tray.hide()
w.close()
