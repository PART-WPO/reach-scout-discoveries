# Policy and inventory review contract

INFERRED: This is the policy/inventory review scope. It contains documentation, the source inventory and public safety evidence. It does not contain an imported research ledger, scheduler implementation, workflow change or activation. The ledger/research-evidence review is separate and remains on hold.

INFERRED: Accept two research tables. Table 1 holds canonical research subjects and four independent discovery-method states: award search, related-identifier sweep, full-text link scan and agent review. Table 2 holds artifact leads and one claim tier: same-DOI award, supporting output of a named paper, or unverified. Store input hashes, actual attempt history, blocker class and retry dates. Share work identity across campaigns and source lanes; reuse unchanged successful results.

INFERRED: Table 1 must cover two campaigns: existing REACH publication rediscovery and award-driven registry research. A registry record without a REACH match is still a first-class research subject. Its appearance in Crossref and DataCite must not create two independent research subjects or two discoveries. A registry artifact can also reference its artifact-lead row without being counted twice.

INFERRED: The registry campaign covers public primary SPARK awards from their earliest verified year through the captured as-of time. Search all available registry years for those awards, avoiding an arbitrary ten-year cutoff and retaining anomalous pre-award dates for review. Include valid primary identifiers with unknown years; never substitute Related Award Number(s) for primary query awards. Current-source year evidence and query enumeration belong to the separate ledger/evidence review.

INFERRED: Keep an immutable campaign-run manifest as operational evidence alongside the two research tables. It must track every award/provider query unit, including successful zero-result units, failed units and unstarted units; exact query/filter, source hashes, page/cursor receipts, terminal-page evidence, retry dates and source totals are required. Two research tables alone cannot represent a zero-result query. Report query enumeration completion separately from the disposition of returned identities and from unknown real-world recall.

VERIFIED_SOURCE: Existing harvest code filters primary awards and verifies public SPARK shard hashes; historical Crossref scanning checks pagination and complete shard coverage (`api-discoveries/tools/harvest.py:82`; `api-discoveries/tools/harvest.py:98`; `api-discoveries/tools/historical_crossref.py:21`; `api-discoveries/tools/historical_crossref.py:69`).

INFERRED: Add a separate DOI-resolution state with exact identity evidence, input hash, attempts, blocker and retry date. Native DOI metadata tied to an exact record may resolve an identifier; title-only results remain candidates. A resolved DOI is not proof of publication status, funding or novelty. Unresolved DOI-dependent methods stay blocked; native URL methods can remain eligible.

INFERRED: Schedule applicable deterministic methods across the full REACH seed population. Use the forty-seed agent pilot for agent time, false positives and human-review burden; keep previously resolved, newly resolved and unresolved strata separate. Do not count a blocked query as a negative result. Do not repeat a successful unchanged method to fill a mission or meet a population count.

INFERRED: Build the evaluation reference set from existing code/data records toward explicitly named papers. Keep citation-only and title-only associations outside positive labels until reviewed. Group version/work families and multiple papers per artifact before freezing reference cases. Owner ratification precedes treating the proposed source-reviewed cases as a frozen benchmark. This measures rediscovery, not recall of outputs missing from REACH.

INFERRED: A supporting artifact without its own award can be retained for human eligibility review. Do not promote the paper's award into same-DOI artifact funding, and do not discard a plausible study output solely because its own award field is absent. Distinguish newly produced study outputs from third-party input data and software dependencies.

INFERRED: Retain useful source collectors, metadata caches, identity/version checks, privacy/schema validators and immutable batches. Merge independent queue, cooldown and method-completion authorities behind one canonical work ledger. Derived scorecards and previews are views, not independent evidence that research completed. The complete per-file source inventory is in `../inventory.csv` and `../inventory.md`.

INFERRED: Consolidate routine data publication into one reviewed publishing stream, or separate generated data from protected code/policy. Verify actual GitHub plan capabilities before depending on a path-scoped bot permission. A branch-wide bypass is not a data-folder-only authorization rule. See `BRANCH-SAFETY-REVISION.md` for current public documentation and public PR identity checks.

INFERRED: Research proposals, public staging, private import, human decisions, insertion and public catalog additions are separate events. No public analysis grants permission to approve artifacts, edit private decisions or write to REACH, SPARK, Discovery Hub or Smartsheet. No such writes or scheduler activation are part of this review.
