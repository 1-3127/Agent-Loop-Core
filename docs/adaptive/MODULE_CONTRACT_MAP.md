# Adaptive Skill / Workflow Orchestration — Module Contract Map

## Prospective Session-start authority amendment

For User-started Specification Dialogue, [SESSION_SPECIFICATION_DIALOGUE_START_CONTRACT_v1.md](SESSION_SPECIFICATION_DIALOGUE_START_CONTRACT_v1.md) prospectively supersedes the freeze-before-creation timing below and in the original Session-start authority contract. Core consumes one grant at Request-bound dialogue creation, then binds a ready Frozen Specification to the same live Session without another creation/consumption. The original contract/checkpoint and failed fresh-004 entry evidence remain immutable. No post-corrective retry or new Session is authorized.

Future top-level starts also follow [SESSION_START_AUTHORITY_CONTRACT_v1.md](SESSION_START_AUTHORITY_CONTRACT_v1.md), superseding v1.2 §26.6/§32 and this map's historical corrective→new Specification/Session continuation meaning. Original adopted v1.2 bytes remain unchanged. User-only SessionStartGrant authorizes at most one ACTUAL Session; readiness/corrective/tests/push/`next` are not authority. After terminal/corrective publication, stop at WAITING_FOR_USER_SESSION_START.

`session.session_start_authority` is the narrow pinned-receipt/outer-preflight/ledger gate, not a generic auth framework. Prospective initializer/intake calls its gate before namespace creation. SessionBoundary independently validates/consumes at new top-level creation and binds exact SID, Request and Frozen Spec. Historical handles are readable without consumption; synthetic fixtures cannot authorize ACTUAL. Frontier/Reviewer/Diagnosis vocabulary stays unchanged; Run/Attempt restarts retain Session and never consume grants. Request Bundle inheritance is deferred.

M0 contract freeze. Current user-adopted Work Specification v1.2 is normative for this assigned scope; older Direction Gate remains preserved history wherever the current specification changes its scope. Baseline: `fresh-session-refresh-proof-final-3` / `001db7e1377c2b291632d2a80746860cb15d7dcd`.

Authority source SHA-256: `7be871c5484da15c58f29d6866f8f8e5cb23d42b3fa7bd95c9831bb6a693e020`. No new generic DSL, arbitrary DAG, recovery/resume service, model lifecycle manager, or unrelated I-01/I-02 refactor.

Conceptual modules may share the compact implementation files listed below. Existing public Session/Artifact identity contracts and Scenario tool primitives are reused; Core never imports Scenario A. All semantic planning/diagnosis uses an injected Frontier inference adapter. Deterministic mocks are synthetic evidence only. Reviewer cannot invoke execution or restart.

A sequential Workflow version is one Run strategy; parameter/local artifact correction is a new Attempt under the exact same Workflow. Meaningful strategy revision creates a new Workflow version and Production Run, preserving prior artifacts/reviews/terminal evidence. A current acceptance declaration needs every applicable mandatory criterion SATISFIED, with current hashes and lineage. Late human feedback stays outside the trajectory.

Compatibility: legacy fixed Scenario A and human-supplied receipt methods remain testable and historical evidence stays intact. The adaptive delivery seam adds locally verifiable handoff closure without making human acknowledgement a prerequisite. No historical failure is promoted to success.

Storage: existing `runs/session/<session_id>` plus immutable adaptive contract, Workflow/Decision/Artifact refs, `production_runs/run-NNN/attempts/attempt-NNN`, canonical module event records and a hash-bound global event index. Namespace preflight precedes child/expensive effects; unresolved reserved effects cannot be repeated or refunded. File overwrite is avoided for version identities; VCS/hash pins retain historical meaning.

Dependency/call boundary: Specification → Session → Frontier planning → Registry/Workflow preflight → Production Run → Attempt → injected Execution Adapter → Artifact Store → independent Reviewer → Frontier diagnosis → current-lineage Acceptance → Delivery. Logging observes these operations without changing decisions; resource accounting gates each effect. Skill dependency resolution requires existence/version/capability and no cycles.

## Specification Layer

- **Implementation:** session.session_boundary (reuse)
- **Responsibility:** Freeze original request/reference interpretation before Loop; retain one Specification per Session
- **Inputs:** Original request; exact Reference FileIdentity; resolved dialogue; criteria/applicability; envelope
- **Outputs:** FrozenSpecification + adaptive contract projection pinned to specification identity
- **Owned State:** Frozen bytes and explicitly finalized authority fields
- **May Call:** Public freeze_specification / FileIdentity validation
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence
- **Persistent Artifacts:** Frozen Specification; dialogue evidence; adaptive specification contract
- **Failure Vocabulary:** SPECIFICATION_NOT_EXECUTION_ELIGIBLE; SPECIFICATION_CONTENT_CHANGED; UNSUPPORTED_ACCEPTANCE_CRITERION
- **Logging Namespace:** specification
- **Focused Tests:** Existing test_session_boundary + new contract projection tests

## Session Controller

- **Implementation:** core.adaptive_loop
- **Responsibility:** Own one existing SessionBoundary and its adaptive trajectory
- **Inputs:** Frozen Specification; immutable envelope; current reference; adapters
- **Outputs:** Bound Session; terminal result
- **Owned State:** Session current run/attempt and monotonic execution ownership
- **May Call:** Public SessionBoundary methods; Production/Attempt Controller; Frontier; logging; acceptance
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence; direct tool API; same-Session human approval
- **Persistent Artifacts:** Existing Session binding; adaptive contract; terminal
- **Failure Vocabulary:** ALREADY_TERMINAL; SESSION_BINDING_MISMATCH
- **Logging Namespace:** session
- **Focused Tests:** test_adaptive_loop: identity and terminal guards

## Frontier Supervisor

- **Implementation:** core.frontier + replaceable adapter
- **Responsibility:** Obtain model inference for planning and next action, with observable invocation lineage
- **Inputs:** Frozen Specification; Session/Run/Attempt; Workflow; artifacts/reviews; skills/capabilities; remaining envelope
- **Outputs:** Frontier Decision Artifact with structured reason and selected action
- **Owned State:** Decision/invocation identity only
- **May Call:** Injected inference adapter; validators; Skill/Workflow services via controller
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence; direct Worker effect; manufacture Reviewer verdict
- **Persistent Artifacts:** Frontier request; invocation; sanitized stream evidence; Decision Artifact
- **Failure Vocabulary:** FRONTIER_INVOCATION_FAILED; DECISION_CONTEXT_MISMATCH; UNSUPPORTED_ACTION
- **Logging Namespace:** frontier
- **Focused Tests:** test_frontier: context binding, mock boundary, invocation lineage

## Skill Artifact Layer

- **Implementation:** core.skill_artifact
- **Responsibility:** Version portable reusable guidance, metadata, immutable executable knowledge identity
- **Inputs:** SKILL.md and supporting content; provenance/license review; dependency pins; capabilities
- **Outputs:** CANDIDATE version; explicit actual-success validation evidence
- **Owned State:** Skill version/hash/VCS revision and validation records
- **May Call:** File/hash validation; Event Logging
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence; automatic VALIDATED on synthetic PASS; direct Worker calls
- **Persistent Artifacts:** SKILL.md; core.json; immutable validation record
- **Failure Vocabulary:** SKILL_HASH_MISMATCH; SKILL_VERSION_COLLISION; ACTUAL_SUCCESS_REQUIRED
- **Logging Namespace:** skills
- **Focused Tests:** test_skill_artifact: hashes, version immutability, actual-only promotion

## Skill Registry / Discovery

- **Implementation:** core.skill_registry
- **Responsibility:** Resolve local versions and composition; expose reviewed community-copy boundary
- **Inputs:** Local registry; installed capability inventory; pinned community sources/review/license evidence
- **Outputs:** Exact skill refs; admissible dependency order; discovery report
- **Owned State:** Registry candidates and provenance; no Session state
- **May Call:** Skill Artifact validation; reviewed-copy import
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence; Session transitions; Worker; acceptance; execution of unreviewed community commands
- **Persistent Artifacts:** Discovery/reuse report; local reviewed copy; source revision/license/review refs
- **Failure Vocabulary:** DEPENDENCY_MISSING; VERSION_UNRESOLVED; CAPABILITY_UNAVAILABLE; DEPENDENCY_CYCLE; UNREVIEWED_SOURCE
- **Logging Namespace:** skills
- **Focused Tests:** test_skill_registry: all four composition preflights and reviewed-copy rejection

## Workflow Planner

- **Implementation:** core.workflow_artifact + Frontier adapter
- **Responsibility:** Validate a model-proposed compact sequential configuration against authority and installed capabilities
- **Inputs:** Frozen contract; skill refs; capabilities; model proposal; current failure evidence for revision
- **Outputs:** Versioned Workflow Artifact + non-blocking disclosure
- **Owned State:** Planning validation only
- **May Call:** Skill Registry; Workflow Artifact; Event Logging
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence; production execution; inventing missing user intent
- **Persistent Artifacts:** Planning decision; USER_WORKFLOW_REVIEW_REQUESTED_NON_BLOCKING
- **Failure Vocabulary:** WORKFLOW_INVALID; UNSUPPORTED_ACCEPTANCE_CRITERION; CAPABILITY_UNAVAILABLE
- **Logging Namespace:** workflow
- **Focused Tests:** test_workflow_artifact: capability/applicability coverage and declaration boundaries

## Workflow Artifact / Instance

- **Implementation:** core.workflow_artifact
- **Responsibility:** Pin stages, tools/models/skills, authority, version/hash and revision cause
- **Inputs:** Planner configuration; Specification ref; exact Skill refs; source Review/Decision refs
- **Outputs:** Immutable Workflow ref and stage definitions
- **Owned State:** Workflow version and strategy identity
- **May Call:** Artifact/hash validation; Skill Registry composition preflight
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence; recursive retry representation; mutable historical versions
- **Persistent Artifacts:** Workflow vN JSON with evidence-linked revision
- **Failure Vocabulary:** WORKFLOW_VERSION_COLLISION; WORKFLOW_SPECIFICATION_MISMATCH; REVISION_CAUSE_REQUIRED
- **Logging Namespace:** workflow
- **Focused Tests:** test_workflow_artifact: version pins and unchanged Specification

## Production Run Controller

- **Implementation:** core.adaptive_loop
- **Responsibility:** Bind one Workflow version to a fresh Run; supersede old Run when strategy changes
- **Inputs:** Validated Workflow; Frontier Decision; Session; collision preflight
- **Outputs:** Fresh Production Run; preserved terminal/superseded old Run
- **Owned State:** Production Run identity, bound Workflow, terminal
- **May Call:** Attempt Controller; namespace preflight; logging
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence; promote another Run evidence silently; resume historical Run
- **Persistent Artifacts:** Run contract; superseded/terminal record; restart cause
- **Failure Vocabulary:** RUN_NAMESPACE_COLLISION; RUN_ALREADY_TERMINAL; STALE_RUN_EVIDENCE
- **Logging Namespace:** production_runs/run-NNN/controller
- **Focused Tests:** test_adaptive_loop: restart, strategy binding, stale evidence

## Attempt Controller

- **Implementation:** core.adaptive_loop
- **Responsibility:** Manage bounded local corrections under same Run/Workflow; reserve effects before dispatch
- **Inputs:** Current Run; same-strategy Frontier action; resource envelope; adapter namespaces
- **Outputs:** Fresh Attempt; work order; preserved previous attempt outcome
- **Owned State:** Attempt namespace and reservation/consumed effect slots
- **May Call:** Execution Adapter; Artifact Store; Reviewer routing; logging
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence; change strategy in same Run; blind retry after unresolved effect
- **Persistent Artifacts:** Attempt contract; work orders; reservations; result/outcome
- **Failure Vocabulary:** ATTEMPT_NAMESPACE_COLLISION; ENVELOPE_EXHAUSTED; UNRESOLVED_EXECUTION
- **Logging Namespace:** production_runs/run-NNN/attempts/attempt-NNN
- **Focused Tests:** test_adaptive_loop: local Attempt vs strategy Run and reservation guards

## Artifact / Evidence Store

- **Implementation:** core.adaptive_artifacts; session.FileIdentity (reuse)
- **Responsibility:** Retain every meaningful artifact and validate exact current lineage and hashes
- **Inputs:** Produced files; source refs; Session/Run/Attempt; Workflow/Skill identities; producer/event
- **Outputs:** Immutable Artifact refs and validated lineage
- **Owned State:** Write-once metadata; authoritative bytes refs
- **May Call:** Public file_identity / FileIdentity validation; logging
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence; silent current promotion from another Run; acceptance judgment
- **Persistent Artifacts:** Artifact metadata, generated/reference/diagnostic bytes, supporting execution reports
- **Failure Vocabulary:** ARTIFACT_HASH_MISMATCH; ARTIFACT_LINEAGE_MISMATCH; STALE_ARTIFACT
- **Logging Namespace:** production_runs/run-NNN/artifacts
- **Focused Tests:** test_adaptive_artifacts: content mutation, lineage mismatch, retained predecessors

## Reviewer Layer

- **Implementation:** core.artifact_review + semantic inference adapter
- **Responsibility:** Independently judge applicable frozen criteria for current artifact stage
- **Inputs:** Applicable criteria; current artifact; supporting refs; authority context
- **Outputs:** Evidence-bound verdict and criterion outcomes
- **Owned State:** Review request/result/invocation only
- **May Call:** Injected semantic review adapter; evidence validation; logging
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence; Workflow mutation; Worker; Attempt/Run restart
- **Persistent Artifacts:** Stage Review request/result, invocation and stream evidence
- **Failure Vocabulary:** REVIEW_SOURCE_MISMATCH; REVIEW_INVOCATION_FAILED; UNSUPPORTED_CRITERION; HUMAN_REQUIRED
- **Logging Namespace:** production_runs/run-NNN/reviewer
- **Focused Tests:** test_artifact_review: criterion coverage, current-source binding, no execution

## Diagnosis / Decision Layer

- **Implementation:** core.frontier decision validation
- **Responsibility:** Bind next-action judgment to current Review, Artifact, and frozen authority
- **Inputs:** Current Review/Artifact/lineage; Specification; current state; remaining envelope
- **Outputs:** CONTINUE / REVISE_ARTIFACT / ACQUIRE_EVIDENCE / REVISE_WORKFLOW / RESTART_PRODUCTION_RUN / ACCEPT; justified terminal
- **Owned State:** Structured decision and evidence refs only
- **May Call:** Frontier inference adapter; deterministic invariant validation
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence; artifact fabrication; verdict forgery; automatic REVISE-to-seed/restart rule
- **Persistent Artifacts:** Decision + reason summary + cited evidence + selected action
- **Failure Vocabulary:** DECISION_CONTEXT_MISMATCH; ACCEPT_WITH_UNMET_CRITERION; LATE_SPECIFICATION_AMBIGUITY
- **Logging Namespace:** production_runs/run-NNN/diagnosis
- **Focused Tests:** test_frontier + test_adaptive_loop: evidence-bound action and no hidden reasoning transcripts

## Execution Adapter Layer

- **Implementation:** scenario_a.adaptive_adapter; core injected execution interface
- **Responsibility:** Perform explicitly selected tool/API/CLI effects with tool-specific transport validation
- **Inputs:** Reserved work order; exact input refs; selected installed tool/model; unique namespaces
- **Outputs:** Artifact files + Execution Report + observable runtime evidence
- **Owned State:** Tool-local transport state only
- **May Call:** Existing Comfy executor, PNG/GLB validation, normalization, Blender diagnostic helpers; selected Worker/tool
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence; alter Goal or criteria; download/delete model; automatic reuse/resume after failure
- **Persistent Artifacts:** Command/API input; reservation; execution reports; generated/intermediate artifact bytes
- **Failure Vocabulary:** CAPABILITY_UNAVAILABLE; EXECUTION_FAILED; UNRESOLVED_EXECUTION; EXTERNAL_NAMESPACE_COLLISION
- **Logging Namespace:** production_runs/run-NNN/execution
- **Focused Tests:** test_adaptive_adapter: injected effect-light calls, namespace/input checks

## Acceptance / Terminal Layer

- **Implementation:** core.adaptive_loop acceptance gate; existing SessionBoundary
- **Responsibility:** Accept only complete mandatory criterion coverage from current valid lineage; preserve justified terminal failure
- **Inputs:** Current Workflow/Run/Artifact/Review; acceptance criteria/applicability; Frontier ACCEPT
- **Outputs:** INTERNAL_ACCEPT or guarded FAILED/ABORT/BLOCKED terminal
- **Owned State:** Final acceptance evidence and terminal
- **May Call:** Current-lineage validation; public SessionBoundary internal_accept/stop; Delivery Boundary
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence; human-in-loop gate; stale Review authorization; semantic REVISE alone as terminal
- **Persistent Artifacts:** Current criterion coverage; internal_accept; terminal
- **Failure Vocabulary:** ACCEPT_WITH_UNMET_CRITERION; STALE_REVIEW; ALREADY_TERMINAL; ENVELOPE_EXHAUSTED
- **Logging Namespace:** acceptance
- **Focused Tests:** test_adaptive_loop: stale Review rejects, current full coverage accepts

## Delivery Boundary

- **Implementation:** session.session_boundary additive local handoff API
- **Responsibility:** Prepare exact accepted package, observe local submission/handoff record and close without human acknowledgement
- **Inputs:** Current accepted package; locally verifiable handoff/submission evidence; intended boundary
- **Outputs:** CLOSED terminal with delivery evidence and explicit observation limits
- **Owned State:** Delivery package/submission record; no user quality state
- **May Call:** Public accepted-package validation; file identity; local record
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence; demand receipt token/user quality approval; reopen closed Session
- **Persistent Artifacts:** Delivery package; local handoff record; terminal; late feedback stored outside trajectory
- **Failure Vocabulary:** HANDOFF_PACKAGE_MISMATCH; HANDOFF_RECORD_INVALID; ALREADY_TERMINAL
- **Logging Namespace:** acceptance/delivery
- **Focused Tests:** test_session_boundary additive tests: no-human closure, package lineage, legacy receipt preserved

## Event Logging

- **Implementation:** core.event_logging
- **Responsibility:** Keep canonical module-local events and hash-bound global index with Session-local monotonic ordering
- **Inputs:** Event envelope; causal parent; input/output refs; structured decision/reason
- **Outputs:** Canonical event + event_index pointer; reconstructable chronology
- **Owned State:** Session-local event_seq; canonical events; append-only index
- **May Call:** Write-once/hash helpers; validation
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence; duplicate full event payloads in divergent logs; private chain-of-thought persistence
- **Persistent Artifacts:** Module events; event_index.jsonl; reconstruction report
- **Failure Vocabulary:** EVENT_SEQUENCE_INVALID; EVENT_HASH_MISMATCH; CAUSAL_PARENT_INVALID; INDEX_INCOMPLETE
- **Logging Namespace:** module-local canonical event records + global event_index
- **Focused Tests:** test_event_logging: sequence, hash/index reconstruction and no duplicate payload authority

## Deadline / Resource Envelope

- **Implementation:** core.adaptive_loop resource envelope
- **Responsibility:** Freeze inferred/explicit task envelope; account reserved invocations/attempts/time before expensive effects
- **Inputs:** Frozen deadline/limits; monotonic observed elapsed time; consumed reservations
- **Outputs:** Remaining capacity; admitted action or justified terminal
- **Owned State:** Immutable limits and consumed slots within Session
- **May Call:** Controller reservation/clock; logging
- **Must Not Call:** Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence; extend limits silently; infer developer-session time limit; refund unresolved expensive effect
- **Persistent Artifacts:** Frozen envelope; reservation/accounting evidence; exhaustion reason
- **Failure Vocabulary:** ENVELOPE_EXHAUSTED; ENVELOPE_INVALID
- **Logging Namespace:** session/resources
- **Focused Tests:** test_adaptive_loop: pre-effect limits and no unresolved refund

## Model Lifecycle Manager

- **Implementation:** DEFERRED
- **Responsibility:** Remain explicitly deferred; represent required/candidate capabilities without acquisition or cleanup effects
- **Inputs:** Installed capability inventory; metadata acquisition requirement
- **Outputs:** Availability metadata or evidence-backed capability blocker
- **Owned State:** No acquisition/deletion lifecycle state
- **May Call:** Read-only installed capability inventory
- **Must Not Call:** Model download; model delete/cleanup; cache cleanup; lifecycle daemon; Change frozen Goal, mandatory criteria, or reference authority; resume terminal history; erase prior evidence
- **Persistent Artifacts:** Deferred declaration; availability evidence only
- **Failure Vocabulary:** CAPABILITY_UNAVAILABLE
- **Logging Namespace:** skills/capabilities
- **Focused Tests:** Structural audit: no model lifecycle effects

## Checkpoint validation and defect handling

M0 focused validation checks all 18 modules, all contract fields, explicit deferred lifecycle status and normative authority hash. M1–M6 run module-focused and related regressions; M7 runs the complete existing/new suite, synthetic adaptive restart and structural audit before any actual GPU proof. Contract assumption defects stop the affected checkpoint, retain evidence, update this map and revalidate. Actual Session contract defects terminate that Session, receive bounded corrective work, and start a new Specification/Session; the failed Session is never resumed.
