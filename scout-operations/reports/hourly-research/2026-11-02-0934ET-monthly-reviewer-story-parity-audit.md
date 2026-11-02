# REACH Scout — October 2026 monthly original reviewer-story parity audit

**Audit run:** 2026-11-02, 09:34 ET. **Scope:** 9 active October original DOI proposals in the validated public Scout feed. **Mode:** read-only review-guidance audit; no duplicate drafts, manifest edits, private Hub writes, reviewer decisions, or REACH publication. The narratives below are **reviewer companion guidance**, not new 24-column submissions and not proof that the private Discovery Hub has imported or refreshed a card.

**Finding:** The current `quick_monthly_intake.py` synthesizes the three required review labels, and `prepare_batch.py` rejects NEW monthly proposals missing them. However, among the **9 already published original monthly proposals**, **7 legacy fast-intake CSVs contain none of the three labels**, the enriched Fire Radiative Power proposal contains all three, and the enriched immigrant-workers proposal contains Finding and What to check but **no Reviewer question**. These are preexisting public-feed records, not nine new discoveries. The current 37-batch/85-row manifest is a staging feed, not Hub delivery. Existing immutable batches and prior human decisions must remain unchanged. A future authorized replacement should use the unique inbox → validation → automated manifest supersession process, not duplicate insertion or editing immutable CSVs.

**Evidence boundary:** Previous October intake checks compared normalized DOI/title/output URL against the checksum-verified public REACH index and detail snapshot and active/pending Scout feed; those checks found no exact public match for these original DOI identities. The source-specific ledger also marks alternate DOI/version/secondary-link checks as incomplete for several cases. An absent exact match is not proof that every alternative identity was excluded. Public REACH baseline in the checked snapshot: 1,238 outputs. No private Hub imports, human approvals or new public REACH additions were independently observed in this audit.

## Original DOI reviewer guidance (do not re-stage existing candidates)

### 1. 10.1016/j.pdisas.2026.100696 — multilingual immigrant workers
**Finding:** October Crossref identified an Elsevier article on extreme weather as an occupational hazard. The NOAA Institutional Repository record `noaa:77174` corroborates WPO primary award **NA22OAR4590187**, the *A Weather-Ready Nation Para Todos* project, and provides the previously missing abstract, now summarized in the replacement Scout review proposal. Initial exact DOI/title comparison found no REACH match; the NOAA IR URL is the same work, not a second output. Four same-project focus-group records already exist in REACH (reach-000765–000768); complete secondary-link/version comparison remains outstanding.

**What to check before adding this output:** Confirm the recovered Brief Abstract against NOAA IR `noaa:77174` | Verify exact primary project and grant NA22OAR4590187 | Compare article with the four existing focus-group outputs without equating related materials with a duplicate publication | Finish alternate URL, secondary-link and version checks | Confirm **2026-10-01** follows Crossref published-print month-only normalization, not DOI-created.

**Reviewer question:** Is this independently catalogable journal article supported by the named funded project and distinct from the four existing focus-group outputs, or should it remain Needs Investigation pending secondary-link review?

Sources: https://repository.library.noaa.gov/view/noaa/77174 ; https://api.crossref.org/works/10.1016/j.pdisas.2026.100696

### 2. 10.1080/01431161.2026.2749622 — extreme Fire Radiative Power
**Finding:** October Crossref identified the 2026 International Journal of Remote Sensing article and three structured NOAA primary award matches: **NA22OAR4590512**, **NA23OAR4590387**, and **NA23OAR4590388**. Those map to at least two different SPARK projects (RRFS-CMAQ and S2S fire emissions/forecasts); the exact funded parent cannot be chosen automatically. The original API record lacked an abstract. A matching independent scholarly index supplied enough information for an original concise summary, but the publisher's full abstract was inaccessible. No exact public REACH match was recorded; prior firecasting outputs and a similarly named code repository require separate identity checks.

**What to check before adding this output:** Verify the summarized abstract against publisher full text if available, recording access failure otherwise | Determine which of the three awards funded this exact article and select only supported SPARK parent(s) | Finish alternate DOI/secondary-link and related Firecasting code comparisons | Use **2026-10-30** Crossref published-online date | Do not treat the related code as a new output without independent funding and identity proof.

**Reviewer question:** Which SPARK primary-award project actually funded this publication, and is the publication distinct from previously cataloged fire research and software?

Sources: https://api.crossref.org/works/10.1080/01431161.2026.2749622 ; https://onescholar.app/v/earth-and-environmental-sciences?days=7&page=1&page_size=25

### 3. 10.1088/2515-7620/aeaad2 — seasonal cyclone energy / GLORe
**Finding:** The Crossref journal article evaluates western North Pacific seasonal cyclone energy using experimental SFS reforecasts. Its full-text Funding section explicitly attributes support for this research to **NA24OARX459C0015**, a SPARK primary award for the *GLORe ocean reanalysis* project; the paper also uses GLORe initial states. Whether the cyclone-forecast study is a deliverable of the specific funded GLORe tasks remains a human attribution question. NOAA IR `noaa:76692` is an alternate record for the same article. No exact public REACH match was found in prior screening; alternate links/version checks are incomplete. A separate Zenodo notebook/code family remains in the expansion lane and is not part of this article's original intake decision.

**What to check before adding this output:** Confirm exact article-level funding statement and project task attribution, distinguishing NOAA/GOMO's separate support for GLORe development | Compare NOAA IR `noaa:76692` and all REACH secondary links as alternate locations for the same article | Verify **2026-10-01** Crossref date convention | Do not merge or automatically add the separately investigated Zenodo family.

**Reviewer question:** Does the explicitly funded cyclone reforecast paper belong under the GLORe SPARK parent as a distinct WPO output, or does its project-task relationship require Needs Investigation?

Sources: https://api.crossref.org/works/10.1088/2515-7620/aeaad2 ; https://repository.library.noaa.gov/view/noaa/76692

### 4. 10.1175/aies-d-26-0004.1 — severe weather ML target datasets
**Finding:** Crossref identified a 2026 *Artificial Intelligence for the Earth Systems* article about severe hail, wind and tornado target datasets, with structured primary award **NA22OAR4590530**. Its topic and Loken/Sandmael authors align with SPARK's *Bridging Watch-to-Warning Forecast Operations with Refined Probabilistic Guidance* project, but the article's own grant acknowledgment has not been independently inspected. Initial public REACH exact screening was negative; four earlier same-project severe-weather ML/software records (reach-000508, -000509, -000511, -000514) were found as related, not established duplicates.

**What to check before adding this output:** Verify article funding acknowledgment for NA22OAR4590530 and the named funded project | Compare the four prior severe-weather records by DOI, alternate URL, version and secondary links | Confirm Crossref **2026-10-01** publication date is the print-month office convention, not an invented online day | Do not infer PI identity solely from article authors.

**Reviewer question:** Is the target-dataset comparison a separate funded article rather than a version or already-cataloged project product, and is its exact parent established?

Source: https://api.crossref.org/works/10.1175/aies-d-26-0004.1

### 5. 10.1175/waf-d-25-0044.1 — RRFS valid-time shifting
**Finding:** Crossref identified a *Weather and Forecasting* paper on multiscale valid-time-shifting blending in ensemble assimilation, with structured primary award **NA19OAR4590138**. The subject overlaps SPARK's regional FV3 Hybrid EnVar large-background-ensemble project, but direct article-level funding/PI confirmation is still missing. Earlier REACH index checks found no exact match; five related ensemble/VTS papers (reach-000301, -000503 through -000506) need explicit comparison before treating this as new.

**What to check before adding this output:** Confirm exact article grant acknowledgment and project bridge to NA19OAR4590138 | Compare DOI, title, publisher links and REACH secondary links with the five earlier VTS/ensemble records | Confirm **2026-10-01** is Crossref print-month normalization | Keep previously published related work separate unless same-work/version evidence appears.

**Reviewer question:** Is this blending method paper a distinct article supported by the specified funded project, rather than an alternate version of an existing VTS output?

Source: https://api.crossref.org/works/10.1175/waf-d-25-0044.1

### 6. 10.1175/waf-d-26-0084.1 — 2025 FFaIR FV3-LAM/MPAS
**Finding:** Crossref identified a 2026 *Weather and Forecasting* article about FV3-LAM and MPAS forecasts for the 2025 Flash Flood and Intense Rainfall Experiment, with structured primary award **NA22OAR4590522**. HMT FFaIR and FV3-LAM methods fit the named SPARK ensemble/precipitation project, but direct publisher grant confirmation remains incomplete. Initial REACH exact DOI/title checks found no match; existing reach-000558 concerns an earlier 2024 FFaIR paper, not yet proven identical. Conflicting online-day snippets do not override the recorded month-only print-date convention.

**What to check before adding this output:** Verify article acknowledgment for NA22OAR4590522 and the correct FV3-LAM/HMT SPARK parent | Compare the 2025 FFaIR study against reach-000558 and REACH secondary links/version URLs | Keep **2026-10-01** if Crossref published-print supplies only October; do not invent a specific online day from conflicting snippets | Treat experiment model configurations as methods, not automatically separate research outputs.

**Reviewer question:** Is this 2025 FFaIR article distinct from the previously cataloged 2024 experiment publication and attributable to the listed primary project?

Source: https://api.crossref.org/works/10.1175/waf-d-26-0084.1

### 7. 10.3390/rs18193383 — offshore wind/wave assimilation
**Finding:** Crossref and NOAA IR `noaa:77382` identify a *Remote Sensing* article about assimilation of offshore wind and wave observations. The publisher funding statement and NOAA IR independently identify primary WPO award **NA22OAR4590179** for SPARK's wind-wave-current data assimilation project. Initial exact public REACH comparison found no match, and two same-award articles (reach-000397, -000398) are related but not shown to be the same paper. Copernicus datasets and the preexisting UMD-LETKF library are cited inputs, not automatically additional WPO outputs.

**What to check before adding this output:** Confirm primary project and publisher/NOAA IR award evidence | Compare REACH secondary links, NOAA IR alternate URL and any versions with reach-000397/-000398 | Confirm **2026-10-02** publisher online date | Keep Copernicus datasets and reused UMD-LETKF code out of the new-output count without independent funding evidence.

**Reviewer question:** Is the wind/wave assimilation article a distinct funded publication not represented by existing same-award papers or alternate links?

Sources: https://api.crossref.org/works/10.3390/rs18193383 ; https://repository.library.noaa.gov/view/noaa/77382

### 8. 10.5194/egusphere-2026-5876 — Skynet survey preprint
**Finding:** The original EGUsphere preprint PDF explicitly acknowledges **NA21OAR4590208** (WPO Social Sciences), and its five-NWS-office community-risk communication work matches SPARK's *Employing Rhetoric to Improve Probabilistic Forecast Communication* project. Initial exact REACH comparison found no match. Three same-project REACH outputs (reach-000820–000822) and two **distinct** related article leads (10.1177/10506519261455873 and 10.1145/3794916.3794919) are separately tracked; those articles are not alternate versions of this preprint merely because they cite related work. A future Geoscience Communication final article DOI has not been verified.

**What to check before adding this output:** Confirm preprint grant and project from PDF page 6 | Check whether a later Geoscience Communication final DOI now represents the same preprint work | Compare REACH alternate links and existing reach-000820–000822 | Use **2026-10-22** Crossref posted date for this preprint | Do not duplicate the two separately staged related article review cases or existing technical memorandum.

**Reviewer question:** Should this funded preprint be cataloged now as its own work, or does a verified final published version require a single canonical publication decision?

Sources: https://api.crossref.org/works/10.5194/egusphere-2026-5876 ; https://egusphere.copernicus.org/preprints/2026/egusphere-2026-5876/egusphere-2026-5876.pdf

### 9. 10.5194/tc-20-5973-2026 — California snow/vegetation simulations
**Finding:** The final 2026 *The Cryosphere* paper acknowledges WPO primary award **NA25OARX459C0342-T1-01** and also a separate CIROH award (not a WPO search seed). SPARK associates the WPO award with remote effects of western snow dynamics on Southern Great Plains precipitation; whether this California snow/vegetation methods paper is a direct deliverable of those tasks remains unresolved. The publisher explicitly links an earlier EGUsphere preprint **10.5194/egusphere-2025-3884** to this final article: **one publication version family, not two additions**. The paper's supplement is not automatically a separate output, and Noah-MP is reused code. Initial exact REACH screening was negative; full alternate-link/version scan remains incomplete.

**What to check before adding this output:** Confirm project-task relationship to NA25OARX459C0342-T1-01, keeping CIROH distinct | Compare final DOI and preprint 10.5194/egusphere-2025-3884 as one work family in REACH secondary links | Use final publication date **2026-10-15** from publisher | Do not separately count the article supplement or preexisting Noah-MP code.

**Reviewer question:** Should the final journal article be the single canonical output for this preprint/final family under the listed WPO parent, or is project-specific attribution still too uncertain?

Sources: https://tc.copernicus.org/articles/20/5973/2026/tc-20-5973-2026-discussion.html ; https://api.crossref.org/works/10.5194/tc-20-5973-2026

## Disposition and next steps

The audit **does not alter** the nine existing active original Scout proposals, their classifications, batch SHA checksums, previous human decisions, or the monthly-triage statuses. The seven legacy fast-intake batches remain guidance-incomplete as immutable CSVs, and the enriched immigrant-workers batch lacks its explicit reviewer-question label. **Do not re-stage these as new discoveries.** If reviewer-facing guidance must appear inside Discovery Hub cards rather than in this companion report, authorize a controlled, unique **replacement/supersession** of the affected existing proposal identities through the existing validated inbox and GitHub Action, preserving reviewer decisions and preventing duplicate cards. Until the private Hub import is independently observed, use the Hub's **Sync to Scout** action and verify the resulting cards; do not assert delivery or approval.

**Other queues:** 13 October primary-only API original DOI cases are all research-terminal in current coverage (9 staged for human review, 4 no-action: two conflicting funding and two previously tracked version-family identities). The separate monthly expansion ledger has six identities: two staged for human review, three already in REACH, one pending human intake; these are not additional original monthly rows. The historical DataCite coverage reports 188/188 investigated and zero remaining; ongoing normal award-centered independent discovery continues under the weekday schedule. Source manifests and counts should be re-read before any future briefing.