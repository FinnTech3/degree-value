#!/usr/bin/env python3
"""Cut the DfE's 787 MB LEO provider file down to what this project reads.

The DfE publishes the data behind its LEO provider dashboard as one CSV of 2.5
million rows: every tax year since 2015-16, every provider, subject, region and
graduate characteristic. This keeps:

  - the 2022-23 tax year (the latest), at one, three and five years after
    graduation
  - home and current region both "Total" (no regional splits)
  - graduates as a whole, by sex, and by prior attainment
  - the columns the analysis uses

and writes them, sorted, to data/derived/leo_2022_23.csv.gz. Earlier tax years
are kept only for the all-graduates rows, which is enough to see how the
national medians have moved.

    python3 scripts/extract_leo.py <unzipped provider_data_20250716.csv>

The source zip's address and checksum are in docs/SOURCES.md.
"""

from __future__ import annotations

import csv
import gzip
import io
import sys

KEEP = [
    "tax_year", "academic_year", "YAG", "ukprn", "provider_name", "provider_type",
    "provider_country_code", "provider_region_code", "cah2_code", "cah2_subject_name",
    "characteristic_type", "characteristic_value", "grads", "grads_uk",
    "sust_emp_fs_or_both", "grads_earnings_include",
    "earnings_LQ", "earnings_median", "earnings_UQ",
]
CHARACTERISTICS = {"All graduates", "sex", "prior_attainment_code"}


def main(path: str, out: str = "data/derived/leo_2022_23.csv.gz") -> int:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["home_region_code"] != "Total" or r["current_region_code"] != "Total":
                continue
            if r["characteristic_type"] not in CHARACTERISTICS:
                continue
            if r["tax_year"] != "2022/2023" and r["characteristic_type"] != "All graduates":
                continue
            rows.append([r[k] for k in KEEP])
    rows.sort()
    # mtime=0 so the same input always produces a byte-identical file
    with open(out, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz, \
            io.TextIOWrapper(gz, encoding="utf-8", newline="") as text:
        w = csv.writer(text, lineterminator="\n")
        w.writerow(KEEP)
        w.writerows(rows)
    print(f"{len(rows):,} rows written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
