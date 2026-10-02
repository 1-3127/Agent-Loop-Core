import json
from pathlib import Path
from dataclasses import asdict
import unittest

from core.adaptive_loop import AdaptiveSession, LIMITS
from core.frontier import FrontierSupervisor, InferenceResult
from core.skill_artifact import canonical_bytes, write_once
from session.session_boundary import file_identity, freeze_specification
from tests import test_workflow_artifact as fixture


class SyntheticInference:
    def __init__(self, action, proposal=None):
        self.action, self.proposal = action, proposal

    def __call__(self, request, schema, directory, images):
        write_once(directory / 'result.json', {'selected_action': self.action, 'reason_summary': 'Synthetic contract fixture.',
            'workflow_proposal_json': json.dumps(self.proposal) if self.proposal else None,
            'action_parameters_json': None, 'new_skill_proposals_json': None})
        result = file_identity(directory / 'result.json', 'synthetic-result')
        write_once(directory / 'invocation.json', {'status': 'SUCCESS', 'mode': 'SYNTHETIC',
            'request_ref': asdict(request), 'result_ref': asdict(result), 'model_identity': None})
        return InferenceResult(result, file_identity(directory / 'invocation.json', 'synthetic-invocation'), 'SYNTHETIC', None)


class AdaptiveLoopTests(unittest.TestCase):
    def setUp(self):
        fixture.WorkflowArtifactTests.setUp(self)
        self.limits = dict.fromkeys(LIMITS, 4)
        path = Path(self.frozen.reference.specification_path)
        path.write_bytes(path.read_bytes() + b'\n' + canonical_bytes({'resource_limits': self.limits, 'deadline_seconds': None}))
        self.frozen = freeze_specification(path, self.frozen.fields)
        # Scope must be bound after the final specification bytes are frozen.
        from core.workflow_artifact import freeze_workflow_scope
        self.scope = freeze_workflow_scope(self.frozen, self.root / 'scope-final.json', self.mapping, 'geometry')
        self.session = AdaptiveSession(self.frozen, self.scope, self.root / 'session', self.limits, mode='SYNTHETIC')
        self.decision_count = 0

    def decide(self, action, proposal=None, reviews=(), artifacts=()):
        self.decision_count += 1
        return FrontierSupervisor(SyntheticInference(action, proposal)).decide(self.frozen, self.scope,
            state=self.session.state(), workflow=self.session.run['workflow'] if self.session.run else None,
            reviews=reviews, artifacts=artifacts, skills=(self.skill,), capabilities=['geometry'],
            envelope=self.session.resources.remaining(), directory=self.root / ('decision-%d' % self.decision_count),
            planner=self.planner, workflow_output=self.root / ('workflow-%d.json' % self.decision_count))

    def begin(self):
        from core.workflow_artifact import WorkflowRef
        decision = self.decide('PLAN_WORKFLOW', self.proposal)
        workflow = json.loads(Path(decision.path).read_text())['selected_workflow_ref']
        from session.session_boundary import FileIdentity
        workflow['file'] = FileIdentity(**workflow['file'])
        self.workflow = WorkflowRef(**workflow)
        self.session.start_run(self.workflow, decision)
        self.session.start_attempt(self.decide('CONTINUE'))

    def test_one_session_collision_and_terminal_never_resume(self):
        with self.assertRaisesRegex(ValueError, 'COLLISION'):
            AdaptiveSession(self.frozen, self.scope, self.root / 'session', self.limits)
        self.session.stop('ABORT', 'SYNTHETIC_TERMINAL')
        with self.assertRaisesRegex(ValueError, 'TERMINAL'):
            self.session.checked_decision(self.decide('CONTINUE'), {'CONTINUE'})

    def test_local_correction_retains_run_workflow_and_prior_attempt(self):
        self.begin()
        self.session.finish_attempt('REVIEWED', ())
        first = self.session.attempt['directory'] / 'attempt.json'
        self.session.start_attempt(self.decide('REVISE_ARTIFACT'))
        self.assertEqual(self.session.state()['production_run_id'], 'run-001')
        self.assertEqual(self.session.state()['attempt_id'], 'attempt-002')
        self.assertEqual(self.session.run['workflow'], self.workflow)
        self.assertTrue(first.exists())

    def test_unresolved_execution_blocks_attempt_and_keeps_reserved_effect(self):
        self.begin()
        self.session.reserve_effect('worker_calls')
        self.session.finish_attempt('UNRESOLVED', ())
        with self.assertRaisesRegex(ValueError, 'UNRESOLVED'):
            self.session.start_attempt(self.decide('REVISE_ARTIFACT'))
        self.assertEqual(self.session.resources.remaining()['used']['worker_calls'], 1)

    def test_collision_and_capacity_reject_before_effect(self):
        self.begin()
        self.session.finish_attempt('REVIEWED', ())
        collision = self.root / 'external'
        collision.mkdir()
        before = self.session.resources.remaining()['used']['attempts']
        with self.assertRaisesRegex(ValueError, 'COLLISION'):
            self.session.start_attempt(self.decide('REVISE_ARTIFACT'), external_namespaces=(collision,))
        self.assertEqual(before, self.session.resources.remaining()['used']['attempts'])
        for _ in range(4):
            self.session.resources.reserve('worker_calls', {})
        with self.assertRaisesRegex(ValueError, 'EXHAUSTED'):
            self.session.resources.reserve('worker_calls', {})

    def test_stale_decision_and_wrong_mode_cannot_start(self):
        decision = self.decide('PLAN_WORKFLOW', self.proposal)
        self.session.mode = 'ACTUAL'
        with self.assertRaisesRegex(ValueError, 'CONTEXT'):
            self.session.checked_decision(decision, {'PLAN_WORKFLOW'})
        self.session.mode = 'SYNTHETIC'
        self.begin()
        with self.assertRaisesRegex(ValueError, 'CONTEXT'):
            self.session.checked_decision(decision, {'PLAN_WORKFLOW'})

    def test_elapsed_deadline_and_mutable_limit_tampering_reject(self):
        from core.adaptive_loop import ResourceEnvelope
        path = Path(self.frozen.reference.specification_path)
        path.write_bytes(path.read_bytes() + b'\n' + canonical_bytes({'resource_limits': self.limits, 'deadline_seconds': 1}))
        frozen = freeze_specification(path, self.frozen.fields)
        now = [0]
        resource = ResourceEnvelope(frozen, self.limits, self.root / 'timed', seconds=1, clock=lambda: now[0])
        now[0] = 2
        with self.assertRaisesRegex(ValueError, 'EXHAUSTED'):
            resource.reserve('worker_calls', {})
        self.assertEqual(resource.sequence, 0)
        resource.limits['worker_calls'] = 100
        with self.assertRaisesRegex(ValueError, 'CHANGED'):
            resource.remaining()


if __name__ == '__main__':
    unittest.main()
