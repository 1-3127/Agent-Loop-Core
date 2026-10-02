from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest

from core.skill_artifact import canonical_bytes, create_skill
from core.skill_registry import SkillRegistry
from core.workflow_artifact import WorkflowPlanner, checked_scope, freeze_workflow_scope
from session.session_boundary import AcceptanceCriterion, AuthorityReference, FinalizedFields, file_identity, freeze_specification
from tests.test_skill_artifact import candidate, guidance


class WorkflowArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mapping = {'geometry': ['form', 'opening']}
        projection = {'criterion_applicability': self.mapping, 'deliverable_type': 'geometry'}
        spec = self.root / 'spec.md'
        spec.write_bytes(b'Original request: make target with an opening.\n' + canonical_bytes(projection))
        fields = FinalizedFields('session-one', 'v1', 'NEW_WORK', True, (),
            (AcceptanceCriterion('form', 'request', True, 'Target form'), AcceptanceCriterion('opening', 'request', True, 'Actual opening')),
            (AuthorityReference('request', 'Original request: make target with an opening.'),), ('Infer the hidden sides consistently.',))
        self.frozen = freeze_specification(spec, fields)
        self.scope = freeze_workflow_scope(self.frozen, self.root / 'scope.json', self.mapping, 'geometry')
        self.registry = SkillRegistry(self.root / 'skills', '1' * 40)
        metadata = candidate('geometry', capabilities=('geometry',))
        metadata['candidate_tools'] = ['fixture']
        create_skill(self.registry.directory, metadata, guidance('geometry'))
        self.skill = self.registry.resolve('geometry', 'v1')
        self.planner = WorkflowPlanner(self.registry, ('geometry',))
        self.proposal = {'workflow_id': 'target-workflow', 'version': 1,
            'selected_skills': [{'skill_id': self.skill.skill_id, 'version': self.skill.version, 'content_hash': self.skill.content_hash}],
            'stages': [{'stage_id': 'build', 'skill_id': 'geometry', 'skill_version': 'v1', 'capability': 'geometry',
                'tool': 'fixture', 'model': None, 'input_artifact_types': ['reference'], 'output_artifact_type': 'geometry',
                'criterion_ids': ['form', 'opening'], 'parameters': {}}]}

    def test_frozen_scope_version_pins_and_caller_mutation(self):
        ref = self.planner.write(self.frozen, self.scope, self.proposal, self.root / 'workflow-v1.json')
        self.proposal['stages'][0]['parameters']['mutable'] = True
        self.assertEqual(ref.validate(self.frozen, self.scope)['stages'][0]['parameters'], {})
        self.assertEqual(ref.specification_identity_sha256, self.frozen.identity_sha256)
        with self.assertRaisesRegex(ValueError, 'COLLISION'):
            self.planner.write(self.frozen, self.scope, self.proposal, self.root / 'workflow-v1.json')

    def test_criterion_weakening_and_unavailable_input_block_before_write(self):
        self.proposal['stages'][0]['criterion_ids'] = ['form']
        with self.assertRaisesRegex(ValueError, 'UNSUPPORTED_ACCEPTANCE_CRITERION'):
            self.planner.write(self.frozen, self.scope, self.proposal, self.root / 'invalid.json')
        self.assertFalse((self.root / 'invalid.json').exists())
        self.proposal['stages'][0]['criterion_ids'] = ['form', 'opening']
        self.proposal['stages'][0]['input_artifact_types'] = ['future-stage']
        with self.assertRaisesRegex(ValueError, 'WORKFLOW_INPUT_UNAVAILABLE'):
            self.planner.write(self.frozen, self.scope, self.proposal, self.root / 'invalid.json')

    def test_scope_cannot_be_inferred_or_mutated_after_freeze(self):
        with self.assertRaisesRegex(ValueError, 'NOT_IN_FROZEN'):
            freeze_workflow_scope(self.frozen, self.root / 'other.json', {'geometry': ['form']}, 'geometry')
        data = json.loads(Path(self.scope.path).read_text())
        data['criterion_applicability']['geometry'] = ['form']
        Path(self.scope.path).write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            checked_scope(self.frozen, self.scope)

    def test_revision_requires_evidence_and_preserves_prior_version(self):
        first = self.planner.write(self.frozen, self.scope, self.proposal, self.root / 'workflow-v1.json')
        evidence = self.root / 'review.json'
        evidence.write_text('{"verdict":"REVISE","reason":"strategy inadequate"}')
        self.proposal['version'] = 2
        self.proposal['stages'][0]['parameters'] = {'strategy': 'isolate target'}
        with self.assertRaisesRegex(ValueError, 'REVISION_CAUSE_REQUIRED'):
            self.planner.write(self.frozen, self.scope, self.proposal, self.root / 'workflow-v2.json', previous=first)
        second = self.planner.write(self.frozen, self.scope, self.proposal, self.root / 'workflow-v2.json', previous=first,
            cause_refs=(file_identity(evidence, 'review'),))
        self.assertNotEqual(first.strategy_hash, second.strategy_hash)
        self.assertEqual(first.validate(self.frozen, self.scope)['version'], 1)
        self.assertEqual(second.specification_identity_sha256, first.specification_identity_sha256)

    def test_model_tool_and_skill_selection_are_preflighted(self):
        self.proposal['stages'][0]['model'] = 'uninstalled-model'
        with self.assertRaisesRegex(ValueError, 'MODEL'):
            self.planner.write(self.frozen, self.scope, self.proposal, self.root / 'invalid.json')
        self.proposal['stages'][0]['model'] = None
        self.proposal['selected_skills'][0]['content_hash'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'VERSION_UNRESOLVED'):
            self.planner.write(self.frozen, self.scope, self.proposal, self.root / 'invalid.json')

    def test_seed_only_change_is_local_attempt_not_strategy_revision(self):
        first = self.planner.write(self.frozen, self.scope, self.proposal, self.root / 'workflow-v1.json')
        cause = self.root / 'cause.json'
        cause.write_text('{"action":"REVISE_ARTIFACT"}')
        self.proposal['version'] = 2
        self.proposal['stages'][0]['parameters'] = {'seed': 123}
        with self.assertRaisesRegex(ValueError, 'STRATEGY_UNCHANGED_USE_ATTEMPT'):
            self.planner.write(self.frozen, self.scope, self.proposal, self.root / 'workflow-v2.json', previous=first,
                cause_refs=(file_identity(cause, 'cause'),))


if __name__ == '__main__':
    unittest.main()
