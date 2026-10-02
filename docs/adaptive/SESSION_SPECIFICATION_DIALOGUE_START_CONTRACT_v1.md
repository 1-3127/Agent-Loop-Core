# Session Specification Dialogue Start Contract v1

Prospective amendment, 2026-10-02. The explicit fresh-004 User order requires a
User-granted top-level Session before Specification Dialogue, and forbids Frozen
Specification before actual clarification. Its ACTUAL entry was blocked by
SESSION_START_FROZEN_SPECIFICATION_REQUIRED. Original failed evidence is preserved;
this correction is not permission to retry that entry or start another Session.

## Two phases within one User-started Session

This amendment supersedes only the freeze-before-creation timing in
SESSION_START_AUTHORITY_CONTRACT_v1. That original document and previous checkpoint
evidence remain unchanged. User-only origin, exact SID/Request binding, runtime
User provenance, single-use ledger, finite expiry, no reuse/refund, current-Session
Frontier autonomy, terminal wait and trusted-ingress limitations remain in force.

1. Outer preflight independently validates the explicit User grant and exact
   Request authority before namespace/intake. Request authority may pin the exact
   original Request and Reference FileIdentities in a small immutable manifest.
   This manifest is subject authority identity, not a Frozen Specification.
2. `core.adaptive_loop.SpecificationDialogueSession` creates one SessionBoundary
   with the grant, exact Request authority and SID, before any freeze. Only that
   boundary consumes the grant. Its immutable start record and ledger carry
   start_phase=SPECIFICATION_DIALOGUE and exact Request identity; they do not
   contain null/default/invented Frozen Specification fields.
3. Its owned EventLogger records USER_SESSION_START_AUTHORITY_RECEIVED,
   SESSION_START_GRANT_VALIDATED, SESSION_START_GRANT_CONSUMED and SESSION_BOUND
   with USER_REQUEST_BOUND_SPECIFICATION_PENDING. This SESSION_BOUND binds User
   authority to the top-level Session; it does not mean production is eligible.
4. Actual Frontier intake/clarification may run under this live dialogue owner.
   The outer host records WAITING_FOR_USER_SPECIFICATION_CLARIFICATION and waits
   for actual User evidence whenever decisive ambiguity remains. No timeout/default
   or synthetic User response; no Frozen Specification, Run, Attempt, Worker,
   production Reviewer, Blender/ComfyUI or production Artifact until resolution.
5. After resolution, the caller freezes exactly one ready Work Specification and
   scope/envelope, then passes the **same live** dialogue_session to AdaptiveSession.
   Core verifies mode, directory, SID, exact consumed Request in Frozen authority
   refs and ready Specification. It reuses the original boundary/logger and emits
   FROZEN_SPECIFICATION_BOUND. There is no second boundary constructor, namespace,
   grant validation/consumption, authority rewrite or top-level Session.
6. Production controls become available only after that binding; normal bounded
   Run/Attempt/review/Frontier/acceptance/delivery semantics are unchanged.

## Guards and compatibility

Missing, foreign/stale or synthetic-on-ACTUAL authority still rejects before
creation/consumption. Missing/foreign expected Request is rejected. Grant reuse is
rejected immediately after dialogue start. Not-ready/foreign SID or Request Frozen
Specifications cannot enter production. Current terminal guards also apply before
promotion. One live owner can bind one loop; re-promotion is rejected.

Disk handles remain available for historical reading. They cannot promote a
pre-freeze dialogue: its later binding requires the live creation owner. Hosts
retain SpecificationDialogueSession in memory across actual User waiting; there
is no replay, reader-to-owner conversion, recovery/resume or new auth framework.
An interrupted/failed consumed start is not refunded or resumed.

The previous direct AdaptiveSession-with-ready-Frozen API remains guarded and
testable; its legacy event sequence is preserved. Existing local SYNTHETIC fixtures
remain synthetic and do not validate ACTUAL semantic success or Skill promotion.
Request Bundle inheritance remains deferred. No prior clarification/Spec/Artifact
becomes new User intent. No historical proof, v1.2 or authority-fix bytes are rewritten.

## This correction's stop boundary

fresh-004 failed before a Core Session/consumption was created. Record actual counts
honestly: received=1, outer validated=1, consumed=0, top-level created=0, intake=0
and all production effects=0. The proof namespace is failed entry evidence, not a
Core terminal. Retire this execution after the observed defect; do not fabricate a
consumption or terminal record. Fix -> focused -> related -> full -> checkpoint ->
normal push/equality -> SESSION_RESTART_AVAILABLE / WAITING_FOR_USER_SESSION_START.
Only a separate later explicit User start instruction permits another ACTUAL entry.
