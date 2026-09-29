"""Attach a validated refinement Review and replay the existing Controller policy."""

import copy

import ac6_f2_geometry as geometry
import ac6_f2_review_route as image_review
import ac6_f2_refinement as refinement
import persist_geometry_state as persistence
import pipeline_a_controller as controller


def attach(request_ref, pending_ref, evidence_ref, manifest_ref,
           review_request_ref, result_ref, invocation_ref, *,
           output_root=geometry.coverage.OUTPUT_ROOT, evidence_dir=geometry.ROOT / "runs",
           allow_control_fixture=False):
    execution_request = geometry.read(request_ref)
    before = geometry.read(pending_ref)
    source, review_request, review = image_review.checked_review(
        review_request_ref, result_ref, invocation_ref, allow_control_fixture)
    expected = refinement.reviewer_request(
        execution_request, before["intent_receipt"], before["result"], pending_ref,
        evidence_ref, manifest_ref, output_root=output_root, evidence_dir=evidence_dir,
        allow_reserved=True)
    if (review_request != expected or review_request["state"] != pending_ref
            or review_request["context"]["run_id"] != before["run_id"]
            or review_request["source_result"] != before["result"]
            or review["source_result"] != before["result"]):
        raise ValueError("refinement Review lineage differs")
    if before["state"]["current_state"] != "REFINEMENT_REVIEW" or not before["pending_semantic_review"]:
        raise ValueError("refinement pending state differs")
    after = copy.deepcopy(before)
    after["state_version"] = "ac6-f2-refinement-review.0"
    after["refinement_request"] = request_ref
    after["review_source_state"] = pending_ref
    after["evidence_request"] = evidence_ref
    after["evidence_manifest"] = manifest_ref
    after["review_request"] = review_request_ref
    after["review_invocation"] = invocation_ref
    after["review"] = {"path": source["path"], "sha256": source["sha256"]}
    after["review_verdict"] = review["verdict"]
    after["pending_semantic_review"] = False
    after["state"]["latest_review"] = after["review"]
    controller.validate_state(after["state"])
    if (after["state"]["current_state"] != "REFINEMENT_REVIEW"
            or after["state"]["latest_artifact"] != before["glb"]
            or after["state"]["iteration_count"] != before["state"]["iteration_count"]
            or after["state"]["action_counts"] != before["state"]["action_counts"]
            or after["state"]["action_history"] != before["state"]["action_history"]
            or after["remaining_total_iterations"] != before["remaining_total_iterations"]
            or after["terminal"] is not False):
        raise ValueError("refinement Review attachment changed execution state")
    return after


def controller_input(attached_ref, *, output_root=geometry.coverage.OUTPUT_ROOT,
                     evidence_dir=geometry.ROOT / "runs", allow_control_fixture=False):
    attached = geometry.read(attached_ref)
    if attached.get("state_version") != "ac6-f2-refinement-review.0":
        raise ValueError("refinement Review-attached state version differs")
    expected = attach(attached["refinement_request"], attached["review_source_state"],
                      attached["evidence_request"], attached["evidence_manifest"],
                      attached["review_request"], attached["review"], attached["review_invocation"],
                      output_root=output_root, evidence_dir=evidence_dir,
                      allow_control_fixture=allow_control_fixture)
    if attached != expected:
        raise ValueError("refinement Review-attached state differs")
    source = image_review.review_source(attached["review_request"], attached["review"],
                                         attached["review_invocation"])
    signal = controller.load_signal(source)
    if (signal["kind"] != "RESULT_REVIEW" or signal["stage"] != "REFINEMENT_REVIEW"
            or signal["artifact_type"] != "geometry"
            or signal["state_ref"] != attached["review_source_state"]
            or signal["decision"] != attached["review_verdict"]):
        raise ValueError("refinement Controller Review provenance differs")
    item = {"schema_version": "0.1", "state": attached["state"],
            "source": source, "normalized_action": None}
    decision = controller.decide(item)
    if decision["run_id"] != attached["run_id"]:
        raise ValueError("refinement Controller run differs")
    return item, decision


def terminal_state(attached_ref, input_ref, decision_ref, *,
                   output_root=geometry.coverage.OUTPUT_ROOT, evidence_dir=geometry.ROOT / "runs",
                   allow_control_fixture=False):
    item, decision = controller_input(attached_ref, output_root=output_root,
                                      evidence_dir=evidence_dir,
                                      allow_control_fixture=allow_control_fixture)
    if geometry.read(input_ref) != item or geometry.read(decision_ref) != decision:
        raise ValueError("refinement Controller Input/Decision differs")
    if decision["execution_required"] is not False or decision["next_state"] not in persistence.TERMINAL_STATES:
        raise ValueError("refinement Controller did not authorize terminal")
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
            or persistence.guard_execution(after) != "TERMINAL"):
        raise ValueError("refinement terminal invariants differ")
    return after
