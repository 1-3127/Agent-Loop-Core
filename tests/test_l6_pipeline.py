"""L6 local control tests; every Worker/Reviewer effect is mocked."""
import contextlib
import copy
import io
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from scenario_a import l6_pipeline as pipeline


class L6PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.comfy = self.root / "Comfy"
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.source = self.comfy / "work/input/hunyuan-official-demo-padded.png"
        self.source.parent.mkdir(parents=True)
        Image.new("RGB", (768, 768), "white").save(self.source)
        # Build synthetic graphs from fixed node identities, without any user image/model dependency.
        self.assets = copy.deepcopy(json.loads((PROJECT / "docs/l6/L6_ASSET_MANIFEST.json").read_text()))
        self.assets["source"] = pipeline.png_identity(self.source, "front")
        self.assets["models"] = []
        for role in pipeline.VIEWS + ("geometry",):
            v = self.assets["geometry"] if role == "geometry" else self.assets["view_generation"][role]
            graph = {key: {"class_type": value, "inputs": {}} for key, value in v["node_classes"].items()}
            graph["1"]["inputs"] = {"image": self.source.name}
            if role == "geometry":
                for name, node in pipeline.MAPPING.items():
                    graph[node]["inputs"] = {"image": self.source.name}
                    vision = v["conditioning_mapping"][name]
                    graph[vision]["inputs"] = {"image": [node, 0], "crop": "none"}
                graph["10"]["inputs"] = {name: [node, 0] for name, node in v["conditioning_mapping"].items()}
                graph["5"]["inputs"] = {"ckpt_name": v["model"]}
                graph["12"]["inputs"] = {"resolution": 1024}
                graph["15"]["inputs"] = {"octree_resolution": 128}
                graph["14"]["inputs"] = {"seed": v["seed"]}
                graph["17"]["inputs"] = {"filename_prefix": "mesh/template"}
            else:
                graph["4"]["inputs"] = {"unet_name": v["model"]}
                graph["8"]["inputs"] = {"prompt": v["prompt"]}
                graph["11"]["inputs"] = {"seed": v["template_seed"]}
                graph["13"]["inputs"] = {"filename_prefix": "template/" + role}
            path = self.comfy / v["workflow_relative"]
            path.parent.mkdir(parents=True, exist_ok=True)
            pipeline.write_once(path, graph)
            v["workflow"] = str(path)
            v["sha256"] = pipeline.digest(path)
        model = self.comfy / "models/checkpoints/fixture.bin"
        model.parent.mkdir(parents=True)
        model.write_bytes(b"synthetic-model-never-loaded")
        self.assets["models"] = [{"path": str(model), "bytes": model.stat().st_size}]
        self.asset_path = self.repo / "assets.json"
        pipeline.write_once(self.asset_path, self.assets)
        self.run_id = "l6-test"
        self.run_dir = self.repo / "runs/l6" / self.run_id
        for name, value in [("ROOT", self.repo), ("ASSET_MANIFEST", self.asset_path),
                            ("MANIFEST_SHA256", pipeline.digest(self.asset_path))]:
            p = mock.patch.object(pipeline, name, value)
            p.start()
            self.addCleanup(p.stop)
        # Tripwires ensure unintended actual transport cannot occur in any local test.
        self.network = mock.patch.object(pipeline.worker, "request_json",
                                         side_effect=AssertionError("actual Comfy transport forbidden")).start()
        self.process = mock.patch.object(pipeline.reviewer.subprocess, "run",
                                         side_effect=AssertionError("actual Reviewer process forbidden")).start()
        self.addCleanup(mock.patch.stopall)
        self.worker_mock = mock.patch.object(pipeline.worker, "run", side_effect=self.fake_worker).start()
        self.review_mock = mock.patch.object(pipeline.reviewer, "review_once", side_effect=self.fake_review).start()
        self.verdict = "PASS"
        self.worker_status = {}
        self.review_status = "SUCCESS"
        self.review_after = None
        self.worker_after = None
        self.invalid_glb = False

    def fake_worker(self, plan_path, report_path, comfy_root, timeout):
        plan = pipeline.read_json(plan_path)
        role = plan["task_id"].rsplit("-", 1)[-1]
        status = self.worker_status.get(role, "SUCCESS")
        report = {"schema_version": "0.1", "task_id": plan["task_id"],
                  "workflow": plan["workflow"], "output_node": plan["output_node"], "status": status,
                  "client_id": "fake-client-" + plan["task_id"],
                  "prompt_id": None if status == "UNRESOLVED" else "fake-prompt-" + plan["task_id"],
                  "started_at": pipeline.now(), "completed_at": None if status == "UNRESOLVED" else pipeline.now(),
                  "outputs": [], "errors": [] if status == "SUCCESS" else ["fixture failure"]}
        if status == "SUCCESS":
            node = "17" if role == "geometry" else "13"
            prefix = plan["patches"][node]["filename_prefix"]
            path = self.comfy / "work/output" / (prefix + "_00007_." + ("glb" if role == "geometry" else "png"))
            path.parent.mkdir(parents=True, exist_ok=True)
            if role == "geometry":
                data = struct.pack("<4sII", b"glTF", 2, 24) + struct.pack("<I4s", 4, b"JSON") + b"{}  "
                path.write_bytes(data[:-1] if self.invalid_glb else data)
                # Report success can lie: runner must validate the actual container independently.
                report["outputs"] = [{"type": "geometry", "path": str(path), "bytes": path.stat().st_size,
                                      "sha256": pipeline.digest(path), "glb_version": 2, "declared_length": len(data)}]
            else:
                Image.new("RGB", (768, 768), {"right": "red", "left": "green", "back": "blue"}[role]).save(path)
                report["outputs"] = [{"type": "image", "path": str(path), "width": 768, "height": 768}]
        pipeline.worker.write_report(report_path, report)
        if self.worker_after:
            self.worker_after(role, report_path)
        return 0 if status == "SUCCESS" else 2 if status == "UNRESOLVED" else 1

    def fake_review(self, request_path, result_path, report_path, timeout, workspace):
        request = pipeline.read_json(request_path)
        action = {"code": "NONE", "target": None}
        blockers = []
        if self.verdict == "REVISE":
            action = {"code": "MULTIVIEW_REVISE", "target": "back"}
            blockers = ["fixture blocker"]
        if self.verdict == "HUMAN_REQUIRED":
            action = {"code": "HUMAN_REQUIRED", "target": None}
        result = {"review_version": "0.3", "review_id": request["review_id"], "stage": request["stage"],
                  "source_result": request["source_result"], "artifacts": request["artifacts"],
                  "verdict": self.verdict, "blocking_issues": blockers,
                  "observations": ["synthetic local fixture, not actual semantic proof"], "suggested_action": action}
        pipeline.write_once(result_path, result)
        report = {"review_id": request["review_id"], "reviewer_mode": "CODEX_CLI",
                  "reviewer_process_started": True, "invocation_status": self.review_status,
                  "request_sha256": pipeline.digest(request_path), "result_sha256": pipeline.digest(result_path),
                  "result_path": str(result_path.resolve()), "verdict": self.verdict,
                  "started_at": pipeline.now(), "finished_at": pipeline.now(),
                  "duration_seconds": 0.01, "auth_mode": "SYNTHETIC_TEST",
                  "attached_images": [{key: a[key] for key in ("role", "path", "sha256")}
                                      for a in request["artifacts"]]}
        pipeline.write_once(report_path, report)
        if self.review_after:
            self.review_after(request_path, result_path, report_path)
        return report

    def run_fixture(self):
        return pipeline.run_pipeline(self.run_id, self.comfy, 1, 1, execute=True)

    def assert_calls(self, worker, review):
        self.assertEqual(self.worker_mock.call_count, worker)
        self.assertEqual(self.review_mock.call_count, review)
        self.network.assert_not_called()
        self.process.assert_not_called()

    def test_default_callable_and_preflight_are_effect_free(self):
        self.assertEqual(pipeline.run_pipeline(self.run_id, self.comfy)["status"], "PREFLIGHT_PASS")
        self.assertFalse(self.run_dir.exists())
        self.assert_calls(0, 0)

    def test_cli_help_default_and_preflight_are_safe(self):
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                pipeline.main(["--help"])
            self.assertEqual(result.exception.code, 0)
            for args in [[], ["--preflight"]]:
                self.assertEqual(pipeline.main(args + ["--comfy-root", str(self.comfy)]), 0)
        self.assertFalse(self.run_dir.exists())
        self.assert_calls(0, 0)

    def test_manifest_hash_and_workflow_hash_drift_block(self):
        self.asset_path.write_bytes(self.asset_path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "manifest hash"):
            pipeline.preflight(self.comfy)
        self.asset_path.write_bytes(self.asset_path.read_bytes()[:-1])
        path = Path(self.assets["view_generation"]["right"]["workflow"])
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "workflow hash"):
            pipeline.preflight(self.comfy)
        self.assert_calls(0, 0)

    def test_missing_model_blocks_without_effect(self):
        Path(self.assets["models"][0]["path"]).unlink()
        with self.assertRaisesRegex(ValueError, "model missing"):
            pipeline.preflight(self.comfy)
        self.assert_calls(0, 0)

    def test_image_plans_have_exact_schema_workflows_patches_and_prefixes(self):
        for role in pipeline.VIEWS:
            plan = pipeline.make_plan(self.run_id, role, self.assets)
            self.assertEqual(set(plan), {"schema_version", "task_id", "workflow", "patches", "output_node"})
            self.assertEqual(plan["workflow"], self.assets["view_generation"][role]["workflow_relative"])
            self.assertEqual(plan["patches"], {"1": {"image": self.source.name},
                             "8": {"prompt": self.assets["view_generation"][role]["prompt"]},
                             "11": {"seed": 29481}, "13": {"filename_prefix": f"l6/{self.run_id}/{role}"}})
            pipeline.worker.validate_plan(plan, self.comfy)

    def test_full_pass_four_workers_one_review_exact_staging_and_geometry(self):
        state = self.run_fixture()
        self.assertEqual(state["state"], "GEOMETRY_READY")
        self.assert_calls(4, 1)
        request = pipeline.read_json(self.run_dir / "review_request.json")
        self.assertEqual([a["role"] for a in request["artifacts"]], list(pipeline.ROLES))
        self.assertEqual(len({pipeline.read_json(self.run_dir / (v + "_execution.json"))["prompt_id"]
                              for v in pipeline.VIEWS}), 3)
        initial = pipeline.read_json(self.run_dir / "initial.json")
        self.assertEqual(initial["worker_budget"], {"limit": 4, "consumed": 0, "remaining": 4})
        self.assertEqual(initial["reviewer_budget"], {"limit": 1, "consumed": 0, "remaining": 1})
        for role in pipeline.VIEWS:
            generated = self.comfy / f"work/output/l6/{self.run_id}/{role}_00007_.png"
            staged = self.comfy / f"work/input/l6/{self.run_id}/{role}.png"
            self.assertEqual(staged.read_bytes(), generated.read_bytes())
            self.assertEqual(pipeline.digest(staged), pipeline.digest(generated))
        plan = pipeline.read_json(self.run_dir / "geometry_plan.json")
        for role, node in pipeline.MAPPING.items():
            self.assertEqual(plan["patches"][node]["image"],
                             self.source.name if role == "front" else f"l6/{self.run_id}/{role}.png")
        terminal = pipeline.read_json(self.run_dir / "terminal.json")
        self.assertIsNotNone(terminal["artifact"])
        self.assertEqual(terminal["worker_budget"]["remaining"], 0)
        self.assertEqual(terminal["reviewer_budget"]["remaining"], 0)

    def test_revise_aborts_without_geometry_or_revision(self):
        self.verdict = "REVISE"
        state = self.run_fixture()
        self.assertEqual((state["state"], state["reason"]), ("ABORT", "MULTIVIEW_REVISE"))
        self.assert_calls(3, 1)
        self.assertFalse((self.run_dir / "geometry_plan.json").exists())

    def test_human_required_aborts_without_geometry(self):
        self.verdict = "HUMAN_REQUIRED"
        state = self.run_fixture()
        self.assertEqual((state["state"], state["reason"]), ("ABORT", "HUMAN_REQUIRED"))
        self.assert_calls(3, 1)
        self.assertFalse((self.run_dir / "geometry_work_order.json").exists())

    def test_image_known_failure_stops_remaining_workers(self):
        self.worker_status["right"] = "FAILED"
        state = self.run_fixture()
        self.assertEqual((state["state"], state["reason"], state["failed_stage"]), ("FAILED", "VIEW_STAGE", "right"))
        self.assert_calls(1, 0)
        self.assertEqual(state["worker_budget"]["consumed"], 1)

    def test_image_uncertain_has_no_retry_or_downstream(self):
        self.worker_status["right"] = "UNRESOLVED"
        state = self.run_fixture()
        self.assertEqual(state["state"], "UNRESOLVED")
        self.assert_calls(1, 0)
        with self.assertRaisesRegex(ValueError, "L6_RUN_ALREADY_EXISTS"):
            self.run_fixture()
        self.assert_calls(1, 0)
        self.assertFalse((self.run_dir / "terminal.json").exists())

    def test_reviewer_known_failure_no_retry_or_geometry(self):
        self.review_status = "FAILED"
        state = self.run_fixture()
        self.assertEqual((state["state"], state["reason"]), ("FAILED", "REVIEW_STAGE"))
        self.assert_calls(3, 1)

    def test_reviewer_uncertain_no_retry_or_geometry(self):
        self.review_status = "UNRESOLVED"
        state = self.run_fixture()
        self.assertEqual(state["state"], "UNRESOLVED")
        self.assert_calls(3, 1)
        self.assertEqual(state["reviewer_budget"]["consumed"], 1)

    def test_geometry_known_failure(self):
        self.worker_status["geometry"] = "FAILED"
        state = self.run_fixture()
        self.assertEqual((state["state"], state["reason"]), ("FAILED", "GEOMETRY_STAGE"))
        self.assert_calls(4, 1)

    def test_geometry_uncertain_no_retry(self):
        self.worker_status["geometry"] = "UNRESOLVED"
        state = self.run_fixture()
        self.assertEqual(state["state"], "UNRESOLVED")
        self.assert_calls(4, 1)

    def test_invalid_glb_rejects_success_report(self):
        self.invalid_glb = True
        state = self.run_fixture()
        self.assertEqual(state["state"], "FAILED")
        self.assertEqual(state["reason"], "GEOMETRY_STAGE")
        self.assert_calls(4, 1)

    def test_review_attachment_mismatch_is_unresolved(self):
        def mutate(req, result, report):
            data = pipeline.read_json(report)
            data["attached_images"].reverse()
            pipeline.worker.write_report(report, data)
        self.review_after = mutate
        self.assertEqual(self.run_fixture()["state"], "UNRESOLVED")
        self.assert_calls(3, 1)

    def test_review_result_hash_mismatch_is_unresolved(self):
        self.review_after = lambda req, result, report: result.write_bytes(result.read_bytes() + b" ")
        self.assertEqual(self.run_fixture()["state"], "UNRESOLVED")
        self.assert_calls(3, 1)

    def test_generated_output_mutation_after_pass_blocks_geometry(self):
        original = pipeline.stage_reviewed_bytes
        def mutate_then_stage(run_dir, root):
            path = Path(pipeline.read_json(run_dir / "multiview_manifest.json")["views"][0]["path"])
            Image.new("RGB", (768, 768), "black").save(path)
            return original(run_dir, root)
        with mock.patch.object(pipeline, "stage_reviewed_bytes", side_effect=mutate_then_stage):
            self.assertEqual(self.run_fixture()["state"], "FAILED")
        self.assert_calls(3, 1)

    def test_staged_mutation_blocks_geometry(self):
        original = pipeline.stage_reviewed_bytes
        def stage_then_mutate(run_dir, root):
            original(run_dir, root)
            Image.new("RGB", (768, 768), "black").save(root / f"work/input/l6/{self.run_id}/right.png")
        with mock.patch.object(pipeline, "stage_reviewed_bytes", side_effect=stage_then_mutate):
            self.assertEqual(self.run_fixture()["state"], "FAILED")
        self.assert_calls(3, 1)

    def test_staging_collision_never_overwrites_identical_bytes(self):
        def collision(req, result, report):
            path = self.comfy / f"work/input/l6/{self.run_id}/right.png"
            path.parent.mkdir(parents=True)
            image = Path(pipeline.read_json(req)["artifacts"][1]["path"])
            path.write_bytes(image.read_bytes())
            self.collision_bytes = path.read_bytes()
        self.review_after = collision
        self.assertEqual(self.run_fixture()["state"], "FAILED")
        self.assertEqual((self.comfy / f"work/input/l6/{self.run_id}/right.png").read_bytes(), self.collision_bytes)
        self.assert_calls(3, 1)

    def test_fixed_roles_missing_duplicate_unknown_are_rejected(self):
        self.run_fixture()
        original = pipeline.read_json(self.run_dir / "multiview_manifest.json")
        for mutation in ("missing", "duplicate", "unknown"):
            manifest = copy.deepcopy(original)
            if mutation == "missing":
                manifest["views"].pop()
            elif mutation == "duplicate":
                manifest["views"][1]["role"] = "right"
            else:
                manifest["views"][1]["role"] = "top"
            with self.assertRaisesRegex(ValueError, "fixed roles"):
                pipeline.validate_manifest(manifest, self.run_dir)

    def test_cross_run_execution_lineage_is_rejected(self):
        self.run_fixture()
        p = self.run_dir / "right_execution.json"
        execution = pipeline.read_json(p)
        execution["run_id"] = "another-run"
        pipeline.worker.write_report(p, execution)
        manifest = pipeline.read_json(self.run_dir / "multiview_manifest.json")
        manifest["views"][0]["execution_report"] = pipeline.reference(p)
        with self.assertRaisesRegex(ValueError, "execution/run lineage"):
            pipeline.validate_manifest(manifest, self.run_dir)

    def test_worker_reservation_bypass_different_task_and_report_has_no_effect(self):
        def probe(role, report):
            if role != "right":
                return
            p = self.run_dir / "right_work_order.json"
            altered = pipeline.read_json(p)
            altered["work_order_id"] = "different-task"
            altered["worker_report_path"] = str(self.run_dir / "bypass.json")
            alternate = self.run_dir / "alternate_order.json"
            pipeline.write_once(alternate, altered)
            with self.assertRaisesRegex(ValueError, "WORKER_STAGE_ALREADY_RESERVED"):
                pipeline.run_worker(alternate, self.comfy, 1)
        self.worker_after = probe
        self.assertEqual(self.run_fixture()["state"], "GEOMETRY_READY")
        self.assert_calls(4, 1)
        self.assertFalse((self.run_dir / "bypass.json").exists())

    def test_reviewer_reservation_bypass_alternate_identity_and_paths(self):
        def probe(req, result, report):
            alternate = pipeline.read_json(req)
            alternate["review_id"] = "different-review"
            path = self.run_dir / "alternate_request.json"
            pipeline.write_once(path, alternate)
            with self.assertRaisesRegex(ValueError, "REVIEW_BUDGET_ALREADY_RESERVED"):
                pipeline.reserve_review(self.run_dir, path, self.run_dir / "alternate_result.json",
                                        self.run_dir / "alternate_invocation.json")
            with self.assertRaisesRegex(ValueError, "REVIEW_BUDGET_ALREADY_RESERVED"):
                pipeline.run_review(self.run_dir, 1)
        self.review_after = probe
        self.assertEqual(self.run_fixture()["state"], "GEOMETRY_READY")
        self.assert_calls(4, 1)

    def test_terminal_reentry_preserves_bytes_and_effect_counts(self):
        self.run_fixture()
        p = self.run_dir / "terminal.json"
        before = p.read_bytes()
        self.assertEqual(self.run_fixture()["status"], "ALREADY_TERMINAL")
        for effect in [lambda: pipeline.run_review(self.run_dir, 1),
                       lambda: pipeline.run_worker(self.run_dir / "right_work_order.json", self.comfy, 1),
                       lambda: pipeline.update_state(self.run_dir, "SOURCE_READY"),
                       lambda: pipeline.finish(self.run_dir, "ABORT", "probe", "review"),
                       lambda: pipeline.stage_reviewed_bytes(self.run_dir, self.comfy)]:
            with self.assertRaisesRegex(ValueError, "ALREADY_TERMINAL"):
                effect()
        self.assertEqual(p.read_bytes(), before)
        self.assert_calls(4, 1)

    def test_budget_invariants_and_unknown_usage_stay_null(self):
        self.run_fixture()
        usage = pipeline.read_json(self.run_dir / "usage.json")
        for b in usage["budgets"].values():
            self.assertLessEqual(b["consumed"], b["limit"])
            self.assertEqual(b["remaining"], b["limit"] - b["consumed"])
        for key in ("requested_model", "requested_reasoning_effort", "actual_model", "actual_reasoning_effort",
                    "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "reported_credits"):
            self.assertIsNone(usage["frontier"][key])
        self.assertEqual([v["invocations"] for v in usage["workers"]], [1, 1, 1, 1])
        self.assertEqual(usage["frontier"]["invocations"], 1)

    def test_wrong_worker_task_is_rejected_before_review(self):
        def mutate(role, path):
            if role == "right":
                report = pipeline.read_json(path)
                report["task_id"] = "historical-task"
                pipeline.worker.write_report(path, report)
        self.worker_after = mutate
        self.assertEqual(self.run_fixture()["state"], "FAILED")
        self.assert_calls(1, 0)

    def test_no_automatic_resume_of_incomplete_namespace(self):
        self.run_dir.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "L6_RUN_ALREADY_EXISTS"):
            self.run_fixture()
        self.assert_calls(0, 0)

    def test_failure_execution_summary_retains_report_and_null_artifact(self):
        self.worker_status["right"] = "FAILED"
        self.run_fixture()
        execution = pipeline.read_json(self.run_dir / "right_execution.json")
        self.assertEqual(execution["status"], "FAILED")
        self.assertIsNone(execution["artifact"])
        self.assertEqual(execution["worker_report"], pipeline.reference(self.run_dir / "right_worker_report.json"))
        terminal = pipeline.read_json(self.run_dir / "terminal.json")
        self.assertIsNone(terminal["records"]["geometry_execution"])

    def test_worker_exception_after_reservation_is_unresolved_without_refund(self):
        self.worker_mock.side_effect = TimeoutError("fixture transport timeout")
        state = self.run_fixture()
        self.assertEqual(state["state"], "UNRESOLVED")
        self.assertEqual(state["worker_budget"]["consumed"], 1)
        self.assert_calls(1, 0)
        self.assertIsNone(pipeline.read_json(self.run_dir / "right_execution.json")["worker_report"])

    def test_malformed_worker_report_is_unresolved_and_retained(self):
        self.worker_after = lambda role, path: path.write_bytes(b"{broken")
        self.assertEqual(self.run_fixture()["state"], "UNRESOLVED")
        self.assert_calls(1, 0)
        self.assertEqual((self.run_dir / "right_worker_report.json").read_bytes(), b"{broken")

    def test_malformed_review_result_cannot_open_geometry_gate(self):
        def malformed(req, result, report):
            result.write_bytes(b"{broken")
            invocation = pipeline.read_json(report)
            invocation["result_sha256"] = pipeline.digest(result)
            pipeline.worker.write_report(report, invocation)
        self.review_after = malformed
        self.assertEqual(self.run_fixture()["state"], "UNRESOLVED")
        self.assert_calls(3, 1)

    def test_invalid_png_does_not_create_success_execution_or_review(self):
        def corrupt(role, path):
            if role == "right":
                output = pipeline.read_json(path)["outputs"][0]["path"]
                Path(output).write_bytes(b"not a png")
        self.worker_after = corrupt
        self.assertEqual(self.run_fixture()["state"], "FAILED")
        self.assert_calls(1, 0)
        self.assertIsNone(pipeline.read_json(self.run_dir / "right_execution.json")["artifact"])

    def test_geometry_order_requires_pass_even_on_direct_publication(self):
        def probe(req, result, report):
            with self.assertRaisesRegex(ValueError, "Geometry requires PASS"):
                pipeline.publish_order(self.run_dir, "geometry", self.assets, {})
        self.verdict = "REVISE"
        self.review_after = probe
        self.assertEqual(self.run_fixture()["state"], "ABORT")
        self.assert_calls(3, 1)
        self.assertFalse((self.run_dir / "geometry_plan.json").exists())


if __name__ == "__main__":
    unittest.main()
