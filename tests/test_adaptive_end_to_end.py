from dataclasses import asdict
import json
from pathlib import Path
import unittest

from core.adaptive_artifacts import ArtifactStore
from core.artifact_review import ArtifactReviewer
from core.event_logging import reconstruct
from core.skill_artifact import validation_status, write_once
from core.skill_artifact import record_validation
from session.session_boundary import file_identity
from scenario_a.adaptive_adapter import ExecutionAdapter
from tests import test_adaptive_transitions as fixture
from tests import test_artifact_review as review_fixture


class AdaptiveEndToEndTests(unittest.TestCase):
    def setUp(self):
        fixture.AdaptiveTransitionTests.setUp(self)

    def decide(self, *args, **kwargs):
        return fixture.AdaptiveTransitionTests.decide(self, *args, **kwargs)

    def action(self, *args, **kwargs):
        return fixture.AdaptiveTransitionTests.action(self, *args, **kwargs)

    def test_two_run_synthetic_path_preserves_failure_and_accepts_only_b(self):
        a, old_workflow = self.artifact, self.workflow
        review_a = fixture.AdaptiveTransitionTests.reviewed(self)
        workflow_b = fixture.AdaptiveTransitionTests.revision(self, review_a)
        old_dir = self.session.run['directory']
        restart = fixture.AdaptiveTransitionTests.action(self, 'RESTART_PRODUCTION_RUN', review_a)
        self.session.start_run(workflow_b, restart)
        self.session.start_attempt(self.decide('CONTINUE'))
        reservation = self.session.reserve_effect('worker_calls')
        def runner(order):
            output = Path(order['output_directory']) / 'artifact-b.bin'
            output.write_bytes(b'SYNTHETIC ARTIFACT B NOT GLB')
            return {'status': 'SUCCESS', 'outputs': [str(output)], 'observations': {'synthetic': True}}
        outputs, execution = ExecutionAdapter({'fixture': runner}, mode='SYNTHETIC').execute(
            self.frozen, self.scope, workflow_b, self.session.state(), 'build', (), reservation,
            self.session.attempt['directory'] / 'execution')
        b = ArtifactStore(self.frozen, self.scope, workflow_b, self.session.state(), self.root / 'artifacts-b', mode='SYNTHETIC').register(
            'artifact-b', 'build', outputs, (), execution)
        review_b = ArtifactReviewer(review_fixture.SyntheticReview()).review(
            self.frozen, self.scope, workflow_b, b, self.root / 'review-b')
        self.session.register_review(b, review_b)
        self.session.finish_attempt('REVIEWED', (b.metadata, review_b.file))
        decision = self.decide('ACCEPT', reviews=(review_b.file,), artifacts=(b.metadata,))
        with self.assertRaisesRegex(ValueError, 'STALE'):
            self.session.accept(decision, a, review_a)
        self.session.accept(decision, b, review_b)
        self.assertEqual(self.session.boundary.outcome.status, 'INTERNAL_ACCEPT')
        self.assertEqual(json.loads((old_dir / 'terminal.json').read_text())['status'], 'SUPERSEDED')
        self.assertEqual(a.validate(self.frozen, self.scope, old_workflow)['production_run_id'], 'run-001')
        self.assertEqual(validation_status(self.skill), 'CANDIDATE')
        events = reconstruct(self.session.directory / 'logs', self.frozen.reference.session_id)
        self.assertEqual([e['event_seq'] for e in events], list(range(1, len(events) + 1)))
        self.assertEqual(len([e for e in events if e['event_type'] == 'PRODUCTION_RUN_STARTED']), 2)
        self.assertEqual(events[-1]['event_type'], 'INTERNAL_ACCEPT')
        # Forging only the outer ACTUAL label must not promote this fully
        # hash-bound but entirely synthetic accepted trajectory.
        success = self.root / 'mislabelled-success.json'
        terminal = self.root / 'fake-closed.json'
        write_once(terminal, {'status': 'CLOSED', 'session_id': self.frozen.reference.session_id})
        invocation = json.loads(Path(decision.path).read_text())['frontier_invocation_ref']
        write_once(success, {'scope': 'ACTUAL', 'INTERNAL_ACCEPT': True, 'session_terminal': 'CLOSED',
            'session_id': self.frozen.reference.session_id, 'production_run_id': 'run-002',
            'skill_refs': [asdict(self.skill)], 'review_refs': [asdict(review_b.file)],
            'frontier_invocation_refs': [invocation], 'known_limitations': ['Synthetic fixture'],
            'terminal_ref': asdict(file_identity(terminal, 'fake-terminal')),
            'acceptance_gate_ref': asdict(file_identity(self.session.directory / 'acceptance_gate.json', 'gate'))})
        with self.assertRaisesRegex(ValueError, 'ACTUAL_SUCCESS_REQUIRED'):
            record_validation(self.skill, file_identity(success, 'mislabelled'), self.root / 'promotion.json')
        self.assertFalse((self.root / 'promotion.json').exists())
        fake_validation = self.root / 'fake-validation.json'
        write_once(fake_validation, {'status': 'VALIDATED', 'skill_ref': asdict(self.skill),
            'actual_success': asdict(file_identity(success, 'mislabelled'))})
        with self.assertRaisesRegex(ValueError, 'ACTUAL_SUCCESS_REQUIRED'):
            validation_status(self.skill, file_identity(fake_validation, 'fake-validation'))


if __name__ == '__main__':
    unittest.main()
