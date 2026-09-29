"""Minimal Worker execution boundary shared by interchangeable adapters."""

import hashlib
import re
from pathlib import Path


ORDER_FIELDS = {"version", "run_id", "work_order_id", "requested_task",
                "expected_output_kind", "adapter_id", "payload"}
RESULT_FIELDS = {"version", "run_id", "work_order_id", "adapter_id", "backend",
                 "status", "invocation_id", "artifact", "execution_seconds"}
ARTIFACT_FIELDS = {"path", "kind", "bytes", "sha256"}


def execute(adapter, work_order):
    """Call the injected adapter once, then verify its common result and artifact."""
    if not isinstance(work_order, dict) or set(work_order) != ORDER_FIELDS or work_order["version"] != "c5.0":
        raise ValueError("Worker Work Order fields differ")
    for key in ("run_id", "work_order_id", "adapter_id"):
        if not isinstance(work_order[key], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", work_order[key]):
            raise ValueError("Worker Work Order identity differs")
    if (not isinstance(work_order["requested_task"], str) or not work_order["requested_task"]
            or not isinstance(work_order["expected_output_kind"], str) or not work_order["expected_output_kind"]
            or not isinstance(work_order["payload"], dict) or not work_order["payload"]
            or getattr(adapter, "adapter_id", None) != work_order["adapter_id"]
            or not callable(adapter)):
        raise ValueError("Worker adapter or task differs")
    result = adapter(work_order)
    if not isinstance(result, dict) or set(result) != RESULT_FIELDS or result["version"] != "c5.0":
        raise ValueError("Worker Result fields differ")
    if (result["run_id"] != work_order["run_id"]
            or result["work_order_id"] != work_order["work_order_id"]
            or result["adapter_id"] != work_order["adapter_id"]
            or result["status"] != "SUCCESS"
            or not isinstance(result["backend"], str) or not result["backend"]
            or not isinstance(result["invocation_id"], str) or not result["invocation_id"]
            or type(result["execution_seconds"]) not in (int, float)
            or result["execution_seconds"] < 0):
        raise ValueError("Worker Result identity or status differs")
    artifact = result["artifact"]
    if (not isinstance(artifact, dict) or set(artifact) != ARTIFACT_FIELDS
            or artifact["kind"] != work_order["expected_output_kind"]
            or type(artifact["bytes"]) is not int or artifact["bytes"] <= 0
            or not isinstance(artifact["sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
            or not isinstance(artifact["path"], str)):
        raise ValueError("Worker artifact fields differ")
    path = Path(artifact["path"])
    if not path.is_absolute() or not path.is_file() or path.stat().st_size != artifact["bytes"]:
        raise ValueError("Worker artifact path or size differs")
    if hashlib.sha256(path.read_bytes()).hexdigest() != artifact["sha256"]:
        raise ValueError("Worker artifact hash differs")
    return result
