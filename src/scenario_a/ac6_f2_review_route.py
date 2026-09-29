"""Dry fresh image Review attachment and Controller/F2A routing contracts."""

import copy
import json
from pathlib import Path

import ac6_f2_image_transition as image_transition
import persist_geometry_state as persistence
import pipeline_a_controller as controller
import result_review_adapter as reviewer
import scenario_a_coverage as coverage


ROOT = Path(__file__).resolve().parents[2]
INSTRUCTIONS = ROOT / "reviewer_requests/ac6_f2_partial_image_instructions.md"


def read(ref):
    path = reviewer.checked_ref(ref)
    return json.loads(path.read_text(encoding="utf-8"))


def review_source(request_ref, result_ref, report_ref):
    return {"kind": "RESULT_REVIEW", "path": result_ref["path"], "sha256": result_ref["sha256"],
            "request_path": request_ref["path"], "request_sha256": request_ref["sha256"],
            "invocation_report_path": report_ref["path"],
            "invocation_report_sha256": report_ref["sha256"]}


def build_request(pending_ref):
    """Use the existing two-image Review 0.3 envelope for the current view."""
    pending = read(pending_ref)
    state = pending["state"]
    controller.validate_state(state)
    config, initial = coverage.load_config()
    role = pending["generated_role"]
    receipt = read(pending["intent_receipt"])
    report = read(pending["result"])
    decision = read(pending["decision"])
    source_state = read(pending["source_state"])
    plan = read(receipt["plan"])
    artifact = pending["generated_artifact"]
    if (pending.get("state_version") != "ac6-f2.0"
            or pending.get("classification") != "FRESH_RUNTIME_VALIDATION_RUN"
            or pending["run_id"] != config["run_id"] or state["run_id"] != config["run_id"]
            or source_state["run_id"] != pending["run_id"]
            or pending["scenario_id"] != initial["scenario_id"]
            or role not in config["generated_view_contracts"]
            or state["current_state"] != "MULTIVIEW_REVIEW"
            or state["latest_artifact"] != artifact or role not in state["used_views"]
            or state["latest_review"] is not None or state["termination"] is not None
            or pending["pending_semantic_review"] is not True or pending["terminal"] is not False
            or pending["remaining_total_iterations"] != state["budget_config"]["max_total_iterations"] - state["iteration_count"]
            or receipt["run_id"] != pending["run_id"] or receipt["role"] != role
            or receipt["status"] != "INTENT_RESERVED" or receipt["source_state"] != pending["source_state"]
            or receipt["decision"] != pending["decision"]
            or receipt["iteration_before"] != source_state["state"]["iteration_count"]
            or receipt["iteration_after"] != receipt["iteration_before"] + 1
            or receipt["iteration_after"] != state["iteration_count"]
            or receipt["remaining_after"] != pending["remaining_total_iterations"]
            or receipt["reserved_state"]["iteration_count"] != state["iteration_count"]
            or receipt["reserved_state"]["current_state"] != "EXECUTING"
            or decision["run_id"] != pending["run_id"] or decision["target"] != role
            or decision["return_review_state"] != "MULTIVIEW_REVIEW"
            or report["status"] != "SUCCESS" or report["prompt_id"] != pending["prompt_id"]
            or report["task_id"] != receipt["task_id"] or plan["task_id"] != receipt["task_id"]
            or report["workflow"] != plan["workflow"]
            or report["output_node"] != plan["output_node"]
            or len(report["outputs"]) != 1
            or report["outputs"][0]["type"] != "image"
            or Path(report["outputs"][0]["path"]).resolve() != Path(artifact["path"]).resolve()
            or reviewer.digest(artifact["path"]) != artifact["sha256"]):
        raise ValueError("fresh pending image/Result lineage differs")
    source = initial["source_artifact"]
    reviewer.checked_ref(source)
    request = {
        "request_version": "0.1",
        "review_id": f"{pending['run_id']}-{role}-{state['iteration_count']}",
        "stage": "MULTIVIEW_REVIEW", "output_kind": "image",
        "source_result": pending["result"], "previous_decision": pending["decision"],
        "invocation": pending["intent_receipt"], "state": pending_ref,
        "artifacts": [
            {"role": "generated_output", **artifact, "media_type": "image/png"},
            {"role": "source_reference", **source, "media_type": "image/png"},
        ],
        "instruction_file": image_transition.ref(INSTRUCTIONS),
        "context": {"run_id": pending["run_id"], "generated_role": role,
                    "source_state": pending["source_state"],
                    "coverage_config": coverage.reference(coverage.CONFIG),
                    "review_scope": "CURRENT_GENERATED_VIEW_ONLY"},
    }
    reviewer.validate_request(request)
    return request


def checked_review(request_ref, result_ref, report_ref, allow_control_fixture=False):
    source = review_source(request_ref, result_ref, report_ref)
    request, result = reviewer.checked_invocation(source)
    report = read(report_ref)
    if report.get("classification") == "SYNTHETIC_CONTROL_FIXTURE":
        if (not allow_control_fixture or report.get("reviewer_mode") != "CURRENT_SESSION"
                or report.get("reviewer_process_started") is not False
                or report.get("external_transfer_performed") is not False):
            raise ValueError("synthetic Review cannot enter production path")
    elif (report.get("reviewer_mode") != "CODEX_CLI"
          or report.get("reviewer_process_started") is not True
          or report.get("process_exit_code") != 0):
        raise ValueError("automatic Reviewer invocation proof missing")
    return source, request, result


def build_attachment(pending_ref, request_ref, result_ref, report_ref, allow_control_fixture=False):
    before = read(pending_ref)
    expected_request = build_request(pending_ref)
    source, request, result = checked_review(request_ref, result_ref, report_ref, allow_control_fixture)
    if request != expected_request or request["state"] != pending_ref:
        raise ValueError("Review request does not match pending Result state")
    after = copy.deepcopy(before)
    after["state_version"] = "ac6-f2-review.0"
    after["review_source_state"] = pending_ref
    after["review_request"] = request_ref
    after["review_invocation"] = report_ref
    after["review"] = {"path": source["path"], "sha256": source["sha256"]}
    after["review_verdict"] = result["verdict"]
    after["pending_semantic_review"] = False
    after["state"]["latest_review"] = after["review"]
    controller.validate_state(after["state"])
    if (after["state"]["current_state"] != "MULTIVIEW_REVIEW"
            or after["state"]["latest_artifact"] != before["state"]["latest_artifact"]
            or after["state"]["iteration_count"] != before["state"]["iteration_count"]
            or after["state"]["action_counts"] != before["state"]["action_counts"]
            or after["state"]["action_history"] != before["state"]["action_history"]
            or after["remaining_total_iterations"] != before["remaining_total_iterations"]
            or after["terminal"] is not False):
        raise ValueError("Review attachment changed execution state")
    return after


def build_controller(attached_ref, allow_control_fixture=False):
    attached = read(attached_ref)
    if attached.get("state_version") != "ac6-f2-review.0":
        raise ValueError("Review-attached state version differs")
    expected = build_attachment(attached["review_source_state"], attached["review_request"],
                                attached["review"], attached["review_invocation"], allow_control_fixture)
    if attached != expected:
        raise ValueError("latest Review-attached state differs")
    source = review_source(attached["review_request"], attached["review"], attached["review_invocation"])
    signal = controller.load_signal(source)
    if (signal["state_ref"] != attached["review_source_state"]
            or signal["decision"] != attached["review_verdict"]
            or signal["stage"] != "MULTIVIEW_REVIEW"
            or signal["artifact_type"] != "image"):
        raise ValueError("Controller Review provenance differs")
    item = {"schema_version": "0.1", "state": attached["state"],
            "source": source, "normalized_action": None}
    decision = controller.decide(item)
    if decision["run_id"] != attached["run_id"]:
        raise ValueError("Controller run identity differs")
    return item, decision


def route(coverage_ref, attached_ref, input_ref, decision_ref,
          *, output_root=coverage.OUTPUT_ROOT, allow_control_fixture=False):
    """Only Controller geometry ADVANCE enters F2A; preserve all other Decisions."""
    item, expected = build_controller(attached_ref, allow_control_fixture)
    if read(input_ref) != item or read(decision_ref) != expected:
        raise ValueError("Controller Input/Decision differs from actual policy")
    if (expected["controller_decision"] == "ADVANCE"
            and expected["reason_code"] == "GEOMETRY_STAGE_READY"
            and expected["execution_required"] is True):
        return coverage.route_after_controller(coverage_ref, attached_ref, input_ref,
                                               decision_ref, output_root=output_root)
    if expected["execution_required"] and persistence.guard_execution(read(attached_ref)) != "EXECUTION_ALLOWED":
        raise ValueError("BUDGET_EXHAUSTED")
    return "CONTROLLER_DECISION_PRESERVED", expected
