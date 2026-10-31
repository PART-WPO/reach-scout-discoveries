# Authorized URRD Discovery-feed repair and prevention controls

**Date:** October 30, 2026 ET (GitHub commits October 31 UTC)

## Root cause and explicit authority
User directed a one-time URRD repair and permanent publication/attribution safeguards. The unmanifested October 30 20:29 ET CSV used `Original API seed DOI: 10.25923/t7t6-m677` where `build_manifest.py` required the standalone `Scout seed DOI:` field. The original free-form `Intake origin:` and `Scout verification:` strings also differed from the canonical historical DataCite format.

The prior invalid CSV was first archived **byte-identically** at:
`scout-operations/repair-archives/2026-10-30-hourly-2029ET-urrd-dataverse-recovery-001.csv.original.txt`
Original Git blob SHA: `5a832bfce7c9a3402db49fcdecc027e310d88c2e`. Original content SHA-256 according to the 20:29 mission audit: `5fd74af4781bfef6c6380e35c4ec437435b2a7add3b358c28709167c8b1f4d4a`. Archive commit `0b95eeef81443feb9cdace68306008e52ea6b595`.

The human-authorized one-time CSV change was committed at `a046a09c66d35d64f4a7fda793652e804052083c`. Exactly one of the 24 CSV fields changed: `Scout Discovery Rationale`. The repaired rationale now has exact standalone historical origin, verification, classification, route, evidence URL, `Scout seed DOI`, REACH snapshot, sources checked, funding basis, and related-output proof. Other 23 fields, DOI `10.7910/DVN/JWZEWF`, award `NA23OAR4590137`, date `2025-10-17`, review question and existing human decisions were not edited.

**Automatic manifest result:** GitHub Actions exclusively generated `scout-discoveries/manifest.json` at `2026-10-31T00:50:45Z`. The new entry `2026-10-30-hourly-2029ET-urrd-dataverse-recovery-001` has one candidate, source run `REACH-SCOUT-2026-10-30-HOURLY-2029ET`, and SHA-256 `bd1bac647d08ea577bc346b5d0cca135811fb31bdb8f9b9d21e33775a69a83b5`. All 21 previously manifested batch entries were independently compared to the pre-repair manifest and **none changed**. Published feed is now **22 validated batches / 69 candidates**.

## New permanent prepublication controls
- `scout-discoveries/tools/prepare_batch.py`: standard-library-only structured provenance writer producing exactly 24 CSV columns, canonical standalone labels and local check using the **same inspect_batch validation** as production; refuses overwrites.
- `scout-discoveries/tools/promote_inbox.py`: validates all *new* changed inbox drafts before writing a single published batch; exact bytes are promoted, idempotently, without overwriting published files. An invalid draft stays in `scout-discoveries/inbox/` and **cannot poison the published batch manifest**.
- `.github/workflows/build-scout-discovery-manifest.yml`: triggers on inbox changes, runs offline unit tests, validates and promotes valid inbox files, runs sole-owner manifest generator, and commits published batches, manifest and metrics atomically.
- `scout-discoveries/tools/rebuild_discovery_rollup.py`: independently reads each manifest-listed CSV byte-for-byte; verifies SHA-256, row count, and run IDs; derives route counts; preserves legacy no-route identities as unclassified.
- `scout-discoveries/tools/tests/test_pipeline.py`: unit fixtures for canonical seed label, missing-seed failure, full validator equivalence, SHA failure, successful/idempotent inbox promotion and atomic rejection when any draft invalid.
- `scout-discoveries/tools/CANDIDATE_DRAFT_FORMAT.md` and repository README explain the canonical structured JSON and new inbox-only procedure.

**First action-generated reconciliation:** `scout-operations/discovery-origin-rollup.json`, committed by GitHub Actions as `66915a5a0ebe2a6950fb1e64516e59a46bc718bb` after the tests/validation steps, reports the same 22 batches and 69 candidates: Direct API 5; API-seeded expansion 13; Independent discovery 5; Metadata correction 6; legacy unclassified 40. Summed category rows reconcile to 69. The separate impact calculation `beyond_direct_api_staged_review_candidates=18` is **staged research proposals**, NOT 18 reviewer-confirmed impacts. Public REACH count 1238 is retained as historical baseline, not claimed as refreshed.

## Scheduled task enforcement
Existing active weekday hourly mission, special first-of-month weekend mission and weekday morning briefing prompts were amended to use the canonical templates, new inbox draft path, GH Action promotion and live attribution rollup with distinct impact states. All three existing schedules were preserved, with no additional tasks or paid AI workers.

## Invariants and limits
- Published batches remain immutable; this one human-authorized URRD correction is the documented exception.
- Only GitHub Actions' `build_manifest.py` authors `scout-discoveries/manifest.json`. Neither Scout nor the metric script writes the manifest.
- The repository contains only public candidate staging; raw API batches are not forwarded unchanged.
- No human reviewer decisions, Smartsheet, SPARK, production REACH or approved-output state were altered.
- **Private Discovery Hub import NOT VERIFIED**. Feed-validated publication is not evidence of private Hub import, reviewer approval or a public REACH addition.
- Every future Scout-generated candidate must use unique new inbox draft, not a direct batch write.
