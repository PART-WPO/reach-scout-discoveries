# REACH Scout — 2026-11-01 ~15:28 EST monthly preprint funding and linked-output investigation

## Source-of-truth checkpoint
Read current `api-discoveries/manifest.json`, `scout-operations/monthly-triage.json`, `scout-operations/coverage.json`, and `scout-operations/active-workstream.json` first. Active October batch is **2026-11-01-monthly-api-2026-10-primary-only-part001**, 13 DOI cases. Coverage 13 received / 0 closed / 0 missing, 0 errors; workstream monthly_api_triage/additional_evidence_research. Superseded 26-row contaminated batch excluded. Earlier 1,238-row REACH index / 68 active Scout exact screens not repeated.

## Original monthly case: 10.5194/egusphere-2026-5876 — material new evidence
Independently read the **eight-page original EGUsphere preprint PDF**, not just the abstract: https://egusphere.copernicus.org/preprints/2026/egusphere-2026-5876/egusphere-2026-5876.pdf .

- Page 6 acknowledgment explicitly states NOAA Weather Program Office **Social Sciences Program grant NA21OAR4590208**. This is direct source-specific funding evidence, previously missing.
- Page 1–2 authors describe their NOAA WPO-funded research on weather-hazard visualization, community commonplaces, surveys of five western NWS forecast-office audiences and follow-up A/B testing. The PDF explicitly connects the reported bot-response analysis to that study.
- SPARK **spark-000246** has literal PRIMARY Award Number(s) **NA21OAR4590208**; the full project description explicitly plans community commonplaces/risk-threshold research, NWS-partner/public surveys, forecast-visualization testing, and rhetorical tools. This makes the same-project link **strongly corroborated by primary grant + exact study methods and aims**, rather than merely thematic similarity. https://github.com/PART-WPO/SPARK/blob/main/agent-data/index/part-003.csv and https://github.com/PART-WPO/SPARK/blob/main/agent-data/details/part-020.csv .
- Publisher date is **2026-10-22**; type **Preprint** (under review for Geoscience Communication). Do not label it a final journal publication or infer an unobserved final DOI.
- Page 6 expressly states **"No code is available"** and **"No datasets are available."** The cited general-purpose Orange text-mining application is reused software, not a newly created funded code output.

## Evidence-backed research expansion
The preprint's references identify three concrete **distinct** same-project research products, but these are NOT new output counts without dedup/funding checks:
1. **10.25923/k9kh-y971**, *Tailoring probabilistic information to community needs: A rhetorical CRIB sheet* (NOAA Technical Memorandum, 2025), is **ALREADY in public REACH as reach-000821** under primary award NA21OAR4590208. Verified in `reach-dashboard/agent-data/details/part-097.csv`; NOAA IR https://repository.library.noaa.gov/view/noaa/71353 directly acknowledges WPO NA21OAR4590208. This is an existing related output, **not** a new candidate.
2. **10.1177/10506519261455873**, *Bridging the Gap Between Numbers and Experience: Identifying Community Risk Thresholds in Extreme Weather Communication* (SAGE Journal of Business and Technical Communication, first online 2026-07-06), is a **related publication lead**, not a duplicate of the October bot-response preprint. Publisher: https://journals.sagepub.com/doi/abs/10.1177/10506519261455873 . Exact DOI code search of REACH and active Scout repository yielded no hits; this is **not** a complete REACH index/detail or award-eligibility determination. Specific publication grant acknowledgment remains unverified.
3. **10.1145/3794916.3794919**, *Visualizing Probabilistic Forecast Information Around Community Risk Thresholds* (Communication Design Quarterly, 2026), is another **related publication lead**; bibliographic identity confirmed by https://pinakes.wacclearinghouse.org/article/376641 . Exact DOI code search of REACH and active Scout repository yielded no hits; funding attribution and complete dedup remain unverified.

Additional same-primary-award public REACH records `reach-000820` (2023 probabilistic information visual communication publication) and `reach-000822` (2023 forecast-graphic template) were observed in the same `part-097.csv` detail shard. They are existing research products, **not** fresh findings.

## Disposition / next
Update the **existing** monthly DOI ledger entry for `10.5194/egusphere-2026-5876` with this evidence. Retain status **needs_more_research** because comprehensive secondary-link/preprint-version REACH dedup and any future final publication DOI relation are not complete. The two older article leads require separate primary-project funding and duplicate checks before any independent new-output proposal; do not insert them as monthly API original cases or automatically stage them.

**No** new inbox candidate, Discovery Hub import, human approval, public REACH addition, or existing record modification. Preserve retired related-only award correction proposals, Great Lakes provenance, immutable batches, monthly-first workstream and current special month-start schedule.
