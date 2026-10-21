# -*- coding: utf-8 -*-
"""查看 GitHub Pages 构建状态和最终地址"""
import sys
import time
from pathlib import Path

import requests

tok = ""
for line in Path(r"C:\Users\hanli\AppData\Local\Temp\gh_token.txt").read_text(encoding="utf-8", errors="ignore").splitlines():
    s = line.strip()
    if s.startswith(("ghp_", "github_pat_")):
        tok = s
        break
H = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
     "X-GitHub-Api-Version": "2022-11-28"}
R = "https://api.github.com/repos/hanlinbachelor/fhcmd"

p = requests.get(R + "/pages", headers=H, timeout=30)
print("pages:", p.status_code, p.text[:300])

for i in range(12):
    r = requests.get(R + "/actions/runs?per_page=3", headers=H, timeout=30).json()
    runs = r.get("workflow_runs", [])
    if not runs:
        print("· 还没有工作流运行")
    for w in runs:
        print(f"· run #{w['run_number']} {w['name']} status={w['status']} concl={w['conclusion']}")
    if runs and runs[0]["status"] == "completed":
        break
    time.sleep(10)
