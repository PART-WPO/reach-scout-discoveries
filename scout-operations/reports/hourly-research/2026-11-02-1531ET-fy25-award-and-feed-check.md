# REACH Scout hourly research report — 2026-11-02 15:31 ET

**Selected mode:** Normal historical discovery; focused FY25+ task-qualified award validation. **No new candidate staged.** Research, reviewer decisions and source batches remain unchanged.

## Current queue and feed
- Monthly active primary-only API batch: 13 distinct original DOIs; coverage 13/13 checked and missing_from_ledger=0; 9 staged in validated public Scout review feed; 4 documented no-action; no uninvestigated originals.
- Historical DataCite: 188 original DOIs fully investigated, remaining=0, human_metadata_needed=28 (separate from private Hub import).
- Monthly API-seeded expansions: 6 leads; 2 staged for public human review, 3 already in REACH, 1 pending human intake. Never count as original monthly DOIs.
- Current Scout manifest and rollup: 30 batches, 85 staged proposal rows, 22 effective direct-API discovery, 17 API-seeded, 46 independent, 0 unknown. Public REACH baseline 1,238; no public addition observed in this run.

## Exact FY25+ primary-award research
**DOI:** 10.5194/tc-20-5973-2026; published 2026-10-15 in *The Cryosphere*.

**Finding:** Publisher and NOAA IR exact publication record both explicitly name full award **NA25OARX459C0342-T1-01**. All six public SPARK index shards were screened for the shared base NA25OARX459C0342: exactly one record was found, spark-000373, with the complete -T1-01 suffix as PRIMARY Award Number(s). No sibling task was found in this snapshot; this does not prove none exist elsewhere. The California snow/vegetation modeling paper is related to spark-000373's western-snow-dynamics topic, but a direct contribution to the Southern Great Plains remote precipitation objective has not been independently verified. Publisher links the earlier preprint 10.5194/egusphere-2025-3884 to the same final publication; supplement and reused Noah-MP software are not separately eligible outputs by default.

**What to check before adding this output:** Confirm exact spark-000373 task deliverable and SGP remote-effects bridge | Compare final DOI and preprint DOI across REACH secondary links, URL aliases and private Hub decisions before counting one publication | Preserve complete NA25OARX459C0342-T1-01 in CSV and reviewer notes, not base-only NA25OARX459C0342 or a sibling task | Do not count article supplement or reused model as independent outputs | Retain publisher publication date 2026-10-15 and exact grant evidence.

**Reviewer question:** Is this article a deliverable of the exact task-qualified primary SPARK project, and is the final publication absent from REACH secondary links and private human review history?

## Pipeline and reviewer-story checks
The current quick_monthly_intake.py regex accepts full FY25 OARX/C task-qualified identifiers and legacy NA17OAR4590184. check_funding() uses exact full-set intersection against SPARK literal PRIMARY Award Number(s), not Related Award Number(s); sample parsing distinguishes T1-01 and T2-01. The active eight-row monthly reviewer-story batch contains eight each of Finding, What to check, and Reviewer question, with >=3 pipe separators in each specific checklist. The separate FRP enriched single-row batch has all three labels. Full factual reviewer approval, live private Hub sync and automated validator execution were not observed.

Eight research-lead JSON files were enumerated; unified independent-metadata report has 14 successful exact DOI lookups and two GitHub release records. Existing DeepFlood Figshare 26791243/28328339 metadata is recovered, but native file inventory, DOI canonical/version relation and dataset-specific WPO funding remain unresolved. Native Figshare API endpoints were inaccessible in this run, not evidence of missing files. No lead was reclassified or restaged.

## Limits
No complete 140-shard REACH detail scan or full Scout batch checksum recalculation occurred in this run. Public index and manifest checks are not equivalent to private Hub review. No REACH, SPARK, Smartsheet, human decision, immutable batch or manifest was edited; no new CSV was created. Reviewer should use Discovery Hub **Sync to Scout** for validated feed proposals if not already imported, then independently decide. Next research priority: DeepFlood canonical identity/file scope and exact funded project attribution, or a different unreviewed primary SPARK award.

## Evidence
- https://tc.copernicus.org/articles/20/5973/2026/
- https://repository.library.noaa.gov/view/noaa/76974
- https://github.com/PART-WPO/SPARK/blob/main/agent-data/index/part-004.csv
- https://github.com/PART-WPO/reach-scout-discoveries/blob/main/scout-operations/api-followup-priority-policy.md
- https://github.com/PART-WPO/reach-scout-discoveries/blob/main/scout-operations/tools/quick_monthly_intake.py
- https://github.com/PART-WPO/reach-scout-discoveries/blob/main/scout-discoveries/batches/2026-11-02-monthly-reviewer-story-parity-001.csv
- https://github.com/PART-WPO/reach-scout-discoveries/blob/main/scout-discoveries/batches/2026-11-02-monthly-enriched-frp-2749622-001.csv
