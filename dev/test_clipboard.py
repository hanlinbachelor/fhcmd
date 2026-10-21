# -*- coding: utf-8 -*-
"""跨进程剪贴板验证: A 进程写入图片 -> B 进程读取，模拟"粘到别的软件里" """
import subprocess, sys, os, textwrap
HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

setter = textwrap.dedent("""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QColor
from PySide6.QtCore import QTimer
app = QApplication(sys.argv)
img = QImage(240, 120, QImage.Format_RGB32)
img.fill(QColor(30, 140, 90))
QApplication.clipboard().setImage(img)
QTimer.singleShot(6000, app.quit)   # 保持存活，模拟程序不退出
app.exec()
""")
reader = textwrap.dedent("""
import sys, json
from PySide6.QtWidgets import QApplication
app = QApplication(sys.argv)
img = QApplication.clipboard().image()
md = QApplication.clipboard().mimeData()
print(json.dumps({"null": img.isNull(), "w": img.width(), "h": img.height(),
                  "hasImage_mime": bool(md and md.hasImage()),
                  "formats": list(md.formats()) if md else []}, ensure_ascii=False))
""")
open(os.path.join(HERE, "_set_clip.py"), "w", encoding="utf-8").write(setter)
open(os.path.join(HERE, "_read_clip.py"), "w", encoding="utf-8").write(reader)

p = subprocess.Popen([PY, os.path.join(HERE, "_set_clip.py")])
import time
time.sleep(2.5)
r = subprocess.run([PY, os.path.join(HERE, "_read_clip.py")], capture_output=True, text=True)
print("reader stdout:", r.stdout.strip(), "| stderr:", r.stderr.strip()[:200])
p.terminate()
