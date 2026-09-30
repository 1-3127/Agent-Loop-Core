# L6-M1 Existing Asset Audit

## 판정 / 범위

L6-M1 ASSET / CONTRACT READY. 정적 파일 감사이며 actual pipeline proof가 아니다.
[L6_PIPELINE_CONTRACT_v0.md](L6_PIPELINE_CONTRACT_v0.md), [L6_ASSET_MANIFEST.json](L6_ASSET_MANIFEST.json)과 함께 읽는다.
Direction Gate 및 이번 명시적 post-freeze L6 handoff를 적용한다.

## Baseline / instructions

- Compact root: D:\VSCODE-WorkSpace\Others\Agent-Loop-Core
- Remote: https://github.com/1-3127/Agent-Loop-Core.git
- 시작 main == origin/main == core-v1.0.0 dereference == 7eee393801f4d8c14278b43ebcbaabaec7ccc9df; tree clean.
- Live remote main/tag dereference 일치. Annotated tag object 8b962c5d94828af852d020237554606c305ef01e.
- Local/remote scenario-a-l6 부재 확인 후 frozen tag에서 생성. main merge/tag/release 변경 없음.
- 적용 규칙: root AGENTS.md, Agents/workflow.md, Others/AGENTS.md, Compact/Research AGENTS.md.
  Runtime source 검사에는 runtime ComfyUI/AGENTS.md 적용. Research commit 지시보다 이번 read-only 지시 우선.
- M0 PROVENANCE.md/SOURCE_MANIFEST.md 및 frozen C1–C5는 참조만.
- Research root: D:\VSCODE-WorkSpace\Others\Agent-Loop; HEAD 7e1572a7e35866519b75b767398288396a27f9b0.
  유일한 untracked ac6_f2b_resume.py SHA 2a58ab64e8838e8c3da6d8b4d62526e1a8d0d834bb26058d905d80d73dfd9369.
- Comfy root: D:\VSCODE-WorkSpace\Comfy-UI; start_comfyui.bat가 models, work/input, work/output roots 명시.
  현재 extra_model_paths.yaml 부재는 --models-directory가 실제 root를 지정하므로 blocker 아님.

## Source / front

- Path: D:\VSCODE-WorkSpace\Comfy-UI\work\input\hunyuan-official-demo-padded.png
- SHA-256: 8a6dd9ca3f8984b31c1243e7698cd5030b423464d80e0ad763609148e0ff4f51
- Bytes: 142572; dimensions: 768×768.
- Original front이며 재생성하지 않는다. Historical 세 view Plan 및 geometry node1 input에 같은 source 사용.
- Pillow load와 기존 png_dimensions integrity/decode validation.

## Fixed multiview routes

Pattern A: 기존 right/left/back 별도 API 세 파일. 동일 topology이며 prompt/prefix가 다르다.
공통 nodes: 1 LoadImage; 2 CLIPLoader; 3 VAELoader; 4 UnetLoaderGGUF; 5/6 LoraLoaderModelOnly;
7 ModelSamplingAuraFlow; 8 positive/9 empty negative TextEncodeQwenImageEditPlus;
10 VAEEncode; 11 KSampler; 12 VAEDecode; 13 SaveImage.
Input hunyuan-official-demo-padded.png; template seed=29481; steps=8/cfg=1/euler/simple/denoise=1.
Expected 768×768: source latent path에 spatial resize 없음; historical PNG dimensions와 일치.
Output work/output/<filename_prefix>_<counter>_.png. M3 actual output dimensions는 다시 검사한다.

### right

- Workflow: D:\VSCODE-WorkSpace\Comfy-UI\workflows\02_Image_to_Multiview\Qwen2509_Multiangle_RTX4060_api.json
- SHA: bb16c26a0aa599f3eee35f206940f1e6ab40bd39c9569025fa8a4f80de67311a
- Input/prompt/seed/output nodes: 1/8/11/13.
- Model node4: Qwen-Image-Edit-2509-Q4_K_S.gguf
- Prompt node8: Rotate the camera 45 degrees to the right. Keep the entire object visible, centered and at the same scale. Do not zoom in.
- Template prefix: multiview/right; future patch l6/<run_id>/right.
- Existing validate_plan static PASS.

### left

- Workflow: D:\VSCODE-WorkSpace\Comfy-UI\workflows\02_Image_to_Multiview\Qwen2509_Left_api.json
- SHA: 65e97b19b89736cf6431c3803c8cecbdee2466067a63aa8eeb3e11d1e7d30f28
- Input/prompt/seed/output nodes: 1/8/11/13.
- Model node4: Qwen-Image-Edit-2509-Q4_K_S.gguf
- Prompt node8: Rotate the camera 45 degrees to the left. Keep the entire object visible, centered and at the same scale. Do not zoom in.
- Template prefix: multiview/left; future patch l6/<run_id>/left.
- Existing validate_plan static PASS.

### back

- Workflow: D:\VSCODE-WorkSpace\Comfy-UI\workflows\02_Image_to_Multiview\Qwen2509_Back_api.json
- SHA: ac80748728f98d7ad1e08806778f91a42fce026e7a35cdf0d52e46b4e18eacfb
- Input/prompt/seed/output nodes: 1/8/11/13.
- Model node4: Qwen-Image-Edit-2509-Q4_K_S.gguf
- Prompt node8: Rotate the camera 180 degrees around the object to show its rear. Keep the entire object visible, centered and at the same scale. Do not zoom in.
- Template prefix: multiview/back; future patch l6/<run_id>/back.
- Existing validate_plan static PASS.

## Hunyuan multiview → GLB

- Workflow: D:\VSCODE-WorkSpace\Comfy-UI\workflows\03_Multiview_to_3D\Hunyuan3D_MV_RTX4060_api.json
- SHA: 729e9e02c3ef655c5f576067ec3cb291285dcf1d1db70100857c141c026ab2fa
- Model node5 ImageOnlyCheckpointLoader: hunyuan3d-dit-v2-mv-turbo_fp16.safetensors; output0=model, 1=CLIP vision, 2=VAE.

| Role | LoadImage.image | CLIPVisionEncode | Node10 input |
|---|---|---|---|
| front | 1 | 6 | front |
| right | 4 | 9 | right |
| left | 2 | 7 | left |
| back | 3 | 8 | back |

- LoadImage decoding→CLIPVisionEncode crop=none; 별도 resize/background-removal 노드 없음.
- Node10 Hunyuan3Dv2ConditioningMultiView local source all_embeds=[front,left,back,right].
  Review attachment 순서 front/right/left/back과 conditioning 순서를 혼동하지 않는다.
- Node11 FluxGuidance=3.5; node12 EmptyLatentHunyuan3Dv2 resolution=1024/batch=1.
- Node13 ModelSamplingAuraFlow shift=1; node14 KSampler seed=528364197559477, steps20/cfg4/euler/normal/denoise1.
- Node15 VAEDecodeHunyuan3D num_chunks=8000/octree_resolution=128.
- Node16 VoxelToMesh algorithm=surface net/threshold=0.6.
- Node17 SaveGLB mesh input=[16,0]; prefix=mesh/hunyuan_demo_multiview.
- Output root: D:\VSCODE-WorkSpace\Comfy-UI\work\output; mesh/hunyuan_demo_multiview_<counter>_.glb.
  Future prefix=mesh/l6/<run_id>/geometry.
- Local nodes_hunyuan3d.py / nodes_save_3d.py에서 order 및 SaveGLB 3d output 구현 확인.
- Template demo left/back/right 파일은 static validation용이다. Future actual run의 fresh inputs를 대체하지 않는다.

## Required models

실제 stat 결과. 큰 binary의 SHA 계산은 요청에서 허용한 대로 생략(null), 별도 hash 비용 subsystem 없음.

| Role | Actual path | Bytes |
|---|---|---:|
| image diffusion | D:\VSCODE-WorkSpace\Comfy-UI\models\unet\Qwen-Image-Edit-2509-Q4_K_S.gguf | 12204309024 |
| image encoder | D:\VSCODE-WorkSpace\Comfy-UI\models\text_encoders\split_files\text_encoders\qwen_2.5_vl_7b_fp8_scaled.safetensors | 9384670680 |
| image VAE | D:\VSCODE-WorkSpace\Comfy-UI\models\vae\split_files\vae\qwen_image_vae.safetensors | 253806246 |
| image acceleration LoRA | D:\VSCODE-WorkSpace\Comfy-UI\models\loras\Qwen-Image-Lightning-8steps-V1.1.safetensors | 1698951104 |
| multiview LoRA | D:\VSCODE-WorkSpace\Comfy-UI\models\loras\split_files\loras\Qwen-Edit-2509-Multiple-angles.safetensors | 236117032 |
| geometry model/CLIP vision/VAE checkpoint | D:\VSCODE-WorkSpace\Comfy-UI\models\checkpoints\hunyuan3d-dit-v2-mv-turbo_fp16.safetensors | 4930777530 |

Geometry node5의 한 checkpoint가 model/vision/VAE를 제공한다.
Live node registration, model load/GPU-memory compatibility는 이번 M1에서 확인하지 않았다.

## Existing executor / adapter reuse

- src/scenario_a/codex_to_comfy.py Plan0.1 exact fields:
  schema_version, task_id, workflow, patches, output_node.
- Patch whitelist: LoadImage.image; TextEncodeQwenImageEditPlus.prompt; KSampler.seed;
  SaveImage/SaveGLB.filename_prefix; ImageScale.width/height; VAEDecodeHunyuan3D.octree_resolution.
  전체 graph class allowlist가 아니라 scalar patch 제한이며 다른 class는 그대로 전달된다.
- SaveImage/SaveGLB 지원. PNG remote/local bytes equality, CRC/IEND/full decode/dimensions.
  GLB prefix/path containment, size≥20, magic glTF, version2, declared length, SHA.
- Existing report 존재 거절 + exclusive open(x) 예약 후 submission. Uncertain submission/history/timeout은 UNRESOLVED, 자동 retry 없음.
- Image outputs에는 hash/bytes가 없다. M2 Scenario A glue가 실제 파일 identity와 report lineage를 추가한다.
- run(plan_path, report_path, comfy_root, timeout) 재사용. Future whitelist extension 필요 없음: 네 route validate_plan PASS.
- comfy_worker_adapter는 c1_delegate wrapper. c1_delegate는 initial-right/image/iteration0/특정 task와 prefix 결합.
  c3_revision은 right REGENERATE_VIEW 전용, c5_worker_swap은 boundary proof다.
- worker_port.execute는 c5.0 단건 contract 검증. Existing adapter는 left/back/geometry를 직접 받지 않는다.
  M2는 Scenario A runner에서 existing executor 직접 재사용; frozen WorkerPort 변경/F05 generic integration은 요구하지 않는다.
- core.result_review_adapter request0.2/result0.3은 arbitrary nonempty artifacts list를 받고 image마다 실제 -i attachment를 추가한다.
  두 이미지/right에 결합된 c2/c3 wrapper는 L6에서 사용하지 않는다.
- c4_bounded durable Reviewer reservation은 reference. c4 state 및 worker limit1 coupling 때문에 통째 호출하지 않는다.
  M2 caller가 동일 최소 one-time reservation을 적용한다.
- Historical pipeline_a_controller/persist_geometry_state는 새 sequential runner의 의존성이 아니다.
  기존 mapping/Plan/reference convention만 활용한다.
- 관련 existing tests 확인: test_execution(GLB/duplicate/uncertain), test_png_integrity,
  test_c1_delegate, test_worker_port, test_c4_review_budget. M1 신규 tests/수정 없음.

## Historical actual evidence — REFERENCE_ONLY

실제 Report SUCCESS + 현재 artifact bytes/hash 확인. Future fresh L6 actual proof 대체 금지.
Historical Plan은 workflow relative path만 기록하므로 과거 template SHA는 null.
Image PNG embedded prompt에서 actual Qwen model/seed도 확인.
M4b fixture는 선택한 historical 작업 이름이며 실제 prompt_id/생성 PNG를 갖는다. Synthetic policy fixture와 구분한다.

### right: multiview-right-example

- Plan: D:\VSCODE-WorkSpace\Others\Agent-Loop\plans\multiview_right_example.json
- Plan SHA: 97d834d008343c292a8ca5c55ffa03f1f24b7823e87904d86409b54aa33c9cc0
- Report: D:\VSCODE-WorkSpace\Others\Agent-Loop\runs\multiview_right_example_report.json
- Report SHA: 24955d4bd2354e7624f1a8715775b9870143e891a86d0641b2b696ea310b7ab1
- SUCCESS; prompt_id=9c983d79-4f57-4291-9efb-85bbbc912505; client_id=f81a9e8e-cdf1-4f91-8129-86a27d87d236.
- Artifact: D:\VSCODE-WorkSpace\Comfy-UI\work\output\codex_to_comfy\multiview_right_example_00001_.png
- Bytes=233499; SHA=576606c29d64d6146a90814d1d40c58ee9f3c0f3ed6a18437519af656d67a017.
- Original workflow/prompt/input/seed/patches는 manifest historical_evidence에 보존.

### left: m4b-add-left-fixture

- Plan: D:\VSCODE-WorkSpace\Others\Agent-Loop\plans\m4b_add_left_fixture.json
- Plan SHA: e6f3082748b06ac9e2a893eb2cbc29d7a0f98ca32eab06ed6f70923b3db50dd6
- Report: D:\VSCODE-WorkSpace\Others\Agent-Loop\runs\m4b_add_left_fixture_report.json
- Report SHA: 4794b1a37c5d865f69a3797574ce259a51bf386c479df20ae0a545671c8e19f2
- SUCCESS; prompt_id=daaad44a-09c4-4caa-8daa-d95b30cd41b0; client_id=ab2a383d-4cb0-42d3-a5bb-5815a1d50768.
- Artifact: D:\VSCODE-WorkSpace\Comfy-UI\work\output\codex_to_comfy\m4b_left_fixture_00001_.png
- Bytes=259076; SHA=4fa980d17baf0c422d6326a385b6a1a726de24fa8dd5b9be752fb41452d8f248.
- Original workflow/prompt/input/seed/patches는 manifest historical_evidence에 보존.

### back: m4d-adaptive-back

- Plan: D:\VSCODE-WorkSpace\Others\Agent-Loop\plans\m4d_adaptive_back.json
- Plan SHA: 2df91b7ebc30277e491bdba0f8e68447baf93a8ffc1ea100d06c28d06e2f9484
- Report: D:\VSCODE-WorkSpace\Others\Agent-Loop\runs\m4d_adaptive_back_report.json
- Report SHA: d9e8e13e1a1174ceae28b3c9d82c73003c2363d49f582601dc7026f9d8ffea38
- SUCCESS; prompt_id=5f522c94-48f2-4f99-85dc-1dceaa549425; client_id=e29881be-fb00-4ab6-aa04-bca863b005e9.
- Artifact: D:\VSCODE-WorkSpace\Comfy-UI\work\output\codex_to_comfy\m4d_adaptive_back_00001_.png
- Bytes=198427; SHA=bb5ef87a06cc772033ffd313086dfa79d54290f51493400da642140f82d19b31.
- Original workflow/prompt/input/seed/patches는 manifest historical_evidence에 보존.

### geometry: m5a-current-multiview-geometry

- Plan: D:\VSCODE-WorkSpace\Others\Agent-Loop\plans\m5a_current_multiview_geometry.json
- Plan SHA: 94ba24d38efcebc424a53fa6d11560144187a474c8cffb0e445648dda40901b2
- Report: D:\VSCODE-WorkSpace\Others\Agent-Loop\runs\m5a_current_multiview_geometry_report.json
- Report SHA: 3b80a5b835b825e13a2bb16e983338430910826f08376bd854a874f86c95d386
- SUCCESS; prompt_id=a1f9dc8c-a2b0-4627-85dc-1a2d64235164; client_id=1b9201cc-025c-44a2-915d-9adb4ede5925.
- Artifact: D:\VSCODE-WorkSpace\Comfy-UI\work\output\mesh\m5a_current_multiview_geometry_00001_.glb
- Bytes=1071692; SHA=9090cdb0266f4661f239d297682d30514458a4db79abaee5b17212762bf12195.
- Original workflow/prompt/input/seed/patches는 manifest historical_evidence에 보존.

Geometry M5a front=source; left=m5a_current_left.png; back=m5a_current_back.png; right=m5a_current_right.png.
GLB glTF/version2/declared length1071692 확인. Embedded asset.extras.prompt에서 actual checkpoint hunyuan3d-dit-v2-mv-turbo_fp16.safetensors, seed528364197559478 및 네 LoadImage input hash를 추가 확인했다.
Front hash는 source와, right/left/back hashes는 위 actual historical PNG들과 각각 일치한다. 이 결과는 L6 fresh four-view PASS gate의 증거가 아니다.

## Audit questions

| # | 질문 | 판정 | 근거 |
|---|---|---|---|
| 1 | 기존 source 사용 | YES | exists/hash/decode/768×768 |
| 2 | right route | YES | right API nodes1–13 |
| 3 | left route | YES | Left API nodes1–13 |
| 4 | back route | YES | Back API nodes1–13 |
| 5 | current executor 세 route | YES | validate_plan static PASS; live run은 M3 |
| 6 | Hunyuan→GLB route | YES | existing 17-node workflow/model |
| 7 | exact mapping | YES | LoadImage1/4/2/3→conditioning front/right/left/back |
| 8 | image models local | YES | required five files/stat |
| 9 | geometry model local | YES | exact checkpoint/stat |
| 10 | executor SaveGLB | YES | validation/track/verify_glb + existing test |
| 11 | reviewed exact set→Geometry | YES | contract manifest/Review refs + same-bytes staging |
| 12 | frozen Core 무수정 M2 | YES | executor/reviewer primitive + Scenario A glue |
| 13 | Level7 없이 L6 | YES | PASS→GLB structural validation→GEOMETRY_READY |

## Blockers / non-blockers

- BLOCKER 없음.
- NON-BLOCKING: model SHA 생략; historical template SHA 없음; live runtime 미검사;
  F05 generic WorkerPort integration; F07/F2B recovery; geometry semantic quality 미검증.
- M2 최소 추가: sequential runner, exact-role manifest/identity reports, durable stage/Reviewer reservations,
  reviewed-byte input staging, PASS-only geometry gate, usage. 이번 M1에서 구현하지 않는다.

## Local validation / protection

- Inline Python3.12/Pillow static audit. Existing validate_plan 네 번; png_dimensions source integrity/decode.
- Manifest JSON/workflow JSON/graph edges/referenced IDs/output nodes/models/paths/hash: PASS.
- Historical PNG/GLB/report/Plan identity와 document references/mapping/self-review: PASS.
- git diff core-v1.0.0 -- src tests result_review_schema.json reviewer_result_schema.json: empty.
- docs/l6 세 파일만 변경. Workflow hashes/model stat/Research HEAD/status/WIP hash 재검사 unchanged.
- Comfy submissions=0; semantic Reviewer=0; Blender=0.
- Core/source/tests/schema/workflow/model/Research 변경=0; existing verified evidence/tag/release 변경=0.
- python -B / sys.dont_write_bytecode 사용; run/review_once/model import/server startup 호출 없음.

## Final state

AGENT LOOP CORE V1.0.0 = FROZEN / UNCHANGED
L6-M1 ASSET / CONTRACT READY
L6-M2 PIPELINE IMPLEMENTATION = NOT STARTED
LEVEL 6 MULTI-STAGE SUPERVISED PIPELINE = NOT VERIFIED
LEVEL 7 CLOSED FEEDBACK PIPELINE = NOT STARTED
HYPOTHESIS BENCHMARK = NOT STARTED
