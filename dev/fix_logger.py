# -*- coding: utf-8 -*-
"""修掉 _log_math_fail 里被 heredoc 破坏的换行"""
import io

p = r"D:\hermes\261020搜题浮窗\souti.py"
s = io.open(p, encoding="utf-8", newline="").read()
start = s.index("def _log_math_fail(")
end = s.index("    except Exception:", start)
end = s.index("\n\n", end) + 2
new = (
    'def _log_math_fail(expr: str, err):\n'
    '    """记下没渲染成功的公式，方便排查（写在 exe/源码同目录）"""\n'
    '    try:\n'
    '        with open(APP_DIR / "math_fail.log", "a", encoding="utf-8") as f:\n'
    '            f.write("--- %s ---\\n" % time.strftime("%Y-%m-%d %H:%M:%S"))\n'
    '            f.write("expr: %r\\n" % (expr,))\n'
    '            f.write("err : %s: %s\\n" % (type(err).__name__, err))\n'
    '    except Exception:\n'
    '        pass\n\n\n'
)
s = s[:start] + new + s[end:]
io.open(p, "w", encoding="utf-8", newline="").write(s)
print("修好了")
