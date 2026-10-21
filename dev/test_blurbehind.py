# -*- coding: utf-8 -*-
"""试验：DwmEnableBlurBehindWindow + 圆角 Region 能不能"只糊圆角以内"。
   判定：窗内高频能量下降(说明糊了) + 角落像素等于背景(说明圆角外没糊)"""
import ctypes
import os
import sys
import time
from ctypes import wintypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QBrush
from PySide6.QtCore import Qt, QRect

app = QApplication(sys.argv)
import souti

SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
os.makedirs(SHOTS, exist_ok=True)
W, H = 1280, 800


class DWM_BLURBEHIND(ctypes.Structure):
    _fields_ = [("dwFlags", wintypes.DWORD), ("fEnable", wintypes.BOOL),
                ("hRgnBlur", wintypes.HANDLE), ("fTransitionOnMaximized", wintypes.BOOL)]


DWM_BB_ENABLE = 0x1
DWM_BB_BLURREGION = 0x2


def blur_behind_region(hwnd, rect_w, rect_h, radius, on=True):
    """按圆角 Region 开 blur-behind（区域外的圆角不会被糊）"""
    u32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    dwm = ctypes.windll.dwmapi
    if not on:
        bb = DWM_BLURBEHIND(DWM_BB_ENABLE, False, None, False)
        return dwm.DwmEnableBlurBehindWindow(int(hwnd), ctypes.byref(bb)) == 0
    d = max(2, int(radius * 2))
    rgn = gdi32.CreateRoundRectRgn(0, 0, rect_w + 1, rect_h + 1, d, d)
    bb = DWM_BLURBEHIND(DWM_BB_ENABLE | DWM_BB_BLURREGION, True, rgn, False)
    hr = dwm.DwmEnableBlurBehindWindow(int(hwnd), ctypes.byref(bb))
    return hr == 0


class Backdrop(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setGeometry(0, 0, W, H)

    def paintEvent(self, _):
        p = QPainter(self)
        g = QLinearGradient(0, 0, W, H)
        for i, c in enumerate(["#E86A5C", "#F2B34B", "#5FB49C", "#4C7FD6", "#9B6BC4", "#E86A5C"]):
            g.setColorAt(i / 5.0, QColor(c))
        p.fillRect(self.rect(), QBrush(g))


def grab():
    for _ in range(8):
        app.processEvents()
    time.sleep(0.25)
    for _ in range(8):
        app.processEvents()
    return app.primaryScreen().grabWindow(0).toImage()


def hf(img, rect):
    g = img.copy(rect)
    tot, n = 0, 0
    for y in range(0, g.height() - 2, 2):
        for x in range(0, g.width() - 2, 2):
            c = g.pixelColor(x, y).lightness()
            tot += abs(c - g.pixelColor(x + 2, y).lightness())
            n += 1
    return tot / max(1, n)


bd = Backdrop()
bd.show(); bd.raise_()
bg = grab()

cfg = souti.load_config()
cfg["theme"] = "morandi"
w = souti.FloatWindow(cfg)
w.move(300, 160)
w.resize(440, 620)
w.show(); bd.raise_(); w.raise_()
for _ in range(10):
    app.processEvents()
time.sleep(0.4)

r = wintypes.RECT()
ctypes.windll.user32.GetWindowRect(int(w.winId()), ctypes.byref(r))
L, T, Wd, Hd = r.left, r.top, r.right - r.left, r.bottom - r.top
dpr = app.primaryScreen().devicePixelRatio()
print("窗口:", (L, T, Wd, Hd), "dpr", dpr)

# 1) 先关掉亚克力，只试 blur-behind + 圆角 region
souti.enable_acrylic(w.winId(), (0, 0, 0), 0)
w.repaint()
time.sleep(0.3)
ok = blur_behind_region(w.winId(), int(w.width() * dpr), int(w.height() * dpr), 14 * dpr, on=True)
print("blur-behind 返回:", ok)
time.sleep(0.4)

img = grab()
inside = QRect(L + int(60 * dpr), T + int(380 * dpr), int(320 * dpr), int(160 * dpr))
outside = QRect(L + int(500 * dpr), T + int(380 * dpr), int(320 * dpr), int(160 * dpr))
print("窗内清晰度 %.2f / 窗外 %.2f" % (hf(img, inside), hf(img, outside)))

corners = [(L + 4, T + 4), (L + Wd - 5, T + 4), (L + 4, T + Hd - 5), (L + Wd - 5, T + Hd - 5)]
diffs = []
for x, y in corners:
    a, b = img.pixelColor(x, y), bg.pixelColor(x, y)
    diffs.append(abs(a.red() - b.red()) + abs(a.green() - b.green()) + abs(a.blue() - b.blue()))
print("角落与背景差:", diffs)

img.copy(QRect(L - 30, T - 30, 160, 160)).scaled(480, 480, Qt.KeepAspectRatio,
                                                 Qt.SmoothTransformation).save(
    os.path.join(SHOTS, "blurbehind_corner.png"))

w.ball.hide(); w.tray.hide(); w.close(); bd.close()
