"""Fresh Scenario A geometry boundaries. Builders are read-only; no service calls."""

import copy
import hashlib
import json
import re
import struct
from pathlib import Path

import codex_to_comfy as executor
import dispatch_geometry as historical
import persist_geometry_state as persistence
import pipeline_a_controller as controller
import result_review_adapter as reviewer
import scenario_a_coverage as coverage


ROOT = Path(__file__).resolve().parents[2]
ROLES = ("front", "left", "back", "right")
AXES = (("front", "+Z", [0, -1, 0]), ("left", "-X", [-1, 0, 0]),
        ("back", "-Z", [0, 1, 0]), ("right", "+X", [1, 0, 0]))
BLENDER = Path("D:/Blender_5.2/blender.exe")
REVIEW_INSTRUCTIONS = ROOT / "reviewer_requests/ac6_f2_geometry_instructions.md"


def ref(path):
    path = Path(path).resolve()
    return {"path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
            "sha256": reviewer.digest(path)}


def read(item):
    path = reviewer.checked_ref(item)
    return json.loads(path.read_text(encoding="utf-8"))


def within(root, relative):
    path = (Path(root).resolve() / relative).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError("path escapes namespace")
    return path


def namespace(run_id, decision_ref):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", run_id):
        raise ValueError("unsafe run identity")
    key = decision_ref["sha256"][:12]
    stem = f"{run_id}-geometry-{key}"
    if len(stem) > 80:
        raise ValueError("geometry task identity too long")
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


def build_dispatch(coverage_ref, state_ref, input_ref, decision_ref, receipts,
                   *, output_root=coverage.OUTPUT_ROOT, comfy_root=executor.DEFAULT_COMFY_ROOT,
                   allow_consumed=False):
    selected = read(coverage_ref)
    generated = sorted((v for v in selected["resolved_views"] if v["kind"] == "GENERATED"),
                       key=lambda v: coverage.load_config()[0]["acquisition_order"].index(v["role"]))
    if coverage.evaluate(generated, output_root=output_root) != selected or selected["geometry_ready"] is not True:
        raise ValueError("four-view coverage is not READY")
    outcome, decision = coverage.route_after_controller(coverage_ref, state_ref, input_ref,
                                                        decision_ref, output_root=output_root)
    if outcome != "READY_FOR_CONTROLLER" or decision != read(decision_ref):
        raise ValueError("Controller geometry Decision required")
    state = read(state_ref)
    if state["run_id"] != selected["run_id"] or state["state"]["run_id"] != selected["run_id"]:
        raise ValueError("geometry run differs")
    if set(receipts) != {"right", "left", "back"}:
        raise ValueError("all generated view receipts required")
    previous = 0
    for role in ("right", "left", "back"):
        view = next(v for v in generated if v["role"] == role)
        receipt = read(receipts[role])
        report = read(view["report"])
        if (receipt.get("run_id") != selected["run_id"] or receipt.get("role") != role
                or receipt.get("decision") != view["decision"]
                or receipt.get("status") not in ("INTENT_RESERVED", "SUCCESS")
                or receipt.get("task_id") != report["task_id"]
                or receipt.get("iteration_before") != previous
                or receipt.get("iteration_after") != previous + 1
                or receipt.get("remaining_after") != state["state"]["budget_config"]["max_total_iterations"] - previous - 1):
            raise ValueError("generated view receipt lineage differs: " + role)
        previous += 1
    if previous != state["state"]["iteration_count"]:
        raise ValueError("generated intent count differs")
    ns = namespace(selected["run_id"], decision_ref)
    for key in ("plan", "receipt", "report", "state", "evidence_request", "manifest", "review_request",
                "review_result", "review_report"):
        if not allow_consumed and ns[key].exists():
            raise ValueError("fresh namespace collision: " + key)
    prefix = executor.safe_relative(ns["prefix"], "filename_prefix")
    output_dir = (Path(comfy_root) / "work/output" / prefix.parent).resolve()
    if not allow_consumed and output_dir.exists() and any(output_dir.glob(prefix.name + "_*")):
        raise ValueError("geometry output collision")
    input_root = Path(comfy_root) / "work/input"
    staged = []
    for view in selected["resolved_views"]:
        role = view["role"]
        name = f"{ns['task_id']}_{role}.png"
        source = Path(view["path"]).resolve()
        if reviewer.digest(source) != view["sha256"]:
            raise ValueError("view hash differs: " + role)
        target = within(input_root, name)
        if not target.is_file() or reviewer.digest(target) != view["sha256"]:
            raise ValueError("staged view missing or differs: " + role)
        staged.append({"role": role, "source": view, "staged_input": name,
                       "staged_sha256": view["sha256"]})
    template = read(ref(ROOT / "plans/ac6_p1_ac5_geometry.json"))
    plan = copy.deepcopy(template)
    plan["task_id"] = ns["task_id"]
    plan["patches"]["17"]["filename_prefix"] = ns["prefix"]
    for item in staged:
        plan["patches"][historical.NODES[item["role"]]]["image"] = item["staged_input"]
    graph = executor.validate_plan(plan, comfy_root)
    if (plan["workflow"] != historical.WORKFLOW or plan["output_node"] != "17"
            or [v["role"] for v in selected["resolved_views"]] != list(ROLES)
            or graph["10"]["inputs"] != {"front": ["6", 0], "left": ["7", 0],
                                           "back": ["8", 0], "right": ["9", 0]}
            or any(graph[historical.NODES[r]]["class_type"] != "LoadImage" for r in ROLES)
            or graph["17"]["class_type"] != "SaveGLB"):
        raise ValueError("geometry workflow mapping differs")
    return {"classification": "FRESH_GEOMETRY_DISPATCH_CONTRACT", "run_id": selected["run_id"],
            "coverage": coverage_ref, "coverage_config": selected["config"], "source_state": state_ref,
            "controller_input": input_ref, "decision": decision_ref, "view_receipts": receipts,
            "selected_inputs": staged, "workflow": plan["workflow"], "plan": plan,
            "namespace": {key: str(value) if isinstance(value, Path) else value for key, value in ns.items()}}


def intent(dispatch):
    state = read(dispatch["source_state"])
    if persistence.guard_execution(state) != "EXECUTION_ALLOWED":
        raise ValueError("BUDGET_EXHAUSTED")
    before = state["state"]["iteration_count"]
    limit = state["state"]["budget_config"]["max_total_iterations"]
    reserved = copy.deepcopy(state["state"])
    reserved["iteration_count"] = before + 1
    reserved["current_state"] = "EXECUTING"
    controller.validate_state(reserved)
    return {"classification": "FRESH_GEOMETRY_INTENT_CONTRACT", "status": "INTENT_RESERVED",
            "run_id": dispatch["run_id"], "source_state": dispatch["source_state"],
            "decision": dispatch["decision"], "task_id": dispatch["namespace"]["task_id"],
            "plan_sha256": hashlib.sha256(controller.canonical(dispatch["plan"])).hexdigest(),
            "output_prefix": dispatch["namespace"]["prefix"], "iteration_before": before,
            "iteration_after": before + 1, "remaining_after": limit - before - 1,
            "reserved_state": reserved}


def glb(path):
    path = Path(path).resolve()
    with path.open("rb") as stream:
        header = stream.read(12)
    if len(header) != 12 or struct.unpack("<4sII", header) != (b"glTF", 2, path.stat().st_size):
        raise ValueError("GLB header/length differs")
    return ref(path)


def result_snapshot(dispatch, receipt_ref, report_ref, *, output_root=coverage.OUTPUT_ROOT):
    receipt, report = read(receipt_ref), read(report_ref)
    expected = intent(dispatch)
    if receipt != expected:
        raise ValueError("geometry intent differs or already consumed")
    if dispatch["classification"] != "SYNTHETIC_CONTROL_FIXTURE":
        replayed = build_dispatch(dispatch["coverage"], dispatch["source_state"],
                                  dispatch["controller_input"], dispatch["decision"],
                                  dispatch["view_receipts"], allow_consumed=True)
        if replayed != dispatch:
            raise ValueError("fresh dispatch replay differs")
        ns = dispatch["namespace"]
        if (reviewer.checked_ref(receipt_ref) != Path(ns["receipt"]).resolve()
                or reviewer.checked_ref(report_ref) != Path(ns["report"]).resolve()
                or read(ref(ns["plan"])) != dispatch["plan"]):
            raise ValueError("fresh Plan/receipt/Report namespace differs")
    if (report.get("classification") == "SYNTHETIC_CONTROL_FIXTURE"
            and dispatch.get("classification") != "SYNTHETIC_CONTROL_FIXTURE"):
        raise ValueError("synthetic Result in production contract")
    if (report.get("status") != "SUCCESS" or not report.get("prompt_id")
            or not report.get("client_id") or report.get("errors") != []
            or report.get("task_id") != expected["task_id"]
            or report.get("workflow") != dispatch["workflow"]
            or report.get("output_node") != "17" or len(report.get("outputs", [])) != 1
            or report["outputs"][0].get("type") != "geometry"):
        raise ValueError("geometry Result identity differs")
    output = report["outputs"][0]
    prefix = executor.safe_relative(expected["output_prefix"], "output prefix")
    path = Path(output["path"]).resolve()
    if (path.parent != (Path(output_root) / prefix.parent).resolve()
            or not path.name.startswith(prefix.name + "_") or path.suffix.lower() != ".glb"):
        raise ValueError("geometry output namespace differs")
    artifact = glb(path)
    if (output.get("sha256") != artifact["sha256"] or output.get("bytes") != path.stat().st_size
            or output.get("glb_version") != 2 or output.get("declared_length") != path.stat().st_size
            or report.get("run_id", dispatch["run_id"]) != dispatch["run_id"]):
        raise ValueError("geometry GLB or run differs")
    state = copy.deepcopy(expected["reserved_state"])
    state["current_state"] = "GEOMETRY_REVIEW"
    state["latest_artifact"] = artifact
    state["latest_review"] = None
    controller.validate_state(state)
    return {"state_version": "ac6-f2-geometry.0", "classification": dispatch["classification"],
            "run_id": dispatch["run_id"], "source_state": dispatch["source_state"],
            "decision": dispatch["decision"], "intent_receipt": receipt_ref, "result": report_ref,
            "glb": artifact, "prompt_id": report["prompt_id"],
            "pending_semantic_review": True, "remaining_total_iterations": expected["remaining_after"],
            "terminal": False, "state": state}


def evidence_request(dispatch, receipt_ref, report_ref, pending_ref, *,
                     output_root=coverage.OUTPUT_ROOT, evidence_dir=ROOT / "runs",
                     allow_generated=False):
    pending = read(pending_ref)
    if pending != result_snapshot(dispatch, receipt_ref, report_ref, output_root=output_root):
        raise ValueError("stale geometry pending state")
    if (dispatch["classification"] != "SYNTHETIC_CONTROL_FIXTURE"
            and reviewer.checked_ref(pending_ref) != Path(dispatch["namespace"]["state"]).resolve()):
        raise ValueError("fresh geometry state namespace differs")
    if not BLENDER.is_file():
        raise ValueError("Blender renderer unavailable")
    ns = dispatch["namespace"]
    views = [{"role": role, "mesh_axis": axis, "blender_direction": direction,
              "output": str(Path(evidence_dir).resolve() / f"{ns['task_id']}_{role}.png")}
             for role, axis, direction in AXES]
    for item in views:
        if not allow_generated and within(ROOT, item["output"]).exists():
            raise ValueError("evidence output collision")
    if not allow_generated and Path(ns["manifest"]).exists():
        raise ValueError("evidence manifest collision")
    return {"evidence_version": "ac6-f2-geometry.0", "classification": dispatch["classification"],
            "run_id": dispatch["run_id"], "state": pending_ref, "decision": dispatch["decision"],
            "receipt": receipt_ref, "report": report_ref, "source_glb": pending["glb"],
            "source_views": [{"role": v["role"], "path": v["source"]["path"],
                              "sha256": v["source"]["sha256"]} for v in dispatch["selected_inputs"]],
            "renderer": {"name": "Blender", "version": "5.2.0 LTS", "engine": "BLENDER_WORKBENCH",
                         "resolution": [512, 512], "margin": 1.2, "executable": str(BLENDER)},
            "views": views, "manifest": str(ns["manifest"])}


def reviewer_request(dispatch, receipt_ref, report_ref, pending_ref, evidence_ref, manifest_ref,
                     instruction_ref, *, output_root=coverage.OUTPUT_ROOT, evidence_dir=ROOT / "runs",
                     allow_reserved=False):
    evidence = read(evidence_ref)
    if evidence != evidence_request(dispatch, receipt_ref, report_ref, pending_ref,
                                    output_root=output_root, evidence_dir=evidence_dir,
                                    allow_generated=True):
        raise ValueError("stale geometry evidence request")
    if dispatch["classification"] != "SYNTHETIC_CONTROL_FIXTURE":
        ns = dispatch["namespace"]
        if (reviewer.checked_ref(evidence_ref) != Path(ns["evidence_request"]).resolve()
                or reviewer.checked_ref(manifest_ref) != Path(ns["manifest"]).resolve()
                or instruction_ref != ref(REVIEW_INSTRUCTIONS)):
            raise ValueError("fresh evidence namespace differs")
    manifest = read(manifest_ref)
    generated_manifest = manifest.get("evidence_version") == "p2-e1.0"
    manifest_request_valid = (manifest.get("request_sha256") == evidence_ref["sha256"]
                              and Path(manifest.get("request_path", "")).resolve()
                              == reviewer.checked_ref(evidence_ref)) if generated_manifest else (
                                  manifest.get("classification") == "SYNTHETIC_CONTROL_FIXTURE"
                                  and dispatch["classification"] == "SYNTHETIC_CONTROL_FIXTURE"
                                  and manifest.get("request") == evidence_ref)
    if (not manifest_request_valid or manifest.get("source_glb") != evidence["source_glb"]
            or manifest.get("state") != pending_ref or manifest.get("report") != report_ref
            or (generated_manifest and (manifest.get("status") != "SUCCESS"
                                        or manifest.get("source_views") != evidence["source_views"]
                                        or manifest.get("receipt") != receipt_ref))
            or [v.get("role") for v in manifest.get("views", [])] != list(ROLES)):
        raise ValueError("stale geometry evidence manifest")
    artifacts = []
    for source, rendered in zip(evidence["source_views"], manifest["views"]):
        image = ref(rendered["path"])
        if (source["role"] != rendered["role"] or image["sha256"] != rendered["sha256"]
                or Path(rendered["path"]).resolve() != (Path(evidence_dir).resolve() /
                    f"{dispatch['namespace']['task_id']}_{source['role']}.png")):
            raise ValueError("geometry preview identity differs")
        artifacts.extend(({"role": "source_" + source["role"], "path": source["path"],
                           "sha256": source["sha256"], "media_type": "image/png"},
                          {"role": "geometry_" + source["role"], **image, "media_type": "image/png"}))
    ns = dispatch["namespace"]
    if not allow_reserved and (Path(ns["review_result"]).exists() or Path(ns["review_report"]).exists()):
        raise ValueError("REVIEW_ALREADY_RESERVED")
    request = {"request_version": "0.1", "review_id": ns["task_id"], "stage": "GEOMETRY_REVIEW",
               "output_kind": "geometry", "source_result": report_ref,
               "previous_decision": dispatch["decision"], "invocation": receipt_ref,
               "state": pending_ref, "artifacts": artifacts, "instruction_file": instruction_ref,
               "context": {"run_id": dispatch["run_id"], "evidence_manifest": manifest_ref,
                           "glb_sha256": evidence["source_glb"]["sha256"],
                           "review_scope": "GROSS_GEOMETRY_FOUR_VIEW_COMPARISON",
                           "review_identity": {"state_sha256": pending_ref["sha256"],
                                               "result_sha256": report_ref["sha256"],
                                               "manifest_sha256": manifest_ref["sha256"]}}}
    reviewer.validate_request(request)
    return request
