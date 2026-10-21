#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""反谋财害命器 · 版本下载站（纯标准库，无需安装任何依赖）

用法:
    python serve.py                # 默认 0.0.0.0:8000
    python serve.py --port 8080    # 换端口
    python serve.py --host 127.0.0.1   # 只允许本机访问

接口:
    GET /                     首页（版本选择 + 下载）
    GET /api/versions         版本清单 JSON（含下载次数）
    GET /download/<文件名>     下载，并记录一次到 downloads.log
"""
import argparse
import json
import mimetypes
import os
import socket
import sys
import time
from collections import Counter
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
RELEASES = ROOT / "releases"
VERSIONS = ROOT / "versions.json"
DL_LOG = ROOT / "downloads.log"


def lan_ips():
    """列出本机可能被同学访问到的 IPv4（不含回环）"""
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.3)
        s.connect(("8.8.8.8", 80))          # 不会真的发包，只为拿到出口地址
        ips.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except Exception:
        pass
    return sorted(i for i in ips if not i.startswith("127."))


def download_counts():
    cnt = Counter()
    if DL_LOG.exists():
        for line in DL_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
            parts = line.split("\t")
            if len(parts) >= 3:
                cnt[parts[2]] += 1
    return cnt


def load_versions():
    data = json.loads(VERSIONS.read_text(encoding="utf-8"))
    cnt = download_counts()
    for v in data.get("versions", []):
        v["downloads"] = cnt.get(v["file"], 0)
    return data


class Handler(SimpleHTTPRequestHandler):
    server_version = "fhcmd-site/1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    # ---------- 路由
    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path == "/api/versions":
            return self.send_json(load_versions())
        if path == "/qr.png":
            return self.send_qr()
        if path.startswith("/download/"):
            return self.send_download(path[len("/download/"):])
        if self._blocked(path):
            self.send_error(404, "Not found")
            return
        return super().do_GET()

    def do_HEAD(self):
        path = unquote(urlparse(self.path).path)
        if path.startswith("/download/"):
            return self.send_download(path[len("/download/"):], head_only=True)
        if self._blocked(path):
            self.send_error(404, "Not found")
            return
        return super().do_HEAD()

    @staticmethod
    def _blocked(path: str) -> bool:
        """只对外提供页面与安装包；隐藏文件和后端脚本不暴露"""
        low = path.lower()
        if "/." in low:
            return True
        return os.path.basename(low) in {"serve.py", "add_release.py", "downloads.log"}

    # ---------- 具体处理
    def send_qr(self):
        """把当前访问地址做成二维码，手机扫一下就进来（不用手打端口）"""
        host = self.headers.get("Host") or f"127.0.0.1:{self.server.server_port}"
        url = f"http://{host}/"
        try:
            import io
            import qrcode
            img = qrcode.make(url, box_size=8, border=2)
            buf = io.BytesIO()
            img.save(buf, "PNG")
            body = buf.getvalue()
        except Exception as e:
            self.send_error(503, f"QR 生成失败: {e}")
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_json(self, obj):
        body = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_download(self, name, head_only=False):
        name = os.path.basename(name)                 # 防目录穿越
        f = RELEASES / name
        if not f.is_file():
            self.send_error(404, "No such release")
            return
        size = f.stat().st_size
        ctype = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(size))
        # 下载名用中文（RFC 5987），文件名本身保持 ASCII 以免 URL 乱码
        display = load_versions().get("display_names", {}).get(name, name)
        from urllib.parse import quote
        self.send_header("Content-Disposition",
                         f"attachment; filename=\"{name}\"; filename*=UTF-8''{quote(display)}")
        self.end_headers()
        if head_only:
            return
        with open(f, "rb") as fh:
            while True:
                chunk = fh.read(256 * 1024)
                if not chunk:
                    break
                self.wfile.write(chunk)
        # 记录一次下载
        ip = self.client_address[0]
        with open(DL_LOG, "a", encoding="utf-8") as log:
            log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\t{ip}\t{name}\n")
        print(f"  ↓ {ip} 下载 {name} ({size/1048576:.1f} MB)")

    def log_message(self, fmt, *args):
        # 默认日志太吵，只保留错误和首页之外的关键行
        if args and str(args[1]).startswith(("4", "5")):
            sys.stderr.write("  ! %s - %s\n" % (self.address_string(), fmt % args))


class SiteServer(ThreadingHTTPServer):
    # Windows 上 SO_REUSEADDR 会让两个进程绑同一个端口（后绑的抢走流量），
    # 导致“端口被占用就自动换一个”的判断失效 —— 这里显式关掉。
    allow_reuse_address = False
    daemon_threads = True


def main():
    ap = argparse.ArgumentParser(description="版本下载站")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=80,
                    help="默认 80（别人打开地址不用带端口）；被占用会自动退到 8000/8080")
    args = ap.parse_args()

    if not VERSIONS.exists():
        sys.exit("缺少 versions.json，先运行 add_release.py 打包一个版本")
    data = load_versions()

    httpd = None
    for port in dict.fromkeys([args.port, 8000, 8080]):
        try:
            httpd = SiteServer((args.host, port), Handler)
            if port != args.port:
                print(f"  ! 端口 {args.port} 被占用，改用 {port}")
            break
        except OSError as e:
            print(f"  ! 端口 {port} 不可用：{e}")
    if httpd is None:
        sys.exit("没有可用端口，用 --port 指定一个")
    port = httpd.server_address[1]
    suffix = "" if port == 80 else f":{port}"

    print("=" * 58)
    print("  反谋财害命器 · 版本下载站已启动")
    print("=" * 58)
    print(f"  当前版本: {data.get('latest', '?')}   共 {len(data.get('versions', []))} 个版本")
    print(f"  监听    : http://{args.host}:{port}")
    print("  访问地址:")
    print(f"    本机      http://127.0.0.1{suffix}")
    for ip in lan_ips():
        print(f"    局域网/校园网  http://{ip}{suffix}")
    print(f"  二维码    http://127.0.0.1{suffix}/qr.png  （页面右侧也直接显示）")
    print("  提示: 首次运行 Windows 会弹防火墙提示，勾选“专用网络”并允许")
    print("  Ctrl+C 停止")
    print("=" * 58)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")


if __name__ == "__main__":
    main()
