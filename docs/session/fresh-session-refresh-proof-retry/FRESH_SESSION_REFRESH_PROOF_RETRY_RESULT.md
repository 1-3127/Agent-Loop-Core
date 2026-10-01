# Fresh Session / Refresh Proof Retry — 실제 실패 결과

작성: 2026-10-01T15:39:54.918764+09:00.

**FRESH SESSION / REFRESH PROOF = NOT VERIFIED**
Actual executor classification: **RUNTIME_FAILED**. Canonical L6 및 새 Session terminal: **FAILED**.
원인: 첫 right view의 `Worker PNG dimensions differ` / `VIEW_STAGE`.
별도 source 진단: **CONTRACT_DEFECT_FOUND — current PNG와 fixed 768×768 view 계약의 호환성**. 이 진단은 actual terminal이나 Worker SUCCESS를 덮어쓰지 않는다.

## 실제 결과와 원인

현재 Reference는 467×539 PNG다. ComfyUI는 right image 464×536을 실제 생성했고 adapter Report와 history는 SUCCESS다. L6 `run_worker()`의 `src/scenario_a/l6_pipeline.py:374–376`은 generated PNG와 Report 모두 정확히 768×768이어야 한다고 검사하여 거부했다. L6 execution artifact는 null, state는 FAILED이며 Session도 FAILED로 종료됐다.

`preflight():98–152`는 새 PNG의 integrity/identity와 plan/workflow/model을 검사하지만 768×768 입력 제한이나 normalization을 적용하지 않는다. 고정 workflow의 LoadImage→VAEEncode→KSampler→VAEDecode 경로는 원본 latent 크기를 사용한다. 현지 ComfyUI VAE crop 코드는 compression ratio에 맞춰 크기를 줄인다. [추론] 467×539→464×536은 이 crop 동작과 일치하며, 임의 current PNG 허용과 기존 768×768 출력 gate가 호환되지 않는다. 실제 Worker/model generation 장애나 semantic rejection으로 혼동하지 않는다.

현재 source/test를 고치거나 입력을 crop/pad/resize해 같은 attempt를 재실행하지 않았다. 새 hidden ID, seed 확대, artifact replacement, retry/resume0. Correction은 semantic REVISE까지 도달하지 않아 수행하지 않았다.

## 요청·명세·분리

시작 `stabilization-current-reference-binding` / `03d62fb0ab8b3a7ac8a89c548961830475e72e92`, clean, local/tracking/live equal.
새 branch `fresh-session-refresh-proof-retry`.
현재 요청은 사진 속 석등 GLB 한 개이며 넓은 지붕·등실·받침 실루엣과 실제 중앙 사각 개구부를 필수로 삼았다. 사람·앞쪽 기둥·배경은 대상에서 제외했다. 결정적 intent ambiguity가 없어 추가 질문0.
현재 Request/Reference와 durable contract로 새 [Frozen Specification](STONE_LANTERN_WORK_SPECIFICATION_v1.md)을 독립 작성했다. 이전 candidate는 historical 비교자료이며 frozen 내용으로 복사하지 않았다.

- Session: `fsr-session-20261001-152846-ccab2a25`.
- Loop: `fsr-loop-20261001-152846-ccab2a25`.
- L6: `fsr-l6-20261001-152846-ccab2a25`.
- Bridge / correction IDs는 예약 설계만 했으며 child 실행 namespace는 미생성이다.
- Reference SHA-256: `9da5ed9e7f3490d058673122a7bd50b46635d4f0b5a36ca3199f0c1636cd17e5` (362,412 bytes).
- Multiview: `LANTERN_VIEW_IDENTITY`.
- Geometry: `LANTERN_GLB_SILHOUETTE`, `LANTERN_SQUARE_APERTURE`.
- 세 blocking criterion이 지원 stage에 모두 배정됐다. 실제 Reviewer0으로 criteria 평가/coverage SATISFIED를 주장하지 않는다.

이 chat은 이전 proof/closed Session과 분리된 projectless chat이다. 초기에 첨부 historical 자료를 읽었으나 이전 raw reasoning/transcript/active trajectory는 읽지 않았고 old Session을 reopen하지 않았다. 과거 Spec/artifact/verdict/correction state를 이번 execution 입력으로 사용하지 않았다. 별도 host context reset의 기계적 증명은 주장하지 않는다.

## 실제 Reference propagation

User PNG bytes → immutable CurrentReference FileIdentity → Frozen Spec REF authority source → 새 Session binding → Scenario parent → L6 preflight → exclusive per-attempt front.png → right Plan/Work Order → actual Comfy invocation/history/PNG metadata를 확인했다.
원본과 staged copy의 bytes/SHA-256은 동일하다. actual LoadImage node1은 `l6/fsr-l6-20261001-152846-ccab2a25/front.png`를 사용했다.
Prompt ID: `e4ccf5d2-1ec5-40a1-a78b-6184ff7bac36`; history completed=true/success, execution_cached nodes=[]; actual PNG embedded prompt도 동일 입력을 기록한다.
Old fixed penguin source fallback0. left/back/geometry는 실행되지 않았으므로 그 actual propagation은 미검증이다.

## Readiness·호출·verdict

| 항목 | 이번 관측 |
|---|---|
| 전체 regression | 231/231 PASS, 450.000초; 실패/오류/skip0 |
| regression external effects | network0 / production subprocess0 / 기존 import smoke1 |
| ComfyUI | endpoint·19 required nodes·model registration·empty queue PASS |
| workflow/model assets | 4 pinned workflow hash / 6 model size PASS; large model 전체 hash 미측정 |
| Blender readiness | 실제 --version 5.2.0 LTS 및 script identity PASS; production render0 |
| Reviewer readiness | CHATGPT_ACCOUNT / 같은 read-only CLI transport probe PASS; sandbox 초기화 실패2는 별도 보존 |
| readiness inference | 성공1; actual semantic artifact Review 수에 포함하지 않음 |
| I-03 | 실제 첫 effect 전 repository3 / external7 namespace gate PASS |
| CP1 generation effects | 0 |
| actual Worker / Comfy submissions | 1 / 1 (right) |
| actual geometry / Blender / semantic Reviewer | 0 / 0 / 0 |
| actual correction / Delivery | 0 / 0 |
| Reviewer verdict | 미생성; semantic acceptance 미평가 |
| INTERNAL_ACCEPT | 미생성 |
| canonical terminal | L6 FAILED / VIEW_STAGE; Session FAILED |

[CP1 readiness](CP1_READINESS.json)는 당시 dry/runtime 관측 PASS다. Actual dimensions contract failure가 이후 나타났으므로 readiness PASS나 synthetic regression을 전체 generation/Refresh proof로 승격하지 않는다.

## 보호·Git·종료

기존 tracked502개 byte SHA-256 모두 동일하다. source/test 변경0, 이전 closed Session/역사적 evidence/고정 input/manifest 변경0. 4 external workflow hashes와 6 model size/mtime 및 old fixed source hash/size/mtime도 동일하다. 새 Session terminal은 FAILED로 보존했고 old Session reopen0.
CP1: `291b9be9e6038145daea7fc3ce7cc1e31ab791d7` (subject: `docs(proof): freeze fresh-session stone-lantern specification and readiness`).
CP2 subject: `docs(proof): record fresh-session stone-lantern actual result`.
이번 기록을 정상 commit/push하고 local=tracking=live, clean 및 protected refs를 확인한 후 종료한다. 이 commit 자체에 self-referential hash나 아직 실행하지 않은 push 성공을 기록하지 않는다. 최종 publication은 별도 사용자-facing completion report에 기록한다.

Evidence: [actual entry](ACTUAL_ENTRY_RESULT.json), [actual lineage/protection/counts](ACTUAL_VALIDATION.json), [dimension diagnosis](DIMENSION_FAILURE_DIAGNOSIS.json), [Comfy history](comfy_history/l6-right.json), [rejected PNG metadata](RIGHT_VIEW_PNG_METADATA.json). RIGHT_VIEW_REJECTED.png는 실패 evidence이며 accepted GLB/Delivery가 아니다.
