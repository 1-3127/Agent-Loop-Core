"""Attach one validated fresh geometry Review without consuming execution budget."""

import copy

import ac6_f2_geometry as geometry
import ac6_f2_review_route as image_review
import persist_geometry_state as persistence
import pipeline_a_controller as controller


def attach(dispatch_ref, pending_ref, evidence_ref, manifest_ref,
           request_ref, result_ref, invocation_ref, *,
           output_root=geometry.coverage.OUTPUT_ROOT, evidence_dir=geometry.ROOT / "runs",
           allow_control_fixture=False):
    dispatch = geometry.read(dispatch_ref)
    before = geometry.read(pending_ref)
    source, request, review = image_review.checked_review(
        request_ref, result_ref, invocation_ref, allow_control_fixture)
    expected = geometry.reviewer_request(
        dispatch, before["intent_receipt"], before["result"], pending_ref,
        evidence_ref, manifest_ref, geometry.ref(geometry.REVIEW_INSTRUCTIONS),
        output_root=output_root, evidence_dir=evidence_dir, allow_reserved=True)
    if (request != expected or request["state"] != pending_ref
            or request["context"]["run_id"] != before["run_id"]
            or request["context"]["evidence_manifest"] != manifest_ref
            or request["source_result"] != before["result"]
            or review["source_result"] != before["result"]):
        raise ValueError("geometry Review lineage differs")
    if before["state"]["current_state"] != "GEOMETRY_REVIEW" or not before["pending_semantic_review"]:
        raise ValueError("geometry Review source state differs")
    after = copy.deepcopy(before)
    after["state_version"] = "ac6-f2-geometry-review.0"
    after["geometry_dispatch"] = dispatch_ref
    after["review_source_state"] = pending_ref
    after["evidence_request"] = evidence_ref
    after["evidence_manifest"] = manifest_ref
    after["review_request"] = request_ref
    after["review_invocation"] = invocation_ref
    after["review"] = {"path": source["path"], "sha256": source["sha256"]}
    after["review_verdict"] = review["verdict"]
    after["pending_semantic_review"] = False
    after["state"]["latest_review"] = after["review"]
    controller.validate_state(after["state"])
    if (after["state"]["current_state"] != "GEOMETRY_REVIEW"
            or after["state"]["latest_artifact"] != before["glb"]
            or after["state"]["iteration_count"] != before["state"]["iteration_count"]
            or after["state"]["action_counts"] != before["state"]["action_counts"]
            or after["state"]["action_history"] != before["state"]["action_history"]
            or after["remaining_total_iterations"] != before["remaining_total_iterations"]
            or after["terminal"] is not False or after["state"]["termination"] is not None):
        raise ValueError("geometry Review attachment changed execution state")
    return after


def controller_input(attached_ref, *, output_root=geometry.coverage.OUTPUT_ROOT,
                     evidence_dir=geometry.ROOT / "runs", allow_control_fixture=False):
    attached = geometry.read(attached_ref)
    if attached.get("state_version") != "ac6-f2-geometry-review.0":
        raise ValueError("geometry Review-attached state version differs")
    expected = attach(attached["geometry_dispatch"], attached["review_source_state"],
                      attached["evidence_request"], attached["evidence_manifest"],
                      attached["review_request"], attached["review"], attached["review_invocation"],
                      output_root=output_root, evidence_dir=evidence_dir,
                      allow_control_fixture=allow_control_fixture)
    if attached != expected:
        raise ValueError("geometry Review-attached state differs")
    source = image_review.review_source(attached["review_request"], attached["review"],
                                         attached["review_invocation"])
    signal = controller.load_signal(source)
    if (signal["kind"] != "RESULT_REVIEW" or signal["stage"] != "GEOMETRY_REVIEW"
            or signal["artifact_type"] != "geometry"
            or signal["state_ref"] != attached["review_source_state"]
            or signal["decision"] != attached["review_verdict"]):
        raise ValueError("geometry Controller Review provenance differs")
    item = {"schema_version": "0.1", "state": attached["state"],
            "source": source, "normalized_action": None}
    decision = controller.decide(item)
    if decision["run_id"] != attached["run_id"]:
        raise ValueError("geometry Controller run identity differs")
    return item, decision


def terminal_state(attached_ref, input_ref, decision_ref, *,
                   output_root=geometry.coverage.OUTPUT_ROOT, evidence_dir=geometry.ROOT / "runs",
                   allow_control_fixture=False):
    item, decision = controller_input(attached_ref, output_root=output_root,
                                      evidence_dir=evidence_dir,
                                      allow_control_fixture=allow_control_fixture)
    if geometry.read(input_ref) != item or geometry.read(decision_ref) != decision:
        raise ValueError("geometry Controller Input/Decision differs")
    if decision["execution_required"] is not False or decision["next_state"] not in persistence.TERMINAL_STATES:
        raise ValueError("Controller did not authorize terminal")
    before = geometry.read(attached_ref)
    after = copy.deepcopy(before)
    after["state_version"] = "ac6-f2-terminal.0"
    after["terminal_source_state"] = attached_ref
    after["controller_input"] = input_ref
    after["decision"] = decision_ref
    after["terminal"] = True
    after["termination_reason"] = decision["termination"]
    after["state"]["current_state"] = decision["next_state"]
    after["state"]["termination"] = decision["termination"]
    controller.validate_state(after["state"])
    if (after["state"]["iteration_count"] != before["state"]["iteration_count"]
            or after["remaining_total_iterations"] != before["remaining_total_iterations"]
            or after["state"]["latest_review"] != before["state"]["latest_review"]
            or persistence.guard_execution(after) != "TERMINAL"):
        raise ValueError("terminal state invariants differ")
    return after
