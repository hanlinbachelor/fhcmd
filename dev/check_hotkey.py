import ctypes
from ctypes import wintypes
u32 = ctypes.windll.user32
# 如果浮窗已经占用 Ctrl+Alt+Q，这里注册必然失败(=0)
ok = u32.RegisterHotKey(None, 99, 0x0002 | 0x0001, 0x51)
print("再注册 Ctrl+Alt+Q:", ok, "err:", ctypes.windll.kernel32.GetLastError())
if ok:
    u32.UnregisterHotKey(None, 99)
# 顺手看 Ctrl+Alt+S 是否空闲
ok2 = u32.RegisterHotKey(None, 98, 0x0002 | 0x0001, 0x53)
print("Ctrl+Alt+S 空闲:", bool(ok2))
if ok2:
    u32.UnregisterHotKey(None, 98)
