"""Validate a fresh C3 initial execution before one right-view Reviewer call."""

import argparse
import json
import sys
from pathlib import Path

from core import result_review_adapter as reviewer
from scenario_a import c2_review


CRITERIA = [
    "Preserve the source penguin and sign identity and structure.",
    "Show a plausible right-side camera change.",
    "Keep the complete object visible and centered on the 768 by 768 canvas.",
    "Keep the subject at approximately the source image scale; do not zoom in.",
    "Avoid blocking distortion or detached elements.",
]


def validate_request(request):
    order, execution = c2_review.validate_c1_lineage(request, CRITERIA)
    if not request["run_id"].startswith("m3-c3-") or order["iteration"] != 0:
        raise ValueError("C3 initial identity differs")
    plan = c2_review.read_ref(order["plan"])
    if plan["patches"]["8"]["prompt"] != (
        "Rotate the camera 45 degrees to the right. Keep the entire object visible, "
        "centered and at the same scale. Do not zoom in."
    ) or plan["patches"]["11"]["seed"] != 29481:
        raise ValueError("C3 challenge configuration differs")
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
        validate_request(request)
        if args.result.exists() or args.report.exists():
            raise ValueError("Review result or report already exists")
        if args.preflight:
            print("C3_REVIEW_PREFLIGHT_VALID " + request["review_id"])
            return 0
        report = reviewer.review_once(args.request, args.result, args.report, timeout=600)
        print("C3_REVIEW " + report["invocation_status"] + " " + request["review_id"])
        return 0 if report["invocation_status"] == "SUCCESS" else 1
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("C3_REVIEW_BLOCKED " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
