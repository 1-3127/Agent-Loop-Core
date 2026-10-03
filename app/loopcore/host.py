"""Host-owned provenance, trusted ingress and verified local delivery.

Grant issuance is deliberately absent from MCP and semantic model ports.
The Host must protect this inbox from subordinate write access.
"""
import json
from pathlib import Path
import shutil

from .core import check_ref, file_ref, identity, require, write_once


class LocalHost:
    def __init__(self, inbox, allowed_reads, allowed_writes):
        self.inbox = Path(inbox).resolve()
        self.reads = [Path(p).resolve() for p in allowed_reads]
        self.writes = [Path(p).resolve() for p in allowed_writes]

    def path(self, path, *, write=False):
        resolved = Path(path).resolve()
        roots = self.writes if write else self.reads + self.writes
        require(any(resolved == root or resolved.is_relative_to(root) for root in roots), "HOST_PATH_NOT_GRANTED")
        return resolved

    def grant(self, grant_id):
        path = self.inbox / "grants" / (identity(grant_id) + ".json")
        grant = json.loads(path.read_text(encoding="utf-8"))
        require(grant["grant_id"] == grant_id and grant["issuer"] == "codex-host" and grant["mode"] == "ACTUAL", "UNTRUSTED_GRANT")
        self.user_evidence(grant["user_evidence"])
        self.path(grant["request"]["path"])
        for ref in grant["references"]:
            self.path(ref["path"])
        return grant

    def user_evidence(self, evidence):
        """Codex-specific decoding stays outside Core; immutable exact user record."""
        check_ref(evidence["file"])
        lines = Path(evidence["file"]["path"]).read_text(encoding="utf-8").splitlines()
        record = json.loads(lines[evidence["line"] - 1])
        payload = record.get("payload", {})
        require(record.get("type") == "response_item" and payload.get("role") == "user", "USER_ORIGIN_REQUIRED")
        content = payload.get("content", [])
        text = "\n".join(c.get("text", "") for c in content if c.get("type") == "input_text")
        require(text.strip() and text == evidence["text"], "USER_EVIDENCE_MISMATCH")
        return text

    def issue_grant(self, grant_id, sid, request_path, reference_paths, evidence, *, start_authorized, bootstrap_calls=8):
        # start_authorized is a decision of the trusted Host, not inferred by Core
        # or accepted from an untrusted model payload. Provenance alone is not consent.
        require(start_authorized is True, "EXPLICIT_HOST_START_DECISION_REQUIRED")
        self.user_evidence(evidence)
        grant = {"grant_id": identity(grant_id), "session_id": identity(sid), "issuer": "codex-host",
            "mode": "ACTUAL", "request": file_ref(self.path(request_path)),
            "references": [file_ref(self.path(p)) for p in reference_paths],
            "user_evidence": evidence, "bootstrap_calls": bootstrap_calls}
        return write_once(self.inbox / "grants" / (grant_id + ".json"), grant)

    def clarification(self, receipt_id, sid):
        item = json.loads((self.inbox / "clarifications" / (identity(receipt_id) + ".json")).read_text(encoding="utf-8"))
        require(item["session_id"] == sid, "CLARIFICATION_SESSION_MISMATCH")
        self.user_evidence(item["user_evidence"])
        check_ref(item["response"])
        self.path(item["response"]["path"])
        return item["response"]

    def assessment(self, receipt_id, sid):
        """Trusted Host presentation facts or verbatim User feedback, scoped exactly."""
        ref = file_ref(self.inbox / "assessments" / (identity(receipt_id) + ".json"))
        item = json.loads(check_ref(ref).read_text(encoding="utf-8"))
        require(item["session_id"] == sid and item["owner"] == "HOST", "ASSESSMENT_HOST_BINDING")
        if item["kind"] == "USER_FEEDBACK":
            require(item["text"] == self.user_evidence(item["user_evidence"]), "VERBATIM_USER_FEEDBACK_REQUIRED")
        elif item["kind"] == "DELIVERY":
            check_ref(item["presentation"])
            self.path(item["presentation"]["path"])
        else:
            require(False, "ASSESSMENT_KIND")
        return item, ref

    def deliver(self, state, target):
        require(state["status"] == "ACCEPTED", "DELIVERY_REQUIRES_ACCEPTANCE")
        directory = self.path(target, write=True)
        require(not directory.exists(), "DELIVERY_NAMESPACE_COLLISION")
        directory.mkdir(parents=True)
        entries = []
        refs = [("original-" + str(i), ref) for i, ref in enumerate(state["grant"]["references"])]
        refs += [("final-" + str(i), state["artifacts"][aid]["file"]) for i, aid in enumerate(state["acceptance"]["artifact_ids"])]
        for label, ref in refs:
            source = check_ref(ref)
            self.path(source)
            destination = directory / (label + source.suffix)
            shutil.copyfile(source, destination)
            exported = file_ref(destination)
            require(exported["sha256"] == ref["sha256"], "DELIVERY_COPY_CHANGED")
            entries.append({"role": label, "source": ref, "export": exported})
        return write_once(directory / "handoff.json", {"session_id": state["id"], "entries": entries,
            "status": "LOCAL_FILES_VERIFIED_HUMAN_RECEIPT_NOT_OBSERVED", "human_quality_verdict": None})
