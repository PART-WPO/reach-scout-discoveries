#!/usr/bin/env python3
"""Evidence-pinned Scout throughput scorecard; never equate routing with research."""
import hashlib,json,argparse
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]
FILES={"queue":"scout-operations/crossref-candidate-queue.json","crossref":"scout-operations/historical-crossref-coverage.json","datacite":"scout-operations/historical-coverage.json","feed":"scout-discoveries/manifest.json","watchlist":"scout-operations/preprint-watchlist.json","archive":"scout-operations/preprint-retirement-archive.json","reconciliation":"scout-operations/preprint-13-identity-reconciliation.json","registry":"scout-operations/research-outcome-registry.json"}
OUTPUT="scout-operations/scout-throughput-scorecard.json"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build(root):
 data={k:json.loads((root/p).read_text()) for k,p in FILES.items()}
 q,c,d,f,w,a,r,g=(data[k] for k in FILES)
 if len(q["items"])!=q["total"] or sum(q["lane_counts"].values())!=q["total"]:raise ValueError("Incomplete Crossref candidate queue")
 if c["total_distinct_dois"]!=q["total"]:raise ValueError("Crossref cohorts differ")
 if c["originals_completed"]+c["unverified_terminal_statuses"]>c["total_distinct_dois"]:raise ValueError("Invalid Crossref completed claims")
 if len(w["entries"])!=w["metrics"]["preprints_tracked"]:raise ValueError("Active watchlist mismatch")
 if len(a["entries"])!=a["retired_preprint_versions_total"]:raise ValueError("Retirement archive mismatch")
 if set(x["preprint_doi"] for x in w["entries"]) & set(x["preprint_doi"] for x in a["entries"]):raise ValueError("Archived preprint still active")
 if r["total"]!=len(r["entries"]):raise ValueError("Targeted reconciliation count mismatch")
 lane=Counter(x["lane"] for x in q["items"])
 current_sha={p:sha(root/p) for p in FILES.values()}
 queue_sources={p:{"recorded_sha256":expected,"current_sha256":sha(root/p),"fresh":sha(root/p)==expected} for p,expected in q["source_sha256"].items()}
 queue_fresh=all(x["fresh"] for x in queue_sources.values())
 # A queue may be stale after monthly retirement; never misrepresent its counts as current.
 counts=Counter(x["classification"] for x in r["entries"])
 result={"schema":"reach-scout-throughput-scorecard-v1",
 "source_sha256":current_sha,
 "source_freshness":{"crossref_queue_source_checks":queue_sources,"crossref_queue_fresh":queue_fresh,"targeted_reconciliation_scope_is_snapshot":True},
 "screening_not_research":{"historical_crossref_dois":q["total"],"identity_fast_exits":lane["EXISTING_REACH_FAST_EXIT"],"bounded_identity_reviews":lane["BOUNDED_IDENTITY_REVIEW"],"novel_research_candidates":lane["NOVEL_IDENTITY_RESEARCH"],"preprint_holds":lane["PREPRINT_WATCHLIST_HOLD"],"published_version_leads":lane["PREPRINT_PUBLISHED_VERSION_LEAD"],"other_evidence_holds":lane["WAIT_FOR_NEW_EVIDENCE"]},
 "verified_original_research":{"crossref_completed":c["originals_completed"],"crossref_unverified_terminal_claims":c["unverified_terminal_statuses"],"crossref_remaining_reported":c["remaining"],"datacite_completed":d["fully_investigated"],"datacite_unverified_terminal_claims":d["unverified_terminal_statuses"],"datacite_remaining_reported":d["remaining"],"crossref_completion_percent":round(100*c["originals_completed"]/c["total_distinct_dois"],1),"datacite_completion_percent":round(100*d["fully_investigated"]/d["total_distinct_dois"],1)},
 "separate_related_output_expansion":{"crossref_verified_completed":c["seed_expansions_completed"],"crossref_pending":c["seed_expansion_pending"]},
 "preprint_workload":{"active":w["metrics"]["preprints_tracked"],"awaiting_official_publication":w["metrics"]["preprints_still_waiting_for_official_publication"],"published_version_needs_resolution":w["metrics"]["preprints_with_verified_published_versions"],"archived_versions":a["retired_preprint_versions_total"],"confirmed_reach_published_articles_archived":a["confirmed_published_articles_total"],"targeted_snapshot_counts":dict(sorted(counts.items()))},
 "public_candidate_pipeline":{"public_feed_rows":f["candidate_rows"],"public_feed_batches":f["batch_count"],"private_hub_imports":"NOT_VERIFIED","reviewer_approvals":"NOT_VERIFIED","new_public_reach_additions":"NOT_VERIFIED"},
 "effectiveness_measurement":{"verified_new_research_completions_since_prior_scorecard":"NOT_MEASURABLE_WITHOUT_BASELINE","repeat_research_avoided":"NOT_MEASURABLE_WITHOUT_EVENT_LOG","hours_saved":"NOT_MEASURABLE_WITHOUT_TIME_DATA","reviewer_ready_outputs":"NOT_VERIFIED","verified_reach_additions":"NOT_VERIFIED"},
 "interpretation":"Queue classification is NOT a completed research investigation. No public Scout row implies private Hub import or approval. No calculated hours saved or repeated-work reduction without event evidence."}
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=ROOT);p.add_argument("--check",action="store_true");args=p.parse_args()
 result=build(args.root);content=json.dumps(result,indent=2,ensure_ascii=False)+"\n";path=args.root/OUTPUT
 if args.check:
  if not path.exists() or path.read_text()!=content:raise SystemExit("Throughput scorecard stale")
 else:path.write_text(content)
 print(json.dumps({"crossref_verified":result["verified_original_research"]["crossref_completed"],"datacite_verified":result["verified_original_research"]["datacite_completed"],"preprints_active":result["preprint_workload"]["active"],"queue_fresh":result["source_freshness"]["crossref_queue_fresh"]}))
if __name__=="__main__":main()
