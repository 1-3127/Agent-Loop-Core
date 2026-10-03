# Reconstruction 구현 및 Cleanup 상태 — 2026-10-04

확정된 Specification에 따른 독립 구현과 승인된 active-tree 전환을 적용했다.
**보고 범위는 구현 제공·bootstrap Smoke·cleanup 완료다. 실제 Scenario A 성공이나 정식 검증 완료를 주장하지 않는다.**

## 제공한 구조

- `app/loopcore`: Host-independent Session/grant ledger/Frozen Specification, Artifact/Skill/Workflow,
  bounded Run/Attempt/restart, current lineage, 독립 Review/Frontier Decision, acceptance/terminal/retention 계약.
- Host·Codex model·ComfyUI·Blender·primary-source read adapters, local CLI와 stdio MCP entry.
- Frontier/Reviewer 각각 `gpt-6.1-sol` / `low`, 별도 adapter/calls. 미래 backend는 해당 port에서 교체한다.
- 여섯 candidate Skills와 Scenario A native graph binding 예시. 실제 성공으로 승격하지 않았다.
- active AGENTS/README, Specification, 한 차례 Specification 전수점검, compact HISTORY 및 legacy 복구 manifest.

Scope: 새 Python Core는 이전 runtime이나 cloud reconstruction을 import/hook하지 않는다.
ComfyUI/Blender native 경로는 config/adapter에서 관리한다. Core에는 Domain별 실행 분기나 model name이 없다.

## 승인된 Cleanup

User가 광범위한 이전 버전 삭제와 지침 덮어쓰기 등 모든 reconstruction Cleanup을 직접 승인했다.
이전 tracked tree 1,841개 파일을 제거하고 AGENTS/README를 전환했다.
오래된 gitattributes 규칙과 중복 README 초안을 제거하고 local/generated state ignore 정책을 정리했다.
원래 branch/refs/history, global instructions, Host config 및 외부 Tool files는 변경하지 않았다.

복구 기준: `12366d9f2e377cfda898790f65c5033306905a99`.
파일별 복구 목록: `history/legacy-tree-manifest.json`. 적용 결과: `history/cleanup-result.json`.
두 번의 과거 자동 승인 거절은 명시적 User 승인으로 해소되었고, 현재 cleanup 승인 BLOCKER는 없다.

## Smoke 및 실제 실행 경계

- Python compile/import와 CLI help.
- config/catalog bootstrap: 여섯 candidate Skills.
- 실제 local MCP stdio handshake/tool inventory: 7개 tools, negotiated protocol `2026-07-28`.
- cleanup 후 이전 source가 없는 상태에서 bootstrap 재확인 통과.

```text
Session 시작 0 / grant 소비 0 / 모델 호출 0
ComfyUI prompt 0 / Blender 호출 0
```

정식 tests/regression, lifecycle/failure/recovery, 실제 model identity/가용성,
Scenario A 생성·semantic acceptance·delivery는 수행하지 않았다. 전체 reconstruction 뒤 사용자와 함께 진행한다.
ComfyUI segmentation Skill은 candidate knowledge이며 SAM3 UI blueprint를 실행 가능한 API graph로 간주하지 않는다.
해당 전처리가 필요하면 native graph/capability를 binding해야 한다.

구현을 actual proof로 해석하지 않으며, actual Session 시작에는 별도의 명시적 User start grant가 필요하다.
공개 push는 수행하지 않았다.
