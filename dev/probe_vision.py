# -*- coding: utf-8 -*-
"""探测: DeepSeek 是否支持 vision 模型读题"""
import base64, io, os, sys, json, requests
from PIL import Image, ImageDraw, ImageFont

W, H = 700, 260
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
fp = "C:/Windows/Fonts/msyh.ttc"
f = ImageFont.truetype(fp, 26)
lines = [
    "7. 已知函数 f(x)=x^3-3x+1，求 f(x) 在区间 [-2, 2] 上的最大值与最小值。",
    "8. 阅读下面文字，回答问题：",
    "   “落霞与孤鹜齐飞，秋水共长天一色”出自哪篇文章？作者是谁？",
]
y = 24
for ln in lines:
    d.text((24, y), ln, fill="black", font=f)
    y += 70
img.save("probe.png")

b = io.BytesIO(); img.save(b, format="PNG")
b64 = base64.b64encode(b.getvalue()).decode()
key = os.environ["HERMES_CUSTOM_API_DEEPSEEK_COM_API_KEY"]

for model in ["deepseek-v4-flash-vision-exp", "deepseek-v4-flash"]:
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "读出图中全部文字，原样输出。"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
            ],
        }],
        "max_tokens": 500,
    }
    try:
        r = requests.post("https://api.deepseek.com/chat/completions",
                          headers={"Authorization": "Bearer " + key,
                                   "Content-Type": "application/json"},
                          json=payload, timeout=90)
        print("==", model, r.status_code)
        print(r.text[:800])
    except Exception as e:
        print("==", model, "ERR", e)
