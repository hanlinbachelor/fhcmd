# -*- coding: utf-8 -*-
"""验证公式渲染：把一段带 LaTeX 的答案喂给浮窗，检查图片是否生成、HTML 是否引用"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

cfg = souti.load_config()
w = souti.FloatWindow(cfg)
w.show()
app.processEvents()

ANSWER = """### 题目
求 f(x)=x^3-3x+1 在 [-2,2] 上的最大值与最小值。

### 答案
最大值 $3$，最小值 $-1$

### 解析
先求导：$f'(x)=3x^2-3$，令 $f'(x)=0$ 得 $x=\\pm 1$。
比较端点与驻点：
$$f(-2)=-1,\\quad f(-1)=3,\\quad f(1)=-1,\\quad f(2)=3$$
又因为 $\\frac{1}{2}+\\frac{1}{3}=\\frac{5}{6}$，可验证连续性。
曲线满足 $\\lim_{n\\to\\infty}(1+\\frac1n)^n=e$。

### 考点
导数与函数最值、闭区间最值比较
"""

w.current_answer = ANSWER
w._present_answer(ANSWER)
app.processEvents()

html = w.view.toHtml()
box = w.answer_box.text()
imgs = sorted(os.listdir(souti.MATH_DIR)) if souti.MATH_DIR.exists() else []
print("答案条含图片:", "<img" in box)
print("正文含图片数:", html.count("<img"))
print("生成的公式图片:", len(imgs), "个")
print("渲染缓存:", len(souti._MATH_CACHE), "条")
for name in imgs[:4]:
    p = souti.MATH_DIR / name
    print("  ", name, p.stat().st_size, "字节")
pm = w.grab()
pm.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots", "math_answer.png"))
print("截图已保存: dev/shots/math_answer.png")
assert "<img" in box, "答案条没有渲染公式"
assert html.count("<img") >= 3, "正文公式没有渲染"
print("✅ 公式渲染通过")
w.ball.hide(); w.tray.hide(); w.close()
