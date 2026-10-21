# -*- coding: utf-8 -*-
"""提交前安全检查：暂存的每个文件里都不能出现真实 API key"""
import os
import subprocess
import sys

REPO = r"D:\hermes\261020搜题浮窗"
key = os.environ.get("HERMES_CUSTOM_API_DEEPSEEK_COM_API_KEY", "")
assert key, "环境变量里没有 key，无法比对"

out = subprocess.run(["git", "-C", REPO, "diff", "--cached", "--name-only"],
                     capture_output=True, text=True, encoding="utf-8").stdout
files = [f for f in out.splitlines() if f.strip()]
print("待提交文件数:", len(files))

bad = []
for f in files:
    p = os.path.join(REPO, f)
    try:
        txt = open(p, encoding="utf-8", errors="ignore").read()
    except Exception:
        continue
    if key in txt:
        bad.append(f)

print("含真实 key 的文件:", bad or "无 ✅")
# 再顺手扫一遍常见泄漏形态
import re
pat = re.compile(r"sk-[A-Za-z0-9]{16,}")
hits = []
for f in files:
    p = os.path.join(REPO, f)
    if not p.endswith((".py", ".json", ".md", ".bat", ".txt")):
        continue
    try:
        txt = open(p, encoding="utf-8", errors="ignore").read()
    except Exception:
        continue
    if pat.search(txt):
        hits.append(f)
print("形如 sk-xxx 的疑似 key:", hits or "无 ✅")
sys.exit(1 if (bad or hits) else 0)
