# -*- coding: utf-8 -*-
"""给 README 和下载页加“Windows 拦截怎么办”的说明"""
import io
import os

ROOT = r"D:\hermes\261020搜题浮窗"

BLOCK_MD = """
## 如果 Windows 提示「应用程序控制策略已阻止此文件」

新版 Windows 11 默认开启**智能应用控制（Smart App Control）**，它只放行有信誉或带签名的程序，
未签名的 exe 第一次运行可能被直接拦下（提示「应用程序控制策略已阻止此文件」）。三种处理方式，任选一种：

1. **改用包里的源码版**（推荐，不影响系统安全）
   双击 `启动反谋财害命器.bat`，它会自动建虚拟环境并安装依赖（需要先装 Python 3.11/3.12）。
2. **临时放行这个 exe**
   右键 `反谋财害命器.exe` → 属性 → 勾选「解除锁定」→ 确定，再双击运行。
3. **关闭智能应用控制**
   设置 → 隐私和安全性 → Windows 安全中心 → 应用和浏览器控制 → 智能应用控制 → 关闭。
   （关闭后不能只关一段时间再自动打开，请自行权衡。）

程序本身不联网上传任何截图以外的内容，也不需要管理员权限。
"""


def patch_readme():
    p = os.path.join(ROOT, "README.md")
    s = io.open(p, encoding="utf-8").read()
    if "智能应用控制" in s:
        return "README 已有说明"
    anchor = "## 安装与启动"
    if anchor in s:
        s = s.replace(anchor, BLOCK_MD.strip() + "\n\n" + anchor, 1)
    else:
        s += "\n" + BLOCK_MD
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    return "README 已加说明"


def patch_site():
    p = os.path.join(ROOT, "site", "index.html")
    s = io.open(p, encoding="utf-8").read()
    if "智能应用控制" in s:
        return "站点已有说明"
    block = '''    <div class="card" style="margin-top:18px">
      <div class="k">如果 Windows 提示「应用程序控制策略已阻止此文件」</div>
      <div class="v" style="line-height:1.85">
        Windows 11 的<strong>智能应用控制</strong>只放行有信誉/签名的程序，未签名的 exe 可能被拦。三选一：<br>
        ① 用包里的源码版：双击 <code>启动反谋财害命器.bat</code>（需先装 Python 3.11/3.12，会自动装依赖）<br>
        ② 放行 exe：右键 → 属性 → 勾「解除锁定」→ 确定<br>
        ③ 关闭智能应用控制：设置 → 隐私和安全性 → Windows 安全中心 → 应用和浏览器控制 → 智能应用控制
      </div>
    </div>
'''
    marker = '<div class="foot">'
    if marker in s:
        s = s.replace(marker, block + "    " + marker, 1)
    else:
        s = s.replace("</body>", block + "</body>", 1)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    return "站点已加说明"


print(patch_readme())
print(patch_site())
