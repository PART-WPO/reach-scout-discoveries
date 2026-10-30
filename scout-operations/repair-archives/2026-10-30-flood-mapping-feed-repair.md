# Authorized one-time repair — October 30, 2026

## Authority and scope
The human reviewer explicitly authorized a one-time, documented replacement of the invalid `2026-10-30-hourly-1329ET-independent-flood-mapping-001.csv` after retaining an exact original archive. This is an exception **only for this unmanifested failed batch**; the normal immutable-batch rule remains effective for all other records.

## Original preserved before amendment
- Original Git blob: `bcb7a886b8d48fc399c317c5db5ca4b73a5d4c37`
- Original SHA-256 (exact UTF-8 content): `97905d8908bcfca04cff68b5cf54e8635e3660184279e2a9fc01ca996deb0402`
- Byte-identical archive: `scout-operations/repair-archives/2026-10-30-hourly-1329ET-independent-flood-mapping-001.csv.original.txt`
- Archive commit: `3ca426451ba99fe857550de99b75d26bd10bb2e5`
- The archive is outside `scout-discoveries/batches/`, so the validator does not publish a duplicate batch.

## Minimal in-place correction to formerly invalid file
- Repair commit: `3531bae5f9fd2012b655b5c8ceced4d86b95f5a1`
- Corrected CSV: `scout-discoveries/batches/2026-10-30-hourly-1329ET-independent-flood-mapping-001.csv`
- Each of the same two candidate rationale fields changed as follows:
  1. `Scout classification: A NEW CANDIDATE` changed to `Scout classification: NEW CANDIDATE`.
  2. Added `Scout discovery path evidence: https://...` with the actual article publisher URL (Nature or IEEE, respectively).
  3. Added `Scout discovery method: ...` describing documented SPARK award-centered research and source comparison.
- No other CSV field changed. Header remains exactly 24 columns, candidate count remains two, DOI/award/date/title/source-run values are unchanged, no original candidate or reviewer identity was overwritten.

## Manifest and data-integrity verification
- GitHub Action owns the manifest; Scout did **not** edit, create, or compute `scout-discoveries/manifest.json` by hand.
- Fresh main-branch manifest reports generation `2026-10-30T23:48:00Z`, 21 batches and 68 review proposals (previously 20 / 66).
- The restored batch ID is listed with `record_count: 2` and source run `REACH-SCOUT-2026-10-30-HOURLY-1329ET`.
- Independent SHA-256 calculation of the reread corrected exact UTF-8 CSV content: `7c510c57c737c342841d4fc7e2c8f62a63f7b6738743e1493134596059589271`; matches the fresh manifest.
- All 20 prior manifest entries were compared with the previous GitHub manifest commit (`a6d5c11d92d3ba7f5bb32600c59acf72fe594e73`) and are unchanged; exactly one new entry is present.
- The SHA-256 implementation was self-tested using the standard `abc` test vector.
- Independently checking the GitHub Actions job conclusion was not possible through the available connector; nevertheless fresh published manifest contents and exact CSV digest agree.

## Human-review boundary
These two outputs are **feed-verified and available for public feed ingestion**. There is no observation that the private Discovery Hub has imported them, processed a reviewer decision, added them to Smartsheet, or changed public REACH; those states remain **NOT VERIFIED**. This repair does not authorize any approval or further immutability exceptions.
