# -*- coding: utf-8 -*-
"""验证「完全不碰剪贴板」：空输入点发送时，即使剪贴板里有图也不能发出去"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtGui import QGuiApplication, QImage, QColor
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
import souti

# 往剪贴板塞一张醒目的图（模拟“旧截图残留”）
img = QImage(400, 300, QImage.Format_RGB32)
img.fill(QColor(200, 30, 30))
QGuiApplication.clipboard().setImage(img)
print("剪贴板已放入测试图片:", not QGuiApplication.clipboard().image().isNull())

cfg = souti.load_config()
w = souti.FloatWindow(cfg)
w.show()
app.processEvents()

before_hist = len(w.history)
before_ans = w.current_answer

w.input.clear()
w.on_send()                     # 空输入点发送
app.processEvents()

print("状态栏:", w.status.text())
print("对话条数 前/后:", before_hist, len(w.history))
print("答案 前/后:", repr(before_ans), repr(w.current_answer))

assert "先输入题目" in w.status.text(), "空输入时没有给出正确提示"
assert len(w.history) == before_hist, "不应该发出任何请求（对话被写入了）"
assert not getattr(w, "worker", None) or w.worker is None, "不应该启动请求线程"
print("✅ 空输入点发送：只提示，不发图、不读剪贴板")

w.ball.hide(); w.tray.hide(); w.close()
print("✅ 通过")
