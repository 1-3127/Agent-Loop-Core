# B-01–B-04 accepted repair specification — 2026-10-04

직접 User의 ‘모두 수용한다’를 근거로 B-01–B-04 보완을 구현한다.
기준 source는 `6b8dd5ee75050e51d68e019c21958a2cc2ee6871`이다.
`RECONSTRUCTION_SPECIFICATION.md` v1과 한 차례 수행한 audit는 당시 기록으로 보존한다.
이 문서는 v1의 일괄 VALIDATED 승격 및 독립 Promotion 제외를 대체하는 최신 결정이다.
그 외 frozen authority, 예산, 독립 Reviewer, terminal 재실행 금지와 Smoke-only 범위는 유지한다.

## B-01: native evidence classification

Host → MCP/stdio → Runtime/Core → Tool adapter → native API/process를 사용한다.
추가 wrapper, watcher, 중계 service, 서버 patch, 필수 client prompt UUID는 없다.
ComfyUI는 server-issued prompt ID와 original receipt/history를 사용한다. ID는 중복 제거 권한이 아니다.

- production dispatch 이전 검증 실패: FAILED, `execution_observed=false`. staging 파일은 남을 수 있다.
- 구조화된 native prompt 검증 거절: FAILED, rejection JSON 보존.
- original history의 error/interrupted: FAILED. completed=false만으로 running이라고 판단하지 않는다.
- 원래 process 종료 관측 + exit/traceback/output 오류: FAILED. 부분 효과 가능성은 별개로 보존한다.
- 성공 종료 및 기대 output refs/현재 bytes 확인: Tool SUCCESS. semantic ACCEPT나 User 호평이 아니다.
- 제출 응답 유실, history 부재, 관측하지 못한 process 결과: UNRESOLVED. 자동 재제출하지 않는다.

ticket에 dispatch claim, native phase, prompt/process receipt, terminal history 및 output refs를 연결한다.
HTTP 코드나 임의 exception 문자열만으로 원래 실행 여부를 확정하지 않는다.

## B-02: durable Decision application Rule

Frontier 결과와 Decision PREPARED를 같은 SQLite transaction에서 보존한다.
`application={ticket_id,phase,value,effect_ticket_id}`를 현재 state와 history의 적용 표시에 연결한다.
phase는 PREPARED/APPLYING/APPLIED/REJECTED다.

Core-only 변경은 적용 표시와 같은 transaction이다. CREATE_SKILL/Promotion 기록도 이 transaction에 참여한다.
Tool/Reviewer reservation은 원래 Decision에 연결하여 commit한 뒤 native dispatch/inference를 수행한다.
관측 결과와 출력/Review 등록 및 적용 완료 표시는 같은 transaction이다.
중간에 중단되면 pending/application guard가 다음 inference를 차단한다.
UNRESOLVED 관측은 적용이 끝난 결과이지만 원래 effect가 미해결이라는 별도 사실로 남는다.

하위 effect 중단의 판단자는 Frontier이고 Host에 올릴 수 있다. Frontier 또는 Host dispatch 중단은 Host가 판단한다.
trusted Host receipt의 APPLY_DECISION은 **정확한 PREPARED Decision만** 적용하며 새 inference를 만들지 않는다.
REJECT_DECISION은 미dispatch 판단을 명시적으로 거절한다. APPLYING effect는 원래 ticket 결과만 관측한다.
터미널 Session에서 어떤 recovery action도 실행을 재개하지 않는다.

SQLite가 정본이다. revision-bound state.json, specification.json, run/attempt evidence.json,
Review JSON, promotion.json과 summary.md는 읽기용 projection이다. 현재 view는 status/edit에서 갱신·복원한다.
file projection은 DB와 원자적으로 commit되지 않는다. DB commit 후 view 오류가 나도 이미 적용된 효과를 재실행하지 않는다.
status는 `projection_error`로 남은 오류를 드러낸다. 외부 소비자는 SQLite/revision과 binding을 확인한다.
새 scheduler/background service 또는 별도 .unfin 정본을 만들지 않는다.

## B-03: frozen typed evidence slots

Criterion은 기존 필드에 `evidence_slots:{logical_slot:artifact_type}`를 추가한다.
artifact_types는 evidence_slots의 type 집합과 같아야 한다.
슬롯 이름과 증거 요구는 freeze 때 Frontier가 정한다. Workflow의 stage outputs와 diagnostics가 같은 논리 슬롯을 생산한다.
Core에 특정 Domain의 front/right/left/back 또는 이미지/3D 판단을 넣지 않는다.

```json
{"id":"view-consistency","description":"...","mandatory":true,
 "artifact_types":["view"],
 "evidence_slots":{"front":"view","right":"view","left":"view","back":"view"}}
```

Review 슬롯은 선택된 criterion들의 필수 슬롯 합집합과 같아야 한다. 부분/미결합 evidence는 거절한다.
binding은 criterion ID, spec/Workflow hash, Run/Attempt, slot/Artifact ID/file hash, dependency refs와 실제 Reviewer invocation을 보존한다.
Reviewer context에 binding과 실제 입력을 전달하고 Core가 다시 확인한다.
ACCEPT는 유효한 현재 binding의 마지막 criterion outcome, mandatory MET 및 final Artifact의 binding coverage를 확인한다.
추가 무관 output 때문에 Review를 삭제하지 않는다. 변경된 evidence/dependency와 이전 Run/Attempt의 Review는 현재 acceptance에서 제외한다.
역사적 Review와 실패는 보존한다. Run/Attempt의 checkpoint adoption은 기존 명시적 restart_from/동일 preceding stage 계약이다.
Tool output과 큰 Artifact의 native 경로는 이동하지 않는다.

## B-04: compact factual Promotion

`promotion.py` 하나와 기존 SQLite의 `promotion` table 하나를 사용한다.
selection/reservation, 실제 관측 사용 또는 불명확 상태, task/spec/Workflow/run/attempt/stage,
Skill ID/version/hash, invocation/output refs, 최종 Artifact dependency를 통한 참여를 기록한다.
최종 Workflow 참여는 실제 성공한 producer ticket에서 추출한다. 선택된 모든 Skill에 성공을 부여하지 않는다.
NO_RECORDED_USE는 현재 ledger 범위의 미사용이며 불량을 뜻하지 않는다.
Frontier의 PROMOTION action은 업무별 판단/이유를 기록한다. 전역 점수/ranking, 빈도 선호 및 자동 VALIDATED 일괄 승격은 없다.

Host inbox `assessments/<receipt-id>.json`의 DELIVERY/USER_FEEDBACK을 `loop_assess`로 기록한다.
공통 필드: `{owner:"HOST",session_id,kind,scope}`.
DELIVERY: scope `{kind:"ARTIFACT",artifact_ids:[...]}`, 실제 User-facing presentation의 immutable FileReference `presentation`.
USER_FEEDBACK: scope는 ARTIFACT(ids), WORKFLOW(workflow_hash), SKILL(skill ID/version/hash) 중 하나,
`text`는 원래 User record와 정확히 같으며 `user_evidence`로 연결한다.
Workflow/Artifact 호평을 모든 참여 Skill의 개별 평가로 확장하지 않는다.
local handoff는 LOCAL_EXPORT이며 User 실제 전달/품질 승인이 아니다.
terminal 실행 상태를 유지한 채 Host 이력만 추가한다. 실제 전달 미확인 refs는 status에서 안내한다.

## 실행 경계

현재 구현 중 허용된 확인은 syntax/import/config/catalog/MCP bootstrap Smoke뿐이다.
ACTUAL Session/grant 소비, 모델/ComfyUI/Blender 호출, 장애 주입, regression/semantic/production 검증은 하지 않는다.
이 문서는 새로운 전체 지침 전수점검 또는 실제 Proof 결과가 아니다.
actual Scenario A, 실제 interruption 복구, Reviewer coverage 및 User 전달/평가는 사용자 공동 검증 단계에 남는다.
