# Proposed two-table ledger

INFERRED: This is a design for owner review. The accompanying dry-run JSON/CSV files are new analysis artifacts, not live scheduling inputs. No discovery, publication or private-system action is authorized by a row in these tables.

## Table 1: publication seeds

INFERRED: A seed is one existing REACH publication record identified by its stable REACH UID. Keep source record IDs when two REACH rows appear to describe the same work. Share a canonical work key across those rows so repeated DOIs and preprint/final aliases cannot cause repeated method work. An artifact is a separate output, even when its supporting paper is already in REACH.

| Proposed field | Plain-English meaning |
|---|---|
| INFERRED: `seed_id`, `reach_record_ids`, `seed_url`, `title` | Stable identity and public record locators; a title is descriptive, never sufficient identity proof. |
| INFERRED: `canonical_work_key`, `doi_aliases`, `version_family_evidence` | Exact DOI or canonical primary URL; share verified aliases across source lanes. Record evidence before linking preprints to final articles. |
| INFERRED: `source_lanes`, `source_refs` | All monthly, historical and independent intake appearances, with file/line, source content hash and observation date. Preserve every appearance without creating another seed. |
| INFERRED: `input_hash` | Hash of normalized seed facts plus the policy version. This records the imported snapshot; method hashes below control reuse. |
| INFERRED: `award_search` | One method-state object for output-level funding research. |
| INFERRED: `related_identifier_sweep` | One method-state object for explicit DOI relationships and structured references. Record each source and scope; a reference-list scan does not establish a full relationship sweep. |
| INFERRED: `full_text_link_scan` | One method-state object for accessible article/manuscript data and code statements, links and supplements. Save article version, extraction version and content hash. |
| INFERRED: `agent_review` | One method-state object for a bounded synthesis of the captured evidence; this is research, not human approval. Save model/prompt/policy version and source hashes. |
| INFERRED: `legacy_scheduler_state`, `legacy_evidence_refs` | Preserve old attempts/cooldowns/dispositions in their original scope. An original-output terminal status does not complete any expansion method. |
| INFERRED: `lease_owner`, `lease_until`, `row_revision` | One worker claims a canonical work/method/hash combination atomically. Expired leases permit recovery without publishing twice. |

INFERRED: Each of the four method objects contains exactly one current `status`, plus `input_hash`, `attempts`, `blocker_class`, `retry_after`, `last_attempt_at`, `evidence_refs`, `result_hash`, `policy_version` and an append-only `attempt_history` inside the row. The history retains each attempt's ID, inputs, scope, time, result, source fingerprints and error. `attempts` counts actual starts for that method, not selections, schedules or graph refreshes. Legacy unknown counts remain null; they do not become zero.

| Proposed status | Meaning and next action |
|---|---|
| INFERRED: `NOT_DETERMINED` | Legacy method history cannot be reconstructed. Hold for one bounded baseline review; never label it never researched. |
| INFERRED: `pending` | Explicitly eligible work, with known inputs and no result for those inputs. |
| INFERRED: `running` | An unexpired claim exists; other workers skip it. |
| INFERRED: `observed` | A source-level observation was recovered, but the whole method was not proved complete. Preserve it and identify only the missing scope. |
| INFERRED: `complete_no_lead` | The documented method scope completed successfully and found no qualifying lead in that scope. This never means no output exists anywhere. |
| INFERRED: `complete_with_leads` | The method completed and its leads are in table 2. Leads still need identity, metadata and claim checks. |
| INFERRED: `blocked` | Work stopped for a documented technical/source problem; retain partial evidence. |
| INFERRED: `human_review_required` | A specific eligibility, relationship, identity or attribution question remains for a person. Unchanged automated reviews cannot reopen it. |
| INFERRED: `ineligible` | Supported reason excludes this method/input, with a reversible decision and provenance. |

INFERRED: Proposed blocker classes are `source_access`, `rate_limited`, `source_invalid`, `identity_ambiguous`, `version_ambiguous`, `metadata_missing`, `funding_unverified`, `relationship_unverified`, `legacy_method_history_unknown`, and `policy_conflict`. A blocker names a cause rather than an outcome. HTTP 403 is not evidence that no artifact exists.

INFERRED: A method input hash includes the canonical work identity, that method's source-content/availability observations, relevant REACH/Scout identity snapshot, award-rule snapshot, parser version and policy version. Agent review also includes the evidence bundle and prompt/model version. Exclude clock time, queue position, unrelated records and generated report timestamps. Changing a global queue must not invalidate every seed.

INFERRED: Before claiming work, look up `(canonical_work_key, method, input_hash)`. Reuse a completed result with that key. Skip a blocked result until `retry_after` and a relevant new availability observation or explicitly authorized new source changes its inputs. A due retry permits a small availability/conditional-fetch probe; it does not rerun an unchanged successful method. HTTP ETag/Last-Modified checks may establish changed inputs cheaply. Missing or unreliable headers require a documented source-content check. Store failed probes as source checks; do not count them as repeated full investigations. Persistent human/eligibility holds have no automatic retry date.

INFERRED: Set `retry_after` from the source's Retry-After when present; otherwise use bounded backoff appropriate to the recorded failure, with a cap and a maximum-attempt policy. These values are proposed policy choices, not measurements. After the cap, rotate to other work and ask a focused human question. A new substantive source can reopen only the affected method. No broad timer should relaunch unchanged completed work.

VERIFIED_SOURCE: Existing DOI metadata memory already distinguishes seven-day successes, six-hour failures and fresh preprint checks (`scout-operations/tools/research_memory.py:27`). The independent selector bounds missions to five distinct DOIs (`scout-operations/tools/select_independent_mission_candidates.py:27`). These are reusable components, although their current fields do not form a complete four-method history.

## Table 2: artifact leads

| Proposed field | Plain-English meaning |
|---|---|
| INFERRED: `artifact_id`, `artifact_identity`, `artifact_type` | Exact DOI or canonical repository/dataset URL; type is code, software or data, supported by metadata. Preserve version, fork and subpath distinctions. |
| INFERRED: `seed_ids`, `named_paper_dois` | A list of seeds and specifically named papers supporting the lead. One artifact may support several papers without becoming several outputs. |
| INFERRED: `claim_tier` | Exactly one of the three tiers below. This is about evidentiary attribution, not permission to publish. |
| INFERRED: `artifact_own_award_evidence` | Official exact-artifact-DOI award statement, source URL, full award string, content hash and observation time. |
| INFERRED: `relationship_evidence` | Explicit paper-to-artifact statement, source excerpt/locator, source hash and version. Topic, author and shared-award similarities are insufficient. |
| INFERRED: `identity_status`, `reach_matches`, `scout_matches`, `version_family` | Exact public duplicate checks, supporting-link versus primary-output match, ambiguous identities and known versions. |
| INFERRED: `input_hash`, `attempts`, `blocker_class`, `retry_after`, `evidence_refs` | Same reuse and uncertainty rules as seed methods. |
| INFERRED: `review_status`, `public_staging_reference`, `private_review_status` | Distinct research, public proposal and human-review events. Private status stays NOT_DETERMINED in this public-only analysis. |

| Allowed `claim_tier` | Required evidence and permissible wording |
|---|---|
| INFERRED: `same-DOI award` | The artifact's own DOI has official output-level WPO award evidence. An award on its paper does not satisfy this tier. “This artifact's DOI carries award X.” |
| INFERRED: `supporting output of a named paper` | Explicit paper/artifact relationship, including whether it is produced for the study or merely reused. “This is a supporting output of paper X; the artifact's own award is unverified.” |
| INFERRED: `unverified` | Identity, relationship or attribution is insufficiently supported. Keep a research lead without a WPO-funded-artifact claim. |

INFERRED: A human eligibility policy should decide whether supporting outputs can proceed to review without their own award. Do not discard that tier merely because an award field is empty, and do not silently promote it to same-DOI funding. Third-party input datasets and generic software dependencies need a distinct relationship role; their citation is not proof they were produced by the funded study.

VERIFIED_SOURCE: The saved Gulf Stream data-availability report names `10.5281/zenodo.4433147` and `10.5281/zenodo.5057616` as two supporting datasets while explicitly leaving their own awards unverified (`scout-operations/historical-crossref-phase2/2026-11-05-1426ET-gulf-stream-publisher-data-availability-seed-expansion.json:9`). The dry run preserves both in the supporting-paper tier, with attribution explicitly INFERRED from recorded source evidence rather than a fresh publisher check.

INFERRED: Keep raw API batches, immutable public review batches and signed/private human decisions outside these public research tables. The two tables store public references and status boundaries; they are not replacements for private human decision authority.
