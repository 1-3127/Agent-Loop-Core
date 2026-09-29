"""C2 guards the committed C1 evidence before the only Reviewer call."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/core"))
sys.path.insert(0, str(ROOT / "src/scenario_a"))
import c2_review  # noqa: E402
import result_review_adapter as reviewer  # noqa: E402

REQUEST = ROOT / "reviewer_requests/m2-c2-20260930-041139-003f61d0.json"


class C2ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))

    def test_c1_lineage_and_changed_artifact_rejected(self):
        self.assertEqual(c2_review.validate_c1_lineage(self.request)[0]["run_id"],
                         self.request["run_id"])
        changed = copy.deepcopy(self.request)
        changed["artifacts"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash differs"):
            c2_review.validate_c1_lineage(changed)

    def test_changed_c1_execution_report_rejected(self):
        changed = copy.deepcopy(self.request)
        changed["source_result"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash differs"):
            c2_review.validate_c1_lineage(changed)

    def test_existing_result_blocks_reviewer_process(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.json"
            report = Path(directory) / "report.json"
            result.write_text("reserved", encoding="utf-8")
            with mock.patch.object(reviewer.subprocess, "run") as process:
                with self.assertRaisesRegex(ValueError, "refusing repeat"):
                    reviewer.review_once(REQUEST, result, report)
                process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
