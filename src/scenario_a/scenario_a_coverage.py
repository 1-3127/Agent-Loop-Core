"""Validate fresh Scenario A view identities and gate geometry readiness."""

import hashlib
import json
from pathlib import Path

import codex_to_comfy as executor
import persist_geometry_state as persistence
import pipeline_a_controller as controller
import result_review_adapter as reviewer


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "coverage_configs/ac6_f2a_validation_20260929_01.json"
INITIAL_COVERAGE = ROOT / "coverage_states/ac6_f2a_initial_20260929_01.json"
OUTPUT_ROOT = (executor.DEFAULT_COMFY_ROOT / "work/output").resolve()
ROLE_NODES = {"front": "1", "left": "2", "back": "3", "right": "4"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reference(path):
    path = Path(path).resolve()
    return {"path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
            "sha256": sha(path)}


def load_config(config_path=CONFIG):
    config_path = Path(config_path).resolve()
    if config_path != CONFIG or not config_path.is_file():
        raise ValueError("coverage config identity differs")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    expected = {"coverage_version", "run_id", "bootstrap_request", "initial_state",
                "initial_decision", "geometry_workflow", "selection_evidence", "required_roles",
                "acquisition_order", "generated_view_contracts", "selection_policy"}
    if set(config) != expected or config["coverage_version"] != "ac6-f2a.0":
        raise ValueError("coverage config fields differ")
    request = json.loads(reviewer.checked_ref(config["bootstrap_request"]).read_text(encoding="utf-8"))
    initial = json.loads(reviewer.checked_ref(config["initial_state"]).read_text(encoding="utf-8"))
    decision = json.loads(reviewer.checked_ref(config["initial_decision"]).read_text(encoding="utf-8"))
    workflow = json.loads(reviewer.checked_ref(config["geometry_workflow"]).read_text(encoding="utf-8"))
    for item in config["selection_evidence"]:
        reviewer.checked_ref(item)
    if (config["run_id"] != request["run_id"] or initial["run_id"] != config["run_id"]
            or decision["run_id"] != config["run_id"]
            or initial["bootstrap_request"] != config["bootstrap_request"]
            or initial["initial_decision"] != config["initial_decision"]
            or initial["source_artifact"]["sha256"] != request["source"]["sha256"]
            or config["required_roles"] != list(ROLE_NODES)
            or config["acquisition_order"] != ["right", "left", "back"]
            or config["selection_policy"] != "EXPLICIT_VALIDATION_RUN_SEQUENCE_FROM_M2_M4B_M4C_M4D"
            or set(config["generated_view_contracts"]) != {"right", "left", "back"}):
        raise ValueError("fresh coverage authority differs")
    if any(workflow[node]["class_type"] != "LoadImage" for node in ROLE_NODES.values()):
        raise ValueError("geometry role mapping differs")
    for role, contract in config["generated_view_contracts"].items():
        if set(contract) != {"workflow", "filename_prefix"}:
            raise ValueError("generated view contract differs")
        prefix = executor.safe_relative(contract["filename_prefix"], "filename_prefix")
        if prefix.as_posix() != "codex_to_comfy/ac6_f1_20260929_01_" + role:
            raise ValueError("fresh output namespace differs")
        if role == "right" and contract["workflow"] != "workflows/02_Image_to_Multiview/Qwen2509_Multiangle_RTX4060_api.json":
            raise ValueError("initial workflow differs")
        workflow_path = (executor.DEFAULT_COMFY_ROOT / contract["workflow"]).resolve()
        if not workflow_path.is_file():
            raise ValueError("view workflow missing: " + role)
        graph = json.loads(workflow_path.read_text(encoding="utf-8"))
        if graph["1"]["class_type"] != "LoadImage" or graph["13"]["class_type"] != "SaveImage":
            raise ValueError("view workflow node mapping differs")
    if initial["planned_output_prefix"] != config["generated_view_contracts"]["right"]["filename_prefix"]:
        raise ValueError("F1 initial output prefix differs")
    return config, initial


def evaluate(generated, config=None, output_root=OUTPUT_ROOT):
    authoritative, initial = load_config()
    if config is not None and config != authoritative:
        raise ValueError("coverage configuration differs")
    config = authoritative
    if not isinstance(generated, list):
        raise ValueError("generated view records required")
    front = initial["source_artifact"]
    front_path = Path(front["path"]).resolve()
    if not front_path.is_file() or sha(front_path) != front["sha256"]:
        raise ValueError("front source path/hash differs")
    views = {"front": {"role": "front", "kind": "SOURCE", "run_id": config["run_id"],
                       "path": str(front_path), "sha256": front["sha256"],
                       "provenance": initial["bootstrap_request"]}}
    output_root = Path(output_root).resolve()
    for record in generated:
        fields = {"role", "kind", "run_id", "path", "sha256", "decision", "report"}
        if not isinstance(record, dict) or set(record) != fields:
            raise ValueError("generated view identity fields differ")
        role = record["role"]
        if role not in config["generated_view_contracts"] or record["kind"] != "GENERATED" or record["run_id"] != config["run_id"]:
            raise ValueError("generated view run/role differs")
        path = Path(record["path"]).resolve()
        prefix = executor.safe_relative(config["generated_view_contracts"][role]["filename_prefix"], "filename_prefix")
        expected_parent = (output_root / prefix.parent).resolve()
        if (path.parent != expected_parent or not path.name.startswith(prefix.name + "_")
                or path.suffix.lower() != ".png" or not path.is_file()
                or sha(path) != record["sha256"]):
            raise ValueError("fresh generated path/hash differs: " + role)
        decision = json.loads(reviewer.checked_ref(record["decision"]).read_text(encoding="utf-8"))
        report = json.loads(reviewer.checked_ref(record["report"]).read_text(encoding="utf-8"))
        if role != "right":
            source = decision.get("source")
            if (decision.get("policy_version") != "D-016/SCENARIO_A_COVERAGE"
                    or decision.get("reason_code") != "MISSING_REQUIRED_GEOMETRY_VIEW"
                    or decision.get("next_state") != "EXECUTING"
                    or not isinstance(source, dict) or source.get("kind") != "SCENARIO_A_COVERAGE"
                    or source.get("config") != reference(CONFIG)):
                raise ValueError("fresh next-view Decision provenance differs: " + role)
            for key in ("coverage", "controller_input", "controller_decision", "review", "state"):
                reviewer.checked_ref(source[key])
            prior = json.loads(reviewer.checked_ref(source["coverage"]).read_text(encoding="utf-8"))
            expected_prior = evaluate([views[view] for view in config["acquisition_order"] if view in views],
                                      output_root=output_root)
            if (prior != expected_prior or prior["next_target"] != role
                    or prior["run_id"] != config["run_id"]):
                raise ValueError("next-view Decision used stale coverage: " + role)
        if (decision.get("run_id") != config["run_id"] or decision.get("target") != role
                or decision.get("execution_required") is not True
                or (role == "right" and record["decision"] != config["initial_decision"])
                or (role != "right" and (decision.get("action") != "ADD_VIEW"
                                           or decision.get("return_review_state") != "MULTIVIEW_REVIEW"))
                or report.get("status") != "SUCCESS" or not report.get("prompt_id")
                or not str(report.get("task_id", "")).startswith(config["run_id"] + "-")
                or not str(report.get("task_id", "")).endswith("-" + role)
                or report.get("workflow") != config["generated_view_contracts"][role]["workflow"]
                or len(report.get("outputs", [])) != 1
                or report["outputs"][0].get("type") != "image"
                or Path(report["outputs"][0].get("path", "")).resolve() != path):
            raise ValueError("fresh generated provenance differs: " + role)
        if role in views:
            if views[role] != record:
                raise ValueError("conflicting role identity: " + role)
            continue
        views[role] = record
    missing = [role for role in config["required_roles"] if role not in views]
    if missing:
        target = next(role for role in config["acquisition_order"] if role in missing)
        outcome = "NEEDS_EXECUTION"
    else:
        target, outcome = None, "READY_FOR_CONTROLLER"
    return {"coverage_version": "ac6-f2a.0", "run_id": config["run_id"],
            "config": reference(CONFIG), "required_roles": config["required_roles"],
            "resolved_views": [views[role] for role in config["required_roles"] if role in views],
            "missing_roles": missing, "geometry_ready": not missing,
            "next_target": target, "outcome": outcome}


def publish_coverage(path, generated, output_root=OUTPUT_ROOT):
    """Publish an immutable Scenario A view set; no execution or reservation."""
    target = Path(path).resolve()
    if not target.is_relative_to(ROOT):
        raise ValueError("coverage state outside repository")
    coverage = evaluate(generated, output_root=output_root)
    return persistence.apply_once(target, coverage), coverage


def route_after_controller(coverage_ref, state_ref, input_ref, decision_ref, output_root=OUTPUT_ROOT):
    """Keep a validated Controller ADVANCE intact; gate its Scenario A dispatch."""
    coverage = json.loads(reviewer.checked_ref(coverage_ref).read_text(encoding="utf-8"))
    order = load_config()[0]["acquisition_order"]
    generated = sorted((item for item in coverage["resolved_views"] if item["kind"] == "GENERATED"),
                       key=lambda item: order.index(item["role"]))
    if evaluate(generated, output_root=output_root) != coverage:
        raise ValueError("coverage identity differs")
    state_path = reviewer.checked_ref(state_ref)
    input_path = reviewer.checked_ref(input_ref)
    decision_path = reviewer.checked_ref(decision_ref)
    snapshot = json.loads(state_path.read_text(encoding="utf-8"))
    item = json.loads(input_path.read_text(encoding="utf-8"))
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    state = snapshot["state"]
    controller.validate_state(state)
    if (snapshot["run_id"] != coverage["run_id"] or state["run_id"] != coverage["run_id"]
            or item["state"] != state or item["source"]["kind"] != "RESULT_REVIEW"
            or state["latest_review"] != {"path": item["source"]["path"], "sha256": item["source"]["sha256"]}
            or state["current_state"] != "MULTIVIEW_REVIEW" or snapshot["terminal"] is not False
            or snapshot["pending_semantic_review"] is not False):
        raise ValueError("fresh Review-attached state differs")
    if controller.decide(item) != decision or (decision.get("run_id"), decision.get("controller_decision"),
            decision.get("reason_code"), decision.get("execution_required"),
            decision.get("return_review_state")) != (
                coverage["run_id"], "ADVANCE", "GEOMETRY_STAGE_READY", True, "GEOMETRY_REVIEW"):
        raise ValueError("Controller ADVANCE lineage differs")
    review_path = reviewer.checked_ref({"path": item["source"]["path"], "sha256": item["source"]["sha256"]})
    review = json.loads(review_path.read_text(encoding="utf-8"))
    by_role = {record["role"]: record for record in generated}
    latest = next((by_role[role] for role in reversed(load_config()[0]["acquisition_order"])
                   if role in by_role), None)
    if (latest is None or review.get("stage") != "MULTIVIEW_REVIEW"
            or review.get("source_result") != latest["report"]
            or not any(artifact.get("path") == latest["path"] and artifact.get("sha256") == latest["sha256"]
                       for artifact in review.get("artifacts", []))):
        raise ValueError("latest Review does not cover fresh view")
    if persistence.guard_execution(snapshot) != "EXECUTION_ALLOWED":
        raise ValueError("fresh execution budget or state blocked: " + persistence.guard_execution(snapshot))
    if coverage["geometry_ready"]:
        return "READY_FOR_CONTROLLER", decision
    target = coverage["next_target"]
    if target == "right":
        raise ValueError("initial right must use F1 bootstrap Decision")
    source = {"kind": "SCENARIO_A_COVERAGE", "coverage": coverage_ref, "config": coverage["config"],
        "controller_input": input_ref, "controller_decision": decision_ref,
        "review": {"path": item["source"]["path"], "sha256": item["source"]["sha256"]},
        "state": state_ref}
    next_decision = {
        "schema_version": "0.1", "policy_version": "D-016/SCENARIO_A_COVERAGE",
        "run_id": coverage["run_id"], "input_sha256": controller.sha256(controller.canonical(source)),
        "source": source, "controller_decision": "EXECUTE", "action": "ADD_VIEW",
        "target": target, "next_state": "EXECUTING", "termination": None,
        "reason_code": "MISSING_REQUIRED_GEOMETRY_VIEW", "execution_required": True,
        "return_review_state": "MULTIVIEW_REVIEW",
    }
    return "NEEDS_EXECUTION", next_decision
