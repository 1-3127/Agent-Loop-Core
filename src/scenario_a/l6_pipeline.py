"""Fixed Scenario A L6 pipeline; default CLI and callable perform preflight only."""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from core import result_review_adapter as reviewer
from scenario_a import codex_to_comfy as worker

ROOT = Path(__file__).resolve().parents[2]
ASSET_MANIFEST = ROOT / "docs/l6/L6_ASSET_MANIFEST.json"
MANIFEST_SHA256 = "ceff2ea2ed0ac799ca08673c6d4d912c03e23e16770eaac04dfd9c9160f6a716"
VIEWS = ("right", "left", "back")
ROLES = ("front",) + VIEWS
MAPPING = {"front": "1", "right": "4", "left": "2", "back": "3"}
TERMINALS = {"GEOMETRY_READY", "ABORT", "FAILED"}


class StageFailure(ValueError):
    def __init__(self, state, reason):
        super().__init__(reason)
        self.state = state
        self.reason = reason


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reference(path):
    return {"path": str(Path(path).resolve()), "sha256": digest(path)}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_ref(ref):
    return read_json(reviewer.checked_ref(ref))


def write_once(path, data):
    path = Path(path)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def png_identity(path, role):
    path = Path(path).resolve()
    data = path.read_bytes()
    width, height = worker.png_dimensions(data)
    return {"role": role, "path": str(path), "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data), "width": width, "height": height}


def checked_image(artifact):
    identity = png_identity(artifact["path"], artifact["role"])
    if any(artifact.get(key) != value for key, value in identity.items()):
        raise ValueError("image bytes/hash/dimensions differ")
    return identity


def make_plan(run_id, stage, assets, staged=False):
    view = assets["geometry"] if stage == "geometry" else assets["view_generation"][stage]
    if stage == "geometry":
        # Preflight inspects existing template inputs; actual plans consume staged images.
        graph = read_json(view["workflow"])
        patches = {node: {"image": ("hunyuan-official-demo-padded.png" if role == "front"
                                   else f"l6/{run_id}/{role}.png") if staged
                         else graph[node]["inputs"]["image"]}
                   for role, node in MAPPING.items()}
        patches.update({"14": {"seed": view["seed"]},
                        "17": {"filename_prefix": f"mesh/l6/{run_id}/geometry"}})
    else:
        patches = {"1": {"image": "hunyuan-official-demo-padded.png"},
                   "8": {"prompt": view["prompt"]}, "11": {"seed": view["template_seed"]},
                   "13": {"filename_prefix": f"l6/{run_id}/{stage}"}}
    return {"schema_version": "0.1", "task_id": run_id + "-" + stage,
            "workflow": view["workflow_relative"], "patches": patches,
            "output_node": view["output_node"]}


def preflight(comfy_root):
    """Read real assets and validate all four plans without reserving or executing."""
    comfy_root = Path(comfy_root).resolve()
    if digest(ASSET_MANIFEST) != MANIFEST_SHA256:
        raise ValueError("M1 CONTRACT REVISION REQUIRED: asset manifest hash differs")
    assets = read_json(ASSET_MANIFEST)
    source = assets["source"]
    if Path(source["path"]).resolve() != comfy_root / "work/input/hunyuan-official-demo-padded.png":
        raise ValueError("M1 source/root differs")
    checked_image(source)
    if set(assets["view_generation"]) != set(VIEWS) or assets["geometry"]["view_mapping"] != MAPPING:
        raise ValueError("M1 role mapping differs")
    for stage in VIEWS + ("geometry",):
        view = assets["geometry"] if stage == "geometry" else assets["view_generation"][stage]
        path = worker.within(comfy_root, worker.safe_relative(view["workflow_relative"], "workflow"))
        if path != Path(view["workflow"]).resolve() or digest(path) != view["sha256"]:
            raise ValueError("M1 CONTRACT REVISION REQUIRED: workflow hash/path differs")
        graph = read_json(path)
        if {key: node["class_type"] for key, node in graph.items()} != view["node_classes"]:
            raise ValueError("M1 node classes differ")
        if stage == "geometry":
            for role, node in MAPPING.items():
                vision = view["conditioning_mapping"][role]
                if (graph[vision]["inputs"]["image"] != [node, 0]
                        or graph["10"]["inputs"][role] != [vision, 0]
                        or graph[vision]["inputs"]["crop"] != "none"):
                    raise ValueError("M1 geometry wiring differs")
            if (graph["12"]["inputs"]["resolution"] != 1024
                    or graph["15"]["inputs"]["octree_resolution"] != 128
                    or graph["5"]["inputs"]["ckpt_name"] != view["model"]):
                raise ValueError("M1 geometry settings differ")
        elif (graph["8"]["inputs"]["prompt"] != view["prompt"]
              or graph["4"]["inputs"]["unet_name"] != view["model"]):
            raise ValueError("M1 view settings differ")
        worker.validate_plan(make_plan("l6-preflight", stage, assets), comfy_root)
    for model in assets["models"]:
        path = Path(model["path"]).resolve()
        if (not path.is_relative_to(comfy_root / "models") or not path.is_file()
                or path.stat().st_size != model["bytes"]):
            raise ValueError("M1 model missing/size differs")
    return assets


def budgets(run_dir):
    consumed = sum((run_dir / (stage + "_reservation.json")).exists()
                   for stage in VIEWS + ("geometry",))
    reviewed = int((run_dir / "review_reservation.json").exists())
    return {"worker_budget": {"limit": 4, "consumed": consumed, "remaining": 4 - consumed},
            "reviewer_budget": {"limit": 1, "consumed": reviewed, "remaining": 1 - reviewed}}


def guard(run_dir):
    if (run_dir / "terminal.json").exists():
        raise ValueError("ALREADY_TERMINAL")
    state = read_json(run_dir / "state.json")
    if state["terminal"] or state["state"] == "UNRESOLVED":
        raise ValueError("ALREADY_TERMINAL or UNRESOLVED")
    initial = read_ref(state["initial_contract"])
    if (initial["run_id"] != run_dir.name or initial["terminal"] is not False
            or initial["worker_budget"] != {"limit": 4, "consumed": 0, "remaining": 4}
            or initial["reviewer_budget"] != {"limit": 1, "consumed": 0, "remaining": 1}):
        raise ValueError("initial run/budget differs")
    return state


def update_state(run_dir, state_name, **fields):
    guard(run_dir)
    state = read_json(run_dir / "state.json")
    state.update(state=state_name, **budgets(run_dir), **fields)
    worker.write_report(run_dir / "state.json", state)


def reserve_worker(run_dir, stage, order_path):
    guard(run_dir)
    if stage not in VIEWS + ("geometry",):
        raise ValueError("unknown Worker stage")
    if (run_dir / (stage + "_reservation.json")).exists():
        raise ValueError("WORKER_STAGE_ALREADY_RESERVED")
    if budgets(run_dir)["worker_budget"]["remaining"] < 1:
        raise ValueError("Worker budget exhausted")
    write_once(run_dir / (stage + "_reservation.json"),
               {"run_id": run_dir.name, "stage": stage, "work_order": reference(order_path),
                "initial_contract": reference(run_dir / "initial.json"), "created_at": now()})
    update_state(run_dir, read_json(run_dir / "state.json")["state"])


def reserve_review(run_dir, request_path, result_path, report_path):
    guard(run_dir)
    if (run_dir / "review_reservation.json").exists():
        raise ValueError("REVIEW_BUDGET_ALREADY_RESERVED")
    if budgets(run_dir)["reviewer_budget"]["remaining"] < 1:
        raise ValueError("Reviewer budget exhausted")
    write_once(run_dir / "review_reservation.json",
               {"run_id": run_dir.name, "review_request": reference(request_path),
                "review_id": read_json(request_path)["review_id"],
                "result_path": str(Path(result_path).resolve()),
                "invocation_report_path": str(Path(report_path).resolve()),
                "initial_contract": reference(run_dir / "initial.json"), "created_at": now()})
    update_state(run_dir, "MULTIVIEW_REVIEW_READY")


def publish_order(run_dir, stage, assets, inputs):
    guard(run_dir)
    if stage == "geometry":
        if checked_review(run_dir)["verdict"] != "PASS":
            raise ValueError("Geometry requires PASS")
        validate_staging(run_dir)
    view = assets["geometry"] if stage == "geometry" else assets["view_generation"][stage]
    plan_path = run_dir / (stage + "_plan.json")
    write_once(plan_path, make_plan(run_dir.name, stage, assets, staged=stage == "geometry"))
    order = {"version": "l6.0", "run_id": run_dir.name,
             "work_order_id": run_dir.name + "-" + stage, "stage": stage,
             "worker_type": "ComfyUI", "adapter": "src/scenario_a/codex_to_comfy.py",
             "requested_task": ("Generate GLB from the exact reviewed four-view set"
                                if stage == "geometry" else f"Generate one {stage} view from original front"),
             "expected_output_kind": "geometry" if stage == "geometry" else "image",
             "workflow": {"path": view["workflow"], "sha256": view["sha256"]},
             "plan": reference(plan_path), "inputs": inputs,
             "worker_report_path": str(run_dir / (stage + "_worker_report.json")),
             "execution_report_path": str(run_dir / (stage + "_execution.json")),
             "initial_contract": reference(run_dir / "initial.json")}
    path = run_dir / (stage + "_work_order.json")
    write_once(path, order)
    return path


def validate_worker_report(order, report):
    plan = read_ref(order["plan"])
    if any(report.get(key) != plan[key] for key in ("task_id", "workflow", "output_node")):
        raise ValueError("Worker Report/Plan identity differs")
    if report.get("schema_version") != "0.1" or not report.get("client_id"):
        raise ValueError("Worker Report identity missing")
    initial = read_ref(order["initial_contract"])
    if datetime.fromisoformat(report["started_at"]) < datetime.fromisoformat(initial["created_at"]):
        raise ValueError("Worker started before initial contract")
    if report["status"] == "UNRESOLVED":
        raise StageFailure("UNRESOLVED", order["stage"].upper() + "_SUBMISSION_UNCERTAIN")
    if report["status"] == "FAILED":
        raise StageFailure("FAILED", "GEOMETRY_STAGE" if order["stage"] == "geometry" else "VIEW_STAGE")
    if (report["status"] != "SUCCESS" or not report.get("prompt_id") or report.get("errors")
            or not report.get("completed_at") or len(report.get("outputs", [])) != 1
            or datetime.fromisoformat(report["completed_at"]) < datetime.fromisoformat(report["started_at"])):
        raise ValueError("Worker SUCCESS evidence differs")
    return report["outputs"][0]


def run_worker(order_path, comfy_root, timeout):
    order_path = Path(order_path)
    run_dir = order_path.parent
    order = read_json(order_path)
    stage = order["stage"]
    guard(run_dir)
    # Stage reservation cannot be bypassed by a different task/report namespace.
    if (run_dir / (stage + "_reservation.json")).exists():
        raise ValueError("WORKER_STAGE_ALREADY_RESERVED")
    if (order["run_id"] != run_dir.name or order["work_order_id"] != run_dir.name + "-" + stage
            or stage not in VIEWS + ("geometry",)
            or order["initial_contract"] != reference(run_dir / "initial.json")):
        raise ValueError("Worker Work Order identity differs")
    plan_path = reviewer.checked_ref(order["plan"])
    reviewer.checked_ref(order["workflow"])
    assets = preflight(comfy_root)
    expected = make_plan(run_dir.name, stage, assets, staged=stage == "geometry")
    if read_json(plan_path) != expected:
        raise ValueError("Worker Plan differs from frozen L6 mapping")
    if stage == "geometry":
        if checked_review(run_dir)["verdict"] != "PASS":
            raise ValueError("Geometry requires PASS")
        validate_staging(run_dir)
        if order["inputs"] != geometry_inputs(run_dir):
            raise ValueError("Geometry Work Order lineage differs")
    elif order["inputs"] != {"source": read_json(run_dir / "initial.json")["source"]}:
        raise ValueError("view source identity differs")
    worker.validate_plan(expected, Path(comfy_root))
    report_path = run_dir / (stage + "_worker_report.json")
    execution_path = run_dir / (stage + "_execution.json")
    if (order["worker_report_path"] != str(report_path)
            or order["execution_report_path"] != str(execution_path)
            or report_path.exists() or execution_path.exists()):
        raise ValueError("Worker output records differ or already exist")
    prefix = expected["patches"]["17" if stage == "geometry" else "13"]["filename_prefix"]
    output_prefix = worker.within(Path(comfy_root) / "work/output", worker.safe_relative(prefix, "prefix"))
    if any(output_prefix.parent.glob(output_prefix.name + "_*")):
        raise ValueError("Worker artifact namespace already exists")
    reserve_worker(run_dir, stage, order_path)
    worker.run(plan_path, report_path, Path(comfy_root), timeout)
    report = read_json(report_path)
    output = validate_worker_report(order, report)
    artifact_path = Path(output["path"]).resolve()
    if (not Path(output["path"]).is_absolute() or artifact_path.parent != output_prefix.parent
            or not artifact_path.name.startswith(output_prefix.name + "_")):
        raise ValueError("Worker artifact namespace differs")
    if stage == "geometry":
        history = {"outputs": {"17": {"3d": [{"filename": artifact_path.name,
                    "subfolder": str(artifact_path.parent.relative_to(Path(comfy_root) / "work/output")).replace("\\", "/"),
                    "type": "output"}]}}}
        artifact = worker.verify_glb(history, "17", Path(comfy_root), prefix)[0]
        if output != artifact:
            raise ValueError("GLB Worker Report artifact identity differs")
    else:
        if output.get("type") != "image" or artifact_path.suffix.lower() != ".png":
            raise ValueError("Worker output is not PNG")
        artifact = png_identity(artifact_path, stage)
        if ((artifact["width"], artifact["height"]) != (768, 768)
                or (output.get("width"), output.get("height")) != (768, 768)):
            raise ValueError("Worker PNG dimensions differ")
    record_execution(order_path, report, artifact, "SUCCESS", [])
    return artifact | {"execution_report": reference(execution_path)}


def record_execution(order_path, report, artifact, status, errors):
    order = read_json(order_path)
    run_dir = order_path.parent
    assets = read_ref(read_json(run_dir / "initial.json")["asset_manifest"])
    stage = order["stage"]
    report_path = Path(order["worker_report_path"])
    execution = {
        "version": "l6.0", "run_id": run_dir.name, "work_order_id": order["work_order_id"],
        "stage": stage, "status": status, "work_order": reference(order_path),
        "plan": order["plan"], "workflow": order["workflow"],
        "worker_report": reference(report_path) if report_path.exists() else None,
        "initial_contract": order["initial_contract"], "backend": "ComfyUI",
        "model": assets["geometry"]["model"] if stage == "geometry" else assets["view_generation"][stage]["model"],
        "prompt_id": report.get("prompt_id"), "client_id": report.get("client_id"),
        "started_at": report.get("started_at"), "completed_at": report.get("completed_at"),
        "artifact": artifact, "errors": errors}
    write_once(run_dir / (stage + "_execution.json"), execution)


def available_report(path):
    # A malformed report is retained as raw evidence; telemetry must not invent values.
    if not path.exists():
        return {}
    try:
        report = read_json(path)
        return report if isinstance(report, dict) else {}
    except (ValueError, OSError):
        return {}


def validate_manifest(manifest, run_dir):
    if manifest.get("version") != "l6.0" or manifest.get("run_id") != run_dir.name:
        raise ValueError("manifest run identity differs")
    images = [manifest["source"]] + manifest["views"]
    if len(images) != 4 or [item["role"] for item in images] != list(ROLES):
        raise ValueError("fixed roles must be front/right/left/back exactly once")
    source = read_json(run_dir / "initial.json")["source"]
    if manifest["source"] != source or source["execution_report"] is not None:
        raise ValueError("original source identity differs")
    for item in images:
        checked_image(item)
        if item["role"] == "front":
            continue
        role = item["role"]
        execution_path = run_dir / (role + "_execution.json")
        if item["execution_report"] != reference(execution_path):
            raise ValueError("view execution reference differs")
        execution = read_ref(item["execution_report"])
        order_path = run_dir / (role + "_work_order.json")
        order = read_ref(execution["work_order"])
        if (execution["run_id"] != run_dir.name or execution["stage"] != role
                or execution["work_order_id"] != run_dir.name + "-" + role
                or execution["status"] != "SUCCESS"
                or execution["work_order"] != reference(order_path)
                or execution["artifact"] != {key: value for key, value in item.items() if key != "execution_report"}
                or execution["plan"] != order["plan"] or execution["workflow"] != order["workflow"]
                or execution["initial_contract"] != reference(run_dir / "initial.json")):
            raise ValueError("view execution/run lineage differs")
        report = read_ref(execution["worker_report"])
        validate_worker_report(order, report)
        if execution["prompt_id"] != report["prompt_id"] or report["outputs"][0]["path"] != item["path"]:
            raise ValueError("view invocation lineage differs")
    return images


def prepare_review(run_dir, manifest):
    images = validate_manifest(manifest, run_dir)
    write_once(run_dir / "multiview_manifest.json", manifest)
    initial = read_json(run_dir / "initial.json")
    orders = [reference(run_dir / (role + "_work_order.json")) for role in VIEWS]
    executions = [reference(run_dir / (role + "_execution.json")) for role in VIEWS]
    write_once(run_dir / "multiview_work_order.json",
               {"version": "l6.0", "run_id": run_dir.name, "stage": "MULTIVIEW",
                "requested_task": "Acquire fixed right/left/back from original front",
                "initial_contract": reference(run_dir / "initial.json"),
                "source": manifest["source"], "workflows": [read_ref(ref)["workflow"] for ref in orders],
                "work_orders": orders})
    write_once(run_dir / "multiview_execution.json",
               {"version": "l6.0", "run_id": run_dir.name, "stage": "MULTIVIEW",
                "status": "SUCCESS", "manifest": reference(run_dir / "multiview_manifest.json"),
                "executions": executions})
    instruction = (
        "Review the four attached images in front/right/left/back order once. Are they a coherent "
        "same-subject set usable by the next Geometry Worker? Check identity/major structure, direction "
        "plausibility, severe crop, missing/detached major parts, cross-view contradictions and clear "
        "downstream blockers. Do not judge GLB, topology, UV, texture, PBR or final quality. "
        "Do not favor PASS or REVISE. PASS requires no blockers and NONE/null action. REVISE requires "
        "blockers and diagnostic MULTIVIEW_REVISE with target role or null; no correction will execute. "
        "Uncertain verdict HUMAN_REQUIRED uses HUMAN_REQUIRED/null. Return only the requested Result0.3 JSON.")
    with (run_dir / "review_instructions.md").open("x", encoding="utf-8") as stream:
        stream.write(instruction + "\n")
    request = {"request_version": "0.2", "run_id": run_dir.name,
               "review_id": run_dir.name + "-multiview-review", "stage": "MULTIVIEW_REVIEW",
               "output_kind": "multiview_images",
               "source_result": reference(run_dir / "multiview_manifest.json"),
               "work_order": reference(run_dir / "multiview_work_order.json"),
               "worker_report": reference(run_dir / "multiview_execution.json"),
               "artifacts": [{key: item[key] for key in ("role", "path", "sha256")}
                             | {"media_type": "image/png"} for item in images],
               "instruction_file": reference(run_dir / "review_instructions.md"),
               "context": {"initial_contract": reference(run_dir / "initial.json"),
                           "asset_manifest": initial["asset_manifest"],
                           "fixed_role_order": list(ROLES), "requested_task": "Assess four-view geometry inputs"}}
    reviewer.validate_request(request)
    write_once(run_dir / "review_request.json", request)
    update_state(run_dir, "MULTIVIEW_REVIEW_READY")
    return request


def validate_review_lineage(run_dir):
    request = reviewer.validate_request(read_json(run_dir / "review_request.json"))
    manifest = read_ref(request["source_result"])
    images = validate_manifest(manifest, run_dir)
    expected_artifacts = [{key: image[key] for key in ("role", "path", "sha256")}
                          | {"media_type": "image/png"} for image in images]
    orders = [reference(run_dir / (role + "_work_order.json")) for role in VIEWS]
    executions = [reference(run_dir / (role + "_execution.json")) for role in VIEWS]
    if (request["run_id"] != run_dir.name or request["stage"] != "MULTIVIEW_REVIEW"
            or request["review_id"] != run_dir.name + "-multiview-review"
            or request["source_result"] != reference(run_dir / "multiview_manifest.json")
            or request["work_order"] != reference(run_dir / "multiview_work_order.json")
            or request["worker_report"] != reference(run_dir / "multiview_execution.json")
            or request["artifacts"] != expected_artifacts
            or request["context"]["initial_contract"] != reference(run_dir / "initial.json")
            or read_ref(request["work_order"])["work_orders"] != orders
            or read_ref(request["worker_report"])["executions"] != executions
            or read_ref(request["worker_report"])["manifest"] != request["source_result"]):
        raise ValueError("multiview Review lineage differs")
    return request


def run_review(run_dir, timeout):
    guard(run_dir)
    if (run_dir / "review_reservation.json").exists():
        raise ValueError("REVIEW_BUDGET_ALREADY_RESERVED")
    validate_review_lineage(run_dir)
    paths = [run_dir / name for name in ("review_request.json", "review_result.json", "review_invocation.json")]
    reserve_review(run_dir, *paths)
    return reviewer.review_once(*paths, timeout=timeout, workspace=run_dir)


def checked_review(run_dir):
    request = validate_review_lineage(run_dir)
    paths = [run_dir / name for name in ("review_request.json", "review_result.json", "review_invocation.json")]
    request_path, result_path, report_path = paths
    reservation = read_json(run_dir / "review_reservation.json")
    if (reservation["run_id"] != run_dir.name or reservation["review_request"] != reference(request_path)
            or reservation["result_path"] != str(result_path)
            or reservation["invocation_report_path"] != str(report_path)
            or reservation["initial_contract"] != reference(run_dir / "initial.json")):
        raise StageFailure("UNRESOLVED", "REVIEW_IDENTITY_UNCERTAIN")
    report = read_json(report_path)
    if report["invocation_status"] == "UNRESOLVED":
        raise StageFailure("UNRESOLVED", "REVIEW_UNCERTAIN")
    if report["invocation_status"] == "FAILED":
        raise StageFailure("FAILED", "REVIEW_STAGE")
    source = {"kind": "RESULT_REVIEW", "path": str(result_path), "sha256": digest(result_path),
              "request_path": str(request_path), "request_sha256": digest(request_path),
              "invocation_report_path": str(report_path), "invocation_report_sha256": digest(report_path)}
    try:
        _, result = reviewer.checked_invocation(source)
        expected = [{key: item[key] for key in ("role", "path", "sha256")} for item in request["artifacts"]]
        if (report["reviewer_mode"] != "CODEX_CLI" or report["reviewer_process_started"] is not True
                or report["attached_images"] != expected
                or datetime.fromisoformat(report["started_at"]) < datetime.fromisoformat(reservation["created_at"])):
            raise ValueError("Reviewer attachments/process lineage differs")
    except (ValueError, KeyError, TypeError) as exc:
        raise StageFailure("UNRESOLVED", "REVIEW_IDENTITY_UNCERTAIN") from exc
    return result


def stage_reviewed_bytes(run_dir, comfy_root):
    guard(run_dir)
    if checked_review(run_dir)["verdict"] != "PASS":
        raise ValueError("Geometry requires PASS")
    images = validate_manifest(read_json(run_dir / "multiview_manifest.json"), run_dir)
    destination = worker.within(Path(comfy_root) / "work/input", Path("l6") / run_dir.name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()  # Exclusive, including collision with identical historical bytes.
    staged = []
    for image in images[1:]:
        checked_image(image)
        data = Path(image["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != image["sha256"] or len(data) != image["bytes"]:
            raise ValueError("reviewed bytes mutated before staging")
        path = destination / (image["role"] + ".png")
        with path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        staged.append({"role": image["role"], "original": image, "staged": png_identity(path, image["role"])})
    write_once(run_dir / "staging.json", {"version": "l6.0", "run_id": run_dir.name, "views": staged})
    validate_staging(run_dir)


def validate_staging(run_dir):
    manifest = read_json(run_dir / "multiview_manifest.json")
    validate_manifest(manifest, run_dir)
    record = read_json(run_dir / "staging.json")
    if record["run_id"] != run_dir.name or [item["role"] for item in record["views"]] != list(VIEWS):
        raise ValueError("staged roles/run differ")
    root = Path(read_json(run_dir / "initial.json")["comfy_root"])
    for image, item in zip(manifest["views"], record["views"]):
        if (item["original"] != image
                or Path(item["staged"]["path"]) != root / "work/input/l6" / run_dir.name / (image["role"] + ".png")):
            raise ValueError("staged input mapping differs")
        checked_image(item["staged"])
        if any(item["staged"][key] != image[key] for key in ("role", "sha256", "bytes", "width", "height")):
            raise ValueError("staged bytes differ from reviewed bytes")


def geometry_inputs(run_dir):
    return {"multiview": reference(run_dir / "multiview_manifest.json"),
            "artifacts": validate_manifest(read_json(run_dir / "multiview_manifest.json"), run_dir),
            "review_request": reference(run_dir / "review_request.json"),
            "review_result": reference(run_dir / "review_result.json"),
            "review_invocation": reference(run_dir / "review_invocation.json"),
            "staging": reference(run_dir / "staging.json")}


def finish(run_dir, state_name, reason, stage, error=None):
    guard(run_dir)
    state = read_json(run_dir / "state.json")
    state.update(state=state_name, terminal=state_name in TERMINALS, reason=reason,
                 failed_stage=stage if state_name in ("FAILED", "UNRESOLVED") else None,
                 errors=[] if error is None else [str(error)], finished_at=now(), **budgets(run_dir))
    if stage in VIEWS + ("geometry",) and (run_dir / (stage + "_reservation.json")).exists():
        order_path = run_dir / (stage + "_work_order.json")
        execution_path = run_dir / (stage + "_execution.json")
        if not execution_path.exists():
            report = available_report(run_dir / (stage + "_worker_report.json"))
            record_execution(order_path, report, None, state_name, state["errors"])
    usage = {"version": "l6.0", "run_id": run_dir.name, "workers": [], "frontier": {},
             "budgets": budgets(run_dir), "final_state": state_name}
    assets = read_ref(read_json(run_dir / "initial.json")["asset_manifest"])
    for role in VIEWS + ("geometry",):
        path = run_dir / (role + "_worker_report.json")
        report = available_report(path)
        duration = None
        if report and report.get("started_at") and report.get("completed_at"):
            duration = (datetime.fromisoformat(report["completed_at"]) - datetime.fromisoformat(report["started_at"])).total_seconds()
        usage["workers"].append({"stage": role, "backend": "ComfyUI",
                                 "model": assets["geometry"]["model"] if role == "geometry" else assets["view_generation"][role]["model"],
                                 "invocations": (1 if report.get("prompt_id") else None) if report else
                                                (None if (run_dir / (role + "_reservation.json")).exists() else 0),
                                 "execution_seconds": duration})
    path = run_dir / "review_invocation.json"
    report = available_report(path)
    usage["frontier"] = {"provider": "OpenAI", "auth_mode": report.get("auth_mode"),
                         "invocations": int(report["reviewer_process_started"]) if "reviewer_process_started" in report
                                        else (None if (run_dir / "review_reservation.json").exists() else 0),
                         "review_duration_seconds": report.get("duration_seconds"),
                         **{key: None for key in ("requested_model", "requested_reasoning_effort", "actual_model",
                            "actual_reasoning_effort", "input_tokens", "cached_input_tokens",
                            "output_tokens", "reasoning_tokens", "reported_credits")},
                         "unavailable_reason": "Existing direct Reviewer API has no explicit model/effort override; unobserved telemetry is null."}
    worker.write_report(run_dir / "state.json", state)
    write_once(run_dir / "usage.json", usage)
    if state["terminal"]:
        names = ["initial", "multiview_manifest", "multiview_work_order", "multiview_execution",
                 "review_request", "review_result", "review_invocation", "review_reservation", "staging", "usage"]
        names += [stage + suffix for stage in VIEWS + ("geometry",)
                  for suffix in ("_work_order", "_plan", "_worker_report", "_execution", "_reservation")]
        records = {name: reference(run_dir / (name + ".json"))
                   if (run_dir / (name + ".json")).exists() else None for name in names}
        artifact_path = run_dir / "geometry_execution.json"
        artifact = read_json(artifact_path)["artifact"] if state_name == "GEOMETRY_READY" else None
        write_once(run_dir / "terminal.json", state | {"records": records, "artifact": artifact})
    return state


def run_pipeline(run_id, comfy_root=worker.DEFAULT_COMFY_ROOT, worker_timeout=600,
                 review_timeout=600, *, execute=False):
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", run_id):
        raise ValueError("invalid run_id")
    if worker_timeout <= 0 or review_timeout <= 0:
        raise ValueError("timeouts must be positive")
    run_dir = ROOT / "runs/l6" / run_id
    if execute and run_dir.exists():
        if (run_dir / "terminal.json").exists():
            return {"status": "ALREADY_TERMINAL", "terminal": reference(run_dir / "terminal.json")}
        raise ValueError("L6_RUN_ALREADY_EXISTS")
    assets = preflight(comfy_root)
    if not execute:
        return {"status": "PREFLIGHT_PASS", "asset_manifest": reference(ASSET_MANIFEST),
                "worker_limit": 4, "reviewer_limit": 1, "effects": 0}
    run_dir.parent.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir()
    source = png_identity(assets["source"]["path"], "front") | {"execution_report": None}
    initial = {"version": "l6.0", "run_id": run_id, "created_at": now(), "state": "SOURCE_READY",
               "source": source, "comfy_root": str(Path(comfy_root).resolve()),
               "asset_manifest": reference(ASSET_MANIFEST),
               "worker_budget": {"limit": 4, "consumed": 0, "remaining": 4},
               "reviewer_budget": {"limit": 1, "consumed": 0, "remaining": 1}, "terminal": False}
    write_once(run_dir / "initial.json", initial)
    worker.write_report(run_dir / "state.json", initial | {"initial_contract": reference(run_dir / "initial.json")})
    stage = "right"
    try:
        views = []
        for stage in VIEWS:
            order_path = publish_order(run_dir, stage, assets, {"source": source})
            views.append(run_worker(order_path, comfy_root, worker_timeout))
        update_state(run_dir, "VIEWS_READY")
        prepare_review(run_dir, {"version": "l6.0", "run_id": run_id, "source": source, "views": views})
        stage = "review"
        run_review(run_dir, review_timeout)
        result = checked_review(run_dir)
        update_state(run_dir, "MULTIVIEW_REVIEWED", latest_review=reference(run_dir / "review_result.json"))
        if result["verdict"] == "REVISE":
            return finish(run_dir, "ABORT", "MULTIVIEW_REVISE", stage)
        if result["verdict"] == "HUMAN_REQUIRED":
            return finish(run_dir, "ABORT", "HUMAN_REQUIRED", stage)
        stage = "geometry"
        stage_reviewed_bytes(run_dir, comfy_root)
        order_path = publish_order(run_dir, stage, assets, geometry_inputs(run_dir))
        update_state(run_dir, "GEOMETRY_RUNNING")
        run_worker(order_path, comfy_root, worker_timeout)
        return finish(run_dir, "GEOMETRY_READY", "REVIEWED_MULTIVIEW_TO_VALID_GLB", stage)
    except StageFailure as exc:
        return finish(run_dir, exc.state, exc.reason, stage, exc)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        # An exception after a reservation without a resolved report must never retry.
        report = run_dir / ("review_invocation.json" if stage == "review" else stage + "_worker_report.json")
        reserved = run_dir / ("review_reservation.json" if stage == "review" else stage + "_reservation.json")
        unresolved = reserved.exists() and not available_report(report)
        reason = "REVIEW_STAGE" if stage == "review" else "GEOMETRY_STAGE" if stage == "geometry" else "VIEW_STAGE"
        return finish(run_dir, "UNRESOLVED" if unresolved else "FAILED", reason, stage, exc)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight", action="store_true", help="Static validation only (default)")
    mode.add_argument("--execute", action="store_true", help="Explicit opt-in to actual Worker/Reviewer effects")
    parser.add_argument("--run-id", default="l6-preflight")
    parser.add_argument("--comfy-root", type=Path, default=worker.DEFAULT_COMFY_ROOT)
    parser.add_argument("--worker-timeout", type=int, default=600)
    parser.add_argument("--review-timeout", type=int, default=600)
    args = parser.parse_args(argv)
    try:
        result = run_pipeline(args.run_id, args.comfy_root, args.worker_timeout,
                              args.review_timeout, execute=args.execute)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("state", result.get("status")) in ("PREFLIGHT_PASS", "GEOMETRY_READY", "ALREADY_TERMINAL", "ABORT") else 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"L6 BLOCKED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
