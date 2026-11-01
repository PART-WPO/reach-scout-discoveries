# October 2026 primary-only monthly intake — substantive source and version follow-up

**Mission:** 2026-11-01 approximately 11:32 EST. **Status:** Five existing monthly DOI cases received additional evidence-backed research; all remain `needs_more_research` (no terminal decision, no new Hub draft).

## Source-of-truth validation

- Active `api-discoveries/manifest.json` remains batch `2026-11-01-monthly-api-2026-10-primary-only-part001` (13 DOIs), superseding the contaminated 26-row batch. The latter is not research input.
- `scout-operations/monthly-triage.json` contained 13/13 active cases; `coverage.json` read `received=13, missing_from_ledger=0, checked=0, errors=[]` before mission.
- `active-workstream.json` still prioritizes monthly API additional-evidence research. First-pass exact DOI/title scans against public REACH and active Scout batches were not repeated.
- Five **existing** ledger entries were updated in place; source identities and original statuses preserved. Ledger commit: `ba7e1fefa49ee34afd645b60896e05a7f7bab7e6`.

## Case findings

### 10.1002/qj.70325 — serious same-project funding mismatch

The [publisher's article](https://rmets.onlinelibrary.wiley.com/doi/10.1002/qj.70325) gives first-publication date **2026-10-12**. Its full acknowledgments explicitly assign NOAA grant **NA20OAR4320278** to Luca Centurioni, 15 surface drifters, their relay and the **Global Drifter Program**. It credits other authors to California DWR, ERDC, and NOAA CIMEAS AR Recon Project 316792. In contrast, [SPARK primary project index](https://github.com/PART-WPO/SPARK/blob/main/agent-data/index/part-004.csv) associates that grant with the West Coast AQPI project. Same-project WPO attribution **NOT VERIFIED**; do not stage as AQPI. Article's data-availability section links ECMWF OSE DOI **10.21957/befj-es73** and **10.21957/e8rz-wh72**. They are **research leads only**, not established WPO outputs; observations are access-restricted.

### 10.1016/j.pdisas.2026.100696 — stronger same-project evidence

[NOAA IR noaa:77174](https://repository.library.noaa.gov/view/noaa/77174) confirms the exact DOI, eight authors, `Progress in Disaster Science` volume 31, journal-article type, downloadable CC BY PDF, **WPO/OAR tags**, and explicit **Grant no. NA22OAR4590187**. [SPARK primary project spark-000134](https://github.com/PART-WPO/SPARK/blob/main/agent-data/index/part-002.csv) is *A Weather-Ready Nation Para Todos*, aligned with the publication's Spanish-speaking immigrant workers and extreme-weather communication topic. The NOAA IR URL is another location for the **same work**, not a distinct new output. Crossref print-month convention gives Pub Date **2026-10-01**; NOAA IR provides year 2026, not exact day. Alternate-URL REACH dedup and related-output expansion remain pending.

### 10.1080/01431161.2026.2749622 — multi-project and code lead

[Taylor & Francis journal listing](https://www.tandfonline.com/subjects/geography?ContentItemType=research-article&PrimaryLanguageFacetField=en&SeriesKey=tres20&content=standard&pageSize=10&startPage=0&subjectTitle=&target=default) confirms online publication **2026-10-30**. [SPARK index](https://github.com/PART-WPO/SPARK/blob/main/agent-data/index/part-005.csv) shows **NA22OAR4590512** under RRFS-CMAQ (spark-000536) and **NA23OAR4590387 / NA23OAR4590388** under S2S Fire Emissions (spark-000544). Fire Radiative Power research fits the latter, but the former's project-specific contribution is not yet confirmed. A [similarly titled public code repository](https://github.com/earth-artificial-intelligence/wildfire_guass_physics) was located; its README does not prove the exact article, funding, or output identity. **Do not stage code** until linked independently.

### 10.5281/zenodo.23289230 and 10.5281/zenodo.23289231 — confirmed concept/version DOI family

The [previously verified exact-DOI DataCite checkpoint](https://github.com/PART-WPO/reach-scout-discoveries/blob/main/scout-operations/reports/doi-metadata-checkpoint/latest.json) shows `10.5281/zenodo.23289230` **HasVersion** `10.5281/zenodo.23289231`; the latter **IsVersionOf** the former. Both have the same dataset title, Xu/Zaron creators, **NA22OAR0110487**, created **2026-10-10** (accepted DataCite Pub Date), and CC BY 4.0. Both already appeared as original historical DataCite records in October 28 batch `part002` and historical review unit **zenodo-mom6**; October monthly rediscovered that family. [SPARK spark-000391](https://github.com/PART-WPO/SPARK/blob/main/agent-data/index/part-004.csv) has the primary award and MOM6 ocean-tides project. [NOAA-GFDL/MOM6 PR #1104](https://github.com/NOAA-GFDL/MOM6/pull/1104) is a merged code change titled *Baroclinic sea level calculation*, with an intended JPO manuscript but **no verified publication DOI**. The PR is an expansion lead, not a new staged output. Do not create two dataset candidates. Confirm Zenodo public-file accessibility and which DOI best represents the dataset; reconcile existing historical human review unit first.

## Research metrics and safeguards

- Active primary-only monthly source records: **13**; source records missing from ledger: **0**.
- Original monthly cases substantively advanced this mission: **5**; remaining cases needing additional evidence: **13** (including these five; not terminal).
- New **candidate** drafts: **0**. Private Hub imports verified: **0**. Human approvals observed: **0**. Public REACH additions: **0**.
- Linked-output leads: **2 ECMWF experiment DOIs**, **1 potential Fire Radiative Power code repository**, **1 MOM6 merged code PR**; none established as separately WPO-funded, unique, and eligible.
- No immutable API batch, Scout published batch, manifest, human decision, Smartsheet, or public REACH entry was changed. Retired related-award corrections remain retired.
- `coverage.json` and `active-workstream.json` are GitHub Actions-generated/validated; this mission did not manually assert terminal counts. Recheck after automated regeneration; until then prior verified counts are 13 received / 0 closed / 0 missing.

**Next:** Finish REACH alternate-link/version comparisons, publication-specific funding proofs and related-output expansion for the remaining 8 DOI cases, and reconcile the Zenodo historical review unit. Never turn source discovery or preliminary funding into a Hub approval.
