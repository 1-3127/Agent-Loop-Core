"""Run a validated image or GLB workflow on an already running local ComfyUI server."""

import argparse
import hashlib
import io
import json
import os
import re
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path


BASE_URL = "http://127.0.0.1:8188"
DEFAULT_COMFY_ROOT = Path(__file__).resolve().parents[4] / "Comfy-UI"
ALLOWED_PATCHES = {
    "LoadImage": {"image"},
    "TextEncodeQwenImageEditPlus": {"prompt"},
    "KSampler": {"seed"},
    "SaveImage": {"filename_prefix"},
    "SaveGLB": {"filename_prefix"},
    "ImageScale": {"width", "height"},
    "VAEDecodeHunyuan3D": {"octree_resolution"},
}


def now():
    return datetime.now(timezone.utc).isoformat()


def write_report(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def reserve_report(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise ValueError(f"report already exists; refusing duplicate submission: {path}") from exc


def request_json(path, body=None):
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + path,
        data=payload,
        headers={"Content-Type": "application/json"} if payload is not None else {},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def safe_relative(value, label):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError(f"{label} must be a nonempty relative slash path")
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts) or value.startswith("/"):
        raise ValueError(f"{label} contains an unsafe path component")
    return Path(*parts)


def within(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"path escapes {root}")
    return path


def validate_plan(plan, comfy_root, *, planned_inputs=None):
    if not isinstance(plan, dict) or set(plan) != {"schema_version", "task_id", "workflow", "patches", "output_node"}:
        raise ValueError("plan must contain exactly schema_version, task_id, workflow, patches, output_node")
    if plan["schema_version"] != "0.1" or not isinstance(plan["task_id"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", plan["task_id"]):
        raise ValueError("invalid schema_version or task_id")
    workflow_rel = safe_relative(plan["workflow"], "workflow")
    if len(workflow_rel.parts) < 3 or workflow_rel.parts[0] != "workflows" or not workflow_rel.name.endswith("_api.json"):
        raise ValueError("workflow must identify an existing workflows/*/*_api.json")
    workflow_path = within(comfy_root, workflow_rel)
    if not workflow_path.is_file():
        raise ValueError(f"workflow does not exist: {workflow_path}")
    graph = json.loads(workflow_path.read_text(encoding="utf-8"))
    if not isinstance(graph, dict):
        raise ValueError("workflow must be a node graph")
    if not isinstance(plan["patches"], dict):
        raise ValueError("patches must be an object")
    for node_id, fields in plan["patches"].items():
        if node_id not in graph or not isinstance(fields, dict) or not fields:
            raise ValueError(f"invalid patch node {node_id}")
        node = graph[node_id]
        allowed = ALLOWED_PATCHES.get(node.get("class_type"), set())
        for name, value in fields.items():
            if name not in allowed or name not in node.get("inputs", {}):
                raise ValueError(f"patch is not allowed: {node_id}.{name}")
            original = node["inputs"][name]
            if isinstance(original, bool) or type(value) is not type(original) or isinstance(value, (list, dict)):
                raise ValueError(f"patch type mismatch: {node_id}.{name}")
            if isinstance(value, str) and (not value or len(value) > 4096):
                raise ValueError(f"invalid patch text: {node_id}.{name}")
            if name == "seed" and not 0 <= value < 2**64:
                raise ValueError("seed out of range")
            if name in ("width", "height") and not 1 <= value <= 8192:
                raise ValueError(f"{name} out of range")
            if name == "octree_resolution" and not 16 <= value <= 512:
                raise ValueError("octree_resolution out of range")
            if name in ("image", "filename_prefix"):
                safe_relative(value, name)
            node["inputs"][name] = value
    output_node = plan["output_node"]
    if not isinstance(output_node, str) or graph.get(output_node, {}).get("class_type") not in ("SaveImage", "SaveGLB"):
        raise ValueError("output_node must be a SaveImage or SaveGLB node")
    for node in graph.values():
        if node.get("class_type") == "LoadImage":
            image = safe_relative(node["inputs"]["image"], "image")
            actual_path = within(comfy_root / "work" / "input", image)
            # Explicit dry preflight only; run() always validates actual staged files.
            if planned_inputs is not None and str(image).replace("\\", "/") in planned_inputs:
                actual_path = Path(planned_inputs[str(image).replace("\\", "/")])
            if not actual_path.is_file():
                raise ValueError(f"input image does not exist: {image}")
        if node.get("class_type") in ("SaveImage", "SaveGLB"):
            safe_relative(node["inputs"]["filename_prefix"], "filename_prefix")
    return graph


def png_dimensions(data):
    from PIL import Image

    # Pillow verifies chunk CRCs up to IEND; check the complete IEND too.
    iend = b"\x00\x00\x00\x00IEND\xaeB\x60\x82"
    if len(data) < 24 or not data.endswith(iend):
        raise ValueError("PNG missing or corrupt IEND")
    try:
        expected = struct.unpack(">II", data[16:24])
        with io.BytesIO(data) as stream:
            with Image.open(stream, formats=["PNG"]) as image:
                if image.size != expected:
                    raise ValueError("PNG dimensions differ")
                image.verify()
            if stream.tell() != len(data) - 4:
                raise ValueError("PNG has a premature IEND or trailing data")
        # verify() checks the container; reopening and load() decode IDAT.
        with Image.open(io.BytesIO(data), formats=["PNG"]) as image:
            image.load()
            if image.size != expected or min(image.size) < 1:
                raise ValueError("PNG decoded dimensions differ")
            return image.size
    except (OSError, SyntaxError, ValueError, struct.error, Image.DecompressionBombError) as exc:
        raise ValueError("PNG integrity or decode failed") from exc


def verify_images(record, node_id, comfy_root):
    images = record.get("outputs", {}).get(node_id, {}).get("images", [])
    if not images:
        raise ValueError(f"no images for output node {node_id}")
    result = []
    output_root = comfy_root / "work" / "output"
    for item in images:
        if item.get("type") != "output":
            raise ValueError("unexpected ComfyUI output type")
        filename = safe_relative(item.get("filename"), "filename")
        if len(filename.parts) != 1:
            raise ValueError("output filename must be a basename")
        subfolder = item.get("subfolder") or ""
        subpath = Path() if subfolder == "" else safe_relative(subfolder.replace("\\", "/"), "subfolder")
        path = within(output_root, subpath / filename)
        query = urllib.parse.urlencode({key: item[key] for key in ("filename", "subfolder", "type")})
        with urllib.request.urlopen(BASE_URL + "/view?" + query, timeout=20) as response:
            remote_data = response.read()
        local_data = path.read_bytes()
        if remote_data != local_data:
            raise ValueError(f"PNG remote/local payload differs: {path}")
        width, height = png_dimensions(local_data)
        result.append({"type": "image", "path": str(path), "width": width, "height": height})
    return result


def verify_glb(record, node_id, comfy_root, filename_prefix):
    items = record.get("outputs", {}).get(node_id, {}).get("3d", [])
    if not items:
        raise ValueError(f"no 3d output for node {node_id}")
    output_root = comfy_root / "work" / "output"
    prefix = safe_relative(filename_prefix, "filename_prefix")
    result = []
    for item in items:
        if item.get("type") != "output":
            raise ValueError("unexpected ComfyUI output type")
        filename = safe_relative(item.get("filename"), "filename")
        if len(filename.parts) != 1 or filename.suffix.lower() != ".glb":
            raise ValueError("3d output must be a GLB basename")
        subfolder = item.get("subfolder") or ""
        subpath = Path() if subfolder == "" else safe_relative(subfolder.replace("\\", "/"), "subfolder")
        if subpath != prefix.parent or not filename.name.startswith(prefix.name + "_"):
            raise ValueError("GLB output does not match planned prefix")
        path = within(output_root, subpath / filename)
        data = path.read_bytes()
        if len(data) < 20:
            raise ValueError("GLB is too small")
        magic, version, declared_length = struct.unpack_from("<4sII", data)
        if magic != b"glTF" or version != 2 or declared_length != len(data):
            raise ValueError("invalid GLB header or declared length")
        result.append({"type": "geometry", "path": str(path), "bytes": len(data),
                       "sha256": hashlib.sha256(data).hexdigest(), "glb_version": version,
                       "declared_length": declared_length})
    return result


def track(report_path, report, comfy_root, deadline, graph):
    prompt_id = report["prompt_id"]
    while time.monotonic() < deadline:
        try:
            record = request_json("/history/" + urllib.parse.quote(prompt_id)).get(prompt_id)
        except (OSError, ValueError, urllib.error.URLError) as exc:
            report["errors"] = [f"history unavailable: {exc}"]
            write_report(report_path, report)
            return 2
        if record:
            status = record.get("status", {}).get("status_str")
            if status != "success":
                report.update(status="FAILED", completed_at=now(), errors=[f"ComfyUI status: {status}"])
                write_report(report_path, report)
                return 1
            try:
                node = graph[report["output_node"]]
                if node["class_type"] == "SaveGLB":
                    report["outputs"] = verify_glb(record, report["output_node"], comfy_root,
                                                   node["inputs"]["filename_prefix"])
                else:
                    report["outputs"] = verify_images(record, report["output_node"], comfy_root)
            except (OSError, ValueError, KeyError, urllib.error.URLError) as exc:
                report.update(status="FAILED", completed_at=now(), errors=[f"artifact verification: {exc}"])
                write_report(report_path, report)
                return 1
            report.update(status="SUCCESS", completed_at=now(), errors=[])
            write_report(report_path, report)
            return 0
        time.sleep(2)
    report["errors"] = ["history deadline reached; inspect existing run before any retry"]
    write_report(report_path, report)
    return 2


def run(plan_path, report_path, comfy_root, timeout):
    if report_path.exists():
        raise ValueError(f"report already exists; refusing duplicate submission: {report_path}")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    graph = validate_plan(plan, comfy_root)
    stats = request_json("/system_stats")
    if "devices" not in stats:
        raise ValueError("expected a local ComfyUI server")
    report = {
        "schema_version": "0.1", "task_id": plan["task_id"], "workflow": plan["workflow"],
        "output_node": plan["output_node"], "status": "UNRESOLVED", "client_id": str(uuid.uuid4()),
        "prompt_id": None, "started_at": now(), "completed_at": None, "outputs": [], "errors": [],
    }
    reserve_report(report_path, report)
    try:
        queued = request_json("/prompt", {"prompt": graph, "client_id": report["client_id"]})
        prompt_id = queued["prompt_id"]
        if not isinstance(prompt_id, str) or not prompt_id:
            raise ValueError("missing prompt_id in submission response")
        report["prompt_id"] = prompt_id
        write_report(report_path, report)
    except (OSError, ValueError, KeyError, urllib.error.URLError) as exc:
        report["errors"] = [f"submission uncertain: {exc}; inspect queue/history before any retry"]
        write_report(report_path, report)
        return 2
    return track(report_path, report, comfy_root, time.monotonic() + timeout, graph)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--comfy-root", type=Path, default=DEFAULT_COMFY_ROOT)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    try:
        if args.timeout < 1:
            raise ValueError("timeout must be positive")
        result = run(args.plan, args.report, args.comfy_root, args.timeout)
        print(f"{json.loads(args.report.read_text(encoding='utf-8'))['status']} report={args.report}") if args.report.exists() else None
        return result
    except (OSError, ValueError, KeyError, json.JSONDecodeError, urllib.error.URLError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
