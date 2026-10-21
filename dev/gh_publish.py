# -*- coding: utf-8 -*-
"""通过 api.github.com 发布：建仓库 → 单提交上传全部文件 → 开启 Pages

用法:  python gh_publish.py <token文件路径> [仓库名]
说明:  github.com 网页/OAuth 被网络阻断，但 api.github.com 可用，
       因此用 REST API 完成（不依赖 git push）。
"""
import base64
import json
import sys
import time
from pathlib import Path

import requests

APP = Path(__file__).resolve().parent.parent
TOKEN_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\Users\hanli\AppData\Local\Temp\gh_token.txt")
REPO = sys.argv[2] if len(sys.argv) > 2 else "fhcmd"
API = "https://api.github.com"
HDRS = {}


def call(method, path, **kw):
    r = requests.request(method, API + path, headers=HDRS, timeout=60, **kw)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
    return r.json() if r.text.strip() else {}


def main():
    raw = TOKEN_FILE.read_text(encoding="utf-8", errors="ignore")
    token = ""
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith(("ghp_", "github_pat_", "gho_", "ghu_")):
            token = s
            break
    if not token:
        token = raw.strip()
    assert token.startswith(("ghp_", "github_pat_", "gho_", "ghu_")), \
        f"没在文件里找到令牌（现在内容是 {len(raw)} 字符）"
    HDRS.update({"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28"})

    me = call("GET", "/user")
    owner = me["login"]
    print(f"✅ 登录成功：{owner}")

    # 1) 建仓库（已存在就复用）
    try:
        repo = call("POST", "/user/repos", json={
            "name": REPO, "private": False, "auto_init": False,
            "description": "反谋财害命器 · 截图搜题浮窗（版本下载 + 源码）",
        })
        print(f"✅ 仓库已创建：{repo['full_name']}")
    except RuntimeError as e:
        if "already exists" not in str(e):
            raise
        repo = call("GET", f"/repos/{owner}/{REPO}")
        print(f"ℹ️ 仓库已存在，复用：{repo['full_name']}")

    # 2) 空仓库没法建 blob（409 Git Repository is empty）→ 先用 Contents API 打一个初始提交
    try:
        call("GET", f"/repos/{owner}/{REPO}/git/ref/heads/main")
        print("ℹ️ main 分支已存在")
    except RuntimeError:
        call("PUT", f"/repos/{owner}/{REPO}/contents/.gitkeep",
             json={"message": "init", "content": base64.b64encode(b"init\n").decode()})
        print("· 已创建初始提交（.gitkeep）")

    # 3) 收集要上传的文件（以 git 记录为准）
    import subprocess
    out = subprocess.run(["git", "-C", str(APP), "ls-files"], capture_output=True, text=True,
                         encoding="utf-8").stdout
    paths = [p for p in out.splitlines() if p.strip()]
    print(f"· 待上传 {len(paths)} 个文件")

    entries, blobs = [], 0
    for p in paths:
        f = APP / p
        if not f.exists():
            continue
        data = f.read_bytes()
        is_text = True
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            is_text = False
        if is_text:
            entries.append({"path": p, "mode": "100644", "type": "blob", "content": text})
        else:
            sha = call("POST", f"/repos/{owner}/{REPO}/git/blobs", json={
                "content": base64.b64encode(data).decode(), "encoding": "base64"})["sha"]
            entries.append({"path": p, "mode": "100644", "type": "blob", "sha": sha})
            blobs += 1
    print(f"· 其中二进制 {blobs} 个已转 blob")

    # 3) 一次性提交
    msg = "v1.1.1: 截图搜题浮窗 + 版本下载站（设置窗置顶修复）"
    tree = call("POST", f"/repos/{owner}/{REPO}/git/trees", json={"tree": entries})
    parents = []
    try:
        head = call("GET", f"/repos/{owner}/{REPO}/git/ref/heads/main")
        parents = [head["object"]["sha"]]
    except RuntimeError:
        pass
    commit = call("POST", f"/repos/{owner}/{REPO}/git/commits",
                  json={"message": msg, "tree": tree["sha"], "parents": parents})
    try:
        call("POST", f"/repos/{owner}/{REPO}/git/refs",
             json={"ref": "refs/heads/main", "sha": commit["sha"]})
    except RuntimeError:
        call("PATCH", f"/repos/{owner}/{REPO}/git/refs/heads/main",
             json={"sha": commit["sha"], "force": True})
    print(f"✅ 已提交 {commit['sha'][:10]}：{msg}")

    # 4) 开启 Pages：site/ 不在 Pages 允许的 / 或 /docs 里，所以用 Actions 工作流发布
    try:
        call("GET", f"/repos/{owner}/{REPO}/pages")
        print("ℹ️ Pages 已存在")
    except RuntimeError:
        try:
            call("POST", f"/repos/{owner}/{REPO}/pages", json={"build_type": "workflow"})
            print("✅ Pages 已启用（build_type=workflow）")
        except RuntimeError as e:
            print("⚠ Pages 启用失败：", e)

    # 5) 等构建完成
    for i in range(20):
        try:
            st = call("GET", f"/repos/{owner}/{REPO}/pages/builds/latest")
            print(f"· 构建状态：{st.get('status')}")
            if st.get("status") == "built":
                break
        except Exception:
            pass
        time.sleep(8)
    print(f"REPO_URL=https://github.com/{owner}/{REPO}")


if __name__ == "__main__":
    main()
