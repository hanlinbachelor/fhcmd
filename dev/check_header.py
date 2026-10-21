# -*- coding: utf-8 -*-
"""检查标题栏 6 个按钮是否放得下、不重叠；并输出各控件几何"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRect

app = QApplication(sys.argv)
import souti
cfg = souti.load_config()
w = souti.FloatWindow(cfg)
w.show()
for _ in range(8):
    app.processEvents()

btns = [("框选", w.btn_shot), ("复制", w.btn_copy), ("清空", w.btn_clear),
        ("外观", w.btn_theme), ("收起", w.btn_fold), ("关闭", w.btn_close)]
bar_w = w.bar.width()
print("标题条宽度:", bar_w, "| 窗口:", w.width(), "x", w.height())
total = 0
prev_right = 0
ok = True
for name, b in btns:
    g = b.geometry()          # 相对 DragBar
    print(f"  {name}: x={g.x():4d} w={g.width():3d} h={g.height():3d} 右={g.right():4d}")
    if g.left() < prev_right:
        print("    ⚠ 与上一个按钮重叠!"); ok = False
    if g.right() > bar_w:
        print("    ⚠ 超出标题条!"); ok = False
    prev_right = g.right()
    total += g.width()

# 标题文字有没有被挤掉
title = w.bar.findChildren(type(w.bar))  # 占位，真正检查用布局余量
print("按钮总宽:", total, "| 标题所需约:", bar_w - total, "px")
print("结论:", "✅ 放得下，无重叠" if ok else "❌ 有重叠/溢出")
w.ball.hide(); w.tray.hide(); w.close()
