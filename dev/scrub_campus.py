# -*- coding: utf-8 -*-
"""把站点/文档里涉及校园网、学生身份的表述全部替换成中性说法"""
import io
import os
import sys

ROOT = r"D:\hermes\261020搜题浮窗"

REPLACERS = {
    "site/index.html": [
        ('<span class="badge">● 校园网 · 内测分发</span>',
         '<span class="badge">● 内测分发 · 免费使用</span>'),
        ('<p class="quote">“浪费别人的时间等于谋财害命。”——水课的本质就是谋杀</p>',
         '<p class="quote">“浪费别人的时间等于谋财害命。”——这就是名字的由来</p>'),
        ('// 1) 本机/校园网服务器：带下载次数', '// 1) 自建服务器：带下载次数'),
        ('由 hb 维护', '由作者维护'),
    ],
    "site/serve.py": [
        ('"""列出本机可能被同学访问到的 IPv4（不含回环）"""',
         '"""列出本机可能被其他设备访问到的 IPv4（不含回环）"""'),
        ('print(f"    局域网/校园网  http://{ip}{suffix}")',
         'print(f"    局域网        http://{ip}{suffix}")'),
    ],
    "site/tunnel.py": [
        ('3. 把地址打印出来、写进 public_url.txt，并复制到剪贴板——直接发给同学',
         '3. 把地址打印出来、写进 public_url.txt，并复制到剪贴板——直接发给需要的人'),
        ('print("  公网地址（发给同学，校园网/4G 都能打开）：\\n")',
         'print("  公网地址（任何人、任何网络都能打开）：\\n")'),
    ],
    "README.md": [
        ('> “浪费别人的时间等于谋财害命。”——水课的本质就是谋杀',
         '> “浪费别人的时间等于谋财害命。”——这就是名字的由来'),
        ('## 版本下载站（同学来下载）', '## 版本下载站（分享给别人）'),
        ('详见 [site/README.md](site/README.md)（含“校园网隔离怎么办”“怎么换成公网托管”）。',
         '详见 [site/README.md](site/README.md)（含本地、公网、静态托管三种部署方式）。'),
    ],
}

for rel, pairs in REPLACERS.items():
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        print("跳过（不存在）:", rel)
        continue
    s = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        if old in s:
            s = s.replace(old, new)
            print(f"✓ {rel}: {old[:28]}…")
        else:
            print(f"– {rel}: 未找到 {old[:28]}…")
    io.open(path, "w", encoding="utf-8", newline="").write(s)

# site/README.md 整段重写（改动太多）
site_readme = os.path.join(ROOT, "site", "README.md")
txt = io.open(site_readme, encoding="utf-8").read()
start = txt.find("## 一、启动")
end = txt.find("## 二、发布新版本")
if start > 0 and end > start:
    txt = txt[:start] + """## 一、启动（本机 / 局域网）

双击 **`启动下载站.bat`**，或：

```bash
cd site
..\\.venv\\Scripts\\python.exe serve.py        # 默认 80 端口 => 地址不用带端口号
..\\.venv\\Scripts\\python.exe serve.py --port 8080   # 想换端口时
```

**默认监听 80**，别人打开 `http://<这台机器的IP>/` 就行，**不需要写 `:8000`**。
如果 80 被别的软件占用，会自动退到 8000 并在窗口里提示。

启动后窗口会打印可访问地址，例如：

```
本机            http://127.0.0.1
局域网          http://192.168.1.20
```

把**局域网那一行**发出去即可；页面右侧还有**二维码**，手机扫一下就进来。
首次运行 Windows 会弹防火墙提示，勾选「专用网络」并允许，否则别的设备连不上。

> 换了网络环境后 IP 会变，重新启动一次看新地址即可（页面内容不用改）。

""" + txt[end:]
txt = txt.replace("## 三、想放到公网/学校空间（推荐，同学不受隔离影响）",
                  "## 三、放到公网 / 静态托管（最省心）")
txt = txt.replace("所以既能本机/校园网跑，也能原样丢到任何静态托管（GitHub Pages、Cloudflare Pages、学校空间）。",
                  "所以既能本机/局域网跑，也能原样丢到任何静态托管（GitHub Pages、Cloudflare Pages、任意支持静态文件的服务器）。")
txt = txt.replace("- **GitHub Pages**：把仓库推到 GitHub", "- **GitHub Pages**：把仓库推到 GitHub（本项目已配置好 Actions 自动发布）")
io.open(site_readme, "w", encoding="utf-8", newline="").write(txt)
print("✓ site/README.md 已重写为中性表述")
print("完成")
