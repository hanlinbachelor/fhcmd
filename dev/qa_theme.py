# -*- coding: utf-8 -*-
"""主题目检: 用视觉模型检查两套外观的观感（低饱和/玻璃质感/对比度/乱码）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
import requests, souti

app = QApplication(sys.argv)
cfg = souti.load_config()
key, _ = souti.resolve_api_key(cfg)

PROMPT = """这些是我做的同一个桌面浮窗程序的几套外观截图（深色小卡片：标题栏+正文区+输入框）。
第一张是「镭射」风格（青蓝霓虹/深空黑），第二三张是「莫兰迪 · 液态玻璃」风格（低饱和灰调+半透明+顶部高光+内缘亮边）。

请针对每张依次只回答这 5 点，简短、结论式，不要长篇推理：
1) 文字有没有乱码/方框/缺字？有没有被裁切或控件重叠？
2) 暗底上的字对比度够不够看？（正文、次要灰字、输入框占位文字分开说）
3) 看着像不像「低饱和莫兰迪色系」？
4) 有没有「玻璃/液态玻璃」的观感（半透明、顶部亮边、边缘高光）？还是像普通实心深色块？
5) 这套配色下最容易显脏/显廉价的地方在哪？给一句改进建议（只一句）。
最后用一句话分别概括每张图的整体气质。"""

paths = sys.argv[1:]
imgs = []
parts = [{"type": "text", "text": PROMPT}]
for p in paths:
    img = QImage(p)
    b64, mime = souti.encode_image(img)
    parts.append({"type": "text", "text": os.path.basename(p)})
    parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})

r = requests.post("https://api.deepseek.com/chat/completions",
                  headers={"Authorization": "Bearer " + key},
                  json={"model": cfg["model"], "max_tokens": 3000,
                        "messages": [{"role": "user", "content": parts}]},
                  timeout=240)
j = r.json()
m = j["choices"][0]["message"]
print(m.get("content") or m.get("reasoning_content"))
