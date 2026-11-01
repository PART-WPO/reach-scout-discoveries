# REACH Scout — November 1, 2026, 18:27 EST — bounded monthly attribution decision and expansion follow-up

## Scope and authoritative sources
Read current `api-discoveries/manifest.json`, `scout-operations/monthly-fast-intake.json`, `monthly-triage.json`, `coverage.json`, `active-workstream.json`, `monthly-decision-queue.json`, `monthly-expansion-leads.json`, `scout-discoveries/manifest.json` and the November 1 monthly intake-first policy before research. The sole active October monthly API batch is `2026-11-01-monthly-api-2026-10-primary-only-part001` (13 original DOI records); the earlier 26-record batch remains superseded. Existing 8 originals are already validated and present in the **public Scout discovery feed**; do not duplicate. The Scout manifest was 76 active records across 31 batches when read. This does not verify private Discovery Hub import, approval or public REACH addition.

## Lane A: original monthly funding-scope decisions

### DOI 10.1002/qj.70325 — evidence-backed **no_action for this WPO project attribution**
The Wiley article's acknowledgments explicitly assign NOAA grant `NA20OAR4320278` to Centurioni, the Global Drifter Program and 15 Mediterranean drifters. The corresponding SPARK PRIMARY-award project, West Coast Advanced Quantitative Precipitation Information (AQPI), instead concerns West Coast radar/modeling/decision support. NOAA IR independently records the DOI and award, but does not bridge the article to AQPI. After prior publisher, SPARK full-project and ECMWF OSE research plus this separate NOAA IR check, no same-project primary-SPARK WPO bridge was found and the article contains concrete contrary project evidence. **Disposition:** mark this original monthly ledger case `no_action` (do not stage as AQPI). This is *not* a claim that the article lacks NOAA funding or could never be eligible under another independently documented primary WPO project. Reopen only with positive same-project documentary evidence or explicit reviewer direction.
Evidence: https://rmets.onlinelibrary.wiley.com/doi/10.1002/qj.70325 ; https://repository.library.noaa.gov/view/noaa/77398 .

### DOI 10.1088/2515-7620/aeaad2 — human attribution question remains pending, NOT delivered
NOAA IR verifies the exact DOI and grant `NA24OARX459C0015`. The study evaluates Western North Pacific tropical-cyclone accumulated cyclone energy using seasonal forecast system reforecasts; the primary SPARK GLORe project concerns ocean reanalysis/sea-ice monitoring. This does not prove non-funding, but neither the original project record nor the repository metadata establishes that the article was produced under the GLORe-funded tasks. **Do not stage as a confirmed WPO output**. Reviewer question: *Was the SFS study a deliverable of the primary GLORe award or is the award attribution broad/unrelated?* The question remains recorded in the existing ledger; no private Hub handoff is verified.
Evidence: https://repository.library.noaa.gov/view/noaa/76692 .

### DOI 10.5194/egusphere-2026-4928 — human attribution question remains pending, NOT delivered
Copernicus verifies the preprint, October 30 discussion date, authors and ARM Southern Great Plains land-observation stability methods. The primary SPARK `NA22OAR4590118` projects concern saildrone hurricane air–sea interaction. NOAA coauthor affiliation is not a project bridge. The publisher PDF request timed out and XML was inaccessible through the browser, so funding acknowledgment is **source inaccessible**, not known absent. Reviewer question: *Is there documentary evidence this land-based study was produced under the primary saildrone award's tasks?* No candidate staged and no private Hub delivery observed.
Evidence: https://egusphere.copernicus.org/preprints/2026/egusphere-2026-4928/ .

## Lane B: API-seeded expansion — separate from original review staging
- `10.1177/10506519261455873` — SAGE independently confirms online publication July 6, 2026 and attaches a supplemental PDF to the *same* article. The supplement is not a distinct candidate by default. Accessible publisher content does not establish article-specific WPO award. Still `investigating`; no separate draft. https://journals.sagepub.com/doi/abs/10.1177/10506519261455873 .
- `10.1145/3794916.3794919` — Pinakes confirms a distinct March 2026 Communication Design Quarterly article and points to an open-access DOI-linked PDF. The DOI landing request returned 403, so publisher acknowledgments were not inspected; article-specific primary WPO funding and full REACH/Scout detail/version dedup remain unverified. Still `investigating`; no separate draft. https://pinakes.wacclearinghouse.org/article/376641 .
- `10.25923/k9kh-y971` — existing public REACH record `reach-000821`, unchanged; do not restage.
All three leads retain original seed DOI `10.5194/egusphere-2026-5876` and `API-seeded expansion` origin. The two independent leads were updated in their **existing** expansion ledger entries, not duplicated.

## Funnel and safeguards
- October original API records: **13**.
- Validated **public Scout feed staged** original candidates: **8** (unchanged).
- Original monthly cases newly closed this mission: **1** (`no_action`, funding-scope mismatch).
- Original exceptions still needing project attribution decision: **2**; human referral not yet delivered.
- Original version-family historical review cases: **2** previously closed as `no_action` to avoid duplicate proposals.
- Private Discovery Hub imports: **NOT VERIFIED**. Reviewer should use **Sync to Scout** to import the 8 manifest-listed candidates.
- Human approvals: **NOT VERIFIED**; public REACH additions: **none observed**.
- API-seeded expansion leads: **2 investigating**, **1 already in REACH**, **0 separately staged**.
- No related-only SPARK awards used as eligible seeds; retired historical award-update proposals remain excluded. No Smartsheet, REACH, human decision, immutable batch, or schedule change.

## Validation
Ledger and expansion-lead updates committed through GitHub contents API. **Coverage and workstream automation may lag the new ledger commit**: the previously read coverage was 13 received / 10 checked / 3 open / 0 missing, while the newly written ledger now contains 11 terminal cases and 2 open. Do not represent the refreshed 11/2 coverage as GitHub Actions validated until its regenerated artifacts are observed. Recheck generated coverage, decision queue and active-workstream after workflow completion; investigate rather than skip if `missing_from_ledger` becomes nonzero.
