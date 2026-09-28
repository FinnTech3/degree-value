"""Write the data the web tool loads, from the same run the README quotes.

    PYTHONPATH=pipeline/src python3 -m degreevalue.build

One file, data/built/degree.json, copied into the app at build time:

  - for each subject: its earnings one, three, five and ten years out
    (quartiles, all graduates, women and men), its loan outcome in the
    central run and with ranks moving, and the exact loan of a graduate at
    every place from the 5th to the 95th among its graduates in work;
  - for each subject, every university's median pay one, three and five
    years out, where the DfE publishes it;
  - for each subject, its thread: what the median graduate still owes at
    the end of each year, in pounds at 2024-25 prices, to the nearest £10,
    until the loan is cleared or written off. The app draws these;
  - the checks, the calibration and the model's comparison with the DfE.

Refuses to write anything if a verification check fails.
"""

from __future__ import annotations

import json
import os
import sys

from . import loans
from .sources import ROOT
from .study import PLACES, run

BUILT = os.path.join(ROOT, "data", "built")
SEXES = ("Total", "Female", "Male")


def payload() -> dict:
    r = run()
    t = r["targets"]
    subjects = []
    providers: list[list] = []
    provider_index: dict[str, int] = {}
    for name in sorted(r["by_subject"]):
        a, b = r["by_subject"][name], r["by_subject_moving"][name]
        paths, places, not_working = {}, {}, {}
        for sex in SEXES:
            pts = {p.years_after: p for p in r["all_paths"] if p.subject == name and p.sex == sex}
            paths[sex] = {str(y): [pts[y].lower_quartile, pts[y].median, pts[y].upper_quartile]
                          for y in (1, 3, 5, 10) if y in pts}
            prof = r["profiles"].get((name, sex))
            if prof:
                not_working[sex] = round(prof.not_working, 4)
            outcomes = r["places"].get((name, sex))
            if outcomes:
                places[sex] = {"years": [o.years for o in outcomes],
                               "cleared": [o.repaid_in_full for o in outcomes],
                               "repaid": [round(o.repaid_real / 100) for o in outcomes]}
        unis = []
        for d in r["providers"].get(name, []):
            key = d["provider"]
            if key not in provider_index:
                provider_index[key] = len(providers)
                providers.append([d["name"], d["type"]])
            ys = d["years"]
            unis.append([provider_index[key]] + [ys.get(y, {}).get("median") for y in (1, 3, 5)]
                        + [ys.get(5, {}).get("in_earnings")])
        thread = loans.balance_path(r["profiles"][(name, "Total")], 0.5, r["growth"], t["balance_nominal"])
        subjects.append({
            "name": name,
            "thread": [round(b, -1) for b in thread],
            "graduates": round(a["graduates"]),
            "full": a["full"], "years": a["median_years"], "cleared": a["median_cleared"],
            "repaid": round(a["median_repaid_real"]),
            "full_moving": round(b["full"], 10), "years_moving": b["median_years"],
            "rank1": r["rank_year1"].get(name), "rank10": r["rank_year10"].get(name),
            "paths": paths, "places": places, "not_working": not_working, "universities": unis,
        })
    s = r["summary"]
    return {
        "places": PLACES,
        "first_year": loans.FIRST_YEAR,
        "graduation_age": loans.GRADUATION_AGE,
        "term": loans.TERM_YEARS,
        "balance": t["balance_nominal"],
        "balance_real": round(t["balance_nominal"] / loans.dfe_targets()["deflator_at_start"]),
        "growth": r["growth"],
        # rounded well below their precision: Python 3.12's sum() compensates
        # for rounding and 3.11's does not, and the file must build the same on both
        "model": {k: round(s[k], 10)
                  for k in ("full_repayment_share", "median_years", "repayments_real", "share_repaid_real")},
        "dfe": {k: t[k] for k in ("full_repayment_share", "median_years", "repayments_real", "share_repaid_real")},
        "written_off": r["written_off"],
        "written_off_share": r["written_off_share"],
        "checks": [{"name": c.name, "passed": c.passed, "summary": c.summary} for c in r["checks"]],
        "providers": providers,
        "subjects": subjects,
    }


def main() -> int:
    if not all(c.passed for c in run()["checks"]):
        print("A verification check failed; not writing the app's data.", file=sys.stderr)
        return 1
    os.makedirs(BUILT, exist_ok=True)
    text = json.dumps(payload(), separators=(",", ":"), ensure_ascii=False) + "\n"
    with open(os.path.join(BUILT, "degree.json"), "w", encoding="utf-8") as f:
        f.write(text)
    print(f"data/built/degree.json: {len(text.encode()):,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
