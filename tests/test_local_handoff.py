from dataclasses import asdict
import json
from pathlib import Path
import unittest

from core.artifact_review import ArtifactReviewer
from core.skill_artifact import write_once
from session.session_boundary import file_identity
from tests import test_adaptive_transitions as fixture
from tests import test_artifact_review as review_fixture


class LocalHandoffTests(unittest.TestCase):
    def setUp(self):
        fixture.AdaptiveTransitionTests.setUp(self)
        review = fixture.AdaptiveTransitionTests.reviewed(self, 'PASS', ('MET', 'MET'))
        decision = fixture.AdaptiveTransitionTests.action(self, 'ACCEPT', review)
        self.session.accept(decision, self.artifact, review)
        self.package = self.session.boundary.prepare_delivery()

    def decide(self, *args, **kwargs):
        return fixture.AdaptiveTransitionTests.decide(self, *args, **kwargs)

    def record(self, *, artifact=None, package=None):
        output = self.root / 'export.bin'
        output.write_bytes(Path(self.output.path).read_bytes())
        record = self.root / 'handoff.json'
        write_once(record, {'session_id': self.frozen.reference.session_id, 'delivery_package': asdict(package or self.package),
            'boundary': 'LOCAL_DELIVERABLE_EXPORT', 'delivered_artifact': asdict(artifact or file_identity(output, 'export')),
            'delivered_references': [], 'observation_scope': 'LOCAL_FILES_VERIFIED_HUMAN_RECEIPT_NOT_OBSERVED'})
        return file_identity(record, 'handoff')

    def test_local_export_closes_without_receipt_or_user_approval(self):
        terminal = self.session.boundary.record_local_handoff(self.package, self.record())
        self.assertEqual(json.loads(Path(terminal.path).read_text())['status'], 'CLOSED')
        self.assertTrue(self.session.boundary.outcome.delivered)
        with self.assertRaisesRegex(ValueError, 'TERMINAL'):
            self.session.boundary.record_local_handoff(self.package, file_identity(self.root / 'handoff.json', 'handoff'))

    def test_changed_deliverable_cannot_close(self):
        wrong = self.root / 'wrong.bin'
        wrong.write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError, 'MISMATCH'):
            self.session.boundary.record_local_handoff(self.package, self.record(artifact=file_identity(wrong, 'wrong')))
        self.assertFalse(self.session.boundary.outcome.terminal)


if __name__ == '__main__':
    unittest.main()
