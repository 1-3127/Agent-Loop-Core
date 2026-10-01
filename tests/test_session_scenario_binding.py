"""S3B local integration. All production adapters use existing synthetic fixtures."""
import json
from dataclasses import replace
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
        self.f.review_after = self.tag_l6_review
        self.path = self.f.run_dir

    def prepare(self, boundary=None, binding=None, **overrides):
        options = dict(goal={"text": "create four-view GLB.", "authority_ref": "USER"},
            must_haves=({"text": "preserve the object.", "authority_ref": "USER"},),
            stage_criteria={"multiview": ("AC1",), "geometry": ("AC1", "AC2")},
            child_ids=self.ids, legacy_fixture=True)
        options.update(overrides)
        return bound.prepare(boundary or self.session, binding or self.binding, **options)

    def execute_l6(self):
        return l6.run_pipeline(self.f.run_id, self.f.comfy, 1, 1,
                               execute=True, session_binding=self.parent)

    def select_criteria(self, stages, extra=()):
        # New fixture binding, before any adapters run; original records stay intact.
        fields = replace(self.spec.fields, acceptance_criteria=self.spec.fields.acceptance_criteria + extra)
        self.spec = sb.freeze_specification(self.doc, fields)
        self.session = sb.SessionBoundary("session-test", self.f.root / "criterion-session")
        self.binding = self.session.create_binding(self.spec, "logical-loop")
        self.parent = self.prepare(stage_criteria=stages)

    def split_mandatory_criteria(self):
        self.select_criteria({"multiview": ("AC1",), "geometry": ("AC3",)},
            (sb.AcceptanceCriterion("AC3", "USER", True, "preserve geometry identity"),))

    def test_c01_geometry_subset_and_multiview_only_mandatory(self):
        self.split_mandatory_criteria()
        self.geometry_fixture()
        self.assertEqual(self.execute_bridge()["state"], "GEOMETRY_REVIEWED")
        path = self.f.repo / "runs/l7" / self.ids["bridge"]
        self.assertEqual([c["criterion_id"] for c in bound.review_contract(path, "geometry")["criteria"]], ["AC3"])
        instructions = (path / "review_instructions.md").read_text(encoding="utf-8")
        self.assertNotIn('"criterion_id": "AC1"', instructions)
        self.assertNotIn('"criterion_id": "AC2"', instructions)
        bound.internal_accept_candidate(self.parent, path).validate()
        accepted = l6.read_json(self.session.directory / "scenario_a_accept.json")
        self.assertEqual(accepted["mandatory_criterion_ids"], ["AC1", "AC3"])
        self.assertEqual(l6.read_ref(accepted["stage_coverage"]["multiview"])["coverage"], {"AC1": "SATISFIED"})
        self.assertEqual(l6.read_ref(accepted["stage_coverage"]["geometry"])["coverage"], {"AC3": "SATISFIED"})
        self.assertFalse(self.session.outcome.delivered)

    def test_c01_unassigned_nonblocking_does_not_block_final(self):
        self.select_criteria({"multiview": ("AC1",), "geometry": ("AC1",)})
        self.geometry_fixture()
        self.assertEqual(self.execute_bridge()["state"], "GEOMETRY_REVIEWED")
        path = self.f.repo / "runs/l7" / self.ids["bridge"]
        bound.internal_accept_candidate(self.parent, path).validate()
        accepted = l6.read_json(self.session.directory / "scenario_a_accept.json")
        self.assertEqual(accepted["criterion_ids"], ["AC1", "AC2"])
        self.assertEqual(accepted["mandatory_criterion_ids"], ["AC1"])
        for reference in accepted["stage_coverage"].values():
            self.assertEqual(l6.read_ref(reference)["coverage"], {"AC1": "SATISFIED"})

    def test_c01_unsupported_mandatory_preflight_zero_effects(self):
        fields = replace(self.spec.fields, acceptance_criteria=self.spec.fields.acceptance_criteria +
            (sb.AcceptanceCriterion("PERFORMANCE", "USER", True, "runtime performance"),))
        spec = sb.freeze_specification(self.doc, fields)
        boundary = sb.SessionBoundary("session-test", self.f.root / "unsupported-session")
        binding = boundary.create_binding(spec, "logical-loop")
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_ACCEPTANCE_CRITERION: PERFORMANCE"):
            self.prepare(boundary=boundary, binding=binding)
        self.assertFalse((boundary.directory / "scenario_a.json").exists())
        self.f.assert_calls(0, 0)
        self.f.network.assert_not_called()

    def test_c01_reloaded_parent_cannot_bypass_mandatory_preflight(self):
        # Even a caller-supplied parent ref cannot turn omitted mandatory coverage
        # into effect eligibility at the direct L6 or fixed entry.
        self.geometry_fixture(execute=False)
        data = l6.read_ref(self.parent)
        data["stage_criteria"] = {"multiview": ["AC2"], "geometry": ["AC2"]}
        path = self.session.directory / "unsupported_parent.json"
        l6.write_once(path, data)
        parent = l6.reference(path)
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_ACCEPTANCE_CRITERION: AC1"):
            l6.run_pipeline(self.ids["l6"], self.f.comfy, execute=True, session_binding=parent)
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_ACCEPTANCE_CRITERION: AC1"):
            bound.run_session(parent, comfy_root=self.f.comfy, blender_executable=self.g.executable, execute=True)
        self.f.worker_mock.assert_not_called()
        self.renderer.assert_not_called()
        self.reviewer.assert_not_called()
        self.f.network.assert_not_called()
        self.assertFalse(self.path.exists())

    def test_c01_selected_stage_coverage_rejections(self):
        contract = {"criteria": [dict(criterion_id="AC1", authority_ref="USER", blocking_when_unmet=True),
                                  dict(criterion_id="AC2", authority_ref="USER", blocking_when_unmet=False)]}
        good = {"verdict": "PASS", "observations": ["[AC1@USER] SATISFIED: evidence", "[AC2@USER] UNMET: optional"],
                "blocking_issues": []}
        cases = ([], [good["observations"][0]], [good["observations"][0]] * 2,
                 ["[AC1@USER] UNMET: failure", good["observations"][1]],
                 ["[AC1@USER] UNCERTAIN: unknown", good["observations"][1]],
                 ["[AC1@HIDDEN] SATISFIED: wrong authority", good["observations"][1]])
        for observations in cases:
            with self.subTest(observations=observations), self.assertRaises(ValueError):
                bound.validate_coverage(contract, good | {"observations": observations})
        self.assertEqual(bound.validate_coverage(contract, good), {"AC1": "SATISFIED", "AC2": "UNMET"})

    def test_c01_final_rejects_invalid_current_stage_evidence(self):
        self.split_mandatory_criteria()
        self.geometry_fixture()
        self.assertEqual(self.execute_bridge()["state"], "GEOMETRY_REVIEWED")
        final = self.f.repo / "runs/l7" / self.ids["bridge"]
        for stage_dir, prefix in ((self.path, "review"), (final, "review")):
            result_path = stage_dir / (prefix + "_result.json")
            original = result_path.read_bytes()
            result = l6.read_json(result_path)
            tag = result["observations"][0]
            cases = ([], [tag.replace("SATISFIED", "UNMET")], [tag.replace("SATISFIED", "UNCERTAIN")],
                     [tag.replace("@USER", "@HIDDEN")])
            for observations in cases:
                with self.subTest(stage=stage_dir.name, observations=observations):
                    try:
                        l6.worker.write_report(result_path, result | {"observations": observations})
                        with self.assertRaises((ValueError, l6.StageFailure)):
                            bound.internal_accept_candidate(self.parent, final)
                        self.assertFalse((self.session.directory / "internal_accept.json").exists())
                        self.assertFalse((self.session.directory / "scenario_a_accept.json").exists())
                    finally:
                        result_path.write_bytes(original)
            # Wrong Spec and stale Request lineage must also reject, regardless of PASS.
            for name, key in (("geometry_criteria.json" if stage_dir == final else "multiview_criteria.json",
                               "specification_identity_sha256"), (prefix + "_request.json", "run_id")):
                path = stage_dir / name
                original = path.read_bytes()
                content = l6.read_json(path)
                try:
                    l6.worker.write_report(path, content | {key: "wrong-current-identity"})
                    with self.subTest(stage=stage_dir.name, key=key), self.assertRaises((ValueError, l6.StageFailure)):
                        bound.internal_accept_candidate(self.parent, final)
                    self.assertFalse((self.session.directory / "internal_accept.json").exists())
                finally:
                    path.write_bytes(original)
        bound.internal_accept_candidate(self.parent, final).validate()

    def test_c01_geometry_correction_retains_multiview_and_uses_current_geometry(self):
        self.split_mandatory_criteria()
        h = self.correction_fixture()
        self.assertEqual(self.execute_correction(h.source)["state"], "INTERNAL_ACCEPT")
        path = self.f.repo / "runs/l7" / self.ids["correction"]
        before = {p.name: p.read_bytes() for p in self.path.iterdir() if p.is_file()}
        bound.internal_accept_candidate(self.parent, path).validate()
        accepted = l6.read_json(self.session.directory / "scenario_a_accept.json")
        self.assertEqual(accepted["stage_coverage"]["multiview"], l6.reference(self.path / "review_result_coverage.json"))
        self.assertEqual(accepted["stage_coverage"]["geometry"], l6.reference(path / "geometry_review_result_coverage.json"))
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.path.iterdir() if p.is_file()})
        self.assertFalse((path / "multiview_review_result.json").exists())

    def test_c01_view_correction_uses_replacement_multiview_evidence(self):
        self.split_mandatory_criteria()
        h = self.correction_fixture("right")
        self.assertEqual(self.execute_correction(h.source)["state"], "INTERNAL_ACCEPT")
        path = self.f.repo / "runs/l7" / self.ids["correction"]
        bound.internal_accept_candidate(self.parent, path).validate()
        accepted = l6.read_json(self.session.directory / "scenario_a_accept.json")
        self.assertEqual(accepted["stage_coverage"]["multiview"], l6.reference(path / "multiview_review_result_coverage.json"))
        self.assertNotEqual(accepted["stage_coverage"]["multiview"], l6.reference(self.path / "review_result_coverage.json"))
        self.assertEqual(accepted["stage_coverage"]["geometry"], l6.reference(path / "geometry_review_result_coverage.json"))

    def test_c01_initial_geometry_pass_cannot_accept_after_correction_started(self):
        self.geometry_fixture()
        self.assertEqual(self.execute_bridge()["state"], "GEOMETRY_REVIEWED")
        source = self.f.repo / "runs/l7" / self.ids["bridge"]
        current = source.parent / self.ids["correction"]
        current.mkdir()
        bound.child_binding(self.parent, "correction", current, source)
        with self.assertRaisesRegex(ValueError, "current correction evidence required"):
            bound.internal_accept_candidate(self.parent, source)
        self.assertFalse((self.session.directory / "internal_accept.json").exists())

    def test_c01_correction_failure_cannot_fall_back_to_initial_coverage(self):
        self.split_mandatory_criteria()
        h = self.correction_fixture()
        h.final_verdict = "REVISE"
        result = self.execute_correction(h.source)
        self.assertEqual((result["state"], result["reason"]), ("ABORT", "REVISION_BUDGET_EXHAUSTED"))
        path = self.f.repo / "runs/l7" / self.ids["correction"]
        for candidate in (h.source, path):
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                bound.internal_accept_candidate(self.parent, candidate)
        self.assertFalse((self.session.directory / "internal_accept.json").exists())

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

    def geometry_fixture(self, execute=True):
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
        if execute:
            self.assertEqual(self.execute_l6()["state"], "GEOMETRY_READY")
        self.g = bridge_tests.GeometryBridgeTests()
        self.g.fixture = self.f
        self.g.run_id = self.ids["bridge"]
        self.g.executable = self.f.root / "blender.exe"
        self.g.executable.write_bytes(b"SYNTHETIC_EXECUTABLE_NEVER_RUN")
        self.g.render_mutation = None
        self.g.review_mutation = self.tag_bridge_review
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
        other_doc = self.f.root / "other_spec.md"
        other_doc.write_text(self.doc.read_text(encoding="utf-8") + "\nDistinct Spec bytes.", encoding="utf-8")
        other_spec = sb.freeze_specification(other_doc, self.spec.fields)
        other_binding = other.create_binding(other_spec, "other-loop")
        parent = self.prepare(boundary=other, binding=other_binding)
        with self.assertRaises(ValueError):
            self.execute_bridge(parent)
        self.renderer.assert_not_called()
        self.assertEqual(self.execute_bridge()["state"], "GEOMETRY_REVIEWED")
        path = self.f.repo / "runs/l7" / self.ids["bridge"]
        with self.assertRaises(ValueError):
            controller.run_feedback(self.ids["correction"], path, self.f.comfy, self.g.executable,
                                    execute=True, session_binding=parent)

    def tagged_result(self, request, result):
        reference = request["context"].get("specification_review")
        if reference is None:
            return result
        criteria = l6.read_ref(reference)["criteria"]
        result["observations"] = [
            "[{criterion_id}@{authority_ref}] {status}: synthetic evidence".format(
                **c, status="UNMET" if result["verdict"] == "REVISE" and c["blocking_when_unmet"] else
                "UNCERTAIN" if result["verdict"] == "HUMAN_REQUIRED" else "SATISFIED")
            for c in criteria]
        result["blocking_issues"] = [t for t in result["observations"] if "] UNMET:" in t]
        return result

    def tag_l6_review(self, request_path, result_path, report_path):
        result = self.tagged_result(l6.read_json(request_path), l6.read_json(result_path))
        l6.worker.write_report(result_path, result)
        report = l6.read_json(report_path)
        report["result_sha256"] = l6.digest(result_path)
        l6.worker.write_report(report_path, report)

    def tag_bridge_review(self, request, result, report):
        result = self.tagged_result(request, result)
        if getattr(self, "review_mutator", None):
            self.review_mutator(result)
        l6.worker.write_report(Path(report["result_path"]), result)
        report["result_sha256"] = l6.digest(report["result_path"])

    def test_final_bridge_accept_candidate_no_delivery(self):
        self.geometry_fixture()
        self.review_mutator = lambda r: r["observations"].__setitem__(1, "[AC2@USER] UNMET: optional cosmetic preference")
        self.assertEqual(self.execute_bridge()["state"], "GEOMETRY_REVIEWED")
        path = self.f.repo / "runs/l7" / self.ids["bridge"]
        evidence = bound.internal_accept_candidate(self.parent, path)
        evidence.validate()
        self.assertEqual(self.session.outcome.status, "INTERNAL_ACCEPT")
        self.assertFalse(self.session.outcome.delivered)
        self.assertFalse((self.session.directory / "delivery_package.json").exists())
        with self.assertRaises(ValueError):
            bound.checked_parent(self.parent, execution=True)
        instructions = (path / "review_instructions.md").read_text(encoding="utf-8")
        self.assertIn("preserve the object", instructions)
        self.assertNotIn("Ignore texture", instructions)
        request = l6.read_json(path / "review_request.json")
        coverage = l6.read_json(path / "review_result_coverage.json")
        self.assertEqual(coverage["coverage"], {"AC1": "SATISFIED", "AC2": "UNMET"})
        self.assertEqual(coverage["request"], l6.reference(path / "review_request.json"))
        self.assertEqual(set(l6.read_json(path / "review_result.json")),
            {"review_version", "review_id", "stage", "source_result", "artifacts", "verdict",
             "blocking_issues", "observations", "suggested_action"})

    def unsupported_review(self, mutation):
        self.geometry_fixture()
        self.g.verdict = "REVISE"
        self.review_mutator = mutation
        state = self.execute_bridge()
        self.assertEqual((state["state"], state["reason"]), ("FAILED", "REVIEW_CONTRACT_VIOLATION"))
        path = self.f.repo / "runs/l7" / self.ids["bridge"]
        result = l6.read_json(path / "review_result.json")
        self.assertEqual(result["verdict"], "REVISE")  # raw verdict never coerced
        with self.assertRaises(ValueError):
            controller.run_feedback(self.ids["correction"], path, self.f.comfy, self.g.executable,
                                    execute=True, session_binding=self.parent)
        with self.assertRaises(ValueError):
            bound.internal_accept_candidate(self.parent, path)
        self.assertEqual((self.renderer.call_count, self.reviewer.call_count), (1, 1))
        self.f.assert_calls(4, 1)  # original L6 mock remains separately counted

    def test_unknown_criterion_blocks_correction_and_accept(self):
        self.unsupported_review(lambda r: r["blocking_issues"].__setitem__(0, "[UNKNOWN@USER] UNMET: blocker"))

    def test_review_undeclared_authority_blocks(self):
        self.unsupported_review(lambda r: r["blocking_issues"].__setitem__(0, "[AC1@HIDDEN] UNMET: blocker"))

    def test_nonblocking_criterion_cannot_be_blocker(self):
        def mutation(result):
            result["observations"][1] = "[AC2@USER] UNMET: cosmetic"
            result["blocking_issues"].append("[AC2@USER] UNMET: cosmetic")
        self.unsupported_review(mutation)

    def test_malformed_unsupported_blocker_is_contract_failure(self):
        self.unsupported_review(lambda r: r["blocking_issues"].__setitem__(0, "hidden invented quality goal"))

    def test_unbound_historical_pass_not_accept(self):
        legacy = bridge_tests.GeometryBridgeTests()
        legacy.setUp()
        self.addCleanup(legacy.doCleanups)
        self.assertEqual(legacy.execute()["state"], "GEOMETRY_REVIEWED")
        self.assertEqual(l6.read_json(legacy.run_dir / "review_result.json")["verdict"], "PASS")
        with self.assertRaisesRegex(ValueError, "UNBOUND"):
            bound.internal_accept_candidate(self.parent, legacy.run_dir)
        self.assertEqual(self.session.outcome.status, "LOOP_READY")

    def test_artifact_review_lineage_mismatch(self):
        self.geometry_fixture()
        self.execute_bridge()
        path = self.f.repo / "runs/l7" / self.ids["bridge"]
        manifest = l6.read_json(path / "render_manifest.json")
        manifest["source_glb"]["sha256"] = "0" * 64
        l6.worker.write_report(path / "render_manifest.json", manifest)
        with self.assertRaises(ValueError):
            bound.internal_accept_candidate(self.parent, path)
        self.assertFalse((self.session.directory / "internal_accept.json").exists())

    def test_terminal_session_prevents_registration_and_effect(self):
        self.session.stop("ABORT", "local fixture stop")
        with self.assertRaises(ValueError):
            self.session.register_child_evidence("new", sb.file_identity(self.doc, "spec"))
        with self.assertRaises(ValueError):
            self.execute_l6()
        self.f.assert_calls(0, 0)

    def test_typed_ambiguity_stops_same_loop(self):
        ambiguity = sb.SpecificationAmbiguity("relief or texture", "different geometry",
            "frozen context does not choose", ("relief", "texture"))
        bound.block_for_ambiguity(self.parent, ambiguity)
        self.assertEqual(self.session.outcome.status, "BLOCKED_SPECIFICATION_AMBIGUITY")
        with self.assertRaises(ValueError):
            self.execute_l6()
        with self.assertRaises(ValueError):
            self.session.register_child_evidence("new", sb.file_identity(self.doc, "spec"))
        self.f.assert_calls(0, 0)

    def correction_fixture(self, target="geometry"):
        import tests.test_l7_feedback_controller as feedback_tests
        self.geometry_fixture()
        self.g.verdict = "REVISE"
        self.g.action = {"code": "REGENERATE_GEOMETRY" if target == "geometry" else "REGENERATE_VIEW", "target": target}
        self.assertEqual(self.execute_bridge()["state"], "GEOMETRY_REVIEWED")
        h = feedback_tests.FeedbackControllerTests()
        h.fixture = self.g
        h.source = self.f.repo / "runs/l7" / self.ids["bridge"]
        h.comfy = self.f.comfy
        h.final_verdict = "PASS"
        h.multiview_verdict = "PASS"
        for name in ("worker_error", "render_error", "review_error", "worker_after", "render_after", "review_after"):
            setattr(h, name, None)
        h.old_glb = h.invalid_glb = h.invalid_png = False
        self.f.worker_mock.reset_mock()
        self.f.worker_mock.side_effect = h.fake_worker
        self.renderer.reset_mock()
        def render(command, **kwargs):
            value = h.fake_render(command, **kwargs)
            request = l6.read_json(Path(command[-1]))
            manifest = l6.read_json(request["manifest_path"])
            manifest["source_l6_run_id"] = request["source_l6_run_id"]
            l6.worker.write_report(Path(request["manifest_path"]), manifest)
            return value
        self.renderer.side_effect = render
        self.reviewer.reset_mock()
        self.reviewer.side_effect = h.fake_review
        return h

    def execute_correction(self, source):
        return controller.run_feedback(self.ids["correction"], source, self.f.comfy,
            self.g.executable, 1, 1, 1, execute=True, session_binding=self.parent)

    def test_correction_geometry_same_spec_authority_and_final_gate(self):
        h = self.correction_fixture()
        result = self.execute_correction(h.source)
        self.assertEqual(result["state"], "INTERNAL_ACCEPT", result)
        path = self.f.repo / "runs/l7" / self.ids["correction"]
        bound.internal_accept_candidate(self.parent, path).validate()
        self.assertEqual(self.session.outcome.status, "INTERNAL_ACCEPT")
        self.assertEqual((self.f.worker_mock.call_count, self.renderer.call_count, self.reviewer.call_count), (1, 1, 1))
        self.assertEqual(l6.read_json(path / "geometry_criteria.json")["criteria"],
            l6.read_json(h.source / "geometry_criteria.json")["criteria"])

    def test_correction_view_preserves_spec_through_both_reviews(self):
        h = self.correction_fixture("right")
        result = self.execute_correction(h.source)
        self.assertEqual(result["state"], "INTERNAL_ACCEPT", result)
        path = self.f.repo / "runs/l7" / self.ids["correction"]
        bound.internal_accept_candidate(self.parent, path).validate()
        self.assertEqual((self.f.worker_mock.call_count, self.renderer.call_count, self.reviewer.call_count), (2, 1, 2))
        self.assertEqual(l6.read_json(path / "multiview_criteria.json")["specification_identity_sha256"],
                         l6.read_json(path / "geometry_criteria.json")["specification_identity_sha256"])

    def assert_namespace_rejection(self, paths, message):
        for path in paths:
            with self.subTest(namespace=str(path)):
                path.mkdir(parents=True)
                marker = path / "existing_record.json"
                marker.write_bytes(b"historical namespace: never overwrite or reuse\n")
                before = {str(p): p.read_bytes() if p.is_file() else None
                          for p in self.f.root.rglob("*")}
                for execute in (False, True):
                    with self.subTest(execute=execute), self.assertRaisesRegex(ValueError, message):
                        bound.run_session(self.parent, comfy_root=self.f.comfy,
                            blender_executable=self.g.executable, execute=execute)
                    self.f.worker_mock.assert_not_called()
                    self.renderer.assert_not_called()
                    self.reviewer.assert_not_called()
                    self.f.network.assert_not_called()
                    self.assertEqual(self.session.outcome.status, "LOOP_READY")
                    self.assertEqual(before, {str(p): p.read_bytes() if p.is_file() else None
                                              for p in self.f.root.rglob("*")})
                # Only test-owned collision fixtures are removed between cases.
                marker.unlink()
                path.rmdir()

    def test_i03_clean_preflight_creates_no_namespace_or_records(self):
        self.geometry_fixture(execute=False)
        before = {str(p): p.read_bytes() if p.is_file() else None
                  for p in self.f.root.rglob("*")}
        result = bound.run_session(self.parent, comfy_root=self.f.comfy,
                                   blender_executable=self.g.executable)
        self.assertEqual(result["status"], "PREFLIGHT_PASS")
        self.assertEqual(result["effects"], 0)
        self.assertEqual(result["child_ids"], self.ids)
        self.assertEqual(before, {str(p): p.read_bytes() if p.is_file() else None
                                  for p in self.f.root.rglob("*")})
        self.f.worker_mock.assert_not_called()
        self.renderer.assert_not_called()
        self.reviewer.assert_not_called()
        self.f.network.assert_not_called()

    def test_i03_repository_child_collision_zero_effects(self):
        self.geometry_fixture(execute=False)
        paths = [self.f.repo / "runs/l6" / self.ids["l6"],
                 self.f.repo / "runs/l7" / self.ids["bridge"],
                 self.f.repo / "runs/l7" / self.ids["correction"]]
        self.assert_namespace_rejection(paths, "BOUND_ATTEMPT_ALREADY_EXISTS")

    def test_i03_l6_external_collision_zero_effects(self):
        self.geometry_fixture(execute=False)
        paths = [self.f.comfy / prefix / self.ids["l6"] for prefix in
                 ("work/input/l6", "work/output/l6", "work/output/mesh/l6")]
        self.assert_namespace_rejection(paths, "external namespace exists")

    def test_i03_bridge_external_collision_before_first_l6_effect(self):
        self.geometry_fixture(execute=False)
        self.assert_namespace_rejection(
            [self.f.comfy / "work/output/l7" / self.ids["bridge"]], "external namespace exists")

    def test_i03_correction_external_collision_before_first_l6_effect(self):
        self.geometry_fixture(execute=False)
        paths = [self.f.comfy / prefix / self.ids["correction"] for prefix in
                 ("work/input/l7", "work/output/l7", "work/output/mesh/l7")]
        self.assert_namespace_rejection(paths, "external namespace exists")

    def test_i03_direct_bridge_revalidates_after_clean_entry_preflight(self):
        self.geometry_fixture(execute=False)
        bound.run_session(self.parent, comfy_root=self.f.comfy,
                          blender_executable=self.g.executable)
        self.assertEqual(self.execute_l6()["state"], "GEOMETRY_READY")
        path = self.f.comfy / "work/output/l7" / self.ids["bridge"]
        path.mkdir(parents=True)
        marker = path / "existing_record.json"
        marker.write_bytes(b"preserve direct-entry collision")
        with self.assertRaisesRegex(ValueError, "external namespace exists"):
            self.execute_bridge()
        self.renderer.assert_not_called()
        self.assertEqual(self.reviewer.call_count, 1)  # Mock L6 Review only.
        self.assertEqual(marker.read_bytes(), b"preserve direct-entry collision")
        self.assertFalse((self.f.repo / "runs/l7" / self.ids["bridge"]).exists())

    def test_i03_direct_correction_local_external_guards(self):
        h = self.correction_fixture()
        for prefix in ("work/input/l7", "work/output/l7", "work/output/mesh/l7"):
            with self.subTest(prefix=prefix):
                path = self.f.comfy / prefix / self.ids["correction"]
                path.mkdir(parents=True)
                marker = path / "existing_record.json"
                marker.write_bytes(b"preserve direct-entry collision")
                with self.assertRaisesRegex(ValueError, "external namespace exists"):
                    self.execute_correction(h.source)
                self.f.worker_mock.assert_not_called()
                self.renderer.assert_not_called()
                self.reviewer.assert_not_called()
                self.assertEqual(marker.read_bytes(), b"preserve direct-entry collision")
                self.assertFalse((self.f.repo / "runs/l7" / self.ids["correction"]).exists())
                marker.unlink()
                path.rmdir()

    def test_fixed_session_entry_default_preflight_and_local_pass(self):
        self.geometry_fixture(execute=False)
        checks = bound.run_session(self.parent, comfy_root=self.f.comfy,
                                    blender_executable=self.g.executable)
        self.assertEqual(checks["effects"], 0)
        self.f.worker_mock.assert_not_called()
        self.renderer.assert_not_called()
        self.reviewer.assert_not_called()
        state = bound.run_session(self.parent, comfy_root=self.f.comfy,
            blender_executable=self.g.executable, execute=True,
            worker_timeout=1, review_timeout=1, render_timeout=1)
        self.assertEqual(state["state"], "INTERNAL_ACCEPT", state)
        self.assertFalse(state["delivered"])
        self.assertEqual((self.f.worker_mock.call_count, self.renderer.call_count, self.reviewer.call_count), (4, 1, 2))
        with self.assertRaises(ValueError):
            bound.run_session(self.parent, comfy_root=self.f.comfy, blender_executable=self.g.executable, execute=True)

    def test_whole_capability_missing_renderer_before_first_worker(self):
        self.geometry_fixture(execute=False)
        with self.assertRaises(FileNotFoundError):
            bound.run_session(self.parent, comfy_root=self.f.comfy,
                              blender_executable=self.f.root / "missing.exe", execute=True)
        self.f.worker_mock.assert_not_called()
        self.reviewer.assert_not_called()
        self.renderer.assert_not_called()

    def test_unsupported_action_is_deterministic_contract_failure(self):
        self.unsupported_review(lambda r: r.update(suggested_action={"code": "REGENERATE_VIEW", "target": "front"}))

    def test_bound_source_cannot_fall_back_to_legacy_controller(self):
        self.geometry_fixture()
        self.g.verdict = "REVISE"
        self.execute_bridge()
        source = self.f.repo / "runs/l7" / self.ids["bridge"]
        self.session.stop("ABORT", "explicit Session stop")
        self.f.worker_mock.reset_mock()
        self.renderer.reset_mock()
        self.reviewer.reset_mock()
        with self.assertRaisesRegex(ValueError, "BOUND_SOURCE_REQUIRES_SESSION_BINDING"):
            controller.preflight(source, self.f.comfy, self.g.executable)
        with self.assertRaisesRegex(ValueError, "BOUND_SOURCE_REQUIRES_SESSION_BINDING"):
            controller.run_feedback("legacy-bypass", source, self.f.comfy, self.g.executable, execute=True)
        self.f.worker_mock.assert_not_called()
        self.renderer.assert_not_called()
        self.reviewer.assert_not_called()
