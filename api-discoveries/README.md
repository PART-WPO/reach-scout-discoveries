# Monthly Crossref / DataCite — Scout-only research inbox

**Important: This is NOT a Discovery Hub import feed.** Monthly API outputs must be investigated by REACH Scout *before* any review card is created for a human reviewer.

The completed monthly Apps Script harvest publishes public, immutable 24-column CSVs to `api-discoveries/batches/`. GitHub Actions validates them and updates `api-discoveries/manifest.json`. These raw records have `Source Run ID: REACH-MONTHLY-API-YYYY-MM`, `Intake origin: Monthly API`, and `Existing REACH Match: Unchecked`; they are **research leads**, not verified candidates.

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
