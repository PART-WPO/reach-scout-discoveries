# Monthly Crossref / DataCite — Scout-only research inbox

**Important: This is NOT a Discovery Hub import feed.** Monthly API outputs must be investigated by REACH Scout *before* any review card is created for a human reviewer.

The primary monthly process now runs **directly in GitHub Actions**, reading every award shard from the public SPARK index, querying DataCite and Crossref, and publishing immutable 24-column CSVs into `api-discoveries/batches/`. It generates and validates `api-discoveries/manifest.json` in the same workflow run. The original Google Sheets/Apps Script approach is retained only as an optional fallback until the new run is verified. These raw records have `Source Run ID: REACH-MONTHLY-API-YYYY-MM`, `Intake origin: Monthly API`, and `Existing REACH Match: Unchecked`; they are **research leads**, not verified candidates.

## Required path to human review

1. Scout reads the entire monthly manifest and all untriaged rows, keeping a persistent per-DOI/URL/award monthly-triage ledger.
2. Scout compares each candidate against **all** current REACH public index/detail shards, previously published Scout discoveries and known human decisions; identifies matching versions and verified existing record IDs when available.
3. Scout examines public award/funder metadata and follows connected articles, datasets, code, reports, and other related output evidence.
4. Scout records a concrete classification, checked evidence, relevant REACH match/absence, linked-output research, remaining questions and confidence. Outputs not fully checked stay in Scout's research queue.
5. Exact existing REACH duplicates without actionable metadata updates are recorded in Scout's ledger/report and **suppressed** from the Hub. Eligible new, investigated possible duplicates, materially investigated holds, additional linked outputs and verified existing-REACH metadata-update proposals are published as new immutable `scout-discoveries/batches/` CSVs for human review.
6. Every original monthly output published for human review uses the same 24 columns but MUST contain separate `Scout Discovery Rationale` lines:
   - `Intake origin: Monthly API`
   - `Monthly intake: YYYY-MM`
   - `Scout verification: Completed`
   - `Scout classification: A NEW CANDIDATE` (or B POSSIBLE DUPLICATE, C NEEDS INVESTIGATION or REACH METADATA UPDATE).
   - `Finding:` with comparison and evidence, meaningful relationship exploration, and the human review question.
   The `Existing REACH Match` field MUST describe a completed comparison; never leave `Unchecked`, `Pending`, or `Unknown`. Source Run ID identifies the *Scout research mission*, not the monthly raw ingestion run.

## Review boundary

The Discovery Hub's **only** automatic feed is `scout-discoveries/manifest.json`, and its parser separately rejects unverified monthly-origin CSVs, including manual uploads. Reviewer filters use the preserved monthly-origin marker to show `Monthly API · Scout checked` alongside historically discovered items.

No GitHub publication approves an output, edits Smartsheet, or publishes to public REACH. Preserve the original source API/provenance and all prior human decisions. Never include private information, email addresses, tokens, source-system row IDs or review logs in public batches.

Monthly inbox: https://raw.githubusercontent.com/PART-WPO/reach-scout-discoveries/main/api-discoveries/manifest.json

Human-review feed: https://raw.githubusercontent.com/PART-WPO/reach-scout-discoveries/main/scout-discoveries/manifest.json

## GitHub Actions API harvest — installed October 28, 2026

- **Workflow:** [REACH API harvest - DataCite and Crossref](https://github.com/PART-WPO/reach-scout-discoveries/actions/workflows/reach-api-harvest.yml).
- **Scheduled:** 12:17 UTC on the **first day of each month**. On November 1, 2026 this is 7:17 AM Eastern Standard Time; it searches **October 1–31, 2026 inclusive**. The month is calculated as the previous full UTC calendar month (not the last 30 rolling days). GitHub schedules may be delayed.
- **Search scope:** all six SPARK award shards (990 award-to-project records, 764 unique identifiers as of 2026-10-28), including standard NOAA OAR and nonstandard public project IDs. Verify source shard SHA-256 and deduplicate award identifiers. Crossref uses its documented `award.number` filter; DataCite uses exact `fundingReferences.awardNumber` search. **Only exact award numbers present in API funding metadata qualify** as matches.
- **Monthly modes:** both DataCite (datasets, software, articles and other deposited works) and Crossref (scholarly publications and other Crossref types). Records are deduplicated by DOI across APIs/awards; preserve all matching awards/programs. Clear, record-specific publication dates are retained. When DataCite reports an October DOI registration but no month-specific publication date, it is explicitly flagged `registration_only_publication_unverified`, with Pub Date blank, for Scout verification. A dated publication demonstrably outside the month is not labeled new for the month.
- **Historical DataCite test:** Run workflow manually with `mode=historical_datacite` or use the one-time 2026-10-28 pilot trigger. Search all SPARK award IDs across all years; outputs go to `api-discoveries/historical/batches/*.csv` with independent `api-discoveries/historical/manifest.json`, **not** the monthly feed and not directly to the Hub.
- **Robustness:** eight award shards per API; retry HTTP 429/5xx with backoff; paginate; retain job artifacts for 14 days; stop publication if any shard fails, any award is skipped, or SPARK snapshots differ. Publication and run summaries are append-only; reruns may not rewrite immutable batch content.
- **Run evidence:** see `api-discoveries/runs/monthly-YYYY-MM.json` or historical run summary for complete award counts and output counts. To rerun a month, use Actions → Run workflow → `monthly` with override `YYYY-MM`; a rerun with different output must be handled explicitly as a new correction batch, not silently overwrite a prior batch.
- **Scout gate:** only `scout-discoveries/manifest.json` is imported into the Discovery Hub. Scout reads monthly and historical raw API manifests, independently investigates REACH novelty, award attribution, linked research and missing metadata, and publishes only review-ready checked candidates. Human approval remains unchanged.

### Excel comparison workbook (starting with November 1, 2026)

For the first months of the GitHub transition, the same completed monthly Action automatically creates a **read-only Excel comparison report** at [api-discoveries/reports/](reports/README.md), named `REACH_API_Comparison_YYYY-MM.xlsx`. For the November 1 run, the month is `2026-10`, covering October 1–31 inclusive. The file is both committed as a durable public snapshot and uploaded to the run's downloadable `reach-monthly-api-excel-comparison` artifact (90-day retention).

The seven-sheet workbook includes a five-column **Crossref Legacy View** matching the old Google Apps Script headers, separate detailed Crossref/DataCite results, DOI-deduplicated combined results, complete per-award counts, a summary and comparison notes. It uses the same validated API shard results as the Scout research intake, but **is never imported into the Discovery Hub**.

### Google Sheets transition

The original monthly Google Apps Script and its spreadsheet tabs are **not used by this GitHub Actions pipeline**. Once the new GitHub pipeline has been validated, disable any pre-existing Apps Script scheduled triggers for `monthlyPublicationsTrigger`, `getLastMonthPublications`, `monthlyAwardOutputsTrigger` and continuation functions that would otherwise re-run overlapping API searches. The GitHub connection cannot change those Apps Script triggers itself. Do not delete historical spreadsheet reports.

### Limitations

Funding metadata may omit the award number or contain unindexed textual acknowledgments. Those outputs cannot be discovered by exact API award searches alone and should be explored via Scout's normal research methods. Crossref / DataCite can deposit metadata late or change historical publication records; the monthly `published` date window does not guarantee detection of late deposits. A periodic backfill/updated-record sweep would improve recall after the initial scheduled migration.
