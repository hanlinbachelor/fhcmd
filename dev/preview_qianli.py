# -*- coding: utf-8 -*-
"""生成「千里江山」主题预览（含宣纸纹理与公式渲染）"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

ANS = ("### 题目\n求 $\\lim_{x\\to 0}\\dfrac{\\sin x}{x}$ 的值\n\n"
       "### 答案\n$\\lim_{x\\to 0}\\dfrac{\\sin x}{x}=1$\n\n"
       "### 解析\n由等价无穷小 $\\sin x\\sim x$ 可得，当 $x\\to 0$ 时比值为 1。\n\n"
       "### 考点\n重要极限 · 等价无穷小替换\n")

cfg = souti.load_config()
cfg["theme"] = "qianli"
w = souti.FloatWindow(cfg)
w.show()
app.processEvents()
w._present_answer(ANS)
app.processEvents()
dlg = souti.SettingsDialog(w, cfg, w.th)
dlg.show()
app.processEvents()

a, b = w.grab(), dlg.grab()
out = QImage(a.width() + b.width() + 90, max(a.height(), b.height()) + 60, QImage.Format_RGB32)
out.fill(QColor(190, 196, 200))
p = QPainter(out)
p.drawPixmap(30, 30, a)
p.drawPixmap(a.width() + 60, 30, b)
p.end()
out.save("dev/shots/qianli.png")
print("主题:", w.th["label"], "| 尺寸", out.width(), out.height())
dlg.close()
w.ball.hide(); w.tray.hide(); w.close()
