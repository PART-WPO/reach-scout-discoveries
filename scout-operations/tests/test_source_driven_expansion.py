"""Offline positive control: source-backed dataset DOI, not generic reference scraping."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import source_driven_expansion as src

SEED = "10.1002/hyp.13998"
DATASET = "10.6075/j0sn07g9"

ARTICLE = """
<html><head><script>10.1234/unsafe.script</script></head><body>
<h2>DATA AVAILABILITY STATEMENT</h2>
<p>Processed soil moisture and runoff observations for this paper are in the
Sumargo et al. (2020b) repository.</p>
<h2>REFERENCES</h2>
<p>Smith, A. Some unrelated meteorological paper, https://doi.org/10.1175/WAF-D-19-0019.1.</p>
<p>Sumargo, E., McMillan, H., et al. Data from: A soil moisture monitoring
network to assess controls on runoff generation during atmospheric river events.
UC San Diego Library Digital Collections. https://doi.org/10.6075/J0SN07G9.</p>
</body></html>
"""
CROSSREF = {
    "message": {"DOI": SEED, "reference": [
        {"DOI": "10.1175/WAF-D-19-0019.1", "article-title": "A weather study unrelated to data"},
        {"DOI": DATASET, "unstructured": "Sumargo E. Data from: A soil moisture monitoring network in California. 2020."},
    ]}
}


class SourceDrivenResearchTests(unittest.TestCase):
    def fetch(self, url):
        if url.startswith("https://api.crossref.org/works/"):
            return json.dumps(CROSSREF).encode()
        if url == "https://onlinelibrary.wiley.com/doi/" + SEED:
            return ARTICLE.encode()
        raise AssertionError("Unexpected/untrusted request: " + url)

    def test_real_publisher_positive_control_finds_dataset_not_unrelated_reference(self):
        result = src.discover(SEED, fetch=self.fetch)
        self.assertEqual(result["status"], "SOURCE_BACKED_LEADS_FOUND")
        self.assertEqual([x["doi"] for x in result["discovered_doi_leads"]], [DATASET])
        self.assertEqual(len(result["source_checks"]), 2)
        self.assertTrue(all(x["source_sha256"] for x in result["source_checks"]))
        self.assertTrue(all(x["eligibility"] == "RESEARCH_LEAD_ONLY" for x in result["discovered_doi_leads"]))
        self.assertEqual(result["new_public_candidates"], 0)

    def test_generic_reference_and_scripts_do_not_create_leads(self):
        raw = "<script>data from https://doi.org/10.1111/fake</script><p>See https://doi.org/10.1175/WAF-D-19-0019.1.</p>"
        p = src.VisibleText()
        p.feed(raw)
        self.assertEqual(src.candidate_cues(p.plain(), SEED, "publisher_article_html", "https://onlinelibrary.wiley.com"), [])

    def test_incorrect_crossref_seed_identity_rejected(self):
        wrong = {"message": {"DOI": "10.1002/not-the-seed", "reference": [
            {"DOI": DATASET, "article-title": "Data from: wrong paper"}]}}
        self.assertRaisesRegex(ValueError, "wrong DOI", src.crossref_reference_leads,
                               json.dumps(wrong).encode(), SEED, "https://api.crossref.org/works/" + SEED)

    def test_partial_source_access_holds_remain_visible(self):
        def fail_one(url):
            if "onlinelibrary" in url:
                raise OSError("Publisher declined access")
            return json.dumps(CROSSREF).encode()
        x = src.discover(SEED, fetch=fail_one)
        self.assertEqual(x["status"], "SOURCE_BACKED_LEADS_FOUND")
        self.assertEqual(len(x["source_checks"]), 2)
        self.assertEqual(x["source_checks"][-1]["status"], "SOURCE_ACCESS_OR_PARSE_HOLD")
        self.assertEqual(x["discovered_doi_leads"][0]["doi"], DATASET)

    def test_bounded_doi_limit_and_host_allowlist(self):
        self.assertRaisesRegex(ValueError, "Unapproved", src.request_source,
                               "https://example.com/file.html")
        self.assertEqual(len(src.source_urls(SEED)), 2)
        self.assertEqual(len(src.source_urls("10.5194/gmd-2022-311")), 1)

    def test_doi_and_html_punctuation_normalized(self):
        self.assertEqual(src.canonical("https://doi.org/10.6075/J0SN07G9."), DATASET)
        self.assertEqual(src.canonical("DOI:10.6075/J0SN07G9"), DATASET)



    def test_verified_noaa_ir_manuscript_fallback_discovers_positive_dataset(self):
        item = "https://repository.library.noaa.gov/view/noaa/57177"
        pdf = item + "/noaa_57177_DS1.pdf"
        seen = []
        def fetch(url):
            seen.append(url)
            if url.startswith("https://api.crossref.org/works/"):
                return json.dumps({"message":{"DOI":SEED,"reference":[]}}).encode()
            if url.startswith("https://onlinelibrary.wiley.com/doi/"):
                raise OSError("Publisher blocked automated access")
            if url == item:
                return (('<a href="https://attacker.example/bad.pdf">bad</a>'
                         '<a href="noaa_57177_DS1.pdf">Accepted manuscript</a>').encode())
            if url == pdf:
                return b"%PDF-1.5 accepted manuscript bytes fixture"
            raise AssertionError("Unexpected untrusted request: " + url)
        def text_extractor(raw):
            self.assertTrue(raw.startswith(b"%PDF"))
            return ("A dataset is discussed.\n"
                    "Sumargo E et al. Data from: A soil moisture monitoring network "
                    "https://doi.org/10.6075/J0SN07G9.\n"
                    "Ordinary reference https://doi.org/10.1175/WAF-D-19-0019.1.")
        result = src.discover(SEED, fetch=fetch, ir_url=item, pdf_to_text=text_extractor)
        self.assertEqual(result["status"], "SOURCE_BACKED_LEADS_FOUND")
        self.assertEqual([x["doi"] for x in result["discovered_doi_leads"]], [DATASET])
        self.assertIn(pdf, seen)
        self.assertTrue(all("attacker.example" not in url for url in seen))
        self.assertEqual(result["source_checks"][-1]["status"], "SOURCE_READ")
        self.assertEqual(result["source_checks"][-1]["kind"], "noaa_ir_manuscript_pdf")

    def test_noaa_ir_item_must_match_verified_host_and_path(self):
        with self.assertRaisesRegex(ValueError, "not an exact trusted"):
            src.noaa_ir_pdf_leads(SEED, "https://example.com/view/noaa/57177",
                                 fetch=lambda _: b"")
        with self.assertRaisesRegex(ValueError, "not an exact trusted"):
            src.noaa_ir_pdf_leads(SEED, "https://repository.library.noaa.gov/view/noaa/57177/evil",
                                 fetch=lambda _: b"")

    def test_does_not_invent_noaa_ir_pdf_path_when_page_has_no_link(self):
        item = "https://repository.library.noaa.gov/view/noaa/57177"
        fetched = []
        def fetch(url):
            fetched.append(url)
            return b"<html><p>No public PDF link here.</p></html>"
        sources, leads = src.noaa_ir_pdf_leads(SEED, item, fetch=fetch)
        self.assertEqual(fetched, [item])
        self.assertEqual(leads, [])
        self.assertEqual(sources[-1]["status"], "NO_VALIDATED_MANUSCRIPT_PDF_LINK")

if __name__ == "__main__":
    unittest.main()
