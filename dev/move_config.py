# -*- coding: utf-8 -*-
"""配置搬到 %LOCALAPPDATA%\\fhcmd\\config.json，并自动从旧位置迁移"""
import io

P = r"D:\hermes\261020搜题浮窗\souti.py"
s = io.open(P, encoding="utf-8", newline="").read()

old = 'CONFIG_PATH = APP_DIR / "config.json"'
new = '''CONFIG_DIR = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "fhcmd"
CONFIG_PATH = CONFIG_DIR / "config.json"
LEGACY_CONFIG = APP_DIR / "config.json"      # 旧版本放在 exe 旁边，首次启动自动搬过来'''
assert old in s
s = s.replace(old, new, 1)

# 迁移逻辑：放在 load_config 里读之前
old_load = '''        if CONFIG_PATH.exists():'''
new_load = '''        if (not CONFIG_PATH.exists()) and LEGACY_CONFIG.exists():
            try:
                CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                CONFIG_PATH.write_bytes(LEGACY_CONFIG.read_bytes())
            except Exception as e:
                print("配置迁移失败", e)
        if CONFIG_PATH.exists():'''
assert old_load in s
s = s.replace(old_load, new_load, 1)

# 保存时确保目录存在
old_save = '''        CONFIG_PATH.write_text('''
new_save = '''        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text('''
assert old_save in s
s = s.replace(old_save, new_save, 1)

# 版本
s = s.replace('__version__ = "1.3.4"', '__version__ = "1.3.5"')

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("配置迁移已接入；版本 ->", [l for l in s.splitlines() if l.startswith("__version__")][0])
