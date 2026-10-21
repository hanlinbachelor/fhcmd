# -*- coding: utf-8 -*-
"""把本程序进程的所有顶层窗口全列出来（不管有没有标题/可见）"""
import ctypes, subprocess
from ctypes import wintypes
u32 = ctypes.windll.user32
u32.SetProcessDPIAware()
EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"],
                     capture_output=True, text=True, encoding="gbk", errors="ignore").stdout
pids = set()
for line in out.splitlines()[1:]:
    parts = [p.strip('"') for p in line.split('","')]
    if len(parts) > 1 and parts[1].isdigit():
        pids.add(int(parts[1]))
print("pythonw pids:", pids)


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD),
                ("hwndActive", wintypes.HWND), ("hwndFocus", wintypes.HWND),
                ("hwndCapture", wintypes.HWND), ("hwndMenuOwner", wintypes.HWND),
                ("hwndMoveSize", wintypes.HWND), ("hwndCaret", wintypes.HWND),
                ("rcCaret", wintypes.RECT)]

rows = []

def cb(h, lp):
    pid = wintypes.DWORD()
    u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
    if pid.value in pids:
        n = u32.GetWindowTextLengthW(h)
        b = ctypes.create_unicode_buffer(n + 1)
        u32.GetWindowTextW(h, b, n + 1)
        r = wintypes.RECT()
        u32.GetWindowRect(h, ctypes.byref(r))
        ex = u32.GetWindowLongW(h, -20)
        cls = ctypes.create_unicode_buffer(256)
        u32.GetClassNameW(h, cls, 256)
        rows.append((h, pid.value, b.value[:22], cls.value, r.left, r.top,
                     r.right - r.left, r.bottom - r.top, bool(u32.IsWindowVisible(h)),
                     bool(ex & 8), bool(ex & 0x80), bool(ex & 0x80000)))
    return True

u32.EnumWindows(EnumProc(cb), 0)
for r in rows:
    print("hwnd=%-9s pid=%-6s title=%-24r cls=%-22s %4dx%-4d @%5d,%-5d vis=%-5s topmost=%-5s tool=%-5s layered=%s" % r)
