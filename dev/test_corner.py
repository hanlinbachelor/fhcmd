# -*- coding: utf-8 -*-
"""验证圆角外的“尖角”：先拿到窗口真实矩形，再检查矩形角落（弧线之外）的像素是否等于背景"""
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


def win_rect(title="反谋财害命器"):
    u32 = ctypes.windll.user32
    u32.SetProcessDPIAware()
    EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    out = []

    def cb(h, lp):
        n = u32.GetWindowTextLengthW(h)
        if n:
            b = ctypes.create_unicode_buffer(n + 1)
            u32.GetWindowTextW(h, b, n + 1)
            if b.value == title and u32.IsWindowVisible(h):
                r = wintypes.RECT()
                u32.GetWindowRect(h, ctypes.byref(r))
                out.append((r.left, r.top, r.right - r.left, r.bottom - r.top))
        return True

    u32.EnumWindows(EnumProc(cb), 0)
    return out[-1] if out else None


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

# 用自己这个 window 的 hwnd 取矩形，避免抓到正在运行的另一个实例
r = wintypes.RECT()
ctypes.windll.user32.GetWindowRect(int(w.winId()), ctypes.byref(r))
rect = (r.left, r.top, r.right - r.left, r.bottom - r.top)
print("本测试窗口矩形(物理):", rect, "| 亚克力:", getattr(w, "_acrylic_ok", None))
assert rect[2] > 100, "矩形异常"
L, T, Wd, Hd = rect
dpr = app.primaryScreen().devicePixelRatio()
corners = [(L + 4, T + 4), (L + Wd - 5, T + 4), (L + 4, T + Hd - 5), (L + Wd - 5, T + Hd - 5)]
center = (L + Wd // 2, T + Hd // 2)


def measure(tag):
    img = grab()
    diffs = []
    for x, y in corners:
        a, b = img.pixelColor(x, y), bg.pixelColor(x, y)
        diffs.append(abs(a.red() - b.red()) + abs(a.green() - b.green()) + abs(a.blue() - b.blue()))
    c = img.pixelColor(*center)
    cb_ = bg.pixelColor(*center)
    print(f"{tag:<18} 角落与背景差 {diffs} 平均 {sum(diffs)/4:5.1f} | 中心像素 {c.red(),c.green(),c.blue()} "
          f"背景 {cb_.red(),cb_.green(),cb_.blue()}")
    return img, diffs


img_r, d_r = measure("Region 已裁圆角")
ok = souti.set_round_region(w, 14, on=False)
time.sleep(0.3)
img_n, d_n = measure("Region 关闭(问题态)")
print("set_round_region 返回值:", ok)

for name, img in (("corner_fixed", img_r), ("corner_broken", img_n)):
    c = img.copy(QRect(L - 30, T - 30, 150, 150))
    c = c.scaled(c.width() * 3, c.height() * 3, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    c.save(os.path.join(SHOTS, name + ".png"))

a, b = sum(d_r) / 4, sum(d_n) / 4
print(f"\n角落与背景的平均差：裁圆角 {a:.1f} / 未裁 {b:.1f}")
w.ball.hide(); w.tray.hide(); w.close(); bd.close()
assert a < b * 0.5, "裁圆角没生效"
print("✅ 圆角外侧尖角已消除")
