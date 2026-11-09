# REACH Scout: Evidence Evaluator + Decision Compiler (read-only pilot)

## Purpose

Translate existing source-backed research into an actionable **research disposition** rather than generating additional open-ended research notes. This is not a new automatic Discovery Hub approval system or a substitute for the existing authoritative publication, duplicate, funding, review, and 24-column staging gates.

Inputs: current SHA-verified source preflight, existing research outcome journal, and the 19 annotated historical research decision cases with their individually pinned source files. Coverage target at the time of pilot launch: 34 distinct public research identities and 52 accumulated note events. The pilot reads the same previously recorded research; it does **not** conduct new external searches or reclassify the entire 827-source intake corpus.

Generated artifact: `scout-operations/reports/evidence-action-pilot/latest.json`.

## Evidence Evaluator

Each DOI or publicly recorded code URL receives an evidence-gate assessment:

1. **Public identity**: existing REACH, existing published Scout queue, recorded public no-action, possible version collision or not yet fully identified. A confirmed original publication already in REACH may still be an eligible related-output *expansion seed*.
2. **Official publication**: preprint vs previously documented publisher release vs unknown. Preprints must remain on the monthly watchlist. An older source claim of publication is **not** a fresh publication check.
3. **Exact WPO project funding**: explicit same-project primary SPARK proof, contradiction or missing corroboration. A 459/432 grant pattern, contributor similarity, or topic match is not positive project evidence.
4. **Required metadata and secondary identities**: documented verification vs unresolved work. A missing source or API access failure is not a negative finding.
5. **Contradictions and technical failures**: independently expose contradictory grant/source flags and exact metadata retry needs.
6. **Related output status**: a related publication, dataset or code URL is evaluated as a separate output and never inherits its parent's verified funding or identity.

The evaluation includes immutable source-note hashes and bounded source URL pointers. It does not copy investigator names, author lists, collaborator details, or private reviewer records.

## Decision Compiler

The compiler produces **exactly one research next-action route per distinct identity**, an accountable owner, a specific action, and a trigger for further work. Routes include preserving verified REACH originals while keeping expansion open, preprint monthly watchlist, retaining already staged public candidates, preserving a recorded no-action, a specific project contradiction hold, a sourced bounded question for human judgment, one exact metadata retry, an evidence-change-only hold, and a one-gate bounded research task.

Research resolution and formal publication closure remain distinct. A "bounded evidence hold" means stop repeating generic searches without material new source evidence. It does **not** mean that the historical original, expansion, reviewer decision, private Hub state or REACH publication is completed. Similarly, one actionable human question is a **proposed** assessment request, not a created Discovery Hub case or an instruction for the reviewer to justify the response.

All outputs are reviewed by a separate, deterministic adversarial gate-check that vetoes any attempt to route a preprint into new output staging, ignore verified REACH identity or explicit project contradiction, ask an unsupported human question, or claim a reviewer-ready source without required publication, identity, metadata and same-project funding checks.

## Testing and review

1. Run `python -m unittest discover -s scout-operations/tests -p 'test_evidence_action_pilot.py' -v`.
2. Generate `python scout-operations/tools/evaluate_research_to_action.py`.
3. Verify `python scout-operations/tools/evaluate_research_to_action.py --check`.
4. Inspect **every** route and the source SHA, especially preprints, previous public Scout staging, project-funding conflicts, other-award/Cooperative Institute cases, and the two previously recorded bounded human questions.
5. Sample both held and research-ready classifications against primary source evidence before authorizing any runtime integration. Measure whether human reviewers would consider the next-action output useful and whether the compiler avoids missed WPO outputs.
6. Keep original/expansion status ledgers, review-feed proposals, private Discovery Hub, Smartsheet, public REACH, hourly mission prompts and existing automations unchanged during pilot testing.

## Measuring effectiveness

Track proportion of prior research identities receiving a **specific next action** (not a claimed new proposal); explicit reopen triggers; prior repeated-research loops that would be suppressed; legitimately actionable candidate proposals; source-backed human questions; false holds and missed eligible outputs. Any change in reviewer-ready conversion must be compared against independently verified case labels, never inferred from a larger number of disposition categories.

A strong result would not necessarily increase the number of public Scout proposals. It could reveal that several cases are reasonably resolved as bounded attribution holds or documented existing outputs, freeing research cycles for independent DOI expansion.

## Privacy and limitations

All action recommendations are read-only, GitHub-public-only and use previously recorded DOI/source evidence. The pilot cannot see private Hub imports or human approval decisions. All published outputs state `private_hub_imports: NOT_VERIFIED`, `human_approvals: NOT_VERIFIED`, and zero actual public reviewer proposals or REACH additions. No automated GitHub-to-Smartsheet or Discovery Hub handoff is enabled by this pilot.

Because the evaluator relies on structured notes and older snapshots, it may recommend a further source check even when the publication would ultimately qualify. Treat these as **triage decisions**, not definitive funding or publication findings. Future phase: use a manually adjudicated positive/negative control set to calibrate decision accuracy, especially cases where exact DOI evidence exists but was not yet carried into standardized structured fields.
