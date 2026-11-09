"""Safeguard regression tests: disambiguation, topic, award, and no SPARK."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from replay_author_safeguards import (
    AWARD, author_evidence, awards_recorded, funding_evidence, topical_evidence,
    choose_tier, evaluate_leads
)
from test_identity_disposition import index, watchlist


def author(given="Alex", family="Researcher", orcid="", affiliation=None):
    d = {"given": given, "family": family}
    if orcid: d["ORCID"] = "https://orcid.org/" + orcid
    if affiliation: d["affiliation"] = [{"name": affiliation}]
    return d


def source():
    return {"DOI": "10.1234/seed", "type": "journal-article",
            "title": ["Atmospheric air quality modeling"],
            "published": {"date-parts": [[2025, 1, 1]]},
            "author": [author(orcid="0000-0001-0002-0003"),
                       author("Morgan", "Colleague")]}


def candidate(doi, title, *, authors=None, funder=None):
    return {"DOI": doi, "type": "journal-article",
            "title": [title],
            "author": authors if authors is not None else [
                author(orcid="0000-0001-0002-0003")],
            "funder": funder or []}


def cache():
    return {"schema": "reach-scout-comparison-cache-v1",
            "source_repo": "PART-WPO/reach-dashboard",
            "records": [{
                "reach_uid": "reach-pilot-source", "title": source()["title"][0],
                "awards": AWARD, "dois": ["10.1234/seed"], "links": []
            }]}


class AuthorEvidenceSafeguardsTests(unittest.TestCase):

    def test_orcid_match_vs_mismatch(self):
        good = candidate("10.1234/candidate", "Ambient air pollution")
        self.assertEqual(author_evidence(source(), good), "SAME_REPORTED_ORCID")
        bad = candidate("10.1234/candidate", "Ambient air pollution",
                        authors=[author(orcid="0000-0001-0002-0004")])
        self.assertEqual(author_evidence(source(), bad), "ORCID_CONFLICT")
        self.assertEqual(author_evidence(source(),
                         candidate("10.1234/c", "Air pollution",
                                   authors=[author("Different", "Person")])),
                         "AUTHOR_NAME_NOT_CORROBORATED")

    def test_affiliation_and_two_coauthors_only_support_not_verify(self):
        prior = source()
        prior["author"][0].pop("ORCID")
        prior["author"][0]["affiliation"] = [
            {"name": "Department of Atmospheric Science at Example University"}]
        work = candidate("10.1234/c", "Air quality",
                         authors=[author(affiliation="Department of Atmospheric Science at Example University")])
        self.assertEqual(author_evidence(prior, work), "SHARED_PUBLIC_AFFILIATION")
        prior["author"][0].pop("affiliation")
        prior["author"] += [author("Pat", "Smith")]
        work["author"] = [author(), author("Morgan", "Colleague"), author("Pat", "Smith")]
        self.assertEqual(author_evidence(prior, work), "TWO_SHARED_COAUTHORS")
        work["author"] = [author()]
        self.assertEqual(author_evidence(prior, work), "AUTHOR_IDENTITY_UNRESOLVED")

    def test_topic_not_confused_by_health_risk_or_environmental_finance(self):
        self.assertEqual(topical_evidence(
            "Assessing disparities associated with ambient air pollution")[0],
            "DIRECT_ATMOSPHERIC_AIR_QUALITY_TOPIC")
        self.assertEqual(topical_evidence(
            "On the Very Idea of Health Equity")[0], "OUTSIDE_AWARD_TOPIC")
        self.assertEqual(topical_evidence(
            "Quality of Sustainability Reporting and Bank Stability")[0],
            "BROAD_CONTEXT_NEEDS_REVIEW")
        self.assertEqual(topical_evidence(
            "A Lidar Evaluation of Urban Phenomena")[0],
            "BROAD_CONTEXT_NEEDS_REVIEW")

    def test_exact_award_only_no_na_prefix_or_related_award(self):
        work = candidate("10.1234/x", "Ambient air pollution", funder=[
            {"name": "NOAA", "award": ["NA22OAR45905150", "NA22OAR4590515-T1-01",
                                      "NA21OAR4590515"]}])
        self.assertNotIn(AWARD, awards_recorded(work))
        self.assertEqual(funding_evidence(work, AWARD)[0],
                         "DIFFERENT_NOAA_AWARD_REGISTERED")
        work["funder"][0]["award"].append(AWARD)
        self.assertEqual(funding_evidence(work, AWARD)[0],
                         "EXACT_TARGET_AWARD_REGISTERED")
        self.assertEqual(funding_evidence({"funder": []}, AWARD)[0],
                         "NO_STRUCTURED_AWARD_EVIDENCE")

    def test_review_tiers_do_not_claim_funding_or_stage(self):
        self.assertEqual(choose_tier(
            "DIRECT_ATMOSPHERIC_AIR_QUALITY_TOPIC",
            "AUTHOR_IDENTITY_UNRESOLVED", "NO_STRUCTURED_AWARD_EVIDENCE",
            "NO_PUBLIC_IDENTITY_MATCH"), "TARGETED_FUNDING_INVESTIGATION")
        self.assertEqual(choose_tier(
            "OUTSIDE_AWARD_TOPIC", "SAME_REPORTED_ORCID",
            "NO_STRUCTURED_AWARD_EVIDENCE", "NO_PUBLIC_IDENTITY_MATCH"),
            "LOWER_PRIORITY_ORCID_FOLLOWUP")
        self.assertEqual(choose_tier(
            "OUTSIDE_AWARD_TOPIC", "ORCID_CONFLICT",
            "NO_STRUCTURED_AWARD_EVIDENCE", "NO_PUBLIC_IDENTITY_MATCH"),
            "DEFER_OFF_TOPIC_RETAIN_LEAD")
        self.assertEqual(choose_tier(
            "DIRECT_ATMOSPHERIC_AIR_QUALITY_TOPIC", "SAME_REPORTED_ORCID",
            "EXACT_TARGET_AWARD_REGISTERED", "NO_PUBLIC_IDENTITY_MATCH"),
            "TARGET_AWARD_PROJECT_VALIDATION")

    def test_32_case_evaluation_with_one_topical_and_one_award_positive(self):
        rows = [{
            "doi": "10.1234/lead" + str(i),
            "title": "Unrelated clinical ethics " + str(i),
            "seed_reach_doi": "10.1234/seed"
        } for i in range(32)]
        rows[0]["title"] = "Air pollution and atmospheric chemistry"
        rows[1]["title"] = "Urban particulate matter emissions"
        output = {"schema": "reach-scout-public-reach-author-pilot-v1",
                  "award": AWARD, "independent_doi_leads": rows}
        documents = {"10.1234/seed": source()}
        for row in rows:
            funder = [{"name": "NOAA", "award": [AWARD]}] if row["doi"] == "10.1234/lead1" else []
            documents[row["doi"]] = candidate(
                row["doi"], row["title"], funder=funder,
                authors=[author()] if row["doi"] not in
                    {"10.1234/lead0", "10.1234/lead1"} else None)
        def meta(doi): return documents[doi]
        result = evaluate_leads(output, cache(), index(), watchlist(), {"dois": {}},
                                get_metadata=meta)
        self.assertEqual(result["rows_reviewed"], 32)
        self.assertEqual(result["tiers"]["TARGETED_FUNDING_INVESTIGATION"], 1)
        self.assertEqual(result["tiers"]["TARGET_AWARD_PROJECT_VALIDATION"], 1)
        self.assertEqual(result["tiers"]["DEFER_OFF_TOPIC_RETAIN_LEAD"], 30)
        self.assertTrue(result["no_promotion_to_discovery_hub"])
        self.assertFalse(result["spark_personnel_accessed"])
        self.assertFalse(result["author_names_saved"])
        self.assertTrue(all(r.get("hub_eligible") is False for r in result["results"]))
        self.assertNotIn("Alex Researcher", json.dumps(result))
        self.assertNotIn("Morgan Colleague", json.dumps(result))

    def test_missing_metadata_preserved_not_false_negative(self):
        rows = [{"doi": "10.1234/lead" + str(i),
                 "title": "Atmospheric air quality study " + str(i),
                 "seed_reach_doi": "10.1234/seed"} for i in range(32)]
        pilot = {"schema": "reach-scout-public-reach-author-pilot-v1",
                 "award": AWARD, "independent_doi_leads": rows}
        out = evaluate_leads(pilot, cache(), index(), watchlist(), {"dois": {}},
                             get_metadata=lambda doi: source() if doi == "10.1234/seed" else None)
        self.assertEqual(out["tiers"], {"METADATA_RETRY_REQUIRED": 32})

    def test_wrong_award_and_forged_seed_fail_closed(self):
        rows = [{"doi": "10.1234/lead" + str(i),
                 "title": "Air pollution", "seed_reach_doi": "10.1234/seed"}
                for i in range(32)]
        pilot = {"schema": "reach-scout-public-reach-author-pilot-v1",
                 "award": "NA22OAR4320515", "independent_doi_leads": rows}
        with self.assertRaisesRegex(ValueError, "Unexpected original award"):
            evaluate_leads(pilot, cache(), index(), watchlist(), {"dois": {}},
                           get_metadata=lambda _: source())
        pilot["award"] = AWARD
        pilot["independent_doi_leads"][0]["seed_reach_doi"] = "10.1234/forged"
        with self.assertRaisesRegex(ValueError, "exact-award public REACH seed"):
            evaluate_leads(pilot, cache(), index(), watchlist(), {"dois": {}},
                           get_metadata=lambda _: source())


if __name__ == "__main__":
    unittest.main()
