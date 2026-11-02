# October 2026 monthly intake — metadata recovery audit

**Completed November 2, 2026.** All 13 original DOI records from the corrected October DataCite/Crossref monthly harvest were reviewed for the core REACH metadata fields.

| Original October API intake | Count |
|---|---:|
| Original DOI records | 13 |
| Originally missing Brief Abstract | 2 |
| Abstracts recovered into active Scout review feed | 2 |
| Other originally missing critical metadata (title, DOI, URL, type, authors, date, source/funding URLs) | 0 |
| Active original monthly Scout review proposals | 9 |
| Original funding / DOI-family exclusions, not newly staged | 4 |

## Corrected findings

1. **Extreme weather as an occupational hazard: Structural vulnerability among multilingual immigrant workers** — DOI `10.1016/j.pdisas.2026.100696`. Concise source-based abstract recovered via [NOAA Institutional Repository record 77174](https://repository.library.noaa.gov/view/noaa/77174), with explicit grant `NA22OAR4590187`. The active [enriched Scout batch](../../scout-discoveries/batches/2026-11-02-monthly-enriched-pdisas-100696-001.csv) replaces one original monthly proposal; secondary-link/version duplicate review remains outstanding.

2. **Improving extreme Fire Radiative Power forecasting with Gaussian loss-based transformer and LSTM models** — DOI `10.1080/01431161.2026.2749622`. Concise abstract recovered from the [matching indexed article abstract](https://onescholar.app/v/earth-and-environmental-sciences?days=7&page=1&page_size=25) and cross-checked against the [publisher's journal listing](https://www.tandfonline.com/subjects/geography?ContentItemType=research-article&PrimaryLanguageFacetField=en&SeriesKey=tres20&content=standard&pageSize=10&startPage=0&subjectTitle=&target=default). **Limitation:** the original publisher's full abstract was not directly retrievable through the research browser; the value is an evidence-based, independently written summary, not copied publisher text. The [enriched Scout batch](../../scout-discoveries/batches/2026-11-02-monthly-enriched-frp-2749622-001.csv) retains `NEEDS INVESTIGATION`: three structured award links map to multiple distinct primary SPARK projects, so the correct exact WPO-funded parent and remaining duplicate/version questions need human confirmation.

## What was not auto-filled

The principal investigator is not assumed from the first author; blank `Principal Investigators` and `Principal Investigator Email(s)` fields were left unchanged. IR-specific fields (`IR?`, `IR Status`, `IR Pub Date`, `IR Repository URL`) cannot be inferred from a Crossref record. Multiple plausible project-parent matches remain blank until supported by output-specific funding evidence. Four original records excluded for funding anomalies or DOI-family overlap remain no-action; they are not automatically staged because metadata was present.

## Feed and reviewer safeguards

The corrected monthly API harvest is kept immutable. Original Scout CSV batches are also retained; validated metadata supersessions replace the two active single-row entries in the public feed **without increasing the proposal count**. The metadata recovery ledger and the [machine-readable 13-record audit](monthly-2026-10-metadata-audit.json) capture the changes. Private Hub Sync, any preserved private human review decision, and public REACH publication are separate and **not verified from public GitHub**.

**No automatic publication or Smartsheet write was performed.** When a reviewer syncs the updated source, the Hub must use its reviewed-candidate-safe update pathway rather than creating a second item.
