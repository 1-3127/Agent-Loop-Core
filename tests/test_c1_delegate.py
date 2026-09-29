"""C1 preflight rejects stale input and duplicate output before Worker invocation."""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from scenario_a import c1_delegate  # noqa: E402


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def ref(path, relative):
    return {"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


class DelegatePreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root, self.comfy = base / "repo", base / "Comfy-UI"
        self.source = self.comfy / "work/input/source.png"
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes(b"source")
        self.workflow = self.comfy / "workflows/02_Image_to_Multiview/view_api.json"
        write_json(self.workflow, {
            "1": {"class_type": "LoadImage", "inputs": {"image": "source.png"}},
            "4": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "model.gguf"}},
            "13": {"class_type": "SaveImage", "inputs": {"images": ["1", 0],
                                                         "filename_prefix": "base/out"}},
        })
        self.plan = self.root / "plans/run-initial-right.json"
        write_json(self.plan, {"schema_version": "0.1", "task_id": "run-initial-right",
                               "workflow": "workflows/02_Image_to_Multiview/view_api.json",
                               "patches": {"1": {"image": "source.png"},
                                           "13": {"filename_prefix": "codex_to_comfy/run"}},
                               "output_node": "13"})
        self.order_path = self.root / "work_orders/run.json"
        self.order = {
            "version": "c1.0", "run_id": "run", "work_order_id": "run-initial-right",
            "worker_type": "ComfyUI", "adapter": "src/scenario_a/c1_delegate.py",
            "requested_task": "Generate one right view from the source image", "iteration": 0,
            "source": ref(self.source, "source.png"),
            "workflow": ref(self.workflow, "workflows/02_Image_to_Multiview/view_api.json"),
            "plan": ref(self.plan, "plans/run-initial-right.json"),
            "expected_output_kind": "image", "worker_report_path": "runs/worker.json",
            "execution_report_path": "runs/c1.json", "usage_path": "usage/run.json",
            "worker_model": "model.gguf",
        }
        write_json(self.order_path, self.order)
        self.root_patch = mock.patch.object(c1_delegate, "ROOT", self.root)
        self.comfy_patch = mock.patch.object(c1_delegate, "COMFY", self.comfy)
        self.root_patch.start()
        self.comfy_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.comfy_patch.stop)

    def test_valid_work_order_and_stale_input(self):
        self.assertEqual(c1_delegate.preflight(self.order_path)[0], self.order)
        self.source.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "file reference identity differs"):
            c1_delegate.preflight(self.order_path)

    def test_output_collision_blocks_execution(self):
        output = self.comfy / "work/output/codex_to_comfy/run_00001_.png"
        output.parent.mkdir(parents=True)
        output.write_bytes(b"old")
        with mock.patch.object(c1_delegate.worker, "run") as worker_run:
            with self.assertRaisesRegex(ValueError, "namespace already consumed"):
                c1_delegate.run(self.order_path)
            worker_run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
