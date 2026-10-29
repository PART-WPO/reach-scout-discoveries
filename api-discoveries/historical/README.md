# Historical DataCite SPARK backfill — Scout-only intake

**This folder is NOT a Discovery Hub feed.** The 2026-10-28 historical pilot queries public DataCite metadata for every usable, distinct award identifier in the full SPARK GitHub `agent-data/awards/` shards, across all years and WPO programs.

The workflow `REACH API harvest - DataCite and Crossref` uses `historical_datacite` mode, eight parallel source shards, exact `fundingReferences.awardNumber` verification, backoff/pagination and complete coverage checks. One malformed SPARK identifier consisting only of a quotation mark was found in the source (not a real award); it is excluded, without excluding nonstandard but meaningful OWAQ/WPO IDs.

When all searches complete successfully, it writes immutable 24-column CSVs to `batches/`, a checksummed `manifest.json`, and a run summary under `../runs/`. Any failed award prevents publication; job artifacts retain errors and partial results for repair. Never treat a failed run as an empty result.

Scout reads this historical manifest and uses a separate `scout-operations/historical-triage.json` research checkpoint. For each DOI it compares the complete current public REACH index/details and reviewer feedback, confirms funding and explores related outputs, then only publishes **individually investigated** candidates to `scout-discoveries/batches/`. Confirmed exact duplicates are suppressed unless an actionable metadata correction is evidenced. All final approvals and Smartsheet insertions remain human controlled.

The parallel monthly DataCite/Crossref pull remains separate: it runs on the first day of each month for the previous entire calendar month, beginning November 1, 2026 (October 1–31).

## Excel comparison workbook

For a read-only, side-by-side comparison of the original historical DataCite API findings and Scout's current research assessment, see the [Historical DataCite and Scout Excel comparison](../reports/REACH_DataCite_Historical_2026-10-28_Scout_Comparison.xlsx). The daily [comparison workflow](https://github.com/PART-WPO/reach-scout-discoveries/actions/workflows/historical-datacite-report.yml) refreshes the report as Scout's investigation progresses, without re-querying DataCite or changing the original 188 DOI records. The workbook is never used for Discovery Hub intake or human-review decisions.
