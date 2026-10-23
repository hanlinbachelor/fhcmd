# -*- coding: utf-8 -*-
"""探针：在 PyInstaller 打包环境里试渲染公式，把结果写进 probe_out.txt"""
import os
import sys
import traceback

out = os.path.join(os.path.dirname(sys.executable), "probe_out.txt")
lines = []


def log(s):
    lines.append(str(s))


log("frozen = %s" % getattr(sys, "frozen", False))
try:
    import matplotlib
    log("matplotlib = %s" % matplotlib.__version__)
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    fig = Figure(figsize=(0.1, 0.1), dpi=200)
    FigureCanvasAgg(fig)
    fig.patch.set_alpha(0)
    fig.text(0, 0, r"$\sqrt e=e^{\frac12}$", color="#ffffff", fontsize=12)
    p = os.path.join(os.path.dirname(sys.executable), "probe_math.png")
    fig.savefig(p, format="png", transparent=True, bbox_inches="tight", pad_inches=0.05)
    log("savefig OK -> %s (%d bytes)" % (p, os.path.getsize(p)))
except Exception:
    log("FAILED:\n" + traceback.format_exc())

with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
