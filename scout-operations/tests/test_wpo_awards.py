import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from wpo_awards import is_wpo_459, oar_segment, official_459_awards


class WpoAwardRuleTests(unittest.TestCase):
    def test_exact_459_variants_only(self):
        self.assertTrue(is_wpo_459("NA21OAR4590367"))
        self.assertTrue(is_wpo_459("NA26OARX459C0001"))
        for other in ("NA22OAR0110123", "NA22OAR4690123",
                      "NA20OAR4320278", "NA20NES4320003",
                      "NA26OARX459C0001-not-a-match", "NA22OAR459"):
            self.assertFalse(is_wpo_459(other), other)

    def test_other_oar_awards_are_not_wpo(self):
        self.assertEqual(oar_segment("NA21OAR4590367"), "459")
        self.assertEqual(oar_segment("NA20OAR4320278"), "432")
        self.assertEqual(oar_segment("NA22OAR0110123"), "011")
        self.assertEqual(oar_segment("NA22OAR4690123"), "469")
        self.assertIsNone(oar_segment("NA20NES4320003"))

    def test_official_metadata_exact_doi_funding_not_research_note(self):
        metadata={"status":"ok","provider":"crossref",
                  "funding_references":[
                      {"name":"NOAA Weather Program Office","award":["NA21OAR4590367"]},
                      {"name":"NOAA CI","award":["NA20OAR4320278"]}]}
        self.assertEqual(official_459_awards(metadata), ["NA21OAR4590367"])
        self.assertEqual(official_459_awards({**metadata,"funding_references":[]}),[])
        self.assertEqual(official_459_awards({**metadata,"provider":"search_note"}),[])
        self.assertEqual(official_459_awards({**metadata,"status":"not_verified"}),[])


if __name__=="__main__":
    unittest.main()
