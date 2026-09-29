"""Bind the verified C1 right-view result to one semantic Reviewer call."""

import argparse
import json
import sys
from pathlib import Path

from core import result_review_adapter as reviewer


ROOT = Path(__file__).resolve().parents[2]
COMFY = Path("D:/VSCODE-WorkSpace/Comfy-UI").resolve()
CRITERIA = [
    "Preserve the source object's identity and structure.",
    "Show a plausible right-side camera change.",
    "Keep the whole object sufficiently visible without severe crop or zoom.",
    "Avoid blocking structural distortion or floating elements.",
    "Remain coherent enough for the next production step.",
]


def read_ref(ref):
    return json.loads(reviewer.checked_ref(ref).read_text(encoding="utf-8"))


def validate_c1_lineage(request, criteria=CRITERIA):
    reviewer.validate_request(request)
    if (request["request_version"] not in ("0.2", "0.3") or request["stage"] != "RIGHT_VIEW_REVIEW"
            or request["output_kind"] != "image" or request["review_id"] == request["run_id"]
            or request["context"] != {
                "requested_task": "Generate one right view from the source image",
                "acceptance_criteria": criteria,
            }):
        raise ValueError("C2 right-view request differs")
    order = read_ref(request["work_order"])
    execution = read_ref(request["source_result"])
    worker_report = read_ref(request["worker_report"])
    if (order["run_id"] != request["run_id"] or order["work_order_id"] != execution["work_order_id"]
            or order["requested_task"] != request["context"]["requested_task"]
            or execution["run_id"] != request["run_id"] or execution["status"] != "SUCCESS"
            or execution["work_order"] != request["work_order"]
            or execution["worker_report"] != request["worker_report"]
            or execution["source"] != order["source"]
            or execution["workflow"] != order["workflow"]
            or worker_report["status"] != "SUCCESS" or worker_report["task_id"] != order["work_order_id"]
            or worker_report["prompt_id"] != execution["prompt_id"]
            or worker_report["client_id"] != execution["client_id"]):
        raise ValueError("C1 Work Order, execution, or invocation lineage differs")
    plan = read_ref(order["plan"])
    if (plan["task_id"] != order["work_order_id"] or plan["workflow"] != order["workflow"]["path"]
            or plan["patches"]["1"]["image"] != order["source"]["path"]
            or plan["output_node"] != "13"):
        raise ValueError("C1 Plan lineage differs")
    source = (COMFY / "work/input" / order["source"]["path"]).resolve()
    if (source.parent != (COMFY / "work/input").resolve()
            or reviewer.digest(source) != order["source"]["sha256"]):
        raise ValueError("C1 source image differs")
    artifact = execution["artifact"]
    output = worker_report["outputs"]
    if (len(output) != 1 or output[0]["type"] != "image"
            or Path(output[0]["path"]).resolve() != Path(artifact["path"]).resolve()
            or (output[0]["width"], output[0]["height"]) != (artifact["width"], artifact["height"])):
        raise ValueError("C1 worker output differs")
    generated = Path(artifact["path"]).resolve()
    if (generated.parent != (COMFY / "work/output/codex_to_comfy").resolve()
            or generated.stat().st_size != artifact["bytes"]
            or reviewer.digest(generated) != artifact["sha256"]):
        raise ValueError("C1 generated artifact differs")
    expected = [
        {"role": "generated_output", "path": str(generated),
         "sha256": artifact["sha256"], "media_type": "image/png"},
        {"role": "source_reference", "path": str(source),
         "sha256": order["source"]["sha256"], "media_type": "image/png"},
    ]
    if request["artifacts"] != expected:
        raise ValueError("C2 attached image identity differs")
    return order, execution


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    try:
        request = json.loads(args.request.read_text(encoding="utf-8"))
        validate_c1_lineage(request)
        if args.result.exists() or args.report.exists():
            raise ValueError("Review result or report already exists")
        if args.preflight:
            print("C2_PREFLIGHT_VALID " + request["review_id"])
            return 0
        report = reviewer.review_once(args.request, args.result, args.report, timeout=600)
        print("C2_REVIEW " + report["invocation_status"] + " " + request["review_id"])
        return 0 if report["invocation_status"] == "SUCCESS" else 1
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("C2_BLOCKED " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
