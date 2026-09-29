"""A-C1: decide one Pipeline A policy transition without dispatching work."""

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from pathlib import Path

from validate_adaptive_decision import validate as validate_adaptive
from validate_review import validate as validate_review
from reviewer_adapter import validate_request as validate_reviewer_request, validate_result as validate_reviewer_result
from result_review_adapter import checked_invocation as checked_result_review


ROOT = Path(__file__).resolve().parents[2]
STATES = {"SOURCE_READY", "MULTIVIEW_REVIEW", "GEOMETRY_REVIEW", "REFINEMENT_REVIEW", "EXECUTING", "ACCEPTED", "HUMAN_REQUIRED", "FAILED", "UNRESOLVED"}
REVIEW_STATES = {"MULTIVIEW_REVIEW", "GEOMETRY_REVIEW", "REFINEMENT_REVIEW"}
ACTIONS = {"ADD_VIEW", "REGENERATE_VIEW", "REBUILD_GEOMETRY", "REFINE_GEOMETRY"}
BUDGET_KEYS = {"max_total_iterations", "max_view_regenerations", "max_added_views", "max_geometry_rebuilds", "max_refinements", "max_repeated_blocker_actions"}
COUNT_KEYS = {"ADD_VIEW", "REGENERATE_VIEW", "REBUILD_GEOMETRY", "REFINE_GEOMETRY"}
ACTION_BUDGET = {"ADD_VIEW": "max_added_views", "REGENERATE_VIEW": "max_view_regenerations", "REBUILD_GEOMETRY": "max_geometry_rebuilds", "REFINE_GEOMETRY": "max_refinements"}
STATE_FIELDS = {"run_id", "current_state", "iteration_count", "used_views", "action_counts", "action_history", "budget_config", "capabilities", "refinement", "latest_artifact", "latest_review", "termination"}
NORMAL_FIELDS = {"code", "target", "blocker_code", "region", "coverage_sufficient", "reconstruction_suspected", "author"}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def project_path(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError("source path must be project-relative")
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("source path is missing or outside project")
    return path


def load_signal(source):
    if not isinstance(source, dict) or "kind" not in source:
        raise ValueError("source reference is invalid")
    reviewer_fields = {"kind", "path", "sha256", "request_path", "request_sha256", "invocation_report_path", "invocation_report_sha256"}
    if set(source) != (reviewer_fields if source["kind"] in ("REVIEWER_RESULT", "RESULT_REVIEW") else {"kind", "path", "sha256"}):
        raise ValueError("source reference fields differ")
    if source["kind"] not in ("ADAPTIVE_DECISION", "REVIEW", "EXECUTION_REPORT", "REVIEWER_RESULT", "RESULT_REVIEW"):
        raise ValueError("source kind is unsupported")
    path = project_path(source["path"])
    raw = path.read_bytes()
    if not re.fullmatch(r"[0-9a-f]{64}", str(source["sha256"])) or sha256(raw) != source["sha256"]:
        raise ValueError("source hash differs")
    item = json.loads(raw)
    if source["kind"] == "RESULT_REVIEW":
        request, review = checked_result_review(source)
        return {"kind": "RESULT_REVIEW", "decision": review["verdict"], "target": review["suggested_action"]["target"],
                "action_code": review["suggested_action"]["code"], "stage": request["stage"],
                "artifact_type": request["output_kind"], "state_ref": request["state"], "promoted": False}
    if source["kind"] == "REVIEWER_RESULT":
        request_path = project_path(source["request_path"])
        report_path = project_path(source["invocation_report_path"])
        if sha256(request_path.read_bytes()) != source["request_sha256"] or sha256(report_path.read_bytes()) != source["invocation_report_sha256"]:
            raise ValueError("reviewer lineage hash differs")
        request = json.loads(request_path.read_text(encoding="utf-8"))
        validate_reviewer_request(request)
        validate_reviewer_result(item, request)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if (report.get("invocation_status") != "SUCCESS" or report.get("schema_valid") is not True or
                report.get("task_identity_match") is not True or report.get("artifact_identity_match") is not True or
                report.get("task_id") != item["task_id"] or report.get("request_sha256") != source["request_sha256"] or
                (ROOT / report.get("result_path", "")).resolve() != path or report.get("semantic_decision") != item["decision"] or
                report.get("normalized_action") != item["controller_action"]):
            raise ValueError("reviewer invocation report differs")
        return {"kind": "REVIEWER_RESULT", "decision": item["decision"], "target": item["controller_action"]["target"],
                "action_code": item["controller_action"]["code"], "stage": item["stage"], "artifact_type": "image", "promoted": False}
    if source["kind"] == "ADAPTIVE_DECISION":
        validate_adaptive(item)
        return {"kind": "ADAPTIVE_DECISION", "decision": item["decision"], "target": None if item["requested_view"] is None else item["requested_view"]["view_id"], "existing_views": sorted({v["view_id"] for v in item["generated_views"]}), "blocker_code": item["decision_id"]}
    if source["kind"] == "REVIEW":
        report = validate_review(item)
        output_types = {out.get("type") for out in report["outputs"]}
        if len(output_types) != 1:
            raise ValueError("Review outputs have mixed types")
        return {"kind": "REVIEW", "decision": item["decision"], "target": None, "existing_views": [], "blocker_code": None, "artifact_type": output_types.pop(), "promoted": item.get("promotion_comparison", {}).get("canonical_geometry") == "PROMOTED"}
    if item.get("schema_version") != "0.1" or item.get("status") not in ("SUCCESS", "FAILED", "UNRESOLVED") or not isinstance(item.get("task_id"), str) or not isinstance(item.get("client_id"), str):
        raise ValueError("Execution Report is invalid")
    return {"kind": "EXECUTION_REPORT", "decision": item["status"], "target": None, "existing_views": [], "blocker_code": None, "prompt_id": item.get("prompt_id"), "client_id": item["client_id"]}


def validate_state(state):
    if not isinstance(state, dict) or set(state) != STATE_FIELDS:
        raise ValueError("controller state fields differ")
    if not isinstance(state["run_id"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", state["run_id"]):
        raise ValueError("invalid run_id")
    if state["current_state"] not in STATES or type(state["iteration_count"]) is not int or state["iteration_count"] < 0:
        raise ValueError("invalid state or iteration_count")
    views = state["used_views"]
    if not isinstance(views, list) or any(not isinstance(v, str) or not v for v in views) or len(views) != len(set(views)):
        raise ValueError("used_views must be unique")
    counts = state["action_counts"]
    if not isinstance(counts, dict) or set(counts) != COUNT_KEYS or any(type(v) is not int or v < 0 for v in counts.values()):
        raise ValueError("invalid action_counts")
    history = state["action_history"]
    if not isinstance(history, list) or any(not isinstance(h, dict) or set(h) != {"code", "target", "blocker_code", "region"} or h["code"] not in ACTIONS for h in history):
        raise ValueError("invalid action_history")
    if not isinstance(state["budget_config"], dict) or not set(state["budget_config"]).issubset(BUDGET_KEYS):
        raise ValueError("invalid budget_config")
    caps = state["capabilities"]
    if not isinstance(caps, dict) or set(caps) != {"supported_views", "refinement_transition"} or not isinstance(caps["supported_views"], list) or any(not isinstance(v, str) for v in caps["supported_views"]):
        raise ValueError("invalid capabilities")
    if caps["refinement_transition"] is not None and caps["refinement_transition"] != [128, 192]:
        raise ValueError("unvalidated refinement capability")
    ref = state["refinement"]
    if not isinstance(ref, dict) or set(ref) != {"current_octree", "target_octree"} or any(v is not None and (type(v) is not int or v <= 0) for v in ref.values()):
        raise ValueError("invalid refinement state")
    for name in ("latest_artifact", "latest_review"):
        item = state[name]
        if item is not None and (not isinstance(item, dict) or set(item) != {"path", "sha256"}):
            raise ValueError(f"invalid {name}")
    if state["termination"] is not None and not isinstance(state["termination"], str):
        raise ValueError("invalid termination")


def result(request, controller_decision, next_state, reason_code, action=None, target=None, termination=None, execution_required=False):
    return {"schema_version": "0.1", "policy_version": "D-016/A-C1", "run_id": request["state"]["run_id"], "input_sha256": sha256(canonical(request)), "source": request["source"], "controller_decision": controller_decision, "action": action, "target": target, "next_state": next_state, "termination": termination, "reason_code": reason_code, "execution_required": execution_required}


def stop(request, next_state, reason, termination=None):
    return result(request, "STOP", next_state, reason, termination=termination or reason)


def budget_ready(state, action):
    limits = state["budget_config"]
    if set(limits) != BUDGET_KEYS or any(type(v) is not int or v <= 0 for v in limits.values()):
        return "BUDGET_CONFIG_MISSING"
    if state["iteration_count"] >= limits["max_total_iterations"] or state["action_counts"][action] >= limits[ACTION_BUDGET[action]]:
        return "BUDGET_EXHAUSTED"
    return None


def action_gate(request, signal, action):
    state = request["state"]
    current = state["current_state"]
    code = action["code"]
    target = action["target"]
    if code not in ACTIONS:
        return stop(request, "HUMAN_REQUIRED", "UNSUPPORTED_ACTION")
    if code in ("ADD_VIEW", "REGENERATE_VIEW"):
        if current not in ("MULTIVIEW_REVIEW", "GEOMETRY_REVIEW"):
            return stop(request, "HUMAN_REQUIRED", "INVALID_STATE_ACTION")
        if not isinstance(target, str) or not target:
            return stop(request, "HUMAN_REQUIRED", "TARGET_REQUIRED")
        if target not in state["capabilities"]["supported_views"]:
            return stop(request, "HUMAN_REQUIRED", "CAPABILITY_MISSING")
        if code == "ADD_VIEW" and target in state["used_views"]:
            return stop(request, "HUMAN_REQUIRED", "DUPLICATE_VIEW")
        if code == "REGENERATE_VIEW" and target not in state["used_views"]:
            return stop(request, "HUMAN_REQUIRED", "REGENERATION_TARGET_MISSING")
        if current == "GEOMETRY_REVIEW" and code == "ADD_VIEW" and not action["region"]:
            return stop(request, "HUMAN_REQUIRED", "MISSING_COVERAGE_REGION")
    elif code == "REBUILD_GEOMETRY":
        if current != "GEOMETRY_REVIEW":
            return stop(request, "HUMAN_REQUIRED", "INVALID_STATE_ACTION")
        if action["coverage_sufficient"] is not True or action["reconstruction_suspected"] is not True:
            return stop(request, "HUMAN_REQUIRED", "REBUILD_GATE_NOT_MET")
    else:
        if current != "GEOMETRY_REVIEW" or signal["decision"] != "PASS":
            return stop(request, "HUMAN_REQUIRED", "INVALID_STATE_ACTION")
        if state["capabilities"]["refinement_transition"] != [128, 192] or state["refinement"] != {"current_octree": 128, "target_octree": 192}:
            return stop(request, "HUMAN_REQUIRED", "REFINEMENT_UNVALIDATED")
    budget_error = budget_ready(state, code)
    if budget_error:
        return stop(request, "HUMAN_REQUIRED", budget_error)
    key = {k: action[k] for k in ("code", "target", "blocker_code", "region")}
    repeated = 0
    for old in reversed(state["action_history"]):
        if old != key:
            break
        repeated += 1
    if repeated >= state["budget_config"]["max_repeated_blocker_actions"]:
        return stop(request, "HUMAN_REQUIRED", "NO_PROGRESS")
    if code != "REFINE_GEOMETRY" and action["blocker_code"] is None and not (
            code == "ADD_VIEW" and current == "MULTIVIEW_REVIEW" and signal["kind"] == "REVIEWER_RESULT"):
        return stop(request, "HUMAN_REQUIRED", "BLOCKER_ID_REQUIRED")
    next_review = "GEOMETRY_REVIEW" if code == "REBUILD_GEOMETRY" else "REFINEMENT_REVIEW" if code == "REFINE_GEOMETRY" else "MULTIVIEW_REVIEW"
    return result(request, "EXECUTE", "EXECUTING", "ACTION_ALLOWED", action=code, target=target, execution_required=True) | {"return_review_state": next_review}


def decide(request):
    if not isinstance(request, dict) or set(request) != {"schema_version", "state", "source", "normalized_action"} or request["schema_version"] != "0.1":
        raise ValueError("controller input schema differs")
    validate_state(request["state"])
    state = request["state"]
    signal = load_signal(request["source"])
    normalized = request["normalized_action"]
    if normalized is not None and (not isinstance(normalized, dict) or set(normalized) != NORMAL_FIELDS or normalized["author"] != "Codex" or any(normalized[k] is not None and not isinstance(normalized[k], str) for k in ("code", "target", "blocker_code", "region")) or any(normalized[k] is not None and type(normalized[k]) is not bool for k in ("coverage_sufficient", "reconstruction_suspected"))):
        raise ValueError("normalized action contract differs")
    current = state["current_state"]
    if current in ("ACCEPTED", "HUMAN_REQUIRED", "FAILED"):
        return stop(request, current, "ALREADY_TERMINAL")
    if signal["kind"] == "EXECUTION_REPORT":
        if current not in ("EXECUTING", "UNRESOLVED"):
            return stop(request, "HUMAN_REQUIRED", "INVALID_STATE_SOURCE")
        if signal["decision"] == "UNRESOLVED":
            return result(request, "RECOVER", "UNRESOLVED", "RECOVER_EXISTING_EXECUTION")
        if signal["decision"] == "FAILED":
            return stop(request, "FAILED", "EXECUTION_FAILED")
        return stop(request, "HUMAN_REQUIRED", "REVIEW_REQUIRED")
    if current not in REVIEW_STATES:
        return stop(request, "HUMAN_REQUIRED", "INVALID_STATE_SOURCE")
    if signal["kind"] == "ADAPTIVE_DECISION" and current != "MULTIVIEW_REVIEW":
        return stop(request, "HUMAN_REQUIRED", "INVALID_STATE_SOURCE")
    if signal["kind"] in ("REVIEW", "REVIEWER_RESULT", "RESULT_REVIEW"):
        expected_type = "image" if current == "MULTIVIEW_REVIEW" else "geometry"
        if signal["artifact_type"] != expected_type or (signal["kind"] in ("REVIEWER_RESULT", "RESULT_REVIEW") and signal["stage"] != current):
            return stop(request, "HUMAN_REQUIRED", "INVALID_STATE_SOURCE")
        if state["latest_review"] is not None and state["latest_review"] != {"path": request["source"]["path"], "sha256": request["source"]["sha256"]}:
            return stop(request, "HUMAN_REQUIRED", "SOURCE_STATE_CONFLICT")
    if signal["kind"] == "ADAPTIVE_DECISION":
        if normalized is not None or not set(signal["existing_views"]).issubset(state["used_views"]):
            return stop(request, "HUMAN_REQUIRED", "SOURCE_STATE_CONFLICT")
    if signal["kind"] in ("REVIEWER_RESULT", "RESULT_REVIEW"):
        if signal["decision"] == "HUMAN_REQUIRED":
            return stop(request, "HUMAN_REQUIRED", "REVIEWER_UNCERTAIN")
        if signal["decision"] == "PASS" and normalized is not None:
            return stop(request, "HUMAN_REQUIRED", "PASS_ACTION_CONFLICT")
        if signal["decision"] == "REVISE" and ((signal["kind"] == "REVIEWER_RESULT" and normalized is None) or
                (normalized is not None and (normalized["code"] != signal["action_code"] or normalized["target"] != signal["target"]))):
            return stop(request, "HUMAN_REQUIRED", "SOURCE_ACTION_CONFLICT")
        if signal["kind"] == "RESULT_REVIEW" and normalized is not None:
            return stop(request, "HUMAN_REQUIRED", "ACTION_NORMALIZATION_REQUIRED")
    if signal["decision"] == "PASS":
        if normalized is not None:
            return stop(request, "HUMAN_REQUIRED", "PASS_ACTION_CONFLICT")
        if current == "REFINEMENT_REVIEW":
            if signal["kind"] != "REVIEW" or not signal["promoted"]:
                return stop(request, "HUMAN_REQUIRED", "FINAL_REVIEW_REQUIRED")
            return stop(request, "ACCEPTED", "PIPELINE_A_ACCEPTED", "ACCEPTED")
        if current == "GEOMETRY_REVIEW":
            if state["refinement"]["target_octree"] is None or state["refinement"]["target_octree"] == state["refinement"]["current_octree"]:
                return stop(request, "ACCEPTED", "BASELINE_ACCEPTED", "ACCEPTED")
            action = {"code": "REFINE_GEOMETRY", "target": None, "blocker_code": None, "region": None, "coverage_sufficient": None, "reconstruction_suspected": None}
            return action_gate(request, signal, action)
        return result(request, "ADVANCE", "EXECUTING", "GEOMETRY_STAGE_READY", execution_required=True) | {"return_review_state": "GEOMETRY_REVIEW"}
    if signal["kind"] == "ADAPTIVE_DECISION":
        if signal["decision"] not in ("ADD_VIEW", "REGENERATE_VIEW"):
            return stop(request, "HUMAN_REQUIRED", "UNSUPPORTED_ACTION")
        action = {"code": signal["decision"], "target": signal["target"], "blocker_code": signal["blocker_code"], "region": None, "coverage_sufficient": None, "reconstruction_suspected": None}
    else:
        if normalized is None:
            return stop(request, "HUMAN_REQUIRED", "ACTION_NORMALIZATION_REQUIRED")
        action = normalized
    return action_gate(request, signal, action)


def write_decision(path, decision):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError("decision already exists; refusing overwrite")
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(decision, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            raise ValueError("decision appeared during write; refusing overwrite")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        request = json.loads(args.input.read_text(encoding="utf-8"))
        decision = decide(request)
        write_decision(args.output, decision)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"INVALID {exc}", file=sys.stderr)
        return 1
    print(f"{decision['controller_decision']} next={decision['next_state']} reason={decision['reason_code']} output={args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
