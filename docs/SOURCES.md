# Sources

Everything was downloaded on 24 September 2026. Small files are committed in
`data/sources` as downloaded, or as the one table taken from a larger release.
The two LEO releases are too large to commit; the extracts the analysis reads
are in `data/derived`, made by the scripts named below, and the archives'
SHA-256 are listed so a fresh download can be checked against them.

## Committed

| File | Publisher and title | SHA-256 |
|---|---|---|
| `leo_national_headline_figures.csv` | DfE, LEO graduate and postgraduate outcomes, tax year 2022-23: headline figures | `4c2d55bc58221da81308e44111c3c086c95d321ed5b262f50806586d3af55527` |
| `leo_variable_names_lookup.csv` | DfE, LEO graduate outcomes provider level data 2022-23: variable lookup, including the prior attainment bands | `daead742c1d39f66df7d53f2b78981885ff283ac660a3c50670c375850a47910` |
| `slf_2024_25_long_9.csv` | DfE, Student loan forecasts for England 2024-25: Plan 5 repayment outcomes by lifetime earnings decile | `184436fc38d4b2ea553bb233fc253ed10a385da2b043ba7916f0586e7b47322e` |
| `slf_2024_25_long_6b.csv` | as above: repayment thresholds by plan | `69a2284db39c7b3bed8a4d2f534fe123b5471e691e2ba23cc30dfba1606bd271` |
| `slf_2024_25_key_statistics_ay.csv` | as above: key statistics, including the share expected to repay in full | `c3f4275e595ea1276c96d3012109afd5e135557ccbf5088eefb92518ebd823c2` |
| `yearly_salaries_by_sex3_200724.csv` | DfE, Graduate labour market statistics 2024: median salary by graduate type, age band and sex | `5a77349f516b95598998229de0e54c1ef79069f3003b4d007829b55f3a8d3d2b` |
| `ashe_table_6_7a_annual_pay_gross_2025_provisional.xlsx` | ONS, Annual Survey of Hours and Earnings 2025 provisional, table 6.7a (annual gross pay by age group), from `ashetable62025provisional.zip` | `00e6bc64a47391f18cfe9a6fa6c064eb114f074e8178ac8c23628bb6c72c2a02` |
| `ons_awe_kab9.csv` | ONS, average weekly earnings, whole economy, total pay, seasonally adjusted (series KAB9) | `cbe3ded9b676a67bd63b33d2ca0504d39380bf51166111c1845af5cba4c6c524` |
| `macro_assumptions.csv` | RPI and average earnings growth, 2027 to 2031, typed from the OBR's Economic and fiscal outlook, March 2026, with a note on each row saying where it comes from | `a3ed245d9b9ec1ed1bb9b413ef46fbb040fac93d6516f5ec1294b9ab02b50cda` |

Addresses:

- LEO provider level data 2022-23: https://content.explore-education-statistics.service.gov.uk/api/releases/a13c6267-1527-4761-bf8e-3566d8d26629/files?fromPage=ReleaseDownloads
- LEO graduate and postgraduate outcomes (national) 2022-23: https://content.explore-education-statistics.service.gov.uk/api/releases/83556e53-65d7-45af-7b11-08dd9854b6b7/files?fromPage=ReleaseDownloads
- Student loan forecasts for England 2024-25: https://content.explore-education-statistics.service.gov.uk/api/releases/e9726259-7fe5-44c3-866d-afc3ba9a7b74/files?fromPage=ReleaseDownloads
- Graduate labour market statistics 2024: https://content.explore-education-statistics.service.gov.uk/api/releases/947eb47c-7115-444a-be5a-6c689d183687/files?fromPage=ReleaseDownloads
- ASHE table 6, 2025 provisional: https://www.ons.gov.uk/file?uri=/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/agegroupashetable6/2025provisional/ashetable62025provisional.zip
- KAB9: https://www.ons.gov.uk/generator?format=csv&uri=/employmentandlabourmarket/peopleinwork/earningsandworkinghours/timeseries/kab9/lms
- OBR, Economic and fiscal outlook, March 2026: https://assets.publishing.service.gov.uk/media/69a6d7b62e1f4fbda4252208/economic-and-fiscal-outlook-march-2026-web-accessible.pdf

## Too large to commit

| Archive | SHA-256 | Extract | Made by |
|---|---|---|---|
| LEO provider level data 2022-23 (`leo_2022_23.zip`, 787 MB unzipped) | `0863d41832f6eaa666701abaa01d297e6e2017b4725509cdce3c3ad048413c1d` | `data/derived/leo_2022_23.csv.gz` | `scripts/extract_leo.py` |
| LEO national 2022-23 (`leo_national_2022_23.zip`) | `0a19dc86a406aa13b5e1958b50b6e0bc0941ab3d8856b12da636fd20e583dfe6` | `data/derived/leo_paths_2022_23.csv` | `scripts/extract_paths.py` |
| Student loan forecasts 2024-25 (`slf_2024_25.zip`) | `6027f42ae9c6615faeade03a759dcc2fe3abaa87bcc3ff70f28c8d6449fb4cf9` | three CSVs above | copied |
| Graduate labour market statistics (`glms_2024.zip`) | `a9c38d8eaea4a6e33715626ac5f7ef9c6931463e39d9142ee7e56071888b6732` | one CSV above | copied |
| ASHE table 6 (`ashetable62025provisional.zip`) | `23ce201e87e3b780e76fd464ae4fd7cd8e6ca7ba8b679ba10ce77427e8841de9` | table 6.7a above | copied |
| OBR EFO March 2026 (PDF) | `e1d08a66afdda02789a087b79ddbb3398a4e9414254aed8c5de0fc74577f8be6` | `macro_assumptions.csv` | typed |

The extracts' own checksums: `leo_2022_23.csv.gz`
`85130e3e4fc9a392f8a3ece90eaa376cc386d9cdbb950d12d91b038febc78443`,
`leo_paths_2022_23.csv`
`10ea6afa9988c85a1576670dc88217a5ae5a7170e8b86c601b8072d51e06c7bf`.

## Traps, and what was done about them

- **Two LEO releases.** The provider-level file follows graduates to five years
  out; only the national file goes to ten. Subject paths come from the national
  file, university figures from the provider file. The subject names match
  exactly between them.
- **Suppressed and missing values.** The DfE marks small or unreliable values
  "c", "low", "x" or "z". They load as missing and nothing fills them in.
- **Percentiles.** The DfE's published ranges use the type 1 percentile. The
  interpolated default in most software gives different ranges; see the README.
- **Real terms.** The DfE's "real terms" are 2024-25 prices. The model starts
  from the DfE's own ratio of real to nominal balance at the start of
  repayment, 47,900 to 40,700, rather than an assumed inflation path.
- **The OBR's spreadsheet.** A script asking for the OBR's detailed forecast
  tables got a web page back instead of the spreadsheet, so the five years of
  RPI and earnings growth used were typed from the published PDF. Each row of
  `macro_assumptions.csv` says where its numbers come from.

## Licences

DfE and ONS data: Open Government Licence v3.0. OBR material: Open Government
Licence v3.0.
