# Monthly Harvest Reports

**DataCite + Crossref monthly comparison workbooks**, organized by the month the research outputs were published.

## Reports

| Reporting month | Current report | Notes |
| --- | --- | --- |
| October 2026 | [October_2026.xlsx](October_2026.xlsx) | Corrected primary-WPO-award-only harvest, generated November 1, 2026; **13 DOIs** identified for Scout research |

Each report covers the **previous complete calendar month**, not the date when GitHub Actions generated it. For example, the harvest run on November 1 produces **October_2026.xlsx**. The scheduled workflow runs on the first day of each month at **12:01 AM Eastern**, subject to GitHub Actions scheduling delays.

### File naming

- **Standard report:** `Month_YYYY.xlsx`, such as `November_2026.xlsx`.
- **A later separately published correction:** `Month_YYYY_Correction_Reason.xlsx` when appropriate; the original cannot be silently overwritten.
- **Historical superseded versions:** kept under [archive/](archive/) for audit only.

### How to interpret these

These workbooks compare monthly DataCite and Crossref award-based API findings and provide the source details, DOI-deduplicated results, and which **primary SPARK Award Number(s)** were searched. They are **unreviewed research input**, not confirmed new REACH outputs and **not** a feed to the Discovery Hub. Scout must independently review funding, duplicates and connected research, and a person must approve any new public output.

The **October 2026** corrected report includes only primary awards from SPARK's `Award Number(s)` column. The [superseded original](archive/October_2026_Superseded_Related_Awards.xlsx) used related award numbers and must **not** be used to assign WPO funding.

Source and automation: [GitHub Actions monthly harvest](../.github/workflows/reach-api-harvest.yml) · [Monthly Scout research inbox](../api-discoveries/manifest.json) · [Report methodology](../api-discoveries/reports/README.md).

Excel files are committed permanently to GitHub and may also be downloaded from the corresponding GitHub Actions run under Artifacts (90-day retention).
