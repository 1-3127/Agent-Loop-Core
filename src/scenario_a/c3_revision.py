"""Consume one verified C3 REVISE result and execute one right-view revision."""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from core import result_review_adapter as reviewer
from scenario_a import c1_delegate as delegate
from scenario_a import c3_review, codex_to_comfy as worker


ROOT = delegate.ROOT
COMFY = delegate.COMFY


def supported_revision(review):
    if review["verdict"] != "REVISE":
        raise ValueError("fresh Review is not REVISE")
    if not review["blocking_issues"]:
        raise ValueError("REVISE has no blocking issue")
    if review["suggested_action"] != {"code": "REGENERATE_VIEW", "target": "right"}:
        raise ValueError("unsupported revision action or target")


def preflight(order_path):
    order_path = Path(order_path).resolve()
    if not order_path.is_relative_to(ROOT) or not order_path.is_file():
        raise ValueError("revision Work Order must be a repository file")
    order = json.loads(order_path.read_text(encoding="utf-8"))
    fields = {"version", "run_id", "work_order_id", "iteration", "worker_type", "adapter",
              "requested_task", "revision_instruction", "source_review", "source_artifact",
              "blocking_issues", "suggested_action", "initial_work_order", "source",
              "workflow", "plan", "expected_output_kind", "worker_model",
              "worker_report_path", "execution_report_path"}
    if not isinstance(order, dict) or set(order) != fields or order["version"] != "c3.0":
        raise ValueError("revision Work Order fields differ")
    run_id = order["run_id"]
    if (not isinstance(run_id, str) or not re.fullmatch(r"m3-c3-[A-Za-z0-9_-]{1,58}", run_id)
            or order["work_order_id"] != run_id + "-revision-right" or order["iteration"] != 1
            or order["worker_type"] != "ComfyUI"
            or order["adapter"] != "src/scenario_a/c3_revision.py"
            or order["expected_output_kind"] != "image"
            or not isinstance(order["requested_task"], str) or not order["requested_task"]):
        raise ValueError("unsupported C3 revision Work Order")
    request, review = reviewer.checked_invocation(order["source_review"])
    c3_review.validate_request(request)
    supported_revision(review)
    invocation = json.loads(reviewer.checked_ref({
        "path": order["source_review"]["invocation_report_path"],
        "sha256": order["source_review"]["invocation_report_sha256"],
    }).read_text(encoding="utf-8"))
    attachments = [{key: artifact[key] for key in ("role", "path", "sha256")}
                   for artifact in request["artifacts"]]
    if (invocation.get("reviewer_mode") != "CODEX_CLI"
            or invocation.get("auth_mode") != "CHATGPT_ACCOUNT"
            or invocation.get("process_exit_code") != 0
            or invocation.get("attached_images") != attachments
            or request["run_id"] != run_id
            or order["initial_work_order"] != request["work_order"]
            or order["source_artifact"] != {key: request["artifacts"][0][key]
                                            for key in ("path", "sha256")}
            or order["blocking_issues"] != review["blocking_issues"]
            or order["suggested_action"] != review["suggested_action"]):
        raise ValueError("Review to revision lineage differs")
    initial = c3_review.c2_review.read_ref(order["initial_work_order"])
    if (order["source"] != initial["source"] or order["workflow"] != initial["workflow"]
            or order["worker_model"] != initial["worker_model"]):
        raise ValueError("revision changed Worker, source, or workflow")
    source = delegate.checked_file(order["source"], COMFY / "work/input")
    delegate.checked_file(order["workflow"], COMFY)
    plan_path = delegate.checked_file(order["plan"], ROOT)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    original_plan = c3_review.c2_review.read_ref(initial["plan"])
    if (not isinstance(order["revision_instruction"], str) or not order["revision_instruction"]
            or plan["task_id"] != order["work_order_id"]
            or plan["workflow"] != order["workflow"]["path"]
            or plan["output_node"] != "13"
            or plan["patches"]["1"]["image"] != source.name
            or plan["patches"]["8"]["prompt"] != order["revision_instruction"]
            or plan["patches"]["11"]["seed"] != original_plan["patches"]["11"]["seed"]
            or plan["patches"]["13"]["filename_prefix"] != "codex_to_comfy/" + run_id + "-revision"):
        raise ValueError("revision Plan differs from approved feedback or source")
    graph = worker.validate_plan(plan, COMFY)
    if (graph["13"]["class_type"] != "SaveImage"
            or graph["4"]["inputs"]["unet_name"] != order["worker_model"]):
        raise ValueError("revision Worker graph differs")
    report = delegate.repo_path(order["worker_report_path"])
    evidence = delegate.repo_path(order["execution_report_path"])
    if (report.exists() or evidence.exists()
            or any((COMFY / "work/output/codex_to_comfy").glob(run_id + "-revision_*"))):
        raise ValueError("revision already consumed or output namespace exists")
    return order, plan_path, report, evidence


def run(order_path):
    order, plan_path, report_path, evidence_path = preflight(order_path)
    status = worker.run(plan_path, report_path, COMFY, timeout=600)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if status != 0 or report["status"] != "SUCCESS":
        raise ValueError("revision Worker did not succeed; inspect report before any retry")
    if (report["task_id"] != order["work_order_id"] or report["workflow"] != order["workflow"]["path"]
            or not report["prompt_id"] or not report["client_id"] or len(report["outputs"]) != 1):
        raise ValueError("revision Worker report identity differs")
    output = report["outputs"][0]
    artifact = Path(output["path"]).resolve()
    if (output["type"] != "image"
            or artifact.parent != (COMFY / "work/output/codex_to_comfy").resolve()
            or not artifact.name.startswith(order["run_id"] + "-revision_")
            or not artifact.is_file() or artifact.stat().st_size <= 24):
        raise ValueError("revision artifact identity differs")
    started = datetime.fromisoformat(report["started_at"])
    finished = datetime.fromisoformat(report["completed_at"])
    if finished < started:
        raise ValueError("revision Worker report time differs")
    evidence = {
        "version": "c3.0", "run_id": order["run_id"],
        "revision_work_order_id": order["work_order_id"],
        "revision_work_order": {"path": order_path.as_posix() if isinstance(order_path, Path)
                                 else Path(order_path).as_posix(), "sha256": delegate.digest(order_path)},
        "source_review": order["source_review"],
        "source_artifact": order["source_artifact"],
        "blocking_issues": order["blocking_issues"],
        "suggested_action": order["suggested_action"],
        "plan": order["plan"], "worker_type": order["worker_type"],
        "adapter": order["adapter"], "worker_model": order["worker_model"],
        "worker_report": {"path": order["worker_report_path"], "sha256": delegate.digest(report_path)},
        "status": "SUCCESS", "client_id": report["client_id"], "prompt_id": report["prompt_id"],
        "started_at": report["started_at"], "completed_at": report["completed_at"],
        "execution_seconds": (finished - started).total_seconds(),
        "artifact": {"path": str(artifact), "kind": "image", "bytes": artifact.stat().st_size,
                     "sha256": delegate.digest(artifact), "width": output["width"],
                     "height": output["height"]},
    }
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    with evidence_path.open("x", encoding="utf-8") as stream:
        json.dump(evidence, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-order", type=Path, required=True)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    try:
        if args.preflight:
            print("C3_REVISION_PREFLIGHT_VALID " + preflight(args.work_order)[0]["work_order_id"])
            return 0
        evidence = run(args.work_order)
        print("C3_REVISION_SUCCESS " + evidence["prompt_id"])
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("C3_REVISION_BLOCKED " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
