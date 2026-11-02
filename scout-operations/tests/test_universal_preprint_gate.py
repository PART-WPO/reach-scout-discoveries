"""Every discovery origin is subjected to the same preprint review gate."""
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from verify_preprint_intake import publication_decision, preprint_type, verify

POSTED = {"type": "posted-content", "posted": {"date-parts": [[2026, 10, 1]]}}
JOURNAL = {"type": "journal-article",
           "published-online": {"date-parts": [[2026, 11, 1]]}}
CREATED_ONLY = {"type": "journal-article",
                "created": {"date-parts": [[2026, 9, 1]]}}
DATA_PREPRINT = {"types": {"resourceTypeGeneral": "Text",
                           "resourceType": "Preprint"},
                 "created": "2026-10-01"}

class UniversalPreprintGateTests(unittest.TestCase):
    def test_publication_type_classifications(self):
        self.assertTrue(preprint_type(POSTED, None))
        self.assertTrue(preprint_type(None, DATA_PREPRINT))
        self.assertEqual(publication_decision("10.1234/pre", "1", cr=POSTED)[0],
                         "preprint_hold")
        self.assertEqual(publication_decision("10.1234/pre", "1", dc=DATA_PREPRINT)[0],
                         "preprint_hold")
        self.assertEqual(publication_decision("10.1234/final", "1", cr=JOURNAL)[0],
                         "eligible")
        self.assertEqual(publication_decision("10.1234/created", "1", cr=CREATED_ONLY)[0],
                         "metadata_hold")
        self.assertEqual(publication_decision("10.1234/error", "1", cr_error=True,
                                              dc_error=True)[0], "metadata_hold")
        self.assertEqual(publication_decision("", "1", output_url=
                         "https://arxiv.org/abs/2610.00001")[0], "preprint_hold")
        self.assertEqual(publication_decision("10.1234/data", "3", dc={
            "types": {"resourceTypeGeneral":"Dataset"}})[0], "eligible")
        self.assertEqual(publication_decision("10.1234/pre", "1", cr=JOURNAL,
                                              watched=True)[0], "preprint_hold")

    def fixture(self, root, modes):
        (root / "scout-operations").mkdir()
        (root / "scout-discoveries/inbox").mkdir(parents=True)
        (root / "scout-discoveries/batches").mkdir()
        (root / "scout-operations/preprint-watchlist.json").write_text(json.dumps({
            "schema":"reach-scout-preprint-watchlist-v1", "entries":[]}))
        (root / "scout-discoveries/manifest.json").write_text(json.dumps({"batches":[]}))
        for name, doi, origin in modes:
            with (root / "scout-discoveries/inbox" / (name + ".csv")).open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=[
                    "DOI","Output Type","Title","Output URL",
                    "NOAA Award Number(s)","Scout Discovery Rationale"])
                w.writeheader()
                w.writerow({"DOI":doi,"Output Type":"1","Title":name,
                            "Output URL":"https://doi.org/"+doi,
                            "NOAA Award Number(s)":"NA22OAR4590179",
                            "Scout Discovery Rationale":origin})

    def test_all_five_discovery_routes_hold_posted_doi_and_preserve_original(self):
        modes=[
            ("monthly","10.1234/m1","Intake origin: Monthly API"),
            ("historical_crossref","10.1234/h1","Intake origin: Historical Crossref"),
            ("historical_datacite","10.1234/d1","Intake origin: Historical DataCite"),
            ("independent","10.1234/i1","Scout discovery route: Independent discovery"),
            ("expansion","10.1234/x1","Scout discovery route: API-seeded expansion")
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.fixture(root,modes)
            def cr(doi):
                return POSTED
            report=verify(root,fetch_crossref=cr,fetch_datacite=lambda d:None,
                          now="2026-11-02T20:00:00Z")
            self.assertEqual(report["held_batches"],5)
            self.assertEqual(report["eligible_batches"],0)
            watch=json.loads((root/"scout-operations/preprint-watchlist.json").read_text())
            self.assertEqual(len(watch["entries"]),5)
            self.assertTrue(all(e["seed_expansion_allowed"] for e in watch["entries"]))
            self.assertEqual({e["preprint_doi"] for e in watch["entries"]},
                             {m[1] for m in modes})
            self.assertTrue(all(item["verdict"]=="hold" for item in report["checks"]))

    def test_preprint_cannot_be_released_by_final_article_doi(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.fixture(root,[("pre","10.1234/pre","Independent discovery"),
                               ("final","10.1234/final","Independent discovery")])
            report=verify(root,fetch_crossref=lambda doi:
                POSTED if doi=="10.1234/pre" else JOURNAL,
                fetch_datacite=lambda doi:None)
            decisions={x["rows"][0]["doi"]:x["verdict"] for x in report["checks"]}
            self.assertEqual(decisions["10.1234/pre"],"hold")
            self.assertEqual(decisions["10.1234/final"],"eligible")
            self.assertEqual(len(json.loads((root/
                "scout-operations/preprint-watchlist.json").read_text())["entries"]),1)

    def test_existing_published_batches_not_mutated_or_rechecked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.fixture(root,[("original","10.1234/one","Monthly API")])
            p=root/"scout-discoveries/inbox/original.csv"
            published=root/"scout-discoveries/batches/original.csv"
            published.write_bytes(p.read_bytes())
            (root/"scout-discoveries/manifest.json").write_text(json.dumps(
                {"batches":[{"path":"scout-discoveries/batches/original.csv",
                             "sha256":hashlib.sha256(p.read_bytes()).hexdigest()}]}))
            report=verify(root,fetch_crossref=lambda doi:
                self.fail("published DOI should not be reclassified in new-intake gate"),
                fetch_datacite=lambda doi:None)
            self.assertEqual(len(report["checks"]),0)
            self.assertEqual(published.read_bytes(),p.read_bytes())

if __name__=="__main__":
    unittest.main()
