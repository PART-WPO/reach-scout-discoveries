# Revised branch-safety recommendation

VERIFIED_SOURCE: GitHub's current documentation makes ordinary branch/tag rulesets available for public repositories, including Free plans. It describes file-path push rulesets for private/internal repositories, with Team-plan availability and inherited fork restrictions. Branch/tag rulesets target branch/tag names rather than code-folder patterns. Sources: [About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets), saved at `scout-operations/analysis-v3/revision-1/github-rules-doc-markdown.json:1`; [Available rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).

NOT_DETERMINED: The repository owner's actual GitHub billing plan and administrator-only settings. No credentials or billing API were used. The public repository metadata identifies the owner account as type `User`, so organization-plan assumptions are not established (`scout-operations/analysis-v3/revision-1/public-repo.json:1`).

INFERRED: Do not recommend a path-scoped push rule as an available public-repository control without administrator verification. Do not describe a branch-wide bot bypass as a data-folder-only permission. CODEOWNERS can require reviewers on pull requests, but does not make a bypassing bot unable to push code or policy changes directly.

INFERRED: The owner's concern about 40 workflows generating separate PRs is valid. Prefer one of these deliberately designed alternatives, rather than a PR per bot commit:

1. INFERRED: Retain data on main but consolidate generated updates into one bot-owned rolling PR on a regular cadence. Protect code/workflow/policy changes with review and required checks. Coordinate data refreshes behind one publisher; do not let 40 workflows independently open PRs.
2. INFERRED: Protect the code/policy main branch and place frequently generated public data on a dedicated data branch or separate data repository. Give the narrow publisher access to that destination and migrate feed consumers explicitly. A separate repository provides a stronger permission boundary than a branch-wide bypass.
3. INFERRED: If an administrator confirms a supported server-enforced path control for this exact public repository and plan, evaluate it with a non-production test before relying on it. A publisher-side path allowlist is useful validation but is not equivalent to server-enforced write authorization.

INFERRED: Keep force-push/deletion protection and code/workflow/policy review. Before changing enforcement, select the publication design and prove that existing monthly feeds and immutable batches still work. No settings, feed URLs, workflows, schedules or permissions were changed by this review.

VERIFIED_SOURCE: The anonymous API lists no open PRs. Actual GitHub PR #1 is the already merged October 22 setup change, “Initialize Scout discovery feed and automated validation”; its six files include paths outside analysis-v3. It is not the proposed policy/inventory review (`scout-operations/analysis-v3/revision-1/public-prs.json:1`; `scout-operations/analysis-v3/revision-1/pr-one-status.json:1`; `scout-operations/analysis-v3/revision-1/pr-one-files.json:1`).

INFERRED: Do not approve that historical PR as if it were this analysis. The current local analysis includes ledger data as well as inventory/policy, so a future policy-only PR must use an explicit file allowlist and a separate diff. The proposed PR 2 ledger approval remains held. The scope report records both folder confinement and this unsatisfied policy-only separation condition.
