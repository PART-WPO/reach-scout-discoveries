# REACH Scout discoveries — unreviewed public staging

This separate public repository is a staging feed for **unreviewed** REACH Scout findings. It is **not** the live REACH catalog. Scout commits validated, append-only daily CSV batches directly to `main`; Discovery Hub reads the manifest and handles **all decisions about whether individual research outputs should be added to REACH**.

## Daily workflow

1. ChatGPT Scout performs research on public sources and checks funding attribution against the complete public REACH catalog.
2. Scout saves the full evidence report, exactly 24-column Discovery Hub import CSV, and investigation/coverage ledger to ChatGPT Library `/REACH Scout`.
3. Scout checks that the CSV contains **only public evidence and metadata**; `Candidate ID` and `Principal Investigator Email(s)` must remain blank. It excludes private Smartsheet row IDs, credentials, personal details and reviewer decisions.
4. When **new findings** exist, Scout creates one **new, uniquely named file** directly on this repository's `main` branch at `scout-discoveries/batches/YYYY-MM-DD-unique-run.csv`. Existing batches are immutable. **No branches or pull requests are needed.**
5. GitHub Actions validates the batches and automatically regenerates `scout-discoveries/manifest.json` with counts and SHA-256 hashes. Scout verifies publication; if the workflow is delayed or fails, the Library CSV is retained and the run reports the error.
6. Discovery Hub uses **Sync from Scout** to retrieve new batches from the public manifest and add them to its existing *unreviewed* queue. Prior reviewer decisions remain untouched.
7. A person reviews the research evidence and controls any final addition to Smartsheet/REACH. Publishing here **never** constitutes approval for insertion.

## Files

- `scout-discoveries/batches/*.csv` — append-only public finding batches with the exact 24-column import schema
- `scout-discoveries/manifest.json` — manifest of verified batches, checksums, counts and run IDs
- `scout-discoveries/tools/build_manifest.py` — strict schema validation, content checks and manifest builder
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

