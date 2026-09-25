"""Plan 5 student loans, repaid year by year, for every kind of graduate.

This is the part of the project that has to look forty years ahead, so it is
the part that is checked hardest. The DfE forecasts Plan 5 repayments with a
microsimulation built on the same LEO data used here, and publishes what comes
out: the share of borrowers expected to repay in full, and, for each tenth of
borrowers by lifetime earnings, how long they repay for. The model below is set
up from public inputs, one number is tuned so that it matches the DfE's share
repaying in full, and everything else it produces is then compared with what
the DfE published. It is judged on the comparisons it was not tuned to.

The cohort is the DfE's: full-time undergraduates starting in autumn 2024, on
three-year courses, graduating in summer 2027 at 21, entering repayment in
April 2028 with the DfE's forecast average balance, and written off after
forty years.

Earnings. LEO gives, for each subject and sex, the lower quartile, median and
upper quartile of what graduates earned one, three, five and ten years after
graduating, all in 2022-23 pounds. Between those years, log earnings are
interpolated in a straight line. Past ten years out, at 31, each path follows
the ONS's 2025 profile of median pay by age for the graduate's sex (ASHE table
6.7a, all employees): a little growth into the forties and a decline through
the fifties, taken from data rather than chosen.

Rank. A graduate's place in their subject's distribution can move from year to
year: z(t) = phi z(t-1) + sqrt(1 - phi^2) e(t), with e(t) standard normal. Each
year's z is still standard normal, so every published quartile is reproduced
exactly in every year. Whoever falls below the share not in sustained work or
study earns nothing that year; everyone else earns the matching point of a
log-normal fitted through that year's quartiles. The central run keeps everyone
at the same rank for life (phi = 1). Letting ranks move makes more people repay
in full, not fewer, because a good year pays down a lump; the report shows how
much.

The tuned number. From 2031, when the OBR's forecast ends, economy-wide pay
grows at RPI plus a constant, and that constant is the one number set so the
model's share repaying in full equals the DfE's 56%. It comes out at about 0.3%
a year. The model is then judged on what it was not tuned to. It matches the
median length of repayment (32 years against 31.5) and the bottom half of
earners repaying for the full term. It misses in two stated ways: it collects
about 5% less over the term than the DfE forecasts, and because each graduate
keeps their rank for life, the best-paid half finishes three to six years
sooner than the DfE expects. Tests pin both gaps so neither can drift unseen.

Money. Earnings are moved from 2022-23 pounds to each future year with actual
average weekly earnings to mid-2026 (ONS series KAB9) and the OBR's forecast
after that. Repayments are 9% of earnings above the threshold, which is £25,000
to 2026-27, the DfE's published uprated values to 2029-30, and RPI-uprated
after. Interest is RPI. All balances and payments are held in whole pence.
Real values are in 2024-25 prices, starting from the DfE's own ratio of real
to nominal balance at the start of repayment and adding 2% CPI a year after.
"""

from __future__ import annotations

import csv
import functools
import math
import os
import random
from dataclasses import dataclass

from .sheets import read_xlsx
from .sources import SOURCES, PathPoint

RATE_PCT = 9
TERM_YEARS = 40
FIRST_YEAR = 2028            # tax year 2028-29 is the first year of repayment
GRADUATION_AGE = 21
LAST_LEO_AGE = GRADUATION_AGE + 10
Z_QUARTILE = 0.6744897501960817   # standard normal upper quartile


# --------------------------------------------------------------------------
# inputs

def _csv(name: str) -> list[dict]:
    with open(os.path.join(SOURCES, name), newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


@functools.lru_cache(maxsize=None)
def pay_index(real_growth: float = 0.0) -> dict[int, float]:
    """Average weekly earnings by tax year (the year it starts), with 2022 = 1.

    Actual ONS values are used for every complete tax year and for the part of
    2026-27 published so far; the OBR forecast carries it to 2030; after that
    pay grows at RPI plus `real_growth`.
    """
    monthly = {}
    with open(os.path.join(SOURCES, "ons_awe_kab9.csv"), newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) == 2 and len(row[0]) == 8 and row[0][:4].isdigit():
                year, mon = int(row[0][:4]), row[0][5:]
                monthly[(year, mon)] = float(row[1])
    months = ["APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC", "JAN", "FEB", "MAR"]

    def tax_year_mean(y: int) -> float | None:
        vals = [monthly.get((y if i < 9 else y + 1, m)) for i, m in enumerate(months)]
        vals = [v for v in vals if v is not None]
        return sum(vals) / len(vals) if vals else None

    index = {}
    base = tax_year_mean(2022)
    y = 2022
    while (v := tax_year_mean(y)) is not None:
        index[y] = v / base
        y += 1
    growth = {int(r["year"]): float(r["earnings_growth_pct"]) / 100
              for r in _csv("macro_assumptions.csv") if r["earnings_growth_pct"]}
    rpi = rpi_path()
    for year in range(y, FIRST_YEAR + TERM_YEARS + 1):
        g = growth[year] if year in growth and year <= 2030 else rpi[year] + real_growth
        index[year] = index[year - 1] * (1 + g)
    return index


@functools.lru_cache(maxsize=None)
def rpi_path() -> dict[int, float]:
    rpi = {int(r["year"]): float(r["rpi_pct"]) / 100 for r in _csv("macro_assumptions.csv")}
    last = max(rpi)
    return {y: rpi.get(y, rpi[last]) for y in range(2027, FIRST_YEAR + TERM_YEARS + 1)}


@functools.lru_cache(maxsize=None)
def thresholds() -> dict[int, int]:
    """Plan 5 repayment threshold by tax year, in pounds."""
    published = {int(r["time_period"][:4]): int(r["repayment_threshold"])
                 for r in _csv("slf_2024_25_long_6b.csv") if r["plan_type"] == "Plan 5"}
    rpi = rpi_path()
    out = dict(published)
    for y in range(max(published) + 1, FIRST_YEAR + TERM_YEARS + 1):
        out[y] = round(out[y - 1] * (1 + rpi[y]))
    return out


@functools.lru_cache(maxsize=None)
def age_profile() -> dict[str, list[tuple[float, float]]]:
    """(age, log median annual pay) at each ASHE age band's midpoint, by sex."""
    sheets = read_xlsx(os.path.join(SOURCES, "ashe_table_6_7a_annual_pay_gross_2025_provisional.xlsx"))
    mids = {"22-29": 25.5, "30-39": 34.5, "40-49": 44.5, "50-59": 54.5, "60+": 64.5}
    out = {}
    for sheet, sex in (("All", "Total"), ("Male", "Male"), ("Female", "Female")):
        pts = []
        for row in sheets[sheet]:
            label = row[0].strip() if row else ""
            if label in mids:
                pts.append((mids[label], math.log(float(row[3]))))
        out[sex] = sorted(pts)
    return out


def age_factor(profile: list[tuple[float, float]], age: float) -> float:
    """Pay at `age` relative to pay at the last LEO age, following ASHE."""
    def log_at(a: float) -> float:
        if a <= profile[0][0]:
            return profile[0][1]
        for (a0, v0), (a1, v1) in zip(profile, profile[1:]):
            if a <= a1:
                return v0 + (a - a0) / (a1 - a0) * (v1 - v0)
        return profile[-1][1]
    return math.exp(log_at(age) - log_at(LAST_LEO_AGE))


@functools.lru_cache(maxsize=None)
def dfe_targets() -> dict:
    rows = _csv("slf_2024_25_long_9.csv")
    by_decile = {int(r["lifetime_earning_decile"]): {
        "years": float(r["median_length_of_repayment"]),
        "share_repaid_real": float(r["proportion_of_outlay_repaid_real_terms"]) / 100,
        "repayments_real": float(r["average_lifetime_repayments_real_terms"]),
    } for r in rows if r["study_type"] == "Total" and r["sex"] == "Total" and r["lifetime_earning_decile"] != "Total"}
    ft = next(r for r in rows if r["study_type"] == "Higher education full time" and r["sex"] == "Total")
    key = next(r for r in _csv("slf_2024_25_key_statistics_ay.csv")
               if r["loan_type"] == "Higher education full time")
    nominal = float(ft["average_loan_balance_at_srdd_nominal"])
    real = float(ft["average_loan_balance_at_srdd_real_terms"])
    return {
        "balance_nominal": nominal,
        "balance_real": real,
        # the DfE's own price level at the start of repayment, relative to 2024-25
        "deflator_at_start": nominal / real,
        "repayments_real": float(ft["average_lifetime_repayments_real_terms"]),
        "median_years": float(ft["median_length_of_repayment"]),
        "share_repaid_real": float(ft["proportion_of_outlay_repaid_real_terms"]) / 100,
        "full_repayment_share": float(key["proportion_expected_to_fully_repay"]) / 100,
        "by_decile": by_decile,
    }


# --------------------------------------------------------------------------
# earnings

@dataclass(frozen=True)
class Profile:
    subject: str
    sex: str
    graduates: float
    not_working: float                 # share with no earnings
    points: dict[int, tuple[float, float]]   # years out -> (log median, log sd)


def profiles(paths: list[PathPoint], include_total: bool = False) -> list[Profile]:
    """One earnings profile per subject and sex that has all four years published.

    The simulation runs women and men separately and weights them, so the
    all-graduates profile of each subject is left out unless asked for; the
    app uses it for a reader who does not say.
    """
    groups: dict[tuple[str, str], dict[int, PathPoint]] = {}
    for p in paths:
        groups.setdefault((p.subject, p.sex), {})[p.years_after] = p
    out = []
    for (subject, sex), pts in groups.items():
        if subject == "Total" or (sex == "Total" and not include_total) or set(pts) != {1, 3, 5, 10}:
            continue
        points = {}
        for y, p in pts.items():
            lo, hi = p.lower_quartile, p.upper_quartile
            if p.median is None or lo is None or hi is None:
                break
            points[y] = (math.log(p.median), (math.log(hi) - math.log(lo)) / (2 * Z_QUARTILE))
        else:
            five = pts[5]
            out.append(Profile(subject, sex, pts[1].graduates or 0.0,
                               1 - (five.sustained or 100) / 100, points))
    return out


def log_point(profile: Profile, years_after: float) -> tuple[float, float]:
    """Log median and log sd at any point in the first ten years, interpolated."""
    ys = sorted(profile.points)
    if years_after <= ys[0]:
        return profile.points[ys[0]]
    for a, b in zip(ys, ys[1:]):
        if years_after <= b:
            w = (years_after - a) / (b - a)
            (ma, sa), (mb, sb) = profile.points[a], profile.points[b]
            return ma + w * (mb - ma), sa + w * (sb - sa)
    return profile.points[ys[-1]]


def inverse_normal(p: float) -> float:
    """Acklam's rational approximation to the inverse standard normal CDF."""
    a = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2,
         1.383577518672690e2, -3.066479806614716e1, 2.506628277459239e0]
    b = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2,
         6.680131188771972e1, -1.328068155288572e1]
    c = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838e0,
         -2.549732539343734e0, 4.374664141464968e0, 2.938163982698783e0]
    d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996e0, 3.754408661907416e0]
    lo = 0.02425
    if p < lo:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > 1 - lo:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def earnings_path(profile: Profile, ages: list[tuple[float, float]], phi: float,
                  pay: dict[int, float], rng: random.Random) -> list[int]:
    """Nominal earnings in pence for each of the 40 repayment years."""
    zs = []
    z = rng.gauss(0.0, 1.0)
    shock = math.sqrt(max(0.0, 1 - phi * phi))
    for k in range(1, TERM_YEARS + 1):
        if k > 1:
            z = phi * z + shock * rng.gauss(0.0, 1.0)
        zs.append(z)
    return earnings_for(profile, ages, [0.5 * math.erfc(-z / math.sqrt(2)) for z in zs], pay)


def earnings_for(profile: Profile, ages: list[tuple[float, float]], ranks: list[float],
                 pay: dict[int, float]) -> list[int]:
    """Nominal earnings in pence, given the graduate's rank (0 to 1) in each year."""
    out = []
    for k, u in enumerate(ranks, 1):
        if u <= profile.not_working:
            out.append(0)
            continue
        within = inverse_normal(min(max((u - profile.not_working) / (1 - profile.not_working), 1e-12), 1 - 1e-12))
        mu, sd = log_point(profile, min(k, 10))
        real = math.exp(mu + within * sd)
        age = GRADUATION_AGE + k
        if age > LAST_LEO_AGE:
            real *= age_factor(ages, age)
        out.append(round(real * pay[FIRST_YEAR + k - 1] * 100))
    return out


# --------------------------------------------------------------------------
# repayment

@dataclass(frozen=True)
class Outcome:
    repaid_in_full: bool
    years: int                  # years until repaid, or the full term if written off (as the DfE counts)
    repaid_nominal: int         # pence
    repaid_real: int            # pence, deflated to 2024-25 prices with CPI
    lifetime_earnings_real: int


def repay(balance_pence: int, earnings: list[int], rpi: dict[int, float], threshold: dict[int, int],
          cpi: float = 0.02, first_deflator: float = 1.0) -> Outcome:
    """Run one loan through its term: interest added, then 9% above the threshold
    collected, each year, until it is cleared or written off.

    Real values are in 2024-25 prices. `first_deflator` is the price level of
    the first repayment year relative to 2024-25; each later year adds `cpi`.
    """
    balance = balance_pence
    paid = paid_real = earned_real = 0
    deflator = first_deflator / (1 + cpi)
    for k, e in enumerate(earnings):
        year = FIRST_YEAR + k
        deflator *= (1 + cpi)
        earned_real += round(e / deflator)
        balance += round(balance * rpi[year])
        due = max(0, (e - threshold[year] * 100) * RATE_PCT // 100)
        payment = min(due, balance)
        balance -= payment
        paid += payment
        paid_real += round(payment / deflator)
        if balance == 0:
            for rest in earnings[k + 1:]:
                deflator *= (1 + cpi)
                earned_real += round(rest / deflator)
            return Outcome(True, k + 1, paid, paid_real, earned_real)
    return Outcome(False, TERM_YEARS, paid, paid_real, earned_real)


@dataclass(frozen=True)
class Graduate:
    subject: str
    sex: str
    weight: float
    outcome: Outcome


def simulate(profs: list[Profile], real_growth: float, balance_pounds: float, phi: float = 1.0,
             people: int = 400, seed: int = 2024, first_deflator: float | None = None) -> list[Graduate]:
    """Every graduate the model follows. Deterministic: each subject and sex has
    its own seeded generator, so the same inputs give the same answer."""
    pay, rpi, thr, ages = pay_index(real_growth), rpi_path(), thresholds(), age_profile()
    balance = round(balance_pounds * 100)
    if first_deflator is None:
        first_deflator = dfe_targets()["deflator_at_start"]
    out = []
    for prof in profs:
        rng = random.Random(f"{seed}:{prof.subject}:{prof.sex}")
        w = prof.graduates / people
        for _ in range(people):
            path = earnings_path(prof, ages[prof.sex], phi, pay, rng)
            out.append(Graduate(prof.subject, prof.sex, w,
                                repay(balance, path, rpi, thr, first_deflator=first_deflator)))
    return out


def at_rank(profile: Profile, place: float, real_growth: float, balance_pounds: float) -> Outcome:
    """The loan of a graduate who stays at one place among their subject's
    graduates for life: `place` 0.5 is the median graduate. The lowest places,
    up to the share not in sustained work or study, earn nothing.

    With ranks fixed, as in the central run, this is exact rather than a
    simulation, which is what lets the app show every place on a slider.
    """
    earnings = earnings_for(profile, age_profile()[profile.sex], [place] * TERM_YEARS, pay_index(real_growth))
    return repay(round(balance_pounds * 100), earnings, rpi_path(), thresholds(),
                 first_deflator=dfe_targets()["deflator_at_start"])


def clearing_share(profile: Profile, real_growth: float, balance_pounds: float, steps: int = 30) -> float:
    """The share of a subject's graduates who clear the loan before it is
    written off. Better-paid places never take longer, so there is one place
    above which everyone clears it; this finds it by bisection."""
    if not at_rank(profile, 1 - 1e-9, real_growth, balance_pounds).repaid_in_full:
        return 0.0
    lo, hi = 0.0, 1 - 1e-9
    for _ in range(steps):
        mid = (lo + hi) / 2
        if at_rank(profile, mid, real_growth, balance_pounds).repaid_in_full:
            hi = mid
        else:
            lo = mid
    return 1 - hi


def summarise(grads: list[Graduate], balance_pounds: float) -> dict:
    total = math.fsum(g.weight for g in grads)
    full = sum(g.weight for g in grads if g.outcome.repaid_in_full) / total
    ordered = sorted(grads, key=lambda g: g.outcome.lifetime_earnings_real)
    deciles: list[list[Graduate]] = [[] for _ in range(10)]
    acc = 0.0
    for g in ordered:
        deciles[min(9, int(10 * acc / total + TIE))].append(g)
        acc += g.weight
    by = {}
    # the balance at the start of repayment in 2024-25 prices, at the DfE's own price level
    real_outlay = balance_pounds * 100 / dfe_targets()["deflator_at_start"]
    for i, d in enumerate(deciles, 1):
        yrs = [g.outcome.years for g in d]
        weights = [g.weight for g in d]
        by[i] = {
            "years": weighted_median(yrs, weights),
            "share_repaid_real": sum(g.outcome.repaid_real * g.weight for g in d) / sum(weights) / real_outlay,
            "repayments_real": sum(g.outcome.repaid_real * g.weight for g in d) / sum(weights) / 100,
        }
    all_years = weighted_median([g.outcome.years for g in grads], [g.weight for g in grads])
    share_real = sum(g.outcome.repaid_real * g.weight for g in grads) / total / real_outlay
    repaid_real = sum(g.outcome.repaid_real * g.weight for g in grads) / total / 100
    return {"full_repayment_share": full, "median_years": all_years, "share_repaid_real": share_real,
            "repayments_real": repaid_real, "by_decile": by}


# Running totals of weights pick out medians and deciles. When the weights are
# equal, the total can fall exactly on the halfway mark, and whether the
# running sum reaches it would then depend on rounding in the last digit,
# which differs between Python versions. Totals are summed exactly and a
# running sum within this share of a boundary counts as on it.
TIE = 1e-9


def weighted_median(values: list[float], weights: list[float]) -> float:
    """The lower of the two middle values on a tie."""
    pairs = sorted(zip(values, weights))
    half = math.fsum(weights) / 2
    acc = 0.0
    for v, w in pairs:
        acc += w
        if acc >= half * (1 - TIE):
            return v
    return pairs[-1][0]


def calibrate(profs: list[Profile], balance_pounds: float, target: float, phi: float = 1.0,
              lo: float = -0.02, hi: float = 0.02, steps: int = 16, people: int = 200) -> float:
    """The real pay growth after 2030 that reproduces the target share repaying
    in full, found by bisection. Faster pay growth means more full repayers."""
    for _ in range(steps):
        mid = (lo + hi) / 2
        share = summarise(simulate(profs, mid, balance_pounds, phi=phi, people=people),
                          balance_pounds)["full_repayment_share"]
        if share < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2
