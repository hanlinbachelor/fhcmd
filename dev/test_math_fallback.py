# -*- coding: utf-8 -*-
"""验证：1) \boxed 等 mathtext 不支持的命令能降级渲染；2) 设置窗配色对比度"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
os.makedirs(SHOTS, exist_ok=True)

cases = [
    r"\boxed{\sqrt e=e^{\frac12}}",
    r"\dfrac{1}{2}+\dfrac{1}{3}=\dfrac{5}{6}",
    r"\text{当 } x>0 \text{ 时}, \sqrt{x^2}=x",
    r"\operatorname{lim}_{n\to\infty}\left(1+\frac1n\right)^n",
    r"\because a^2+b^2=c^2 \therefore c=\sqrt{a^2+b^2}",
]
fails = []
for c in cases:
    r = souti.render_math(c, "#efeae2", 13)
    print(("✅" if r else "❌"), c, "->", r[1:] if r else "渲染失败")
    if not r:
        fails.append(c)

# 设置窗截图
cfg = souti.load_config()
w = souti.FloatWindow(cfg)
w.show()
app.processEvents()
dlg = souti.SettingsDialog(w, cfg)
dlg.show()
app.processEvents()
pm = dlg.grab()
pm.save(os.path.join(SHOTS, "settings_v2.png"))
print("设置窗尺寸:", pm.width(), pm.height(), "→ dev/shots/settings_v2.png")
dlg.close()
w.ball.hide(); w.tray.hide(); w.close()

assert not fails, f"这些没渲染出来: {fails}"
print("✅ 全部公式都渲染成功（含 \\boxed / \\dfrac / \\text / \\operatorname）")
