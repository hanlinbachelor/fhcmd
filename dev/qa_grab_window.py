# -*- coding: utf-8 -*-
"""抓取正在运行的浮窗区域截图（用于目检）: 输出 qa_window2.png"""
import os, sys, ctypes
from ctypes import wintypes
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRect

app = QApplication(sys.argv)
sc = app.primaryScreen()
full = sc.grabWindow(0).toImage()
u32 = ctypes.windll.user32
EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
rects = []
def cb(h, lp):
    n = u32.GetWindowTextLengthW(h)
    if n:
        b = ctypes.create_unicode_buffer(n + 1)
        u32.GetWindowTextW(h, b, n + 1)
        if "反谋财害命器" in b.value:
            r = wintypes.RECT(); u32.GetWindowRect(h, ctypes.byref(r))
            rects.append((r.left, r.top, r.right - r.left, r.bottom - r.top))
    return True
u32.EnumWindows(EnumProc(cb), 0)
print("window(physical px):", rects, "desktop:", full.width(), full.height())
if not rects:
    sys.exit("浮窗没在运行")
l, t, w, h = rects[0]
# Qt 进程本身是 per-monitor DPI aware，GetWindowRect 拿到的已是物理像素，直接用
crop = full.copy(QRect(l, t, w, h))
crop.save("qa_window2.png")
print("saved qa_window2.png", crop.width(), crop.height())
