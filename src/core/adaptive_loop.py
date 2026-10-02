"""One frozen Session, sequential Workflow-bound Runs, bounded local Attempts.

Controllers retain live ownership in memory. Historical files are evidence, never
a recovery protocol. Expensive effects reserve capacity before dispatch.
"""
from dataclasses import asdict
import json
from pathlib import Path
import time

from core.skill_artifact import canonical_bytes, identifier, write_once
from session.session_boundary import SessionBoundary, file_identity

LIMITS = frozenset({'production_runs', 'attempts', 'worker_calls', 'reviewer_calls',
                   'frontier_calls', 'diagnostic_calls'})


class ResourceEnvelope:
    def __init__(self, frozen, limits, directory, *, seconds=None, clock=time.monotonic):
        frozen.validate(require_ready=True)
        if (set(limits) != LIMITS or any(type(v) is not int or v < 1 for v in limits.values())
                or seconds is not None and (type(seconds) not in (int, float) or seconds <= 0)):
            raise ValueError('ENVELOPE_INVALID')
        projection = {'resource_limits': limits, 'deadline_seconds': seconds}
        if canonical_bytes(projection).decode() not in Path(frozen.reference.specification_path).read_text(encoding='utf-8'):
            raise ValueError('ENVELOPE_NOT_IN_FROZEN_SPECIFICATION')
        self.frozen, self.limits = frozen, json.loads(canonical_bytes(limits))
        self.directory, self.seconds, self.clock = Path(directory), seconds, clock
        self.started, self.used, self.sequence = clock(), dict.fromkeys(LIMITS, 0), 0
        write_once(self.directory / 'envelope.json', {'specification_identity_sha256': frozen.identity_sha256, **projection})
        self.reference = file_identity(self.directory / 'envelope.json', 'resource-envelope')

    def remaining(self):
        self.frozen.validate(require_ready=True)
        self.reference.validate()
        data = json.loads(Path(self.reference.path).read_text(encoding='utf-8'))
        if data['resource_limits'] != self.limits or data['deadline_seconds'] != self.seconds:
            raise ValueError('ENVELOPE_CHANGED')
        return {'limits': self.limits.copy(), 'used': self.used.copy(),
            'remaining': {k: self.limits[k] - self.used[k] for k in LIMITS},
            'remaining_seconds': None if self.seconds is None else max(0, self.seconds - (self.clock() - self.started))}

    def reserve(self, kind, context):
        remaining = self.remaining()
        if kind not in LIMITS or remaining['remaining'][kind] <= 0 or remaining['remaining_seconds'] == 0:
            raise ValueError('ENVELOPE_EXHAUSTED: ' + str(kind))
        sequence = self.sequence + 1
        target = self.directory / ('reservation-%04d.json' % sequence)
        write_once(target, {'kind': kind, 'context': context, 'sequence': sequence,
            'envelope_ref': asdict(self.reference), 'remaining_before': remaining,
            'refund_policy': 'NO_REFUND_AFTER_RESERVATION_INCLUDING_UNRESOLVED_EFFECT'})
        self.sequence, self.used[kind] = sequence, self.used[kind] + 1
        return file_identity(target, 'reservation-%04d' % sequence)


class AdaptiveSession:
    def __init__(self, frozen, scope_ref, directory, limits, *, seconds=None, mode='ACTUAL', clock=time.monotonic):
        from core.workflow_artifact import checked_scope
        frozen.validate(require_ready=True)
        checked_scope(frozen, scope_ref)
        if mode not in ('ACTUAL', 'SYNTHETIC'):
            raise ValueError('EXECUTION_MODE_INVALID')
        if (set(limits) != LIMITS or any(type(v) is not int or v < 1 for v in limits.values())
                or seconds is not None and (type(seconds) not in (int, float) or seconds <= 0)):
            raise ValueError('ENVELOPE_INVALID')
        directory = Path(directory)
        if directory.exists():
            raise ValueError('SESSION_NAMESPACE_COLLISION')
        # Check the envelope before creating Session records.
        projection = {'resource_limits': limits, 'deadline_seconds': seconds}
        if canonical_bytes(projection).decode() not in Path(frozen.reference.specification_path).read_text(encoding='utf-8'):
            raise ValueError('ENVELOPE_NOT_IN_FROZEN_SPECIFICATION')
        self.frozen, self.scope, self.directory, self.mode = frozen, scope_ref, directory, mode
        self.boundary = SessionBoundary(frozen.reference.session_id, directory)
        self.binding = self.boundary.create_binding(frozen, frozen.reference.session_id + '-adaptive-loop')
        self.resources = ResourceEnvelope(frozen, limits, directory / 'resources', seconds=seconds, clock=clock)
        self.run, self.attempt, self.run_count, self.attempt_count = None, None, 0, 0
        self.pending_workflow = None
        self.decisions_consumed = set()

    def state(self):
        return {'session_id': self.frozen.reference.session_id,
            'production_run_id': self.run['production_run_id'] if self.run else None,
            'attempt_id': self.attempt['attempt_id'] if self.attempt else None}

    def assert_execution_open(self):
        self.boundary.assert_open()
        self.frozen.validate(require_ready=True)
        if self.boundary.outcome.status == 'INTERNAL_ACCEPT':
            raise ValueError('ALREADY_INTERNAL_ACCEPTED')

    def checked_decision(self, reference, actions):
        from core.frontier import InferenceResult
        from session.session_boundary import FileIdentity
        self.assert_execution_open()
        reference.validate()
        data = json.loads(Path(reference.path).read_text(encoding='utf-8'))
        if (data['selected_action'] not in actions or data['source_specification_ref'] != asdict(self.frozen.reference)
                or any(data.get(k) != v for k, v in self.state().items()) or data['inference_mode'] != self.mode):
            raise ValueError('DECISION_CONTEXT_MISMATCH')
        if reference.sha256 in self.decisions_consumed:
            raise ValueError('DECISION_ALREADY_CONSUMED')
        request = FileIdentity(**data['frontier_request_ref'])
        InferenceResult(FileIdentity(**data['frontier_result_ref']), FileIdentity(**data['frontier_invocation_ref']),
            data['inference_mode'], data['frontier_model_identity']).validate(request)
        context = json.loads(Path(request.path).read_text(encoding='utf-8'))
        if context['state'] != self.state() or canonical_bytes(context['frozen_specification']) != canonical_bytes(asdict(self.frozen)):
            raise ValueError('DECISION_CONTEXT_MISMATCH')
        current = asdict(self.run['workflow']) if self.run else None
        if data['source_workflow_ref'] != current:
            raise ValueError('DECISION_WORKFLOW_MISMATCH')
        for item in data['evidence_refs'] + data['review_refs']:
            FileIdentity(**item).validate()
        return data

    def start_run(self, workflow, decision):
        data = self.checked_decision(decision, {'PLAN_WORKFLOW', 'RESTART_PRODUCTION_RUN'})
        workflow.validate(self.frozen, self.scope)
        if data['selected_workflow_ref'] != asdict(workflow):
            raise ValueError('DECISION_WORKFLOW_MISMATCH')
        if self.run and self.attempt and not self.attempt['finished']:
            raise ValueError('UNRESOLVED_EXECUTION')
        if self.run and self.run['workflow'] == workflow:
            raise ValueError('STRATEGY_UNCHANGED_USE_ATTEMPT')
        if self.run and workflow.version != self.run['workflow'].version + 1:
            raise ValueError('WORKFLOW_VERSION_INVALID')
        number = self.run_count + 1
        run_id = 'run-%03d' % number
        directory = self.directory / 'production_runs' / run_id
        if directory.exists():
            raise ValueError('RUN_NAMESPACE_COLLISION')
        reservation = self.resources.reserve('production_runs', {**self.state(), 'next_run': run_id})
        if self.run:
            write_once(self.run['directory'] / 'terminal.json', {'status': 'SUPERSEDED',
                'cause_decision_ref': asdict(decision), 'next_run_id': run_id})
        record = {**self.state(), 'production_run_id': run_id, 'attempt_id': None,
            'workflow_ref': asdict(workflow), 'start_decision_ref': asdict(decision),
            'reservation_ref': asdict(reservation), 'mode': self.mode}
        write_once(directory / 'run.json', record)
        self.run = {'production_run_id': run_id, 'workflow': workflow, 'directory': directory}
        self.run_count, self.attempt, self.attempt_count, self.pending_workflow = number, None, 0, None
        self.decisions_consumed.add(decision.sha256)
        return file_identity(directory / 'run.json', run_id)

    def start_attempt(self, decision, *, external_namespaces=()):
        data = self.checked_decision(decision, {'CONTINUE', 'REVISE_ARTIFACT'})
        if self.run is None or self.pending_workflow is not None:
            raise ValueError('CURRENT_RUN_REQUIRED')
        if self.attempt and not self.attempt['finished']:
            raise ValueError('UNRESOLVED_EXECUTION')
        if data['selected_workflow_ref'] != asdict(self.run['workflow']):
            raise ValueError('DECISION_WORKFLOW_MISMATCH')
        attempt_id = 'attempt-%03d' % (self.attempt_count + 1)
        directory = self.run['directory'] / 'attempts' / attempt_id
        if directory.exists() or any(Path(p).exists() for p in external_namespaces):
            raise ValueError('ATTEMPT_NAMESPACE_COLLISION')
        reservation = self.resources.reserve('attempts', {**self.state(), 'next_attempt': attempt_id})
        write_once(directory / 'attempt.json', {**self.state(), 'attempt_id': attempt_id,
            'workflow_ref': asdict(self.run['workflow']), 'decision_ref': asdict(decision),
            'reservation_ref': asdict(reservation), 'external_namespaces': [str(p) for p in external_namespaces]})
        self.attempt = {'attempt_id': attempt_id, 'directory': directory, 'finished': False}
        self.attempt_count += 1
        self.decisions_consumed.add(decision.sha256)
        return file_identity(directory / 'attempt.json', attempt_id)

    def reserve_effect(self, kind):
        self.assert_execution_open()
        if self.attempt is None or self.attempt['finished']:
            raise ValueError('ACTIVE_ATTEMPT_REQUIRED')
        return self.resources.reserve(kind, self.state())

    def finish_attempt(self, status, evidence_refs):
        self.assert_execution_open()
        if not self.attempt or self.attempt['finished'] or status not in ('REVIEWED', 'FAILED', 'UNRESOLVED'):
            raise ValueError('ATTEMPT_OUTCOME_INVALID')
        for ref in evidence_refs:
            ref.validate()
        write_once(self.attempt['directory'] / 'outcome.json', {'status': status, **self.state(),
            'evidence_refs': [asdict(r) for r in evidence_refs]})
        # Unresolved effects cannot authorize another attempt or Run.
        self.attempt['finished'] = status != 'UNRESOLVED'

    def stop(self, status, reason):
        self.assert_execution_open()
        if self.run and not (self.run['directory'] / 'terminal.json').exists():
            write_once(self.run['directory'] / 'terminal.json', {'status': status, 'reason': reason})
        return self.boundary.stop(status, reason)
