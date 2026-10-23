# -*- coding: utf-8 -*-
"""真 E2E：用真模型答一道数学题，看答案里的公式有没有被渲染成图片"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

cfg = souti.load_config()
key, src = souti.resolve_api_key(cfg)
print("key 来源:", src, "| 模型:", cfg["model"])
assert key, "没有 key，无法做真 E2E"

q = "求 f(x)=x^3-3x+1 在 [-2,2] 上的最大值和最小值，结论用 \\boxed 包起来"
r = requests.post(cfg["api_base"].rstrip("/") + "/chat/completions",
                  headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                  json={"model": cfg["model"], "max_tokens": 1200, "temperature": 0.2,
                        "messages": [{"role": "system", "content": souti.SYSTEM_PROMPT},
                                     {"role": "user", "content": q}]},
                  timeout=120)
print("HTTP", r.status_code)
txt = r.json()["choices"][0]["message"]["content"]
print("---- 模型答案（前 600 字）----")
print(txt[:600])

w = souti.FloatWindow(cfg)
w.show()
w.current_answer = txt
w._present_answer(txt)
app.processEvents()

html = w.view.toHtml()
box = w.answer_box.text()
n_img_body = html.count("<img")
n_img_box = box.count("<img")
print("---- 渲染结果 ----")
print("答案条含公式图:", n_img_box, "| 正文含公式图:", n_img_body)
print("答案条纯文本:", " ".join(box.replace("<", " <").split())[:160])
print("正文里是否还有裸露的 LaTeX 源码:", ("\\frac" in html) or ("\\boxed" in html))

os.makedirs("dev/shots", exist_ok=True)
w.grab().save("dev/shots/e2e_math.png")
print("截图: dev/shots/e2e_math.png")
w.ball.hide(); w.tray.hide(); w.close()

assert n_img_box + n_img_body > 0, "公式一张都没渲染"
print("✅ E2E 通过：真模型答案里的公式被渲染成图片")
