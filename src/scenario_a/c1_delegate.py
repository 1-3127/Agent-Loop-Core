"""Execute one fresh Scenario A Work Order through the existing ComfyUI worker."""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import codex_to_comfy as worker


ROOT = Path(__file__).resolve().parents[2]
COMFY = worker.DEFAULT_COMFY_ROOT.resolve()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def repo_path(value):
    path = (ROOT / worker.safe_relative(value, "repository path")).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("repository path escapes root")
    return path


def checked_file(ref, root):
    if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
        raise ValueError("file reference fields differ")
    path = (root / worker.safe_relative(ref["path"], "file reference")).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file() or digest(path) != ref["sha256"]:
        raise ValueError("file reference identity differs")
    return path


def preflight(order_path):
    order_path = Path(order_path).resolve()
    if not order_path.is_relative_to(ROOT) or not order_path.is_file():
        raise ValueError("Work Order must be a repository file")
    order = json.loads(order_path.read_text(encoding="utf-8"))
    fields = {"version", "run_id", "work_order_id", "worker_type", "adapter",
              "requested_task", "iteration", "source", "workflow", "plan",
              "expected_output_kind", "worker_report_path", "execution_report_path",
              "usage_path", "worker_model"}
    if not isinstance(order, dict) or set(order) != fields or order["version"] != "c1.0":
        raise ValueError("Work Order fields differ")
    run_id, work_order_id = order["run_id"], order["work_order_id"]
    if (not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", run_id)
            or work_order_id != run_id + "-initial-right" or order["iteration"] != 0
            or order["worker_type"] != "ComfyUI"
            or order["adapter"] != "src/scenario_a/c1_delegate.py"
            or order["expected_output_kind"] != "image"
            or order["requested_task"] != "Generate one right view from the source image"):
        raise ValueError("unsupported C1 Work Order")
    source = checked_file(order["source"], COMFY / "work/input")
    workflow = checked_file(order["workflow"], COMFY)
    plan_path = checked_file(order["plan"], ROOT)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if (plan["task_id"] != work_order_id or plan["workflow"] != order["workflow"]["path"]
            or plan["patches"]["1"]["image"] != source.name
            or plan["output_node"] != "13"
            or plan["patches"]["13"]["filename_prefix"] != "codex_to_comfy/" + run_id):
        raise ValueError("Work Order and Plan differ")
    graph = worker.validate_plan(plan, COMFY)
    if (graph["13"]["class_type"] != "SaveImage"
            or graph["1"]["class_type"] != "LoadImage"
            or graph["4"]["inputs"]["unet_name"] != order["worker_model"]):
        raise ValueError("worker graph differs")
    report = repo_path(order["worker_report_path"])
    evidence = repo_path(order["execution_report_path"])
    usage = repo_path(order["usage_path"])
    if (report.exists() or evidence.exists() or usage.exists()
            or any((COMFY / "work/output/codex_to_comfy").glob(run_id + "_*"))):
        raise ValueError("fresh C1 namespace already consumed")
    return order, plan_path, report, evidence, usage


def run(order_path):
    order, plan_path, report_path, evidence_path, usage_path = preflight(order_path)
    result = worker.run(plan_path, report_path, COMFY, timeout=600)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if result != 0 or report["status"] != "SUCCESS":
        raise ValueError("worker execution did not succeed; inspect reserved report before any retry")
    if (report["task_id"] != order["work_order_id"] or report["workflow"] != order["workflow"]["path"]
            or not report["prompt_id"] or not report["client_id"] or len(report["outputs"]) != 1):
        raise ValueError("worker report identity differs")
    output = report["outputs"][0]
    artifact = Path(output["path"]).resolve()
    prefix = order["run_id"] + "_"
    if (output["type"] != "image" or artifact.parent != (COMFY / "work/output/codex_to_comfy").resolve()
            or not artifact.name.startswith(prefix) or not artifact.is_file()):
        raise ValueError("fresh worker artifact identity differs")
    size = artifact.stat().st_size
    if size <= 24:
        raise ValueError("worker artifact is empty")
    started = datetime.fromisoformat(report["started_at"])
    finished = datetime.fromisoformat(report["completed_at"])
    seconds = (finished - started).total_seconds()
    if seconds < 0:
        raise ValueError("worker report time differs")
    evidence = {
        "version": "c1.0", "run_id": order["run_id"], "work_order_id": order["work_order_id"],
        "work_order": {"path": str(Path(order_path).resolve().relative_to(ROOT)).replace("\\", "/"),
                       "sha256": digest(order_path)},
        "plan": order["plan"], "source": order["source"], "workflow": order["workflow"],
        "worker_type": order["worker_type"], "adapter": order["adapter"],
        "worker_model": order["worker_model"], "status": "SUCCESS",
        "worker_report": {"path": order["worker_report_path"], "sha256": digest(report_path)},
        "client_id": report["client_id"], "prompt_id": report["prompt_id"],
        "started_at": report["started_at"], "completed_at": report["completed_at"],
        "artifact": {"path": str(artifact), "kind": "image", "bytes": size,
                     "sha256": digest(artifact), "width": output["width"], "height": output["height"]},
    }
    usage = {
        "run_id": order["run_id"],
        "frontier": {"provider": "OpenAI", "model": None, "invocations": None,
                     "input_tokens": None, "cached_input_tokens": None,
                     "output_tokens": None, "reasoning_tokens": None, "reported_credits": None},
        "workers": [{"worker_id": "scenario-a-qwen-right", "backend": "ComfyUI",
                     "model": order["worker_model"], "invocations": 1,
                     "execution_seconds": seconds}],
    }
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    usage_path.parent.mkdir(parents=True, exist_ok=True)
    with evidence_path.open("x", encoding="utf-8") as stream:
        json.dump(evidence, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    with usage_path.open("x", encoding="utf-8") as stream:
        json.dump(usage, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-order", type=Path, required=True)
    args = parser.parse_args()
    try:
        evidence = run(args.work_order)
        print("C1_EXECUTION_SUCCESS " + evidence["prompt_id"])
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("C1_BLOCKED " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
