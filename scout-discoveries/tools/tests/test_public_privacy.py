"""Privacy checks for Scout's public discovery-feed boundary."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from public_privacy import check_public_metadata

class PublicPrivacyTests(unittest.TestCase):
    def test_allowed_research_metadata_and_noaa_award(self):
        row = {
            "Title": "An analysis of severe weather warnings",
            "Authors / PI": "A. Researcher; B. Meteorologist",
            "Principal Investigators": "A. Researcher",
            "NOAA Award Number(s)": "NA25OAR4590001-01",
            "DOI": "10.1175/WAF-D-26-0001.1",
            "Brief Abstract": "Public analysis of communication and alerts.",
            "Evidence URL": "https://doi.org/10.1175/WAF-D-26-0001.1",
            "Scout Discovery Rationale": "Reviewer question: Is the award supported by public evidence?",
        }
        self.assertTrue(check_public_metadata(row))

    def test_reviewer_email_anywhere_is_blocked_without_leaking_value(self):
        for field in ("Brief Abstract", "Scout Discovery Rationale", "Output URL"):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "email address") as err:
                    check_public_metadata({field: "Contact analyst@example.org"}, "draft.csv", 2)
                self.assertNotIn("analyst@example.org", str(err.exception))

    def test_internal_reviewer_and_row_metadata_are_blocked(self):
        for s in ("Reviewer Decision: On Hold", "Review Notes: reviewer rationale",
                  "Created Row ID: 123456789", "Decision Fingerprint: abc",
                  "Reviewed At: 2026-11-06T15:00:00Z"):
            with self.subTest(s=s):
                with self.assertRaises(ValueError):
                    check_public_metadata({"Scout Discovery Rationale": s})

    def test_private_only_column_cannot_be_added(self):
        with self.assertRaisesRegex(ValueError, "internal field"):
            check_public_metadata({"Reviewer Email": ""})

    def test_auth_and_signed_links_blocked(self):
        for s in ("Bearer " + "a"*40,
                  "https://example.org/file?access_token=" + "a"*30,
                  "github_pat_" + "p"*30):
            with self.subTest(prefix=s[:14]):
                with self.assertRaises(ValueError):
                    check_public_metadata({"Funding Evidence URL": s})

    def test_private_tracker_links_blocked(self):
        with self.assertRaisesRegex(ValueError, "private tracker URL"):
            check_public_metadata({"Evidence URL":"https://app.smartsheetgov.com/b/home?test=1"})

    def test_public_url_and_question_not_mistaken_for_reviewer_data(self):
        self.assertTrue(check_public_metadata({
            "Brief Abstract": "A journal article where reviewers evaluate model skill.",
            "Scout Discovery Rationale": "Reviewer question: Is this a distinct deliverable?",
            "IR Repository URL": "https://repository.library.noaa.gov/view/noaa/70182",
        }))

if __name__ == "__main__":
    unittest.main()
