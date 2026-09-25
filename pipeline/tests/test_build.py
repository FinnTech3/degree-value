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


def test_the_written_off_subjects_are_the_ones_whose_median_graduate_repays_for_forty_years():
    p = payload()
    assert p["written_off"] == sorted(s["name"] for s in p["subjects"] if s["years"] >= p["term"])
