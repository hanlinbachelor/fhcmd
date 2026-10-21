# -*- coding: utf-8 -*-
"""量化检查浮层截图: 选区内应亮、选区外应被压暗、提示文字应存在"""
from PIL import Image
import sys, os

path = sys.argv[1] if len(sys.argv) > 1 else "e2e_overlay.png"
im = Image.open(path).convert("RGB")
W, H = im.size
print("size", W, H)

def mean(box):
    r = im.crop(box).convert("L")
    d = list(r.getdata())
    return sum(d) / len(d)

# 逻辑选区 (240,260)-(1180,700)，scale=2 -> 物理 (480,520)-(2360,1400)
inside = mean((700, 700, 1600, 1200))
outside_top = mean((100, 60, 900, 300))
outside_bottom = mean((100, 1450, 900, 1560))
print("选区内亮度 %.1f | 选区外(上) %.1f | 选区外(下) %.1f" % (inside, outside_top, outside_bottom))
print("暗化生效:", outside_top < inside * 0.75, " 选区内保持原亮度:", inside > 120)

# 选区边框: 找 480 列附近的蓝色像素
px = [im.getpixel((480, y)) for y in range(520, 1400, 40)]
bluish = sum(1 for r, g, b in px if b > 180 and b > r + 40)
print("左边框蓝色采样命中 %d/%d" % (bluish, len(px)))

# 提示文字区域 (顶部居中) 是否有亮像素
hint = im.crop((300, 40, 2300, 140)).convert("L")
bright = sum(1 for v in hint.getdata() if v > 170)
print("顶部提示文字亮像素数:", bright)
