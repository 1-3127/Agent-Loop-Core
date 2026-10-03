"""Host-bound Tool ports; native paths and output ownership stay here."""
from copy import deepcopy
import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import time
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from .core import canonical, check_ref, file_ref, require, write_once
from .models import safe_text


class Tools:
    def __init__(self, host, config):
        self.host, self.config = host, config
        self.runners = {"image-normalize": self.normalize, "comfy": self.comfy,
                        "blender-diagnose": self.blender, "read-source": self.read_source}

    def capabilities(self):
        return {"image-normalize": "Contain-pad current image; size is stage policy.",
            "comfy": "Run a bound native API graph. Parameters: template_ref, loaders {node: input_slot}, patches {node: inputs}, selectors {output_slot: {node, collection, index}}. Local tuning uses /patches/<KSampler node>/<sampler input> JSON-pointer names; model/graph/loaders are strategy.",
            "blender-diagnose": "Fresh import of current GLB, neutral multi-angle views and metrics. Parameters: source_slot, size, azimuths. Outputs slots: configured view names + metrics.",
            "read-source": "Read a Host-allowed public primary source into sandbox. Parameters: url. No execute/install."}

    def local_tuning(self, tool, parameters):
        if tool != "comfy":
            return []
        graph = json.loads(check_ref(parameters["template_ref"]).read_text(encoding="utf-8"))
        return ["/patches/" + node_id + "/" + key for node_id, node in graph.items() if node["class_type"] == "KSampler"
                for key in ("seed", "steps", "cfg", "sampler_name", "scheduler", "denoise") if key in node["inputs"]]

    def execute(self, ticket, artifacts):
        request = ticket["request"]
        directory = Path(ticket["directory"])
        report = {"ticket_id": ticket["id"], "status": "UNRESOLVED", "outputs": {}, "observations": {}, "mode": "ACTUAL"}
        try:
            for artifact in artifacts.values():
                check_ref(artifact["file"])
                self.host.path(artifact["file"]["path"])
            require(request["tool"] in self.runners, "CAPABILITY_UNAVAILABLE")
            # One permanent claim before effects, including process creation / POST.
            write_once(directory / "dispatch.json", {"ticket_id": ticket["id"], "tool": request["tool"]})
            outputs, observations = self.runners[request["tool"]](ticket, artifacts)
            require(set(outputs) == set(request["outputs"]), "TOOL_OUTPUT_CONTRACT")
            for ref in outputs.values():
                check_ref(ref)
                self.host.path(ref["path"])
            for artifact in artifacts.values():
                check_ref(artifact["file"])
            report.update(status="SUCCESS", outputs=outputs, observations=observations)
        except Exception as exc:
            # Never turn an uncertain submission / process / output into no effect.
            report["error"] = safe_text(str(exc))
        ref = write_once(directory / "execution.json", report)
        return {"status": report["status"], "outputs": report["outputs"], "report": ref}

    def normalize(self, ticket, artifacts):
        from PIL import Image, ImageOps, __version__
        parameters = ticket["request"]["parameters"]
        require(set(parameters) <= {"source_slot", "size"}, "NORMALIZE_PARAMETERS")
        source = check_ref(artifacts[parameters["source_slot"]]["file"])
        size = parameters["size"]
        require(len(size) == 2 and all(type(n) is int and n > 0 for n in size), "IMAGE_SIZE")
        with Image.open(source) as image:
            image.load()
            original_size = list(image.size)
            image = ImageOps.exif_transpose(image)
            mode = "RGBA" if "A" in image.getbands() or "transparency" in image.info else "RGB"
            image = image.convert(mode)
            image.thumbnail(tuple(size), Image.Resampling.LANCZOS)
            canvas = Image.new(mode, tuple(size), (255, 255, 255, 0) if mode == "RGBA" else (255, 255, 255))
            canvas.paste(image, ((size[0] - image.width)//2, (size[1] - image.height)//2))
            path = Path(ticket["directory"]) / "normalized.png"
            canvas.save(path, format="PNG")
        slot, = ticket["request"]["outputs"]
        return {slot: file_ref(path)}, {"original_size": original_size, "normalized_size": size,
            "policy": "contain_pad_no_upscale_no_crop", "pillow": __version__}

    def http(self, route, payload=None):
        base = self.config["comfy"]["url"]
        parsed = urlparse(base)
        require(parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}, "COMFY_LOOPBACK_ONLY")
        request = Request(base.rstrip("/") + route, data=None if payload is None else canonical(payload).encode(),
                          headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=30) as response:
            return json.load(response)

    def comfy(self, ticket, artifacts):
        directory = Path(ticket["directory"])
        parameters = deepcopy(ticket["request"]["parameters"])
        graph_ref = parameters["template_ref"]
        graph = json.loads(check_ref(graph_ref).read_text(encoding="utf-8"))
        self.host.path(graph_ref["path"])
        require(graph and all(isinstance(node, dict) and "class_type" in node and "inputs" in node for node in graph.values()), "API_GRAPH_REQUIRED")
        require(set(parameters.get("loaders", {})) == {node_id for node_id, node in graph.items() if node["class_type"] == "LoadImage"}, "ALL_CURRENT_IMAGE_INPUTS_REQUIRED")
        # Namespace is tied to reservation, independent of historical demo files.
        namespace = "loopcore/" + ticket["id"]
        input_root = self.host.path(self.config["comfy"]["input"], write=True)
        output_root = self.host.path(self.config["comfy"]["output"], write=True)
        staged = input_root / namespace
        require(not staged.exists() and not (output_root / namespace).exists(), "COMFY_NAMESPACE_COLLISION")
        staged.mkdir(parents=True)
        for node_id, slot in parameters.get("loaders", {}).items():
            require(graph[node_id]["class_type"] == "LoadImage", "LOAD_IMAGE_BINDING")
            ref = artifacts[slot]["file"]
            source = check_ref(ref)
            destination = staged / (slot + source.suffix)
            shutil.copyfile(source, destination)
            require(file_ref(destination)["sha256"] == ref["sha256"], "STAGED_INPUT_CHANGED")
            graph[node_id]["inputs"]["image"] = destination.relative_to(input_root).as_posix()
        for node_id, patch in parameters.get("patches", {}).items():
            require(node_id in graph and set(patch) <= set(graph[node_id]["inputs"]), "COMFY_PATCH_CONTRACT")
            require(not set(patch) & {"image", "filename_prefix"}, "PATH_PATCH_FORBIDDEN")
            graph[node_id]["inputs"].update(patch)
        for node_id, node in graph.items():
            if "filename_prefix" in node["inputs"]:
                node["inputs"]["filename_prefix"] = namespace + "/" + node_id
        # Server rejects unknown/missing nodes before /prompt effects.
        known = self.http("/object_info")
        require(all(node["class_type"] in known for node in graph.values()), "COMFY_NODE_UNAVAILABLE")
        graph_record = write_once(directory / "graph.json", graph)
        response = self.http("/prompt", {"prompt": graph, "client_id": ticket["id"]})
        require(response.get("prompt_id") and not response.get("node_errors"), "COMFY_SUBMISSION_UNCERTAIN")
        receipt = {"prompt_id": response["prompt_id"], "graph": graph_record, "namespace": namespace,
                   "selectors": parameters["selectors"], "output_root": str(output_root)}
        write_once(directory / "comfy-receipt.json", receipt)
        deadline = time.monotonic() + self.config["comfy"]["timeout"]
        while time.monotonic() < deadline:
            observed = self.observe_comfy(receipt)
            if observed is not None:
                return observed
            time.sleep(1)
        raise ValueError("COMFY_HISTORY_DEADLINE_UNRESOLVED: " + receipt["prompt_id"])

    def observe_comfy(self, receipt):
        pid = receipt["prompt_id"]
        history = self.http("/history/" + quote(pid, safe="")).get(pid)
        if history is None or not history.get("status", {}).get("completed"):
            return None
        require(history["status"].get("status_str") == "success", "COMFY_EXECUTION_FAILED")
        outputs = {}
        for slot, selector in receipt["selectors"].items():
            item = history["outputs"][selector["node"]][selector["collection"]][selector.get("index", 0)]
            require(item.get("type") == "output", "COMFY_OUTPUT_TYPE")
            root = Path(receipt["output_root"]).resolve()
            file = (root / item.get("subfolder", "") / item["filename"]).resolve()
            require(file.is_relative_to(root / receipt["namespace"]) and Path(item["filename"]).name == item["filename"], "COMFY_OUTPUT_ESCAPE")
            outputs[slot] = file_ref(self.host.path(file))
        return outputs, {"prompt_id": pid, "server_status": history["status"], "history_sha256": hashlib.sha256(canonical(history).encode()).hexdigest()}

    def reconcile(self, ticket):
        directory = Path(ticket["directory"])
        if (directory / "execution.json").is_file():
            ref = file_ref(directory / "execution.json")
            report = json.loads(check_ref(ref).read_text(encoding="utf-8"))
            if report["status"] in {"SUCCESS", "FAILED"}:
                return {"status": report["status"], "outputs": report["outputs"], "report": ref}
        receipt_path = directory / "comfy-receipt.json"
        require(receipt_path.is_file(), "NO_OBSERVABLE_TOOL_RECEIPT_HOST_DECISION_REQUIRED")
        observed = self.observe_comfy(json.loads(receipt_path.read_text(encoding="utf-8")))
        require(observed is not None, "EFFECT_STILL_UNRESOLVED")
        outputs, observations = observed
        ref = write_once(directory / "recovery.json", {"ticket_id": ticket["id"], "status": "SUCCESS", "outputs": outputs, "observations": observations})
        return {"status": "SUCCESS", "outputs": outputs, "report": ref}

    def blender(self, ticket, artifacts):
        directory = Path(ticket["directory"])
        parameters = ticket["request"]["parameters"]
        source = artifacts[parameters["source_slot"]]["file"]
        script = Path(__file__).with_name("blender_diagnostic.py")
        request = write_once(directory / "blender-request.json", {"source": source, "directory": str(directory / "diagnostics"),
            "size": parameters["size"], "azimuths": parameters["azimuths"], "slots": list(ticket["request"]["outputs"])})
        executable = self.host.path(self.config["blender"]["executable"])
        process = subprocess.Popen([str(executable), "--background", "--factory-startup", "--python", str(script), "--", request["path"]],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        write_once(directory / "process.json", {"pid": process.pid, "request": request})
        try:
            stdout, stderr = process.communicate(timeout=self.config["blender"]["timeout"])
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise ValueError("BLENDER_TIMEOUT_UNRESOLVED")
        for name, data in (("stdout", stdout), ("stderr", stderr)):
            (directory / (name + ".txt")).write_text(safe_text(data), encoding="utf-8")
        require(process.returncode == 0 and b"Traceback" not in stderr and b"Traceback" not in stdout, "BLENDER_RUNTIME_FAILED")
        result = json.loads((directory / "diagnostics" / "outputs.json").read_text(encoding="utf-8"))
        return {slot: file_ref(path) for slot, path in result.items()}, {"exit_code": process.returncode,
            "stdout": file_ref(directory / "stdout.txt"), "stderr": file_ref(directory / "stderr.txt")}

    def read_source(self, ticket, artifacts):
        url = ticket["request"]["parameters"]["url"]
        require(urlparse(url).scheme == "https" and urlparse(url).hostname in self.config["research_domains"], "RESEARCH_URL_NOT_GRANTED")
        with urlopen(url, timeout=30) as response:
            require(urlparse(response.url).hostname in self.config["research_domains"], "RESEARCH_REDIRECT_NOT_GRANTED")
            content = response.read(1024 * 1024 + 1)
            require(len(content) <= 1024 * 1024, "RESEARCH_SOURCE_TOO_LARGE")
        path = Path(ticket["directory"]) / "source.txt"
        path.write_bytes(content)
        slot, = ticket["request"]["outputs"]
        return {slot: file_ref(path)}, {"url": url, "classification": "UNTRUSTED_PRIMARY_SOURCE_READ_ONLY"}
