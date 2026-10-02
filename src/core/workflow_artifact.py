"""Compact sequential Workflow versions; frozen authority and capability checks."""
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from core.skill_artifact import canonical_bytes, digest_bytes, identifier, write_once
from session.session_boundary import FileIdentity, file_identity

STAGE_FIELDS = {'stage_id', 'skill_id', 'skill_version', 'capability', 'tool', 'model',
    'input_artifact_types', 'output_artifact_type', 'criterion_ids', 'parameters'}
LOCAL_TUNING_KEYS = frozenset({'seed', 'steps', 'cfg', 'sampler_name', 'scheduler', 'denoise'})


def strategy_hash(stages, skill_refs):
    stable_stages = [stage | {'parameters': {k: v for k, v in stage['parameters'].items() if k not in LOCAL_TUNING_KEYS}} for stage in stages]
    return digest_bytes(canonical_bytes({'stages': stable_stages, 'skill_refs': skill_refs}))


def freeze_workflow_scope(frozen, path, applicability, deliverable_type):
    """Pin an explicit projection already present verbatim in frozen task bytes."""
    frozen.validate(require_ready=True)
    projection = {'criterion_applicability': applicability, 'deliverable_type': deliverable_type}
    if canonical_bytes(projection).decode('utf-8') not in Path(frozen.reference.specification_path).read_text(encoding='utf-8'):
        raise ValueError('WORKFLOW_SCOPE_NOT_IN_FROZEN_SPECIFICATION')
    validate_projection(frozen, projection)
    write_once(path, projection | {'specification_identity_sha256': frozen.identity_sha256,
        'specification_ref': asdict(frozen.reference)})
    return file_identity(path, frozen.reference.session_id + ':workflow-scope')


def validate_projection(frozen, projection):
    ids = {c.criterion_id for c in frozen.fields.acceptance_criteria}
    mandatory = {c.criterion_id for c in frozen.fields.acceptance_criteria if c.blocking_when_unmet}
    mapping = projection['criterion_applicability']
    if not isinstance(mapping, dict) or not mapping or not isinstance(projection['deliverable_type'], str) or not projection['deliverable_type']:
        raise ValueError('invalid Workflow scope')
    for stage_type, selected in mapping.items():
        if (not isinstance(stage_type, str) or not stage_type or not isinstance(selected, list) or not selected
                or len(set(selected)) != len(selected) or not set(selected) <= ids):
            raise ValueError('UNSUPPORTED_ACCEPTANCE_CRITERION')
    if not mandatory <= set().union(*(set(v) for v in mapping.values())):
        raise ValueError('UNSUPPORTED_ACCEPTANCE_CRITERION')


def checked_scope(frozen, scope_ref):
    frozen.validate(require_ready=True)
    scope_ref.validate()
    data = json.loads(Path(scope_ref.path).read_text(encoding='utf-8'))
    if data['specification_identity_sha256'] != frozen.identity_sha256 or data['specification_ref'] != asdict(frozen.reference):
        raise ValueError('WORKFLOW_SPECIFICATION_MISMATCH')
    projection = {key: data[key] for key in ('criterion_applicability', 'deliverable_type')}
    if canonical_bytes(projection).decode('utf-8') not in Path(frozen.reference.specification_path).read_text(encoding='utf-8'):
        raise ValueError('WORKFLOW_SCOPE_NOT_IN_FROZEN_SPECIFICATION')
    validate_projection(frozen, projection)
    return data


@dataclass(frozen=True)
class WorkflowRef:
    workflow_id: str
    version: int
    file: FileIdentity
    strategy_hash: str
    specification_identity_sha256: str

    def validate(self, frozen, scope_ref):
        self.file.validate()
        scope = checked_scope(frozen, scope_ref)
        data = json.loads(Path(self.file.path).read_text(encoding='utf-8'))
        if (data['workflow_id'] != self.workflow_id or data['version'] != self.version
                or data['strategy_hash'] != self.strategy_hash or data['specification_identity_sha256'] != frozen.identity_sha256
                or self.specification_identity_sha256 != frozen.identity_sha256 or data['scope_ref'] != asdict(scope_ref)
                or strategy_hash(data['stages'], data['skill_refs']) != self.strategy_hash):
            raise ValueError('WORKFLOW_SPECIFICATION_MISMATCH')
        if data['stages'][-1]['output_artifact_type'] != scope['deliverable_type']:
            raise ValueError('WORKFLOW_DELIVERABLE_MISMATCH')
        return data


class WorkflowPlanner:
    def __init__(self, registry, available_capabilities):
        self.registry = registry
        self.available_capabilities = frozenset(available_capabilities)

    def write(self, frozen, scope_ref, proposal, path, *, previous=None, cause_refs=()):
        scope = checked_scope(frozen, scope_ref)
        if not isinstance(proposal, dict) or set(proposal) != {'workflow_id', 'version', 'selected_skills', 'stages'}:
            raise ValueError('WORKFLOW_INVALID')
        identifier(proposal['workflow_id'])
        if type(proposal['version']) is not int or proposal['version'] < 1:
            raise ValueError('WORKFLOW_INVALID')
        if previous is None and proposal['version'] != 1:
            raise ValueError('previous Workflow required')
        if previous is not None:
            previous.validate(frozen, scope_ref)
            if proposal['workflow_id'] != previous.workflow_id or proposal['version'] != previous.version + 1 or not cause_refs:
                raise ValueError('REVISION_CAUSE_REQUIRED')
        for ref in cause_refs:
            ref.validate()
        refs = []
        for selected in proposal['selected_skills']:
            if set(selected) != {'skill_id', 'version', 'content_hash'}:
                raise ValueError('exact Skill selection required')
            ref = self.registry.resolve(selected['skill_id'], selected['version'])
            if ref.content_hash != selected['content_hash']:
                raise ValueError('VERSION_UNRESOLVED')
            refs.append(ref)
        if not refs or len({(r.skill_id, r.version) for r in refs}) != len(refs):
            raise ValueError('unique selected Skills required')
        resolved = self.registry.composition_preflight(refs, self.available_capabilities)
        metadata = {(r.skill_id, r.version): r.validate() for r in resolved}
        stages = proposal['stages']
        if not isinstance(stages, list) or not stages:
            raise ValueError('WORKFLOW_INVALID')
        stage_ids, available_types, coverage = set(), {'reference'}, set()
        for stage in stages:
            if not isinstance(stage, dict) or set(stage) != STAGE_FIELDS:
                raise ValueError('WORKFLOW_INVALID')
            identifier(stage['stage_id'])
            if stage['stage_id'] in stage_ids:
                raise ValueError('duplicate Workflow stage')
            stage_ids.add(stage['stage_id'])
            skill = metadata.get((stage['skill_id'], stage['skill_version']))
            if skill is None or stage['capability'] not in self.available_capabilities:
                raise ValueError('CAPABILITY_UNAVAILABLE')
            if (stage['tool'] not in skill['candidate_tools'] or stage['model'] is not None and stage['model'] not in skill['candidate_models']
                    or not isinstance(stage['parameters'], dict)):
                raise ValueError('WORKFLOW_INVALID_TOOL_OR_MODEL')
            inputs = stage['input_artifact_types']
            if not isinstance(inputs, list) or not inputs or not set(inputs) <= available_types or not set(inputs) <= set(skill['input_artifact_types']):
                raise ValueError('WORKFLOW_INPUT_UNAVAILABLE')
            output = stage['output_artifact_type']
            if output not in skill['output_artifact_types'] or stage['criterion_ids'] != scope['criterion_applicability'].get(output):
                raise ValueError('UNSUPPORTED_ACCEPTANCE_CRITERION')
            coverage.update(stage['criterion_ids'])
            available_types.add(output)
        mandatory = {c.criterion_id for c in frozen.fields.acceptance_criteria if c.blocking_when_unmet}
        if not mandatory <= coverage or stages[-1]['output_artifact_type'] != scope['deliverable_type']:
            raise ValueError('UNSUPPORTED_ACCEPTANCE_CRITERION / WORKFLOW_DELIVERABLE_MISMATCH')
        # Clone through canonical bytes, so mutable proposal objects never own persisted authority.
        data = json.loads(canonical_bytes(proposal))
        data['skill_refs'] = [asdict(r) for r in resolved]
        data.update(specification_identity_sha256=frozen.identity_sha256, scope_ref=asdict(scope_ref),
            previous_workflow=asdict(previous) if previous is not None else None, cause_refs=[asdict(r) for r in cause_refs])
        data['disclosure_event'] = {'event_type': 'USER_WORKFLOW_REVIEW_REQUESTED_NON_BLOCKING',
            'workflow_id': data['workflow_id'], 'version': data['version'], 'goal_specification_ref': asdict(frozen.reference),
            'summary': ' → '.join(stage['stage_id'] for stage in stages), 'response_required': False,
            'feedback_boundary': 'Before Loop feedback may be considered; late feedback is external/new Request.'}
        data['strategy_hash'] = strategy_hash(data['stages'], data['skill_refs'])
        if previous is not None and data['strategy_hash'] == previous.strategy_hash:
            raise ValueError('STRATEGY_UNCHANGED_USE_ATTEMPT')
        if Path(path).exists():
            raise ValueError('WORKFLOW_VERSION_COLLISION')
        write_once(path, data)
        ref = WorkflowRef(data['workflow_id'], data['version'], file_identity(path, data['workflow_id'] + ':v' + str(data['version'])), data['strategy_hash'], frozen.identity_sha256)
        ref.validate(frozen, scope_ref)
        return ref
