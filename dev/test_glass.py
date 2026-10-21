# -*- coding: utf-8 -*-
"""真实透过率测量：桌面上摆一块彩色底 -> 浮窗盖上去 -> 抓屏；
   换一块纯色底再来一次，用两次抓屏的差值 / 底色的差值 = 真实透过率。
   这是走 DWM 合成的真实路径，不是离屏渲染。"""
import os
import sys
import time
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QImage, QPainter, QColor, QLinearGradient, QBrush
from PySide6.QtCore import Qt, QRect, QTimer

app = QApplication(sys.argv)
import souti

SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
os.makedirs(SHOTS, exist_ok=True)
cfg = souti.load_config()
W, H = 1280, 800
POS = (60, 40)


class Backdrop(QWidget):
    """全屏底图：mode='stripes' 彩色渐变条纹；mode='solid' 纯中灰"""

    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setGeometry(0, 0, W, H)

    def paintEvent(self, _):
        p = QPainter(self)
        if self.mode == "stripes":
            g = QLinearGradient(0, 0, W, H)
            for i, c in enumerate(["#E86A5C", "#F2B34B", "#5FB49C", "#4C7FD6", "#9B6BC4", "#E86A5C"]):
                g.setColorAt(i / 5.0, QColor(c))
            p.fillRect(self.rect(), QBrush(g))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 80))
            for x in range(-H, W, 90):
                p.drawRect(QRect(x, 0, 34, H))
        else:
            p.fillRect(self.rect(), QColor(128, 128, 128))


def pixels(img, pts):
    return [img.pixelColor(x, y) for x, y in pts]


def grab_screen():
    for _ in range(8):
        app.processEvents()
    time.sleep(0.25)
    for _ in range(8):
        app.processEvents()
    return app.primaryScreen().grabWindow(0).toImage()


def measure(theme):
    cfg["theme"] = theme
    win = souti.FloatWindow(cfg)
    win.move(*POS)
    win.resize(440, 620)
    win.show()
    for _ in range(10):
        app.processEvents()
    win.view.setHtml(win._welcome_html())

    # 采样点（窗口内坐标，避开文字/按钮：正文面板左侧空白、卡片边距处）
    local = [(24, 470), (200, 470), (400, 470), (24, 240), (420, 240)]
    dpr = app.primaryScreen().devicePixelRatio()
    global_pts = [(int((POS[0] + x) * dpr), int((POS[1] + y) * dpr)) for x, y in local]

    results = {}
    for mode in ("stripes", "solid"):
        bd = Backdrop(mode)
        bd.show()
        bd.raise_()
        win.raise_()          # 浮窗在最上面
        for _ in range(8):
            app.processEvents()
        shot = grab_screen()
        bd.close()
        results[mode] = pixels(shot, global_pts)
        shot.copy(QRect(POS[0] - 10, POS[1] - 10, 470, 650)).save(
            os.path.join(SHOTS, f"real_{theme}_{mode}.png"))

    diffs_win, diffs_bg = [], []
    for i, (a, b) in enumerate(zip(results["stripes"], results["solid"])):
        dw = abs(a.red() - b.red()) + abs(a.green() - b.green()) + abs(a.blue() - b.blue())
        diffs_win.append(dw)

    # 底色本身在这几个点的差值（条纹 vs 灰）
    bg_s = []
    bd = Backdrop("stripes"); bd.show()
    for _ in range(6): app.processEvents()
    s_shot = grab_screen(); bd.close()
    bd = Backdrop("solid"); bd.show()
    for _ in range(6): app.processEvents()
    g_shot = grab_screen(); bd.close()
    for pt in global_pts:
        a = s_shot.pixelColor(*pt); b = g_shot.pixelColor(*pt)
        bg_s.append(abs(a.red() - b.red()) + abs(a.green() - b.green()) + abs(a.blue() - b.blue()))

    pairs = [(dw, bs) for dw, bs in zip(diffs_win, bg_s) if bs > 20]
    t = statistics.median([dw / bs for dw, bs in pairs]) if pairs else 0.0
    print(f"{theme:<8} 透过率 ≈ {t*100:4.1f}%   窗口差值 {diffs_win} / 底色差值 {bg_s}")
    win.ball.hide(); win.tray.hide(); win.close()
    return t


t_laser = measure("laser")
t_morandi = measure("morandi")
print("\n真实透过率：镭射 %.0f%% / 莫兰迪 %.0f%%" % (t_laser * 100, t_morandi * 100))
assert t_morandi > t_laser + 0.06, "莫兰迪没有明显更透"
assert t_morandi > 0.08, "莫兰迪透过率太低，玻璃感立不住"
print("✅ 莫兰迪是实打实的半透明玻璃（背景会透上来），镭射基本不透")
