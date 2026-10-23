# -*- coding: utf-8 -*-
"""重建 _math_img 头部（注释里不写反斜杠，避免 heredoc/转义把源码写坏）"""
import io

P = r"D:\hermes\261020搜题浮窗\souti.py"
s = io.open(P, encoding="utf-8", newline="").read()

start = s.index("def _math_img(")
end = s.index("    r = render_math(expr, color, fontsize)", start)
new = (
    'def _math_img(m, color, fontsize=12.0):\n'
    '    """把一条公式渲染成 img 标签（含中文的公式交给 render_math 去掉中文后整体渲染）"""\n'
    '    expr = m.group(1) or m.group(2) or m.group(3) or m.group(4) or ""\n'
)
s = s[:start] + new + s[end:]
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("ok")
