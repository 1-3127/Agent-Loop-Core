# L6-M2 Implementation + Local Validation

## 결과

**L6-M2 PIPELINE IMPLEMENTATION READY**

M1 계약을 변경하지 않고 Scenario A sequential runner를 구현했다.
외부 Worker/Reviewer는 focused tests에서 mock으로 대체했다.
실제 자산에는 effect-free static preflight만 수행했다. Level 6 actual proof는 수행하지 않았다.

## Baseline / repository

- Repository: D:\VSCODE-WorkSpace\Others\Agent-Loop-Core
- Remote: https://github.com/1-3127/Agent-Loop-Core.git
- Branch: scenario-a-l6
- M1 start HEAD / origin/scenario-a-l6: 935b5cb746e9b0533f846728b9d87eb02699276e
- Frozen main / origin/main / core-v1.0.0 target: 7eee393801f4d8c14278b43ebcbaabaec7ccc9df
- Start tree clean. Live remote branch/main/tag dereference 확인.
- Root AGENTS.md, Others/AGENTS.md, project AGENTS.md, Agents/workflow.md 적용.
- Annotated tag/release/main 변경 및 merge 없음.

M1 files의 실제 SHA-256은 유지된다:

| File | SHA-256 |
|---|---|
| L6_M1_ASSET_AUDIT.md | 19421bd4b21287df6572406a2b727a9eae93cba80887a50661cd3a0ad6bb2a52 |
| L6_PIPELINE_CONTRACT_v0.md | 4e229bde44eae59e581f7ab749bba3ff764aa8f13e9d922df3dd90de6b2b9f5c |
| L6_ASSET_MANIFEST.json | ceff2ea2ed0ac799ca08673c6d4d912c03e23e16770eaac04dfd9c9160f6a716 |

## Changed files

- src/scenario_a/l6_pipeline.py: fixed sequential execution, Scenario A validators, record/persistence/budget/staging/usage glue.
- tests/test_l6_pipeline.py: 34 focused tests; temporary synthetic graphs/model-file stubs/PNG/GLB and mocked external calls.
- docs/l6/L6_M2_IMPLEMENTATION.md: implementation/evidence report.
- Helper file 추가 없음. 기존 Core/executor/adapters/tests/schema/M1 docs 수정 없음.

## Top-level runner / CLI

Callable:
run_pipeline(run_id, comfy_root, worker_timeout, review_timeout, execute=False).

Default callable/CLI와 --preflight는 static validation만 수행한다.
Actual branch는 명시적인 execute=True / CLI --execute opt-in이 필요하다.
이번 M2에서 --execute CLI를 사용하지 않았다.
Tests의 execute=True는 Worker/Reviewer를 patch한 임시 namespace만 사용한다.

Sequential flow:
validate M1 assets/source → exclusive namespace → immutable initial record →
right → left → back → exact four-role manifest / aggregate records →
run-scoped Review reservation → single Review →
REVISE/HUMAN_REQUIRED이면 ABORT;
PASS이면 reviewed-byte staging → Geometry Work Order/Plan →
Worker reservation → existing executor → GLB verification → GEOMETRY_READY.

Record root: runs/l6/<run_id>.
Binary generated output / staged input은 Comfy work/output 및 work/input/l6/<run_id>에 둔다.
Preflight는 namespace/reservations/output artifacts를 생성하지 않는다.
L6-M2 real-asset preflight namespace l6-m2-static이 생성되지 않았음을 확인했다.

## Existing primitives / minimal glue

Direct reuse:
- codex_to_comfy.validate_plan / run: existing Plan0.1 및 Comfy execution path.
- codex_to_comfy.png_dimensions: CRC/IEND/full decode/dimensions.
- codex_to_comfy.verify_glb: output prefix/path, magic/version/declared length/hash.
- codex_to_comfy.write_report: atomic current-state persistence.
- result_review_adapter.validate_request / checked_invocation:
  checked_invocation에서 existing validate_result를 포함해 identity/schema/verdict 검사.
- result_review_adapter.review_once: existing arbitrary image attachments / one-process call.
- Existing absolute path + SHA reference and exclusive/fsync persistence convention.

Scenario A 전용 추가:
- fixed-role Plans 및 L6 Work Orders / actual-or-mocked Worker Report→Execution summaries.
- Immutable initial budget + current state + per-stage Worker reservations.
- Exactly-once four-role manifest와 aggregate acquisition records.
- Run-scoped exclusive Reviewer reservation.
- Four attachment identity validation / PASS-only geometry gate.
- Reviewed PNG binary staging 및 original/staged identity record.
- Terminal evidence, stopped UNRESOLVED state, usage.
- C4 예약 방식은 참고만 했다. c4_bounded 자체 dependency 없음.
- WorkerPort/F05 generic integration, controller/recovery engine, DAG/DB/DSL/registry 추가 없음.

## Durable identities / failure records

Worker Work Order binds run/stage/task, initial contract, workflow SHA, Plan SHA, input lineage, report paths.
Worker Report는 task/workflow/output node/client/prompt/timestamps/status/output을 확인한다.
SUCCESS output namespace가 해당 run의 fresh prefix와 일치해야 하며 기존 출력이 있으면 effect 전에 거절한다.
Comfy counter는 Report actual filename에서 읽는다. Test output은 00007을 사용해 counter 추측을 검출한다.

Generated PNG identity에는 role/absolute path/bytes/SHA/dimensions/Execution Report reference를 기록한다.
Front는 original identity이며 execution_report=null이다.
Known failure/uncertain에도 Execution summary를 남기고 artifact=null,
Worker Report가 있다면 원본 raw file SHA를 참조한다.
Report가 없거나 malformed이면 invocation/time telemetry를 추정하지 않는다.

Initial budget 문서는 rewrite하지 않는다.
터미널 evidence는 생성된 Work Orders/Plans/Reports/manifest/Review/staging/usage refs를 기록한다.
미발생 record ref는 null이다.

## Control paths — local fixtures only

| Path | Fake Worker calls | Fake Reviewer calls | Geometry calls | Final state |
|---|---:|---:|---:|---|
| PASS | 4 | 1 | 1 | GEOMETRY_READY |
| REVISE | 3 | 1 | 0 | ABORT / MULTIVIEW_REVISE |
| HUMAN_REQUIRED | 3 | 1 | 0 | ABORT / HUMAN_REQUIRED |
| right known failure | 1 | 0 | 0 | FAILED / VIEW_STAGE |
| right uncertain | 1 | 0 | 0 | UNRESOLVED |
| Reviewer known failure | 3 | 1 | 0 | FAILED / REVIEW_STAGE |
| Reviewer uncertain / invocation identity uncertain | 3 | 1 | 0 | UNRESOLVED |
| geometry known failure / invalid GLB | 4 | 1 | 1 | FAILED / GEOMETRY_STAGE |
| geometry uncertain | 4 | 1 | 1 | UNRESOLVED |

모든 경로에서 automatic retry=0이며 후속 expensive effect를 중단한다.
Fixture Report의 CODEX_CLI/process_started 값은 구조를 모사한 temporary local data이며 actual process evidence가 아니다.

## Geometry mapping / byte identity

| Role | LoadImage node | Actual L6 input |
|---|---|---|
| front | 1 | original hunyuan-official-demo-padded.png |
| right | 4 | l6/<run_id>/right.png |
| left | 2 | l6/<run_id>/left.png |
| back | 3 | l6/<run_id>/back.png |

Review attachment order: front,right,left,back.
Hunyuan conditioning order: front,left,back,right.
Role 이름으로 mapping하며 resolution1024/octree128/SaveGLB17을 유지한다.

PASS 후:
- original reviewed artifacts를 다시 hash/decode하여 manifest/Review refs와 대조한다.
- exclusive staging directory/file creation, binary copy.
- no resize/re-encode/crop/rembg/metadata edit.
- staged SHA/bytes/dimensions==reviewed original.
- Geometry publication과 effect 직전에도 PASS/lineage/staged identity를 재검사한다.

Tests에서 output mutation, staged mutation, 동일 내용 staging collision을 검출했다.
Collision의 기존 bytes는 불변이며 Geometry call은0이다.

## Budgets / duplicate / terminal

- Worker limit4; right/left/back/geometry 각 stage slot1.
- Reviewer limit1; result/report/review_id와 독립적인 run-scoped reservation.
- Reservation은 effect 전에 durable exclusive creation하며 failure/timeout/uncertain 이후에도 환불하지 않는다.
- Budget은 reservation files에서 계산하며 mutable state만 신뢰해 slot을 복원하지 않는다.
- 다른 task/report path로 Worker stage reservation을 우회할 수 없다.
- 다른 review_id/result/report path로 Reviewer reservation을 우회할 수 없다.
- consumed≤limit, remaining=limit-consumed≥0.
- GEOMETRY_READY/ABORT/FAILED terminal 이후 Worker/Reviewer/state update/terminal writer/staging을 차단한다.
- Same run re-entry: ALREADY_TERMINAL, terminal bytes/hash 불변, additional effects0.
- Incomplete/UNRESOLVED namespace: L6_RUN_ALREADY_EXISTS. 자동 resume/retry 없음.

## Usage

Stage별 backend/model/invocations/duration과 Frontier provider/auth/calls/duration,
worker/reviewer budgets, final_state를 기록한다.
Invocation이 불명확하면 null, 미실행 stage는 invocations0이다.
requested_model/requested_reasoning_effort는 direct reuse가 CLI override를 전달하지 않으므로 null이다.
actual model/effort/tokens/credits는 independently unobserved이므로 null이다.
Fixture 값을 actual usage로 취급하지 않는다. Collector subsystem 추가 없음.

## Tests / validation evidence

Runtime:
C:\Users\Worker\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
(Python3.12/Pillow; system Python과 별도이며 install 불필요.)

Commands (repository cwd; bytecode writes disabled):
- python -B -m unittest tests.test_l6_pipeline
- python -B -m unittest discover -s tests -p "test_*.py"
- PYTHONPATH=src python -B -m scenario_a.l6_pipeline --help
- PYTHONPATH=src python -B -m scenario_a.l6_pipeline --preflight --run-id l6-m2-static

Results:
- Focused 34/34 PASS.
- Existing frozen 38 tests를 유지했으며 full 72/72 PASS.
- CLI help exit0.
- Real-asset CLI preflight exit0 / PREFLIGHT_PASS / effects0.
- Source PNG integrity/hash, four workflow hashes/nodes/mapping, six model files stat,
  four Plans validate_plan: PASS.
- Tests에는 actual Comfy request_json / Reviewer subprocess.run에 fail-fast tripwire를 두고,
  Worker run / Review review_once를 mock했다. 실제 transport/process call0.
- Synthetic model 파일은 stat용 stub이며 model loading 없음.
- PNG는 Pillow로 생성한 full-valid 768×768 temporary file.
- GLB는 최소 version2 container를 임시 생성하여 기존 verify_glb로 검증한다.
- Focused coverage: missing/duplicate/unknown roles, cross-run execution, Plan mapping,
  PASS/REVISE/HUMAN_REQUIRED, known/uncertain failures,
  reservation bypass, mutation/collision, invalid PNG/GLB,
  terminal re-entry, budget/usage-null, default CLI safety.

## M1 contract self-review

| # | Requirement | Result |
|---|---|---|
| 1 | fixed front/right/left/back | YES |
| 2 | front not generated | YES |
| 3 | review attachment order | YES |
| 4 | exact Hunyuan mapping | YES |
| 5 | PASS-only Geometry | YES |
| 6 | REVISE/HUMAN_REQUIRED no revision | YES |
| 7 | Worker budget4 | YES |
| 8 | Reviewer budget1 | YES |
| 9 | retry0 | YES |
| 10 | byte-identical staging | YES |
| 11 | GEOMETRY_READY meaning not expanded | YES |
| 12 | frozen Core unchanged | YES |
| 13 | Level7 absent | YES |

## Protection / limits

- main/origin/main/tag target unchanged.
- src/core, existing C1–C5 implementation/tests/evidence, schema, freeze/regression/Gate docs diff0.
- M1 three docs unchanged.
- Workflows/source/model stat identity unchanged; workspace assets 쓰기 없음.
- Research HEAD 7e1572a7e35866519b75b767398288396a27f9b0,
  sole untracked ac6_f2b_resume.py hash
  2a58ab64e8838e8c3da6d8b4d62526e1a8d0d834bb26058d905d80d73dfd9369 unchanged.
- Research tracked diff0 / commit/push0.
- Comfy actual submissions = 0
- Frontier semantic Reviewer actual invocations = 0
- Blender executions = 0

Known limits: no actual Qwen/Frontier/Hunyuan execution; no live runtime/model-load success claim.
No comprehensive recovery/resume, concurrent/distributed coordination, generic WorkerPort integration,
quality/cost benchmark, geometry semantic Review, Blender or Level7 behavior.
UNRESOLVED remains stopped and is not successful actual proof.

## Final state

AGENT LOOP CORE V1.0.0 = FROZEN / UNCHANGED
L6-M1 ASSET / CONTRACT READY
L6-M2 PIPELINE IMPLEMENTATION READY
L6-M3 ACTUAL E2E PROOF = NOT STARTED
LEVEL 6 MULTI-STAGE SUPERVISED PIPELINE = NOT VERIFIED
LEVEL 7 CLOSED FEEDBACK PIPELINE = NOT STARTED
HYPOTHESIS BENCHMARK = NOT STARTED
