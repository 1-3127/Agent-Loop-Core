# S1 Session / Request / Work Specification Contract v0

## 1. 지위와 범위

이 문서는 Request 해석, Session 명세, Loop 경계, Delivery, Feedback, Session Refresh와 Knowledge Inheritance의 normative contract다. MUST/금지는 필수 규칙이며 SHOULD/권장은 안전한 기본값이다. production state machine이나 저장 schema를 정의하지 않는다.

최상위 방향은 [Direction Gate v1](../Agent-Loop_Direction_Gate_v1.md)이다. S1은 그 방향 위에 Session의 의미를 명시한다. [Core v1 freeze](../../CORE_V1_FREEZE.md), 기존 Core/L6/L7 source와 historical evidence를 변경하거나 재판정하지 않는다.

작성 baseline: `scenario-a-l7` / `1da2bef094d2cc3f4bd70bbc266d99dc955460bb`. 문서 branch: `session-contract-s1`. Core main/tag target: `7eee393801f4d8c14278b43ebcbaabaec7ccc9df`; L6 branch: `840b138cc023c623108c44c3944948b065300f99`.

범위는 이 contract와 [Work Specification template](S1_WORK_SPECIFICATION_TEMPLATE_v0.md), [Session Handoff template](S1_SESSION_HANDOFF_TEMPLATE_v0.md) 3개다. 구현, CLI, DB, scheduler, generic DAG/DSL, resume engine, L7 correction-policy 실험과 실제 generation/render/semantic Review는 포함하지 않는다.

## 2. Request / Session / Loop / User

| 개념 | 정의 | 책임과 경계 |
|---|---|---|
| Request | 업무가 시작되는 원인. User가 무엇을 원하는가 | Goal, Reference, 자연어, 이전 artifact 또는 feedback을 포함할 수 있다. 불완전한 Request도 정상이다. |
| Session | 요구 해석, 명세, 실행과 제출을 포함하는 업무 단위 | 관련 Knowledge 조회 → User↔Frontier Specification Dialogue → 실행 가능한 Work Specification → Loop → Delivery → 종료 |
| Loop | 고정 Specification을 만족하는 artifact를 만드는 내부 실행 조직 | Frontier가 지휘하고 Workers가 제작하며 Reviewer가 내부 검수한다. Session과 동일하지 않다. |
| User | Loop 외부의 고객/의뢰자이며 Delivery 이후 외부 평가자 | Goal, 선호, 제약과 의도를 확정한다. Worker/Reviewer/Tool 또는 반복 HITL 승인 구성요소가 아니다. |

관계: Request → Session {Specification Dialogue, Work Specification, Loop {Frontier, Workers, Reviewer, Correction}}.

작업에 요구되는 외부 전송/권한 승인은 별도 authorization 조건이다. 이를 사용자 semantic Review나 일상적인 기술 결정 위임으로 해석하지 않는다.

## 3. 모든 Session의 시작

새 작업, 산출물 수정, 후속 요구, ambiguity 이후 재시작 모두 같은 진입 규칙을 따른다.

Request + References + relevant Durable Knowledge → User↔Frontier Specification Dialogue → 새 Work Specification → SPECIFICATION_READY → 새 Loop.

새 Frontier의 startup 순서:

1. Current User Request
2. Current References
3. Relevant Durable Knowledge
4. Previous Delivered Artifact / Specification, 해당하는 경우
5. User Feedback, 해당하는 경우
6. Frontier independent interpretation
7. User↔Frontier Specification Dialogue
8. New Work Specification와 readiness 확인
9. Loop Start

이전 명세는 현재 Request를 해석할 reference다. 이전 명세가 있어도 이번 Session의 dialogue와 명세 확정을 생략하지 않는다. 이미 충분한 context가 제공되었다면 불필요한 질문 없이 이해와 해석을 정리하여 명세를 확정할 수 있다. Dialogue는 고정 질문 수나 인터뷰 양식이 아니다.

## 4. Specification Dialogue / Sufficient Context

Frontier는 Goal, References의 의미, intended use, deliverables, Must-Have, acceptance criteria와 중요한 constraints를 User와 정리한다. 질문 대상은 User의 의도/선호/권위 있는 결정이다. octree, sampler 등 내부 기술 선택을 User에게 떠넘기지 않는다.

질문 전 다음 조건을 모두 확인한다.

1. 제공된 context에서 답을 합리적으로 추론할 수 없는가?
2. 답이 실제 Work Specification을 바꾸는가?
3. User가 해당 답의 authoritative source인가?
4. 답을 정하지 않으면 artifact 방향이 의미 있게 달라지는가?

이 조건에 해당하는 decision-critical ambiguity만 clarification 대상으로 삼는다. User가 명시하지 않은 모든 세부사항을 질문으로 채우지 않는다. 기술 불확실성은 허용된 범위/예산 안에서 inspect, test, search, experiment, reason 등 내부 수단으로 해결한다.

Sufficient Context는 다음을 이해/정의할 수 있고 남은 세부사항을 안전하게 추론할 수 있는 상태다.

- Goal과 desired outcome
- References의 역할, authority, 보존/해석 범위
- Intended use (현재 판단에 무관하면 unknown/irrelevant와 이유 허용)
- Deliverable의 type/format/quantity
- Must-Have와 Reviewer가 사용할 acceptance criteria
- 중요한 constraints와 실행 budget
- 남은 ambiguity의 처리 가능성

모든 세부사항이 User의 직접 발언으로 확정되어야 하는 것은 아니다. 예를 들어 context 없는 “배”는 과일/선박/신체 중 무엇인지 결정할 수 없으므로 blocking이다. 선박 reference, 사용 플랫폼과 style이 충분하다면 bolt 개수나 sampler는 Frontier가 결정할 수 있다.

## 5. Work Specification / Ready Gate

Work Specification은 이번 Session의 최종 업무 계약이다. 최소 필드는 template에 고정한다.

- Identity: session_id, specification_version, request_type, optional previous_session/lineage
- User Goal: original_request_summary, desired_outcome, project/background context
- References: role, authority, purpose, 보존할 것과 해석 가능한 것
- Intended Use와 Deliverables (type/format/quantity/supporting outputs)
- Must-Have / Should-Have / Non-Goals
- Acceptance Criteria: 실제 Reviewer PASS/REVISE의 근거
- Constraints: 관련 deadline/budget/cost/environment/performance/format/compatibility/legal 조건
- Interpretation Envelope: Frontier가 스스로 결정할 수 있는 범위
- Explicit User Decisions / Known Unknowns
- SPECIFICATION_READY, readiness_reason, unresolved_blocking_ambiguities

request_type은 NEW_WORK / ARTIFACT_MODIFICATION / FOLLOW_UP / RESTART_AFTER_AMBIGUITY 중 하나다.

Ready Gate는 Goal, Reference 역할, Intended Use, Deliverable, Must-Have, Acceptance Criteria, 중요한 constraints를 이해/정의할 수 있으며 남은 ambiguity를 합리적으로 추론할 수 있을 때만 true다. decision-critical ambiguity가 하나라도 남으면 false이고 Loop를 시작하지 않는다.

Reference authority는 기능별로 명시한다. 이미지가 색상/스타일의 authority인지, 구조/문자의 authority인지, 단순 inspiration인지 구분한다. 이미지에 보이는 모든 요소가 자동으로 Must-Have가 되지는 않는다. criterion마다 User Goal/결정/authoritative reference와의 근거를 연결한다.

Should-Have와 범위 밖 개선점만으로 REVISE하지 않는다. REVISE는 고정 acceptance criteria를 만족하지 못하는 BLOCKER에 대해 사용한다.

Loop 시작 시 specification_version과 내용은 immutable하다. 결과에 맞춰 acceptance criteria를 낮추거나 새 blocker를 조용히 추가하지 않는다. Plan/Work Order는 그 Goal contract와 Interpretation Envelope 안에서 파생한다. 계약 밖 요구 변경은 새 Request/Session에서 다룬다.

명세에는 최종 facts/decisions/constraints/acceptance/authority와 필요한 resolved interpretation만 남긴다. raw transcript, hidden/internal chain-of-thought, 장문 reasoning stream이나 가설 변화 chronology를 넣지 않는다.

## 6. Loop 경계 / Inference / Ambiguity

내부 흐름: Specification → Frontier → Plan/Work Order → Worker → Evidence → Reviewer → Diagnosis → Correction → … → INTERNAL_ACCEPT → DELIVERED. 실제 effect와 반복은 명시된 authorization과 bounded budget 안에서 수행한다.

Loop 도중 unspecified detail이 발견되면 다음 순서로 판단한다.

1. Current Work Specification
2. Original User Request
3. Authoritative References
4. 확정된 Session Dialogue context
5. Durable inherited Knowledge
6. Current Evidence

하나의 합리적 방향을 선택할 수 있으면 Frontier가 결정하고 계속한다. 기존 Knowledge는 현재 명세를 조용히 덮어쓰지 않는다. 사실/결정/추론/미확인을 구분하며 중요한 추론은 추론으로 표시한다.

다음이 모두 참이면 irreducible decision-critical ambiguity다: 두 개 이상 합리적 해석이 있고, 선택에 따라 artifact 방향이 의미 있게 달라지며, 기존 context로 User Goal에 맞는 쪽을 결정할 수 없다.

이 경우 현재 Loop의 추가 effect를 중단하고 Session을 BLOCKED_SPECIFICATION_AMBIGUITY로 종료한다. 이는 Worker/Reviewer/technical failure와 별개의 Session-level 종료 사유다. 필요한 ambiguity와 evidence를 durable하게 남긴 뒤 clarification을 Loop 밖에서 요청한다.

금지되는 처리: ASK_USER → same Loop resume. clarification은 새 Request의 원인이며 새 Session → 새 Specification Dialogue → 새 Work Specification → 새 Loop를 만든다. 이전 artifact/specification/verified evidence/ambiguity record는 재사용할 수 있다. 기존 Core/L7 Run의 state를 S1 용어로 rewrite하지 않는다. production 종료 상태와의 연결 구현은 별도 migration 대상이다.

## 7. Delivery / Feedback / New Session

INTERNAL_ACCEPT는 Frontier가 고정 명세 기준으로 제출 가능하다고 내부 판단한 상태다. User 승인이 아니며 실제 제출 전에는 DELIVERED가 아니다.

DELIVERED는 INTERNAL_ACCEPT된 artifact가 User에게 실제 제출된 상태다. 정상 Loop terminal이며 동시에 정상 Session의 종료 지점이다. CLOSED는 그 종료를 표현하는 Session 표기이며 추가 사용자 승인 대기나 effect를 뜻하지 않는다.

제출 시 최종 payload와 identity를 명확히 한다. 시각적 artifact의 User 판정을 요청할 때 최초 Input과 최종 Output을 함께 제시한다. Direction Gate에 따라 다음 외부 판정을 반드시 요청한다: 승인 / 자연어 피드백 / 사용하지 않음. 수정 요청과 추가 요구는 자연어 피드백으로 표현할 수 있다.

User Evaluation은 Delivery 이후 Loop 밖에서 발생한다. Core Run state에 User 판정을 넣지 않으며 COMPLETE/Session close를 사용자 승인에 의존시키지 않는다. ABORT/FAILED 결과는 evidence/debug 자료로 제시할 수 있지만 정상 DELIVERED payload로 제출하지 않는다.

Feedback은 Internal Reviewer Result나 old Loop REVISE가 아니다. 승인/사용하지 않음은 외부 평가로 보존할 수 있다. 수정/추가 요구가 업무로 이어질 경우 새로운 Request/Session의 원인이 된다. User feedback으로 이미 종료한 Session/Loop를 다시 열지 않는다.

예: Session A → Specification A → Loop A → Artifact A → DELIVERED/close. 이후 “몸통을 더 매끄럽게”는 ARTIFACT_MODIFICATION Request → Session B → dialogue → Specification B → Loop B다. Artifact A/specification/feedback/verified facts/results/known failures/evidence를 사용할 수 있다.

## 8. Session Refresh / Knowledge Inheritance

Refresh는 anchoring, accumulated assumptions, local optimization bias, long-context inertia와 이전 Frontier의 active mental trajectory를 끊고 현재 Request를 독립적으로 재구성하는 것이다. 이전 증거를 버리거나 매번 처음부터 제작하라는 의미가 아니다.

Durable Knowledge로 다음을 상속할 수 있다: previous specifications, delivered artifacts, references, user feedback, explicit preferences/constraints, verified facts, measurements, test/execution results, known failures, confirmed technical findings, current tool/environment state, final decisions, unresolved issues, evidence와 lineage. 환경 정보는 관측 시점과 근거를 함께 남기고 현재 validity가 필요한 경우 확인한다.

기본 active context로 상속하지 않는 항목: full thought transcript, hidden/internal chain-of-thought, moment-to-moment hypothesis transitions, raw speculation, 사고 chronology, conversational inertia, uncommitted intuitions, prior active reasoning state.

FACTS / ARTIFACTS / RESULTS / DECISIONS / CONSTRAINTS / EVIDENCE는 durable이고 THOUGHT TRAJECTORY는 transient다. 결정의 근거 evidence reference와 짧은 확정 이유는 보존할 수 있다. speculative hypothesis는 verified fact로 승격하지 않으며 필요한 후속 항목은 미확인으로 남긴다.

Raw logs/transcripts/historical files를 삭제하지 않는다. Archive로 보존하고 필요할 때 특정 evidence를 조회할 수 있다. 새 Session 시작 시 전체 reasoning stream을 자동 주입하거나 복원하지 않는다. 새 Frontier는 무슨 일이 있었는지 알 수 있으나 이전 Frontier의 생각 흐름 안에서 시작하지 않는다.

## 9. Conceptual Session Lifecycle

정상: REQUEST_RECEIVED → SPECIFICATION_DIALOGUE → SPECIFICATION_READY → LOOP_RUNNING → INTERNAL_ACCEPT → DELIVERED → CLOSED.

| Session 개념 | 의미 |
|---|---|
| REQUEST_RECEIVED | Request 수신과 관련 Knowledge 조회 시작 |
| SPECIFICATION_DIALOGUE | context 해석/필요한 clarification/명세 정리 |
| SPECIFICATION_READY | Ready Gate true; 새 Loop 진입 가능 |
| LOOP_RUNNING | 고정 명세에 따른 내부 execution/review/correction |
| INTERNAL_ACCEPT | 내부 제출 가능 판정; 실제 제출 전 |
| DELIVERED / CLOSED | 실제 제출 및 정상 업무 종료; 이후 effect 없음 |
| BLOCKED_SPECIFICATION_AMBIGUITY | 결정 불가능한 중요 모호성으로 현재 Session 종료; clarification은 새 Session |
| FAILED | 정의된 실패 조건에 따라 업무 종료 |
| ABORT | 예산/한도/명시적 중단으로 업무 종료 |

Session lifecycle ≠ existing Core/L7 Run state. 예: Session LOOP_RUNNING 중 내부 Loop가 GEOMETRY_REVIEWING일 수 있다. 이 개념 목록은 production enum/transition graph/DB schema를 변경하는 지시가 아니다. 기존 UNRESOLVED/infrastructure uncertainty를 S1만으로 성공 terminal로 재분류하지 않는다.

## Compatibility Notes

| 용어 / 기존 근거 | 기존 의미 | S1 상위 의미 | 충돌 / 향후 migration |
|---|---|---|---|
| INTERNAL_ACCEPT / Direction Gate §3, Core freeze | Frontier 내부 제출 가능 판정 | Session에서도 내부 판단과 실제 제출을 구분 | 호환. User 승인으로 바꾸지 않음. |
| DELIVERED / Direction Gate §2.3/3, freeze | 실제 사용자 제출; Loop terminal | 정상 Session 종료 지점 | 호환. Core record의 status만으로 실제 제출을 추정하지 않음. |
| User verdict / feedback / Direction Gate §2.3 | 승인/자연어 피드백/사용하지 않음; 외부 평가; 필요 시 새 Run 입력 | 새 업무라면 새 Request/Session/dialogue/specification/Loop | 호환하는 상위 확장. 미래 Session–Run lineage 연결 필요; 기존 run reopen 금지. |
| run / Core, L6, L7 run_id | 효과/예산/evidence를 묶는 실행 identity | Session은 요구 해석과 명세를 포함하는 업무 identity | 같은 이름/identity로 합치면 충돌. 미래 session_id/specification_version과 run_id 연결은 별도 구현; 기존 run_id rename 없음. |
| session / current-session Review transport | 현재 Codex 검수 전달 context | S1의 독립 업무 단위 | 이름 중복. 기존 transport/session 표현을 S1 업무 Session proof로 해석하지 않음. 미래 interface에서 의미 구분 필요. |
| request / Review Request, Work Order | Worker dispatch 또는 내부 Reviewer 입력 계약 | User Request는 업무의 원인 | 이름 중복. 미래 User Request와 Review Request의 type/identity 연결을 명시; 기존 schema 변경 없음. |
| review / L6/L7 | 내부 이미지/geometry 검수와 structured verdict | 고정 Work Specification acceptance criteria에 의한 내부 검수 | 역할 호환. 미래 명세-version/criterion authority를 Review 입력에 연결할 필요; historical verdict는 재판정하지 않음. |
| feedback / L7 controller, C3 revision | 내부 structured REVISE/action의 실행 경로 | User Feedback은 Delivery 이후 외부 평가/새 Request의 원인 | 이름 중복. 내부 correction과 외부 feedback을 구분할 migration 필요; 현재 policy 수정 없음. |
| GEOMETRY_READY / L6 §7 | reviewed inputs로 fresh valid GLB 생성; 품질 PASS/Delivery 아님 | 내부 stage 결과로 사용 가능 | 호환. Session DELIVERED로 자동 승격 금지. |
| GEOMETRY_REVIEWED / L7-M1, INTERNAL_ACCEPT / L7-M2 | 검수 stage 완료 또는 내부 controller 판단; delivery workflow 없음 | 정상 Session 제출 여부는 별도 판단 | 호환. stage terminal을 Session Delivery로 간주하지 않음. |
| ABORT / L7-M3, R1 | 실제 REVISE 후 REVISION_BUDGET_EXHAUSTED; L7 proof NOT PASSED | 실패/중단 history를 Knowledge로 재사용 | 호환. S1으로 L7 VERIFIED 선언/결과 rewrite 금지. |
| BLOCKED_SPECIFICATION_AMBIGUITY / S1 | 기존 Core에 동일 production state 없음 | 현재 Session-level ambiguity 종료 | 새 상위 개념. 미래 Core/Session 종료 연결은 명시적 migration 필요; frozen enum에 추가하지 않음. |

용어 확인에 사용한 기존 경로: [current-session Review transport](../../src/core/result_review_adapter.py), [internal feedback controller](../../src/scenario_a/l7_feedback_controller.py), [C3 internal revision](../../src/scenario_a/c3_revision.py). 이 경로는 read-only로 참조했다.

관련 문서: [L6 contract](../l6/L6_PIPELINE_CONTRACT_v0.md), [L6 actual proof](../l6/L6_M3_ACTUAL_PROOF.md), [L7 geometry bridge](../l7/L7_M1_GEOMETRY_REVIEW_BRIDGE.md), [L7 feedback controller](../l7/L7_M2_FEEDBACK_CONTROLLER.md), [L7 actual proof](../l7/L7_M3_ACTUAL_CLOSED_FEEDBACK_PROOF.md), [L7-R1 diagnosis](../l7/L7_R1_GEOMETRY_REVISION_DIAGNOSIS.md).

L7의 eyes/HY3D relief/body smoothness 등은 이번 User Goal에 대한 authority를 새 명세에서 확정할 수 있다. 기존 판정 당시 criteria를 S1으로 변경하지 않는다. S1은 seed-only policy나 geometry technical diagnosis를 해결하지 않는다.

## 10. Static Consistency Audit

아래는 문서 계약의 정적 검증이다. production 실행이나 actual Reviewer proof를 뜻하지 않는다.

| Case | 입력 / 상황 | 계약에 따른 결과 | 판정 |
|---|---|---|---|
| A | context/reference 없이 “배를 만들어줘” | 중요한 의미가 미확정. dialogue 지속, Ready=false, Loop 미시작 | PASS |
| B | 특정 선박 reference, platform, style이 충분. 일부 detail 미지정 | non-critical detail 추론. 질문을 끝내고 명세 확정, Ready=true, Loop 시작 | PASS |
| C | Loop 중 경미한 미지정 detail, context로 한 방향 결정 가능 | inference 우선순위로 결정하고 동일 Loop 지속 | PASS |
| D | 두 합리적 해석이 artifact 방향을 바꾸며 context로 선택 불가 | 현재 Session을 BLOCKED_SPECIFICATION_AMBIGUITY로 종료. clarification은 새 Request/Session/dialogue/specification/Loop | PASS |
| E | DELIVERED 이후 “몸통을 더 매끄럽게” | old Loop는 종료 유지. 새 ARTIFACT_MODIFICATION Session, 이전 artifact/spec/evidence 재사용과 새 dialogue/spec/Loop | PASS |
| F | facts/results/artifacts/decisions를 새 Frontier에 handoff | active thought trajectory를 전달하지 않고 current Request와 durable Knowledge로 독립 재구성 | PASS |

최종 문서 검사: 신규 Markdown 3개 UTF-8/표 구조/fence/공백 검사 PASS, 상대 repository 링크 16개 모두 존재, 두 template 필수 항목 PASS. 기존 tracked 파일 231개의 SHA-256이 시작 snapshot과 동일하다. Research tracked files 및 F2B WIP 총186개도 SHA-256 동일하다. L6 manifest가 참조하는 external 자산18개는 size/mtime 동일하고, 작은 파일은 SHA-256도 동일하다. 대형 model 전체 hash는 측정하지 않았으며 byte equality를 주장하지 않는다. Production 변경이 없어 full regression을 실행하지 않았다.

## 11. Status / Protection / Stop

S1은 문서 계약의 COMPLETE이며 Session production 구현 완료를 뜻하지 않는다. Core/L6/L7 실행 품질이나 Hypothesis를 새로 증명하지 않는다.

Production source/tests/runs, 기존 docs/l6 및 docs/l7, workflow/model, Research/F2B는 변경 대상이 아니다. S1의 Comfy submissions / Blender processes / Frontier semantic Reviewer invocation / revision dispatch는 모두0이다.

문서3개 → consistency/link/diff/protected-file 감사 → session-contract-s1에 정상 commit/push → clean 확인 후 STOP. main merge/tag/release나 다음 milestone을 시작하지 않는다.

```text
AGENT LOOP CORE V1.0.0 = FROZEN / UNCHANGED
LEVEL 6 MULTI-STAGE SUPERVISED PIPELINE = VERIFIED
L7-M0 MANDATORY GATE = PASS
L7-M1 GEOMETRY REVIEW BRIDGE = VERIFIED
L7-M2 MINIMAL FEEDBACK CONTROLLER = READY
L7-M3 ACTUAL CLOSED FEEDBACK PROOF = NOT PASSED
L7-R1 GEOMETRY REVISION DIAGNOSIS = COMPLETE
S1 SESSION / REQUEST / WORK SPECIFICATION CONTRACT = COMPLETE
LEVEL 7 CLOSED FEEDBACK PIPELINE = NOT VERIFIED
HYPOTHESIS BENCHMARK = NOT STARTED
```
