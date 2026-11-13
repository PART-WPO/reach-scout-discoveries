"""Offline regression tests for source-review proposal consistency, not scheduler tests."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from gold_proposal import (
    SUPPORTED, UNREVIEWED, TIER, apply_source_review, pair_key,
    read_csv, synchronize_files, validate_files, validate_rows, write_csv,
)

DIRECTORY = Path(__file__).resolve().parent


def fixtures():
    candidates = read_csv(DIRECTORY / 'artifact-first-gold-candidates.csv')
    proposal = read_csv(DIRECTORY / 'gold-source-reviewed.csv')
    proposal = [{**row, 'gold_state': SUPPORTED} for row in proposal]
    return apply_source_review(candidates, proposal), proposal


class GoldProposalTests(unittest.TestCase):
    def test_actual_38_candidates_and_written_10_pair_proposal_agree(self):
        result = validate_files(DIRECTORY)
        self.assertEqual(result['candidate_pairs'], 38)
        self.assertEqual(result['source_supported_proposal_pairs'], 10)
        self.assertEqual(result['source_reviewed_relation_basis'], {
            'EXPLICIT_TYPED_SUPPORT_RELATION': 4,
            'DOCUMENT_DOI_MENTION_REQUIRES_REVIEW': 6,
        })

    def test_historical_wrong_ten_pair_set_is_rejected_despite_equal_counts(self):
        candidates, proposal = fixtures()
        for row in candidates:
            explicit = row['evidence_class'] in {
                'EXPLICIT_TYPED_SUPPORT_RELATION',
                'EXPLICIT_RELATION_REQUIRES_ROLE_REVIEW',
            }
            row['gold_state'] = SUPPORTED if explicit else UNREVIEWED
        self.assertEqual(sum(r['gold_state'] == SUPPORTED for r in candidates), len(proposal))
        with self.assertRaisesRegex(ValueError, 'Supported pair sets differ'):
            validate_rows(candidates, proposal)

    def test_citation_derivation_and_even_typed_relation_do_not_select_without_review(self):
        candidates, _ = fixtures()
        result = apply_source_review(candidates, [])
        self.assertTrue(any(r['relation'] == 'IsCitedBy' for r in result))
        self.assertTrue(any(r['relation'] == 'IsDerivedFrom' for r in result))
        self.assertTrue(any(r['relation'] == 'IsSupplementTo' for r in result))
        self.assertTrue(all(r['gold_state'] == UNREVIEWED for r in result))
        self.assertTrue(all(r['claim_tier'] == 'unverified' for r in result))

    def test_documented_pairs_require_written_reasons(self):
        candidates, proposal = fixtures()
        reviewed = next(r for r in proposal if r['evidence_class'] == 'DOCUMENT_DOI_MENTION_REQUIRES_REVIEW')
        reviewed['review_reason'] = '  '
        with self.assertRaisesRegex(ValueError, 'Missing written'):
            apply_source_review(candidates, proposal)

    def test_changed_source_cannot_reuse_a_pair_review(self):
        candidates, proposal = fixtures()
        proposal[0]['source'] = 'changed-source.json:1'
        with self.assertRaisesRegex(ValueError, 'evidence changed'):
            apply_source_review(candidates, proposal)

    def test_unknown_or_duplicate_proposal_members_are_rejected(self):
        candidates, proposal = fixtures()
        with self.assertRaisesRegex(ValueError, 'Duplicate proposal'):
            apply_source_review(candidates, proposal + [proposal[0]])
        proposal[0]['paper_doi'] = '10.1234/different-work'
        with self.assertRaisesRegex(ValueError, 'absent from candidates'):
            apply_source_review(candidates, proposal)

    def test_label_sync_preserves_members_reasons_and_human_uncertainty(self):
        candidates, proposal = fixtures()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            # Mimic stale displayed states without changing the proposal membership.
            for row in candidates:
                row['gold_state'] = UNREVIEWED
            for row in proposal:
                row['gold_state'] = UNREVIEWED
            write_csv(directory / 'artifact-first-gold-candidates.csv', candidates)
            write_csv(directory / 'gold-source-reviewed.csv', proposal)
            before = copy.deepcopy(proposal)
            result = synchronize_files(directory)
            after = read_csv(directory / 'gold-source-reviewed.csv')
            self.assertEqual(result['source_supported_proposal_pairs'], 10)
            self.assertEqual([pair_key(r) for r in before], [pair_key(r) for r in after])
            self.assertEqual([r['review_reason'] for r in before], [r['review_reason'] for r in after])
            self.assertTrue(all(r['human_adjudication'] == 'NOT_DETERMINED' for r in after))

    def test_summary_cannot_drift_from_the_reviewed_set(self):
        candidates, proposal = fixtures()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_csv(directory / 'artifact-first-gold-candidates.csv', candidates)
            write_csv(directory / 'gold-source-reviewed.csv', proposal)
            summary = json.loads((DIRECTORY / 'gold-rebuild-summary.json').read_text())
            summary['source_reviewed_relationship_pairs'] = 11
            (directory / 'gold-rebuild-summary.json').write_text(json.dumps(summary))
            with self.assertRaisesRegex(ValueError, 'summary disagrees'):
                validate_files(directory)

    def test_no_human_adjudication_is_created_by_support_flags(self):
        candidates, proposal = fixtures()
        self.assertTrue(all(r['human_adjudication'] == 'NOT_DETERMINED' for r in candidates + proposal))
        self.assertTrue(all(r['claim_tier'] == TIER for r in candidates if r['gold_state'] == SUPPORTED))
        candidates[0]['human_adjudication'] = 'APPROVED'
        with self.assertRaisesRegex(ValueError, 'human adjudication'):
            validate_rows(candidates, proposal)


if __name__ == '__main__':
    unittest.main()
