# Agent-Loop Direction Gate v1 — Codex Handoff

- 작성일: 2026-09-30
- 상태: **AUTHORITATIVE DIRECTION GATE**
- 목적: 기존 Agent-Loop 작업을 폐기하지 않으면서, 프로젝트를 다시 **Compact Frontier-Supervised Local Worker Loop Core** 중심으로 고정한다.
- 대상: 로컬 Codex 및 이후 구현 세션
- 주의: **이 문서는 실행 명령이 아니라 상위 방향·범위·판정 기준이다.** 실제 파일 수정, 새 repository 생성, migration, refactor는 별도의 명시적 작업 지시가 있을 때만 수행한다.

---

## 0. 우선순위 / 곡해 방지 규칙

이 문서는 프로젝트 방향에 관해 **이전 문서와 충돌할 경우 우선한다.**

특히 다음의 과거 방향은 이 문서로 수정되거나 범위가 축소되었다.

- Agent-Loop를 범용 production orchestration framework처럼 확대하는 해석
- A-C6/F2B comprehensive resume을 현재 Core v1의 필수 완료 조건으로 보는 해석
- Scenario A 품질 우위를 Loop Core 완료 조건으로 보는 해석
- 사용자의 최종 피드백을 동일 Loop Run의 REVISE로 다시 넣는 해석
- portability / Scenario B / distributed reliability를 Core v1 이전에 증명해야 한다는 해석

과거 문서·evidence·Git history는 **삭제하지 않는다.**
다만 방향과 scope에 관한 normative authority는 이 문서가 가진다.

### Codex가 반드시 지킬 해석 규칙

1. **"Agent-Loop"라는 이름을 근거로 범용 Agent Framework를 설계하지 말 것.**
2. Core v1에 필요하지 않은 reliability/hardening 기능을 선제 구현하지 말 것.
3. 기존 구현이 다소 복잡하거나 못생겼다는 이유만으로 먼저 대규모 refactor하지 말 것.
4. 현재까지의 A-C/P/F 계열 구현·테스트·evidence를 실패한 작업으로 취급하지 말 것.
5. 이 문서를 읽었다는 이유만으로 새 repository를 만들거나 코드를 이동하지 말 것. 별도 작업 지시가 필요하다.
6. 모호한 경우 추측으로 범위를 넓히지 말고, 현재 Core v1 완료 기준에 직접 필요한가를 기준으로 축소할 것.

---

# 1. 프로젝트의 최상위 철학

프로젝트의 최초 철학과 현재 철학은 동일하다.

> **Frontier Model이 모든 제작 작업을 직접 수행하지 않는다.**
>
> **고정된 Frontier Supervisor가 팀장 역할을 맡고, 교체 가능한 Local Worker들이 팀원처럼 실제 제작을 수행한다.**
>
> Frontier는 지시·검수·피드백·최종 제출을 담당하고, 반복 제작 작업은 가능한 한 Local Worker에게 위임한다.
>
> 궁극적인 목적은 **Frontier 사용량/크레딧 소비를 줄이면서도 사용자가 사용할 수 있는 산출물을 얻는 것**이다.

모티브는 Frontier Model + 외부 생성/제작 도구의 결합을 통해 Blender/Unreal 등 실제 제작을 수행하는 고비용 파이프라인이며, 본 프로젝트는 그 철학을 **Local Worker 중심의 저비용 구조**로 검증하려는 시도다.

---

# 2. 역할 정의

## 2.1 Frontier Supervisor

Frontier는 고정 역할이다.

책임:

- 사용자 요청 이해
- Work Order / 작업 지시 생성
- Local Worker 선택 및 지시
- Worker 결과 검수
- `REVISE` 또는 `INTERNAL_ACCEPT` 판단
- 반복 횟수/예산 내에서 Loop 관리
- 최종 산출물 사용자에게 제출

Core v1에서는 Frontier provider 자체를 범용 교체 가능 구조로 만들 필요가 없다.

## 2.2 Local Worker

Local Worker는 교체 가능하다.

예:
- ComfyUI + Local Image/3D Model
- Blender automation
- Unreal automation
- 향후 다른 Local Model / CLI / DCC worker

Core는 특정 Worker의 내부 semantics를 알아서는 안 된다.

## 2.3 User

사용자는 **Loop 외부의 최종 평가자**다.

정상 흐름:

```text
User Request
    ↓
Frontier Supervisor
    ↓
Local Worker
    ↓
Artifact
    ↓
Frontier Review
    ├─ REVISE → Local Worker 재작업
    ├─ FAILED / ABORT
    └─ INTERNAL_ACCEPT
             ↓
          DELIVERED
             ↓
        해당 Loop Run 종료
             ↓
       User External Verdict
```

사용자의 판정은 다음 셋 중 하나다.

- 승인
- 자연어 피드백
- 사용하지 않음

Frontier는 결과 제출 후 사용자에게 이 판정 중 하나를 **반드시 요구**한다.

그러나 이 계약은 **Frontier prompt의 짧은 interaction contract**이며 Core state machine의 일부가 아니다.

사용자가 자연어 피드백을 주더라도 기존 Run을 재개하지 않는다.

```text
Run A → DELIVERED → 종료

User Feedback
→ 필요하다면 새로운 Run B의 입력
```

---

# 3. 확정 용어

## `INTERNAL_ACCEPT`
Frontier가 Worker 결과를 검수한 후 사용자에게 제출 가능한 수준이라고 내부 판정한 상태.
아직 사용자의 승인과 동일하지 않다.

## `DELIVERED`
`INTERNAL_ACCEPT`된 결과가 사용자에게 실제 제출된 상태.
**정상 Loop Run의 terminal state**다.

## `FAILED`
Worker/Loop가 정의된 조건에서 정상 진행할 수 없어 실패한 terminal.

## `ABORT`
예산, 반복 한도, 명시적 중단 조건 등으로 실행을 종료한 terminal.

## `COMPLETE`
Run state가 아니다.

> **Loop Core v1이 정의된 기술적 완료 조건을 충족했다는 프로젝트 판정**

에 사용한다.

---

# 4. Loop Core v1의 정확한 목표

Loop Core v1은 production-grade orchestration framework가 아니다.

정의:

> **하나의 고정 Frontier Supervisor가 교체 가능한 Local Worker에게 작업을 위임하고, Worker 산출물을 검수하여 REVISE 또는 INTERNAL_ACCEPT를 반복하며, 제한된 반복 안에서 DELIVERED / FAILED / ABORT로 종료하는 Compact Control Loop.**

최소 개념:

```text
WorkOrder
Artifact
ExecutionReport
Review
Decision
RunState
Budget
WorkerPort
```

개념적으로 필요한 흐름:

```text
Frontier
→ WorkOrder
→ Worker
→ Artifact + ExecutionReport
→ Frontier Review
   ├─ REVISE → 다음 WorkOrder
   └─ INTERNAL_ACCEPT
→ DELIVERED
```

---

# 5. Core v1에서 반드시 유지할 Safety Floor

아래는 "나중에 안정화할 기능"이 아니라 Core semantics이므로 유지한다.

- bounded iteration 또는 bounded Frontier budget
- 최소한의 duplicate expensive execution 방지
- Execution / Result / Review의 최소 durable 기록
- 명시적 terminal: `DELIVERED`, `FAILED`, `ABORT`
- Worker artifact와 Review 대상의 identity/provenance 확인

---

# 6. Core v1에서 제외할 Hardening / Future Work

아래는 현재 Core v1 완료에 필수가 아니다.

- comprehensive restart/resume
- 모든 crash point recovery
- partial phase recovery
- Reviewer reservation recovery
- multi-worker concurrency
- distributed locking
- database abstraction
- arbitrary DAG
- generic workflow DSL
- plugin registry / marketplace
- dashboard
- production-grade scheduler
- arbitrary multi-agent topology
- perfect crash recovery
- portability proof를 위한 대형 Scenario B

### F2B 결정

기존 `F2B comprehensive resume` 조사와 WIP는 **폐기하지 않는다.**

분류:

> `Hardening / Future Reliability Research`

로 동결한다.

기존에 이미 확보된 minimal duplicate guard, bounded state 등 필요한 safety floor는 유지한다.

**F2B comprehensive resume을 현재 Core v1 완료를 위해 계속 확장하지 않는다.**

---

# 7. 현재 Scenario A의 역할

Scenario A:

> Single Image → Multiview → 3D

는 최종 제품이 아니라 **첫 reference implementation 및 validation benchmark**다.

현재 Scenario A 관련 기존 자산:
- ComfyUI `_api.json` workflows
- Qwen image/multiview
- Hunyuan3D multiview → 3D
- existing HTTP executor
- 실제 execution reports
- PNG / GLB artifacts
- Reviewer/evidence contracts
- A-C / P / F 계열 테스트와 evidence

는 버리지 않는다.

이들은 앞으로:
1. 실제 Core Loop proof의 reference implementation
2. Core extraction 후 regression evidence
3. 마지막 품질/비용 가설 benchmark의 자료

로 사용한다.

---

# 8. 품질/비용 가설의 위치

품질 우위 또는 비용 우위는 **Loop Core v1 COMPLETE의 조건이 아니다.**

Core는:

> 만들었고, 정의한 Loop가 제대로 작동하면 COMPLETE.

품질/경제성 가설은 **프로젝트 맨 마지막 milestone에서 별도로 검증**한다.

현재 기록할 가설:

### H1 — Scenario A 비교 가설
Local one-shot 결과와 Frontier-supervised Local Loop 결과 사이에 유의미한 품질 차이가 있는가?
그 차이를 만들기 위해 Frontier가 얼마나 사용되었는가?

### H2 — 최종 경제성 가설
Frontier가 제작 대부분을 직접 담당하는 방식과 비교할 때:
> Frontier Supervisor + Local Workers 방식이 유사한 품질에서 Frontier 자원 사용을 줄일 수 있는가?

H2는 현재 증명하지 않는다.

마지막 hypothesis milestone에 진입할 때 benchmark design을 다시 검토한다.

필요하다면 사용자는 그때:
- Higgsfield API
- 유료 API
- 기타 비교 수단

을 확보할 의향이 있다.

**현재 Core 구현을 H1/H2를 미리 증명하려는 방향으로 왜곡하지 말 것.**

---

# 9. Usage 기록 원칙

마지막 benchmark 때 과거 실행을 다시 해석하지 않아도 되도록, Run별 사용량을 **model/provider-independent 문서**로 남긴다.

목표:
> 작업 종료 후 Usage 문서들만 비교해도 각 Run의 Frontier/Worker 사용량을 비교할 수 있어야 한다.

원칙:
- 측정 가능한 값만 기록
- 측정 불가능한 값은 추정하지 않고 `null` / `unavailable`
- provider/model별 raw metric은 보존
- 공통 metric 이름으로 정규화 가능하면 함께 기록
- usage collector가 Core logic의 필수 dependency가 되어서는 안 됨

예시 개념:

```json
{
  "run_id": "...",
  "started_at": "...",
  "finished_at": "...",
  "frontier": {
    "provider": "...",
    "model": "...",
    "invocations": 0,
    "input_tokens": null,
    "cached_input_tokens": null,
    "output_tokens": null,
    "reasoning_tokens": null,
    "reported_credits": null
  },
  "workers": [
    {
      "worker_id": "...",
      "backend": "...",
      "model": "...",
      "invocations": 0,
      "execution_seconds": null
    }
  ],
  "loop": {
    "revision_count": 0,
    "final_state": "DELIVERED"
  }
}
```

정확한 telemetry source와 collector 구현은 별도 작업에서 현재 Frontier 환경을 확인한 뒤 정한다.

---

# 10. Loop Core v1 기술적 완료 조건

다음 C1~C5가 실제 evidence로 증명되면:

> **Loop Core v1 = COMPLETE**

로 판정한다.

## C1 — Supervisor Delegation
Frontier가 Local Worker에게 실제 Work Order를 전달하여 실제 실행이 일어난다.

## C2 — Semantic Supervision
Frontier가 실제 Worker artifact를 보고 의미적 Review를 수행한다.

## C3 — Actual Revision Loop
실제 결과를 근거로 최소 한 번:
```text
REVISE
→ Worker 재실행
```
이 발생한다.

단순 synthetic fixture만으로는 충족하지 않는다.

## C4 — Bounded Termination
Run이 정의된 iteration/budget 안에서 반드시 다음 중 하나로 종료된다.
```text
DELIVERED
FAILED
ABORT
```

## C5 — Replaceable Worker Boundary
Core logic을 수정하지 않고 Worker Adapter를 교체할 수 있음을 최소 smoke test로 증명한다.

이를 위해 별도의 대형 Scenario B를 만들 필요는 없다.
작은 deterministic/fake Worker 또는 저비용 substitute로도 충분하다.

---

# 11. 사용자 외부 평가와 Core COMPLETE의 관계

사용자의 최종 판정은 매우 중요하지만 Core 내부 state가 아니다.

Core C1~C5가 PASS하면 기술적으로 Core는 COMPLETE 판정 가능하다.

그 뒤 Scenario A 결과가:
- one-shot보다 우수
- 비슷함
- 열등

중 어느 결과가 나오더라도 Core의 기술적 산출물 자체는 의미가 있다.

따라서:
```text
Core 기술적 성공
≠
Scenario A 품질 가설 성공
```
을 항상 분리한다.

---

# 12. 기존 Repository와 새 Compact Repository의 관계

## 12.1 현재 `Agent-Loop`

현재 repository는 유지한다.

역할:
- 원본 연구 workspace
- 기존 A-C/P/F 구현
- historical evidence
- audit
- Scenario A artifacts/contracts
- future hardening research

언리얼 프로젝트 비유로:
> 여러 원본 에셋과 실험 결과가 모여 있는 Asset/Research Project

에 가깝다.

## 12.2 새 Compact Repository

별도의 Git repository를 새로 만든다.

목적:
> 실제 Compact Loop Core v1을 제작·증명하는 본 작업 workspace

가칭 예:
```text
Agent-Loop-Core
```

단, **repository 이름/경로/생성 시점은 별도 명시적 작업 지시가 있을 때 확정한다.**

현재 이 문서를 읽었다는 이유만으로 생성하지 말 것.

---

# 13. Soft Cleanup 전략

새 Compact Repository를 시작할 때 **Logical Diet + Soft Cleanup**을 한 번 수행한다.

목적:
> 현재 Agent-Loop에서 Core v1 실제 proof에 필요한 것만 작은 workspace로 옮긴다.

이는 리팩터링 milestone이 아니다.

### 허용
- 필요한 파일만 선별 복사
- historical bulk artifact 제외
- dead/unused research file 제외
- 폴더 정리
- import/path 최소 수정
- Core 후보와 Scenario A adapter 위치 분리
- source provenance 기록

### 금지
- 새 state machine 선제 설계
- schema 전면 재작성
- generic abstraction 확대
- runner 재설계
- comprehensive resume 추가
- old Agent-Comfy-Model wholesale migration
- architecture cleanup을 이유로 동작 semantics 변경

---

# 14. Provenance 규칙

새 repo 생성 시 반드시 source provenance를 남긴다.

예:
```text
PROVENANCE.md
```

내용:
- source repository
- source commit
- copied components
- copied file SHA 또는 equivalent identity
- KEEP / COPY / REFERENCE / NOT COPIED 이유
- F2B 등 제외한 영역과 이유
- old Agent-Comfy-Model에서 참고한 primitive가 있다면 그 출처

목표:
> 미래에 "이 코드는 어디서 왔고 왜 이렇게 선택되었는가?"가 다시 불명확해지지 않게 한다.

---

# 15. Old `Agent-Comfy-Model`에 대한 최종 결정

이번 Gate audit에서 old Core를 실제 source 수준으로 확인했다.

확정:
- old Core는 실제 작동했던 최소 Core였다.
- 37/37 test PASS 기록이 있다.
- 실제 PASS / REVISE → child PASS E2E가 존재한다.
- 그러나 알려진 구현 gap도 실제 source에 남아 있다.
- 현재 Agent-Loop 요구를 wholesale 충족하지 않는다.

따라서:
```text
old Core wholesale migration → NO
old Core primitive/reference 가치 → YES
현재 project를 old Core로 되돌림 → NO
hash / atomic persistence / run identity / adapter boundary 등의 설계 참고 → YES
```

old/new reconciliation을 별도 대형 프로젝트로 확장하지 않는다.

---

# 16. 현재 감사에서 발견된 기술 부채의 취급

확인된 항목:
- D-015 / D-016 historical namespace collision
- 일부 historical workflow execution에서 template SHA provenance 부족
- 반복되는 hash/ref/persistence helper
- current controller에 Scenario A semantics가 일부 포함
- F2에서 top-level integration blocker 발견보다 supporting contract 확장이 앞선 구간

이들은 기록한다.

그러나 **현재 Core proof보다 먼저 전부 정리해야 하는 blocker로 승격하지 않는다.**

Core COMPLETE 후 refactor 단계에서 필요한 항목만 정리한다.

---

# 17. Refactor 시점

대규모/구조적 refactor는 Core functional proof 이전에 하지 않는다.

순서:
```text
Soft Cleanup Workspace
        ↓
C1~C5 actual proof
        ↓
Loop Core v1 COMPLETE
        ↓
Refactor
        ↓
동일 C1~C5 regression
        ↓
Core v1 Frozen
        ↓
마지막 Hypothesis Benchmark
```

Refactor 후 반드시 동일 acceptance regression을 다시 통과해야 한다.

---

# 18. 현재까지의 작업은 무효화되지 않는다

기존 작업의 역할:

```text
A-C1~A-C5 → contracts / lifecycle 연구와 검증 evidence
P1 → 실제 executor boundary
P3 → durable bounded state 연구
P2 / P2-E1 → semantic Reviewer + evidence path
F1 → fresh-start bootstrap 연구
F2A/F2 → policy coverage / Review→Decision→next execution 연구
F2B → future hardening / resume 연구
Scenario A artifacts → actual proof / regression / benchmark 자료
Agent-Comfy-Model → historical Core / primitive reference
```

따라서 새 Compact Repository는 현재 프로젝트를 폐기하는 것이 아니라:

> **연구 repository에서 증명된/필요한 부분만 본 작업 프로젝트로 옮기는 단계**

다.

---

# 19. 앞으로 모든 작업을 통과시킬 단일 Gate 질문

새 기능 또는 리팩터링을 제안하기 전에 반드시 묻는다.

> **"이 작업이 없으면 C1~C5의 실제 Compact Loop Core proof를 수행할 수 없는가?"**

- YES → Core v1 후보
- NO → backlog / hardening / post-complete refactor / hypothesis 단계

추가 질문:

> **"이 작업은 실제 integration blocker를 제거하는가, 아니면 미래의 가능성을 위해 abstraction을 추가하는가?"**

후자라면 현재 단계에서는 기본적으로 하지 않는다.

---

# 20. 다음 실행 지시와의 관계

이 문서는 **Direction Gate**다.

따라서 Codex는 이 문서를 받은 즉시 다음을 임의로 실행해서는 안 된다.

- 새 repository 생성
- 현재 repo 수정
- F2B 삭제
- migration
- Core extraction
- refactor
- benchmark 실행

다음 실제 작업은 별도의 handoff prompt에서 **하나의 milestone만** 지정한다.

해당 prompt는 반드시:
1. 이 Direction Gate를 먼저 확인하고,
2. 현재 repository 상태를 확인하고,
3. Existing-First 원칙을 적용하고,
4. 현재 milestone acceptance만 구현하고,
5. 다음 milestone을 선제 구현하지 않고,
6. 완료 후 STOP

해야 한다.

---

# 21. 현재 권장 상위 진행 순서

현재 Gate 이후의 전체 방향만 기록한다.

```text
[Direction Gate Freeze]
        ↓
[현재 Agent-Loop source freeze / provenance 기준점]
        ↓
[새 Compact Repository 생성 — 별도 명시적 작업]
        ↓
[Source Manifest + Soft Cleanup Copy]
        ↓
[Compact Core Actual Proof: C1~C5]
        ↓
[Loop Core v1 COMPLETE]
        ↓
[Refactor + C1~C5 Regression]
        ↓
[Core v1 Frozen]
        ↓
[Final Hypothesis Milestone 재설계]
        ↓
[필요 시 Higgsfield/API/유료 수단 확보]
        ↓
[품질 / Frontier Usage 가설 검증]
```

---

# 22. Codex가 기억해야 할 최종 요약

> **Frontier가 팀장, Local Models가 교체 가능한 팀원으로 동작하는 작고 실제적인 제작 Loop Core를 만든다. 먼저 이 Loop가 실제로 만들어지고 제대로 작동함을 증명한다. Production-grade orchestration, comprehensive recovery, 범용 framework, 품질 우위 증명은 Core v1 이전의 목표가 아니다.**

그리고:

> **현재까지 만든 것은 버릴 실패물이 아니라, Compact Core를 추출·증명하기 위한 연구·evidence 자산이다.**
