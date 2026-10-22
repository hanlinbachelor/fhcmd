# -*- coding: utf-8 -*-
"""
搜题浮窗 (souti.py)
-------------------
一个不依赖浏览器的 Windows 桌面浮窗：始终置顶、随便拖动，按 Ctrl+Alt+Q 框选屏幕任意区域，
程序把选区原图交给视觉大模型 -> 识别题目 -> 直接给出答案 / 解析 / 考点。

依赖: PySide6-Essentials, requests  (已装在 .venv)
配置: 同目录 config.json
运行: 双击「启动搜题浮窗.bat」或 .venv\Scripts\pythonw.exe souti.py
"""
import base64
import io
import json
import os
import re
import sys
import time
import ctypes
from ctypes import wintypes
from pathlib import Path

import requests
from PySide6.QtCore import (Qt, QRect, QRectF, QPoint, QSize, QThread, Signal, QTimer,
                            QBuffer, QIODevice, QByteArray, QStandardPaths)
from PySide6.QtGui import (QImage, QPixmap, QPainter, QColor, QPen, QFont,
                           QGuiApplication, QCursor, QPainterPath, QTextCursor,
                           QClipboard, QIcon, QKeySequence, QPalette,
                           QActionGroup, QLinearGradient)
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QTextBrowser, QLineEdit,
                               QSizeGrip, QToolButton, QFrame, QMessageBox,
                               QSystemTrayIcon, QMenu, QDialog)

__version__ = "1.2.2"
APP_NAME = "反谋财害命器"

BACKDROP_DOWNSCALE = 8          # 抓来的背景先缩小再放大 = 廉价高斯模糊

def _app_dir() -> Path:
    """打包成 exe 后 __file__ 在临时解包目录里，配置必须放在 exe 旁边，否则每次重启都丢"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = _app_dir()
CONFIG_PATH = APP_DIR / "config.json"
HISTORY_DIR = APP_DIR / "history"

DEFAULT_CFG = {
    "api_base": "https://api.deepseek.com",
    "model": "deepseek-v4-flash-vision-exp",
    "api_key": "",
    "api_key_env": ["HERMES_CUSTOM_API_DEEPSEEK_COM_API_KEY", "DEEPSEEK_API_KEY"],
    "hotkey": "ctrl+alt+q",
    "theme": "laser",
    "max_tokens": 4000,
    "temperature": 0.2,
    "window": {"x": 820, "y": 60, "w": 440, "h": 620, "collapsed": False},
}

# ---------------------------------------------------------------- 外观主题
# 加新主题只需要在这里加一项：card_fill/panel/按钮都用 rgba 字符串或 (r,g,b,a) 元组
THEMES = {
    "laser": {
        "label": "镭射",
        "desc": "青蓝霓虹 · 深空黑，截图准星也是这一套色",
        "accent": (80, 235, 255),
        "font_ui": "Noto Sans SC",
        "font_body": "Noto Sans SC",
        "ans_bg": "rgba(80, 235, 255, 44)",
        "ans_border": "rgba(110, 232, 255, 175)",
        "ans_tag": "#a6ecff",
        "card_fill": (22, 25, 32, 246),
        "card_border": (96, 170, 255, 110),
        "glass": False,
        "gloss_top": 0,
        "edge": 0,
        "panel_bg": "rgba(13, 16, 21, 235)",
        "panel_border": "rgba(255,255,255,24)",
        "text": "#dfe8f5",
        "title": "#eaf2ff",
        "subtext": "#a3b9d4",
        "placeholder": "#9aafc8",
        "btn_bg": "rgba(58, 96, 150, 210)",
        "btn_hover": "rgba(74, 126, 196, 235)",
        "btn_press": "rgba(44, 76, 122, 240)",
        "btn_disabled": "rgba(70,78,90,140)",
        "btn_text": "#eef5ff",
        "focus_border": "rgba(96,170,255,150)",
        "selection": "#2f6fb5",
        "menu_bg": "#171b22",
        "menu_sel": "rgba(74,126,196,235)",
        "menu_border": "rgba(96,170,255,110)",
        "ball_fill": (20, 23, 30, 246),
        "ball_ring": (80, 235, 255, 235),
        "ball_inner": (80, 235, 255, 110),
        "ball_cross": (80, 235, 255, 255),
    },
    "morandi": {
        "label": "液态玻璃",
        "desc": "低饱和灰调 · 燕麦白字，背景真模糊 + 顶部高光 + 内缘亮边",
        "accent": (169, 192, 207),
        "font_ui": "Noto Sans SC",
        "font_body": "Noto Sans SC",
        "ans_bg": "rgba(169, 192, 207, 58)",
        "ans_border": "rgba(200, 216, 228, 170)",
        "ans_tag": "#dde7ee",
        "card_fill": (48, 52, 60, 166),          # 盖在"已模糊的背影"上的灰调色
        "card_border": (255, 255, 255, 58),
        "glass": True,
        "gloss_top": 40,                        # 顶部高光不透明度
        "edge": 112,                             # 内缘亮边不透明度
        "panel_bg": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(44,48,56,136), stop:0.45 rgba(26,29,35,120), stop:1 rgba(16,19,24,148))",
        "panel_border": "rgba(255,255,255,40)",
        "text": "#efeae2",
        "title": "#f8f4ed",
        "subtext": "#d0c9be",
        "placeholder": "#d8d1c7",
        "btn_bg": "rgba(156, 170, 182, 160)",
        "btn_hover": "rgba(180, 194, 206, 200)",
        "btn_press": "rgba(136, 149, 161, 215)",
        "btn_disabled": "rgba(96, 100, 106, 130)",
        "btn_text": "#faf7f2",
        "focus_border": "rgba(200, 214, 224, 185)",
        "selection": "#7d93a3",
        "menu_bg": "#3a3e45",
        "menu_sel": "rgba(156,170,182,195)",
        "menu_border": "rgba(255,255,255,66)",
        "ball_fill": (50, 54, 61, 238),
        "ball_ring": (176, 198, 212, 235),
        "ball_inner": (176, 198, 212, 90),
        "ball_cross": (234, 230, 222, 255),
    },
}

SYSTEM_PROMPT = """你是一名严谨、准确的中文搜题／解题助手。用户发给你的是屏幕截图，内容可能是题目、试卷、教材、课件或代码题。

请严格按下面格式输出 Markdown（三个标题都要有）：

### 题目
原样抄录图中题目文字。公式用 $...$ 行内 LaTeX。多道题用 "**1.**" "**2.**" 分列。看不清的字用一个 ▢ 代替，绝不猜测补全。

### 答案
先给最终结论：选择题写选项字母并附该选项原文；填空题写应填内容；计算／解答题写最终结果。

### 解析
简明步骤与关键公式，三四行内说清；不要重复题干。

### 考点
一行：考什么、常见错误是什么。

硬性规则：
1. 看不清或信息不足时，直接写“图中信息不足，缺少××”，绝不编造题干、数字或选项。
2. 若图中没有题目（只是普通文字、网页、代码、界面），先转写可见文字，再说明“图中未发现题目”。
3. 全部简体中文；数学式子用 LaTeX；不要客套话、不要解释你在做什么。"""


_SEC_KEYS = ("题目", "答案", "解析", "考点")


def split_sections(text: str) -> dict:
    """把模型输出按 题目/答案/解析/考点 拆开（兼容 ### 标题 与 **标题** 两种写法）"""
    t = re.sub(r"^\s*\*\*(题目|答案|解析|考点)\s*[:：]?\s*\*\*\s*$", r"### \1", text, flags=re.M)
    ms = list(re.finditer(r"^\s*#{1,4}\s*(题目|答案|解析|考点)\s*$", t, re.M))
    out = {}
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(t)
        out[m.group(1)] = t[m.end():end].strip()
    return out


def md_inline(s: str) -> str:
    """极简 markdown -> HTML：转义、**粗体**、`代码`、换行"""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<span style='background:rgba(127,127,127,45);'>\1</span>", s)
    return s.replace("\n", "<br>")


# ---------------------------------------------------------------- 配置
def load_config():
    cfg = json.loads(json.dumps(DEFAULT_CFG))
    try:
        if CONFIG_PATH.exists():
            user = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            for k, v in user.items():
                if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                    cfg[k].update(v)
                else:
                    cfg[k] = v
    except Exception as e:
        print("config.json 读取失败，用默认配置:", e)
    return cfg


def save_config(cfg):
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print("config 保存失败:", e)


def _scan_env_file(path, key):
    try:
        for line in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == key:
                return v.strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def resolve_api_key(cfg):
    """优先级: config.json > 配置里列出的环境变量 > Hermes 的 .env（可选）"""
    if cfg.get("api_key", "").strip():
        return cfg["api_key"].strip(), "config.json"
    # 可自定义：config.json 里写 "api_key_env": ["MY_KEY", ...]
    names = cfg.get("api_key_env") or ["HERMES_CUSTOM_API_DEEPSEEK_COM_API_KEY",
                                       "DEEPSEEK_API_KEY", "OPENAI_API_KEY"]
    if isinstance(names, str):
        names = [names]
    for n in names:
        if os.environ.get(n):
            return os.environ[n].strip(), "环境变量 " + n
    cands = []
    la = os.environ.get("LOCALAPPDATA")
    if la:
        cands.append(Path(la) / "hermes" / ".env")
    cands.append(Path.home() / ".hermes" / ".env")
    cands.append(Path.home() / "AppData" / "Local" / "hermes" / ".env")
    for p in cands:
        for n in names:
            v = _scan_env_file(p, n)
            if v:
                return v, f"{p} 里的 {n}"
    return "", "未找到"


# ---------------------------------------------------------------- 图片编码
def encode_image(img: QImage):
    """QImage -> (base64, mime)。太小放大（利于认出小字），太大缩到 1600px，超 1.4MB 转 JPEG。"""
    w, h = img.width(), img.height()
    longest = max(w, h)
    im = img
    if longest < 900:                      # 小图放大
        f = min(3.0, 900.0 / max(1, longest))
        im = img.scaled(int(w * f), int(h * f), Qt.KeepAspectRatio, Qt.SmoothTransformation)
    elif longest > 1600:
        im = img.scaled(1600, 1600, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    im.save(buf, "PNG")
    buf.close()
    data = bytes(ba)
    if len(data) > 1_400_000:              # 太大改 JPEG
        ba2 = QByteArray()
        b2 = QBuffer(ba2)
        b2.open(QIODevice.WriteOnly)
        im.save(b2, "JPG", 92)
        b2.close()
        return base64.b64encode(bytes(ba2)).decode(), "image/jpeg"
    return base64.b64encode(data).decode(), "image/png"


# ---------------------------------------------------------------- 网络请求线程
class AskThread(QThread):
    """把 图/文 发给视觉模型，流式把结果丢回界面。"""
    chunk = Signal(str)
    reasoning = Signal(int)          # 已思考的字符数（仅用于进度提示）
    done = Signal(str, dict)
    failed = Signal(str)

    def __init__(self, cfg, api_key, messages, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.api_key = api_key
        self.messages = messages
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        url = self.cfg["api_base"].rstrip("/") + "/chat/completions"
        payload = {
            "model": self.cfg["model"],
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + self.messages,
            "max_tokens": int(self.cfg.get("max_tokens", 4000)),
            "temperature": float(self.cfg.get("temperature", 0.2)),
            "stream": True,
        }
        headers = {"Authorization": "Bearer " + self.api_key,
                   "Content-Type": "application/json"}
        buf, think, usage = [], 0, {}
        try:
            with requests.post(url, headers=headers, json=payload,
                               stream=True, timeout=(15, 300)) as r:
                if r.status_code != 200:
                    try:
                        detail = r.text[:600]
                    except Exception:
                        detail = ""
                    hint = {401: "API Key 无效/过期，检查 config.json 或 .env",
                            402: "余额不足",
                            429: "请求太频繁或额度用尽，稍后再试"}.get(r.status_code, "")
                    self.failed.emit(f"HTTP {r.status_code} {hint}\n{detail}")
                    return
                for raw in r.iter_lines(decode_unicode=False):
                    if self._cancel:
                        break
                    if not raw:
                        continue
                    line = raw.decode("utf-8", "ignore").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                    except Exception:
                        continue
                    if obj.get("usage"):
                        usage = obj["usage"]
                    ch = (obj.get("choices") or [{}])[0]
                    delta = ch.get("delta") or {}
                    rc = delta.get("reasoning_content")
                    if rc:
                        think += len(rc)
                        self.reasoning.emit(think)
                    c = delta.get("content")
                    if c:
                        buf.append(c)
                        self.chunk.emit(c)
            text = "".join(buf).strip()
            if self._cancel and not text:
                text = "（已停止）"
            if not text:
                text = "（模型没有返回内容，可能是额度或模型不支持图片输入）"
            self.done.emit(text, usage)
        except requests.exceptions.Timeout:
            self.failed.emit("请求超时（可能是网络/代理问题，或模型响应太慢）")
        except Exception as e:
            self.failed.emit(f"{type(e).__name__}: {e}")


# ---------------------------------------------------------------- 截图选区
def grab_virtual_desktop():
    """抓整个虚拟桌面（多屏合并），返回 (QImage物理像素, 缩放比例, 虚拟矩形逻辑坐标)"""
    app = QApplication.instance()
    scr0 = app.primaryScreen()
    vg = scr0.virtualGeometry()
    screens = app.screens()
    scale = max([s.devicePixelRatio() or 1.0 for s in screens] or [1.0])
    W, H = max(1, int(round(vg.width() * scale))), max(1, int(round(vg.height() * scale)))
    canvas = QImage(W, H, QImage.Format_RGB32)
    canvas.fill(QColor(0, 0, 0))
    p = QPainter(canvas)
    p.setRenderHint(QPainter.SmoothPixmapTransform, False)
    for s in screens:
        g = s.geometry()
        img = s.grabWindow(0).toImage()
        if img.isNull():
            continue
        dst = QRect(int(round((g.x() - vg.x()) * scale)), int(round((g.y() - vg.y()) * scale)),
                    int(round(g.width() * scale)), int(round(g.height() * scale)))
        p.drawImage(dst, img, QRect(0, 0, img.width(), img.height()))
    p.end()
    return canvas, scale, vg


class RegionCatcher(QWidget):
    """全屏暗化浮层，拖框选区；Esc/右键取消。光标=大号准星十字线（不落盘）"""
    captured = Signal(QImage)
    cancelled = Signal()

    def __init__(self, accent=(80, 235, 255)):
        super().__init__()
        self.accent = accent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setCursor(Qt.BlankCursor)      # 隐藏系统小箭头，自己画大准星
        self.setMouseTracking(True)
        self.canvas, self.scale, self.vg = grab_virtual_desktop()
        self.setGeometry(self.vg)
        self.p0 = None
        self.p1 = None
        self.cur = QPoint(self.width() // 2, self.height() // 2)

    # ---- 准星：细黑描边 + 主题强调色芯，屏幕任意底色都看得清
    def _acc(self, alpha=255, boost=0):
        r, g, b = self.accent
        return QColor(min(255, int(r) + boost), min(255, int(g) + boost),
                      min(255, int(b) + boost), alpha)

    def _draw_reticle(self, p: QPainter, pt: QPoint):
        x, y = pt.x(), pt.y()
        w, h = self.width(), self.height()
        for col, width in ((QColor(0, 0, 0, 160), 4), (self._acc(255), 2)):
            p.setPen(QPen(col, width))
            p.drawLine(0, y, w, y)
            p.drawLine(x, 0, x, h)
        # 中心圆环 + 四个刻度
        for col, width, r in ((QColor(0, 0, 0, 180), 6, 16), (self._acc(255), 3, 16),
                              (QColor(0, 0, 0, 180), 6, 5), (QColor(255, 255, 255, 255), 3, 5)):
            p.setPen(QPen(col, width))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(pt, r, r)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            p.setPen(QPen(QColor(0, 0, 0, 180), 6))
            p.drawLine(x + dx * 24, y + dy * 24, x + dx * 44, y + dy * 44)
            p.setPen(QPen(self._acc(255), 3))
            p.drawLine(x + dx * 24, y + dy * 24, x + dx * 44, y + dy * 44)

    def _draw_tick(self, p: QPainter, pt: QPoint, r: int = 12):
        """拖动时用的小十字（自带深色描边，压在任何底色上都可见）"""
        for col, width in ((QColor(0, 0, 0, 180), 4), (self._acc(250), 2)):
            p.setPen(QPen(col, width))
            p.drawLine(pt.x() - r, pt.y(), pt.x() + r, pt.y())
            p.drawLine(pt.x(), pt.y() - r, pt.x(), pt.y() + r)

    def paintEvent(self, _):
        p = QPainter(self)
        w, h = self.width(), self.height()
        p.drawImage(QRect(0, 0, w, h), self.canvas, QRect(0, 0, self.canvas.width(), self.canvas.height()))
        p.fillRect(self.rect(), QColor(10, 12, 16, 130))
        if self.p0 and self.p1:
            sel = QRect(self.p0, self.p1).normalized()
            src = QRect(int(sel.x() * self.scale), int(sel.y() * self.scale),
                        max(1, int(sel.width() * self.scale)), max(1, int(sel.height() * self.scale)))
            p.drawImage(sel, self.canvas, src)
            p.setPen(QPen(self._acc(255), 2))
            p.drawRect(sel.adjusted(0, 0, -1, -1))
            # 四角加粗
            p.setPen(QPen(QColor(255, 255, 255, 230), 4))
            L = min(18, sel.width() // 2, sel.height() // 2)
            for cx, cy, dx, dy in ((sel.left(), sel.top(), 1, 1), (sel.right(), sel.top(), -1, 1),
                                   (sel.left(), sel.bottom(), 1, -1), (sel.right(), sel.bottom(), -1, -1)):
                p.drawLine(cx, cy, cx + dx * L, cy)
                p.drawLine(cx, cy, cx, cy + dy * L)
            txt = f"{src.width()} × {src.height()} px"
            p.setFont(QFont("Noto Sans SC", 10, QFont.Bold))
            fm = p.fontMetrics()
            tw, th = fm.horizontalAdvance(txt) + 16, fm.height() + 8
            bx = min(max(4, sel.left() + 4), w - tw - 4)
            by = sel.top() - th - 6 if sel.top() - th - 6 > 4 else sel.bottom() + 6
            p.fillRect(QRect(bx, by, tw, th), QColor(12, 16, 22, 230))
            p.setPen(self._acc(255, 40))
            p.drawText(QRect(bx, by, tw, th), Qt.AlignCenter, txt)
            # 拖动中也保留一个小十字，避免看不见鼠标
            self._draw_tick(p, self.cur)
        else:
            self._draw_reticle(p, self.cur)
            # 光标旁坐标
            p.setFont(QFont("Consolas", 9))
            fm = p.fontMetrics()
            txt = f"{int(self.cur.x()*self.scale)}, {int(self.cur.y()*self.scale)}"
            tw, th = fm.horizontalAdvance(txt) + 10, fm.height() + 4
            bx = min(self.cur.x() + 34, w - tw - 4)
            by = min(self.cur.y() + 34, h - th - 4)
            p.fillRect(QRect(bx, by, tw, th), QColor(12, 16, 22, 210))
            p.setPen(self._acc(255, 60))
            p.drawText(QRect(bx, by, tw, th), Qt.AlignCenter, txt)
            p.setPen(QColor(235, 240, 250))
            p.setFont(QFont("Noto Sans SC", 13))
            p.drawText(self.rect().adjusted(0, 40, 0, 0), Qt.AlignHCenter | Qt.AlignTop,
                       "按住鼠标左键框选题目区域   ·   Esc / 右键取消")

    def mousePressEvent(self, e):
        self.cur = e.position().toPoint()
        if e.button() == Qt.LeftButton:
            self.p0 = e.position().toPoint()
            self.p1 = self.p0
            self.update()
        elif e.button() == Qt.RightButton:
            self.cancelled.emit()
            self.close()

    def mouseMoveEvent(self, e):
        self.cur = e.position().toPoint()
        if self.p0:
            self.p1 = self.cur
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton or not self.p0:
            return
        sel = QRect(self.p0, e.position().toPoint()).normalized()
        self.p0 = None
        if sel.width() < 8 or sel.height() < 8:
            return                      # 误触，继续选
        src = QRect(int(sel.x() * self.scale), int(sel.y() * self.scale),
                    max(1, int(sel.width() * self.scale)), max(1, int(sel.height() * self.scale)))
        crop = self.canvas.copy(src)
        self.captured.emit(crop)
        self.close()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.cancelled.emit()
            self.close()


# ---------------------------------------------------------------- 全局热键
class SettingsDialog(QDialog):
    """设置接口地址 / 模型 / API Key —— 让拿到安装包的人自己填，不用手改 JSON"""

    def __init__(self, parent, cfg):
        super().__init__(None)                       # 不挂父窗口：否则会被置顶的浮窗压住
        self.cfg = cfg
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.Dialog, True)
        self.setWindowTitle("设置 · 反谋财害命器")
        self.setModal(True)
        self.setMinimumWidth(430)
        self.setStyleSheet(parent.styleSheet() if parent else "")
        self._place_near(parent)

        form = QVBoxLayout(self)
        form.setContentsMargins(18, 16, 18, 14)
        form.setSpacing(10)

        tip = QLabel("填你自己的接口和 Key（程序不会上传，只存在本机 config.json）")
        tip.setWordWrap(True)
        tip.setObjectName("status")
        form.addWidget(tip)

        def row(label, widget, hint=None):
            lab = QLabel(label)
            lab.setObjectName("title")
            form.addWidget(lab)
            form.addWidget(widget)
            if hint:
                h = QLabel(hint)
                h.setObjectName("status")
                h.setWordWrap(True)
                form.addWidget(h)

        self.ed_base = QLineEdit(cfg.get("api_base", ""))
        self.ed_base.setPlaceholderText("https://api.deepseek.com")
        row("接口地址 api_base", self.ed_base, "OpenAI 兼容的 /chat/completions 地址；DeepSeek 填 https://api.deepseek.com")

        self.ed_model = QLineEdit(cfg.get("model", ""))
        self.ed_model.setPlaceholderText("deepseek-v4-flash-vision-exp")
        row("模型 model", self.ed_model, "必须是支持图片输入的模型，否则读不了截图")

        self.ed_key = QLineEdit(cfg.get("api_key", ""))
        self.ed_key.setEchoMode(QLineEdit.Password)
        self.ed_key.setPlaceholderText("sk-...")
        row("API Key api_key", self.ed_key, "在模型服务商后台创建；只保存在本机，不会发给我们")

        btns = QHBoxLayout()
        self.lb_test = QLabel("")
        self.lb_test.setObjectName("status")
        btns.addWidget(self.lb_test, 1)

        b_test = QPushButton("测试连接")
        b_test.clicked.connect(self.test)
        btns.addWidget(b_test)
        b_cancel = QPushButton("取消")
        b_cancel.clicked.connect(self.reject)
        btns.addWidget(b_cancel)
        b_save = QPushButton("保存")
        b_save.setDefault(True)
        b_save.clicked.connect(self.save)
        btns.addWidget(b_save)
        form.addLayout(btns)

    # ---------- 位置：尽量放在浮窗左侧空地，放不下就居中
    def _place_near(self, parent):
        scr = QGuiApplication.primaryScreen()
        if not scr:
            return
        a = scr.availableGeometry()
        self.adjustSize()
        w, h = max(self.width(), 440), max(self.height(), 380)
        if parent is not None:
            g = parent.frameGeometry()
            x = g.left() - w - 16
            if x < a.left() + 8:                     # 左边放不下 → 放右边
                x = g.right() + 16
            if x + w > a.right() - 8:                # 两边都放不下 → 居中
                x = a.center().x() - w // 2
            y = min(max(g.top(), a.top() + 8), a.bottom() - h - 8)
        else:
            x = a.center().x() - w // 2
            y = a.center().y() - h // 2
        self.move(int(x), int(y))

    def showEvent(self, e):
        super().showEvent(e)
        self.raise_()
        self.activateWindow()
        QTimer.singleShot(60, self.raise_)           # 再抬一次，防止被置顶窗口压住

    # ---------- 动作
    def _collect(self):
        self.cfg["api_base"] = self.ed_base.text().strip() or self.cfg.get("api_base", "")
        self.cfg["model"] = self.ed_model.text().strip() or self.cfg.get("model", "")
        self.cfg["api_key"] = self.ed_key.text().strip()

    def save(self):
        self._collect()
        if not self.cfg["api_base"] or not self.cfg["model"]:
            self.lb_test.setText("接口地址和模型不能为空")
            return
        save_config(self.cfg)
        self.accept()

    def test(self):
        self._collect()
        if not self.cfg["api_key"]:
            self.lb_test.setText("先填 Key 再测")
            return
        self.lb_test.setText("测试中…")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            r = requests.post(
                self.cfg["api_base"].rstrip("/") + "/chat/completions",
                headers={"Authorization": f"Bearer {self.cfg['api_key']}",
                         "Content-Type": "application/json"},
                json={"model": self.cfg["model"], "max_tokens": 8,
                      "messages": [{"role": "user", "content": "ping"}]},
                timeout=20)
            if r.status_code == 200:
                self.lb_test.setText("✅ 连接正常，可以保存了")
            elif r.status_code in (401, 403):
                self.lb_test.setText(f"❌ Key 不对或无权限（{r.status_code}）")
            elif r.status_code == 402:
                self.lb_test.setText("❌ 余额不足（402）")
            else:
                self.lb_test.setText(f"⚠ 服务返回 {r.status_code}：{r.text[:60]}")
        except Exception as e:
            self.lb_test.setText(f"❌ 连不上：{type(e).__name__}")
        finally:
            QApplication.restoreOverrideCursor()


class HotkeyThread(QThread):
    triggered = Signal()

    MOD = {"alt": 0x0001, "ctrl": 0x0002, "shift": 0x0004, "win": 0x0008}
    VK = {"q": 0x51, "a": 0x41, "s": 0x53, "w": 0x57, "e": 0x45, "d": 0x44,
          "f": 0x46, "z": 0x5A, "x": 0x58, "c": 0x43, "v": 0x56, "1": 0x31,
          "space": 0x20, "`": 0xC0}

    def __init__(self, spec="ctrl+alt+q", parent=None):
        super().__init__(parent)
        self.spec = (spec or "").lower().replace(" ", "")
        self.thread_id = 0
        self.ok = False

    def parse(self):
        mods = 0
        vk = 0
        for part in self.spec.split("+"):
            if part in self.MOD:
                mods |= self.MOD[part]
            elif part in self.VK:
                vk = self.VK[part]
        return mods, vk

    def run(self):
        mods, vk = self.parse()
        if not vk:
            return
        u32 = ctypes.windll.user32
        self.thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        self.ok = bool(u32.RegisterHotKey(None, 1, mods | 0x4000, vk))
        if not self.ok:
            return
        msg = wintypes.MSG()
        try:
            while u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == 0x0312:
                    self.triggered.emit()
        finally:
            u32.UnregisterHotKey(None, 1)

    def stop(self):
        try:
            if self.thread_id:
                ctypes.windll.user32.PostThreadMessageW(self.thread_id, 0x0012, 0, 0)
        except Exception:
            pass


# ---------------------------------------------------------------- 拖动条
class DragBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self._off = None
        self.setFixedHeight(38)
        self.setCursor(Qt.SizeAllCursor)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._off = e.globalPosition().toPoint() - self.window().pos()

    def mouseMoveEvent(self, e):
        if self._off is not None:
            self.window().move(e.globalPosition().toPoint() - self._off)

    def mouseReleaseEvent(self, e):
        self._off = None

    def mouseDoubleClickEvent(self, e):
        w = self.window()
        if hasattr(w, "minimize_to_ball"):
            w.minimize_to_ball()


# ---------------------------------------------------------------- 悬浮小球（第一档最小化）
class FloatBall(QWidget):
    """贴边小球：单击展开窗口，右键菜单，拖动自动吸边"""
    clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.resize(58, 58)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("单击展开 · 右键菜单 · 可拖动（松手自动吸附屏幕边缘）")
        self.menu = None
        self._press = None
        self._moved = False
        self.th = THEMES["laser"]

    def set_theme(self, th):
        self.th = th
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = self.rect().adjusted(3, 3, -3, -3)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 90))
        p.drawEllipse(r.translated(0, 3))
        p.setBrush(QColor(*self.th["ball_fill"]))
        p.setPen(QPen(QColor(*self.th["ball_ring"]), 2))
        p.drawEllipse(r)
        p.setPen(QPen(QColor(*self.th["ball_inner"]), 1))
        p.drawEllipse(r.adjusted(6, 6, -6, -6))
        c = r.center()
        p.setPen(QPen(QColor(*self.th["ball_cross"]), 2))
        p.drawLine(c.x() - 13, c.y(), c.x() - 5, c.y())
        p.drawLine(c.x() + 5, c.y(), c.x() + 13, c.y())
        p.drawLine(c.x(), c.y() - 13, c.x(), c.y() - 5)
        p.drawLine(c.x(), c.y() + 5, c.x(), c.y() + 13)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 255))
        p.drawEllipse(c, 3, 3)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._press = e.globalPosition().toPoint() - self.pos()
            self._moved = False

    def mouseMoveEvent(self, e):
        if self._press is not None:
            new = e.globalPosition().toPoint() - self._press
            if (new - self.pos()).manhattanLength() > 4:
                self._moved = True
            self.move(new)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self._press is not None:
            self._press = None
            if self._moved:
                self.snap_to_edge()
            else:
                self.clicked.emit()

    def contextMenuEvent(self, e):
        if self.menu:
            self.menu.popup(e.globalPos())

    # ---- 吸附到最近的一条边
    def snap_to_edge(self):
        scr = QGuiApplication.screenAt(self.frameGeometry().center()) or QGuiApplication.primaryScreen()
        if not scr:
            return
        a = scr.availableGeometry()
        g = self.frameGeometry()
        left_d, right_d = abs(g.left() - a.left()), abs(a.right() - g.right())
        x = a.left() + 4 if left_d < right_d else a.right() - self.width() - 4
        y = min(max(self.y(), a.top() + 4), a.bottom() - self.height() - 4)
        self.move(x, y)

    def place_near(self, rect):
        """从浮窗收起时：球贴到离浮窗最近的那条屏幕侧边，高度对齐浮窗"""
        scr = QGuiApplication.primaryScreen()
        a = scr.availableGeometry() if scr else QRect(0, 0, 1280, 800)
        cx = rect.center().x()
        x = a.left() + 4 if cx < a.center().x() else a.right() - self.width() - 4
        y = min(max(rect.top() + 40, a.top() + 4), a.bottom() - self.height() - 4)
        self.move(x, y)


def enable_acrylic(hwnd, tint=(40, 44, 50), alpha=150):
    """Windows 10/11 亚克力模糊（真·背景虚化）。失败返回 False，UI 自己回退成不透明雾面。"""
    class ACCENTPOLICY(ctypes.Structure):
        _fields_ = [("AccentState", ctypes.c_int), ("AccentFlags", ctypes.c_int),
                    ("GradientColor", ctypes.c_uint), ("AnimationId", ctypes.c_int)]

    class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
        _fields_ = [("Attribute", ctypes.c_int), ("Data", ctypes.c_void_p),
                    ("SizeOfData", ctypes.c_size_t)]

    try:
        u32 = ctypes.windll.user32
        if not hasattr(u32, "SetWindowCompositionAttribute"):
            return False
        r, g, b = tint
        grad = (int(alpha) << 24) | (b << 16) | (g << 8) | r      # ABGR
        accent = ACCENTPOLICY(4, 2, grad, 0)                        # 4 = ACRYLICBLURBEHIND
        data = WINDOWCOMPOSITIONATTRIBDATA(
            19, ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p), ctypes.sizeof(accent))
        return bool(u32.SetWindowCompositionAttribute(int(hwnd), ctypes.byref(data)))
    except Exception:
        return False


def set_round_region(win, radius=14, on=True):
    """把窗口本身裁成圆角（亚克力模糊只认矩形，不裁就会在圆角外露出四个直角）。
       on=False 时清掉 Region，恢复 Qt 的抗锯齿圆角。"""
    try:
        hwnd = int(win.winId())
        u32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
        if not on:
            u32.SetWindowRgn(hwnd, None, True)
            return True
        dpr = win.devicePixelRatioF() or 1.0
        w = int(round(win.width() * dpr))
        h = int(round(win.height() * dpr))
        d = max(2, int(round(radius * 2 * dpr)))          # 圆角椭圆直径
        rgn = gdi32.CreateRoundRectRgn(0, 0, w + 1, h + 1, d, d)
        if not rgn:
            return False
        return bool(u32.SetWindowRgn(hwnd, rgn, True))
    except Exception:
        return False


class CardWidget(QWidget):
    """窗口卡片本体：按主题自绘
       镭射 = 实底 + 亮色描边；莫兰迪 = 半透明 + 顶部液体高光 + 内缘亮边（玻璃感）"""

    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.th = theme or THEMES["laser"]
        self.bg_img = None
        self.bg_origin = QPoint(0, 0)
        self.bg_k = 1.0            # 背景图每 1 逻辑像素对应多少背景图像素

    def set_backdrop(self, img, origin, k):
        self.bg_img = img
        self.bg_origin = QPoint(origin)
        self.bg_k = k
        self.update()

    def set_theme(self, th):
        self.th = th
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(0.6, 0.6, -0.6, -0.6)
        path = QPainterPath()
        path.addRoundedRect(r, 14, 14)
        # 玻璃底：真正被模糊过的背景（只在圆角路径内）
        if self.th.get("glass") and self.bg_img is not None and not self.bg_img.isNull():
            gp = self.mapToGlobal(QPoint(0, 0))
            src = QRectF((gp.x() - self.bg_origin.x()) * self.bg_k,
                         (gp.y() - self.bg_origin.y()) * self.bg_k,
                         self.width() * self.bg_k, self.height() * self.bg_k)
            p.save()
            p.setClipPath(path)
            p.setRenderHint(QPainter.SmoothPixmapTransform, True)
            p.drawImage(QRectF(self.rect()), self.bg_img, src)
            p.restore()
        p.fillPath(path, QColor(*self.th["card_fill"]))
        if self.th.get("glass"):
            g = QLinearGradient(0, r.top(), 0, r.top() + r.height() * 0.55)
            g.setColorAt(0.0, QColor(255, 255, 255, self.th["gloss_top"]))
            g.setColorAt(0.45, QColor(255, 255, 255, max(0, self.th["gloss_top"] // 4)))
            g.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.fillPath(path, g)
            g2 = QLinearGradient(0, r.bottom() - r.height() * 0.32, 0, r.bottom())
            g2.setColorAt(0.0, QColor(0, 0, 0, 0))
            g2.setColorAt(1.0, QColor(0, 0, 0, 48))
            p.fillPath(path, g2)
            inner = QPainterPath()
            inner.addRoundedRect(r.adjusted(1.2, 1.2, -1.2, -1.2), 13, 13)
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(255, 255, 255, self.th["edge"]), 1.4))
            p.drawPath(inner)
            # 顶部镜面高光：中间亮两头淡，最像玻璃的一条线
            spec = QLinearGradient(r.left() + 18, 0, r.right() - 18, 0)
            spec.setColorAt(0.0, QColor(255, 255, 255, 0))
            spec.setColorAt(0.5, QColor(255, 255, 255, min(255, int(self.th["edge"] * 1.7))))
            spec.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setPen(QPen(spec, 1.8))
            p.drawLine(int(r.left() + 20), int(r.top() + 1.4),
                       int(r.right() - 20), int(r.top() + 1.4))
            # 底部反光：光从玻璃边缘折回来那一道
            bounce = QLinearGradient(r.left() + 30, 0, r.right() - 30, 0)
            bounce.setColorAt(0.0, QColor(255, 255, 255, 0))
            bounce.setColorAt(0.5, QColor(255, 255, 255, int(self.th["edge"] * 0.5)))
            bounce.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setPen(QPen(bounce, 1.3))
            p.drawLine(int(r.left() + 26), int(r.bottom() - 1.4),
                       int(r.right() - 26), int(r.bottom() - 1.4))
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(*self.th["card_border"]), 1))
        p.drawPath(path)


def app_icon(accent=(80, 235, 255)) -> QIcon:
    """托盘/窗口图标：跟着主题的强调色走"""
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setBrush(QColor(22, 25, 32, 255))
    p.setPen(QPen(QColor(*accent), 3))
    p.drawEllipse(pm.rect().adjusted(4, 4, -4, -4))
    c = pm.rect().center()
    p.setPen(QPen(QColor(*accent), 3))
    p.drawLine(c.x() - 14, c.y(), c.x() - 5, c.y())
    p.drawLine(c.x() + 5, c.y(), c.x() + 14, c.y())
    p.drawLine(c.x(), c.y() - 14, c.x(), c.y() - 5)
    p.drawLine(c.x(), c.y() + 5, c.x(), c.y() + 14)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(255, 255, 255, 255))
    p.drawEllipse(c, 2, 2)
    p.end()
    return QIcon(pm)


# ---------------------------------------------------------------- 主浮窗
class FloatWindow(QWidget):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.history = []            # 发送给模型的消息（含图片 data-url）
        self.current_answer = ""
        self.worker = None
        self.catcher = None
        self.last_image_path = None
        self._pending_info = ""
        self._expanded_h = 620
        self.state = "window"        # window / ball / tray
        self._prev_state = "window"

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(app_icon())
        self.setMinimumSize(340, 120)

        win = cfg.get("window", {})
        self.resize(int(win.get("w", 440)), int(win.get("h", 620)))
        self.move(int(win.get("x", 820)), int(win.get("y", 60)))
        self._clamp_to_screen()
        self._expanded_h = self.height()

        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)
        self.theme_name = cfg.get("theme", "laser")
        if self.theme_name not in THEMES:
            self.theme_name = "laser"
        self.th = THEMES[self.theme_name]
        self.card = CardWidget(self, self.th)
        self.card.setObjectName("card")
        root.addWidget(self.card)

        v = QVBoxLayout(self.card)
        v.setContentsMargins(12, 6, 10, 8)
        v.setSpacing(6)

        # —— 标题栏
        self.bar = DragBar(self.card)
        hb = QHBoxLayout(self.bar)
        hb.setContentsMargins(2, 0, 0, 0)
        hb.setSpacing(4)
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        title.setToolTip(f"截图搜题浮窗 · 快捷键 {cfg.get('hotkey','ctrl+alt+q')}")
        hb.addWidget(title)
        hb.addStretch(1)
        self.btn_shot = self._mkbtn("框选", "截图并搜题 (Ctrl+Alt+Q)", self.start_capture)
        self.btn_copy = self._mkbtn("复制", "复制答案", self.copy_answer)
        self.btn_clear = self._mkbtn("清空", "清空对话", self.clear_all)
        self.btn_settings = self._mkbtn("⚙", "设置接口 / 模型 / API Key", self.open_settings)
        self.btn_theme = self._mkbtn("◐", "外观", self._show_theme_menu)
        self.btn_fold = self._mkbtn("—", "收成悬浮球（第一档）；再收一次进托盘", self.minimize_to_ball)
        self.btn_close = self._mkbtn("✕", "关闭", self.close)
        for b in (self.btn_shot, self.btn_copy, self.btn_clear, self.btn_settings,
                  self.btn_theme, self.btn_fold, self.btn_close):
            hb.addWidget(b)
        v.addWidget(self.bar)

        # —— 答案条：把"答案"单独提出来放大、加底色，一眼能看到
        self.answer_box = QLabel(self.card)
        self.answer_box.setObjectName("ansbox")
        self.answer_box.setTextFormat(Qt.RichText)
        self.answer_box.setWordWrap(True)
        self.answer_box.setVisible(False)
        v.addWidget(self.answer_box)

        # —— 正文
        self.view = QTextBrowser(self.card)
        self.view.setObjectName("view")
        self.view.setOpenExternalLinks(True)
        self.view.setReadOnly(True)
        v.addWidget(self.view, 1)

        # —— 状态 + 进度
        self.status = QLabel(f"就绪 · v{__version__} · 按 Ctrl+Alt+Q 或点「框选」")
        self.status.setObjectName("status")
        v.addWidget(self.status)

        # —— 追问输入
        row = QHBoxLayout()
        row.setSpacing(6)
        self.input = QLineEdit(self.card)
        self.input.setPlaceholderText("输入题目或追问，Enter 发送…")
        pal = self.input.palette()
        pal.setColor(QPalette.PlaceholderText, QColor(154, 175, 200))
        self.input.setPalette(pal)
        self.input.returnPressed.connect(self.on_send)
        row.addWidget(self.input, 1)
        self.btn_send = self._mkbtn("发送", "发送输入框里的文字", self.on_send)
        row.addWidget(self.btn_send)
        v.addLayout(row)

        self.grip = QSizeGrip(self.card)
        self.grip.setFixedSize(16, 16)
        gr = QHBoxLayout()
        gr.setContentsMargins(0, 0, 0, 0)
        gr.addStretch(1)
        gr.addWidget(self.grip)
        v.addLayout(gr)

        self.setStyleSheet(self._qss())

        self.view.setHtml(self._welcome_html())

        self.hotkey = HotkeyThread(cfg.get("hotkey", "ctrl+alt+q"), self)
        self.hotkey.triggered.connect(self.start_capture)
        self.hotkey.start()
        QTimer.singleShot(1200, self._check_hotkey)
        QTimer.singleShot(1400, self._maybe_first_run)

        # —— 两档最小化：悬浮小球 + 托盘图标
        self.ball = FloatBall()
        self.ball.clicked.connect(self.restore_window)
        self.theme_menu = self._build_theme_menu()
        self.menu = self._build_menu()
        self.ball.menu = self.menu
        self.tray = QSystemTrayIcon(app_icon(self.th["accent"]), self)
        self.tray.setToolTip(f"{APP_NAME} v{__version__} · Ctrl+Alt+Q 截图搜题")
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._tray_activated)
        bpos = cfg.get("ball") or {}
        if bpos:
            self.ball.move(int(bpos.get("x", 0)), int(bpos.get("y", 0)))
        self.apply_theme(self.theme_name, persist=False)
        self.refresh_backdrop()          # 此刻窗口还没显示，抓到的正是"背后"

    # ---------- 外观主题
    def _qss(self) -> str:
        t = getattr(self, "teff", None) or self.th
        fu, fb = t["font_ui"], t["font_body"]
        return f"""
        QLabel#title {{ color: {t['title']}; font: 600 11.5pt "{fu}"; }}
        QLabel#status {{ color: {t['subtext']}; font: 8.5pt "{fu}"; }}
        QLabel#ansbox {{
            background: {t['ans_bg']};
            border: 1px solid {t['ans_border']};
            border-radius: 10px;
            padding: 9px 13px;
        }}
        QTextBrowser#view {{
            background: {t['panel_bg']};
            border: 1px solid {t['panel_border']};
            border-radius: 10px;
            color: {t['text']};
            font: 10.5pt "{fb}";
            padding: 9px 11px;
            selection-background-color: {t['selection']};
        }}
        QLineEdit {{
            background: {t['panel_bg']};
            border: 1px solid {t['panel_border']};
            border-radius: 10px;
            color: {t['text']};
            font: 10.5pt "{fb}";
            padding: 6px 9px;
        }}
        QLineEdit:focus {{ border: 1px solid {t['focus_border']}; }}
        QPushButton {{
            background: {t['btn_bg']};
            color: {t['btn_text']};
            border: none;
            border-radius: 8px;
            padding: 4px 9px;
            font: 9pt "{fu}";
        }}
        QPushButton:hover {{ background: {t['btn_hover']}; }}
        QPushButton:pressed {{ background: {t['btn_press']}; }}
        QPushButton:disabled {{ background: {t['btn_disabled']}; color: {t['subtext']}; }}
        QToolTip {{
            background: {t['menu_bg']}; color: {t['text']};
            border: 1px solid {t['menu_border']}; padding: 4px 6px;
        }}
        """

    def _menu_qss(self) -> str:
        t = getattr(self, "teff", None) or self.th
        return f"""
        QMenu {{ background: {t['menu_bg']}; color: {t['text']};
                border: 1px solid {t['menu_border']}; border-radius: 8px; padding: 6px;
                font: 9.5pt "{t['font_ui']}"; }}
        QMenu::item {{ padding: 6px 24px 6px 14px; border-radius: 5px; }}
        QMenu::item:selected {{ background: {t['menu_sel']}; }}
        QMenu::separator {{ height: 1px; background: {t['panel_border']}; margin: 4px 8px; }}
        """

    def _build_theme_menu(self) -> QMenu:
        m = QMenu("外观", self)
        grp = QActionGroup(m)
        grp.setExclusive(True)
        self._theme_acts = {}
        for key, th in THEMES.items():
            act = m.addAction(th["label"])
            act.setCheckable(True)
            act.setChecked(key == self.theme_name)
            act.setStatusTip(th.get("desc", ""))
            act.triggered.connect(lambda _=False, k=key: self.apply_theme(k))
            grp.addAction(act)
            self._theme_acts[key] = act
        m.setToolTipsVisible(True)
        for key, act in self._theme_acts.items():
            act.setToolTip(THEMES[key].get("desc", ""))
        return m

    def _show_theme_menu(self):
        p = self.btn_theme.mapToGlobal(self.btn_theme.rect().bottomLeft())
        self.theme_menu.popup(p)

    def refresh_backdrop(self, canvas=None):
        """抓一张"窗口背后"的桌面图，缩小再放大当模糊底（玻璃主题用）。
           必须在窗口不可见时调用：构造时、截完图时、或用户点"刷新玻璃背景"。"""
        try:
            scr = QGuiApplication.primaryScreen()
            vg = scr.virtualGeometry()
            img = canvas if canvas is not None else scr.grabWindow(0).toImage()
            if img is None or img.isNull():
                return
            d = BACKDROP_DOWNSCALE
            w1, h1 = max(1, img.width() // d), max(1, img.height() // d)
            small = img.scaled(w1, h1, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            # 再叠一次缩放-放大，模糊半径翻三倍，接近高斯（文字彻底化开）
            small = small.scaled(max(1, w1 // 3), max(1, h1 // 3),
                                 Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            small = small.scaled(w1, h1, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            k = d / (scr.devicePixelRatio() or 1.0)      # 背景图像素 / 逻辑像素
            self.card.set_backdrop(small, vg.topLeft(), k)
        except Exception as e:
            print("refresh_backdrop 失败:", e)

    def refresh_backdrop_visible(self):
        """用户主动刷新：藏起窗口抓一张再露出来（会闪一下，所以只做成菜单项）"""
        was = self.state
        self.hide()
        self.ball.hide()
        QTimer.singleShot(120, lambda: (self.refresh_backdrop(), self._apply_state(was)))

    def _apply_acrylic(self):
        """按当前主题开/关系统亚克力模糊；返回是否生效"""
        a = self.th.get("acrylic")
        if not a:
            enable_acrylic(self.winId(), (0, 0, 0), 0)      # 关掉
            return False
        ok = enable_acrylic(self.winId(), tuple(a[:3]), a[3])
        return ok

    def apply_theme(self, name, persist=True):
        if name not in THEMES:
            return
        self.theme_name = name
        self.th = THEMES[name]
        self._acrylic_ok = False           # 已改为自绘模糊背景（见 refresh_backdrop）
        eff = dict(self.th)
        self.teff = eff
        self.card.set_theme(eff)
        self.ball.set_theme(self.th)
        self.setStyleSheet(self._qss())
        self.menu.setStyleSheet(self._menu_qss())
        self.theme_menu.setStyleSheet(self._menu_qss())
        self.tray.setIcon(app_icon(self.th["accent"]))
        self.setWindowIcon(app_icon(self.th["accent"]))
        pal = self.input.palette()
        pal.setColor(QPalette.PlaceholderText, QColor(self.th["placeholder"]))
        self.input.setPalette(pal)
        act = getattr(self, "_theme_acts", {}).get(name)
        if act:
            act.setChecked(True)
        self.btn_theme.setToolTip(f"外观：{self.th['label']}")
        # 没在答题时，欢迎页也跟着换色
        if not self.current_answer:
            self.view.setHtml(self._welcome_html())
        if persist:
            self.cfg["theme"] = name
            save_config(self.cfg)
            self.status.setText(f"外观已切换：{self.th['label']}")

    # ---------- 两档最小化
    def _build_menu(self) -> QMenu:
        m = QMenu(self)
        m.setStyleSheet(self._menu_qss())
        m.addAction("展开窗口", self.restore_window)
        m.addAction("截图搜题  (Ctrl+Alt+Q)", self.start_capture)
        m.addSeparator()
        m.addMenu(self.theme_menu)
        m.addAction("设置（接口 / 模型 / Key）…", self.open_settings)
        m.addSeparator()
        m.addAction("收成悬浮球", self.minimize_to_ball)
        m.addAction("收进托盘（完全隐藏）", self.minimize_to_tray)
        m.addAction("刷新玻璃背景", self.refresh_backdrop_visible)
        m.addSeparator()
        m.addAction("退出", self.quit_app)
        ver = m.addAction(f"v{__version__} · {APP_NAME}")
        ver.setEnabled(False)
        return m

    def _remember_geometry(self):
        self.cfg["window"] = {"x": self.x(), "y": self.y(),
                              "w": self.width(), "h": self._expanded_h,
                              "collapsed": False}

    def minimize_to_ball(self):
        """第一档：收成贴边悬浮小球"""
        if self.state == "ball" and self.ball.isVisible():
            return
        self._remember_geometry()
        g = self.frameGeometry()
        self.state = "ball"
        self.hide()
        self.tray.hide()
        self.ball.place_near(g)
        self.ball.show()
        self.ball.raise_()

    def minimize_to_tray(self):
        """第二档：完全隐藏，只留在托盘（Win11 默认在“隐藏的图标”溢出区里）"""
        self._remember_geometry()
        self.state = "tray"
        self.hide()
        self.ball.hide()
        self.tray.show()
        self.tray.showMessage("反谋财害命器", "已收进托盘：点托盘图标或按 Ctrl+Alt+Q 随时回来",
                              QSystemTrayIcon.Information, 1500)

    def restore_window(self):
        self.state = "window"
        self.ball.hide()
        self.tray.hide()
        self.show()
        self.raise_()
        self.activateWindow()

    def _tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.restore_window()

    def _apply_state(self, s):
        if s == "ball":
            self.minimize_to_ball()
        elif s == "tray":
            self.minimize_to_tray()
        else:
            self.restore_window()

    def quit_app(self):
        self.hide()
        self.ball.hide()
        self.tray.hide()
        QApplication.quit()

    # ---------- 小工具
    def _mkbtn(self, text, tip, slot):
        b = QPushButton(text, self.card)
        b.setToolTip(tip)
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(slot)
        b.setFixedHeight(26)
        return b

    def _welcome_html(self):
        hk = self.cfg.get('hotkey', 'ctrl+alt+q')
        t = getattr(self, "teff", None) or self.th
        return f"""
        <div style="color:{t['subtext']}; font-family:'Noto Sans SC'; font-size:10pt; line-height:150%">
        <p style="color:{t['title']}; font-size:12pt"><b>截图即可搜题</b></p>
        <p>① 按 <b style="color:{t['text']}">{hk}</b>（或点「框选」）<br>
           ② 用鼠标框住屏幕上的题目<br>
           ③ 答案、解析、考点自动出现在这里</p>
        <p>可以在下面粘贴/输入题目文字回车。<br>
           截图连着框多道题也可以，会逐题给出答案。</p>
        <p style="color:#8ea9c9; font-size:9pt">第一次用？点右上角 <b>⚙</b> 填自己的接口地址、模型和 API Key（只存本机）</p>
        <p style="color:{t['subtext']}; font-size:8.5pt">模型：{self.cfg.get('model')}　·　外观：{t['label']}　·　v{__version__}</p>
        </div>"""

    def _check_hotkey(self):
        if not self.hotkey.ok:
            self.status.setText(f"提示：全局热键 {self.cfg.get('hotkey')} 注册失败（被别的软件占用），点「框选」一样能用")

    # ---------- 截图流程
    def start_capture(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.status.setText("已停止")
            return
        self._prev_state = self.state if self.state != "window" else "window"
        self.hide()
        self.ball.hide()          # 小球别出现在截图里
        QTimer.singleShot(160, self._do_capture)

    def _do_capture(self):
        try:
            self.catcher = RegionCatcher(self.th["accent"])
            self.catcher.captured.connect(self.on_captured)
            self.catcher.cancelled.connect(self._show_me)
            self.catcher.show()
            self.catcher.raise_()
            self.catcher.activateWindow()
        except Exception as e:
            self._show_me()
            self.status.setText(f"截图失败: {e}")

    def _show_me(self):
        """取消截图：回到进去之前的状态（窗口/球/托盘）"""
        self._apply_state(self._prev_state)
        self.raise_()

    def on_captured(self, img: QImage):
        try:
            c = getattr(self, "catcher", None)
            if c is not None and getattr(c, "canvas", None) is not None:
                self.refresh_backdrop(c.canvas)      # 这张画布里没有我们的窗口
        except Exception:
            pass
        self.restore_window()     # 框完总要看到答案，所以一律展开窗口
        # 不碰剪贴板：截图既不从中读取，也不往里写入（图片只在内存里直接送模型）
        self.last_image_path = None
        self.send_image(img)

    # 说明：程序不保存任何截图文件，历史截图也不会留在磁盘上

    # ---------- 与模型交互
    def _b64_image(self, img: QImage):
        return encode_image(img)

    def send_image(self, img: QImage):
        b64, mime = self._b64_image(img)
        content = [
            {"type": "text", "text": "请识别图中题目并解答（按系统要求的格式）。"},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        ]
        # 新截图视为新的一道题：清掉旧上下文，省 token 也避免串题
        self.history = [{"role": "user", "content": content}]
        info = f"🖼 截图 {img.width()}×{img.height()}px"
        if self.last_image_path:
            info += f" · {self.last_image_path.name}"
        self.view.setPlainText("")
        self.answer_box.setVisible(False)
        self.current_answer = ""
        self._pending_info = info
        self._start_worker()

    def on_send(self):
        """点「发送」/回车：只发输入框里的文字。
        不读剪贴板 —— 不碰剪贴板是硬要求，避免把无关的旧图当题目送出去。"""
        text = self.input.text().strip()
        if not text:
            self.status.setText("先输入题目，或按 Ctrl+Alt+Q 框选屏幕上的题目")
            return
        self.ask_text(text)

    def ask_text(self, text):
        text = (text or "").strip()
        if not text:
            return
        content = [{"type": "text", "text": text}]
        self.input.clear()
        # 文字追问：接在上一题后面，模型能理解"为什么""换个解法"这类指代
        if not self.history:
            self.history = []
        self.history.append({"role": "user", "content": content})
        self._trim_history()
        self.view.setPlainText(f"你：{text}\n\n")
        self.answer_box.setVisible(False)
        self.current_answer = ""
        self._pending_info = ""
        self._start_worker()

    @staticmethod
    def _esc(s):
        return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    def _trim_history(self):
        # 只保留最近 8 条，避免越聊越贵
        if len(self.history) > 8:
            self.history = self.history[-8:]

    def _start_worker(self):
        key, src = resolve_api_key(self.cfg)
        if not key:
            env_hint = (self.cfg.get("api_key_env") or ["<你的KEY变量名>"])
            env_hint = env_hint[0] if isinstance(env_hint, list) else env_hint
            self.view.setHtml("<div style='color:#ff9a9a'>还没配置 API Key。<br>"
                              "点右上角 <b>⚙</b>（或右键菜单「设置」）填一次接口地址、模型和 Key 就能用。<br>"
                              f"也可以手动写进 config.json 的 <code>api_key</code>，或设置环境变量 "
                              f"<code>{env_hint}</code>。</div>")
            self.status.setText("缺少 API Key · 点 ⚙ 填写")
            self.open_settings()
            return
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(1500)
        self.worker = AskThread(self.cfg, key, list(self.history), self)
        self.worker.chunk.connect(self.on_chunk)
        self.worker.reasoning.connect(self.on_reasoning)
        self.worker.done.connect(self.on_done)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()
        self.btn_shot.setText("停止")
        self.btn_send.setEnabled(False)
        pre = getattr(self, "_pending_info", "") or ""
        self.status.setText((pre + "　").strip() + f"请求中… · {self.cfg.get('model')}")
        self._t0 = time.time()

    def on_chunk(self, s):
        self.current_answer += s
        self.view.moveCursor(QTextCursor.End)
        self.view.insertPlainText(s)
        self.view.moveCursor(QTextCursor.End)
        sb = self.view.verticalScrollBar()
        sb.setValue(sb.maximum())
        pre = (getattr(self, "_pending_info", "") or "")
        self.status.setText((pre + "　" if pre else "") + f"生成中… {len(self.current_answer)} 字 · {time.time()-self._t0:.0f}s")

    def on_reasoning(self, n):
        pre = (getattr(self, "_pending_info", "") or "")
        self.status.setText((pre + "　" if pre else "") + f"思考中… · {time.time()-self._t0:.0f}s")

    def on_done(self, text, usage):
        self.current_answer = text
        self.history.append({"role": "assistant", "content": text})
        self._present_answer(text)
        self.btn_shot.setText("框选")
        self.btn_send.setEnabled(True)
        u = ""
        if usage:
            u = f" · tokens {usage.get('total_tokens', '?')}"
        self.status.setText(f"✓ 完成 · {time.time()-self._t0:.0f}s{u}")

    def on_failed(self, msg):
        self.btn_shot.setText("框选")
        self.btn_send.setEnabled(True)
        self.view.moveCursor(QTextCursor.End)
        self.view.insertPlainText("\n\n⚠ " + msg)
        self.status.setText("出错")

    def _present_answer(self, text):
        """答案单独做成大字高亮条；题目/解析/考点 用排好版的 HTML 显示"""
        t = getattr(self, "teff", None) or self.th
        secs = split_sections(text)
        ans = (secs.get("答案") or "").strip()

        if ans:
            self.answer_box.setText(
                f'<span style="color:{t["ans_tag"]}; font-size:8.5pt;">答 案</span>'
                f'<br><span style="color:{t["text"]}; font-size:15.5pt; font-weight:700;">{md_inline(ans)}</span>')
            self.answer_box.setVisible(True)
        else:
            self.answer_box.setVisible(False)

        if not secs:                             # 模型没按格式走：退回 markdown
            self.view.setMarkdown(text)
            self.view.verticalScrollBar().setValue(0)
            return

        blocks = []
        for k in _SEC_KEYS:
            body = (secs.get(k) or "").strip()
            if not body or (k == "答案" and ans):
                continue
            blocks.append(
                f'<div style="color:{t["ans_tag"]}; font-size:9pt; margin:2px 0 4px 0;">{k}</div>'
                f'<div style="color:{t["text"]}; font-size:10.5pt; margin:0 0 12px 0;">{md_inline(body)}</div>')
        self.view.setHtml(
            f'<div style="font-family:\'{t["font_body"]}\'; line-height:158%;">'
            + "".join(blocks) + "</div>")
        self.view.verticalScrollBar().setValue(0)

    def _render_markdown(self, text):
        md = text
        # 简单美化：加粗 ### 标题、代码块保持
        self.view.setMarkdown(md)
        sb = self.view.verticalScrollBar()
        sb.setValue(0)

    def copy_answer(self):
        if not self.current_answer:
            self.status.setText("还没有答案可复制")
            return
        secs = split_sections(self.current_answer)
        txt = (secs.get("答案") or self.current_answer).strip()
        QGuiApplication.clipboard().setText(txt)
        self.status.setText("答案已复制到剪贴板")

    def _maybe_first_run(self):
        """第一次运行 / 没配置 key：直接弹设置窗，别让人去改 JSON"""
        key, _ = resolve_api_key(self.cfg)
        if key:
            return
        self.status.setText("还没配置 API Key · 在设置里填一次即可")
        self.open_settings()

    def open_settings(self):
        """设置接口 / 模型 / Key，保存后立即生效（不用重启）"""
        dlg = SettingsDialog(self, self.cfg)
        dlg.raise_()
        dlg.activateWindow()
        res = dlg.exec()
        self.raise_()                                # 关掉后把浮窗重新抬起来
        if res == QDialog.Accepted:
            key, src = resolve_api_key(self.cfg)
            if key:
                self.status.setText(f"设置已保存 · key 来自 {src}")
            else:
                self.status.setText("设置已保存 · 还没填 API Key")

    def clear_all(self):
        self.history.clear()
        self.current_answer = ""
        self.answer_box.setVisible(False)
        self.view.setHtml(self._welcome_html())
        self.status.setText("已清空")

    # ---------- 窗口
    def _clamp_to_screen(self):
        """上次的位置若跑到屏幕外（拖出边缘/拔显示器），拉回可见区域，保证标题条能抓到"""
        scr = QGuiApplication.primaryScreen()
        if not scr:
            return
        a = scr.availableGeometry()
        x = min(max(self.x(), a.left()), max(a.left(), a.right() - 160))
        y = min(max(self.y(), a.top()), max(a.top(), a.bottom() - 80))
        if (x, y) != (self.x(), self.y()):
            self.move(x, y)

    def showEvent(self, e):
        super().showEvent(e)
        if self.card.bg_img is None:
            QTimer.singleShot(0, self.refresh_backdrop)

    def paintEvent(self, e):
        pass    # 背景由 card 的样式负责

    def closeEvent(self, e):
        try:
            self.cfg["window"] = {"x": self.x(), "y": self.y(),
                                  "w": self.width(), "h": self._expanded_h,
                                  "collapsed": False}
            self.cfg["ball"] = {"x": self.ball.x(), "y": self.ball.y()}
            save_config(self.cfg)
        except Exception:
            pass
        try:
            self.ball.hide()
            self.tray.hide()
        except Exception:
            pass
        self.hotkey.stop()
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(1200)
        super().closeEvent(e)
        QApplication.quit()


def _install_crash_log():
    """pythonw 没有控制台，异常会静默消失 -> 落到 error.log，便于事后排查"""
    import traceback
    import datetime
    log = APP_DIR / "error.log"

    def hook(t, v, tb):
        try:
            with open(log, "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {t.__name__}: {v}\n")
                f.write("".join(traceback.format_exception(t, v, tb)))
        except Exception:
            pass
    sys.excepthook = hook


def main():
    _install_crash_log()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)   # 收成球/进托盘时不能退出
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    cfg = load_config()
    w = FloatWindow(cfg)
    w.show()
    w.raise_()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
