# -*- coding: utf-8 -*-
"""验证答案条：是否显示、是否挤压正文、长答案会不会溢出"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPainter, QColor

app = QApplication(sys.argv)
import souti

SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
os.makedirs(SHOTS, exist_ok=True)

TEXT = """### 题目
**3.**【单选题】（2分）哪一年 8 月 15 日，时任浙江省委书记的习近平在安吉考察时首次提出“绿水青山就是金山银山”？

A. 2007　B. 2008　C. 2004　D. 2005

### 答案
**D. 2005**

### 解析
2005 年 8 月 15 日，时任浙江省委书记的习近平在浙江安吉县天荒坪镇余村考察时，首次提出“绿水青山就是金山银山”的科学论断；其余年份均与该历史事实不符。

### 考点
考查该理念的提出时间与地点；易错点是与 2003 年“八八战略”、2007 年十七大混淆。"""

LONG_ANS = """### 题目
求函数 f(x)=x^3-3x+1 在 [-2,2] 上的最值。

### 答案
最大值 3（在 x=-1 与 x=2 处取到），最小值 -1（在 x=1 与 x=-2 处取到）

### 解析
f'(x)=3x^2-3=3(x-1)(x+1)，驻点 x=±1，比较驻点与端点函数值。

### 考点
闭区间最值需比较驻点与端点。"""

cfg = souti.load_config()
cfg["theme"] = "morandi"
w = souti.FloatWindow(cfg)
w.move(30, 30)
w.resize(440, 620)
w.show()
for _ in range(10):
    app.processEvents()

for tag, txt in (("normal", TEXT), ("long", LONG_ANS)):
    w.current_answer = txt
    w._present_answer(txt)
    for _ in range(8):
        app.processEvents()
    box = w.answer_box
    print(f"[{tag}] 答案条可见={box.isVisible()} 尺寸={box.width()}x{box.height()} "
          f"| 正文区={w.view.width()}x{w.view.height()} | 窗口={w.width()}x{w.height()}")
    assert box.isVisible(), "答案条没显示"
    assert box.height() >= 40, "答案条太扁"
    assert w.view.height() > 180, "答案条把正文挤没了"
    pm = w.grab()
    img = QImage(pm.width() + 36, pm.height() + 36, QImage.Format_RGB32)
    img.fill(QColor(236, 238, 242))
    p = QPainter(img)
    p.drawPixmap(18, 18, pm)
    p.end()
    out = os.path.join(SHOTS, f"answer_{tag}.png")
    img.save(out)
    print("   saved", out)

w.ball.hide(); w.tray.hide(); w.close()
print("\n答案条断言通过 ✅")
