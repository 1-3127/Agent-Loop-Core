# Immutable origin and reconstruction history

## Historical source

기존 active tree는 새 runtime에 연결하지 않는다. exact source/proof bytes는 다음 Git commit/refs에서 복구한다.

- [출발 tree](https://github.com/1-3127/Agent-Loop-Core/tree/12366d9f2e377cfda898790f65c5033306905a99): 기존 src/tests/docs/skills/proof hosts와 원래 AGENTS/README.
- `core-v1.0.0` / `7eee393801f4d8c14278b43ebcbaabaec7ccc9df`: 기존 C1–C5 frozen baseline.
- `fresh-session-refresh-proof-final-3` / `001db7e1377c2b291632d2a80746860cb15d7dcd`: actual proof는 ABORT / REVISION_BUDGET_EXHAUSTED 및 semantic closure failure. regression 보고를 actual 성공으로 바꾸지 않는다.
- 출발 tree의 `docs/adaptive/FINAL_REPORT.md`: 실제 stone-lantern 성공과 synthetic adaptive restart 증거를 구분한다. 실제 workflow revision/restart 0. model identity 미관측. local delivery와 human receipt 구분.
- 클라우드 `ponytail-loopcore-rebuild-02` / `426b1f93b08fe39722ce61b0be3a3a830f4f9ca5`: 이번 reconstruction에서 코드·tests·runtime dependency 사용 0.

복구 예시(현재 tree를 변경하지 않는 읽기): `git show 12366d9f2e377cfda898790f65c5033306905a99:src/core/adaptive_loop.py`.
원래 refs/history를 삭제하거나 proof bytes/판정을 수정하지 않는다.

## 2026-10-04 — Specification boundary COMPLETE

목표: handoff와 직접 User 결정을 수집하여 새로운 독립 reconstruction Specification을 정리한다.
결과: model `gpt-6.1-sol`/`low`, 독립 Frontier/Reviewer, ComfyUI Tool/Skill, Tool 경로 존중, Session 끝 보존/정리,
Terminal 재실행 금지 및 미전달 Artifact 안내 확정. 전역 지침에 따른 Specification 전수점검 한 차례 수행, Specification BLOCKER 0.
실행/검증 범위: 원래 source/문서와 branch/base 및 공식 자료 read-only review. 실제 production Session/Tool/모델 호출 없음.
중요 교훈: ‘terminal 미전달’과 ‘같은 Session 복구’를 혼동하지 않는다. User의 마지막 1번 선택으로 비종료 중단만 복구한다.
후속: 독립 구현 후 사용자와 actual 검증. 과거 fixed scope/proof 실행 명령은 새로운 개발 권한이 아니다.

## 2026-10-04 — Independent active-tree transition COMPLETE

목표: 승인된 지침 전환과 이전 버전 cleanup으로 독립 active tree를 확정한다.
결과: 기존 tracked source/docs/proof/tests 등 1,841개 파일을 working tree에서 제거하고
AGENTS/README를 reconstruction scope와 새 entry로 전환했다. 오래된 gitattributes 규칙 및 중복 초안도 정리했다.
복구: 출발 commit `12366d9f2e377cfda898790f65c5033306905a99`, 원래 refs,
`history/legacy-tree-manifest.json`의 path/Git blob 목록. 원래 proof bytes와 실패 판정은 원본 commit에 그대로 보존했다.
결정: User가 광범위한 이전 버전 삭제·지침 덮어쓰기 등 모든 reconstruction Cleanup을 명시적으로 승인했다.
전역 지침·현재 Host config·외부 Tool files는 변경하지 않았다. runtime은 app/loopcore만 사용한다.
Smoke: 이전 source가 없는 상태에서 CLI/config/catalog bootstrap 통과. 앞선 MCP stdio inventory도 7개 tool을 제공했다.
actual Session/grant/모델/ComfyUI/Blender 효과 0. 정식 및 semantic 검증은 사용자 공동 단계로 유보한다.
실패/redirect 교훈: 처음 두 자동 승인 심사는 광범위 삭제 및 지침 덮어쓰기의 명시적 승인 부족으로 거절했다.
기존 파일을 보존한 독립 package 추가와 review diff/manifest 준비를 먼저 마쳤고, 직접 User 승인 후 cleanup을 적용했다.
후속: 실제 Scenario A·recovery·quality·delivery 및 다른 Host/Domain/모델 교체 검증. cleanup은 production proof가 아니다.
