# -*- coding: utf-8 -*-
"""离屏快照: 只渲染浮窗自身(不管桌面)，铺在浅灰底上导出，供视觉质检"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QPoint

app = QApplication(sys.argv)
import souti

DEMO = """### 题目
**3.**【单选题】（2分）哪一年 8 月 15 日，时任浙江省委书记的习近平在安吉考察时首次提出“绿水青山就是金山银山”？

A. 2007　B. 2008　C. 2004　D. 2005

### 答案
**D. 2005**

### 解析
2005 年 8 月 15 日，时任浙江省委书记的习近平在浙江安吉县天荒坪镇余村考察时，首次提出“绿水青山就是金山银山”的科学论断。其余年份不符。

### 考点
考查该理念的提出时间与地点；易错点是把它与 2003 年“八八战略”、2007 年十七大等时间混淆。"""

cfg = souti.load_config()
w = souti.FloatWindow(cfg)
w.move(20, 20)
w.show()
for _ in range(6):
    app.processEvents()

def dump(widget, path, pad=16, bg=(232, 234, 238), maxw=None):
    pm = widget.grab()
    if maxw and pm.width() > maxw:
        pm = pm.scaledToWidth(maxw, Qt.SmoothTransformation)
    img = QImage(pm.width() + pad * 2, pm.height() + pad * 2, QImage.Format_RGB32)
    img.fill(QColor(*bg))
    p = QPainter(img)
    p.drawPixmap(pad, pad, pm)
    p.end()
    img.save(path)
    print("saved", path, img.width(), "x", img.height())
    return img

dump(w, "ui_welcome.png")

w.view.setMarkdown(DEMO)
w.status.setText("✓ 完成 · 5s · tokens 1933")
w.view.verticalScrollBar().setValue(0)
for _ in range(6):
    app.processEvents()
dump(w, "ui_answer.png")

w.toggle_collapse()
for _ in range(6):
    app.processEvents()
dump(w, "ui_collapsed.png")
w.toggle_collapse()

# 框选浮层：光标态（准星 + 坐标）
cat = souti.RegionCatcher()
cat.show()
cat.cur = QPoint(700, 430)
for _ in range(8):
    app.processEvents()
cat.repaint()
for _ in range(4):
    app.processEvents()
dump(cat, "ui_overlay_hint.png", pad=0, bg=(0, 0, 0), maxw=None)

# 框选浮层：拖拽中（选区高亮 + 尺寸标签 + 小十字）
cat.p0, cat.p1 = QPoint(480, 300), QPoint(1180, 700)
cat.cur = QPoint(1180, 700)
cat.repaint()
for _ in range(4):
    app.processEvents()
dump(cat, "ui_overlay_drag.png", pad=0, bg=(0, 0, 0), maxw=None)
cat.close()
w.close()
print("done")
