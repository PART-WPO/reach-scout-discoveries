"""Offline provider fallback regression: no guesswork, no candidate/handoff."""
import base64
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from recover_related_output_source import recover


class NativeRecoveryTests(unittest.TestCase):
    def test_zenodo_exact_version_verifies_even_when_datacite_blocked(self):
        calls = []
        doi = "10.5281/zenodo.12627444"
        def getter(url):
            calls.append(url)
            if "api.datacite.org" in url:
                raise TimeoutError("blocked")
            return {"doi": doi, "metadata": {"title": "GLStormTrends"}}
        result = recover(doi, get_json=getter)
        self.assertTrue(result["official_exact_doi_verified"])
        self.assertTrue(result["native_exact_doi_or_readme_verified"])
        self.assertEqual(result["status"], "OFFICIAL_DOI_VERIFIED")
        self.assertEqual(len(calls), 2)
        self.assertEqual(result["new_public_candidate_count"], 0)

    def test_zenodo_concept_version_mismatch_is_not_a_verified_release(self):
        def getter(url):
            if "datacite" in url:
                raise TimeoutError("blocked")
            return {"doi": "10.5281/zenodo.999999", "metadata": {"title": "Other version"}}
        result = recover("10.5281/zenodo.12627444", get_json=getter)
        self.assertFalse(result["official_exact_doi_verified"])
        self.assertEqual(result["status"], "SOURCE_ACCESS_FAILURE")
        self.assertIn("VERSION_OR_DOI_IDENTITY_MISMATCH",
                      [x["status"] for x in result["evidence"]])

    def test_deep_blue_landing_must_come_from_exact_datacite_record(self):
        doi = "10.7302/17vn-x488"
        landing = "https://deepblue.lib.umich.edu/data/concern/data_sets/exact"
        calls = []
        def getter(url):
            calls.append(url)
            return {"data": {"attributes": {
                "doi": doi, "url": landing, "titles": [{"title": "Cyclone tracks"}],
                "types": {"resourceTypeGeneral": "Dataset"}, "created": "2024-11-02"}}}
        result = recover(doi, get_json=getter,
                         get_text=lambda url: "<html>10.7302/17vn-x488 Cyclone Tracks</html>")
        self.assertEqual(result["status"], "OFFICIAL_DOI_VERIFIED")
        self.assertEqual(result["title"], "Cyclone tracks")
        self.assertEqual(len(calls), 1)

    def test_unverified_datacite_url_never_triggers_guessed_native_path(self):
        doi = "10.7302/17vn-x488"
        html_calls = []
        result = recover(doi, get_json=lambda url: {
            "data": {"attributes": {"doi": "10.7302/unrelated",
                                    "url": "https://deepblue.lib.umich.edu/danger"}}},
            get_text=lambda url: html_calls.append(url))
        self.assertFalse(result["official_exact_doi_verified"])
        self.assertEqual(html_calls, [])
        self.assertEqual(result["status"], "SOURCE_ACCESS_FAILURE")

    def test_author_github_readme_exact_doi_and_release_without_zenodo(self):
        doi = "10.5281/zenodo.12627444"
        def getter(url):
            if "datacite" in url or "zenodo.org" in url:
                raise TimeoutError("native blocked")
            if url.endswith("/readme"):
                return {"encoding": "base64",
                        "content": base64.b64encode(("DOI: "+doi).encode()).decode()}
            if url.endswith("/releases"):
                return [{"tag_name": "v1.0", "published_at": "2024-07-02T16:58:17Z",
                         "html_url": "https://github.com/abkenyon/GLStormTrends_2024/releases/tag/v1.0",
                         "draft": False}]
            raise AssertionError(url)
        result = recover(doi, github_repo_url="https://github.com/abkenyon/GLStormTrends_2024",
                         github_source_url="https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2024GL109890",
                         get_json=getter)
        self.assertTrue(result["native_exact_doi_or_readme_verified"])
        self.assertFalse(result["official_exact_doi_verified"])
        self.assertEqual(result["github_initial_release"]["published_at"],
                         "2024-07-02T16:58:17Z")
        self.assertEqual(result["status"], "OUTPUT_METADATA_PARTIAL")
        self.assertEqual(result["project_attribution"], "NOT_VERIFIED_FROM_PARENT_ARTICLE")

    def test_unverified_github_link_not_fetched(self):
        calls = []
        def getter(url):
            calls.append(url)
            raise TimeoutError("blocked")
        recover("10.5281/zenodo.12627444", github_repo_url="https://github.com/abkenyon/GLStormTrends_2024",
                get_json=getter)
        self.assertFalse(any("api.github.com" in x for x in calls))


if __name__ == "__main__":
    unittest.main()
