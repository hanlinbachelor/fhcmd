# -*- coding: utf-8 -*-
"""终验：欢迎页(空白区) + 文字密集背景。量：空白处的背景是否被糊；圆角外是否干净"""
import ctypes, os, sys, time
from ctypes import wintypes
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import Qt, QRect

app = QApplication(sys.argv)
import souti
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
W, H = 1280, 800


class TextPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setGeometry(0, 0, W, H)

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#ffffff"))
        p.setPen(QColor("#1a1a1a"))
        p.setFont(QFont("Microsoft YaHei UI", 9))
        y = 40
        for para in range(6):
            for line in range(4):
                p.drawText(30, y, "3.【单选题】哪一年8月15日，时任浙江省委书记在安吉考察时提出绿水青山就是金山银山")
                y += 24
            y += 96


def grab():
    for _ in range(8): app.processEvents()
    time.sleep(0.3)
    for _ in range(8): app.processEvents()
    return app.primaryScreen().grabWindow(0).toImage()


def hf(img, rect):
    g = img.copy(rect)
    tot = n = 0
    for y in range(0, g.height() - 2, 2):
        for x in range(0, g.width() - 2, 2):
            c = g.pixelColor(x, y).lightness()
            tot += abs(c - g.pixelColor(x + 2, y).lightness()); n += 1
    return tot / max(1, n)


page = TextPage(); page.show(); page.raise_()
bg = grab()

cfg = souti.load_config(); cfg["theme"] = "morandi"
w = souti.FloatWindow(cfg)
w.move(300, 140); w.resize(440, 620)
w.show(); page.raise_(); w.raise_()
for _ in range(12): app.processEvents()
time.sleep(0.4)

r = wintypes.RECT(); ctypes.windll.user32.GetWindowRect(int(w.winId()), ctypes.byref(r))
L, T, Wd, Hd = r.left, r.top, r.right - r.left, r.bottom - r.top
dpr = app.primaryScreen().devicePixelRatio()
img = grab()

# 欢迎页正文明显是空的区域（窗口内 200..380 x, 470..590 y —— 只有空白面板）
box = QRect(int((300 + 190) * dpr), int((140 + 430) * dpr), int(180 * dpr), int(120 * dpr))
print("同一空白区清晰度：合成后 %.2f / 原始背景 %.2f" % (hf(img, box), hf(bg, box)))

corners = [(L + 4, T + 4), (L + Wd - 5, T + 4), (L + 4, T + Hd - 5), (L + Wd - 5, T + Hd - 5)]
diffs = []
for x, y in corners:
    a, b = img.pixelColor(x, y), bg.pixelColor(x, y)
    diffs.append(abs(a.red()-b.red()) + abs(a.green()-b.green()) + abs(a.blue()-b.blue()))
print("角落与背景差:", diffs)

img.copy(QRect(L - 20, T - 20, Wd + 40, Hd + 40)).save(os.path.join(SHOTS, "final_morandi_welcome.png"))
img.copy(QRect(L - 24, T - 24, 140, 140)).scaled(420, 420, Qt.KeepAspectRatio,
                                                 Qt.SmoothTransformation).save(os.path.join(SHOTS, "final_corner_zoom.png"))
print("saved previews")
w.ball.hide(); w.tray.hide(); w.close(); page.close()
