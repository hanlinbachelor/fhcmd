# -*- coding: utf-8 -*-
"""看图：把本地图片发给视觉模型，只输出文字（当我的“眼睛”）"""
import base64
import json
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import souti

cfg = souti.load_config()
key, src = souti.resolve_api_key(cfg)
if not key:
    sys.exit("没有 API key")

path = sys.argv[1]
question = sys.argv[2] if len(sys.argv) > 2 else "请描述这张图片，并把其中所有可见文字完整读出来。"
with open(path, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
ext = os.path.splitext(path)[1].lower().lstrip(".") or "jpeg"
mime = "image/png" if ext == "png" else "image/jpeg"

r = requests.post(
    cfg["api_base"].rstrip("/") + "/chat/completions",
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    json={
        "model": cfg["model"],
        "max_tokens": 4000,
        "temperature": 0.1,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        ]}],
    },
    timeout=180,
)
r.raise_for_status()
msg = r.json()["choices"][0]["message"]
print(msg.get("content") or msg.get("reasoning_content") or "(空)")
