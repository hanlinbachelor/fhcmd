import ctypes, sys
from ctypes import wintypes

u32 = ctypes.windll.user32
u32.SetProcessDPIAware()

EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
found = []

def cb(hwnd, lparam):
    n = u32.GetWindowTextLengthW(hwnd)
    if n:
        buf = ctypes.create_unicode_buffer(n + 1)
        u32.GetWindowTextW(hwnd, buf, n + 1)
        t = buf.value
        if "反谋财害命器" in t:
            r = wintypes.RECT()
            u32.GetWindowRect(hwnd, ctypes.byref(r))
            ex = u32.GetWindowLongW(hwnd, -20)
            style = u32.GetWindowLongW(hwnd, -16)
            found.append((hwnd, t, r.left, r.top, r.right - r.left, r.bottom - r.top,
                          bool(ex & 0x00000008), bool(u32.IsWindowVisible(hwnd)),
                          hex(style), hex(ex)))
    return True

u32.EnumWindows(EnumProc(cb), 0)
print("matched windows:", len(found))
for f in found:
    print("hwnd=%s title=%r rect=(%d,%d,%dx%d) topmost=%s visible=%s style=%s ex=%s" % f)
if not found:
    sys.exit(2)
