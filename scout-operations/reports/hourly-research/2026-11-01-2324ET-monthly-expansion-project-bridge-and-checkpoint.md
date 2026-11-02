# REACH Scout — October monthly API expansion follow-up
**Research time:** 2026-11-01 23:24–23:27 EST (2026-11-02 04:24–04:27 UTC)  
**Mode:** Monthly originals complete; independent API-seeded related-output research.  
**Human/REACH protections:** No human approval, private Hub import, REACH insertion, or Smartsheet edit observed or attempted.

## Source-of-truth intake accounting
- Active October primary-only API manifest: **13 DOI originals**, batch `2026-11-01-monthly-api-2026-10-primary-only-part001`; contaminated 26-record predecessor superseded.
- Existing monthly ledger: **13/13 research terminal**: **9** `staged_for_hub_import` in validated public Scout discovery feed, **4** `no_action` (two contradictory project funding, two already in historical concept/version review). These are not 9 private Hub imports or approvals.
- Coverage: **received 13; checked 13; missing_from_ledger 0; staged_for_hub_import 9; forwarded_to_hub 0**. Public Scout manifest **77 candidate rows in 32 active batches**, of which nine are October originals.
- Public REACH manifest index: **1,238 outputs in 10 shards**, no observed additions; actual private Discovery Hub import **NOT VERIFIED**. Reviewer must use **Sync to Scout** to import validated feed if not yet present.
- Monthly expansion ledger: **6 distinct DOI leads**; **3 already in REACH** and **3 still investigating**. No new expansion batch submitted this mission.

## New source-specific finding — NOAA grant proposal directly bridges two related 2026 articles
The NOAA Institutional Repository original award record [noaa:67218](https://repository.library.noaa.gov/view/noaa/67218) names **Kathryn Lambrecht and Lynda Olman** and primary award **NA21OAR4590208**, and describes the specific planned work: identifying stakeholder/community risk thresholds, surveying National Weather Service office partners, testing probabilistic hazard forecast visualizations and creating a communication toolkit. This is a stronger, project-specific corroboration than mere coauthor overlap for the two API-seeded articles:
1. [10.1177/10506519261455873](https://journals.sagepub.com/doi/abs/10.1177/10506519261455873), *Bridging the Gap Between Numbers and Experience* (publisher first online 2026-07-06).
2. [10.1145/3794916.3794919](https://pinakes.wacclearinghouse.org/article/376641), *Visualizing Probabilistic Forecast Information Around Community Risk Thresholds* (secondary index March 2026; exact publisher date not verified).

**Funding evidence tier:** credible same-project research bridge, **NOT verified article-level funding acknowledgment**. The 2021 proposal is not an independent statement that each 2026 paper was charged to this award. Neither was submitted to the Scout feed or private Hub.

## Duplicate/identity and native metadata checks
- Compared exact DOIs and distinctive titles against all **10 REACH index shards**, all **32 manifest-active Scout batch CSVs (77 rows)**, and **10 current inbox drafts**. **No exact DOI/title hits for the three open leads.** This does not cover every secondary link in all public REACH detail shards, private Hub, or all alternate versions; no full duplicate-clearance claim.
- Third lead [10.5281/zenodo.22758716](https://doi.org/10.5281/zenodo.22758716) is cited in [the original 10.1088/2515-7620/aeaad2 article's Data Availability](https://repository.library.noaa.gov/view/noaa/76692/noaa_76692_DS1.pdf). Its own dataset title, creators, DataCite created date, funding, and concept/version relation remain **NOT VERIFIED**; DataCite/Zenodo native access was unsuccessful in the browsing interface, which is **source inaccessible, not proof of no record**.
- Created [a read-only three-DOI metadata-checkpoint research lead](https://github.com/PART-WPO/reach-scout-discoveries/blob/main/scout-operations/research-leads/2026-11-01-2324ET-monthly-expansion-doi-checkpoint.json) to trigger the **existing** GitHub Actions native DOI metadata checkpoint. This is research metadata intake only; it is not a candidate or human action.
- Updated [the six-entry monthly expansion ledger](https://github.com/PART-WPO/reach-scout-discoveries/blob/main/scout-operations/monthly-expansion-leads.json) with the distinct NOAA grant evidence, index/feed comparisons, exact seed lineage and outstanding verification steps. Existing three already-in-REACH decisions unchanged.

## Actions/next decisions
- GitHub `scout-doi-metadata-checkpoint.yml` and monthly coverage validation were **in progress** at the last check. Read their **actual final conclusions and output** next mission; never assert a checkpoint succeeded just because it was triggered.
- For the two articles, obtain native Crossref metadata, article-specific grant acknowledgments or final-project deliverable documentation, and complete REACH detail/secondary-link version dedup. If article attribution remains unresolved after bounded research, present the specific question to a human via compatible validated Needs Investigation intake; no invented grant proof.
- For the Zenodo dataset, use native DataCite metadata to establish title, creators, created date, own funding, concept/version family and public file scope; retain blocked status if source remains inaccessible.
- Do not reopen terminal October originals without genuinely new evidence. Continue separate API-seeded expansion. No public REACH/SPARK/Smartsheet modifications.
