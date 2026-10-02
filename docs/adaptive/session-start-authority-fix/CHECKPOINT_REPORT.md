# Session-start authority correction checkpoint

Development correction only; not a new Proof or top-level Core Session.
User Work Order SHA-256: `e0fed679a158351cdb91b4b3eabd451161247f775bc95f2c3136aa9239a89b4f`.
Baseline: `feature/adaptive-skill-orchestration` / `1d13df7a12a19e72e36a653197c8c477f6be5a52`.
Final development state: **SESSION_RESTART_AVAILABLE / WAITING_FOR_USER_SESSION_START**.

## A. Root cause addressed

The incident identified root Codex corrective orchestration as the fresh-002/003
creation actor. Existing loop controllers retained their SID. Historical v1.2 and
Proof wording granted standing corrective-to-fresh continuation, so this correction
does not rewrite historical behavior as a violation of a then-absent per-start gate.

The prospective contract supersedes that continuation meaning. Current AGENTS,
README and MODULE_CONTRACT_MAP bind future hosts to a User-only gate. The outer
`prepare_session_namespace` guard validates before initializer/intake/namespace
creation, and the ACTUAL AdaptiveSession/SessionBoundary ingress independently
validates grant/SID/Request/Frozen identity before creating or binding a Session.
Publication readiness, `next`, chat continuation and clarification do not supply
start authority. Historical host scripts remain immutable evidence, not prospective
entry points. No new intake/host is executed in this correction.

## B. Exact changed surface

Twelve implementation/contract/test files:

- `AGENTS.md`
- `README.md`
- `docs/adaptive/MODULE_CONTRACT_MAP.md`
- `docs/adaptive/SESSION_START_AUTHORITY_CONTRACT_v1.md`
- `src/core/adaptive_loop.py`
- `src/session/session_boundary.py`
- `src/session/session_start_authority.py`
- `tests/test_current_reference_binding.py`
- `tests/test_reference_dimension_normalization.py`
- `tests/test_session_boundary.py`
- `tests/test_session_scenario_binding.py`
- `tests/test_session_start_authority.py`

The four existing SessionBoundary test modules only mark 14 local fixture calls
explicitly SYNTHETIC. No production Scenario, Reviewer, Run/Attempt algorithm or
Frontier vocabulary is changed. Verification evidence is confined to the new
development namespace `docs/adaptive/session-start-authority-fix/`. Its exact file
bytes and index payload are audited before commit; preserved fresh-003 is excluded.
`FINAL_SOURCE_MANIFEST.json` describes the final tested surface. `APPLIED_SURFACE`
records the initial application; `REVIEW_CORRECTION` records the subsequent narrow
three-file correction, so earlier application hashes are not final source hashes.

## C. SessionStartGrant and User-origin boundary

Grant binds ID, USER_SESSION_START kind, exact User message/receipt/Request refs,
target SID, observed receipt issue time, finite expiry, single_use=true and mode.
The consumer has no issuing API. Independent trusted ingress supplies immutable
receipt pins and a stable external consumption ledger. ACTUAL also independently
checks a complete User message line under runtime-owned ~/.codex/sessions: thread
identity, source byte range/hash, role=user and exact input_text bytes. Arbitrary
labels, consumer-directory fake User events, unpinned/self-issued/synthetic ACTUAL
claims and malformed/foreign/stale grants fail closed.

Only the top-level boundary consumes by exclusive write-once ledger creation before
Session mkdir. The key uses User event identity; renaming the grant cannot spend
the same start again. A consumed failed start is burned, never refunded/reused.
Outer preflight does not consume. Existing historical read handles do not consume
or write; creating new bindings remains guarded. SYNTHETIC is explicit and cannot
authorize ACTUAL or establish actual success.

Structured authority-received, validated, consumed and bound events are distinct;
outer rejection may leave external SESSION_START_REJECTED evidence with zero
effects. No private reasoning is stored. Passive observation of this Work Order's
real runtime User event verified provenance only; it created **zero ACTUAL grants**.

## D. Focused checks and preserved findings

Required A-H are exercised by local synthetic fixtures: Workflow revision/new Run
retains SID/Frozen identity without another constructor/intake/consumption; terminal
or corrective readiness without a grant rejects; one explicit synthetic grant binds
one start and rejects reuse; same chat and subject clarification do not authorize;
foreign/stale Request/SID grants reject; malformed Reviewer/Frontier NEW_SESSION
content fails schema/action validation.

Initial focused-001: 13/13 PASS. Related-001: 198/198 PASS. Additional real negative
checks then reproduced two validation gaps: self-labelled ACTUAL provenance was
accepted by validation without a runtime-origin check, and outer validation lacked
a mandatory expected-Request check. focused-002: 15 total, 13 PASS, **2 FAIL**, zero
ERROR/SKIP; original log is preserved. These were validation-only/synthetic tests,
not forced Artifact failures or actual Core Session starts.

A minimal module/contract/test correction added runtime-event verification, exact
outer Request requirement and same-User-event consumption coverage. Final ordered
focused-003 -> related-002 -> full-001 all PASS. Earlier failed evidence is not erased.

## E-F. Final related and full regression

| Phase | Total | PASS | FAIL | ERROR | SKIP | Seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| focused | 17 | 17 | 0 | 0 | 0 | 3.344 |
| related | 130 | 130 | 0 | 0 | 0 | 194.281 |
| full | 343 | 343 | 0 | 0 | 0 | 1212.359 |

For each final phase: network tripwire=0, production-process tripwire=0 and
repository-write tripwire=0. Allowed local fixture subprocess counts are focused=0,
related=4, full=4.
The subprocesses are exact allowlisted package/import and raw-stream fixtures,
not production models/tools. Final full covers all 343 discovered tests, including
legacy binding/dimension normalization, M7 synthetic contracts, M8 actual-success
gates as local tests, closed/collision guards, Reviewer observability and package
boundaries. These results do not establish a new actual E2E Artifact acceptance.

## G. Structural audit

All checks in `STRUCTURAL_AND_HISTORICAL_AUDIT-post-full.json` PASS: no new
Core/Session->Scenario hard import; Reviewer source unchanged; Frontier's eight
actions unchanged and NEW_SESSION absent; only SessionBoundary creation calls
grant consumption; validation/consumption precede mkdir; historical reader branch
precedes creation. No generic auth service/framework, recovery/resume, model policy,
Bundle inheritance or unrelated refactor is added.

## H. Historical integrity

1788 baseline tracked files checked; only the exact authorized surface may change.
All other bytes, including v1.2, M0-M8, fresh-001/002, original Request/Reference,
clarification and terminal evidence, remain unchanged. v1.2 SHA-256 remains
`7be871c5484da15c58f29d6866f8f8e5cb23d42b3fa7bd95c9831bb6a693e020`.
All 45 protected refs and 569 external incident package files remain unchanged.
The incident report identity is recorded in `AUTHORITY_IDENTITIES.json`.

## I. fresh-003 preservation

All 79 fresh-003 files (14 tracked +65 preserved untracked) retain their original
bytes/hash; no new file exists there. SID fresh-spec-dialogue-artifact-003 remains
historical interrupted evidence: derived LOOP_READY, run-001/attempt-001, last
EFFECT_RESERVED and unfinished Worker dispatch/reservation. External host stop is
STOPPED_BY_USER_REQUEST. No Artifact, Review, internal_accept or terminal record
is created. No resume/retry/new Run/Attempt/cleanup/refund/reuse occurs. No fresh-004
namespace exists. Preserved untracked files are never part of this commit payload.

## J-K. Checkpoint publication

This document is part of the checkpoint payload. The containing commit identifies
the publication; post-commit push/equality observations are recorded separately in
the external user-facing `PUBLICATION_VERIFICATION.json` and final checkpoint
report to avoid self-referential commit hashes. Required sequence: all checks PASS
-> exact path/blob audit -> normal commit -> normal push to origin on the same
branch -> local/tracking/live equality -> tracked clean and exact preserved
untracked set. No reset/rebase/amend/force/history rewrite or protected-ref change.

## L. Known limitations

Runtime-owned local User-event provenance is observable; signed account attestation
is unavailable. Trusted ingress still interprets explicit start intent and selects
pins independently. A privileged host able to rewrite runtime transcripts, pins or
the stable ledger defeats local attestation; no cryptographic account guarantee is
claimed. Unsupported runtimes fail closed. No actual grant issuance or start is
tested in this Work Order; permitted synthetic tests and passive real Work Order
origin verification are clearly separate. Future hosts must integrate the guarded
entry; historical host scripts are preserved and must not be used prospectively.

## M. Request Authority Bundle

DEFERRED. Cross-Session clarification inheritance and duplicate-dialogue behavior
are not required for this authority correction. Only exact Request FileIdentity
binding to Frozen authority references is added. Subject clarification never grants
top-level start permission.

## N. Final stop and effect assertions

SESSION_RESTART_AVAILABLE / **WAITING_FOR_USER_SESSION_START** is a development
readiness/report state, not a Core terminal rewrite. At both the correction start
and publication end, added ACTUAL grants=0, Session namespaces/bindings=0, intake=0,
Production Runs=0, Attempts=0, Worker=0, production Reviewer=0, Frontier production=0,
Blender production=0, ComfyUI production=0, Artifact generation=0. Counts refer to
new actual effects in this Work Order; existing historical interrupted reservation
and SYNTHETIC test fixtures are not relabelled. After publication STOP. A separate
later User Session-start instruction is required for a new top-level Session.
