# -*- coding: utf-8 -*-
"""真模型问一道极限题，检查答案里是否还有未渲染的 LaTeX"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

cfg = souti.load_config()
key, src = souti.resolve_api_key(cfg)
print("key 来源:", src)
base = cfg["api_base"].rstrip("/") + "/chat/completions"
q = "求极限 lim_{x→0} (1+tan x)/(1+sin x) 的 1/x^3 次方，给出完整推导。按【题目】【答案】【解析】【考点】分段，公式用 $...$ 包起来。"
r = requests.post(base, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                  json={"model": cfg["model"], "max_tokens": 2000, "temperature": 0.2,
                        "messages": [{"role": "user", "content": q}]}, timeout=180)
ans = r.json()["choices"][0]["message"]["content"]
print("\n--- 模型输出前 400 字 ---\n", ans[:400])

secs = souti.split_sections(ans)
print("\n分区:", list(secs.keys()))
total_img = 0
for k, body in secs.items():
    h = souti.rich_html(body, "#2A2F26")
    n = h.count("<img")
    total_img += n
    left = re.findall(r"\$[^$]{0,60}", re.sub(r"<[^>]+>", "", h))
    print(f"  {k}: img={n}  残留美元符号片段={len(left)}")
    for s in left[:2]:
        print("     ", s.replace("\n", "⏎")[:70])
print("总图片:", total_img)
