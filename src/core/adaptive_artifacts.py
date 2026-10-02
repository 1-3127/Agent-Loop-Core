"""Immutable artifact metadata with complete producer and input lineage."""
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from core.skill_artifact import SkillRef, write_once
from session.session_boundary import FileIdentity, file_identity


@dataclass(frozen=True)
class ArtifactRef:
    metadata: FileIdentity

    def validate(self, frozen, scope, workflow, *, state=None):
        self.metadata.validate()
        data = json.loads(Path(self.metadata.path).read_text(encoding='utf-8'))
        configured = workflow.validate(frozen, scope)
        if (data['source_specification_ref'] != asdict(frozen.reference)
                or data['workflow_ref'] != asdict(workflow) or data['session_id'] != frozen.reference.session_id
                or state is not None and any(data.get(k) != v for k, v in state.items())):
            raise ValueError('ARTIFACT_LINEAGE_MISMATCH / STALE_ARTIFACT')
        stage = next((s for s in configured['stages'] if s['stage_id'] == data['stage_id']), None)
        if stage is None or stage['output_artifact_type'] != data['artifact_type']:
            raise ValueError('ARTIFACT_STAGE_MISMATCH')
        expected_skills = configured['skill_refs']
        if data['skill_refs'] != expected_skills:
            raise ValueError('ARTIFACT_SKILL_MISMATCH')
        for item in data['skill_refs']:
            item = dict(item)
            item['metadata'] = FileIdentity(**item['metadata'])
            SkillRef(**item).validate()
        for item in data['files'] + data['input_refs'] + [data['execution_report_ref']]:
            FileIdentity(**item).validate()
        if not data['files'] or data['mode'] not in ('ACTUAL', 'SYNTHETIC'):
            raise ValueError('ARTIFACT_INVALID')
        return data


class ArtifactStore:
    def __init__(self, frozen, scope, workflow, state, directory, *, mode):
        workflow.validate(frozen, scope)
        if (set(state) != {'session_id', 'production_run_id', 'attempt_id'} or any(not v for v in state.values())
                or state['session_id'] != frozen.reference.session_id or mode not in ('ACTUAL', 'SYNTHETIC')):
            raise ValueError('ARTIFACT_LINEAGE_MISMATCH')
        self.frozen, self.scope, self.workflow = frozen, scope, workflow
        self.state, self.directory, self.mode = dict(state), Path(directory), mode

    def register(self, artifact_id, stage_id, files, input_refs, execution_report):
        from core.skill_artifact import identifier
        identifier(artifact_id)
        workflow = self.workflow.validate(self.frozen, self.scope)
        stage = next((s for s in workflow['stages'] if s['stage_id'] == stage_id), None)
        if stage is None or not isinstance(files, tuple) or not files or not isinstance(input_refs, tuple):
            raise ValueError('ARTIFACT_STAGE_MISMATCH')
        for ref in files + input_refs + (execution_report,):
            ref.validate()
        report = json.loads(Path(execution_report.path).read_text(encoding='utf-8'))
        if (report.get('status') != 'SUCCESS' or report.get('mode') != self.mode
                or report.get('state') != self.state or report.get('workflow_ref') != asdict(self.workflow)
                or report.get('stage_id') != stage_id or report.get('output_refs') != [asdict(r) for r in files]
                or report.get('input_refs') != [asdict(r) for r in input_refs]):
            raise ValueError('EXECUTION_REPORT_LINEAGE_MISMATCH')
        target = self.directory / (artifact_id + '.json')
        write_once(target, {'artifact_id': artifact_id, **self.state,
            'source_specification_ref': asdict(self.frozen.reference), 'workflow_ref': asdict(self.workflow),
            'stage_id': stage_id, 'artifact_type': stage['output_artifact_type'], 'skill_refs': workflow['skill_refs'],
            'files': [asdict(r) for r in files], 'input_refs': [asdict(r) for r in input_refs],
            'execution_report_ref': asdict(execution_report), 'mode': self.mode,
            'reuse_policy': 'No cross-Run promotion; explicit producer/input lineage required'})
        result = ArtifactRef(file_identity(target, artifact_id))
        result.validate(self.frozen, self.scope, self.workflow, state=self.state)
        return result
