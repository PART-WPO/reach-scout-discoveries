# Analysis v3 deliverable index

INFERRED: Start with [OWNER-REPORT.md](OWNER-REPORT.md) for the seven requested deliverables in plain English.

| Deliverable | Files |
|---|---|
| INFERRED: Inventory and ownership | [inventory-ownership.md](inventory-ownership.md), [inventory.md](inventory.md), [inventory.csv](inventory.csv), [dependency-references.json](dependency-references.json), [code-io.json](code-io.json) |
| INFERRED: Proposed two-table contract | [ledger-design.md](ledger-design.md) |
| INFERRED: Dry-run import | [import-summary.json](import-summary.json), [seed-ledger.csv](seed-ledger.csv), [seed-ledger.json](seed-ledger.json), [artifact-leads.csv](artifact-leads.csv), [artifact-leads.json](artifact-leads.json), [import-exceptions.json](import-exceptions.json) |
| INFERRED: Repeated selections | [reselected-seeds.csv](reselected-seeds.csv), [selection-events.json](selection-events.json) |
| INFERRED: Frozen evaluation proposal | [gold-candidates.csv](gold-candidates.csv), [gold-confirmed.csv](gold-confirmed.csv), [pilot-seeds.csv](pilot-seeds.csv) |
| INFERRED: Twenty scheduler test specifications | [scheduler-test-spec.md](scheduler-test-spec.md) |
| INFERRED: Repository safety | [workflow-safety.csv](workflow-safety.csv), [branch-main.json](branch-main.json), [branch-protection.json](branch-protection.json), [branch-rules.json](branch-rules.json), [rulesets.json](rulesets.json) |
| INFERRED: Public source provenance | [source-files.csv](source-files.csv), [reach-manifest.json](reach-manifest.json), [reach-public-projection.json](reach-public-projection.json) |
| INFERRED: Integrity verification | [validation.json](validation.json) |

VERIFIED_SOURCE: `build_analysis.py` reads the pinned repository snapshot and saved public export projection; `write_report.py` assembles the owner report; `verify_analysis.py` checks source preservation and deliverable consistency. They do not import operational repository modules or make network calls (`scout-operations/analysis-v3/build_analysis.py:1`; `scout-operations/analysis-v3/write_report.py:1`; `scout-operations/analysis-v3/verify_analysis.py:1`).

INFERRED: Reproduce offline from the repository root, in this order:

```text
python scout-operations/analysis-v3/build_analysis.py
python scout-operations/analysis-v3/write_report.py
python scout-operations/analysis-v3/verify_analysis.py
```

INFERRED: VERIFIED_SOURCE labels identify a source-backed fact about the pinned files or saved public responses. They do not certify that every historical narrative assertion was independently rechecked at its original external publisher. INFERRED labels identify interpretation/design choices. HYPOTHESIS identifies a proposal to test. NOT_DETERMINED explicitly preserves missing knowledge. Public candidate staging, private import, human approval and actual REACH additions remain separate.
