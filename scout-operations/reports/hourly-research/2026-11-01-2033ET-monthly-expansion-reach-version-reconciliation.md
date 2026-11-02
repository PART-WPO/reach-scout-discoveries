# REACH Scout — November 1, 2026, 20:33 EST — monthly expansion lineage and duplicate reconciliation

**Scope:** Monthly intake-first; research lane B only. No new original DOI candidates or private Hub actions.

## Authoritative state read before research
- Active monthly API manifest: 13 primary-SPARK-award DOI records in `2026-11-01-monthly-api-2026-10-primary-only-part001`. Superseded 26-record related-award batch excluded.
- Monthly fast-intake: 8 ordinary originals already validated and published to the public Scout feed; 3 funding anomalies and 2 cross-cohort Zenodo records in the fast-intake exceptions view. The monthly research ledger/coverage supersedes that static exception breakdown for terminal decisions.
- Monthly ledger and coverage: 13 received; 11 research-terminal (8 staged for public Scout feed, 3 closed without new staging), 2 original attribution cases open, 0 missing, 0 coverage errors.
- Active Scout discovery manifest: 76 active candidate rows across 31 batches, including 8 monthly-fast original batches. This is a PUBLIC research feed, not evidence of private Discovery Hub import.
- Monthly decision queue: 2 original decisions due. Active workstream: monthly_api_triage / original_decision_fast_path.
- Expansion ledger before this mission: 3 entries (2 investigating, 1 already in REACH).

## New evidence-backed source-linked research
Original monthly seed: `10.5194/egusphere-2026-5876` (Direct API). Its references link to the 2026 SAGE publication `10.1177/10506519261455873` (tracked expansion lead), whose publisher reference list cites the 2023 Heggli et al. BAMS article. The 2023 BAMS article in turn describes a WPO-funded visualization template.

**Existing REACH publication** — `10.1175/BAMS-D-22-0220.1`, *Visual Communication of Probabilistic Information to Enhance Decision Support*. Publisher acknowledgments explicitly name NOAA WPO Social Sciences Program grant `NA21OAR4590208`; NOAA Institutional Repository `noaa:63628` corroborates. Full public REACH index part-007 and detail part-097 already list this exact publication as **reach-000820**. Added one expansion-ledger entry with status `already_in_reach`, preserving the original monthly seed DOI and two-hop path. **No new Scout candidate**.

**Existing REACH visualization template** — Zenodo version DOI `10.5281/zenodo.7999820`, *Visual Communication of Probabilistic Information To Enhance Decision Support*. Native Zenodo record confirms 2023-06-02 publication, version v3, direct `NA21OAR4590208` WPO funding, and PDF/PPTX/XLSX files belonging to the same record. Full public REACH index part-007 and detail part-097 list the template as **reach-000822**. Added one expansion-ledger entry with status `already_in_reach`; component files are not separately countable outputs. The BAMS paper also cites `10.5281/zenodo.7600486`; OpenAIRE aggregates `7600486`, `7600487`, `7999180`, and `7999820` under the same title, suggesting a version/concept family. **Native DataCite relationship direction is NOT VERIFIED**; do not count the four DOIs separately or assert exact parent/version mapping.

## Original exceptions — no false resolution
- `10.1088/2515-7620/aeaad2`: NOAA IR primary-award grant string is confirmed; source-specific connection to SPARK GLORe ocean-reanalysis/sea-ice tasks remains unverified. Human attribution question remains pending compatible review, not Hub-delivered.
- `10.5194/egusphere-2026-4928`: Copernicus confirms 2026-10-30 discussion start, 2026-08-15 received date, and ARM Southern Great Plains land-site stability analysis. No positive funded-task bridge to SPARK's saildrone hurricane project. Publisher PDF timed out and XML was not accessible through this research environment. Human attribution question remains pending compatible review, not Hub-delivered.
- No change to existing `10.1002/qj.70325` no-action attribution disposition, the two closed Zenodo historical version cases, or any human decisions.

## Verified post-write accounting
- 13 original monthly DOI rows: **8 public Scout feed staged**, **3 closed without new staging**, **2 original attribution exceptions open**.
- Public Scout manifest: 76 active proposals, including the 8 monthly originals; no new proposal in this mission.
- Expansion ledger: **5 total**, **3 already in public REACH**, **2 investigating**, **0 newly staged**. The two additions are already-public historical products, NOT newly found additions.
- Coverage: 13 received, 11 checked, 8 staged_for_hub_import, 0 forwarded_to_hub, 0 missing, 0 errors.
- Private Discovery Hub import: **NOT VERIFIED**. Reviewer must use **Sync to Scout**; no human approval or public REACH addition is inferred.
- `monthly-decision-queue.json` refreshed read shows 5 expansion leads, 2 awaiting independent verification. `active-workstream.json` continues to prioritize 2 original funding exceptions.
- No public REACH, SPARK, Smartsheet, immutable batches, superseded records, or reviewer decisions changed.

## Evidence URLs
- https://journals.sagepub.com/doi/10.1177/10506519261455873
- https://journals.ametsoc.org/view/journals/bams/104/9/BAMS-D-22-0220.1.xml
- https://repository.library.noaa.gov/view/noaa/63628
- https://zenodo.org/records/7999820
- https://explore.openaire.eu/search/result?pid=10.5281%2Fzenodo.7999820
- https://github.com/PART-WPO/reach-dashboard/blob/main/agent-data/index/part-007.csv
- https://github.com/PART-WPO/reach-dashboard/blob/main/agent-data/details/part-097.csv
- https://egusphere.copernicus.org/preprints/2026/egusphere-2026-4928/
- https://repository.library.noaa.gov/view/noaa/76692

**Next priority:** Resolve the two original funded-task attribution questions with project PI/deliverable evidence or explicit reviewer Investigate decision, then independently verify article-specific funding and complete REACH/Scout detail/version comparisons for the two 2026 SAGE/ACM expansion leads. Do not re-run already completed original monthly screening.
