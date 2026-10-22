# REACH Scout discoveries — public staging

This repository is a **human-reviewed staging channel**, not the official REACH output catalog. ChatGPT Scout proposes new dated discovery CSV batches on separate branches and opens pull requests. A human reviewer decides whether to merge each PR. Once merged, GitHub Actions validates all batches and refreshes the public manifest. Discovery Hub reads the manifest and places new findings in its *unreviewed* queue. **Nothing here automatically approves or inserts a record into REACH.**

## Contents

- `scout-discoveries/batches/YYYY-MM-DD-unique-run.csv`: append-only, exact 24-column Discovery Hub CSV. Existing batches must never be modified.
- `scout-discoveries/manifest.json`: verified SHA-256s, counts, paths and source run IDs.
- `scout-discoveries/tools/build_manifest.py`: batch schema and safety checks.
- `.github/workflows/build-scout-discovery-manifest.yml`: validates proposed batches in PRs and updates manifest on merge.

The manifest is publicly readable at:
https://raw.githubusercontent.com/PART-WPO/reach-scout-discoveries/main/scout-discoveries/manifest.json

## Daily Scout PR process

1. Research all available public sources for the current award investigation backlog, verifying funded workstream attribution and full REACH deduplication.
2. Save the detailed research report, exact 24-column discovery CSV and award-coverage ledger in ChatGPT Library `/REACH Scout`, preserving the registry and previous decisions.
3. Screen CSV for nonpublic information, personal emails, tokens, private Smartsheet IDs and notes. Publish **public source metadata only**; leave Candidate ID and investigator-email fields empty. If no new results, do not publish an empty CSV.
4. Create a new `scout/YYYY-MM-DD-run-ID` branch in this repository. Add a **new** `scout-discoveries/batches/YYYY-MM-DD-run-ID.csv`; never overwrite a previous batch or push directly to `main`.
5. Open a pull request with counts, funding sources, duplicate assessments, and research limitations. **Do not merge.** The repository owner reviews and merges.
6. After merge, GitHub Actions refreshes the manifest and Discovery Hub's `Sync from Scout` fetches new findings, without resetting earlier human decisions.

## Security and review

This repository is public. Do not upload private information, NOAA restricted records, PI email addresses, Smartsheet tokens or native private row IDs, API credentials, or human decisions. `main` should use repository rules requiring PR review before changes are accepted where available. Grant ChatGPT GitHub App access to this repository **only**, not `reach-dashboard` or `SPARK`.

`github-actions[bot]` may need permission to update `manifest.json` after PR merge. If a branch protection rule blocks the bot's update, include the regenerated manifest in each PR instead.

Discovery Hub v1.24 uses read-only GitHub GETs to this dedicated repo, with per-batch checksum checks and a separate import ledger. Human review in Discovery Hub and the Smartsheet insertion confirmation remain mandatory.
