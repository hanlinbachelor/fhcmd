# -*- coding: utf-8 -*-
"""用视觉模型当"眼睛"检查浮窗的实际渲染效果（本机视觉aux不可用，改用 DeepSeek 视觉模型）"""
import os, sys, json, base64, io, ctypes
from ctypes import wintypes
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
from PySide6.QtCore import QRect
import requests
import souti

app = QApplication(sys.argv)
sc = app.primaryScreen()
full = sc.grabWindow(0).toImage()
print("desktop:", full.width(), full.height(), "dpr", sc.devicePixelRatio())
full.save("qa_desktop.png")

# 找窗口矩形
u32 = ctypes.windll.user32
EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
rect = []
def cb(hwnd, lp):
    n = u32.GetWindowTextLengthW(hwnd)
    if n:
        b = ctypes.create_unicode_buffer(n + 1)
        u32.GetWindowTextW(hwnd, b, n + 1)
        if "搜题" in b.value:
            r = wintypes.RECT(); u32.GetWindowRect(hwnd, ctypes.byref(r))
            rect.append((r.left, r.top, r.right, r.bottom))
    return True
u32.EnumWindows(EnumProc(cb), 0)
print("window rects:", rect)
if rect:
    dpr = sc.devicePixelRatio()
    l, t, r, b = rect[0]
    crop = full.copy(QRect(int(l*dpr), int(t*dpr), int((r-l)*dpr), int((b-t)*dpr)))
    crop.save("qa_window.png")
    print("cropped:", crop.width(), crop.height())

cfg = souti.load_config()
key, src = souti.resolve_api_key(cfg)
b64, mime = souti.encode_image(crop)
prompt = ("这是我自己写的 Windows 桌面浮窗程序（深色小窗，用于截图搜题）的实时截图。"
          "请只做界面质量检查并简短回答：1) 中文有没有乱码或方框字？2) 有没有文字被裁切、控件重叠、按钮挤在一起或空白区块？"
          "3) 排版是否整齐、可读？请逐条列出你看到的问题（没有就说没有），不要评价功能。")
payload = {"model": cfg["model"], "max_tokens": 2000, "direction": None,
           "messages": [{"role": "user", "content": [
               {"type": "text", "text": prompt},
               {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}]}]}
payload.pop("direction")
r = requests.post("https://api.deepseek.com/chat/completions",
                  headers={"Authorization": "Bearer " + key}, json=payload, timeout=180)
print("status", r.status_code)
j = r.json()
m = j["choices"][0]["message"]
print("--- reasoning(len %d) ---" % len(m.get("reasoning_content") or ""))
print(m.get("content") or m.get("reasoning_content"))
