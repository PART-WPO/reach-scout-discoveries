#!/usr/bin/env python3
"""INFERRED: Assemble the owner-facing report from the offline dry run; no network or operational imports."""
import csv,json
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[1];P='scout-operations/analysis-v3/'
def read(n):return list(csv.DictReader((O/n).open()))
def c(n,key=''):
 p=R/n
 return f'{n}:'+str(next((i for i,l in enumerate(p.read_text().splitlines(),1) if key and key in l),1))
def s(key):return '`'+c(P+'import-summary.json','"'+key+'"')+'`'
a=json.loads((O/'import-summary.json').read_text());g=read('gold-candidates.csv');pilot=read('pilot-seeds.csv');w=read('workflow-safety.csv');rep=read('reselected-seeds.csv')
md=f'''# Owner report: evolve the evidence, replace fragmented scheduling state

INFERRED: Preserve the existing collection, validation, identity and public-staging components. Build one shared research ledger and scheduler around them. The import does not support carrying old aggregate statuses forward as completed discovery methods. This is an evolution of useful code and evidence, with a new scheduling contract; it is not a recommendation to discard history.

VERIFIED_SOURCE: The source snapshot is public repository `PART-WPO/reach-scout-discoveries`, commit `{a['source_commit']}`. The offline importer pins that commit and records the hashes of all {a['tracked_files']:,} original tracked files (`{c(P+'source-files.csv')}`; `{c(P+'build_analysis.py','BASE_COMMIT=')}`). All analysis deliverables belong under `scout-operations/analysis-v3/` on the local branch `analysis-v3-read-only`.

INFERRED: Read this report first, followed by `ledger-design.md`, `inventory-ownership.md`, `gold-candidates.csv`, `pilot-seeds.csv` and `scheduler-test-spec.md`. The large JSON/CSV files preserve row-level audit details for a developer; the recommendations here are for the project owner.

## 1. Inventory and overlaps

VERIFIED_SOURCE: The pinned repository has **{a['python_scripts_including_tests']} Python files including tests**, **{a['workflows']} GitHub workflows**, and **{a['tracked_files']:,} files overall** ({s('python_scripts_including_tests')}; {s('workflows')}; {s('tracked_files')}). `inventory.csv` includes every original asset, so state, memory and ledgers cannot be omitted because of an unexpected filename. `inventory.md` has individual cards for every Python file and workflow; `workflow-safety.csv` lists every workflow's literal commit/push commands and schedules. All static dependencies include file/line references.

INFERRED: The main overlap is ownership of the same work across original triage, candidate queues, mission previews, handoff state, expansion retry state, metadata blockers and generated decision rollups. Keep the distinct monthly/historical lanes, original-versus-related output distinction, version service, evidence cache and immutable publication records. Merge who decides what to work on, which methods are complete, and when blocked work may reopen. The exact grouped ownership map and retirement conditions are in `inventory-ownership.md`; per-file recommendations are in `inventory.csv`.

NOT_DETERMINED: A static inventory cannot prove every runtime reader/writer, outside agent, integration installation or manually edited state source. The dependency register labels source references and inferred read/write candidates, distinguishes unknown directions, and preserves computed-path operations in `code-io.json`. It does not claim that a workflow ran merely because it exists.

## 2. Proposed ledger

INFERRED: Use two logical tables. **Seeds** have one row per existing publication record and separate award-search, related-identifier, full-text-link and agent-review status objects. **Artifact leads** hold independently identifiable code/software/data, related seed IDs, evidence and one claim tier: **same-DOI award**, **supporting output of a named paper**, or **unverified**. Each method/lead stores `input_hash`, `attempts`, `blocker_class` and `retry_after`.

INFERRED: Skip the same canonical work/method/input hash across every lane and worker. Reopen only the method affected by changed evidence or policy. Preserve explicit version and duplicate relationships. A retry date permits a bounded availability probe, not another unchanged successful investigation. Save unknown legacy counts as null, and distinguish a seed selection, source observation, completed method, eligible lead, public proposal and human approval. Full fields, transitions, locking and examples are in `ledger-design.md`.

## 3. Dry-run import: decision numbers

| Measured item | Result and evidence |
|---|---|
| VERIFIED_SOURCE: Existing REACH publication records available as seeds | **{a['publication_seed_records']}** of {a['public_reach_records']:,} public catalog records. “Publication” is export Output Type 1, not a new certification that each is a final peer-reviewed article. {s('publication_seed_records')} |
| VERIFIED_SOURCE: Previously marked REACH expansion seeds in the existing graph | **{a['existing_graph_verified_reach_expansion_dois']} DOI nodes**, of which **{a['publication_seed_records_linked_to_existing_graph_seed']} publication rows** map through the strict import's public DOI/URL/record-ID associations. These are a narrower existing worklist, not an alternative count of the whole catalog. {s('existing_graph_verified_reach_expansion_dois')} |
| VERIFIED_SOURCE: Seed DOI resolution | **{a['distinct_resolved_seed_dois']} distinct DOI identities**; **{a['seed_records_without_resolved_doi']} seed rows** have no resolved DOI in this import and retain their public record UID/URL. Multiple DOI associations and repeated source records remain visible. {s('distinct_resolved_seed_dois')} |
| VERIFIED_SOURCE: Any reliably linked prior context | **{a['seed_records_with_any_importable_prior_context']} seeds**: {a['seed_records_with_importable_method_observations']} with explicit method observations plus {a['seed_records_with_context_only']} with original-state/selection context only. {s('seed_records_with_any_importable_prior_context')} |
| VERIFIED_SOURCE: Specific method observations reliably imported | **{a['seed_records_with_importable_method_observations']} seeds**, from structured official-source expansion reports. Observed scope is preserved, not upgraded to a completed method. {s('seed_records_with_importable_method_observations')} |
| VERIFIED_SOURCE: No linked prior work found by these import rules | **{a['seed_records_without_linked_prior_work']} seeds**. This is missing linked evidence, not proof they were never researched. {s('seed_records_without_linked_prior_work')} |
| VERIFIED_SOURCE: Complete four-method history reconstructed | **0 of {a['publication_seed_records']} seeds**. All {a['publication_seed_records']} lack a complete reconstructable four-method audit trail in this import. {s('complete_four_method_histories_reconstructed')} |
| VERIFIED_SOURCE: Recorded selections | **{a['explicit_recorded_selection_events']} distinct mission/pass events**, {a['selection_doi_track_rows']} DOI/track rows, {a['distinct_selected_dois']} distinct selected DOI identities. {s('explicit_recorded_selection_events')} |
| VERIFIED_SOURCE: Selected in more than one recorded event | **{a['distinct_dois_selected_in_multiple_events']} DOI identities**, including **{a['reselected_dois_matching_publication_seeds']} DOI identities mapping to {a['publication_seed_records_reselected_in_recorded_events']} publication seeds**. {s('distinct_dois_selected_in_multiple_events')} |

INFERRED: These counts answer two different migration questions. **465** seeds have useful linked prior context worth preserving; **11** support source-level method observations under the strict importer. **933** do not have complete four-method histories. It would be misleading to describe 465 as completed methods or 468 as never attempted. The evidence supports evolving the useful pipeline while replacing fragmented scheduling authority.

VERIFIED_SOURCE: The import matches primary publication DOI/URL, a unique existing NOAA IR DOI-to-canonical-URL association, or an explicit recorded REACH match ID/UID. NOAA IR shard hashes are checked. It does not join seeds by title or author. Method observations come only from explicit structured bounded-expansion source checks; narrative notes and aggregate statuses remain context. `legacy_scheduler_state` retains old attempt/cooldown fields without assigning them to an unsupported method (`{c(P+'build_analysis.py','# Existing NOAA IR')}`; `{c(P+'build_analysis.py','# Method attempts')}`; `{c(P+'seed-ledger.json')}`).

NOT_DETERMINED: Complete historical request hashes, every attempted source, actual method completion, unlogged missions, private reviewer decisions and the exact number of unchanged repeated investigations cannot be recovered here. Current mission/pass files are deduplicated by explicit event ID. Queue previews, schedules, graph refreshes, checkpoint revisions and DOI mentions are not counted as selections. The recorded recurrence count is a bounded observed count, not a lifetime total. The full Git history was not mined to manufacture execution events.

INFERRED: Records missing method state need a bounded migration review, with existing notes presented first. Do not rerun every method on all 933 records by default. Start with the isolated 40-seed pilot and measure newly required source work, reuse and human time before expanding.

VERIFIED_SOURCE: The new artifact table contains **{a['artifact_lead_rows']} rows**: 234 existing public code/data records retained at a conservative unverified *attribution* tier, plus two explicitly recorded supporting-paper dataset leads. Existing public membership is a separate fact from freshly verified output-level award evidence (`{c(P+'artifact-leads.json')}`; `{c(P+'build_analysis.py','for a in artifacts:')}`). No same-DOI award tier was invented from a catalog award column.

## 4. Frozen rediscovery evaluation and separate pilot

INFERRED: Freeze the confirmed control below, source hashes, expected artifact primary identity, scoring rules and policy version before testing. Keep the remaining title-derived candidates as a reserve until the relationship and version-family identity are checked. Do not silently convert all title matches into truth labels.

VERIFIED_SOURCE: The confirmed control is **reach-000066**, “Development of an Objective Low Flow Identification Method Using Breakpoint Analysis,” whose supporting code URL is exactly the primary URL of separate code record **reach-000079**, `https://github.com/chrisrac/objective_thresholds` (`{c(P+'gold-confirmed.csv')}`). Two other publication records have embedded code links but no separately matched artifact primary record under this exact-URL rule (`{c(P+'reach-public-projection.json','"reach-000014"')}`; `{c(P+'reach-public-projection.json','"reach-000016"')}`).

INFERRED: These are all {len(g)} candidate seed/artifact pairs under the direct-link or full-paper-title-in-artifact-title rules. Only the first is confirmed by the direct-URL rule. The CSV includes exact titles, URLs and source record citations for every pair.

| Candidate seed | Publication title | Existing artifact record | Evidence category |
|---|---|---|---|
'''
for x in g:
 md+=f"| {x['claim_label']}: {x['seed_record_id']} | {x['seed_title'].replace('|','/')} | {x['artifact_record_id']} | {'Direct matching primary/supporting URL' if x['claim_label']=='VERIFIED_SOURCE' else 'Title-derived reserve; relation needs confirmation'}; `{x['seed_source']}`; `{x['artifact_source']}` |\n"
md+='''
VERIFIED_SOURCE: The existing 100-case benchmark declares that human truth labels have not been collected and that it is candidate-identity-only (`scout-operations/scout-v2-benchmark-100.json:1`). It is not a verified artifact rediscovery gold set.

INFERRED: Check duplicated paper titles/IDs (`reach-000439`/`reach-001169`, `reach-000372`/`reach-001177`) and versioned artifact identifiers (`reach-000901`/`reach-000902`) before counting independent gold work families. They are visible candidates, not three asserted independent findings.

INFERRED: The proposed pilot below has **40 seeds**, ten in each stratum: resolved DOI with linked prior work; resolved DOI without linked prior work; no resolved DOI with multiple awards; and no resolved DOI with one/no award. Selection uses a deterministic UID hash. Exclude every gold candidate record, known overlapping DOI and gold-candidate award context. Do not use pilot results to tune rules on the frozen gold set. Full URLs and citations are in `pilot-seeds.csv`.

| Pilot seed | Publication title | Stratum |
|---|---|---|
'''
for x in pilot:md+=f"| INFERRED: {x['record_id']} | {x['title'].replace('|','/')} | {x['stratum']}; `{x['source']}` |\n"
md+='''
INFERRED: Score rediscovery as the fraction of the frozen, independently confirmed paper/artifact pairs that the method rediscovers with the correct primary artifact identity and relationship tier. Also report duplicate proposals avoided, unsupported same-DOI award claims, method reuse, source failures, actual source attempts and owner review time. Report code and data separately where the set permits. A one-pair confirmed gold set is a smoke control; it cannot support a credible broad performance estimate. Expand it only after reserve adjudication, then freeze a new version before the next evaluation.

INFERRED: **This measures rediscovery, not recall of outputs missing from REACH.** Unknown missing outputs are not in this denominator. Evaluation against existing REACH artifacts cannot establish how many unrecorded artifacts the system misses. Unknown artifact eligibility and private reviewer acceptance remain NOT_DETERMINED.

## 5. Scheduler test specification

INFERRED: `scheduler-test-spec.md` contains exactly 20 proposed cases and expected outcomes. They cover repeated/cross-lane DOIs, unchanged inputs, source/access/metadata failures, incomplete negative duplicate checks, existing artifact URLs, pending Scout proposals, verified and ambiguous preprint/final pairs, artifacts supporting funded papers without their own award, generic reused inputs, genuine novel leads, selective reopening, concurrent workers and incomplete legacy history. None of these scheduler tests is implemented.

## 6. Repository safety
'''
branch=json.loads((O/'branch-main.json').read_text());rules=json.loads((O/'rulesets.json').read_text());brules=json.loads((O/'branch-rules.json').read_text());bp=json.loads((O/'branch-protection.json').read_text())
md+=f'''
VERIFIED_SOURCE: At the saved anonymous API observation, `main` reports `protected: false`, protection `enabled: false`, and status-check enforcement `off` (`{c(P+'branch-main.json','"protected"')}`). Repository rulesets and effective rules for `main` both return empty arrays (`{c(P+'rulesets.json','"body"')}`; `{c(P+'branch-rules.json','"body"')}`). The detailed protection endpoint returns HTTP {bp['http_status']} (`{c(P+'branch-protection.json','"http_status"')}`). Observation times and public URLs are preserved in those files.

INFERRED: **Direct commits to main are currently possible for an actor with repository write permission**, based on the public branch/rules response and configured direct-push workflows. This analysis did not attempt a push, and does not establish any user's permission or bypass privileges. NOT_DETERMINED: administrator-only details hidden by the protection endpoint, organization policy not exposed in these responses, and future settings.

VERIFIED_SOURCE: **{a['workflows_with_literal_push']} workflows contain literal push commands.** Each is listed below with its exact source location and targeting evidence; this is configuration evidence, not a claim that all 40 executed successfully. The latest pinned source commit is authored by `github-actions[bot]` for the guarded handoff (`{c(P+'branch-main.json','"message"')}`).

| Automation | Configured push evidence | Target assessment |
|---|---|---|
'''
for x in w:
 if x['push_commands']:md+=f"| VERIFIED_SOURCE: {x['workflow']} | `{x['push_commands']}` | {x['interpretation']} |\n"
md+='''
INFERRED: Recommend a rule targeting `main` that requires pull requests, at least one independent approval, approval refresh after new commits, resolved review conversations, and successful existing privacy, schema, identity/version and relevant regression checks. Select required checks from actual stable check names rather than guessed workflow titles. Block force pushes and deletion; apply protection to administrators; restrict bypass to an explicitly reviewed emergency role. Give ordinary workflows read-only contents permission. A narrowly scoped publishing identity should open/update a generated-change branch and PR; human approval and passing checks should precede merge. Group related generated artifacts into one reviewed change and give the scheduler one canonical-work lease across workflows. These are recommendations only; changing permissions would require adapting the 40 direct-push workflows to prevent breakage.

## 7. Risks and decisions for the owner

| Area | Evidence and risk | Proposed boundary |
|---|---|---|
| Monthly harvesting | VERIFIED_SOURCE: Initialization starts new inputs as awaiting research and preserves prior state; a bot commit is not a reliable follow-on trigger (`scout-operations/README.md:43`). INFERRED: Superseded batches, date precision and incomplete source pages can cause omissions or duplicate intake. | INFERRED: Preserve monthly source receipts, exact publication window/date basis, checksums, pagination coverage and supersessions. Register all inputs before scheduling; avoid treating a successful empty page as a complete harvest. Keep monthly originals ahead of discretionary expansion without losing historical fairness. |
| Historical research | VERIFIED_SOURCE: Existing graph and triage split originals and expansion; the import lacks complete four-method histories (`scout-operations/historical-crossref-triage.json:4`; `scout-operations/analysis-v3/import-summary.json:1`). INFERRED: Old notes and status rollups can be mistaken for current checks, causing either repeated research or false completion. | INFERRED: Preserve notes, dates and their scope; reconstruct only needed baseline state. Use explicit method hashes and bounded retries. Measure completed distinct work separately from notes, previews and selections. |
| Duplicate checks | VERIFIED_SOURCE: The policy distinguishes an artifact's primary URL from a publication's supporting links (`scout-operations/SCOUT_OPERATING_POLICY_V2.md:117`). INFERRED: An incomplete negative scan, title-only merge, fork collapse or stale catalog can misclassify outputs. | INFERRED: Share exact public identity/version snapshots; verify primary artifact identity and code/data type. Fail closed on incomplete negative checks. Normalize safe URL equivalents without collapsing forks, subpaths, exact versions or related papers. |
| Preprint handling | VERIFIED_SOURCE: A DOI is not automatically a distinct intellectual work; earlier/final links govern updates (`README.md:59`). INFERRED: Final articles can be re-proposed or preprints wrongly treated as official final articles. | INFERRED: Keep explicit version evidence and a separate watchlist. Existing-work final versions use metadata review and preserve UID; independently citable software/data do not merge into the paper. |
| Metadata validation | VERIFIED_SOURCE: The operating contract specifies output-level funding, date conventions, canonical 24-column validation and unknown NOAA IR status (`scout-operations/SCOUT_OPERATING_POLICY_V2.md:12`). INFERRED: Missing awards, ambiguous dates and blocked sources can become invented certainty; source citations may identify reused input data rather than new study output. | INFERRED: Preserve the official source, observed time, content hash, parser version and field-level uncertainty. Separate paper-support from artifact-own funding. Do not fabricate DOI, date, award, artifact type or an IR FALSE from absence. |
| Human-review boundaries | VERIFIED_SOURCE: Inbox draft, public proposal, private import, signed decision, insertion and public catalog addition are separate events (`scout-operations/SCOUT_OPERATING_POLICY_V2.md:26`; `README.md:14`). INFERRED: Public status counters can be mistaken for human approval. | INFERRED: Research agents may prepare evidence and a focused question. Only authorized humans decide eligibility/parent attribution and final additions. Private decisions remain outside this public analysis; no output is automatically approved by the new ledger. |

HYPOTHESIS: A shared method ledger will reduce repeat research and improve distinct artifact lead yield. The 40-seed pilot should test this with actual source attempts and review time; repository structure and the recurrence count alone do not establish savings.

NOT_DETERMINED: True recall for outputs absent from REACH, private Hub import status, human acceptance rates, total uninstrumented research, complete historical request counts and the number of harmful unchanged retries.

INFERRED: The immediate decision is whether to accept the two-table contract and run a separately authorized pilot. This analysis makes the design and migration evidence reviewable; it does not activate a scheduler, change a schedule, publish a candidate or modify any source ledger.
'''
(O/'OWNER-REPORT.md').write_text(md)
print('Owner report assembled:',len(md),'characters')
