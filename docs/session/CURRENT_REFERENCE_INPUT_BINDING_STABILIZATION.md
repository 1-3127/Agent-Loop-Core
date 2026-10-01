# Current Reference Input Binding — Corrective Addendum

2026-10-01 (Asia/Seoul). Bounded source/contract correction, local validation only.

## Scope and baseline

Start: `fresh-session-refresh-proof` / `b7bc1d65f6d6c7cf62fdb654591f2061f020cb90`;
clean; local = tracking = live remote. Its parent diff adds the five Fresh Session failure
documents/evidence only. Corrective branch: `stabilization-current-reference-binding`.
Authority: this user's Current Reference corrective request; applicable AGENTS.md and
`D:/VSCODE-WorkSpace/Agents/workflow.md`; [Direction Gate philosophy/contract](../Agent-Loop_Direction_Gate_v1.md),
[Core freeze](../../CORE_V1_FREEZE.md), [S1](S1_SESSION_CONTRACT_v0.md),
[S2](S2_SESSION_INTEGRATION_SEAM_AUDIT.md), [S3A](S3A_SESSION_BOUNDARY_LOCAL_PROOF.md),
[S3B/C-01/I-03](S3B_SESSION_BOUND_SCENARIO_INTEGRATION.md), and the
[Fresh Session failure](fresh-session-refresh-proof/Fresh_Session_Refresh_Proof_2026-10-01.md)
and [candidate](fresh-session-refresh-proof/Fresh_Session_Work_Specification_Candidate_2026-10-01.md).
Historical execution instructions are evidence, not new authorization.

Revalidated defect: L6 preflight selected the pinned old source; view and geometry-front
plans hardcoded `hunyuan-official-demo-padded.png`; parent preparation carried no input
bytes identity. L7 geometry correction also reset front to that filename. Current source
confirmed the failure report rather than an already repaired contract.

Goal: one immutable current PNG reference must pass through frozen authority, Session,
attempt staging and Worker plans/evidence. No generic asset/reference system, Core/S3A
change, Reviewer/correction policy/budget change, actual production run or Delivery.

## Reference authority and preparation

Reuse the unchanged S3A `FileIdentity(identity, path, bytes, sha256)`.
Scenario-local frozen `CurrentReference` contains that file identity, `authority_ref`,
`authority_source`, `session_id`, and `specification_identity_sha256`.
`reference_authority(file)` is the canonical JSON of the exact FileIdentity. Its string
must be a selected `AuthorityReference.source_ref` in the finalized fields **before**
freezing the Specification. Thus bytes/hash are already part of FrozenSpecification
identity and SessionRunBinding identity; no post-freeze path-only attachment is accepted.

Minimal caller sequence (author the new document/fields for its own Request):

```python
file = session.file_identity(current_path, "USER_CURRENT_REFERENCE")
authority = session.AuthorityReference("REF", bound.reference_authority(file))
# Include authority in finalized_fields.authority_references, then freeze:
spec = session.freeze_specification(document, finalized_fields)
binding = boundary.create_binding(spec, logical_loop_id)
current = bound.freeze_current_reference(binding, file, "REF")
parent = bound.prepare(boundary, binding, goal=goal, must_haves=must_haves,
    stage_criteria=stage_criteria, child_ids=child_ids, current_reference=current)
# Production entry receives the Reference through this frozen parent:
checks = bound.run_session(parent, execute=False, comfy_root=comfy_root,
                           blender_executable=blender_executable)
```

Caller-supplied expected bytes/hash may instead initialize FileIdentity directly;
validation refuses incorrect identity. Runtime never replaces expected SHA with a new
observed hash. The Scenario parent version is `s3b-scenario-a.1`, with explicit
`input_mode=current_reference` and serialized current reference. Current parent location/hash,
Session, Spec, authority, PNG integrity/type and source bytes are checked at entry and
before child effects. `run_pipeline(session_binding=parent)` consumes the same record.

New preparation without current Reference rejects `CURRENT_REFERENCE_REQUIRED`.
`legacy_fixture=True` explicitly records fixture compatibility and cannot also carry a
current Reference. Unbound L6 keeps its original fixture behavior. Historical `.0` parent
records remain readable as evidence, but cannot authorize new execution. No bound-current
production plan can silently select the manifest's historical image. Existing C-01/I-03
tests opt into fixture mode only in their common preparation helper; test bodies are unchanged.

## Staging and Worker propagation

I-03's unchanged three-repository-child/seven-external-namespace gate is shared by fixed
entry and direct bound L6. Both dry/execute paths check it; no staging write occurs before
that gate passes. Preflight reuses manifest/workflow/model pins as capability assets while
selecting current source identity in memory. The manifest file is never rewritten.

Validated source bytes are exclusively copied into
`<comfy_root>/work/input/l6/<l6_id>/front.png`, using mkdir/exclusive open/flush/fsync.
Original and copy SHA-256/size must match. `reference_staging.json` records parent,
current Reference and staged identity; `initial.json` binds its hash and the Reference.
Every L6 Work Order/execution links the same initial contract and existing Session sidecars.
Multiview manifest/source and geometry artifacts retain the original front bytes identity.

All view source plans and geometry front use `l6/<l6_id>/front.png`. Reviewed derived
right/left/back are written exclusively into the same owned attempt namespace; only the
validated front may already exist there. Dispatch validates actual staged files, current
binding and exact plan before reservation. L6 staging validation is also reused by L7,
including correction guards. L7 correction preserves the prior verified front patch and
changes only the existing seed/output/derived-view namespace fields.

`codex_to_comfy.validate_plan` adds a keyword-only `planned_inputs` mapping for dry graph
and patch validation before staged/derived files exist. It uses the already verified PNG
as a read-only availability substitute, without creating directories. This is structural
preflight, not proof of future derived outputs. `worker.run()` never accepts/passes that
mapping and still validates real staged paths before transport. Worker Plan schema is unchanged.

## Local validation

Runtime: bundled Python 3.12.14 / Pillow 12.3.0, `-B`, writable process-local TEMP/TMP.
All production adapters are synthetic/mocked. Audit tripwires forbid socket connect/name
resolution and production subprocess; only the existing exact package import smoke is allowed.

| Suite / subset | Result | Seconds |
|---|---|---|
| Current Reference focused | 18/18 PASS | 55.547 |
| Full unittest discovery | 231/231 PASS | 477.579 |
| C-01 in full discovery | 10/10 PASS | included above |
| I-03 in full discovery | 7/7 PASS | included above |
| Existing related Session/L6/L7 in full discovery | 175/175 PASS | included above |

Final suites: failures0/errors0/skips0; network0/production subprocess0;
full package import-only subprocess 1. Binding-first/L6-first fresh-process
import smoke both PASS with network0/production subprocess0. `git diff --check` and changed
surface review PASS. Final full discovery includes all focused tests.

Focused cases: new Reference source/plan/evidence equality; distinct A/B attempts;
wrong expected hash; mutation after freeze and between gate/staging; missing input/binding;
foreign Session/Spec/authority; staging collision in dry/execute; staged-byte mutation;
unsupported non-PNG; explicit fixture compatibility. Repository-safe drawn stone-lantern
fixture follows new identity → preparation → L6 plans. Deleting the old canonical fixture
still permits bound preflight and mock generation; any old filename in its plans fails.
Additional existing-adapter mock integrations cover both geometry and view correction,
exact embedded GLB front-input identity, and staged-front corruption before correction.
Mock INTERNAL_ACCEPT is a test expectation, not an actual production verdict.

Earlier local validation exposed a test callback signature/return expectation, one omitted
entry path variable, and Windows string-form import audit matching; these were corrected.
No production transport/process ran during those failures. A stale intermediate full-suite
process was stopped by its verified task-owned PID; only the final full run above is PASS evidence.

## Changed surface and protection

Runtime files: `src/scenario_a/session_binding.py`, `l6_pipeline.py`,
`l7_feedback_controller.py`, `codex_to_comfy.py`.
Tests: new `tests/test_current_reference_binding.py`; one explicit compatibility-fixture
argument in `tests/test_session_scenario_binding.py`. Documentation: this new addendum only.

Starting tracked files 500; exactly five allowed existing files changed;
the other 495 retain byte SHA-256. All original C-01/I-03 test functions
are AST-identical. Frozen Core/src/core, S3A source/contracts, schemas, historical S3B/S3C,
old penguin proof, Delivery/Closure, C-01/I-03 reports, Fresh Session failure and candidate
are unchanged. The Fresh Session candidate remains CANDIDATE ONLY/NOT FROZEN/NOT EXECUTION READY.
Fixed global input SHA remains `8a6dd9ca3f8984b31c1243e7698cd5030b423464d80e0ad763609148e0ff4f51`. Existing local refs/tags
remain unchanged; protected live refs are rechecked after normal push.

Actual Worker / ComfyUI / Blender / semantic Reviewer / correction / Delivery: **0 / 0 / 0 / 0 / 0 / 0**.
No Fresh Session proof restart, historical resume, merge, protected-ref update or tag creation.
I-01 circular import and I-02 S3A private API coupling remain unchanged and deferred.

## Completion boundary

CURRENT REFERENCE INPUT BINDING — LOCAL CONTRACT REGRESSION = PASS.
The requested STABILIZED verdict additionally requires one corrective commit, normal push,
local = tracking = live remote and final clean tree, verified after publication in the final report.
This correction does not establish Fresh Session/Refresh PASS, stone-lantern generation PASS,
actual INTERNAL_ACCEPT or Delivery. Stop after Git verification.
