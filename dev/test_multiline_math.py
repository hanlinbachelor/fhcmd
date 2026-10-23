# -*- coding: utf-8 -*-
"""复现：跨行 $...$ 公式为什么没渲染"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

CASES = [
    "多行 $\\frac{1+\\tan x}{1+\\sin x}\n=1+\\frac{\\tan x-\\sin x}{1+\\sin x}\n=1+\\frac{x^3}{2}+o(x^3).$ 结束",
    "单行 $\\frac{1+\\tan x}{1+\\sin x}=1+\\frac{x^3}{2}$ 结束",
    "带竖线 $\\left.\\frac{x^3}{3}\\right|_0^1=\\frac13$",
    "裸多行：\n\\frac{1+\\tan x}{1+\\sin x}\n=1+\\frac{x^3}{2}",
]

for i, text in enumerate(CASES, 1):
    html = souti.rich_html(text, "#2A2F26", 12.0)
    imgs = html.count("<img")
    raw = "\\" in html
    print(f"[{i}] img={imgs} 残留反斜杠={raw}")
    if raw:
        # 打印残留片段
        import re
        for m in re.finditer(r"[^<>]{0,40}\\\\[a-zA-Z]+[^<>]{0,40}", html):
            print("     残留:", m.group(0).replace("\n", "⏎")[:90])
            break
    print("     _MATH_RE pattern:", souti._MATH_RE.pattern.replace("\\\\", "\\"))
