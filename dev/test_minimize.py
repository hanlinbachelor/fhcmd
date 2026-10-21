# -*- coding: utf-8 -*-
"""验证两档最小化 + 尺寸/可见性 + 截图流程恢复（隔离进程，不干扰正在跑的实例）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication, QSystemTrayIcon
from PySide6.QtCore import Qt, QPoint

app = QApplication(sys.argv)
import souti
print("托盘可用:", QSystemTrayIcon.isSystemTrayAvailable())

cfg = souti.load_config()
w = souti.FloatWindow(cfg)
w.resize(440, 620)
w.move(300, 150)
w.show()
for _ in range(10):
    app.processEvents()
print("启动尺寸:", w.width(), "x", w.height(), "| 可见", w.isVisible())

def st(tag):
    print(f"{tag:<18} state={w.state:<7} 窗口={w.isVisible()!s:<5} 尺寸={w.width()}x{w.height():<6} "
          f"球={w.ball.isVisible()!s:<5} 球尺寸={w.ball.width()}x{w.ball.height()} 球位置={w.ball.pos().toTuple()} "
          f"托盘={w.tray.isVisible()}")

st("启动")

# ---- 第一档
w.minimize_to_ball()
for _ in range(8):
    app.processEvents()
st("第一档: 球")
assert w.state == "ball" and not w.isVisible() and w.ball.isVisible()
assert (w.ball.width(), w.ball.height()) == (58, 58), "球尺寸不对"
scr = app.primaryScreen().availableGeometry()
gap = min(abs(w.ball.x() - scr.left()), abs(scr.right() - (w.ball.x() + w.ball.width())))
print("   距最近侧边:", gap, "px")
assert gap <= 8, "球没有贴边"

w.ball.grab().save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots", "ui_ball.png"))

# ---- 点球展开（尺寸必须还原，不能变窄/压扁）
w.ball.clicked.emit()
for _ in range(10):
    app.processEvents()
st("点球展开")
assert w.state == "window" and w.isVisible() and not w.ball.isVisible()
assert (w.width(), w.height()) == (440, 620), f"还原后尺寸错了: {w.width()}x{w.height()}"

# ---- 第二档: 托盘
w.minimize_to_ball(); app.processEvents()
w.minimize_to_tray()
for _ in range(8):
    app.processEvents()
st("第二档: 托盘")
assert w.state == "tray" and not w.isVisible() and not w.ball.isVisible() and w.tray.isVisible()

# ---- 托盘点一下恢复
w._tray_activated(QSystemTrayIcon.Trigger)
for _ in range(8):
    app.processEvents()
st("托盘恢复")
assert w.isVisible() and (w.width(), w.height()) == (440, 620)

# ---- 从球状态触发截图 -> 取消 -> 回到球；成功 -> 回到窗口
w.minimize_to_ball(); app.processEvents()
w._prev_state = w.state
w.hide(); w.ball.hide()
w._show_me()
for _ in range(8):
    app.processEvents()
st("球态取消截图")
assert w.state == "ball" and w.ball.isVisible()

w.hide(); w.ball.hide()
w.restore_window()
for _ in range(8):
    app.processEvents()
st("截图完成展开")
assert w.state == "window" and w.isVisible() and (w.width(), w.height()) == (440, 620)

print("quitOnLastWindowClosed =", app.quitOnLastWindowClosed(), "(该 app 是测试进程，程序内 main() 设为 False)")

# ---- 隐藏窗口后不应退出应用
w.minimize_to_tray()
for _ in range(6):
    app.processEvents()
print("隐藏后 app 仍在运行:", not app.closingDown())

w.ball.hide(); w.tray.hide(); w.close()
print("\n全部断言通过 ✅")
