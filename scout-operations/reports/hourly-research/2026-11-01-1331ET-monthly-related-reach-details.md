# October 2026 primary-only monthly intake — 13:31 EST bounded REACH detail and cross-cohort investigation

**Mission:** 2026-11-01 13:31 EST. **Active intake:** 2026-11-01-monthly-api-2026-10-primary-only-part001 (13 DOI entries). **No candidate staged, no private Hub import verified, no public REACH addition.**

## Mandatory live ledger checks
- `api-discoveries/manifest.json`: 1 active primary-only batch, 13 DOI rows; superseded contaminated 26-row batch excluded.
- `scout-operations/monthly-triage.json`: 13 existing `needs_more_research` entries, no missing cases.
- `scout-operations/coverage.json`: received=13, checked=0, missing_from_ledger=0, errors=[].
- `scout-operations/active-workstream.json`: monthly_api_triage / additional_evidence_research; 13 unresolved follow-ups.
- No repeat of the completed 1,238-REACH index exact DOI/title, 68-Scout exact, or 578-project/990-mapping SPARK primary-award checks.
- This round **selectively inspected complete REACH detail rows** for relevant existing same-primary-award records; it does **not** claim all 1,238 full detail rows or publisher preprint/version variants were exhausted.

## New evidence and case-specific dispositions

### 10.1016/j.pdisas.2026.100696 — existing related REACH data, not the same publication
- [NOAA IR noaa:77174](https://repository.library.noaa.gov/view/noaa/77174) confirms the paper's DOI, eight authors, grant NA22OAR4590187, 2026 publication, seven focus groups with 29 Spanish-speaking immigrant workers in Wichita and Garden City, Kansas.
- Inspected REACH detail shard [part-092](https://github.com/PART-WPO/reach-dashboard/blob/main/agent-data/details/part-092.csv). Existing funded dataset and supporting materials are:
  - REACH reach-000765, [questionnaire/focus-group guide](https://doi.org/10.17603/ds2-6g47-4387).
  - REACH reach-000766, [workshop agenda/flyer](https://doi.org/10.17603/ds2-gc4p-2m64).
  - REACH reach-000767, [demographics worksheet](https://doi.org/10.17603/ds2-ehfz-ja17), explicitly 29 Kansas participants.
  - REACH reach-000768, [translated participant quotes](https://doi.org/10.17603/ds2-jmwe-bm11).
- Same primary award, overlapping investigators, locations, and 29-participant focus-group scope strongly support **related research materials**, but do **not** make the 2026 journal article a duplicate of these distinct dataset/material records. No exact DOI was found in the relevant detail rows. The publication still needs full REACH secondary-link/version and journal publication identity verification. **No new output lead is counted for the already-in-REACH datasets.**

### 10.3390/rs18193383 — targeted REACH detail check supports uniqueness, not complete dedup
- [Publisher](https://www.mdpi.com/2072-4292/18/19/3383) and [NOAA IR noaa:77382](https://repository.library.noaa.gov/view/noaa/77382) confirm the same DOI article and primary award NA22OAR4590179.
- Examined [REACH detail shard part-050](https://github.com/PART-WPO/reach-dashboard/blob/main/agent-data/details/part-050.csv): existing same-primary-award reach-000397 and reach-000398 are different-titled publications with distinct NOAA IR URLs, not the monthly DOI. The NOAA IR copy of the monthly paper is an alternate location, not another output.
- Funding remains strongly corroborated; full cross-award detail/version check remains open. Do not stage reused Copernicus datasets or UMD-LETKF code.

### 10.5281/zenodo.23289230 and 10.5281/zenodo.23289231 — one cross-cohort review family
- [DataCite exact DOI metadata checkpoint](https://github.com/PART-WPO/reach-scout-discoveries/blob/main/scout-operations/reports/doi-metadata-checkpoint/latest.json) records HasVersion/IsVersionOf, identifying concept DOI .23289230 and version DOI .23289231, created 2026-10-10, primary award NA22OAR0110487.
- Historical `scout-operations/historical-triage.json` has both DOIs as `human_metadata_needed`, with prior native-Zenodo access failure and **Hub delivery NOT VERIFIED**. `metadata-review-units.json` has one `zenodo-mom6` review unit, canonical identity undecided. Cross-cohort rediscovery does **not** create two new independent outputs or reset human review.
- Inspected [REACH detail shard part-137](https://github.com/PART-WPO/reach-dashboard/blob/main/agent-data/details/part-137.csv): same-award REACH reach-001210–001213 are prior publications and `Frequency-dependent Drag (Source Code)` at c2xu/MOM6; none matches either new dataset DOI. This existing code record is not the same identity as [MOM6 PR #1104](https://github.com/NOAA-GFDL/MOM6/pull/1104). Do not claim PR #1104 is a separately funded new output without further evidence.
- Exact DataCite metadata lists named dataset files in the description but **does not independently establish native Zenodo file accessibility** (listed_formats=0, listed_sizes=0). Direct Zenodo record pages were not retrievable in this mission. Preserve human_metadata_needed status in historical review; keep monthly entries open pending cross-cohort reconciliation, native file verification, and a reviewer-safe canonical DOI decision.

### 10.1175/WAF-D-26-0084.1 — related earlier REACH article, distinct 2026 work
- [REACH detail shard part-069](https://github.com/PART-WPO/reach-dashboard/blob/main/agent-data/details/part-069.csv) contains reach-000558, *Evaluation of an Experimental 15-Member FV3-LAM Ensemble for the Summer 2024 Flash Flood and Intense Rainfall Experiment* (DOI 10.1175/waf-d-25-0256.1). The monthly paper concerns **summer 2025 FFaIR** and has DOI 10.1175/WAF-D-26-0084.1. These are related workstreams, not exact same DOI or title. Same-primary-award detail check found no match to monthly DOI, but a preprint/secondary URL check is still pending.

### 10.1175/AIES-D-26-0004.1 — same-award prior REACH research, not an exact duplicate
- [REACH detail shards part-063](https://github.com/PART-WPO/reach-dashboard/blob/main/agent-data/details/part-063.csv) and [part-064](https://github.com/PART-WPO/reach-dashboard/blob/main/agent-data/details/part-064.csv) include prior NA22OAR4590530 publications, reports, code and training/operational outputs. None contains the monthly exact DOI in the inspected detail fields. Those preexisting outputs are not new monthly discoveries. Direct funding acknowledgment and full identity checks remain pending.

### 10.1080/01431161.2026.2749622 — retain multiple primary projects
- The active monthly record has three primary awards spanning RRFS-CMAQ and S2S Fire Emissions projects. [REACH index shard part-009](https://github.com/PART-WPO/reach-dashboard/blob/main/agent-data/index/part-009.csv) contains earlier S2S fire publications and a distinct existing Firecasting software record `reach-001095` (`GMU-SESS-AQ/firecasting`). These are relevant related outputs, not proof the 2026 paper or speculative similarly named code is already in REACH. Same-project attribution for RRFS-CMAQ still needs publisher acknowledgments.

## Workstream safeguards
- All 13 monthly original DOI entries remain nonterminal. `checked=0` counts closed cases, not number with research.
- Two retired related-award historical proposals remain excluded from the active Scout feed; private Hub cleanup unverified.
- No invented DOI seed, inferred related-only WPO award, new Hub draft, human decision, or public REACH change.
- Update existing monthly entries with bounded evidence and regenerate coverage/workstream via existing GitHub Actions; do not manually edit derived coverage, manifests, or immutable source batches.
