# REACH Scout — Crossref Publication Metadata Audit

Read-only Crossref DOI-level research metadata. The source snapshots are verified Crossref /works/{DOI} responses previously fetched by Scout, recalculated under the WPO print-first rule. The scheduled job will also refresh Crossref API metadata for newer print dates.

## WPO Pub Date rule

Use `published-print` first (year-month -> first of month), then `published-online` when print is unavailable, followed by `published`, `issued`, or `posted` as applicable. For preprints, `posted` takes precedence. A month-only date `2020-12` produces REACH Pub Date **2020-12-01**, with an explicit `month` precision and normalization flag. Crossref `created` is kept as DOI registration metadata but is **never used for Pub Date**. A year-only value does not yield an invented Jan 1.

## Source-verified coverage

| Metric | Number |
|---|---:|
| Crossref DOIs examined | 36 |
| Pub Date satisfied by preferred print/online/publication field | 36 |
| Chosen full-day publication dates | 17 |
| Chosen YYYY-MM dates represented with day 01 | 19 |
| Selected from `published-print` | 30 |
| Selected from `published-online` | 5 |
| Previously blank Scout Pub Date now satisfiable | 7 |
| Of these, month-to-day-01 selections | 6 |
| Existing Scout dates differing from print-first selection | 17 |
| Previously missing abstract now available through Crossref | 1 |

## DOI-by-DOI selection

| DOI | Existing Scout Pub Date | Selected REACH Pub Date | Crossref field | Normalized day? |
|---|---|---|---|---|
| 10.1029/2024gl109890 | 2024-08-15 | 2024-08-28 | Crossref published-print | No |
| 10.1029/2024ms004319 | 2024-10-13 | 2024-10-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1029/2024wr037507 | 2024-08-29 | 2024-09-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1029/2025ms005126 | 2025-11-10 | 2025-11-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1038/s43017-020-0057-7 | 2020-06-02 | 2020-06-02 | Crossref published-online | No |
| 10.1061/(asce)st.1943-541x.0003275 | 2022-02-17 | 2022-05-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1080/02626667.2018.1430898 | 2018-02-15 | 2018-02-17 | Crossref published-print | No |
| 10.1088/1748-9326/ab98b4 | 2020-08-05 | 2020-08-01 | Crossref published-print | No |
| 10.1109/tgrs.2020.2984458 | — | 2020-12-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1175/aies-d-23-0064.1 | 2024-01-30 | 2024-01-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1175/bams-d-15-00283.1 | 2016-07-19 | 2017-02-01 | Crossref published-print | No |
| 10.1175/bams-d-19-0245.1 | — | 2020-10-01 | Crossref published-print | No |
| 10.1175/bams-d-20-0186.1 | 2021-09-01 | 2021-09-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1175/bams-d-23-0036.1 | 2024-08-19 | 2024-08-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1175/bams-d-25-0032.1 | 2026-10-14 | 2026-10-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1175/jamc-d-18-0094.1 | — | 2019-02-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1175/jas-d-17-0385.1 | 2018-09-01 | 2018-09-01 | Crossref published-print | No |
| 10.1175/jas-d-20-0117.1 | — | 2021-05-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1175/jcli-d-14-00448.1 | 2015-11-15 | 2015-11-15 | Crossref published-print | No |
| 10.1175/jcli-d-19-0908.1 | 2021-01-06 | 2021-02-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1175/jtech-d-18-0224.1 | — | 2019-11-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1175/mwr-d-18-0246.1 | — | 2019-06-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1175/mwr-d-19-0146.1 | 2020-01-01 | 2020-01-01 | Crossref published-print | No |
| 10.1175/mwr-d-22-0051.1 | — | 2023-06-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1175/mwr-d-23-0144.1 | 2024-07-11 | 2024-07-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1175/waf-d-17-0120.1 | 2018-06-01 | 2018-06-01 | Crossref published-print | No |
| 10.1175/waf-d-19-0105.1 | 2020-01-01 | 2020-02-01 | Crossref published-print | No |
| 10.1175/waf-d-19-0216.1 | 2020-08-01 | 2020-08-01 | Crossref published-print | No |
| 10.1175/waf-d-22-0178.1 | 2023-08-02 | 2023-08-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1175/waf-d-24-0249.1 | 2025-10-10 | 2025-11-01 | Crossref published-print (month -> day 01) | Yes |
| 10.1175/wcas-d-23-0046.1 | 2023-11-10 | 2023-10-01 | Crossref published-print (month -> day 01) | Yes |
| 10.15191/nwajom.2023.1107 | 2023-09-07 | 2023-09-07 | Crossref published-online | No |
| 10.15191/nwajom.2023.1109 | 2023-12-19 | 2023-12-19 | Crossref published-online | No |
| 10.3390/atmos12101286 | 2021-10-02 | 2021-10-02 | Crossref published-online | No |
| 10.36227/techrxiv.175035136.63535291/v2 | 2025-12-09 | 2025-12-09 | Crossref posted | No |
| 10.5194/gmd-18-7969-2025 | 2025-10-28 | 2025-10-28 | Crossref published-online | No |

## Interpretation

Dates that differ from earlier Scout values are **informational** (e.g., an existing online date versus the selected print date), not automatic metadata-quality errors. No existing human-reviewed date, previous Scout source CSV, Smartsheet row, or public REACH entry has been edited.

Crossref 'created' is not used as a publication-date fallback. All DOI records retain their original `published-print`, `published-online`, other date fields, precision and their provenance in `latest.json`. A new print date may change a suggestion on a future refresh, but not override a human decision.

Source: https://api.crossref.org/works/{DOI}. Source snapshot recalculation does not claim a new live API fetch.
