import json
from pathlib import Path
import tempfile
import unittest

from core.event_logging import EventLogger, reconstruct


class EventLoggingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.logger = EventLogger(self.root, 'session')

    def test_global_order_module_ownership_and_parent_reconstruct(self):
        first = self.logger.emit('workflow', 'WORKFLOW_CREATED', decision='PLAN_WORKFLOW')
        self.logger.emit('production_runs/run-001/controller', 'RUN_STARTED', parent_event_id=first.identity)
        events = reconstruct(self.root, 'session')
        self.assertEqual([e['event_seq'] for e in events], [1, 2])
        index = json.loads(self.logger.index.read_text().splitlines()[0])
        self.assertNotIn('decision', index)
        self.assertEqual(events[1]['parent_event_id'], events[0]['event_id'])
        with self.assertRaisesRegex(ValueError, 'NO_RESUME'):
            EventLogger(self.root, 'session')

    def test_tamper_or_orphan_blocks_reconstruction(self):
        first = self.logger.emit('session', 'BOUND')
        Path(first.path).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'HASH'):
            reconstruct(self.root, 'session')

    def test_invalid_parent_path_and_reasoning_field_reject_before_append(self):
        with self.assertRaisesRegex(ValueError, 'PARENT'):
            self.logger.emit('session', 'INVALID', parent_event_id='future-event')
        with self.assertRaisesRegex(ValueError, 'MODULE'):
            self.logger.emit('../escape', 'INVALID')
        with self.assertRaisesRegex(ValueError, 'UNSUPPORTED'):
            self.logger.emit('frontier', 'INVALID', identities={'chain_of_thought': 'private'})
        self.assertEqual(self.logger.index.read_bytes(), b'')

    def test_duplicate_index_or_missing_canonical_event_is_detected(self):
        self.logger.emit('session', 'BOUND')
        original = self.logger.index.read_bytes()
        self.logger.index.write_bytes(original + original)
        with self.assertRaisesRegex(ValueError, 'SEQUENCE'):
            reconstruct(self.root, 'session')
        self.logger.index.write_bytes(original)
        orphan = self.root / 'worker/events/event-999999.json'
        orphan.parent.mkdir(parents=True)
        orphan.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'INCOMPLETE'):
            reconstruct(self.root, 'session')


if __name__ == '__main__':
    unittest.main()
