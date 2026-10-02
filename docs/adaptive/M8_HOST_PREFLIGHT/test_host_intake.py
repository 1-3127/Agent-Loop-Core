"""Host-only pre-loop eligibility checks; no actual inference/tool execution."""
from pathlib import Path
import unittest
import actual_host as host

class AdaptiveIntakeEligibilityTests(unittest.TestCase):
    def test_initial_optimistic_envelope_cannot_enter_adaptive_loop(self):
        self.assertFalse(host.adaptive_intake_eligible({'production_runs': 1, 'attempts': 1,
            'worker_calls': 2, 'reviewer_calls': 2, 'frontier_calls': 3, 'diagnostic_calls': 2}))

    def test_adequate_inferred_envelope_is_admitted(self):
        self.assertTrue(host.adaptive_intake_eligible({'production_runs': 3, 'attempts': 8,
            'worker_calls': 8, 'reviewer_calls': 12, 'frontier_calls': 24, 'diagnostic_calls': 12}))

    def test_boolean_or_missing_resource_is_not_a_budget(self):
        limits = {'production_runs': 2, 'attempts': 2, 'worker_calls': 2,
            'reviewer_calls': 2, 'frontier_calls': 6, 'diagnostic_calls': 2}
        self.assertFalse(host.adaptive_intake_eligible(limits | {'production_runs': True}))
        self.assertFalse(host.adaptive_intake_eligible({k:v for k,v in limits.items() if k != 'diagnostic_calls'}))

    def test_bound_v1_intake_has_no_started_production_session(self):
        path = host.ROOT / 'docs/adaptive/actual-stone-lantern-v1'
        self.assertTrue((path / 'frozen.json').exists())
        self.assertFalse((path / 'session').exists())

if __name__ == '__main__':
    unittest.main(verbosity=2)
