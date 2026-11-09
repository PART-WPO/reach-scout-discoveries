# Scout persistent research memory (v1)

## Scope

This phase reuses DOI metadata from **existing public independent lookup reports**. The new shared index at `scout-operations/research-memory/doi-cache-index.json` stores only SHA-256 DOI keys, source report and metadata hashes, provider status and observation time. It does **not** copy authors, investigators, abstracts or private reviewer records into the index. The existing source report is verified before any response is reused.

Both `lookup_independent_dois.py` and `lookup_independent_metadata.py` consult the index and commit the updated report plus index together. Previous observation timestamps never advance merely because a cached response was read.

| DOI metadata observation | Policy |
|---|---|
| Published DOI success | Reuse up to 7 days |
| Failed or missing DOI lookup | Retry after 6 hours |
| Preprint | Always refresh |
| Missing observation time, outdated parser policy, altered source SHA or response | Refresh; never treat as verified cache |
| New REACH / NOAA IR identity evidence | Always rerun shared identity check |

## Historical research memory

`scout-operations/research-memory/public-author-20261109-leads.json` retains the 32 source-fingerprinted author-pilot cases, but only as DOI hashes, public source-seed hashes and **nonterminal** research tiers. A future independent DOI check can retrieve previous work and resume investigation; no archived tier proves WPO funding or changes a private reviewer decision. No SPARK personnel, author names, or PI information are included.

The fixed 32-case pilot found one research-only other-award bridge, 25 lower-priority off-topic leads, and six deferred off-topic metadata retries. Those historical dispositions are context, not current funding evidence.

## Validate

Run `python scout-operations/tools/research_memory.py --rebuild` then `python scout-operations/tools/research_memory.py --check`. PR validation tests source SHA integrity, tampered metadata, cache expiration, failed-lookups, preprints, privacy and historical lead lookup. The first full independent lookup after deployment seeds new timestamps; legacy reports without timestamps are **not** presumed fresh.

**Boundaries:** No Discovery Hub import, reviewer approval, Smartsheet mutation, REACH publication, SPARK author lookup or automatic historical closure. This first version covers independent DOI metadata; historical DataCite/Crossref bulk APIs, citation graphs, full-text and GitHub release caches require provider-specific rules in a later phase. The independent 100-case gold-label benchmark remains uncollected.
