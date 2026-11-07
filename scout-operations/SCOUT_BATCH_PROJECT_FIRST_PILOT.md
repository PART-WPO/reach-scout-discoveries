# Scout batch-and-project-first research pilot (2026-11-06)

Status: **pilot protocol; not authorization to bypass existing decision pipeline**. The authoritative `SCOUT_OPERATING_POLICY_V2.md` and all immutable original/human decisions remain controlling.

## Per-hour operating sequence

1. Read and verify current main blob SHAs and internal SHA256 source references for the outcome registry, exact-DOI recovery queue, human-project referrals, impact report, preflight, current monthly source manifests, relevance priorities and scorecard. Check most recent Actions conclusions. If stale or inconsistent, repair/hold; do not issue proposals.
2. **Resolve ready follow-ups first.** Reuse successful exact-DOI DataCite→Crossref queue results; avoid repeat API calls. Recheck a human funding question only on materially new evidence. Do not recycle previously held cases as fresh investigations.
3. **Screen up to 20 distinct identities**, in this order: current-month primary-award originals and related leads; unresolved source-specific attribution/identity follow-ups; historical verified WPO REACH seeds for *project-specific* related-output searches; historical index-negative originals with primary-award context; DataCite exceptions; independent project-first leads. This is a screening ceiling, not a quota.
4. Give each screened case a recorded source lane, DOI/canonical URL, source manifest SHA, existing REACH/Scout identity state, preprint status, known primary SPARK award evidence (or explicit unknown), and screening decision. Classify:
   - **A / deep research:** verified WPO primary project/award association, or confirmed WPO REACH seed with a specific related-output lead and no duplicate.
   - **B / bounded check:** precise project context but unverified award, identity/version ambiguity, or source-specific recoverable metadata.
   - **C / defer:** generic NOAA affiliation, title similarity alone, prior evidence hold with no new source, preprint, or confirmed existing identity without a specific related lead.
5. Deeply investigate **up to five A/B cases**, preferably at least three if source availability permits, stopping on the initial check plus one truly independent follow-up. Do not replace exhausted A cases with low-quality C cases just to hit a number.
6. **Every investigated case** must yield an individually source-backed operational registry disposition or an explicit unlinked-source technical exception, with next action and separate original/expansion state. Commit evidence append-only, reconcile and verify successful Actions before counting outcomes. No public inbox proposal without existing 24-column validation and all referral safeguards; no private Hub/Smartsheet/REACH writes.

## Project-first candidate generation

Start from a verified SPARK **primary** `Award Number(s)` and a specific project. Search outputs using a bounded combination of project title, PI, organization and verified award. Match each discovered DOI or URL to its own author/version, project scope, funding evidence and full REACH+Scout identity. Never promote `Related Award Numbers`, broad NOAA grants, project-title similarity, or an index-negative result to WPO funding proof. When project linkage remains ambiguous after two distinct checks, record the exact missing authoritative project evidence and hold.

## Per-run scorecard

Report separately: screened (A/B/C), deep investigations, distinct-source follow-ups, new verified dispositions, previously held cases resolved, formal historical originals closed, seed expansions explored/completed, eligible public review proposals, verified private decisions, duplicates avoided, and technical failures. Calculate **useful disposition yield** as verified case dispositions divided by deep investigations; **review yield** as individually eligible new public proposals divided by deep investigations. Never call a screening-only defer a formal original or seed completion. Preserve a zero-target for unsupported WPO attributions, duplicate proposals and invented reviewer decisions.

## Pilot acceptance criteria

Compare seven days of pilot data with the prior one-case-per-run baseline. Advance only if SHA consistency, duplicate prevention, human-safe staging and original-versus-expansion accounting pass; at least some missions safely investigate multiple genuinely distinct cases; and useful yield improves without false WPO attribution. If an hour lacks enough eligible cases, report the actual count rather than fabricating throughput. Hourly scheduling remains seven days/week per the latest explicit user instruction; weekday morning briefing and first-of-month exception remain unchanged.
