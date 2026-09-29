"""C3 gates a revision on the actual Review and preserves both Worker outputs."""

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/core"))
sys.path.insert(0, str(ROOT / "src/scenario_a"))
import c3_revision  # noqa: E402


RUN = "m3-c3-20260930-042431-1dfe5d99"


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class C3RevisionTests(unittest.TestCase):
    def test_challenge_configuration_has_fresh_identity(self):
        provenance = read(f"runs/{RUN}_challenge.json")
        initial = read(f"plans/{RUN}-initial-right.json")
        self.assertEqual(initial["patches"]["8"]["prompt"], provenance["reused_prompt"])
        self.assertEqual(initial["patches"]["11"]["seed"], provenance["reused_seed"])
        self.assertEqual(initial["task_id"], RUN + "-initial-right")
        self.assertEqual(initial["patches"]["13"]["filename_prefix"], "codex_to_comfy/" + RUN)

    def test_only_supported_revise_can_request_worker(self):
        result = read(f"reviewer_results/{RUN}-review.json")
        c3_revision.supported_revision(result)
        for verdict in ("PASS", "HUMAN_REQUIRED"):
            changed = copy.deepcopy(result)
            changed["verdict"] = verdict
            with self.assertRaisesRegex(ValueError, "not REVISE"):
                c3_revision.supported_revision(changed)
        for action in ({"code": "NONE", "target": None},
                       {"code": "REGENERATE_VIEW", "target": "left"}):
            changed = copy.deepcopy(result)
            changed["suggested_action"] = action
            with self.assertRaisesRegex(ValueError, "unsupported revision"):
                c3_revision.supported_revision(changed)

    def test_review_hash_change_and_duplicate_block_worker(self):
        order_path = ROOT / f"work_orders/{RUN}-revision-right.json"
        order = read(f"work_orders/{RUN}-revision-right.json")
        changed = copy.deepcopy(order)
        changed["source_review"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash differs"):
            c3_revision.reviewer.checked_invocation(changed["source_review"])
        with mock.patch.object(c3_revision.worker, "run") as worker_run:
            with self.assertRaisesRegex(ValueError, "already consumed"):
                c3_revision.run(order_path)
            worker_run.assert_not_called()

    def test_artifact_b_is_distinct_and_hashed(self):
        initial = read(f"runs/{RUN}_initial_execution.json")
        revision = read(f"runs/{RUN}_revision_execution.json")
        artifact_a = Path(initial["artifact"]["path"])
        artifact_b = Path(revision["artifact"]["path"])
        self.assertNotEqual(artifact_a, artifact_b)
        self.assertNotEqual(initial["prompt_id"], revision["prompt_id"])
        self.assertEqual(artifact_b.stat().st_size, revision["artifact"]["bytes"])
        self.assertEqual(hashlib.sha256(artifact_b.read_bytes()).hexdigest(),
                         revision["artifact"]["sha256"])


if __name__ == "__main__":
    unittest.main()
