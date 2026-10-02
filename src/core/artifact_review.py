"""Independent stage-level Reviewer; no controller or Worker effect authority."""
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from core.frontier import InferenceResult
from core.skill_artifact import canonical_bytes, write_once
from core.workflow_artifact import checked_scope
from session.session_boundary import FileIdentity, file_identity

REVIEW_SCHEMA = {'type': 'object', 'additionalProperties': False,
    'required': ['verdict', 'reason_summary', 'criterion_results_json', 'requested_evidence_json'],
    'properties': {'verdict': {'type': 'string', 'enum': ['PASS', 'REVISE', 'HUMAN_REQUIRED']},
        'reason_summary': {'type': 'string'}, 'criterion_results_json': {'type': 'string'},
        'requested_evidence_json': {'type': 'string'}}}


def checked_outcomes(data, applicable):
    outcomes = json.loads(data['criterion_results_json'])
    if (not isinstance(outcomes, list) or len(outcomes) != len(applicable)
            or {r.get('criterion_id') for r in outcomes} != set(applicable)):
        raise ValueError('REVIEW_CRITERION_COVERAGE_MISMATCH')
    for result in outcomes:
        if (set(result) != {'criterion_id', 'outcome', 'reason'} or result['outcome'] not in ('MET', 'UNMET', 'UNCERTAIN')
                or not isinstance(result['reason'], str) or not result['reason'].strip()):
            raise ValueError('REVIEW_CRITERION_INVALID')
    if data['verdict'] == 'PASS' and any(r['outcome'] != 'MET' for r in outcomes):
        raise ValueError('PASS_WITH_UNMET_CRITERION')
    return outcomes


@dataclass(frozen=True)
class ReviewRef:
    file: FileIdentity

    def validate(self, frozen, scope, workflow, artifact, *, state=None, mode=None):
        self.file.validate()
        data = json.loads(Path(self.file.path).read_text(encoding='utf-8'))
        material = artifact.validate(frozen, scope, workflow, state=state)
        applicable = checked_scope(frozen, scope)['criterion_applicability'][material['artifact_type']]
        if (data['artifact_ref'] != asdict(artifact) or data['workflow_ref'] != asdict(workflow)
                or data['source_specification_ref'] != asdict(frozen.reference)
                or any(data.get(k) != material[k] for k in ('session_id', 'production_run_id', 'attempt_id'))
                or mode is not None and data['inference_mode'] != mode):
            raise ValueError('REVIEW_SOURCE_MISMATCH / STALE_REVIEW')
        result = FileIdentity(**data['result_ref'])
        request = FileIdentity(**data['request_ref'])
        InferenceResult(result, FileIdentity(**data['invocation_ref']), data['inference_mode'],
            data['model_identity']).validate(request)
        request.validate()
        context = json.loads(Path(request.path).read_text(encoding='utf-8'))
        if (context['artifact_ref'] != asdict(artifact) or context['workflow_ref'] != asdict(workflow)
                or context['applicable_criterion_ids'] != applicable):
            raise ValueError('REVIEW_SOURCE_MISMATCH')
        observed = json.loads(Path(result.path).read_text(encoding='utf-8'))
        if any(data[k] != observed[k] for k in REVIEW_SCHEMA['required']):
            raise ValueError('REVIEW_RESULT_CHANGED')
        for item in context['image_refs'] + context['supporting_refs']:
            FileIdentity(**item).validate()
        checked_outcomes(data, applicable)
        return data


class ArtifactReviewer:
    def __init__(self, inference_adapter):
        self.adapter = inference_adapter

    def review(self, frozen, scope, workflow, artifact, directory, *, images=(), supporting_refs=()):
        material = artifact.validate(frozen, scope, workflow)
        applicable = checked_scope(frozen, scope)['criterion_applicability'][material['artifact_type']]
        for ref in images + supporting_refs:
            ref.validate()
        directory = Path(directory)
        if directory.exists():
            raise ValueError('REVIEW_NAMESPACE_COLLISION')
        context = {'role': 'INDEPENDENT_ARTIFACT_REVIEWER', 'frozen_specification': asdict(frozen),
            'specification_document': Path(frozen.reference.specification_path).read_text(encoding='utf-8'),
            'artifact_ref': asdict(artifact), 'artifact': material, 'workflow_ref': asdict(workflow),
            'applicable_criterion_ids': applicable,
            'applicable_criteria': [asdict(c) for c in frozen.fields.acceptance_criteria if c.criterion_id in applicable],
            'image_refs': [asdict(r) for r in images], 'supporting_refs': [asdict(r) for r in supporting_refs],
            'supporting_documents': [Path(r.path).read_text(encoding='utf-8') for r in supporting_refs if Path(r.path).suffix in ('.json', '.txt')],
            'responsibility': 'Judge only applicable frozen criteria against supplied current evidence. '
                'Report criterion_results_json as a list of {criterion_id,outcome:MET|UNMET|UNCERTAIN,reason}. '
                'requested_evidence_json is a list. PASS requires every applicable outcome MET. '
                'UNCERTAIN means evidence acquisition or revision; never manufacture visibility or geometry. '
                'No Worker, Workflow mutation, restart, user approval, or Specification editing authority.'}
        write_once(directory / 'request.json', context)
        request = file_identity(directory / 'request.json', 'artifact-review-request')
        result = self.adapter(request, REVIEW_SCHEMA, directory / 'invocation', images)
        result.validate(request)
        observed = json.loads(Path(result.result.path).read_text(encoding='utf-8'))
        if (set(observed) != set(REVIEW_SCHEMA['required']) or observed['verdict'] not in ('PASS', 'REVISE', 'HUMAN_REQUIRED')
                or not isinstance(observed['reason_summary'], str) or not 0 < len(observed['reason_summary']) <= 2000
                or not isinstance(json.loads(observed['requested_evidence_json']), list)):
            raise ValueError('REVIEW_RESULT_INVALID')
        checked_outcomes(observed, applicable)
        request.validate()
        artifact.validate(frozen, scope, workflow)
        for ref in images + supporting_refs:
            ref.validate()
        write_once(directory / 'review.json', {**observed,
            **{k: material[k] for k in ('session_id', 'production_run_id', 'attempt_id')},
            'artifact_ref': asdict(artifact), 'workflow_ref': asdict(workflow),
            'source_specification_ref': asdict(frozen.reference), 'request_ref': asdict(request),
            'result_ref': asdict(result.result), 'invocation_ref': asdict(result.invocation),
            'inference_mode': result.mode, 'model_identity': result.model_identity})
        review = ReviewRef(file_identity(directory / 'review.json', directory.name))
        review.validate(frozen, scope, workflow, artifact)
        return review
