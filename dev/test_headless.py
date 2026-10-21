# -*- coding: utf-8 -*-
"""无界面测试: 造一张题目图 -> 走完 截图编码 -> 视觉模型 -> 输出 全链路"""
import os, sys, time
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage

app = QApplication(sys.argv)
import souti

# ---- 造题
img = Image.new("RGB", (1000, 320), "white")
d = ImageDraw.Draw(img)
f = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 26)
lines = [
    "1. 已知函数 f(x)=x^3-3x+1，求 f(x) 在闭区间 [-2, 2] 上的最大值与最小值。",
    "",
    "2. 设 A={1,2,3}，B={2,3,4}，则 A∩B 的子集个数为（  ）",
    "   A. 2    B. 3    C. 4    D. 8",
    "",
    "3. “落霞与孤鹜齐飞，秋水共长天一色”出自哪篇文章？作者是谁？",
]
y = 20
for ln in lines:
    d.text((20, y), ln, fill="black", font=f)
    y += 44
img.save("test_question.png")

# PIL -> QImage
img = img.convert("RGB")
qimg = QImage(img.tobytes(), img.width, img.height, img.width * 3, QImage.Format_RGB888)

cfg = souti.load_config()
key, src = souti.resolve_api_key(cfg)
print("key source:", src, "len:", len(key), "model:", cfg["model"])
assert key, "没有 API key"

b64, mime = souti.encode_image(qimg)
print("image b64 len:", len(b64), mime)

msgs = [{"role": "user", "content": [
    {"type": "text", "text": "请识别图中题目并解答（按系统要求的格式）。"},
    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
]}]

buf = []
t = souti.AskThread(cfg, key, msgs)
t.chunk.connect(lambda s: buf.append(s))
t.done.connect(lambda text, usage: print("\n=== DONE ===\nusage:", usage))
t.failed.connect(lambda m: print("\n=== FAILED ===\n", m))
t0 = time.time()
t.run()          # 直接同线程跑，省掉事件循环
out = "".join(buf)
print("elapsed %.1fs, chars=%d" % (time.time() - t0, len(out)))
print("=== OUTPUT ===")
print(out if out else "(空)")
