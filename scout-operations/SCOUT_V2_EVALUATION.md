# Scout 2.0 — Independent 100-case quality benchmark

## What it measures
The first version of `scout-v2-benchmark-100.json` is a **frozen, auditable sampling frame**, NOT a claim of accuracy or recall. It contains 100 public DOI/source identities selected without human-derived true labels. Selection is stratified to make failure patterns visible, with the following target mix:

| Stratum | Count |
| --- | ---: |
| Strong existing REACH identities | 20 |
| Ambiguous title/version public identity | 20 |
| Index-negative original outputs | 20 |
| Preprint/version families | 10 |
| New monthly API originals | 10 |
| Historical DataCite cases | 10 |
| Independent discovery leads | 5 |
| Monthly related-output leads | 5 |

Two independently investigated biomedical project-attribution anomalies are included as **blinded negative-attribution test cases**, not preassigned labels. Human adjudicators should use live source evidence rather than Scout's own predicted results. The 100-case sample freezes upon first verified publication, so subsequent source refreshes cannot move the sample.

## How to run the evaluation privately
1. An authorized independent WPO reviewer opens the public sample and privately evaluates each DOI, current published/version identity, primary SPARK project and specific funded deliverable. Use source references independent of Scout's claimed disposition, including official publisher/repository, primary award, or SPARK project evidence.
2. In a **private spreadsheet** (NOT public GitHub), maintain `case_id`, `gold_label` and optional `reviewer_minutes`. Allowed private gold labels:
   - `EXISTING_IN_REACH`: same DOI/canonical version demonstrably cataloged.
   - `NEW_ELIGIBLE_WPO_OUTPUT`: distinct, officially available, same-project WPO-supported output not cataloged.
   - `NOT_WPO_ASSOCIATED`: independent source evidence demonstrates lack of the proposed specific WPO project linkage; not merely a missing acknowledgment.
   - `PREPRINT_ONLY`: no official final published version eligible for new-output staging.
   - `VERSION_AMBIGUOUS`: conflicting version or multiple identity records remain unresolved.
   - `INSUFFICIENT_EVIDENCE`: bounded research cannot establish a defensible gold disposition.
3. A second adjudicator should resolve disagreements before metrics are trusted. Do not copy private free-text reviewer comments, identities, personal data or Smartsheet row IDs into the public sample.
4. Once **all 100** cases have independent labels, run locally `python scout-operations/tools/score_private_benchmark.py --gold-private-csv <private_gold_file.csv>`. This prints **aggregate-only** duplicate precision, duplicate recall, false-duplicate rate, average documented reviewer minutes and unresolved-gold counts. The tool does not write or transmit private records.
5. Independently measure genuine new WPO output recall using a separately constructed **known-positive** sample of legitimate omitted outputs; this 100-case *source cohort* alone is not an exhaustive truth set for undiscovered research, so the reported `eligible_output_recall` remains `NOT_ESTIMABLE_FROM_CASE_CLASSIFICATION_ALONE`.
6. Release only aggregates with authorization. Do not assert 8/10 or 9/10 Scout accuracy, 20 weekly completed decisions or verified new public REACH outputs until this has actually been observed.

## Reviewer workload and decision throughput
20+ review decisions/week is the **design target**. Only signed verified private reviewer feedback can support counts of actual human decisions, and a public Scout candidate is not a verified Hub import. Maintain a separate private weekly time study so improvements can be assessed in reviewer minutes per accepted WPO output, not just number of API leads.

## Rollout safety
The sample does not create a candidate or alter any original status, DOI-seeded expansion, human decision, public REACH entry or private Hub. A current REACH snapshot is evidence but not a guarantee that a historical duplicate match or award link was correct at publication time.
