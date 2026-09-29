"""Build a fresh left/back Plan from the verified Scenario A historical templates."""

import copy
from pathlib import Path

import ac6_f2_image_transition as image_transition
import codex_to_comfy as executor
import persist_geometry_state as persistence
import scenario_a_coverage as coverage


ROOT = coverage.ROOT
TEMPLATES = {"left": ROOT / "plans/m4b_add_left_fixture.json",
             "back": ROOT / "plans/m4d_adaptive_back.json"}


def namespace(run_id, role, decision_ref):
    stem = f"{run_id}-{role}"
    return {"plan": ROOT / "plans" / (stem + ".json"),
            "receipt": ROOT / "dispatch_receipts" / (decision_ref["sha256"] + ".json"),
            "report": ROOT / "runs" / (stem + "_report.json"),
            "state": ROOT / "controller_states" / (stem + "_pending.json"),
            "review_request": ROOT / "reviewer_requests" / (stem + ".json"),
            "review_result": ROOT / "reviewer_results" / (stem + ".json"),
            "review_report": ROOT / "invocation_reports" / (stem + ".json")}


def build(coverage_ref, state_ref, controller_input_ref, controller_decision_ref, view_decision_ref,
          *, output_root=coverage.OUTPUT_ROOT, comfy_root=executor.DEFAULT_COMFY_ROOT,
          allow_consumed=False):
    outcome, expected = coverage.route_after_controller(
        coverage_ref, state_ref, controller_input_ref, controller_decision_ref,
        output_root=output_root)
    decision = image_transition.read(view_decision_ref)[1]
    if outcome != "NEEDS_EXECUTION" or expected != decision or decision["target"] not in TEMPLATES:
        raise ValueError("fresh next-view Decision differs")
    role = decision["target"]
    selected = image_transition.read(coverage_ref)[1]
    config, initial = coverage.load_config()
    if selected["run_id"] != config["run_id"]:
        raise ValueError("view Plan run differs")
    source = initial["source_artifact"]
    coverage.reviewer.checked_ref(source)
    template = image_transition.read(coverage.reference(TEMPLATES[role]))[1]
    contract = config["generated_view_contracts"][role]
    plan = copy.deepcopy(template)
    plan["task_id"] = config["run_id"] + "-" + role
    plan["patches"]["1"]["image"] = Path(source["path"]).name
    plan["patches"]["13"]["filename_prefix"] = contract["filename_prefix"]
    if plan["workflow"] != contract["workflow"] or plan["output_node"] != "13":
        raise ValueError("historical view Plan contract differs")
    graph = executor.validate_plan(plan, comfy_root)
    if (graph["1"]["inputs"]["image"] != Path(source["path"]).name
            or graph["13"]["inputs"]["filename_prefix"] != contract["filename_prefix"]):
        raise ValueError("fresh view input/output mapping differs")
    ns = namespace(config["run_id"], role, view_decision_ref)
    for key, path in ns.items():
        if not allow_consumed and path.exists():
            raise ValueError("fresh view namespace collision: " + key)
    prefix = executor.safe_relative(contract["filename_prefix"], "filename_prefix")
    output_dir = Path(comfy_root) / "work/output" / prefix.parent
    if not allow_consumed and output_dir.exists() and any(output_dir.glob(prefix.name + "_*")):
        raise ValueError("fresh view output collision")
    if persistence.guard_execution(image_transition.read(state_ref)[1]) != "EXECUTION_ALLOWED":
        raise ValueError("BUDGET_EXHAUSTED")
    return {"classification": "FRESH_VIEW_PLAN_CONTRACT", "run_id": config["run_id"],
            "role": role, "coverage": coverage_ref, "source_state": state_ref,
            "controller_input": controller_input_ref,
            "controller_decision": controller_decision_ref, "decision": view_decision_ref,
            "plan": plan, "namespace": {key: str(value) for key, value in ns.items()}}
