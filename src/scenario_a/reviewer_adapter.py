"""A-C2: one bounded, read-only Codex semantic review; no controller or ComfyUI dispatch."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMFY = Path("D:/VSCODE-WorkSpace/Comfy-UI").resolve()
SCHEMA = ROOT / "reviewer_result_schema.json"
ROLES = ["front_source", "right_m2", "right_m4a", "left_m4b"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_request(item):
    if not isinstance(item, dict) or set(item) != {"request_version", "task_id", "stage", "instruction_file", "artifacts", "supported_views"}:
        raise ValueError("invalid request fields")
    if item["request_version"] != "0.1" or item["stage"] != "MULTIVIEW_REVIEW" or not re.fullmatch(r"[a-z0-9-]{1,80}", str(item["task_id"])):
        raise ValueError("invalid request identity")
    if item["supported_views"] != ["right", "left", "back"]:
        raise ValueError("unsupported view capability")
    instruction = (ROOT / item["instruction_file"]).resolve()
    if instruction != (ROOT / "reviewer_requests/multiview_coverage_instructions.md").resolve() or not instruction.is_file():
        raise ValueError("instruction file is invalid")
    artifacts = item["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) != 4:
        raise ValueError("four artifacts required")
    for expected_role, artifact in zip(ROLES, artifacts):
        if not isinstance(artifact, dict) or set(artifact) != {"role", "path", "sha256"} or artifact["role"] != expected_role:
            raise ValueError("artifact role/fields invalid")
        path = Path(artifact["path"]).resolve()
        if not path.is_relative_to(COMFY) or not path.is_file() or path.suffix.lower() != ".png":
            raise ValueError("artifact missing or outside Comfy-UI")
        if not re.fullmatch(r"[0-9a-f]{64}", str(artifact["sha256"])) or digest(path) != artifact["sha256"]:
            raise ValueError("artifact SHA-256 differs")
    return instruction


def validate_result(result, request):
    if not isinstance(result, dict) or set(result) != {"review_version", "task_id", "stage", "artifacts", "decision", "blocking_issues", "controller_action", "observations"}:
        raise ValueError("invalid result fields")
    if result["review_version"] != "0.2" or result["task_id"] != request["task_id"] or result["stage"] != request["stage"]:
        raise ValueError("result identity differs")
    if result["artifacts"] != request["artifacts"]:
        raise ValueError("result artifact identity differs")
    if result["decision"] not in {"PASS", "REVISE", "HUMAN_REQUIRED"}:
        raise ValueError("unsupported semantic decision")
    blockers, notes, action = result["blocking_issues"], result["observations"], result["controller_action"]
    if not isinstance(blockers, list) or not isinstance(notes, list) or any(not isinstance(x, str) or not x.strip() for x in blockers + notes):
        raise ValueError("invalid observations or blockers")
    if not isinstance(action, dict) or set(action) != {"code", "target"}:
        raise ValueError("invalid normalized action")
    code, target = action["code"], action["target"]
    if result["decision"] == "PASS" and (blockers or code != "NONE" or target is not None):
        raise ValueError("PASS must have no blocker/action")
    if result["decision"] == "REVISE" and (not blockers or code not in {"ADD_VIEW", "REGENERATE_VIEW"} or not isinstance(target, str) or not target):
        raise ValueError("REVISE requires blocker and target-bearing normalized action")
    if result["decision"] == "HUMAN_REQUIRED" and (code != "HUMAN_REQUIRED" or target is not None):
        raise ValueError("uncertain result cannot request execution")
    if code == "ADD_VIEW" and target in {"right", "left"}:
        raise ValueError("ADD_VIEW target already represented")
    if code == "REGENERATE_VIEW" and target not in {"right", "left"}:
        raise ValueError("REGENERATE_VIEW target absent")
    return result


def auth_mode(env):
    if any(env.get(k) for k in ("OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_ACCESS_TOKEN", "OPENAI_FEDERATION_RULE_ID", "OPENAI_IDENTITY_TOKEN_FILE")):
        return "API_KEY"
    codex_home = env.get("CODEX_HOME") or str(Path("C:/Users/Worker/.codex"))
    probe_env = dict(env, CODEX_HOME=codex_home)
    status = subprocess.run(["codex", "login", "status"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20, env=probe_env)
    if status.returncode == 0 and "Logged in using ChatGPT" in (status.stdout + status.stderr):
        return "CHATGPT_ACCOUNT"
    return "UNKNOWN"


def review(request_path, result_path, report_path, timeout=300):
    request = json.loads(Path(request_path).read_text(encoding="utf-8"))
    instruction = validate_request(request)
    result_path, report_path = Path(result_path), Path(report_path)
    if result_path.exists() or report_path.exists():
        raise ValueError("result/report exists; refusing repeat or overwrite")
    mode = auth_mode(os.environ)
    if mode != "CHATGPT_ACCOUNT":
        raise ValueError("BLOCKED_BY_AUTH_MODE: " + mode)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    # Both paths are reserved before the only reviewer process starts.
    with result_path.open("x", encoding="utf-8"):
        pass
    try:
        with report_path.open("x", encoding="utf-8") as stream:
            json.dump({"task_id": request["task_id"], "invocation_status": "UNRESOLVED", "auth_mode": mode, "request_sha256": digest(Path(request_path)), "result_path": str(result_path), "reviewer_process_started": False}, stream, indent=2)
            stream.write("\n")
    except BaseException:
        result_path.unlink(missing_ok=True)
        raise
    report = json.loads(report_path.read_text(encoding="utf-8"))
    prompt = instruction.read_text(encoding="utf-8") + "\n\nREQUEST JSON:\n" + json.dumps(request, ensure_ascii=False, indent=2)
    args = ["codex", "exec", "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only", "--output-schema", str(SCHEMA), "-C", str(ROOT)]
    for artifact in request["artifacts"]:
        args += ["-i", artifact["path"]]
    args += ["-"]
    report["reviewer_process_started"] = True
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(args, input=prompt, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                              env=dict(os.environ, CODEX_HOME=os.environ.get("CODEX_HOME") or "C:/Users/Worker/.codex"))
        report.update(process_exit_code=proc.returncode, stdout_present=bool(proc.stdout.strip()), stderr_present=bool(proc.stderr.strip()),
                      stdout_bytes=len(proc.stdout.encode("utf-8")), stderr_bytes=len(proc.stderr.encode("utf-8")),
                      stdout_sha256=hashlib.sha256(proc.stdout.encode("utf-8")).hexdigest(),
                      stderr_sha256=hashlib.sha256(proc.stderr.encode("utf-8")).hexdigest())
        if proc.returncode != 0:
            report.update(invocation_status="FAILED", json_parse=False, schema_valid=False, task_identity_match=False, artifact_identity_match=False)
        else:
            try:
                value = json.loads(proc.stdout)
                report["json_parse"] = True
                report["task_identity_match"] = isinstance(value, dict) and value.get("task_id") == request["task_id"]
                report["artifact_identity_match"] = isinstance(value, dict) and value.get("artifacts") == request["artifacts"]
                validate_result(value, request)
                report.update(schema_valid=True, invocation_status="SUCCESS", semantic_decision=value["decision"], normalized_action=value["controller_action"])
                result_path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                report.update(invocation_status="FAILED", schema_valid=False, validation_error=str(exc))
    except subprocess.TimeoutExpired:
        report.update(invocation_status="UNRESOLVED", process_exit_code=None, stdout_present=False, stderr_present=False,
                      json_parse=False, schema_valid=False, task_identity_match=False, artifact_identity_match=False)
    finally:
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    try:
        if args.timeout <= 0:
            raise ValueError("timeout must be positive")
        report = review(args.request, args.result, args.report, args.timeout)
        print(f"A-C2 invocation={report['invocation_status']} exit={report.get('process_exit_code')} result={args.result}")
        return 0 if report["invocation_status"] == "SUCCESS" else 1
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"A-C2 preflight failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
