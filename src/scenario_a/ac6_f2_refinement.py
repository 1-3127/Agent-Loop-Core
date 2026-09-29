"""Run-scoped dry contract for the reachable 128-to-192 geometry refinement."""

import copy
import hashlib
from pathlib import Path

import ac6_f2_geometry as geometry
import ac6_f2_geometry_review as geometry_review
import codex_to_comfy as executor
import persist_geometry_state as persistence
import pipeline_a_controller as controller


ROOT = geometry.ROOT


def namespace(run_id, decision_ref):
    stem = f"{run_id}-refine-{decision_ref['sha256'][:12]}"
    if len(stem) > 80:
        raise ValueError("refinement task identity too long")
    return {"task_id": stem, "prefix": f"mesh/{stem}",
            "plan": ROOT / "plans" / (stem + ".json"),
            "receipt": ROOT / "dispatch_receipts" / (decision_ref["sha256"] + ".json"),
            "report": ROOT / "runs" / (stem + "_report.json"),
            "state": ROOT / "controller_states" / (stem + "_pending.json"),
            "evidence_request": ROOT / "evidence_requests" / (stem + ".json"),
            "manifest": ROOT / "evidence_manifests" / (stem + ".json"),
            "review_request": ROOT / "reviewer_requests" / (stem + ".json"),
            "review_result": ROOT / "reviewer_results" / (stem + ".json"),
            "review_report": ROOT / "invocation_reports" / (stem + ".json")}


def build(attached_ref, input_ref, decision_ref, *,
          output_root=geometry.coverage.OUTPUT_ROOT,
          comfy_root=executor.DEFAULT_COMFY_ROOT, evidence_dir=ROOT / "runs",
          allow_control_fixture=False, allow_consumed=False):
    item, expected = geometry_review.controller_input(
        attached_ref, output_root=output_root, evidence_dir=evidence_dir,
        allow_control_fixture=allow_control_fixture)
    if geometry.read(input_ref) != item or geometry.read(decision_ref) != expected:
        raise ValueError("refinement Controller Input/Decision differs")
    attached = geometry.read(attached_ref)
    if (expected["run_id"] != attached["run_id"]
            or expected["controller_decision"] != "EXECUTE"
            or expected["action"] != "REFINE_GEOMETRY"
            or expected["execution_required"] is not True
            or expected["next_state"] != "EXECUTING"
            or expected["return_review_state"] != "REFINEMENT_REVIEW"
            or persistence.guard_execution(attached) != "EXECUTION_ALLOWED"):
        raise ValueError("refinement not authorized by policy/budget")
    source = geometry.read(attached["geometry_dispatch"])
    baseline_plan = source["plan"]
    plan = copy.deepcopy(baseline_plan)
    ns = namespace(attached["run_id"], decision_ref)
    plan["task_id"] = ns["task_id"]
    plan["patches"]["15"] = {"octree_resolution": 192}
    plan["patches"]["17"]["filename_prefix"] = ns["prefix"]
    if (attached["state"]["refinement"] != {"current_octree": 128, "target_octree": 192}
            or attached["state"]["latest_artifact"] != attached["glb"]
            or baseline_plan["patches"].get("15") is not None
            or plan["workflow"] != "workflows/03_Multiview_to_3D/Hunyuan3D_MV_RTX4060_api.json"):
        raise ValueError("historical 128-to-192 refinement contract differs")
    graph = executor.validate_plan(plan, comfy_root)
    if (graph["15"]["inputs"]["octree_resolution"] != 192
            or graph["17"]["class_type"] != "SaveGLB"):
        raise ValueError("refinement graph differs")
    for key in ("plan", "receipt", "report", "state", "evidence_request", "manifest",
                "review_request", "review_result", "review_report"):
        if not allow_consumed and ns[key].exists():
            raise ValueError("refinement namespace collision: " + key)
    prefix = executor.safe_relative(ns["prefix"], "filename_prefix")
    output_dir = Path(comfy_root) / "work/output" / prefix.parent
    if not allow_consumed and output_dir.exists() and any(output_dir.glob(prefix.name + "_*")):
        raise ValueError("refinement output collision")
    return {"classification": "FRESH_REFINEMENT_CONTRACT", "run_id": attached["run_id"],
            "source_state": attached_ref, "controller_input": input_ref,
            "decision": decision_ref, "geometry_dispatch": attached["geometry_dispatch"],
            "baseline_glb": attached["glb"], "plan": plan,
            "namespace": {key: str(value) if isinstance(value, Path) else value for key, value in ns.items()}}


def intent(request):
    source = geometry.read(request["source_state"])
    state = source["state"]
    if persistence.guard_execution(source) != "EXECUTION_ALLOWED":
        raise ValueError("BUDGET_EXHAUSTED")
    if state["action_counts"]["REFINE_GEOMETRY"] >= state["budget_config"]["max_refinements"]:
        raise ValueError("REFINEMENT_BUDGET_EXHAUSTED")
    before = state["iteration_count"]
    reserved = copy.deepcopy(state)
    reserved["iteration_count"] += 1
    reserved["current_state"] = "EXECUTING"
    controller.validate_state(reserved)
    return {"classification": "FRESH_REFINEMENT_INTENT_CONTRACT", "status": "INTENT_RESERVED",
            "run_id": request["run_id"], "source_state": request["source_state"],
            "decision": request["decision"], "task_id": request["namespace"]["task_id"],
            "plan_sha256": hashlib.sha256(controller.canonical(request["plan"])).hexdigest(),
            "output_prefix": request["namespace"]["prefix"], "iteration_before": before,
            "iteration_after": before + 1,
            "remaining_after": state["budget_config"]["max_total_iterations"] - before - 1,
            "reserved_state": reserved}


def result_snapshot(request, receipt_ref, report_ref, *, output_root=geometry.coverage.OUTPUT_ROOT):
    receipt, report = geometry.read(receipt_ref), geometry.read(report_ref)
    expected = intent(request)
    if receipt != expected:
        raise ValueError("refinement intent differs")
    if request["classification"] != "SYNTHETIC_CONTROL_FIXTURE":
        replayed = build(request["source_state"], request["controller_input"],
                         request["decision"], allow_consumed=True)
        if replayed != request:
            raise ValueError("fresh refinement replay differs")
        ns = request["namespace"]
        if (geometry.reviewer.checked_ref(receipt_ref) != Path(ns["receipt"]).resolve()
                or geometry.reviewer.checked_ref(report_ref) != Path(ns["report"]).resolve()
                or geometry.read(geometry.ref(ns["plan"])) != request["plan"]):
            raise ValueError("refinement Plan/Result namespace differs")
    if (report.get("classification") == "SYNTHETIC_CONTROL_FIXTURE"
            and request["classification"] != "SYNTHETIC_CONTROL_FIXTURE"):
        raise ValueError("synthetic refinement Result in production contract")
    if (report.get("status") != "SUCCESS" or not report.get("client_id")
            or not report.get("prompt_id") or report.get("errors") != []
            or report.get("task_id") != request["namespace"]["task_id"]
            or report.get("workflow") != request["plan"]["workflow"]
            or report.get("output_node") != "17" or len(report.get("outputs", [])) != 1
            or report["outputs"][0].get("type") != "geometry"):
        raise ValueError("refinement Result differs")
    output = report["outputs"][0]
    path = Path(output["path"]).resolve()
    prefix = executor.safe_relative(request["namespace"]["prefix"], "output prefix")
    if (path.parent != (Path(output_root) / prefix.parent).resolve()
            or not path.name.startswith(prefix.name + "_") or path.suffix.lower() != ".glb"):
        raise ValueError("refinement output namespace differs")
    artifact = geometry.glb(path)
    if (output.get("sha256") != artifact["sha256"] or output.get("bytes") != path.stat().st_size
            or output.get("glb_version") != 2 or output.get("declared_length") != path.stat().st_size):
        raise ValueError("refinement GLB differs")
    state = copy.deepcopy(expected["reserved_state"])
    state["current_state"] = "REFINEMENT_REVIEW"
    state["latest_artifact"] = artifact
    state["latest_review"] = None
    state["action_counts"]["REFINE_GEOMETRY"] += 1
    state["action_history"].append({"code": "REFINE_GEOMETRY", "target": None,
                                    "blocker_code": None, "region": None})
    controller.validate_state(state)
    return {"state_version": "ac6-f2-refinement.0", "classification": request["classification"],
            "run_id": request["run_id"], "source_state": request["source_state"],
            "decision": request["decision"], "intent_receipt": receipt_ref,
            "result": report_ref, "glb": artifact, "baseline_glb": request["baseline_glb"],
            "pending_semantic_review": True, "remaining_total_iterations": expected["remaining_after"],
            "terminal": False, "state": state}


def evidence_request(request, receipt_ref, report_ref, pending_ref, *,
                     output_root=geometry.coverage.OUTPUT_ROOT,
                     evidence_dir=ROOT / "runs", allow_generated=False):
    pending = geometry.read(pending_ref)
    if pending != result_snapshot(request, receipt_ref, report_ref, output_root=output_root):
        raise ValueError("stale refinement pending state")
    if (request["classification"] != "SYNTHETIC_CONTROL_FIXTURE"
            and geometry.reviewer.checked_ref(pending_ref) != Path(request["namespace"]["state"]).resolve()):
        raise ValueError("refinement pending namespace differs")
    if not geometry.BLENDER.is_file():
        raise ValueError("Blender unavailable")
    original = geometry.read(request["geometry_dispatch"])
    ns = request["namespace"]
    views = [{"role": role, "mesh_axis": axis, "blender_direction": direction,
              "output": str(Path(evidence_dir).resolve() / f"{ns['task_id']}_{role}.png")}
             for role, axis, direction in geometry.AXES]
    if not allow_generated and (any(Path(v["output"]).exists() for v in views)
                                or Path(ns["manifest"]).exists()):
        raise ValueError("refinement evidence collision")
    return {"evidence_version": "ac6-f2-refinement.0", "classification": request["classification"],
            "run_id": request["run_id"], "state": pending_ref, "decision": request["decision"],
            "receipt": receipt_ref, "report": report_ref, "source_glb": pending["glb"],
            "source_views": [{"role": v["role"], "path": v["source"]["path"],
                              "sha256": v["source"]["sha256"]} for v in original["selected_inputs"]],
            "renderer": {"name": "Blender", "version": "5.2.0 LTS",
                         "engine": "BLENDER_WORKBENCH", "resolution": [512, 512],
                         "margin": 1.2, "executable": str(geometry.BLENDER)},
            "views": views, "manifest": str(ns["manifest"])}


def reviewer_request(request, receipt_ref, report_ref, pending_ref, evidence_ref, manifest_ref,
                     *, output_root=geometry.coverage.OUTPUT_ROOT, evidence_dir=ROOT / "runs",
                     allow_reserved=False):
    evidence = geometry.read(evidence_ref)
    if evidence != evidence_request(request, receipt_ref, report_ref, pending_ref,
                                    output_root=output_root, evidence_dir=evidence_dir,
                                    allow_generated=True):
        raise ValueError("stale refinement evidence")
    ns = request["namespace"]
    if request["classification"] != "SYNTHETIC_CONTROL_FIXTURE":
        if (geometry.reviewer.checked_ref(evidence_ref) != Path(ns["evidence_request"]).resolve()
                or geometry.reviewer.checked_ref(manifest_ref) != Path(ns["manifest"]).resolve()):
            raise ValueError("refinement evidence namespace differs")
    manifest = geometry.read(manifest_ref)
    generated = manifest.get("evidence_version") == "p2-e1.0"
    identity = (manifest.get("request_sha256") == evidence_ref["sha256"]
                and Path(manifest.get("request_path", "")).resolve()
                == geometry.reviewer.checked_ref(evidence_ref)) if generated else (
                    manifest.get("classification") == "SYNTHETIC_CONTROL_FIXTURE"
                    and request["classification"] == "SYNTHETIC_CONTROL_FIXTURE"
                    and manifest.get("request") == evidence_ref)
    if (not identity or manifest.get("source_glb") != evidence["source_glb"]
            or manifest.get("state") != pending_ref or manifest.get("report") != report_ref
            or (generated and (manifest.get("status") != "SUCCESS"
                               or manifest.get("receipt") != receipt_ref
                               or manifest.get("source_views") != evidence["source_views"]))
            or [v.get("role") for v in manifest.get("views", [])] != list(geometry.ROLES)):
        raise ValueError("stale refinement manifest")
    artifacts = []
    for source, rendered in zip(evidence["source_views"], manifest["views"]):
        image = geometry.ref(rendered["path"])
        expected_path = Path(evidence_dir).resolve() / f"{ns['task_id']}_{source['role']}.png"
        if (source["role"] != rendered["role"] or image["sha256"] != rendered["sha256"]
                or Path(rendered["path"]).resolve() != expected_path):
            raise ValueError("refinement preview identity differs")
        artifacts.extend(({"role": "source_" + source["role"], "path": source["path"],
                           "sha256": source["sha256"], "media_type": "image/png"},
                          {"role": "geometry_" + source["role"], **image,
                           "media_type": "image/png"}))
    if not allow_reserved and (Path(ns["review_result"]).exists() or Path(ns["review_report"]).exists()):
        raise ValueError("REVIEW_ALREADY_RESERVED")
    result = {"request_version": "0.1", "review_id": ns["task_id"],
              "stage": "REFINEMENT_REVIEW", "output_kind": "geometry",
              "source_result": report_ref, "previous_decision": request["decision"],
              "invocation": receipt_ref, "state": pending_ref,
              "artifacts": artifacts, "instruction_file": geometry.ref(geometry.REVIEW_INSTRUCTIONS),
              "context": {"run_id": request["run_id"], "evidence_manifest": manifest_ref,
                          "baseline_glb_sha256": request["baseline_glb"]["sha256"],
                          "glb_sha256": evidence["source_glb"]["sha256"],
                          "review_scope": "GROSS_REFINEMENT_FOUR_VIEW_COMPARISON",
                          "review_identity": {"state_sha256": pending_ref["sha256"],
                                              "result_sha256": report_ref["sha256"],
                                              "manifest_sha256": manifest_ref["sha256"]}}}
    geometry.reviewer.validate_request(result)
    return result
