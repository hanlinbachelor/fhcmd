# -*- coding: utf-8 -*-
"""一键发版：打包 → 更新站点 → 推到 GitHub → 建 Release（令牌自动从本机受限文件读）

用法:
    .venv\\Scripts\\python.exe dev/release_all.py            # 用 souti.py 里的 __version__
    .venv\\Scripts\\python.exe dev/release_all.py v1.2.0     # 指定版本号（会改 souti.py 与 CHANGELOG）
"""
import os
import re
import subprocess
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
PY = str(APP / ".venv" / "Scripts" / "python.exe")
TOKEN = Path(os.path.expandvars(r"%LOCALAPPDATA%\hermes\secrets\github_fhcmd_token.txt"))


def run(args, label):
    print(f"\n=== {label} ===")
    p = subprocess.run(args, cwd=str(APP), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (p.stdout or "") + (p.stderr or "")
    print(out.strip()[-1200:])
    if p.returncode != 0:
        sys.exit(f"❌ {label} 失败（退出码 {p.returncode}）")
    return out


def main():
    ver = sys.argv[1] if len(sys.argv) > 1 else None
    if not TOKEN.exists():
        sys.exit("❌ 没有令牌：先按 README 里“发版”一节把令牌存到 " + str(TOKEN))

    args = [PY, str(APP / "site" / "add_release.py")]
    if ver:
        args += ["--version", ver]
    run(args, "1/4 打包新版本 + 更新站点清单")

    run(["git", "-C", str(APP), "add", "-A"], "2/4 git add")
    cur = subprocess.run(["git", "-C", str(APP), "diff", "--cached", "--quiet"])
    if cur.returncode != 0:
        v = ver or re.search(r'__version__\s*=\s*"([^"]+)"',
                             (APP / "souti.py").read_text(encoding="utf-8")).group(1)
        run(["git", "-C", str(APP), "commit", "-m", f"release: {v}"], "   git commit")

    run([PY, str(APP / "dev" / "gh_publish.py"), str(TOKEN), "fhcmd"], "3/4 推送到 GitHub")
    run([PY, str(APP / "dev" / "gh_releases.py")], "4/4 建 Release 并上传附件")
    print("\n✅ 发版完成")


if __name__ == "__main__":
    main()
