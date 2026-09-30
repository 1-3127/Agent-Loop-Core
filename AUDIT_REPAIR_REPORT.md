# M6.5 audit defect repair report

- Audit basis: user-supplied F01 (High / REAL_DEFECT) and F03 (Medium / REAL_DEFECT), independently reproduced against current source before repair.
- Baseline: `52ffd52abb2470dba5e879f4f8cdba6ad2d33d8d`, main, local HEAD = origin/main, clean at start.
- requested_model = GPT-6.1 Sol; requested_reasoning_effort = High.
- actual_model = UNKNOWN; actual_reasoning_effort = UNKNOWN. This session has no independent model receipt; no value was inferred.
- Outcome: M6.5 AUDIT DEFECT REPAIR PASS. Actual C1-C5 external regression has not run; Core v1 is not frozen.

## F01 reproduction and root cause

Baseline probe: `PYTHONPATH=src python -` with the committed C4 Review Request; terminal lookup redirected to an empty temporary namespace, auth probe mocked, and the actual `review_once` subprocess mocked with the existing valid Review JSON. The same request was passed twice with result/report pairs A and B. Both returned SUCCESS:

`F01_REPRODUCED C4_DECLARED_REVIEW_LIMIT=1 ACTUAL_DISPATCHES=2`

The immutable worker state continued to declare reviewer remaining=1. C4 did not reserve the budget before dispatch, while the generic adapter's duplicate guard only checked caller-selected output paths.

## F01 repair and local proof

- `c4_bounded.py` creates `runs/<run_id>_review_reservation.json` with exclusive create, flush and fsync before calling the generic Reviewer. The run-scoped key enforces the total limit even if a caller changes review_id.
- The reservation binds run_id, review_id, Request path/hash, bounded contract and worker-state references, reserved/consumed flags, consumed budget, both output paths, and timestamp.
- A duplicate returns REVIEW_BUDGET_ALREADY_RESERVED before another dispatch. FAILED, UNRESOLVED, malformed output, and launch failure retain the reservation; there is no automatic refund or retry.
- A new terminal must validate the reservation against Request/output identity and invocation start time, and includes the reservation path/hash. Existing terminal re-entry remains no-effect; historical terminal files were not rewritten.
- Focused tests: 9 PASS. Different output paths, changed review_id, failure, timeout, malformed result, launch error, exclusive-create collision, PASS-to-DELIVERED linkage, and reservation/output mismatch rejection.
- The after-repair equivalent two-output-path probe dispatches once and rejects the second call. PASS/REVISE/HUMAN_REQUIRED terminal policy remains unchanged.

## F03 reproduction and root cause

The baseline memory-only probe mocked local read_bytes and remote urlopen with PNG signature/IHDR width=768, height=768, followed by different invalid payloads:

`F03_REPRODUCED INVALID_PNG_AND_MISMATCH_ACCEPTED`

It returned an image record with dimensions 768 x 768. The same defect was reproduced after F01 repair and before F03 repair. verify_images had read/compared only 24 bytes and never validated the complete PNG or IDAT.

## F03 repair and local proof

- Existing library reused: Pillow 12.3.0 is already installed in the bundled Python and ComfyUI embedded runtime. The default system Python lacks Pillow. No installation or download was performed; `requirements.txt` declares the tested dependency for standalone environments.
- `png_dimensions` uses Pillow verify() for PNG container/chunk CRC validation, then reopens and load() decodes IDAT. It verifies decoded dimensions against IHDR. Because Pillow stops before the IEND CRC, the helper additionally requires the complete canonical IEND at EOF and verifies its stream position, rejecting premature IEND/trailing data.
- verify_images reads the entire /view response and local artifact, requires exact byte equality, then validates/decode the identical bytes. The local ComfyUI server.py /view source returns FileResponse for this request (no preview/channel conversion), supporting full identity comparison.
- Focused tests: 9 PASS. Valid PNG, invalid payload, truncated/missing IEND, corrupt IDAT CRC, undecodable IDAT with a repaired CRC, same-header/different valid payload, corrupt IEND CRC, premature IEND/trailing payload, and tracking rejection without SUCCESS.
- All corrupt fixtures are generated in memory or temporary test directories. Existing production PNGs are read-only; GLB logic is unchanged.

## Full validation

Using existing bundled Python 3.12.14 with Pillow 12.3.0:

```powershell
$env:PATH = 'C:\Users\Worker\.cache\codex-runtimes\codex-primary-runtime\dependencies\python;' + $env:PATH
python -m unittest discover -s tests -p 'test_*.py'
```

- Full local suite: 38/38 PASS.
- Core independence, Scenario A -> Core direction, single src import root: PASS.
- Changed active CLIs with PYTHONPATH=src and --help: PASS.
- Protected historical evidence: work_orders, plans, runs, reviewer_requests, reviewer_results, invocation_reports, usage. Existing evidence modified count = 0; historical M1-M5 proof is unchanged.
- ComfyUI production calls = 0; Frontier semantic Reviewer calls = 0; new production artifacts = 0; production external API calls = 0.
- Research Agent-Loop remains at `7e1572a7e35866519b75b767398288396a27f9b0`; sole untracked F2B WIP SHA-256 remains `2a58ab64e8838e8c3da6d8b4d62526e1a8d0d834bb26058d905d80d73dfd9369`.

## Follow-up boundaries

- F01 = FIXED; F03 = FIXED.
- F02 = ACTUAL REGRESSION NOT YET RUN.
- F04 = DEFERRED_TO_M7: record Reviewer requested model/reasoning and actual identity only if observable; otherwise UNKNOWN.
- F05 = NON-BLOCKING ARCHITECTURAL DEBT.
- F06 = DEFERRED DOCUMENTATION/PROVENANCE: audit identifies no immutable Direction Gate v1 body in the repository snapshot; it was not reconstructed or designated canonical here.
- F07 = CONTRACT DECISION DEFERRED: no complete failure-terminal lifecycle or recovery implementation.
- M7 old prompt = SUPERSEDED / DO NOT RUN. A separate new milestone must use the repaired HEAD.
- No F2B, global idempotency/recovery framework, WorkerPort migration, benchmark, freeze tag, or actual regression was performed.


```text
LOOP CORE V1 TECHNICAL COMPLETE
CORE V1 REFACTOR COMPLETE
M6.5 AUDIT DEFECT REPAIR PASS
POST-REFACTOR C1-C5 ACTUAL REGRESSION NOT YET RUN
CORE V1 FROZEN = NO
```
