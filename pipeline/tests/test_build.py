"""The app's data must say what the report says."""

from __future__ import annotations

import functools

from degreevalue import build, study


@functools.lru_cache(maxsize=None)
def payload() -> dict:
    return build.payload()


def test_every_subject_in_the_loan_model_is_in_the_app():
    names = [s["name"] for s in payload()["subjects"]]
    assert names == sorted(study.run()["by_subject"])


def test_each_place_on_the_slider_is_stored_and_better_pay_never_repays_slower():
    for s in payload()["subjects"]:
        for sex, v in s["places"].items():
            assert len(v["years"]) == len(study.PLACES)
            assert all(a >= b for a, b in zip(v["years"], v["years"][1:])), (s["name"], sex)


def test_the_written_off_subjects_are_the_ones_whose_median_graduate_never_clears_it():
    p = payload()
    assert p["written_off"] == sorted(s["name"] for s in p["subjects"] if not s["cleared"])
    assert all(s["years"] == p["term"] for s in p["subjects"] if not s["cleared"])


def test_each_thread_runs_exactly_as_long_as_the_loan_the_app_quotes():
    p = payload()
    for s in p["subjects"]:
        t = s["thread"]
        assert len(t) == s["years"], s["name"]
        if s["cleared"]:
            assert t[-1] == 0 and all(b > 0 for b in t[:-1]), s["name"]
        else:
            assert t[-1] > 0, s["name"]


def test_twin_a_thread_from_a_better_paid_place_never_runs_longer():
    r = study.run()
    for name in ("Economics", "Creative arts and design"):
        prof = r["profiles"][(name, "Total")]
        from degreevalue import loans

        low = loans.balance_path(prof, 0.3, r["growth"], r["targets"]["balance_nominal"])
        high = loans.balance_path(prof, 0.7, r["growth"], r["targets"]["balance_nominal"])
        assert len(high) <= len(low)
        assert all(h <= lo for h, lo in zip(high, low))
