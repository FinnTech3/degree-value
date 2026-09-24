"""Load the committed LEO extract and the graduate labour market tables.

LEO (Longitudinal Education Outcomes) links graduates' student records to their
HMRC tax records, so the earnings here are what graduates were actually paid in
the 2022-23 tax year, not what they told a survey. Its gap is that it only
follows graduates for five years in this release, which is why the lifetime
projection elsewhere in this package is labelled as a projection.

Values the DfE suppresses ("c"), marks as too low to publish ("low"), or has
no data for ("x", "z") load as None. Nothing is filled in here.
"""

from __future__ import annotations

import csv
import gzip
import os
from dataclasses import dataclass

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DERIVED = os.path.join(ROOT, "data", "derived")
SOURCES = os.path.join(ROOT, "data", "sources")

LATEST = "2022/2023"


def _number(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


@dataclass(frozen=True)
class Row:
    tax_year: str
    years_after: int
    provider: str          # UKPRN, or "Total"
    provider_name: str
    provider_type: str     # HEI, FEC (further education college) or AP (alternative provider)
    country: str           # provider's country code, or "Total"
    region: str            # provider's region code, or "Total"
    subject: str           # CAH2 code, or "Total"
    subject_name: str
    characteristic: str    # "All graduates", "sex" or "prior_attainment_code"
    value: str             # e.g. "M", "prior_attainment_1", "All graduates"
    graduates: float | None
    in_earnings: float | None
    sustained: float | None   # % in sustained employment, further study or both
    lower_quartile: float | None
    median: float | None
    upper_quartile: float | None


def load_leo(path: str | None = None) -> list[Row]:
    path = path or os.path.join(DERIVED, "leo_2022_23.csv.gz")
    out = []
    with gzip.open(path, "rt", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.append(Row(
                tax_year=r["tax_year"], years_after=int(r["YAG"]),
                provider=r["ukprn"], provider_name=r["provider_name"], provider_type=r["provider_type"],
                country=r["provider_country_code"], region=r["provider_region_code"],
                subject=r["cah2_code"], subject_name=r["cah2_subject_name"],
                characteristic=r["characteristic_type"], value=r["characteristic_value"],
                graduates=_number(r["grads"]), in_earnings=_number(r["grads_earnings_include"]),
                sustained=_number(r["sust_emp_fs_or_both"]),
                lower_quartile=_number(r["earnings_LQ"]), median=_number(r["earnings_median"]),
                upper_quartile=_number(r["earnings_UQ"]),
            ))
    return out


def provider_totals(rows: list[Row], years_after: int = 5, characteristic: str = "All graduates",
                    value: str = "All graduates") -> list[Row]:
    """One row per provider, all subjects together, latest tax year, no regional split."""
    return [r for r in rows
            if r.tax_year == LATEST and r.years_after == years_after and r.provider != "Total"
            and r.subject == "Total" and r.characteristic == characteristic and r.value == value]


@dataclass(frozen=True)
class Salary:
    year: int
    age_band: str        # "16-64" or "21-30"
    group: str           # "Graduate", "Postgraduate" or "Non-graduate"
    sex: str             # "Total", "Male" or "Female"
    median: float        # nominal, full-time, rounded to £500 by the DfE


def load_salaries(path: str | None = None) -> list[Salary]:
    """DfE Graduate labour market statistics: median salary by group and age band."""
    path = path or os.path.join(SOURCES, "yearly_salaries_by_sex3_200724.csv")
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            m = _number(r["median"])
            if m is None:
                continue
            out.append(Salary(int(r["time_period"]), r["age_band"], r["graduate_type"], r["sex"], m))
    return out


@dataclass(frozen=True)
class PathPoint:
    years_after: int
    sex: str               # "Total", "Male" or "Female"
    subject: str           # subject name, or "Total"
    graduates: float | None
    lower_quartile: float | None
    median: float | None
    upper_quartile: float | None
    sustained: float | None


def load_paths(path: str | None = None) -> list[PathPoint]:
    """National LEO, 2022-23 tax year: first-degree earnings 1, 3, 5 and 10 years out."""
    path = path or os.path.join(DERIVED, "leo_paths_2022_23.csv")
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.append(PathPoint(int(r["YAG"].split()[0]), r["sex"], r["subject_name"],
                                 _number(r["grads"]), _number(r["earnings_LQ"]),
                                 _number(r["earnings_median"]), _number(r["earnings_UQ"]),
                                 _number(r["sust_emp_fs_or_both"])))
    return out


def load_national_headline(path: str | None = None) -> dict[str, float]:
    path = path or os.path.join(SOURCES, "leo_national_headline_figures.csv")
    with open(path, newline="", encoding="utf-8") as f:
        row = next(csv.DictReader(f))
    return {"median": float(row["median_nominal_fd"]), "sustained": float(row["sust_emp_fs_both_fd"]),
            "sex_gap": float(row["sex_gap"])}
