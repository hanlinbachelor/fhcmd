# -*- coding: utf-8 -*-
"""清理线上不可用的版本：删 Release（连附件）+ 删对应 tag，并同步 versions.json

判定标准（依 hb 要求：只留“拿起来就能用”的版本）：
  删 v1.0.0 / v1.1.0 / v1.1.1 / v1.1.2 / v1.2.0  —— 源码包，启动脚本依赖 .venv，用户拿到直接报错
  删 v1.3.0 / v1.3.1                              —— exe 内公式渲染全废（打包漏了 PIL）
  留 v1.2.2（干净的 exe） / v1.3.2（公式可用的 exe）
"""
import json
import os
import re
import sys
from pathlib import Path

import requests

APP = Path(__file__).resolve().parent.parent
OWNER, REPO = "hanlinbachelor", "fhcmd"
DROP = ["v1.0.0", "v1.1.0", "v1.1.1", "v1.1.2", "v1.2.0", "v1.3.0", "v1.3.1"]
KEEP = ["v1.2.2", "v1.3.2"]

tok = re.search(r"ghp_[A-Za-z0-9_]{20,}",
                Path(os.path.expandvars(r"%LOCALAPPDATA%\hermes\secrets\github_fhcmd_token.txt")).read_text()).group(0)
H = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"}

rels = {r["tag_name"]: r for r in requests.get(
    f"https://api.github.com/repos/{OWNER}/{REPO}/releases", headers=H, timeout=40).json()}

for tag in DROP:
    r = rels.get(tag)
    if r:
        d = requests.delete(f"https://api.github.com/repos/{OWNER}/{REPO}/releases/{r['id']}", headers=H, timeout=60)
        print(f"删除 Release {tag}: {d.status_code}")
    t = requests.delete(f"https://api.github.com/repos/{OWNER}/{REPO}/git/refs/tags/{tag}", headers=H, timeout=60)
    print(f"删除 tag     {tag}: {t.status_code}")

# 同步本地站点清单
vs = json.loads((APP / "site" / "versions.json").read_text(encoding="utf-8"))
before = [v["version"] for v in vs["versions"]]
vs["versions"] = [v for v in vs["versions"] if v["version"] in KEEP]
if vs["versions"]:
    latest = sorted(vs["versions"], key=lambda v: [int(x) for x in v["version"].lstrip("v").split(".")])[-1]
    vs["latest"] = latest["version"]
for k in list(vs.get("display_names", {})):
    file_of = {v["file"] for v in vs["versions"]}
    if k not in file_of:
        vs["display_names"].pop(k, None)
(APP / "site" / "versions.json").write_text(json.dumps(vs, ensure_ascii=False, indent=2), encoding="utf-8")
print("清单:", before, "->", [v["version"] for v in vs["versions"]], "latest =", vs["latest"])
