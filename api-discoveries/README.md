# Monthly Crossref / DataCite discoveries — public unreviewed staging

This is a second intake feed for the same REACH Discovery Hub reviewer queue. It does **not** replace the existing `scout-discoveries/` historical research feed or the live REACH catalog.

The existing Google Apps Script monthly job searches the prior calendar month, writes its three report tabs, and (with the optional companion exporter installed) exports an immutable 24-column Discovery Hub CSV for that month to `api-discoveries/batches/YYYY-MM-DD-monthly-api-YYYY-MM.csv` on `main`. This must happen **only after** the complete monthly job and its continuation runs have finished. No API credentials or private reviewer information may be included.

GitHub Actions validates all CSVs and generates `api-discoveries/manifest.json` with SHA-256 checksums and record counts. The Hub should synchronize **both** the existing Scout manifest and this manifest into its existing queue, preserving stable candidate identity, existing human decisions, and import history.

## Feed and UI semantics

- **Feed:** `https://raw.githubusercontent.com/PART-WPO/reach-scout-discoveries/main/api-discoveries/manifest.json`
- **Source Run ID:** `REACH-MONTHLY-API-YYYY-MM` on every imported record.
- **Rationale marker:** `Intake origin: Monthly API` followed by the discovery month and API provenance.
- **Queue filter:** `Monthly API` vs `Historical Scout`, with optional `All Sources`. Default view should prioritize pending monthly intake; do not discard or demote historical discoveries.
- **Review status:** initially needs investigation until a REACH and Scout queue duplicate check is completed. Matching an award number in API metadata does not prove an output is missing from REACH.
- **Scout order:** check current REACH shards and staged/human-reviewed candidates for direct DOI/URL/title identity first, then check linked versions, related publications, datasets, software, reports and metadata corrections. Return to historical awards when the monthly queue's actionable candidates have been triaged. Do not reset human decisions.
- **Classification:** separate A new, B possible duplicate, C investigation, D known duplicate, and supported REACH metadata-update proposals. Keep public evidence and the original API provenance.
- **Approvals:** remain exclusively with the human reviewer; publication here never inserts into Smartsheet or REACH.

## Safety

The monthly API exporter is idempotent: identical re-runs should not create new batches or overwrite old ones. If a past month's results change, do not mutate its immutable file: use a deliberately named correction/version batch after reviewing existing records. Avoid publishing email fields, credentials, Smartsheet internal IDs, and reviewer decisions. Only HTTPS source evidence may enter this feed.

The initial manifest is intentionally empty: an actual completed monthly report is required before a batch can be published.
