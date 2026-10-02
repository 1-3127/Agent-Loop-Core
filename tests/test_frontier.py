from dataclasses import asdict
import json
import re
from pathlib import Path
import unittest
from unittest import mock

from core.frontier import CodexInferenceAdapter, DECISION_SCHEMA, FrontierSupervisor, InferenceResult
from core.skill_artifact import write_once
from session.session_boundary import file_identity
from tests import test_workflow_artifact as workflow_fixture


class FrontierTests(unittest.TestCase):
    def setUp(self):
        workflow_fixture.WorkflowArtifactTests.setUp(self)

    def adapter(self, request_ref, schema, directory, images):
        directory.mkdir()
        write_once(directory / 'result.json', {'selected_action': 'PLAN_WORKFLOW', 'reason_summary': 'Use installed geometry capability.',
            'workflow_proposal_json': json.dumps(self.proposal), 'action_parameters_json': None, 'new_skill_proposals_json': None})
        result = file_identity(directory / 'result.json', 'fixture-result')
        write_once(directory / 'invocation.json', {'mode': 'SYNTHETIC', 'status': 'SUCCESS', 'request_ref': asdict(request_ref),
            'result_ref': asdict(result), 'model_identity': None})
        return InferenceResult(result, file_identity(directory / 'invocation.json', 'fixture-invocation'), 'SYNTHETIC', None)

    def test_mock_is_bound_to_context_and_not_claimed_actual_intelligence(self):
        frontier = FrontierSupervisor(self.adapter)
        decision = frontier.decide(self.frozen, self.scope, state={'session_id': 'session-one', 'production_run_id': None, 'attempt_id': None},
            workflow=None, artifacts=(), reviews=(), skills=(self.skill,), capabilities=['geometry'], envelope={'remaining': 3}, directory=self.root / 'decision-001',
            planner=self.planner, workflow_output=self.root / 'workflow.json')
        data = json.loads(Path(decision.path).read_text())
        self.assertEqual(data['inference_mode'], 'SYNTHETIC')
        self.assertEqual(data['selected_action'], 'PLAN_WORKFLOW')
        self.assertEqual(data['source_specification_ref'], asdict(self.frozen.reference))
        self.assertIsNone(data['frontier_model_identity'])
        self.assertTrue(data['frontier_invocation_ref']['sha256'])
        self.assertEqual(data['selected_workflow_ref']['version'], 1)

    def test_context_session_mismatch_has_no_invocation(self):
        calls = []
        frontier = FrontierSupervisor(lambda *args: calls.append(args))
        with self.assertRaisesRegex(ValueError, 'DECISION_CONTEXT_MISMATCH'):
            frontier.decide(self.frozen, self.scope, state={'session_id': 'wrong'}, workflow=None,
                artifacts=(), reviews=(), skills=(self.skill,), capabilities=['geometry'], envelope={}, directory=self.root / 'invalid')
        self.assertFalse(calls)

    def test_current_review_and_skill_guidance_are_model_inputs(self):
        review = self.root / 'review.json'
        review.write_text('{"verdict":"REVISE","observation":"conditioning includes occluder"}')
        decision = FrontierSupervisor(self.adapter).decide(self.frozen, self.scope, state={'session_id': 'session-one'},
            workflow=None, artifacts=(), reviews=(file_identity(review, 'review'),), skills=(self.skill,),
            capabilities=['geometry'], envelope={}, directory=self.root / 'decision-001',
            planner=self.planner, workflow_output=self.root / 'workflow.json')
        data = json.loads(Path(decision.path).read_text())
        request = json.loads(Path(data['frontier_request_ref']['path']).read_text())
        self.assertEqual(request['current_reviews'][0]['result']['verdict'], 'REVISE')
        self.assertIn('Preserve reference authority.', request['available_skills'][0]['guidance'])

    def test_state_change_during_inference_rejects_decision(self):
        state = {'session_id': 'session-one', 'production_run_id': 'run-one'}
        def mutating_adapter(*args):
            outcome = self.adapter(*args)
            state['production_run_id'] = 'run-two'
            return outcome
        with self.assertRaisesRegex(ValueError, 'DECISION_CONTEXT_MISMATCH'):
            FrontierSupervisor(mutating_adapter).decide(self.frozen, self.scope, state=state, workflow=None,
                artifacts=(), reviews=(), skills=(self.skill,), capabilities=['geometry'], envelope={}, directory=self.root / 'decision-001')
        self.assertFalse((self.root / 'decision-001/decision.json').exists())

    def test_wrong_auth_mode_blocks_before_invocation_namespace(self):
        request = self.root / 'request.json'
        request.write_text('{}')
        with mock.patch('core.frontier.auth_mode', return_value='API_KEY'), mock.patch('core.frontier.subprocess.run') as process:
            with self.assertRaisesRegex(ValueError, 'BLOCKED_BY_AUTH_MODE'):
                CodexInferenceAdapter(self.root)(file_identity(request, 'request'), DECISION_SCHEMA, self.root / 'invocation')
        process.assert_not_called()
        self.assertFalse((self.root / 'invocation').exists())

    def test_model_can_plan_multiple_stages_from_advertised_frozen_contract(self):
        def context_adapter(request_ref, schema, directory, images):
            request = json.loads(Path(request_ref.path).read_text())
            contract = request['workflow_proposal_contract']
            self.assertIsNone(re.fullmatch(contract['identifier_pattern'], 'reference_geometry'))
            self.assertIsNotNone(re.fullmatch(contract['identifier_pattern'], 'reference-geometry'))
            self.proposal['stages'] = [dict(self.proposal['stages'][0], stage_id=name,
                criterion_ids=contract['criterion_ids_by_output_artifact_type']['geometry'],
                input_artifact_types=inputs) for name, inputs in (
                    ('reference-geometry', ['reference']), ('stone-finish', ['reference']))]
            self.assertEqual(set(self.proposal['stages'][0]), set(contract['stage_fields']))
            return self.adapter(request_ref, schema, directory, images)
        decision = FrontierSupervisor(context_adapter).decide(self.frozen, self.scope,
            state={'session_id': 'session-one'}, workflow=None, artifacts=(), reviews=(), skills=(self.skill,),
            capabilities=['geometry'], envelope={}, directory=self.root / 'decision-001',
            planner=self.planner, workflow_output=self.root / 'workflow.json')
        workflow = json.loads((self.root / 'workflow.json').read_text())
        self.assertEqual([s['stage_id'] for s in workflow['stages']], ['reference-geometry', 'stone-finish'])
        self.assertTrue(all(s['criterion_ids'] == ['form', 'opening'] for s in workflow['stages']))
        self.assertEqual(json.loads(Path(decision.path).read_text())['source_specification_ref'], asdict(self.frozen.reference))

    def test_advertised_contract_does_not_silently_repair_invalid_model_proposal(self):
        self.proposal['stages'][0]['stage_id'] = 'reference_geometry'
        with self.assertRaisesRegex(ValueError, 'invalid Skill identity/version'):
            FrontierSupervisor(self.adapter).decide(self.frozen, self.scope,
                state={'session_id': 'session-one'}, workflow=None, artifacts=(), reviews=(), skills=(self.skill,),
                capabilities=['geometry'], envelope={}, directory=self.root / 'decision-001',
                planner=self.planner, workflow_output=self.root / 'workflow.json')
        result = json.loads((self.root / 'decision-001/invocation/result.json').read_text())
        self.assertEqual(json.loads(result['workflow_proposal_json'])['stages'][0]['stage_id'], 'reference_geometry')
        self.assertFalse((self.root / 'workflow.json').exists())
        self.assertFalse((self.root / 'decision-001/decision.json').exists())


if __name__ == '__main__':
    unittest.main()
