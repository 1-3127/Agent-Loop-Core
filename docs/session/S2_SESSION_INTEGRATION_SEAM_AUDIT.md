# S2 Session Integration Seam Audit

## Executive Summary

**S2 SESSION INTEGRATION SEAM AUDIT = COMPLETE**. 이 문서는 source inspection에 근거한 통합 지점 감사와 S3 제안이다. Production 구현이나 actual Session E2E proof가 아니다.

**Recommended Minimal Seam: 새 Session boundary가 immutable Specification을 받고, 고정 Scenario A adapter를 통해 기존 L6/L7 callable을 연결한다.** Frozen Core source/schema와 C1–C5 proof 경로는 변경할 필요가 없다. 다만 wrapper만 추가하고 기존 criteria/역사적 source를 그대로 두면 S1을 만족하지 못한다. opt-in Scenario binding 검증과 L7 source parameterization이 최소 변경으로 필요하다.

핵심 사실:

- 현재 단일 global Loop entry는 없다. C1–C5는 개별 proof entry, L6는 `run_pipeline`, L7은 `run_bridge` 및 `run_feedback`이다.
- Worker/Review/Artifact/invocation hash lineage는 존재한다. User Request → frozen Work Specification → acceptance criteria authority 연결은 없다.
- C4의 local `DELIVERED` record는 사용자 전송 함수가 아니다. L7의 `INTERNAL_ACCEPT`도 `delivered=false`다. 실제 제출은 external Frontier interaction의 관측 가능한 사건으로 완료해야 한다.
- Session-level ambiguity는 현재 typed signal이 없다. `HUMAN_REQUIRED`를 일괄 ambiguity로 변환하면 기술/증거 불확실성과 User intent 모호성을 혼동한다.
- S3의 가장 작은 목표는 이 연결의 local validation이며 expensive effects0이다. geometry 개선, 새 backend, Session CLI/DB/framework와 실제 Delivery transport 구축은 이 제안에 포함하지 않는다.

S1 정본: [Contract](S1_SESSION_CONTRACT_v0.md), [Work Specification Template](S1_WORK_SPECIFICATION_TEMPLATE_v0.md), [Handoff Template](S1_SESSION_HANDOFF_TEMPLATE_v0.md). 최상위 방향: [Direction Gate](../Agent-Loop_Direction_Gate_v1.md), [Core Freeze](../../CORE_V1_FREEZE.md).

표기의 의미: **Observed**는 현재 source/record에서 확인한 사실, **[추론]**은 그 사실에 대한 architecture 판단, **Proposed**는 아직 구현하지 않은 S3 계약이다. 기존 proof의 판정은 재판정하지 않는다.

## Verified Baseline

| 항목 | 확인 결과 |
|---|---|
| Repository | `D:\VSCODE-WorkSpace\Others\Agent-Loop-Core` |
| Remote | `https://github.com/1-3127/Agent-Loop-Core.git` |
| 시작 branch | `session-contract-s1` |
| 시작 HEAD / origin/session-contract-s1 / live remote | `ba04e8c127c92163f686cd07695ae3e16d8c11cc` |
| Parent / S1 source baseline | `1da2bef094d2cc3f4bd70bbc266d99dc955460bb` |
| main / origin/main / tag dereference | `7eee393801f4d8c14278b43ebcbaabaec7ccc9df` |
| core-v1.0.0 annotated tag object | `8b962c5d94828af852d020237554606c305ef01e` |
| L6 local / tracking / live remote | `840b138cc023c623108c44c3944948b065300f99` |
| L7 local / tracking / live remote | `1da2bef094d2cc3f4bd70bbc266d99dc955460bb` |
| L7-M3 history | `d4de473fc247c4ae40699d794795ee91b35e5db3`가 HEAD의 ancestor임을 `git merge-base --is-ancestor` exit0으로 확인 |
| 시작 working tree | clean |
| S1 commit diff | 아래3개 문서의 신규 추가만 존재 |
| S2 branch | exact S1 HEAD에서 `session-integration-s2` 신규 생성; 로컬/remote 동일 이름 branch가 없음을 먼저 확인 |

S1 exact files:

- `docs/session/S1_SESSION_CONTRACT_v0.md`
- `docs/session/S1_WORK_SPECIFICATION_TEMPLATE_v0.md`
- `docs/session/S1_SESSION_HANDOFF_TEMPLATE_v0.md`

적용 지침: workspace root `AGENTS.md`, `Agents/workflow.md`, `Others/AGENTS.md`, repository `AGENTS.md`. repository 내부에 더 가까운 AGENTS는 발견되지 않았다. 검토는 read-only이고 허용된 신규 tracked 파일은 이 문서 하나다.

## Existing Execution Topology

### Core primitives / effect boundary

| Source / callable | 실제 역할 | 소유하지 않는 책임 |
|---|---|---|
| [worker_port.execute](../../src/core/worker_port.py#L15) | injected adapter를1회 호출하고 공통 Work Order/Result 및 artifact path/bytes/hash 검증 | Session/dialogue/budget scheduler/Delivery |
| [result_review_adapter.review_once](../../src/core/result_review_adapter.py#L120) | Request refs 검증 → exclusive Result/Invocation reservation → auth 확인 → instruction+Request JSON+실제 image attachment로 Codex subprocess1회 → Result validation | User Request 해석, criterion authority, correction dispatch, 사용자 제출 |
| [checked_invocation](../../src/core/result_review_adapter.py#L98) | Request/Result/Invocation identity/hash/status 연결 검사 | Specification semantics, 실제 User Delivery |
| [reviewer_auth.auth_mode](../../src/core/reviewer_auth.py#L7) | API-key 환경 구분 및 Codex login status probe | User 의도 판정/Session |
| [codex_to_comfy.run](../../src/scenario_a/codex_to_comfy.py#L255) | validated Plan → local /system_stats → report 예약 → /prompt → history → output 검증 | User Goal/Specification/Review |
| [l7_blender_diagnostic.render](../../src/scenario_a/l7_blender_diagnostic.py#L27) | exact GLB와 script/config 검증, 기존 Blender 진단4view 및 manifest 생성 | Specification 판단, correction, Delivery |

Observed: [Plan validator](../../src/scenario_a/codex_to_comfy.py#L87)는 exact5필드만 허용한다. WorkerPort는 exact `ORDER_FIELDS/RESULT_FIELDS`, Review adapter는 version별 exact Request/Result fields를 검사한다. S1 metadata를 그 top-level에 임의 추가하면 계약이 거절된다.

### C1–C5

| 경로 / entry | 실제 연결 | state / evidence ownership |
|---|---|---|
| C1 [c1_delegate.run](../../src/scenario_a/c1_delegate.py#L93), CLI main | 외부에서 준비한 Work Order/Plan → preflight → Comfy executor → fresh PNG → Execution Report/Usage | Work Order가 report/execution/usage 경로를 지정. callable은 문서 작성/명세 dialogue를 수행하지 않음 |
| C2 [c2_review.main](../../src/scenario_a/c2_review.py#L80) | 기존 C1 execution → `validate_c1_lineage` → Core review_once | `reviewer_requests`, `reviewer_results`, `invocation_reports`의 외부 지정 경로; correction/terminal 없음 |
| C3 [c3_review.main](../../src/scenario_a/c3_review.py#L34), [c3_revision.run](../../src/scenario_a/c3_revision.py#L98) | 고정 initial Review → 검증된 REVISE/action → 외부 준비 revision Work Order → 실제 Comfy → Artifact B | Review/initial artifact/Plan/hash 연결은 검사. review와 revision은 별도 entry이며 반복 supervisor 구현이 아님 |
| C4 [run_worker](../../src/scenario_a/c4_bounded.py#L67) / [run_review](../../src/scenario_a/c4_bounded.py#L151) / [resolve_terminal](../../src/scenario_a/c4_bounded.py#L177) | predeclared1Worker/1Reviewer → C1 delegation → C2 criteria Review → terminal policy | `runs/<run_id>_worker_state.json`, `_review_reservation.json`, `_terminal.json`; terminal re-entry 차단 |
| C5 [c5_worker_swap.run](../../src/scenario_a/c5_worker_swap.py#L37) | 동일 WorkerPort → Comfy adapter / deterministic test Worker → Result/proof | `work_orders/<proof_id>-*.json`, `runs/*_worker_result.json`, `*_c5_boundary.json`, usage. semantic Review0. production Session 실행기로 사용하지 않음 |

C5의 [ComfyWorkerAdapter.__call__](../../src/scenario_a/comfy_worker_adapter.py#L11)은 inner C1 order ref만 받는다. 임의 Session payload를 수용하는 adapter가 아니다. C1/C3/C4/L6/L7이 모두 WorkerPort로 실행된다는 주장은 현재 source와 다르다.

### L6

[run_pipeline](../../src/scenario_a/l6_pipeline.py#L576) / CLI [main](../../src/scenario_a/l6_pipeline.py#L634):

`preflight → initial/state → right/left/back publish_order/run_worker → multiview_manifest → prepare_review/run_review/checked_review → PASS → exact byte staging → geometry Work Order/execution → finish(GEOMETRY_READY)`.

REVISE/HUMAN_REQUIRED는 ABORT; known failure는 FAILED; uncertain identity/submission은 UNRESOLVED/no automatic retry다. default callable/CLI는 preflight이고 explicit execute만 effects를 허용한다.

소유 경로: `runs/l6/<run_id>/` 아래 initial/state, stage별 plan/work_order/reservation/worker_report/execution, multiview records, Review instructions/request/reservation/result/invocation, staging, usage, terminal. [publish_order](../../src/scenario_a/l6_pipeline.py#L196)와 [finish](../../src/scenario_a/l6_pipeline.py#L525)가 이를 생성한다. terminal GEOMETRY_READY는 fresh GLB structural success이며 final geometry semantic PASS나 Delivery가 아니다.

### L7

[run_bridge](../../src/scenario_a/l7_geometry_review.py#L366):

`validate_l6 → initial/state → render_request → Blender renderer → 4diagnostics → 8-image Review → GEOMETRY_REVIEWED terminal`.

[validate_l6](../../src/scenario_a/l7_geometry_review.py#L38)은 module constants의 특정 L6 run, terminal SHA, GLB SHA/bytes, 네 reference hash에 고정되어 있다. dispatch0이며 PASS도 즉시 사용자 제출이 아니다.

[run_feedback](../../src/scenario_a/l7_feedback_controller.py#L587):

`validate_source/preflight → initial → source verdict → REVISE/action → revision reservation → selected view(optional) → current multiview Review(optional) → geometry → render → geometry Review → INTERNAL_ACCEPT / ABORT / FAILED / UNRESOLVED`.

[revised_plan](../../src/scenario_a/l7_feedback_controller.py#L234)은 seed+1과 fresh namespace/input만 변경한다. source_review_run 인자는 존재하지만 [validate_source](../../src/scenario_a/l7_feedback_controller.py#L42)는 bridge의 고정 L6 validator를 호출한다. 따라서 argument 하나만 바꾸어 fresh L6를 연결할 수는 없다.

소유 경로: `runs/l7/<run_id>/` 아래 bridge 또는 correction별 initial/state/reservations/render/Review/usage/terminal. correction controller [finish](../../src/scenario_a/l7_feedback_controller.py#L533)는 INTERNAL_ACCEPT도 terminal로 저장하고 `delivered=false`를 기록한다. 이 terminal은 local execution 완료이며 S1 actual Delivery의 증거가 아니다.

### Historical evidence / tests의 범위

현재 읽은 기존 records:

- [C4 terminal](../../runs/m4-c4-reg-20260930-122819-6f5c4427_terminal.json): DELIVERED, internal_accept=true, delivery_channel=final_response.
- [L6 terminal](../../runs/l6/l6-m3-20260930-164920-8109160a/terminal.json): GEOMETRY_READY.
- [L7-M1 terminal](../../runs/l7/l7-m1-20260930-184618-3703fee4/terminal.json): GEOMETRY_REVIEWED, dispatch0.
- [L7-M3 terminal](../../runs/l7/l7-m3-20260930-205145-b6025e96/terminal.json): ABORT/REVISION_BUDGET_EXHAUSTED, delivered=false.

Read-only test inspection: [C4 branch/re-entry](../../tests/test_c4_bounded.py#L20), [L6 PASS/ABORT](../../tests/test_l6_pipeline.py#L195), [L6 terminal guard](../../tests/test_l6_pipeline.py#L385), [bridge PASS/no-dispatch](../../tests/test_l7_geometry_review.py#L165), [controller correction PASS fixture](../../tests/test_l7_feedback_controller.py#L123), [controller action policy](../../tests/test_l7_feedback_controller.py#L409), [WorkerPort fixture](../../tests/test_worker_port.py#L15). 이 테스트는 fixture/historical 검증이며 S2 actual effect 또는 Session/Spec binding proof가 아니다. S2에서는 실행하지 않았다.

## S1-to-Implementation Mapping

Compatibility는 production 연결 기준이다. S1 문서에 정의만 있는 항목은 implementation EXISTS로 세지 않는다. 모든 “migration”은 Proposed이며 이번 S2에서 수행하지 않는다.

| S1 Concept | Current Equivalent | Current Source | Compatibility | Missing Link | Migration Needed | Core Modification Required? |
|---|---|---|---|---|---|---|
| User Request | 고정 requested_task / 외부 milestone 입력 | c1_delegate.preflight, l6.publish_order | PARTIAL | 원 Request identity/Goal 계약 | outer Request→Spec ref | NO |
| Session ID | 없음 | src 전체 검색 | ABSENT | session_id | outer identity | NO |
| Specification Dialogue | 현재 User↔Codex interaction, runner에는 없음 | S1 문서, runner signatures | ABSENT | dialogue의 최종 확정 결과 | external Frontier가 새 Spec 작성/Ready 제출 | NO |
| Work Specification | Work Order/initial/asset manifest만 존재 | l6.publish_order/run_pipeline | PARTIAL | User 업무 계약과 runtime 계약 구분 | immutable Spec ref | NO |
| Specification version | execution schema/version만 존재 | c1/c4/l6 initial | ABSENT | 업무 명세 version | session binding | NO |
| Specification freeze | initial/Plan/hash 및 exclusive write | l6.write_once/guard | PARTIAL | 업무 criteria freeze | Spec snapshot/hash 고정 | NO |
| Reference authority | source front 고정 권위, image roles | l7.prepare_review, c2.validate_c1_lineage | PARTIAL | 기능별 보존/해석 authority | Spec References→Review/Plan binding | NO |
| Must-Have | scenario 고정 품질 기준 | c2.CRITERIA, l7.prepare_review | PARTIAL | User authority와 요구 연결 | Spec MH/criterion IDs | NO |
| Acceptance Criteria | 고정 strings/instructions | c2.CRITERIA, l6.prepare_review, l7.prepare_review | PARTIAL | Spec→criteria 구조/hash lineage | opt-in instruction compiler+validator | NO |
| Interpretation Envelope | Plan allowlist/고정 scenario policy | codex_to_comfy.validate_plan, controller.revised_plan | PARTIAL | 사용자 허용 해석 범위 | Spec envelope과 supported capability 교차검사 | NO |
| Loop entry | milestone callable/runner | c1–c5, l6.run_pipeline, bridge.run_bridge, controller.run_feedback | EXISTS | Session-bound 단일 진입 | fixed Scenario adapter | NO |
| run_id | execution namespace | 모든 runners | EXISTS | session↔logical Loop↔stage 연결 | 새 sidecar lineage; 기존 ID 보존 | NO |
| Work Order | 요청/Plan/input/report refs | c1/l6/controller orders | EXISTS | 어느 Spec Goal/criteria를 위한 것인가 | order_binding ref | NO |
| Worker | direct Comfy / C5 WorkerPort | codex_to_comfy.run, worker_port.execute | EXISTS | pre-effect Spec gate | Scenario caller 검증; executor 변경0 | NO |
| Reviewer | actual attachments, Request/Result/invocation | result_review_adapter.review_once | EXISTS | criterion authority 검증 | opaque context+bound instructions+caller gate | NO |
| REVISE | blocker/action vocab | validate_result, bridge.validate_action | EXISTS | blocker가 허용된 criterion인지 | bound result authority gate | NO |
| Correction | C3 revision / L7 seed-only policy | c3_revision.run, controller.run_feedback | EXISTS | current Spec와 correction 목적 연결 | opt-in binding 전달; policy 개선 제외 | NO |
| INTERNAL_ACCEPT | C4 policy / L7 PASS branch | c4.terminal_policy, controller.run_feedback | PARTIAL | final artifact+Spec+criterion evidence | Session-bound accept evidence | NO |
| DELIVERED | local C4 record의 선언 | c4.resolve_terminal | CONFLICTING | standalone record는 actual submission을 관측하지 않음 | 새 Session에서는 actual receipt 후 close; 역사 record 불변 | NO |
| Session Close | Run terminal만 존재 | l6/bridge/controller.finish | ABSENT | 업무 lifecycle 종료 | outer close record | NO |
| BLOCKED_SPECIFICATION_AMBIGUITY | HUMAN_REQUIRED 또는 일반 errors | bridge instructions, controller verdict branches | ABSENT | 의도 모호성 typed evidence/종료 | typed outcome + 기존 ABORT reason | NO |
| User Evaluation | Direction Gate interaction contract | Direction Gate §2.3, AGENTS | PARTIAL | production 외부 verdict 참조 | 외부 feedback 기록; Core state 변경0 | NO |
| Feedback | 내부 REVISE/action | c3_revision/controller | PARTIAL | 외부 수정 요구와 내부 correction 구분 | 새 Request/Session lineage | NO |
| New Session | 새 run은 가능 | run namespaces | ABSENT | dialogue/Spec/fresh-context 경계 | fresh outer startup | NO |
| Durable Knowledge | durable artifacts/results/reports | runs, docs/l7/R1 | PARTIAL | 선택/증거 성격/관측 시점 | typed selected handoff | NO |
| Handoff | S1 template만 존재 | S1 Handoff Template | ABSENT | startup loader/interface | bounded explicit selection | NO |
| Fresh-context reset | Reviewer subprocess는 ephemeral | result_review_adapter.review_once | PARTIAL | outer planning context refresh | external fresh context + allowlisted startup content | NO |

DELIVERED의 CONFLICTING 판정은 **현재 local record만으로 S1 submission을 완료했다고 간주하는 통합 방식**에 대한 것이다. 기존 C4 technical proof나 당시 external final response를 무효화하는 판정이 아니다. 다른 naming gap도 historical records의 오류로 단정하지 않는다.

## Frozen Core Boundary Assessment

**[추론] Frozen Core 수정은 필요하지 않다.**

근거:

1. Core는 adapter execution 및 evidence-bound semantic Review primitive다. Session 업무 lifecycle을 소유하지 않는다.
2. Review Request `context`는 nonempty dict까지만 Core가 검사한다([validate_request](../../src/core/result_review_adapter.py#L41)). Scenario caller가 안쪽 binding을 검증할 수 있다.
3. Core는 instruction ref hash를 검사하고 그 내용과 Request JSON을 prompt로 전달한다. bound instructions를 Scenario에서 만들면 Core 변경 없이 spec criteria를 전달할 수 있다.
4. Result는 exact schema이므로 새 top-level criterion field를 넣을 수 없다. 기존 string evidence에 criterion ID 표기를 적용하고 별도 caller binding record로 검사할 수 있다.
5. Run-level ABORT 및 reason 문자열이 이미 있다. Session-level ambiguity를 별도 typed outcome으로 올리고 기존 ABORT reason에 연결할 수 있다.

Session wrapper만으로 기존 monolithic callable 내부의 instruction/correction/effect를 통제할 수는 없다. 이를 위한 Scenario opt-in hook은 필요하다. Core 변경의 exact blocker는 확인되지 않았다.

보존해야 할 invariants: budget predeclaration/reservation, duplicate expensive call 차단, raw Request/Result/Invocation/Artifact identity/hash, terminal 후 effect0, uncertain lifecycle에서 blind retry0. C1–C5/common schema/WorkerPort를 Session 지원 명목으로 일반화하지 않는다.

## Specification-to-Worker Binding

**Observed:** current Work Order → Plan → Report → Execution → Artifact lineage는 존재한다. `requested_task`는 고정 scenario 문자열이며 User Goal/Spec identity가 없다. Plan exact fields 때문에 Plan에 session_id/spec hash를 추가할 수 없다.

**Proposed minimum binding:**

- immutable `SpecificationRef`: session_id, specification_version, specification_path, specification_sha256.
- `SessionRunBinding`: SpecificationRef, logical loop_run_id, 고정 child run/stage map, source/reference identity, supported deliverable/interpretation 범위, 명시된 aggregate budget.
- 각 Work Order의 `order_binding.json` equivalent sidecar: SpecificationRef, loop/child/stage/work_order_id, Work Order path/hash, Plan path/hash, 해당 Goal/Must-Have/criterion IDs 및 입력 refs.
- effect 전 Scenario gate가 Spec hash/readiness/capability, Work Order/Plan hash, actual source bytes와 허용 envelope를 확인한다.
- Execution 이후 wrapper linkage는 기존 Report/Execution/Artifact refs를 참조한다. 기존 executor Report schema 변경0, historical record rewrite0.
- L6/L7 opt-in initial에는 binding ref를 넣고, 신규 Work Order에는 sidecar ref를 연결한다. legacy mode는 기존 구조를 유지한다. C1/C3/C4 strict order를 이 방식으로 개조하지 않는다.

Lineage: Session → frozen Specification → SessionRunBinding → child run initial → Work Order binding → Work Order → Plan → actual Execution/Artifact → Review binding → Loop outcome → Delivery Package/receipt.

S3가 지원하는 것은 기존 Scenario A asset/workflow/기술 policy 범위다. Goal이 그 capability를 벗어나면 `SPECIFICATION_READY=true`여도 effect 전에 capability blocker로 중단한다. 명세를 낮추거나 arbitrary Goal→workflow generator를 만들지 않는다.

## Specification-to-Reviewer Binding

### 현재 criteria의 원천

| 단계 | criteria 위치 / authority | 현재 검증 |
|---|---|---|
| C2/C4 right-view | [c2 CRITERIA](../../src/scenario_a/c2_review.py#L13); exact context equality | C1 task/artifact lineage 및 criteria 문자열 동일성. Spec authority 아님 |
| C3 initial | [c3 CRITERIA](../../src/scenario_a/c3_review.py#L12), 고정 prompt/seed | source penguin/sign/scale 기준과 challenge config 검사. User Spec version 없음 |
| L6 multiview | [prepare_review instruction](../../src/scenario_a/l6_pipeline.py#L370) | role/manifest/order/report/hash. same-subject/direction/downstream blockers는 code에서 생성 |
| L7 geometry | [bridge prepare_review](../../src/scenario_a/l7_geometry_review.py#L240) | fixed eight roles, front authority, silhouette/proportion/parts/distortion 등 code instruction |
| L7 correction geometry | [controller prepare_review](../../src/scenario_a/l7_feedback_controller.py#L455) | historical source instruction을 copy/문구 치환. 새 CURRENT images와 연결하지만 업무 Spec 연결은 없음 |
| L7 correction multiview | 같은 controller prepare_review의 else branch | 고정 strings; [validate_request](../../src/scenario_a/l7_feedback_controller.py#L482)는 exact context를 강제 |

현재 cryptographic chain은 **어떤 instruction bytes와 artifact를 검수했는가**를 추적한다. **왜 그 criteria가 User의 Must-Have인가**는 추적하지 못한다. [Result schema](../../result_review_schema.json)는 blocker/observation 문자열과 action을 받으며 criterion ID/authority 필드는 없다.

### Proposed minimum criterion binding

1. Stage별 applicable acceptance criterion IDs를 immutable Spec에서 선택한다. criterion의 condition, blocking_when_unmet, User/Reference authority, 관련 artifact 역할을 binding에 포함한다.
2. Scenario instruction은 **Spec에서 나온 criteria만** 품질 blocker로 사용한다. format/identity/role/camera 등 기술적 검증 조건은 품질 요구와 구분한다. bound mode에서 기존 hardcoded quality prose를 단순 append하여 여전히 숨은 Must-Have로 남기지 않는다.
3. Review Request의 기존 context 안에 SpecificationRef와 `review_binding` ref를 둔다. Core는 그 내부 ref를 자동 검증하지 않으므로 Scenario validator가 직접 current hash/IDs/compiled instruction equality를 검사해야 한다.
4. `review_binding.json` equivalent sidecar는 Spec ref, child run/stage, criterion IDs, actual artifact refs, instruction path/hash를 담는다. Request hash → Invocation request_sha256 → raw Result hash → checked binding evidence까지 연결한다.
5. Result0.3 top-level schema는 유지한다. 기존 blocking_issues/observations 문자열에 예컨대 `[AC1] ...`를 요구하고, bound Scenario validator는 coverage/ID/authority를 검사한다. BLOCKER는 해당 stage의 blocking criterion이어야 한다. Should-Have/unknown ID/non-goal은 blocking authority를 얻지 못한다.
6. unsupported blocker가 나오면 raw REVISE를 보존하고 correction/INTERNAL_ACCEPT/Delivery를 차단한다. `REVIEW_CONTRACT_VIOLATION / UNSUPPORTED_ACCEPTANCE_CRITERION`으로 제한 종료한다. 임의로 raw verdict를 PASS로 바꾸거나 추가 Review/retry를 자동 호출하지 않는다.

ID/hash matching은 **structural traceability**이며 semantic correctness나 User intent 추론의 정확성을 cryptographically 증명하지 않는다. Reviewer가 유효 ID로 관련 없는 issue를 주장하는 경우도 Frontier가 criterion condition/evidence 관계를 확인해야 한다. 기준 부족이 실제 의도 모호성이면 아래 ambiguity 계약을 적용한다. 이를 새 generic Reviewer framework로 확장하지 않는다.

## Session ID / Run ID Relationship

**Observed:** run_id는 effects/evidence namespace다. 현재 Session identity가 없다. L6는1개 run 안에 right/left/back/geometry task IDs를 만들고, L7 bridge/correction은 별도 run_id 및 source lineage를 사용한다.

**Proposed cardinality:** 새 Session당 **하나의 logical top-level Loop attempt**만 만든다. 그 고정 Scenario A 경로에 acquisition(L6), geometry_review(L7 bridge), correction(L7 controller) child run은 각0/1개씩 연결한다. 이 child들은 동일 frozen Specification을 수행하는 내부 stage identities다. 여러 독립 Loop를 생성하거나 terminal 이후 child를 추가하는 manager를 설계하지 않는다.

- session_id와 logical loop_run_id는 서로 다른 값/역할이다. child run_id도 명시적 map으로 연결한다.
- 기존 run_id/task_id와 historical record는 보존한다. 과거 자료에 없는 session_id를 사후 생성하지 않는다.
- source_run은 inherited/reference evidence이며 fresh child로 재포장하지 않는다. source Review의 criteria가 현재 Spec에 bound되지 않으면 새로운 accept proof로 자동 사용하지 않는다.
- existing runner run_id 길이 제한48을 만족하는 child IDs를 사용한다. 단순 timestamp 재사용이나 global constant monkeypatch를 하지 않는다.
- 실행 구성/상한은 first effect 이전에 고정한다. 현재 전체 경로의 보수적 최대는 L6 Worker4/Reviewer1 + bridge Renderer1/Reviewer1 + correction Worker2/Reviewer2/Renderer1/revision1이다. 따라서 Proposed aggregate cap은 Worker6/Reviewer4/Renderer2/revision1, automatic retry0이다. 모든 stage가 실행된다는 뜻이 아니며 남은 budget을 채우기 위해 호출하지 않는다.
- 명세 budget이 위 fixed path보다 작으면 effect 전에 실행 가능성을 판정하거나 명시적으로 더 짧은 지원 경로를 선택한다. budget을 조용히 늘리지 않는다. S3에서 arbitrary budget DSL/공유 scheduler를 만들지 않는다.
- child의 기존 reservation/terminal guards를 유지하고, outer closed/ambiguous gate로 다른 namespace의 child를 추가하는 우회도 차단한다.

이 cardinality는 **Proposed**이며 현재 이미 통합된 end-to-end Session runner가 있다는 주장이 아니다.

## INTERNAL_ACCEPT Mapping

Observed:

- [C4 terminal_policy](../../src/scenario_a/c4_bounded.py#L162): PASS/no blocker/NONE이면 accepted=true와 DELIVERED를 같이 반환한다. Spec binding은 없다.
- [L6 GEOMETRY_READY](../../src/scenario_a/l6_pipeline.py#L622): valid GLB structural terminal이고 내부 제출 판정이 아니다.
- [L7 bridge finish](../../src/scenario_a/l7_geometry_review.py#L332): validated verdict를 기록하되 GEOMETRY_REVIEWED로 종료한다.
- [L7 controller source PASS branch](../../src/scenario_a/l7_feedback_controller.py#L615)와 [final PASS branch](../../src/scenario_a/l7_feedback_controller.py#L638): INTERNAL_ACCEPT, delivered=false. source PASS branch는 새 final Review가 아니라 기존 source Review에 의한 no-correction 결과다.

**Proposed Session-bound InternalAcceptEvidence**는 다음을 함께 고정한다:

- SpecificationRef와 applicable acceptance criterion IDs.
- final delivered-candidate artifact path/kind/bytes/SHA.
- final Review Request/Result/Invocation 및 validated criterion binding refs.
- Review가 그 artifact에 대한 것임을 확인하는 lineage. geometry는 render manifest.source_glb와 exact diagnostic/source roles로 연결한다.
- blocking issue 없음, action NONE/null 및 mandatory criteria 충족.
- local Loop outcome/child terminals와 실제 budget consumption.

“run state가 INTERNAL_ACCEPT”만 읽어 Session submit eligibility를 만들지 않는다. bridge PASS 경로도 Scenario adapter가 final geometry binding을 확인하여 별도 accept evidence를 만들어야 한다. inherited unbound source PASS는 bound proof가 아니며, current-spec final Review 없이는 accept하지 않는다.

## DELIVERED / External Frontier Boundary

### A / B / C 구분

| 분류 | 현재 근거 / 가능한 결과 | S1 의미 |
|---|---|---|
| A: historical technical transition | C4 terminal_policy와 branch test가 PASS→DELIVERED record를 만든다 | technical policy 검증. 이 함수만으로 사용자 전송 관측은 불가 |
| B: local delivery-ready output | validated artifact/final Review/INTERNAL_ACCEPT evidence, future Delivery Package | 아직 actual DELIVERED 아님 |
| C: actual external submission | User-facing Frontier가 package 검증 후 실제 메시지/attachment/file payload를 제출 | 실제 submission evidence 발생 후 DELIVERED/Session Close |

C4 record의 `delivery_channel=final_response`는 채널 의도다. source에 final-response transport 호출이나 message receipt 조회는 없다. Core Freeze는 당시 final response에서 Input/Output 제출을 명시하고 있으나, 이 감사는 local JSON만으로 그 외부 사건을 대체하지 않는다. 기존 C4 verified verdict를 변경하지 않는다.

**[추론] 이 프로젝트에는 Local Loop와 External Frontier Interaction의 분리가 맞는다.** local semantic Reviewer의 Codex subprocess는 사용자 제출 interface가 아니다. 다른 process/window/chat이라는 이유만으로 Delivery가 된 것으로 보지 않는다.

Proposed flow:

`bound local execution → INTERNAL_ACCEPT → immutable Delivery Package → external Frontier validates package → actual User submission → trusted submission evidence → DELIVERED / Session Close`.

local execution이 완료되어도 submission evidence가 없으면 Session은 내부 제출 가능/미제출 상태로 남는다. Worker/Reviewer effects는 이미 차단된다. transport 미확보는 Delivery boundary blocker이며 Worker FAILED, 사용자 불만 또는 same-Loop resume으로 처리하지 않는다.

### Delivery Package 최소 semantic 필드

| 필드 | 최소 의미 |
|---|---|
| session_id / SpecificationRef | session/version/path/hash |
| loop_run_id / child outcome refs | 단일 logical attempt와 관련 실행 결과 |
| artifact identity | final artifact path/URI, kind, bytes, SHA-256 |
| initial reference identity | 최초 Input과 필요한 reference 역할/path/hash |
| final_review identity | Request/Result/Invocation refs 및 criterion binding |
| internal_accept evidence | Spec/criteria/final artifact 연결을 검증한 기록 |
| presentation requirements | 시각적 산출물은 최초 Input + 최종 Output을 함께 제시. geometry는 실제 GLB와 해당 diagnostic view를 구분 |
| external evaluation request | 승인 / 자연어 피드백 / 사용하지 않음; Core state 외부 |
| package identity | package bytes/hash 또는 equivalent immutable identity |

외부 제출 후의 최소 receipt는 package identity, 정확한 제출 artifact/reference identities, 실제 channel, submission timestamp, 관측 가능한 message/attachment/transport ack reference와 생성 주체를 연결한다. message ID가 제공되지 않으면 그 이유와 다른 실제 submission 근거를 기록한다. 모든 submission evidence가 없는데 null을 채워 DELIVERED로 만드는 것은 금지한다.

S3는 receipt를 **검증/수용하는 interface**만 제안한다. 실제 external Frontier transport에서 이 receipt를 얻는 수단은 현재 repo에 없으며 UNKNOWN이다. local Codex가 final response를 작성하기 전에 미리 “전송 완료” receipt를 쓰면 안 된다. host가 실제 제출 뒤 event/ack를 제공할 수 없다면 actual Delivery proof는 BLOCKED로 남긴다. 이를 해결하려고 REST/API/service를 추가하지 않는다.

actual submission 뒤 Session close는 User approval을 기다리지 않는다. 이후 feedback은 외부 기록이다. historical child terminals를 rewrite하지 않고 새 outer delivery/closure record가 그 immutable 결과를 참조한다.

## Specification Ambiguity Signal

### Detection / distinctions

현재 bridge instruction의 HUMAN_REQUIRED는 reference insufficiency, orientation/defect-origin ambiguity, action confidence 부족을 모두 포함한다. controller는 이를 [ABORT/HUMAN_REQUIRED](../../src/scenario_a/l7_feedback_controller.py#L616)로 처리한다. 그것이 User Goal의 결정 불가능한 모호성이라는 typed proof는 없다.

| 현상 | 해석 / 처리 |
|---|---|
| Worker/Reviewer crash / known failure | FAILED와 invocation evidence |
| timeout / unknown submission or identity | UNRESOLVED, effects stop, blind retry0 |
| valid quality BLOCKER | REVISE; approved action과 남은 budget 안에서 correction |
| budget exhausted / explicit stop | ABORT |
| octree128/256 등 최적 기술 parameter 미확인 | 기술적 조사. User에게 선택을 떠넘기지 않음 |
| raised-text geometry가 필요한지 texture면 충분한지 User intent를 context로 선택 불가 | Specification ambiguity 후보 |
| unsupported criterion / malformed binding | contract violation. ambiguity나 PASS로 임의 변환하지 않음 |

감지 책임은 Work Specification을 읽는 Frontier planning/diagnosis 지점이다. Reviewer는 ambiguity evidence를 제안할 수 있지만 mechanical controller가 문자열/HUMAN_REQUIRED만으로 User intent를 추정하지 않는다.

### Proposed typed signal / no Core enum change

새 이름 `SpecificationAmbiguitySignal` / `SessionLoopOutcome`는 감사한 src에서 현재 정의되지 않았다. 아래는 implementation/schema가 아닌 최소 semantic interface다.

Signal minimum: SpecificationRef, logical/child run identity, detection stage, evidence refs, 두 개 이상 합리적 interpretation, artifact 방향의 material difference, frozen context로 선택 불가한 사실, 필요한 User clarification의 주제. 사고 chronology는 포함하지 않는다.

Outcome minimum: `reason=SPECIFICATION_AMBIGUITY`, signal ref, existing Run stop evidence, effects_stopped=true. outer Session은 `BLOCKED_SPECIFICATION_AMBIGUITY`로 종료한다.

전달 지점:

1. effect 전 planning/dispatch gate에서 signal이 확정되면 해당 Scenario runner의 기존 `StageFailure('ABORT', 'SPECIFICATION_AMBIGUITY')` 처리에 연결한다. 새 Core enum은 추가하지 않는다.
2. Review 이후 감지되면 기존 bounded ABORT 결과와 typed signal을 묶고 다음 Worker/Review/child 생성을 차단한다. raw Result는 그대로 보존한다.
3. 아직 child가 시작되지 않았다면 Session만 ambiguity 종료하며 fake Run terminal을 만들지 않는다.
4. 호출 중 발생한 signal은 현재 invocation evidence를 정리한 후 다음 effect 이전에 처리한다. infrastructure outcome이 불확실한 동안 “정상 ABORT 완료”를 조작하지 않는다. 이런 경우 unresolved safety stop도 함께 명시하고 resume하지 않는다.
5. Session 종료 후 external Frontier가 clarification을 요청한다. 답변은 새 Request/Session/dialogue/Spec/Loop다. ASK_USER→same Loop resume 경로를 만들지 않는다.

existing monolithic runners에는 이 gate가 현재 없다. S3 opt-in hooks는 Work Order execution, Reviewer invocation, correction dispatch 및 stage 전환의 추가 effect 이전에 같은 binding/closed guard를 적용해야 한다. 일반화된 graph/interrupt service는 필요하지 않다.

## Feedback / New Session / Handoff

Proposed lineage:

`Previous Session/Specification + actually Delivered Artifact + external User Feedback + relevant evidence → selected Handoff Pack → Current Request → fresh Session interpretation/dialogue → new Work Specification → new logical Loop`.

- Approval, 자연어 수정/추가 요구, 사용하지 않음은 외부 evaluation으로 보존한다.
- modification이면 ARTIFACT_MODIFICATION, follow-up이면 FOLLOW_UP, ambiguity clarification이면 RESTART_AFTER_AMBIGUITY다.
- 이전 artifact/Spec와 verified facts/results/known failures를 reference로 쓸 수 있다. 새로운 Spec authority를 다시 정리한다.
- new Request가 만들어져도 과거 Session/Loop terminal을 변경하지 않는다. feedback을 internal REVISE record에 넣지 않는다.
- 외부 Frontier가 새 dialogue를 수행하고 충분한 context에서 새 Spec를 제출한다. local boundary는 dialogue 결과의 Ready Gate와 blocker 없음만 검사하며 모든 미지정 detail에 질문을 강제하지 않는다.
- R1의 facts/confirmed decision은 inherited Knowledge 대상이다. 아직 실행하지 않은 parameter proposals와 cause hypotheses는 UNKNOWN/FUTURE 성격을 유지한다.
- “몸통을 더 매끄럽게”의 Goal은 새 Session에서 명세화하되 현재 seed-only policy가 목표 달성을 보장한다고 주장하지 않는다. capability 또는 technical policy gap이면 그 사실을 보고한다.

## Durable Knowledge vs Active Context

| 분류 | persist 가능 | startup context eligibility | 제한 |
|---|---|---|---|
| 최종 Specification/References/Delivered Artifacts | Yes | 현재 Request와 관련된 항목만 선택 | 원 authority/identity 유지; 새 Spec와 재해석 |
| User feedback/명시적 preference/constraint | Yes | 적용 범위가 현재 업무에 맞으면 선택 | User 결정과 Frontier 추론 구분 |
| verified facts/measurements/tests/execution/results/known failures/final decisions | Yes | 근거/시점/실제·fixture·historical 성격을 유지하여 선택 | hypothesis를 fact로 승격 금지 |
| environment/tool state/unresolved issues/lineage | Yes | 필요 시 현재 validity 확인 후 선택 | 과거 available을 현재 보장으로 사용 금지 |
| raw log/transcript/historical archive | Yes, 삭제 불필요 | archive-only가 기본; 특정 evidence 조회만 선택 | 전체 startup auto-injection 금지 |
| internal chain-of-thought/가설 변화 chronology/prior active reasoning state | active-context 상속 불가 | 기본 context에서 제외 | 이전 사고 흐름 재구성/복원 목표 금지 |

Proposed 보장 위치: Session boundary의 startup-input selection interface. current Request/References, 명시적으로 선택한 typed durable records, 해당 previous Spec/artifact/feedback만 외부 Frontier의 새 context로 전달한다. archive ref를 넣었다고 transcript content를 자동 읽지 않는다. Spec dialogue가 완료될 때까지 scenario runner를 호출하지 않는다.

새 module이 외부 Codex chat의 기존 hidden/active context를 강제로 지울 수는 없다. Fresh-context reset에는 external host의 fresh conversation/process/context 지원이 필요하다. Core Reviewer `--ephemeral`은 storage mode이며 **outer Frontier의 독립 startup을 증명하지 않는다**. S3 loader는 전달하는 content의 계약만 검증하고, host reset 여부는 separately observable해야 한다.

## Architecture Options

| Option | Files touched (Proposed) | Core impact | Scenario impact | Test surface | Migration cost | S1 compliance / risk | 판단 |
|---|---|---|---|---|---|---|---|
| A. Session boundary above fixed Scenario adapter | 새 session_boundary + session_loop_adapter, L6/bridge/controller opt-in hooks |0; schema/C1–C5 unchanged | binding/selected-source parameterization만 | outer lifecycle, binding, no-effect gates, 기존 legacy tests | 중간: current3runner에 explicit seam 필요 | S1 역할 분리. 순수 wrapper만으로는 불충분하므로 hooks 필수 | **선택** |
| B. Session-aware scenario runner만 사용 | L6/L7에 dialogue/lifecycle/delivery/handoff 책임 삽입 |0 가능 | 세 runner에 상위 책임 중복 | lifecycle와 Scenario tests가 결합 | 높음: 서로 다른 terminals/entry에 Session 의미 중복 | fresh-context/external delivery 경계 흐려질 위험 | 비추천 |
| C. Core-level integration | Core Request/Result/WorkerPort/schema 및 Scenario callers | frozen Core 변경 | strict schemas 전파 | C1–C5 전체 계약 재검증 필요 | 높음 | 편의성 외 exact blocker 없음; freeze 침범 | 거절 |

A는 범용 Session manager가 아니다. 하나의 업무와 하나의 fixed Scenario A logical Loop를 연결하는 문서상 최소 facade다. arbitrary DAG/plugin/scheduler/DB/queue/service를 추가하지 않는다.

## Recommended Minimal Seam

**Proposed 위치와 책임:**

1. `src/session/session_boundary.py`: external Frontier에서 확정한 Request/dialogue/Spec를 받고 Ready/capability 전제 확인, immutable SpecificationRef 생성/검증, selected durable startup content, typed Session outcomes, accept/package 검증, 실제 receipt 후 closure.
2. `src/scenario_a/session_loop_adapter.py`: 고정 Scenario A route와 explicit child run map을 소유한다. session_id를 execution task_id로 사용하지 않는다. Spec binding을 기존 Scenario callers에 전달한다.
3. opt-in `session_binding` parameter를 L6/L7 callable에 추가한다. legacy mode는 기존 contract/criteria/pins 그대로 유지하고, bound mode는 Spec-bound instructions와 pre-effect checks를 사용한다.
4. bridge의 selected `source_l6_run`은 terminal/artifact/reference hashes로 검증한다. default historical pins는 그대로 둔다. controller는 source Review initial에 고정된 selected L6 identity를 따라 검증한다. module constants를 global patch하지 않는다.
5. NEW_WORK fixed route: L6 acquisition → GEOMETRY_READY → bridge final geometry Review. PASS이면 bound InternalAcceptEvidence, REVISE이면 supported action/capability/budget 확인 후 correction controller1회, HUMAN_REQUIRED는 typed intent ambiguity 또는 generic ABORT로 구분한다.
6. multiview 단계에서 REVISE이면 현재 L6 bounded ABORT를 유지한다. arbitrary image correction loop를 추가하지 않는다. correction re-review의 REVISE도 기존 budget exhaustion ABORT다.
7. correction은 현재 seed-only policy를 **그대로 식별**한다. R1의 NOT_SUPPORTED_BY_CURRENT_EVIDENCE를 무시하고 품질 개선을 약속하거나 정책을 바꾸지 않는다. S3는 mock/local validation만, 실제 correction은 별도 명시된 실행 milestone과 policy 판단이 필요하다.
8. 모든 instructions/Work Orders가 frozen Spec authority에 bound되고 effect 전에 검증되어야 한다. mismatched/unsupported/legacy-unbound source는 execution eligibility를 얻지 못한다.
9. local INTERNAL_ACCEPT에서 package까지만 생성한다. external Frontier가 실제 User submission 뒤 관측 가능한 evidence를 제공하면 새 Session delivery/close record를 기록한다. receipt가 없으면 DELIVERED 금지다.
10. 종료된 Session에 추가 child/effect/context resume을 허용하지 않는다. feedback과 clarification은 fresh startup와 new Spec를 만든다.

최소 input interface는 external Frontier가 확정한 S1 Specification document와 해당 필드의 명시적 구조화 projection이다. boundary는 document path/hash와 projection의 identities/criteria를 연결해 검증한다. 자연어 문서를 자동 해석하는 parser나 이전 reasoning transcript 복원은 제안하지 않는다.

Proposed callable surface는 `freeze_specification(specification_document, finalized_fields)`, `build_startup_context(current_request, current_references, selected_durable_refs)`, Scenario adapter의 `run_session_loop(binding_ref, *, execute=False)`, boundary의 `prepare_delivery(outcome_ref)`와 `record_submission(package_ref, submission_evidence)`다. 현재 구현된 API가 아니며 S3에서 기존 exclusive-write/hash helper와 정합하도록 구체화한다. 실제 transport emitter는 이 interface에 포함하지 않는다.

기존 Scenario의 topology 및 budget/reservation/action vocabulary를 재사용한다. 본 제안은 일반적인 User Goal을 기존 고정 workflow가 모두 처리할 수 있다는 의미가 아니다. S3까지의 상태는 local seam implementation/validation이며 actual Session closure/Level7 품질 proof와 별개다.

## Proposed S3 File-Level Change Surface

모두 **Proposed / NOT CREATED / NOT MODIFIED**다. 이번 S2에서 아래 파일을 만들거나 고치지 않는다.

### Existing file changes

| Path | Why / 최소 semantic change | 건드리지 않는 범위 |
|---|---|---|
| `src/scenario_a/l6_pipeline.py` | run_pipeline에 keyword-only optional session_binding; initial/order sidecar refs, bound prepare_review/validate_review_lineage, Work Order/Review pre-effect gates, typed stop→기존 finish 정책 | asset/workflow/Plan/executor/legacy criteria와 기본 effect-free behavior |
| `src/scenario_a/l7_geometry_review.py` | run_bridge/validate_l6와 해당 input/manifest validators에 explicit selected-source binding 전달; current source hash 검사; bound instruction/Review gate; typed stop | renderer/config/camera/model; legacy pins; diagnostic action vocabulary |
| `src/scenario_a/l7_feedback_controller.py` | source Review→selected L6 ref 검증; 초기/Work Order/Review/correction에 동일 session_binding; exact context equality의 bound-mode validator; copied old prose 대신 current Spec criteria; terminal에 binding evidence 연결 | seed+1 policy와 기존 stage/budget/retry semantics; R1 diagnosis |
| `tests/test_l6_pipeline.py` | 기존 default/preflight/legacy contract 검증에 opt-in regression 항목 보강 | actual Comfy 호출 금지 |
| `tests/test_l7_geometry_review.py` | legacy pin 유지 및 explicit fresh-source proof validation fixture | 실제 Blender/Reviewer 금지 |
| `tests/test_l7_feedback_controller.py` | current-bound source/Review를 소비하고 unsupported criteria/ambiguity에서 effect0 추가 검증 | correction quality/parameter experiments 금지 |

`src/core/**`, `result_review_schema.json`, `codex_to_comfy.py`, `comfy_worker_adapter.py`, `c1_delegate.py`–`c5_worker_swap.py`, `l7_blender_diagnostic.py` 변경은 필요하지 않다.

### New files

| Path | Exact role |
|---|---|
| `src/session/__init__.py` | 새 outer package import root; framework registry 없음 |
| `src/session/session_boundary.py` | SpecificationRef/typed binding/outcome, Ready freeze, criterion binding validation, selected startup/handoff, Delivery Package/receipt/Session close 최소 계약 |
| `src/scenario_a/session_loop_adapter.py` | 단일 fixed Scenario A logical Loop를 기존 callable/child IDs와 연결. effect gate와 outcome normalization. 신규 workflow/backend 없음 |
| `tests/test_session_boundary.py` | Request/Spec readiness/immutability, feedback=newSession, ambiguity close, handoff selection, actual receipt 없는 Delivery 차단 |
| `tests/test_session_scenario_binding.py` | L6/L7 opt-in binding integration fixtures, hashes/criteria/source/child lineage, unsupported blocker/capability, bounded/no-effect guards |

Runtime records는 위 semantic refs/sidecars의 최소 durable 표현만 사용한다. DB schema나 새로운 persistence framework를 설계하지 않는다. 파일 위치/encoding은 S3에서 기존 exclusive write/hash helper와 정합하도록 결정한다.

### S3 acceptance / effects

- Frozen Core/schema/C1–C5 및 historical evidence diff0.
- legacy related tests와 opt-in fixture tests PASS; default callable/CLI는 effect-free 유지.
- Ready=false/blocking ambiguity/capability unsupported이면 Worker/Renderer/Reviewer0.
- first effect 전 Spec ref와 immutable SessionRunBinding 존재; mutation/version/identity/criterion mismatch는 다음 effect 차단.
- Plan exact fields 유지; Work Order/Review sidecar와 Request hash로 동일 Spec/criteria/artifact lineage 연결.
- unsupported blocker는 correction/accept 차단; raw Result rewrite0.
- ambiguity는 existing Run ABORT+typed outcome 또는 no-child Session stop; no User inside Loop/no same-Loop resume.
- one logical Loop/fixed child cardinality, budgets/collisions/terminal re-entry 차단.
- INTERNAL_ACCEPT만으로 DELIVERED 불가; actual submission evidence 검증 경계는 fixture임을 명시.
- new Request의 selected startup input은 durable facts/evidence만 포함; prior active reasoning stream 자동 주입0.
- expected actual external effects: **Worker0 / Comfy0 / Blender0 / semantic Reviewer0 / revision dispatch0**. mocks/local fixtures는 actual proof로 선언하지 않는다.
- actual execution/Delivery transport proof/geometry policy 실험은 별도 요청 범위다. 이 계획을 승인하거나 구현한 것처럼 보고하지 않는다.

## Risks / Unknowns

- **S3 implementation risk:** fresh-source parameterization은 source hash 검증을 약화하지 않아야 한다. bridge/controller의 재귀 historical validation을 그대로 호출하는 부분까지 explicit binding을 전달해야 한다. 경로 인자만 추가하고 내부 fixed constants를 남기면 충분하지 않다.
- **Semantic limit:** criterion ID/hash 검사는 authority traceability이며 Reviewer의 의미 판단 정확성을 보장하지 않는다. 유효 ID를 단 unrelated blocker를 처리하는 Frontier validation이 필요하다.
- **Capability limit:** current fixed workflows/source asset/seed-only policy는 임의 Request/수정 요구를 처리하는 generic 제작 능력이 아니다. 부족하면 pre-effect blocker로 남긴다.
- **Actual Delivery UNKNOWN:** repo에 User-facing transport/receipt emitter가 없다. host의 실제 submission ack 지원 여부는 이번 감사에서 확인하지 않았다. 예측/자기선언 receipt는 proof가 아니다.
- **Fresh-context UNKNOWN:** 외부 host가 새 context를 보장하는 방법은 미구현/미확인이다. local selected-input contract만으로 기존 chat context가 지워졌다고 주장할 수 없다.
- **Safety limit:** infrastructure UNRESOLVED는 정상 terminal proof가 아니다. Session integration 때문에 resume/recovery/uncertain refund를 추가하지 않는다.
- **L7 quality limit:** [R1 diagnosis](../l7/L7_R1_GEOMETRY_REVISION_DIAGNOSIS.md)의 seed-only NOT_SUPPORTED_BY_CURRENT_EVIDENCE 및 workflow/normal/shading 조사 결정은 유지한다. S2는 Level7 실패를 해결하지 않는다.
- **Historical scope:** existing Core actual proof, L6 verified structural pipeline, L7 bridge verified와 L7 closed-feedback NOT VERIFIED를 구분한다. Session source binding이 과거에 있었던 것처럼 retrofit하지 않는다.

### Static Walkthrough

아래는 Proposed seam의 문서 검증이다. 코드 실행이나 actual semantic proof가 아니다.

| Case | 경로 / 기대 | 정적 판정 |
|---|---|---|
| A — NEW_WORK | Request→external Spec dialogue→Ready→boundary→fixed adapter/current runners→bound INTERNAL_ACCEPT→package→external actual delivery evidence | PASS; 지원 capability/transport 조건은 명시적으로 확인 |
| B — Reviewer REVISE | frozen criterion ID/authority 검증→supported action→남은 fixed budget 내 controller correction; exhausted이면 기존 ABORT | PASS; 추가 독립 Loop/무한 retry 없음 |
| C — unsupported blocker | criteria 밖 issue는 blocking REVISE 권한 없음. raw Result 보존, REVIEW_CONTRACT_VIOLATION, correction/accept 차단 | PASS; 임의 PASS downgrade 없음 |
| D — technical uncertainty | Spec/envelope/evidence로 internal investigation; User에게 octree/sampler 결정 위임 없음 | PASS; 허용 범위/예산 밖 실험 없음 |
| E — specification ambiguity | typed alternatives/impact/context insufficiency→effects stop→Session BLOCKED_SPECIFICATION_AMBIGUITY→clarification은 새 Request/Session | PASS; same-loop ASK_USER/resume 없음 |
| F — actual Delivery | local INTERNAL_ACCEPT/package만으로 미제출. actual submission receipt 이후 DELIVERED/close; User 승인 대기 없음 | PASS; transport evidence 없으면 Delivery blocker |
| G — modification feedback | old Session closed 유지→new Request→selected handoff→fresh dialogue→new Spec→new supported Loop | PASS; 기존 artifact/evidence 재사용, capability 없는 변경은 effect 전 차단 |
| H — refresh | current Request+선택한 durable facts/results/artifacts/decisions; raw reasoning stream 자동 주입0 | PASS; external host reset proof는 별도 확인 |

## Protection / Effects

S2 수행: file reads, AST parsing, source searches, git/ref/history inspection, hash/stat snapshot 및 감사 문서 작성만 허용했다. Production module을 import/실행하거나 auth probe/runner preflight/CLI를 호출하지 않았다. pytest/unittest도 실행하지 않았다.

- 시작/종료 tracked files234개 SHA-256 비교 PASS, 변경0. S1/Core/L6/L7/tests/runs/기존 docs가 동일하다.
- Research HEAD `7e1572a7e35866519b75b767398288396a27f9b0`; sole untracked `ac6_f2b_resume.py` SHA `2a58ab64e8838e8c3da6d8b4d62526e1a8d0d834bb26058d905d80d73dfd9369`. Research tracked files+WIP 총186개 시작/종료 hash 비교 PASS, 변경0; commit/push0.
- L6 manifest가 참조하는 external assets18개는 size/mtime snapshot. 시작/종료 size/mtime 및 작은 파일 SHA-256 비교 PASS, 변경0. 대형 model 전체 hash는 측정하지 않음.
- Core/main/tag, S1 branch, L6/L7 branches/history, historical Work Orders/Review/Artifacts/Usage, workflows/models 변경0.
- S2 신규 tracked file: `docs/session/S2_SESSION_INTEGRATION_SEAM_AUDIT.md` 하나.
- actual effects: **Comfy submissions0 / Blender processes0 / Frontier semantic Review0 / revision dispatch0 / Worker execution0**.
- 감사 source module15개를 read-only로 확인. AST로 claimed functions44개 존재 확인 PASS; 상대 links57개와 source line anchors46개 유효성, required sections19개, mapping27rows, Markdown 구조, 정확한 신규 파일1개 검증 PASS. Static A–H walkthrough는 문서상 정책 검토 PASS이며 실제 semantic execution proof가 아니다. Production 변경0이므로 full regression은 수행하지 않았다.

## Final Status

S2 감사 완료는 S3 구현이나 actual Session Delivery proof의 완료를 뜻하지 않는다. 문서 static walkthrough/protection 검증 후 `session-integration-s2`에 정상 commit/push하고 clean을 확인하여 STOP한다. main merge/tag/release/L7-R2/geometry 실험/새 effect를 시작하지 않는다.

```text
AGENT LOOP CORE V1.0.0 = FROZEN / UNCHANGED
LEVEL 6 MULTI-STAGE SUPERVISED PIPELINE = VERIFIED
L7-M0 MANDATORY GATE = PASS
L7-M1 GEOMETRY REVIEW BRIDGE = VERIFIED
L7-M2 MINIMAL FEEDBACK CONTROLLER = READY
L7-M3 ACTUAL CLOSED FEEDBACK PROOF = NOT PASSED
L7-R1 GEOMETRY REVISION DIAGNOSIS = COMPLETE
S1 SESSION / REQUEST / WORK SPECIFICATION CONTRACT = COMPLETE
S2 SESSION INTEGRATION SEAM AUDIT = COMPLETE
S3 SESSION INTEGRATION IMPLEMENTATION = NOT STARTED
LEVEL 7 CLOSED FEEDBACK PIPELINE = NOT VERIFIED
HYPOTHESIS BENCHMARK = NOT STARTED
```
