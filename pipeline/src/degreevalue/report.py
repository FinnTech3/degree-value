"""Print every number the README quotes, in the order it quotes them.

    PYTHONPATH=pipeline/src python3 -m degreevalue.report

Refuses to print findings if a verification check has failed.
"""

from __future__ import annotations

import sys

from .study import run


def money(x: float) -> str:
    return f"£{x:,.0f}"


def main() -> int:
    r = run()
    print("Verification")
    for c in r["checks"]:
        print(f"  [{'pass' if c.passed else 'FAIL'}] {c.name}: {c.summary}")
    if not all(c.passed for c in r["checks"]):
        print("\nA check failed; nothing below would mean anything.", file=sys.stderr)
        return 1

    t, s, m = r["targets"], r["summary"], r["summary_moving"]
    print("\nThe loan model against the DfE's Plan 5 forecast (full-time, 2024 starters)")
    print(f"  tuned: pay growth after 2030 of RPI + {100 * r['growth']:.2f}% a year")
    print(f"  share repaying in full   model {s['full_repayment_share']:.1%}   DfE {t['full_repayment_share']:.0%}  (tuned)")
    print(f"  median years repaying    model {s['median_years']}   DfE {t['median_years']:g}")
    print(f"  lifetime repayments      model {money(s['repayments_real'])}   DfE {money(t['repayments_real'])}"
          f"  ({s['repayments_real'] / t['repayments_real'] - 1:+.1%})")
    print(f"  share of balance repaid  model {s['share_repaid_real']:.1%}   DfE {t['share_repaid_real']:.0%}")
    print("  by tenth of lifetime earnings: years (model / DfE), repaid in 2024-25 prices (model / DfE)")
    for d in range(1, 11):
        a, b = s["by_decile"][d], t["by_decile"][d]
        print(f"    {d:>2}  {a['years']:>4g} / {b['years']:<4g}  {money(a['repayments_real']):>8} / {money(b['repayments_real'])}")
    print(f"  with ranks moving (phi 0.9): growth RPI {100 * r['growth_moving']:+.2f}%, median years "
          f"{m['median_years']}, repayments {money(m['repayments_real'])}")

    print("\nBy subject: repay in full, median years, median repaid in 2024-25 prices (ranks moving in brackets)")
    bs, bm = r["by_subject"], r["by_subject_moving"]
    for subj in sorted(bs, key=lambda k: (bs[k]["median_years"], -bs[k]["full"])):
        a, b = bs[subj], bm[subj]
        print(f"  {subj:<42} {a['full']:>4.0%} ({b['full']:.0%})  {a['median_years']:>2}y ({b['median_years']})  "
              f"{money(a['median_repaid_real']):>8} ({money(b['median_repaid_real'])})")
    wo = r["written_off"]
    print(f"  median graduate still repaying at write-off: {len(wo)} of {len(bs)} subjects, "
          f"{r['written_off_share']:.0%} of graduates")

    print("\nEarnings paths, median, 2022-23 tax year")
    p = r["paths"]
    for subj in ("Economics", "Medicine and dentistry", "Nursing and midwifery", "Law", "Creative arts and design",
                 "Education and teaching", "Performing arts"):
        if subj in p:
            v = p[subj]
            print(f"  {subj:<28} " + "  ".join(f"yr{y} {money(v[y].median)}" for y in (1, 3, 5, 10)))
    r1, r10 = r["rank_year1"], r["rank_year10"]
    print(f"  rank correlation, year 1 against year 10, {len(r1)} subjects: {r['rank_correlation']:.2f}")
    moves = sorted(r1, key=lambda k: r10[k] - r1[k])
    for subj in moves[:3] + moves[-3:]:
        print(f"    {subj:<40} {r1[subj]:>2} -> {r10[subj]:>2}")

    g = r["same_grades"]
    print(f"\nSame A-level points (300 to 359 UCAS points), five years out, {g['subjects']} subjects")
    print(f"  spread of log median pay across subjects: all graduates {g['spread_all']:.3f}, "
          f"same grades {g['spread_same_grades']:.3f}, narrowing {g['narrowing']:.0%}")

    ob = [d for d in r["providers"].get("Economics", []) if "Brookes" in d["name"]]
    for d in ob:
        y5 = d["years"].get(5, {})
        print(f"\n{d['name']}, economics, five years out: median {money(y5.get('median') or 0)}, "
              f"{y5.get('in_earnings'):g} graduates in the earnings figure")
    return 0


if __name__ == "__main__":
    sys.exit(main())
