from dataclasses import asdict
import json
from pathlib import Path
import unittest

from core.adaptive_artifacts import ArtifactStore
from core.artifact_review import ArtifactReviewer
from core.frontier import InferenceResult
from core.skill_artifact import write_once
from session.session_boundary import file_identity
from tests import test_adaptive_loop as fixture


class SyntheticReview:
    def __init__(self, verdict='PASS', outcomes=('MET', 'MET')):
        self.verdict, self.outcomes = verdict, outcomes
        self.context = None

    def __call__(self, request, schema, directory, images):
        self.context = json.loads(Path(request.path).read_text())
        write_once(directory / 'result.json', {'verdict': self.verdict, 'reason_summary': 'Synthetic independent review.',
            'criterion_results_json': json.dumps([{'criterion_id': c, 'outcome': o, 'reason': 'fixture'}
                for c, o in zip(self.context['applicable_criterion_ids'], self.outcomes)]),
            'requested_evidence_json': '[]'})
        result = file_identity(directory / 'result.json', 'synthetic-review-result')
        write_once(directory / 'invocation.json', {'status': 'SUCCESS', 'mode': 'SYNTHETIC',
            'request_ref': asdict(request), 'result_ref': asdict(result), 'model_identity': None})
        return InferenceResult(result, file_identity(directory / 'invocation.json', 'synthetic-review-invocation'), 'SYNTHETIC', None)


class ArtifactReviewTests(unittest.TestCase):
    def setUp(self):
        fixture.AdaptiveLoopTests.setUp(self)
        fixture.AdaptiveLoopTests.begin(self)
        output = self.root / 'geometry.bin'
        output.write_bytes(b'SYNTHETIC NOT ACTUAL GLB')
        self.output = file_identity(output, 'geometry')
        report = self.root / 'execution.json'
        write_once(report, {'status': 'SUCCESS', 'mode': 'SYNTHETIC', 'state': self.session.state(),
            'workflow_ref': asdict(self.workflow), 'stage_id': 'build', 'output_refs': [asdict(self.output)], 'input_refs': []})
        self.store = ArtifactStore(self.frozen, self.scope, self.workflow, self.session.state(), self.root / 'artifacts', mode='SYNTHETIC')
        self.artifact = self.store.register('geometry-a', 'build', (self.output,), (), file_identity(report, 'execution'))

    def decide(self, *args, **kwargs):
        return fixture.AdaptiveLoopTests.decide(self, *args, **kwargs)

    def test_independent_applicable_review_has_no_execution_authority(self):
        adapter = SyntheticReview()
        result = ArtifactReviewer(adapter).review(self.frozen, self.scope, self.workflow, self.artifact, self.root / 'review')
        self.assertEqual(result.validate(self.frozen, self.scope, self.workflow, self.artifact)['verdict'], 'PASS')
        self.assertEqual(adapter.context['applicable_criterion_ids'], ['form', 'opening'])
        self.assertEqual(self.session.resources.remaining()['used']['worker_calls'], 0)

    def test_mutation_and_stale_lineage_cannot_authorize(self):
        wrong = {**self.session.state(), 'production_run_id': 'run-002'}
        with self.assertRaisesRegex(ValueError, 'STALE_ARTIFACT'):
            self.artifact.validate(self.frozen, self.scope, self.workflow, state=wrong)
        Path(self.output.path).write_bytes(b'changed')
        with self.assertRaises(ValueError):
            ArtifactReviewer(SyntheticReview()).review(self.frozen, self.scope, self.workflow, self.artifact, self.root / 'invalid')
        self.assertFalse((self.root / 'invalid').exists())

    def test_missing_criterion_and_unmet_pass_are_rejected(self):
        for name, adapter, reason in [('missing', SyntheticReview(outcomes=('MET',)), 'COVERAGE'),
                ('unmet', SyntheticReview(outcomes=('MET', 'UNCERTAIN')), 'UNMET')]:
            with self.assertRaisesRegex(ValueError, reason):
                ArtifactReviewer(adapter).review(self.frozen, self.scope, self.workflow, self.artifact, self.root / name)
            self.assertFalse((self.root / name / 'review.json').exists())

    def test_semantic_revise_is_retained_without_terminal_or_restart(self):
        review = ArtifactReviewer(SyntheticReview('REVISE', ('MET', 'UNMET'))).review(
            self.frozen, self.scope, self.workflow, self.artifact, self.root / 'revise')
        self.assertEqual(review.validate(self.frozen, self.scope, self.workflow, self.artifact)['verdict'], 'REVISE')
        self.assertEqual(self.session.state()['production_run_id'], 'run-001')
        self.assertFalse(self.session.boundary.outcome.terminal)

    def test_wrong_execution_report_rejects_before_artifact_metadata(self):
        report = self.root / 'forged.json'
        write_once(report, {'status': 'SUCCESS', 'mode': 'ACTUAL'})
        with self.assertRaisesRegex(ValueError, 'LINEAGE'):
            self.store.register('forged', 'build', (self.output,), (), file_identity(report, 'forged'))
        self.assertFalse((self.root / 'artifacts/forged.json').exists())


if __name__ == '__main__':
    unittest.main()
