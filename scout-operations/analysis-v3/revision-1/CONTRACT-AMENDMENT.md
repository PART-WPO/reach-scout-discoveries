# Accepted contract amendment: two campaigns and DOI resolution

INFERRED: This document supersedes the original report's recommendation to limit deterministic discovery to the 40-seed pilot. It adds the registry-side campaign without changing any existing ledger, workflow, policy or batch. The two-table structure is retained; no campaign is activated by these analysis files.

## Two campaigns, shared work identity

| Campaign | Unit and scope | Completion denominator |
|---|---|---|
| INFERRED: `reach_rediscovery` | Each of the 933 existing publication records, linked to a canonical DOI/URL work identity. Run applicable deterministic methods across the full population, reusing unchanged verified results. | All 933 record seeds, with separate counts for DOI-ready, DOI-resolution-held, each method's eligibility, attempts, completed scope and blockers. Do not count an unavailable DOI query as a negative result. |
| INFERRED: `award_registry_recall` | Every Crossref/DataCite result retrieved for each verified public primary SPARK award, regardless of whether it is already in REACH. Existing records fast-exit novelty review; exact unmatched records remain identity-review candidates. | First, all award/provider query units for the pinned primary-award universe, with complete pagination evidence; second, all returned distinct identities and their research dispositions. Keep these two denominators separate. |

INFERRED: The owner's revised scope is all outputs associated with primary awards since those awards started, through the campaign's captured as-of time. Use all available registry publication years per primary award rather than an arbitrary rolling ten-year cutoff. This avoids losing backdated/misdated deposits. Record official output dates and exceptions, and verify whether apparent pre-award outputs are reused inputs or incorrectly attributed records. A later monthly campaign advances the watermark; a periodic all-years reconciliation finds late deposits and amended funding metadata.

VERIFIED_SOURCE: The current public SPARK award shards include populated `Year Funded` values from 2015 onward and two primary rows with no year. The analysis checked all six award shard hashes and applies the repository's primary-only normalization to produce 711 distinct identifiers (`scout-operations/analysis-v3/revision-1/award-campaign-universe.json:1`; `scout-operations/analysis-v3/revision-1/public-primary-award-years.json:1`; `api-discoveries/tools/harvest.py:52`). This supports FY15 as the earliest populated year in this public snapshot; completeness of the historical award universe and start dates for the two blank-year rows remain NOT_DETERMINED.

INFERRED: Include blank-year primary awards and non-NOAA-format program identifiers. Do not use Related Award Number(s) as query seeds. Keep rejected placeholder strings and normalization evidence visible. The current proposal starts with 711 × 2 = 1,422 award/provider query units before pagination. This is not a request-count estimate or proof of complete recall.

## Table 1 extension

INFERRED: Generalize the seed table to `research_subjects`. Retain stable REACH record IDs where available, but use a canonical work identity for shared method work. Add `subject_kind` (`reach_publication`, `registry_publication`, `registry_artifact`, `registry_other_or_unknown`), `campaign_memberships`, `provider_record_ids`, `reach_record_ids`, `source_appearances`, `doi_resolution` and `campaign_run_refs`. One subject can belong to both campaigns without repeating its unchanged methods.

INFERRED: `doi_resolution` has its own status, evidence, input hash, attempts, blocker class and retry date. Accept an identifier from authoritative native metadata tied to the exact record; keep title-only search matches as candidates. A resolved DOI is not proof of peer-review status, uniqueness or funding. Preprint/final relationships and independently citable software remain explicit.

INFERRED: Preserve the four discovery method objects. An unresolved DOI sets the DOI-dependent sweep to `blocked` with `doi_unresolved`; URL/native-page methods may still run. No method is completed merely because another campaign already registered the subject. Shared canonical work/method/input-hash keys avoid cross-campaign duplicate requests.

## Table 2 extension

INFERRED: Keep artifact leads and the three claim tiers unchanged. Add `campaign_memberships`, `origin_query_refs`, `artifact_subject_id` and `named_paper_subject_ids`. A registry dataset can be a first-class registry subject and an artifact lead without becoming two discoveries. A supporting artifact without its own award remains in the named-paper tier; it is not silently discarded or promoted to same-DOI funding.

## Campaign progress without adding a third research table

INFERRED: Two research tables alone cannot prove query enumeration completeness: a successful zero-result award query creates no research-subject row. Keep a separate immutable campaign-run manifest as an operational receipt, not a third research/decision table. It must enumerate every award/provider/date-partition query unit, including zero-result, failed and unstarted units.

INFERRED: Each query unit records `campaign_id`, `run_id`, pinned award-universe/source hash, provider, exact query/filter, date semantics, parser/policy version, cursor/page number, response hash, observed advertised totals, records received, next cursor, terminal-page proof, errors, rate-limit headers, retry date and duplicate identities. A date-partition split must account for every partition; a page cap, stalled cursor or failed request remains incomplete. Store cursor/page receipts append-only and make resumption idempotent.

INFERRED: Report (1) fully enumerated query units / planned query units; (2) errored, unstarted and capped units; (3) distinct returned identities, including matched and unmatched REACH; (4) resolved and unresolved novelty/eligibility decisions; and (5) source/funding-coverage limitations. Enumeration coverage is measurable. Recall of outputs whose registry funding metadata is missing remains NOT_DETERMINED.

VERIFIED_SOURCE: Existing historical Crossref code validates shard coverage and rejects incomplete pagination, while the repository summary records 693 awards and 614 DOI identities. The DataCite historical summary records 761 awards and 188 DOI identities under a different historical run (`api-discoveries/tools/historical_crossref.py:21`; `api-discoveries/tools/historical_crossref.py:69`; `api-discoveries/runs/historical-crossref-41526471833.json:1`; `api-discoveries/runs/historical-datacite-2026-10-28.json:1`).

INFERRED: Import those returned identities and source receipts as historical context, but do not transfer their headline coverage to the current 711-award universe. Different award snapshots, normalization rules and missing retained per-page receipts prevent a verified current all-awards completion percentage. The new registry import explicitly leaves that percentage NOT_DETERMINED.

## Full deterministic population and agent pilot

INFERRED: Schedule applicable deterministic methods for all 933 REACH seeds, sharing results for canonical duplicate identities. Resolve missing DOIs first where possible; analyze remaining unresolved records separately, and keep native-URL methods eligible. Do not rerun unchanged successful work simply to achieve a population count. Respect provider rate limits and retain partial successes.

VERIFIED_SOURCE: This follow-up checked all 75 DOI-less records; native metadata resolved 12, while 63 remain unresolved. Two of the original pilot's DOI-less seeds resolved (`scout-operations/analysis-v3/revision-1/doi-resolution-review.json:1`; `scout-operations/analysis-v3/revision-1/pilot-strata-update.json:1`). The original pilot is preserved; its updated availability is reported separately.

INFERRED: Keep the 40-seed pilot for agent effort, false positives and human-review time. Analyze original DOI-ready, newly resolved and still-unresolved strata separately. Report method applicability and denominators so that unavailable relation queries do not look like missed artifacts. Run no agent work on the gold set to tune rules before evaluation.

HYPOTHESIS: A few thousand public requests may cover the deterministic campaign. Actual cost depends on pagination, source availability, full-text retrieval, duplicate reuse and retries; this analysis does not accept that estimate as measured fact. The follow-up observed HTTP 429 responses, reinforcing the need for pacing rather than unbounded parallel requests.

INFERRED: PR 2 remains on hold pending owner review of the artifact-first reference cases, version-family deduplication and the revised campaign contract. No ledger or scheduler has been activated.
