# -*- coding: utf-8 -*-
"""复现用户截图那种解析：跨行公式 + 【题目/答案/解析/考点】分段，走完整 _present_answer"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

TEXT = """【题目】
求极限 $\\lim_{x\\to 0}\\left(\\frac{1+\\tan x}{1+\\sin x}\\right)^{\\frac{1}{x^3}}$

【答案】
$e^{\\frac{1}{2}}=\\sqrt{e}$

【解析】
将分子拆开，先把底数化简：
$\\frac{1+\\tan x}{1+\\sin x}
=1+\\frac{\\tan x-\\sin x}{1+\\sin x}
=1+\\frac{x^3}{2}+o(x^3).$
再取对数：
\\[
\\ln L=\\lim_{x\\to 0}\\frac{1}{x^3}\\ln\\left(1+\\frac{x^3}{2}+o(x^3)\\right)=\\frac{1}{2}
\\]
所以 $\\boxed{L=\\sqrt e}$。

【考点】
等价无穷小替换 · 重要极限
"""

cfg = souti.load_config()
cfg["theme"] = "qianli"
w = souti.FloatWindow(cfg)
w.show()
app.processEvents()
w._present_answer(TEXT)
app.processEvents()

html = w.view.toHtml()
plain = re.sub(r"<[^>]+>", " ", html)
img = html.count("<img")
print("img 标签:", img)
resid = re.findall(r"\\[a-zA-Z]{2,}|\$", plain)
print("残留 LaTeX 命令/美元符:", resid[:8], "总", len(resid))
w.grab().save("dev/shots/math_pipeline.png")
print("截图: dev/shots/math_pipeline.png")
w.ball.hide()
w.tray.hide()
w.close()
