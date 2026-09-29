"""P1: consume the real A-C5 Decision for one evidenced geometry invocation."""

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

import codex_to_comfy as executor
import dispatch_controller as prior_dispatch
import pipeline_a_controller as controller


ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = ROOT.parents[1]
COMFY = executor.DEFAULT_COMFY_ROOT.resolve()
RECEIPTS = ROOT / "dispatch_receipts"
DECISION_SHA = "cd7fac42717b9caddd940f66899a97bb4ae63401bcf021e1b44af131bf432a49"
WORKFLOW = "workflows/03_Multiview_to_3D/Hunyuan3D_MV_RTX4060_api.json"
NODES = {"front": "1", "left": "2", "back": "3", "right": "4"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_ref(ref):
    return prior_dispatch.checked_ref(ref)


def output_path(name):
    return prior_dispatch.new_path(name)


def checked_source(item, decision, controller_input):
    if set(item) != {"role", "source", "sha256", "source_report", "source_review", "staged_input", "selection_reason"}:
        raise ValueError("selected input fields differ")
    role = item["role"]
    if role not in NODES or not isinstance(item["selection_reason"], str) or not item["selection_reason"]:
        raise ValueError("invalid input role or rationale")
    relative = executor.safe_relative(item["source"], "source")
    source = (WORKSPACE / relative).resolve()
    input_root = (COMFY / "work" / "input").resolve()
    output_root = (COMFY / "work" / "output").resolve()
    expected_root = input_root if role == "front" else output_root
    if not source.is_relative_to(expected_root) or not source.is_file() or sha(source) != item["sha256"]:
        raise ValueError(f"{role} source path/hash differs")
    stage = executor.safe_relative(item["staged_input"], "staged_input")
    if len(stage.parts) != 1 or (role != "front" and not stage.name.startswith("ac6_p1_ac5_")):
        raise ValueError("staged input name invalid")
    if role == "front" and source != (input_root / stage).resolve():
        raise ValueError("front input source/stage differs")
    review_path = checked_ref(item["source_review"])
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if role in ("front", "back"):
        wanted = "source_reference" if role == "front" else "generated_output"
        if item["source_review"] != {
                "path": decision["source"]["path"], "sha256": decision["source"]["sha256"]}:
            raise ValueError("A-C5 review reference differs")
        matches = [a for a in review["artifacts"] if a["role"] == wanted and
                   Path(a["path"]).resolve() == source and a["sha256"] == item["sha256"]]
        if len(matches) != 1:
            raise ValueError(f"{role} A-C5 review artifact differs")
    else:
        matches = [a for a in review["reviewed_outputs"] if
                   Path(a["path"]).resolve() == source and a["sha256"] == item["sha256"]]
        if len(matches) != 1:
            raise ValueError(f"{role} review artifact differs")
    if role == "front":
        if item["source_report"] is not None:
            raise ValueError("front original must have no source report")
        return source, input_root / stage
    report_path = checked_ref(item["source_report"])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("status") != "SUCCESS" or not any(
            Path(a.get("path", "")).resolve() == source and a.get("type") == "image"
            for a in report.get("outputs", [])):
        raise ValueError(f"{role} report output differs")
    if role == "back":
        latest = controller_input["state"]["latest_artifact"]
        if latest != {"path": str(source).replace("\\", "/"), "sha256": item["sha256"]}:
            raise ValueError("back is not latest A-C4 artifact")
        if review["source_result"] != item["source_report"]:
            raise ValueError("back review result differs")
    elif review.get("prompt_id") != report.get("prompt_id") or (
            ROOT / review.get("execution_report", "")).resolve() != report_path:
        raise ValueError(f"{role} review/report lineage differs")
    return source, input_root / stage


def validate_request(config):
    required = {"dispatch_version", "controller_decision", "controller_input", "task_id",
                "selected_inputs", "workflow", "seed", "filename_prefix", "plan_path",
                "report_path", "timeout_seconds"}
    if not isinstance(config, dict) or set(config) != required or config["dispatch_version"] != "p1.0":
        raise ValueError("P1 request fields differ")
    decision_path = checked_ref(config["controller_decision"])
    input_path = checked_ref(config["controller_input"])
    if sha(decision_path) != DECISION_SHA:
        raise ValueError("unexpected A-C5 Decision hash")
    receipt_path = RECEIPTS / (DECISION_SHA + ".json")
    if receipt_path.exists():
        raise ValueError("ALREADY_DISPATCHED")
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    controller_input = json.loads(input_path.read_text(encoding="utf-8"))
    if (controller.sha256(controller.canonical(controller_input)) != decision.get("input_sha256")
            or controller.decide(controller_input) != decision):
        raise ValueError("A-C5 policy lineage differs")
    if (decision.get("controller_decision") != "ADVANCE" or
            decision.get("reason_code") != "GEOMETRY_STAGE_READY" or
            decision.get("execution_required") is not True or
            decision.get("next_state") != "EXECUTING" or
            decision.get("return_review_state") != "GEOMETRY_REVIEW" or
            controller_input["state"]["current_state"] != "MULTIVIEW_REVIEW" or
            controller_input["source"]["kind"] != "RESULT_REVIEW"):
        raise ValueError("NOT_DISPATCHABLE")
    selected = config["selected_inputs"]
    if not isinstance(selected, list) or [i.get("role") for i in selected] != list(NODES):
        raise ValueError("4-view roles/order differ")
    sources = {i["role"]: checked_source(i, decision, controller_input) for i in selected}
    if config["workflow"] != WORKFLOW or config["task_id"] != "ac6-p1-ac5-geometry":
        raise ValueError("geometry workflow/task differs")
    if type(config["seed"]) is not int or not 0 <= config["seed"] < 2**64:
        raise ValueError("invalid seed")
    if type(config["timeout_seconds"]) is not int or config["timeout_seconds"] < 1:
        raise ValueError("invalid timeout")
    prefix = executor.safe_relative(config["filename_prefix"], "filename_prefix")
    if prefix.as_posix() != "mesh/ac6_p1_ac5_geometry":
        raise ValueError("unexpected output prefix")
    plan_path, report_path = output_path(config["plan_path"]), output_path(config["report_path"])
    if plan_path != ROOT / "plans/ac6_p1_ac5_geometry.json" or report_path != ROOT / "runs/ac6_p1_ac5_geometry_report.json":
        raise ValueError("unexpected Plan/Report path")
    template_path = (COMFY / WORKFLOW).resolve()
    template = json.loads(template_path.read_text(encoding="utf-8"))
    if (any(template.get(node, {}).get("class_type") != "LoadImage" for node in NODES.values())
            or template.get("17", {}).get("class_type") != "SaveGLB"
            or template.get("10", {}).get("inputs") != {
                "front": ["6", 0], "left": ["7", 0], "back": ["8", 0], "right": ["9", 0]}):
        raise ValueError("geometry workflow role mapping differs")
    plan = {"schema_version": "0.1", "task_id": config["task_id"], "workflow": WORKFLOW,
            "patches": {NODES[i["role"]]: {"image": i["staged_input"]} for i in selected} |
                       {"14": {"seed": config["seed"]}, "17": {"filename_prefix": config["filename_prefix"]}},
            "output_node": "17"}
    return receipt_path, plan_path, report_path, plan, sources


def stage_sources(sources):
    for role, (source, destination) in sources.items():
        if destination.exists():
            if sha(destination) != sha(source):
                raise ValueError(f"{role} staged input hash differs")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        created = False
        try:
            with source.open("rb") as src, destination.open("xb") as dst:
                created = True
                shutil.copyfileobj(src, dst)
                dst.flush()
                os.fsync(dst.fileno())
        except Exception:
            if created:
                destination.unlink(missing_ok=True)
            raise
        if sha(destination) != sha(source):
            raise ValueError(f"{role} staged copy differs")


def preflight(config, api=executor.request_json):
    receipt_path, plan_path, report_path, plan, sources = validate_request(config)
    if report_path.exists():
        raise ValueError("report collision")
    prefix = executor.safe_relative(config["filename_prefix"], "filename_prefix")
    output_dir = (COMFY / "work" / "output" / prefix.parent).resolve()
    if output_dir.exists() and any(output_dir.glob(prefix.name + "_*")):
        raise ValueError("output prefix collision")
    stage_sources(sources)
    graph = executor.validate_plan(plan, COMFY)
    if any(graph[NODES[role]]["inputs"]["image"] != item["staged_input"]
           for role, item in [(i["role"], i) for i in config["selected_inputs"]]):
        raise ValueError("geometry input node mapping differs")
    stats, queue, object_info = api("/system_stats"), api("/queue"), api("/object_info")
    if not stats.get("devices") or queue.get("queue_running") or queue.get("queue_pending"):
        raise ValueError("ComfyUI device unavailable or queue not empty")
    missing = {node["class_type"] for node in graph.values()} - set(object_info)
    if missing:
        raise ValueError("ComfyUI nodes unavailable: " + ",".join(sorted(missing)))
    if plan_path.exists():
        if json.loads(plan_path.read_text(encoding="utf-8")) != plan:
            raise ValueError("existing Plan differs")
    else:
        controller.write_decision(plan_path, plan)
    return receipt_path, plan_path, report_path, plan


def dispatch(config, request_path, api=executor.request_json, run=executor.run):
    receipt_path, plan_path, report_path, _ = preflight(config, api)
    receipt = {
        "dispatch_version": "p1.0", "controller_decision_path": config["controller_decision"]["path"],
        "controller_decision_sha256": DECISION_SHA, "controller_input": config["controller_input"],
        "dispatch_request_path": str(request_path.resolve()), "dispatch_request_sha256": sha(request_path),
        "plan_path": str(plan_path), "plan_sha256": sha(plan_path),
        "execution_report_path": str(report_path), "status": "RESERVED",
        "execution_status": None, "action_consumed": False, "client_id": None,
        "prompt_id": None, "outputs": [], "error": None,
    }
    prior_dispatch.persist_receipt(receipt_path, receipt, exclusive=True)
    try:
        outcome = run(plan_path, report_path, COMFY, config["timeout_seconds"])
        if report_path.exists():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            receipt.update(client_id=report.get("client_id"), prompt_id=report.get("prompt_id"),
                           execution_status=report.get("status"), execution_report_sha256=sha(report_path),
                           action_consumed=True)
        if outcome == 0 and receipt["execution_status"] == "SUCCESS":
            outputs = report.get("outputs", [])
            prefix = executor.safe_relative(config["filename_prefix"], "filename_prefix")
            if len(outputs) != 1:
                raise ValueError("expected exactly one GLB")
            artifact = outputs[0]
            path = Path(artifact["path"]).resolve()
            if (artifact.get("type") != "geometry" or not path.is_relative_to((COMFY / "work/output").resolve())
                    or path.parent != (COMFY / "work/output" / prefix.parent).resolve()
                    or not path.name.startswith(prefix.name + "_") or path.suffix.lower() != ".glb"
                    or sha(path) != artifact["sha256"]):
                raise ValueError("GLB artifact identity differs")
            receipt.update(status="SUCCESS", outputs=outputs)
        elif receipt["execution_status"] == "UNRESOLVED" or outcome == 2:
            receipt["status"] = "UNRESOLVED"
        else:
            receipt["status"] = "FAILED"
    except Exception as exc:
        receipt.update(status="UNRESOLVED" if report_path.exists() else "FAILED", error=str(exc))
        if report_path.exists():
            receipt.update(action_consumed=True, execution_report_sha256=sha(report_path))
    finally:
        prior_dispatch.persist_receipt(receipt_path, receipt)
    return receipt_path, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--dispatch", action="store_true", help="submit exactly one prompt after preflight")
    args = parser.parse_args()
    try:
        config = json.loads(args.request.read_text(encoding="utf-8"))
        if args.dispatch:
            receipt_path, receipt = dispatch(config, args.request)
            print(f"P1_DISPATCH {receipt['status']} receipt={receipt_path} prompt_id={receipt['prompt_id']}")
            return 0 if receipt["status"] == "SUCCESS" else 1
        receipt_path, plan_path, _, _ = preflight(config)
        print(f"P1_PREFLIGHT_VALID decision={DECISION_SHA} plan={plan_path} plan_sha256={sha(plan_path)} receipt_absent={not receipt_path.exists()}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"P1_BLOCKED {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
