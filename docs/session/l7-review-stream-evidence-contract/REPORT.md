# L7 Reviewer Stream Evidence Contract Corrective

## Scope and baseline

- Start: `fresh-session-refresh-proof-final-2`, `77ad3aea90a1dd61d0fbf960c867df6776b4020b`.
- Clean tree and local/tracking/live equality were verified before branch creation.
- Corrective branch: `stabilization-l7-review-stream-evidence-contract`.
- Followed workspace `AGENTS.md`, `Others/AGENTS.md`, `Agents/workflow.md`, repository `AGENTS.md`, and Direction Gate v1.
- User request sections 0 and 20 explicitly authorize this branch, bounded source/test/docs/evidence change, one commit, and normal push to `https://github.com/1-3127/Agent-Loop-Core.git`.

## Defect and minimal correction

Bound `l7_geometry_review.finish()` records each actual file as `p.stem: FileReference`, excluding `state.json` and `terminal.json`. Thus `review_invocation.json.stderr` identifies `review_invocation.json.stderr.txt` (and likewise stdout). Consumer `validate_source()` previously appended `.json` to every record key except `review_instructions`.

Before the fix, the exact Final-2 record-key structure in a safe synthetic bound REVISE fixture failed canonical `run_feedback(execute=False)` at `review_invocation.json.stderr.json`. Network and production process tripwires remained zero. The preliminary default Python 3.14 run had no Pillow and failed at import, before reproduction; its raw log is preserved. The successful reproduction and all regression checks use the same bundled Python 3.12.14 as Final-2.

Only `src/scenario_a/l7_feedback_controller.py` changes in production source. Bound validation now enumerates actual source files with the producer's exclusions, retains their paths, and compares each terminal FileReference to the actual canonical path/hash before `checked_ref()`. Required-record coverage, terminal/run identity, Session binding, result schema, geometry linkage, and action policy remain in place. Duplicate stems are rejected before they collapse into a set/dictionary. Resolved evidence outside the source run is rejected. Extension identities remain `.txt` for the two Reviewer streams, `.md` for instructions, and `.json` for ordinary records; a rehashed replacement `.json` stream is rejected even when the original `.txt` is absent. Legacy/unbound validation keeps its fixed required set and extension mapping.

The geometry producer and Reviewer adapter are unchanged. Raw/decoded hashes, byte counts, sanitization, redaction/truncation flags, and write-once stream evidence remain intact.

## Evidence and regression

`tests/test_l7_review_stream_contract.py` adds 16 tests covering the requested A-J semantics plus duplicate stems, unrecorded evidence, terminal identity, parent binding, and older bound fixtures without streams. Fixture construction runs existing synthetic adapters; after construction, Worker/renderer/Reviewer mocks become dispatch tripwires. Canonical effect-free correction preflight reads the current action, bound correction child ID, source terminal identity, and next seed without creating the correction namespace.

The synthetic fixture's 16 terminal record keys equal the exact committed Final-2 structure. In addition, `validate_source()` passed directly against the unchanged Final-2 committed bridge under read-only file-write, network, and process tripwires. Historical terminal SHA-256 remains `fae677dd4c71947d019620fdc82a9a90f48408bc73baf8eb22ec827ad6aa5ba2`; verdict remains REVISE and action remains REGENERATE_GEOMETRY. This check does not resume the failed Session.

| Regression | Result |
| --- | --- |
| New L7 stream contract | 16/16 |
| Existing feedback controller | 44/44 |
| Geometry bridge | 33/33 |
| Reviewer observability | 17/17 |
| Session Scenario / Session boundary / L6 | 41/41 + 23/23 + 34/34 |
| C-01 / I-03 (Session subsets) | 10/10 + 7/7 |
| Current Reference / Dimension Normalization | 18/18 + 13/13 |
| Combined focused | 239/239 |
| Full unittest | 277/277 (261 existing + 16 new) |
| Binding-first / L6-first imports | PASS / PASS |
| git diff --check | PASS |

Final focused and full runs have zero failures/errors/skips. The runner blocks real network and production subprocess launch; its only subprocess exceptions are the exact package-import script and two Python pipe fixtures from existing tests. These local fixture processes are not Codex CLI/model requests.

## Protection and completion boundary

Byte-hash comparison covers all 800 baseline tracked files: only the allowed controller source differs. Frozen Core, all existing runs, Fresh Session attempts, CP1/CP2, historical FAILED terminal and CONTRACT_DEFECT_EVIDENCE, previous actual Loop/Delivery/Closure, observability proof, and C-01/I-03/Reference/Normalization evidence remain unchanged. Baseline protected refs/tags remain unchanged; the new corrective branch is the only intended moving branch.

Actual Worker/ComfyUI/Blender/semantic Reviewer/correction/Delivery/Codex CLI model effects are all zero. Synthetic mock executions in regression are not production effects. I-01/I-02 remain deferred P2. Geometry quality, prompts, models, seeds, views, criteria, Reviewer instructions, correction policy, and budgets are unchanged.

Implementation and regression verdict: PASS. Declare `L7 REVIEW STREAM EVIDENCE CONTRACT = STABILIZED` only after the single corrective commit, normal push, clean tree, and local/tracking/live equality are verified. Publication completion is reported with the exact resulting commit. This corrective does not establish Fresh Session VERIFIED, successful geometry correction, geometry PASS, or INTERNAL_ACCEPT. Do not automatically run a Fresh Session proof.
