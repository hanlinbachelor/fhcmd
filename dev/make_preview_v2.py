# -*- coding: utf-8 -*-
"""生成两张验收图：答案/解析里的公式渲染 & 设置窗外观"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
os.makedirs(SHOTS, exist_ok=True)

ANS = r"""### 题目
证明 $\sqrt e=e^{\frac12}$，并求 $\lim_{n\to\infty}(1+\dfrac1n)^n$。

### 答案
\[ \boxed{\sqrt e=e^{\frac12}} \]

### 解析
由 $e^x$ 的泰勒展开可知：当 $x>0$ 时 $\sqrt{x^2}=x$。
又 $\because a^2+b^2=c^2$，$\therefore c=\sqrt{a^2+b^2}$。
极限部分：$\lim_{n\to\infty}\left(1+\frac1n\right)^n=e$。

### 考点
指数与对数、重要极限、根式化简
"""

cfg = souti.load_config()
w = souti.FloatWindow(cfg)
w.show()
w.current_answer = ANS
w._present_answer(ANS)
app.processEvents()

pm = w.grab()
out = QImage(pm.width() + 40, pm.height() + 40, QImage.Format_RGB32)
out.fill(QColor(238, 240, 243))
p = QPainter(out)
p.drawPixmap(20, 20, pm)
p.end()
out.save(os.path.join(SHOTS, "math_boxed.png"))
print("公式页:", out.width(), out.height())

dlg = souti.SettingsDialog(w, cfg)
dlg.show()
app.processEvents()
dp = dlg.grab()
d2 = QImage(dp.width() + 60, dp.height() + 60, QImage.Format_RGB32)
d2.fill(QColor(120, 128, 138))
p = QPainter(d2)
p.drawPixmap(30, 30, dp)
p.end()
d2.save(os.path.join(SHOTS, "settings_v3.png"))
print("设置窗:", d2.width(), d2.height())
dlg.close()
w.ball.hide(); w.tray.hide(); w.close()
