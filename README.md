# REACH Scout discoveries — unreviewed public staging

This separate public repository is a staging feed for **unreviewed** REACH Scout findings. It is **not** the live REACH catalog. Scout commits validated, append-only daily CSV batches directly to `main`; Discovery Hub reads the manifest and handles **all decisions about whether individual research outputs should be added to REACH**.

## Daily workflow

1. ChatGPT Scout performs research on public sources and checks funding attribution against the complete public REACH catalog.
2. Scout saves the full evidence report, exactly 24-column Discovery Hub import CSV, and investigation/coverage ledger to ChatGPT Library `/REACH Scout`.
3. Scout checks that the CSV contains **only public evidence and metadata**; `Candidate ID` and `Principal Investigator Email(s)` must remain blank. It excludes private Smartsheet row IDs, credentials, personal details and reviewer decisions.
4. **New procedure (October 30, 2026):** construct the unique 24-column CSV from fixed provenance fields using `scout-discoveries/tools/prepare_batch.py`; independently run `--check` before submission when local execution is available. Do not guess labels such as `Scout seed DOI:`; use the exact canonical template.
5. Scout commits the new **unpublished draft** to `scout-discoveries/inbox/YYYY-MM-DD-unique-run.csv` on `main`, **not directly into batches**. The inbox is a non-publication staging location inside this public repository. Retain the full report and draft in the REACH Scout Library first.
6. GitHub Actions validates the draft, including evidence, 24 columns, public-only fields, classification, discovery route and exact seed DOI. **Only on success**, the workflow copies it into the immutable `scout-discoveries/batches/` directory, runs `build_manifest.py` and rebuilds `scout-operations/discovery-origin-rollup.json` from every SHA-verified batch. Invalid drafts cannot poison the published manifest.
7. The Action commits the new batch, generated manifest and reconciled attribution rollup together. Scout re-reads exact CSV SHA-256, manifest counts, source run ID and origin totals. Inbox commits alone are **NOT** publication. Previously published batches stay immutable; only an explicitly authorized repair permits a documented exception.
8. Discovery Hub uses **Sync from Scout** to retrieve only batches in the validated manifest and add them to its unreviewed queue. Private Hub import cannot be inferred from a GitHub commit or manifest entry.
9. A person reviews the research evidence and controls any final addition to Smartsheet/REACH. Publishing here **never** constitutes approval for insertion.

## Files

- `scout-discoveries/inbox/*.csv` — new, unpublished candidate drafts; invalid drafts cannot change the feed
- `scout-discoveries/batches/*.csv` — GitHub Actions-promoted immutable validated finding batches with the exact 24-column import schema
- `scout-discoveries/manifest.json` — manifest of verified batches, checksums, counts and run IDs
- `scout-discoveries/tools/prepare_batch.py` — canonical provenance template and before-submission CSV preflight
- `scout-discoveries/tools/promote_inbox.py` — validate inbox drafts before promoting any file to published batches
- `scout-discoveries/tools/build_manifest.py` — strict schema validation, content checks and exclusive manifest generator
- `scout-discoveries/tools/rebuild_discovery_rollup.py` — verified attribution and discovery-origin metrics from manifest-listed CSV bytes
- `scout-operations/discovery-origin-rollup.json` — automatically reconciled *staged candidate* counts, not verified human approvals
- `.github/workflows/build-scout-discovery-manifest.yml` — runs checks and refreshes manifest on `main` pushes

Public manifest URL:

https://raw.githubusercontent.com/PART-WPO/reach-scout-discoveries/main/scout-discoveries/manifest.json

## Boundaries

ChatGPT has write access to **this repository only**. The production `PART-WPO/reach-dashboard` and `PART-WPO/SPARK` repositories are read-only public sources. No output is approved, inserted into Smartsheet, or added to the public REACH dashboard until the separate Discovery Hub human review and insertion steps.

This repository is **public**. Do not publish restricted NOAA information, private investigator contact details, Smartsheet native identifiers or authorization details, API secrets, or human-review records. If a batch does not pass the public-only screening or data checks, do not publish it. 

## Monthly Crossref / DataCite — Scout-gated research inbox

The raw monthly API output batches in `api-discoveries/` are **inputs to Scout only**, never direct additions to the Discovery Hub. Scout checks each output against the full REACH catalog, prior findings and supporting public sources, then follows related outputs. Confirmed existing REACH duplicates without an actionable correction remain documented in Scout's research ledger and are not forwarded for unnecessary human review.

Only *Scout-checked* monthly findings that merit human review (new candidates, investigated possible duplicates or holds, or verified existing-REACH metadata updates) are published by Scout into the normal `scout-discoveries/batches/` manifest with `Intake origin: Monthly API`, `Monthly intake: YYYY-MM`, and `Scout verification: Completed` evidence. The Hub syncs **only `scout-discoveries/manifest.json`**; its Source filter distinguishes Scout-checked monthly items from historical Scout research. Prior human decisions and Smartsheet controls are preserved.

See [Scout-only monthly intake protocol](api-discoveries/README.md) for the checked-publication schema and strict review gate.


## Monthly Excel comparison reports

Starting with the November 1, 2026 run for the October 2026 publication window, the DataCite/Crossref GitHub Action saves a read-only, seven-sheet Excel workbook in [api-discoveries/reports/](api-discoveries/reports/README.md), plus a downloadable 90-day GitHub Actions artifact. It includes a five-column Crossref legacy view to compare with existing Google Sheets results. The workbook is for verification only and does not feed the Discovery Hub.
