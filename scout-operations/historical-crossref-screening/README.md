# Historical Crossref screening checkpoints (pilot)

This directory stores small, independently verifiable first-pass REACH screening records. The original `scout-operations/historical-crossref-triage.json` remains authoritative for original research dispositions, human decisions, and separate expansion-seed status. Never overwrite or delete it to speed up screening.

## Contract

- A checkpoint is `batch-NNN.json`, at most 100 unique DOI identities, with `schema: reach-scout-crossref-screening-batch-v1`, `source_manifest_sha256`, `reach_snapshot`, and `records`.
- Each record has `doi` (normalized lowercase DOI), `screening_status` in `CONFIRMED_IN_REACH`, `NOT_FOUND_IN_REACH`, `POSSIBLE_MATCH`, `reach_uid` (when confirmed), `evidence_urls`, `next_action`, and optional `scout_overlap`.
- A match must be supported by REACH index **and** detail/secondary identity evidence before confirmed. An index-only hit is POSSIBLE_MATCH. A missing index DOI is not proof of absence until details/secondary URLs are checked.
- Preserve the same source DOI and all 614 independent expansion seeds; no candidate staging, publication, or funding verification occurs in this layer.
- Each run edits only its target batch and commits it. No run should write a monolithic research ledger to store a first-pass screening result.
- The GitHub Action `historical-crossref-screening-coverage.yml` validates checkpoint batches, uniqueness, source membership, and creates `manifest.json` and `coverage.json`. Invalid input fails rather than silently overwriting conflicts.

The coverage counts are only authoritative for checkpointed, validated records. Existing legacy screening records must be migrated only after their identities and evidence are verified; do not assume prior claimed counts are correct. The generated manifest contains SHA-256 hashes of batch files. The REACH snapshot checksum must be recorded in each batch; the generator does not fabricate or certify that external checksum.
