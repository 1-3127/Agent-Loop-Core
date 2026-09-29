"""P3: persist one validated P1 geometry result as a bounded Scenario A state."""

import argparse
import copy
import hashlib
import json
import os
import struct
import sys
import uuid
from pathlib import Path

import codex_to_comfy as executor
import dispatch_geometry as geometry
import pipeline_a_controller as controller
import scenario_a_result_review


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "controller_states/p3_after_p1_geometry.json"
TERMINAL_STATES = {"ACCEPTED", "HUMAN_REQUIRED", "FAILED", "UNRESOLVED"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_ref(ref):
    return geometry.checked_ref(ref)


def read_ref(ref):
    path = checked_ref(ref)
    return path, json.loads(path.read_text(encoding="utf-8"))


def guard_execution(snapshot):
    state = snapshot["state"]
    controller.validate_state(state)
    if snapshot["terminal"] or state["termination"] is not None or state["current_state"] in TERMINAL_STATES:
        return "TERMINAL"
    limit = state["budget_config"].get("max_total_iterations")
    if type(limit) is not int or limit <= 0:
        return "BUDGET_CONFIG_MISSING"
    if state["iteration_count"] >= limit:
        return "BUDGET_EXHAUSTED"
    if snapshot["pending_semantic_review"]:
        return "REVIEW_REQUIRED"
    return "EXECUTION_ALLOWED"


def require_execution_allowed(snapshot):
    outcome = guard_execution(snapshot)
    if outcome != "EXECUTION_ALLOWED":
        raise ValueError(outcome)


def build_snapshot(request, request_path):
    required = {"state_version", "previous_state", "controller_input", "decision",
                "dispatch_request", "plan", "receipt", "result", "fixture", "state_path"}
    if not isinstance(request, dict) or set(request) != required or request["state_version"] != "p3.0":
        raise ValueError("P3 request fields differ")
    if not request_path.resolve().is_relative_to(ROOT):
        raise ValueError("P3 request identity invalid")
    target = (ROOT / executor.safe_relative(request["state_path"], "state_path")).resolve()
    if target != STATE_PATH:
        raise ValueError("unexpected durable state path")
    previous_path, previous = read_ref(request["previous_state"])
    input_path, controller_input = read_ref(request["controller_input"])
    decision_path, decision = read_ref(request["decision"])
    p1_request_path, p1_request = read_ref(request["dispatch_request"])
    plan_path, plan = read_ref(request["plan"])
    receipt_path, receipt = read_ref(request["receipt"])
    report_path, report = read_ref(request["result"])
    fixture_path = checked_ref(request["fixture"])
    if (previous.get("classification") != "DERIVED_FROM_SYNTHETIC_POLICY_FIXTURE"
            or previous.get("state") != controller_input.get("state")
            or previous.get("basis_result") != {
                "path": "runs/ac4_controller_back_report.json",
                "sha256": sha(ROOT / "runs/ac4_controller_back_report.json")}):
        raise ValueError("previous state provenance differs")
    scenario_a_result_review.validate_ac4(
        json.loads((ROOT / "reviewer_requests/ac5_ac4_result.json").read_text(encoding="utf-8")))
    controller.validate_state(previous["state"])
    if (controller.sha256(controller.canonical(controller_input)) != decision.get("input_sha256")
            or controller.decide(controller_input) != decision
            or decision["controller_decision"] != "ADVANCE"
            or decision["reason_code"] != "GEOMETRY_STAGE_READY"
            or decision["execution_required"] is not True
            or decision["next_state"] != "EXECUTING"
            or decision["return_review_state"] != "GEOMETRY_REVIEW"
            or previous["state"]["current_state"] != "MULTIVIEW_REVIEW"
            or previous["state"]["termination"] is not None):
        raise ValueError("previous state/Decision transition differs")
    if (p1_request["controller_decision"] != request["decision"]
            or p1_request["controller_input"] != request["controller_input"]
            or p1_request["plan_path"] != request["plan"]["path"]
            or p1_request["report_path"] != request["result"]["path"]
            or len(p1_request["selected_inputs"]) != 4):
        raise ValueError("P1 request lineage differs")
    selected = p1_request["selected_inputs"]
    if [item["role"] for item in selected] != list(geometry.NODES):
        raise ValueError("P1 four view roles differ")
    for item in selected:
        source, staged = geometry.checked_source(item, decision, controller_input)
        if not staged.is_file() or sha(source) != sha(staged):
            raise ValueError("P1 staged image differs")
        if plan["patches"][geometry.NODES[item["role"]]]["image"] != staged.name:
            raise ValueError("P1 Plan view mapping differs")
    if (plan["task_id"] != p1_request["task_id"] or
            plan["workflow"] != p1_request["workflow"] or plan["output_node"] != "17" or
            plan["patches"]["17"]["filename_prefix"] != p1_request["filename_prefix"]):
        raise ValueError("P1 Plan identity differs")
    executor.validate_plan(plan, geometry.COMFY)
    if (receipt["controller_decision_path"] != request["decision"]["path"]
            or receipt["controller_decision_sha256"] != request["decision"]["sha256"]
            or receipt["controller_input"] != request["controller_input"]
            or Path(receipt["dispatch_request_path"]).resolve() != p1_request_path
            or receipt["dispatch_request_sha256"] != request["dispatch_request"]["sha256"]
            or Path(receipt["plan_path"]).resolve() != plan_path
            or receipt["plan_sha256"] != request["plan"]["sha256"]
            or Path(receipt["execution_report_path"]).resolve() != report_path
            or receipt["execution_report_sha256"] != request["result"]["sha256"]
            or receipt["status"] != receipt["execution_status"] or receipt["status"] != "SUCCESS"
            or receipt["action_consumed"] is not True or
            report["status"] != "SUCCESS" or not report.get("prompt_id") or
            receipt["prompt_id"] != report["prompt_id"] or
            receipt["client_id"] != report["client_id"] or
            receipt["outputs"] != report["outputs"] or len(report["outputs"]) != 1):
        raise ValueError("P1 receipt/Report lineage differs")
    artifact = report["outputs"][0]
    path = Path(artifact["path"]).resolve()
    output_root = (geometry.COMFY / "work/output").resolve()
    if (artifact["type"] != "geometry" or not path.is_relative_to(output_root)
            or path.suffix.lower() != ".glb" or not path.is_file()
            or sha(path) != artifact["sha256"] or sha(fixture_path) != artifact["sha256"]
            or artifact["sha256"] != request["fixture"]["sha256"]):
        raise ValueError("P1 GLB identity differs")
    data = path.read_bytes()
    if (len(data) != artifact["bytes"] or len(data) < 20 or
            struct.unpack_from("<4sII", data) != (b"glTF", 2, len(data))):
        raise ValueError("P1 GLB header/size differs")
    before = previous["state"]
    limit = before["budget_config"].get("max_total_iterations")
    if type(limit) is not int or limit <= 0 or before["iteration_count"] >= limit:
        raise ValueError("previous global execution budget exhausted")
    after = copy.deepcopy(before)
    after["current_state"] = "GEOMETRY_REVIEW"
    after["iteration_count"] += 1
    after["latest_artifact"] = {"path": path.as_posix(), "sha256": artifact["sha256"]}
    after["latest_review"] = None
    after["termination"] = None
    controller.validate_state(after)
    snapshot = {
        "state_version": "p3.0",
        "classification": "RUNTIME_TRANSITION_FROM_DERIVED_SYNTHETIC_FIXTURE",
        "run_id": after["run_id"],
        "previous_state": request["previous_state"],
        "controller_input": request["controller_input"],
        "decision": request["decision"],
        "dispatch_request": request["dispatch_request"],
        "plan": request["plan"],
        "consumed_receipt": request["receipt"],
        "last_result": request["result"],
        "last_artifact": {"path": path.as_posix(), "sha256": artifact["sha256"]},
        "fixture": request["fixture"],
        "transition": {
            "from": before["current_state"], "to": after["current_state"],
            "reason": "P1_GEOMETRY_EXECUTION_SUCCESS",
            "consumed_receipt_sha256": request["receipt"]["sha256"],
            "prompt_id": report["prompt_id"],
        },
        "pending_semantic_review": True,
        "terminal": False,
        "remaining_total_iterations": limit - after["iteration_count"],
        "state": after,
    }
    return target, snapshot


def encoded(snapshot):
    return (json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def apply_once(target, snapshot):
    if target.exists():
        if target.read_bytes() != encoded(snapshot):
            raise ValueError("existing durable state differs")
        return "ALREADY_APPLIED"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded(snapshot))
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError:
            if target.read_bytes() != encoded(snapshot):
                raise ValueError("concurrent durable state differs")
            return "ALREADY_APPLIED"
    finally:
        temporary.unlink(missing_ok=True)
    if target.read_bytes() != encoded(snapshot):
        raise ValueError("durable state verification differs")
    return "APPLIED"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        request = json.loads(args.request.read_text(encoding="utf-8"))
        target, snapshot = build_snapshot(request, args.request)
        outcome = apply_once(target, snapshot) if args.apply else "P3_PREFLIGHT_VALID"
        print(f"{outcome} state={target} iteration={snapshot['state']['iteration_count']} "
              f"remaining={snapshot['remaining_total_iterations']} guard={guard_execution(snapshot)}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"P3_BLOCKED {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
