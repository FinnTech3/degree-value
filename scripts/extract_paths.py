#!/usr/bin/env python3
"""Cut the DfE's national LEO release down to earnings paths by subject.

The national release (not the provider-level one) follows first-degree
graduates to ten years after graduation. In the 2022-23 tax year it shows four
cohorts at once: one, three, five and ten years out. Read across the four, they
give each subject's earnings path to about age 32, all measured in the same
year's pounds.

Keeps UK-domiciled first-degree graduates, by subject and sex, with every
other breakdown at its total, and writes data/derived/leo_paths_2022_23.csv.

    python3 scripts/extract_paths.py <unzipped data/underlying_data.csv>
"""

from __future__ import annotations

import csv
import sys

TOTAL_DIMENSIONS = ["ethnicity_major", "inst_type", "study_mode", "age_band", "POLAR4",
                    "prior_attainment", "FSM", "region_name_origin", "residence"]
KEEP = ["time_period", "academic_year", "YAG", "sex", "subject_name", "grads", "earnings_include",
        "earnings_LQ", "earnings_median", "earnings_UQ", "sust_emp_fs_or_both"]


def main(path: str, out: str = "data/derived/leo_paths_2022_23.csv") -> int:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["time_period"] != "202223" or r["qualification_level"] != "First-degree":
                continue
            if r["country_of_domicile_grouped"] != "UK" or r["region_code_current"] != "Total":
                continue
            if any(r[d] != "Total" for d in TOTAL_DIMENSIONS):
                continue
            rows.append([r[k] for k in KEEP])
    rows.sort()
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(KEEP)
        w.writerows(rows)
    print(f"{len(rows):,} rows written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
