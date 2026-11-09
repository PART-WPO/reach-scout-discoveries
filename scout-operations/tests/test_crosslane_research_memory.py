"""Source-verified historical discovery graph never collapses distinct expansion."""
import json
import sys
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_crosslane_research_memory import (
    build, source_links, metadata_pointers, ROOT, SCHEMA,
)
from decision_pipeline import norm_doi


class CrosslaneMemoryTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.graph = build()

    def test_all_historical_and_related_source_lanes_preserved(self):
        g = self.graph
        self.assertEqual(g["schema"], SCHEMA)
        self.assertEqual(g["preflighted_lane_doi_records"], 827)
        for lane, minimum in (("historical_crossref", 614),
                              ("historical_datacite", 188),
                              ("monthly_api", 13),
                              ("monthly_related_outputs", 6),
                              ("independent", 6)):
            self.assertEqual(g["lane_doi_counts"][lane], minimum)
        self.assertEqual(sum(g["lane_doi_counts"].values()), 827)
        self.assertEqual(g["historical_note_events_reused_as_context"], 50)
        self.assertGreater(g["explicit_related_output_links"], 0)
        self.assertEqual(len(g["nodes"]), g["distinct_public_doi_nodes"])
        self.assertEqual(len(g["links"]), g["explicit_related_output_links"])
        self.assertEqual(g["historical_metadata_pointers_not_treated_as_current"] >= 0, True)

    def test_all_426_reach_verified_seeds_keep_expansion_even_when_original_screened(self):
        g = self.graph
        self.assertEqual(g["verified_reach_originals_preserved_as_expansion_seeds"], 426)
        original = {x["doi"]: x for x in g["work_items"] if x["track"] == "ORIGINAL"}
        expansions = {x["doi"]: x for x in g["work_items"] if x["track"] == "EXPANSION"}
        reach_seeds = [x for x in g["nodes"] if x["public_reach_verified_existing"]]
        self.assertEqual(len(reach_seeds), 426)
        for node in reach_seeds:
            d = node["doi"]
            self.assertEqual(original[d]["next_action"],
                             "REUSE_VERIFIED_REACH_IDENTITY_NO_DUPLICATE_ORIGINAL")
            self.assertEqual(expansions[d]["next_action"], "EXPAND_VERIFIED_WPO_REACH_SEED")
            self.assertFalse(original[d]["complete"])
            self.assertFalse(expansions[d]["complete"])
        self.assertEqual(g["expansions_closed_by_memory"], 0)

    def test_original_evidence_reuse_does_not_claim_funding_reviewer_or_stage(self):
        g = self.graph
        self.assertEqual(g["originals_closed_by_memory"], 0)
        self.assertEqual(g["human_reviewer_decisions_changed"], 0)
        self.assertEqual(g["hub_records_automatically_staged"], 0)
        self.assertEqual(g["new_reach_publications"], 0)
        self.assertTrue(g["read_only"])
        self.assertFalse(g["public_author_names_or_spark_personnel_indexed"])
        self.assertTrue(all(n["funding_and_same_project_inference"] == "NOT_VERIFIED_BY_MEMORY"
                            and not n["reviewer_approved"] and
                            n["private_hub_status"] == "NOT_VERIFIED" for n in g["nodes"]))
        self.assertTrue(all(x["private_hub_import"] == "NOT_VERIFIED"
                            and not x["funded_by_same_wpo_project"] == True
                            and not x["separate_expansion_complete"] for x in g["links"]))
        # Explicitly prevent person names, email addresses, and speculative
        # author or investigator fields in graph node/edge records.
        for x in g["nodes"] + g["links"] + g["work_items"]:
            self.assertFalse({"authors", "creators", "pi", "collaborators",
                              "email", "investigator"} & set(x))
        for node in g["nodes"]:
            self.assertTrue(node["no_authors_or_spark_personnel_in_graph"])

    def test_research_journal_note_is_reusable_only_as_nonterminal_provenance(self):
        g = self.graph
        journal_nodes = [n for n in g["nodes"]
                         if n["original_research"]["recorded_note_count"] > 0]
        self.assertGreater(len(journal_nodes), 7)
        self.assertTrue(all(n["original_research"]["reuse_prior_notes_before_new_queries"]
                            and not n["original_research"]["formal_original_closed_by_memory"]
                            for n in journal_nodes))
        self.assertTrue(all(
            len(x["source_evidence_file_sha256"]) == x["recorded_note_count"]
            for x in (n["original_research"] for n in journal_nodes)))
        self.assertTrue(all(n["expansion_research"]["separate_expansion_closed_by_memory"] is False
                            for n in journal_nodes))

    def test_explicit_related_child_link_preserved_and_research_remains_open(self):
        g = self.graph
        self.assertGreater(g["explicit_related_output_links"], 1)
        target = next(x for x in g["links"]
                      if x["related_doi"] == "10.1177/10506519261455873")
        self.assertEqual(target["source_doi"], "10.5194/egusphere-2026-5876")
        self.assertTrue(target["source_files"])
        self.assertFalse(target["proven_distinct_eligible_output"])
        self.assertFalse(target["separate_expansion_complete"])
        self.assertTrue(any(x["track"] == "RELATED_OUTPUT"
                            and x["doi"] == target["related_doi"]
                            for x in g["work_items"]))

    def test_new_relation_changes_expansion_evidence_not_original_identity(self):
        baseline = self.graph
        seed = next(x["doi"] for x in baseline["nodes"]
                    if x["public_reach_verified_existing"])
        baseline_node = next(x for x in baseline["nodes"] if x["doi"] == seed)
        edges, shas = source_links(ROOT)
        extra = "10.9999/new-independent-dataset"
        self.assertNotIn((seed, extra), edges)
        edges[(seed, extra)] = {
            ("scout-operations/monthly-expansion-leads.json", "monthly_related_outputs")}
        self.assertIn("scout-operations/monthly-expansion-leads.json", shas)
        with patch("build_crosslane_research_memory.source_links", return_value=(edges, shas)):
            changed = build()
        node = next(x for x in changed["nodes"] if x["doi"] == seed)
        self.assertEqual(node["original_research"]["input_fingerprint"],
                         baseline_node["original_research"]["input_fingerprint"])
        self.assertNotEqual(node["expansion_research"]["input_fingerprint"],
                            baseline_node["expansion_research"]["input_fingerprint"])
        self.assertIn(extra, node["expansion_research"]["explicit_related_dois"])
        self.assertTrue(any(x["track"] == "RELATED_OUTPUT"
                            and x["doi"] == extra for x in changed["work_items"]))

    def test_tampering_a_research_note_fails_closed(self):
        root = ROOT
        from build_research_outcome_registry import build as journal
        registry = journal()
        with patch("build_crosslane_research_memory.research_registry") as fake:
            fake.return_value = registry.copy()
            shas = dict(registry["source_sha256"])
            target = next(iter(shas))
            shas[target] = "0" * 64
            fake.return_value["source_sha256"] = shas
            with self.assertRaisesRegex(ValueError, "source changed"):
                build(root)

    def test_deterministic_replay_ignores_wall_clock(self):
        self.assertEqual(build()["source_fingerprint"], self.graph["source_fingerprint"])
        self.assertEqual(build()["work_action_counts"], self.graph["work_action_counts"])
        self.assertEqual(build()["nodes"], self.graph["nodes"])


if __name__ == "__main__":
    unittest.main()
