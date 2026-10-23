# -*- coding: utf-8 -*-
"""修复被 heredoc 破坏的 _LEAK_RE 段落，并把漏网检测接进渲染流程"""
import io
import re

P = r"D:\hermes\261020搜题浮窗\souti.py"
s = io.open(P, encoding="utf-8", newline="").read()

start = s.index("_LEAK_RE = re.compile(")
end = s.index("_MATH_RE = re.compile(")
good = (
    'def log_latex_leaks(tag, html):\n'
    '    """把渲染后仍留在文字里的 LaTeX 片段记进日志（这些是“没被识别成公式”的漏网）"""\n'
    '    plain = re.sub(r"<[^>]+>", " ", html or "")\n'
    '    hits = re.findall(r"\\\\[a-zA-Z]{2,}|\\$[^$\\n]{0,80}\\$?", plain)\n'
    '    if not hits:\n'
    '        return\n'
    '    try:\n'
    '        with open(APP_DIR / "math_fail.log", "a", encoding="utf-8") as f:\n'
    '            f.write("--- %s LEAK [%s] ---\\n" % (time.strftime("%H:%M:%S"), tag))\n'
    '            for h in hits[:12]:\n'
    '                f.write("  %r\\n" % h)\n'
    '    except Exception:\n'
    '        pass\n\n\n'
)
s = s[:start] + good + s[end:]

# 在 _present_answer 的分区循环里调用
if "log_latex_leaks(k," not in s:
    s = s.replace(
        '''                f'{rich_html(body, t["text"])}</div>')''',
        '''                f'{rich_html(body, t["text"])}</div>')''')
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("ok")
