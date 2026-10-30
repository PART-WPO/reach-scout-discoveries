# Scout original-seed no-action and attribution follow-ups (2026-10-29)

Keep original historical-triage status and existing review decisions. A completed original DOI and a separate future output-attribution lead can coexist; never count the latter as an unresolved original seed.

No-action subtypes:
- NOT_RESEARCH_OUTPUT: a grant notice or prospective project record, rather than an output.
- NO_DEMONSTRATED_WPO_CONNECTION_ALTERNATIVE_FUNDING: a real output whose source evidence identifies non-WPO support.
- NO_DEMONSTRATED_WPO_CONNECTION: a real output associated with broad NOAA cooperative, institutional or fellowship funding, but no demonstrated specific WPO SPARK workstream. Maintain a bounded separate follow-up in attribution-followups.json.
- POTENTIAL_WPO_ATTRIBUTION_UNRESOLVED: only after new positive primary-source workstream evidence establishes a project-to-output bridge that remains incomplete. Do not confer this status from a shared author, broad grant, topic or date alone.

For attribution follow-ups, perform up to five distinct meaningful checks of the actual project report, output list, publisher acknowledgments, dataset/code metadata, and SPARK primary vs related funding. Record checked URLs, contrary explanations and next action. If still no bridge after one round, close the follow-up with evidence; do not loop. If bridge evidence is sufficient, independently corroborate and apply existing full REACH/Scout/human duplicate review before proposing a novel output. Existing REACH additional-award corrections still require direct output-level award proof and exact UID. Hub remains 24 columns with no autoapproval.

Every hourly run must save a timestamped provenance audit including run ID, mode, original seeds and their independent dispositions, route counts, batch path (or explicit verified zero), no-action subtypes, follow-up queue changes, source evidence, coverage before/after, blockers and verifiability gaps. A reconstructed audit must remain PARTIAL when original evidence was not captured.

Cumulative counts must reconcile actual published CSVs against the manifest and never treat missing route labels as independent discoveries. Distinguish proposals, reviewer decisions and public REACH additions; verify public additions in the authoritative REACH agent-data manifest.

## Missing-award-acknowledgment discovery and attribution (2026-10-29)

Search broadly for outputs without award numbers: NOAA reports, publisher records, datasets, code, institutional and PI product catalogs. Missing award acknowledgment is **not** itself negative evidence of WPO funding. A shared NOAA affiliation, cooperative-institute award, topic, author, or time window is **not** project-specific attribution. Require a traceable output-to-SPARK/WPO workstream bridge with independent corroboration for confirmed funding; record positive, negative, and alternative funding evidence separately. Use one bounded substantive follow-up (up to five distinct meaningful checks) for concrete project-specific leads. Keep no-action original seed dispositions and separately tracked leads distinct; reopen only with new positive project-specific evidence or explicit human request. Never send broadly related NOAA material to the Hub without sufficient attribution and eligibility evidence.

On reviewer-confirmed missing-acknowledgment cases, preserve the specific verified bridge and investigate related outputs (articles, data, code, reports), each independently assessed and deduplicated. Track `WPO-funded outputs recovered without explicit award acknowledgment` only after documented absence of acknowledgment **and** human-confirmed WPO project-specific attribution; distinguish credible leads, Hub-visible proposals, confirmed eligible cases and actual verified new public REACH additions. Never count a lead or a no-action NOAA report as a recovered output.
