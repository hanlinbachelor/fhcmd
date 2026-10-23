# -*- coding: utf-8 -*-
"""出一张对照图：主窗 + 设置窗（同一主题，检查风格是否一致）"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

ANS = "### 题目\n求 $x^2-3x+2=0$ 的解\n\n### 答案\n$x=1,2$\n\n### 解析\n因式分解 $x^2-3x+2=(x-1)(x-2)$\n\n### 考点\n一元二次方程\n"

for theme in ("morandi", "laser"):
    cfg = souti.load_config()
    cfg["theme"] = theme
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
    out.fill(QColor(200, 204, 208))
    p = QPainter(out)
    p.drawPixmap(30, 30, a)
    p.drawPixmap(a.width() + 60, 30, b)
    p.end()
    out.save(f"dev/shots/pair_{theme}.png")
    print(f"{theme}: {out.width()}x{out.height()} -> dev/shots/pair_{theme}.png")
    dlg.close()
    w.ball.hide(); w.tray.hide(); w.close()
