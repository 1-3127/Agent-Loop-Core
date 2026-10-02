"""Selected tool effects behind a replaceable, preflighted execution boundary.

This adapter does not choose strategy, call Frontier/Reviewer, or acquire models.
Tool runners are supplied explicitly by the host from reviewed installed code.
"""
from dataclasses import asdict
import json
from pathlib import Path

from core.skill_artifact import write_once
from session.session_boundary import file_identity


class ExecutionAdapter:
    def __init__(self, runners, *, mode='ACTUAL'):
        if mode not in ('ACTUAL', 'SYNTHETIC') or not all(callable(v) for v in runners.values()):
            raise ValueError('EXECUTION_ADAPTER_INVALID')
        self.runners, self.mode = dict(runners), mode

    def execute(self, frozen, scope, workflow, state, stage_id, inputs, reservation, directory, *, local_parameters=None):
        configured = workflow.validate(frozen, scope)
        stage = next((s for s in configured['stages'] if s['stage_id'] == stage_id), None)
        if stage is None or stage['tool'] not in self.runners:
            raise ValueError('CAPABILITY_UNAVAILABLE')
        if set(state) != {'session_id', 'production_run_id', 'attempt_id'} or state['session_id'] != frozen.reference.session_id:
            raise ValueError('EXECUTION_STATE_MISMATCH')
        for ref in inputs + (reservation,):
            ref.validate()
        admitted = json.loads(Path(reservation.path).read_text(encoding='utf-8'))
        if admitted['kind'] != 'worker_calls' or admitted['context'] != state:
            raise ValueError('EXECUTION_RESERVATION_MISMATCH')
        # Reservation is consumed exactly once in its authoritative namespace.
        claim = Path(reservation.path).with_suffix('.dispatch.json')
        directory = Path(directory).resolve()
        if directory.exists() or claim.exists():
            raise ValueError('EXTERNAL_NAMESPACE_COLLISION')
        local_parameters = local_parameters or {}
        allowed = set(stage['parameters'].get('local_parameter_names', ()))
        from core.workflow_artifact import LOCAL_TUNING_KEYS
        if set(local_parameters) - (allowed | LOCAL_TUNING_KEYS):
            raise ValueError('LOCAL_PARAMETER_REQUIRES_WORKFLOW_REVISION')
        work_order = {'state': state, 'workflow_ref': asdict(workflow), 'stage': stage,
            'input_refs': [asdict(r) for r in inputs], 'reservation_ref': asdict(reservation),
            'local_parameters': local_parameters, 'mode': self.mode, 'output_directory': str(directory)}
        write_once(claim, {'directory': str(directory), 'state': state, 'stage_id': stage_id})
        write_once(directory / 'work_order.json', work_order)
        outputs, status, error, observations = (), 'UNRESOLVED', None, None
        try:
            result = self.runners[stage['tool']](work_order)
            if set(result) != {'status', 'outputs', 'observations'} or result['status'] not in ('SUCCESS', 'FAILED', 'UNRESOLVED'):
                raise ValueError('EXECUTION_RESULT_INVALID')
            observations = result['observations']
            status = result['status']
            if status == 'SUCCESS':
                outputs = tuple(file_identity(Path(p), 'output-%d' % i) for i, p in enumerate(result['outputs']))
                if not outputs or any(not Path(r.path).resolve().is_relative_to(directory) for r in outputs):
                    raise ValueError('EXECUTION_OUTPUT_NAMESPACE_MISMATCH')
            for ref in inputs + (reservation,):
                ref.validate()
            workflow.validate(frozen, scope)
        except Exception as exc:
            # Preserve the attempt, report uncertain effects, and propagate no
            # blind retry. The controller decides terminal/revision separately.
            status, error, outputs = 'UNRESOLVED', type(exc).__name__, ()
        write_once(directory / 'execution_report.json', {'status': status, 'error_type': error,
            'mode': self.mode, 'state': state, 'workflow_ref': asdict(workflow), 'stage_id': stage_id,
            'input_refs': [asdict(r) for r in inputs], 'output_refs': [asdict(r) for r in outputs],
            'reservation_ref': asdict(reservation), 'work_order_ref': asdict(file_identity(directory / 'work_order.json', 'work-order')),
            'observations': observations, 'verification_scope': 'HOST_TOOL_RUNNER_RESULT_AND_LOCAL_FILE_IDENTITIES'})
        return outputs, file_identity(directory / 'execution_report.json', 'execution-report')
