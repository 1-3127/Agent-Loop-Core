# S1 Work Specification Template v0

## 사용 규칙

[Session Contract v0](S1_SESSION_CONTRACT_v0.md)에 따라 User↔Frontier Specification Dialogue의 최종 결과를 아래에 간결하게 기록한다. 새 작업/수정/후속/ambiguity 재시작마다 새 Session과 명세를 작성한다. 이전 명세의 복사만으로 dialogue를 생략하지 않는다.

아래는 문서 작성 양식이며 production JSON/DB schema가 아니다. `<...>`는 이번 업무의 최종 값으로 채우고 해당하지 않는 목록은 비운다. null/unknown에는 관련성이나 미측정 이유를 남긴다. 모든 빈칸을 User 질문으로 채울 필요는 없다. 결과 방향을 바꾸는 decision-critical ambiguity만 질문한다.

## 1. Identity / Lineage

- session_id: <이번 업무 identity; 기존 run_id와 구분>
- specification_version: <이번 Session의 명세 version>
- request_type: <NEW_WORK / ARTIFACT_MODIFICATION / FOLLOW_UP / RESTART_AFTER_AMBIGUITY 중 하나>
- previous_session_id: <없거나 historical 자료에 없으면 null; 생성하지 않음>
- lineage: <이전 Request/Session/Specification/Artifact/Feedback/evidence refs; 없으면 []>

## 2. User Goal

- original_request_summary: <원문 의도를 간결하게 요약; 필요하면 원 Request ref>
- desired_outcome: <사용자가 얻으려는 결과>
- project_background_context: <판단에 필요한 프로젝트/배경>

## 3. References

필요한 Reference마다 한 항목을 작성한다. 이전 명세와 artifact도 이번 Request에 대한 역할/authority를 다시 해석한다.

| reference_id / path or URI | role | authority | purpose | what_must_be_preserved | what_may_be_interpreted |
|---|---|---|---|---|---|
| <ref / identity 또는 hash가 있으면 함께> | <source/reference/previous artifact 등> | <구조/색상/스타일/문자 등의 확정 근거 또는 inspiration> | <이번 목표와의 관계> | <필수 보존 범위> | <Frontier의 해석 허용 범위> |

보이는 모든 요소가 자동 acceptance criterion이 되는 것은 아니다. authority가 충돌하고 context로 우선순위를 정할 수 없으며 결과 방향을 바꾸면 blocking ambiguity로 남긴다.

## 4. Intended Use

- intended_use: <mobile / PC / VR / VP / VFX / concept / prototype / production / 기타>
- use_context: <artifact 판단에 필요한 사용 조건; 무관하면 unknown/irrelevant와 이유>

## 5. Deliverables

| deliverable_id | type | format | quantity | supporting_outputs |
|---|---|---|---|---|
| `<D1>` | <image/mesh/document 등> | <필요한 형식> | <수량> | <필요한 보조 자료; 없으면 []> |

## 6. Must-Have

- <MH1: 반드시 충족할 요구; User 결정/Reference authority와 연결>

## 7. Should-Have

- <SH1: 가능하면 달성할 요구; 단독으로 REVISE blocker가 되지 않음; 없으면 []>

## 8. Non-Goals / Out of Scope

- <이번 Session이 하지 않는 작업/품질 확장; 없으면 []>

## 9. Acceptance Criteria

실제 Reviewer PASS/REVISE 기준이다. 정밀도는 Goal과 Intended Use에 필요한 수준으로 정한다. 무관한 benchmark나 개선 목표를 추가하지 않는다.

| criterion_id | requirement / acceptable condition | authority / Must-Have ref | verification_evidence | blocking_when_unmet |
|---|---|---|---|---|
| `<AC1>` | <관측/판정 가능한 충족 조건> | <Request/확정 User 결정/authoritative Reference 및 MH1> | <artifact/진단/검수 방식> | <true/false와 필요한 이유> |

- PASS: 위 고정 criteria를 충족하고 BLOCKER가 없음.
- REVISE: 고정 criteria를 만족하지 못하는 BLOCKER가 있음.
- non-blocking/Should-Have/future 항목만으로 REVISE하지 않음.
- 실제 budget/authorization과 terminal 처리는 해당 실행 계약을 따름. User external evaluation은 internal Review가 아님.

## 10. Constraints

각 항목은 이번 업무에 관련된 최종 값/근거 또는 unknown/irrelevant와 이유를 기록한다. 기술 구현 선택은 Frontier가 맡는다.

- deadline: <일정 또는 null + 이유>
- loop_budget: <Worker/Reviewer/iteration 등 실제 effect 이전에 고정할 명시적 상한>
- cost: <관련 비용 제약 또는 null + 이유; 추정치를 측정값으로 기록하지 않음>
- hardware_software_runtime: <실행 환경 제약 또는 해당 없음>
- performance: <사용 목적에 필요한 성능 제약 또는 해당 없음>
- format_compatibility: <형식/호환성 조건 또는 해당 없음>
- legal_or_usage_constraints: <해당하는 경우 확정 조건; 무관하면 해당 없음>
- other_important_constraints: <추가된 중요한 조건만; 없으면 []>

## 11. Interpretation Envelope

- frontier_may_decide: <명세 안에서 추론/선택 가능한 비핵심 detail과 기술 선택>
- preserved_boundaries: <Goal/Must-Have/Acceptance/Reference authority의 변경 불가 범위>
- resolved_interpretations: <채택된 최종 해석과 필요한 짧은 근거; 추론은 [추론] 표시>

Loop 중 미지정 detail은 Current Work Specification → Original Request → Authoritative References → 확정 dialogue context → Durable inherited Knowledge → Current Evidence 순서로 판단한다. 합리적인 한 방향이면 결정하고 계속한다. 중요 모호성으로 단일 해석이 불가능하면 현재 Session을 BLOCKED_SPECIFICATION_AMBIGUITY로 종료하고 clarification은 새 Request/Session에서 수행한다.

## 12. Explicit User Decisions

| decision | scope / authority | source_reference |
|---|---|---|
| <확정된 User의 선택/선호/제약; 없으면 행 없음> | <적용 범위> | <원문/대화의 필요한 근거 ref> |

Frontier의 추론을 User의 명시적 결정으로 적지 않는다.

## 13. Known Unknowns

| unknown | classification | safe_handling / relevance |
|---|---|---|
| <남은 미확인; 없으면 행 없음> | <NON_CRITICAL / INFERABLE / FUTURE> | <안전한 추론/범위 제외/후속 확인 이유> |

decision-critical ambiguity는 여기에 숨기지 않고 아래 readiness의 unresolved_blocking_ambiguities에 기록한다.

## 14. Readiness

- SPECIFICATION_READY: <true / false>
- readiness_reason: <충분한 context 또는 남은 blocker의 이유>
- unresolved_blocking_ambiguities: <없으면 []; 있으면 해석 후보/결과 영향/필요한 User 결정>

Gate 확인:

- [ ] Goal을 이해할 수 있다.
- [ ] References의 역할/authority를 이해할 수 있다.
- [ ] Intended Use가 충분히 이해되거나 현재 판단에 무관함이 설명된다.
- [ ] Deliverable을 정의할 수 있다.
- [ ] Must-Have를 정의할 수 있다.
- [ ] Acceptance Criteria를 정의할 수 있다.
- [ ] 중요한 constraints가 알려져 있다.
- [ ] 남은 ambiguity를 합리적으로 추론하거나 scope 밖으로 정리할 수 있다.

모든 항목 충족과 blocking ambiguity 없음일 때만 true다. false면 Specification Dialogue를 계속하고 Loop를 시작하지 않는다. User 미지정 detail 모두에 답을 요구하지 않는다.

## 15. Loop Start Freeze / Delivery Boundary

Loop 시작 시 이 session_id/specification_version과 확정 내용은 immutable하다. Plan/Work Order는 해당 명세 범위에서 파생하고 결과에 맞춰 criteria를 rewrite하지 않는다. 계약 밖 변경은 새 Request/Session이다.

INTERNAL_ACCEPT 후 실제 제출 시 DELIVERED/Session close다. 시각적 판정 요청에는 최초 Input과 최종 Output을 함께 제시하고 승인 / 자연어 피드백 / 사용하지 않음을 요청한다. User feedback은 외부 평가이며 old Loop의 REVISE나 재개 조건이 아니다.

이 명세에는 필요한 최종 facts/decisions/constraints/acceptance/authority만 기록한다. full thought transcript, hidden/internal chain-of-thought, chronological speculation, prior active reasoning state를 포함하지 않는다.
