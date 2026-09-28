"""Draw the figures in docs/figures from the committed data.

    PYTHONPATH=pipeline/src python3 scripts/make_figures.py

Every number is computed by the same run the report prints, so a figure cannot
disagree with the text. CI regenerates them and fails on any difference. Each
figure comes in a light and a dark version, written as SVG directly: no
plotting library, nothing to install.
"""

from __future__ import annotations

import math
import os
import sys
from xml.sax.saxutils import escape

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "pipeline", "src"))

from degreevalue.study import run  # noqa: E402

OUT = os.path.join(ROOT, "docs", "figures")
SANS = "'IBM Plex Sans', ui-sans-serif, system-ui, -apple-system, sans-serif"
MONO = "'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

# Checked with a colour-vision validator against both surfaces: blue and red
# stay distinct under protanopia and deuteranopia and clear 3:1 on each.
LIGHT = {"bg": "#fbfaf7", "ink": "#111110", "dim": "#52514e", "muted": "#6b6a65",
         "grid": "#e6e4dc", "axis": "#c3c2b7", "rest": "#cfccc3",
         "blue": "#2a78d6", "red": "#e34948"}
DARK = {"bg": "#161614", "ink": "#f3f2ee", "dim": "#c3c2b7", "muted": "#9a988f",
        "grid": "#2a2a27", "axis": "#3d3d3a", "rest": "#4b4a46",
        "blue": "#3987e5", "red": "#e66767"}

W = 1120
LEFT = 64


def money(x: float, dp: int = 0) -> str:
    return f"£{x:,.{dp}f}"


def short_money(x: float) -> str:
    if x >= 1_000_000:
        return f"£{x / 1e6:.2f}m"
    return f"£{x / 1000:.0f}k"


class Svg:
    def __init__(self, h: int, p: dict, title: str, subtitle: str):
        self.p, self.h = p, h
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" '
            f'role="img" aria-label="{escape(title)}">',
            f'<rect width="{W}" height="{h}" fill="{p["bg"]}"/>',
        ]
        self.text(LEFT, 44, title, 21, "ink", weight=600)
        self.text(LEFT, 70, subtitle, 14, "dim")

    def text(self, x, y, s, size=13, colour="ink", family=SANS, anchor="start", weight=400):
        self.parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{self.p[colour]}" text-anchor="{anchor}">{escape(s)}</text>')

    def line(self, x1, y1, x2, y2, colour="grid", width=1.0):
        self.parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                          f'stroke="{self.p[colour]}" stroke-width="{width}"/>')

    def column(self, x, base, width, height, colour):
        """A column rounded 4px at its data end and square at the baseline."""
        r = min(4.0, width / 2, height)
        top = base - height
        self.parts.append(
            f'<path d="M{x:.1f},{base:.1f} V{top + r:.1f} Q{x:.1f},{top:.1f} {x + r:.1f},{top:.1f} '
            f'H{x + width - r:.1f} Q{x + width:.1f},{top:.1f} {x + width:.1f},{top + r:.1f} V{base:.1f} Z" '
            f'fill="{self.p[colour]}"/>')

    def bar(self, x, y, length, thick, colour):
        """A horizontal bar rounded at its data end."""
        r = min(4.0, thick / 2, length)
        self.parts.append(
            f'<path d="M{x:.1f},{y:.1f} H{x + length - r:.1f} Q{x + length:.1f},{y:.1f} {x + length:.1f},{y + r:.1f} '
            f'V{y + thick - r:.1f} Q{x + length:.1f},{y + thick:.1f} {x + length - r:.1f},{y + thick:.1f} '
            f'H{x:.1f} Z" fill="{self.p[colour]}"/>')

    def dot(self, x, y, colour, r=5.0):
        self.parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 2:.1f}" fill="{self.p["bg"]}"/>')
        self.parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{self.p[colour]}"/>')

    def polyline(self, pts, colour, width=2.0):
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.parts.append(f'<polyline points="{d}" fill="none" stroke="{self.p[colour]}" '
                          f'stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>')

    def footnote(self, s):
        self.text(LEFT, self.h - 24, s, 12, "muted")

    def svg(self) -> str:
        return "\n".join(self.parts + ["</svg>"]) + "\n"


# --------------------------------------------------------------------------

def fig_years_by_subject(r, p):
    bs, bm = r["by_subject"], r["by_subject_moving"]
    order = sorted(bs, key=lambda k: (bs[k]["median_years"], -bs[k]["full"]))
    row = 22
    top = 118
    h = top + row * len(order) + 90
    n = len(r["written_off"])
    s = Svg(h, p, f"In {n} of {len(order)} subjects, the typical graduate is still repaying at 61",
            "Years the median graduate repays a Plan 5 loan, students starting in 2024. Blue means it is still "
            "owed at 61 and written off")
    label_w = 330
    x0 = LEFT + label_w
    span = W - x0 - 120
    for v in (0, 10, 20, 30, 40):
        x = x0 + v / 40 * span
        s.line(x, top - 8, x, top + row * len(order), "grid")
        s.text(x, top - 14, f"{v}", 12, "muted", MONO, "middle")
    for i, subj in enumerate(order):
        y = top + i * row
        yrs = bs[subj]["median_years"]
        off = subj in r["written_off"]
        s.text(x0 - 12, y + 14, subj, 13, "ink" if off else "dim", SANS, "end")
        s.bar(x0, y + 4, yrs / 40 * span, 13, "blue" if off else "rest")
        alt = bm[subj]["median_years"]
        ax = x0 + alt / 40 * span
        s.line(ax, y + 1, ax, y + 20, "ink", 2)
        s.text(max(x0 + yrs / 40 * span, ax) + 10, y + 15, f"{yrs}", 12, "ink", MONO)
    s.footnote(f"Blue: written off at 61, {r['written_off_share']:.0%} of graduates. The dark tick is the same "
               f"subject when graduates' ranks can move from year to year, the other end of the model's range.")
    return s.svg()


def fig_pay_ranks(r, p):
    r1, r10, paths = r["rank_year1"], r["rank_year10"], r["paths"]
    n = len(r1)
    top, step = 128, 17
    h = top + step * (n - 1) + 90
    s = Svg(h, p, "Starting pay is a poor guide to pay ten years on",
            f"Each subject's rank by median pay, one year and ten years after graduating, 2022-23 tax year. "
            f"Rank correlation {r['rank_correlation']:.2f}")
    xa, xb = LEFT + 360, W - 360
    s.text(xa, top - 22, "one year out", 13, "dim", SANS, "middle", 600)
    s.text(xb, top - 22, "ten years out", 13, "dim", SANS, "middle", 600)
    lit = {"Nursing and midwifery", "Economics", "Law", "Education and teaching"}
    for subj in sorted(r1, key=lambda k: k in lit):
        ya, yb = top + (r1[subj] - 1) * step, top + (r10[subj] - 1) * step
        on = subj in lit
        s.polyline([(xa, ya), (xb, yb)], "blue" if on else "rest", 2.5 if on else 1.2)
        if on:
            s.dot(xa, ya, "blue", 4)
            s.dot(xb, yb, "blue", 4)
            v = paths[subj]
            s.text(xa - 12, ya + 4, f"{subj} {money(v[1].median)}", 12, "ink", SANS, "end", 600)
            s.text(xb + 12, yb + 4, f"{money(v[10].median)} {subj}", 12, "ink", SANS, "start", 600)
    s.footnote("First-degree graduates domiciled in the UK, every subject with all four years published. "
               "Ranks, not pounds, so the lines cross.")
    return s.svg()


def fig_model_check(r, p):
    t, m = r["targets"]["by_decile"], r["summary"]["by_decile"]
    s = Svg(560, p, "My loan model against the DfE's own forecast",
            "Each tenth of Plan 5 borrowers by lifetime earnings. The model was tuned only to the share repaying "
            "in full, so every point here is out of sample")
    panels = [("Years repaying", "years", 0, 40, lambda v: f"{v:g}"),
              ("Repaid over the term, 2024-25 prices", "repayments_real", 0, 45_000,
               lambda v: "£0" if v == 0 else short_money(v))]
    pw = (W - LEFT - 80) / 2
    for k, (title, key, lo, hi, fmt) in enumerate(panels):
        x0 = LEFT + k * (pw + 60)
        top, base = 140, 440
        s.text(x0, top - 26, title, 14, "ink", SANS, "start", 600)
        for v in (lo, (lo + hi) / 2, hi):
            y = base - (v - lo) / (hi - lo) * (base - top)
            s.line(x0, y, x0 + pw, y, "grid")
            s.text(x0 - 8, y + 4, fmt(v), 12, "muted", MONO, "end")
        xs = [x0 + 20 + (d - 1) * (pw - 40) / 9 for d in range(1, 11)]
        yd = [base - (t[d][key] - lo) / (hi - lo) * (base - top) for d in range(1, 11)]
        ym = [base - (m[d][key] - lo) / (hi - lo) * (base - top) for d in range(1, 11)]
        s.polyline(list(zip(xs, yd)), "dim", 1.5)
        s.polyline(list(zip(xs, ym)), "blue", 2.5)
        for x, a, b in zip(xs, yd, ym):
            s.dot(x, a, "dim", 3.5)
            s.dot(x, b, "blue", 4)
        s.text(xs[0], base + 24, "lowest earners", 12, "muted", SANS, "start")
        s.text(xs[-1], base + 24, "highest", 12, "muted", SANS, "end")
    s.text(LEFT, 500, "Blue: my model. Grey: the DfE forecast.", 13, "ink", SANS, "start", 600)
    s.footnote("Both have the bottom half repaying for forty years. Because ranks are fixed for life, my top half "
               "finishes 3 to 6 years sooner and my bottom fifth repays almost nothing.")
    return s.svg()


FIGURES = {
    "years-by-subject": fig_years_by_subject,
    "pay-ranks": fig_pay_ranks,
    "model-check": fig_model_check,
}


def main() -> int:
    r = run()
    if not all(c.passed for c in r["checks"]):
        print("a verification check failed; not drawing figures from unverified data", file=sys.stderr)
        return 1
    os.makedirs(OUT, exist_ok=True)
    for name, fig in FIGURES.items():
        for mode, palette in (("light", LIGHT), ("dark", DARK)):
            with open(os.path.join(OUT, f"{name}-{mode}.svg"), "w") as f:
                f.write(fig(r, palette))
    print(f"wrote {len(FIGURES) * 2} figures to docs/figures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
