# -*- coding: utf-8 -*-
"""用真实模型原文（last_answer.txt）测每条公式的渲染结果"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

raw = io.open(r"D:\hermes\261020搜题浮窗\last_answer.txt", encoding="utf-8").read()
raw = raw.split("\n", 1)[1] if raw.startswith("=====") else raw

secs = souti.split_sections(raw)
print("分区:", list(secs.keys()))
for k, body in secs.items():
    html = souti.rich_html(body, "#2A2F26")
    n = html.count("<img")
    plain = re.sub(r"<[^>]+>", " ", html)
    leaks = re.findall(r"\\[a-zA-Z]{2,}", plain)
    print(f"\n[{k}] img={n} 残留命令={len(leaks)}")
    if leaks:
        print("   残留:", leaks[:6])

print("\n--- 逐条公式 ---")
for m in souti._MATH_RE.finditer(raw):
    expr = m.group(1) or m.group(2) or m.group(3) or m.group(4) or ""
    r = souti.render_math(expr, "#2A2F26")
    print(("OK  " if r else "FAIL"), repr(expr.strip()[:60]))
print("\nmath_fail.log:")
try:
    print(io.open(r"D:\hermes\261020搜题浮窗\math_fail.log", encoding="utf-8").read()[-1200:])
except Exception as e:
    print("(无)", e)
