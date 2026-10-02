"""User-only top-level start gate; no grant issuer, inference or effect adapter.

Receipt pins are supplied by a separate trusted User-ingress boundary. This
module verifies their local provenance/hash bindings, not an account signature.
The consumer cannot register receipts or derive authority from model output.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Callable

from session.session_boundary import FileIdentity, _write_once, file_identity

GRANT_FIELDS = frozenset({'session_start_grant_id', 'authority_kind', 'user_message_ref',
    'receipt_ref', 'target_request_authority_ref', 'target_session_id', 'issued_at',
    'expires_at', 'single_use', 'mode'})
RECEIPT_FIELDS = frozenset({'receipt_id', 'session_start_grant_id', 'authority_kind',
    'user_message_ref', 'target_request_authority_ref', 'target_session_id', 'issued_at',
    'expires_at', 'mode', 'source_provenance', 'user_intent'})


def _timestamp(value):
    try:
        result = datetime.fromisoformat(value)
        if result.tzinfo is None:
            raise ValueError()
        return result
    except (TypeError, ValueError):
        raise ValueError('SESSION_START_TIME_INVALID') from None


def _ref(value):
    try:
        reference = FileIdentity(**value)
        reference.validate()
        return reference
    except (TypeError, ValueError, OSError):
        raise ValueError('SESSION_START_EVIDENCE_INVALID') from None


def _read(reference):
    if not isinstance(reference, FileIdentity):
        raise ValueError('SESSION_START_EVIDENCE_INVALID')
    reference.validate()
    try:
        value = json.loads(Path(reference.path).read_text(encoding='utf-8'))
    except (ValueError, OSError):
        raise ValueError('SESSION_START_EVIDENCE_INVALID') from None
    if not isinstance(value, dict):
        raise ValueError('SESSION_START_EVIDENCE_INVALID')
    return value


def _validate_runtime_user_event(source, message):
    """Read one pinned User event from the runtime-owned local Codex transcript.

    Do not copy the full transcript or inspect model reasoning. The byte-range
    hash remains stable while the runtime appends later events. This authenticates
    the configured local origin, not a cryptographically signed account.
    """
    fields = {'path', 'offset', 'bytes', 'sha256', 'thread_id'}
    if not isinstance(source, dict) or set(source) != fields:
        raise ValueError('SESSION_START_RUNTIME_USER_EVENT_REQUIRED')
    if (type(source['offset']) is not int or source['offset'] < 0
            or type(source['bytes']) is not int or not 0 < source['bytes'] <= 1024 * 1024
            or not isinstance(source['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', source['sha256'])
            or not isinstance(source['thread_id'], str) or not isinstance(source['path'], str)):
        raise ValueError('SESSION_START_RUNTIME_USER_EVENT_INVALID')
    path = Path(source['path']).resolve()
    # Consumer-generated files/labels cannot stand in for runtime User events.
    root = (Path.home() / '.codex/sessions').resolve()
    if (not path.is_relative_to(root) or not path.is_file()
            or not path.name.endswith('-' + source['thread_id'] + '.jsonl')):
        raise ValueError('SESSION_START_RUNTIME_USER_EVENT_UNTRUSTED')
    try:
        with path.open('rb') as stream:
            header = json.loads(stream.readline(1024 * 1024))
            if source['offset']:
                stream.seek(source['offset'] - 1)
                if stream.read(1) != b'\n':
                    raise ValueError()
            stream.seek(source['offset'])
            raw = stream.readline(1024 * 1024 + 1)
        event = json.loads(raw)
        payload = event.get('payload', {})
        if (header.get('type') != 'session_meta' or header.get('payload', {}).get('id') != source['thread_id']
                or len(raw) != source['bytes'] or hashlib.sha256(raw).hexdigest() != source['sha256']
                or event.get('type') != 'response_item' or payload.get('type') != 'message'
                or payload.get('role') != 'user' or not isinstance(payload.get('content'), list)):
            raise ValueError()
        text = ''.join(item['text'] for item in payload['content'] if item.get('type') == 'input_text')
        if not text or text.encode('utf-8') != Path(message.path).read_bytes():
            raise ValueError()
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        raise ValueError('SESSION_START_RUNTIME_USER_EVENT_MISMATCH') from None
    return {'thread_id': source['thread_id'], 'offset': source['offset'], 'sha256': source['sha256']}


@dataclass(frozen=True, init=False)
class SessionStartAuthority:
    """Pinned User receipts + one durable consumption ledger per trusted ingress.

    Provision pins/ledger outside the consumer from observed User events. Never
    build pins from a grant's own receipt_ref or relocate/reset the ledger to
    reuse a grant. Writable-host compromise is outside local attestation scope.
    Synthetic pins never authorize ACTUAL creation.
    """
    trusted_receipts: tuple
    ledger_directory: Path
    mode: str
    now: Callable

    def __init__(self, trusted_receipts, ledger_directory, *, mode='ACTUAL', now=None):
        if mode not in ('ACTUAL', 'SYNTHETIC') or not isinstance(trusted_receipts, tuple):
            raise ValueError('SESSION_START_TRUST_INVALID')
        if any(not isinstance(r, FileIdentity) for r in trusted_receipts):
            raise ValueError('SESSION_START_TRUST_INVALID')
        object.__setattr__(self, 'trusted_receipts', trusted_receipts)
        object.__setattr__(self, 'ledger_directory', Path(ledger_directory).resolve())
        object.__setattr__(self, 'mode', mode)
        object.__setattr__(self, 'now', now or (lambda: datetime.now(timezone.utc)))

    def _consumption_path(self, data):
        receipt = _read(_ref(data['receipt_ref']))
        source = receipt['source_provenance']['source_event_ref']
        if data['mode'] == 'ACTUAL':
            source = {key: source[key] for key in ('thread_id', 'offset')}
        key = json.dumps(source, sort_keys=True, separators=(',', ':')).encode('utf-8')
        # Renaming/reissuing a grant ID cannot spend the same User start twice.
        return self.ledger_directory / (hashlib.sha256(key).hexdigest() + '.json')

    def validate(self, grant, session_id, *, request_authority_ref=None, frozen=None, mode='ACTUAL'):
        if grant is None:
            raise ValueError('SESSION_START_GRANT_REQUIRED')
        if mode != self.mode:
            raise ValueError('SESSION_START_TRUST_MODE_MISMATCH')
        data = _read(grant)
        if (set(data) != GRANT_FIELDS or data.get('authority_kind') != 'USER_SESSION_START'
                or data.get('single_use') is not True or data.get('mode') != mode
                or not isinstance(data.get('session_start_grant_id'), str)
                or not data['session_start_grant_id'].strip()
                or not isinstance(data.get('target_session_id'), str) or not data['target_session_id'].strip()):
            raise ValueError('SESSION_START_GRANT_INVALID')
        if data['target_session_id'] != session_id:
            raise ValueError('SESSION_START_SESSION_MISMATCH')
        receipt_ref = _ref(data['receipt_ref'])
        # A claimed receipt in the grant is never a trust anchor.
        if receipt_ref not in self.trusted_receipts:
            raise ValueError('SESSION_START_UNTRUSTED_RECEIPT')
        receipt = _read(receipt_ref)
        if set(receipt) != RECEIPT_FIELDS:
            raise ValueError('SESSION_START_RECEIPT_INVALID')
        for key in ('session_start_grant_id', 'authority_kind', 'user_message_ref',
                    'target_request_authority_ref', 'target_session_id', 'issued_at', 'expires_at', 'mode'):
            if receipt[key] != data[key]:
                raise ValueError('SESSION_START_RECEIPT_MISMATCH')
        provenance = receipt['source_provenance']
        if (receipt['user_intent'] != 'EXPLICIT_TOP_LEVEL_SESSION_START'
                or not isinstance(receipt['receipt_id'], str) or not receipt['receipt_id'].strip()
                or not isinstance(provenance, dict)
                or set(provenance) != {'source_kind', 'source_event_ref', 'observation_scope'}
                or mode == 'SYNTHETIC' and (not isinstance(provenance['source_event_ref'], str) or not provenance['source_event_ref'].strip())
                or provenance['source_kind'] != ('TRUSTED_USER_INGRESS' if mode == 'ACTUAL' else 'SYNTHETIC_USER_FIXTURE')
                or provenance['observation_scope'] != ('HOST_ATTESTED_USER_MESSAGE' if mode == 'ACTUAL' else 'SYNTHETIC_ONLY')):
            raise ValueError('SESSION_START_USER_AUTHORITY_REQUIRED')
        message = _ref(data['user_message_ref'])
        request = _ref(data['target_request_authority_ref'])
        if message.bytes == 0:
            raise ValueError('SESSION_START_USER_AUTHORITY_REQUIRED')
        if mode == 'ACTUAL':
            _validate_runtime_user_event(provenance['source_event_ref'], message)
        if request_authority_ref is not None and request != request_authority_ref:
            raise ValueError('SESSION_START_REQUEST_MISMATCH')
        if frozen is not None:
            frozen.validate(require_ready=True)
            if frozen.reference.session_id != session_id:
                raise ValueError('SESSION_START_SESSION_MISMATCH')
            sources = []
            for item in frozen.fields.authority_references:
                try:
                    sources.append(json.loads(item.source_ref))
                except (TypeError, ValueError):
                    pass
            if asdict(request) not in sources:
                raise ValueError('SESSION_START_REQUEST_MISMATCH')
        issued, expires, now = _timestamp(data['issued_at']), _timestamp(data['expires_at']), self.now()
        if now.tzinfo is None or expires <= issued or now < issued or now >= expires:
            raise ValueError('SESSION_START_GRANT_STALE')
        if self._consumption_path(data).exists():
            raise ValueError('SESSION_START_GRANT_ALREADY_CONSUMED')
        return data

    def _consume(self, grant, session_id, frozen, *, mode='ACTUAL'):
        """Only SessionBoundary top-level creation calls this, before mkdir.

        Exclusive ledger creation is at-most-once, including failed/interrupted
        starts. No refund, resume or implicit new grant is offered.
        """
        data = self.validate(grant, session_id, frozen=frozen, mode=mode)
        target = self._consumption_path(data)
        record = {'event_type': 'SESSION_START_GRANT_CONSUMED',
            'session_start_grant_id': data['session_start_grant_id'],
            'grant_ref': asdict(grant), 'receipt_ref': data['receipt_ref'],
            'user_message_ref': data['user_message_ref'],
            'target_request_authority_ref': data['target_request_authority_ref'],
            'session_id': session_id, 'specification_identity_sha256': frozen.identity_sha256,
            'consumed_at': self.now().isoformat(), 'mode': mode, 'refund_policy': 'NO_REFUND_NO_REUSE'}
        self.ledger_directory.mkdir(parents=True, exist_ok=True)
        try:
            _write_once(target, record)
        except FileExistsError:
            raise ValueError('SESSION_START_GRANT_ALREADY_CONSUMED') from None
        return file_identity(target, 'session-start-consumption')


def preflight_session_start(grant, authority, session_id, request_authority_ref, *, mode='ACTUAL', audit_path=None):
    """Outer initializer/intake gate; does not consume or begin a Core Session.

    audit_path must be an external development/evidence path, not a new Session
    namespace. Host-generated `next`, readiness and clarification are not inputs.
    """
    try:
        if not isinstance(request_authority_ref, FileIdentity):
            raise ValueError('SESSION_START_REQUEST_BINDING_REQUIRED')
        request_authority_ref.validate()
        if not isinstance(authority, SessionStartAuthority):
            raise ValueError('SESSION_START_GRANT_REQUIRED')
        data = authority.validate(grant, session_id, request_authority_ref=request_authority_ref, mode=mode)
    except (ValueError, OSError) as error:
        if audit_path is not None:
            Path(audit_path).parent.mkdir(parents=True, exist_ok=True)
            _write_once(Path(audit_path), {'event_type': 'SESSION_START_REJECTED', 'session_id': session_id,
                'reason_code': str(error), 'mode': mode, 'effects': 0})
        raise
    if audit_path is not None:
        Path(audit_path).parent.mkdir(parents=True, exist_ok=True)
        _write_once(Path(audit_path), {'event_type': 'SESSION_START_GRANT_VALIDATED', 'session_id': session_id,
            'grant_ref': asdict(grant), 'receipt_ref': data['receipt_ref'], 'mode': mode, 'consumed': False})
    return data


def prepare_session_namespace(namespace, grant, authority, session_id, request_authority_ref,
                              *, mode='ACTUAL', audit_path=None):
    """Prospective outer host entry; unauthorized fresh intake cannot mkdir.

    Must precede initializer/intake. Does not run models, freeze a Specification,
    bind a Session or consume a grant. Core creation independently rechecks.
    """
    namespace = Path(namespace).resolve()
    if audit_path is not None and Path(audit_path).resolve().is_relative_to(namespace):
        raise ValueError('SESSION_START_AUDIT_MUST_BE_EXTERNAL')
    data = preflight_session_start(grant, authority, session_id, request_authority_ref,
        mode=mode, audit_path=audit_path)
    if namespace.exists():
        raise ValueError('SESSION_NAMESPACE_COLLISION')
    namespace.mkdir(parents=True, exist_ok=False)
    return data
