# -*- coding: utf-8 -*-
"""给每个版本建 GitHub Release 并上传安装包附件（走 api/uploads.github.com）"""
import json
import os
import sys
from pathlib import Path

import time
import requests

APP = Path(__file__).resolve().parent.parent
CANDIDATES = [
    Path(os.path.expandvars(r"%LOCALAPPDATA%\hermes\secrets\github_fhcmd_token.txt")),
    Path(os.path.expandvars(r"%LOCALAPPDATA%\Temp\gh_token.txt")),
]


def get_token():
    import re
    for p in CANDIDATES:
        if not p.exists():
            continue
        raw = p.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"(ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})", raw)
        if m:
            return m.group(1)
    sys.exit("没找到令牌（%LOCALAPPDATA%\\hermes\\secrets\\github_fhcmd_token.txt）")


TOK = get_token()
OWNER, REPO = "hanlinbachelor", "fhcmd"
H = {"Authorization": f"Bearer {TOK}", "Accept": "application/vnd.github+json",
     "X-GitHub-Api-Version": "2022-11-28"}
API = f"https://api.github.com/repos/{OWNER}/{REPO}"

vers = json.loads((APP / "site" / "versions.json").read_text(encoding="utf-8"))
names = vers.get("display_names", {})

for v in vers["versions"]:
    tag = v["version"]
    file = v["file"]
    cands = [APP / "dist" / "pkgs" / file, APP / "site" / "releases" / file]
    path = next((p for p in cands if p.exists()), cands[0])
    body = (v.get("notes") or "").strip()
    body += ("\n\n---\n"
             "**安装**：下载下面的 zip → 解压 → 双击 `启动反谋财害命器.bat`；"
             "首次运行会弹设置窗，填自己的接口地址、模型和 API Key。\n\n"
             "要求：Windows 10/11 + Python 3.11（装一次）")

    # 1) 建/取 release
    r = requests.post(f"{API}/releases", headers=H, timeout=60, json={
        "tag_name": tag, "name": f"{tag}", "body": body,
        "target_commitish": "main", "draft": False, "prerelease": False,
    })
    if r.status_code == 201:
        rel = r.json()
        print(f"✅ 创建 Release {tag}")
    elif r.status_code == 422:
        rel = requests.get(f"{API}/releases/tags/{tag}", headers=H, timeout=60).json()
        print(f"ℹ️ Release {tag} 已存在")
    else:
        print(f"❌ {tag} 创建失败 {r.status_code}: {r.text[:200]}")
        continue

    # 2) 传附件（已存在则跳过）
    assets = {a["name"] for a in rel.get("assets", [])}
    if file in assets:
        print(f"   · 附件已存在，跳过")
        continue
    if not path.exists():
        print(f"   ⚠ 本地缺文件 {path}")
        continue
    url = f"https://uploads.github.com/repos/{OWNER}/{REPO}/releases/{rel['id']}/assets"
    ok = False
    for attempt in range(1, 4):
        try:
            with open(path, "rb") as fh:
                up = requests.post(url, headers={**H, "Content-Type": "application/zip"},
                                   params={"name": file}, data=fh, timeout=900)
            if up.status_code == 201:
                a = up.json()
                print(f"   ✅ 附件 {a['name']} {a['size']} 字节")
                ok = True
                break
            print(f"   ⚠ 第 {attempt} 次失败 {up.status_code}: {up.text[:160]}")
        except Exception as e:
            print(f"   ⚠ 第 {attempt} 次网络异常: {e}")
        time.sleep(5)
    if not ok:
        print("   ❌ 附件上传最终失败")

# 3) 汇总
print("\n=== 当前 Releases ===")
for r in requests.get(f"{API}/releases", headers=H, timeout=60).json():
    assets = ", ".join(f"{a['name']}({a['size']})" for a in r.get("assets", []))
    print(f"{r['tag_name']:8} | {r['html_url']} | {assets}")
