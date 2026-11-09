# Scout shared public identity and privacy-safe author pilot

**Status (November 9, 2026):** Code and public read-only preflight wired into
monthly original intake, all five source preflight lanes, independent DOI
lookups and independent DOI/GitHub metadata research. No automatic change to
existing Discovery Hub approval, private Smartsheet insertion, REACH or SPARK.

## Public identity before expensive research

The SHA-verified public comparison index covers REACH output IDs, DOI, URLs,
secondary links and current Scout public batches/inbox. The same
`identity_disposition.py` computes a read-only **public** decision and tracks
explicit preprint-to-published-DOI versions separately. Official NOAA IR
DOI-to-URL-to-REACH fallback requires matching normalized titles and a unique
public REACH record; otherwise it stays a bounded identity review.

- **Existing REACH:** no original new-output proposal, but keep independent
  DOI-seeded related output exploration.
- **Identical public Scout published+inbox mirrors:** a single existing public
  *proposal*, not proof of private Hub import or human approval.
- **Possible title/identifier/version conflict:** investigate; do not invent a
  duplicate or automatically reject a distinct dataset, software product or
  published article.
- **Original preprint:** hold for monthly first-of-month watchlist, including
  when a published sibling is known. Each final DOI undergoes its own checks.
- **Index-negative:** continue funding/metadata research, not proof of novelty.

For the full cross-mode read-only regression:
```bash
python -m unittest discover -s scout-operations/tests -p 'test_identity_disposition.py' -v
python -m unittest discover -s scout-operations/tests -p 'test_ir_reach_identity.py' -v
python scout-operations/tools/unified_source_preflight.py
python scout-operations/tools/identity_disposition.py --benchmark
```

## Public author seeding — no SPARK personnel fields

A **manual-only** pilot is available as GitHub Actions:
`Scout public REACH author-seed pilot (manual, read only)`.
Supply an **exact primary award** already represented in public REACH
publications. The pilot:

1. Searches checksum-verified **public REACH output** records for an exact
   award. It never reads authors, investigators, collaborators or any PII from
   SPARK (nor any SPARK record, at all).
2. Uses publicly recorded DOI and, where necessary, checksum-verified NOAA IR
   DOI-to-record links to identify existing REACH publications.
3. Queries Crossref by exact DOI. Only an official **journal article** whose
   public Crossref title agrees with its REACH catalog title is a source for
   transient authors. REACH `Principal Investigators` may be abbreviated
   citations (e.g. "Smith et al."); these are never parsed as author names.
4. Performs **bounded** public author-based Crossref searches. Names exist
   only in memory; they are not printed or committed. Artifacts contain DOI,
   title, public REACH seed UID, seed DOI and explicit **funding unverified**
   fields. New leads cannot be added to a Discovery Hub queue from this pilot.
5. If no qualifying public REACH publication exists, produces **zero author
   seeds**. Scout should use award, title, citation, dataset, code and other
   non-personal discovery rather than reintroduce SPARK personnel.

Manual pilot caps: 5 public DOI seeds, 4 transient authors and 5 result records
per author. The optional output artifact is retained for 2 days and is
**NOT** a public Scout candidate feed. It is intentionally not an hourly
or monthly scheduled action.

## Independent 100-case benchmark: private human truth

`scout-v2-benchmark-100.json` contains 100 public DOI identities and source
predictions, **not** independent evidence of ground truth. A test-only
100-case replay or all-lane source preflight cannot establish precision,
recall, false exclusion rate or reviewer burden.

An authorized reviewer may use the following commands **locally**, with a
directory outside any public GitHub checkout and restricted ACLs:

```bash
python scout-operations/tools/score_private_benchmark.py \
  --create-private-template /PRIVATE_REVIEW_DIRECTORY/scout_gold.csv
```

This creates 100 rows with public case IDs, DOI and strata, but no predictions,
gold labels or reviewer names. The file is created exclusively with private
mode (0600 on POSIX). Do **not** add it to Git, an artifact, log, Hub,
SPARK, or a public repository. Reviewers independently verify eligibility,
version, DOI/URL identity and project funding; supply one supported
`gold_label` per record:

`EXISTING_IN_REACH`, `NEW_ELIGIBLE_WPO_OUTPUT`,
`NOT_WPO_ASSOCIATED`, `PREPRINT_ONLY`,
`VERSION_AMBIGUOUS` or `INSUFFICIENT_EVIDENCE`.

Only after all 100 independent labels are complete:

```bash
python scout-operations/tools/score_private_benchmark.py \
  --gold-private-csv /PRIVATE_REVIEW_DIRECTORY/scout_gold.csv
```

The script prints **aggregate-only** estimates and refuses any gold-label
file located inside the public repo. Reviewer timing is optional. Aggregates
must be reviewed for disclosure before separate publication; no private
reviewer records or DOI-level gold labels are uploaded by this code.

**Strict boundary:** public GitHub batches, source metadata, or Scout
recommendations never attest private Discovery Hub imports, approvals,
Smartsheet inserts or verified new public REACH additions.
