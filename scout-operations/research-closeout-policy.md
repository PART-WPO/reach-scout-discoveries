# REACH Scout research closeout — November 5, 2026

## Purpose
Turn bounded, substantive hourly research into a **reproducible public decision checkpoint**, without equating research evidence with a new output, a human decision, a Discovery Hub import, or a REACH addition.

## Evidence-to-decision pipeline
The GitHub Action `scout-research-decision-closeout.yml` runs on additions/changes to `historical-crossref-phase2/*.json` and on manual dispatch. It verifies the live public REACH source-manifest SHA against the checksum-verified REACH comparison cache, regenerates the source/queue evidence index once, and compiles DOI source-original research notes into `research-decision-cases.json` with individual file paths and SHA-256s. The existing `decision_pipeline.py` produces immutable per-DOI checkpoints. The companion `summarize_research_decisions.py` derives a reviewer-action report. It never creates private Hub entries or publishes Scout candidates automatically.

**Two research rounds** (initial plus one distinct follow-up) define the normal evidence budget. A bounded case with outstanding attribution, identity, or metadata questions routes to an evidence-backed **human assessment preview**, not another unbounded research loop and not an automatic private Hub import. Only reopen when specific new DOI, version, source or project evidence is available. Lack of a valid live snapshot is a technical retry/blocker, not a negative duplicate decision. Source notes may identify original versus related outputs; each DOI requires its own current identity and same-project funding checks.

**Preprints:** The original preprint DOI remains held from staging regardless of promising final-version leads. Recheck on the first of the month; any official journal DOI is a separate evidence-gated lead.

**Award scope:** Only exact SPARK primary Award Number(s) or independently corroborated same-project WPO support can establish project eligibility. A broad NOAA cooperative/umbrella award is insufficient. NOAA Institutional Repository DOI/URL matching is a duplicate identity aid; an ambiguous URL is not proof of a new output.

## Reconciliation without false completion
`reconcile_historical.py` and `reconcile_historical_crossref.py` now:
- Preserve original ledger terminal statuses and earlier human decisions.
- Exclude declared terminals lacking required verified evidence from **validated completion totals**.
- Publish distinct SHA-pinned exception files with DOI, declared status and exact missing proof fields.
- Preserve every historical Crossref original DOI as an independent expansion seed.
- Never silently treat a previously recorded private Hub import as observed.

The workflow fails closed on source SHA changes, missing source identities, unauthorized original disposition changes, and identity-index drift. Unsupported old completion claims should be repaired with genuine DOI-specific evidence, or escalated with a documented human decision, never by weakening validators or manufacturing funding.

## Metrics
`scout-operational-scorecard.json` is the single operational summary for phase-separated REACH screening, original research, seed expansion, public Scout feed staging, and **unverified** private review or public additions. The historical screening checkpoint manifest remains an immutable audit of first-pass labels; the actionable-routing report is the phase-2 priority source. Neither can replace the research completion ledger. No automated source-sync to private Smartsheet, REACH, or Discovery Hub is authorized.

## Human-controlled positive-control handoff
The existing flash-drought positive-control case and 24-column staging draft can validate the public identity, funding, metadata, and duplicate gates. A real end-to-end reviewer test still requires someone with authenticated private Discovery Hub access to observe a selected candidate's Sync to Scout, the parent-project verification, the staged metadata review, and explicit human action. Do not claim these were observed because a public CI test passed. Preserve prior human decisions and do not auto-insert into Smartsheet.

## Next-step priority
1. Review reconciliation exception queues (12 unsupported terminal declarations at the Nov 5 test checkpoint) and source-backed missing evidence.
2. Process bounded human-assessment previews and targeted identity checks; avoid redundant source loops.
3. Progress index-negative Crossref originals and separate DOI-seeded expansions while honoring current-month priority.
4. Keep public staging, private human review and public REACH additions as separate verified counts.
