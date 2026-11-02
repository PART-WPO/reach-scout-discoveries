# REACH Scout — November 1, 2026, 21:27 ET
## October primary-only monthly intake: bounded original exception and separate DOI-seeded data lead

### Inputs and safeguards
Read active `api-discoveries/manifest.json`, `scout-operations/monthly-fast-intake.json`, `monthly-triage.json`, `coverage.json`, `active-workstream.json`, `monthly-decision-queue.json`, `monthly-expansion-leads.json`, `scout-discoveries/manifest.json`, and `api-followup-priority-policy.md` before research. Active October source batch remains `2026-11-01-monthly-api-2026-10-primary-only-part001` (13 DOIs). The superseded contaminated 26-record batch is excluded. SPARK eligibility uses **primary Award Number(s) only**. No pre-existing human decisions or retired proposals were changed.

### Lane A — original DOI 10.1088/2515-7620/aeaad2
**New primary-source evidence:** Read the complete 14-page journal PDF hosted by NOAA IR: https://repository.library.noaa.gov/view/noaa/76692/noaa_76692_DS1.pdf .

* Page 11, **Funding**, explicitly states that this research was supported by NOAA grant **NA24OARX459C0015**. This is stronger than the previously checked NOAA IR metadata funding tag.
* Page 3, **Data / SFS reforecasts**, explicitly says that the ocean and sea-ice initial states for the analyzed seasonal forecast prototypes came from **Global Ocean Reanalysis (GLORe)**. This is a specific technical link to SPARK primary project `spark-000155` (GLORe ocean reanalysis and sea-ice monitoring), despite the paper's tropical-cyclone end-use topic.
* Page 11 separately states that **development of the GLORe reanalysis** was supported by **NOAA/GOMO**. Thus GLORe's use as an input is not by itself proof that the WPO-funded GLORe project produced the publication. The direct article-level grant support and specific GLORe method link make the previous *pure topic-mismatch* rationale insufficient for an automatic exclusion.
* The publisher PDF states **published 2026-10-07** (page 1). Its Data Availability statement (page 11) cites DOI **10.5281/zenodo.22758716** as the data supporting this study.

**Disposition:** Preserve `needs_more_research` with a specific **human attribution / quick-intake eligibility reassessment**. The original still needs a full REACH/Scout detail/secondary-link, alternate DOI and version screen before any validated 24-column human-review draft. Do not force a same-project funding gate to true, assign a definitive project outcome, or claim private Hub import. Existing ledger entry updated; no new original row.

### Lane B — new source-linked data DOI 10.5281/zenodo.22758716
Added one `API-seeded expansion` lead to the existing `scout-operations/monthly-expansion-leads.json` with exact original seed `10.1088/2515-7620/aeaad2`, source-to-lead evidence path (publisher PDF Data Availability), and `investigating` status.

**Not verified:** Native DataCite/Zenodo metadata and exact title/creators/date; this dataset's own WPO award and same-project attribution; concept/version relation; full REACH/Scout index+detail+secondary-link duplicates. GitHub code search returned no indexed hits for `22758716` in either public repository, which is NOT a complete duplicate audit. Do not stage or count the data lead as a new output until independently verified. Existing paper's use of TempestExtremes, GLORe, UFS, etc. is not evidence those external tools/data are new WPO-created products.

### Current intake funnel (re-read, not frozen)
* **Original October DOI rows:** 13.
* **Validated PUBLIC Scout feed original candidates:** 8 (`staged_for_hub_import`); **private Discovery Hub import: NOT VERIFIED**.
* **Other original terminal decisions:** 3 `no_action` (one specific AQPI attribution exclusion and two already-under-historical-review Zenodo version identities).
* **Open original attribution cases:** 2 (`10.1088/2515-7620/aeaad2` and `10.5194/egusphere-2026-4928`).
* **API-seeded expansion leads:** 6 after this mission (3 already in REACH, 3 investigating; 1 new data lead).
* **New expansion candidates staged:** 0. **Human approvals observed:** none. **Public REACH additions observed:** none.
* Last observed `coverage.json` was 13 received, 11 checked, 8 staged, 2 needing research, 0 missing and 0 errors. A new post-commit GitHub Actions validation must be checked; do not claim it already passed.

### Reviewer and next-mission actions
Use **Sync to Scout** in the private Discovery Hub to retrieve the eight public-feed candidates; delivery cannot be inferred from manifest publication. Reassess the GLORe paper using its direct funding and methods evidence, then complete the specific identity checks and use the validated human Needs Investigation path if compatible. Separately query DataCite/Zenodo for the cited dataset and complete its independent funding and duplicate checks. For the other original exception, `10.5194/egusphere-2026-4928`, the Copernicus landing page still supplies no accessible full-text funding acknowledgment (PDF timeout, XML unsupported); preserve its specific blocked reviewer question, not a fabricated rejection. Do not repeat already completed exact first-pass scans, do not stage related-only awards, and do not change the standing schedule or public REACH/Smartsheet.
