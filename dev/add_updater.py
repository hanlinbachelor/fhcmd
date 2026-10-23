# -*- coding: utf-8 -*-
"""给程序加“检查更新”（方案 A）"""
import io

P = r"D:\hermes\261020搜题浮窗\souti.py"
s = io.open(P, encoding="utf-8", newline="").read()
old_len = len(s)

# 1) 常量
if "UPDATE_URL" not in s:
    s = s.replace(
        'APP_NAME = "反谋财害命器"',
        'APP_NAME = "反谋财害命器"\n'
        'UPDATE_URL = "https://hanlinbachelor.github.io/fhcmd/versions.json"\n'
        'UPDATE_PAGE = "https://hanlinbachelor.github.io/fhcmd/"\n'
        'UPDATE_API = "https://api.github.com/repos/hanlinbachelor/fhcmd/releases/latest"'
    )

# 2) 版本比较 + 检查线程（插在 ConnTestThread 之前）
thread_code = '''def ver_tuple(v: str):
    try:
        return tuple(int(x) for x in str(v).lstrip("vV").split(".")[:3])
    except Exception:
        return (0,)


class UpdateThread(QThread):
    """后台查最新版本：先读站点 versions.json，失败再退到 GitHub API"""
    done = Signal(str, str)

    def run(self):
        import json
        latest = ""
        err = ""
        try:
            r = requests.get(UPDATE_URL, timeout=8, headers={"User-Agent": "fhcmd"})
            if r.ok:
                latest = (r.json() or {}).get("latest", "")
        except Exception as e:
            err = type(e).__name__
        if not latest:
            try:
                r = requests.get(UPDATE_API, timeout=8,
                                 headers={"User-Agent": "fhcmd", "Accept": "application/vnd.github+json"})
                if r.ok:
                    latest = (r.json() or {}).get("tag_name", "")
                    err = ""
            except Exception as e:
                err = err or type(e).__name__
        self.done.emit(latest or "", err)


class ConnTestThread(QThread):'''
s = s.replace("class ConnTestThread(QThread):", thread_code, 1)

# 3) 启动后静默检查
s = s.replace(
    "        QTimer.singleShot(1400, self._maybe_first_run)",
    "        QTimer.singleShot(1400, self._maybe_first_run)\n"
    "        QTimer.singleShot(6000, lambda: self.check_updates(True))"
)

# 4) 菜单项
s = s.replace(
    '        m.addAction("设置（接口 / 模型 / Key）…", self.open_settings)',
    '        m.addAction("检查更新…", lambda: self.check_updates(False))\n'
    '        m.addAction("设置（接口 / 模型 / Key）…", self.open_settings)'
)

# 5) 方法
methods = '''    # ---------- 检查更新（方案 A：只提示，不自动下载）
    def check_updates(self, silent=False):
        if getattr(self, "_upd_busy", False):
            return
        self._upd_busy = True
        self._upd_silent = silent
        if not silent:
            self.status.setText("正在检查更新…")
        self._upd_thread = UpdateThread()
        self._upd_thread.done.connect(self._on_update)
        self._upd_thread.start()

    def _on_update(self, latest, err):
        self._upd_busy = False
        silent = getattr(self, "_upd_silent", True)
        base = f"就绪 · v{__version__} · 按 Ctrl+Alt+Q 或点「框选」"
        if latest and ver_tuple(latest) > ver_tuple(__version__):
            self.status.setText(
                f'发现新版本 <b>{latest}</b> · <a href="{UPDATE_PAGE}" style="color:{self.th["accent"]};">去下载</a>')
            return
        if silent:
            self.status.setText(base)
            return
        if latest:
            self.status.setText(base)
            QMessageBox.information(self, "检查更新", f"已经是最新版本：v{__version__}")
        else:
            self.status.setText(base)
            QMessageBox.warning(self, "检查更新", f"检查失败（{err or '网络不可用'}），稍后再试")

    def open_settings(self):'''
s = s.replace("    def open_settings(self):", methods, 1)

# 6) 状态栏支持链接
s = s.replace(
    '        self.status = QLabel(f"就绪 · v{__version__} · 按 Ctrl+Alt+Q 或点「框选」")',
    '        self.status = QLabel(f"就绪 · v{__version__} · 按 Ctrl+Alt+Q 或点「框选」")\n'
    '        self.status.setOpenExternalLinks(True)\n'
    '        self.status.setTextInteractionFlags(Qt.TextBrowserInteraction)'
)

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("字节数", old_len, "->", len(s))
