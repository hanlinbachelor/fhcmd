#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打包一个新版本到下载站：生成 zip → 算 sha256 → 更新 versions.json → 同步进 index.html

用法（在 site 目录下）:
    python add_release.py                     # 打包当前 souti.py 里写的 __version__
    python add_release.py --version v1.1.0    # 指定版本号（同时会改 souti.py 的 __version__）
    python add_release.py --notes "改了啥"      # 手动给更新说明（默认从 CHANGELOG.md 抓）
"""
import argparse
import hashlib
import json
import re
import shutil
import zipfile
from datetime import date
from pathlib import Path

SITE = Path(__file__).resolve().parent
APP = SITE.parent
RELEASES = SITE / "releases"
VERSIONS = SITE / "versions.json"
INDEX = SITE / "index.html"

INCLUDE = [
    "souti.py",
    "config.example.json",
    "README.md",
    "CHANGELOG.md",
    "requirements.txt",
    "启动反谋财害命器.bat",
    "icon.ico",
]


def app_version() -> str:
    txt = (APP / "souti.py").read_text(encoding="utf-8")
    m = re.search(r'^__version__\s*=\s*"([^"]+)"', txt, re.M)
    if not m:
        raise SystemExit("souti.py 里没找到 __version__")
    return "v" + m.group(1)


def set_app_version(ver: str):
    p = APP / "souti.py"
    txt = p.read_text(encoding="utf-8")
    txt = re.sub(r'^__version__\s*=\s*"[^"]+"', f'__version__ = "{ver.lstrip("v")}"', txt, count=1, flags=re.M)
    p.write_text(txt, encoding="utf-8")
    print(f"  souti.py 版本号已改为 {ver}")


def changelog_notes(ver: str) -> str:
    p = APP / "CHANGELOG.md"
    if not p.exists():
        return ""
    txt = p.read_text(encoding="utf-8")
    m = re.search(rf"^##\s*{re.escape(ver)}\b.*?$(.*?)(?=^##\s|\Z)", txt, re.M | re.S)
    if not m:
        return ""
    lines = []
    for raw in m.group(1).strip().splitlines():
        s = raw.strip()
        if not s or s.startswith("---"):
            continue
        s = re.sub(r"^\*\*(.+?)\*\*$", r"【\1】", s)      # 小标题
        s = re.sub(r"^[-*]\s*", "· ", s)
        lines.append(s)
    return "\n".join(lines[:12])


def build_zip(ver: str) -> Path:
    RELEASES.mkdir(parents=True, exist_ok=True)
    name = f"fhcmd-{ver}.zip"
    out = RELEASES / name
    missing = [f for f in INCLUDE if not (APP / f).exists()]
    if missing:
        raise SystemExit("缺少文件：" + ", ".join(missing))
    exe = APP / "dist" / "反谋财害命器.exe"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        if exe.exists():
            # 优先带上免安装版 exe —— 用户双击即用，不需要 Python
            z.write(exe, f"反谋财害命器-{ver}/反谋财害命器.exe")
        for f in INCLUDE:
            z.write(APP / f, f"反谋财害命器-{ver}/{f}")
    return out


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load() -> dict:
    if VERSIONS.exists():
        return json.loads(VERSIONS.read_text(encoding="utf-8"))
    return {"latest": "", "display_names": {}, "versions": []}


def sync_inline(data: dict):
    """把清单同步进 index.html 的内联块，保证静态托管/双击打开也有数据"""
    if not INDEX.exists():
        return
    html = INDEX.read_text(encoding="utf-8")
    payload = json.dumps({"latest": data["latest"], "versions": data["versions"]},
                         ensure_ascii=False, separators=(",", ":"))
    html = re.sub(r'(<script id="versions-inline" type="application/json">).*?(</script>)',
                  lambda m: m.group(1) + payload + m.group(2), html, flags=re.S)
    INDEX.write_text(html, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=None, help="如 v1.1.0；不填则用 souti.py 里的 __version__")
    ap.add_argument("--notes", default=None, help="更新说明；默认从 CHANGELOG.md 抓")
    ap.add_argument("--requires", default="Windows 10/11 · Python 3.11+")
    args = ap.parse_args()

    ver = args.version or app_version()
    if not re.fullmatch(r"v\d+\.\d+\.\d+", ver):
        raise SystemExit("版本号要形如 v1.2.3")
    if args.version:
        set_app_version(ver)

    zp = build_zip(ver)
    notes = args.notes or changelog_notes(ver) or f"{ver} 版本"
    data = load()
    data["versions"] = [v for v in data["versions"] if v["version"] != ver]
    data["versions"].append({
        "version": ver,
        "date": date.today().isoformat(),
        "file": zp.name,
        "size": zp.stat().st_size,
        "sha256": sha256(zp),
        "notes": notes,
        "requires": args.requires,
    })
    data["versions"].sort(key=lambda v: [int(x) for x in v["version"].lstrip("v").split(".")], reverse=True)
    data["latest"] = data["versions"][0]["version"]
    data.setdefault("display_names", {})[zp.name] = f"反谋财害命器-{ver}.zip"

    VERSIONS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    sync_inline(data)

    # 顺手把 CHANGELOG 复制到站点，页面里的“更新记录”链接才打得开
    cl = APP / "CHANGELOG.md"
    if cl.exists():
        shutil.copyfile(cl, SITE / "CHANGELOG.md")

    print(f"✅ 已发布 {ver}")
    print(f"   包   : site/releases/{zp.name}  ({zp.stat().st_size/1048576:.2f} MB)")
    print(f"   sha  : {sha256(zp)[:32]}…")
    print(f"   说明 : {notes.splitlines()[0] if notes else ''}")
    print(f"   共 {len(data['versions'])} 个版本，最新 = {data['latest']}")
    print("\n   重启 serve.py 即可让页面读到新清单（静态文件无需重启也行）")


if __name__ == "__main__":
    main()
