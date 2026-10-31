# REACH Scout legacy provenance backfill: original method vs finding purpose

**Completed:** October 30, 2026 ET (GitHub updates October 31 UTC)

## Authorization and immutable-source boundary

The human reviewer explicitly approved classifying records from the historical logs while recording *original discovery method* separately from *finding purpose*. This is **provenance-only**: no new batch, no edit to old 24-column CSVs, no change to the 22 validated manifest entries, no change to any existing human review decision or public REACH record.

Companion ledger: [legacy-provenance-backfill.json](../legacy-provenance-backfill.json), 40 entries.

## Historical chronology grounded in GitHub

- Monthly DataCite+Crossref infrastructure: Oct 28 **12:46 PM ET**.
- Historical DataCite pilot enabled: Oct 28 **2:53–2:56 PM ET**. Original authorization: [pilot trigger commit](https://github.com/PART-WPO/reach-scout-discoveries/commit/05cfc5b804ba2c120199c6ecc86c9f1d20f38660).
- 188 DOI historical DataCite original seeds first published: **3:02 PM ET**, [manifest/harvest commit](https://github.com/PART-WPO/reach-scout-discoveries/commit/947398ba19aeb52891a6604030731e229032cb2b).
- API-first Scout priority introduced: Oct 28 **3:29 PM ET**, [selector commit](https://github.com/PART-WPO/reach-scout-discoveries/commit/e7218511e79ff4d7d2b413aed9cf5530605b40c3).
- The 33 earlier unclassified findings arose in SPARK award-centered research, not in the later 188-DOI historical API seed queue. The seven 3:30 PM records are from the first DataCite-focused Scout mission.

## Backfilled 40 legacy records: discovery method

| Method | Legacy records | Evidence |
|---|---:|---|
| Independent discovery | **33** | Pre-API original award-centered Scout mission timing, batch rationale, SPARK award and publisher/repository source trails |
| Direct API | **5** | Exact DOI identity verified in immutable historical DataCite original batch part001 (one Parsivel dataset and four DesignSafe records) |
| API-seeded expansion | **2** | Lake-effect article DOI `10.1175/WAF-D-24-0249.1` linked to verified dataset seed, plus Great Lakes cyclone DOI `10.1029/2024GL109890` identified as the other linked publication in the original DataCite triage report. The latter's **exact** seed DOI remains unverified |
| Unclassified | **0** | Original discovery method established for all 40; exact source-to-output path may still be incomplete |
| **Total** | **40** | **40 method classifications supported; one exact seed lineage remains unresolved** |

## Backfilled 40 legacy records: finding purpose

| Purpose | Count |
|---|---:|
| New output proposed for review | **16** |
| Existing REACH metadata correction | **17** |
| Possible duplicate review | **2** |
| Known duplicate review (without supported new correction) | **2** |
| Needs evidence / investigation | **3** |
| **Total** | **40** |

The Oct 27 hail article `10.1175/WAF-D-19-0105.1` retains its *original* source label as NEW, but the supplemental current finding purpose is metadata correction after the separately completed 2026-10-30 17:32 ET four-DOI recheck proved it already exists in REACH. A human reviewer must still decide the proposed additional award. The original CSV and any private decision remain untouched.

## Current two-dimensional metrics for **all 69** validated staged candidates

| Original discovery method | Count |
|---|---:|
| Independent discovery | **38** |
| Direct API | **10** |
| API-seeded expansion | **14** |
| Unclassified | **7** |

**Historical baseline only:** before the later provenance recovery, seven method origins had been unverified. Six non-legacy metadata-correction origins were subsequently recovered through the separate correction ledger. The Great Lakes cyclone method has now also been recovered as API-led; its exact seed DOI is still unknown. Read the current automated rollup for present totals.

| Finding purpose | Count |
|---|---:|
| New output review | **39** |
| Existing REACH metadata correction | **23** |
| Possible duplicate review | **2** |
| Known duplicate review | **2** |
| Needs investigation | **3** |

The effective rollup's **32 beyond-direct-API new-output review proposals** are evidence-supported staged proposals, NOT confirmed novel outputs, reviewer approvals, added public REACH records or proven impossible-to-retrieve-by-API works.

**Authoritative metrics**: [discovery-origin-rollup.json](../discovery-origin-rollup.json) fields `effective_discovery_method_counts`, `effective_finding_purpose_counts`, and `legacy_provenance`. Its `route_counts` and `raw_route_counts` intentionally preserve original CSV labels (including the old 40 blank-route count) only for backward-compatible provenance audit, **not** current unresolved-method totals.

## Safeguards and verification

- The companion ledger keys every recovered record to the **exact published batch ID, manifest CSV SHA-256, source row ordinal, run ID, DOI/URL and title**.
- Updated `rebuild_discovery_rollup.py` strictly rejects a mismatched ledger row, duplicate ledger identity or attempted override of an explicit original route; all SHA/row/run checks must complete before re-issuing metrics.
- GitHub Actions has published reconciled totals of 22 batches / 69 staged candidates. All 40 legacy discovery methods have since been classified; original batch entries remain unchanged.
- Future Scout candidates carry separate `Scout origin method:` and `Scout finding purpose:` lines, while retaining the existing Hub-compatible `Scout discovery route:` field. New metadata corrections are required to supply `origin_method`, so future correction findings need not lose credit for independent research.
- Existing weekday Scout missions, exceptional weekend month-start task and weekday briefing prompts were updated to use effective metrics; **their schedules are unchanged**.
- **Private Discovery Hub import, human eligibility, human-approved changes, and REACH publication remain NOT VERIFIED.**

## Bounded future action

For Great Lakes cyclone DOI `10.1029/2024GL109890`, the discovery METHOD is already categorized as API-seeded expansion based on the original historical DataCite mission report's identification of two linked publications. Its precise source-seed DOI remains unverified; only supplement that narrower lineage information if evidence appears. Six modern correction methods were separately recovered in `scout-operations/method-recovery-followups.json`. Do not repeat original research or republish outputs.
