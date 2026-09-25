"""Run everything once and return every number the write-up, figures and app use.

report.py prints from this, scripts/make_figures.py draws from it and build.py
writes the app's data from it, so a number cannot mean one thing in the README
and another in a chart.
"""

from __future__ import annotations

import functools
import math
import statistics

from . import loans, sources, verify

PLACES = [i / 100 for i in range(5, 96)]   # 5th to 95th place among graduates in work
PHI_RANGE = 0.9                            # the "ranks move" end of the range


def spearman(a: dict[str, float], b: dict[str, float]) -> float:
    keys = sorted(set(a) & set(b))
    ra = {k: i for i, k in enumerate(sorted(keys, key=lambda k: -a[k]), 1)}
    rb = {k: i for i, k in enumerate(sorted(keys, key=lambda k: -b[k]), 1)}
    n = len(keys)
    return 1 - 6 * sum((ra[k] - rb[k]) ** 2 for k in keys) / (n * (n * n - 1))


def ranks(values: dict[str, float]) -> dict[str, int]:
    return {k: i for i, k in enumerate(sorted(values, key=lambda k: -values[k]), 1)}


def subject_paths(paths: list[sources.PathPoint]) -> dict[str, dict[int, sources.PathPoint]]:
    out: dict[str, dict[int, sources.PathPoint]] = {}
    for p in paths:
        if p.sex == "Total" and p.subject != "Total" and p.median:
            out.setdefault(p.subject, {})[p.years_after] = p
    return {s: v for s, v in out.items() if set(v) == {1, 3, 5, 10}}


def same_grades(rows: list[sources.Row], band: str = "prior_attainment_3", min_in_earnings: float = 100) -> dict:
    """How much of the gap between subjects is left among graduates with the
    same A-level points. Five years out, English and other UK universities
    (HEIs) together, national rows only. Spread is the standard deviation of
    log median pay across subjects."""
    raw, within = {}, {}
    for r in rows:
        if (r.tax_year != sources.LATEST or r.years_after != 5 or r.provider != "Total" or r.country != "Total"
                or r.region != "Total" or r.provider_type != "HEI" or r.subject == "Total" or not r.median):
            continue
        if r.characteristic == "All graduates":
            raw[r.subject_name] = r.median
        elif r.characteristic == "prior_attainment_code" and r.value == band and (r.in_earnings or 0) >= min_in_earnings:
            within[r.subject_name] = r.median
    common = sorted(s for s in within if s in raw)
    sd = lambda xs: statistics.pstdev([math.log(x) for x in xs])
    s_raw, s_within = sd([raw[s] for s in common]), sd([within[s] for s in common])
    return {"subjects": len(common), "spread_all": s_raw, "spread_same_grades": s_within,
            "narrowing": 1 - s_within / s_raw, "raw": {s: raw[s] for s in common},
            "same_grades": {s: within[s] for s in common}}


def providers(rows: list[sources.Row]) -> dict[str, list[dict]]:
    """Each university's median pay one, three and five years out, by subject."""
    out: dict[tuple[str, str], dict] = {}
    for r in rows:
        if (r.tax_year != sources.LATEST or r.provider == "Total" or r.characteristic != "All graduates"
                or r.subject == "Total"):
            continue
        d = out.setdefault((r.subject_name, r.provider), {"provider": r.provider, "name": r.provider_name,
                                                          "type": r.provider_type, "years": {}})
        d["years"][r.years_after] = {"median": r.median, "in_earnings": r.in_earnings, "graduates": r.graduates}
    by: dict[str, list[dict]] = {}
    for (subject, _), d in out.items():
        by.setdefault(subject, []).append(d)
    for v in by.values():
        v.sort(key=lambda d: d["name"])
    return by


def loan_by_subject(grads: list[loans.Graduate]) -> dict[str, dict]:
    groups: dict[str, list[loans.Graduate]] = {}
    for g in grads:
        groups.setdefault(g.subject, []).append(g)
    out = {}
    for subject, gs in groups.items():
        w = [g.weight for g in gs]
        total = sum(w)
        out[subject] = {
            "graduates": total,
            "full": sum(g.weight for g in gs if g.outcome.repaid_in_full) / total,
            "median_years": loans.weighted_median([g.outcome.years for g in gs], w),
            "median_repaid_real": loans.weighted_median([g.outcome.repaid_real / 100 for g in gs], w),
        }
    return out


@functools.lru_cache(maxsize=None)
def run() -> dict:
    rows = sources.load_leo()
    paths = sources.load_paths()
    checks = [
        verify.check_published_ranges(rows),
        verify.check_national_headline(paths, sources.load_national_headline()),
    ]

    # loans: the central run, ranks fixed for life
    t = loans.dfe_targets()
    profs = loans.profiles(paths)
    growth = loans.calibrate(profs, t["balance_nominal"], t["full_repayment_share"])
    grads = loans.simulate(profs, growth, t["balance_nominal"])
    summary = loans.summarise(grads, t["balance_nominal"])
    by_subject = loan_by_subject(grads)

    # the other end of the range: ranks move from year to year
    growth_moving = loans.calibrate(profs, t["balance_nominal"], t["full_repayment_share"], phi=PHI_RANGE,
                                    lo=-0.04, hi=0.02)
    grads_moving = loans.simulate(profs, growth_moving, t["balance_nominal"], phi=PHI_RANGE)
    summary_moving = loans.summarise(grads_moving, t["balance_nominal"])
    by_subject_moving = loan_by_subject(grads_moving)

    written_off = [s for s, v in by_subject.items() if v["median_years"] >= loans.TERM_YEARS]
    all_grads = sum(v["graduates"] for v in by_subject.values())

    # every place among graduates in work, for the app: exact at fixed ranks
    places = {}
    for p in loans.profiles(paths, include_total=True):
        places[(p.subject, p.sex)] = [loans.at_rank(p, q, growth, t["balance_nominal"]) for q in PLACES]

    # earnings paths
    sp = subject_paths(paths)
    y1 = {s: v[1].median for s, v in sp.items()}
    y10 = {s: v[10].median for s, v in sp.items()}
    r1, r10 = ranks(y1), ranks(y10)

    return {
        "checks": checks,
        "targets": t,
        "growth": growth,
        "summary": summary,
        "by_subject": by_subject,
        "growth_moving": growth_moving,
        "summary_moving": summary_moving,
        "by_subject_moving": by_subject_moving,
        "written_off": sorted(written_off),
        "written_off_share": sum(by_subject[s]["graduates"] for s in written_off) / all_grads,
        "places": places,
        "paths": sp,
        "rank_correlation": spearman(y1, y10),
        "rank_year1": r1,
        "rank_year10": r10,
        "same_grades": same_grades(rows),
        "providers": providers(rows),
    }


def all_checks_pass() -> bool:
    return all(c.passed for c in run()["checks"])
