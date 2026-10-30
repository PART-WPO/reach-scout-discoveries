# REACH Scout — 2026-10-30 18:29 ET hourly mission

Run: `REACH-SCOUT-2026-10-30-HOURLY-1829ET` · Audit: **PARTIAL** · Primary mode: **Normal historical discovery**.

## Queue reconciliation
Monthly API 0 received / 0 outstanding; historical DataCite **188 of 188** independently dispositioned, 0 unresolved research; ledger categories 37 already in REACH, 6 forwarded, 8 metadata updates forwarded, 109 no action, 28 human metadata intake. The historical coverage is research-complete, **not** human-approved. Attribution ledger has 71 entries, none currently queued. Previous one-time four-DOI recheck is complete and was **not repeated**.

## New substantive expansion: DeepFlood dataset DOI family
Investigated SPARK `spark-000338`, primary award **NA21OAR4590358** (North Carolina A&T, floodwater mapping with optical UAV and SAR). The publisher's 2025 Scientific Data article (DOI `10.1038/s41597-025-04554-3`) directly acknowledges this award and cites **Figshare DOI `10.6084/m9.figshare.26791243`** as its data reference (reference 34). Its DOI resolver points to a `journal_contribution` Figshare path. A distinct 2026 Springer study (DOI `10.1007/s12145-026-02164-0`) names **`10.6084/m9.figshare.28328339`** as the DeepFlood dataset. This is evidence of **two potentially related Figshare identities, not proof of two new REACH outputs**. The later study itself credits NASA/NSF, not WPO; do not attribute that 2026 paper to WPO by association.

Checked all 10 public REACH index shards (1,238 rows) and all 20 manifest-listed Scout batches (66 staged rows): neither Figshare DOI nor a DeepFlood title match found. The earlier 17:32 ET mission checked all 140 REACH detail shards; those were **not** re-read in this run. The invalid unmanifested 13:29 ET CSV separately contains the 2025 DeepFlood *article*, not a verified dataset candidate. Native Figshare and exact DataCite lookups failed through available research interfaces; mark **ACCESS FAILURE**, never 'no metadata.' No DOI-specific `created` timestamp was verified, so no REACH Pub Date has been assigned to either Figshare DOI. Both remain a single **bounded follow-up decision unit** for native DOI metadata, version/identity, public-file scope and exact funding checks; **zero new Hub candidates**.

Sources: https://www.nature.com/articles/s41597-025-04554-3 ; https://link.springer.com/article/10.1007/s12145-026-02164-0 ; https://doi.org/10.6084/m9.figshare.26791243 ; https://doi.org/10.6084/m9.figshare.28328339 ; https://github.com/PART-WPO/SPARK/blob/main/agent-data/details/part-026.csv.

## Feed integrity: confirmed failure and precise reason
The manifest still lists **20 immutable batches / 66 proposals**, while **21** CSV files exist. The unmanifested `scout-discoveries/batches/2026-10-30-hourly-1329ET-independent-flood-mapping-001.csv` contains two article proposals. GitHub Actions run [41100661636](https://github.com/PART-WPO/reach-scout-discoveries/actions/runs/41100661636) failed with exact validator error:

`ValueError: Scout discovery route needs actual public evidence: 2026-10-30-hourly-1329ET-independent-flood-mapping-001.csv:2`

The immutable CSV has `Scout discovery route: Independent discovery` but lacks the validator-required standalone `Scout discovery path evidence: https://...` and `Scout discovery method: ...` lines; it also uses legacy `Scout classification: A NEW CANDIDATE` rather than the clean parser-compatible `Scout classification: NEW CANDIDATE`. The first missing evidence line is the **confirmed immediate failure**; the other gaps are **additional preflight concerns**, not independently observed subsequent workflow failures. **Do not modify or delete the existing CSV, bypass validation, or edit the manifest manually.** A separately authorized human-controlled repair plan is required. No new batch published; Hub synchronization and private reviewer decisions remain NOT VERIFIED.

## Next research and guardrails
Prioritize monthly API intake when it arrives, then one different-source DOI-native Figshare recovery round and further SPARK award-by-award discovery. Maintain DataCite-created as accepted REACH Pub Date only when the exact DOI timestamp is available; Crossref published-print before online (month-only normalized to day 01); preserve human approval, append-only feed, and source provenance. No public REACH additions verified this run.