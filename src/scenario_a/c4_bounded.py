"""One C4 run: record a single Worker, Review once, then resolve one terminal."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import c1_delegate as delegate
import c2_review
import result_review_adapter as reviewer


ROOT = delegate.ROOT


def repo_ref(path):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("evidence path is outside repository")
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": delegate.digest(path)}


def read_ref(ref):
    return json.loads(reviewer.checked_ref(ref).read_text(encoding="utf-8"))


def terminal_path(run_id):
    return ROOT / "runs" / (run_id + "_terminal.json")


def worker_state_path(run_id):
    return ROOT / "runs" / (run_id + "_worker_state.json")


def write_once(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def initial_contract(order):
    contract = read_ref(order["bounded_contract"])
    if (contract.get("version") != "c4.0" or contract.get("run_id") != order["run_id"]
            or contract.get("state") != "SOURCE_READY" or contract.get("terminal") is not False
            or contract.get("terminal_status") is not None
            or contract.get("latest_artifact") is not None
            or contract.get("latest_review") is not None
            or contract.get("source") != order["source"]
            or contract.get("workflow") != order["workflow"]
            or contract.get("requested_task") != order["requested_task"]
            or contract.get("worker_budget") != {"limit": 1, "consumed": 0, "remaining": 1}
            or contract.get("reviewer_budget") != {"limit": 1, "consumed": 0, "remaining": 1}):
        raise ValueError("initial bounded contract differs")
    datetime.fromisoformat(contract["created_at"])
    return contract


def run_worker(order_path):
    order, _, _, _, _ = delegate.preflight(order_path)
    if order["version"] != "c4.0" or terminal_path(order["run_id"]).exists():
        raise ValueError("ALREADY_TERMINAL or wrong C4 Work Order")
    contract = initial_contract(order)
    if worker_state_path(order["run_id"]).exists():
        raise ValueError("Worker budget already consumed")
    execution = delegate.run(order_path)
    if datetime.fromisoformat(execution["started_at"]) < datetime.fromisoformat(contract["created_at"]):
        raise ValueError("Worker started before budget declaration")
    artifact = execution["artifact"]
    state = {
        "version": "c4.0", "run_id": order["run_id"], "state": "REVIEW_READY",
        "initial_contract": order["bounded_contract"],
        "work_order": repo_ref(order_path),
        "execution_report": repo_ref(ROOT / order["execution_report_path"]),
        "latest_artifact": {"path": artifact["path"], "sha256": artifact["sha256"]},
        "worker_budget": {"limit": 1, "consumed": 1, "remaining": 0},
        "reviewer_budget": {"limit": 1, "consumed": 0, "remaining": 1},
        "terminal": False,
    }
    write_once(worker_state_path(order["run_id"]), state)
    return execution


def validate_review_request(request):
    order, execution = c2_review.validate_c1_lineage(request)
    if request["request_version"] != "0.3" or not request["run_id"].startswith("m4-c4-"):
        raise ValueError("C4 Review Request version or run differs")
    contract = initial_contract(order)
    state = read_ref(request["worker_state"])
    artifact = execution["artifact"]
    if (order["version"] != "c4.0" or request["bounded_contract"] != order["bounded_contract"]
            or execution.get("bounded_contract") != order["bounded_contract"]
            or state.get("version") != "c4.0" or state.get("run_id") != order["run_id"]
            or state.get("state") != "REVIEW_READY" or state.get("terminal") is not False
            or state.get("initial_contract") != order["bounded_contract"]
            or state.get("work_order") != request["work_order"]
            or state.get("execution_report") != request["source_result"]
            or state.get("latest_artifact") != {"path": artifact["path"], "sha256": artifact["sha256"]}
            or state.get("worker_budget") != {"limit": 1, "consumed": 1, "remaining": 0}
            or state.get("reviewer_budget") != {"limit": 1, "consumed": 0, "remaining": 1}
            or datetime.fromisoformat(execution["started_at"]) < datetime.fromisoformat(contract["created_at"])):
        raise ValueError("C4 budget, Worker, or Review lineage differs")
    return order, execution, state


def run_review(request_path, result_path, report_path):
    request = json.loads(Path(request_path).read_text(encoding="utf-8"))
    order, _, state = validate_review_request(request)
    if terminal_path(order["run_id"]).exists():
        raise ValueError("ALREADY_TERMINAL")
    if state["reviewer_budget"]["remaining"] < 1:
        raise ValueError("Reviewer budget exhausted")
    return reviewer.review_once(request_path, result_path, report_path, timeout=600)


def terminal_policy(review, worker_remaining):
    verdict = review["verdict"]
    if verdict == "PASS":
        if review["blocking_issues"] or review["suggested_action"] != {"code": "NONE", "target": None}:
            raise ValueError("PASS evidence differs")
        return "DELIVERED", "INTERNAL_ACCEPT", True
    if verdict == "REVISE":
        if not review["blocking_issues"] or worker_remaining != 0:
            raise ValueError("REVISE budget or blocker differs")
        return "ABORT", "BUDGET_EXHAUSTED_AFTER_REVISE", False
    if verdict == "HUMAN_REQUIRED":
        return "ABORT", "HUMAN_REQUIRED", False
    raise ValueError("unsupported Review verdict")


def resolve_terminal(request_path, result_path, report_path):
    request_path, result_path, report_path = map(Path, (request_path, result_path, report_path))
    request = json.loads(request_path.read_text(encoding="utf-8"))
    target = terminal_path(request["run_id"])
    if target.exists():
        return "ALREADY_TERMINAL", None
    order, execution, state = validate_review_request(request)
    source = {"kind": "RESULT_REVIEW", "path": repo_ref(result_path)["path"],
              "sha256": delegate.digest(result_path),
              "request_path": repo_ref(request_path)["path"],
              "request_sha256": delegate.digest(request_path),
              "invocation_report_path": repo_ref(report_path)["path"],
              "invocation_report_sha256": delegate.digest(report_path)}
    _, review = reviewer.checked_invocation(source)
    invocation = read_ref(repo_ref(report_path))
    attachments = [{key: artifact[key] for key in ("role", "path", "sha256")}
                   for artifact in request["artifacts"]]
    if (invocation.get("reviewer_mode") != "CODEX_CLI"
            or invocation.get("auth_mode") != "CHATGPT_ACCOUNT"
            or invocation.get("process_exit_code") != 0
            or invocation.get("attached_images") != attachments
            or invocation.get("reviewer_process_started") is not True):
        raise ValueError("actual Reviewer invocation differs")
    status, reason, accepted = terminal_policy(review, state["worker_budget"]["remaining"])
    artifact = {"path": execution["artifact"]["path"],
                "sha256": execution["artifact"]["sha256"]}
    terminal = {
        "version": "c4.0", "run_id": order["run_id"], "terminal": True,
        "terminal_status": status, "termination_reason": reason,
        "initial_contract": request["bounded_contract"],
        "work_order": request["work_order"],
        "execution_report": request["source_result"],
        "artifact": artifact,
        "worker_state": request["worker_state"],
        "review_request": repo_ref(request_path),
        "review_result": repo_ref(result_path),
        "review_invocation_report": repo_ref(report_path),
        "worker_budget": state["worker_budget"],
        "reviewer_budget": {"limit": 1, "consumed": 1, "remaining": 0},
        "internal_accept": accepted,
        "transitions": ["INTERNAL_ACCEPT", "DELIVERED"] if accepted else ["ABORT"],
        "delivered_artifact": artifact if accepted else None,
        "delivery_channel": "final_response" if accepted else None,
        "terminal_at": datetime.now(timezone.utc).isoformat(),
    }
    if any(b["consumed"] > b["limit"] or b["remaining"] != b["limit"] - b["consumed"]
           for b in (terminal["worker_budget"], terminal["reviewer_budget"])):
        raise ValueError("terminal budget invariant differs")
    write_once(target, terminal)
    return status, terminal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    command = parser.add_subparsers(dest="command", required=True)
    worker_cmd = command.add_parser("worker")
    worker_cmd.add_argument("--work-order", type=Path, required=True)
    for name in ("review", "terminal"):
        sub = command.add_parser(name)
        sub.add_argument("--request", type=Path, required=True)
        sub.add_argument("--result", type=Path, required=True)
        sub.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "worker":
            execution = run_worker(args.work_order)
            print("C4_WORKER_SUCCESS " + execution["prompt_id"])
            return 0
        if args.command == "review":
            report = run_review(args.request, args.result, args.report)
            print("C4_REVIEW " + report["invocation_status"])
            return 0 if report["invocation_status"] == "SUCCESS" else 1
        status, _ = resolve_terminal(args.request, args.result, args.report)
        print("C4_TERMINAL " + status)
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("C4_BLOCKED " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
