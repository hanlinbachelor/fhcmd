# -*- coding: utf-8 -*-
"""列出本程序（python.exe / pythonw.exe）的所有顶层窗口，用于验证最小化状态"""
import ctypes
from ctypes import wintypes
u32 = ctypes.windll.user32
u32.SetProcessDPIAware()
EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def pids_of(exe):
    import subprocess
    try:
        out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {exe}", "/FO", "CSV"],
                             capture_output=True, text=True, encoding="gbk", errors="ignore").stdout
    except Exception:
        return set()
    s = set()
    for line in out.splitlines()[1:]:
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) > 1 and parts[1].isdigit():
            s.add(int(parts[1]))
    return s


pids = pids_of("python.exe") | pids_of("pythonw.exe")
rows = []


def cb(h, lp):
    pid = wintypes.DWORD()
    u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
    if pid.value in pids:
        cls = ctypes.create_unicode_buffer(128)
        u32.GetClassNameW(h, cls, 128)
        if not cls.value.startswith(("Qt6120", "_q_")):
            return True
        n = u32.GetWindowTextLengthW(h)
        b = ctypes.create_unicode_buffer(n + 1)
        u32.GetWindowTextW(h, b, n + 1)
        r = wintypes.RECT()
        u32.GetWindowRect(h, ctypes.byref(r))
        ex = u32.GetWindowLongW(h, -20)
        rows.append((cls.value, b.value[:18], r.left, r.top, r.right - r.left, r.bottom - r.top,
                     bool(u32.IsWindowVisible(h)), bool(ex & 8)))
    return True


u32.EnumWindows(EnumProc(cb), 0)
for r in rows:
    print("cls=%-42s title=%-20r %4dx%-4d @%5d,%-5d vis=%-5s topmost=%s" % r)
if not rows:
    print("没有找到任何程序窗口（可能已退出）")
