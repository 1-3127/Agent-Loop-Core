# Current Reference Dimension Normalization — Corrective Addendum

2026-10-01 (Asia/Seoul). Bounded Scenario A correction; dry/local contract validation only.

## Authority, baseline and defect

Current user's Dimension Normalization corrective request authorizes this checkpoint.
Applicable workspace/repository AGENTS.md and `D:/VSCODE-WorkSpace/Agents/workflow.md`
were read. [Direction Gate philosophy](../Agent-Loop_Direction_Gate_v1.md),
[Core freeze](../../CORE_V1_FREEZE.md), [S1](S1_SESSION_CONTRACT_v0.md),
[S2](S2_SESSION_INTEGRATION_SEAM_AUDIT.md), [S3A](S3A_SESSION_BOUNDARY_LOCAL_PROOF.md),
[S3B/C-01/I-03](S3B_SESSION_BOUND_SCENARIO_INTEGRATION.md),
[Current Reference binding](CURRENT_REFERENCE_INPUT_BINDING_STABILIZATION.md), and
[actual retry failure](fresh-session-refresh-proof-retry/FRESH_SESSION_REFRESH_PROOF_RETRY_RESULT.md)
remain authoritative within their scopes. Historical execution instructions are not new approval.

Start: `fresh-session-refresh-proof-retry` / `75ba8384f2b62714e3452fc781c9530f76f48f4b`;
clean; local = tracking = live remote. New branch:
`stabilization-reference-dimension-normalization`.
The preserved actual result is NOT VERIFIED / RUNTIME_FAILED / FAILED / VIEW_STAGE,
Worker/Comfy 1/1, Blender/Reviewer 0/0, source/test changes0 in that historical attempt.

Reconfirmed current source: staging copied original bytes without dimension normalization;
fixed LoadImage -> VAEEncode -> KSampler -> VAEDecode keeps the input latent dimensions.
The observed 467x539 input yielded a 464x536 right PNG, rejected by L6's 768x768 gate.
The local Comfy VAE crop is consistent with the observed compression-aligned dimensions;
this inference does not change the recorded successful Comfy invocation or failed L6 terminal.
L6 manifest `expected_dimensions` pins 768x768 and the unchanged L6/L7 output validators
enforce it. L6-M3 actual proof used 768x768 front/right/left/back. Geometry uses exact four
reviewed images with CLIPVisionEncode crop=none; no arbitrary-resolution contract was found.
The fix maintains the existing fixed execution contract, without modifying the workflows.

## Policy and authority separation

Scenario-local `reference_normalization.normalize_reference` is a pure bytes transform.
No new dependency: existing Pillow==12.3.0 is reused.

- Target 768x768, contain then centered padding, floor offsets on left/top.
- Smaller images retain all original pixels and dimensions: no upscale, crop or stretch.
- Larger images alone fit the target using fixed LANCZOS and integer-rounded dimensions,
  then pad. Aspect is preserved to the nearest representable integer pixel dimensions.
- Existing canonical padded fixture is RGBA with corner pixel (255,255,255,0); this supplies
  the padding convention, not the image content. RGB uses white; alpha inputs use transparent
  white and preserve content alpha. LoadImage converts to RGB for the image tensor.
- Transformed images use RGB or RGBA, fresh canvas, PNG compress_level=9, optimize=False,
  no inherited metadata. Encoder Pillow/zlib versions are part of the transform contract.
- Already 768x768 is identity: original bytes, pixels, mode and metadata are preserved.
  Original and execution FileIdentity names/paths remain distinct even when their SHA is equal.
- No background removal, semantic crop, enhancement or aesthetic preprocessing.

Original stone authority SHA remains
`9da5ed9e7f3490d058673122a7bd50b46635d4f0b5a36ca3199f0c1636cd17e5`, 362412 bytes,
467x539 RGB. FrozenSpecification/CurrentReference are never changed to claim derivative bytes
as user authority. Deterministic local derivative: 768x768 RGB, 273422 bytes,
SHA `93c081f086bc91821c8aa0ed61e012109d5eb13fd1358c7ef123598dd6574b00`. Resized dimensions 467x539; padding
left150/top114/right151/bottom115. The entire original pixel rectangle is byte-identical.

## Record, staging and propagation

Original FileIdentity -> immutable CurrentReference + Session/Spec authority -> existing
three-child/seven-external namespace gate -> normalization -> exclusive attempt-local
`work/input/l6/<l6_id>/front.png` -> verified normalized identity -> Plan/Work Order ->
invocation/execution -> multiview/geometry -> L7 correction.

`reference_staging.json` now contains original CurrentReference (file/hash, Session and Spec),
parent Session binding reference, attempt run_id, normalization contract/version, original
and resized dimensions, target, padding offsets, modes, encoding/metadata/runtime settings,
normalized bytes/hash, separate `SCENARIO_A_NORMALIZED_EXECUTION_INPUT` FileIdentity and
staged PNG identity. `initial.json` hashes this record and uses the derivative as execution
source; every Work Order/execution already binds that initial contract and Session sidecars.

The original binding and exact attempt are checked before transformation. Exclusive mkdir,
xb creation, flush/fsync and staged hash/dimension checks preserve I-03 collision handling.
Before Worker dispatch, the original authority, Session/Spec/attempt, record hash, fixed
transform record and regenerated derivative hash/size are checked, together with actual
staged PNG bytes/hash/dimensions. Wrong lineage/transform/identity and mutated bytes reject
before production effects. Existing namespaces are never overwritten.

All view Plans and geometry front use `l6/<l6_id>/front.png`; no old-source fallback.
Reviewed generated views remain byte-for-byte staged. L7 inherits verified prior front
Plans/manifests and reuses L6 current-staging guards, so both view and geometry correction
consume the same normalized front. No L7 source/policy/budget change was necessary.
Current binding preflight still reads original authority as its availability substitute for
future inputs; no derivative is written there. Dispatch uses only real staged paths.
Bound-current production normalization occurs after the namespace gate. Unbound and explicit
legacy fixtures retain their existing paths and semantics.

## Local validation and limits

Bundled Python 3.12.14 / Pillow 12.3.0 / zlib 1.3.2; -B; writable process-local TEMP.
All Worker/Reviewer/Blender effects are mocked. Audit gates prohibit production subprocess,
socket connection, DNS and urllib; full-suite process allowlist is the exact pre-existing
package import-only smoke command. Synthetic INTERNAL_ACCEPT is solely a test expectation.

| Suite | PASS | Seconds |
|---|---:|---:|
| Dimension normalization | 13/13 | included in focused |
| Existing Current Reference binding | 18/18 | included in focused |
| Combined focused | 31/31 | 161.188 |
| Full unittest | 244/244 | 565.36 |
| C-01 in full | 10/10 | included in full |
| I-03 in full | 7/7 | included in full |

Full discovery includes all related Session/L6/L7 and explicit legacy fixture regressions.
Failures/errors/skips0. Full tripwires: network0 / production_process0 /
import_smoke_process1. Binding-first and L6-first fresh
import smoke both PASS. Changed-surface review and git diff --check PASS.

Tests use the repository-safe exact failed 467x539 PNG, verify unchanged authority and all
content pixels, no old fixture dependency, real normalized staging/768-square Plan inputs,
multiview and geometry execution identities, identity/no-op, portrait/landscape/large fit,
alpha/metadata, reproducibility across Sessions, source mutation before normalization,
namespace rejection before normalization, derivative mutation before Worker, invalid
Session/Spec/attempt/transform/identity, cross-attempt reuse, both L7 correction paths and
mutated derivative rejection before correction effect.
The 768-square input has no compression-alignment dimension mismatch at the dry/local
contract level. Actual Comfy model output dimensions/quality are not newly verified.

Earlier local focused run failed due to a new test callback passing string instead of Path
to write_report, and an existing assertion expecting one rejection message. Corrected the
callback and allowed the existing hash-validator message: the normalized front now is a
direct Review input, so its mutation can reject earlier at checked_ref. The 18 existing
cases still require ValueError and Worker effect0. No production effect occurred during
the failed run; only final successful reruns are PASS evidence.

## Changed surface, protection and completion boundary

Runtime: `src/scenario_a/l6_pipeline.py` and new
`src/scenario_a/reference_normalization.py`. Tests: new
`tests/test_reference_dimension_normalization.py` and one error-message assertion in
`tests/test_current_reference_binding.py`. Documentation: this new addendum only.

Starting tracked 542; 540 original files retain byte SHA-256;
only the two explicitly listed existing runtime/test files differ. Frozen Core/src/core,
S3A, schemas, S3B/S3C, C-01/I-03 proof, original binding proof, previous Delivery/Closure,
both Fresh Session failures/raw evidence and old source/manifest historical bytes unchanged.
C-01/I-03 test AST is unchanged. External canonical input, four workflows and six models
retain size/mtime; small-file hashes are equal, large model full hashes were not measured.
Protected local refs/tags unchanged; protected live refs are rechecked after publication.

Actual Worker / ComfyUI / Blender / semantic Reviewer / correction / Delivery:
**0 / 0 / 0 / 0 / 0 / 0**. No Fresh Session retry/resume or Delivery.
I-01 circular import and I-02 S3A private API coupling remain unchanged/deferred.

One corrective commit subject:
`fix(scenario-a): normalize current reference dimensions for fixed execution`.
STABILIZED additionally requires its normal push, local = tracking = live remote and clean
tree, checked after publication in the completion report. No force push/reset/amend/rewrite.
This checkpoint does not establish Fresh Session/Refresh VERIFIED, stone-lantern generation
PASS, semantic Reviewer PASS, actual INTERNAL_ACCEPT or Delivery. Historical FAILED/VIEW_STAGE
remains the actual result. Stop after Git equality/protection verification.
