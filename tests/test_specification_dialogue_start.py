"""Local/synthetic reproducer of the actual pre-freeze creation defect."""
import json
from dataclasses import asdict, replace
from pathlib import Path
import unittest
from unittest.mock import patch

from core.adaptive_loop import AdaptiveSession
from core.event_logging import reconstruct
from session.session_boundary import SessionBoundary, AuthorityReference, freeze_specification
from core.workflow_artifact import freeze_workflow_scope
from tests import test_session_start_authority as fixture


class SpecificationDialogueStartTests(unittest.TestCase):
    def setUp(self):
        fixture.SessionStartAuthorityTests.setUp(self)

    def grant_fixture(self, *args, **kwargs):
        return fixture.SessionStartAuthorityTests.grant_fixture(self, *args, **kwargs)

    def test_user_granted_boundary_can_start_before_frozen_specification(self):
        grant, authority = self.grant_fixture()
        directory = self.root / 'dialogue-first'
        boundary = SessionBoundary('session-one', directory, mode='SYNTHETIC',
            start_grant=grant, start_authority=authority, request_authority_ref=self.request)
        self.assertEqual(boundary.outcome.status, 'REQUEST_RECEIVED')
        self.assertFalse((directory / 'binding.json').exists())
        self.assertFalse((directory / 'resources').exists())
        record = json.loads((directory / 'session_start_authority.json').read_text())
        self.assertEqual(record['start_phase'], 'SPECIFICATION_DIALOGUE')
        self.assertNotIn('specification_identity_sha256', record)
        self.assertEqual(len(list(self.ledger.glob('*.json'))), 1)

    def begin(self, name='dialogue', **kwargs):
        from core.adaptive_loop import SpecificationDialogueSession
        grant, authority = self.grant_fixture(name)
        return SpecificationDialogueSession('session-one', self.request, self.root/name,
            mode='SYNTHETIC', start_grant=grant, start_authority=authority, **kwargs)

    def promote(self, dialogue, frozen=None, scope=None, **kwargs):
        return AdaptiveSession(frozen or self.frozen, scope or self.scope, dialogue.boundary.directory,
            self.limits, mode='SYNTHETIC', dialogue_session=dialogue, **kwargs)

    def test_dialogue_start_has_authority_events_without_production_or_frozen_binding(self):
        dialogue = self.begin()
        directory = dialogue.boundary.directory
        events = reconstruct(directory/'logs', 'session-one')
        self.assertEqual([e['event_type'] for e in events], ['USER_SESSION_START_AUTHORITY_RECEIVED',
            'SESSION_START_GRANT_VALIDATED', 'SESSION_START_GRANT_CONSUMED', 'SESSION_BOUND'])
        self.assertEqual(events[-1]['reason_code'], 'USER_REQUEST_BOUND_SPECIFICATION_PENDING')
        for name in ('binding.json','resources','production_runs','terminal.json'):
            self.assertFalse((directory/name).exists())
        self.assertFalse(dialogue.loop_bound)

    def test_ready_specification_promotes_same_live_session_without_second_creation_or_consumption(self):
        dialogue = self.begin()
        boundary, logger = dialogue.boundary, dialogue.logger
        owner_before = (boundary.directory/'session.json').read_bytes()
        ledger = next(self.ledger.glob('*.json')); consumed_before = ledger.read_bytes()
        with patch('core.adaptive_loop.SessionBoundary', side_effect=AssertionError('No second Session')) as constructor, \
             patch('session.session_start_authority.SessionStartAuthority._consume', side_effect=AssertionError('No second consumption')) as consume:
            session = self.promote(dialogue)
            constructor.assert_not_called(); consume.assert_not_called()
        self.assertIs(session.boundary, boundary)
        self.assertIs(session.logger, logger)
        self.assertEqual(owner_before, (boundary.directory/'session.json').read_bytes())
        self.assertEqual(consumed_before, ledger.read_bytes())
        self.assertEqual(session.binding.specification.identity_sha256, self.frozen.identity_sha256)
        self.assertTrue(dialogue.loop_bound)
        self.assertEqual(reconstruct(boundary.directory/'logs','session-one')[-1]['event_type'], 'FROZEN_SPECIFICATION_BOUND')
        self.assertIsNone(session.run); self.assertIsNone(session.attempt)
        with self.assertRaisesRegex(ValueError, 'OWNER_MISMATCH'):
            self.promote(dialogue)

    def test_pre_freeze_grant_is_single_use_and_no_second_namespace_is_created(self):
        grant, authority = self.grant_fixture()
        first = self.root/'first-pre-freeze'
        SessionBoundary('session-one', first, mode='SYNTHETIC', start_grant=grant,
            start_authority=authority, request_authority_ref=self.request)
        second = self.root/'second-pre-freeze'
        with self.assertRaisesRegex(ValueError,'ALREADY_CONSUMED'):
            SessionBoundary('session-one', second, mode='SYNTHETIC', start_grant=grant,
                start_authority=authority, request_authority_ref=self.request)
        self.assertFalse(second.exists())
        self.assertEqual(len(list(self.ledger.glob('*.json'))),1)

    def test_missing_or_foreign_request_is_rejected_before_creation_and_consumption(self):
        from session.session_boundary import file_identity
        grant, authority = self.grant_fixture()
        for request, reason in [(None,'REQUEST_BINDING_REQUIRED'),(file_identity(Path(self.frozen.reference.specification_path),'foreign'),'REQUEST_MISMATCH')]:
            target = self.root/('rejected-'+reason)
            with self.assertRaisesRegex(ValueError,reason):
                SessionBoundary('session-one', target, mode='SYNTHETIC', start_grant=grant,
                    start_authority=authority, request_authority_ref=request)
            self.assertFalse(target.exists())
            self.assertFalse(self.ledger.exists())

    def test_not_ready_or_foreign_session_cannot_enter_loop(self):
        dialogue = self.begin()
        not_ready = replace(self.frozen, fields=replace(self.frozen.fields,specification_ready=False))
        with self.assertRaisesRegex(ValueError,'NOT_EXECUTION_ELIGIBLE'):
            self.promote(dialogue,frozen=not_ready)
        fields = replace(self.frozen.fields,session_id='another-session')
        foreign = freeze_specification(self.frozen.reference.specification_path,fields)
        scope = freeze_workflow_scope(foreign,self.root/'foreign-scope.json',self.mapping,'geometry')
        with self.assertRaisesRegex(ValueError,'OWNER_MISMATCH'):
            self.promote(dialogue,frozen=foreign,scope=scope)
        self.assertFalse((dialogue.boundary.directory/'binding.json').exists())
        self.assertFalse((dialogue.boundary.directory/'resources').exists())

    def test_foreign_ready_request_cannot_bind_consumed_start(self):
        dialogue = self.begin()
        fields = replace(self.frozen.fields,authority_references=(AuthorityReference('request','foreign request'),))
        frozen = freeze_specification(self.frozen.reference.specification_path,fields)
        scope = freeze_workflow_scope(frozen,self.root/'foreign-request-scope.json',self.mapping,'geometry')
        with self.assertRaisesRegex(ValueError,'REQUEST_MISMATCH'):
            self.promote(dialogue,frozen=frozen,scope=scope)
        self.assertFalse((dialogue.boundary.directory/'binding.json').exists())
        self.assertFalse((dialogue.boundary.directory/'resources').exists())

    def test_historical_reader_and_directory_reconstruction_do_not_resume_dialogue(self):
        dialogue = self.begin()
        reader = SessionBoundary('session-one',dialogue.boundary.directory,mode='SYNTHETIC')
        before={p.relative_to(reader.directory):p.read_bytes() for p in reader.directory.rglob('*') if p.is_file()}
        with self.assertRaisesRegex(ValueError,'LIVE_OWNER_REQUIRED'):
            reader.create_binding(self.frozen,'loop-one')
        with self.assertRaisesRegex(ValueError,'SESSION_NAMESPACE_COLLISION'):
            AdaptiveSession(self.frozen,self.scope,reader.directory,self.limits,mode='SYNTHETIC')
        after={p.relative_to(reader.directory):p.read_bytes() for p in reader.directory.rglob('*') if p.is_file()}
        self.assertEqual(before,after)

    def test_terminal_dialogue_cannot_promote_or_restart(self):
        dialogue = self.begin()
        dialogue.boundary.stop('ABORT','SYNTHETIC_DIALOGUE_STOP')
        terminal = dialogue.boundary.directory/'terminal.json'; before=terminal.read_bytes()
        with self.assertRaisesRegex(ValueError,'ALREADY_TERMINAL'):
            self.promote(dialogue)
        self.assertEqual(before,terminal.read_bytes())
        self.assertFalse((dialogue.boundary.directory/'binding.json').exists())

    def test_actual_mode_missing_grant_and_synthetic_start_are_rejected(self):
        from core.adaptive_loop import SpecificationDialogueSession
        target=self.root/'actual-denied'
        with self.assertRaisesRegex(ValueError,'GRANT_REQUIRED'):
            SpecificationDialogueSession('session-one',self.request,target)
        self.assertFalse(target.exists())
        grant,authority=self.grant_fixture()
        with self.assertRaisesRegex(ValueError,'MODE_MISMATCH'):
            SpecificationDialogueSession('session-one',self.request,target,start_grant=grant,start_authority=authority)
        self.assertFalse(target.exists())
        self.assertFalse(self.ledger.exists())


if __name__ == '__main__':
    unittest.main()
