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
- **Scheduled:** 12:01 AM America/New_York on the **first day of each month**, adjusting automatically for standard/daylight saving time; the harvest searches the **previous full UTC calendar month** (not the last 30 rolling days). GitHub schedules may be delayed.
- **Search scope (mandatory primary-only, corrected November 1):** read all six SPARK award lookup shards but search **only** entries with `Match Basis=primary_noaa_award` or `primary_unparsed_identifier`, which correspond to SPARK's **Award Number(s)** column. **Never search** `related_noaa_award` or `related_unparsed_identifier`, which originate in **Related Award Number(s)**. These related identifiers are context for later evidence checks, not search seeds or proof of WPO funding. Reject unknown match-basis values; verify source shard SHA-256 and deduplicate primary award identifiers. Crossref uses its `award.number` filter; DataCite uses exact `fundingReferences.awardNumber` search. A candidate still requires independently verified same-project WPO funding and REACH duplicate checks before human review.
- **Monthly modes:** both DataCite (datasets, software, articles and other deposited works) and Crossref (scholarly publications and other Crossref types). Records are deduplicated by DOI across APIs/awards; preserve all matching awards/programs. Clear, record-specific publication dates are retained. When DataCite reports an October DOI registration but no month-specific publication date, it is explicitly flagged `registration_only_publication_unverified`, with Pub Date blank, for Scout verification. A dated publication demonstrably outside the month is not labeled new for the month.
- **Historical DataCite test:** Run workflow manually with `mode=historical_datacite` or use the one-time 2026-10-28 pilot trigger. Search all SPARK award IDs across all years; outputs go to `api-discoveries/historical/batches/*.csv` with independent `api-discoveries/historical/manifest.json`, **not** the monthly feed and not directly to the Hub.
- **Robustness:** eight award shards per API; retry HTTP 429/5xx with backoff; paginate; retain job artifacts for 14 days; stop publication if any shard fails, any award is skipped, or SPARK snapshots differ. Publication and run summaries are append-only; reruns may not rewrite immutable batch content.
- **Run evidence:** see `api-discoveries/runs/monthly-YYYY-MM.json` or historical run summary for complete award counts and output counts. To rerun a month, use Actions → Run workflow → `monthly` with override `YYYY-MM`; a rerun with different output must be handled explicitly as a new correction batch, not silently overwrite a prior batch.
- **Scout gate:** only `scout-discoveries/manifest.json` is imported into the Discovery Hub. Scout reads monthly and historical raw API manifests, independently investigates REACH novelty, award attribution, linked research and missing metadata, and publishes only review-ready checked candidates. Human approval remains unchanged.

### Primary-award scope correction — November 1, 2026

The initial October 2026 production harvest incorrectly treated SPARK `Related Award Number(s)` as query seeds. The original 26-DOI batch `2026-11-01-monthly-api-2026-10-part001` remains immutable for provenance, but is excluded from Scout's **active** monthly manifest under `api-discoveries/supersessions.json`. The corrected run creates `2026-11-01-monthly-api-2026-10-primary-only-part001` and `runs/monthly-2026-10-primary-only.json`; the comparison Excel workbook is refreshed from its corrected shards.

All workflows consuming `harvest.py` now receive primary-only candidate award IDs; corrected batch manifests are the only eligible monthly intake. The historical October 28 batch is also immutable and was already researched: see `scout-operations/reports/primary-award-scope-audit-2026-11-01.json` for historical award-scope follow-ups. Its 64 affected DOI records need per-output attribution verification, not automatic deletion or changes to human decisions. Scout's scheduled tasks explicitly apply the same primary-only rule to independent discovery and Hub staging. Other tools outside this repository (e.g., an optional Google Apps Script fallback) must be separately audited before claiming they comply.

### Excel comparison workbook (starting with November 1, 2026)

For the first months of the GitHub transition, the same completed monthly Action automatically creates a **read-only Excel comparison report** at [api-discoveries/reports/](reports/README.md), named `REACH_API_Comparison_YYYY-MM.xlsx`. For the November 1 run, the month is `2026-10`, covering October 1–31 inclusive. The file is both committed as a durable public snapshot and uploaded to the run's downloadable `reach-monthly-api-excel-comparison` artifact (90-day retention).

The seven-sheet workbook includes a five-column **Crossref Legacy View** matching the old Google Apps Script headers, separate detailed Crossref/DataCite results, DOI-deduplicated combined results, complete per-award counts, a summary and comparison notes. It uses the same validated API shard results as the Scout research intake, but **is never imported into the Discovery Hub**.

### Google Sheets transition

The original monthly Google Apps Script and its spreadsheet tabs are **not used by this GitHub Actions pipeline**. Once the new GitHub pipeline has been validated, disable any pre-existing Apps Script scheduled triggers for `monthlyPublicationsTrigger`, `getLastMonthPublications`, `monthlyAwardOutputsTrigger` and continuation functions that would otherwise re-run overlapping API searches. The GitHub connection cannot change those Apps Script triggers itself. Do not delete historical spreadsheet reports.

### Limitations

Funding metadata may omit the award number or contain unindexed textual acknowledgments. Those outputs cannot be discovered by exact API award searches alone and should be explored via Scout's normal research methods. Crossref / DataCite can deposit metadata late or change historical publication records; the monthly `published` date window does not guarantee detection of late deposits. A periodic backfill/updated-record sweep would improve recall after the initial scheduled migration.

### Follow-up-first monthly research priority (October 29, 2026)

Every monthly DataCite/Crossref record is researched individually. After the initial pass, unresolved cases and related-output evidence gaps stay ahead of older-award discovery. Scout performs a bounded additional round with genuinely different sources, documents any early-retry exception, and either closes the case with evidence or prepares a truthful human Investigate request. A case lacking essential metadata must never be represented as imported to Discovery Hub unless the Hub actually accepts it. See [the API follow-up priority policy](../scout-operations/api-followup-priority-policy.md).

## DataCite `created` as completed REACH Pub Date — executive policy (2026-10-30)

For each DataCite DOI with a valid full `created` timestamp, **use its YYYY-MM-DD day as the complete REACH Pub Date**. The user explicitly accepts this as sufficiently accurate for cataloging, with the ordinary option for a reviewer to edit it when preparing addition. No separate publication-day verification, acknowledgment, or *Human metadata needed* finding is required **solely** for that date. Preserve source provenance and any alternative date evidence for reference, but do not turn alternate dates into date-quality blockers. A source missing `created` (or a URL-only output without DataCite) can still have a real date gap. Newly harvested monthly DataCite rows have Pub Date filled from created **after** the existing monthly inclusion-window checks; historical immutable batches remain unchanged and are enriched from the separate date-audit snapshot. Identity, funding, version, eligibility and other missing metadata still require independent checks and human approval before REACH insertion. This supersedes older guidance that described an uncorroborated DataCite-created date as an unresolved REACH Pub Date.

## Crossref Pub Date preference — print-first and month-to-day normalization (2026-10-30)

**Authoritative WPO policy:** For Crossref DOI records, use `published-print` when it contains year/month or an exact YYYY-MM-DD, otherwise `published-online`, then `published` or `issued`. Posted preprints use `posted` first. `date-parts=[[YYYY,MM]]` is considered **complete for REACH** and becomes `YYYY-MM-01` with metadata source and `month_first` provenance retained. Year-only dates do not get an arbitrary January 1. **Never use Crossref `created` for REACH Pub Date**; it is DOI registration metadata. The separate DataCite office policy (DataCite `created` accepted as REACH Pub Date) remains unchanged.

The month-scoped API search still uses **actual publication date month** for harvest inclusion and only derives the REACH date **after** the inclusion check. For online-only publications, online date is initially used; once Crossref adds a print date, subsequent checkpoint refreshes can produce a print-preferred date suggestion. Existing immutable API batches, reviewer decisions, human-edited Pub Dates and public REACH entries are not overwritten. The read-only Crossref audit at `scout-operations/reports/crossref-metadata-checkpoint/latest.json` tracks these preferences and date-source differences. This supersedes any earlier Crossref-created default instructions.
