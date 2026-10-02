# Adaptive Skill / Workflow Orchestration 최종 보고

M0–M8 구현과 검증을 완료했다. M7 checkpoint에는 M7 코드·synthetic evidence만 포함했고, M8 준비물은 별도 보존한 뒤 M7 push/HEAD equality/clean gate를 통과한 후 재개했다. 현재 보강 코드의 focused/related **74/74**, full **326/326 PASS**다. 실제 Stone Lantern v3는 독립 Reviewer의 C01–C04 전부 MET, actual Frontier ACCEPT, **INTERNAL_ACCEPT=true → CLOSED**로 종료했다. GLB local handoff와 actual-success에 근거한 Skill validation 1건을 검증했다.

## A. Architecture implementation status

Frozen Work Specification은 한 Session의 불변 Goal authority이며, Frontier가 버전별 Skill/Workflow를 선택·계획·수정하고 Controller가 그 결정을 검증·실행한다. Workflow 전략 변경은 새 Production Run, 같은 전략의 지역 수정은 새 Attempt다. Artifact/Review/Decision은 identity, 파일 해시 및 Session/Workflow/Run/Attempt lineage로 연결된다. Reviewer는 기준을 평가하고, Frontier는 다음 행동을 결정하며, Controller는 budget·namespace·current acceptance 불변식을 적용한다. Core는 Scenario A를 import하지 않고 주입된 inference/execution adapter를 호출한다.

18개 module contract 구조 검사와 기존 public Session 메서드 6개 AST 호환 검사를 통과했다. 기존 정본 v1.2·M0–M6 architecture 및 역사적 실패를 유지했다. Direction/Design Philosophy 및 `D:\VSCODE-WorkSpace\Agents\workflow.md`의 적용 경계를 검토했고, 사용자 채택 Work Specification의 이번 범위에 따라 실행했다. Codex 개발 chat은 동일하다. 아래의 fresh **Core proof Session** 식별자는 새 Codex chat 생성이나 terminal Session 재개를 의미하지 않는다.

## B. Module-by-module status

| Module | 구현 및 검증 상태 |
|---|---|
| Specification Layer | 기존 Session freeze 재사용; 원래 Request/Reference, finalized criteria, envelope를 immutable binding |
| Session Controller | `core.adaptive_loop`; 한 frozen identity와 현재 trajectory 소유 |
| Frontier Supervisor | `core.frontier`; injected actual/synthetic inference와 observable invocation/decision binding |
| Skill Artifact Layer | `core.skill_artifact`; version/hash/VCS pin, CANDIDATE, guarded actual-success attestation |
| Skill Registry / Discovery | `core.skill_registry`; dependencies/capabilities 및 reviewed community copy |
| Workflow Planner | `core.workflow_artifact`와 Frontier; compact sequential proposal grammar/applicability 검증 |
| Workflow Artifact / Instance | immutable version/strategy hash, exact Skill refs, evidence-linked revision cause |
| Production Run Controller | strategy별 새 Run, 이전 Run/evidence 보존, stale authority 거부 |
| Attempt Controller | 같은 전략의 새 Attempt, pre-effect reservation, unresolved effect 중복 방지 |
| Artifact / Evidence Store | `core.adaptive_artifacts`; write-once metadata, bytes/hash/current lineage 검증 |
| Reviewer Layer | `core.artifact_review`; independent criterion outcomes/current Artifact binding |
| Diagnosis / Decision Layer | Frontier의 evidence-bound action; REVISE를 자동 종료/재시도 규칙으로 치환하지 않음 |
| Execution Adapter Layer | `scenario_a.adaptive_adapter`와 주입 interface; 실제 host에서 model-authored Blender 실행 |
| Acceptance / Terminal Layer | current full mandatory coverage, Frontier ACCEPT, terminal immutability |
| Delivery Boundary | 기존 SessionBoundary의 additive local handoff; human receipt 없이 검증 가능한 CLOSED |
| Event Logging | `core.event_logging`; canonical module events + hash-bound global index |
| Deadline / Resource Envelope | frozen limits, consumed/reserved slots, pre-effect gate |
| Model Lifecycle Manager | 명시적 DEFERRED; 자동 download/delete/cleanup 없음 |

상세 계약 정본은 repository `docs/adaptive/MODULE_CONTRACT_MAP.md`와 추가 contract 문서다. 개념 모듈은 작은 구현 파일을 공유하며 별도 generic framework로 확대하지 않았다.

## C. Regression status

| 검증 시점 | focused/related | full | 의미 |
|---|---:|---:|---|
| M7 promotion guard 보강 이전 | historical | 324/324 | historical evidence로만 보존 |
| M7 보강·격리 checkpoint | 72/72 (직접 11 + related 61) | 324/324 | M7 현재 코드 검증 완료 |
| M8 Frontier/Planner contract 보강 후 최종 코드 | 74/74 | 326/326 | 현재 source hash와 일치 |

최종 full은 1,203.328초, failures/errors/skips 모두 0이다. synthetic 검증의 network/production-process/repository-write tripwire는 모두 0이며 full의 허용된 local fixture subprocess는 4개다. 단위/회귀 통과는 actual semantic success의 근거로 사용하지 않는다. 별도의 actual v3 invocation·GLB import·Review·acceptance·handoff가 아래의 actual 근거다. source/test는 최종 full 이후 바뀌지 않았다.

실패 focused 로그와 prematurely started/interrupted preliminary full 로그, M7의 중간 실패/회귀 로그를 삭제하거나 덮어쓰지 않았다. 중단된 full은 PASS로 세지 않았다.

## D. Synthetic adaptive proof

M7 frozen identity `6ad047e428899ffb5e1dc13311ca3e56833ed15dbcccd6291fd4732af278f59d`와 같은 `synthetic-adaptive-proof` Session이 유지됐다. Workflow v1 → Run 1 → Reviewer REVISE(`opening=UNMET`) → Review를 원인으로 Frontier REVISE_WORKFLOW → Workflow v2 → 명시적 RESTART_PRODUCTION_RUN → Run 2의 새 Artifact/Review → current PASS/MET만으로 acceptance/local synthetic CLOSED를 증명했다.

old Artifact A/Review A 원래 bytes/hash를 보존했고, current Workflow v2/Run 2의 authority로 사용할 수 없음을 public lineage gate 및 controller 테스트로 확인했다. Final acceptance는 Artifact B/current Review만 포함한다. 110 proof files 불변, 72 distinct FileRefs, 27 순차 events를 재검증했다.

Skill은 CANDIDATE에 남으며 synthetic validation record는 0이다. ACTUAL로 이름만 바꾼 synthetic evidence, 실제 invocation refs 부재, current acceptance 부재, non-CLOSED attestation 및 forged VALIDATED 소비를 거부했다. synthetic fixture의 VCS pin은 실제 저장소 복구 증거가 아니다. 별도 actual diagnosis invocation이나 actual 전략 revision을 synthetic 결과에서 주장하지 않는다.

## E. Actual Stone Lantern Fresh Session

유일한 subject authority는 최초 요청 `레퍼런스 이미지에 있는 석등을 제작하라. 석등은 중앙의 사각형 구멍을 포함한 실루엣이 명확히 나와야 한다.`와 최초 PNG(467×539, 362,412 bytes, SHA-256 `9da5ed9e7f3490d058673122a7bd50b46635d4f0b5a36ca3199f0c1636cd17e5`)다. 과거 Stone Lantern Specification, generated views, GLB, Review를 새 Goal/criteria authority로 사용하지 않았다.

성공 Core Session: `actual-adaptive-stone-lantern-v3`; frozen Specification identity `43ae532cc4530e6a9f9813cd50746578663b39280711208d92e1eea1b7bf1d7f`. 최초 이미지를 actual intake/Worker/Reviewer에 전달했다. 독립 actual Reviewer가 현재 GLB fresh-import views/report에 대해 C01 silhouette, C02 real square aperture/deep cavity, C03 proportions/gray stone/excluded surroundings, C04 fresh-import geometry/materials 모두 MET로 판정했다.

fresh-import 측정은 **17 meshes, 17,230 polygons, bounds 약 2.057×2.057×2.0**다. 실제 Blender 5.2 headless subprocess는 build/export 1개와 fresh-import renderer 2개로 총 3개이며, Controller의 logical diagnostic episode는 1개다. 실제 ComfyUI generation은 0이다. endpoint readiness는 production 직전 재확인했고 API 200이었다. ComfyUI 자동 실행은 하지 않았다. 미응답 자체를 architecture failure로 판정하지 않았고 사용자 runtime dependency라는 경계를 유지했다.

## F. Frontier invocation / Decision Artifact lineage

actual v3에는 saved-account CLI model inference 6개가 있다: intake 1, Frontier 3, Worker code author 1, 독립 Reviewer 1. Frontier actions는 PLAN_WORKFLOW → CONTINUE → ACCEPT다. 세 decision request/result/invocation은 frozen identity와 current context, exact evidence refs에 바인딩된다. Worker는 별도 model 호출로 geometry code를 작성했고 Blender가 실제로 실행했다. Reviewer는 original reference와 current fresh-import images/report를 별도 호출에서 평가했다.

모든 invocation은 ACTUAL/SUCCESS, process exit 0, unexpected tool calls 0이며, request/result hashes·observed CLI thread ID·usage가 보존됐다. **실제 model/version identity는 출력에서 관찰되지 않아 null**이다. configuration 값으로 특정 model의 실행을 단정하지 않는다. CLI ephemeral inference ID는 observability evidence이며 새 사용자 소유 Codex 개발 chat 생성이 아니다. 비공개 reasoning/raw stream은 저장하지 않고 structured result 및 stream byte/hash 관측을 보존했다.

종료 후 read-only public-boundary audit는 79 distinct bound FileRefs, current Workflow/Artifact/Review와 19 monotonic events, actual-success validation, delivered bytes/hash를 검증했다. evidence 정본은 repository `docs/adaptive/M8_ACTUAL_VERIFICATION.json` 및 `actual-stone-lantern-v3/`다.

## G. Production Run / Attempt chronology

| Proof namespace | 실제 진행/terminal | Production 효과 |
|---|---|---|
| M7 synthetic | Workflow 1/Run 1 REVISE → Workflow 2/Run 2 accept | actual 효과 0; synthetic proof만 |
| actual v1 intake | governance/capability mismatch를 Session binding 전에 REJECTED_BEFORE_SESSION_BINDING으로 보존 | Run/Attempt/Worker/Review 0 |
| actual v2 | actual planning 1회 후 invalid underscore stage ID로 FAILED; never resumed | Run/Attempt/Worker/Review/Blender 0; acceptance/delivery/promotion 0 |
| actual v3 | Workflow 1 `construct-lantern` → run-001/attempt-001 → Review PASS → Frontier ACCEPT → CLOSED | Worker 1, Review 1, Blender subprocess 3, GLB export/local delivery |

v3는 첫 전략에서 성공했으며 **actual Workflow revision 0, Run restart 0**이다. budget은 Runs 3/Attempts 12/Worker 12/Reviewer 15/Frontier 18/diagnostics 24로 freeze됐고 각각 1/1/1/1/3/1만 소비했다. 재검토·추가 생성·repair·retry·delivery를 CLOSED Session 안에서 수행하지 않았다. historical proof failure는 성공으로 재해석하지 않았다.

## H. Skill/Workflow versions created or reused

community `ifBars/blender-agent-studio` commit `de138242e2d05a4f37e7af7343b7ba27ebeb717a`의 MIT License 및 8개 파일을 검토·해시 pin하여 local reviewed copy `skills/v1/blender-modeling-workflow/`를 만들었다. 외부 helper scripts를 실행하지 않았다. v1 intake에서 생성한 CANDIDATE package를 v2/v3에서 exact ref로 재사용했으며 기존 package를 덮어쓰지 않았다. 해당 guidance는 전략 자료이고 criteria authority가 아니다.

Skill version v1/content hash `25549eb5b5a12732ef298f7eac47e2de7b9848f32af530cef685100864527070`; metadata hash `02b08f775e074a3df34778e2d6b7000f0c1fe3cfc305850721ddb0cf79d326e3`; actual used VCS revision `a7020ec1cb3c98cdc5d167fa9a512087ad6af9d0`. 각 package file을 해당 revision에서 read-only 복구하여 현재 bytes와 비교했다.

actual Workflow `stone-lantern-reference` version 1/file hash `d1f1a114ad80266e266b71f144893022ea7e9bad0ac691685306ab6858e818de`; strategy hash `2919ba33c484e685a4d38d8cfef5e2c3736494b022b9712f25a30056fb279dce`. 단일 construct-lantern stage가 frozen C01–C04 전체와 Blender 실행을 바인딩한다.

USER_WORKFLOW_REVIEW_REQUESTED_NON_BLOCKING: Skill/Workflow 내용은 아래 복사본에서 검토할 수 있다. 변경 요청은 가능하며, 이번 실행은 승인 대기 없이 완료됐다. CLOSED 결과에 대한 새 feedback은 기존 trajectory를 변경하지 않는다.

## I. CANDIDATE → VALIDATED promotions

`skill-validation-blender-modeling-workflow.json` 한 건이 v3의 실제 invocation/current acceptance/CLOSED lineage에 바인딩된다. 생성 및 소비 양쪽 attestation gate를 재검증해 **effective VALIDATED**를 확인했다. immutable package `core.json`의 CANDIDATE bytes는 유지한다. 이 promotion은 관찰된 successful actual use의 증거이며 모든 future task/hidden geometry/model에 대한 일반적 성능 보증이 아니다. M7 synthetic/실패 v2 promotion은 0이다.

## J. Final Artifact identity/path/hash

Final Artifact metadata identity `attempt-001-construct-lantern`, hash `5fba7e15cc8f7411f79e43b0a17bedb28c1e768fbcd0f5b5da7aa4f36e102f56`; accepted source는 repository `docs/adaptive/actual-stone-lantern-v3/session/production_runs/run-001/attempts/attempt-001/execution-construct-lantern/asset.glb`다.

Delivered GLB `outputs/actual-adaptive-stone-lantern-v3/stone-lantern.glb`: **372,516 bytes**, SHA-256 **`0f1136bc8045f2114a723a6c7a75437a966b93102faced4d29ad6f354369ff97`**. Source/exported bytes/hash가 동일하다. `.blend`, generated source, original reference, seven diagnostic images도 user outputs에 보존했다. 전달 preview는 current GLB import에서 생성한 이미지다.

## K. INTERNAL_ACCEPT / Session terminal / delivery boundary

Current four mandatory criteria MET + current Review + actual Frontier ACCEPT로 INTERNAL_ACCEPT=true를 기록했다. exact accepted package 및 local handoff record를 검증해 terminal CLOSED다. boundary는 **LOCAL_DELIVERABLE_EXPORT**, observation은 **LOCAL_FILES_VERIFIED_HUMAN_RECEIPT_NOT_OBSERVED**다. 사용자 수령/최종 미적 평가, 단일 이미지에서 관찰할 수 없는 숨은 면의 완전한 일치는 증명하지 않는다. local attestation은 tamper-proof OS/remote service attestation이 아니다.

## L. Git branch/commits/live remote/clean state

Branch `feature/adaptive-skill-orchestration`, origin `https://github.com/1-3127/Agent-Loop-Core.git`. Initial baseline `001db7e1377c2b291632d2a80746860cb15d7dcd`.

| Checkpoint | Commit |
|---|---|
| M0 | 7f65ae214f9c67ff30705735da8609231e5b632c |
| M1 | 66f7a1f4072f96bb91d469c679196d8e3f05cc71 |
| M2 | e6335aa4fc8100e524d215d88c665d46d68401f8 |
| M3 | 2e970390157e4d9ad88981c89e22f2b42107a0b7 |
| M4 | efc8df7ccc8e0e16f2a403b6daabad2b0396621a |
| M5 | 0d3d088abe1337c118e4cec51d2146d650631621 |
| M6 | 0b173baaa96f235e1b5ebb473aad7b0c72c20660 |
| M7 isolated | 79ecadfe617efce9a685831d2498b38ea6882cf2 |
| M8 pre-loop intake correction/reviewed copy | 5c05441d6d89c4c55cc7187c22d17344d296c21b |
| M8 v2 frozen intake | bb0b6222e4fb8264d1aa5ec18999faa72cec4892 |
| M8 Frontier/Planner correction + 326 tests + failed v2 | 1b4e8be4bcf1527dcff4ac3955e69af5325d6b87 |
| M8 v3 frozen intake/host evidence binding | a7020ec1cb3c98cdc5d167fa9a512087ad6af9d0 |

각 checkpoint는 normal push/HEAD equality/clean gate로 공개했다. 최종 actual evidence와 이 보고서의 containing commit을 normal push한 후 local/tracking/live HEAD equality, clean tree, 초기 protected refs 45개, historical bytes 및 M7 proof를 최종 확인한다. repository의 이 버전은 publication 전에 작성했으므로 최종 SHA를 미리 주장하지 않는다. user-facing report 마지막 Publication verification에 실측값을 기록한다. reset/rebase/amend/force push/historical evidence 삭제는 없다.

## M. Deferred items

model download/delete/cache cleanup/lifecycle manager, generic DAG/DSL, recovery/resume service, unrelated I-01/I-02 refactor는 계획대로 deferred다. optional community MCP/benchmark helper 실행 및 ComfyUI 생성 경로의 actual quality proof는 이번에 수행하지 않았다. actual Workflow revision/여러 Run의 semantic 수렴은 이번 actual 성공 사례에서 관찰되지 않았고, M7 synthetic contract proof로만 증명됐다.

## N. Remaining known defects

이번 필수 scope에서 미해결 blocking contract defect는 관찰되지 않았다. 알려진 한계는 단일 reference에 의한 hidden geometry 추정, exact actual model identity 미관측, local delivery와 human receipt의 경계, local evidence가 tamper-proof하지 않다는 점이다. 모든 capability/subject/runtime에 대한 일반화는 미증명이다.

발견한 결함과 한정 수정을 기록한다. v1 intake의 execution governance/capability 불일치는 Core binding 전에 중단하고 host context를 한정 보충했다. v2 model proposal이 기존 Planner identifier/applicability 계약을 충족하지 못해 해당 Session을 FAILED로 봉인하고 Frontier request에 기존 exact grammar/coverage를 공개했다. guard를 약화하거나 불법 proposal을 자동 수정하지 않았고 contract tests 2개를 추가했다. v3 freeze 후·binding 전에 fresh-import polygon evidence 부족을 발견하여 host의 추가 renderer/report를 hash-bound 방식으로 보충했다. frozen Goal/criteria 변경 및 old artifact 재사용은 없다. 수정 후 74/326 PASS와 actual v3의 79 refs/current acceptance/CLOSED를 확인했다. 중간 test fixture 불일치와 너무 이른 full 시작도 실패/중단 로그로 보존했다.

## Deliverables

- [GLB](C:/Users/Worker/Documents/Codex/2026-10-02/agent-loop-adaptive-skill-orchestration-work/outputs/actual-adaptive-stone-lantern-v3/stone-lantern.glb)
- [Blender source](C:/Users/Worker/Documents/Codex/2026-10-02/agent-loop-adaptive-skill-orchestration-work/outputs/actual-adaptive-stone-lantern-v3/asset.blend)
- [Original reference](C:/Users/Worker/Documents/Codex/2026-10-02/agent-loop-adaptive-skill-orchestration-work/outputs/actual-adaptive-stone-lantern-v3/original-reference.png)
- [Current GLB preview](C:/Users/Worker/Documents/Codex/2026-10-02/agent-loop-adaptive-skill-orchestration-work/outputs/actual-adaptive-stone-lantern-v3/perspective-stone.png)
- [Aperture detail](C:/Users/Worker/Documents/Codex/2026-10-02/agent-loop-adaptive-skill-orchestration-work/outputs/actual-adaptive-stone-lantern-v3/aperture-detail.png)
- [Workflow v1](C:/Users/Worker/Documents/Codex/2026-10-02/agent-loop-adaptive-skill-orchestration-work/outputs/WORKFLOW_v1.json)
- [Skill guidance v1](C:/Users/Worker/Documents/Codex/2026-10-02/agent-loop-adaptive-skill-orchestration-work/outputs/SKILL_blender-modeling-workflow_v1.md)
- [Audit evidence](C:/Users/Worker/Documents/Codex/2026-10-02/agent-loop-adaptive-skill-orchestration-work/outputs/FINAL_EVIDENCE.json)
