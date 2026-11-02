# NOAA Institutional Repository (IR) verification for NEW Scout outputs

**Introduced November 2, 2026.** NOAA Central Library's official public [JSON API](https://github.com/NOAA-Central-Library-NCL/noaa_ir_api) serves the *entire* NOAA Institutional Repository. A standalone GitHub Action `.github/workflows/noaa-ir-dataset-index.yml` indexes each unique DOI to the canonical `https://repository.library.noaa.gov/view/noaa/{PID}` item URL. The action verifies every page's count and position, stores only compact DOI-to-landing-page mappings in 16 SHA-256-verified shards, and publishes `scout-operations/noaa-ir/manifest.json` only after all source pages succeed. The workflow refreshes on weekdays before the morning briefing and is manually dispatchable; it never queries or changes Smartsheet/REACH.

## New-candidate intake

The canonical `scout-discoveries/tools/prepare_batch.py` automatically reads a complete, verified NOAA IR index. It checks the exact normalized DOI **only after** normal public REACH/Scout duplicate screening and a defensible **new-output** classification. It fills existing canonical 24-column fields; no schema migration:
- **Verified unique DOI hit:** `IR?=TRUE` and `IR Repository URL=https://repository.library.noaa.gov/view/noaa/NNNN`, with evidence in `Scout Discovery Rationale`. An official IR record URL is not a publisher URL, PDF download URL or search-results URL.
- **Missing DOI, no confirmed match, index missing/incomplete, or multiple IR records for one DOI:** never assert TRUE, never set FALSE. Leave `IR?` and `IR Repository URL` blank; record appropriate check limits/reviewer guidance when a new candidate is being drafted.
- **Existing REACH output, previously reviewed candidate, metadata correction, possible/known duplicate:** no new enrichment. Preserve all existing human decisions and immutable prior batches. A `NEEDS INVESTIGATION` candidate qualifies only when its full REACH comparison explicitly established no match and it is an original potential **new** output.
- **Conflicting prefilled IR link or prior FALSE:** fail closed rather than overwriting metadata. Never fill `IR Pub Date` or `IR Status` from unrelated fields or confuse NOAA IR holdings with release/compliance status.

An exact DOI hit in the official catalog confirms *repository membership only*, not award attribution, embargo status, public PDF availability, compliance, project eligibility or readiness for a human approval. NOAA IR may not have ingested recently published output yet; absence from an index snapshot is not evidence of noncompliance.

## Scout mission responsibilities

At each new eligible output intake (monthly originals, historical Crossref/DataCite originals, DOI-seeded expansions, independent discoveries), Scout should inspect `scout-operations/noaa-ir/manifest.json` and verified DOI mapping, use the populated IR fields from the canonical new-draft generator, and include the exact official URL in reviewer context when found. If the API index is stale/unavailable, report `NOAA_IR_UNVERIFIED` in mission notes, not false. Scout should not use Google search snippets or title similarities to set TRUE. Where a credible same-title different-DOI or DOI-less IR record is found, tell the reviewer what requires verification but leave the field blank.

**Reporting:** count new candidates screened, confirmed TRUE+link, missing or ambiguous matches, and unavailable/stale indexing separately. Do not conflate a returned public Scout CSV with actual Hub import. This feature is not a retrospective audit or metadata-correction sweep of existing REACH outputs.
