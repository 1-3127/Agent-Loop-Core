import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src/scenario_a"))
import codex_to_comfy as execution  # noqa: E402


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.comfy = self.root / "Comfy-UI"
        workflow = self.comfy / "workflows" / "02_Image_to_Multiview" / "sample_api.json"
        workflow.parent.mkdir(parents=True)
        workflow.write_text(json.dumps({
            "1": {"class_type": "LoadImage", "inputs": {"image": "input.png"}},
            "3": {"class_type": "SaveImage", "inputs": {"images": ["1", 0], "filename_prefix": "sample/out"}},
        }), encoding="utf-8")
        source = self.comfy / "work" / "input" / "input.png"
        source.parent.mkdir(parents=True)
        source.write_bytes(b"input")
        self.plan = {
            "schema_version": "0.1", "task_id": "test-run",
            "workflow": "workflows/02_Image_to_Multiview/sample_api.json",
            "patches": {"3": {"filename_prefix": "test/out"}}, "output_node": "3",
        }
        self.plan_path = self.root / "plan.json"
        self.report_path = self.root / "report.json"

    def save_plan(self):
        self.plan_path.write_text(json.dumps(self.plan), encoding="utf-8")

    def test_malformed_plan_rejected_before_submission(self):
        self.plan["patches"]["3"]["filename_prefix"] = "../outside"
        self.save_plan()
        with mock.patch.object(execution, "request_json") as request:
            with self.assertRaises(ValueError):
                execution.run(self.plan_path, self.report_path, self.comfy, 1)
            request.assert_not_called()
        self.assertFalse(self.report_path.exists())

    def test_lost_submission_response_is_durable_and_not_retried(self):
        self.save_plan()
        with mock.patch.object(execution, "request_json", side_effect=[{"devices": []}, TimeoutError("lost")]) as request:
            self.assertEqual(execution.run(self.plan_path, self.report_path, self.comfy, 1), 2)
            self.assertEqual(request.call_count, 2)
        report = json.loads(self.report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "UNRESOLVED")
        self.assertIsNone(report["prompt_id"])
        self.assertTrue(report["client_id"])
        with mock.patch.object(execution, "request_json") as request:
            with self.assertRaises(ValueError):
                execution.run(self.plan_path, self.report_path, self.comfy, 1)
            request.assert_not_called()

    def test_history_deadline_preserves_prompt_id(self):
        self.save_plan()
        with mock.patch.object(execution, "request_json", side_effect=[{"devices": []}, {"prompt_id": "prompt-123"}]) as request:
            self.assertEqual(execution.run(self.plan_path, self.report_path, self.comfy, 0), 2)
            self.assertEqual(request.call_count, 2)
        report = json.loads(self.report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "UNRESOLVED")
        self.assertEqual(report["prompt_id"], "prompt-123")

    def test_glb_plan_and_artifact_validation(self):
        import hashlib
        import struct
        workflow = self.comfy / "workflows" / "03_Multiview_to_3D" / "mesh_api.json"
        workflow.parent.mkdir(parents=True)
        workflow.write_text(json.dumps({
            "1": {"class_type": "LoadImage", "inputs": {"image": "input.png"}},
            "15": {"class_type": "VAEDecodeHunyuan3D", "inputs": {"octree_resolution": 128}},
            "17": {"class_type": "SaveGLB", "inputs": {"mesh": ["1", 0], "filename_prefix": "mesh/base"}},
        }), encoding="utf-8")
        self.plan.update(workflow="workflows/03_Multiview_to_3D/mesh_api.json",
                         patches={"15": {"octree_resolution": 192}, "17": {"filename_prefix": "mesh/m5a_test"}}, output_node="17")
        graph = execution.validate_plan(self.plan, self.comfy)
        self.assertEqual(graph["17"]["inputs"]["filename_prefix"], "mesh/m5a_test")
        self.assertEqual(graph["15"]["inputs"]["octree_resolution"], 192)
        self.plan["patches"]["15"]["octree_resolution"] = 513
        with self.assertRaisesRegex(ValueError, "octree_resolution out of range"):
            execution.validate_plan(self.plan, self.comfy)
        output = self.comfy / "work" / "output" / "mesh" / "m5a_test_00001_.glb"
        output.parent.mkdir(parents=True)
        data = struct.pack("<4sII", b"glTF", 2, 20) + struct.pack("<I4s", 0, b"JSON")
        output.write_bytes(data)
        history = {"outputs": {"17": {"3d": [{"filename": output.name, "subfolder": "mesh", "type": "output"}]}}}
        result = execution.verify_glb(history, "17", self.comfy, "mesh/m5a_test")
        self.assertEqual(result[0]["sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(result[0]["declared_length"], len(data))
        output.write_bytes(data[:-1])
        with self.assertRaisesRegex(ValueError, "GLB is too small"):
            execution.verify_glb(history, "17", self.comfy, "mesh/m5a_test")


if __name__ == "__main__":
    unittest.main()
