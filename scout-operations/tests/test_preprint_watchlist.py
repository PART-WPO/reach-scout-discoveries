import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from preprint_watchlist import linked_final_dois, verified_final, refresh

class PreprintWatchlistTests(unittest.TestCase):
    def test_crossref_and_datacite_links(self):
        self.assertEqual(linked_final_dois({
            "type":"posted-content",
            "relation":{"is-preprint-of":[{"id-type":"doi","id":"10.1234/official"}],
                        "is-supplement-to":[{"id-type":"doi","id":"10.1234/other"}]}
        }), {"10.1234/official"})
        self.assertEqual(linked_final_dois(datacite_record={
            "relatedIdentifiers":[{"relationType":"IsPreprintOf",
                                   "relatedIdentifierType":"DOI",
                                   "relatedIdentifier":"10.1234/official"}]
        }), {"10.1234/official"})
    def test_only_official_journal_publication_qualifies(self):
        self.assertFalse(verified_final({"type":"posted-content","posted":{"date-parts":[[2026,10,1]]}}))
        self.assertFalse(verified_final({"type":"journal-article","created":{"date-parts":[[2026,10,1]]}}))
        self.assertTrue(verified_final({"type":"journal-article","published-online":{"date-parts":[[2026,11]]}}))
    def test_hold_and_release_as_research_lead_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p=root/"scout-operations"
            p.mkdir()
            (p/"preprint-watchlist.json").write_text(json.dumps({
                "schema":"reach-scout-preprint-watchlist-v1",
                "entries":[{"preprint_doi":"10.1234/preprint","status":"tracking_preprint"}]}))
            cr={"type":"posted-content","relation":{
                "is-preprint-of":[{"id":"10.1234/final","id-type":"doi"}]}}
            fetch=lambda doi: cr if doi=="10.1234/preprint" else {
                "type":"journal-article","published-online":{"date-parts":[[2026,11,1]]}}
            _, leads=refresh(root,today="2026-11-02",fetch_crossref=fetch,
                             fetch_datacite=lambda _:None)
            self.assertEqual(leads["entries"][0]["published_doi"], "10.1234/final")
            self.assertEqual(leads["entries"][0]["private_hub_import"],"NOT_VERIFIED")
            data=json.loads((p/"preprint-watchlist.json").read_text())
            self.assertEqual(data["entries"][0]["preprint_doi"],"10.1234/preprint")
            self.assertEqual(data["entries"][0]["status"],"published_version_found")
    def test_api_failure_does_not_release_preprint(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/"scout-operations";p.mkdir()
            (p/"preprint-watchlist.json").write_text(json.dumps({
                "schema":"reach-scout-preprint-watchlist-v1",
                "entries":[{"preprint_doi":"10.1234/pre","status":"tracking_preprint"}]}))
            _, leads=refresh(root,today="2026-11-02",
                            fetch_crossref=lambda doi: (_ for _ in ()).throw(OSError("offline")),
                            fetch_datacite=lambda doi:None)
            self.assertFalse(leads["entries"])

if __name__ == "__main__":
    unittest.main()
