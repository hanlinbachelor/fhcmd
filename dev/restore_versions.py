# -*- coding: utf-8 -*-
"""恢复被删的版本：小包从 git 历史还原并重发 Release；大包只保留“已下架”占位说明"""
import json
import os
import re
import subprocess
from pathlib import Path

import requests

APP = Path(__file__).resolve().parent.parent
OWNER, REPO = "hanlinbachelor", "fhcmd"
SMALL = ["v1.0.0", "v1.1.0", "v1.1.1", "v1.1.2"]          # 源码包，几十 KB，直接重发
BIG_OFF = ["v1.2.0", "v1.2.1", "v1.3.0", "v1.3.1"]        # 大包已下架，只留条目

tok = re.search(r"ghp_[A-Za-z0-9_]{20,}",
                Path(os.path.expandvars(r"%LOCALAPPDATA%\hermes\secrets\github_fhcmd_token.txt")).read_text()).group(0)
H = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"}


def restore_zip(name: str) -> Path:
    """从 git 历史里把某个 zip 取出来"""
    dst = APP / "site" / "releases" / name
    if dst.exists():
        return dst
    commit = subprocess.run(["git", "log", "--all", "--diff-filter=A", "--format=%H", "-1", "--", f"site/releases/{name}"],
                            cwd=APP, capture_output=True, text=True).stdout.strip()
    if not commit:
        raise SystemExit(f"git 历史里找不到 {name}")
    blob = subprocess.run(["git", "show", f"{commit}:site/releases/{name}"], cwd=APP, capture_output=True).stdout
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(blob)
    print(f"还原 {name} ({len(blob)} 字节)")
    return dst


def ensure_release(tag: str, body: str) -> dict:
    r = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/{tag}", headers=H, timeout=30)
    if r.status_code == 200:
        return r.json()
    c = requests.post(f"https://api.github.com/repos/{OWNER}/{REPO}/releases", headers=H,
                      json={"tag_name": tag, "name": tag, "body": body, "target_commitish": "main"}, timeout=60)
    c.raise_for_status()
    print(f"重建 Release {tag}")
    return c.json()


def upload(rel: dict, path: Path):
    if any(a["name"] == path.name for a in rel.get("assets", [])):
        return
    with open(path, "rb") as fh:
        up = requests.post(f"https://uploads.github.com/repos/{OWNER}/{REPO}/releases/{rel['id']}/assets",
                           params={"name": path.name}, headers={**H, "Content-Type": "application/zip"},
                           data=fh, timeout=300)
    print(f"  附件 {path.name}: {up.status_code}")


vers = json.loads((APP / "site" / "versions.json").read_text(encoding="utf-8"))
have = {v["version"]: v for v in vers["versions"]}

for tag in SMALL:
    name = f"fhcmd-{tag}.zip"
    p = restore_zip(name)
    rel = ensure_release(tag, f"{tag}（历史版本）\n\n源码版：需要本机有 Python 3.11+，双击 `启动反谋财害命器.bat` 会自动装依赖。\n最新版请用 v1.3.2（免安装 exe）。")
    upload(rel, p)
    have[tag] = {"version": tag, "file": name, "size": p.stat().st_size,
                 "sha256": __import__("hashlib").sha256(p.read_bytes()).hexdigest(),
                 "notes": f"{tag} 源码版（需 Python）", "status": "历史"}

for tag in BIG_OFF:
    ensure_release(tag, f"{tag}（已下架）\n\n该版本的安装包已下架：exe 内公式渲染失效（打包漏了依赖）。\n请下载 v1.3.2。")
    have[tag] = {"version": tag, "file": f"fhcmd-{tag}.zip", "size": 0, "sha256": "",
                 "notes": "已下架（已知问题）", "status": "已下架", "url": ""}

order = ["v1.0.0", "v1.1.0", "v1.1.1", "v1.1.2", "v1.2.0", "v1.2.1", "v1.2.2",
         "v1.3.0", "v1.3.1", "v1.3.2"]
vers["versions"] = [have[t] for t in order if t in have]
vers["latest"] = "v1.3.2"
(APP / "site" / "versions.json").write_text(json.dumps(vers, ensure_ascii=False, indent=2), encoding="utf-8")
print("时间线:", [v["version"] + ("✓" if v.get("status", "可用") == "可用" else "(" + v.get("status", "") + ")")
                for v in vers["versions"]])
