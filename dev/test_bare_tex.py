# -*- coding: utf-8 -*-
"""验证：模型不写 $ 包裹的裸 LaTeX 也能被渲染；面板不再透背景"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

BARE = r"""### 题目
(7). lim_{x\to 0}\left(\frac{1+\tan x}{1+\sin x}\right)^{\frac{1}{x^3}}

### 答案
e^{\frac12}=\sqrt{e}

### 解析
设原极限为 L，取对数：
\ln L=\lim_{x\to0}\frac{1}{x^3}\ln\left(\frac{1+\tan x}{1+\sin x}\right)
当 x\to 0 时，\tan x-\sin x \sim \frac{x^3}{2}，故 \ln L=\frac12，即 L=\sqrt{e}。

### 考点
无穷小的比较
"""

for theme in ("morandi", "laser"):
    cfg = souti.load_config()
    cfg["theme"] = theme
    w = souti.FloatWindow(cfg)
    w.show()
    app.processEvents()
    w._present_answer(BARE)
    app.processEvents()
    html = w.view.toHtml()
    plain = re.sub(r"<[^>]+>", "", html)
    left = sorted(set(re.findall(r"\\[a-zA-Z]+", plain)))
    print(f"[{theme}] 图片数={html.count('<img')} 源码残留={left if left else '无'}")
    pm = w.grab()
    out = QImage(pm.width() + 40, pm.height() + 40, QImage.Format_RGB32)
    out.fill(QColor(236, 238, 241))
    p = QPainter(out)
    p.drawPixmap(20, 20, pm)
    p.end()
    out.save(f"dev/shots/bare_{theme}.png")
    print(f"   截图 dev/shots/bare_{theme}.png")
    w.ball.hide(); w.tray.hide(); w.close()
