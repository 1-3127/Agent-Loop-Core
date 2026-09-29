"""C5 smoke-only local Worker; not a production backend."""

import hashlib
import time
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class DeterministicTestWorker:
    adapter_id = "deterministic_test_worker"

    def __call__(self, work_order):
        payload = work_order["payload"]
        if set(payload) != {"input", "output_path"}:
            raise ValueError("deterministic Worker payload differs")
        reference = payload["input"]
        if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
            raise ValueError("deterministic Worker input reference differs")
        source = (ROOT / reference["path"]).resolve()
        output = (ROOT / payload["output_path"]).resolve()
        if (source.parent != (ROOT / "tests/fixtures").resolve()
                or output.parent != (ROOT / "runs").resolve()
                or output.suffix != ".txt" or not source.is_file()):
            raise ValueError("deterministic Worker input or output path differs")
        source_bytes = source.read_bytes()
        if hashlib.sha256(source_bytes).hexdigest() != reference["sha256"]:
            raise ValueError("deterministic Worker input hash differs")
        started = time.monotonic()
        invocation_id = str(uuid.uuid4())
        data = b"C5 deterministic worker output\n" + source_bytes
        with output.open("xb") as stream:
            stream.write(data)
        return {
            "version": "c5.0", "run_id": work_order["run_id"],
            "work_order_id": work_order["work_order_id"], "adapter_id": self.adapter_id,
            "backend": "deterministic local worker", "status": "SUCCESS",
            "invocation_id": invocation_id,
            "artifact": {"path": str(output), "kind": "text", "bytes": len(data),
                         "sha256": hashlib.sha256(data).hexdigest()},
            "execution_seconds": time.monotonic() - started,
        }
