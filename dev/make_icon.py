# -*- coding: utf-8 -*-
"""生成程序图标 icon.ico：深色圆角方块 + 青色准星（和框选光标一致）"""
import os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 512
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# 底板：深色圆角方块 + 描边
pad, r = 24, 96
d.rounded_rectangle([pad, pad, S - pad, S - pad], radius=r, fill=(22, 25, 32, 255),
                    outline=(80, 210, 255, 230), width=8)

c = S // 2
cyan = (80, 235, 255, 255)
white = (255, 255, 255, 255)

# 十字线（留出中心缺口）
gap, end = 34, 196
for a, b in [((c - end, c), (c - gap, c)), ((c + gap, c), (c + end, c)),
             ((c, c - end), (c, c - gap)), ((c, c + gap), (c, c + end))]:
    d.line([a, b], fill=cyan, width=14)

# 中心圆环 + 白点
d.ellipse([c - 62, c - 62, c + 62, c + 62], outline=cyan, width=14)
d.ellipse([c - 16, c - 16, c + 16, c + 16], fill=white)

# 四角刻度
for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
    d.line([(c + dx * 150, c + dy * 96), (c + dx * 196, c + dy * 96)], fill=cyan, width=14)

out = os.path.join(HERE, "icon.ico")
img.save(out, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
img.resize((256, 256), Image.LANCZOS).save(os.path.join(HERE, "icon.png"))
print("saved", out, os.path.getsize(out), "bytes")
