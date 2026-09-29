"""Run the two C5 Workers through one unchanged Core entry point."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/core"))
sys.path.insert(0, str(ROOT / "tests/fixtures"))

import worker_port
from comfy_worker_adapter import ComfyWorkerAdapter
from deterministic_worker import DeterministicTestWorker


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def load_order(path):
    path = path.resolve()
    if path.parent != (ROOT / "work_orders").resolve() or not path.is_file():
        raise ValueError("C5 Work Order path differs")
    return json.loads(path.read_text(encoding="utf-8"))


def reference(path):
    return {"path": str(path.resolve().relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(path)}


def run(proof_id):
    if not proof_id.startswith("m5-c5-"):
        raise ValueError("C5 proof identity differs")
    order_a_path = ROOT / "work_orders" / (proof_id + "-comfy.json")
    order_b_path = ROOT / "work_orders" / (proof_id + "-deterministic.json")
    order_a, order_b = load_order(order_a_path), load_order(order_b_path)
    if (order_a["run_id"] != proof_id + "-comfy"
            or order_b["run_id"] != proof_id + "-deterministic"
            or order_a["adapter_id"] != ComfyWorkerAdapter.adapter_id
            or order_b["adapter_id"] != DeterministicTestWorker.adapter_id):
        raise ValueError("C5 order identities differ")
    result_a_path = ROOT / "runs" / (proof_id + "-comfy_worker_result.json")
    result_b_path = ROOT / "runs" / (proof_id + "-deterministic_worker_result.json")
    evidence_path = ROOT / "runs" / (proof_id + "_c5_boundary.json")
    usage_path = ROOT / "usage" / (proof_id + ".json")
    if any(path.exists() for path in (result_a_path, result_b_path, evidence_path, usage_path)):
        raise ValueError("C5 proof namespace already consumed")

    core_path = Path(worker_port.__file__).resolve()
    entry = worker_port.execute
    before_a = digest(core_path)
    result_a = entry(ComfyWorkerAdapter(), order_a)
    write_json(result_a_path, result_a)
    before_b = digest(core_path)
    if before_b != before_a:
        raise ValueError("Core source changed between Workers")
    entry_b = worker_port.execute
    if entry_b is not entry:
        raise ValueError("Core entry point changed between Workers")
    result_b = entry_b(DeterministicTestWorker(), order_b)
    write_json(result_b_path, result_b)
    after_b = digest(core_path)
    if after_b != before_a:
        raise ValueError("Core source changed during Worker swap")

    inner_path = ROOT / order_a["payload"]["delegate_work_order"]["path"]
    inner = json.loads(inner_path.read_text(encoding="utf-8"))
    report_path = ROOT / inner["execution_report_path"]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if (report["prompt_id"] != result_a["invocation_id"]
            or report["artifact"]["sha256"] != result_a["artifact"]["sha256"]):
        raise ValueError("ComfyUI execution lineage differs")
    evidence = {
        "version": "c5.0", "proof_id": proof_id,
        "core_worker_port": {"path": reference(core_path)["path"],
                             "sha256_before_a": before_a,
                             "sha256_before_b": before_b,
                             "sha256_after_b": after_b},
        "same_core_entry_point": entry_b is entry,
        "core_modified_between_swaps": len({before_a, before_b, after_b}) != 1,
        "adapter_a": {"adapter_id": order_a["adapter_id"], "work_order": reference(order_a_path),
                      "result": reference(result_a_path), "invocation_id": result_a["invocation_id"],
                      "artifact": result_a["artifact"], "inner_work_order": reference(inner_path),
                      "execution_report": reference(report_path), "worker_model": inner["worker_model"]},
        "adapter_b": {"adapter_id": order_b["adapter_id"], "work_order": reference(order_b_path),
                      "result": reference(result_b_path), "invocation_id": result_b["invocation_id"],
                      "artifact": result_b["artifact"]},
        "semantic_reviewer_invocations": 0,
        "conclusion": "WORKER_BOUNDARY_REPLACEABLE",
    }
    usage = {
        "proof_id": proof_id,
        "workers": [
            {"adapter_id": order_a["adapter_id"], "backend": result_a["backend"],
             "model": inner["worker_model"], "invocations": 1,
             "execution_seconds": result_a["execution_seconds"]},
            {"adapter_id": order_b["adapter_id"], "backend": result_b["backend"],
             "model": None, "invocations": 1,
             "execution_seconds": result_b["execution_seconds"]},
        ],
        "frontier_reviewer": {"invocations": 0, "model": None, "tokens": None, "credits": None},
    }
    write_json(evidence_path, evidence)
    write_json(usage_path, usage)
    return evidence_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof-id", required=True)
    args = parser.parse_args()
    print(run(args.proof_id))
