# L6 Pipeline Contract v0

## 1. 지위 / 범위

Scenario A Level 6의 문서 계약이다. Core v1 contract/schema/version을 변경하지 않는다.
Frozen baseline: 7eee393801f4d8c14278b43ebcbaabaec7ccc9df / core-v1.0.0.
Working branch: scenario-a-l6.
Actual asset authority: [L6_ASSET_MANIFEST.json](L6_ASSET_MANIFEST.json);
audit: [L6_M1_ASSET_AUDIT.md](L6_M1_ASSET_AUDIT.md).

M2/M3는 이 asset/interface assumptions를 유지한다. 실제 파일과 충돌하면 명시적 contract revision 판단을 거치며 조용히 node/model/workflow를 대체하지 않는다.
M1은 구현/actual proof가 아니다. M2는 구현과 local validation, M3는 별도 승인된 fresh actual execution이다.

L6 의미: 서로 다른 production stages를 한 programmatic sequential pipeline으로 연결한다.
앞 단계의 fresh artifacts와 Frontier PASS가 실제 다음 Geometry Worker 입력/실행 조건이 된다.

Source → right → left → back → 4-view manifest → Frontier Review once → PASS → Hunyuan3D → fresh GLB → GEOMETRY_READY.

## 2. 고정 자산 / Plan

Comfy root: D:\VSCODE-WorkSpace\Comfy-UI.
Launcher roots: models, work/input, work/output.
Source: work/input/hunyuan-official-demo-padded.png, 768×768,
142572 bytes, SHA-256 8a6dd9ca3f8984b31c1243e7698cd5030b423464d80e0ad763609148e0ff4f51.

| Stage | Existing workflow relative to Comfy root | Input/prompt/seed/output |
|---|---|---|
| right | workflows/02_Image_to_Multiview/Qwen2509_Multiangle_RTX4060_api.json | 1/8/11/13 |
| left | workflows/02_Image_to_Multiview/Qwen2509_Left_api.json | 1/8/11/13 |
| back | workflows/02_Image_to_Multiview/Qwen2509_Back_api.json | 1/8/11/13 |
| geometry | workflows/03_Multiview_to_3D/Hunyuan3D_MV_RTX4060_api.json | LoadImage1/2/3/4, seed14, output17 |

Template hashes, node classes, 핵심 입력/출력 mapping과 sampler parameters는 asset manifest에 고정한다. 전체 graph의 authoritative bytes는 해당 hash의 기존 workflow 파일이다.
세 image Plan은 template prompt를 그대로 사용한다. Template seed29481을 초기 기본값으로 사용하며 Plan에 기록한다.
Geometry seed528364197559477, resolution1024, octree128, num_chunks8000 및 나머지 graph settings 그대로.
새 모델/workflow/quality challenge를 도입하지 않는다.
Input front를 생성 결과로 바꾸거나 regenerated front를 추가하지 않는다.

기존 Plan0.1은 exact fields: schema_version="0.1", task_id, workflow, patches, output_node.
Run/Review lineage를 Plan에 추가하면 validator가 거절하므로 별도 L6 Work Order에 둔다.

Image patches: 1.image=source input 상대 경로, 8.prompt=선택 template 기존 prompt,
11.seed=기록된 seed, 13.filename_prefix=l6/<run_id>/<role>.
Geometry patches: 1/2/3/4.image=아래 exact-role staged input, 14.seed, 17.filename_prefix=mesh/l6/<run_id>/geometry.
추가 scalar/model/resolution 변경 없음. 출력노드 image13 / geometry17.

Output PNG: work/output/l6/<run_id>/<role>_<counter>_.png.
Output GLB: work/output/mesh/l6/<run_id>/geometry_<counter>_.glb.
Counter basename은 Comfy report의 실제 값에서 읽으며 00001 고정 추측 금지.

## 3. Identity / 최소 파일 구조

Fresh run_id는 기존 timestamp+unique short ID 관례를 재사용한다.
예시 prefix l6-m3-<timestamp>-<shortid>; 식별자 문자 [A-Za-z0-9_-], run_id 최대48자로 모든 파생 task/review ID 최대80자 보장.
각 run은 repository runs/l6/<run_id>/ 아래 독립 namespace를 exclusive creation으로 확보한다.
Binary outputs는 Comfy workspace에 두며 기존 evidence를 덮어쓰지 않는다.

최소 future records:

- initial.json: version=l6.0, run_id, created_at, state=SOURCE_READY, source identity,
  asset_manifest path/hash, worker_budget {limit:4,consumed:0,remaining:4},
  reviewer_budget {limit:1,consumed:0,remaining:1}, terminal=false.
- <role>_work_order.json, <role>_plan.json, <role>_worker_report.json,
  <role>_execution.json for right/left/back.
- multiview_manifest.json, multiview_work_order.json, multiview_execution.json,
  review_instructions.md, review_request.json, review_result.json, review_invocation.json.
- geometry_work_order.json, geometry_plan.json, geometry_worker_report.json, geometry_execution.json.
- state.json, terminal.json, usage.json; one-time review reservation.
  Artifact를 아직 만들지 않은 phase의 refs는 null이며 성공한 것처럼 채우지 않는다.

File reference는 existing convention {path,sha256}. SHA는 실제 저장 bytes 기준 lowercase64 hex.
외부 artifact와 Reviewer attachment는 absolute path. 내부 ref도 L6에서 absolute path로 통일하여 resolver ambiguity를 줄인다.
Plan의 workflow/image/filename_prefix는 existing executor가 요구하는 safe relative slash path.

각 stage Work Order 최소:
version=l6.0, run_id, work_order_id=<run_id>-<stage>, stage,
worker_type=ComfyUI, adapter=src/scenario_a/codex_to_comfy.py, requested_task,
expected_output_kind=image 또는 geometry, source 또는 multiview refs,
workflow ref, plan ref, worker_report_path, execution_report_path, initial_contract ref.
C1 Work Order를 c1.0이라고 재표기하거나 c1_delegate의 right-only preflight에 강제로 넣지 않는다.

각 stage Execution summary 최소:
version=l6.0, run_id, work_order_id, stage, work_order/plan/workflow/worker_report refs,
backend=ComfyUI, model filename, actual status,
prompt_id, client_id, started_at, completed_at, artifact identity 또는 null, errors.
Worker report는 existing executor가 실제 생성한 Report0.1이며 summary가 새 invocation을 발명하지 않는다.
SUCCESS는 actual file 검증 뒤에만 기록한다. 단순 /prompt 성공은 artifact 성공이 아니다.

## 4. Fixed four-role artifact / manifest

허용 roles exactly once: front, right, left, back.
front=original source; generated roles=right,left,back.
Unknown/missing/duplicate role, 다른 run의 generated report, historical replay는 거절한다.
추가 top/bottom/detail/3/4/adaptive views는 없다.

Artifact identity:
role, path, sha256, bytes, width, height, execution_report.
Generated role의 execution_report는 해당 L6 execution summary의 {path,sha256}.
Front는 original source이며 execution_report=null; fake execution을 생성하지 않는다.
기존 PNG verifier+full local file read로 dimensions/bytes/hash 확인.

Multiview manifest 최소 exact meaning:
version=l6.0, run_id, source=<front artifact>,
views=[<right artifact>,<left artifact>,<back artifact>].
Manifest는 세 SUCCESS execution과 실제 output refs를 연결하고 source/모든 image identity를 재검증한 뒤 immutable하게 게시한다.
Historical reference만으로 fresh SUCCESS를 만들지 않는다.

multiview_work_order는 fixed view acquisition task와 initial contract/source/workflow/각 stage order refs를 요약한다.
multiview_execution은 run_id, stage=MULTIVIEW, SUCCESS, manifest ref, 세 실제 execution refs만 담는 aggregate summary다.
이 summary는 Comfy invocation report가 아니며 prompt_id를 가짜로 하나 합치지 않는다.

## 5. Frontier multiview Review

Existing core.result_review_adapter request_version0.2 / Result review_version0.3을 직접 재사용.
다음 request fields만 사용한다:
request_version, run_id, review_id, stage, output_kind,
source_result, work_order, worker_report, artifacts, instruction_file, context.
추가 L6 fields를 generic request 최상위에 넣지 않는다.

Bindings:
- stage=MULTIVIEW_REVIEW; review_id=<run_id>-multiview-review; output_kind=multiview_images.
- source_result=multiview_manifest ref.
- work_order=multiview_work_order ref.
- worker_report=multiview_execution ref.
- instruction_file=해당 run의 최소 Review instructions ref.
- context: initial_contract ref, asset_manifest ref, fixed role order, requested task 및 criteria.
- artifacts ordered exactly front/right/left/back.
  각 entry는 existing exact {role,path,sha256,media_type:"image/png"}.
  bytes/dimensions/report refs는 source manifest에 남기며 generic artifact shape에 추가하지 않는다.

기존 generic validation은 role uniqueness/run-linked aggregate semantics를 검사하지 않는다.
M2 Scenario A caller가 manifest/order/execution/run/role/Report SUCCESS/hash 연결을 검증한다.
Invocation Report의 attached_images도 동일 순서/4-path/hash와 일치해야 한다.
Actual CODEX_CLI reviewer_process_started=true, invocation_status=SUCCESS, request/result hash가 확인되어야 actual proof로 인정한다.
CURRENT_SESSION 또는 fixture result를 자동 Reviewer proof로 대체하지 않는다.

Criteria:
same subject identity/major structure, target direction plausibility,
severe crop 없음, major missing/detached parts 없음,
major cross-view contradiction 없음, downstream 3D input을 명백히 막는 defect 없음.
정확한 camera pose를 metadata 없이 수치로 추정하지 않는다.
GLB/topology/UV/texture/PBR/geometry semantic quality는 판단하지 않는다.

| Actual verdict | L6 policy |
|---|---|
| PASS, blockers=[], suggested_action={code:NONE,target:null} | Geometry gate 후보 |
| REVISE, blockers 존재 | ABORT / MULTIVIEW_REVISE |
| HUMAN_REQUIRED | ABORT / HUMAN_REQUIRED |

Generic Result validator가 REVISE에 non-NONE code를 요구한다.
L6 instructions는 diagnostic-only {code:MULTIVIEW_REVISE,target:<front/right/left/back 또는 null>}를 요청한다.
이는 executor command가 아니며 자동 dispatch하지 않는다. target은 원인 역할의 진단 정보다.
HUMAN_REQUIRED는 기존 {code:HUMAN_REQUIRED,target:null}.
Review가 다른 revision action을 제안해도 실행하지 않는다; identity/schema validity를 먼저 검사하고 REVISE는 종료한다.
User를 내부 repair worker로 요청하지 않는다.

Reviewer 호출 전에 durable exclusive reservation을 생성하고 limit1을 소비한다.
동일 review_id 또는 다른 review_id로 run budget을 다시 쓰지 못한다.
Result/report 파일 거절만으로 run budget을 보호했다고 주장하지 않는다.
c4_bounded의 reservation 방식은 참고하지만 c4-specific validators/state를 L6에 가져오지 않는다.

## 6. Geometry gate / exact bytes / mapping

Validated actual PASS에서만 geometry Work Order와 실행 Plan을 생성한다.
Order가 참조할 필수 refs:
initial contract, multiview manifest, front/right/left/back artifact identities,
Review Request, Review Result, Reviewer Invocation Report, workflow, Plan.
PASS 검사 시 core validate_result/checked_invocation conventions와 L6 caller lineage 확인을 함께 적용한다.
Fresh prompt_id/result/manifest identities를 직접 연결한다.

Geometry 직전에 다시:
1. Review의 four artifacts가 frozen manifest의 정확한 path/hash/role/order와 일치.
2. 각 파일이 존재하며 bytes/hash/dimensions가 그대로.
3. source/result/request/invocation hashes와 성공 identity 일치.
4. Worker/Review 예산 및 nonterminal guard.
5. 필요한 generated image를 work/input/l6/<run_id>/<role>.png로 byte-for-byte staging.
   Existing LoadImage는 work/input만 resolve하므로 output path를 그대로 image field에 넣지 않는다.
   Exclusive file creation, original artifact ref 및 staged path/bytes/hash mapping 기록.
   staged hash/bytes가 reviewed original과 동일해야 하며 resize/re-encode/crop/rembg 없음.
   front는 현재 original input 상대 path를 그대로 사용한다.
6. Staged files도 제출 직전에 다시 hash 검증. 실패하면 effect 없이 중단한다.

| Role | LoadImage node | Image field | Vision node | Node10 socket / embedding index |
|---|---|---|---|---|
| front | 1 | hunyuan-official-demo-padded.png | 6 | front / 0 |
| right | 4 | l6/<run_id>/right.png | 9 | right / 3 |
| left | 2 | l6/<run_id>/left.png | 7 | left / 1 |
| back | 3 | l6/<run_id>/back.png | 8 | back / 2 |

Required model-side order: front,left,back,right.
Review order: front,right,left,back. 배열 index로 role을 추측하지 않는다.
Crop=none, node12 resolution1024, node15 octree128.
이 계약은 single-process sequential scope이며 distributed concurrency/locking 설계를 요구하지 않는다.

## 7. GLB / success semantics

Executor verify_glb 재사용:
actual output path exists, output namespace/prefix 일치, bytes≥20,
SHA-256, glTF magic, GLB version2, declared length==actual size.
SUCCESS Report의 task_id/output_node17/workflow/prompt_id/client_id 및 order/Plan/input identities와 연결한다.
No JSON/chunk/topology/semantic quality framework를 추가하지 않는다.

GEOMETRY_READY 정확한 의미:
Frontier actual PASS를 받은 exact four-view bytes가 actual Geometry Worker input으로 소비되어 structurally valid fresh GLB 생성.
M3는 original reviewed set→staged inputs→Plan→actual prompt_id→fresh GLB→execution summary 전체 lineage를 검증한다.
GEOMETRY_READY는 L6 final state이며 INTERNAL_ACCEPT/DELIVERED/user approval/final geometry quality PASS를 뜻하지 않는다.
User external feedback을 같은 run state에 기록하거나 terminal run을 다시 열지 않는다.

## 8. State / failure / effects

Scenario A 전용 최소 vocabulary:
SOURCE_READY, VIEWS_READY, MULTIVIEW_REVIEW_READY,
MULTIVIEW_REVIEWED, GEOMETRY_RUNNING, GEOMETRY_READY, ABORT, FAILED, UNRESOLVED.
Arbitrary graph/state engine 없음.
세 acquisition 중 진행은 stage receipts/execution refs에 기록하며 매 view마다 generic state를 추가하지 않는다.

| 상태/상황 | 의미 / 후속 |
|---|---|
| SOURCE_READY | initial immutable contract 이후 fixed acquisition 진행 |
| VIEWS_READY | 세 fresh SUCCESS 및 complete manifest |
| MULTIVIEW_REVIEW_READY | request 및 budget reservation 준비 |
| MULTIVIEW_REVIEWED | validated actual verdict 참조 |
| PASS | nonterminal geometry gate → GEOMETRY_RUNNING |
| GEOMETRY_READY | terminal=true; structurally valid fresh GLB |
| REVISE | terminal ABORT / MULTIVIEW_REVISE |
| HUMAN_REQUIRED | terminal ABORT / HUMAN_REQUIRED |
| known image execution failure | terminal FAILED / VIEW_STAGE, failed role/evidence |
| known geometry execution failure | terminal FAILED / GEOMETRY_STAGE |
| known Reviewer failure / invalid identity | terminal FAILED / REVIEW_STAGE, invocation evidence |
| submission/prompt identity uncertain, history timeout, Reviewer timeout | UNRESOLVED; further effects stop, automatic retry0 |

Missing runtime/auth/input before meaningful effect may be milestone BLOCKED rather than forced FAILED proof.
UNRESOLVED는 successful terminal actual proof가 아니다. comprehensive resume는 구현하지 않는다.
State failure 이유와 실제 subprocess/submission 시작 여부를 evidence로 분리한다.

terminal.json:
version, run_id, state, terminal=true, reason, timestamp,
initial contract/Work Orders/Execution Reports/manifest/Review/geometry refs(미발생이면 null),
actual final artifact 또는 null, final budgets.
Terminal 이후 state transition/Worker/Reviewer effect 없음.
Re-entry는 ALREADY_TERMINAL 또는 existing stage/reservation guard로 effect 없이 거절.
UNRESOLVED reservation이 남은 경우도 inspect/manual future decision 없이 재제출하지 않는다.

Effect ceilings declared before first effect:
worker budget4 (right1,left1,back1,geometry1); Reviewer1; Blender0; automatic retry0.
REVISE/HUMAN_REQUIRED이면 geometry 호출0, total Worker3 이하.
더 적은 actual calls도 기록하되 budget을 채우려고 호출하지 않는다.

Minimal duplicate guards:
run directory exclusive allocation; per-stage Work Order/task/output namespace;
exclusive Worker Report reservation; Reviewer reservation+result/report guard;
geometry namespace collision check; terminal guard.
Worker slot는 effect 전에 durable하게 예약하여 uncertain submission에도 재사용하지 않는다.
Reserved/consumed budget은 보수적인 상한이며 actual invocation count와 구분한다.
Limit/consumed/remaining invariant: consumed≤limit, remaining=limit-consumed≥0.
초기 contract는 immutable. Mutable current state/final record가 해당 hash를 참조한다.
DB/distributed lock/scheduler/global idempotency framework 추가 없음.

## 9. Top-level runner / M2 interface

Future file: src/scenario_a/l6_pipeline.py (M1에는 생성하지 않는다).
Minimum callable: run_pipeline(run_id, comfy_root, worker_timeout, review_timeout).
Same runner CLI may expose those parameters. Fixed asset paths/roles/default seeds are frozen above.
한 invocation이 모든 steps를 programmatically 연결한다:

validate source/assets/budget → exclusive run allocation → initial contract →
generate right → left → back → validate exact-role manifest →
prepare request → reserve Review → reviewer.review_once once →
validate actual verdict → if PASS create geometry Work Order / stage reviewed bytes →
reserve geometry → existing executor.run once → validate GLB → GEOMETRY_READY;
otherwise ABORT/FAILED/UNRESOLVED according to evidence.

동일 runner의 local/preflight validation은 effect-free이며 actual branch와 같은 mapping/Plan validators를 사용한다.
M2 tests는 mock/fixture policy verification이다. M3 actual proof 대체 금지.
사람이 각 phase JSON을 만들고 CLI를 차례로 호출하는 manual handoff는 L6 actual proof로 인정하지 않는다.

Direct reuse:
codex_to_comfy.validate_plan/run/png_dimensions/verify_glb;
result_review_adapter.validate_request/validate_result/review_once/checked_invocation;
existing hash/reference/atomic/exclusive persistence conventions.
Minimal Scenario A glue:
fixed Plan/order generation, report→artifact identity wrapping, aggregate manifest/report,
role/run lineage validators, staging, budgets/reservations, sequential gate, final evidence/usage.
Frozen src/core, c1–c5, schemas/tests/evidence/tag/release 수정 요구 없음.
Existing controller/geometry-review/Blender machinery wholesale migration 없음.

## 10. Usage / telemetry

usage.json minimum:
version=l6.0, run_id, workers list(stage,backend,model,invocations,execution_seconds),
frontier(provider,auth_mode,invocations,review_duration_seconds,
requested_model,requested_reasoning_effort,actual_model,actual_reasoning_effort,
input_tokens,cached_input_tokens,output_tokens,reasoning_tokens,reported_credits),
budgets(worker/reviewer limit/consumed/remaining), final_state.
Worker model filename은 executed graph 기준, duration은 actual timestamps/monotonic 측정 기준.
Actual invocations와 reservation consumption은 별도 값.
Effect가 실행되지 않은 stage는 invocations0, duration null.
Telemetry independently unavailable면 null 및 이유 기록. 추정치 금지.

기존 review_once는 model/effort override parameter가 없고 CLI args에 이를 명시하지 않는다.
Direct reuse 시 requested_model/requested_reasoning_effort는 explicit request 없음으로 null,
actual_model/actual_reasoning_effort는 independently 관측되지 않으면 null.
Task document에 model 이름을 쓴 것만으로 실제 process 요청했다고 주장하지 않는다.
Future 명시적 model 요구가 생기면 frozen Core를 조용히 수정하지 말고 별도 scope 판단.
Usage collector subsystem/Core dependency 없음.

## 11. M3 actual proof / stop

M3 success는 fresh run, three actual view invocations, four actual image attachments,
one validated actual Frontier PASS, one actual geometry invocation,
fresh valid GLB, exact identity lineage, budgets/duplicate no-effect 증거를 모두 요구한다.
Comfy runtime/API accepted alone, historical replay, synthetic control fixture만으로 VERIFIED 금지.
Actual REVISE/HUMAN_REQUIRED는 bounded policy 검증이나 Level6 successful geometry proof는 아니다.
No retry/budget extension으로 PASS를 만들어내지 않는다.

M1 stop: documents/manifest/static validation/branch commit/push/clean까지만.
M2/M3 실행은 별도 사용자 milestone 지시 이후.
Level7 제외: geometry diagnostic render/semantic Review, Blender, regeneration,
adaptive planning, revision iteration, final3D gate, texture/PBR/UV/seam.
F2B/recovery/concurrency/DB/generic DAG/benchmark/ScenarioB 제외.

## 12. Checkpoint 3 self-review

| # | 검토 | 결과 |
|---|---|---|
| 1 | discovered assets와 일치 | PASS: manifest hashes/nodes/paths 기반 |
| 2 | node/model/workflow 발명 없음 | PASS: four existing APIs and six actual model files |
| 3 | 불필요 abstraction 없음 | PASS: fixed sequential Scenario A glue |
| 4 | Level7 혼입 없음 | PASS: only pre-geometry Review; REVISE abort |
| 5 | Core 수정 암묵 요구 없음 | PASS: existing executor/reviewer APIs, caller validation |
| 6 | M2 구현에 구체적인가 | PASS: Plan fields/refs/roles/paths/mapping/entry/guards 확정 |
| 7 | M3 판정 명확한가 | PASS: actual PASS+fresh GLB lineage/budget required |
| 8 | Existing-first 준수 | PASS: static APIs/code/models/reports/artifacts audit |
| 9 | future generic framework 선설계 없음 | PASS: no DAG/DB/resume/DSL |

AGENT LOOP CORE V1.0.0 = FROZEN / UNCHANGED
L6-M1 ASSET / CONTRACT READY
L6-M2 PIPELINE IMPLEMENTATION = NOT STARTED
LEVEL 6 MULTI-STAGE SUPERVISED PIPELINE = NOT VERIFIED
LEVEL 7 CLOSED FEEDBACK PIPELINE = NOT STARTED
HYPOTHESIS BENCHMARK = NOT STARTED
