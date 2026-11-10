"""Offline regression tests for separated Scout discovery throughput and origins."""
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from source_discovery_metrics import summary
from discovery_origin_evidence import historical_crossref_source


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj) + "\n", encoding="utf-8")


class SourceDiscoveryMetricsTests(unittest.TestCase):
    def test_deduplicates_retries_and_counts_leads_not_completions(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            folder = root/"scout-operations/reports/bounded-expansion-research"
            checks = [{"kind":"noaa_ir_manuscript_pdf","status":"SOURCE_READ","source_sha256":"a"*64}]
            def report():
                return {
                    "schema":"reach-scout-bounded-expansion-research-v1",
                    "seed_doi":"10.1002/hyp.13998",
                    "seed_reach_identity_verified_in_graph":True,
                    "source_graph_sha256":"b"*64, "seed_expansion_fingerprint":"c"*64,
                    "source_lookups":[{"role":"VERIFIED_REACH_EXPANSION_SEED","doi":"10.1002/hyp.13998"}],
                    "source_driven_discovery":{
                        "schema":"reach-scout-source-driven-expansion-v1",
                        "seed_doi":"10.1002/hyp.13998", "source_checks":checks,
                        "discovered_doi_leads":[{"doi":"10.6075/J0SN07G9"}]},
                    "new_source_driven_leads_screened":[{
                        "doi":"10.6075/J0SN07G9","source_sha256":"a"*64,
                        "official_metadata_status":"ok", "eligibility":"RESEARCH_LEAD_ONLY_NOT_STAGED"}],
                    "new_distinct_doi_leads_found":1,
                    "separate_expansion_decisions_completed":0, "new_public_candidate_count":0,
                    "new_related_output_eligibility_confirmed":0,
                    "private_hub_import":"NOT_VERIFIED","human_approval":"NOT_VERIFIED"
                }
            write_json(folder/"run1.json",report())
            write_json(folder/"run2.json",report())
            scored=summary(root)
            self.assertEqual(scored["verified_research_report_count"],2)
            self.assertEqual(scored["distinct_verified_reach_seeds_investigated"],1)
            self.assertEqual(scored["new_distinct_source_backed_doi_leads"],1)
            self.assertEqual(scored["new_leads_with_official_metadata_retrieved"],1)
            self.assertEqual(scored["completed_distinct_expansion_decisions"],0)
            self.assertEqual(scored["new_public_candidates_from_these_expansions"],0)
            bad=report()
            bad["new_source_driven_leads_screened"][0]["source_sha256"]="d"*64
            write_json(folder/"run2.json",bad)
            with self.assertRaisesRegex(ValueError,"Unpinned/reused"):
                summary(root)

    def test_no_expansion_reports_are_unknown_not_fake_completions(self):
        with tempfile.TemporaryDirectory() as td:
            scored=summary(Path(td))
            self.assertEqual(scored["verified_research_report_count"],0)
            self.assertEqual(scored["completed_distinct_expansion_decisions"],0)


class HistoricalCrossrefOriginTests(unittest.TestCase):
    def test_exact_sha_award_and_doi_confirm_direct_api(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            doi="10.3390/atmos16070881"
            award="NA19OAR4590133"
            batch="api-discoveries/historical-crossref/batches/2026-11-02-test.csv"
            note_rel="scout-operations/historical-crossref-phase2/auto-verified-oar459-"+hashlib.sha256(doi.encode()).hexdigest()[:18]+".json"
            f=root/batch
            f.parent.mkdir(parents=True)
            with f.open("w",newline="") as out:
                writer=csv.DictWriter(out,fieldnames=["DOI","NOAA Award Number(s)"])
                writer.writeheader()
                writer.writerow({"DOI":doi,"NOAA Award Number(s)":award})
            digest=hashlib.sha256(f.read_bytes()).hexdigest()
            write_json(root/"scout-operations/crossref-candidate-queue.json",{
                "schema":"reach-scout-crossref-candidate-queue-v2",
                "source_sha256":{batch:digest},
                "items":[{"doi":doi,"wpo_459_award_numbers":[award],
                          "award_evidence_source_batches":[batch]}]
            })
            write_json(root/note_rel,{
                "schema":"scout-source-backed-research-evidence-v1",
                "original_doi":doi,"lane":"historical_crossref_original",
                "structured_award":award,
                "funding":"OFFICIAL_CROSSREF_EXACT_DOI_WPO459_CONFIRMED",
                "publication_status":"OFFICIALLY_PUBLISHED_JOURNAL_ARTICLE",
                "award_evidence_source_batches":[batch],
                "source_evidence":[{"type":"sha_verified_historical_crossref_batch",
                    "url":"https://github.com/PART-WPO/reach-scout-discoveries/blob/main/"+batch}]
            })
            result=historical_crossref_source(root,doi)
            self.assertEqual(result["method"],"Direct API")
            self.assertEqual(result["source_batch_sha256"],digest)
            self.assertIsNone(historical_crossref_source(root,"10.3390/atmos16070882"))
            f.write_text(f.read_text().replace(award,"NA22OAR4320001"))
            with self.assertRaisesRegex(ValueError,"SHA mismatch"):
                historical_crossref_source(root,doi)


if __name__ == "__main__":
    unittest.main()
