"""Fast monthly DOI intake regression checks. No private Hub is contacted."""
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from quick_monthly_intake import AWARD, clean, match_reach, check_funding, detect_version, gather_feed, shared_identity_route

class MonthlyQuickIntakeTests(unittest.TestCase):
    def test_html_title_markup_is_removed_not_invented(self):
        self.assertEqual(clean("The <scp>Wind</scp> &amp; Waves"), "The Wind & Waves")
        self.assertIn("Skynet", clean("We &lt;3 Skynet"))

    def test_doi_secondary_field_and_exact_title_checks(self):
        index=[{"Record ID":"reach-1","Title":"Other article", "Link to Output":"https://example.org/other"}]
        details=[{"Record ID":"reach-1","Title":"Other article",
                  "Publications":"https://doi.org/10.1234/paper.1",
                  "Journal Article Link":""}]
        self.assertEqual(match_reach("10.1234/paper.1", "New article",
                                      "https://doi.org/10.1234/paper.1",index,details)[0]["reach_id"],
                         "reach-1")
        self.assertEqual(match_reach("10.1234/absent","Not here",
                                    "https://doi.org/10.1234/absent",index,details), [])

    def test_shared_identity_gate_accepts_only_unique_doi_or_url_with_matching_title(self):
        base={"source":"REACH","title":"Complete WPO article","match_bases":["exact_doi","normalized_title"]}
        shared={"status":"CONFIRMED_PUBLIC_REACH_IDENTITY","matches":[base]}
        found=[{"reach_id":"reach-1","match_basis":"exact_doi"}]
        self.assertEqual(shared_identity_route(found,shared,"Complete WPO article"),"already_in_reach")
        conflict={"status":"CONFIRMED_PUBLIC_REACH_IDENTITY",
                  "matches":[dict(base,title="Different article")]}
        self.assertEqual(shared_identity_route(found,conflict,"Complete WPO article"),"reach_identity_review")
        duplicates={"status":"CONFIRMED_PUBLIC_REACH_IDENTITY",
                    "matches":[base,dict(base,title="Complete WPO article")]}
        self.assertEqual(shared_identity_route(found,duplicates,"Complete WPO article"),"reach_identity_review")
    def test_title_only_and_scout_queue_matches_are_not_new_proposals(self):
        shared={"status":"POSSIBLE_PUBLIC_REACH_MATCH",
                "matches":[{"source":"REACH","title":"Shared title","match_bases":["normalized_title"]}]}
        self.assertEqual(shared_identity_route([],shared,"Shared title"),"reach_identity_review")
        queued={"status":"IN_PUBLIC_SCOUT_QUEUE",
                "matches":[{"source":"SCOUT_PUBLISHED","title":"Other","match_bases":["exact_doi"]}]}
        self.assertEqual(shared_identity_route([],queued,"A title"),"already_in_scout_or_inbox")
        self.assertEqual(shared_identity_route([],None,"A title"),"no_public_identity_match")

    def test_primary_award_is_needed_and_related_awards_are_ignored(self):
        row={"NOAA Award Number(s)":"NA22OAR4590179"}
        spark=[{"Record ID":"spark-1","Award Number(s)":"NA22OAR4590179",
                "Related Award Number(s)":"NA23OAR4599999"}]
        c,status,issues=check_funding(row,{},spark)
        self.assertEqual(status,"primary_award_matched")
        _,status,_=check_funding({"NOAA Award Number(s)":"NA23OAR4599999"},{},spark)
        self.assertEqual(status,"unmatched_primary_award")

    def test_fy25_oarx_task_award_preserved_and_not_confused_with_siblings(self):
        full = "NA25OARX459C0342-T1-01"
        sibling = "NA25OARX459C0342-T1-02"
        base = "NA25OARX459C0342"
        self.assertEqual(AWARD.findall("Grant no. " + full + "; NA22NWS4320003"),
                         [full, "NA22NWS4320003"])
        spark = [
            {"Record ID": "spark-fy25-a", "Award Number(s)": full},
            {"Record ID": "spark-fy25-b", "Award Number(s)": sibling},
        ]
        candidates, status, _ = check_funding(
            {"NOAA Award Number(s)": full}, {}, spark)
        self.assertEqual(status, "primary_award_matched")
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["Record ID"], "spark-fy25-a")
        # A base FAIN alone cannot uniquely name a WPO task.
        _, status, _ = check_funding(
            {"NOAA Award Number(s)": base}, {}, spark)
        self.assertEqual(status, "unmatched_primary_award")

    def test_explicit_contradiction_is_held_but_missing_grant_proof_is_not(self):
        spark=[{"Record ID":"spark-1","Award Number(s)":"NA22OAR4590179"}]
        row={"NOAA Award Number(s)":"NA22OAR4590179"}
        negative={"substantive_research":{"funding_assessment":{
            "same_project_verified":False,"reason":"Article objectives differ from project"}}}
        _,status,_=check_funding(row,negative,spark)
        self.assertEqual(status,"funding_anomaly")
        uncertain={"substantive_research":{"funding_assessment":{
            "same_project_verified":False,"basis":"Article's grant acknowledgment not yet found"}}}
        _,status,_=check_funding(row,uncertain,spark)
        self.assertEqual(status,"primary_award_matched")

    def test_prior_cross_cohort_version_review_is_preserved(self):
        case={"substantive_research":{"identity_and_related_outputs":{
            "historical_review_unit":"zenodo-mom6","concept_doi":"10.1234/first",
            "version_doi":"10.1234/second"}}}
        self.assertEqual(detect_version(case,"10.1234/second"),
                         "existing_historical_review_family")

    def test_source_sha_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"manifest.json").write_text(json.dumps({
                "batches":[{"path":"batches/test.csv","sha256":"0"*64,"record_count":1}]}))
            p=root/"batches/test.csv"
            p.parent.mkdir()
            p.write_text("DOI,Title\n10.1234/x,Test\n")
            with self.assertRaisesRegex(ValueError, "Source SHA mismatch"):
                gather_feed(root,"","manifest.json",None)



class MonthlyRoutingIntegrationTests(unittest.TestCase):
    def test_routes_only_distinct_verified_sources_and_does_not_repeat_inbox(self):
        import csv
        from unittest.mock import patch
        import quick_monthly_intake as intake

        award = "NA22OAR4590179"
        project = {"Record ID": "spark-1", "Award Number(s)": award, "Project Title": "Project"}
        variants = [
            ("full", {}, {}, "NEW CANDIDATE"),
            ("abstract-gap", {"Brief Abstract": ""}, {}, "NEEDS INVESTIGATION"),
            ("unresolved-funding", {}, {"funding_assessment": {"same_project_verified": False}}, "NEEDS INVESTIGATION"),
            ("preprint", {}, {}, None),
            ("registry-only", {}, {}, None),
            ("version", {}, {}, None),
            ("reviewed", {}, {}, None),
            ("duplicate", {}, {}, None),
            ("alias", {}, {}, None),
            ("contradiction", {}, {"funding_assessment": {"reason": "objectives differ"}}, None),
            ("no-date", {"Publication Date": ""}, {}, None),
            ("bad-source", {"Funding Evidence URL": "https://example.org/unsupported"}, {}, None),
        ]
        rows, entries = [], []
        for name, changes, research, expected in variants:
            doi = "10.1234/" + name
            source = "https://api.crossref.org/works/" + doi
            basis = ("registration_only_publication_unverified;reach_pub_date_datacite_created"
                     if name == "registry-only" else "published_exact")
            note = {"preprint": "\nAPI publication status: Preprint",
                    "version": "\nAPI explicit version relationship: present",
                    "alias": "\nAPI output alias: https://example.org/publication"}.get(name, "")
            rows.append({"DOI": doi, "Title": "Fixture study " + name, "Output Type": "1",
                         "Publication Date": "2026-11-17", "Authors / PI": "Researcher",
                         "Brief Abstract": "Available abstract of this test fixture.",
                         "Output URL": "https://doi.org/" + doi, "Evidence URL": source,
                         "Funding Evidence URL": source, "NOAA Award Number(s)": award,
                         "Scout Discovery Rationale": "API date basis: " + basis + note, **changes})
            entries.append({"source_batch_id": "2026-12-01-monthly-api-2026-11-part001",
                            "identity": "doi:" + doi, "cohort": "2026-11",
                            "status": "awaiting_research", "substantive_research": research})

        project_root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "scout-operations").mkdir()
            (root / "scout-discoveries/inbox").mkdir(parents=True)
            (root / "scout-discoveries/tools").symlink_to(project_root / "scout-discoveries/tools")
            (root / "api-discoveries").mkdir()
            source_file = root / "api-discoveries/fixture.csv"
            with source_file.open("w", newline="") as data:
                writer = csv.DictWriter(data, fieldnames=rows[0])
                writer.writeheader()
                writer.writerows(rows)

            def save(relative, obj):
                (root / relative).write_text(json.dumps(obj))

            save("api-discoveries/manifest.json", {"batches": [{
                "id": entries[0]["source_batch_id"], "path": "api-discoveries/fixture.csv",
                "record_count": len(rows), "sha256": hashlib.sha256(source_file.read_bytes()).hexdigest()
            }]})
            save("scout-operations/monthly-triage.json", {"entries": entries})
            save("scout-operations/preprint-watchlist.json",
                 {"schema": "reach-scout-preprint-watchlist-v1", "entries": []})
            save("scout-operations/preprint-retirement-archive.json",
                 {"schema": "reach-scout-preprint-retirement-archive-v1", "entries": []})
            digest = "a" * 64
            index = {"schema": "reach-scout-identity-index-v1",
                     "sources": {"reach_manifest_sha256": digest}, "source_fingerprint": digest}
            no_match = {"status": "NO_MATCH", "matches": []}

            def lookup(_index, doi="", title="", url=""):
                if url == "https://example.org/publication" or doi == "10.1234/duplicate":
                    return {"status": "CONFIRMED_PUBLIC_REACH_IDENTITY", "matches": [{
                        "source": "REACH", "title": "Fixture study duplicate",
                        "match_bases": ["exact_doi", "normalized_title"]
                    }]}
                return no_match

            with (patch.object(intake, "load_external", return_value=([], [], [project], digest, digest)),
                  patch.object(intake, "shared_build_index", return_value=index),
                  patch.object(intake, "shared_lookup", side_effect=lookup),
                  patch.object(intake, "shared_disposition", return_value={
                      "disposition": "NO_PUBLIC_IDENTITY_MATCH", "explicit_version_family": None}),
                  patch.object(intake, "gather_feed", return_value=([], digest)),
                  patch.object(intake, "reviewer_hold_for_proposal",
                               side_effect=lambda doi, _: {} if doi.endswith("/reviewed") else None)):
                report = intake.build(root, root, root, write_drafts=True)
                by_name = {o["identity"].split("/")[-1]: o for o in report["originals"]}
                for name, _, _, expected in variants:
                    self.assertEqual(by_name[name]["classification"], expected, name)
                self.assertEqual(len(report["draft_paths_created"]), 3)
                for path in report["draft_paths_created"]:
                    row = intake.rows_from_csv(root / path)[0]
                    self.assertEqual(len(row), 24)
                    self.assertEqual(row["Candidate ID"], "")
                self.assertEqual(by_name["reviewed"]["status"], "prior_human_review_requires_reconciliation")
                self.assertEqual(by_name["alias"]["status"], "alternate_identity_review")
                self.assertEqual(by_name["registry-only"]["status"], "unverified_publication")
                replay = intake.build(root, root, root, write_drafts=True)
                self.assertEqual(replay["draft_paths_created"], [])

            # Exercise the real public promotion boundary with a synthetic
            # publication verdict. No rows are imported into the private Hub.
            import promote_inbox as promotion
            import os

            inbox = root / "scout-discoveries/inbox"
            batches = root / "scout-discoveries/batches"
            with (patch.object(promotion, "REPO", root),
                  patch.object(promotion, "INBOX", inbox),
                  patch.object(promotion, "BATCHES", batches),
                  patch.dict(os.environ, {"SCOUT_PREPRINT_GATE_REQUIRED": "1"})):
                with self.assertRaisesRegex(ValueError, "gate report missing"):
                    promotion.promote()
                self.assertFalse(batches.exists())
                save("scout-operations/preprint-intake-gate.json", {
                    "schema": "reach-scout-preprint-intake-gate-v1",
                    "checks": [{"path": path, "verdict": "eligible",
                                "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()}
                               for path in report["draft_paths_created"]],
                })
                promotion.promote()
                first = {p.name: p.read_bytes() for p in batches.glob("*.csv")}
                self.assertEqual(len(first), 3)
                promotion.promote()
                self.assertEqual(first, {p.name: p.read_bytes() for p in batches.glob("*.csv")})



if __name__ == "__main__":
    unittest.main()
