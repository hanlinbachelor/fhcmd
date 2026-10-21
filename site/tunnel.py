#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键把下载站放到公网（Cloudflare 免费快速隧道）

它会做三件事：
  1. 本地站点没在跑就先启动 serve.py（80 端口）
  2. 启动 cloudflared 快速隧道，从输出里抓出 https://xxx.trycloudflare.com
  3. 把地址打印出来、写进 public_url.txt，并复制到剪贴板——直接发给同学

注意：快速隧道是临时的，关掉这个窗口就失效；每次启动地址都会变。
"""
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CF_CANDIDATES = [
    shutil.which("cloudflared"),
    r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
    r"C:\Program Files\cloudflared\cloudflared.exe",
]
PORT = 80


def port_open(port=PORT) -> bool:
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex(("127.0.0.1", port)) == 0


def find_cloudflared() -> str:
    for c in CF_CANDIDATES:
        if c and Path(c).exists():
            return c
    sys.exit("没找到 cloudflared。安装方式：winget install Cloudflare.cloudflared")


def start_site():
    if port_open():
        print(f"· 本地站点已在 http://127.0.0.1:{PORT} 运行")
        return
    print("· 本地站点没在跑，先启动 serve.py（新窗口）…")
    subprocess.Popen([sys.executable, "serve.py"], cwd=str(ROOT),
                     creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
    for _ in range(60):
        time.sleep(0.5)
        if port_open():
            print(f"· 站点已就绪 http://127.0.0.1:{PORT}")
            return
    sys.exit("站点没能在 30 秒内起来，先单独运行 serve.py 看看报错")


def copy_to_clipboard(text: str):
    try:
        subprocess.run(["clip"], input=text, text=True, check=False)
        return True
    except Exception:
        return False


def main():
    cf = find_cloudflared()
    start_site()

    print("· 正在向 Cloudflare 申请公网地址…（首次约 5~10 秒）\n")
    p = subprocess.Popen([cf, "tunnel", "--url", f"http://127.0.0.1:{PORT}", "--no-autoupdate"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace", bufsize=1)

    url = None
    registered = False
    t0 = time.time()
    while time.time() - t0 < 90:
        line = p.stdout.readline()
        if not line:
            if p.poll() is not None:
                break
            continue
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
        if m:
            url = m.group(0)          # 先记下，但等注册成功再宣布
        if "Registered tunnel connection" in line:
            registered = True
            break
        if "ERR" in line or "failed" in line.lower():
            print(line.rstrip())

    if url and not registered:
        print("\n· 地址已生成但隧道还没注册成功，再等一会儿…")
        t1 = time.time()
        while time.time() - t1 < 30 and not registered:
            line = p.stdout.readline()
            if not line:
                break
            if "Registered tunnel connection" in line:
                registered = True

    if not url or not registered:
        sys.exit("\n隧道没能建立。检查网络（trycloudflare.com 是否可达），或稍后重试。")

    # 自测一下：从公网绕一圈回到本地，确认真的能用再报地址
    print("· 隧道已注册，正在自测连通性…")
    ok = False
    for _ in range(6):
        try:
            import urllib.request
            with urllib.request.urlopen(url + "/api/versions", timeout=15) as r:
                ok = r.status == 200
            if ok:
                break
        except Exception:
            time.sleep(3)

    (ROOT / "public_url.txt").write_text(url + "\n", encoding="utf-8")
    copied = copy_to_clipboard(url)
    print("=" * 64)
    print("  公网地址（发给同学，校园网/4G 都能打开）：\n")
    print(f"    {url}\n")
    print(f"  自测：{'✅ 公网访问正常' if ok else '⚠ 隧道已连，但自测没通过（可能刚建好，等 10 秒再刷）'}")
    print(f"  {'已复制到剪贴板，直接粘贴即可' if copied else '复制上面这行发出去'}")
    print("  提醒：关掉这个窗口隧道就断了；重启会换新地址")
    print("=" * 64)
    print("\n— 以下为隧道日志（保持窗口开着）—\n")

    try:
        for line in p.stdout:
            # 只保留关键行，别刷屏
            if any(k in line for k in ("ERR", "WRN", "Registered tunnel connection")):
                print(line.rstrip())
    except KeyboardInterrupt:
        pass
    finally:
        p.terminate()
        print("\n隧道已关闭")


if __name__ == "__main__":
    main()
