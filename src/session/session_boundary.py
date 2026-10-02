"""Local Session contracts; no Scenario execution, semantic review or transport.
Finalized fields come from external dialogue. Host context reset is not verified.
Guards apply to one caller-retained, stable Session record directory.
"""
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

REQUEST_TYPES = frozenset({"NEW_WORK", "ARTIFACT_MODIFICATION", "FOLLOW_UP", "RESTART_AFTER_AMBIGUITY"})
STARTUP_CATEGORIES = frozenset({
    "CURRENT_REQUEST", "CURRENT_REFERENCE", "PREVIOUS_SPECIFICATION", "DELIVERED_ARTIFACT",
    "USER_FEEDBACK", "VERIFIED_FACT", "EXECUTION_RESULT", "KNOWN_FAILURE", "FINAL_DECISION",
    "UNRESOLVED_ISSUE", "ENVIRONMENT_STATE", "EVIDENCE_REFERENCE", "ARCHIVE_REFERENCE",
})


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(name + " must be non-empty text")


def _strings(values, name, *, nonempty=False):
    if not isinstance(values, tuple) or (nonempty and not values):
        raise ValueError(name + " must be an immutable tuple")
    for value in values:
        _text(value, name)


def _bytes(value):
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _hash(value):
    return hashlib.sha256(_bytes(value)).hexdigest()


def _write_once(path, value):
    # Existing exclusive-open/flush/fsync pattern, without importing Core/Scenario.
    with Path(path).open("xb") as stream:
        stream.write(_bytes(value) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())


@dataclass(frozen=True)
class AuthorityReference:
    reference_id: str
    source_ref: str


@dataclass(frozen=True)
class AcceptanceCriterion:
    criterion_id: str
    authority_ref: str
    blocking_when_unmet: bool
    description: str


@dataclass(frozen=True)
class SpecificationAmbiguity:
    description: str
    artifact_impact: str
    context_insufficiency: str
    alternatives: tuple[str, ...] = ()

    def validate(self):
        for name in ("description", "artifact_impact", "context_insufficiency"):
            _text(getattr(self, name), name)
        _strings(self.alternatives, "alternatives")
        if self.alternatives and len(set(self.alternatives)) < 2:
            raise ValueError("alternatives must describe at least two choices")


@dataclass(frozen=True)
class FinalizedFields:
    session_id: str
    specification_version: str
    request_type: str
    specification_ready: bool
    unresolved_blocking_ambiguities: tuple[SpecificationAmbiguity, ...]
    acceptance_criteria: tuple[AcceptanceCriterion, ...]
    authority_references: tuple[AuthorityReference, ...]
    interpretation_envelope: tuple[str, ...]

    def validate(self):
        _text(self.session_id, "session_id")
        _text(self.specification_version, "specification_version")
        if self.request_type not in REQUEST_TYPES:
            raise ValueError("unsupported request_type")
        if type(self.specification_ready) is not bool:
            raise ValueError("readiness must be an explicit bool")
        _strings(self.interpretation_envelope, "interpretation_envelope", nonempty=True)
        for name, record_type in (("acceptance_criteria", AcceptanceCriterion),
                                  ("authority_references", AuthorityReference),
                                  ("unresolved_blocking_ambiguities", SpecificationAmbiguity)):
            values = getattr(self, name)
            if not isinstance(values, tuple) or any(type(v) is not record_type for v in values):
                raise ValueError(name + " must contain immutable typed records")
        if not self.acceptance_criteria or not self.authority_references:
            raise ValueError("criteria and authority references are required")
        authority_ids = []
        for reference in self.authority_references:
            _text(reference.reference_id, "authority reference_id")
            _text(reference.source_ref, "authority source_ref")
            authority_ids.append(reference.reference_id)
        if len(set(authority_ids)) != len(authority_ids):
            raise ValueError("duplicate authority reference_id")
        ids = []
        for criterion in self.acceptance_criteria:
            _text(criterion.criterion_id, "criterion_id")
            _text(criterion.authority_ref, "criterion authority_ref")
            _text(criterion.description, "criterion description")
            if type(criterion.blocking_when_unmet) is not bool:
                raise ValueError("blocking_when_unmet must be an explicit bool")
            if criterion.authority_ref not in authority_ids:
                raise ValueError("criterion authority is not declared")
            ids.append(criterion.criterion_id)
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate criterion_id")
        for ambiguity in self.unresolved_blocking_ambiguities:
            ambiguity.validate()


@dataclass(frozen=True)
class SpecificationRef:
    session_id: str
    specification_version: str
    specification_path: str
    specification_sha256: str

    def validate(self):
        _text(self.session_id, "session_id")
        _text(self.specification_version, "specification_version")
        if not re.fullmatch(r"[0-9a-f]{64}", self.specification_sha256):
            raise ValueError("invalid specification_sha256")
        path = Path(self.specification_path)
        if not path.is_absolute() or not path.is_file():
            raise ValueError("Specification must be an absolute regular file")
        if hashlib.sha256(path.read_bytes()).hexdigest() != self.specification_sha256:
            raise ValueError("SPECIFICATION_CONTENT_CHANGED")


@dataclass(frozen=True)
class FrozenSpecification:
    reference: SpecificationRef
    fields: FinalizedFields

    @property
    def identity_sha256(self):
        return _hash(self)

    def validate(self, *, require_ready=False):
        self.reference.validate()
        self.fields.validate()
        if (self.reference.session_id, self.reference.specification_version) != (
                self.fields.session_id, self.fields.specification_version):
            raise ValueError("Specification identity mismatch")
        if require_ready and (not self.fields.specification_ready or
                              self.fields.unresolved_blocking_ambiguities):
            raise ValueError("SPECIFICATION_NOT_EXECUTION_ELIGIBLE")


def freeze_specification(specification_document, finalized_fields):
    """Bind explicit finalized projection to document bytes; never rewrite it."""
    if type(finalized_fields) is not FinalizedFields:
        raise ValueError("explicit FinalizedFields required")
    finalized_fields.validate()
    path = Path(specification_document).resolve()
    if not path.is_file():
        raise ValueError("Specification must be a regular file")
    ref = SpecificationRef(finalized_fields.session_id, finalized_fields.specification_version,
                           str(path), hashlib.sha256(path.read_bytes()).hexdigest())
    frozen = FrozenSpecification(ref, finalized_fields)
    frozen.validate()
    return frozen


@dataclass(frozen=True)
class SessionRunBinding:
    specification: FrozenSpecification
    loop_run_id: str
    scenario: str = "scenario_a"

    def __post_init__(self):
        self.validate()

    @property
    def identity_sha256(self):
        return _hash(self)

    def validate(self):
        self.specification.validate(require_ready=True)
        _text(self.loop_run_id, "loop_run_id")
        if self.loop_run_id == self.specification.reference.session_id:
            raise ValueError("session_id and loop_run_id must differ")
        if self.scenario != "scenario_a":
            raise ValueError("only fixed scenario_a binding is supported")


@dataclass(frozen=True)
class ContextRecord:
    category: str
    reference: str


def build_startup_context(current_request, current_references=(), selected_durable_refs=()):
    """Validate selected inputs only; no host reset or archive content loading."""
    if type(current_request) is not ContextRecord or current_request.category != "CURRENT_REQUEST":
        raise ValueError("current request required")
    if not isinstance(current_references, tuple) or not isinstance(selected_durable_refs, tuple):
        raise ValueError("explicit immutable selections required")
    if any(type(r) is not ContextRecord or r.category != "CURRENT_REFERENCE"
           for r in current_references):
        raise ValueError("current references must be CURRENT_REFERENCE")
    if any(type(r) is not ContextRecord or r.category in ("CURRENT_REQUEST", "CURRENT_REFERENCE")
           for r in selected_durable_refs):
        raise ValueError("durable selection cannot replace current inputs")
    records = (current_request,) + current_references + selected_durable_refs
    for record in records:
        if record.category not in STARTUP_CATEGORIES:
            raise ValueError("startup category not allowed: " + record.category)
        _text(record.reference, "context reference")
    return records  # Caller order retained; reference contents are never read.


@dataclass(frozen=True)
class FileIdentity:
    identity: str
    path: str
    bytes: int
    sha256: str

    def validate(self):
        _text(self.identity, "file identity")
        path = Path(self.path)
        if not path.is_absolute() or not path.is_file():
            raise ValueError("evidence must be an absolute regular file")
        data = path.read_bytes()
        if type(self.bytes) is not int or self.bytes < 0 or len(data) != self.bytes:
            raise ValueError("evidence size mismatch")
        if hashlib.sha256(data).hexdigest() != self.sha256:
            raise ValueError("evidence hash mismatch")


def file_identity(path, identity):
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError("evidence must be a regular file")
    data = path.read_bytes()
    ref = FileIdentity(identity, str(path), len(data), hashlib.sha256(data).hexdigest())
    ref.validate()
    return ref


@dataclass(frozen=True)
class SubmissionEvidence:
    delivery_package_sha256: str
    specification_sha256: str
    artifact_sha256: str
    receipt_id: str
    observed_channel: str
    observed_timestamp: str
    provenance_ref: str

    def validate(self, package):
        for name in ("receipt_id", "observed_channel", "observed_timestamp", "provenance_ref"):
            _text(getattr(self, name), name)
        timestamp = datetime.fromisoformat(self.observed_timestamp)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("observed_timestamp must include timezone")
        if self.delivery_package_sha256 != package.sha256:
            raise ValueError("submission package mismatch")


@dataclass(frozen=True, init=False)
class SessionOutcome:
    status: str
    terminal: bool
    delivered: bool


def _outcome(status, terminal=False, delivered=False):
    result = object.__new__(SessionOutcome)
    for name, value in (("status", status), ("terminal", terminal), ("delivered", delivered)):
        object.__setattr__(result, name, value)
    return result


def _frozen_from_data(data):
    fields = dict(data["fields"])
    fields["acceptance_criteria"] = tuple(AcceptanceCriterion(**v) for v in fields["acceptance_criteria"])
    fields["authority_references"] = tuple(AuthorityReference(**v) for v in fields["authority_references"])
    fields["unresolved_blocking_ambiguities"] = tuple(
        SpecificationAmbiguity(**dict(v, alternatives=tuple(v["alternatives"])))
        for v in fields["unresolved_blocking_ambiguities"])
    fields["interpretation_envelope"] = tuple(fields["interpretation_envelope"])
    return FrozenSpecification(SpecificationRef(**data["reference"]), FinalizedFields(**fields))


class SessionBoundary:
    """One Session, one stable directory, write-once records, no effect dispatch.

    Caller must retain this directory for this Session. This is not a global
    identity registry, concurrency lock, tamper-proof store or recovery service.
    """

    def __init__(self, session_id, record_directory, *, mode="ACTUAL", start_grant=None,
                 start_authority=None, specification=None):
        _text(session_id, "session_id")
        self.session_id = session_id
        self.directory = Path(record_directory).resolve()
        if mode not in ("ACTUAL", "SYNTHETIC"):
            raise ValueError("EXECUTION_MODE_INVALID")
        self.mode = mode
        owner = self.directory / "session.json"
        if owner.exists():
            if self._read("session")["session_id"] != session_id:
                raise ValueError("Session directory identity mismatch")
            # Historical handles are read-only at construction: no grant
            # consumption, new binding, directory mutation or resume protocol.
        else:
            consumption = None
            if mode == "ACTUAL" or start_grant is not None or start_authority is not None:
                from session.session_start_authority import SessionStartAuthority
                if not isinstance(start_authority, SessionStartAuthority) or start_grant is None:
                    raise ValueError("SESSION_START_GRANT_REQUIRED")
                if specification is None:
                    raise ValueError("SESSION_START_FROZEN_SPECIFICATION_REQUIRED")
                if start_authority.ledger_directory.is_relative_to(self.directory):
                    raise ValueError("SESSION_START_LEDGER_MUST_BE_EXTERNAL")
                consumption = start_authority._consume(start_grant, session_id, specification, mode=mode)
            # Missing/invalid ACTUAL grant is rejected before Session mkdir.
            self.directory.mkdir(parents=True, exist_ok=True)
            _write_once(owner, {"session_id": session_id})
            if consumption is not None:
                _write_once(self.directory / "session_start_authority.json", {
                    "event_type": "SESSION_START_GRANT_CONSUMED", "session_id": session_id,
                    "grant_ref": asdict(start_grant), "consumption_ref": asdict(consumption),
                    "specification_identity_sha256": specification.identity_sha256, "mode": mode})

    def _read(self, name):
        return json.loads((self.directory / (name + ".json")).read_text(encoding="utf-8"))

    def _record(self, name, data):
        self.assert_open()
        path = self.directory / (name + ".json")
        _write_once(path, data)
        return file_identity(path, self.session_id + ":" + name)

    def assert_open(self):
        if (self.directory / "terminal.json").exists():
            raise ValueError("ALREADY_TERMINAL")

    def _execution_open(self):
        self.assert_open()
        if (self.directory / "internal_accept.json").exists():
            raise ValueError("ALREADY_INTERNAL_ACCEPTED")

    @property
    def outcome(self):
        if (self.directory / "terminal.json").exists():
            terminal = self._read("terminal")
            return _outcome(terminal["status"], True, terminal["status"] == "CLOSED")
        if (self.directory / "internal_accept.json").exists():
            return _outcome("INTERNAL_ACCEPT")
        if (self.directory / "binding.json").exists():
            return _outcome("LOOP_READY")
        return _outcome("REQUEST_RECEIVED")

    def create_binding(self, specification, loop_run_id):
        self._execution_open()
        binding = SessionRunBinding(specification, loop_run_id)
        binding.validate()
        if specification.reference.session_id != self.session_id:
            raise ValueError("binding Session mismatch")
        authority_path = self.directory / "session_start_authority.json"
        if self.mode == "ACTUAL" and not authority_path.exists():
            raise ValueError("SESSION_START_GRANT_REQUIRED")
        if authority_path.exists():
            authority = self._read("session_start_authority")
            FileIdentity(**authority["grant_ref"]).validate()
            consumed_ref = FileIdentity(**authority["consumption_ref"])
            consumed_ref.validate()
            consumed = json.loads(Path(consumed_ref.path).read_text(encoding="utf-8"))
            if (authority["session_id"] != self.session_id or consumed["session_id"] != self.session_id
                    or authority["mode"] != self.mode or consumed["mode"] != self.mode
                    or authority["grant_ref"] != consumed["grant_ref"]
                    or any(record["specification_identity_sha256"] != specification.identity_sha256
                           for record in (authority, consumed))):
                raise ValueError("SESSION_START_BINDING_MISMATCH")
        self._record("binding", asdict(binding))
        return binding

    def _checked_binding(self):
        data = self._read("binding")
        binding = SessionRunBinding(_frozen_from_data(data["specification"]),
                                    data["loop_run_id"], data["scenario"])
        binding.validate()
        if binding.specification.reference.session_id != self.session_id:
            raise ValueError("binding Session mismatch")
        return binding

    def register_child_evidence(self, child_id, evidence):
        """Record caller evidence only; never invoke a child effect."""
        self._execution_open()
        self._checked_binding()
        _text(child_id, "child_id")
        evidence.validate()
        name = "child-" + hashlib.sha256(child_id.encode("utf-8")).hexdigest()
        return self._record(name, {"child_id": child_id, "evidence": asdict(evidence)})

    def internal_accept(self, binding, artifact, final_review, initial_references=()):
        """Bind a caller's acceptance declaration; no semantic quality judgment."""
        self._execution_open()
        binding.validate()
        if binding != self._checked_binding():
            raise ValueError("accepted binding mismatch")
        if not isinstance(initial_references, tuple):
            raise ValueError("immutable initial references required")
        for ref in (artifact, final_review) + initial_references:
            ref.validate()
        binding_record = file_identity(self.directory / "binding.json", self.session_id + ":binding")
        return self._record("internal_accept", {
            "status": "INTERNAL_ACCEPT", "session_id": self.session_id,
            "specification": asdict(binding.specification.reference), "loop_run_id": binding.loop_run_id,
            "binding": asdict(binding_record), "binding_identity_sha256": binding.identity_sha256,
            "criterion_ids": [c.criterion_id for c in binding.specification.fields.acceptance_criteria],
            "artifact": asdict(artifact), "final_review": asdict(final_review),
            "initial_references": [asdict(r) for r in initial_references],
        })

    def _checked_accept(self):
        binding = self._checked_binding()
        accepted = self._read("internal_accept")
        FileIdentity(**accepted["binding"]).validate()
        if (accepted["status"] != "INTERNAL_ACCEPT" or accepted["session_id"] != self.session_id
                or accepted["loop_run_id"] != binding.loop_run_id
                or accepted["specification"] != asdict(binding.specification.reference)
                or accepted["binding_identity_sha256"] != binding.identity_sha256
                or accepted["criterion_ids"] != [c.criterion_id for c in binding.specification.fields.acceptance_criteria]):
            raise ValueError("INTERNAL_ACCEPT lineage mismatch")
        for item in [accepted["artifact"], accepted["final_review"]] + accepted["initial_references"]:
            FileIdentity(**item).validate()
        return accepted

    def prepare_delivery(self):
        self.assert_open()
        accepted = self._checked_accept()
        ref = file_identity(self.directory / "internal_accept.json", self.session_id + ":internal_accept")
        return self._record("delivery_package", {
            "session_id": self.session_id, "specification": accepted["specification"],
            "loop_run_id": accepted["loop_run_id"], "artifact": accepted["artifact"],
            "initial_references": accepted["initial_references"], "final_review": accepted["final_review"],
            "internal_accept": asdict(ref),
            "presentation": "Show initial input with final output for visual evaluation",
            "external_evaluation_request": "승인 / 자연어 피드백 / 사용하지 않음",
        })

    def record_submission(self, package, submission_evidence):
        """Validate supplied receipt structure; never observe or invoke transport."""
        self.assert_open()
        if type(submission_evidence) is not SubmissionEvidence:
            raise ValueError("structured external submission evidence required")
        package.validate()
        expected = file_identity(self.directory / "delivery_package.json", self.session_id + ":delivery_package")
        if package != expected:
            raise ValueError("delivery package identity mismatch")
        accepted = self._checked_accept()
        data = self._read("delivery_package")
        FileIdentity(**data["internal_accept"]).validate()
        for name in ("session_id", "specification", "loop_run_id", "artifact", "initial_references", "final_review"):
            if data[name] != accepted[name]:
                raise ValueError("delivery package lineage mismatch")
        submission_evidence.validate(package)
        if (submission_evidence.specification_sha256 != data["specification"]["specification_sha256"]
                or submission_evidence.artifact_sha256 != data["artifact"]["sha256"]):
            raise ValueError("submission artifact/Specification mismatch")
        return self._record("terminal", {
            "session_id": self.session_id, "status": "CLOSED", "transitions": ["DELIVERED", "CLOSED"],
            "reason": "EXTERNAL_SUBMISSION_EVIDENCE_ACCEPTED", "delivery_package": asdict(package),
            "submission_evidence": asdict(submission_evidence),
            "verification_scope": "LOCAL_CALLER_SUPPLIED_EVIDENCE_CONTRACT_ONLY",
        })

    def record_local_handoff(self, package, handoff_record):
        """Close on hash-checked local deliverables; no human receipt prerequisite.

        The caller performs the copy/export before supplying this record. This
        method verifies local files only; UI rendering and human receipt remain
        outside the observation scope. Legacy record_submission is unchanged.
        """
        self.assert_open()
        package.validate()
        handoff_record.validate()
        expected = file_identity(self.directory / "delivery_package.json", self.session_id + ":delivery_package")
        if package != expected:
            raise ValueError("HANDOFF_PACKAGE_MISMATCH")
        accepted = self._checked_accept()
        data = self._read("delivery_package")
        for name in ("session_id", "specification", "loop_run_id", "artifact", "initial_references", "final_review"):
            if data[name] != accepted[name]:
                raise ValueError("HANDOFF_PACKAGE_MISMATCH")
        record = json.loads(Path(handoff_record.path).read_text(encoding="utf-8"))
        required = {"session_id", "delivery_package", "boundary", "delivered_artifact", "delivered_references", "observation_scope"}
        if (set(record) != required or record["session_id"] != self.session_id
                or record["delivery_package"] != asdict(package)
                or record["boundary"] != "LOCAL_DELIVERABLE_EXPORT"
                or record["observation_scope"] != "LOCAL_FILES_VERIFIED_HUMAN_RECEIPT_NOT_OBSERVED"):
            raise ValueError("HANDOFF_RECORD_INVALID")
        delivered = FileIdentity(**record["delivered_artifact"])
        delivered.validate()
        if (delivered.sha256, delivered.bytes) != (data["artifact"]["sha256"], data["artifact"]["bytes"]):
            raise ValueError("HANDOFF_PACKAGE_MISMATCH")
        references = record["delivered_references"]
        if len(references) != len(data["initial_references"]):
            raise ValueError("HANDOFF_PACKAGE_MISMATCH")
        for exported, original in zip(references, data["initial_references"]):
            exported = FileIdentity(**exported)
            exported.validate()
            if (exported.sha256, exported.bytes) != (original["sha256"], original["bytes"]):
                raise ValueError("HANDOFF_PACKAGE_MISMATCH")
        return self._record("terminal", {"session_id": self.session_id, "status": "CLOSED",
            "transitions": ["DELIVERED", "CLOSED"], "reason": "LOCAL_HANDOFF_VERIFIED",
            "delivery_package": asdict(package), "handoff_record": asdict(handoff_record),
            "verification_scope": record["observation_scope"]})

    def stop_for_ambiguity(self, specification, ambiguity):
        self.assert_open()
        specification.validate()
        if specification.reference.session_id != self.session_id or type(ambiguity) is not SpecificationAmbiguity:
            raise ValueError("typed Specification ambiguity required")
        ambiguity.validate()
        if (self.directory / "binding.json").exists() and specification != self._checked_binding().specification:
            raise ValueError("ambiguity Specification mismatch")
        return self._record("terminal", {
            "session_id": self.session_id, "status": "BLOCKED_SPECIFICATION_AMBIGUITY",
            "reason": "SPECIFICATION_AMBIGUITY", "specification": asdict(specification.reference),
            "ambiguity": asdict(ambiguity),
        })

    def stop(self, status, reason):
        self.assert_open()
        if status not in ("FAILED", "ABORT"):
            raise ValueError("use guarded delivery or typed ambiguity path")
        _text(reason, "stop reason")
        return self._record("terminal", {"session_id": self.session_id, "status": status, "reason": reason})
