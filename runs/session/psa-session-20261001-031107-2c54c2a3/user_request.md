# Agent Loop — Post-Stabilization Actual Loop Proof

Source: 이번 Codex chat에서 사용자가 직접 제공한 동일 제목의 새 실행 요청 (2026-10-01, Asia/Seoul).
이 파일은 해당 요청의 목적·승인·중단 경계를 기록한 source excerpt 및 요약이다. 전체 원문의 복제라고 주장하지 않는다.

직접 요청의 핵심 문장:

> C-01과 I-03 안정화가 완료된 현재 코드에서 실제 Scenario A Loop를 **새 Session으로 한 번 실행하여**, 현재 architecture가 실제 Worker / tools / semantic Reviewer / bounded correction을 거쳐 `INTERNAL_ACCEPT`까지 도달할 수 있는지 증명한다.

> `NEW SESSION → FROZEN SPECIFICATION → ACTUAL LOOP → INTERNAL_ACCEPT`

> 이번 프롬프트가 actual proof 실행 승인이다.

> `INTERNAL_ACCEPT != DELIVERED`를 유지한다.

현재 기준: D:/VSCODE-WorkSpace/Others/Agent-Loop-Core;
stabilization-i03-namespace-preflight / f212bcdc3749edf96e9e0b68b5cb4e458f9c6770;
clean, local = tracking = live remote. Start Gate 불일치나 regression은 effect0으로 중단한다.

새 branch actual-loop-post-stabilization, 새 Session/Loop/child IDs/binding/records/namespaces.
기존 S3C Request/Reference와 동일 validation objective는 durable reference로 읽되,
이전 active state, Review, artifacts, correction, acceptance를 새 결과로 재사용하지 않는다.
새 Specification Dialogue를 수행하여 현재 intent를 합리적으로 결정한다.
결정적 intent ambiguity가 있으면 BLOCKED_SPECIFICATION_AMBIGUITY로 종료한다.

C-01: 각 blocking criterion을 관측 가능한 지원 stage에 명시적으로 배정하며
unsupported mandatory는 첫 effect 전 실패한다. 새 verifier는 만들지 않는다.
I-03: repository/external/bridge/correction deterministic namespace 전체 사전 검사;
충돌 시 overwrite/delete/suffix/hidden replacement ID/auto-resume 금지.

Checkpoint A에서 Request, References, frozen Specification, applicability, capability,
child plan, runtime/Reviewer/namespace readiness를 기록·commit한다. Generation effects0.
그 후 기존 production run_session(execute=True)을 정확히 한 번 호출한다.
실제 Worker/Comfy/Blender/semantic Reviewer evidence 및 hashes/lineage를 보존한다.
실제 REVISE만 현재 계약의 최대1 bounded correction을 허용한다. 자동 retry0.
PASS hunting, 추가 seed brute force, manual artifact replacement, raw verdict coercion 금지.

source/test 수정0; defect는 evidence를 보존하고 attempt를 종료한다.
INTERNAL_ACCEPT는 production candidate/Session gate로만 생성한다.
성공·실패 모두 evidence integrity, current coverage, historical immutability를 검증한다.
Checkpoint commit과 origin에 정상 push, local/tracking/live equality를 확인한다.
Delivery/DELIVERED/Session delivery closure/fresh Session은 진행하지 않는다.
I-01/I-02 해결과 범용 geometry 품질 증명은 범위 밖이다.

Historical original Request는 별도 original_request_reference.md에 byte-identical 보존한다.
그 안의 과거 실행·Delivery 지시는 이번 승인으로 적용하지 않는다.
