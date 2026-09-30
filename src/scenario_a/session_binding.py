"""Fixed Scenario A Session binding sidecars; no Core schema or transport changes."""
from dataclasses import asdict
import json
from pathlib import Path
import re

from session import session_boundary as session
from scenario_a import l6_pipeline as l6

KINDS = ("l6", "bridge", "correction")
CAPS = {"worker": 6, "reviewer": 4, "renderer": 2, "revision": 1}
CAPABILITY = "fixed_four_view_glb_seed_only"


def prepare(boundary, binding, *, goal, must_haves, stage_criteria, child_ids,
            capability=CAPABILITY, limits=None):
    """Freeze explicit finalized Scenario projection before any child/effect.

    Goal/Must-Have text and authority are caller-selected from frozen bytes.
    This validates references, not natural-language entailment or capability quality.
    """
    boundary._execution_open()
    binding.validate()
    if binding != boundary._checked_binding():
        raise ValueError("Session/logical Loop binding mismatch")
    if capability != CAPABILITY or (limits is not None and limits != CAPS):
        raise ValueError("UNSUPPORTED_SCENARIO_CAPABILITY_OR_BUDGET")
    if set(child_ids) != set(KINDS) or len(set(child_ids.values())) != 3:
        raise ValueError("exactly three distinct fixed child identities required")
    if any(not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", v) for v in child_ids.values()):
        raise ValueError("invalid child run identity")
    if any(v in (boundary.session_id, binding.loop_run_id) for v in child_ids.values()):
        raise ValueError("Session, logical Loop and child identities must differ")
    fields = binding.specification.fields
    authority = {a.reference_id for a in fields.authority_references}
    document = Path(binding.specification.reference.specification_path).read_text(encoding="utf-8")
    if not isinstance(must_haves, tuple) or not must_haves:
        raise ValueError("explicit immutable Must-Haves required")
    for item in (goal,) + must_haves:
        if (set(item) != {"text", "authority_ref"} or not item["text"]
                or item["text"] not in document or item["authority_ref"] not in authority):
            raise ValueError("Goal/Must-Have source or authority mismatch")
    ids = {c.criterion_id for c in fields.acceptance_criteria}
    if set(stage_criteria) != {"multiview", "geometry"}:
        raise ValueError("fixed stage criterion selection required")
    for selection in stage_criteria.values():
        if not isinstance(selection, tuple) or not selection or len(set(selection)) != len(selection) or not set(selection) <= ids:
            raise ValueError("unknown/duplicate stage criterion")
    # Final geometry review covers every declared criterion; no hidden final gate.
    if set(stage_criteria["geometry"]) != ids:
        raise ValueError("final geometry criteria must cover the frozen Specification")
    data = {"version": "s3b-scenario-a.0", "session_directory": str(boundary.directory),
            "session_id": boundary.session_id, "loop_run_id": binding.loop_run_id,
            "binding": l6.reference(boundary.directory / "binding.json"),
            "binding_identity_sha256": binding.identity_sha256,
            "specification_identity_sha256": binding.specification.identity_sha256,
            "specification": asdict(binding.specification.reference), "scenario": "scenario_a",
            "goal": goal, "must_haves": list(must_haves), "stage_criteria": stage_criteria,
            "child_ids": child_ids, "capability": capability, "limits": CAPS, "automatic_retries": 0}
    path = boundary.directory / "scenario_a.json"
    l6.write_once(path, data)
    return l6.reference(path)


def checked_parent(reference, *, execution=False):
    data = l6.read_ref(reference)
    boundary = session.SessionBoundary(data["session_id"], data["session_directory"])
    if execution:
        boundary._execution_open()
    binding = boundary._checked_binding()
    l6.read_ref(data["binding"])
    if (data["binding"] != l6.reference(boundary.directory / "binding.json")
            or data["binding_identity_sha256"] != binding.identity_sha256
            or data["specification_identity_sha256"] != binding.specification.identity_sha256
            or data["specification"] != asdict(binding.specification.reference)
            or data["loop_run_id"] != binding.loop_run_id or data["scenario"] != "scenario_a"
            or data["capability"] != CAPABILITY or data["limits"] != CAPS):
        raise ValueError("Scenario Session/Specification/logical Loop mismatch")
    return data, boundary, binding


def child_binding(parent_ref, kind, run_dir, source=None):
    data, boundary, _ = checked_parent(parent_ref, execution=True)
    run_dir = Path(run_dir)
    if kind not in KINDS or data["child_ids"][kind] != run_dir.name:
        raise ValueError("current child identity mismatch")
    if source is not None:
        checked_child(Path(source), parent_ref=parent_ref)
    record = {"version": "s3b-child.0", "kind": kind, "run_id": run_dir.name,
              "run_directory": str(run_dir.resolve()), "parent": parent_ref,
              "source": l6.reference(Path(source) / "session_binding.json") if source else None}
    path = run_dir / "session_binding.json"
    l6.write_once(path, record)
    boundary.register_child_evidence(kind + ":binding", session.file_identity(path, kind + ":binding"))
    return l6.reference(path)


def checked_child(run_dir, *, parent_ref=None, execution=False):
    run_dir = Path(run_dir)
    initial = l6.read_json(run_dir / "initial.json")
    reference = initial.get("session_binding")
    if reference is None:
        if parent_ref is not None:
            raise ValueError("UNBOUND_CHILD_EVIDENCE")
        return None
    record = l6.read_ref(reference)
    data, boundary, binding = checked_parent(record["parent"], execution=execution)
    if (reference != l6.reference(run_dir / "session_binding.json")
            or record["run_directory"] != str(run_dir.resolve())
            or record["run_id"] != run_dir.name
            or data["child_ids"].get(record["kind"]) != run_dir.name
            or (parent_ref is not None and record["parent"] != parent_ref)):
        raise ValueError("child Specification/identity mismatch")
    if record["source"]:
        source_path = l6.reviewer.checked_ref(record["source"])
        checked_child(source_path.parent, parent_ref=record["parent"])
    return record, data, boundary, binding


def effect_guard(run_dir):
    return checked_child(run_dir, execution=True)


def bind_record(run_dir, path):
    child = checked_child(run_dir)
    if child is None:
        return None
    target = Path(path)
    data = {"session_binding": l6.reference(Path(run_dir) / "session_binding.json"),
            "record": l6.reference(target)}
    sidecar = target.with_name(target.stem + "_session.json")
    if sidecar.exists():
        if l6.read_json(sidecar) != data:
            raise ValueError("bound record changed")
    else:
        l6.write_once(sidecar, data)
    return l6.reference(sidecar)


def check_record(run_dir, path):
    if checked_child(run_dir) is None:
        return
    path = Path(path)
    expected = {"session_binding": l6.reference(Path(run_dir) / "session_binding.json"),
                "record": l6.reference(path)}
    if l6.read_json(path.with_name(path.stem + "_session.json")) != expected:
        raise ValueError("bound record identity mismatch")
