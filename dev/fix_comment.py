# -*- coding: utf-8 -*-
"""修掉 plain_tex 里被转义破坏的注释行（\\right 里的 \\r 变成了回车）"""
import io
import re

p = r"D:\hermes\261020搜题浮窗\souti.py"
lines = io.open(p, encoding="utf-8", newline="").read().split("\n")
out = []
skip_next = False
for i, ln in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
    if "先去掉" in ln and "left" in ln:
        out.append("    # 先去掉 left/right/big 系列，否则后面 le→≤ 的替换会把 left 啃成 ≤ft")
        skip_next = True
        continue
    out.append(ln)
txt = "\n".join(out)
io.open(p, "w", encoding="utf-8", newline="").write(txt)
print("fixed")
