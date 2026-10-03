# B-01–B-04 implementation report — 2026-10-04

User가 모두 수용한 보완을 `ponytail-reconstruction-codex`에 구현했다.
출발 commit: `6b8dd5ee75050e51d68e019c21958a2cc2ee6871`.
원래 reconstruction base와 클라우드 미사용 원칙은 바꾸지 않았다.
최신 계약은 `RECONSTRUCTION_PROOF_REPAIR_SPECIFICATION.md`다.

| 항목 | 구현 결과 |
|---|---|
| B-01 | 기존 MCP/stdio와 native Comfy HTTP/Blender process 유지. phase/receipt/terminal 오류/부분 output과 UNKNOWN을 구분한다. |
| B-02 | inference 관측과 PREPARED를 같은 transaction에 연결. Core 적용과 완료 marker 원자화. reservation commit 뒤 외부 dispatch. 미완료 판단은 새 inference 차단. |
| B-03 | frozen typed evidence slots와 criterion/file/dependency/lineage/Reviewer invocation binding. acceptance가 binding coverage를 소비한다. 관련 없는 출력 때문에 Review를 일괄 삭제하지 않는다. |
| B-04 | promotion.py 하나/기존 SQLite table 하나. 선택/관측 사용/업무/최종 dependency 기여/전달/원문 평가/Frontier 판단 기록. 자동 일괄 VALIDATED 승격 제거. |

추가 MCP tools는 `loop_assess`와 읽기용 `loop_promotion`이다. 모두 9개다.
Core Domain 분기를 넣지 않았으며 기존 candidate Skills/Tool bindings와 native output 위치를 유지했다.
Host의 local export와 실제 User-facing presentation, User 품질 평가는 별도 사실이다.
실제 전달 미확인 Artifact는 terminal status에서도 안내한다. 전달/평가 이력 추가는 Session 재실행이 아니다.
전역 점수, 사용 빈도 선호, 미사용 벌점, 별도 평가 모델/service/scheduler는 없다.

## 확인한 범위

Python source 10개 구문 parse, import/config/candidate catalog bootstrap 및 MCP stdio handshake/tools inventory Smoke 통과.
기존 SQLite에 Promotion table을 초기화했으며 sessions/grants/promotion rows는 모두 0이다.
정확한 기록과 source hashes: `history/b01-b04-bootstrap-smoke.json`.
소스 diff의 whitespace 확인도 수행했다. actual Session/grant 소비, 모델 inference, Comfy prompt, Blender 실행은 0이다.
이미 수행한 Specification 전수점검은 반복하지 않았다. formal regression/semantic/production 검증도 수행하지 않았다.

## 남은 공동 검증

- actual Scenario A의 end-to-end 품질/필수 기준과 독립 Reviewer 판단.
- 실제 중단 구간에서 원래 Decision/effect 관측과 중복 실행 방지.
- native terminal 실패/부분 효과/미관측 결과의 실제 처리.
- 실제 User 전달, 평가 scope와 Skill reuse 판단의 적합성.
- 다른 Host 또는 대체 local Frontier/Reviewer port 연결.

Smoke는 위 의미를 증명하지 않는다. actual 모델 identity는 미관측이다.
실제 Proof Session은 fresh Request/Reference와 별도 명시적 start grant를 받은 뒤 사용자와 진행한다.
정본 DB와 파일 projection은 서로 다른 commit 경계를 가진다. view 오류/동시 읽기는 revision과 projection_error로 확인하며 view만으로 실행하지 않는다.
terminal state와 원래 proof/실패 판단을 다시 열거나 덮어쓰지 않는다.
