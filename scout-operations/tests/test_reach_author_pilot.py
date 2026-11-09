"""Public REACH publication-anchored author exploration remains PII-safe."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from reach_author_pilot import award_matches, publication_dois, research_award, author_identity_key
from test_identity_disposition import index, watchlist


class ReachAuthorPilotTests(unittest.TestCase):
    award = "NA26OARX459C0001"

    def cache(self, awards=None):
        return {
            "schema": "reach-scout-comparison-cache-v1",
            "source_repo": "PART-WPO/reach-dashboard",
            "records": [{
                "reach_uid": "uid-public-1",
                "title": "Published Weather Paper",
                "awards": awards or self.award,
                "dois": ["10.1234/published"],
                "links": ["https://doi.org/10.1234/published"]
            }]
        }

    def crossref_source(self):
        return {
            "DOI": "10.1234/published", "type": "journal-article",
            "title": ["Published Weather Paper"],
            "published-online": {"date-parts": [[2026, 10, 1]]},
            "author": [{"given": "Public", "family": "Scientist"}]
        }

    def search_results(self):
        return [
            {"DOI": "10.1234/unrelated-lead", "type": "journal-article",
             "title": ["Potential Article"], "author": [
                 {"given": "Public", "family": "Scientist"}]},
            {"DOI": "10.1234/other-author", "type": "journal-article",
             "title": ["No Shared Author"], "author": [
                 {"given": "Other", "family": "Person"}]},
        ]

    def test_exact_awards_only_no_related_award_suffix_truncation(self):
        self.assertTrue(award_matches({"awards": self.award + ", NA22OAR4590020"}, self.award))
        self.assertFalse(award_matches({"awards": self.award + "-T1-02"}, self.award))
        self.assertFalse(award_matches({"awards": "NA26OARX459C0002"}, self.award))

    def test_no_public_reach_publication_no_author_exploration(self):
        calls = []
        report = research_award(index(), watchlist(), {"dois": {}},
            self.cache(awards="NA26OARX459C0002"), self.award,
            doi_lookup=lambda doi: calls.append(doi),
            author_search=lambda *_: self.fail("No author query permitted"))
        self.assertEqual(calls, [])
        self.assertEqual(report["potential_seed_dois"], 0)
        self.assertEqual(report["independent_doi_leads"], [])

    def test_no_spark_fields_or_personnel_ever_used(self):
        cache = self.cache()
        cache["records"][0]["spark_principal_investigators"] = "Private Name"
        cache["records"][0]["authors_source"] = "SPARK"
        report = research_award(index(), watchlist(), {"dois": {}},
            cache, self.award, doi_lookup=lambda _: self.crossref_source(),
            author_search=lambda *_: self.search_results())
        serialized = json.dumps(report)
        self.assertEqual(len(report["independent_doi_leads"]), 1)
        self.assertNotIn("Private Name", serialized)
        self.assertNotIn("Public Scientist", serialized)
        self.assertTrue(report["spark_author_data_accessed"] is False)
        self.assertFalse(report["independent_doi_leads"][0]["project_funding_verified"])
        self.assertFalse(report["independent_doi_leads"][0]["discovery_hub_eligible"])

    def test_missing_or_wrong_crossref_publication_identity_no_author_queries(self):
        wrong = self.crossref_source()
        wrong["type"] = "posted-content"
        report = research_award(index(), watchlist(), {"dois": {}},
            self.cache(), self.award, doi_lookup=lambda _: wrong,
            author_search=lambda *_: self.fail("Preprint must not seed author search"))
        self.assertEqual(report["verified_publications"], 0)
        wrong = self.crossref_source()
        wrong["title"] = ["An unrelated study"]
        report = research_award(index(), watchlist(), {"dois": {}},
            self.cache(), self.award, doi_lookup=lambda _: wrong,
            author_search=lambda *_: self.fail("Title mismatch must not seed author search"))
        self.assertEqual(report["verified_publications"], 0)

    def test_no_preprint_family_or_existing_reach_lead(self):
        result = research_award(index(), watchlist(), {"dois": {}},
            self.cache(), self.award, doi_lookup=lambda _: self.crossref_source(),
            author_search=lambda *_: [{
                "DOI": "10.1234/published", "title": ["Published Weather Paper"],
                "type": "journal-article", "author": [
                    {"given": "Public", "family": "Scientist"}]}])
        self.assertEqual(result["independent_doi_leads"], [])

    def test_mixed_doi_sources_continue_until_verified_journal_seed(self):
        cache = self.cache()
        cache["records"].insert(0, {
            "reach_uid": "uid-public-dataset",
            "title": "A Related Data Product",
            "awards": self.award,
            "dois": ["10.1234/data"],
            "links": []})
        observed = []
        def crossref(doi):
            observed.append(doi)
            if doi == "10.1234/data":
                return {"DOI": doi, "type": "dataset",
                        "title": ["A Related Data Product"]}
            return self.crossref_source()
        report = research_award(index(), watchlist(), {"dois": {}},
            cache, self.award, doi_lookup=crossref,
            author_search=lambda *_: self.search_results(),
            max_publications=1, max_source_dois=2)
        self.assertEqual(observed, ["10.1234/data", "10.1234/published"])
        self.assertEqual(report["source_dois_checked"], 2)
        self.assertEqual(report["verified_publications"], 1)
        self.assertEqual(len(report["independent_doi_leads"]), 1)

    def test_verified_publication_author_sampling_is_diverse(self):
        cache = self.cache()
        cache["records"].append({
            "reach_uid": "uid-public-2", "title": "Second Weather Paper",
            "awards": self.award, "dois": ["10.1234/second"],
            "links": ["https://doi.org/10.1234/second"]})
        second = {
            "DOI": "10.1234/second", "title": ["Second Weather Paper"],
            "type": "journal-article",
            "published": {"date-parts": [[2026, 9, 1]]},
            "author": [{"given": "Second", "family": "Researcher"}]}
        first = self.crossref_source()
        first["author"] = [
            {"given": "Public", "family": "Scientist"},
            {"given": "Another", "family": "Contributor"},
            {"given": "Third", "family": "Contributor"}]
        searched = []
        def search(name, count):
            searched.append(name)
            return []
        report = research_award(index(), watchlist(), {"dois": {}},
            cache, self.award,
            doi_lookup=lambda doi: first if doi == "10.1234/published" else second,
            author_search=search, max_publications=2,
            max_authors=2)
        self.assertEqual(report["verified_publications"], 2)
        self.assertEqual(report["transient_authors_used"], 2)
        self.assertEqual(searched, ["Public Scientist", "Second Researcher"])
        self.assertNotIn("Public Scientist", json.dumps(report))
        self.assertNotIn("Second Researcher", json.dumps(report))

    def test_middle_initial_variation_is_a_search_hint_only(self):
        a = {"given": "Public C.", "family": "Scientist"}
        b = {"given": "Public", "family": "Scientist"}
        c = {"given": "Private", "family": "Scientist"}
        self.assertEqual(author_identity_key(a), author_identity_key(b))
        self.assertNotEqual(author_identity_key(b), author_identity_key(c))
        self.assertEqual(author_identity_key({"given": "J.", "family": "Scientist"}), ())

    def test_duplicate_public_doi_is_not_researched_twice(self):
        cache = self.cache()
        cache["records"].append(dict(cache["records"][0]))
        found = publication_dois(cache, {"dois": {}}, self.award)
        self.assertEqual(len(found), 1)

    def test_official_ir_crosswalk_supplies_doi_from_public_reach_article(self):
        cache = self.cache()
        cache["records"][0]["dois"] = []
        cache["records"][0]["links"] = [
            "https://repository.library.noaa.gov/view/noaa/777"]
        ir = {"dois": {"10.1234/published": [
            "https://repository.library.noaa.gov/view/noaa/777"]}}
        seeds = publication_dois(cache, ir, self.award)
        self.assertEqual([x["doi"] for x in seeds], ["10.1234/published"])


if __name__ == "__main__":
    unittest.main()
