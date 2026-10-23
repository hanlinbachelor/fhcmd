# -*- coding: utf-8 -*-
"""验证检查更新：版本比较 + 真实拉取 latest"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

app = QApplication(sys.argv)
import souti

print("版本比较:")
for a, b in (("v1.3.3", "1.3.4"), ("1.4.0", "1.3.9"), ("1.3.3", "1.3.3")):
    print(f"  {a} > {b} ? {souti.ver_tuple(a) > souti.ver_tuple(b)}")

res = {}


def on_done(latest, err):
    res["latest"], res["err"] = latest, err
    app.quit()


t = souti.UpdateThread()
t.done.connect(on_done)
t.start()
QTimer.singleShot(15000, app.quit)
app.exec()

print("拉取结果:", res.get("latest"), "| err:", res.get("err") or "无")
ok = souti.ver_tuple(res.get("latest", "")) > souti.ver_tuple(souti.__version__)
print("当前版本:", souti.__version__, "| 是否有新版:", ok)
print("✅ 检查更新可用" if (res.get("latest") or res.get("err")) else "❌ 两种源都失败")
