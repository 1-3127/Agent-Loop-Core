# L7-M2 Minimal Feedback Controller / Local Validation

## 결과

**L7-M2 MINIMAL FEEDBACK CONTROLLER = READY**

실제 L7-M1의 immutable REVISE를 static source로 읽어 structured action을 resolve하는 controller를 구현했다. 두 action 경로는 mock/temporary fixture로 검증했다. Production Comfy submission=0, Blender diagnostic process=0, Frontier semantic Reviewer=0, automatic production retry=0이다.

**LEVEL 7 CLOSED FEEDBACK PIPELINE = NOT VERIFIED**. Actual correction/closed-feedback proof와 L7-M3는 실행하지 않았다. 기존 GLB를 M2 fresh output으로 재포장하지 않았다.

## Baseline / Repository

- Repository: `D:\VSCODE-WorkSpace\Others\Agent-Loop-Core`
- Remote: https://github.com/1-3127/Agent-Loop-Core.git
- Working branch: `scenario-a-l7`
- 시작 local HEAD / origin/scenario-a-l7: `ef8921505fad3e553f6a1f8053ad0f34687bd99b` (`Verify Level 7 geometry review bridge`)
- 시작 working tree: clean. Live remote baseline 일치 확인 후 구현했다.
- Frozen main/origin/main/tag target: `7eee393801f4d8c14278b43ebcbaabaec7ccc9df`
- `core-v1.0.0` annotated tag object: `8b962c5d94828af852d020237554606c305ef01e`
- `scenario-a-l6` local/remote: `840b138cc023c623108c44c3944948b065300f99`
- M2 commit은 이 report를 포함하는 commit이다: `git log -1 -- docs/l7/L7_M2_FEEDBACK_CONTROLLER.md`. Commit 후 normal push, local/remote HEAD 일치, clean 상태를 별도 최종 확인한다.
- main merge, L6 update, tag/release 변경 없음.
- 적용 지침: root AGENTS.md, Agents/workflow.md, Others/AGENTS.md, Compact AGENTS.md, Direction Gate v1, 이번 L7-M2 명시 지시.

## Source Actual Geometry Review

- Source run: `l7-m1-20260930-184618-3703fee4`
- [Result](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l7/l7-m1-20260930-184618-3703fee4/review_result.json): SHA-256 `f4b08fb1a8eaf2c5778971131e7d97ac24cb038945d9f7ee6360a3a3445446d3`
- [Invocation](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l7/l7-m1-20260930-184618-3703fee4/review_invocation.json): SHA-256 `ce1342de0f6e4852755ecc18bd2aaba38c135df3a239ca7f530033b8801492ab`
- [Terminal](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l7/l7-m1-20260930-184618-3703fee4/terminal.json): SHA-256 `24c2dfe9fca91a016a7a7ada4d3c3a68c7d27952b1c8bfa8832c79aa88cd433b`
- [Render manifest](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l7/l7-m1-20260930-184618-3703fee4/render_manifest.json): SHA-256 `a88e8b93370b3d650c9ba4c2cffbea4f45bc3ddba2297ca87780fd8fd3fbb0bc`
- Terminal GEOMETRY_REVIEWED; actual CODEX_CLI process_started=true; request/result/invocation/8-image identities 다시 검증했다.
- Verdict REVISE; structured action `REGENERATE_GEOMETRY`, target `geometry`; prior dispatches=0.
- Reviewer blocker: reference에서 보이는 눈 구조가 geometry diagnostic에서 누락됨; 전면 HY3D raised letter 형상이 크게 왜곡됨.
- Action은 Reviewer diagnostic이며 geometry generation이 원인이라는 causal proof는 아니다.
- Source GLB: `D:\VSCODE-WorkSpace\Comfy-UI\work\output\mesh\l6\l6-m3-20260930-164920-8109160a\geometry_00001_.glb`
- GLB bytes1139016; SHA-256 `1cc00067c772f3efdad34f36cb44c4b5d54ed5bfa4b03a4888a3f3de80fca252`.
- Source prior geometry Plan seed: `528364197559477`.
- Source M1/L6 evidence는 read-only. Controller는 새 namespace만 사용할 수 있고 terminal source run을 reopen하지 않는다.

## 변경 파일 / Existing-First

| 신규 파일 | 역할 / 필요한 이유 |
|---|---|
| [l7_feedback_controller.py](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/src/scenario_a/l7_feedback_controller.py) | Fixed one-action controller; source proof, policy, seed, current refs, budgets/reservations, stage 연결, terminal/usage, safe CLI |
| [test_l7_feedback_controller.py](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/tests/test_l7_feedback_controller.py) | 44 tests; synthetic fixture 및 production effect tripwires, 실제 source의 read-only preflight |
| [L7_M2_FEEDBACK_CONTROLLER.md](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/docs/l7/L7_M2_FEEDBACK_CONTROLLER.md) | 이번 local implementation proof와 scope/protection 기록 |

Direct reuse:

- `l6_pipeline`: preflight/asset contract, prior Plan builders, file SHA/reference, exclusive JSON writing, atomic state writing, full PNG identity, Worker Report validation, execution report contract.
- `codex_to_comfy`: validate_plan, actual future Worker primitive `run`, output namespace guards, GLB structural identity validation. M2에서는 `run`을 mock으로만 호출했다.
- `l7_geometry_review`: full verified L6/source review/render evidence validation, diagnostic action contract, Blender executable identity.
- `l7_blender_diagnostic`: 기존 standalone script를 그대로 future subprocess command에 연결. Script SHA `d71f932c5679d6e1ad453e1fa39d75c919fec5c1ff975d22c1114ed53f249cd1` 불변.
- Frozen Core `result_review_adapter`: request0.2/Result0.3, schema/ref/invocation validation, existing one-call Reviewer primitive. Core/schema 변경=0.

기존 L6/M1 top-level runner는 historical run input 및 해당 stage budget/guard에 묶여 있다. 새 controller에서 reopened historical namespace나 global monkeypatch를 사용하지 않고, 새 current-reference manifest와 fixed reservation을 최소 범위로 추가했다. Render contract 검증은 기존 M1 검증을 참고해 current GLB에 바인딩했다. Renderer 자체는 변경하지 않았다.

기존 helper를 노출하기 위한 변경도 필요하지 않았다. 기존 source/tests/docs/evidence 수정=0. 새 dependency/framework/state engine/planner/DAG/DB/resume manager 없음.

## Controller Input / Source Validation

`run_feedback(run_id, source_review_run, comfy_root, blender_executable, worker_timeout, review_timeout, render_timeout, execute=False)`.

Default callable / CLI는 effect-free preflight다. Future actual execution은 명시적 `--execute`가 필요하며 M2에서 실제 환경에는 사용하지 않았다.

Preflight는 terminal GEOMETRY_REVIEWED, run identity, complete source record path/hash set, Review schema 및 actual invocation, exact diagnostic renders/references, verified L6 geometry/execution/embedded inputs, prior Plan/workflow/model을 검사한다. 실제 M1의 known terminal SHA도 고정한다. Source action은 free-text에서 추론하지 않는다.

Initial에는 source Result/Invocation/Request/render manifest/GLB/multiview/references/prior geometry Plan 및 view Plan refs, action/verdict, 예측 seed, fixed limits가 기록된다. Initial을 effect 이전에 exclusive 생성하고 후속 records는 initial path/SHA를 참조한다.

Preflight hash checks는 read-only다. Execute path의 source-invalid rejection은 FAILED/SOURCE_REVIEW_INVALID와 zero-consumed durable initial/usage/terminal을 만든다. Invalid seed/action policy는 FAILED/REVISION_POLICY다. Workflow/model/runtime preflight blocker를 실제 Worker FAILED proof로 꾸미지 않는다.

## Action / Seed Policy

허용되는 correction은 정확히 하나다.

- `REGENERATE_GEOMETRY / geometry`
- `REGENERATE_VIEW / right|left|back`

front/all/multiple/arbitrary target, unknown action, malformed verdict/action은 reject한다. PASS는 NONE/null 및 blocker 없음; HUMAN_REQUIRED는 HUMAN_REQUIRED/null이다. Free-text blocker 문장은 실행 명령으로 해석하지 않는다.

첫 revision ordinal=1, `revision_seed = previous_seed + 1`. Boolean/noninteger/negative/uint64 overflow seed는 reject한다.

- Actual source geometry: `528364197559477 → 528364197559478`.
- View fixture: `29481 → 29482`.
- Prior Plan의 workflow/output node/prompt/other parameters는 유지한다. 변경은 task/run identity, seed, current input/output namespace뿐이다.
- Workflow/model/resolution1024/octree128/sampler/steps/cfg/conditioning order는 변경하지 않는다.

`revision_action.json`은 planned action/target, source Review, ordinal, previous/revision seed, initial action budget/status를 기록한 immutable document다. 실제 consumed count는 exclusive reservation과 후속 state/usage에 기록한다. Action record identity/seed도 effect 전에 재검증한다.

## REGENERATE_GEOMETRY Path

```text
validated source REVISE
→ immutable initial / revision action / reservation
→ exact existing approved 4 references
→ new current manifest / byte-identical staging
→ geometry Work Order / seed+1 Plan
→ reserved Geometry Worker
→ fresh GLB + embedded current input hashes/seed validation
→ reserved unchanged Blender diagnostic script
→ fresh four-view manifest validation
→ reserved 8-image Geometry Review
→ final verdict / bounded stop
```

기존 approved reference set이 변하지 않으므로 Multiview Reviewer는 호출하지 않는다.

Mock validated counts: Geometry Worker1 / Blender1 / Geometry Reviewer1 / Multiview Reviewer0.

Geometry Work Order는 initial/source Review/action, current multiview, approved Review, staging, prior execution/Plan/seeds, workflow/new Plan, expected Worker/Execution report path를 연결한다. Execute 전에 Work Order inputs/seed/workflow/prior lineage가 expected values와 같아야 한다.

## REGENERATE_VIEW Path

```text
validated source REVISE / selected right|left|back
→ immutable action / reservation
→ selected target Work Order / same workflow / original front / seed+1
→ reserved target Worker once
→ fresh PNG / replace exactly one role in new manifest
→ reserved 4-image Multiview Review
→ PASS only: staging → geometry seed+1 → Worker → Blender → Geometry Review
→ REVISE/HUMAN_REQUIRED: bounded stop before Geometry
```

Unchanged references는 historical execution refs와 함께 유지하고 새로 생성된 것처럼 relabel하지 않는다. Target fixture 세 경로 모두 검증했다.

Mock validated counts on multiview PASS: target Worker1 / Multiview Reviewer1 / Geometry Worker1 / Blender1 / Geometry Reviewer1.

Multiview REVISE/HUMAN_REQUIRED이면 target Worker1 / Multiview Reviewer1로 중단하고 geometry/render/final review=0이다. 추가 view correction 없음.

## Current References / Staging / Artifacts

- Manifest order: front/right/left/back exactly once; original authoritative front 불변.
- Geometry-only는 exact L6 approved set. View action은 target만 교체된 새 set 및 새 Multiview PASS.
- Future staging namespace: `work/input/l7/<controller_run_id>/<right|left|back>.png`.
- Exclusive directory/file creation, binary copy, no overwrite/resize/re-encode/crop/rembg/metadata edit. Source/staged SHA·bytes·dimensions 동일.
- Geometry mapping: front→node1, left→node2, back→node3, right→node4. Conditioning은 기존 workflow의 front/left/back/right 그대로 유지.
- Future Worker output: `work/output/mesh/l7/<controller_run_id>/geometry_*_.glb`, target PNG는 `work/output/l7/<controller_run_id>/<target>_*_.png`.
- Fresh run/prefix, task/prompt/client identity, Worker Report/Plan/Execution, glTF/version2/declared length, bytes/SHA 검증. Old GLB path 또는 old GLB SHA replay reject.
- GLB embedded LoadImage filenames/input hashes 및 seed가 current geometry Plan/staged references와 일치해야 한다.
- Render namespace: `work/output/l7/<controller_run_id>/geometry_review/`.
- Geometry Review attachment order: source_front/source_right/source_left/source_back/geometry_azimuth_0/90/180/270. Current geometry가 소비한 exact references를 사용한다. View 교체 후 old reference attachment를 넣으면 Reviewer 전에 차단한다.

## Renderer / Reviewer 연결

- 기존 `D:\Blender_5.2\blender.exe`; version5.2.0 LTS는 M1 actual에서 검증된 기대값. M2에서는 executable 존재/size/mtime 및 script hash만 effect-free 검사했고 version/render process를 새로 실행하지 않았다.
- Command: `--background --factory-startup --python-exit-code 1 --python <existing l7_blender_diagnostic.py> -- --request <new render_request.json>`.
- Fixed Workbench/orthographic/512x512/common bounds framing/four azimuth/neutral display contract 유지.
- Review Request0.2/Result0.3 및 existing Reviewer primitive 그대로 사용.
- Exact role/order/hash, process_started, request/result/invocation SHA, durable reservation timestamp 및 structured action validation 후에만 verdict를 해석한다.
- Final instructions의 M1 historical L6 문구는 current generation inputs로 바꾼다. Geometry-only 및 세 view mock 경로에서 instruction/reference binding을 검증했다. Original M1 instruction bytes는 변경하지 않았다.
- M2에서 actual Renderer/Reviewer 호출=0. Mock evidence의 SYNTHETIC_TEST를 actual semantic evidence로 주장하지 않는다.

## Budgets / Reservation / Terminal Policy

| Component | Limit | Geometry-only PASS mock consumed | View PASS mock consumed |
|---|---:|---:|---:|
| Revision action |1|1|1|
| Workers |2|1|2|
| Reviewers |2|1|2|
| Renderer |1|1|1|
| Automatic retry |0|0|0|

Reservation stage names는 revision/view/geometry/multiview_review/renderer/geometry_review로 고정한다. Canonical order/request path만 허용하고 alternate ID/path, repeated stage, second revision을 차단한다. Failure/timeout 이후 slot refund 없음. Geometry-only가 불필요한 view/multiview stage를 예약할 수 없다.

| Condition | Bounded result |
|---|---|
| Source PASS | INTERNAL_ACCEPT, correction0 |
| Source HUMAN_REQUIRED | ABORT/HUMAN_REQUIRED, correction0 |
| Final Geometry PASS + no blockers + NONE/null | INTERNAL_ACCEPT/GEOMETRY_PASS |
| Revised Multiview or final Geometry REVISE | ABORT/REVISION_BUDGET_EXHAUSTED; second action0 |
| Revised Multiview or final Geometry HUMAN_REQUIRED | ABORT/HUMAN_REQUIRED |
| Source invalid / seed/action invalid | FAILED/SOURCE_REVIEW_INVALID or REVISION_POLICY |
| Known Worker/Renderer/Reviewer failure | FAILED with stage reason |
| Submission/process uncertainty, timeout, malformed Review/identity uncertainty | UNRESOLVED; no retry/resume |

INTERNAL_ACCEPT는 M2에서 simulated Review PASS의 controller 판단일 뿐 actual delivery가 아니다. DELIVERED/user verdict workflow 없음.

Terminal re-entry는 ALREADY_TERMINAL/no effect/no writes. UNRESOLVED 또는 incomplete namespace는 automatic resume을 거부한다. Full crash recovery나 distributed lock은 구현하지 않았다.

## Durable Records / Usage

Future execute 또는 temporary mock run에 `initial.json`, `revision_action.json`, stage reservations, Plan/Work Order/Worker Report/Execution, current manifest, staging, render request/invocation/manifest, Review instructions/request/result/invocation, state/terminal/usage가 연결된다. M1 namespace에는 새 record를 쓰지 않는다.

Usage는 action/target/ordinal, worker stage/backend/model/invocations/process duration, reviewer stage/calls/duration, renderer calls/duration, budgets/retry0/final state를 기록한다. Reservation은 소모됐지만 invocation outcome을 측정할 수 없으면 call/time을 null로 남긴다.

Frontier requested/actual model·effort, tokens/cache/reasoning/credits는 existing adapter에서 independently observable하지 않아 null이다. 추정값 없음. Initial의 preflight effect0는 별도 preflight 하위 항목이며 execute 결과의 effect count로 사용하지 않는다.

이번 M2의 production usage는 모두0이며 actual correction run/usage artifact를 생성하지 않았다. Mock records는 test temporary directory에만 존재한다.

## Tests / Real Preflight

Cwd: repository. Bundled Python: `C:\Users\Worker\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`, `PYTHONPATH=src`, `-B`.

| Command / validation | Result |
|---|---|
| `python -B -m unittest tests.test_l7_feedback_controller` | **44/44 PASS**,124.900s |
| `python -B -m unittest discover -s tests -p "test_*.py"` | **149/149 PASS**,192.692s; existing105+new44 |
| `python -B -m scenario_a.l7_feedback_controller --help` | exit0 |
| `python -B -m scenario_a.l7_feedback_controller --preflight --source-review-run <actual M1 run directory>` | exit0 / PREFLIGHT_PASS / effects0 |
| Current-reference instruction binding: geometry/right/left/back targeted cases | **4/4 PASS**,18.820s; 이후 final full149 재실행 PASS |
| New source/test AST parse | PASS |

Focused coverage includes source PASS/HUMAN/action vocabulary/front rejection/free-text non-dispatch; source Result/Invocation/terminal mutation; seeds/overflow/other parameters/ordinal; both complete action paths and all targets; exact manifests/staging/reference/embedded GLB lineage; PASS/second REVISE/HUMAN; known failures/uncertainty; old GLB and invalid PNG/GLB; alternate reservation paths/Review ID; budget/refund/no retry; terminal reentry/no writes; incomplete namespace; unknown telemetry null; real source effect-free preflight.

Comfy transport, Worker primitive, Blender subprocess, Frontier primitive are mocked/tripwired in local tests. L6/M1 fixture setup also uses synthetic temporary assets only. Real L7-M1 evidence is used by one static preflight test and CLI preflight, without execution. Actual source documents are never rewritten for fixtures.

Actual-source preflight resolved REGENERATE_GEOMETRY/geometry; prior528364197559477; predicted528364197559478; existing workflows/models/Blender executable and Reviewer contract PASS; controller namespace created=false.

## Protection / Known Limits

- Existing tracked source/docs/tests/schema/Core files diff0. New files only3; existing tests not weakened/deleted.
- Exact L6 actual evidence40 files and M1 evidence15 files match verified Git blobs byte-for-byte after tests.
- main/origin/main, L6 local/remote and frozen tag unchanged. No tag/release/main merge writes.
- Workflow hashes revalidated; six model sizes and mtime_ns unchanged from start; no model download/load/config changes.
- Research HEAD `7e1572a7e35866519b75b767398288396a27f9b0`; tracked changes0; sole untracked `ac6_f2b_resume.py` SHA `2a58ab64e8838e8c3da6d8b4d62526e1a8d0d834bb26058d905d80d73dfd9369` unchanged. No Research commit/push/cleanup.
- No PNG/GLB or temporary fixture evidence committed.
- Fixed one-action/one-continuation graph only; M1-compatible verified source/L6 asset contract. No multi-action optimization, seed search, best-of-N, third Geometry Review, concurrency or recovery support.
- Geometry action seed+1 does not guarantee quality improvement/PASS. View action is verified with synthetic fixtures; actual target regeneration/re-review remains unproven.
- No actual correction, final geometry quality, closed-feedback success, user acceptance, benchmark/economic claim.
- L7-M3 remains a separate not-started milestone. Current source action is not dispatched in M2.

## Final State / Stop

```text
AGENT LOOP CORE V1.0.0 = FROZEN / UNCHANGED
LEVEL 6 MULTI-STAGE SUPERVISED PIPELINE = VERIFIED
L7-M0 MANDATORY GATE = PASS
L7-M1 GEOMETRY REVIEW BRIDGE = VERIFIED
L7-M2 MINIMAL FEEDBACK CONTROLLER = READY
L7-M3 ACTUAL CLOSED FEEDBACK PROOF = NOT STARTED
LEVEL 7 CLOSED FEEDBACK PIPELINE = NOT VERIFIED
HYPOTHESIS BENCHMARK = NOT STARTED
```

Report / normal commit / push / clean 확인 후 STOP. No actual source action, production generation/render/review, DELIVERED, F2B/F05/F07/Core1.1/ScenarioB.
