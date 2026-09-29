"""Validate one adaptive view decision against current files and run lineage."""

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

from validate_review import project_file, validate as validate_review


PROJECT = Path(__file__).resolve().parents[2]
COMFY_ROOT = PROJECT.parents[1] / "Comfy-UI"
TEMPLATES = {
    "right": "Qwen2509_Multiangle_RTX4060_api.json",
    "left": "Qwen2509_Left_api.json",
    "back": "Qwen2509_Back_api.json",
}
FIELDS = {
    "schema_version", "decision_id", "source_image", "generated_views",
    "decision", "requested_view", "repeat_existing_view_reason",
    "reason", "evidence", "known_issues", "blocking_issues", "confidence",
}
VIEW_FIELDS = {"view_id", "task_id", "execution_report", "review", "path", "sha256"}
EVIDENCE_FIELDS = {"coverage", "novel_information", "redundancy", "consistency", "executor_support"}


def file_hash(path, expected):
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("invalid SHA-256")
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"missing or changed artifact: {path}")


def supported_views():
    result = {}
    base = COMFY_ROOT / "workflows" / "02_Image_to_Multiview"
    for view_id, filename in TEMPLATES.items():
        path = base / filename
        if not path.is_file():
            continue
        workflow = json.loads(path.read_text(encoding="utf-8"))
        prompt = workflow["8"]["inputs"]["prompt"].lower()
        if (view_id == "back" and "rear" not in prompt) or (view_id != "back" and view_id not in prompt):
            continue
        if workflow["1"]["class_type"] != "LoadImage" or workflow["13"]["class_type"] != "SaveImage":
            continue
        result[view_id] = path
    return result


def validate(decision):
    if not isinstance(decision, dict) or set(decision) != FIELDS:
        raise ValueError("decision has missing or extra fields")
    if decision["schema_version"] != "0.1" or not isinstance(decision["decision_id"], str) or not decision["decision_id"].strip():
        raise ValueError("invalid schema_version or decision_id")
    action = decision["decision"]
    if action not in ("PASS", "ADD_VIEW", "REGENERATE_VIEW"):
        raise ValueError("unsupported decision")
    confidence = decision["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if not isinstance(decision["reason"], str) or not decision["reason"].strip():
        raise ValueError("reason is required")
    for name in ("known_issues", "blocking_issues"):
        if not isinstance(decision[name], list) or any(not isinstance(s, str) or not s.strip() for s in decision[name]):
            raise ValueError(f"{name} must contain only nonempty strings")
    evidence = decision["evidence"]
    if not isinstance(evidence, dict) or set(evidence) != EVIDENCE_FIELDS or any(not isinstance(s, str) or not s.strip() for s in evidence.values()):
        raise ValueError("all five evidence criteria are required")

    source = decision["source_image"]
    if not isinstance(source, dict) or set(source) != {"path", "sha256"} or not isinstance(source["path"], str):
        raise ValueError("invalid source image reference")
    source_path = (COMFY_ROOT / source["path"]).resolve()
    if not source_path.is_relative_to((COMFY_ROOT / "work" / "input").resolve()):
        raise ValueError("source image must be under ComfyUI work/input")
    file_hash(source_path, source["sha256"])

    views = decision["generated_views"]
    if not isinstance(views, list) or not views:
        raise ValueError("generated_views must be nonempty")
    available = supported_views()
    seen_tasks = set()
    existing_views = set()
    for view in views:
        if not isinstance(view, dict) or set(view) != VIEW_FIELDS or view["view_id"] not in available:
            raise ValueError("invalid generated view or unsupported view_id")
        if not isinstance(view["task_id"], str) or view["task_id"] in seen_tasks:
            raise ValueError("duplicate or invalid source task")
        seen_tasks.add(view["task_id"])
        existing_views.add(view["view_id"])
        report = json.loads(project_file(view["execution_report"]).read_text(encoding="utf-8"))
        review = json.loads(project_file(view["review"]).read_text(encoding="utf-8"))
        validate_review(review)
        if (report.get("status") != "SUCCESS" or report.get("task_id") != view["task_id"]
                or review.get("task_id") != view["task_id"] or review.get("execution_report") != view["execution_report"]
                or report.get("workflow") != "workflows/02_Image_to_Multiview/" + available[view["view_id"]].name):
            raise ValueError("source task/report/review/template lineage differs")
        plan = json.loads(project_file(review["plan"]).read_text(encoding="utf-8"))
        if plan.get("patches", {}).get("1", {}).get("image") != source_path.name:
            raise ValueError("source image differs from the Plan input")
        outputs = report.get("outputs", [])
        if len(outputs) != 1 or view["path"] != outputs[0].get("path") or view["sha256"] != review["reviewed_outputs"][0]["sha256"]:
            raise ValueError("source artifact/report/review lineage differs")
        file_hash(Path(view["path"]), view["sha256"])

    requested = decision["requested_view"]
    repeat_reason = decision["repeat_existing_view_reason"]
    if action == "PASS":
        if requested is not None or repeat_reason is not None or decision["blocking_issues"]:
            raise ValueError("PASS cannot contain an action or blocker")
    else:
        if not isinstance(requested, dict) or set(requested) != {"view_id", "azimuth_deg", "elevation_deg"}:
            raise ValueError("requested_view is required")
        if requested["azimuth_deg"] is not None or requested["elevation_deg"] is not None:
            raise ValueError("numeric camera metadata is unsupported")
        view_id = requested["view_id"]
        if view_id not in available:
            raise ValueError("requested view lacks an existing supported template")
        if action == "ADD_VIEW":
            if view_id in existing_views and (not isinstance(repeat_reason, str) or not repeat_reason.strip()):
                raise ValueError("existing view requires an explicit repeat reason")
            if view_id not in existing_views and repeat_reason is not None:
                raise ValueError("repeat reason applies only to an existing view")
        elif view_id not in existing_views or repeat_reason is not None:
            raise ValueError("REGENERATE_VIEW must target an existing view")
    return action


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decision_file", type=Path)
    args = parser.parse_args()
    try:
        decision = json.loads(args.decision_file.read_text(encoding="utf-8"))
        action = validate(decision)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"INVALID {exc}", file=sys.stderr)
        return 1
    print(f"VALID decision={action} decision_id={decision['decision_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
