# -*- coding: utf-8 -*-
"""从《千里江山图》原图里提取配色（k-means），再据此生成主题色"""
import io
import sys

import numpy as np
import requests
from PIL import Image

URL = ("https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0d/"
       "1c_Wang_Ximeng._A_Thousand_Li_of_Rivers_and_Mountains._%2851%2C3x1191%2C5cm%291113."
       "_%28section%29_Palace_museum%2C_Beijing.jpg/1920px-"
       "1c_Wang_Ximeng._A_Thousand_Li_of_Rivers_and_Mountains._%2851%2C3x1191%2C5cm%291113."
       "_%28section%29_Palace_museum%2C_Beijing.jpg")

r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=90)
r.raise_for_status()
img = Image.open(io.BytesIO(r.content)).convert("RGB")
print("原图:", img.size, len(r.content), "bytes")
img.save(r"D:\hermes\261020搜题浮窗\dev\shots\qianli_source.jpg", quality=92)

small = img.resize((480, max(1, int(480 * img.height / img.width))))
arr = np.asarray(small).reshape(-1, 3).astype(np.float32)

# k-means
k = 10
rng = np.random.default_rng(7)
cent = arr[rng.choice(len(arr), k, replace=False)]
for _ in range(24):
    d = ((arr[:, None, :] - cent[None, :, :]) ** 2).sum(2)
    lab = d.argmin(1)
    for i in range(k):
        m = lab == i
        if m.any():
            cent[i] = arr[m].mean(0)
counts = np.bincount(lab, minlength=k)
order = np.argsort(-counts)

print("\n主要颜色（按占比）:")
rows = []
for i in order:
    c = tuple(int(v) for v in cent[i])
    share = counts[i] / counts.sum() * 100
    rows.append((c, share))
    print(f"  #{c[0]:02X}{c[1]:02X}{c[2]:02X}  {share:5.1f}%")


def sat(c):
    mx, mn = max(c), min(c)
    return 0 if mx == 0 else (mx - mn) / mx


def lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


greens = [c for c, s in rows if c[1] >= c[0] and c[1] > c[2] and sat(c) > 0.12]
blues = [c for c, s in rows if c[2] >= c[1] > c[0] and sat(c) > 0.10]
ochers = [c for c, s in rows if c[0] > c[2] and c[1] > c[2] and sat(c) > 0.2]
print("\n偏绿:", ["#%02X%02X%02X" % c for c in greens])
print("偏蓝:", ["#%02X%02X%02X" % c for c in blues])
print("偏赭:", ["#%02X%02X%02X" % c for c in ochers])
print("最亮:", "#%02X%02X%02X" % max((c for c, s in rows), key=lum))
print("最暗:", "#%02X%02X%02X" % min((c for c, s in rows), key=lum))
