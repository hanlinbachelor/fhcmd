# -*- coding: utf-8 -*-
"""主题切换验证 + 两套外观截图（铺在浅灰底上，供目检/视觉模型质检）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtCore import Qt

app = QApplication(sys.argv)
import souti

SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
os.makedirs(SHOTS, exist_ok=True)

DEMO = """### 题目
**3.**【单选题】（2分）哪一年 8 月 15 日，时任浙江省委书记的习近平在安吉考察时首次提出“绿水青山就是金山银山”？

A. 2007　B. 2008　C. 2004　D. 2005

### 答案
**D. 2005**

### 解析
2005 年 8 月 15 日，习近平在浙江安吉县天荒坪镇余村考察时首次提出该论断。其余年份不符。

### 考点
考查该理念的提出时间与地点；易错点是与 2003 年“八八战略”混淆。"""

cfg = souti.load_config()
cfg["theme"] = "laser"
w = souti.FloatWindow(cfg)
w.move(30, 30)
w.show()
for _ in range(8):
    app.processEvents()

def dump(path, pad=18, bg=(236, 238, 242)):
    pm = w.grab()
    img = QImage(pm.width() + pad * 2, pm.height() + pad * 2, QImage.Format_RGB32)
    img.fill(QColor(*bg))
    p = QPainter(img)
    p.drawPixmap(pad, pad, pm)
    p.end()
    img.save(path)
    print("saved", path, img.width(), "x", img.height())

print("可用主题:", list(souti.THEMES.keys()))

# 镭射
print("当前:", w.theme_name, "| 卡片主题:", w.card.th["label"])
assert w.theme_name == "laser"
w.view.setHtml(w._welcome_html())
for _ in range(4):
    app.processEvents()
dump(os.path.join(SHOTS, "theme_laser_welcome.png"))

# 切换到莫兰迪
w.apply_theme("morandi")
for _ in range(8):
    app.processEvents()
print("切换后:", w.theme_name, "| 卡片:", w.card.th["label"], "| 球:", w.ball.th["label"], "| 配置:", w.cfg["theme"])
assert w.theme_name == "morandi" and w.card.th["label"] == souti.THEMES["morandi"]["label"]
assert w.ball.th["label"] == souti.THEMES["morandi"]["label"]
dump(os.path.join(SHOTS, "theme_morandi_welcome.png"))

# 莫兰迪 + 答案态
w.view.setMarkdown(DEMO)
w.status.setText("✓ 完成 · 5s · tokens 1933")
w.view.verticalScrollBar().setValue(0)
for _ in range(6):
    app.processEvents()
dump(os.path.join(SHOTS, "theme_morandi_answer.png"))

# 莫兰迪 悬浮球
w.minimize_to_ball()
for _ in range(6):
    app.processEvents()
w.ball.grab().save(os.path.join(SHOTS, "theme_morandi_ball.png"))
print("球尺寸:", w.ball.width(), "x", w.ball.height())
w.restore_window()

# 镭射 + 答案态
w.apply_theme("laser")
w.view.setMarkdown(DEMO)
for _ in range(6):
    app.processEvents()
dump(os.path.join(SHOTS, "theme_laser_answer.png"))

# 落盘检查: 主题被写进 config
import json
saved = json.load(open(souti.CONFIG_PATH, encoding="utf-8"))
print("config.json theme =", saved.get("theme"))
assert saved.get("theme") == "laser"

w.ball.hide(); w.tray.hide(); w.close()
print("\n主题切换断言全部通过 ✅")
