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
