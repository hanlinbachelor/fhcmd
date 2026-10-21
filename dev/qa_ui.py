# -*- coding: utf-8 -*-
"""把指定截图发给视觉模型做界面质检: python qa_ui.py 图片1 [图片2 ...]"""
import os, sys, base64
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
import requests, souti

app = QApplication(sys.argv)
cfg = souti.load_config()
key, _ = souti.resolve_api_key(cfg)

PROMPT = ("这些是我自己写的 Windows 桌面浮窗程序（深色小窗，用来截图搜题）的截图，请做纯界面质量检查，"
          "逐张编号回答：1) 中文有没有乱码/方框/缺字？2) 有没有文字被裁切、控件重叠、按钮挤成一团、异常的空白大块？"
          "3) 配色对比度够不够（暗底上的字看不清就算问题）？4) 一眼看去排版是否整齐。"
          "只报问题，没问题就写“无”。另外用一句话说每张图整体看起来像什么。")

for p in sys.argv[1:]:
    img = QImage(p)
    b64, mime = souti.encode_image(img)
    payload = {"model": cfg["model"], "max_tokens": 2500,
               "messages": [{"role": "user", "content": [
                   {"type": "text", "text": PROMPT + f"\n（图：{os.path.basename(p)}，{img.width()}x{img.height()}）"},
                   {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}]}]}
    r = requests.post("https://api.deepseek.com/chat/completions",
                      headers={"Authorization": "Bearer " + key}, json=payload, timeout=180)
    j = r.json()
    m = j["choices"][0]["message"]
    print("=" * 60)
    print(os.path.basename(p), r.status_code)
    print(m.get("content") or "(只回了推理)\n" + (m.get("reasoning_content") or ""))
