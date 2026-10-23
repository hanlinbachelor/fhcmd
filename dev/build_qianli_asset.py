# -*- coding: utf-8 -*-
"""从《千里江山图》高清扫描里取一张竖向裁切，做成可做背景的宣纸底图 + 提取真实配色"""
import io
import os

import numpy as np
import requests
from PIL import Image, ImageEnhance, ImageFilter

OUT = r"D:\hermes\261020搜题浮窗\assets"
os.makedirs(OUT, exist_ok=True)
API = "https://commons.wikimedia.org/w/api.php"
SECTIONS = [
    "File:1c Wang Ximeng. A Thousand Li of Rivers and Mountains. (51,3x1191,5cm)1113. (section) Palace museum, Beijing.jpg",
    "File:1e Wang Ximeng. A Thousand Li of Rivers and Mountains. (51,3x1191,5cm)1113. (section) Palace museum, Beijing.jpg",
    "File:Wang Ximeng - A Thousand Li of River1.jpg",
]

imgs = []
for title in SECTIONS:
    try:
        r = requests.get(API, params={"action": "query", "titles": title, "prop": "imageinfo",
                                      "iiprop": "url|size", "iiurlwidth": 6000, "format": "json"},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        ii = list(r.json()["query"]["pages"].values())[0]["imageinfo"][0]
        url = ii["thumburl"].split("?")[0]
        data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=180).content
        im = Image.open(io.BytesIO(data)).convert("RGB")
        print("取到", title[:40], im.size, len(data), "bytes")
        imgs.append(im)
        im.save(os.path.join(OUT, f"src_{len(imgs)}.jpg"), quality=90)
    except Exception as e:
        print("失败", title[:40], e)

if not imgs:
    raise SystemExit("一张都没下到")

# 选最“有山有水”的：竖向取中间一块
src = imgs[0]
w, h = src.size
cw = int(h * 0.78)                     # 竖版比例 0.78
x0 = int(w * 0.35)
crop = src.crop((x0, 0, min(w, x0 + cw), h))
print("裁切:", crop.size)

# 做成“旧纸+山水”的柔化底图：降饱和、提亮、轻微模糊
bg = crop.resize((760, int(760 * crop.height / crop.width)), Image.LANCZOS)
bg = ImageEnhance.Color(bg).enhance(0.72)
bg = ImageEnhance.Brightness(bg).enhance(1.16)
bg = ImageEnhance.Contrast(bg).enhance(0.86)
bg = bg.filter(ImageFilter.GaussianBlur(1.1))
bg.save(os.path.join(OUT, "qianli_bg.jpg"), quality=86, optimize=True)
print("底图:", bg.size, os.path.getsize(os.path.join(OUT, "qianli_bg.jpg")), "bytes")

# 从高清原图取真实颜色（只取饱和的矿物色）
small = src.resize((1600, max(1, int(1600 * h / w))), Image.LANCZOS)
a = np.asarray(small).reshape(-1, 3).astype(np.float32)
mx, mn = a.max(1), a.min(1)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
val = mx / 255.0
groups = {
    "石绿": a[(sat > 0.32) & (val > 0.32) & (a[:, 1] >= a[:, 0]) & (a[:, 1] >= a[:, 2])],
    "石青": a[(sat > 0.30) & (val > 0.30) & (a[:, 2] > a[:, 1]) & (a[:, 2] > a[:, 0])],
    "赭石": a[(sat > 0.40) & (val > 0.40) & (a[:, 0] > a[:, 1]) & (a[:, 1] > a[:, 2])],
    "绢底": a[(val > 0.55) & (sat < 0.30)],
}


def km(px, k=3, it=22):
    if len(px) < k * 20:
        return []
    rng = np.random.default_rng(11)
    c = px[rng.choice(len(px), k, replace=False)]
    for _ in range(it):
        d = ((px[:, None, :] - c[None, :, :]) ** 2).sum(2)
        lab = d.argmin(1)
        for i in range(k):
            m = lab == i
            if m.any():
                c[i] = px[m].mean(0)
    cnt = np.bincount(lab, minlength=k)
    return [("#%02X%02X%02X" % tuple(int(v) for v in c[i]), cnt[i] / cnt.sum() * 100) for i in np.argsort(-cnt)]


for name, px in groups.items():
    print(f"\n{name}: {len(px)/len(a)*100:.1f}% 像素")
    for hexv, share in km(px):
        print(f"   {hexv}  {share:.0f}%")
