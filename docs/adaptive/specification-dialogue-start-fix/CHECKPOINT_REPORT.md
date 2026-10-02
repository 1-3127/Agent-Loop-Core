# Sanitized specification dialogue start correction checkpoint

The actual User-authorized entry failed with
`SESSION_START_FROZEN_SPECIFICATION_REQUIRED` before grant consumption or Core
Session creation. User-origin provenance and outer grant validation were actually
checked; production effects remained zero. This is a failure observation, not a
successful Artifact E2E proof. Sanitized attestations and cryptographic witnesses
are provided; private original evidence remains local. Public summaries do not
permit replay of the private runtime transcript and do not claim signed account
attestation.

The correction adds a Request-bound `SpecificationDialogueSession`, single-use
grant consumption before directory creation, and binding of the ready Frozen
Specification to that same live owner. Existing direct Frozen-Spec Session start
remains supported. The prospective contract changes only start/freeze timing;
original authority contract and historical evidence remain unchanged.

Source/tests/current contract documentation are byte-identical to the tested
correction checkpoint. Existing focused 27/27, related 140/140 and full 353/353
PASS results are reused after SHA-256 and Git blob verification. No regression
rerun or production was performed for this evidence-only publication. The initial
focused 17 PASS / 1 ERROR result is preserved by private evidence hash witnesses.
Synthetic fixture processes are separately counted and are not production effects.

The publication commit has sole parent
`3626ed33f75b37ae02c3a453e4d96f0b1803924f`.
Local raw checkpoint `fd5ae9d033e01935d08dc031037b39a9bcbc1a58` is excluded from
public ancestry. The raw User event, input wrapper, Reference bytes, provider
attribution, private transcript and original logs are not publication payload.
Public witnesses disclose only hashes, lengths, logical identities, validation
results and effect counters. Implementation field names and synthetic fixtures
remain required source code, without actual private identifier values.

Publication auditing covers every new/changed blob and path against the published
parent, including source code. Inherited public history is retained unchanged.
Only this sanitized correction checkpoint may be pushed by normal fast-forward;
no other local ref, tag or evidence checkpoint is publication authority.

No successful new dialogue/E2E, clarification, Artifact, acceptance, delivery or
Core CLOSED state is claimed. No new Session, intake, Worker, Reviewer, host
production, Artifact generation or proof restart is authorized or performed.
Final development state remains:
`SESSION_RESTART_AVAILABLE` / `WAITING_FOR_USER_SESSION_START`.
