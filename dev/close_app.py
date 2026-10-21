import ctypes, sys, time
from ctypes import wintypes
u32 = ctypes.windll.user32
EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
hits = []
def cb(h, lp):
    n = u32.GetWindowTextLengthW(h)
    if n:
        b = ctypes.create_unicode_buffer(n + 1); u32.GetWindowTextW(h, b, n + 1)
        if b.value == "反谋财害命器":
            hits.append(h)
    return True
u32.EnumWindows(EnumProc(cb), 0)
print("found", len(hits))
for h in hits:
    u32.PostMessageW(h, 0x0010, 0, 0)   # WM_CLOSE -> 保存窗口位置并退出
time.sleep(1.5)
left = []
def cb2(h, lp):
    n = u32.GetWindowTextLengthW(h)
    if n:
        b = ctypes.create_unicode_buffer(n + 1); u32.GetWindowTextW(h, b, n + 1)
        if b.value == "反谋财害命器":
            left.append(h)
    return True
u32.EnumWindows(EnumProc(cb2), 0)
print("remaining", len(left))
