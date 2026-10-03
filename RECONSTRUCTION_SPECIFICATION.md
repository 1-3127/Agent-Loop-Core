# Agent-Loop-Core Reconstruction Specification v1

상태: 사용자 결정 수집 완료 / 구현 전 Specification 정본
작성일: 2026-10-04 (Asia/Seoul)

## 1. 권한과 기준점

이 문서는 사용자의 reconstruction handoff와 이 Codex 대화에서 확정한 후속 결정을 합친 개발 Specification이다. 과거 Work Order에 포함된 실행 명령은 이번 작업의 실행 권한이 아니다. 직접적인 최신 사용자 결정이 handoff와 과거 프로젝트 범위를 우선한다.

- 세션 전역 Root: `D:\VSCODE-WorkSpace\Others\Ponytail-Proof`.
- 프로젝트: `D:\VSCODE-WorkSpace\Others\Ponytail-Proof\Others\Agent-Loop-Core`.
- 프로젝트 지침으로 취급하는 파일은 전역 Root의 하위 파일뿐이다. 상위 workspace, 다른 checkout, memory의 프로젝트 규칙을 추가하지 않는다.
- 전역 지침 기준: Agents-Profile / Ponytail / `c4d7679ff40b4fbfcc959b3bb50cf0d725447c03`의 `AGENTS.md`, `Agents/workflow.md`, 해당 작업에 적용되는 `Others/AGENTS.md`, 완료 경계의 `Agents/history.md` 및 필요한 경우 `Agents/backup.md`.
- reconstruction branch: `ponytail-reconstruction-codex`.
- 출발 commit: `12366d9f2e377cfda898790f65c5033306905a99`.
- 출발 commit은 클라우드 reconstruction 두 개를 제외한 가장 최근 수정 commit으로 확인했다. `ponytail-loopcore-rebuild`는 같은 commit을 가리키며 독립 구현 commit이 없다. `ponytail-loopcore-rebuild-02`의 `426b1f93b08fe39722ce61b0be3a3a830f4f9ca5`는 사용하지 않는다.
- 클라우드 구현 코드, 설계 구현체, tests는 복사·import·cherry-pick하지 않는다. 원래 비클라우드 코드도 invariant에 필요한 부분만 선택적으로 재사용한다.
- 새 branch의 active tree는 사실상 새 독립 repository로 취급한다. 기존 runtime에 hook을 걸거나 기존 src를 runtime dependency로 삼지 않는다. Git history와 원래 refs를 복구 근거로 보존한다.
- 새 remote, 별도 repository, 공개 push, 기존 refs 삭제 또는 history rewrite는 이번 작업에 포함하지 않는다.

handoff 원본: `C:\Users\Worker\.codex\attachments\b762c29a-ab32-4aed-84de-c086b87dcea9\붙여넣은 텍스트.txt`.

## 2. 목표, 완료 경계, 제외 범위

하나의 현재 Codex 개발 대화 안에서, 일관된 Python Core + MCP 구조를 reconstruction하고 Scenario A를 실행할 수 있는 상태까지 구현한다. 현재 개발 대화와 Core가 관리하는 개별 작업 Session은 별개다.

개발 결과는 다음을 갖춘다.

1. Host와 Domain에 독립적인 Session, Frozen Specification, Skill, Workflow, Artifact, Review, Decision 계약.
2. User authority를 가진 Session start와 단일 사용 grant 소비.
3. 독립된 Frontier와 Reviewer, 교체 가능한 model adapter, Worker/Tool execution adapter.
4. bounded adaptive loop, Run/Attempt 구분, 명시적 restart point, 필요한 checkpoint 및 lineage.
5. Scenario A의 실제 Tool 경로를 이용할 수 있는 adapter와 Skill/Workflow 자료, 실행 entry 및 delivery 경계.
6. Session 종료 시 보존/정리 판단과 최소 durable evidence, 실패 관찰 정보.
7. 새 active tree만으로 실행되는 구성, 설치/실행 안내, compact history 및 과거 proof의 immutable ref index.

구현 중 Smoke check는 허용된다. 실제 사용자 Request/Reference로 생산 Session을 시작하거나, semantic acceptance·actual E2E proof·정식 regression·범용성·자원 절감 효과를 검증하지 않는다. 모든 reconstruction이 끝난 뒤 사용자와 함께 검증한다. Smoke 결과를 production proof 또는 Skill 검증 성공으로 승격하지 않는다.

다른 Domain, Blender Scene, Video, lower-capability Frontier 비교, 다른 Host의 실제 연결 및 Antigravity/Gemma-4 backend 구현은 이번 구현 범위에서 제외한다. 교체 경계만 둔다. 새 framework, scheduler, 상주 background service, 범용 DAG DSL, 포괄적 hardening 또는 독립 promotion subsystem은 만들지 않는다.

## 3. 역할과 책임

| 역할 | 책임 | 권한 경계 |
|---|---|---|
| User | Request/Reference, Goal, 결정적 의도 모호성 해소, 새 Session 시작 허가, 전달 후 평가 | internal loop 밖에 존재 |
| Host | 실제 User provenance, grant 발급, runtime/account, filesystem/network/process, credentials, permissions/sandbox, delivery | Core 밖의 실제 효과 권한을 관리 |
| Core | 신뢰된 grant 검증·소비, Session lifecycle, frozen authority, lineage, budget, Workflow/Skill/Artifact/Review/Decision 보관 및 transition guard | User origin을 스스로 증명하거나 credentials/Host transcript를 해석하지 않음 |
| Frontier | Skill 발견/작성/조합, Workflow 작성/수정, Worker 선택, local retry/evidence acquisition/restart/accept/stop, 하위 실패 대응, 정리 제안 | Goal·mandatory criterion을 바꾸거나 자신의 산출물을 스스로 승인하지 않음 |
| Reviewer | current Artifact와 적용 기준을 독립 평가, 불충분한 evidence 및 기준별 결과 기록 | 실행·Workflow 수정·restart·User 승인 대행 권한 없음 |
| Worker/Tool adapter | 명시된 work order의 실제 수행, 결과와 실패/효과 상태 보고, Tool 고유 I/O 경로 및 capability 존중 | 전략 결정·최종 acceptance 권한 없음 |

현재 Codex 대화가 Host다. Frontier는 별도 Codex CLI inference다. Reviewer도 별도 inference이며 Frontier의 대화 context나 자기 평가를 공유하지 않는다. 두 역할의 현재 요청 model은 `gpt-6.1-sol`, `reasoning_effort=low`로 고정한다. 역할별 adapter 설정은 분리하여 이후 다른 backend로 교체할 수 있다. 요청 설정과 runtime에서 실제 관측한 model identity를 구분하고, 관측 불가 시 unknown을 기록한다.

Core에는 Codex home/transcript/thread offset, ComfyUI node 이름, Blender/GLB/image/video별 분기, 특정 model 이름 또는 sampler parameter 목록을 넣지 않는다. type/capability 문자열 metadata와 일반적인 I/O 및 lineage 계약은 사용할 수 있다.

## 4. Host 연결과 시작 권한

Python Core의 호출 계약 위에 MCP를 첫 transport로 둔다. 첫 local 연결은 stdio를 사용하고, Core는 MCP SDK나 Host에 종속되지 않는다. Python MCP SDK는 protocol transport를 위해 사용한다. 별도 HTTP service는 현재 만들지 않는다.

Host는 실제 User의 새 Session 시작 허가를 확인하여 신뢰된 issuer 경계를 통해 VerifiedStartGrant를 발급한다. 최소 binding은 issuer, grant identity, Session identity, current Request/Reference identity, provenance evidence 및 single-use 소비 상태다. Core는 신뢰된 issuer와 binding을 확인하고 durable ledger로 한 번만 소비한다.

Prompt 안의 ‘승인되었다’는 주장, 과거 proof/config, 같은 Codex 대화, 개발 완료·commit·push·Host next는 새 생산 Session grant가 아니다. grant 발급은 Frontier/Reviewer가 호출하는 일반 inference 기능으로 제공하지 않는다. 다른 Host가 연결되더라도 provenance 검증 방식만 Host adapter에서 교체한다.

namespace collision과 입력 identity 문제는 효과 전에 차단한다. grant 소비와 Session 생성 중 중단 시 기록을 보존하고 Host가 상태를 판단한다. 충돌을 피하려고 suffix를 붙이거나 과거 namespace를 자동 재사용하지 않는다.

권한은 Host가 실제 제공한 capability 범위에서만 작동한다. sandbox 내부 read/search/download/install/기존 허용 Tool 수행은 handoff가 정한 범위에서 가능하다. system-wide install, account/credential, 유료 호출, private data upload, privilege 변경, 상주 service 및 sandbox 밖 파괴적 변경은 해당 Host의 실제 승인 정책을 따른다. 이번 개발 허가는 미래의 모든 Core Session 효과를 자동 허가하지 않는다.

## 5. Specification Dialogue와 Frozen Specification

Session은 한 번의 시작 권한으로 dialogue부터 종료까지 이어진다. dialogue-ready 이후 같은 Session에 Frozen Specification을 결합하며 새 grant나 별도 Session을 만들지 않는다.

Frontier가 current Request/Reference와 필요한 reusable knowledge를 해석한다. 결과 방향을 의미 있게 바꾸는 의도 모호성만 Host를 통해 User에게 묻는다. preprocessing, masks, Tool/Skill/model 선택, view 수, 단계별 retry/restart를 User의 반복 승인 장치로 만들지 않는다.

Frozen Specification은 Session ID, current Request/Reference identity, Goal, deliverable, Must-Have, Should-Have, Non-Goals, constraints, 기준과 applicability, finite resource envelope 및 필요한 delivery 계약을 포함한다. resource/deadline이 User에게서 주어졌으면 존중한다. 없으면 Frontier가 합리적인 bounded envelope을 작성한다. Core가 Domain별 임의 기준이나 무한 budget을 채우지 않는다.

Freeze 후 Goal과 mandatory criteria를 낮추거나 Request/Reference를 과거 것으로 바꾸지 않는다. 기준별 적용 stage/Artifact 관계를 명시하여 단계 밖 기준을 강제하지 않는다. Should-Have 미충족만으로 최종 REVISE를 요구하지 않는다.

Freeze 후 current evidence로 해소할 수 없는 결정적 User intent ambiguity가 발견되면 해당 Session을 terminal로 중단하고 Host에 전달한다. User clarification은 종료된 Session을 재개하는 수단이 아니며 새로운 Request/새 Session 시작으로 이어진다.

## 6. Skill과 Workflow

Skill은 재사용 가능한 작업 지식이다. 최소한 identity/version/hash, 해결 목적, inputs/outputs, capability/dependency, 하위 Skill 관계, known failure, provenance, 검증 상태와 성공 사용 evidence를 갖춘다. 별도의 거대한 registry lifecycle을 만들지 않는다.

Frontier가 missing link를 조사하여 candidate Skill을 자동 작성하고 현재 Workflow에서 사용할 수 있다. 실제 Artifact + 독립 Reviewer의 현재 성공 evidence가 있을 때만 reusable/validated 상태로 자동 승격한다. 매 Skill마다 User 승인하지 않는다. 실패 조건과 제한도 지식으로 남기며 실패를 성공으로 재해석하지 않는다.

Workflow는 versioned durable 실행 전략이다. 최소 구성은 stages, 선택한 Skill/Tool/model, 입력·출력 관계, stage별 기준 적용, previous Workflow 및 revision reason이다. 선언된 단계 관계와 checkpoint만으로 현재 Scenario A를 표현하고 범용 그래프 언어를 추가하지 않는다.

ComfyUI는 Core Workflow에 포함될 수 있는 Tool이다. Segmentation workflow는 ComfyUI Tool을 사용하는 Skill이다. 따라서 전처리 예시는 ‘Core Workflow 안에서 ComfyUI Tool의 Segmentation-workflow Skill 사용’이다. ComfyUI native workflow/subgraph는 adapter와 Skill이 취급하며 Core가 node 의미를 직접 해석하지 않는다. 단일 workflow 파일 하나를 모든 작업의 필수 기본 템플릿으로 강제하지 않는다.

Tool/Skill/model의 교체가 전략을 바꾸면 Workflow revision이다. 동일 전략 안의 parameter correction은 해당 Skill/adapter가 선언한 local tuning 범위 안에서만 Attempt 변경으로 취급한다. Core에 seed/cfg/sampler와 같은 Domain parameter 목록을 고정하지 않는다.

## 7. Artifact, checkpoint와 current lineage

Artifact는 역할 사이의 공용어다. 최소 identity는 type, file/content identity, hash, producer Session/Run/Attempt/stage, dependency refs 및 durability 역할이다. 내부 reasoning/transcript를 역할 간 통신 수단이나 durable runtime history로 수집하지 않는다.

durability는 의미상 TRANSIENT, CHECKPOINT, AUTHORITY, OUTPUT으로 구분한다. 모든 파일을 checkpoint로 만들지 않는다. checkpoint는 재사용과 restart에 필요한 실제 단계 산출물 및 그 입력 binding을 가진다.

Tool에 이미 binding된 실제 input/output/model/workflow 경로를 존중한다. 외부 Tool output을 무조건 Session 하위로 옮기거나 Tool root를 임의로 바꾸지 않는다. Core가 기록하는 file reference는 실제 경로와 hash를 가리킨다. Host가 허용한 경로 밖의 read/write는 adapter가 차단한다. 재사용해야 하는 출력이 Tool에서 overwrite될 수 있으면 adapter가 소유한 immutable snapshot이나 해당 Tool의 유일한 output namespace를 사용한다.

Review와 Decision은 current frozen Specification, Workflow, Artifact bytes, Run/Attempt 및 관련 invocation lineage에 결합한다. 과거 Review/Artifact는 새 Run에서 자동으로 current가 되지 않는다. Frontier가 명시적으로 선택한 restart point 및 checkpoint adoption을 Core가 dependency와 identity로 검증한 경우에만 재사용한다. 재사용 lineage 자체도 기록한다.

## 8. Run, Attempt, bounded loop

Session은 하나의 frozen Goal을 가진다. Run은 하나의 Workflow 전략, Attempt는 같은 전략 내의 local correction이다. Workflow revision은 새 Run, local retry는 새 Attempt다. 정상 작업의 모든 restart는 Frontier 아래 계층에서 진행된다.

Frontier Decision은 최소한 다음 행동과 그 evidence/reason을 표현한다: execute, local retry, acquire evidence, revise Workflow/restart, accept, stop, Host escalation. Workflow가 바뀌면 restart stage와 보존/폐기할 checkpoint가 명시되어야 한다. ‘처음부터 자동 재시도’나 숨겨진 retry를 추가하지 않는다.

budget은 Session state 안에 둔다. 각 inference/Tool effect 전에 finite envelope 내의 reservation을 durable하게 기록한다. 중단되었거나 effects가 UNRESOLVED인 호출을 성공/미실행으로 추정하여 refund하지 않는다. budget 소진은 무한 반복을 막고 terminal 또는 필요한 Host 판단으로 이어진다.

quality threshold 충족이 resource 최소화보다 우선한다. 충족 후 추가 고비용 작업을 계속하지 않는다. 부족함과 실제 evidence가 있을 때만 전략·도구·자원을 확대한다. resource escalation이 Host policy를 넘으면 Host 판단을 요청한다.

## 9. 실패, 복구, Terminal

Tool/inference의 status와 관측 evidence를 분리한다. 성공 process exit만으로 semantic success를 주장하지 않는다. stdout/stderr, transport failure, parse failure, output missing, request/result identity 등 원인 판단에 필요한 최소 관측 정보는 실제 경로를 그대로 보존한다. 비밀값이나 hidden reasoning은 로그에 넣지 않는다.

효과가 불명확하면 UNRESOLVED로 기록하고 해당 effect의 실현 여부를 확인하기 전에 재실행하지 않는다. 비종료 Session의 중단만 같은 Session에서 복구할 수 있다.

- Frontier 아래 계층의 중단: Frontier가 checkpoint와 실제 효과 상태를 보고 판단한다.
- Frontier/그 위 계층의 중단: Host가 판단한다.
- Frontier는 자신의 아래 계층 문제도 필요하면 Host에 escalation할 수 있다.
- 복구는 기존 state/lineage 확인 후 명시적 continuation이다. 종료된 Session의 grant나 acceptance를 다시 사용하는 통로가 아니다.

사용자 최종 결정: **Terminal로 확정되어 최종 Artifact가 User에게 전달되지 않은 Session을 비정상 종료 Session으로 분류한다. Terminal 이후에는 같은 Session을 재실행하지 않는다.** 새 실행은 User authority를 가진 New Session Start뿐이다.

미전달 Artifact가 있으면 Host 또는 Frontier가 그 존재와 상태를 User에게 안내한다. 미전달 Artifact가 없으면 있다고 주장하지 않는다. 안내에는 실제 refs와 내부 acceptance 여부를 구분하며, 안내만으로 delivery/quality success로 상태를 바꾸지 않는다.

## 10. Reviewer, Acceptance, Delivery

Reviewer는 frozen criteria의 적용 부분에 대해 MET/UNMET/UNCERTAIN과 근거, 추가 evidence 요청을 반환한다. 결과가 불충분하면 Frontier가 evidence acquisition과 rework를 선택한다. HUMAN_REQUIRED 같은 상태를 internal human approval loop로 만들지 않는다.

최종 INTERNAL_ACCEPT는 Frontier의 명시적 accept Decision, current final Artifact, current independent Review, 모든 mandatory applicable criterion의 MET 및 미해결 effect 부재가 필요하다. stale evidence, 일부 기준 누락, UNCERTAIN mandatory criterion, failure status, Worker 자기 승인을 성공으로 바꾸지 않는다. nonblocking Should-Have 결과는 기록하되 단독 acceptance blocker로 만들지 않는다.

INTERNAL_ACCEPT는 User 전달이나 User 만족을 뜻하지 않는다. Host가 delivery 계약에 따라 실제 산출물과 refs를 전달/내보낸 뒤에만 delivery 완료를 기록한다. local file hash 확인, UI 안내, 실제 사용자 수신/품질 승인을 각각 구분한다. 시각 산출물의 User 평가에는 원본 입력과 최종 출력을 함께 제시한다. User 평가는 Core Run 밖에 있으며 이후 수정 요구는 새 Request다.

최종 Artifact는 accepted 후 delivery 전에 손실되거나 바뀌지 않도록 보존한다. delivery failure를 terminal로 확정했다면 같은 Session을 다시 실행하여 보충하지 않는다. Host/Frontier의 미전달 안내와 새 Session 시작 경계는 §9를 따른다.

## 11. 종료 시 보존과 정리

Session이 끝나면 Frontier와 Core가 제안한 최소 보존 정책을 기초로 어떤 파일을 정리/보존할지 결정한다. Core는 적용 가능성, 소유권, 현재 refs와 authoritative state 보호를 확인한다. Frontier가 사용할 수 없는 상위 중단 상태에서는 Host가 상태를 판단한다.

보존 기본값: frozen authority 및 소비 grant 요약, 종료 상태와 사용 budget, 최종/미전달 OUTPUT, 재사용에 필요한 checkpoint, 실패 설명 evidence, Review/Decision, Skill/Workflow 지식과 성공/실패 lineage, compact history/index. 불필요한 full stdout dump, 중복 중간 파일, 재생성 가능한 cache와 stale transport 자료는 정리 후보로 제안할 수 있다.

진행 중에는 active failure/checkpoint/authority를 보존하며 자동 GC로 지우지 않는다. 종료 후라도 참조되는 Artifact, 미전달 output, 원본 User 입력, 공유 모델/Tool install/cache, Tool 소유 파일은 Core 판단만으로 파괴적으로 삭제하지 않는다. 실제 삭제는 Host가 허용한 소유 영역과 복구 가능성 안에서 수행한다. retention Decision과 실행 결과를 남긴다.

개발 history는 runtime Session evidence와 별개다. 완료된 개발 경계는 목표/결과/결정/Smoke 범위/실패 교훈/후속 사항/source refs를 compact history에 남긴다. 과거 proof bytes와 실패 판단을 수정하지 않는다. Git으로 완전히 복구 가능한 출발 tree는 Git ref를 복구 근거로 사용할 수 있다.

## 12. Scenario A 구현 경계

Scenario A는 Image → Multiview → 3D의 reference 경로다. 필요한 경우 Segmentation/preprocessing, 생성, geometry, Blender diagnosis/render/export를 Skill과 Tool stage로 조합한다. 매 Request에 모든 stage를 강제하지 않으며 Frontier가 Goal과 evidence로 선택한다.

현재 구현은 설치된 ComfyUI/Blender와 필요한 workflow/model/입출력 경로를 binding하는 adapter, current Reference 전달, 생성 Artifact와 diagnostic evidence, 독립 Review 및 delivery entry를 제공한다. 현재 환경의 asset 경로와 지원은 파일/config 및 공식 자료로 확인하며, 실제 생성·검수 성공은 후속 사용자 공동 검증에서 판단한다.

새 Core는 원래 `src/core`, `src/session`, `src/scenario_a` 또는 과거 proof host scripts를 실행 경로로 import하지 않는다. 원래 실행 코드가 필요한 경우 계약에 필요한 부분만 새 adapter 책임으로 가져오고 출처를 남긴다. cloud reconstruction은 예외 없이 제외한다.

Smoke 또는 configuration 존재만으로 실제 모델 가용성, production 성공, semantic quality, 범용성 또는 lower Frontier 효율을 입증했다고 보고하지 않는다.

## 13. 구현 순서와 점검

1. 이 Specification을 정리한 뒤 전역 지침에 따른 Specification 전수점검을 **한 차례** 실행한다. 이는 요구사항·지침·authority·scope·설계 일관성 점검이며 software/production 검증이 아니다.
2. BLOCKER가 없으면 새 branch에서 최소 contract 및 독립 active 구조를 구현한다. 과거 프로젝트 AGENTS의 Direction Gate/fixed Scope/actual proof 지시는 새 reconstruction authority와 구분하여 active 지침을 정리한다.
3. 통합 Session state, Artifact/Skill/Workflow, budget/lineage/Review/Decision guard를 구현한다.
4. 독립 model adapters, Host authority boundary, MCP entry 및 execution adapters를 연결한다.
5. Scenario A Skill/Workflow 자료와 Tool binding 및 실행/delivery/cleanup 안내를 완성한다.
6. 단계마다 필요한 최소 Smoke만 수행하고 실패를 보존한다. 개발 과정에서 새로운 material ambiguity만 해당 범위에서 User에게 묻고 독립 작업을 계속한다.
7. reconstruction 완료를 코드/문서 제공과 Smoke 범위로 보고한다. actual 검증은 사용자와 함께 별도 진행한다. 이번 구현 완료를 실제 Scenario A acceptance 또는 범용 architecture 검증 완료로 주장하지 않는다.

## 14. 기존 지침과 충돌의 처리

| 과거 항목 | 이번 적용 |
|---|---|
| Direction Gate의 fixed Frontier/narrow Scenario proof scope | 새 handoff와 직접 User 결정이 reconstruction scope를 대체. 과거 지침과 proof는 역사 자료로 보존 |
| Codex transcript 기반 Core authority | 실제 User provenance는 Host로 이동. Core는 신뢰된 grant의 binding/단일 사용 소비를 유지 |
| 과거 Work Specification의 actual Fresh Session proof 자동 실행 명령 | 이번 실행 권한 아님. 현재 검증 제외와 별도 User Session start grant가 우선 |
| 기존 config의 `reasoning_effort=high` | Frontier/Reviewer adapter에서 `gpt-6.1-sol` / `low`를 명시하며 현재 Host 대화 설정을 임의 변경하지 않음 |
| 기존 local output를 Session directory 안에 강제 | Tool에 binding된 경로를 존중하고 Host 허용 경로와 immutable lineage를 관리 |
| 모든 applicable outcome MET/PASS를 강제한 일부 구현 | frozen mandatory 기준만 acceptance blocker로 유지. Should-Have만 미충족이면 최종 실패로 만들지 않음 |
| 과거 terminal Session 재실행 금지 | 유지. 비종료 중단 복구와 구분하고 미전달 Artifact 안내를 추가 |
| 최소 runnable verification 원칙 | 이번 사용자 지시로 구현 중 Smoke에 한정. 정식 검증은 전체 reconstruction 후 공동 진행 |

## 15. 공식 자료와 확인 범위

- Codex CLI local: `0.159.0-alpha.12.1`, `codex exec --help`의 model/config/schema/output/sandbox 옵션을 read-only로 확인. actual inference는 아직 수행하지 않았다.
- `gpt-6.1-sol` / `low`: https://developers.openai.com/api/docs/models/gpt-6.1-sol
- Codex MCP stdio와 timeout 설정: https://learn.chatgpt.com/docs/extend/mcp?surface=cli
- Python MCP SDK: https://github.com/modelcontextprotocol/python-sdk
- MCP transport: https://modelcontextprotocol.io/specification/2025-11-25/basic/transports
- ComfyUI API queue/history: https://docs.comfy.org/development/comfyui-server/comms_routes
- ComfyUI native reusable graphs: https://docs.comfy.org/interface/features/subgraph

공식 지원 정보와 local config는 구현 선택의 근거이며 actual runtime/quality proof가 아니다. 사용자 결정상 새로 질문해야 할 Specification BLOCKER는 남아 있지 않다.
