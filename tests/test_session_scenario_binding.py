"""S3B local integration. All production adapters use existing synthetic fixtures."""
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from session import session_boundary as sb
from scenario_a import session_binding as bound
from scenario_a import l6_pipeline as l6
from scenario_a import l7_geometry_review as bridge
from scenario_a import l7_feedback_controller as controller
import tests.test_l6_pipeline as l6_tests
import tests.test_l7_geometry_review as bridge_tests


class SessionScenarioTests(unittest.TestCase):
    def setUp(self):
        self.f = l6_tests.L6PipelineTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.doc = self.f.root / "work_specification.md"
        self.doc.write_text("Goal: create four-view GLB.\nMust-Have: preserve the object.\n", encoding="utf-8")
        fields = sb.FinalizedFields("session-test", "v1", "NEW_WORK", True, (),
            (sb.AcceptanceCriterion("AC1", "USER", True, "preserve the object"),
             sb.AcceptanceCriterion("AC2", "USER", False, "prefer smooth appearance")),
            (sb.AuthorityReference("USER", "current request"),), ("fixed Scenario A",))
        self.spec = sb.freeze_specification(self.doc, fields)
        self.session = sb.SessionBoundary("session-test", self.f.root / "session")
        self.binding = self.session.create_binding(self.spec, "logical-loop")
        self.ids = {"l6": self.f.run_id, "bridge": "bound-bridge", "correction": "bound-correction"}
        self.parent = self.prepare()
        self.path = self.f.run_dir

    def prepare(self, boundary=None, binding=None, **overrides):
        options = dict(goal={"text": "create four-view GLB.", "authority_ref": "USER"},
            must_haves=({"text": "preserve the object.", "authority_ref": "USER"},),
            stage_criteria={"multiview": ("AC1",), "geometry": ("AC1", "AC2")},
            child_ids=self.ids)
        options.update(overrides)
        return bound.prepare(boundary or self.session, binding or self.binding, **options)

    def execute_l6(self):
        return l6.run_pipeline(self.f.run_id, self.f.comfy, 1, 1,
                               execute=True, session_binding=self.parent)

    def test_l6_binding_full_local_lineage(self):
        self.assertEqual(self.execute_l6()["state"], "GEOMETRY_READY")
        child = bound.checked_child(self.path, parent_ref=self.parent)
        self.assertEqual(child[1]["loop_run_id"], "logical-loop")
        for stage in (*l6.VIEWS, "geometry"):
            for suffix in ("plan", "work_order", "execution"):
                bound.check_record(self.path, self.path / (stage + "_" + suffix + ".json"))
        bound.check_record(self.path, self.path / "multiview_manifest.json")
        self.f.assert_calls(4, 1)

    def test_specification_bytes_mutation_before_effect(self):
        self.doc.write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SPECIFICATION_CONTENT_CHANGED"):
            self.execute_l6()
        self.f.assert_calls(0, 0)

    def test_wrong_session_binding(self):
        other = sb.SessionBoundary("other-session", self.f.root / "other")
        with self.assertRaises(ValueError):
            other.create_binding(self.spec, "other-loop")
        self.f.assert_calls(0, 0)

    def test_wrong_logical_loop_binding(self):
        wrong = sb.SessionRunBinding(self.spec, "wrong-loop")
        with self.assertRaisesRegex(ValueError, "binding mismatch"):
            self.prepare(binding=wrong)
        self.f.assert_calls(0, 0)

    def test_undeclared_authority(self):
        with self.assertRaisesRegex(ValueError, "authority mismatch"):
            self.prepare(goal={"text": "create four-view GLB.", "authority_ref": "HIDDEN"})
        self.f.assert_calls(0, 0)

    def test_capability_and_child_identity_pre_effect(self):
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED"):
            self.prepare(capability="arbitrary geometry")
        with self.assertRaises(ValueError):
            l6.run_pipeline("wrong-child", self.f.comfy, session_binding=self.parent)
        self.f.assert_calls(0, 0)

    def geometry_fixture(self):
        # Existing fixture Worker produces a GLB with exact current embedded inputs.
        import struct
        def embedded(role, report_path):
            if role != "geometry":
                return
            report = l6.read_json(report_path)
            plan = l6.read_json(report_path.parent / "geometry_plan.json")
            graph = {node: {"inputs": plan["patches"][node],
                           "is_changed": [l6.digest(self.f.comfy / "work/input" / plan["patches"][node]["image"])]}
                     for node in l6.MAPPING.values()}
            payload = json.dumps({"asset": {"version": "2.0", "extras": {"prompt": json.dumps(graph)}}}).encode()
            payload += b" " * (-len(payload) % 4)
            data = struct.pack("<4sII", b"glTF", 2, 20 + len(payload)) + struct.pack("<I4s", len(payload), b"JSON") + payload
            path = Path(report["outputs"][0]["path"])
            path.write_bytes(data)
            report["outputs"][0].update(bytes=len(data), sha256=l6.digest(path), declared_length=len(data))
            l6.worker.write_report(report_path, report)
        self.f.worker_after = embedded
        self.assertEqual(self.execute_l6()["state"], "GEOMETRY_READY")
        self.g = bridge_tests.GeometryBridgeTests()
        self.g.fixture = self.f
        self.g.run_id = self.ids["bridge"]
        self.g.executable = self.f.root / "blender.exe"
        self.g.executable.write_bytes(b"SYNTHETIC_EXECUTABLE_NEVER_RUN")
        self.g.render_mutation = None
        self.g.review_mutation = None
        self.g.verdict = "PASS"
        self.g.action = None
        self.g.return_code = 0
        for module in (bridge, controller):
            p = mock.patch.object(module, "ROOT", self.f.repo)
            p.start()
            self.addCleanup(p.stop)
        def render(command, **kwargs):
            result = self.g.fake_render(command, **kwargs)
            request = l6.read_json(Path(command[-1]))
            path = Path(request["manifest_path"])
            manifest = l6.read_json(path)
            manifest["source_l6_run_id"] = request["source_l6_run_id"]
            l6.worker.write_report(path, manifest)
            return result
        self.renderer = mock.patch.object(bridge.subprocess, "run", side_effect=render).start()
        self.reviewer = mock.patch.object(l6.reviewer, "review_once", side_effect=self.g.fake_review).start()
        self.addCleanup(mock.patch.stopall)

    def execute_bridge(self, parent=None):
        return bridge.run_bridge(self.ids["bridge"], self.g.executable, 1, 1, execute=True,
            session_binding=parent or self.parent, source_l6_run=self.path)

    def test_bridge_current_bound_l6_without_global_pin_mutation(self):
        self.geometry_fixture()
        old = (bridge.L6_DIR, bridge.L6_RUN_ID, bridge.GLB_SHA)
        self.assertEqual(self.execute_bridge()["state"], "GEOMETRY_REVIEWED")
        path = self.f.repo / "runs/l7" / self.ids["bridge"]
        self.assertEqual(controller.validate_source(path, self.parent)["input"]["source_run_id"], self.ids["l6"])
        self.assertEqual(old, (bridge.L6_DIR, bridge.L6_RUN_ID, bridge.GLB_SHA))
        self.assertEqual((self.renderer.call_count, self.reviewer.call_count), (1, 1))

    def test_unbound_l6_rejected(self):
        self.f.run_fixture()
        with self.assertRaisesRegex(ValueError, "UNBOUND"):
            bridge.validate_l6(self.path, self.parent)
        self.f.network.assert_not_called()

    def test_different_spec_l6_and_l7_rejected(self):
        self.geometry_fixture()
        alternate = self.f.root / "session-copy"
        alternate.mkdir()
        other = sb.SessionBoundary("session-test", alternate)
        other_binding = other.create_binding(self.spec, "other-loop")
        parent = self.prepare(boundary=other, binding=other_binding)
        with self.assertRaises(ValueError):
            self.execute_bridge(parent)
        self.renderer.assert_not_called()
        self.assertEqual(self.execute_bridge()["state"], "GEOMETRY_REVIEWED")
        path = self.f.repo / "runs/l7" / self.ids["bridge"]
        with self.assertRaises(ValueError):
            controller.run_feedback(self.ids["correction"], path, self.f.comfy, self.g.executable,
                                    execute=True, session_binding=parent)
