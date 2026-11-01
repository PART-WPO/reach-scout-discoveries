# REACH Scout — November 1, 2026, 17:25 ET: monthly exception closure and expansion-source follow-up

## Starting state and authority
Read the active monthly API manifest, monthly-fast-intake.json, monthly-triage.json, coverage.json, active-workstream.json, monthly-decision-queue.json, monthly-expansion-leads.json and scout-discoveries/manifest.json before work. The active primary-only October cohort contains 13 original DOIs. The validated Scout public discovery feed contains 8 October original DOI proposals and 76 total active candidate rows across 31 batches; private Discovery Hub import is NOT VERIFIED. No reviewer approval or public REACH addition was observed. Superseded related-only awards and older 26-record October batch were excluded.

## Original DOI decision lane — two cross-cohort no-action closures
- October `10.5281/zenodo.23289230` (concept) and `10.5281/zenodo.23289231` (version) are exact identities already tracked in historical `scout-operations/historical-triage.json`, both status `human_metadata_needed`, and together form existing `scout-operations/metadata-review-units.json` review unit `zenodo-mom6`.
- Closed **only the two duplicate October monthly intake ledger cases** as `no_action`, with preserved evidence URL, source snapshot, explicit monthly-only scope and no second Scout/Hub submission. This is NOT a human no-action decision on the historical datasets; historical `human_metadata_needed` review remains unchanged and its private Hub delivery is NOT VERIFIED.
- Historical reviewer still must determine native publicly accessible file scope and canonical concept/version representation. Do not reopen or stage a second monthly version-family proposal without new evidence or explicit reviewer direction.
- Three **different** original October funding-conflict cases remain open: `10.1002/qj.70325`, `10.1088/2515-7620/aeaad2`, and `10.5194/egusphere-2026-4928`. No unverified project attribution was converted into a review candidate.

## Separate API-seeded expansion lane — two source-specific bibliographic updates
- `10.1177/10506519261455873` (seed `10.5194/egusphere-2026-5876`): publisher confirms *Journal of Business and Technical Communication*, first online **2026-07-06**, and a 1,429-participant five-NWS-office survey. ASU CRUX Lab independently documents a NOAA SBES-funded probabilistic-forecast communication project led by coauthor Kathryn Lambrecht. This is **project context, NOT an article-specific grant acknowledgment**. Exact primary WPO award attribution and full REACH/Scout secondary-link/version dedup remain NOT VERIFIED. Sources: https://journals.sagepub.com/doi/abs/10.1177/10506519261455873 ; https://cisa.asu.edu/crux-lab/employing-rhetoric-to-improve-probabilistic-forecast-communication ; https://pinakes.wacclearinghouse.org/article/517069 .
- `10.1145/3794916.3794919` (same original seed): Pinakes confirms a *Communication Design Quarterly* two-phase five-NWS-office action-research article and bibliographic date **2026-03-01** (secondary index; publisher date not yet independently confirmed). J-GLOBAL separately corroborates vol. 14, issue 1, pages 22–37. ASU project context does not establish this article's direct grant attribution. Full WPO funding and REACH/Scout version/secondary-link dedup remain NOT VERIFIED. Sources: https://pinakes.wacclearinghouse.org/article/376641 ; https://jglobal.jst.go.jp/en/detail?JGLOBAL_ID=202602211655199313 ; https://cisa.asu.edu/crux-lab/employing-rhetoric-to-improve-probabilistic-forecast-communication .
- Both entries updated in `scout-operations/monthly-expansion-leads.json` with status `investigating`, exact seed and API-seeded expansion method retained, and project_funding_verified=false. Neither was staged. Third expansion DOI `10.25923/k9kh-y971` remains already in public REACH as `reach-000821`, not a new output.

## Automated validation and status accounting
Initial coverage rebuild GitHub Actions run 41357162521 computed 13 received, **10 completed, 3 open**, but failed to push derived files because the simultaneous workstream job changed `active-workstream.json` and Git rebase encountered a conflict. Rerunning that same old-head workflow also failed. A fresh latest-main ledger commit triggered new Actions: **coverage run 41357272452 SUCCESS** and workstream verification run 41357272240 SUCCESS. The live `coverage.json` now reports **13 received, 10 checked (8 public Scout-feed staged + 2 monthly no-action), 3 needs research, missing_from_ledger=0, errors=[]**. These are Scout research dispositions, not private Hub imports, human approvals or public REACH updates.

## Funnel and safeguards
- Original October monthly API DOI records: **13**.
- Public validated Scout feed original candidates: **8**, with private Hub import **NOT VERIFIED**; reviewer should use the Discovery Hub's **Sync to Scout** import and verify its results.
- October monthly original no-action cross-cohort duplicate-review cases: **2**.
- Original funding exceptions still open: **3**.
- Separate API-seeded leads: **3** (2 investigating, 1 already in REACH); **0 separately staged**.
- Human approvals observed: **0**. Public REACH additions observed: **0**.
- No manual manifest editing, no duplicate feed draft, no human decision change, no retired related-award re-staging, no SPARK/Smartsheet/REACH changes, no schedule change.

## Next mission
Resolve the three specific original project-funding contradictions with distinct evidence or defensible human/no-action disposition; independently verify article-specific WPO funding and complete REACH/Scout detail/version dedup for the two expansion publications. Do not repeat already-staged original DOI research.
