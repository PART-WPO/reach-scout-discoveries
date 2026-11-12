# Follow-up to the owner's six review points

INFERRED: Accept the two-table contract with the two-campaign and DOI-resolution extensions in `CONTRACT-AMENDMENT.md`. Replace the original small-pilot-only deterministic recommendation: applicable deterministic methods cover all 933 seeds; the 40-seed pilot measures agent work and review burden. The original analysis files are preserved. This follow-up does not activate the full deterministic sweep or registry sweep.

## 1. Artifact-first gold rebuild

VERIFIED_SOURCE: The follow-up started from every one of the 234 existing code/data records. It observed official registry metadata for 105, author READMEs for 71 and native pages for 38; 20 records had an unavailable/unclassified source outcome (`scout-operations/analysis-v3/revision-1/revision-summary.json:1`; `scout-operations/analysis-v3/revision-1/artifact-side-review.json:1`).

VERIFIED_SOURCE: Artifact-side evidence produced 38 candidate paper/artifact pairs involving 26 artifacts. Source review supports 10 proposed reference pairs involving nine artifacts: four exact IsSupplementTo relations and six clear author/native-documentation relationships. The previous one-pair control is among these source-reviewed cases (`scout-operations/analysis-v3/revision-1/gold-rebuild-summary.json:1`; `scout-operations/analysis-v3/revision-1/gold-source-reviewed.csv:1`).

INFERRED: These are source-supported control proposals, not a human-adjudicated benchmark. The remaining 28 pairs stay unverified candidates; generic citations, bibliography entries and title similarity do not become positive truth labels. Ratify pair identities and relationship roles, group duplicate version/work families, freeze expected identities and source hashes, and then evaluate. Count the nine independent artifacts separately from the ten paper/artifact pairs so one code repository supporting two papers cannot inflate artifact rediscovery.

NOT_DETERMINED: Human adjudication and approval of the new reference set. The set has not been activated as a frozen benchmark. This measures rediscovery, not recall of outputs missing from REACH.

## 2. The two embedded code links

VERIFIED_SOURCE: The current public REACH manifest matches the earlier fully projected export. Neither checked code identity has an exact primary-output match among its 1,238 records, nor a matching primary DOI/URL in the SHA-verified active Scout batches or pending inbox. This supports possible standalone artifact-record misses, not completed novelty/eligibility decisions (`scout-operations/analysis-v3/revision-1/embedded-code-findings.json:1`).

VERIFIED_SOURCE: For `reach-000014`, the Scientific Data article explicitly links `https://github.com/yiwenff/WUS-SR-data-descriptor` in Code availability. The author README describes figure-generation Matlab scripts and a data folder. The paper acknowledges NA18OAR4590396. The repository's own output-level award is NOT_DETERMINED (`scout-operations/analysis-v3/revision-1/snow-journal-fulltext.json:1`; `scout-operations/analysis-v3/revision-1/snow-readme.json:1`).

INFERRED: Treat the snow code as a supporting output of the named paper and a plausible separate-record lead. A reviewer should decide catalog scope and artifact-level attribution. Do not promote the paper's award into the same-DOI award tier for a GitHub repository.

VERIFIED_SOURCE: For `reach-000016`, the GMD article cites Zenodo version `10.5281/zenodo.6873384`; that version and the embedded `10.5281/zenodo.7145414` share concept DOI `10.5281/zenodo.5777820`. The native archive lists Noah-LSM, GA, experiment and plotting archives. Its registry type is JournalArticle despite the code/data contents (`scout-operations/analysis-v3/revision-1/noah-journal-fulltext.json:1`; `scout-operations/analysis-v3/revision-1/noah-cited-version.json:1`; `scout-operations/analysis-v3/revision-1/noah-zenodo-native.json:1`; `scout-operations/analysis-v3/revision-1/datacite-probe.json:1`).

VERIFIED_SOURCE: The exact-title Crossref result for that GMD article identifies Korean funding awards, without establishing an output-level WPO award. This does not prove that WPO funding is absent, but the REACH award association cannot simply be inherited (`scout-operations/analysis-v3/revision-1/noah-paper-crossref-title.json:1`).

INFERRED: Keep one version-family lead for the Noah archive, not separate discoveries for 6873384 and 7145414. Hold a focused human question on funding, resource type and catalog eligibility. No candidate was staged and no REACH metadata was changed.

## 3. DOI resolution and pilot strata

VERIFIED_SOURCE: All 75 unresolved publication records received bounded native-page/title-search checks. Exact native DOI metadata plus an exact native title resolved 12 identifiers. Sixty-three remain unresolved; nine records have title-only candidate matches that are not accepted as identity proof. Two of the pilot's previously DOI-less seeds resolved, leaving its original 40 records split into 20 previously resolved, two newly resolved and 18 still unresolved (`scout-operations/analysis-v3/revision-1/doi-resolution-review.json:1`; `scout-operations/analysis-v3/revision-1/pilot-strata-update.json:1`).

INFERRED: Preserve the original pilot roster and report these strata separately. A DOI identifier is not proof of peer-reviewed publication or funding. Keep URL/native-page methods available for unresolved cases, and block only DOI-dependent sweeps until resolution. Do not score an unavailable query as no artifact found.

## 4. Full deterministic population, bounded agent pilot

INFERRED: Schedule all applicable deterministic methods across the full 933-seed population, with canonical identity deduplication, source/policy hashes and source-specific retry handling. Existing successful unchanged results should be reused. Keep the 40-seed roster for agent effort, false positives and human-review time. A method does not become eligible merely because it is inexpensive.

VERIFIED_SOURCE: The artifact/DOI-resolution follow-up retained 367 distinct request-URL receipts, including 18 HTTP 429 observations. Total network calls across its interrupted and resumed invocations are NOT_DETERMINED; distinct receipts are not a request counter. The completed invocation's own counters are preserved separately. The full 933-seed method sweep has not been performed (`scout-operations/analysis-v3/revision-1/followup-accounting.json:1`).

HYPOTHESIS: The full deterministic run will cost a few thousand requests. Pagination, source restrictions, conditional requests and reuse must be measured before accepting that estimate.

## 5. Two campaigns and the all-awards coverage number

VERIFIED_SOURCE: The current public primary-award universe normalizes to 711 identifiers. Its populated Year Funded values begin in 2015; two primary rows have no year and remain included. The campaign template therefore enumerates 1,422 award/provider units, including units that may return no records (`scout-operations/analysis-v3/revision-1/award-campaign-universe.json:1`; `scout-operations/analysis-v3/revision-1/registry-campaign-run-template.json:1`).

INFERRED: Search all available registry years for those primary awards through a captured as-of time, rather than truncating to an arbitrary decade. Include unparsed-but-valid program award identifiers; do not query Related Award Number(s) as primary awards. Use native publication dates and flag apparent pre-award anomalies rather than silently dropping them.

VERIFIED_SOURCE: The new registry-side dry-run import brings forward 801 distinct DOI subjects from existing active historical and monthly batches, with each appearance and source checksum retained. An exact DOI association locates 495 subjects in existing public outputs, including code/data; 306 still need full identity/version checking. These 306 are not asserted novel outputs (`scout-operations/analysis-v3/revision-1/registry-campaign-import.json:1`; `scout-operations/analysis-v3/revision-1/registry-identity-screen.json:1`).

INFERRED: One shared subject/method key prevents both campaigns researching the same unchanged output twice. The artifact-lead table remains separate, with the three claim tiers. A campaign-run manifest is necessary operational evidence in addition to the two research tables: otherwise zero-result and failed queries disappear from the completeness denominator.

NOT_DETERMINED: Current all-awards registry enumeration completeness. Historical headline counts use older award universes and do not establish completion for the current 711 awards. Full registry recall also depends on funding metadata that registries may not contain. The detailed query-unit and pagination contract is in `CONTRACT-AMENDMENT.md`.

## 6. Branch protection and review separation

VERIFIED_SOURCE: Current GitHub documentation describes branch/tag rulesets for public repositories, but file-path push rulesets for private/internal repositories. The public owner account type is User; its billing plan is NOT_DETERMINED. This review therefore cannot endorse a path-scoped bot bypass as an available public-repository permission boundary (`scout-operations/analysis-v3/revision-1/github-rules-doc-markdown.json:1`; `scout-operations/analysis-v3/revision-1/public-repo.json:1`). See [GitHub's ruleset documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets).

INFERRED: Consolidate data updates into one rolling publication PR, or separate frequently generated data into a data branch/repository while protecting code/policy main. Do not create a new PR from each of 40 workflows. A branch-wide app bypass is not a file-path authorization restriction, and CODEOWNERS does not constrain a direct push that bypasses review. Details and alternatives are in `BRANCH-SAFETY-REVISION.md`.

VERIFIED_SOURCE: No open PR is listed. Actual GitHub PR #1 is an unrelated, already merged setup PR with six changes outside analysis-v3. No approval was submitted (`scout-operations/analysis-v3/revision-1/public-prs.json:1`; `scout-operations/analysis-v3/revision-1/pr-one-status.json:1`; `scout-operations/analysis-v3/revision-1/pr-one-files.json:1`).

INFERRED: A future policy/inventory review and ledger review must have separate explicit file scopes. Policy/inventory scope passing does not authorize merging ledger artifacts. Keep PR 2 on hold for the owner's gold-set and campaign review. No private system, source ledger, workflow, schedule, branch rule or catalog was changed.
