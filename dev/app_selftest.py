# -*- coding: utf-8 -*-
"""端到端自测: 真实抓屏 -> 浮层选区 -> 裁剪 -> 视觉模型读题 (不经过主窗口)"""
import os, sys, ctypes, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
from PySide6.QtCore import QRect, QPoint, Qt, QTimer
import requests
import souti

app = QApplication(sys.argv)

# ---- 1) 抓整个虚拟桌面（与程序内同一函数）
canvas, scale, vg = souti.grab_virtual_desktop()
print("canvas", canvas.width(), canvas.height(), "scale", scale, "vg", vg)
lut = lambda i: int(i * 255 / 255)
# 亮度统计，确认不是黑图
small = canvas.scaled(320, 200, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
vals = []
for y in range(small.height()):
    for x in range(small.width()):
        c = small.pixelColor(x, y)
        vals.append((c.red() + c.green() + c.blue()) / 3)
print("grab mean brightness: %.1f  (近黑占比 %.1f%%)" % (sum(vals)/len(vals), 100*sum(1 for v in vals if v < 12)/len(vals)))
assert sum(vals)/len(vals) > 40, "抓屏结果是黑的，功能不可用！"

# ---- 2) 模拟一次框选: 逻辑坐标 (240,260)-(1180,700)，走与鼠标完全相同的裁剪代码
p0, p1 = QPoint(240, 260), QPoint(1180, 700)
sel = QRect(p0, p1).normalized()
src = QRect(int(sel.x()*scale), int(sel.y()*scale), int(sel.width()*scale), int(sel.height()*scale))
crop = canvas.copy(src)
crop.save("e2e_crop.png")
print("selection", sel, "-> source", src, "crop", crop.width(), "x", crop.height())
assert crop.width() == int(sel.width()*scale), "裁剪缩放不对"

# ---- 3) 浮层本身画得对不对（暗化 + 提示文字 + 选区内提亮）
cat = souti.RegionCatcher()
cat.show()
cat.p0, cat.p1 = p0, p1
cat.repaint()
app.processEvents()
cat.grab().save("e2e_overlay.png")
cat.close()
print("overlay grabbed")

# ---- 4) 把真实裁剪图发给模型，看能不能读出你屏幕上的内容
cfg = souti.load_config()
key, _ = souti.resolve_api_key(cfg)
b64, mime = souti.encode_image(crop)
t = souti.AskThread(cfg, key, [{"role": "user", "content": [
    {"type": "text", "text": "请识别图中题目并解答（按系统要求的格式）。"},
    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}]}])
buf = []
t.chunk.connect(lambda s: buf.append(s))
t.done.connect(lambda text, u: print("\n=== DONE", u.get("total_tokens") if u else "", "==="))
t.failed.connect(lambda m: print("\n=== FAILED ===\n", m))
t0 = time.time()
t.run()
print("elapsed %.1fs" % (time.time() - t0))
print("".join(buf))
