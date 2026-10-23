# -*- coding: utf-8 -*-
"""通过 api.github.com 发布：增量上传（只传内容变了的文件）→ 一次提交 → 开启 Pages

用法:  python gh_publish.py [token文件] [仓库名]

为什么要增量：仓库里有几十 MB 的安装包，每次都全量上传会被网络/GitHub 掐断（502/连接重置）。
做法：对比远端 tree 与本地 HEAD 的 blob sha，相同的直接复用 sha，不再上传内容。
"""
import base64
import os
import subprocess
import sys
from pathlib import Path

import requests

APP = Path(__file__).resolve().parent.parent
DEFAULT_TOKEN = Path(os.path.expandvars(
    r"%LOCALAPPDATA%\hermes\secrets\github_fhcmd_token.txt"))
TOKEN_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TOKEN
REPO = sys.argv[2] if len(sys.argv) > 2 else "fhcmd"
API = "https://api.github.com"
OWNER = None
HDRS = {}


def call(method, path, **kw):
    r = requests.request(method, API + path, headers=HDRS, timeout=120, **kw)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
    return r.json() if r.text.strip() else {}


def read_token():
    import re
    for p in [TOKEN_FILE, DEFAULT_TOKEN]:
        if p.exists():
            m = re.search(r"(ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})",
                          p.read_text(encoding="utf-8", errors="ignore"))
            if m:
                return m.group(1)
    sys.exit(f"没找到令牌：{DEFAULT_TOKEN}")


def local_blobs() -> dict:
    """本地 HEAD 里每个文件的 blob sha（git 自己算，和 GitHub 一致）"""
    out = subprocess.run(["git", "-C", str(APP), "ls-tree", "-r", "HEAD"],
                         capture_output=True, text=True, encoding="utf-8").stdout
    res = {}
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        sha = meta.split()[2]
        res[path] = sha
    return res


def main():
    global OWNER
    token = read_token()
    HDRS.update({"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28"})
    me = call("GET", "/user")
    OWNER = me["login"]
    print(f"✅ 登录：{OWNER}")

    try:
        repo = call("POST", "/user/repos", json={
            "name": REPO, "private": False, "auto_init": False,
            "description": "反谋财害命器 · 截图搜题浮窗（版本下载 + 源码）"})
        print("✅ 仓库已创建")
    except RuntimeError as e:
        if "already exists" not in str(e):
            raise
        repo = call("GET", f"/repos/{OWNER}/{REPO}")
        print("ℹ️ 仓库已存在，复用")

    # 保证有 main 分支
    try:
        head = call("GET", f"/repos/{OWNER}/{REPO}/git/ref/heads/main")
        remote_sha = head["object"]["sha"]
    except RuntimeError:
        call("PUT", f"/repos/{OWNER}/{REPO}/contents/.gitkeep",
             json={"message": "init", "content": base64.b64encode(b"init\n").decode()})
        head = call("GET", f"/repos/{OWNER}/{REPO}/git/ref/heads/main")
        remote_sha = head["object"]["sha"]
        print("· 已建初始提交")

    # 远端已有文件的 sha（用于跳过未变内容）
    tree = call("GET", f"/repos/{OWNER}/{REPO}/git/trees/{remote_sha}?recursive=1")
    remote = {t["path"]: t["sha"] for t in tree.get("tree", []) if t["type"] == "blob"}

    local = local_blobs()
    entries, uploaded, reused = [], 0, 0
    for path, sha in local.items():
        f = APP / path
        if not f.exists():
            continue
        if remote.get(path) == sha:
            entries.append({"path": path, "mode": "100644", "type": "blob", "sha": sha})
            reused += 1
            continue
        data = f.read_bytes()
        try:
            text = data.decode("utf-8")
            entries.append({"path": path, "mode": "100644", "type": "blob", "content": text})
        except UnicodeDecodeError:
            new_sha = call("POST", f"/repos/{OWNER}/{REPO}/git/blobs", json={
                "content": base64.b64encode(data).decode(), "encoding": "base64"})["sha"]
            entries.append({"path": path, "mode": "100644", "type": "blob", "sha": new_sha})
        uploaded += 1
    print(f"· 文件 {len(entries)} 个：新上传 {uploaded}，复用 {reused}")
    if uploaded == 0 and len(entries) == len(remote):
        print("✅ 远端已是最新，无需提交")
    else:
        v = subprocess.run(["git", "-C", str(APP), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True).stdout.strip()
        msg = f"sync {v}: 反谋财害命器（截图搜题浮窗 + 版本下载站）"
        t = call("POST", f"/repos/{OWNER}/{REPO}/git/trees", json={"tree": entries})
        c = call("POST", f"/repos/{OWNER}/{REPO}/git/commits",
                 json={"message": msg, "tree": t["sha"], "parents": [remote_sha]})
        call("PATCH", f"/repos/{OWNER}/{REPO}/git/refs/heads/main",
             json={"sha": c["sha"], "force": True})
        print(f"✅ 已提交 {c['sha'][:10]}：{msg}")

    # Pages（site/ 不在允许的 / 或 /docs 里 → 用 Actions 工作流发布）
    try:
        call("GET", f"/repos/{OWNER}/{REPO}/pages")
    except RuntimeError:
        try:
            call("POST", f"/repos/{OWNER}/{REPO}/pages", json={"build_type": "workflow"})
            print("✅ Pages 已启用（workflow）")
        except RuntimeError as e:
            print("⚠ Pages 启用失败：", e)

    print(f"REPO_URL=https://github.com/{OWNER}/{REPO}")


if __name__ == "__main__":
    main()
