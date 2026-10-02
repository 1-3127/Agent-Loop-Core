# Actual pre-freeze Session start: host evidence lookup correction

The new User-authorized actual Session successfully passed outer and Core creation
ingress validation, consumed one grant and created one Request-bound pre-freeze
Session. Core persisted USER_SESSION_START_AUTHORITY_RECEIVED,
SESSION_START_GRANT_VALIDATED, SESSION_START_GRANT_CONSUMED and SESSION_BOUND with
USER_REQUEST_BOUND_SPECIFICATION_PENDING. No Frozen Specification was fabricated.

The outer host then failed with KeyError('receipt_ref') while computing the
consumption path from its incomplete pre-receipt grant projection. This occurred
after successful Core creation and before Frontier intake. It is a host defect;
current Core and Session authority contracts require no change. The actual Session
is preserved at REQUEST_RECEIVED with start_phase=SPECIFICATION_DIALOGUE. Its live
owner process terminated. No terminal record was fabricated and it cannot resume.

The minimal prospective correction reads FileIdentity from the canonical
session_start_authority.json consumption_ref that Core already persisted, validates
its byte length/hash, and returns that evidence. It neither recomputes a ledger
locator from a grant projection nor creates/validates/consumes another Session start.

```python
consumed_ref = consumed_start_evidence(dialogue)
```

`host_start.py` contains this helper. The private original failed host source is
retained with a public hash witness. The private prospective host source was fixed
to use this helper and syntax-checked, but it was not executed again. Three synthetic
tests reproduce the actual incomplete-projection failure, verify read-only lookup
without another constructor/validation/consumption, and reject corrupted evidence.

| Regression | Result | Verdict |
| --- | --- | --- |
| focused | 30/30 | PASS |
| related | 143/143 | PASS |
| full | 356/356 | PASS |

These regressions were actually rerun after the host correction. Network,
production-process and repository-write tripwires are zero. Approved local fixture
processes are separately counted. Passing synthetic checks do not demonstrate
actual dialogue, clarification, same-SID Frozen binding or Artifact success.

The first two full regression runs were interrupted after diagnosed failures from
legacy published fixture locations. Their partial logs/results and failure counts
are preserved with hashes and are not presented as full PASS. Final full-003 uses
a test-only locator context for 20 historical C2/C3/C4/static preflight cases.
Those validators execute unchanged against their immutable pinned records at the
original location; no validator, verdict or effect result is substituted. Other
tests, current correction source and Core imports use the clean execution clone.
The historical fixture context is never applied to the actual fresh Session and
is not subject authority for the new task. No historical evidence was rewritten.

SessionStartGrant received=1; validated=2 (outer=1, Core creation=1); consumed=1;
reuse attempts=0; top-level Sessions created=1. Frozen bindings, Frontier
invocations, Runs, Attempts, Workers, Reviewers, Blender/ComfyUI production,
production Artifacts, Workflow revisions and Run restarts all remain zero.

This checkpoint starts from public sanitized `84c55cf27981832be00b9a7eb5dcc11b1b889ff1` and excludes raw local
`fd5ae9d033e01935d08dc031037b39a9bcbc1a58` from ancestry. Only the helper, tests and sanitized verification/report
evidence are publication payload. Original User events/turns, Reference bytes,
provider attribution, absolute runtime paths and private logs stay local-only.
Public provenance records disclose hashes, lengths, logical Request/Reference/grant
identities, validation results and counters. They are local attestations, not public
raw transcript replay or signed account evidence. Inherited public history remains
unchanged; privacy audit applies to every new/changed publication blob and path.

No decisive ambiguity was actually observed, no clarification question was asked,
and no User clarification was received. No Specification, Resource Envelope,
Skill/Workflow, production strategy or acceptance criteria were authored. No mesh,
final diagnostic, production Review, semantic Frontier decision, internal
acceptance, Artifact delivery or Core CLOSED is claimed. Human quality judgment
remains outside Core and has not occurred.

| Proof dimension | Actual result |
| --- | --- |
| A. clean sanitized baseline | PASS |
| B. actual User grant provenance | PASS - actual role=user event/text/Reference bytes checked locally |
| C. single-use grant consumption | PASS - one actual consumption persisted |
| D. Request-bound pre-freeze Session creation | PASS - one actual Core Session and four authority/binding events persisted |
| E. Specification Dialogue | NOT EXERCISED - host stopped before actual Frontier intake |
| F. actual User wait | NOT EXERCISED - no clarification question was dispatched |
| G. clarification binding | NOT EXERCISED |
| H. same-SID Frozen binding | NOT EXERCISED - no Frozen Specification |
| I. no second grant consumption | PASS - count remains one; promotion path itself NOT EXERCISED |
| J. Frontier planning | NOT EXERCISED |
| K. Skill/Workflow | NOT EXERCISED - none selected, created or promoted |
| L. Artifact lineage | PRODUCTION NOT EXERCISED - immutable input/failure evidence only |
| M. Reviewer independence | NOT EXERCISED |
| N. Frontier decisions | NOT EXERCISED |
| O. adaptive Attempt/Run behavior | NOT EXERCISED - actual multi-run adaptation NOT EXERCISED |
| P. INTERNAL_ACCEPT | NOT REACHED |
| Q. CLOSED/delivery | NOT REACHED - exact interrupted state retained |
| R. output package completeness | FINAL ARTIFACT PACKAGE NOT CREATED - failure/correction report and Original Reference available locally |
| S. publication privacy | PASS - new publication payload scanned; raw evidence local-only; post-push verification recorded externally |
| T. historical integrity | PASS - original archival files and protected refs unchanged |

After correction verification and sanitized normal publication, stop at
**SESSION_RESTART_AVAILABLE / WAITING_FOR_USER_SESSION_START**. This consumed grant
is retired. No second actual Session, grant reuse, replay or automatic fresh restart
is authorized. A new explicit User start instruction is required for any later proof.
