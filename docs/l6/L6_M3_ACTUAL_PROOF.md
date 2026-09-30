# L6-M3 Actual End-to-End Multi-Stage Proof

## 결과

**L6-M3 ACTUAL E2E PROOF = PASS**
**LEVEL 6 MULTI-STAGE SUPERVISED PIPELINE = VERIFIED**

한 번의 existing top-level runner invocation에서 source → actual right/left/back → actual Frontier PASS → exact byte staging → actual Hunyuan GLB → GEOMETRY_READY가 연결되었다. Manual stage handoff, source patch, retry는 없었다.

Geometry structural validation 및 identity lineage proof만 수행했다. Geometry semantic quality, final user delivery, Level 7, hypothesis benchmark는 시작하지 않았다.

## Repository / baseline

- Root: `D:\VSCODE-WorkSpace\Others\Agent-Loop-Core`
- Remote: https://github.com/1-3127/Agent-Loop-Core.git
- Branch: `scenario-a-l6`
- Frozen main / origin/main / core-v1.0.0 target: `7eee393801f4d8c14278b43ebcbaabaec7ccc9df`
- Annotated tag object: `8b962c5d94828af852d020237554606c305ef01e`
- M1 commit: `935b5cb746e9b0533f846728b9d87eb02699276e`
- M2 / M3 start HEAD == origin/scenario-a-l6: `2160515db9161ea7221b214c1878e31eb57c7c83`
- Start tree clean; live remote heads/tag matched. This report and actual run metadata are the only M3 additions.
- M3 branch commit: this report-containing commit, identified by `git log -1 -- docs/l6/L6_M3_ACTUAL_PROOF.md`; final HEAD/remote equality is reported after normal push.
- main merge / tag creation / release change = 0.
- Instructions: root AGENTS.md, Agents/workflow.md, Others/AGENTS.md, Compact AGENTS.md, current L6-M3 handoff.

## Pre-Actual Validation

Bundled Python3.12/Pillow runtime: `C:\Users\Worker\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
Repository cwd; bytecode disabled; module CLI uses `PYTHONPATH=src`.

| Command | Result |
|---|---|
| `python -B -m unittest tests.test_l6_pipeline` | 34/34 PASS, 15.213s |
| `python -B -m unittest discover -s tests -p "test_*.py"` | 72/72 PASS, 16.043s |
| `python -B -m scenario_a.l6_pipeline --help` | exit0 |
| `python -B -m scenario_a.l6_pipeline --preflight --run-id l6-m3-preflight` | PREFLIGHT_PASS, exit0, effects0 |

Tests are mock/fixture policy validation. Actual proof below uses real Comfy /prompt and Codex CLI, independently of test fixtures. No new tests or production code were added.

### Protected document / workflow identities

| File / workflow | SHA-256 |
|---|---|
| L6_M1_ASSET_AUDIT.md | `19421bd4b21287df6572406a2b727a9eae93cba80887a50661cd3a0ad6bb2a52` |
| L6_PIPELINE_CONTRACT_v0.md | `4e229bde44eae59e581f7ab749bba3ff764aa8f13e9d922df3dd90de6b2b9f5c` |
| L6_ASSET_MANIFEST.json | `ceff2ea2ed0ac799ca08673c6d4d912c03e23e16770eaac04dfd9c9160f6a716` |
| L6_M2_IMPLEMENTATION.md | `e73ba974a446e7289a28050e33de694d6ed8fb6413341663ef9b3fd2dddebf15` |
| workflows/02_Image_to_Multiview/Qwen2509_Multiangle_RTX4060_api.json | `bb16c26a0aa599f3eee35f206940f1e6ab40bd39c9569025fa8a4f80de67311a` |
| workflows/02_Image_to_Multiview/Qwen2509_Left_api.json | `65e97b19b89736cf6431c3803c8cecbdee2466067a63aa8eeb3e11d1e7d30f28` |
| workflows/02_Image_to_Multiview/Qwen2509_Back_api.json | `ac80748728f98d7ad1e08806778f91a42fce026e7a35cdf0d52e46b4e18eacfb` |
| workflows/03_Multiview_to_3D/Hunyuan3D_MV_RTX4060_api.json | `729e9e02c3ef655c5f576067ec3cb291285dcf1d1db70100857c141c026ab2fa` |

Six required model files: existing paths, byte sizes and mtime_ns all match the M1 asset manifest. Multi-GB model hashes were not calculated; no downloads/install/upgrades/workflow edits.

## Runtime / fresh run declaration

- Endpoint: `http://127.0.0.1:8188`
- Existing runtime already healthy: ComfyUI0.37.4, NVIDIA GeForce RTX4060; queue running0/pending0 before actual call. Existing server reused; startup0.
- Required 19 node classes registered. Reviewer auth gate: `CHATGPT_ACCOUNT`.
- User standing approval for future Agent-Loop CORE image transfer to Codex applied; exactly four PNGs attached once.
- Run ID: `l6-m3-20260930-164920-8109160a`
- Run/output/mesh/staging namespaces all absent before first effect.
- Single actual command: `python -B -m scenario_a.l6_pipeline --execute --run-id l6-m3-20260930-164920-8109160a`
- worker-timeout600 / review-timeout600 defaults unchanged.
- Effect ceiling declared before execution: Worker4, Reviewer1, Blender0, retry0.
- Initial contract: [initial.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/initial.json) (SHA-256 `c6f1468eaaec1a55a640927ef2a55646868178e1d3bc1ea63c515c61cab900b0`)
- Initial state SOURCE_READY; terminal=false; budgets4/1, consumed0. Created_at `2026-09-30T07:50:03.196098+00:00`.
- Initial contract hash persisted in state/orders/reservations/executions before first Worker started at `2026-09-30T07:50:03.292931+00:00`. Immutable initial bytes verified after terminal.

## Source / four-role identity

Front is the existing original input, not regenerated. All four files fully PNG-decoded/CRC-checked, bytes/dimensions/hash validated before Review and after PASS.

| Role | Absolute path | Bytes | Dimensions | SHA-256 |
|---|---|---:|---|---|
| front | `D:\VSCODE-WorkSpace\Comfy-UI\work\input\hunyuan-official-demo-padded.png` | 142572 | 768x768 | `8a6dd9ca3f8984b31c1243e7698cd5030b423464d80e0ad763609148e0ff4f51` |
| right | `D:\VSCODE-WorkSpace\Comfy-UI\work\output\l6\l6-m3-20260930-164920-8109160a\right_00001_.png` | 233500 | 768x768 | `6c4828c226de954cab7daee8975f4e2f60ee1507bee5c9eb72fd34d9c146bc4d` |
| left | `D:\VSCODE-WorkSpace\Comfy-UI\work\output\l6\l6-m3-20260930-164920-8109160a\left_00001_.png` | 223398 | 768x768 | `d1f6c681ebbee462e26b42e5de710caf34424edfa68eb01686f7caa88b7b89d6` |
| back | `D:\VSCODE-WorkSpace\Comfy-UI\work\output\l6\l6-m3-20260930-164920-8109160a\back_00001_.png` | 232979 | 768x768 | `2aa7f06a081869b961650498fe77bb19955019b958098156cee42b30bc1f937f` |

## Actual Right

- Work Order: [right_work_order.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/right_work_order.json) (SHA-256 `f944fc1a77a8203855f84cb147aa030455543902c40e28cd82fc9e395ae2a5f6`)
- Plan: [right_plan.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/right_plan.json) (SHA-256 `6d14521136a9fb25ad8a2b48d8184971774302fb5c0e4f34800832385264ba32`)
- Worker Report: [right_worker_report.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/right_worker_report.json) (SHA-256 `ffca750e3563c5b0874acb34cf519d46277051434dec13a3db656ab226854252`)
- Execution: [right_execution.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/right_execution.json) (SHA-256 `c2a867890c872d465f277f9d7c19e4e02c12e16fc2981fb861c54a28c868f579`)
- Live Comfy history snapshot: [right_comfy_history.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/right_comfy_history.json) (SHA-256 `3e02305483e6dc7daccd02b6715be30b6a2f8b4d94ea7ed27852b89d9692b0d9`)
- work_order_id: `l6-m3-20260930-164920-8109160a-right`
- backend/model: ComfyUI / `Qwen-Image-Edit-2509-Q4_K_S.gguf`
- prompt_id: `064e265c-b79c-467d-99e3-ec89c0302574`; client_id: `6650d361-4ca6-44e9-9fc1-1428ac8f1c20`
- Started/completed UTC: `2026-09-30T07:50:03.292931+00:00` / `2026-09-30T07:51:49.304399+00:00`
- SUCCESS, fresh namespace, actual history status=success/completed=true. Report/Plan/workflow/initial/artifact hashes and run identity validated.
- Output identity: above four-role table; current-run PNG and distinct prompt_id, not historical replay.

## Actual Left

- Work Order: [left_work_order.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/left_work_order.json) (SHA-256 `ba2949f2f6814683c15ae7d3dd8543df236ee3a9eecd2b6d5dbe62cc984c4b60`)
- Plan: [left_plan.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/left_plan.json) (SHA-256 `0c3e08e97cd4905ac0b7ec0305a3c8aa291ce8e075429fb7ae0253e1568d191c`)
- Worker Report: [left_worker_report.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/left_worker_report.json) (SHA-256 `87511a3208cf2d439452ca73132d0763cddbc1b38414941b3a8d7468ad522273`)
- Execution: [left_execution.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/left_execution.json) (SHA-256 `62cbadf74458c7a869c9c1dad1614ca759887eee62b3f4ca489ccd11de8cf72a`)
- Live Comfy history snapshot: [left_comfy_history.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/left_comfy_history.json) (SHA-256 `313a2c94a1ce3ec07788f71ae276001c6b149b65a094f7c237ff189422af319c`)
- work_order_id: `l6-m3-20260930-164920-8109160a-left`
- backend/model: ComfyUI / `Qwen-Image-Edit-2509-Q4_K_S.gguf`
- prompt_id: `f90e6894-d815-4599-bd9b-2622316919b2`; client_id: `4f5a2188-eb07-4db4-8f1c-ae3388cc0b93`
- Started/completed UTC: `2026-09-30T07:51:49.407798+00:00` / `2026-09-30T07:53:47.344745+00:00`
- SUCCESS, fresh namespace, actual history status=success/completed=true. Report/Plan/workflow/initial/artifact hashes and run identity validated.
- Output identity: above four-role table; current-run PNG and distinct prompt_id, not historical replay.

## Actual Back

- Work Order: [back_work_order.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/back_work_order.json) (SHA-256 `83673ea2e62231439e2584d3135cfaa1d7547b0d42ad858b0363163d70b4fb0e`)
- Plan: [back_plan.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/back_plan.json) (SHA-256 `2de0147f7f5a37970708d9210ca37738448f2dccf076be9a82cb6e77911cf026`)
- Worker Report: [back_worker_report.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/back_worker_report.json) (SHA-256 `58ae332d9741754f0063bcb372d1b090b91855bdb76fa2c8c097ed95ab698ed9`)
- Execution: [back_execution.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/back_execution.json) (SHA-256 `3e061f882a0004339165e71cdd1f8114ec41cee0ac9afe1e5c15f698b4ce1056`)
- Live Comfy history snapshot: [back_comfy_history.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/back_comfy_history.json) (SHA-256 `4768d3c34a3732d1f3aae801228aa6c8e91f795dd2f00b777e86380bf03d7e32`)
- work_order_id: `l6-m3-20260930-164920-8109160a-back`
- backend/model: ComfyUI / `Qwen-Image-Edit-2509-Q4_K_S.gguf`
- prompt_id: `56b08605-092b-4fa0-900e-d08672537f6e`; client_id: `15885294-daac-4a21-8104-592d3ee6c749`
- Started/completed UTC: `2026-09-30T07:53:47.436300+00:00` / `2026-09-30T07:55:44.325933+00:00`
- SUCCESS, fresh namespace, actual history status=success/completed=true. Report/Plan/workflow/initial/artifact hashes and run identity validated.
- Output identity: above four-role table; current-run PNG and distinct prompt_id, not historical replay.

## Multiview Manifest / Review

- Manifest: [multiview_manifest.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/multiview_manifest.json) (SHA-256 `6795396e374873d720bd2fd0a721e179a4887880a87f4dd54148ed832c0b7724`)
- Aggregate Work Order: [multiview_work_order.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/multiview_work_order.json) (SHA-256 `3fe5e686e8ee73594ed39effb243e418ad1732000519a0d9758c4188c7dfa4e2`)
- Aggregate Execution: [multiview_execution.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/multiview_execution.json) (SHA-256 `b360d2bca1c9053d167681c0f33c5136b73946b7009b1278517d8363d03041d3`)
- Instructions: [review_instructions.md](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/review_instructions.md) (SHA-256 `dc88e0e533b1900d89748a26f4a79c655949edab44102f83f3d1e487328705d9`)
- Request: [review_request.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/review_request.json) (SHA-256 `42a41c733fa2a9a8279229d0e61a2c6886f6e51a99e2bc1c5a19c0252bfd910a`)
- Reservation: [review_reservation.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/review_reservation.json) (SHA-256 `5115a715a565b2bd31cf78ee52dea9107d3a5606aadbd2dbf890a33ca27e6f08`)
- Result: [review_result.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/review_result.json) (SHA-256 `9206c223a68fe26c8e1cf06972da4dd57acd4b8560a1df36592833d4d48e15d1`)
- Invocation: [review_invocation.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/review_invocation.json) (SHA-256 `6b86dafa8bba7fd0d1cd8a8e3a1d53005b71e82adb20b759f0a985f4e77fc65b`)
- review_id: `l6-m3-20260930-164920-8109160a-multiview-review`
- Actual attachment order exactly front/right/left/back; paths and SHA exactly equal four-role table and Request/Manifest.
- reviewer_mode=CODEX_CLI; process_started=true; auth=CHATGPT_ACCOUNT; exit0; invocation_status=SUCCESS.
- Process started UTC `2026-09-30T07:55:44.591800+00:00`, finished `2026-09-30T07:56:27.074852+00:00`.
- Duration 42.484 seconds; invocation/request/result SHA and checked_invocation validation PASS.
- verdict=PASS; blocking_issues=[]; suggested_action=NONE/null.
- Observations:
  - All four views depict the same penguin holding a two-post HY3D sign, with plausible opposing side views and a consistent rear view.
  - Major parts remain present and within frame; no clear cross-view contradiction or downstream geometry blocker is visible.
- Reviewer actual invocations1; consumed1/remaining0.
- Geometry gate opened YES only after validated PASS. Geometry reservation/submission came after Review completion.

## Staging / Geometry mapping

- Staging evidence: [staging.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/staging.json) (SHA-256 `8b59435678604a77f7d842d1e8bcc8d6d2cf926669386a7a6aa42a2754400d5e`)
- PASS-reviewed originals rehashed and compared byte-for-byte with staged files, not re-encoded/cropped/resized/rembg processed.
- Exclusive new staged files under `D:\VSCODE-WorkSpace\Comfy-UI\work\input\l6\l6-m3-20260930-164920-8109160a`.
- Reviewed SHA == staged SHA for right/left/back; bytes/dimensions unchanged. Front remains original.

| Role | LoadImage node | Actual image field | Reviewed / staged SHA |
|---|---|---|---|
| front | 1 | `hunyuan-official-demo-padded.png` | `8a6dd9ca3f8984b31c1243e7698cd5030b423464d80e0ad763609148e0ff4f51` |
| right | 4 | `l6/l6-m3-20260930-164920-8109160a/right.png` | `6c4828c226de954cab7daee8975f4e2f60ee1507bee5c9eb72fd34d9c146bc4d` |
| left | 2 | `l6/l6-m3-20260930-164920-8109160a/left.png` | `d1f6c681ebbee462e26b42e5de710caf34424edfa68eb01686f7caa88b7b89d6` |
| back | 3 | `l6/l6-m3-20260930-164920-8109160a/back.png` | `2aa7f06a081869b961650498fe77bb19955019b958098156cee42b30bc1f937f` |

Conditioning order front,left,back,right; Review order front,right,left,back.

## Actual Geometry

- Work Order: [geometry_work_order.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/geometry_work_order.json) (SHA-256 `8502572572d03336cb13b2e1b8e047268bcf7627d82c997ad267124e55ef9355`)
- Plan: [geometry_plan.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/geometry_plan.json) (SHA-256 `56daf925fc0c06b46af1a2808244298eb321ed7d0f520a9e9b8095c4f3bc1e2a`)
- Reservation: [geometry_reservation.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/geometry_reservation.json) (SHA-256 `b85dfe292b2a959b4606ea19ad2940740eb7ec4e3c0c162e4c815d249664e1d9`)
- Worker Report: [geometry_worker_report.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/geometry_worker_report.json) (SHA-256 `f7b84052053f2f1411c739b88f406445f1f6443dea6e9b3c27d0dbf833824803`)
- Execution: [geometry_execution.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/geometry_execution.json) (SHA-256 `0803cf18fb7ea3a9c8eaa9b76f2c471b15bf0ac87100f34ecad3d695bd3a2ea6`)
- Comfy history: [geometry_comfy_history.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/geometry_comfy_history.json) (SHA-256 `54822cd4ce37e002a415b43db8ffcbd25acfb8d49d57283f6d12988ca5b86c59`)
- backend/model: ComfyUI / `hunyuan3d-dit-v2-mv-turbo_fp16.safetensors`
- work_order_id: `l6-m3-20260930-164920-8109160a-geometry`
- prompt_id: `88bcf8cf-083d-4698-a238-08e6b5801cdb`; client_id: `c5987bcb-e0f6-4c79-9f28-c42b8b285243`
- Started/completed UTC: `2026-09-30T07:56:27.775096+00:00` / `2026-09-30T07:57:11.415549+00:00`
- Existing resolution1024/octree128/SaveGLB17/seed528364197559477, sampler parameters unchanged.
- GLB evidence path: `D:\VSCODE-WorkSpace\Comfy-UI\work\output\mesh\l6\l6-m3-20260930-164920-8109160a\geometry_00001_.glb`
- Bytes: 1139016; SHA-256: `1cc00067c772f3efdad34f36cb44c4b5d54ed5bfa4b03a4888a3f3de80fca252`
- Structural check: exists, fresh mesh/l6 current-run prefix, size>=20, magic=glTF, version2, declared_length=1139016==actual bytes. Existing verify_glb against live history/report PASS.
- Embedded metadata evidence: [geometry_embedded_identity.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/geometry_embedded_identity.json) (SHA-256 `8884cf1b4a77f5f9f99a2a31168fc7c82250ca19eb07159cecb4c3a771b02034`)
- GLB embedded LoadImage is_changed SHA values exactly match the four reviewed inputs, with expected node paths/model/seed. This corroborates actual consumed byte identity.
- No GLB rendering/Blender/topology/UV/texture/PBR/semantic geometry assessment or final user delivery.

## Counts / cache / budget / terminal

- One top-level actual runner call. Live Comfy history grew4→8, exact four added IDs equal these Reports; submitted graphs exactly equal patched Plans; fresh output prefixes.
- Comfy submissions4; semantic Reviewer1; Blender0; retry0; manual stage handoff0.
- Final Worker limit4/consumed4/remaining0; Reviewer limit1/consumed1/remaining0. Invariants consumed<=limit, remaining>=0 PASS.
- Cache usage from actual Comfy execution_cached events:
  - right: [["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]].
  - left: [["1", "2", "3", "4", "5", "6", "7", "9", "10"]].
  - back: [["1", "2", "3", "4", "5", "6", "7", "9", "10"]].
  - geometry: [["1"]].
- Image KSampler11/VAEDecode12/SaveImage13 and geometry generation/save nodes were not in those cached-node lists. Existing input/model/upstream cache reuse is permitted; fresh prompts and artifacts verified. Model residency at each instant was not independently recorded.

- Final state GEOMETRY_READY, terminal=true; reason REVIEWED_MULTIVIEW_TO_VALID_GLB.
- Terminal: [terminal.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/terminal.json) (SHA-256 `f595e1dc4834368faba477a0afa1f3412062d9410027800e7b1b5e55e25c4abc`)
- State: [state.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/state.json) (SHA-256 `8559987f402fb2bc258b56f8ee8a8d87de4fa3ce1a58244275de447c6080a61b`)
- Worker/Reviewer/state-transition entry probes returned ALREADY_TERMINAL; existing runner file bytes/hashes unchanged; live history ID set unchanged; additional effects0.
- Derived validation: [actual_validation.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/actual_validation.json) (SHA-256 `3f3d8104236be18143a5215d8413af5ec242b96feadb18ef13c83cc1c75b89d4`)
- All 150 nested file/artifact reference occurrences validated by direct SHA; terminal record refs complete/non-null; run/work-order/Plan/Report/artifact/Review/staging/GLB chain intact.

## Usage

- Usage record: [usage.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/usage.json) (SHA-256 `5f89068b9f187f2b47fe88b8ff092984257f137ccc5d81dbd5831746a64534fc`)

| Stage | Actual calls | Report wall duration seconds |
|---|---:|---:|
| right | 1 | 106.011468 |
| left | 1 | 117.936947 |
| back | 1 | 116.889633 |
| geometry | 1 | 43.640453 |
| Frontier semantic Reviewer | 1 | 42.484 |

Worker backend/model filenames are recorded above. Frontier provider OpenAI, auth mode CHATGPT_ACCOUNT.
requested_model/requested_reasoning_effort/actual_model/actual_reasoning_effort/input_tokens/cached_input_tokens/output_tokens/reasoning_tokens/reported_credits are null. Existing Reviewer call has no explicit override and does not expose independently observable telemetry. Unknown values were not estimated as0. Durations are report wall time, not GPU-only compute/cost.

## Protection / changed files / limits

- Added only `runs/l6/l6-m3-20260930-164920-8109160a/**` JSON/Review instructions and `docs/l6/L6_M3_ACTUAL_PROOF.md`. Four live history snapshots plus validation/GLB-metadata records are post-run derived evidence; runner-generated evidence was not rewritten.
- All previously tracked repository files unchanged vs M2; src/core diff0 vs frozen baseline. Existing C1-C5 evidence and schemas unchanged.
- M1 audit/contract/manifest SHA maintained; M2 source/tests/report maintained.
- main/origin/main/frozen tag object/target unchanged. No main merge/tag/release API writes.
- Workflows/source SHA maintained; six model sizes/mtime unchanged. Large model hashes null as authorized.
- Research HEAD `7e1572a7e35866519b75b767398288396a27f9b0`, tracked diff0, sole untracked `ac6_f2b_resume.py` unchanged SHA `2a58ab64e8838e8c3da6d8b4d62526e1a8d0d834bb26058d905d80d73dfd9369`. Research commit/push0.
- PNG/GLB remain outside Git in Comfy workspace; no binary artifacts committed.
- Run-local `.gitattributes` preserves immutable `review_instructions.md` bytes with `-text`. Existing global JSON preservation rules are unchanged. Git automatic CRLF normalization would otherwise change this request-linked instruction SHA; packaging metadata only, no production source/runner/evidence rewrite.
- Post-run audit command initially passed a full artifact object to strict checked_ref (path/sha256-only shape); corrected only the audit command to hash artifact bytes directly. No production defect, no runner retry, no evidence status/verdict modifications.
- Known remaining scope: geometry semantic quality/final delivery, Level7, F05 generic boundary/F07/F2B recovery, quality/economics benchmark unproven. No implementation of these items.

## Evidence index

Absolute run root: `D:\VSCODE-WorkSpace\Others\Agent-Loop-Core\runs\l6\l6-m3-20260930-164920-8109160a`. Each link resolves actual stored bytes; hashes below are after execution/no-effect probes.

| Record | SHA-256 |
|---|---|
| [.gitattributes](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/.gitattributes) | `1eec50926e6891df6e6e7d680859ae3395c160c72419d93a47342cf948d7e730` |
| [actual_validation.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/actual_validation.json) | `3f3d8104236be18143a5215d8413af5ec242b96feadb18ef13c83cc1c75b89d4` |
| [back_comfy_history.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/back_comfy_history.json) | `4768d3c34a3732d1f3aae801228aa6c8e91f795dd2f00b777e86380bf03d7e32` |
| [back_execution.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/back_execution.json) | `3e061f882a0004339165e71cdd1f8114ec41cee0ac9afe1e5c15f698b4ce1056` |
| [back_plan.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/back_plan.json) | `2de0147f7f5a37970708d9210ca37738448f2dccf076be9a82cb6e77911cf026` |
| [back_reservation.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/back_reservation.json) | `12d9227841048339ade1caf7483cd31ee3adaf6807c17f68e604ee76b29d99d2` |
| [back_work_order.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/back_work_order.json) | `83673ea2e62231439e2584d3135cfaa1d7547b0d42ad858b0363163d70b4fb0e` |
| [back_worker_report.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/back_worker_report.json) | `58ae332d9741754f0063bcb372d1b090b91855bdb76fa2c8c097ed95ab698ed9` |
| [geometry_comfy_history.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/geometry_comfy_history.json) | `54822cd4ce37e002a415b43db8ffcbd25acfb8d49d57283f6d12988ca5b86c59` |
| [geometry_embedded_identity.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/geometry_embedded_identity.json) | `8884cf1b4a77f5f9f99a2a31168fc7c82250ca19eb07159cecb4c3a771b02034` |
| [geometry_execution.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/geometry_execution.json) | `0803cf18fb7ea3a9c8eaa9b76f2c471b15bf0ac87100f34ecad3d695bd3a2ea6` |
| [geometry_plan.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/geometry_plan.json) | `56daf925fc0c06b46af1a2808244298eb321ed7d0f520a9e9b8095c4f3bc1e2a` |
| [geometry_reservation.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/geometry_reservation.json) | `b85dfe292b2a959b4606ea19ad2940740eb7ec4e3c0c162e4c815d249664e1d9` |
| [geometry_work_order.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/geometry_work_order.json) | `8502572572d03336cb13b2e1b8e047268bcf7627d82c997ad267124e55ef9355` |
| [geometry_worker_report.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/geometry_worker_report.json) | `f7b84052053f2f1411c739b88f406445f1f6443dea6e9b3c27d0dbf833824803` |
| [initial.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/initial.json) | `c6f1468eaaec1a55a640927ef2a55646868178e1d3bc1ea63c515c61cab900b0` |
| [left_comfy_history.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/left_comfy_history.json) | `313a2c94a1ce3ec07788f71ae276001c6b149b65a094f7c237ff189422af319c` |
| [left_execution.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/left_execution.json) | `62cbadf74458c7a869c9c1dad1614ca759887eee62b3f4ca489ccd11de8cf72a` |
| [left_plan.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/left_plan.json) | `0c3e08e97cd4905ac0b7ec0305a3c8aa291ce8e075429fb7ae0253e1568d191c` |
| [left_reservation.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/left_reservation.json) | `d1ce18d410721225390d1a6adb55e079eb0405804d376ecf144c66d99ca7bf1a` |
| [left_work_order.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/left_work_order.json) | `ba2949f2f6814683c15ae7d3dd8543df236ee3a9eecd2b6d5dbe62cc984c4b60` |
| [left_worker_report.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/left_worker_report.json) | `87511a3208cf2d439452ca73132d0763cddbc1b38414941b3a8d7468ad522273` |
| [multiview_execution.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/multiview_execution.json) | `b360d2bca1c9053d167681c0f33c5136b73946b7009b1278517d8363d03041d3` |
| [multiview_manifest.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/multiview_manifest.json) | `6795396e374873d720bd2fd0a721e179a4887880a87f4dd54148ed832c0b7724` |
| [multiview_work_order.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/multiview_work_order.json) | `3fe5e686e8ee73594ed39effb243e418ad1732000519a0d9758c4188c7dfa4e2` |
| [review_instructions.md](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/review_instructions.md) | `dc88e0e533b1900d89748a26f4a79c655949edab44102f83f3d1e487328705d9` |
| [review_invocation.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/review_invocation.json) | `6b86dafa8bba7fd0d1cd8a8e3a1d53005b71e82adb20b759f0a985f4e77fc65b` |
| [review_request.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/review_request.json) | `42a41c733fa2a9a8279229d0e61a2c6886f6e51a99e2bc1c5a19c0252bfd910a` |
| [review_reservation.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/review_reservation.json) | `5115a715a565b2bd31cf78ee52dea9107d3a5606aadbd2dbf890a33ca27e6f08` |
| [review_result.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/review_result.json) | `9206c223a68fe26c8e1cf06972da4dd57acd4b8560a1df36592833d4d48e15d1` |
| [right_comfy_history.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/right_comfy_history.json) | `3e02305483e6dc7daccd02b6715be30b6a2f8b4d94ea7ed27852b89d9692b0d9` |
| [right_execution.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/right_execution.json) | `c2a867890c872d465f277f9d7c19e4e02c12e16fc2981fb861c54a28c868f579` |
| [right_plan.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/right_plan.json) | `6d14521136a9fb25ad8a2b48d8184971774302fb5c0e4f34800832385264ba32` |
| [right_reservation.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/right_reservation.json) | `b78b5e1d735fbc957c078872342037bbb1fae71f4b495abdc2d9beccd1f99f7c` |
| [right_work_order.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/right_work_order.json) | `f944fc1a77a8203855f84cb147aa030455543902c40e28cd82fc9e395ae2a5f6` |
| [right_worker_report.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/right_worker_report.json) | `ffca750e3563c5b0874acb34cf519d46277051434dec13a3db656ab226854252` |
| [staging.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/staging.json) | `8b59435678604a77f7d842d1e8bcc8d6d2cf926669386a7a6aa42a2754400d5e` |
| [state.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/state.json) | `8559987f402fb2bc258b56f8ee8a8d87de4fa3ce1a58244275de447c6080a61b` |
| [terminal.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/terminal.json) | `f595e1dc4834368faba477a0afa1f3412062d9410027800e7b1b5e55e25c4abc` |
| [usage.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l6/l6-m3-20260930-164920-8109160a/usage.json) | `5f89068b9f187f2b47fe88b8ff092984257f137ccc5d81dbd5831746a64534fc` |

## 최종 판정

AGENT LOOP CORE V1.0.0 = FROZEN / UNCHANGED
L6-M1 ASSET / CONTRACT READY
L6-M2 PIPELINE IMPLEMENTATION READY
L6-M3 ACTUAL E2E PROOF = PASS
LEVEL 6 MULTI-STAGE SUPERVISED PIPELINE = VERIFIED
LEVEL 7 CLOSED FEEDBACK PIPELINE = NOT STARTED
HYPOTHESIS BENCHMARK = NOT STARTED

Normal branch evidence commit/push 후 종료. GEOMETRY_READY를 DELIVERED 또는 user-approved asset으로 확대 해석하지 않는다.
