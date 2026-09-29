"""Validate a Reviewer decision against its Plan, Execution Report, and artifacts."""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from codex_to_comfy import DEFAULT_COMFY_ROOT, validate_plan


PROJECT = Path(__file__).resolve().parents[2]
FIELDS = {
    "schema_version", "task_id", "prompt_id", "plan", "execution_report",
    "reviewer", "reviewed_at", "decision", "blocking_issues",
    "requested_actions", "notes", "reviewed_outputs",
}
PROMOTION_FIELD = "promotion_comparison"


def project_file(relative):
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ValueError("plan/report must be relative project paths")
    parts = relative.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError("plan/report path contains an unsafe component")
    path = (PROJECT / Path(*parts)).resolve()
    if not path.is_relative_to(PROJECT.resolve()) or not path.is_file():
        raise ValueError(f"plan/report file is unavailable: {relative}")
    return path


def nonempty_strings(value, name):
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{name} must be a list of nonempty strings")


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_promotion(comparison, review, promoted_report):
    required = {"baseline", "preview", "promotion_decision", "fidelity_gain", "canonical_geometry", "observations"}
    if not isinstance(comparison, dict) or set(comparison) != required:
        raise ValueError("promotion_comparison fields are invalid")
    if comparison["fidelity_gain"] not in ("CONFIRMED", "NOT CONFIRMED", "REGRESSION"):
        raise ValueError("invalid fidelity_gain")
    if comparison["canonical_geometry"] not in ("PROMOTED", "BASELINE", "UNDECIDED"):
        raise ValueError("invalid canonical_geometry")
    if comparison["canonical_geometry"] == "PROMOTED" and (review["decision"] != "PASS" or comparison["fidelity_gain"] != "CONFIRMED"):
        raise ValueError("PROMOTED requires PASS and confirmed fidelity gain")
    if comparison["fidelity_gain"] == "REGRESSION" and review["decision"] != "REVISE":
        raise ValueError("REGRESSION requires REVISE")
    observations = comparison["observations"]
    regions = {"body_surface", "sign_border", "tail", "wings", "feet", "beak", "fine_details"}
    if not isinstance(observations, dict) or set(observations) != {"identity", "gross_shape", "coverage", "new_defects", "cost", "regions"}:
        raise ValueError("promotion observations are incomplete")
    for name in ("identity", "gross_shape", "coverage", "new_defects", "cost"):
        if not isinstance(observations[name], str) or not observations[name].strip():
            raise ValueError(f"promotion observation {name} is empty")
    if not isinstance(observations["regions"], dict) or set(observations["regions"]) != regions:
        raise ValueError("promotion region observations are incomplete")
    for item in observations["regions"].values():
        if (not isinstance(item, dict) or set(item) != {"status", "note"}
                or item["status"] not in ("IMPROVED", "SAME", "WORSE", "UNCLEAR")
                or not isinstance(item["note"], str) or not item["note"].strip()):
            raise ValueError("invalid promotion region observation")

    baseline = comparison["baseline"]
    if not isinstance(baseline, dict) or set(baseline) != {"task_id", "prompt_id", "plan", "report", "glb_path", "glb_sha256"}:
        raise ValueError("baseline fields are invalid")
    baseline_plan = json.loads(project_file(baseline["plan"]).read_text(encoding="utf-8"))
    baseline_report = json.loads(project_file(baseline["report"]).read_text(encoding="utf-8"))
    outputs = baseline_report.get("outputs", [])
    if (baseline_report.get("status") != "SUCCESS" or baseline_plan.get("task_id") != baseline["task_id"]
            or baseline_report.get("task_id") != baseline["task_id"] or baseline_report.get("prompt_id") != baseline["prompt_id"]
            or len(outputs) != 1 or outputs[0].get("type") != "geometry"
            or outputs[0].get("path") != baseline["glb_path"] or outputs[0].get("sha256") != baseline["glb_sha256"]):
        raise ValueError("baseline identity or report output differs")
    baseline_file = Path(baseline["glb_path"])
    if not baseline_file.is_file() or file_hash(baseline_file) != baseline["glb_sha256"]:
        raise ValueError("baseline GLB changed or is missing")
    if len(promoted_report.get("outputs", [])) != 1 or promoted_report["outputs"][0].get("type") != "geometry":
        raise ValueError("promoted output must be one GLB")

    preview = comparison["preview"]
    if not isinstance(preview, dict) or set(preview) != {"path", "sha256"}:
        raise ValueError("preview fields are invalid")
    preview_path = project_file(preview["path"])
    if file_hash(preview_path) != preview["sha256"]:
        raise ValueError("comparison preview changed")
    decision = json.loads(project_file(comparison["promotion_decision"]).read_text(encoding="utf-8"))
    if (decision.get("baseline", {}).get("glb_sha256") != baseline["glb_sha256"]
            or decision.get("promotion", {}).get("glb_sha256") != review["reviewed_outputs"][0]["sha256"]
            or decision.get("preview", {}).get("sha256") != preview["sha256"]):
        raise ValueError("M6a decision lineage differs")

    baseline_graph = validate_plan(baseline_plan, DEFAULT_COMFY_ROOT)
    promoted_plan = json.loads(project_file(review["plan"]).read_text(encoding="utf-8"))
    promoted_graph = validate_plan(promoted_plan, DEFAULT_COMFY_ROOT)
    if baseline_plan["workflow"] != promoted_plan["workflow"] or baseline_graph.keys() != promoted_graph.keys():
        raise ValueError("geometry workflow changed")
    changes = {(node_id, name): (value, promoted_graph[node_id]["inputs"].get(name))
               for node_id, node in baseline_graph.items() for name, value in node["inputs"].items()
               if value != promoted_graph[node_id]["inputs"].get(name)}
    if (set(changes) != {("15", "octree_resolution"), ("17", "filename_prefix")}
            or changes[("15", "octree_resolution")] != (128, 192)):
        raise ValueError("geometry control comparison differs")
    manifest = json.loads(project_file(decision["promotion"]["input_manifest"]).read_text(encoding="utf-8"))
    for item in manifest["selected_inputs"]:
        source = PROJECT.parents[1] / item["source"]
        staged = DEFAULT_COMFY_ROOT / "work" / "input" / item["staged_input"]
        if (not source.is_file() or not staged.is_file() or file_hash(source) != item["sha256"]
                or file_hash(staged) != item["sha256"]):
            raise ValueError("source input lineage changed")


def validate(review):
    if not isinstance(review, dict) or set(review) not in (FIELDS, FIELDS | {PROMOTION_FIELD}):
        raise ValueError("review has missing or extra fields")
    if review["schema_version"] != "0.1" or review["reviewer"] != "Codex":
        raise ValueError("unsupported schema_version or reviewer")
    if review["decision"] not in ("PASS", "REVISE"):
        raise ValueError("decision must be PASS or REVISE")
    try:
        reviewed_at = datetime.fromisoformat(review["reviewed_at"].replace("Z", "+00:00"))
        if reviewed_at.tzinfo is None:
            raise ValueError("timezone is required")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("reviewed_at must be an ISO timestamp") from exc
    for name in ("blocking_issues", "requested_actions", "notes"):
        nonempty_strings(review[name], name)
    if review["decision"] == "PASS" and (review["blocking_issues"] or review["requested_actions"]):
        raise ValueError("PASS cannot contain blockers or requested actions")
    if review["decision"] == "REVISE" and (not review["blocking_issues"] or not review["requested_actions"]):
        raise ValueError("REVISE requires a blocker and a requested action")

    plan = json.loads(project_file(review["plan"]).read_text(encoding="utf-8"))
    report = json.loads(project_file(review["execution_report"]).read_text(encoding="utf-8"))
    if report.get("status") != "SUCCESS":
        raise ValueError("only a successful Execution Report can receive a quality review")
    if not isinstance(review["task_id"], str) or not isinstance(review["prompt_id"], str):
        raise ValueError("task_id and prompt_id must be strings")
    if (review["task_id"] != plan.get("task_id") or review["task_id"] != report.get("task_id")
            or review["prompt_id"] != report.get("prompt_id")
            or plan.get("workflow") != report.get("workflow")):
        raise ValueError("review, plan, and report identities differ")

    expected = report.get("outputs")
    observed = review["reviewed_outputs"]
    if not isinstance(expected, list) or not expected or not isinstance(observed, list) or len(observed) != len(expected):
        raise ValueError("reviewed_outputs must match all report outputs")
    for output, item in zip(expected, observed):
        if not isinstance(item, dict) or set(item) != {"path", "sha256"} or item["path"] != output.get("path"):
            raise ValueError("reviewed output path differs from the Execution Report")
        if not isinstance(item["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            raise ValueError("reviewed output hash is invalid")
        path = Path(item["path"])
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"reviewed output file changed or is missing: {path}")
    if any(output.get("type") == "geometry" for output in expected) and review["decision"] == "REVISE":
        for action in review["requested_actions"]:
            if action.startswith("ADD_VIEW: "):
                if not re.search(r"\bregion=[^;]+; reason=\S", action):
                    raise ValueError("ADD_VIEW requires a missing region and reason")
            elif action.startswith("REBUILD_GEOMETRY: "):
                if not re.search(r"\breason=\S", action):
                    raise ValueError("REBUILD_GEOMETRY requires a geometry-level reason")
            else:
                raise ValueError("geometry action must be ADD_VIEW or REBUILD_GEOMETRY")
    if PROMOTION_FIELD in review:
        validate_promotion(review[PROMOTION_FIELD], review, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review", type=Path)
    args = parser.parse_args()
    try:
        review = json.loads(args.review.read_text(encoding="utf-8"))
        report = validate(review)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"INVALID {exc}", file=sys.stderr)
        return 1
    print(f"VALID decision={review['decision']} task_id={report['task_id']} prompt_id={report['prompt_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
