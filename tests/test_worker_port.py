"""The Core boundary accepts either Worker without changing its entry point."""

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/core"))
import worker_port


class WorkerPortTests(unittest.TestCase):
    def test_two_adapters_share_entry_and_validate_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            entry = worker_port.execute
            for adapter_id in ("first", "second"):
                path = Path(directory) / (adapter_id + ".txt")
                data = adapter_id.encode()

                class Adapter:
                    def __init__(self, identity):
                        self.adapter_id = identity

                    def __call__(self, order):
                        path.write_bytes(data)
                        return {"version": "c5.0", "run_id": order["run_id"],
                                "work_order_id": order["work_order_id"], "adapter_id": self.adapter_id,
                                "backend": self.adapter_id, "status": "SUCCESS",
                                "invocation_id": self.adapter_id + "-call",
                                "artifact": {"path": str(path), "kind": "text", "bytes": len(data),
                                             "sha256": hashlib.sha256(data).hexdigest()},
                                "execution_seconds": 0.01}

                order = {"version": "c5.0", "run_id": "test-run", "work_order_id": "test-order",
                         "requested_task": "create artifact", "expected_output_kind": "text",
                         "adapter_id": adapter_id, "payload": {"test": True}}
                self.assertIs(entry, worker_port.execute)
                result = entry(Adapter(adapter_id), order)
                self.assertEqual(result["artifact"]["sha256"], hashlib.sha256(data).hexdigest())
                self.assertEqual(result["adapter_id"], adapter_id)

    def test_rejects_wrong_identity_and_invalid_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.txt"
            path.write_text("data", encoding="utf-8")

            class BadAdapter:
                adapter_id = "bad"

                def __init__(self, fault):
                    self.fault = fault

                def __call__(self, order):
                    result = {"version": "c5.0", "run_id": order["run_id"],
                              "work_order_id": order["work_order_id"], "adapter_id": self.adapter_id,
                              "backend": "local", "status": "SUCCESS", "invocation_id": "call",
                              "artifact": {"path": str(path), "kind": "text", "bytes": 4,
                                           "sha256": hashlib.sha256(path.read_bytes()).hexdigest()},
                              "execution_seconds": 0.01}
                    if self.fault == "identity":
                        result["work_order_id"] = "other"
                    elif self.fault == "hash":
                        result["artifact"]["sha256"] = "0" * 64
                    elif self.fault == "missing":
                        result["artifact"]["path"] = str(path.parent / "missing.txt")
                    return result

            order = {"version": "c5.0", "run_id": "test-run", "work_order_id": "test-order",
                     "requested_task": "create artifact", "expected_output_kind": "text",
                     "adapter_id": "bad", "payload": {"test": True}}
            for fault in ("identity", "hash", "missing"):
                with self.subTest(fault=fault), self.assertRaises(ValueError):
                    worker_port.execute(BadAdapter(fault), order)


if __name__ == "__main__":
    unittest.main()
