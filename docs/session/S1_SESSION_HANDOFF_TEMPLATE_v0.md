# S1 Session Handoff Template v0

## 사용 규칙

[Session Contract v0](S1_SESSION_CONTRACT_v0.md)의 Durable Knowledge 전달 양식이다. Session 종료 후 다음 Session이 필요한 결과와 근거를 재사용하도록 작성한다. 이전 active reasoning state를 복원하는 startup prompt가 아니다.

각 기록은 FACT / RESULT / DECISION / CONSTRAINT / UNKNOWN의 성격과 evidence를 구분한다. 추론은 [추론]이며 verified fact로 승격하지 않는다. 해당하지 않는 항목은 [] 또는 null과 이유를 사용한다. 과거 자료에 Session identity가 없으면 새 historical session_id를 꾸며내지 않는다.

## 1. Previous Session / Request / Specification

- previous_session_id: <이전 identity; 미기록이면 null>
- previous_request: <확정 요청 요약과 원 Request ref>
- previous_final_specification: <path/ref, version, identity/hash가 있으면 포함>
- previous_session_outcome: <DELIVERED/CLOSED/BLOCKED_SPECIFICATION_AMBIGUITY/FAILED/ABORT 또는 미기록>
- previous_loop_run_refs: <실행 run_id/terminal/evidence ref; 없으면 []>
- closure_reason: <제출/명세 모호성/예산/실패의 확정 사유>

Conceptual Session outcome과 historical Core/L6/L7 run state를 구분한다. GEOMETRY_READY/GEOMETRY_REVIEWED/INTERNAL_ACCEPT만으로 DELIVERED를 선언하지 않는다. 과거 verdict/terminal record를 rewrite하지 않는다.

## 2. Delivered Artifacts

| artifact_id / path or URI | kind / format | bytes / SHA-256 if measured | delivery_reference | related_specification / run |
|---|---|---|---|---|
| <실제 사용자 제출된 artifact만> | <type/format> | <측정값 또는 null + 이유> | <실제 제출 근거> | <명세/실행 refs> |

- delivered_artifacts: <없으면 []>
- other_reusable_artifacts: <ABORT/FAILED/candidate/debug artifact는 별도 분류하여 identity/evidence와 함께 기록; 없으면 []>
- original_input_references: <다음 시각적 User 판정 시 함께 제시할 최초 Input identity/path>

ABORT/FAILED artifact를 정상 Delivered Artifact로 포장하지 않는다.

## 3. User Feedback / Explicit Preferences / Constraints

- user_feedback: <원문 의미와 source ref; 없으면 []>
- explicit_user_preferences_constraints: <최종 확인된 선호/제약과 적용 범위/근거; 없으면 []>
- prospective_request_type: <새 업무가 있으면 NEW_WORK / ARTIFACT_MODIFICATION / FOLLOW_UP / RESTART_AFTER_AMBIGUITY; 아직 없으면 null>

Feedback은 외부 평가다. 새 업무의 input으로 사용할 수 있지만 old Loop REVISE나 종료 Session reopen을 뜻하지 않는다. User 승인 자체를 내부 품질 proof나 technical verification으로 승격하지 않는다.

## 4. Verified Facts / Measurements / Tests

| fact_id | verified_fact / measurement / test_result | evidence_reference | observed_at / applicable_scope |
|---|---|---|---|
| `<F1>` | <확정된 관측/측정/검증 결과> | <path/ref와 hash가 있으면 포함> | <관측 시점, 적용 범위, 실제/fixture/replay 구분> |

- verified_facts: <없으면 []>
- confirmed_technical_findings: <근거 있는 technical finding만; 없으면 []>

기존 fixture PASS, historical actual execution, 현재 actual observation은 서로 구분한다. 두 candidate가 모두 REVISE였다는 사실은 보존할 수 있으나 원인 미확정 hypothesis를 fact로 옮기지 않는다.

## 5. Execution Results / Known Failures

| run / invocation identity | execution_result | artifact / report / review refs | known_failure / limitation |
|---|---|---|---|
| <기존 run/prompt/process identity> | <실제 성공/실패/미확인과 terminal> | <근거 refs> | <확인된 실패/한계; 없으면 null> |

- execution_results: <없으면 []>
- known_failures: <재사용 판단에 필요한 확정 실패/조건; 없으면 []>

실제 Reviewer verdict와 execution success를 구분한다. 성공한 Worker/API 호출은 semantic PASS의 근거가 아니다. 원인과 결과 관계가 미확정이면 그렇게 표시한다.

## 6. Final Decisions / Unresolved Issues

| final_decision | scope | evidence_reference / concise_confirmed_basis |
|---|---|---|
| <확정된 최종 결정> | <적용 범위/후속 조건> | <근거 ref와 필요한 짧은 이유> |

- final_decisions: <없으면 []>
- unresolved_issues: <미확인 사항/다음 결정/조사가 필요한 범위와 근거; 없으면 []>
- ambiguity_record: <모호성 종료인 경우 해석 후보, artifact 영향, context로 결정 불가한 이유, 필요한 clarification; 아니면 null>

미승인 proposal/experiment는 실행 사실이나 확정 correction policy로 기록하지 않는다. 최종 결정과 근거는 보존하되 가설이 떠오른 순서/사고 변화 chronology를 기록하지 않는다.

## 7. Relevant Environment / Tool State

| environment_or_tool | confirmed_state | observed_at | evidence_reference | needs_current_verification |
|---|---|---|---|---|
| <관련 tool/runtime/version/asset> | <관측된 상태; 미확인은 null> | <시점> | <근거> | <true/false와 이유> |

- relevant_environment_tool_state: <없으면 []>

현재 실행에 필요한 환경은 관련 사실의 변동 가능성과 확인 비용을 고려하여 현재 상태를 확인한다. 과거 available 상태를 현재 보장으로 선언하지 않는다. credentials/secret 값을 기록하지 않는다.

## 8. Evidence References / Lineage / Archive

- evidence_references: <필요한 path/URI, 역할, identity/hash와 evidence 성격; 없으면 []>
- lineage: <Request → Specification → Run/Work Order → Execution → Artifact → Review → terminal/delivery, 실제 존재하는 연결만>
- archive_references: <필요 시 특정 evidence 조회용 raw logs/transcript refs; 없으면 []>

이전 artifact/specification/evidence를 재사용할 수 있다. 로그/역사를 삭제하거나 매번 처음부터 생성하지 않는다. Archive 전체를 기본 startup context에 자동 주입하지 않는다.

## 9. Explicitly Excluded Context

이 pack에는 다음을 포함하지 않는다.

- full thought transcript
- hidden/internal chain-of-thought
- chronological speculation log / moment-to-moment hypothesis transitions
- prior active reasoning state / previous mental trajectory
- uncommitted intuitions / conversational inertia

새 Frontier는 이전에 일어난 일과 근거를 알 수 있으나 이전 Frontier의 생각 흐름을 이어받아 판단을 시작하지 않는다.

## 10. Fresh Session Startup Checklist

1. Current User Request를 읽는다.
2. Current References를 확인한다.
3. Relevant Durable Knowledge를 선택한다.
4. 해당하는 previous Delivered Artifact / Specification을 참조한다.
5. 해당하는 User Feedback을 읽는다.
6. Frontier가 독립적으로 현재 목표를 해석한다.
7. User↔Frontier Specification Dialogue를 수행한다.
8. [새 Work Specification](S1_WORK_SPECIFICATION_TEMPLATE_v0.md)을 작성하고 Ready Gate를 확인한다.
9. Ready=true 및 blocking ambiguity 없음이면 새 Loop를 시작한다.

모든 새 Session은 이 순서를 따른다. Handoff pack은 새 Request나 새 명세를 대신하지 않는다. 불필요한 질문 없이 충분한 context를 확인할 수 있다. ambiguity clarification이나 artifact 수정도 새 Session이며 old Loop를 재개하지 않는다.
