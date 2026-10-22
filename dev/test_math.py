# -*- coding: utf-8 -*-
"""先验证：matplotlib mathtext -> PNG -> file:// 嵌进 QTextBrowser / QLabel 能否正常显示"""
import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication, QLabel, QTextBrowser


def render(expr, color="#efeae2", fontsize=13.0, dpi=220):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    fig = Figure(figsize=(0.1, 0.1), dpi=dpi)
    FigureCanvasAgg(fig)
    fig.patch.set_alpha(0)
    fig.text(0, 0, f"${expr}$", color=color, fontsize=fontsize)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True, bbox_inches="tight", pad_inches=0.03)
    return buf.getvalue()


app = QApplication(sys.argv)
out = tempfile.mkdtemp(prefix="mathtest_")
exprs = [r"f(x)=x^3-3x+1", r"x=\frac{-b\pm\sqrt{b^2-4ac}}{2a}", r"\lim_{n\to\infty}\left(1+\frac1n\right)^n=e"]
html = []
for i, e in enumerate(exprs):
    png = render(e)
    p = os.path.join(out, f"m{i}.png")
    open(p, "wb").write(png)
    img = QImage(p)
    print(f"{e!r} -> {img.width()}x{img.height()}  {len(png)}B")
    html.append(f'<img src="file:///{p.replace(chr(92), "/")}" width="{img.width()//2}" height="{img.height()//2}">')

tb = QTextBrowser()
tb.resize(400, 300)
tb.setHtml("<p style='color:#efeae2'>公式测试：<br>" + "<br>".join(html) + "</p>")
tb.show()
app.processEvents()
pm = tb.grab()
img = pm.toImage()
nonblank = sum(1 for y in range(0, img.height(), 4) for x in range(0, img.width(), 4)
               if img.pixelColor(x, y).red() > 60)
print("QTextBrowser 渲染非空白采样点数:", nonblank)
pm.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots", "math_test.png"))

lb = QLabel()
lb.setStyleSheet("color:#efeae2; background:#22262c")
lb.setText('<span style="color:#efeae2">答案：</span>' + html[0])
lb.resize(300, 60)
lb.show()
app.processEvents()
print("QLabel 显示图片是否成功:", lb.grab().toImage().pixelColor(200, 30).alpha() > 0)
print("PNG 目录:", out)
