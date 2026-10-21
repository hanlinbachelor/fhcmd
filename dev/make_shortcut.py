# -*- coding: utf-8 -*-
"""在桌面创建快捷方式: 反谋财害命器.lnk -> .venv\\Scripts\\pythonw.exe souti.py"""
import os, sys
import win32com.client
from win32com.shell import shell, shellcon

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pyw = os.path.join(APP, ".venv", "Scripts", "pythonw.exe")
script = os.path.join(APP, "souti.py")
icon = os.path.join(APP, "icon.ico")

desktop = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOPDIRECTORY, None, 0)
print("desktop:", desktop)
lnk_path = os.path.join(desktop, "反谋财害命器.lnk")

sh = win32com.client.Dispatch("WScript.Shell")
lnk = sh.CreateShortCut(lnk_path)
lnk.Targetpath = pyw
lnk.Arguments = f'"{script}"'
lnk.WorkingDirectory = APP
lnk.IconLocation = icon if os.path.exists(icon) else pyw
lnk.Description = "截图搜题浮窗：Ctrl+Alt+Q 框选题目，直接出答案"
lnk.WindowStyle = 1
lnk.save()
print("created:", lnk_path, os.path.exists(lnk_path))
