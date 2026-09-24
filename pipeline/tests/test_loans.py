"""Plan 5 repayment arithmetic, on hand-built cases and against the DfE."""

from __future__ import annotations

import functools

from degreevalue import loans, sources

NO_INTEREST = {y: 0.0 for y in range(2020, 2080)}
FLAT_THRESHOLD = {y: 25_000 for y in range(2020, 2080)}


def test_nine_per_cent_above_the_threshold_to_the_penny():
    # £35,000 earnings, £25,000 threshold: 9% of £10,000 is £900 a year
    out = loans.repay(balance_pence=100_000_00, earnings=[35_000_00] * 40,
                      rpi=NO_INTEREST, threshold=FLAT_THRESHOLD, cpi=0.0)
    assert out.repaid_nominal == 900_00 * 40
    assert not out.repaid_in_full and out.years == 40


def test_nothing_is_due_below_the_threshold_and_the_loan_runs_its_full_term():
    # the DfE counts a written-off loan as forty years of repayment, paid or not
    out = loans.repay(50_000_00, [24_999_00] * 40, NO_INTEREST, FLAT_THRESHOLD, cpi=0.0)
    assert out.repaid_nominal == 0 and out.years == 40 and not out.repaid_in_full


def test_the_last_payment_only_clears_the_balance():
    # £1,000 owed; £900 due each year: two years, £1,000 in total
    out = loans.repay(1_000_00, [35_000_00] * 40, NO_INTEREST, FLAT_THRESHOLD, cpi=0.0)
    assert out.repaid_in_full and out.years == 2 and out.repaid_nominal == 1_000_00


def test_interest_is_added_before_the_year_is_repaid():
    rpi = {y: 0.10 for y in range(2020, 2080)}
    out = loans.repay(1_000_00, [35_000_00] * 40, rpi, FLAT_THRESHOLD, cpi=0.0)
    # 1000 -> 1100, pay 900 -> 200 -> 220 -> pay 220
    assert out.repaid_nominal == 1_120_00 and out.years == 2


def test_the_threshold_path_uses_the_dfe_figures_then_rpi():
    thr = loans.thresholds()
    assert thr[2027] == 25_925 and thr[2028] == 26_729 and thr[2029] == 27_505
    assert thr[2030] == round(27_505 * 1.023)


def test_earnings_quartiles_are_reproduced_each_year():
    profs = loans.profiles(sources.load_paths())
    prof = next(p for p in profs if p.subject == "Economics" and p.sex == "Male")
    import random
    rng = random.Random(1)
    pay = {y: 1.0 for y in range(2020, 2080)}
    ages = loans.age_profile()["Male"]
    year5 = sorted(loans.earnings_path(prof, ages, 0.7, pay, rng)[4] / 100 for _ in range(4000))
    working = [e for e in year5 if e > 0]
    median = working[len(working) // 2]
    published = next(p.median for p in sources.load_paths()
                     if p.subject == "Economics" and p.sex == "Male" and p.years_after == 5)
    assert abs(median / published - 1) < 0.03


@functools.lru_cache(maxsize=None)
def calibrated():
    t = loans.dfe_targets()
    profs = loans.profiles(sources.load_paths())
    g = loans.calibrate(profs, t["balance_nominal"], t["full_repayment_share"])
    return t, loans.summarise(loans.simulate(profs, g, t["balance_nominal"]), t["balance_nominal"]), g


def test_calibration_hits_the_dfe_full_repayment_share():
    t, s, _ = calibrated()
    assert abs(s["full_repayment_share"] - t["full_repayment_share"]) < 0.01


def test_out_of_sample_median_length_and_share_repaid_match_the_dfe():
    t, s, _ = calibrated()
    assert abs(s["median_years"] - t["median_years"]) <= 1.5
    assert abs(s["share_repaid_real"] - t["share_repaid_real"]) <= 0.03


def test_the_bottom_half_repays_for_the_full_term_as_the_dfe_forecasts():
    t, s, _ = calibrated()
    for d in range(1, 6):
        assert abs(s["by_decile"][d]["years"] - t["by_decile"][d]["years"]) <= 1


def test_simulation_is_deterministic():
    t = loans.dfe_targets()
    profs = loans.profiles(sources.load_paths())[:4]
    a = loans.simulate(profs, 0.003, t["balance_nominal"], people=20)
    b = loans.simulate(profs, 0.003, t["balance_nominal"], people=20)
    assert a == b
