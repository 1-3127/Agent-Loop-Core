"""C4 policy terminates each semantic branch within its declared budget."""

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/core"))
sys.path.insert(0, str(ROOT / "src/scenario_a"))
import c4_bounded  # noqa: E402


RUN = "m4-c4-20260930-044212-c0aef33d"


class C4BoundedTests(unittest.TestCase):
    def test_semantic_terminal_branches(self):
        pass_review = {"verdict": "PASS", "blocking_issues": [],
                       "suggested_action": {"code": "NONE", "target": None}}
        self.assertEqual(c4_bounded.terminal_policy(pass_review, 0),
                         ("DELIVERED", "INTERNAL_ACCEPT", True))
        revise = copy.deepcopy(pass_review)
        revise.update(verdict="REVISE", blocking_issues=["Visible blocking defect"],
                      suggested_action={"code": "REGENERATE_VIEW", "target": "right"})
        human = copy.deepcopy(pass_review)
        human.update(verdict="HUMAN_REQUIRED",
                     suggested_action={"code": "HUMAN_REQUIRED", "target": None})
        with mock.patch.object(c4_bounded.delegate, "run") as worker_run:
            self.assertEqual(c4_bounded.terminal_policy(revise, 0),
                             ("ABORT", "BUDGET_EXHAUSTED_AFTER_REVISE", False))
            with self.assertRaisesRegex(ValueError, "budget"):
                c4_bounded.terminal_policy(revise, 1)
            self.assertEqual(c4_bounded.terminal_policy(human, 0),
                             ("ABORT", "HUMAN_REQUIRED", False))
            worker_run.assert_not_called()

    def test_initial_contract_precedes_worker(self):
        order = json.loads((ROOT / f"work_orders/{RUN}.json").read_text(encoding="utf-8"))
        contract = c4_bounded.initial_contract(order)
        self.assertEqual(contract["worker_budget"], {"limit": 1, "consumed": 0, "remaining": 1})
        self.assertEqual(contract["reviewer_budget"], {"limit": 1, "consumed": 0, "remaining": 1})
        self.assertFalse(contract["terminal"])

    def test_terminal_reentry_has_no_effect(self):
        request = ROOT / f"reviewer_requests/{RUN}-review.json"
        result = ROOT / f"reviewer_results/{RUN}-review.json"
        report = ROOT / f"invocation_reports/{RUN}-review.json"
        terminal = ROOT / f"runs/{RUN}_terminal.json"
        before = c4_bounded.delegate.digest(terminal)
        with mock.patch.object(c4_bounded.delegate, "run") as worker_run, mock.patch.object(
                c4_bounded.reviewer, "review_once") as reviewer_run:
            self.assertEqual(c4_bounded.resolve_terminal(request, result, report)[0],
                             "ALREADY_TERMINAL")
            with self.assertRaises(ValueError):
                c4_bounded.run_worker(ROOT / f"work_orders/{RUN}.json")
            with self.assertRaisesRegex(ValueError, "ALREADY_TERMINAL"):
                c4_bounded.run_review(request, result, report)
            worker_run.assert_not_called()
            reviewer_run.assert_not_called()
        self.assertEqual(c4_bounded.delegate.digest(terminal), before)


if __name__ == "__main__":
    unittest.main()
