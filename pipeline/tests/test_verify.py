"""The DfE's published provider ranges, and twins proving the check can fail."""

from __future__ import annotations

import dataclasses
import functools

from degreevalue import sources, verify


@functools.lru_cache(maxsize=None)
def rows():
    return tuple(sources.load_leo())


def test_all_eight_published_numbers_are_reproduced():
    r = verify.check_published_ranges(list(rows()))
    assert r.passed, r.summary


def test_twin_the_default_percentile_does_not_reproduce_them():
    r = verify.check_published_ranges(list(rows()), verify.percentile_type7)
    # it misses the top end of two ranges: all graduates and men
    assert r.detail["numbers_matched"] == 6
    assert not r.passed


def test_twin_england_only_is_the_wrong_provider_universe():
    england = [r for r in rows() if r.country in ("E92000001", "Total")]
    assert not verify.check_published_ranges(england).passed


def test_twin_a_misread_column_is_caught():
    # read the upper quartile as if it were the median
    swapped = [dataclasses.replace(r, median=r.upper_quartile) for r in rows()]
    assert not verify.check_published_ranges(swapped).passed


def test_percentile_definitions_on_a_known_case():
    v = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    assert verify.percentile_type1(v, 0.05) == 1.0
    assert verify.percentile_type1(v, 0.95) == 10.0
    assert abs(verify.percentile_type7(v, 0.95) - 9.55) < 1e-9


def test_national_headline_is_reproduced():
    r = verify.check_national_headline(sources.load_paths(), sources.load_national_headline())
    assert r.passed, r.summary


def test_twin_the_sex_gap_measured_against_women_does_not_match():
    r = verify.check_national_headline(sources.load_paths(), sources.load_national_headline(),
                                       gap=verify.sex_gap_share_of_women)
    assert not r.passed
