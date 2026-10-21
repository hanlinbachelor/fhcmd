# -*- coding: utf-8 -*-
"""验证设置窗真的在最上层：把屏幕截图里"对话框区域"和对话框自身渲染对比，
   重合率高 => 没被置顶浮窗压住。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtCore import QRect, QTimer, Qt
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
os.makedirs(SHOTS, exist_ok=True)

cfg = souti.load_config()
w = souti.FloatWindow(cfg)
w.move(700, 120)
w.resize(440, 620)
w.show()

result = {}


def check():
    dlg = QApplication.activeModalWidget()
    if dlg is None:
        result["err"] = "没有模态窗"
        app.quit()
        return
    app.processEvents()
    g = dlg.geometry()                      # 逻辑坐标
    dpr = app.primaryScreen().devicePixelRatio()
    screen = app.primaryScreen().grabWindow(0).toImage()
    r = QRect(int(g.x() * dpr), int(g.y() * dpr), int(g.width() * dpr), int(g.height() * dpr))
    area = screen.copy(r)
    dlg_pm = dlg.grab().toImage()

    # 逐点比对（步长 6）
    same = total = 0
    ww, hh = min(area.width(), dlg_pm.width()), min(area.height(), dlg_pm.height())
    for y in range(4, hh - 4, 6):
        for x in range(4, ww - 4, 6):
            a = area.pixelColor(x, y)
            b = dlg_pm.pixelColor(x, y)
            total += 1
            if abs(a.red() - b.red()) + abs(a.green() - b.green()) + abs(a.blue() - b.blue()) < 30:
                same += 1
    ratio = same / max(1, total)
    result.update(dlg_rect=(g.x(), g.y(), g.width(), g.height()), ratio=ratio,
                  topmost=bool(dlg.windowFlags() & Qt.WindowStaysOnTopHint))
    screen.copy(r.adjusted(-30, -30, 30, 30)).save(os.path.join(SHOTS, "settings_dialog.png"))
    dlg.reject()
    app.quit()


QTimer.singleShot(400, w.open_settings)
QTimer.singleShot(1600, check)
app.exec()

w.ball.hide(); w.tray.hide(); w.close()
print("对话框矩形:", result.get("dlg_rect"), "| 置顶标志:", result.get("topmost"))
print("屏幕与对话框内容重合率: %.1f%%" % (result.get("ratio", 0) * 100))
assert result.get("topmost"), "对话框没有 WindowStaysOnTopHint"
assert result.get("ratio", 0) > 0.85, "对话框被遮挡（重合率过低）"
print("✅ 设置窗确实在最上层，没有被浮窗挡住")
