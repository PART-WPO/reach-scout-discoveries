# REACH Scout discoveries — unreviewed public staging

This separate public repository is a staging feed for **unreviewed** REACH Scout findings. It is **not** the live REACH catalog. Scout commits validated, append-only daily CSV batches directly to `main`; Discovery Hub reads the manifest and handles **all decisions about whether individual research outputs should be added to REACH**.

## Daily workflow

1. ChatGPT Scout performs research on public sources and checks funding attribution against the complete public REACH catalog.
2. Scout saves the full evidence report, exactly 24-column Discovery Hub import CSV, and investigation/coverage ledger to ChatGPT Library `/REACH Scout`.
3. Scout checks that the CSV contains **only public evidence and metadata**; `Candidate ID` and `Principal Investigator Email(s)` must remain blank. It excludes private Smartsheet row IDs, credentials, personal details and reviewer decisions.
4. When **new findings** exist, Scout creates one **new, uniquely named file** directly on this repository's `main` branch at `scout-discoveries/batches/YYYY-MM-DD-unique-run.csv`. Existing batches are immutable. **No branches or pull requests are needed.**
5. GitHub Actions validates the batches and automatically regenerates `scout-discoveries/manifest.json` with counts and SHA-256 hashes. Scout verifies publication; if the workflow is delayed or fails, the Library CSV is retained and the run reports the error.
6. Discovery Hub v1.24 uses **Sync from Scout** to retrieve new batches from the public manifest and add them to its existing *unreviewed* queue. Prior reviewer decisions remain untouched.
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

## Monthly Crossref / DataCite API intake (parallel feed)

Monthly API outputs are staged separately at `api-discoveries/batches/*.csv` using the **same** 24-column Discovery Hub schema. An independent GitHub Actions validator publishes `api-discoveries/manifest.json`; this feed has its own batch IDs and provenance. See [monthly intake documentation](api-discoveries/README.md).

**Public monthly manifest:** https://raw.githubusercontent.com/PART-WPO/reach-scout-discoveries/main/api-discoveries/manifest.json

A monthly API match is **not** automatically a new REACH output: it must be deduplicated against complete REACH index shards, existing staged items and human dispositions. Scout checks the monthly intake first, searches associated datasets/software/publications/reports for additional output discoveries, then returns to historical award work. Review remains exclusively human-controlled in the Discovery Hub, and no CSV in either feed is authority to change Smartsheet or publish to REACH.
