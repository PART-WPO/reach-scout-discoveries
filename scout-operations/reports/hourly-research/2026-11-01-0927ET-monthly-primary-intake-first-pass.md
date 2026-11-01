# October 2026 primary-only monthly intake — first-pass Scout audit
Checked 2026-11-01 approximately 09:27–09:45 EST. **Research in progress; no new candidate staged, Hub import not verified.**

## Source state
- Active `api-discoveries/manifest.json`: 13 DOI rows, batch `2026-11-01-monthly-api-2026-10-primary-only-part001` (generated 2026-11-01T13:52:45Z).
- Superseded contaminated 26-row batch `2026-11-01-monthly-api-2026-10-part001` is NOT eligible research input.
- Active `scout-discoveries/manifest.json`: 68 staged rows across 23 batches (generated 2026-11-01T14:02:48Z); related-award-only proposals for `10.17603/ds2-xjyf-nc93` and `10.1175/BAMS-D-23-0036.1` retired from active feed. Existing private Hub imports remain NOT VERIFIED.
- Live origin rollup: 40/40 legacy methods classified, 0 unclassified; Great Lakes `10.1029/2024GL109890` is API-seeded expansion, exact seed DOI NOT_VERIFIED.

## Completed checks
- Parsed 13 active monthly DOI rows. Checked normalized exact DOI/title against all 10 public REACH index shards (1,238 rows): **0 exact matches**; detail/alternate-link dedup still pending.
- Checked against all 23 active Scout batches (68 rows): **0 exact matches**.
- Checked all 6 SPARK project-index shards (578 projects) and all 6 award shards (990 mappings): each of the 13 monthly DOI rows has at least one reported award that is a literal primary SPARK award. This does NOT establish same-project attribution.
- No inbox draft, approval, Smartsheet insertion, or REACH addition was made.

## Research flags / next steps
1. **Same-project funding conflict:** `10.1002/qj.70325`. Publisher acknowledgments call `NA20OAR4320278` “The Global Drifter Program,” whereas SPARK primary project for that award is the West-Coast AQPI project. Do NOT stage as AQPI output until independently reconciled. https://rmets.onlinelibrary.wiley.com/doi/10.1002/qj.70325 ; https://repository.library.noaa.gov/view/noaa/77398
2. **Multiple valid primary projects:** `10.1080/01431161.2026.2749622` has `NA22OAR4590512` (RRFS-CMAQ project) and `NA23OAR4590387` / `NA23OAR4590388` (S2S Fire Emissions project). Preserve both project associations; don't invent a single parent.
3. **Potential concept/version family:** `10.5281/zenodo.23289230` and `10.5281/zenodo.23289231` share exact title and award; check DataCite relatedIdentifiers and Zenodo concept/version identity before deciding whether one or two distinct outputs.
4. **Scope verification:** `10.5194/egusphere-2026-4928` (land lower-tropospheric stability) vs SPARK saildrone hurricane project needs task-specific corroboration. `10.1088/2515-7620/aeaad2` has matching NOAA IR award evidence but still needs same-project scope review.
5. Continue exact DOI metadata and source-specific date checks, alternate-link dedup, related-output expansion, and per-project funding corroboration for all 13 rows. Do not publish a draft until eligible and 24-column `prepare_batch.py` validation passes.

## All active DOI IDs
`10.1002/qj.70325`, `10.1016/j.pdisas.2026.100696`, `10.1080/01431161.2026.2749622`, `10.1088/2515-7620/aeaad2`, `10.1175/aies-d-26-0004.1`, `10.1175/waf-d-25-0044.1`, `10.1175/waf-d-26-0084.1`, `10.3390/rs18193383`, `10.5194/egusphere-2026-4928`, `10.5194/egusphere-2026-5876`, `10.5194/tc-20-5973-2026`, `10.5281/zenodo.23289230`, `10.5281/zenodo.23289231`.

This report is an evidence checkpoint, **not** a Discovery Hub batch or a verified publication.
