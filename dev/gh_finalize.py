# -*- coding: utf-8 -*-
"""把 GitHub 令牌存到受限文件，并把 v1.1.2 设为 Latest release"""
import os
import re
import subprocess
import sys
from pathlib import Path

import requests

TEMP = Path(os.path.expandvars(r"%LOCALAPPDATA%\Temp\gh_token.txt"))
SECRET = Path(os.path.expandvars(r"%LOCALAPPDATA%\hermes\secrets\github_fhcmd_token.txt"))
OWNER, REPO = "hanlinbachelor", "fhcmd"

raw = TEMP.read_text(encoding="utf-8", errors="ignore")
m = re.search(r"(ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})", raw)
if not m:
    sys.exit("❌ 没在文件里找到令牌")
tok = m.group(1)

H = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
     "X-GitHub-Api-Version": "2022-11-28"}

me = requests.get("https://api.github.com/user", headers=H, timeout=30)
if me.status_code != 200:
    sys.exit(f"❌ 令牌无效：{me.status_code} {me.text[:120]}")
login = me.json()["login"]
scopes = me.headers.get("x-oauth-scopes", "")
print(f"✅ 令牌有效：{login}（权限 {scopes}）")

# 1) 存到受限目录
SECRET.parent.mkdir(parents=True, exist_ok=True)
SECRET.write_text(tok + "\n", encoding="utf-8")
subprocess.run(["icacls", str(SECRET.parent), "/inheritance:r",
                "/grant:r", f"{os.environ['USERNAME']}:(OI)(CI)F"],
               capture_output=True)
print(f"✅ 已保存到 {SECRET}（仅本账户可读）")

# 2) 把 v1.1.2 设为 Latest
rel = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/v1.1.2",
                   headers=H, timeout=30).json()
r = requests.patch(f"https://api.github.com/repos/{OWNER}/{REPO}/releases/{rel['id']}",
                   headers=H, json={"make_latest": "true"}, timeout=30)
print("设置 Latest:", r.status_code, r.json().get("tag_name"))
chk = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest",
                   headers=H, timeout=30).json()
print("✅ 现在 /releases/latest =", chk["tag_name"])

# 3) 清理临时文件
TEMP.unlink(missing_ok=True)
print("✅ 临时文件已删除")
