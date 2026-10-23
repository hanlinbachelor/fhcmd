# -*- coding: utf-8 -*-
"""取《千里江山图》全卷缩略图，按“高饱和像素”聚类，得出真正的石青/石绿/赭石/绢底色"""
import io
import json
import os
import urllib.parse

import numpy as np
import requests
from PIL import Image

API = "https://commons.wikimedia.org/w/api.php"
TITLE = "File:王希孟千里江山图卷.png"
r = requests.get(API, params={"action": "query", "titles": TITLE, "prop": "imageinfo",
                             "iiprop": "url|size", "iiurlwidth": 4000, "format": "json"},
                 headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
pg = list(r.json()["query"]["pages"].values())[0]
ii = pg["imageinfo"][0]
url = ii["thumburl"].split("?")[0]
print("原图", ii["width"], "x", ii["height"], "→ 下载 4000px")

resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=180)
resp.raise_for_status()
img = Image.open(io.BytesIO(resp.content)).convert("RGB")
print("缩略图:", img.size, len(resp.content), "bytes")
img.save(r"D:\hermes\261020搜题浮窗\dev\shots\qianli_full.jpg", quality=88)

small = img.resize((1400, max(1, int(1400 * img.height / img.width))), Image.LANCZOS)
a = np.asarray(small).reshape(-1, 3).astype(np.float32)
mx, mn = a.max(1), a.min(1)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
val = mx / 255.0

groups = {
    "石绿(饱和绿)": a[(sat > 0.30) & (val > 0.30) & (a[:, 1] >= a[:, 0]) & (a[:, 1] >= a[:, 2])],
    "石青(饱和蓝)": a[(sat > 0.28) & (val > 0.28) & (a[:, 2] > a[:, 1]) & (a[:, 2] > a[:, 0])],
    "赭石(饱和红黄)": a[(sat > 0.35) & (val > 0.35) & (a[:, 0] > a[:, 1]) & (a[:, 1] > a[:, 2])],
    "绢底(亮而不艳)": a[(val > 0.62) & (sat < 0.22)],
    "墨(暗)": a[(val < 0.28)],
}


def kmeans(px, k=4, iters=25):
    if len(px) < k * 10:
        return []
    rng = np.random.default_rng(5)
    c = px[rng.choice(len(px), k, replace=False)]
    for _ in range(iters):
        d = ((px[:, None, :] - c[None, :, :]) ** 2).sum(2)
        lab = d.argmin(1)
        for i in range(k):
            m = lab == i
            if m.any():
                c[i] = px[m].mean(0)
    cnt = np.bincount(lab, minlength=k)
    return [("#%02X%02X%02X" % tuple(int(v) for v in c[i]), cnt[i] / cnt.sum() * 100)
            for i in np.argsort(-cnt)]


for name, px in groups.items():
    print(f"\n{name}: {len(px)} 像素 ({len(px)/len(a)*100:.1f}%)")
    for hexv, share in kmeans(px):
        print(f"   {hexv}  {share:.0f}%")
