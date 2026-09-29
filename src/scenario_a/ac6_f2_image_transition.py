"""Fresh Scenario A image intent and Result boundary; no service calls."""

import copy
import json
from pathlib import Path
import struct

import codex_to_comfy as executor
import persist_geometry_state as persistence
import pipeline_a_controller as controller
import result_review_adapter as reviewer
import scenario_a_coverage as coverage


ROOT = Path(__file__).resolve().parents[2]


def ref(path):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("fresh artifact must be in repository")
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": reviewer.digest(path)}


def read(ref_value):
    path = reviewer.checked_ref(ref_value)
    return path, json.loads(path.read_text(encoding="utf-8"))


def reservation(source_ref, decision_ref, plan_ref, receipt_path):
    """Build one atomic pre-submit intent record. Re-entry must never resubmit."""
    _, source = read(source_ref)
    _, decision = read(decision_ref)
    _, plan = read(plan_ref)
    state = source["state"]
    controller.validate_state(state)
    run_id = source["run_id"]
    if (state["run_id"] != run_id or decision.get("run_id") != run_id
            or decision.get("controller_decision") != "EXECUTE"
            or decision.get("execution_required") is not True
            or decision.get("next_state") != "EXECUTING"
            or decision.get("return_review_state") != "MULTIVIEW_REVIEW"
            or decision.get("target") not in ("right", "left", "back")
            or persistence.guard_execution(source) != "EXECUTION_ALLOWED"):
        raise ValueError("fresh image intent is not executable")
    if source.get("remaining_total_iterations") != (
            state["budget_config"]["max_total_iterations"] - state["iteration_count"]):
        raise ValueError("durable remaining budget differs")
    role = decision["target"]
    config, _ = coverage.load_config()
    if config["run_id"] != run_id:
        raise ValueError("coverage run identity differs")
    expected_prefix = config["generated_view_contracts"][role]["filename_prefix"]
    if (plan.get("task_id") != run_id + ("-initial-right" if state["current_state"] == "SOURCE_READY" else "-" + role)
            or plan.get("workflow") != config["generated_view_contracts"][role]["workflow"]
            or plan.get("patches", {}).get("13", {}).get("filename_prefix") != expected_prefix):
        raise ValueError("fresh image Plan identity differs")
    executor.validate_plan(plan, executor.DEFAULT_COMFY_ROOT)
    if state["current_state"] == "SOURCE_READY":
        if (role != "right" or source.get("initial_decision") != decision_ref
                or source.get("initial_plan") != plan_ref
                or source.get("pending_initial_execution") is not True
                or source.get("initial_intent_consumed") is not False):
            raise ValueError("initial image lineage differs")
    elif (state["current_state"] != "MULTIVIEW_REVIEW"
          or source.get("pending_semantic_review") is not False
          or state["latest_review"] is None):
        raise ValueError("subsequent image state differs")
    action = decision.get("action")
    if action in controller.ACTION_BUDGET and controller.budget_ready(state, action):
        raise ValueError(controller.budget_ready(state, action))
    expected_receipt = ROOT / "dispatch_receipts" / (decision_ref["sha256"] + ".json")
    if Path(receipt_path).resolve() != expected_receipt:
        raise ValueError("receipt identity differs")
    limit = state["budget_config"]["max_total_iterations"]
    next_iteration = state["iteration_count"] + 1
    if next_iteration > limit:
        raise ValueError("BUDGET_EXHAUSTED")
    reserved = copy.deepcopy(state)
    reserved["current_state"] = "EXECUTING"
    reserved["iteration_count"] = next_iteration
    controller.validate_state(reserved)
    return {
        "receipt_version": "ac6-f2.0", "run_id": run_id, "status": "INTENT_RESERVED",
        "source_state": source_ref, "decision": decision_ref, "plan": plan_ref,
        "role": role, "task_id": plan["task_id"], "output_prefix": expected_prefix,
        "iteration_before": state["iteration_count"], "iteration_after": next_iteration,
        "remaining_after": limit - next_iteration, "reserved_state": reserved,
    }


def result_snapshot(receipt_ref, report_ref):
    """Validate one completed image Report and build its immutable Review-pending state."""
    _, intent = read(receipt_ref)
    _, source = read(intent["source_state"])
    _, decision = read(intent["decision"])
    _, plan = read(intent["plan"])
    _, report = read(report_ref)
    expected = reservation(intent["source_state"], intent["decision"], intent["plan"],
                           reviewer.checked_ref(receipt_ref))
    if intent != expected:
        raise ValueError("intent reservation differs")
    if (source["state"]["current_state"] == "SOURCE_READY"
            and report_ref["path"] != source["planned_report_path"]):
        raise ValueError("initial Result namespace differs")
    role = intent["role"]
    if (report.get("status") != "SUCCESS" or not report.get("prompt_id")
            or not report.get("client_id") or report.get("task_id") != plan["task_id"]
            or report.get("workflow") != plan["workflow"]
            or report.get("output_node") != plan["output_node"]
            or len(report.get("outputs", [])) != 1
            or report["outputs"][0].get("type") != "image"):
        raise ValueError("fresh image Result differs")
    output = report["outputs"][0]
    path = Path(output["path"]).resolve()
    prefix = executor.safe_relative(intent["output_prefix"], "output prefix")
    parent = (coverage.OUTPUT_ROOT / prefix.parent).resolve()
    if (path.parent != parent or not path.name.startswith(prefix.name + "_")
            or path.suffix.lower() != ".png" or not path.is_file()):
        raise ValueError("fresh image output identity differs")
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR":
        raise ValueError("fresh image PNG header differs")
    width, height = struct.unpack(">II", header[16:24])
    if not width or not height:
        raise ValueError("fresh image PNG dimensions invalid")
    if (output.get("width"), output.get("height")) != (width, height):
        raise ValueError("fresh image dimensions differ")
    image = {"path": str(path), "sha256": reviewer.digest(path)}
    state = copy.deepcopy(intent["reserved_state"])
    state["current_state"] = decision["return_review_state"]
    if role not in state["used_views"]:
        state["used_views"].append(role)
    action = decision.get("action")
    if action in ("ADD_VIEW", "REGENERATE_VIEW"):
        state["action_counts"][action] += 1
        state["action_history"].append({"code": action, "target": role,
                                        "blocker_code": None, "region": None})
    state["latest_artifact"] = image
    controller.validate_state(state)
    return {
        "state_version": "ac6-f2.0", "classification": "FRESH_RUNTIME_VALIDATION_RUN",
        "run_id": intent["run_id"], "scenario_id": source["scenario_id"],
        "source_state": intent["source_state"], "decision": intent["decision"],
        "intent_receipt": receipt_ref, "result": report_ref, "generated_role": role,
        "generated_artifact": image, "prompt_id": report["prompt_id"],
        "pending_initial_execution": False, "pending_semantic_review": True,
        "initial_intent_consumed": True,
        "remaining_total_iterations": intent["remaining_after"],
        "terminal": False, "state": state,
    }
