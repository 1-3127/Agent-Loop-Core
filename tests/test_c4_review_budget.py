"""F01: C4 dispatch consumes one durable run budget, regardless of output paths."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from scenario_a import c4_bounded as c4

REQUEST = PROJECT / "reviewer_requests/m4-c4-20260930-044212-c0aef33d-review.json"
RESULT = PROJECT / "reviewer_results/m4-c4-20260930-044212-c0aef33d-review.json"


class ReviewBudgetTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.request = json.loads(REQUEST.read_text(encoding="utf-8"))
        # Copy metadata only; existing production PNGs are read-only references.
        refs = [self.request[key] for key in
                ("source_result", "work_order", "worker_report", "bounded_contract",
                 "worker_state", "instruction_file")]
        order = json.loads((PROJECT / self.request["work_order"]["path"]).read_text(encoding="utf-8"))
        refs.append(order["plan"])
        for reference in refs:
            target = self.root / reference["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT / reference["path"], target)
        self.request_path = self.root / "reviewer_requests" / REQUEST.name
        shutil.copyfile(REQUEST, self.request_path)
        self.result_path = self.root / "reviewer_results/result-a.json"
        self.report_path = self.root / "invocation_reports/report-a.json"
        for patch in (mock.patch.object(c4, "ROOT", self.root),
                      mock.patch.object(c4.reviewer, "ROOT", self.root),
                      mock.patch.object(c4.reviewer, "auth_mode", return_value="CHATGPT_ACCOUNT")):
            patch.start()
            self.addCleanup(patch.stop)

    def success(self):
        return subprocess.CompletedProcess([], 0, RESULT.read_bytes(), b"")

    def assert_retry_blocked(self, dispatch):
        reservation = c4.review_reservation_path(self.request["run_id"])
        before = reservation.read_bytes()
        with self.assertRaisesRegex(ValueError, "REVIEW_BUDGET_ALREADY_RESERVED"):
            c4.run_review(self.request_path, self.root / "result-b.json", self.root / "report-b.json")
        self.assertEqual(dispatch.call_count, 1)
        self.assertEqual(reservation.read_bytes(), before)
        self.assertFalse((self.root / "result-b.json").exists())
        self.assertFalse((self.root / "report-b.json").exists())

    def test_different_output_paths_dispatch_only_once(self):
        with mock.patch.object(c4.reviewer.subprocess, "run", return_value=self.success()) as dispatch:
            report = c4.run_review(self.request_path, self.result_path, self.report_path)
            self.assertEqual(report["invocation_status"], "SUCCESS")
            self.assert_retry_blocked(dispatch)

    def test_failed_process_does_not_restore_budget(self):
        failure = subprocess.CompletedProcess([], 1, b"", b"failed")
        with mock.patch.object(c4.reviewer.subprocess, "run", return_value=failure) as dispatch:
            report = c4.run_review(self.request_path, self.result_path, self.report_path)
            self.assertEqual(report["invocation_status"], "FAILED")
            self.assert_retry_blocked(dispatch)

    def test_uncertain_process_does_not_restore_budget(self):
        with mock.patch.object(c4.reviewer.subprocess, "run",
                               side_effect=subprocess.TimeoutExpired("mock reviewer", 600)) as dispatch:
            report = c4.run_review(self.request_path, self.result_path, self.report_path)
            self.assertEqual(report["invocation_status"], "UNRESOLVED")
            self.assert_retry_blocked(dispatch)

    def test_launch_failure_does_not_restore_budget(self):
        with mock.patch.object(c4.reviewer.subprocess, "run",
                               side_effect=OSError("mock launch failure")) as dispatch:
            report = c4.run_review(self.request_path, self.result_path, self.report_path)
            self.assertEqual(report["invocation_status"], "FAILED")
            self.assertFalse(report["reviewer_process_started"])
            self.assert_retry_blocked(dispatch)

    def test_malformed_result_does_not_restore_budget(self):
        invalid = subprocess.CompletedProcess([], 0, b"not JSON", b"")
        with mock.patch.object(c4.reviewer.subprocess, "run", return_value=invalid) as dispatch:
            report = c4.run_review(self.request_path, self.result_path, self.report_path)
            self.assertEqual(report["invocation_status"], "FAILED")
            self.assert_retry_blocked(dispatch)

    def test_reservation_collision_precedes_dispatch(self):
        _, _, state = c4.validate_review_request(self.request)
        with mock.patch.object(c4.reviewer, "review_once") as dispatch:
            reservation = c4.reserve_review(self.request_path, self.result_path,
                                            self.report_path, self.request, state)
            self.assertTrue(reservation["reserved"])
            self.assertEqual(reservation["reviewer_budget"], {"limit": 1, "consumed": 1, "remaining": 0})
            with self.assertRaisesRegex(ValueError, "REVIEW_BUDGET_ALREADY_RESERVED"):
                c4.reserve_review(self.request_path, self.result_path,
                                  self.report_path, self.request, state)
            dispatch.assert_not_called()

    def test_pass_fixture_reservation_connects_to_terminal(self):
        def after_reservation(*args, **kwargs):
            path = c4.review_reservation_path(self.request["run_id"])
            self.assertTrue(path.is_file(), "reservation must precede dispatch")
            return self.success()
        with mock.patch.object(c4.reviewer.subprocess, "run", side_effect=after_reservation) as dispatch:
            c4.run_review(self.request_path, self.result_path, self.report_path)
            status, terminal = c4.resolve_terminal(self.request_path, self.result_path, self.report_path)
            self.assertEqual(status, "DELIVERED")
            self.assertTrue(terminal["internal_accept"])
            self.assertEqual(terminal["review_reservation"],
                             c4.repo_ref(c4.review_reservation_path(self.request["run_id"])))
            self.assertEqual(terminal["reviewer_budget"], {"limit": 1, "consumed": 1, "remaining": 0})
            self.assertEqual(c4.resolve_terminal(self.request_path, self.result_path,
                                                 self.report_path)[0], "ALREADY_TERMINAL")
            dispatch.assert_called_once()

    def test_resolver_rejects_reservation_output_mismatch(self):
        with mock.patch.object(c4.reviewer.subprocess, "run", return_value=self.success()):
            c4.run_review(self.request_path, self.result_path, self.report_path)
        path = c4.review_reservation_path(self.request["run_id"])
        value = json.loads(path.read_text(encoding="utf-8"))
        value["result_path"] = str(self.root / "other.json")
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "reservation lineage"):
            c4.resolve_terminal(self.request_path, self.result_path, self.report_path)

    def test_changed_review_identity_does_not_restore_run_budget(self):
        with mock.patch.object(c4.reviewer.subprocess, "run", return_value=self.success()) as dispatch:
            c4.run_review(self.request_path, self.result_path, self.report_path)
            self.request["review_id"] += "-other"
            changed = self.root / "reviewer_requests/other.json"
            changed.write_text(json.dumps(self.request), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "REVIEW_BUDGET_ALREADY_RESERVED"):
                c4.run_review(changed, self.root / "result-b.json", self.root / "report-b.json")
            dispatch.assert_called_once()


if __name__ == "__main__":
    unittest.main()
