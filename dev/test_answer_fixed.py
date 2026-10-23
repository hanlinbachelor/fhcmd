# -*- coding: utf-8 -*-
"""用用户截图里那种“难搞”的答案渲染一遍，检查：无源码残留 / 无重叠 / 答案醒目"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

ANS = r"""### 题目
(7). $\lim_{x\to 0}\left(\frac{1+\tan x}{1+\sin x}\right)^{\frac{1}{x^3}}$

### 答案
\[ \boxed{e^{\frac12}=\sqrt{e}} \]

### 解析
设原极限为 $L$，取对数：
\[ \ln L=\lim_{x\to0}\frac{1}{x^3}\ln\left(\frac{1+\tan x}{1+\sin x}\right) \]
当 $x\to 0$ 时 $\tan x-\sin x\sim\frac{x^3}{2}$，且 $1+\sin x\to 1$，故
$$ \ln L=\lim_{x\to0}\frac{1}{x^3}\cdot\frac{x^3}{2}=\frac12 $$
所以 $L=\sqrt{e}$。当 $x>0$ 时 $\sqrt{1+ax^2}-1$ 与 $\sin^2 x$ 等价。

### 考点
无穷小的比较；$\ln(1+u)\sim u$ 的等价代换
"""

cfg = souti.load_config()
w = souti.FloatWindow(cfg)
w.show()
w.current_answer = ANS
w._present_answer(ANS)
app.processEvents()

html = w.view.toHtml()
plain = re.sub(r"<[^>]+>", "", html)
left = sorted(set(re.findall(r"\\[a-zA-Z]+", plain)))
print("公式图片数:", html.count("<img"))
print("答案块存在:", "答 案" in plain)
print("残留 LaTeX 命令:", left if left else "无 ✅")
print("≤ft 之类破坏:", "≤ft" in plain)

pm = w.grab()
out = QImage(pm.width() + 40, pm.height() + 40, QImage.Format_RGB32)
out.fill(QColor(236, 238, 241))
p = QPainter(out)
p.drawPixmap(20, 20, pm)
p.end()
os.makedirs("dev/shots", exist_ok=True)
out.save("dev/shots/answer_fixed.png")
print("截图: dev/shots/answer_fixed.png")
w.ball.hide(); w.tray.hide(); w.close()
assert not left, f"还有源码残留: {left}"
print("✅ 无源码残留")
