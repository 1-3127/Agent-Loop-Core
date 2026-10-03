# Specification 전수점검 — 2026-10-04

대상: `RECONSTRUCTION_SPECIFICATION.md` v1 전체 (§1–§15)

판정: **Specification 기준 BLOCKER 0 / 추가 사용자 결정 필요 0**.

이 점검은 사용자 결정과 전역 지침의 일관성에 대한 한 차례의 전수점검이다. 구현 코드, 실제 Scenario A, semantic quality, regression 및 runtime/model 가용성 검증은 수행하지 않았다. reconstruction 또는 production 성공 판정이 아니다.

## 1. 고정한 입력

- Global instruction commit: `c4d7679ff40b4fbfcc959b3bb50cf0d725447c03` / Agents-Profile / Ponytail.
- Project branch/HEAD: `ponytail-reconstruction-codex` / `12366d9f2e377cfda898790f65c5033306905a99`.
- 점검 시 project source tree: clean. 이 점검 전 source 변경 없음.
- Handoff SHA256: `c3d6bf595b1c36096719731017779f5fafc8c05c575e3cff77922c58a9fcd44b`.
- Specification SHA256:

```text
fa1454b38b3dcd2f77b17424f1f0188a745bbeeab32394db1631c42e30598e13
```

적용 지침: Root `AGENTS.md`, `Agents/workflow.md`, `Others/AGENTS.md`, project `AGENTS.md`. history/backup 관련 조건은 Root `Agents/history.md`, `Agents/backup.md`에 대조했다. 전역 Root 밖의 repository 지침이나 memory는 적용하지 않았다.

## 2. 전역 지침 전 항목 대조

| 지침 항목 | Specification 대응 | 점검 결과 |
|---|---|---|
| 지침 scope와 가까운 AGENTS | §1, §14 | 전역 Root 범위 고정. 과거 project scope를 최신 User authority가 대체하는 이유 명시 |
| Goal·명시 제약 보존 | §1–§3, §12 | Python Core+MCP, 독립 역할, 새 branch, Scenario A 실행 준비, 검증 유보 모두 반영 |
| 최소 일관된 변경 | §2, §6–§8, §13 | 기존 compatibility·framework·추측성 일반화 제외. invariant에 필요한 역할만 유지 |
| 기존/native/설치 dependency/새 코드 순서 | §4, §12–§13 | 원래 evidence와 책임 분석을 먼저 사용. stdlib 중심 Core, transport에는 공식 SDK. cloud 구현 재사용 제외 |
| 대체 수단의 material 설계 선택 | §1, §4 | User가 선택한 Python Core+MCP와 독립 branch 유지. 별도 repo/hook을 임의 생성하지 않음 |
| 삭제·축소와 복구 가능성 | §1, §11, §13 | 기존 clean commit/refs 보존. 실제 삭제 전 사용처와 복구 범위 확인은 구현 단계 의무 |
| 검토·설명·진단은 Read-Only | 본 점검 | source/Tool 효과/실제 생산 Session 실행 없음. Specification 문서화만 수행 |
| Critical 변경 승인 | §4, §11 | 파괴적 외부 변경/credential/상주 service 등을 Host 실제 권한에 결합 |
| 버전·API 1차 출처 | §15 | 공식 model/CLI/MCP/ComfyUI 자료와 local metadata 구분 |
| secret 기록 금지 | §4, §9 | credentials 책임은 Host, 로그에는 secret/hidden reasoning 없음 |
| 결과를 바꾸는 모호성 해소 | §9 | Terminal 경계를 직접 질문하고 User의 1번 선택 반영 |
| objective ambiguity는 repository로 해소 | §1, §14–§15 | base commit, cloud refs, 기존 역할/criterion/path/config를 source로 확인 |
| 변경 전 Specification | §13 | 완성된 Specification 전수점검 후 구현 순서 고정 |
| 새 발견은 blocker만 현재 범위 수정 | §13 | material ambiguity만 질문, 나머지는 후속 사항 |
| 반복 실패 그대로 재실행 금지 | §8–§9 | UNRESOLVED effect 관측 전 retry 차단 |
| 위험에 비례한 최소 check | §2, §13–§14 | User의 명시적 검증 유보를 적용. 구현 중 Smoke만 허용 |
| BLOCKER/NON-BLOCKING/FUTURE 구분 | §2, §10, §13 및 본 보고 | Should-Have만으로 실패시키지 않으며 범용성·후속 backend 검증은 FUTURE |
| PASS 주장은 실제 점검 범위 이내 | §2, §12–§15 | config/Smoke/exit 0와 actual proof·semantic acceptance 구분 |
| 진행 기록과 COMPLETE history | §11, §13 | active failures 보존, 완료 경계에서 compact history, 과거 실패 판단 불변 |
| 독립 하위 프로젝트와 실제 경로 확인 | §1, §7, §12 | nested project root 고정, Tool-native 경로 binding 존중 |
| local loopback·외부 공유 비활성 기본값 | §4 | local stdio MCP. 새 외부 server/service 없음 |
| 사용자 작성 파일 보존 | §1, §11 | 과거 proof/refs 및 원본 입력 보존. bulk rewrite/reorder 없음 |
| 모델·도구 배포 조건과 큰 download 기록 | §4, §15 | 현재 큰 download·새 backend 구현 없음. 추가 dependency/asset은 실제 필요 시 해당 지침 적용 |

## 3. 사용자 결정 전 항목 대조

| 결정 | 반영 위치 | 상태 |
|---|---|---|
| cloud 두 구현 제외, 최신 비클라우드 base, 지정 branch | §1 | 확정 |
| 한 개발 Session에서 Scenario A 구현 가능한 상태까지 | §2, §12–§13 | 확정 |
| Python Core+MCP, 다른 Host 교체 경계 | §3–§4 | 확정 |
| 현재 Codex Host / 별도 Codex CLI Frontier | §3 | 확정 |
| model `GPT-6.1-sol low`, Frontier/Reviewer 독립·교체 가능 | §3 | 확정 |
| 정상 restart는 Frontier 아래, 중단 계층별 Frontier/Host 책임 | §8–§9 | 확정 |
| Terminal 미전달은 비정상 종료, Terminal 재실행 금지 | §9 | 마지막 직접 답변 1번 적용 |
| 미전달 Artifact 존재를 Host 또는 Frontier가 안내 | §9–§10 | 마지막 직접 답변 반영 |
| 기준별 Review·mandatory/Should-Have 경계 | §5, §10 | 확정 |
| 최소 Skill 자동 축적/승격 방식 | §6 | 확정 |
| ComfyUI는 Core Workflow 내 Tool/Skill | §6 | 확정 |
| User는 Session 밖 | §3, §5, §10 | 확정 |
| 기존 코드 구체적 검토로 9번 해소 | §5, §7–§10, §14 | 해결된 사항 재질문 없음 |
| Tool-bound 경로 존중, 10번 해소 | §7, §12, §14 | 해결된 사항 재질문 없음 |
| Session 끝에 Frontier/Core가 보존·정리 결정 | §11 | 확정 |
| 12번과 다른 Domain/lower Frontier 검증은 현재 구현 밖 | §2 | 제외 |
| 구현 중 Smoke 허용, 모든 reconstruction 후 공동 검증 | §2, §12–§14 | 확정 |
| Specification 정리 후 한 차례 전수점검 | §13 및 본 보고 | 수행 |

## 4. 충돌과 오해 가능성의 처리

1. **과거 지침의 현재성:** project AGENTS의 Direction Gate/fixed scope 및 옛 Work Specification의 actual proof 명령은 이번 reconstruction과 충돌한다. 최신 직접 User 결정으로 scope를 대체하며 과거 evidence 자체를 수정하지 않는다. 구현 단계에서 active AGENTS/README를 새 scope로 정리한다.
2. **Terminal 의미:** ‘Terminal 미전달’을 같은 Session 복구 대상으로 해석할 가능성이 있었다. User가 1번안을 선택했다. 비종료 중단만 복구하며 Terminal 후에는 안내와 New Session Start만 허용한다.
3. **Review의 nonblocking 기준:** 일부 원래 구현은 모든 applicable outcome MET/PASS를 요구했다. 문서와 User 의도에 맞춰 mandatory 기준만 acceptance blocker로 둔다. 이것은 과거 proof 성공/실패 판정 변경이 아니다.
4. **경로 강제:** 원래 adapter의 Session directory 내부 출력 강제를 새 Core에 가져오지 않는다. Tool의 실제 경로/소유권을 Host가 허용하고 Core는 identity/lineage를 유지한다.
5. **모델 설정:** 원래 project config의 `high`는 새 Frontier/Reviewer runtime 설정으로 재사용하지 않는다. Host 대화 설정은 임의 변경하지 않고 각각 `gpt-6.1-sol` / `low`를 명시한다.
6. **검증 혼동:** 이번 전수점검은 Specification 전체 일관성 점검이다. reconstruction 완료 후 할 실제 검증을 미리 실행한 것이 아니다.

## 5. 남은 항목 분류

- **BLOCKER:** 없음. 결과를 바꿀 미확정 User intent 없음.
- **NON-BLOCKING / 구현 의무:** 실제 asset/path binding, protocol entry, grant ledger, current lineage/mandatory acceptance guard, Terminal notice, 끝난 Session retention, active instruction 정리. 아직 구현 성공을 주장하지 않는다.
- **FUTURE / 공동 검증:** actual Request/Reference로 Scenario A 실행·품질·delivery, 다른 Host 연결, 다른 Domain, lower Frontier 효율, Antigravity/Gemma-4 backend.

결과는 구현 전 Specification 일관성에 한정한다. 다음 경계는 확정된 Specification에 따른 reconstruction이다.
