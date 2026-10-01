"""One generic, evidence-bound semantic review; no controller or executor call."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from core.reviewer_auth import auth_mode


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "result_review_schema.json"
REF = {"path", "sha256"}
ARTIFACT = {"role", "path", "sha256", "media_type"}
REQUEST = {"request_version", "review_id", "stage", "output_kind", "source_result", "previous_decision", "invocation", "state", "artifacts", "instruction_file", "context"}
REQUEST_C2 = {"request_version", "run_id", "review_id", "stage", "output_kind", "source_result", "work_order", "worker_report", "artifacts", "instruction_file", "context"}
REQUEST_C4 = REQUEST_C2 | {"bounded_contract", "worker_state"}
RESULT = {"review_version", "review_id", "stage", "source_result", "artifacts", "verdict", "blocking_issues", "observations", "suggested_action"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked_ref(ref):
    if not isinstance(ref, dict) or set(ref) != REF or not re.fullmatch(r"[0-9a-f]{64}", str(ref["sha256"])):
        raise ValueError("invalid file reference")
    path = Path(ref["path"])
    path = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    if not path.is_file() or digest(path) != ref["sha256"]:
        raise ValueError("file reference missing or hash differs")
    return path


def validate_request(item):
    if not isinstance(item, dict):
        raise ValueError("review request fields differ")
    version = item.get("request_version")
    if (version == "0.1" and set(item) != REQUEST) or (version == "0.2" and set(item) != REQUEST_C2) or (version == "0.3" and set(item) != REQUEST_C4) or version not in ("0.1", "0.2", "0.3"):
        raise ValueError("review request fields differ")
    if any(not isinstance(item[k], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", item[k]) for k in ("review_id", "stage")):
        raise ValueError("review identity differs")
    if version in ("0.2", "0.3") and (not isinstance(item["run_id"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", item["run_id"])):
        raise ValueError("review run identity differs")
    if not isinstance(item["output_kind"], str) or not item["output_kind"]:
        raise ValueError("output kind missing")
    refs = ("source_result", "previous_decision", "invocation", "state", "instruction_file") if version == "0.1" else ("source_result", "work_order", "worker_report", "instruction_file")
    for key in refs:
        checked_ref(item[key])
    if version == "0.3":
        checked_ref(item["bounded_contract"])
        checked_ref(item["worker_state"])
    if not isinstance(item["context"], dict) or not item["context"]:
        raise ValueError("review context missing")
    artifacts = item["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("artifacts required")
    for artifact in artifacts:
        if not isinstance(artifact, dict) or set(artifact) != ARTIFACT or not isinstance(artifact["role"], str) or not artifact["role"] or not isinstance(artifact["media_type"], str) or not artifact["media_type"]:
            raise ValueError("invalid artifact reference")
        checked_ref({k: artifact[k] for k in REF})
    return item


def validate_result(item, request):
    if not isinstance(item, dict) or set(item) != RESULT or item["review_version"] != "0.3":
        raise ValueError("review result fields differ")
    if item["review_id"] != request["review_id"] or item["stage"] != request["stage"] or item["source_result"] != request["source_result"] or item["artifacts"] != request["artifacts"]:
        raise ValueError("review source identity differs")
    for key in ("source_result",):
        checked_ref(item[key])
    for artifact in item["artifacts"]:
        checked_ref({k: artifact[k] for k in REF})
    if item["verdict"] not in ("PASS", "REVISE", "HUMAN_REQUIRED"):
        raise ValueError("unsupported verdict")
    blockers, notes, action = item["blocking_issues"], item["observations"], item["suggested_action"]
    if not isinstance(blockers, list) or not isinstance(notes, list) or any(not isinstance(x, str) or not x.strip() for x in blockers + notes):
        raise ValueError("invalid review evidence")
    if request["request_version"] in ("0.2", "0.3") and not notes:
        raise ValueError("C2 review needs visual observations")
    if not isinstance(action, dict) or set(action) != {"code", "target"} or not isinstance(action["code"], str) or not action["code"] or action["target"] is not None and (not isinstance(action["target"], str) or not action["target"]):
        raise ValueError("invalid suggested action")
    if item["verdict"] == "PASS" and (blockers or action != {"code": "NONE", "target": None}):
        raise ValueError("PASS cannot request action")
    if item["verdict"] == "REVISE" and (not blockers or action["code"] == "NONE"):
        raise ValueError("REVISE needs a blocker and proposed action")
    if item["verdict"] == "HUMAN_REQUIRED" and action != {"code": "HUMAN_REQUIRED", "target": None}:
        raise ValueError("uncertain review cannot request execution")
    return item


def checked_invocation(source):
    fields = {"kind", "path", "sha256", "request_path", "request_sha256", "invocation_report_path", "invocation_report_sha256"}
    if not isinstance(source, dict) or set(source) != fields or source["kind"] != "RESULT_REVIEW":
        raise ValueError("review source fields differ")
    review_path = checked_ref({"path": source["path"], "sha256": source["sha256"]})
    request_path = checked_ref({"path": source["request_path"], "sha256": source["request_sha256"]})
    report_path = checked_ref({"path": source["invocation_report_path"], "sha256": source["invocation_report_sha256"]})
    request = validate_request(json.loads(request_path.read_text(encoding="utf-8")))
    review = validate_result(json.loads(review_path.read_text(encoding="utf-8")), request)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    mode = report.get("reviewer_mode")
    if mode not in ("CODEX_CLI", "CURRENT_SESSION") or report.get("reviewer_process_started") is not (mode == "CODEX_CLI"):
        raise ValueError("reviewer mode differs")
    if mode == "CURRENT_SESSION" and report.get("external_transfer_performed") is not False:
        raise ValueError("current-session review transfer status differs")
    if (report.get("invocation_status") != "SUCCESS" or report.get("request_sha256") != source["request_sha256"] or
            report.get("result_sha256") != source["sha256"] or Path(report.get("result_path", "")).resolve() != review_path or
            report.get("review_id") != review["review_id"] or report.get("verdict") != review["verdict"]):
        raise ValueError("review invocation identity differs")
    return request, review



# Evidence is bounded independently of the complete stdout used for Result validation.
STREAM_EVIDENCE_CAP = 65536
_CREDENTIAL_NAME = r"(?:[\w-]*(?:api[_-]?key|token|secret|password|passwd|authorization|cookie|credential)[\w-]*|[\w-]*_key)"
_CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?im)(?<![\w-])([\"']?" + _CREDENTIAL_NAME + r"[\"']?\s*[:=]\s*)"
    r'''(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\r\n]+)''')


def _sanitized_stream(text):
    """Bounded Reviewer evidence redaction; never read credential files."""
    original = text
    # Remove obvious inherited credential values, including bare values in errors.
    values = {value for key, value in os.environ.items()
              if value and re.fullmatch(_CREDENTIAL_NAME, key, re.IGNORECASE)}
    for value in sorted(values, key=lambda item: (-len(item), item)):
        text = text.replace(value, "[REDACTED]")
    text = _CREDENTIAL_ASSIGNMENT.sub(lambda match: match[1] + '"[REDACTED]"', text)
    text = re.sub(r"(?i)\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+", "[REDACTED]", text)
    text = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[REDACTED]", text)
    text = re.sub(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[REDACTED]", text)
    text = re.sub(r"(?i)(https?://)[^\s/@:]+:[^\s/@]+@", r"\1[REDACTED]@", text)
    text = re.sub(r"(?s)-----BEGIN [^-\r\n]*PRIVATE KEY-----.*?-----END [^-\r\n]*PRIVATE KEY-----",
                  "[REDACTED]", text)
    return text, text != original


def _decoded_stream(raw):
    # Preserve text-mode universal-newline behavior for validation and legacy hashes.
    return raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


def _stream_evidence(raw, path, complete):
    decoded = _decoded_stream(raw)
    try:
        raw.decode("utf-8", errors="strict")
        replaced = False
    except UnicodeDecodeError:
        replaced = True
    sanitized, redacted = _sanitized_stream(decoded)
    payload = sanitized.encode("utf-8")
    # Do not split a UTF-8 character at the deterministic prefix boundary.
    saved = payload[:STREAM_EVIDENCE_CAP].decode("utf-8", errors="ignore").encode("utf-8")
    with path.open("xb") as stream:
        stream.write(saved)
    return {"path": str(path.resolve()), "sha256": hashlib.sha256(saved).hexdigest(),
            "bytes": len(saved), "raw_bytes": len(raw), "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "decoded_bytes": len(decoded.encode("utf-8")), "sanitized_bytes": len(payload),
            "encoding": "utf-8", "decode_errors": "replace", "decode_replacement": replaced,
            "newline_normalization": "universal", "redacted": redacted,
            "truncated": len(payload) > STREAM_EVIDENCE_CAP, "cap_bytes": STREAM_EVIDENCE_CAP,
            "capture_complete": complete}


def review_once(request_path, result_path, report_path, timeout=300, workspace=None):
    request_path, result_path, report_path = map(Path, (request_path, result_path, report_path))
    request = validate_request(json.loads(request_path.read_text(encoding="utf-8")))
    evidence_paths = {name: report_path.with_name(report_path.name + "." + name + ".txt")
                      for name in ("stdout", "stderr")}
    if result_path.exists() or report_path.exists() or any(path.exists() for path in evidence_paths.values()):
        raise ValueError("review result/report exists; refusing repeat")
    mode = auth_mode(os.environ)
    if mode != "CHATGPT_ACCOUNT":
        raise ValueError("BLOCKED_BY_AUTH_MODE: " + mode)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with result_path.open("x", encoding="utf-8"):
        pass
    try:
        with report_path.open("x", encoding="utf-8") as stream:
            json.dump({"review_id": request["review_id"], "reviewer_mode": "CODEX_CLI", "invocation_status": "UNRESOLVED", "request_sha256": digest(request_path), "result_path": str(result_path.resolve()), "reviewer_process_started": False}, stream, indent=2)
            stream.write("\n")
    except BaseException:
        result_path.unlink(missing_ok=True)
        raise
    report = json.loads(report_path.read_text(encoding="utf-8"))
    prompt = checked_ref(request["instruction_file"]).read_text(encoding="utf-8") + "\n\nREQUEST JSON:\n" + json.dumps(request, ensure_ascii=False, indent=2)
    cli_workspace = Path(workspace).resolve() if workspace is not None else ROOT
    if not cli_workspace.is_dir():
        raise ValueError("Reviewer workspace missing")
    args = ["codex", "exec", "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only", "--output-schema", str(SCHEMA), "-C", str(cli_workspace)]
    attached_images = []
    for artifact in request["artifacts"]:
        if artifact["media_type"].startswith("image/"):
            image_path = checked_ref({k: artifact[k] for k in REF})
            args += ["-i", str(image_path)]
            attached_images.append({"role": artifact["role"], "path": str(image_path), "sha256": artifact["sha256"]})
    args += ["-"]
    report.update(auth_mode=mode, attached_images=attached_images, reviewer_process_started=True,
                  started_at=datetime.now(timezone.utc).isoformat())
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    started = time.monotonic()
    stdout_raw, stderr_raw, capture_complete = b"", b"", False
    report["process_exit_code"] = None
    try:
        proc = subprocess.run(args, input=prompt.replace("\n", os.linesep).encode("utf-8"), capture_output=True, timeout=timeout,
                              env=dict(os.environ, CODEX_HOME=os.environ.get("CODEX_HOME") or "C:/Users/Worker/.codex"))
        stdout_raw, stderr_raw, capture_complete = proc.stdout, proc.stderr, True
        stdout, stderr = _decoded_stream(stdout_raw), _decoded_stream(stderr_raw)
        report.update(process_exit_code=proc.returncode, stdout_sha256=hashlib.sha256(stdout.encode("utf-8")).hexdigest(), stderr_sha256=hashlib.sha256(stderr.encode("utf-8")).hexdigest())
        if proc.returncode != 0:
            report["invocation_status"] = "FAILED"
        else:
            try:
                result = validate_result(json.loads(stdout), request)
                result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                report.update(invocation_status="SUCCESS", result_sha256=digest(result_path), verdict=result["verdict"])
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                report.update(invocation_status="FAILED", validation_error=str(exc))
    except subprocess.TimeoutExpired as exc:
        stdout_raw, stderr_raw = exc.stdout or b"", exc.stderr or b""
        report["invocation_status"] = "UNRESOLVED"
    except OSError as exc:
        report.update(invocation_status="FAILED", reviewer_process_started=False,
                      launch_error=f"{type(exc).__name__}: {exc}")
    finally:
        for name, raw in (("stdout", stdout_raw), ("stderr", stderr_raw)):
            try:
                report[name + "_evidence"] = _stream_evidence(raw, evidence_paths[name], capture_complete)
            except OSError as exc:
                report[name + "_evidence_error"] = type(exc).__name__
        report.update(finished_at=datetime.now(timezone.utc).isoformat(),
                      duration_seconds=time.monotonic() - started)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    try:
        if args.timeout <= 0:
            raise ValueError("timeout must be positive")
        report = review_once(args.request, args.result, args.report, args.timeout)
        print(f"REVIEW {report['invocation_status']} review_id={report['review_id']}")
        return 0 if report["invocation_status"] == "SUCCESS" else 1
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"INVALID {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
