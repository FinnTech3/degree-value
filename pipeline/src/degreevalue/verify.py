"""Reproduce the DfE's own published figures before using its data for anything.

The LEO provider-level release states four ranges across providers, five years
after graduation, each as the spread of "the middle 90% of providers":

    median earnings, all graduates       £20,400 to £42,000
    median earnings, men                  £21,200 to £48,200
    median earnings, women                £18,900 to £40,300
    in sustained work or study            71.4% to 95.0%

Eight numbers. They are only reproduced with one of the nine standard ways of
taking a percentile, the inverse of the empirical distribution function
(Hyndman and Fan's type 1: the smallest value with at least p of the providers
at or below it), taken over every UK provider of every type. The linear
interpolation most software uses by default (type 7) gets two of the four
ranges right, which is why the twin test uses it.

Reproducing all eight at once confirms three things together: that the extract
holds the rows the DfE published from, that the provider universe is the one
the DfE used, and that this package reads the columns the way the DfE meant
them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .sources import PathPoint, Row, provider_totals

PUBLISHED = {
    "earnings, all graduates": (20_400, 42_000),
    "earnings, men": (21_200, 48_200),
    "earnings, women": (18_900, 40_300),
    "sustained work or study": (71.4, 95.0),
}


@dataclass
class Result:
    name: str
    passed: bool
    summary: str
    detail: dict = field(default_factory=dict)


def percentile_type1(values: list[float], p: float) -> float:
    """Inverse empirical distribution: the smallest value with at least p at or below it."""
    v = sorted(values)
    k = max(math.ceil(len(v) * p), 1)
    return v[k - 1]


def percentile_type7(values: list[float], p: float) -> float:
    """Linear interpolation between order statistics, the common software default."""
    v = sorted(values)
    h = (len(v) - 1) * p
    lo = math.floor(h)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (h - lo) * (v[hi] - v[lo])


def provider_ranges(rows: list[Row], percentile=percentile_type1) -> dict[str, tuple[float, float]]:
    """The middle-90% range for each published statistic, rounded as the DfE rounds."""
    series = {
        "earnings, all graduates": [r.median for r in provider_totals(rows)],
        "earnings, men": [r.median for r in provider_totals(rows, characteristic="sex", value="M")],
        "earnings, women": [r.median for r in provider_totals(rows, characteristic="sex", value="F")],
        "sustained work or study": [r.sustained for r in provider_totals(rows)],
    }
    out = {}
    for name, values in series.items():
        values = [v for v in values if v is not None]
        lo, hi = percentile(values, 0.05), percentile(values, 0.95)
        if name.startswith("earnings"):
            out[name] = (round(lo, -2), round(hi, -2))
        else:
            out[name] = (round(lo, 1), round(hi, 1))
    return out


def check_published_ranges(rows: list[Row], percentile=percentile_type1) -> Result:
    rebuilt = provider_ranges(rows, percentile)
    matched = [k for k in PUBLISHED if rebuilt[k] == PUBLISHED[k]]
    numbers = sum(a == b for k in PUBLISHED for a, b in zip(rebuilt[k], PUBLISHED[k]))
    lines = "; ".join(f"{k}: {rebuilt[k][0]:g} to {rebuilt[k][1]:g} "
                      f"({'matches' if k in matched else 'published ' + str(PUBLISHED[k])})"
                      for k in PUBLISHED)
    return Result(
        "published provider ranges",
        len(matched) == len(PUBLISHED),
        f"{numbers} of {2 * len(PUBLISHED)} published numbers reproduced. {lines}",
        {"rebuilt": rebuilt, "matched": matched, "numbers_matched": numbers},
    )


def sex_gap_share_of_men(men: float, women: float) -> float:
    return 100 * (men - women) / men


def sex_gap_share_of_women(men: float, women: float) -> float:
    return 100 * (men - women) / women


def check_national_headline(paths: list[PathPoint], published: dict[str, float],
                            gap=sex_gap_share_of_men) -> Result:
    """The national release's headline: first-degree median, share in work or
    study, and the gap between men's and women's medians, five years out."""
    at5 = {p.sex: p for p in paths if p.years_after == 5 and p.subject == "Total"}
    rebuilt = {
        "median": at5["Total"].median,
        "sustained": at5["Total"].sustained,
        "sex_gap": round(gap(at5["Male"].median, at5["Female"].median), 1),
    }
    matched = [k for k in published if rebuilt[k] == published[k]]
    return Result(
        "national headline",
        len(matched) == len(published),
        "; ".join(f"{k} {rebuilt[k]:g} (published {published[k]:g})" for k in published),
        {"rebuilt": rebuilt},
    )
