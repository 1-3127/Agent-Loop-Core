"""Validate Scenario A's A-C4 evidence before the generic result review."""

import argparse
import copy
import json
import sys
from pathlib import Path

import pipeline_a_controller as controller
import result_review_adapter as generic


def validate_ac4(request):
    generic.validate_request(request)
    decision = json.loads(generic.checked_ref(request["previous_decision"]).read_text(encoding="utf-8"))
    receipt = json.loads(generic.checked_ref(request["invocation"]).read_text(encoding="utf-8"))
    report = json.loads(generic.checked_ref(request["source_result"]).read_text(encoding="utf-8"))
    state_file = json.loads(generic.checked_ref(request["state"]).read_text(encoding="utf-8"))
    state = state_file["state"]
    controller.validate_state(state)
    context = request["context"]
    if (set(context) != {"performed_action", "acceptance_criteria"} or
            not isinstance(context["performed_action"], dict) or set(context["performed_action"]) != {"code", "target"} or
            context["performed_action"] != {"code": decision.get("action"), "target": decision.get("target")} or
            not isinstance(context["acceptance_criteria"], list) or not context["acceptance_criteria"] or
            any(not isinstance(x, str) or not x.strip() for x in context["acceptance_criteria"])):
        raise ValueError("Scenario A review context differs")
    if (decision.get("controller_decision") != "EXECUTE" or decision.get("return_review_state") != request["stage"] or
            receipt.get("controller_decision_sha256") != request["previous_decision"]["sha256"] or
            receipt.get("execution_report_sha256") != request["source_result"]["sha256"] or
            receipt.get("status") != report.get("status") or report.get("status") != "SUCCESS" or
            receipt.get("prompt_id") != report.get("prompt_id") or receipt.get("client_id") != report.get("client_id") or
            receipt.get("action_consumed") is not True):
        raise ValueError("A-C4 Decision/receipt/Result lineage differs")
    outputs = report.get("outputs", [])
    artifacts = request["artifacts"]
    if (len(outputs) != 1 or len(artifacts) != 2 or len(receipt.get("outputs", [])) != 1 or
            outputs[0].get("type") != "image" or artifacts[0]["role"] != "generated_output" or artifacts[0]["media_type"] != "image/png" or
            Path(artifacts[0]["path"]).resolve() != Path(outputs[0].get("path", "")).resolve() or
            artifacts[0]["sha256"] != receipt["outputs"][0].get("sha256") or
            Path(artifacts[0]["path"]).resolve() != Path(receipt["outputs"][0].get("path", "")).resolve()):
        raise ValueError("A-C4 Artifact/Result lineage differs")
    plan = json.loads(Path(receipt["plan_path"]).read_text(encoding="utf-8"))
    source = Path("D:/VSCODE-WorkSpace/Comfy-UI/work/input") / plan["patches"]["1"]["image"]
    if (generic.digest(Path(receipt["plan_path"])) != receipt["plan_sha256"] or
            artifacts[1]["role"] != "source_reference" or artifacts[1]["path"] != source.as_posix() or
            artifacts[1]["sha256"] != generic.digest(source)):
        raise ValueError("source reference differs from A-C4 Plan")
    if (state["current_state"] != request["stage"] or decision["target"] not in state["used_views"] or
            state["latest_artifact"] != {"path": artifacts[0]["path"], "sha256": artifacts[0]["sha256"]} or
            state_file.get("basis_decision") != request["previous_decision"] or
            state_file.get("basis_invocation") != request["invocation"] or
            state_file.get("basis_result") != request["source_result"]):
        raise ValueError("Scenario state reference differs")
    prior_input_path = Path(receipt["controller_input_path"])
    prior_input = json.loads(prior_input_path.read_text(encoding="utf-8"))
    if generic.digest(prior_input_path) != receipt["controller_input_sha256"]:
        raise ValueError("prior Controller Input hash differs")
    expected = copy.deepcopy(prior_input["state"])
    expected["current_state"] = decision["return_review_state"]
    expected["iteration_count"] += 1
    expected["used_views"].append(decision["target"])
    expected["action_counts"][decision["action"]] += 1
    expected["action_history"].append({"code": decision["action"], "target": decision["target"], "blocker_code": None, "region": None})
    expected["latest_artifact"] = {"path": artifacts[0]["path"], "sha256": artifacts[0]["sha256"]}
    if state_file.get("classification") != "DERIVED_FROM_SYNTHETIC_POLICY_FIXTURE" or state != expected:
        raise ValueError("derived state differs from previous synthetic state and actual result")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    try:
        request = json.loads(args.request.read_text(encoding="utf-8"))
        validate_ac4(request)
        report = generic.review_once(args.request, args.result, args.report, args.timeout)
        print(f"A-C5 REVIEW {report['invocation_status']} review_id={report['review_id']}")
        return 0 if report["invocation_status"] == "SUCCESS" else 1
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"INVALID {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
