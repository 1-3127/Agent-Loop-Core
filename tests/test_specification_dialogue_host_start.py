"""Synthetic regression for the actual post-creation host evidence lookup failure."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from core.adaptive_loop import SpecificationDialogueSession
from tests import test_session_start_authority as fixture

path = Path(__file__).resolve().parents[1] / 'docs/adaptive/specification-dialogue-host-start-fix/host_start.py'
spec = importlib.util.spec_from_file_location('dialogue_host_start', path)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class SpecificationDialogueHostStartTests(unittest.TestCase):
    def setUp(self):
        fixture.SessionStartAuthorityTests.setUp(self)

    def grant_fixture(self, *args, **kwargs):
        return fixture.SessionStartAuthorityTests.grant_fixture(self, *args, **kwargs)

    def start(self):
        grant, authority = self.grant_fixture()
        dialogue = SpecificationDialogueSession('session-one', self.request,
            self.root / 'dialogue', mode='SYNTHETIC', start_grant=grant, start_authority=authority)
        return dialogue, grant, authority

    def test_incomplete_host_grant_projection_reproduces_failure_after_one_creation(self):
        dialogue, grant, authority = self.start()
        data = json.loads(Path(grant.path).read_text(encoding='utf-8'))
        data.pop('receipt_ref')
        with self.assertRaises(KeyError) as error:
            authority._consumption_path(data)
        self.assertEqual(error.exception.args, ('receipt_ref',))
        self.assertTrue((dialogue.boundary.directory / 'session.json').exists())
        self.assertEqual(len(list(self.ledger.glob('*.json'))), 1)
        self.assertFalse((dialogue.boundary.directory / 'binding.json').exists())

    def test_canonical_consumption_ref_lookup_has_no_creation_consumption_or_revalidation(self):
        dialogue, grant, authority = self.start()
        ledger = next(self.ledger.glob('*.json'))
        before = ledger.read_bytes()
        owner = (dialogue.boundary.directory / 'session.json').read_bytes()
        with patch('core.adaptive_loop.SessionBoundary', side_effect=AssertionError('No second Session')), \
             patch.object(type(authority), '_consume', side_effect=AssertionError('No second consumption')), \
             patch.object(type(authority), 'validate', side_effect=AssertionError('No new validation')), \
             patch.object(type(authority), '_consumption_path', side_effect=AssertionError('No host projection lookup')):
            reference = helper.consumed_start_evidence(dialogue)
        self.assertEqual(Path(reference.path), ledger)
        self.assertEqual(reference.sha256, json.loads((dialogue.boundary.directory / 'session_start_authority.json').read_text())['consumption_ref']['sha256'])
        self.assertEqual(ledger.read_bytes(), before)
        self.assertEqual((dialogue.boundary.directory / 'session.json').read_bytes(), owner)
        self.assertFalse(dialogue.loop_bound)
        self.assertFalse((dialogue.boundary.directory / 'binding.json').exists())
        self.assertFalse((dialogue.boundary.directory / 'production_runs').exists())

    def test_corrupted_consumption_evidence_is_rejected_without_new_start(self):
        dialogue, grant, authority = self.start()
        ledger = next(self.ledger.glob('*.json'))
        ledger.write_bytes(ledger.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'evidence size mismatch'):
            helper.consumed_start_evidence(dialogue)
        self.assertEqual(len(list(self.ledger.glob('*.json'))), 1)
        self.assertFalse((dialogue.boundary.directory / 'binding.json').exists())
