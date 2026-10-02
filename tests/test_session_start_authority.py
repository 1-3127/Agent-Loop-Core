"""Synthetic/local authority fixtures only; no actual User grant or production."""
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from core.adaptive_loop import AdaptiveSession, LIMITS
from core.event_logging import reconstruct
from core.skill_artifact import canonical_bytes, write_once
from core.workflow_artifact import freeze_workflow_scope
from session.session_boundary import AuthorityReference, SessionBoundary, file_identity, freeze_specification
from session.session_start_authority import SessionStartAuthority, prepare_session_namespace
from tests import test_workflow_artifact as workflow_fixture
from tests import test_adaptive_transitions as transition_fixture
from tests import test_artifact_review as review_fixture


class SessionStartAuthorityTests(unittest.TestCase):
    def setUp(self):
        workflow_fixture.WorkflowArtifactTests.setUp(self)
        self.request_path = self.root / 'original-request.txt'
        self.request_path.write_bytes(b'SYNTHETIC user request: target with opening')
        self.request = file_identity(self.request_path, 'original-request')
        self.limits = dict.fromkeys(LIMITS, 4)
        spec = Path(self.frozen.reference.specification_path)
        spec.write_bytes(spec.read_bytes() + b'\n' + canonical_bytes({'resource_limits': self.limits, 'deadline_seconds': None}))
        self.frozen = freeze_specification(spec, replace(self.frozen.fields,
            authority_references=(AuthorityReference('request', json.dumps(asdict(self.request))),)))
        self.scope = freeze_workflow_scope(self.frozen, self.root / 'scope-authority.json', self.mapping, 'geometry')
        self.now = datetime(2026, 10, 2, 0, 1, tzinfo=timezone.utc)
        self.ledger = self.root / 'trusted-ingress-ledger'

    def grant_fixture(self, name='one', *, session_id='session-one', request=None,
                      intent='EXPLICIT_TOP_LEVEL_SESSION_START', source='SYNTHETIC_USER_FIXTURE',
                      expires='2026-10-02T01:00:00+00:00'):
        # This is an explicitly synthetic trusted-ingress fixture, not an
        # ACTUAL User receipt; it cannot authorize ACTUAL Session creation.
        message = self.root / (name + '-user.txt')
        message.write_text('둘 다 포함한다.' if intent != 'EXPLICIT_TOP_LEVEL_SESSION_START'
                           else 'SYNTHETIC: start this specific new Session.', encoding='utf-8')
        record = {'session_start_grant_id': 'grant-' + name, 'authority_kind': 'USER_SESSION_START',
            'user_message_ref': asdict(file_identity(message, 'user-message-' + name)),
            'target_request_authority_ref': asdict(request or self.request), 'target_session_id': session_id,
            'issued_at': '2026-10-02T00:00:00+00:00', 'expires_at': expires, 'mode': 'SYNTHETIC'}
        receipt = self.root / (name + '-receipt.json')
        write_once(receipt, {**record, 'receipt_id': 'receipt-' + name, 'user_intent': intent,
            'source_provenance': {'source_kind': source, 'source_event_ref': 'synthetic-event-' + name,
                                  'observation_scope': 'SYNTHETIC_ONLY'}})
        receipt_ref = file_identity(receipt, 'trusted-receipt-' + name)
        grant = self.root / (name + '-grant.json')
        write_once(grant, {**record, 'receipt_ref': asdict(receipt_ref), 'single_use': True})
        authority = SessionStartAuthority((receipt_ref,), self.ledger, mode='SYNTHETIC', now=lambda: self.now)
        return file_identity(grant, 'user-session-start-' + name), authority

    def assert_rejected(self, grant=None, authority=None, reason='SESSION_START', *, mode='ACTUAL'):
        target = self.root / 'unauthorized-session'
        with self.assertRaisesRegex(ValueError, reason):
            AdaptiveSession(self.frozen, self.scope, target, self.limits, mode=mode,
                start_grant=grant, start_authority=authority)
        self.assertFalse(target.exists())
        self.assertFalse(self.ledger.exists())

    def test_b_terminal_without_grant_rejected_and_old_terminal_unchanged(self):
        old = AdaptiveSession(self.frozen, self.scope, self.root / 'old-session', self.limits, mode='SYNTHETIC')
        old.stop('ABORT', 'LOCAL_FIXTURE_TERMINAL')
        terminal = old.directory / 'terminal.json'
        before = terminal.read_bytes()
        self.assert_rejected(reason='GRANT_REQUIRED')
        self.assertEqual(before, terminal.read_bytes())

    def test_c_corrective_publication_readiness_is_not_authority(self):
        readiness = {'tests': 'PASS', 'commit': 'fixture', 'push': 'fixture', 'HEAD_equality': True,
                     'clean_tree': True, 'next': 'fresh intake'}
        write_once(self.root / 'readiness.json', readiness)
        audit = self.root / 'development' / 'rejected.json'
        target = self.root / 'fresh-fixture-namespace'
        with self.assertRaisesRegex(ValueError, 'GRANT_REQUIRED'):
            prepare_session_namespace(target, None, None, 'session-one', self.request, audit_path=audit)
        self.assertFalse(target.exists())
        self.assertEqual(json.loads(audit.read_text())['event_type'], 'SESSION_START_REJECTED')
        self.assertEqual(json.loads(audit.read_text())['effects'], 0)
        self.assert_rejected()

    def test_d_explicit_synthetic_user_grant_exactly_one_bound_start(self):
        grant, authority = self.grant_fixture()
        namespace = self.root / 'authorized-fixture'
        prepare_session_namespace(namespace, grant, authority, 'session-one', self.request,
            mode='SYNTHETIC', audit_path=self.root / 'validated.json')
        self.assertFalse(self.ledger.exists())  # Outer preflight never consumes.
        session = AdaptiveSession(self.frozen, self.scope, namespace / 'session', self.limits,
            mode='SYNTHETIC', start_grant=grant, start_authority=authority)
        record = json.loads((session.directory / 'session_start_authority.json').read_text())
        self.assertEqual(record['grant_ref'], asdict(grant))
        self.assertEqual(record['specification_identity_sha256'], self.frozen.identity_sha256)
        ledger = list(self.ledger.glob('*.json'))
        self.assertEqual(len(ledger), 1)
        before = ledger[0].read_bytes()
        # Fresh authority handle with the SAME ingress ledger still rejects.
        second_authority = SessionStartAuthority(authority.trusted_receipts, self.ledger,
            mode='SYNTHETIC', now=lambda: self.now)
        target = self.root / 'second-fixture-session'
        with self.assertRaisesRegex(ValueError, 'ALREADY_CONSUMED'):
            AdaptiveSession(self.frozen, self.scope, target, self.limits, mode='SYNTHETIC',
                start_grant=grant, start_authority=second_authority)
        self.assertFalse(target.exists())
        self.assertEqual(before, ledger[0].read_bytes())
        events = reconstruct(session.directory / 'logs', 'session-one')
        self.assertEqual([e['event_type'] for e in events], ['USER_SESSION_START_AUTHORITY_RECEIVED',
            'SESSION_START_GRANT_VALIDATED', 'SESSION_START_GRANT_CONSUMED', 'SESSION_BOUND'])

    def test_e_same_development_chat_is_not_a_grant(self):
        write_once(self.root / 'chat.json', {'continue_development_chat': True, 'prior_start_approved': True})
        self.assert_rejected(reason='GRANT_REQUIRED')

    def test_f_subject_clarification_is_not_start_authority(self):
        grant, authority = self.grant_fixture(intent='SUBJECT_CLARIFICATION')
        self.assert_rejected(grant, authority, 'USER_AUTHORITY_REQUIRED', mode='SYNTHETIC')

    def test_g_foreign_session_request_and_stale_grants_reject_before_mkdir(self):
        other = self.root / 'another-request.txt'
        other.write_text('A different subject', encoding='utf-8')
        for name, kwargs, reason in [
            ('foreign-session', {'session_id': 'another-session'}, 'SESSION_MISMATCH'),
            ('foreign-request', {'request': file_identity(other, 'other')}, 'REQUEST_MISMATCH'),
            ('expired', {'expires': '2026-10-02T00:00:01+00:00'}, 'STALE')]:
            with self.subTest(name=name):
                grant, authority = self.grant_fixture(name, **kwargs)
                self.assert_rejected(grant, authority, reason, mode='SYNTHETIC')

    def test_unpinned_and_frontier_self_issued_receipts_are_rejected(self):
        grant, authority = self.grant_fixture()
        untrusted = SessionStartAuthority((), self.ledger, mode='SYNTHETIC', now=lambda: self.now)
        self.assert_rejected(grant, untrusted, 'UNTRUSTED_RECEIPT', mode='SYNTHETIC')
        forged, authority = self.grant_fixture('frontier', source='FRONTIER')
        self.assert_rejected(forged, authority, 'USER_AUTHORITY_REQUIRED', mode='SYNTHETIC')

    def test_synthetic_grant_cannot_be_used_on_actual_ingress(self):
        grant, authority = self.grant_fixture()
        self.assert_rejected(grant, authority, 'MODE_MISMATCH')
        actual = SessionStartAuthority(authority.trusted_receipts, self.ledger, mode='ACTUAL', now=lambda: self.now)
        self.assert_rejected(grant, actual, 'GRANT_INVALID')

    def test_malformed_reused_previous_and_mutated_message_reject(self):
        grant, authority = self.grant_fixture()
        data = json.loads(Path(grant.path).read_text())
        for key, value in [('single_use', False), ('authority_kind', 'REVISE_WORKFLOW'), ('extra', 'NEW_SESSION')]:
            modified = dict(data, **{key: value})
            p = self.root / ('invalid-' + key + '.json')
            write_once(p, modified)
            self.assert_rejected(file_identity(p, 'bad'), authority, 'GRANT_INVALID', mode='SYNTHETIC')
        p = self.root / 'forged-label.json'
        write_once(p, dict(data, mode='ACTUAL'))
        actual = SessionStartAuthority(authority.trusted_receipts, self.ledger, mode='ACTUAL', now=lambda: self.now)
        self.assert_rejected(file_identity(p, 'forged-actual'), actual, 'RECEIPT_MISMATCH')
        Path(data['user_message_ref']['path']).write_text('tampered', encoding='utf-8')
        self.assert_rejected(grant, authority, 'EVIDENCE_INVALID', mode='SYNTHETIC')

    def test_raw_boundary_actual_creation_and_existing_unbound_binding_are_gated(self):
        target = self.root / 'raw-session'
        with self.assertRaisesRegex(ValueError, 'GRANT_REQUIRED'):
            SessionBoundary('session-one', target)
        self.assertFalse(target.exists())
        legacy = SessionBoundary('session-one', target, mode='SYNTHETIC')
        before = {p.name: p.read_bytes() for p in target.iterdir()}
        reader = SessionBoundary('session-one', target)
        with self.assertRaisesRegex(ValueError, 'GRANT_REQUIRED'):
            reader.create_binding(self.frozen, 'loop-one')
        self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})
        legacy.create_binding(self.frozen, 'synthetic-loop')
        legacy.stop('ABORT', 'FIXTURE_CLOSED_READER')
        before = {p.name: p.read_bytes() for p in target.iterdir()}
        self.assertEqual(SessionBoundary('session-one', target).outcome.status, 'ABORT')
        self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})

    def test_request_target_mismatch_blocks_outer_preflight(self):
        grant, authority = self.grant_fixture()
        p = self.root / 'other.txt'
        p.write_text('foreign request', encoding='utf-8')
        target = self.root / 'outer-mismatch'
        with self.assertRaisesRegex(ValueError, 'REQUEST_MISMATCH'):
            prepare_session_namespace(target, grant, authority, 'session-one', file_identity(p, 'other'), mode='SYNTHETIC')
        self.assertFalse(target.exists())
        self.assertFalse(self.ledger.exists())

    def test_actual_self_labelled_receipt_without_runtime_user_event_rejected(self):
        grant, _ = self.grant_fixture('self-label')
        data = json.loads(Path(grant.path).read_text())
        receipt = json.loads(Path(data['receipt_ref']['path']).read_text())
        receipt['mode'] = 'ACTUAL'
        receipt['source_provenance'] = {'source_kind': 'TRUSTED_USER_INGRESS',
            'source_event_ref': 'host-invented-user-event', 'observation_scope': 'HOST_ATTESTED_USER_MESSAGE'}
        path = self.root / 'self-labelled-receipt.json'
        write_once(path, receipt)
        pinned = file_identity(path, 'self-labelled')
        data.update(mode='ACTUAL', receipt_ref=asdict(pinned))
        path = self.root / 'self-labelled-grant.json'
        write_once(path, data)
        authority = SessionStartAuthority((pinned,), self.ledger, mode='ACTUAL', now=lambda: self.now)
        # Exercise validation only; never create an ACTUAL Session from fake text.
        with self.assertRaisesRegex(ValueError, 'USER_EVENT|USER_AUTHORITY'):
            authority.validate(file_identity(path, 'self-labelled-grant'), 'session-one', frozen=self.frozen)
        self.assertFalse(self.ledger.exists())

    def test_actual_fake_user_event_in_consumer_directory_rejected(self):
        from session.session_start_authority import _validate_runtime_user_event
        import hashlib
        p = self.root / 'rollout-fake-thread.jsonl'
        header = canonical_bytes({'type': 'session_meta', 'payload': {'id': 'fake-thread'}}) + b'\n'
        raw = canonical_bytes({'type': 'response_item', 'payload': {'type': 'message', 'role': 'user',
            'content': [{'type': 'input_text', 'text': 'Host-invented permission'}]}}) + b'\n'
        p.write_bytes(header + raw)
        text = self.root / 'host-message.txt'
        text.write_bytes(b'Host-invented permission')
        source = {'path': str(p), 'offset': len(header), 'bytes': len(raw),
                  'sha256': hashlib.sha256(raw).hexdigest(), 'thread_id': 'fake-thread'}
        with self.assertRaisesRegex(ValueError, 'USER_EVENT_UNTRUSTED'):
            _validate_runtime_user_event(source, file_identity(text, 'host-label'))

    def test_grant_id_relabel_cannot_spend_same_user_start_event_twice(self):
        grant, authority = self.grant_fixture('reissue')
        AdaptiveSession(self.frozen, self.scope, self.root / 'first-granted', self.limits,
            mode='SYNTHETIC', start_grant=grant, start_authority=authority)
        data = json.loads(Path(grant.path).read_text())
        receipt = json.loads(Path(data['receipt_ref']['path']).read_text())
        receipt['session_start_grant_id'] = 'renamed-grant'
        p = self.root / 'renamed-receipt.json'
        write_once(p, receipt)
        pin = file_identity(p, 'renamed-receipt')
        data.update(session_start_grant_id='renamed-grant', receipt_ref=asdict(pin))
        p = self.root / 'renamed-grant.json'
        write_once(p, data)
        new_authority = SessionStartAuthority((pin,), self.ledger, mode='SYNTHETIC', now=lambda: self.now)
        with self.assertRaisesRegex(ValueError, 'ALREADY_CONSUMED'):
            new_authority.validate(file_identity(p, 'renamed'), 'session-one', frozen=self.frozen, mode='SYNTHETIC')
        self.assertEqual(len(list(self.ledger.glob('*.json'))), 1)

    def test_missing_expected_request_cannot_prepare_namespace(self):
        grant, authority = self.grant_fixture('missing-request')
        target = self.root / 'missing-expected-request'
        with self.assertRaisesRegex(ValueError, 'REQUEST'):
            prepare_session_namespace(target, grant, authority, 'session-one', None, mode='SYNTHETIC')
        self.assertFalse(target.exists())


class SessionStartLoopBoundaryTests(unittest.TestCase):
    def setUp(self):
        transition_fixture.AdaptiveTransitionTests.setUp(self)

    def decide(self, *args, **kwargs):
        return transition_fixture.AdaptiveTransitionTests.decide(self, *args, **kwargs)

    def action(self, *args, **kwargs):
        return transition_fixture.AdaptiveTransitionTests.action(self, *args, **kwargs)

    def test_a_reviewer_revise_workflow_restart_retains_session_without_grant(self):
        frozen_identity, sid = self.frozen.identity_sha256, self.session.state()['session_id']
        with patch('session.session_start_authority.SessionStartAuthority._consume', side_effect=AssertionError('No new grant consumption')) as consume, \
             patch('core.adaptive_loop.SessionBoundary', side_effect=AssertionError('No second Session constructor')) as constructor:
            review = transition_fixture.AdaptiveTransitionTests.reviewed(self)
            workflow = transition_fixture.AdaptiveTransitionTests.revision(self, review)
            self.session.start_run(workflow, self.action('RESTART_PRODUCTION_RUN', review))
            self.assertEqual(self.session.run['workflow'].version, 2)
            self.assertEqual(self.session.state()['production_run_id'], 'run-002')
            self.assertEqual(self.session.state()['session_id'], sid)
            self.assertEqual(self.frozen.identity_sha256, frozen_identity)
            constructor.assert_not_called()
            consume.assert_not_called()
        self.assertFalse((self.root / 'intake').exists())

    def test_h_reviewer_new_session_and_frontier_action_schema_cannot_issue_grant(self):
        from core.artifact_review import ArtifactReviewer
        from core.frontier import ACTIONS
        self.assertNotIn('NEW_SESSION', ACTIONS)
        with self.assertRaisesRegex(ValueError, 'REVIEW_RESULT_INVALID'):
            ArtifactReviewer(review_fixture.SyntheticReview('NEW_SESSION')).review(
                self.frozen, self.scope, self.workflow, self.artifact, self.root / 'invalid-review')
        self.assertFalse((self.root / 'invalid-review' / 'review.json').exists())
        with self.assertRaises(ValueError):
            self.decide('NEW_SESSION')
        self.assertEqual(self.session.state()['session_id'], self.frozen.reference.session_id)
        self.assertFalse((self.session.directory / 'session_start_authority.json').exists())


if __name__ == '__main__':
    unittest.main()
