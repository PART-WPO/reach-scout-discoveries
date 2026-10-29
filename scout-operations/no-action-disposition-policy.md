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
