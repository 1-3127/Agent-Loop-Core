from dataclasses import asdict
import json
from pathlib import Path
import unittest

from core.adaptive_artifacts import ArtifactStore
from core.artifact_review import ArtifactReviewer
from core.skill_artifact import write_once
from core.workflow_artifact import WorkflowRef
from session.session_boundary import FileIdentity, file_identity
from tests import test_artifact_review as fixture


def workflow_from(data):
    value = dict(data)
    value['file'] = FileIdentity(**value['file'])
    return WorkflowRef(**value)


class AdaptiveTransitionTests(unittest.TestCase):
    def setUp(self):
        fixture.ArtifactReviewTests.setUp(self)

    def decide(self, *args, **kwargs):
        return fixture.ArtifactReviewTests.decide(self, *args, **kwargs)

    def reviewed(self, verdict='REVISE', outcomes=('MET', 'UNMET'), name='review-a'):
        review = ArtifactReviewer(fixture.SyntheticReview(verdict, outcomes)).review(
            self.frozen, self.scope, self.workflow, self.artifact, self.root / name)
        self.session.register_review(self.artifact, review)
        self.session.finish_attempt('REVIEWED', (self.artifact.metadata, review.file))
        return review

    def action(self, action, review, proposal=None):
        return self.decide(action, proposal, reviews=(review.file,), artifacts=(self.artifact.metadata,))

    def revision(self, review):
        self.proposal['version'] = 2
        self.proposal['stages'][0]['parameters'] = {'strategy': 'target isolation before reconstruction'}
        decision = self.action('REVISE_WORKFLOW', review, self.proposal)
        workflow = workflow_from(json.loads(Path(decision.path).read_text())['selected_workflow_ref'])
        self.session.revise_workflow(workflow, decision)
        return workflow

    def test_revise_workflow_requires_explicit_restart_and_preserves_run(self):
        review = self.reviewed()
        workflow = self.revision(review)
        self.assertEqual(self.session.state()['production_run_id'], 'run-001')
        self.assertEqual(self.session.run['workflow'].version, 1)
        with self.assertRaisesRegex(ValueError, 'CURRENT_RUN'):
            self.session.start_attempt(self.action('REVISE_ARTIFACT', review))
        # A fresh inference explicitly selects the already materialized v2.
        decision = self.action('RESTART_PRODUCTION_RUN', review)
        self.assertEqual(json.loads(Path(decision.path).read_text())['selected_workflow_ref'], asdict(workflow))
        old_directory = self.session.run['directory']
        self.session.start_run(workflow, decision)
        self.assertEqual(self.session.state()['production_run_id'], 'run-002')
        self.assertEqual(json.loads((old_directory / 'terminal.json').read_text())['status'], 'SUPERSEDED')
        self.assertEqual(self.session.current_reviews, {})
        self.session.start_attempt(self.decide('CONTINUE'))
        with self.assertRaisesRegex(ValueError, 'STALE'):
            self.session.register_review(self.artifact, review)
        self.assertTrue(Path(self.artifact.metadata.path).exists())

    def test_current_pass_accepts_and_stale_or_unmet_review_cannot(self):
        review = self.reviewed('PASS', ('MET', 'MET'))
        decision = self.action('ACCEPT', review)
        accepted = self.session.accept(decision, self.artifact, review)
        self.assertTrue(accepted.path.endswith('internal_accept.json'))
        self.assertEqual(self.session.boundary.outcome.status, 'INTERNAL_ACCEPT')
        with self.assertRaisesRegex(ValueError, 'ACCEPTED'):
            self.session.reserve_effect('worker_calls')

    def test_accept_unmet_or_omitted_current_evidence_is_rejected(self):
        review = self.reviewed()
        with self.assertRaisesRegex(ValueError, 'UNMET'):
            self.session.accept(self.action('ACCEPT', review), self.artifact, review)
        with self.assertRaisesRegex(ValueError, 'MISSING_CURRENT'):
            self.session.accept(self.decide('ACCEPT'), self.artifact, review)
        self.assertFalse((self.session.directory / 'internal_accept.json').exists())

    def test_evidence_acquisition_reserves_without_worker_or_restart(self):
        review = self.reviewed('REVISE', ('MET', 'UNCERTAIN'))
        self.session.acquire_evidence(self.action('ACQUIRE_EVIDENCE', review))
        self.assertEqual(self.session.resources.remaining()['used']['diagnostic_calls'], 1)
        self.assertEqual(self.session.resources.remaining()['used']['worker_calls'], 0)
        self.assertEqual(self.session.state()['attempt_id'], 'attempt-001')

    def test_forged_action_cannot_replace_model_inference(self):
        review = self.reviewed()
        decision = self.action('ACQUIRE_EVIDENCE', review)
        data = json.loads(Path(decision.path).read_text())
        data['selected_action'] = 'ACCEPT'
        target = self.root / 'forged-decision.json'
        write_once(target, data)
        with self.assertRaisesRegex(ValueError, 'RESULT_MISMATCH'):
            self.session.accept(file_identity(target, 'forged-decision'), self.artifact, review)


if __name__ == '__main__':
    unittest.main()
