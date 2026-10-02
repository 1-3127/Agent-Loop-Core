import json
from pathlib import Path
import unittest

from scenario_a.adaptive_adapter import ExecutionAdapter
from tests import test_adaptive_loop as fixture


class AdaptiveAdapterTests(unittest.TestCase):
    def setUp(self):
        fixture.AdaptiveLoopTests.setUp(self)
        fixture.AdaptiveLoopTests.begin(self)
        self.calls = 0

    def decide(self, *args, **kwargs):
        return fixture.AdaptiveLoopTests.decide(self, *args, **kwargs)

    def runner(self, order):
        self.calls += 1
        output = Path(order['output_directory']) / 'fixture.bin'
        output.write_bytes(b'SYNTHETIC fixture output')
        return {'status': 'SUCCESS', 'outputs': [str(output)], 'observations': {'synthetic': True}}

    def execute(self, adapter, reservation, path='execution', **kwargs):
        return adapter.execute(self.frozen, self.scope, self.workflow, self.session.state(), 'build', (),
            reservation, self.root / path, **kwargs)

    def test_reserved_effect_one_dispatch_and_exact_output_report(self):
        reservation = self.session.reserve_effect('worker_calls')
        adapter = ExecutionAdapter({'fixture': self.runner}, mode='SYNTHETIC')
        outputs, report = self.execute(adapter, reservation)
        self.assertEqual(json.loads(Path(report.path).read_text())['status'], 'SUCCESS')
        self.assertEqual(len(outputs), 1)
        with self.assertRaisesRegex(ValueError, 'COLLISION'):
            self.execute(adapter, reservation, 'another-path')
        self.assertEqual(self.calls, 1)

    def test_unavailable_tool_or_strategy_parameters_no_dispatch(self):
        reservation = self.session.reserve_effect('worker_calls')
        with self.assertRaisesRegex(ValueError, 'CAPABILITY'):
            self.execute(ExecutionAdapter({}), reservation)
        with self.assertRaisesRegex(ValueError, 'REVISION'):
            self.execute(ExecutionAdapter({'fixture': self.runner}), reservation, local_parameters={'tool': 'different'})
        self.assertEqual(self.calls, 0)
        self.assertFalse((self.root / 'execution').exists())

    def test_exception_preserves_unresolved_report_without_retry(self):
        def fail(order):
            self.calls += 1
            raise OSError('synthetic effect uncertainty')
        reservation = self.session.reserve_effect('worker_calls')
        outputs, report = self.execute(ExecutionAdapter({'fixture': fail}, mode='SYNTHETIC'), reservation)
        self.assertEqual(outputs, ())
        self.assertEqual(json.loads(Path(report.path).read_text())['status'], 'UNRESOLVED')
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.session.resources.remaining()['used']['worker_calls'], 1)


if __name__ == '__main__':
    unittest.main()
