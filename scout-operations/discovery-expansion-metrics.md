# Scout discovery expansion: provenance and impact measurement

**Purpose:** Scout's distinctive benefit is research **beyond** directly retrieved award-number DataCite/Crossref records. Count direct API outputs separately from (a) additional outputs reached by following an API seed's citations, related identifiers, data availability/code links, authors, or repositories and (b) independently discovered outputs from award/project/researcher exploration.

## Required human-auditable route in every NEW Scout-verified finding

Keep the existing 24-column Scout-reviewed CSV format, existing evidence verification, current award/provenance requirements and all human review boundaries. Put these separate exact **lines in `Scout Discovery Rationale`**:

- Direct DataCite/Crossref raw API input: `Scout discovery route: Direct API` plus `Scout discovery path evidence: https://...` (the exact original API source).
- New connected output, found by **following** an API input into a related work: `Scout discovery route: API-seeded expansion`, `Scout seed DOI: 10.xxxx/...`, and `Scout discovery path evidence: https://...` (the actual relation/citation/repository source demonstrating the trail from seed to new distinct output).
- New output identified through **independent** SPARK award, institution, investigator, project, bibliographic, software or dataset searches: `Scout discovery route: Independent discovery`, `Scout discovery path evidence: https://...` and a brief `Scout discovery method: ...` explaining the actual search path.
- Uncertain origin: `Scout discovery route: Unclassified`. Do not guess or invent research paths.
- Metadata corrections (not novel outputs): `Scout discovery route: Metadata correction` and cite original correction evidence. Do not count them as additional outputs.

A candidate is not "beyond the API" simply because it has a DOI or was found in a non-API Scout mission. Check BOTH current monthly and historical API source manifests/CSV shards. **Not present in captured direct award-number API batches** is the accurate statement; it does not prove the work can never be retrieved through any API or is truly absent from all Crossref/DataCite holdings. Note the exact input cohort, award and relation that generated the discovery. If the same DOI is also present in direct award-number API source batches, don't label it as beyond those captured pulls without a separately demonstrated earlier discovery time and human verification.

In each API-focused investigation, **follow related articles/code/data** and pursue credible expansion leads; do not limit Scout to checking whether each initial API record already appears in REACH. Maintain a separate research trail of linked outputs beyond the seed DOI. Expand only as evidence supports and continue the priority API queue across missions until each seed record has a documented disposition. This is what makes Scout complementary to direct API harvesting.

## Evidence funnel / no inflated claims

Use these distinct stages in reporting:
1. **Research lead:** found and Scout-reviewed; not necessarily new or actionable.
2. **Discovery route confirmed:** a human reviewer in the PRIVATE Hub checked origin evidence and compared DOI or stable URL against all recorded direct-award API batches. This is the count of Scout leads outside captured direct API pulls (not publication).
3. **Approved and staged:** reviewer accepts a genuinely distinct, funded output; no public publication yet.
4. **Verified added to public REACH:** output has a new Smartsheet source insertion and is found through exact public REACH output-link/UID verification. A correction to an existing output isn't a new record.

Human attribution and time-study data are stored in the **private** Discovery Hub spreadsheet, **not this public repo**. The October 28, 2026 REACH baseline is 1,238 public records (source index SHA256 054d139eacf0c687ef4efe54be525198db20ffb47febe80683888beaa547103e). A published-output increase can be calculated against the baseline, but distinguish Scout-attributable additions from normal REACH growth. Never use staged findings, approved cases, API DOI records or unverified publication dates as new published REACH outputs.

Time metrics: measured manual research minutes and Scout-assisted human review minutes must be genuinely paired/observed, not invented estimates. Elapsed intake-to-disposition hours include waiting; don't confuse them with actively worked researcher minutes. Costs or hours saved must be labeled modeled unless observed.

## Hourly evidence audit — 2026-10-28 22:33 ET

Audit JSON: [REACH-SCOUT-2026-10-28-HOURLY-2233ET](hourly-run-audits/2026-10-28-2233ET.json). Primary mode: historical DataCite; monthly API source empty. Original seeds examined **5**, all **already in public REACH** (five exact DOI and award matches), not new candidates. Four distinct journal articles followed from API seed datasets were also **already in public REACH**, not new expansion findings. New review candidates by route: Direct API **0**; API-seeded expansion **0**; Independent discovery **0**; Metadata correction **0**; Unclassified **0**. Human metadata-needed escalations **0**; existing ten unresolved historical seed cases have a bounded retry scheduled. REACH public baseline remains **1,238**, with **no Scout-attributable public addition** verified this run. Historical originals completed **25 → 30**; remaining **163 → 158**. Source audit: all ten REACH index shards, six SPARK index shards, eleven Scout batch files and matching REACH detail shards checked; not every detail shard inspected. This is an evidence-backed disposition audit, not a claim of exhaustive expansion research.

## Hourly evidence audit — 2026-10-28 23:31 ET

Audit JSON: [REACH-SCOUT-2026-10-28-HOURLY-2331ET](hourly-run-audits/2026-10-28-2331ET.json). Primary mode **historical DataCite**, monthly queue **0**. Historical original seeds examined **14**: **12** individually disposed (**10** already in REACH, **1** new verified original dataset forwarded for human review, **1** ineligible grant/NOFO record no-action), **2** new bounded metadata/scope blockers due **2026-11-05 UTC**. Original-seed completions **30 → 42**, remaining **158 → 146**; **12** unresolved metadata blockers overall (prior ten plus two new), none due now; human metadata-needed escalations **0**.

New distinct GitHub human-review candidates by route: **Direct API 1** (Dryad dataset DOI `10.5061/dryad.b5mkkwhh9`, original historical seed); **API-seeded expansion 1** (final GMD article DOI `10.5194/gmd-18-7969-2025`, followed from software seed `10.5281/zenodo.15002615`); **Independent discovery 0**; **Metadata correction 0**; **Unclassified 0**. Both require human verification: the dataset's SPARK project attribution and the final article's overlap with an existing REACH preprint, respectively. They are **not approved or publicly published**. New immutable review batch: [2026-10-28-hourly-2331ET-datacite-original-and-expansion-001.csv](../scout-discoveries/batches/2026-10-28-hourly-2331ET-datacite-original-and-expansion-001.csv) (2 rows; run `REACH-SCOUT-2026-10-28-HOURLY-2331ET`). Original seed and expanded work are distinct identities and counts; the original software seed is already REACH `reach-000462`, the earlier preprint is `reach-000460`.

Source audit: all **10** REACH index shards (1,238 rows), all **6** SPARK index shards (578 rows), and all **11** pre-existing Scout batch files (47 rows) compared, plus relevant REACH detail shards. Audit **PARTIAL** because not every REACH detail shard was inspected and no private human decisions were available. Public REACH count **1,238**, **0** Scout-attributable public additions verified. 'Beyond direct API' means beyond the **captured historical DataCite source batch**, not a claim that the journal article could never be found through another API.
