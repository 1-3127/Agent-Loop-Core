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
    if any(not re.fullmatch(r'[A-Za-z0-9_-]+', c.criterion_id) or not re.fullmatch(r'[A-Za-z0-9_-]+', c.authority_ref) for c in fields.acceptance_criteria):
        raise ValueError('unsupported bound criterion identifier')
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

def review_contract(run_dir, stage):
    child = checked_child(run_dir)
    if child is None:
        return None
    if stage not in ("multiview", "geometry"):
        raise ValueError("unsupported bound review stage")
    record, data, _, binding = child
    fields = binding.specification.fields
    criteria = {c.criterion_id: asdict(c) for c in fields.acceptance_criteria}
    selected = [criteria[i] for i in data["stage_criteria"][stage]]
    authorities = {a.reference_id: a.source_ref for a in fields.authority_references}
    return {"session_binding": l6.reference(Path(run_dir) / "session_binding.json"),
            "specification_identity_sha256": binding.specification.identity_sha256,
            "stage": stage, "criteria": selected, "authorities": authorities}


def compile_instructions(contract):
    if contract is None:
        raise ValueError("explicit bound Review contract required")
    stage = contract["stage"]
    actions = ("MULTIVIEW_REVISE with right/left/back/null" if stage == "multiview" else
               "REGENERATE_VIEW with right/left/back or REGENERATE_GEOMETRY with geometry")
    return (
        "Bound Scenario A review. The criteria below are the only user quality acceptance authority.\n"
        "Inspect the exact attached evidence. Identity, schema, role order, camera configuration and "
        "invocation hashes are technical contracts, not additional quality criteria.\n"
        "Do not invent goals or quality blockers; do not favor a verdict. Return exact Result0.3 JSON.\n"
        "Every selected criterion needs exactly one observations entry formatted "
        "[criterion_id@authority_ref] SATISFIED: evidence, UNMET: evidence, or UNCERTAIN: evidence.\n"
        "blocking_issues entries use [criterion_id@authority_ref] UNMET: evidence and may only name "
        "selected blocking_when_unmet=true criteria. Nonblocking UNMET stays an observation.\n"
        "PASS requires every blocking criterion SATISFIED, no blocking_issues, NONE/null. "
        "REVISE requires valid blockers and " + actions + ". HUMAN_REQUIRED uses HUMAN_REQUIRED/null; "
        "it is not by itself Specification ambiguity. Correction is bounded seed-only, no quality guarantee.\n"
        "Criteria and declared authority sources:\n" +
        json.dumps({"criteria": contract["criteria"], "authorities": contract["authorities"]},
                   ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def review_instruction(run_dir, stage, legacy):
    contract = review_contract(run_dir, stage)
    if contract is None:
        return legacy
    path = Path(run_dir) / (stage + "_criteria.json")
    l6.write_once(path, contract)
    return compile_instructions(contract).rstrip("\n")


def review_context(run_dir, stage, context):
    if checked_child(run_dir) is None:
        return context
    return context | {"specification_review": l6.reference(Path(run_dir) / (stage + "_criteria.json"))}


def check_request(run_dir, stage, request):
    contract = review_contract(run_dir, stage)
    if contract is None:
        return
    reference = l6.reference(Path(run_dir) / (stage + "_criteria.json"))
    if (request["context"].get("specification_review") != reference
            or l6.read_ref(reference) != contract
            or l6.reviewer.checked_ref(request["instruction_file"]).read_text(encoding="utf-8").strip()
               != compile_instructions(contract).strip()):
        raise l6.StageFailure("FAILED", "REVIEW_CONTRACT_VIOLATION")


_TAG = re.compile(r"^\[([A-Za-z0-9_-]+)@([A-Za-z0-9_-]+)\] (SATISFIED|UNMET|UNCERTAIN):\s*(\S.*)$", re.DOTALL)


def validate_coverage(contract, result):
    """Structural ID/authority/coverage checks; not semantic entailment proof."""
    criteria = {c["criterion_id"]: c for c in contract["criteria"]}
    def parse(text):
        match = _TAG.fullmatch(text)
        if match is None:
            raise ValueError("unsupported/malformed criterion evidence")
        cid, authority, status, evidence = match.groups()
        if cid not in criteria or criteria[cid]["authority_ref"] != authority:
            raise ValueError("unknown criterion or authority mismatch")
        return cid, status
    coverage = {}
    for text in result["observations"]:
        cid, status = parse(text)
        if cid in coverage:
            raise ValueError("duplicate criterion coverage")
        coverage[cid] = status
    if set(coverage) != set(criteria):
        raise ValueError("incomplete applicable criterion coverage")
    blockers = set()
    for text in result["blocking_issues"]:
        cid, status = parse(text)
        if (not criteria[cid]["blocking_when_unmet"] or status != "UNMET"
                or coverage[cid] != "UNMET" or cid in blockers):
            raise ValueError("blocking authority violation")
        blockers.add(cid)
    unmet = {cid for cid, c in criteria.items() if c["blocking_when_unmet"] and coverage[cid] == "UNMET"}
    if blockers != unmet:
        raise ValueError("blocking coverage mismatch")
    if result["verdict"] == "PASS" and (blockers or any(
            c["blocking_when_unmet"] and coverage[cid] != "SATISFIED" for cid, c in criteria.items())):
        raise ValueError("blocking criteria not satisfied")
    if result["verdict"] == "REVISE" and not blockers:
        raise ValueError("REVISE has no authorized blocker")
    return coverage


def check_result(run_dir, stage, request, result, result_path, invocation_path):
    contract = review_contract(run_dir, stage)
    if contract is None:
        return None
    try:
        check_request(run_dir, stage, request)
        coverage = validate_coverage(contract, result)
        if stage == "geometry":
            from scenario_a import l7_geometry_review as bridge
            bridge.validate_action(result)
        elif not ((result["verdict"] == "PASS" and result["suggested_action"] == {"code": "NONE", "target": None})
                  or (result["verdict"] == "HUMAN_REQUIRED" and result["suggested_action"] == {"code": "HUMAN_REQUIRED", "target": None})
                  or (result["verdict"] == "REVISE" and result["suggested_action"]["code"] == "MULTIVIEW_REVISE"
                      and result["suggested_action"]["target"] in (*l6.VIEWS, None))):
            raise ValueError("unsupported bound stage action")
        if (result["review_id"] != request["review_id"] or result["artifacts"] != request["artifacts"]
                or result["source_result"] != request["source_result"]):
            raise ValueError("bound result/evidence lineage mismatch")
    except (ValueError, KeyError, TypeError) as exc:
        # Caller retains raw Result and invocation; no reclassification as intent ambiguity.
        raise l6.StageFailure("FAILED", "REVIEW_CONTRACT_VIOLATION") from exc
    data = {"session_binding": l6.reference(Path(run_dir) / "session_binding.json"),
            "criteria": l6.reference(Path(run_dir) / (stage + "_criteria.json")),
            "request": l6.reference(Path(invocation_path).with_name(
                "review_request.json" if Path(invocation_path).name == "review_invocation.json"
                else stage + "_review_request.json")),
            "result": l6.reference(result_path), "invocation": l6.reference(invocation_path),
            "coverage": coverage, "verdict": result["verdict"]}
    path = Path(result_path).with_name(Path(result_path).stem + "_coverage.json")
    if path.exists():
        if l6.read_json(path) != data:
            raise l6.StageFailure("FAILED", "REVIEW_CONTRACT_VIOLATION")
    else:
        l6.write_once(path, data)
    return l6.reference(path)


def internal_accept_candidate(parent_ref, final_dir):
    """Current bound artifact + final geometry Review only; no delivery transport."""
    from scenario_a import l7_geometry_review as bridge
    from scenario_a import l7_feedback_controller as controller
    final_dir = Path(final_dir)
    record, data, boundary, binding = checked_child(final_dir, parent_ref=parent_ref, execution=True)
    terminal = l6.read_json(final_dir / "terminal.json")
    for ref in terminal["records"].values():
        if ref is not None:
            l6.reviewer.checked_ref(ref)
    if record["kind"] == "bridge":
        if terminal["state"] != "GEOMETRY_REVIEWED":
            raise ValueError("current final bridge not reviewed")
        result = bridge.checked_review(final_dir)
        artifact = bridge.validate_input(l6.read_json(final_dir / "initial.json"))["artifact"]
        request_path = final_dir / "review_request.json"
        result_path = final_dir / "review_result.json"
        invocation_path = final_dir / "review_invocation.json"
    elif record["kind"] == "correction":
        if terminal["state"] != "INTERNAL_ACCEPT":
            raise ValueError("current correction not accepted")
        result = controller.checked_review(final_dir, "geometry")
        artifact = controller.validate_geometry(final_dir)
        request_path = final_dir / "geometry_review_request.json"
        result_path = final_dir / "geometry_review_result.json"
        invocation_path = final_dir / "geometry_review_invocation.json"
    else:
        raise ValueError("GEOMETRY_READY is not final Review authority")
    if (result["verdict"] != "PASS" or result["blocking_issues"]
            or result["suggested_action"] != {"code": "NONE", "target": None}):
        raise ValueError("current final Review not acceptable")
    manifest = l6.read_ref(l6.read_json(request_path)["source_result"])
    if manifest["source_glb"] != artifact:
        raise ValueError("artifact/final Review lineage mismatch")
    coverage_ref = check_result(final_dir, "geometry", l6.read_json(request_path), result, result_path, invocation_path)
    lineage = []
    source = record
    while True:
        child_dir = Path(source["run_directory"])
        checked_child(child_dir, parent_ref=parent_ref)
        lineage.append(l6.reference(child_dir / "terminal.json"))
        if source["source"] is None:
            break
        source = l6.read_ref(source["source"])
    for ref in lineage:
        child_terminal = l6.read_ref(ref)
        if not child_terminal["terminal"]:
            raise ValueError("child not terminal")
        for entry in child_terminal["records"].values():
            if entry is not None:
                l6.reviewer.checked_ref(entry)
    candidate = boundary._record("scenario_a_accept", {
        "status": "INTERNAL_ACCEPT_CANDIDATE", "specification": data["specification"],
        "session_binding": l6.reference(final_dir / "session_binding.json"),
        "artifact": artifact, "request": l6.reference(request_path), "result": l6.reference(result_path),
        "invocation": l6.reference(invocation_path), "coverage": coverage_ref,
        "criterion_ids": data["stage_criteria"]["geometry"], "child_terminals": lineage,
        "delivered": False})
    refs = tuple(session.file_identity(r["path"], "child-terminal") for r in lineage)
    return boundary.internal_accept(binding, session.file_identity(artifact["path"], "final-glb"),
        session.file_identity(result_path, "final-geometry-review"), (candidate,) + refs)


def block_for_ambiguity(parent_ref, ambiguity, current_child=None):
    data, boundary, binding = checked_parent(parent_ref, execution=True)
    if type(ambiguity) is not session.SpecificationAmbiguity or len(set(ambiguity.alternatives)) < 2:
        raise ValueError("two explicit intent alternatives required")
    ambiguity.validate()
    child_ref = None
    if current_child is not None:
        from scenario_a import l7_geometry_review as bridge
        from scenario_a import l7_feedback_controller as controller
        path = Path(current_child)
        record, _, _, _ = checked_child(path, parent_ref=parent_ref)
        state = l6.read_json(path / "state.json")
        if not state["terminal"] and state["state"] != "UNRESOLVED":
            if record["kind"] == "l6":
                l6.finish(path, "ABORT", "SPECIFICATION_AMBIGUITY", "specification")
            elif record["kind"] == "bridge":
                bridge.finish(path, "ABORT", "SPECIFICATION_AMBIGUITY")
            else:
                controller.finish(path, "ABORT", "SPECIFICATION_AMBIGUITY")
        child_ref = l6.reference(path / "state.json")
    boundary._record("scenario_a_ambiguity", {"loop_run_id": binding.loop_run_id,
        "ambiguity": asdict(ambiguity), "child_stop_evidence": child_ref,
        "effects_stopped": True})
    return boundary.stop_for_ambiguity(binding.specification, ambiguity)

def run_session(parent_ref, *, comfy_root=l6.worker.DEFAULT_COMFY_ROOT,
                blender_executable=None, execute=False, worker_timeout=600,
                review_timeout=600, render_timeout=600):
    """One fixed Scenario A path. Default is zero-effect capability preflight.

    S3B tests exercise execute=True only with production adapters mocked.
    Explicit actual execution is reserved for a separately authorized milestone.
    """
    from scenario_a import l7_geometry_review as bridge
    from scenario_a import l7_feedback_controller as controller
    data, boundary, _ = checked_parent(parent_ref, execution=True)
    if min(worker_timeout, review_timeout, render_timeout) <= 0:
        raise ValueError("timeouts must be positive")
    # Prevalidate the whole fixed capability before the first Worker effect.
    l6.preflight(comfy_root)
    renderer = bridge.blender_identity(blender_executable or bridge.BLENDER)
    script = l6.reference(bridge.SCRIPT)
    if not execute:
        return {"status": "PREFLIGHT_PASS", "session_binding": parent_ref,
                "child_ids": data["child_ids"], "capability": CAPABILITY, "limits": CAPS,
                "renderer": renderer, "script": script, "effects": 0, "delivered": False}
    ids = data["child_ids"]
    l6_dir = l6.ROOT / "runs/l6" / ids["l6"]
    bridge_dir = bridge.ROOT / "runs/l7" / ids["bridge"]
    correction_dir = controller.ROOT / "runs/l7" / ids["correction"]
    if any(path.exists() for path in (l6_dir, bridge_dir, correction_dir)):
        raise ValueError("BOUND_ATTEMPT_ALREADY_EXISTS: no automatic resume")
    result = l6.run_pipeline(ids["l6"], comfy_root, worker_timeout, review_timeout,
                              execute=True, session_binding=parent_ref)
    if result["state"] != "GEOMETRY_READY":
        boundary.stop("FAILED" if result["state"] in ("FAILED", "UNRESOLVED") else "ABORT", result["state"])
        return result
    result = bridge.run_bridge(ids["bridge"], renderer["executable"], render_timeout, review_timeout,
        execute=True, session_binding=parent_ref, source_l6_run=l6_dir)
    if result["state"] != "GEOMETRY_REVIEWED":
        boundary.stop("FAILED" if result["state"] in ("FAILED", "UNRESOLVED") else "ABORT", result["state"])
        return result
    review = bridge.checked_review(bridge_dir)
    if review["verdict"] == "PASS":
        accepted = internal_accept_candidate(parent_ref, bridge_dir)
    elif review["verdict"] == "REVISE":
        result = controller.run_feedback(ids["correction"], bridge_dir, comfy_root,
            renderer["executable"], worker_timeout, review_timeout, render_timeout,
            execute=True, session_binding=parent_ref)
        if result["state"] != "INTERNAL_ACCEPT":
            boundary.stop("FAILED" if result["state"] in ("FAILED", "UNRESOLVED") else "ABORT", result["state"])
            return result
        accepted = internal_accept_candidate(parent_ref, correction_dir)
    else:
        boundary.stop("ABORT", "HUMAN_REQUIRED")  # No automatic intent-ambiguity inference.
        return {"state": "ABORT", "reason": "HUMAN_REQUIRED", "delivered": False}
    return {"state": "INTERNAL_ACCEPT", "candidate": asdict(accepted), "delivered": False}
