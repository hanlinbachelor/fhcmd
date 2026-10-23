# -*- coding: utf-8 -*-
"""修掉被 heredoc 破坏的原文落盘代码，并给答案块接上漏网检测"""
import io

P = r"D:\hermes\261020搜题浮窗\souti.py"
s = io.open(P, encoding="utf-8", newline="").read()

# 1) 定位并重建被破坏的那段 try 块
start = s.index("        try:                                     # 把模型原文存一份，排查公式问题用")
end = s.index("        t = getattr(self, \"teff\", None) or self.th", start)
good = (
    '        try:                                     # 把模型原文存一份，排查公式问题用\n'
    '            with open(APP_DIR / "last_answer.txt", "w", encoding="utf-8") as f:\n'
    '                f.write("===== %s =====\\n" % time.strftime("%Y-%m-%d %H:%M:%S"))\n'
    '                f.write(text or "")\n'
    '        except Exception:\n'
    '            pass\n'
)
s = s[:start] + good + s[end:]

# 2) 答案块加检测（若还没加）
if 'log_latex_leaks("答案"' not in s:
    s = s.replace('            ans_html = rich_html(ans, t["text"], fontsize=15.0)',
                  '            ans_html = rich_html(ans, t["text"], fontsize=15.0)\n'
                  '            log_latex_leaks("答案", ans_html)')
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("ok:", 'last_answer.txt' in s, '|', 'log_latex_leaks("答案"' in s)
