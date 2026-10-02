"""Single-owner, module-local canonical events with a hash-only global index."""
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

from core.skill_artifact import canonical_bytes, write_once
from session.session_boundary import FileIdentity, file_identity


class EventLogger:
    def __init__(self, directory, session_id):
        self.directory, self.session_id = Path(directory).resolve(), session_id
        self.index = self.directory / 'event_index.jsonl'
        if self.index.exists():
            raise ValueError('EVENT_LOG_ALREADY_OWNED_NO_RESUME')
        self.directory.mkdir(parents=True, exist_ok=True)
        with self.index.open('xb'):
            pass
        self.sequence, self.parents = 0, set()

    def emit(self, module, event_type, *, state=None, parent_event_id=None, input_refs=(), output_refs=(),
            decision=None, reason_code=None, identities=None):
        if not re.fullmatch(r'[a-z0-9_-]+(?:/[a-z0-9_-]+)*', module):
            raise ValueError('EVENT_MODULE_INVALID')
        if not isinstance(event_type, str) or not event_type or parent_event_id is not None and parent_event_id not in self.parents:
            raise ValueError('CAUSAL_PARENT_INVALID')
        state = state or {'session_id': self.session_id, 'production_run_id': None, 'attempt_id': None}
        if set(state) != {'session_id', 'production_run_id', 'attempt_id'} or state['session_id'] != self.session_id:
            raise ValueError('EVENT_SESSION_MISMATCH')
        identities = identities or {}
        if set(identities) - {'skill_id', 'skill_version', 'workflow_id', 'workflow_version', 'review_id', 'artifact_hash'}:
            raise ValueError('EVENT_FIELD_UNSUPPORTED')
        if decision is not None and (not isinstance(decision, str) or len(decision) > 2000):
            raise ValueError('EVENT_DECISION_INVALID')
        for ref in input_refs + output_refs:
            ref.validate()
        sequence = self.sequence + 1
        event_id = 'event-%06d' % sequence
        timestamp = datetime.now(timezone.utc).isoformat()
        target = self.directory / module / 'events' / (event_id + '.json')
        write_once(target, {'event_id': event_id, 'event_seq': sequence, 'timestamp': timestamp,
            'module': module, 'event_type': event_type, **state, 'parent_event_id': parent_event_id,
            'input_refs': [asdict(r) for r in input_refs], 'output_refs': [asdict(r) for r in output_refs],
            'decision': decision, 'reason_code': reason_code, **identities})
        reference = file_identity(target, event_id)
        pointer = {'event_id': event_id, 'event_seq': sequence, 'timestamp': timestamp,
            'module': module, 'path': str(target.relative_to(self.directory)), 'hash': reference.sha256}
        with self.index.open('ab') as stream:
            stream.write(canonical_bytes(pointer) + b'\n')
            stream.flush()
            os.fsync(stream.fileno())
        self.sequence, self.parents = sequence, self.parents | {event_id}
        return reference


def reconstruct(directory, session_id):
    directory = Path(directory).resolve()
    pointers = [json.loads(line) for line in (directory / 'event_index.jsonl').read_text(encoding='utf-8').splitlines()]
    events, parents, paths = [], set(), set()
    for number, pointer in enumerate(pointers, 1):
        if set(pointer) != {'event_id', 'event_seq', 'timestamp', 'module', 'path', 'hash'} or pointer['event_seq'] != number:
            raise ValueError('EVENT_SEQUENCE_INVALID')
        path = (directory / pointer['path']).resolve()
        if not path.is_relative_to(directory) or path in paths:
            raise ValueError('EVENT_PATH_INVALID')
        identity = file_identity(path, pointer['event_id'])
        if identity.sha256 != pointer['hash']:
            raise ValueError('EVENT_HASH_MISMATCH')
        data = json.loads(path.read_text(encoding='utf-8'))
        if (any(data[k] != pointer[k] for k in ('event_id', 'event_seq', 'timestamp', 'module'))
                or data['session_id'] != session_id or data['event_id'] in parents
                or data['parent_event_id'] is not None and data['parent_event_id'] not in parents):
            raise ValueError('CAUSAL_PARENT_INVALID / EVENT_SEQUENCE_INVALID')
        for value in data['input_refs'] + data['output_refs']:
            FileIdentity(**value).validate()
        events.append(data)
        parents.add(data['event_id'])
        paths.add(path)
    if {p.resolve() for p in directory.rglob('event-*.json')} != paths:
        raise ValueError('INDEX_INCOMPLETE')
    return events
