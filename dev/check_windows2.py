# -*- coding: utf-8 -*-
"""列出本程序的所有窗口（主窗口/悬浮球）+ 状态，用来验证两档最小化"""
import ctypes
from ctypes import wintypes
u32 = ctypes.windll.user32
u32.SetProcessDPIAware()
EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def snap():
    rows = []

    def cb(h, lp):
        n = u32.GetWindowTextLengthW(h)
        if n:
            b = ctypes.create_unicode_buffer(n + 1)
            u32.GetWindowTextW(h, b, n + 1)
            t = b.value
            if "反谋财害命器" in t or t.strip() == "":
                pass
            if "反谋财害命器" in t:
                r = wintypes.RECT()
                u32.GetWindowRect(h, ctypes.byref(r))
                rows.append(("titled", t, r.left, r.top, r.right - r.left, r.bottom - r.top,
                             bool(u32.IsWindowVisible(h))))
        return True

    u32.EnumWindows(EnumProc(cb), 0)

    # 无标题的 Qt.Tool 小窗（悬浮球）只能按尺寸+进程找
    import subprocess, json
    pid_out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq pythonw.exe", "/FO", "CSV"],
                             capture_output=True, text=True, encoding="gbk", errors="ignore").stdout
    pids = set()
    for line in pid_out.splitlines()[1:]:
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) > 1 and parts[1].isdigit():
            pids.add(int(parts[1]))

    balls = []

    def cb2(h, lp):
        pid = wintypes.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if pid.value in pids and u32.IsWindowVisible(h):
            r = wintypes.RECT()
            u32.GetWindowRect(h, ctypes.byref(r))
            w, hh = r.right - r.left, r.bottom - r.top
            n = u32.GetWindowTextLengthW(h)
            if 90 <= w <= 140 and 90 <= hh <= 140 and n == 0:
                balls.append((r.left, r.top, w, hh))
        return True

    u32.EnumWindows(EnumProc(cb2), 0)
    return rows, balls


rows, balls = snap()
print("带标题窗口:", rows if rows else "无（主窗口已隐藏）")
print("悬浮球窗口:", balls if balls else "无")
