"""Adapt the verified Scenario A executor to the common Worker Result."""

from datetime import datetime

import c1_delegate as delegate


class ComfyWorkerAdapter:
    adapter_id = "scenario_a_comfy"

    def __call__(self, work_order):
        payload = work_order["payload"]
        if set(payload) != {"delegate_work_order"}:
            raise ValueError("ComfyUI adapter payload differs")
        order_path = delegate.checked_file(payload["delegate_work_order"], delegate.ROOT)
        inner, _, _, _, _ = delegate.preflight(order_path)
        if (inner["run_id"] != work_order["run_id"]
                or inner["work_order_id"] != work_order["work_order_id"]
                or inner["requested_task"] != work_order["requested_task"]
                or inner["expected_output_kind"] != work_order["expected_output_kind"]):
            raise ValueError("ComfyUI adapter Work Order lineage differs")
        execution = delegate.run(order_path)
        artifact = execution["artifact"]
        elapsed = (datetime.fromisoformat(execution["completed_at"])
                   - datetime.fromisoformat(execution["started_at"])).total_seconds()
        return {
            "version": "c5.0", "run_id": work_order["run_id"],
            "work_order_id": work_order["work_order_id"], "adapter_id": self.adapter_id,
            "backend": "ComfyUI", "status": execution["status"],
            "invocation_id": execution["prompt_id"],
            "artifact": {key: artifact[key] for key in ("path", "kind", "bytes", "sha256")},
            "execution_seconds": elapsed,
        }
