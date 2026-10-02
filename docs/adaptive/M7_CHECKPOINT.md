# M7 checkpoint: isolated synthetic adaptive proof

M7 is complete on the promotion-contract correction: focused and related tests passed 72/72 and the corrected full regression passed 324/324, with no failures, errors or skips. The persistent proof demonstrates the adaptive control contracts using synthetic inference and artifacts. It does not establish actual Frontier intelligence, Stone Lantern semantic success, or actual Skill validation.

## Implemented modules and contracts

This checkpoint adds the two-Run end-to-end test and immutable synthetic proof, and strengthens `core.skill_artifact.checked_actual_success()`. Both promotion creation and validation-status consumption require actual successful Frontier/Review invocation bindings, the exact accepted Skill/Workflow identity, current accepted Reviews with mandatory MET coverage, current acceptance authority and a CLOSED Session. The local evidence contract does not provide tamper-proof operating-system or remote-service attestation.

The M0-M6 architecture is retained: Frozen Specification, Skill registry, versioned Workflow, Frontier decisions, Session/Run/Attempt controller, Artifact lineage, independent stage Reviews, event reconstruction and local handoff. The structural audit covers 18 module contracts, no Core-to-Scenario imports and unchanged ASTs for the six legacy public Session methods.

## Exact changed surface and checkpoint isolation

Before report preparation, A consisted of one tracked source change (`src/core/skill_artifact.py`), one new test (`tests/test_adaptive_end_to_end.py`) and 110 files under `docs/adaptive/synthetic-proof/`. The checkpoint also includes the M7 reports and verification logs listed below. No M8 source or community discovery contents are part of this payload.

B consisted of 12 files outside this repository: `work/actual_host.py`, `work/actual_extra_views.py`, `work/readiness.py`, the discovery report and eight pinned community source files. They were copied byte-for-byte to a separate local preservation namespace; originals remain in place. The original/snapshot paths, byte lengths and matching SHA-256 values are recorded in `M7_CHECKPOINT_ISOLATION.json`. New M8 source changes were suspended through this checkpoint. No reset, rebase, amend, force push or historical evidence deletion occurred.

## Focused tests and related regression

`M7_FOCUSED.log` contains the current-code combined 72/72 PASS: the end-to-end test and Skill artifact/promotion contracts (11 tests), plus related execution, logging, handoff, transitions, controller, Workflow, Frontier, Review and legacy package/Session boundaries (61 tests). `M7_VALIDATION.json` lists module counts and exact current source/test SHA-256 values. All synthetic tripwires remained zero for network, production process and repository writes; one explicitly allowed local fixture process was used.

## Full regression and retained diagnostics

`M7_FULL_REGRESSION.log` and `.json` record the corrected full suite: 324/324 PASS, zero failures/errors/skips, about 1,167 seconds. Four explicitly allowed local fixture subprocesses ran; no network, production subprocess or repository write occurred.

`M7_PRE_GUARD_FULL_REGRESSION.log` and `.json` retain the earlier 324/324 run as historical pre-correction evidence. They do not substitute for the corrected full suite. `M7_DIAGNOSTICS/local-defect.log` preserves the missing test-helper forwarding failure; `interrupted-regression.log` preserves the prematurely started preliminary regression that was interrupted before production effects. Their originals are also retained outside the repository.

The interrupted log's unfinished test line retains one trailing space from the original test runner output. The immutable diagnostic is excluded from the whitespace-format check; its exact bytes and hash are verified instead. All other staged files pass `git diff --cached --check` with the repository's CRLF policy.

## Persistent synthetic proof and revalidation

The proof is sealed at `synthetic-proof/`. `PROOF_RESULT.json` and `M7_PROOF_REVERIFICATION.json` record:

- Frozen Work Specification identity `6ad047e428899ffb5e1dc13311ca3e56833ed15dbcccd6291fd4732af278f59d` is maintained in the same `synthetic-adaptive-proof` Session.
- Workflow v1 creates `run-001`; its independent synthetic Reviewer returns REVISE with `opening=UNMET`.
- The synthetic Frontier receives that current Review, emits REVISE_WORKFLOW, and records its evidence as the cause of Workflow v2. A separate explicit RESTART_PRODUCTION_RUN decision creates `run-002`.
- Run 2 creates a new Artifact and Review. Both old Artifact A and Review A retain their original bytes and hashes; their public current-lineage checks reject them against Workflow v2/Run 2. The end-to-end test also exercises the controller's stale acceptance rejection.
- Final acceptance contains only Artifact B and its current PASS/MET Review, with the same frozen mandatory criteria. Local synthetic handoff closes the Session without asserting human receipt.
- All 110 proof files stayed byte-identical during revalidation; 72 distinct bound file references were validated, and all 27 events reconstruct in monotonic sequence.
- The Skill remains CANDIDATE; synthetic proof produces no validation record. Negative checks reject synthetic evidence labelled ACTUAL, absent actual invocation refs, absent current acceptance authority and a non-CLOSED attestation before writing any promotion. The test also rejects consumption of a forged VALIDATED record.

The Skill VCS value of forty `1` characters is explicitly a synthetic fixture pin. No claim of live VCS recovery or actual model intelligence is made from this fixture. No separate actual diagnosis invocation is claimed; the synthetic Review/Frontier evidence exercises revision causality.

## Actual effects, artifacts and historical boundaries

There were zero actual Frontier/Worker/Reviewer invocations, ComfyUI generations or Blender production effects in M7. The synthetic `.bin` artifacts are not GLB deliverables. The original adopted Work Specification bytes match the file under `docs/adaptive/WORK_SPECIFICATION_v1.2.md`; M7 introduces no authority change. Historical M0-M6 checkpoints, failed actual Sessions, original references and evidence remain preserved. The only change to an initially tracked source file since the initial baseline is the already-published M6 additive local-handoff method.

## Git checkpoint and push boundary

The containing feature-branch commit is the M7 checkpoint (`git log -1 -- docs/adaptive/M7_CHECKPOINT.md`). Normal push to the authorized `origin` follows this checkpoint. Local HEAD, tracking HEAD, live remote HEAD equality and a clean tree are verified externally after publication, along with unchanged initial historical bytes and protected local refs. The saved user-facing publication report records the resulting commit SHA and verification; this document does not claim a push before it occurs.

## Known limitations and next checkpoint

Model acquisition/deletion/lifecycle integration, generic DAG/DSL, recovery/resume and unrelated I-01/I-02 refactoring remain deferred. Actual model/tool behavior and Stone Lantern semantic acceptance remain unproven until M8.

M8 resumes only after the M7 normal push, three-HEAD equality and clean-tree checks pass. The user starts ComfyUI manually. Immediately before actual M8 execution, readiness is checked again; an unavailable endpoint is reported as `WAITING_FOR_USER_RUNTIME_DEPENDENCY: COMFYUI_NOT_RUNNING` before production effects. It is not an architecture defect, Specification ambiguity or reason for a new Codex Session. M8 retains only the first natural-language request and first Reference Image as authority; prior Stone Lantern Specifications, generated views, GLBs and Reviews do not gain authority.
