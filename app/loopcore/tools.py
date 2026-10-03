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
from urllib.error import HTTPError

from .core import canonical, check_ref, file_ref, identity, require, write_once
from .models import safe_text


class NativeFailure(ValueError):
    """A native rejection or observed terminal failure, possibly with partial effects."""
    def __init__(self, reason, observations, outputs=None, *, executed=True):
        super().__init__(reason)
        self.observations, self.outputs, self.executed = observations, outputs or {}, executed


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
        require(not (directory / "dispatch.json").exists(), "ORIGINAL_DISPATCH_ALREADY_CLAIMED")
        ticket["operation"] = {"phase": "PREPARING", "execution_observed": False}
        report = {"ticket_id": ticket["id"], "status": "UNRESOLVED", "outputs": {}, "observations": {}, "mode": "ACTUAL"}
        try:
            for artifact in artifacts.values():
                check_ref(artifact["file"])
                self.host.path(artifact["file"]["path"])
            require(request["tool"] in self.runners, "CAPABILITY_UNAVAILABLE")
            # One permanent claim before effects, including process creation / POST.
            write_once(directory / "dispatch.json", {"ticket_id": ticket["id"], "tool": request["tool"]})
            outputs, observations = self.runners[request["tool"]](ticket, artifacts)
            if ticket["operation"]["phase"] != "TERMINAL_OBSERVED":
                self.phase(ticket, "TERMINAL_OBSERVED", True)
            report.update(outputs=outputs, observations=observations)
            require(set(outputs) == set(request["outputs"]), "TOOL_OUTPUT_CONTRACT")
            for ref in outputs.values():
                check_ref(ref)
                self.host.path(ref["path"])
            for artifact in artifacts.values():
                check_ref(artifact["file"])
            report.update(status="SUCCESS", outputs=outputs, observations=observations)
        except NativeFailure as exc:
            report.update(status="FAILED", outputs=exc.outputs, observations=exc.observations, error=safe_text(str(exc)))
            ticket["operation"].update(phase="NATIVE_FAILED", execution_observed=exc.executed)
        except Exception as exc:
            report["error"] = safe_text(str(exc))
            # Classification follows a durable dispatch/termination boundary,
            # not HTTP codes, arbitrary exception text or completed=false alone.
            if ticket["operation"]["phase"] in {"PREPARING", "LOCAL_EXECUTION", "TERMINAL_OBSERVED"}:
                report["status"] = "FAILED"
        report.update(ticket["operation"])
        report["partial_effects_possible"] = report["execution_observed"] is not False or request["tool"] == "comfy"
        ref = write_once(directory / "execution.json", report)
        return {"status": report["status"], "outputs": report["outputs"], "report": ref}

    def phase(self, ticket, phase, executed, **facts):
        operation = {"phase": phase, "execution_observed": executed, **facts}
        write_once(Path(ticket["directory"]) / ("native-" + phase.lower() + ".json"), operation)
        ticket["operation"] = operation

    def normalize(self, ticket, artifacts):
        from PIL import Image, ImageOps, __version__
        parameters = ticket["request"]["parameters"]
        require(set(parameters) <= {"source_slot", "size"}, "NORMALIZE_PARAMETERS")
        source = check_ref(artifacts[parameters["source_slot"]]["file"])
        size = parameters["size"]
        require(len(size) == 2 and all(type(n) is int and n > 0 for n in size), "IMAGE_SIZE")
        self.phase(ticket, "LOCAL_EXECUTION", True)
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
        require(set(parameters["selectors"]) == set(ticket["request"]["outputs"]), "COMFY_SELECTOR_COVERAGE")
        for selector in parameters["selectors"].values():
            require(selector["node"] in graph and isinstance(selector["collection"], str) and selector["collection"]
                    and type(selector.get("index", 0)) is int and selector.get("index", 0) >= 0, "COMFY_SELECTOR_CONTRACT")
        # Namespace is tied to reservation, independent of historical demo files.
        namespace = "loopcore/" + ticket["id"]
        input_root = self.host.path(self.config["comfy"]["input"], write=True)
        output_root = self.host.path(self.config["comfy"]["output"], write=True)
        staged = input_root / namespace
        require(not staged.exists() and not (output_root / namespace).exists(), "COMFY_NAMESPACE_COLLISION")
        staged.mkdir(parents=True)
        ticket["operation"].update(staged_input_directory=str(staged), output_namespace=str(output_root / namespace))
        for node_id, slot in parameters.get("loaders", {}).items():
            identity(slot)
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
        self.phase(ticket, "SUBMITTING", None, graph=graph_record, namespace=namespace)
        try:
            response = self.http("/prompt", {"prompt": graph, "client_id": ticket["id"]})
        except HTTPError as exc:
            body = exc.read(65536)
            try:
                response = json.loads(body)
            except (ValueError, UnicodeError):
                raise ValueError("COMFY_SUBMISSION_OUTCOME_UNKNOWN") from exc
            error = response.get("error", {})
            if (not response.get("prompt_id") and isinstance(error, dict) and error.get("type") in
                    {"prompt_outputs_failed_validation", "prompt_no_outputs", "invalid_prompt"}):
                rejected = write_once(directory / "comfy-rejection.json", response)
                raise NativeFailure("COMFY_NATIVE_VALIDATION_REJECTED", {"rejection": rejected}, executed=False) from exc
            raise ValueError("COMFY_SUBMISSION_OUTCOME_UNKNOWN") from exc
        require(response.get("prompt_id"), "COMFY_SUBMISSION_UNCERTAIN")
        receipt = {"prompt_id": response["prompt_id"], "graph": graph_record, "namespace": namespace,
                   "selectors": parameters["selectors"], "output_root": str(output_root), "directory": str(directory),
                   "submission_node_errors": response.get("node_errors", {})}
        write_once(directory / "comfy-receipt.json", receipt)
        self.phase(ticket, "ACCEPTED", None, prompt_id=receipt["prompt_id"], graph=graph_record)
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
        if history is None:
            return None
        status = history.get("status", {})
        messages = status.get("messages", [])
        native_failure = status.get("status_str") == "error" or any(
            isinstance(m, (list, tuple)) and len(m) == 2 and m[0] in {"execution_error", "execution_interrupted"}
            and isinstance(m[1], dict) and m[1].get("prompt_id") == pid for m in messages)
        if not native_failure and not (status.get("completed") is True and status.get("status_str") == "success"):
            return None
        history_path = Path(receipt["directory"]) / "comfy-terminal-history.json"
        if history_path.exists():
            require(json.loads(history_path.read_text(encoding="utf-8")) == history, "NATIVE_TERMINAL_HISTORY_CHANGED")
            history_ref = file_ref(history_path)
        else:
            history_ref = write_once(history_path, history)
        observations = {"prompt_id": pid, "server_status": status, "history": history_ref,
                        "history_sha256": hashlib.sha256(canonical(history).encode()).hexdigest()}
        outputs = {}
        for slot, selector in receipt["selectors"].items():
            try:
                item = history["outputs"][selector["node"]][selector["collection"]][selector.get("index", 0)]
                require(item.get("type") == "output", "COMFY_OUTPUT_TYPE")
                root = Path(receipt["output_root"]).resolve()
                file = (root / item.get("subfolder", "") / item["filename"]).resolve()
                require(file.is_relative_to(root / receipt["namespace"]) and Path(item["filename"]).name == item["filename"], "COMFY_OUTPUT_ESCAPE")
                outputs[slot] = file_ref(self.host.path(file))
            except (KeyError, IndexError, OSError, ValueError) as exc:
                observations.setdefault("output_errors", {})[slot] = safe_text(str(exc))
        if native_failure or observations.get("output_errors"):
            raise NativeFailure("COMFY_EXECUTION_FAILED" if native_failure else "COMFY_TERMINAL_OUTPUT_MISSING", observations, outputs)
        return outputs, observations

    def reconcile(self, ticket):
        directory = Path(ticket["directory"])
        if (directory / "recovery.json").is_file():
            ref = file_ref(directory / "recovery.json")
            report = json.loads(check_ref(ref).read_text(encoding="utf-8"))
            require(report["ticket_id"] == ticket["id"], "RECOVERY_TICKET_MISMATCH")
            return {"status": report["status"], "outputs": report["outputs"], "report": ref}
        if (directory / "execution.json").is_file():
            ref = file_ref(directory / "execution.json")
            report = json.loads(check_ref(ref).read_text(encoding="utf-8"))
            if report["status"] in {"SUCCESS", "FAILED"}:
                return {"status": report["status"], "outputs": report["outputs"], "report": ref}
        receipt_path = directory / "comfy-receipt.json"
        require(receipt_path.is_file(), "NO_OBSERVABLE_TOOL_RECEIPT_HOST_DECISION_REQUIRED")
        status = "SUCCESS"
        try:
            observed = self.observe_comfy(json.loads(receipt_path.read_text(encoding="utf-8")))
            require(observed is not None, "EFFECT_STILL_UNRESOLVED")
            outputs, observations = observed
        except NativeFailure as exc:
            status, outputs, observations = "FAILED", exc.outputs, exc.observations
        ref = write_once(directory / "recovery.json", {"ticket_id": ticket["id"], "status": status, "outputs": outputs,
            "observations": observations, "phase": "TERMINAL_OBSERVED", "execution_observed": True, "partial_effects_possible": True})
        return {"status": status, "outputs": outputs, "report": ref}

    def blender(self, ticket, artifacts):
        directory = Path(ticket["directory"])
        parameters = ticket["request"]["parameters"]
        source = artifacts[parameters["source_slot"]]["file"]
        script = Path(__file__).with_name("blender_diagnostic.py")
        request = write_once(directory / "blender-request.json", {"source": source, "directory": str(directory / "diagnostics"),
            "size": parameters["size"], "azimuths": parameters["azimuths"], "slots": list(ticket["request"]["outputs"]),
            "slot_types": dict(ticket["request"]["outputs"])})
        executable = self.host.path(self.config["blender"]["executable"])
        self.phase(ticket, "SUBMITTING", None, executable=str(executable))
        try:
            process = subprocess.Popen([str(executable), "--background", "--factory-startup", "--python", str(script), "--", request["path"]],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        except OSError as exc:
            raise NativeFailure("BLENDER_PROCESS_NOT_CREATED", {"error": safe_text(str(exc))}, executed=False) from exc
        write_once(directory / "process.json", {"pid": process.pid, "request": request})
        self.phase(ticket, "EXECUTING", True, pid=process.pid)
        try:
            stdout, stderr = process.communicate(timeout=self.config["blender"]["timeout"])
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate(timeout=30)
            for name, data in (("stdout", stdout), ("stderr", stderr)):
                (directory / (name + ".txt")).write_text(safe_text(data), encoding="utf-8")
            raise NativeFailure("BLENDER_TIMEOUT_PROCESS_TERMINATION_OBSERVED", {"pid": process.pid,
                "exit_code": process.returncode, "stdout": file_ref(directory / "stdout.txt"),
                "stderr": file_ref(directory / "stderr.txt"), "partial_outputs_may_remain": True})
        for name, data in (("stdout", stdout), ("stderr", stderr)):
            (directory / (name + ".txt")).write_text(safe_text(data), encoding="utf-8")
        self.phase(ticket, "TERMINAL_OBSERVED", True, exit_code=process.returncode,
            stdout=file_ref(directory / "stdout.txt"), stderr=file_ref(directory / "stderr.txt"))
        require(process.returncode == 0 and b"Traceback" not in stderr and b"Traceback" not in stdout, "BLENDER_RUNTIME_FAILED")
        result = json.loads((directory / "diagnostics" / "outputs.json").read_text(encoding="utf-8"))
        return {slot: file_ref(path) for slot, path in result.items()}, {"exit_code": process.returncode,
            "stdout": file_ref(directory / "stdout.txt"), "stderr": file_ref(directory / "stderr.txt")}

    def read_source(self, ticket, artifacts):
        url = ticket["request"]["parameters"]["url"]
        require(urlparse(url).scheme == "https" and urlparse(url).hostname in self.config["research_domains"], "RESEARCH_URL_NOT_GRANTED")
        self.phase(ticket, "LOCAL_EXECUTION", True, url=url)
        with urlopen(url, timeout=30) as response:
            require(urlparse(response.url).hostname in self.config["research_domains"], "RESEARCH_REDIRECT_NOT_GRANTED")
            content = response.read(1024 * 1024 + 1)
            require(len(content) <= 1024 * 1024, "RESEARCH_SOURCE_TOO_LARGE")
        path = Path(ticket["directory"]) / "source.txt"
        path.write_bytes(content)
        slot, = ticket["request"]["outputs"]
        return {slot: file_ref(path)}, {"url": url, "classification": "UNTRUSTED_PRIMARY_SOURCE_READ_ONLY"}
