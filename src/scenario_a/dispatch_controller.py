"""A-C4: dispatch one validated ADD_VIEW back Decision through the existing executor."""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import codex_to_comfy as executor
import pipeline_a_controller as controller


ROOT = Path(__file__).resolve().parents[2]
COMFY = executor.DEFAULT_COMFY_ROOT.resolve()
BACK_WORKFLOW = "workflows/02_Image_to_Multiview/Qwen2509_Back_api.json"
RECEIPTS = ROOT / "dispatch_receipts"


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def new_path(value):
    relative = executor.safe_relative(value, "project output")
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("project output escapes root")
    return path


def checked_ref(ref):
    if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
        raise ValueError("reference fields differ")
    path = controller.project_path(ref["path"])
    if file_hash(path) != ref["sha256"]:
        raise ValueError("reference hash differs")
    return path


def preflight(config, api=executor.request_json):
    if not isinstance(config, dict) or set(config) != {"dispatch_version", "controller_decision", "controller_input", "task_id", "seed", "filename_prefix", "plan_path", "report_path", "timeout_seconds"} or config["dispatch_version"] != "0.1":
        raise ValueError("dispatch request fields differ")
    decision_path = checked_ref(config["controller_decision"])
    input_path = checked_ref(config["controller_input"])
    decision_hash = config["controller_decision"]["sha256"]
    receipt_path = RECEIPTS / (decision_hash + ".json")
    if receipt_path.exists():
        raise ValueError("ALREADY_DISPATCHED")
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    controller_input = json.loads(input_path.read_text(encoding="utf-8"))
    if (controller.sha256(controller.canonical(controller_input)) != decision.get("input_sha256") or
            controller.decide(controller_input) != decision):
        raise ValueError("Controller Decision lineage differs")
    if (decision.get("controller_decision") != "EXECUTE" or decision.get("action") != "ADD_VIEW" or
            decision.get("target") != "back" or decision.get("next_state") != "EXECUTING" or
            decision.get("return_review_state") != "MULTIVIEW_REVIEW" or decision.get("execution_required") is not True):
        raise ValueError("NOT_DISPATCHABLE")
    if controller_input["source"]["kind"] != "REVIEWER_RESULT":
        raise ValueError("reviewer lineage required")
    request_path = controller.project_path(controller_input["source"]["request_path"])
    reviewed = json.loads(request_path.read_text(encoding="utf-8"))
    front = reviewed["artifacts"][0]
    if front["role"] != "front_source":
        raise ValueError("front source identity missing")
    source_path = Path(front["path"]).resolve()
    input_root = (COMFY / "work" / "input").resolve()
    if not source_path.is_relative_to(input_root) or file_hash(source_path) != front["sha256"]:
        raise ValueError("front source hash differs")
    if not isinstance(config["task_id"], str) or not config["task_id"].startswith("ac4-") or not isinstance(config["seed"], int) or isinstance(config["seed"], bool) or not 0 <= config["seed"] < 2**64:
        raise ValueError("invalid task or seed")
    if type(config["timeout_seconds"]) is not int or config["timeout_seconds"] < 1:
        raise ValueError("invalid timeout")
    prefix = executor.safe_relative(config["filename_prefix"], "filename_prefix")
    if prefix.parts[0] != "codex_to_comfy" or not prefix.name.startswith("ac4_"):
        raise ValueError("output prefix must be new A-C4 namespace")
    plan_path, report_path = new_path(config["plan_path"]), new_path(config["report_path"])
    if plan_path.exists() or report_path.exists():
        raise ValueError("plan/report collision")
    output_dir = (COMFY / "work" / "output" / prefix.parent).resolve()
    if output_dir.exists() and any(output_dir.glob(prefix.name + "_*")):
        raise ValueError("output prefix collision")
    template_path = (COMFY / BACK_WORKFLOW).resolve()
    if not template_path.is_file():
        raise ValueError("back workflow missing")
    template = json.loads(template_path.read_text(encoding="utf-8"))
    if any(template.get(n, {}).get("class_type") != cls for n, cls in (("1", "LoadImage"), ("8", "TextEncodeQwenImageEditPlus"), ("11", "KSampler"), ("13", "SaveImage"))):
        raise ValueError("back workflow capability differs")
    plan = {"schema_version": "0.1", "task_id": config["task_id"], "workflow": BACK_WORKFLOW,
            "patches": {"1": {"image": source_path.name}, "11": {"seed": config["seed"]},
                        "13": {"filename_prefix": config["filename_prefix"]}}, "output_node": "13"}
    graph = executor.validate_plan(plan, COMFY)
    if graph["8"]["inputs"]["prompt"] != template["8"]["inputs"]["prompt"]:
        raise ValueError("back prompt changed")
    stats, queue, object_info = api("/system_stats"), api("/queue"), api("/object_info")
    if not stats.get("devices") or queue.get("queue_running") or queue.get("queue_pending"):
        raise ValueError("ComfyUI device unavailable or queue not empty")
    missing = {node["class_type"] for node in graph.values()} - set(object_info)
    if missing:
        raise ValueError("ComfyUI nodes unavailable: " + ",".join(sorted(missing)))
    return decision_path, input_path, receipt_path, plan_path, report_path, plan


def persist_receipt(path, item, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if exclusive:
        with path.open("x", encoding="utf-8") as stream:
            json.dump(item, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    else:
        executor.write_report(path, item)


def dispatch(config, api=executor.request_json, run=executor.run):
    decision_path, input_path, receipt_path, plan_path, report_path, plan = preflight(config, api)
    controller.write_decision(plan_path, plan)
    decision_hash = config["controller_decision"]["sha256"]
    receipt = {"dispatch_version": "0.1", "dispatch_id": "ac4-" + decision_hash[:16],
               "controller_decision_path": str(decision_path), "controller_decision_sha256": decision_hash,
               "controller_input_path": str(input_path), "controller_input_sha256": file_hash(input_path),
               "plan_path": str(plan_path), "plan_sha256": file_hash(plan_path),
               "execution_report_path": str(report_path), "status": "RESERVED", "execution_status": None,
               "action_consumed": False, "client_id": None, "prompt_id": None, "outputs": [], "error": None}
    persist_receipt(receipt_path, receipt, exclusive=True)
    try:
        outcome = run(plan_path, report_path, COMFY, config["timeout_seconds"])
        if report_path.exists():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            receipt.update(client_id=report.get("client_id"), prompt_id=report.get("prompt_id"),
                           execution_status=report.get("status"), execution_report_sha256=file_hash(report_path),
                           action_consumed=True)
        if outcome == 0 and receipt["execution_status"] == "SUCCESS":
            outputs = []
            for output in report["outputs"]:
                path = Path(output["path"]).resolve()
                if output.get("type") != "image" or not path.is_relative_to(COMFY / "work" / "output") or not path.is_file():
                    raise ValueError("invalid output artifact")
                data = path.read_bytes()
                outputs.append({"path": str(path), "sha256": hashlib.sha256(data).hexdigest(),
                                "bytes": len(data), "width": output["width"], "height": output["height"]})
            if not outputs:
                raise ValueError("no output artifact")
            receipt.update(status="SUCCESS", outputs=outputs)
        elif receipt["execution_status"] == "UNRESOLVED" or outcome == 2:
            receipt["status"] = "UNRESOLVED"
        else:
            receipt["status"] = "FAILED"
    except Exception as exc:
        receipt.update(status="UNRESOLVED" if report_path.exists() else "FAILED", error=str(exc))
        if report_path.exists():
            receipt.update(action_consumed=True, execution_report_sha256=file_hash(report_path))
    finally:
        persist_receipt(receipt_path, receipt)
    return receipt_path, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    args = parser.parse_args()
    try:
        config = json.loads(args.request.read_text(encoding="utf-8"))
        path, receipt = dispatch(config)
        print(f"DISPATCH {receipt['status']} receipt={path} prompt_id={receipt['prompt_id']}")
        return 0 if receipt["status"] == "SUCCESS" else 1
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"INVALID {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
