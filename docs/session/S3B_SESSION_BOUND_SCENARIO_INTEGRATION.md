# S3B Session-bound Scenario Integration

## Scope / baseline
단일 S3B milestone, branch session-bound-scenario-s3b.
Start a651e38d3435c661185862692e5e69fe9f501ec6 (clean session-boundary-s3a).
local/tracking/live equality 직접 확인; main/Core tag/L6/L7/S1/S2/S3A 보호.
적용 AGENTS.md, Agents/workflow.md, Direction Gate, Core Freeze, S1 templates,
S2 audit, S3A source/proof, L6/bridge/controller/tests/historical evidence 확인.
Baseline 재측정: S3A 23 PASS; full 172 PASS (234.712s).
Network0 / production process0 / exact package import smoke1.
Goal: frozen Spec authority/identity가 fixed L6→L7→correction→accept gate 관통.
Actual Worker/Blender/Reviewer/revision/Delivery 금지. L7-M3 NOT PASSED 유지.

## Checkpoint 1 — L6 binding
- Starting commit: a651e38d3435c661185862692e5e69fe9f501ec6.
- Inspected seams: S3A checked binding/execution guard/child evidence,
  L6 guard/reservation/publish_order/record_execution/manifest.
- Implementation: fixed three-child map; parent pins Spec/Goal/Must-Haves/stage criteria/
  authority/capability/caps. L6 opt-in session_binding; initial pins child sidecar.
  Plan/Work Order/execution/manifest hash sidecars; Core/Work Order/Plan schemas unchanged.
- Invariants: Session != logical Loop != child; same Spec bytes/projection; Ready Gate
  before effects; existing reservation/budget/terminal semantics retained.
- Positive: complete fixture L6 geometry and all record sidecars.
- Negative: Spec mutation/wrong Session,Loop,child/undeclared authority/capability.
- Tests: process-local writable tempfile, Python -B discovery
  test_session_scenario_binding.py: 6/6 PASS (1.886s), audit effect tripwire.
- Effects: network0 / production process0 / import smoke0; adapter calls mocked.
- Limits: Explicit caller-finalized projection validates text occurrence/authority refs,
  not natural-language entailment. Fixed fixed_four_view_glb_seed_only with conservative
  Worker6/Reviewer4/Renderer2/revision1/retry0, no budget DSL/quality guarantee.
  L7 and Review authority compilation remain upcoming internal checkpoints.
- Files: binding module, L6 hooks, focused tests, this cumulative document.
- Commit subject: feat(s3b): bind L6 records to frozen session specification
  (exact identity via git log; avoid self-referential commit hash).
- Result: CHECKPOINT 1 LOCAL PASS.

## Checkpoint 2 — L7 binding
- Starting commit: 3e7d240 (Checkpoint 1).
- Inspected seams: bridge validate_l6/input, render request/manifest, request/invocation;
  controller validate_source/preflight/guard/publish_order.
- Implementation: explicit source_l6_run + session_binding opt-in bridge;
  current source derives from immutable source child ref, never global constant monkeypatch.
  Legacy pinned defaults retained. Bound controller validates same parent before source/correction.
  Correction geometry approved Review resolves current source's L6 manifest directory.
  Bound bridge terminal includes sidecars; controller checks exact durable file set.
- Invariants: current child map, same parent/Spec, hash checked source chain, existing bounds
  and reservation guards. No inherited unbound source PASS becomes bound proof.
- Positive: complete mocked L6→bridge and controller source validation.
- Negative: unbound L6; different parent/Spec L6 or L7; no mock renderer effect on rejection.
- Tests: same focused runner 9/9 PASS (8.817s), network0/process0/import smoke0.
- Limit: Review authority compiler/final acceptance gate not yet completed.
  New source selection is allowed only with Session binding; legacy defaults unchanged.
- Changed files: bridge/controller hooks, focused tests, this document.
- Commit subject: feat(s3b): bind current L7 source and correction to session
- Result: CHECKPOINT 2 LOCAL PASS.
