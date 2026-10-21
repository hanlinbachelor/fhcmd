# -*- coding: utf-8 -*-
"""排查 Pages 开启问题：打印 GET / POST / PUT /pages 的真实返回"""
import json
import sys
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
BASE = "https://api.github.com/repos/hanlinbachelor/fhcmd"

print("--- 令牌权限（响应头）---")
r = requests.get("https://api.github.com/user", headers=H, timeout=30)
print(r.status_code, r.headers.get("x-oauth-scopes"))

for method, path, body in [
    ("GET", "/pages", None),
    ("POST", "/pages", {"source": {"branch": "main", "path": "/site"}, "build_type": "legacy"}),
    ("POST", "/pages", {"source": {"branch": "main", "path": "/site"}}),
]:
    r = requests.request(method, BASE + path, headers=H, json=body, timeout=60)
    print(f"\n{method} {path} body={body} -> {r.status_code}")
    print(r.text[:600])
