# Monthly DataCite / Crossref — Excel comparison reports

Beginning with the first scheduled **November 1, 2026** harvest (October 1–31, 2026 output window), every completed monthly API run also publishes an Excel workbook here:

`REACH_API_Comparison_YYYY-MM.xlsx` — for example `REACH_API_Comparison_2026-10.xlsx`.

The workbook is a **public, read-only comparison aid**, **not** a second Scout/Discovery Hub ingestion path. No Google Spreadsheet, Drive integration, human review notes, personal emails, Smartsheet identifiers, or credentials are required.

## Where to download

1. **Permanent GitHub file:** browse this `api-discoveries/reports/` folder once the first completed monthly run publishes its workbook, select the matching `.xlsx`, then **Download raw file**.
2. **GitHub Actions artifact:** open [REACH API harvest – DataCite and Crossref](https://github.com/PART-WPO/reach-scout-discoveries/actions/workflows/reach-api-harvest.yml), select the successful monthly workflow run, and download the artifact named `reach-monthly-api-excel-comparison` under **Artifacts**. Its retention is configured for 90 days; the committed copy in this folder is retained normally.
3. **For manual reruns:** choose Actions → Run workflow → `monthly` and optionally specify a `YYYY-MM` period. Identical reruns preserve the existing workbook. If API metadata changed, an immutable-file conflict is raised instead of silently altering the original evidence; publish a separately named correction batch/workbook after review.

## Workbook sheets

| Sheet | Purpose |
|---|---|
| Summary | Month, inclusive date range, award coverage, API match counts, overlapping DOIs, unverified dates and SPARK source checksum |
| Combined Results | One row per distinct DOI across DataCite, Crossref and award matches; retains all matching award identifiers and source labels |
| Crossref Results | One row per **award + DOI** with publication date, date basis, type, program and source metadata URL |
| DataCite Results | Equivalent **award + DOI** DataCite view, including software and dataset output types |
| Crossref Legacy View | Exactly the original five headers from the Google Apps Script: `Award Number`, `DOI`, `Title`, `Published Date`, `Citation` |
| Awards Checked | All awards searched in SPARK, including those with zero API matches, and per-source counts |
| Read Me | Comparability cautions, research status, date limitations and deduplication instructions |

Rows are filterable, header rows are frozen, column widths are bounded, and text is stored as literal text (never user-provided Excel formulas). A blank publication date remains blank when the API proves only a DOI registration or month-level date.

**Comparison cautions:** The old Google Sheets code might have searched a different division-specific award list and prioritized `published-print` dates, while this GitHub workflow uses **all SPARK awards** and deliberately retains record-specific date-basis uncertainty. Compare DOI+award, then inspect `WPO Program` and `Date Basis` for discrepancies before interpreting count differences. A DOI associated with two awards appears twice in source tabs but once in Combined Results.

The underlying 24-column **Scout-only research inbox** still resides in `api-discoveries/batches/`; the workbook does **not** enter the Discovery Hub and does not affect automated Scout triage.

## Historical DataCite backfill — comparison with Scout

The original **October 28, 2026 historical DataCite** award-number search has its own regularly refreshed Excel comparison workbook:

**[REACH_DataCite_Historical_2026-10-28_Scout_Comparison.xlsx](REACH_DataCite_Historical_2026-10-28_Scout_Comparison.xlsx)**

It has seven sheets: **Summary**, **Historical DataCite Results** (all 188 raw API DOI records), **Scout DOI Comparison** (original DOIs matched to current Scout research), **Related Scout Findings** (separately staged API-seeded expansion candidates), **Awards with API Matches**, **Scout Status Breakdown**, and **Read Me**. The API run searched 761 unique award identifiers, finding 188 unique DOIs and 212 award/DOI matches. Original API evidence is clearly separated from subsequent Scout research; neither API matches nor GitHub staging imply human approval or publication in REACH.

The report is refreshed daily at 14:10 UTC or by manually running [Historical DataCite — Excel comparison with Scout](https://github.com/PART-WPO/reach-scout-discoveries/actions/workflows/historical-datacite-report.yml). The workflow also provides a 90-day Actions artifact named `reach-historical-datacite-scout-comparison`. The GitHub file above is retained normally.

**Read-only and report-only:** This never alters the immutable API batches, Scout's research ledger, Discovery Hub, Smartsheet, or REACH.

## DataCite date evidence audit — historical and future monthly intakes

[GitHub Actions: DataCite date reconciliation](https://github.com/PART-WPO/reach-scout-discoveries/actions/workflows/datacite-date-reconciliation.yml) independently revisits original DataCite DOI records and compares date evidence without altering the immutable 24-column API inputs, the Scout research ledgers, human-review decisions, or public REACH. It runs on changes to the source manifest, weekly and on the first of each month, with manual **Run workflow** support.

The historical workbook is **[REACH_DataCite_Date_Reconciliation_Historical_2026-10-28.xlsx](REACH_DataCite_Date_Reconciliation_Historical_2026-10-28.xlsx)**, covering every original 188 historical DOI records. Each completed monthly intake gets **`REACH_DataCite_Date_Reconciliation_YYYY-MM.xlsx`**. The equivalent machine-readable read-only date snapshots are under [api-discoveries/date-audits/](../date-audits/), with keys `historical-2026-10-28.json` and `monthly-YYYY-MM.json`. The first workbook is available after a successful first workflow run, not merely because this README links to it.

Each workbook contains **Summary**, **Date Reconciliation** (original title, award, parent, output type, typed Issued/Available, full DataCite published/created/registered/updated timestamps, native date evidence and classifications), **Repository Breakdown**, **Needs Reviewer Check**, and **Read Me**. The date categories deliberately separate exact DOI-matched repository publication metadata from typed DataCite dates that still need corroboration and DOI registration/record-creation dates that are **only provisional clues**. A DataCite year is not converted to an invented January 1 date. Access barriers, version ambiguity and conflicting dates are shown, not silently corrected.

**Never use the workbook as a Smartsheet import.** It is a source-first reference for Scout and reviewers. An exact date still requires an eligible, distinct output, the proper parent project and an authorized human approval before publishing.

### REACH Pub Date office default — DataCite `created` (October 30, 2026)

For REACH candidate **preparation**, the reviewer chose the **calendar day of the DataCite `created` timestamp** as the pre-filled Pub Date. This is explicitly a **reviewer-editable default**, not necessarily the first public release date. The historical and monthly date-audit JSON reports now separately expose `default_pub_date` and `default_pub_date_basis` alongside `verified_date`, `issued_dates`, `available_dates`, `created`, `registered`, and `updated`. The Excel date reconciliation includes **Default REACH Pub Date (DataCite created; editable)**. Reviewer corrections, DOI/version checks and eligibility decisions remain independent. Existing original API batches and already-published REACH data are not rewritten.
