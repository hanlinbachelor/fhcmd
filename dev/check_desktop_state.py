import ctypes
from ctypes import wintypes
u32, k32 = ctypes.windll.user32, ctypes.windll.kernel32
u32.SetProcessDPIAware()

# 1) 当前输入桌面（锁屏时会变成 Winlogon）
hdesk = u32.OpenInputDesktop(0, False, 0x0100)
name = ctypes.create_unicode_buffer(256)
need = wintypes.DWORD()
if hdesk:
    u32.GetUserObjectInformationW(hdesk, 2, name, 256*2, ctypes.byref(need))
print("input desktop:", name.value if hdesk else "FAILED(err=%d)" % k32.GetLastError())

# 2) 前台窗口
hw = u32.GetForegroundWindow()
b = ctypes.create_unicode_buffer(512); u32.GetWindowTextW(hw, b, 512)
print("foreground:", repr(b.value))

# 3) 所有可见顶层窗口标题
EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
rows = []
def cb(h, lp):
    if u32.IsWindowVisible(h):
        n = u32.GetWindowTextLengthW(h)
        if n:
            bb = ctypes.create_unicode_buffer(n+1); u32.GetWindowTextW(h, bb, n+1)
            r = wintypes.RECT(); u32.GetWindowRect(h, ctypes.byref(r))
            rows.append((bb.value, r.left, r.top, r.right-r.left, r.bottom-r.top))
    return True
u32.EnumWindows(EnumProc(cb), 0)
print("visible titled windows:", len(rows))
for t, x, y, w, h in rows[:25]:
    print("  %-40r %dx%d @ %d,%d" % (t[:40], w, h, x, y))
