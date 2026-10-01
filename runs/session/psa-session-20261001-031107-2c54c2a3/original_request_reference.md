# Agent Loop — S3C Actual Session E2E Proof

이 프롬프트는 Durable Handoff 이후의 **새 User Request**다.

현재 Handoff에서 확인한 상태:

```text
S3B SESSION-BOUND SCENARIO INTEGRATION = LOCAL-VERIFIED
S3C ACTUAL SESSION E2E PROOF = READY / NOT STARTED
```

이 요청으로 **S3C — Actual Session E2E Proof**를 시작하라.

별도 사용자 재확인은 필요하지 않다.  
단 아래 Ready Gate와 Stop Condition을 모두 지켜야 한다.

---

# 1. S3C의 단일 명제

이번 milestone이 증명할 것은 다음이다.

> 하나의 실제 User Request에서 생성한 Frozen Work Specification과 Session binding을 사용하여, fixed Scenario A를 실제로 한 번 실행하고, 실제 evidence를 통해 Session lifecycle이 어디까지 성립하는지 확인한다.

S3B를 다시 구현하거나 확장하는 milestone이 아니다.

기본 runtime source 변경은 **0**이어야 한다.

---

# 2. Canonical baseline

Repository:

`D:\VSCODE-WorkSpace\Others\Agent-Loop-Core`

Remote:

`https://github.com/1-3127/Agent-Loop-Core.git`

Expected S3B baseline:

```text
branch:
session-bound-scenario-s3b

commit:
89201d2511985a054cfc3045768e6b29ef62e5cf
```

새 Codex 세션에서 이미 확인한 사실:

- local HEAD는 위 commit과 일치
- tracking branch도 일치
- working tree clean
- live remote는 아직 새 세션에서 재조회하지 않음

따라서 **첫 작업은 live remote까지 다시 조회하는 것**이다.

최소 확인:

```text
local HEAD
tracking ref
live origin/session-bound-scenario-s3b
working tree
current diff
```

세 값이 모두 exact `89201d2511985a054cfc3045768e6b29ef62e5cf`이고 tree가 clean인 경우에만 S3C branch를 만든다.

권장:

`session-e2e-s3c`

baseline mismatch가 있으면 자동 해결하지 말고 중단한다.

---

# 3. Authority

Handoff를 이미 읽었으므로 reasoning history를 복원하지 않는다.

작업 전 필요한 canonical authority만 다시 확인한다.

- 적용되는 `AGENTS.md`
- `Agents/workflow.md`
- `CORE_V1_FREEZE.md`
- `docs/Agent-Loop_Direction_Gate_v1.md`
- S1 Session Contract / Work Specification / Handoff template
- `docs/session/S2_SESSION_INTEGRATION_SEAM_AUDIT.md`
- `docs/session/S3A_SESSION_BOUNDARY_LOCAL_PROOF.md`
- `docs/session/S3B_SESSION_BOUND_SCENARIO_INTEGRATION.md`
- `src/session/session_boundary.py`
- `src/scenario_a/session_binding.py`
- current L6 / L7 / Worker / Reviewer implementation
- current asset manifest

Historical status를 재판정하지 않는다.

---

# 4. 이번 User Request / Work Specification

이번 프롬프트 자체를 S3C의 User Request로 취급한다.

Request Type:

`NEW_WORK`

현재 context는 다음 Work Specification을 확정하기에 충분하다.

기술 parameter 선택을 User에게 다시 묻지 않는다.

## Goal

Work Specification 문서에 다음 문장을 그대로 포함한다.

> 현재 canonical Scenario A input을 사용하여 실제 Single Image → Multiview → 3D Geometry Session을 한 번 실행하고, 최종 GLB를 사용자 평가 가능한 상태까지 만든다.

## Must-Have 1

> right/left/back multiview는 canonical front source와 동일한 대상을 유지하고, 주요 실루엣과 구조 파츠를 보존하며, 심각한 crop, missing/detached major part, cross-view identity contradiction이 없어야 한다.

## Must-Have 2

> final GLB는 canonical source와 동일한 대상으로 인식 가능하도록 주요 실루엣, 비율, 주요 구조 파츠를 보존해야 하며 심각한 변형이나 분리된 주요 파츠가 없어야 한다.

## Intended deliverable

- actual final GLB
- actual final geometry Review evidence
- diagnostic renders/references
- immutable Session/Spec/execution lineage
- INTERNAL_ACCEPT가 성립할 경우 Delivery Package

이번 acceptance scope가 아닌 것:

- Texture
- PBR
- UV
- benchmark quality
- generalized geometry-quality research

---

# 5. Acceptance authority

최소 authority:

```text
USER_CURRENT_REQUEST
CANONICAL_SOURCE
```

실제 `source_ref`는 이번 Request와 canonical source identity를 정확히 가리키게 작성한다.

Acceptance criteria:

## AC-MULTIVIEW-COHERENCE

`blocking_when_unmet = true`

> Generated multiview images must depict the same canonical source object, preserve its recognizable major silhouette and structural parts, and contain no severe crop, missing/detached major part, or cross-view identity contradiction.

## AC-GEOMETRY-IDENTITY

`blocking_when_unmet = true`

> The final GLB must remain recognizable as the canonical source object by preserving its major silhouette, proportions, and structural parts without severe deformation or detached major parts.

Stage projection:

```text
multiview:
- AC-MULTIVIEW-COHERENCE

geometry:
- AC-MULTIVIEW-COHERENCE
- AC-GEOMETRY-IDENTITY
```

Final geometry stage는 모든 declared criterion을 cover한다.

추가 User-quality criterion을 임의로 만들지 않는다.

특히 다음을 hidden acceptance authority로 추가하지 않는다.

- smoothness
- topology aesthetics
- UV
- texture
- PBR
- normals
- benchmark
- 특정 눈/표지판 디테일 자체

단 그러한 실제 결함이 위 criterion의 identity / major structure 위반이라고 Reviewer가 판단하는 것은 가능하다.

---

# 6. Canonical source

Current manifest expected identity:

```text
path:
D:\VSCODE-WorkSpace\Comfy-UI\work\input\hunyuan-official-demo-padded.png

sha256:
8a6dd9ca3f8984b31c1243e7698cd5030b423464d80e0ad763609148e0ff4f51

dimensions:
768 x 768

role:
front
```

production effect 전에 실제 bytes/hash/dimensions를 다시 검사한다.

불일치하면 manifest/source를 수정하거나 과거 값으로 강제하지 않는다.

종료:

`BLOCKED_INPUT_IDENTITY_CHANGED`

---

# 7. Fixed capability

이번 Session의 Interpretation Envelope:

`fixed_four_view_glb_seed_only`

실행 topology:

```text
canonical front
→ Qwen right
→ Qwen left
→ Qwen back
→ multiview semantic Review
→ Hunyuan3D MV geometry
→ Blender diagnostic
→ geometry semantic Review
→ if authorized REVISE:
     one bounded correction
→ final Review
→ INTERNAL_ACCEPT candidate
```

현재 seed-only correction policy는 그대로 식별한다.

좋은 quality-improvement policy라고 주장하지 않는다.

S3C에서는 정책을 변경하지 않는다.

---

# 8. Proof integrity — 가장 중요한 규칙

## 첫 production effect 전

문제 발견 시 수정/중단 가능하다.

## 첫 production effect 후

해당 actual Session은 immutable proof attempt다.

다음을 금지한다.

- 같은 Session 재실행
- child ID 교체 후 우회 실행
- run directory 삭제
- seed reroll
- 추가 Reviewer 호출
- blind retry
- PASS hunting
- runtime source 수정 후 같은 proof 재개
- workflow/model parameter 수정
- 실패한 evidence 삭제

첫 production effect 이후 implementation defect가 발견되면:

```text
S3C ACTUAL PROOF = NOT PASSED
reason = IMPLEMENTATION_DEFECT
```

로 종료한다.

수정은 별도 repair milestone이다.

---

# 9. Checkpoint 1 — Actual Readiness + Genuine Specification Freeze

아직 actual generation/review/render를 실행하지 않는다.

## 9.1 Git

확인:

- local HEAD
- tracking HEAD
- live remote HEAD
- clean tree
- current diff empty
- protected refs unchanged
- 기존 S3C Session/run namespace 없음

## 9.2 Genuine Work Specification

권장:

`docs/session/S3C_WORK_SPECIFICATION_v1.md`

Goal / Must-Haves / criteria / authority / interpretation envelope를 durable artifact로 기록한다.

Reasoning transcript는 넣지 않는다.

## 9.3 Freeze

기존 S3A API 사용:

- `freeze_specification`
- `FinalizedFields`
- `AcceptanceCriterion`
- `AuthorityReference`

조건:

```text
specification_ready = true
blocking ambiguities = none
```

새 parser를 만들지 않는다.

## 9.4 Session identities

실제 fresh identities를 한 번 결정한다.

```text
session_id
logical_loop_run_id
l6_child_id
bridge_child_id
correction_child_id
```

모두 서로 달라야 한다.

기존 namespace와 충돌 금지.

결정 후 변경 금지.

## 9.5 Stable Session directory

하나의 stable Session record directory를 사용한다.

현재 repository convention을 우선한다.

DB/global manager를 만들지 않는다.

## 9.6 Scenario binding

S3B `prepare()`를 그대로 사용하여:

- Goal
- Must-Haves
- stage criteria
- child IDs
- fixed capability
- existing caps

를 bind한다.

## 9.7 Existing zero-effect preflight

`run_session(... execute=False)`

실행.

확인:

- Specification
- source identity
- manifest
- workflow hashes
- model presence/size
- renderer
- script
- child identities
- capability

production effects는 아직 0이어야 한다.

## 9.8 Live ComfyUI

read-only:

`http://127.0.0.1:8188/system_stats`

확인.

실제 `devices` 응답 필요.

현재 ComfyUI가 꺼져 있고 기존 launch 방법이 repository/environment에서 명확하게 확인되면 기존 runtime만 시작해도 된다.

하지 말 것:

- 설치
- update
- dependency 수정
- model download
- workflow 수정
- config migration

안전한 기존 launch path를 확인할 수 없으면:

`BLOCKED_RUNTIME_UNAVAILABLE`

## 9.9 Reviewer auth

실제 `reviewer_auth.auth_mode(...)`를 검사한다.

허용:

`CHATGPT_ACCOUNT`

다음이면 actual Reviewer 실행 금지:

```text
API_KEY
UNKNOWN
```

API 환경변수를 임의 제거하여 우회하지 않는다.

## 9.10 Ready verdict

모두 PASS하면:

`S3C ACTUAL_EXECUTION_READY`

이때 actual counts:

```text
Comfy submissions = 0
semantic Reviewer = 0
Blender production = 0
correction dispatch = 0
```

Checkpoint evidence/document를 commit한다.

---

# 10. Checkpoint 2 — Exactly One Actual Bound Session

Checkpoint 1 PASS 후 별도 사용자 확인 없이 진행한다.

이 프롬프트가 **actual one-shot execution 승인**이다.

기존 S3B entry를 사용한다.

```python
run_session(
    parent_ref,
    ...,
    execute=True
)
```

한 번만 호출한다.

새 orchestration framework는 만들지 않는다.

필요하면 최소 one-shot driver 또는 documented invocation만 추가할 수 있다.

---

# 11. Actual evidence

## L6 Worker

실제로 확인:

- `/prompt`
- prompt_id
- `/history`
- right PNG
- left PNG
- back PNG
- bytes/hash/dimensions
- Plan / Work Order / Report / Execution
- Session sidecars

## Multiview Reviewer

실제로 확인:

- Codex subprocess started
- `reviewer_mode = CODEX_CLI`
- `auth_mode = CHATGPT_ACCOUNT`
- actual image attachments
- Review Request
- raw Result
- Invocation
- hashes
- criterion coverage
- authority validation

## Geometry Worker

실제로 확인:

- actual Hunyuan3D prompt
- actual GLB
- artifact bytes/hash
- exact reviewed multiview input lineage

## Blender

실제로 확인:

- actual Blender process
- actual diagnostic renders
- source GLB → render manifest linkage

## Geometry Reviewer

실제로 확인:

- actual semantic Reviewer
- actual attachments
- exact bound criteria
- raw Result
- coverage
- suggested action authority

---

# 12. Outcome policy

## Initial geometry PASS

```text
L6 actual
→ bridge actual
→ geometry PASS
→ INTERNAL_ACCEPT candidate
```

correction = 0.

## Initial geometry REVISE

기존 authorized action만 허용.

최대 correction = 1.

```text
REVISE
→ one correction
→ final Review
```

Final PASS:

→ INTERNAL_ACCEPT candidate

Final REVISE:

→ 기존 budget-exhaustion semantics 그대로 종료.

두 번째 correction 금지.

## HUMAN_REQUIRED

Specification ambiguity로 자동 변환하지 않는다.

## UNRESOLVED

retry 금지.

## REVIEW_CONTRACT_VIOLATION

raw Result 보존.

retry/correction/PASS coercion 금지.

---

# 13. INTERNAL_ACCEPT proof

`run_session()` 반환 문자열만 신뢰하지 않는다.

실제 evidence에서 다시 검증한다.

필수:

- current Specification
- current Session binding
- final artifact
- artifact hash
- final geometry Review
- actual Invocation
- criterion coverage
- child terminals
- exact source GLB linkage
- stale/unbound evidence 없음

성립 시:

```text
S3C ACTUAL BOUND LOOP = VERIFIED
INTERNAL_ACCEPT = VERIFIED
DELIVERED = false
```

이것만으로 Session E2E VERIFIED가 아니다.

---

# 14. Delivery Package

INTERNAL_ACCEPT 성공 시에만 기존:

`prepare_delivery()`

를 사용한다.

새 transport를 만들지 않는다.

Package에 실제:

- Session
- Specification
- logical Loop
- canonical source
- final GLB
- final Review
- INTERNAL_ACCEPT identity

가 들어가야 한다.

검증 후:

`S3C DELIVERY PACKAGE = VERIFIED`

가능.

아직 `DELIVERED`는 아니다.

---

# 15. Actual User Delivery / Receipt Boundary

`ACTUAL SESSION E2E = VERIFIED`

가 되려면 실제 User-facing submission과 authentic observable receipt가 필요하다.

local JSON에 `DELIVERED`라고 쓰는 것은 proof가 아니다.

Codex가 final response를 보내기 전에 미래 receipt를 예측해서 기록하지 않는다.

필요 evidence:

- Delivery Package identity
- exact artifact identity
- actual channel
- actual timestamp
- message / attachment / transport acknowledgement
- provenance

S3A `SubmissionEvidence` 형식을 채웠다는 이유만으로 authenticity가 생기지 않는다.

## Host가 post-submission receipt를 제공하지 않는 경우

새 API/service/plugin을 만들지 않는다.

정확한 판정:

```text
S3C ACTUAL BOUND LOOP = VERIFIED
INTERNAL_ACCEPT = VERIFIED
S3C DELIVERY PACKAGE = VERIFIED
ACTUAL USER DELIVERY RECEIPT = NOT VERIFIED / BLOCKED
ACTUAL SESSION E2E = NOT VERIFIED
```

이 결과도 유효한 S3C proof다.

---

# 16. Fresh-context 경계

이번 S3C actual execution이 성공해도 자동으로:

`EXTERNAL FRESH-CONTEXT RESET = VERIFIED`

라고 하지 않는다.

외부 host reset evidence가 없으면:

`NOT VERIFIED`

유지.

---

# 17. Semantic closure 실패 시

Actual runtime은 정상 실행됐지만 geometry가 one correction 후에도 PASS하지 못하면:

```text
S3C ACTUAL RUNTIME PATH = EXECUTED
S3C ACTUAL BOUND LOOP = NOT PASSED
ACTUAL SESSION E2E = NOT VERIFIED
```

S3B는 여전히 LOCAL-VERIFIED다.

즉시 geometry-quality 개선 작업을 시작하지 않는다.

그 evidence는 이후 별도 Scenario A Quality/L7 milestone의 입력이다.

---

# 18. Historical L7 verdict

Historical:

```text
L7-M3 ACTUAL CLOSED FEEDBACK PROOF = NOT PASSED
LEVEL 7 CLOSED FEEDBACK PIPELINE = NOT VERIFIED
```

를 rewrite하지 않는다.

이번 S3C에서 fresh correction PASS가 나오더라도 별도 fresh evidence다.

S3C 완료와 동시에 자동으로:

`LEVEL 7 = VERIFIED`

라고 선언하지 않는다.

---

# 19. Code-change policy

S3C는 proof milestone이다.

기본 production source diff:

`0`

다음 변경 금지:

- Frozen Core
- S3A
- S3B architecture
- L6 behavior
- L7 behavior
- correction policy
- Reviewer schema
- Worker schema
- workflow
- model parameter

actual execution 전에 purely proof-driver/documentation 문제가 발견되면 최소 수정 여부를 판단할 수 있다.

하지만 **첫 production effect 이후 runtime defect는 그 자리에서 수정하지 않는다.**

별도 repair milestone로 넘긴다.

---

# 20. Documentation

Milestone document:

`docs/session/S3C_ACTUAL_SESSION_E2E_PROOF.md`

권장 Work Specification:

`docs/session/S3C_WORK_SPECIFICATION_v1.md`

checkpoint마다 새 normative document를 만들지 않는다.

Proof document 최소 기록:

- exact baseline
- local/tracking/live remote
- Specification SHA
- Session/Loop/child IDs
- canonical source SHA
- runtime readiness
- auth mode
- actual invocation counts
- prompt IDs
- artifacts
- artifact SHA
- Review IDs/hashes
- verdict/action
- correction count
- INTERNAL_ACCEPT
- Delivery Package
- receipt availability
- final Session state
- protected state
- commits
- known limits

reasoning trajectory는 기록하지 않는다.

---

# 21. Git policy

```text
one branch = S3C milestone
commit = meaningful checkpoint
```

main merge/tag/release 없음.

Actual evidence를 없애기 위한 reset/rebase/history rewrite 금지.

Generated model/cache/workspace 전체를 repo에 복제하지 않는다.

Large final asset은 기존 evidence convention을 먼저 확인한다.

repo에 넣지 않는 경우에도 최소:

- canonical absolute path
- byte count
- SHA-256
- producing run/prompt/report

를 남긴다.

---

# 22. Final classification ladder

## A. Full Session proof

실제 submission receipt까지 authentic하게 확인된 경우에만:

```text
S3C ACTUAL SESSION E2E PROOF = VERIFIED
ACTUAL SESSION E2E = VERIFIED
ACTUAL USER DELIVERY RECEIPT = VERIFIED
```

## B. Actual Loop success / Delivery boundary blocked

```text
S3C ACTUAL BOUND LOOP = VERIFIED
INTERNAL_ACCEPT = VERIFIED
S3C DELIVERY PACKAGE = VERIFIED
ACTUAL USER DELIVERY RECEIPT = NOT VERIFIED / BLOCKED
ACTUAL SESSION E2E = NOT VERIFIED
```

## C. Semantic closure failure

```text
S3C ACTUAL RUNTIME PATH = EXECUTED
S3C ACTUAL BOUND LOOP = NOT PASSED
ACTUAL SESSION E2E = NOT VERIFIED
```

## D. Infrastructure uncertainty

```text
S3C ACTUAL PROOF = UNRESOLVED
ACTUAL SESSION E2E = NOT VERIFIED
```

## E. Implementation defect after production effect

```text
S3C ACTUAL PROOF = NOT PASSED
reason = IMPLEMENTATION_DEFECT
ACTUAL SESSION E2E = NOT VERIFIED
```

실제 evidence에 해당하는 하나를 사용한다.

---

# 23. Stop Conditions

즉시 중단:

- local/tracking/live remote baseline mismatch
- dirty unexpected worktree
- canonical source identity mismatch
- Specification Ready failure
- unresolved decision-critical Specification ambiguity
- capability mismatch
- model/workflow identity mismatch
- child namespace collision
- Comfy runtime unavailable + safe existing launch path 없음
- Reviewer auth != CHATGPT_ACCOUNT
- actual submission state uncertainty
- production effect 후 implementation defect
- authentic receipt가 없는데 DELIVERED/CLOSED 기록이 요구됨

중단 시 상태를 좋게 보이도록 재시도하지 않는다.

---

# 24. Out of Scope

S3C에서 하지 않는다.

- geometry quality research
- normal/export investigation
- extraction investigation
- shading investigation
- correction-policy redesign
- extra seed rerolls
- additional view strategy
- benchmark
- cost experiment
- generic framework
- Core refactor
- transport implementation
- fresh-context infrastructure implementation
- main merge
- tag
- release

---

# 25. Checkpoint reporting

## Checkpoint 1

```text
## S3C Checkpoint 1 — Actual Readiness + Specification Freeze

- baseline:
- local / tracking / live remote:
- working tree:
- Specification:
- Specification SHA:
- Session / Loop / child IDs:
- canonical input:
- Comfy readiness:
- Reviewer auth:
- zero-effect preflight:
- actual production effects:
- commit:
- verdict:
```

PASS 조건:

`S3C ACTUAL_EXECUTION_READY`

Checkpoint 1 PASS 전에는 actual `/prompt`, semantic Reviewer, Blender production render 금지.

## Checkpoint 2

```text
## S3C Checkpoint 2 — One Actual Bound Session

- actual Worker calls:
- actual Reviewer calls:
- actual Blender calls:
- L6:
- multiview Review:
- GLB:
- geometry Review:
- correction:
- final Review:
- INTERNAL_ACCEPT:
- actual evidence:
- commit:
- verdict:
```

## Checkpoint 3

INTERNAL_ACCEPT가 있을 때만:

```text
## S3C Checkpoint 3 — Delivery Boundary

- Delivery Package:
- artifact identity:
- actual User-facing submission:
- observable receipt:
- receipt authenticity:
- Session terminal:
- final classification:
```

---

# 26. First action

지금부터 **S3C Checkpoint 1 — Actual Readiness + Genuine Specification Freeze**를 수행하라.

순서:

1. live remote 포함 baseline 재검증
2. S3C branch 생성
3. canonical authority/source 재확인
4. genuine Work Specification 작성
5. freeze + Session binding
6. zero-effect preflight
7. live Comfy readiness
8. Reviewer auth 확인
9. Checkpoint 1 evidence 기록/commit
10. PASS일 경우 즉시 Checkpoint 2 actual one-shot execution으로 진행

Checkpoint 1 PASS 후 추가 사용자 허가는 요구하지 않는다.

이 프롬프트가 actual one-shot execution 승인이다.

단 **production proof integrity rule**, **no retry**, **stop conditions**는 끝까지 유지한다.