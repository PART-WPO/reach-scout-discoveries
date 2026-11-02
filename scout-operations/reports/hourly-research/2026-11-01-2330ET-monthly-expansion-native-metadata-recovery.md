# REACH Scout — Native DOI metadata recovery (late November 1, 2026)

This is a **research-only** continuation of the [23:24 ET expansion mission](2026-11-01-2324ET-monthly-expansion-project-bridge-and-checkpoint.md). The independent metadata GitHub Action [run 41388471017](https://github.com/PART-WPO/reach-scout-discoveries/actions/runs/41388471017) **completed successfully**, and the [native lookup report](../independent-metadata-lookup/latest.json) contains successful source-specific responses for all three October monthly API-seeded leads. Earlier DataCite/Zenodo browser access errors were access limitations, not evidence of missing metadata.

## New verified evidence

**1. SAGE journal publication DOI 10.1177/10506519261455873**
- Native Crossref exact DOI response: [Crossref works record](https://api.crossref.org/works/10.1177/10506519261455873).
- **Publisher-deposited structured funding**: NOAA Weather Program Office, funder DOI `10.13039/100018606`, grant `#NA21OAR4590208` (normalize to primary `NA21OAR4590208`). This is the same primary SPARK project supported by the NOAA IR grant [noaa:67218](https://repository.library.noaa.gov/view/noaa/67218), whose survey/visualization workstream matches the article. It is strong source-specific WPO attribution evidence for **human review**, not human approval.
- Crossref **published-print 2026-10 (month only)** -> WPO office date **2026-10-01**, with day 1 explicitly imputed; publisher first-online date **2026-07-06** is separate and not the print-first office date.
- Full title, seven creators, abstract and journal-article type returned. Strip JATS markup from abstract. Exact title/DOI absent from 10 public REACH index shards, 32 active Scout batches, 10 inbox drafts. **Full secondary-link/version dedup remains unverified**, so no new draft yet.

**2. ACM journal publication DOI 10.1145/3794916.3794919**
- Native [Crossref works record](https://api.crossref.org/works/10.1145/3794916.3794919) verifies exact title, seven creators, abstract and **published-print 2026-03-01** (day precision).
- Crossref **funding_references empty**. The NOAA IR primary award proposal describes the same research workstream, but this does **not** verify article-specific grant attribution. Funding remains open for a bounded human attribution question or source-specific acknowledgment.
- Full secondary-link/version dedup remains unverified; no draft.

**3. Zenodo DOI 10.5281/zenodo.22758716**
- Native [DataCite DOI record](https://api.datacite.org/dois/10.5281/zenodo.22758716) verifies title **2026 Nedza Huang Zhu - NWP Dynamical Forecasting Manuscript**, creator **Nedza, Douglas**, resource type **ComputationalNotebook**, description **data and Python code** for the Nedza/Huang/Zhu manuscript, and **created 2026-09-14** (WPO office publication date).
- DataCite **fundingReferences empty**. Parent journal article acknowledgment cannot automatically be attributed to this notebook.
- **IsVersionOf DOI 10.5281/zenodo.20046428**; verify the concept/version parent before treating the notebook as independently catalogable. The parent was queued as a **metadata-only version-family check**, NOT a new output.
- File access, own funding, proper Code/Data/Other classification, complete secondary-link/version dedup remain open; no draft.

## State and follow-up
Original October monthly DOI cases remain **13 checked, 9 staged in public Scout feed, 4 no_action, missing_from_ledger 0**. The **6** API-seeded expansion leads remain **3 existing REACH duplicates and 3 investigating**, with **one of the investigating leads now supported by explicit structured primary WPO funding**. Private Hub imports **NOT VERIFIED**; no human approvals or new public REACH additions observed. Monthly coverage and Scout manifest validation passed after the ledger update; the larger direct DOI checkpoint remains separately pending at the last check. Use the validated private Hub **Sync to Scout** import for the nine staged originals; do not assert import until observed.

Research metadata and source evidence were written into the **existing** [monthly expansion ledger](../../monthly-expansion-leads.json). No new 24-column candidate, immutable batch, human decision or REACH/Smartsheet change was made.
