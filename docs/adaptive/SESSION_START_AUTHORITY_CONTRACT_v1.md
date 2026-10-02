# Session Start Authority Contract v1

Prospective amendment, 2026-10-02, authorized by the User's Session-start defect
correction Work Order. **That Work Order is not a new Session-start grant.**
The incident report and Work Order identities are in the correction checkpoint.

## Authority and precedence

User → top-level Core Session → Workflow versions → Production Runs → Attempts
→ terminal. Frontier autonomy ends inside the **current top-level Session**.
Only the User may originate top-level Session-start authority.

For future execution this amendment supersedes the standing corrective→fresh /
no-reapproval meaning of adopted v1.2 §26.6/§32, original fresh Proof §13, and
MODULE_CONTRACT_MAP's corresponding corrective continuation wording. Preserve
original v1.2 bytes, old prompts, M0–M8 evidence, fresh-001/002/003 and commits.
Do not retrospectively recast all historical behavior as implementation violation
of a per-start gate that those older contracts did not contain.

No Frontier, Reviewer, Worker, Controller, Diagnosis layer, Execution Adapter,
corrective-development host or Codex orchestration may originate start authority.
One explicit User-originated SessionStartGrant permits **at most one** ACTUAL
top-level Session start.

REVISE, REVISE_ARTIFACT, REVISE_WORKFLOW, RESTART_PRODUCTION_RUN, terminal/FAILED/
CLOSED, defects, corrective completion, regression PASS, commit/push, HEAD equality/
clean, same chat, previous approval, clarification, non-blocking feedback, host
`next` and report recommendations are not grants. Subject authority ≠ start permission.

Reviewer REVISE → Frontier diagnosis → current Run/new Attempt, evidence
acquisition or Workflow revision/new Run. SID/Frozen Spec stay fixed. Strong
Restart is RESTART_PRODUCTION_RUN inside that Session, never NEW_SESSION.
When continuation is impossible: current Session terminal → STOP/report →
SESSION_RESTART_AVAILABLE → WAITING_FOR_USER_SESSION_START. Corrective publication
establishes readiness only; a separate later User instruction is required.

## Grant and trusted User-ingress receipt

`session.session_start_authority` is a narrow creation gate, not a generic auth
framework. The consumer exposes **no receipt/grant issuing API**. A separate
trusted User-ingress boundary supplies pinned receipt FileIdentities and a stable
external consumption-ledger directory. A grant cannot pin its own receipt.

Grant fields: session_start_grant_id, authority_kind=USER_SESSION_START,
user_message_ref (exact bytes/hash), receipt_ref, target_request_authority_ref,
target_session_id, issued_at, expires_at, single_use=true, mode.

The pinned receipt binds the same fields to receipt_id and user_intent=
EXPLICIT_TOP_LEVEL_SESSION_START. Provenance includes source_kind, source_event_ref
and observation_scope. ACTUAL requires TRUSTED_USER_INGRESS /
HOST_ATTESTED_USER_MESSAGE; SYNTHETIC requires SYNTHETIC_USER_FIXTURE /
SYNTHETIC_ONLY. Clarification, Frontier/host-origin claims, arbitrary strings,
unpinned or relabelled synthetic receipts do not authorize ACTUAL. All referenced
message/Request/receipt bytes must match hashes. Missing, malformed, foreign,
stale, consumed and other-Session/Request grants reject before effects.

Pins come from independently observed explicit User events, never model output,
the consumer, or invented human messages. Trusted outer ingress can materialize
observed evidence; it cannot invent intent. A provider event ID or accurately
labelled host receipt/source reference is allowed; do not label an invented ID
as an account signature. issued_at is observed ingress receipt time, not an
invented UI submission time; expiry is a finite technical policy.

ACTUAL additionally requires a `source_event_ref` object with path/offset/bytes/
sha256/thread_id pointing to an exact complete User-message line in the runtime-owned
`~/.codex/sessions` transcript. The gate independently checks root, thread filename,
session_meta identity, response_item/message/role=user, raw event range/hash and
exact extracted input_text bytes against user_message_ref. A fabricated receipt
label or consumer-directory "User event" is rejected even when the consumer pins it.
The raw range stays stable during append; the full transcript/private reasoning
is neither copied nor stored. SYNTHETIC uses an explicitly synthetic source string.

**Trust limit:** this runtime provides source User events and message/attachment
bytes, not signed account attestation. The runtime-owned transcript is the local
origin trust root; trusted ingress remains responsible for interpreting explicit
start intent and independently selecting receipt pins. A privileged host that can
rewrite runtime transcripts or replace trust configuration/ledger can defeat local
attestation; hashes cannot defend against that adversary. No tamper-proof account
verification is claimed. Other runtimes/unknown origin fail closed; no fallback to
self-labelled text. This Work Order provisions **no ACTUAL receipt/grant** and
starts no production Session.

The target Request FileIdentity must match intake and occur as an exact serialized
FileIdentity in FrozenSpecification.authority_references. This is the minimal
Request authority hook, not full cross-Session Request Bundle implementation.

## Outer and Core creation boundaries

Prospective hosts call `prepare_session_namespace` / `preflight_session_start`
before initializer/intake. Invalid authority rejects before target namespace mkdir
or any intake/production continuation. Optional rejected/validated structured audit
is written to an **external development evidence path**. Outer validation does
not consume a grant or create a Core Session; production is a separate step.

AdaptiveSession passes grant/context/Frozen Spec to SessionBoundary. New ACTUAL
SessionBoundary validates and consumes before Session mkdir/session.json/binding.
create_binding also checks the exact consumed SID/mode/Frozen identity. Raw
construction and historical unbound directories cannot bypass the binding gate.
ACTUAL is the default. Existing historical handles are constructible for read-only
inspection without new writes/consumption; that is not resume/new-binding authority.

Explicit mode=SYNTHETIC permits existing local non-production fixtures. Optional
synthetic grants exercise the same validation/ledger. Synthetic mode, pins and
grants cannot authorize ACTUAL or count as actual success/Skill promotion.

Only top-level SessionBoundary creation consumes. Run/Attempt/Reviewer/Frontier
never consumes. Exclusive write-once ledger consumption is keyed by the pinned
User event identity (runtime thread+offset, or synthetic fixture event) and records
the grant ID plus grant/receipt/message/Request/SID/Frozen/time/mode. Renaming a grant
cannot spend the same User start twice. All consumers
of the same ingress retain its stable ledger. Relocation/reset/deletion must never
be used to reuse a grant. Failed/interrupted starts after consumption burn it:
no refund/reuse/resume or transaction recovery. AdaptiveSession checks ordinary
namespace collisions before consumption.

Grant-bound starts preserve USER_SESSION_START_AUTHORITY_RECEIVED,
SESSION_START_GRANT_VALIDATED, SESSION_START_GRANT_CONSUMED and SESSION_BOUND
structured evidence. Failed outer requests may preserve SESSION_START_REJECTED
with reason and zero effects outside the target. No private chain-of-thought.

## Corrective host and historical evidence

After correction/tests/commit/normal push/equality, STOP at
SESSION_RESTART_AVAILABLE / WAITING_FOR_USER_SESSION_START. `next = fresh intake`
is readiness/advice only. Do not execute historical initializer/intake/host scripts
as prospective entry points. Their bytes remain evidence; new hosts must use the
outer gate and pass the grant to Core. README/MODULE_CONTRACT_MAP/AGENTS link this
rule for Codex development orchestration as well as ordinary hosts.

fresh-003 remains interrupted historical evidence: derived LOOP_READY, external
host STOPPED_BY_USER_REQUEST, run-001/attempt-001, unfinished Worker dispatch/
reservation, no Artifact/Review/internal_accept/terminal. No resume, terminal
rewrite, retry/refund/reuse, new Run/Attempt, cleanup or staging.

Request Authority Bundle inheritance/duplicate-clarification handling is deferred:
only the Request-reference hook is added. Human clarification remains subject
authority, never a start grant; no previous machine Spec/Review/Artifact is carried
as new intent authority.
