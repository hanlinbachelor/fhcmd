# -*- coding: utf-8 -*-
"""对比三种抓屏方式的可用性: Qt grabWindow / GDI BitBlt / PIL ImageGrab"""
import os, sys, ctypes
from ctypes import wintypes
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
sc = app.primaryScreen()
W, H = 2560, 1600

def stats(img, tag):
    img = img.convert("L") if hasattr(img, "convert") else img
    b = img.tobytes()
    n = len(b)
    mn, mx = min(b), max(b)
    mean = sum(b) / n
    dark = sum(1 for v in b if v < 12) / n
    print(f"{tag}: min={mn} max={mx} mean={mean:.1f} 近黑占比={dark:.1%}")
    return mean, dark

# 1) Qt grabWindow
q = sc.grabWindow(0).toImage()
q.save("cap_qt.png")
print("qt size", q.width(), q.height())
from PIL import Image, ImageGrab
stats(Image.open("cap_qt.png"), "Qt grabWindow")

# 2) GDI BitBlt
user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
user32.SetProcessDPIAware()
hdesk = user32.GetDC(0)
mdc = gdi32.CreateCompatibleDC(hdesk)
bmp = gdi32.CreateCompatibleBitmap(hdesk, W, H)
gdi32.SelectObject(mdc, bmp)
ok = gdi32.BitBlt(mdc, 0, 0, W, H, hdesk, 0, 0, 0x00CC0020)

class BMI(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]

bi = BMI(ctypes.sizeof(BMI), W, -H, 1, 32, 0, 0, 0, 0, 0, 0)
buf = ctypes.create_string_buffer(W * H * 4)
lines = gdi32.GetDIBits(mdc, bmp, 0, H, buf, ctypes.byref(bi), 0)
img_gdi = Image.frombuffer("RGBA", (W, H), buf, "raw", "BGRA", 0, 1).convert("RGB")
img_gdi.save("cap_gdi.png")
print("gdi ok=", ok, "lines=", lines)
stats(img_gdi, "GDI BitBlt")

# 3) PIL ImageGrab
img = ImageGrab.grab(all_screens=False)
img.save("cap_pil.png")
print("pil size", img.size)
stats(img, "PIL ImageGrab")
