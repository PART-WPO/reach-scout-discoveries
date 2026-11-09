"""Read-only cross-mode identity and author-source privacy regressions."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from identity_disposition import decide, public_reach_author_seeds, version_relationships, verified_disposition


def index():
    records = [
        {"source": "REACH", "identity": "reach-1", "title": "Published Weather Paper",
         "location": "details.csv", "dois": ["10.1234/published"], "urls": []},
        {"source": "REACH", "identity": "reach-2", "title": "Distinct Dataset",
         "location": "details.csv", "dois": ["10.1234/dataset"], "urls": []},
        {"source": "SCOUT_INBOX", "identity": "candidate-a", "title": "Queued Publication",
         "location": "inbox.csv", "dois": ["10.1234/queued"], "urls": []}
    ]
    return {"schema": "reach-scout-identity-index-v1",
            "source_fingerprint": "sample-verified-snapshot",
            "records": records,
            "keys": {
                "doi": {"10.1234/published": [0], "10.1234/dataset": [1],
                        "10.1234/queued": [2]},
                "url": {},
                "title": {"published weather paper": [0], "distinct dataset": [1],
                          "queued publication": [2]}
            }}


def watchlist():
    return {"schema": "reach-scout-preprint-watchlist-v1",
            "entries": [
                {"preprint_doi": "10.1234/preprint-v1",
                 "verified_published_dois": ["10.1234/published"]},
                {"preprint_doi": "10.1234/preprint-v2",
                 "verified_published_dois": ["10.1234/published"]}
            ]}


class SharedDispositionTests(unittest.TestCase):
    def test_exact_published_reach_duplicate(self):
        x = decide(index(), watchlist(), doi="10.1234/published",
                   title="Published Weather Paper")
        self.assertEqual(x["disposition"], "EXISTING_IN_REACH")
        self.assertTrue(x["expansion_seed_preserved"])
        self.assertFalse(x["auto_staging"])

    def test_preprint_is_held_even_if_published_sibling_exists(self):
        x = decide(index(), watchlist(), doi="10.1234/preprint-v1",
                   title="Working paper")
        self.assertEqual(x["disposition"], "PREPRINT_WATCHLIST_HOLD")
        self.assertEqual(x["explicit_version_family"]["official_published_doi_leads"],
                         ["10.1234/published"])

    def test_all_preprint_generations_point_to_same_final_independently(self):
        x = version_relationships(watchlist(), "10.1234/published")
        self.assertEqual(x["preprint_dois"],
                         ["10.1234/preprint-v1", "10.1234/preprint-v2"])

    def test_final_doi_with_missing_title_is_not_auto_duplicate(self):
        x = decide(index(), watchlist(), doi="10.1234/published")
        self.assertEqual(x["disposition"], "IDENTITY_REVIEW_REQUIRED")

    def test_distinct_dataset_not_merged_with_article(self):
        x = decide(index(), watchlist(), doi="10.1234/dataset",
                   title="Distinct Dataset")
        self.assertEqual(x["disposition"], "EXISTING_IN_REACH")
        self.assertNotEqual(x["identity"]["matches"][0]["identity"], "reach-1")
        y = decide(index(), watchlist(), doi="10.1234/new-dataset",
                   title="Published Weather Paper")
        self.assertEqual(y["disposition"], "IDENTITY_REVIEW_REQUIRED")

    def test_exact_public_scout_candidate_not_private_approval(self):
        x = decide(index(), watchlist(), doi="10.1234/queued",
                   title="Queued Publication")
        self.assertEqual(x["disposition"], "EXISTING_PUBLIC_SCOUT_CANDIDATE")
        self.assertEqual(x["private_review"], "NOT_VERIFIED")

    def test_no_match_does_not_mean_verified_eligible(self):
        x = decide(index(), watchlist(), doi="10.1234/new",
                   title="New Observation")
        self.assertEqual(x["disposition"], "NO_PUBLIC_IDENTITY_MATCH")
        self.assertEqual(x["next_action"], "PROCEED_TO_ELIGIBILITY_AND_FUNDING_RESEARCH")

    def test_bad_watchlist_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "schema"):
            decide(index(), {"entries": []}, doi="10.1234/new")
        w = watchlist()
        w["entries"].append(w["entries"][0])
        with self.assertRaisesRegex(ValueError, "duplicate preprint"):
            decide(index(), w, doi="10.1234/new")

    def test_spark_personnel_cannot_seed_authors(self):
        cache = {"schema": "reach-scout-comparison-cache-v1",
                 "source_repo": "PART-WPO/reach-dashboard",
                 "records": [
                     {"output_type": "Publication", "awards": "NA26OARX459C0001",
                      "authors": ["Not From SPARK"], "authors_source": "SPARK"},
                 ]}
        self.assertEqual(public_reach_author_seeds(cache, "NA26OARX459C0001"), [])

    def test_reach_published_author_seeds_require_exact_award(self):
        cache = {"schema": "reach-scout-comparison-cache-v1",
                 "source_repo": "PART-WPO/reach-dashboard",
                 "records": [
                     {"output_type": "Publication", "awards": "NA26OARX459C0001",
                      "authors": ["Public Author", "Public Author"],
                      "authors_source": "REACH_PUBLIC_VERIFIED"},
                     {"output_type": "Publication", "awards": "NA26OARX459C0002",
                      "authors": ["Different Award"],
                      "authors_source": "REACH_PUBLIC_VERIFIED"},
                     {"output_type": "Dataset", "awards": "NA26OARX459C0001",
                      "authors": ["Dataset Creator"],
                      "authors_source": "REACH_PUBLIC_VERIFIED"}
                 ]}
        self.assertEqual(public_reach_author_seeds(cache, "NA26OARX459C0001"),
                         ["Public Author"])
        self.assertEqual(public_reach_author_seeds(cache, "NA26OARX459C0003"), [])

    def test_shared_and_official_ir_identify_existing_reach_consistently(self):
        public=index()
        url="https://repository.library.noaa.gov/view/noaa/333"
        public["records"][0]["urls"].append(url)
        public["keys"]["url"][url]=[0]
        ir={"dois":{"10.1234/alternate-doi":[url]}}
        result=verified_disposition(public,watchlist(),ir,doi="10.1234/alternate-doi",
                                    title="Published Weather Paper")
        self.assertEqual(result["disposition"],"EXISTING_IN_REACH")
        self.assertEqual(result["identity_confirmation_basis"],
                         "VERIFIED_IR_DOI_URL_AND_TITLE")
        unsafe=verified_disposition(public,watchlist(),ir,doi="10.1234/alternate-doi",
                                    title="Unrelated Dataset")
        self.assertEqual(unsafe["disposition"],"IDENTITY_REVIEW_REQUIRED")

    def test_shared_preprint_hold_cannot_be_overridden_by_existing_scout_queue(self):
        public=index()
        public["records"].append({
            "source":"SCOUT_INBOX","identity":"bad-preprint","title":"Working Paper",
            "location":"inbox.csv","dois":["10.1234/preprint-v1"],"urls":[]})
        public["keys"]["doi"]["10.1234/preprint-v1"]=[3]
        public["keys"]["title"]["working paper"]=[3]
        result=verified_disposition(public,watchlist(),{"dois":{}},
                                    doi="10.1234/preprint-v1",
                                    title="Working Paper")
        self.assertEqual(result["disposition"],"PREPRINT_WATCHLIST_HOLD")

    def test_no_reach_publication_means_no_author_route(self):
        cache = {"schema": "reach-scout-comparison-cache-v1",
                 "source_repo": "PART-WPO/reach-dashboard",
                 "records": [{"title": "project only", "awards": "NA26OARX459C0001"}]}
        self.assertEqual(public_reach_author_seeds(cache, "NA26OARX459C0001"), [])


if __name__ == "__main__":
    unittest.main()
