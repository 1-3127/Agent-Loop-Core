# L7-R1 Geometry Revision Diagnosis

## Executive Summary

**L7-R1 GEOMETRY REVISION DIAGNOSIS = COMPLETE**. Seed-only revision 평가는 **NOT_SUPPORTED_BY_CURRENT_EVIDENCE**. 다음 결정은 **C. workflow/model limitation investigation should come first**를 선택한다.

A/B는 같은 references/model/workflow/settings에서 seed만 바뀐 실제 후보이며 모두 기존 Geometry Review에서 REVISE였다. 기존 PNG를 직접 비교하면 body concentric banding은 A에도 네 azimuth 모두 존재하고, 얼굴 분리 부족과 문자 형태 왜곡도 양쪽에서 지속된다. Reviewer가 서로 다른 blocker를 열거한 사실을 defect의 생성/해소 시점으로 해석할 수 없다.

중요한 추가 사실: 둘 다 POSITION만 있는 untextured GLB이고 NORMAL이 없다. 설치된 Blender importer가 이를 flat shading으로 처리하므로, banding의 실제 표면 굴곡과 면별 shading 강조가 섞여 보일 수 있다. 또한 두 mesh에 non-manifold edges가 있다. 이 사실들은 extraction/export/diagnostic 경로를 우선 조사할 근거이며, 모델 한계 또는 단일 parameter가 원인이라는 확정 증거는 아니다.

이번 작업은 기존 파일의 read-only 분석과 결정 문서 작성이다. Comfy submissions / Blender renders / Frontier semantic Review / revision dispatch 모두0. Blender statistics process도0. 기존 verdict를 변경하거나 새 semantic verdict를 생성하지 않았다.

## Verified Facts

### Baseline / governance

- Repository `D:\VSCODE-WorkSpace\Others\Agent-Loop-Core`; branch scenario-a-l7
- Start HEAD = local origin/scenario-a-l7 = live remote `d4de473fc247c4ae40699d794795ee91b35e5db3`; working tree clean
- main/origin/main/tag dereference `7eee393801f4d8c14278b43ebcbaabaec7ccc9df`
- Tag object `8b962c5d94828af852d020237554606c305ef01e`
- L6 local/remote `840b138cc023c623108c44c3944948b065300f99`
- Root/Others/project AGENTS 및 Agents/workflow.md 확인. Direction Gate v1, R1 scope를 적용.

### Candidate / Review integrity

| Candidate | Artifact SHA-256 | Existing Result SHA-256 | Existing Invocation SHA-256 |
|---|---|---|---|
|A|`1cc00067c772f3efdad34f36cb44c4b5d54ed5bfa4b03a4888a3f3de80fca252`|`f4b08fb1a8eaf2c5778971131e7d97ac24cb038945d9f7ee6360a3a3445446d3`|`ce1342de0f6e4852755ecc18bd2aaba38c135df3a239ca7f530033b8801492ab`|
|B|`24e0b6a9ff2b3aa23f9a211ade467453900b45a94d33cb41a945f3251df6c83b`|`a582d44d00eacfad3f42e1a8748a5cce09a76d1a9f28a261ce4c8e74d633954e`|`6e25e2ad96dfa1747c55aa918e086a2b52d45023e26a86d1b0e3e309af6ff1b3`|

- Candidate A GLB: [geometry_00001_.glb](D:/VSCODE-WorkSpace/Comfy-UI/work/output/mesh/l6/l6-m3-20260930-164920-8109160a/geometry_00001_.glb)
- Candidate B GLB: [geometry_00001_.glb](D:/VSCODE-WorkSpace/Comfy-UI/work/output/mesh/l7/l7-m3-20260930-205145-b6025e96/geometry_00001_.glb)
- A source Review: [review_result.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l7/l7-m1-20260930-184618-3703fee4/review_result.json); REVISE/REGENERATE_GEOMETRY/geometry
- B Review: [geometry_review_result.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/runs/l7/l7-m3-20260930-205145-b6025e96/geometry_review_result.json); REVISE/REGENERATE_GEOMETRY/geometry
- A/B Invocation SUCCESS/CODEX_CLI/CHATGPT_ACCOUNT; exact8 attachments checked from current bytes; terminal record references checked
- M3 final ABORT/REVISION_BUDGET_EXHAUSTED; additional effect0. A/M1 final GEOMETRY_REVIEWED.
- Exact four source references match both GLBs embedded is_changed hashes and both Review attachment sets.
- Workflow SHA-256 `729e9e02c3ef655c5f576067ec3cb291285dcf1d1db70100857c141c026ab2fa`
- Six models match manifest size/exact nanosecond mtime; full multi-GB model hash not measured.

### Settings are current graph values

`hunyuan3d-dit-v2-mv-turbo_fp16.safetensors`; latent resolution1024; batch1; FluxGuidance3.5; AuraFlow shift1.0; steps20; cfg4.0; sampler euler; scheduler normal; denoise1.0; decode num_chunks8000; octree128; surface net; threshold0.6; SaveGLB17.

A/B embedded graph differences are exactly left/back/right input namespace, seed, and output prefix. No input bytes/model/conditioning order/sampling/decoding/extraction setting differences. Seed A528364197559477 → B528364197559478.

## Candidate A vs Candidate B

Pure GLB JSON/BIN parsing + installed numpy; no Blender process, dependency install, asset rewrite, or topology repair. Accessor boundaries/types/counts, triangle indexing, finite coordinates, JSON min/max, reference/seed identity checked.

| Metric | Candidate A | Candidate B |
|---|---:|---:|
|File bytes|1139016|1049244|
|GLB version / declared length|2 / 1139016|2 / 1049244|
|Scene / nodes / mesh instances / mesh primitives|1 / 1 / 1 / 1|1 / 1 / 1 / 1|
|Vertices|31023|28706|
|Triangles (mode4)|63590|58426|
|Index connected components|1|1|
|Exact-position welded components|1|1|
|Isolated / duplicate-position vertices|0 / 0|0 / 0|
|Unique edges|94229|86884|
|Boundary edges (incidence1)|8|5|
|Non-manifold edges (incidence>2)|2225|1446|
|Maximum edge incidence|4|4|
|Zero-area / duplicate unoriented triangles|0 / 0|0 / 0|
|V-E+F (not genus)|384|248|
|Surface area, normalized units|5.469771198|5.031099619|
|NORMAL / UV / texture images|absent / absent / 0|absent / absent / 0|

| Blender world coordinate metric | A | B |
|---|---|---|
|bbox min|-0.524817348, -0.452930063, -0.835320473|-0.540125191, -0.483146012, -0.818140209|
|bbox max|0.540090144, 0.491504759, 0.851402819|0.556996405, 0.449561715, 0.835731328|
|Dimensions X/Y/Z|1.064907491, 0.944434822, 1.686723292|1.097121596, 0.932707727, 1.653871536|
|Center|0.007636398, 0.019287348, 0.008041173|0.008435607, -0.016792148, 0.008795559|

glTF nodes are `{mesh:0}` without TRS/matrix, meaning identity. Existing Blender import matrix is identity for Mesh_0. Applying glTF(x,y,z) → Blender(x,-z,y) to decoded coordinates reproduces both historical render-manifest bbox exactly within1e-7. No transform/framing mismatch was found. Manifest world dimensions are normalized asset units, not measured real-world size.

Graph components count is not semantic object/part count: the sign/body/poles can belong to one connected index graph. Boundary/non-manifold counts show the meshes are not clean closed two-manifold meshes, but do not locate a visually significant hole or prove the cause of facial loss/banding. With non-manifold topology, V-E+F is not interpreted as genus and volume/watertight quality is not claimed. Lower counts or file size in B are not evidence of quality improvement.

## Reference Sufficiency Audit

Labels below describe directly inspected existing PNG appearance. VISIBLE is image evidence, not calibrated multiview geometry or proof of relief depth. PARTIAL = only part of the feature is visible; OCCLUDED = hidden by view/object; AMBIGUOUS = appearance cannot resolve requested geometry.

| Feature | front | right | left | back | Evidence / limitation |
|---|---|---|---|---|---|
| Eyes | VISIBLE | VISIBLE | VISIBLE | OCCLUDED | Two separate eye regions visible in all3 front-facing images; pupil/highlight color contrast may be texture, relief depth not calibrated. |
| Bill/beak | VISIBLE | VISIBLE | VISIBLE | OCCLUDED | Broad protruding bill with lower edge; side pictures are oblique, not exact profile. Relative proportions vary modestly. |
| HY3D letter identity | VISIBLE | VISIBLE | VISIBLE | OCCLUDED | All3 front-facing sign images read HY3D; no obvious view-synthesis glyph substitution found. Black H/Y/D ink does not prove raised geometry. |
| HY3D relief depth | AMBIGUOUS | AMBIGUOUS | AMBIGUOUS | OCCLUDED | Red3 looks shaded/raised; exact relief heights for all letters cannot be recovered from these PNGs. |
| Body surface | VISIBLE | VISIBLE | VISIBLE | VISIBLE | Smooth shaded appearance in all4; no obvious concentric ridges in references. Black/white pattern and gradients are not evidence of physical grooves. |
| Two sign poles | VISIBLE | PARTIAL | PARTIAL | VISIBLE | Both poles present; flippers/body occlude parts and visible lower length differs by projection. |
| Feet | VISIBLE | VISIBLE | VISIBLE | PARTIAL | Two feet clear from front/oblique sides; back mostly hides feet with only lower extremities visible. |
| Flippers | PARTIAL | PARTIAL | PARTIAL | PARTIAL | Major gripping pads visible, full attachment/thickness hidden in every view; near/far prominence changes. |

| Reference | Bytes / dimensions | SHA-256 |
|---|---|---|
|[front](D:/VSCODE-WorkSpace/Comfy-UI/work/input/hunyuan-official-demo-padded.png)|142572 /768x768|`8a6dd9ca3f8984b31c1243e7698cd5030b423464d80e0ad763609148e0ff4f51`|
|[right](D:/VSCODE-WorkSpace/Comfy-UI/work/output/l6/l6-m3-20260930-164920-8109160a/right_00001_.png)|233500 /768x768|`6c4828c226de954cab7daee8975f4e2f60ee1507bee5c9eb72fd34d9c146bc4d`|
|[left](D:/VSCODE-WorkSpace/Comfy-UI/work/output/l6/l6-m3-20260930-164920-8109160a/left_00001_.png)|223398 /768x768|`d1f6c681ebbee462e26b42e5de710caf34424edfa68eb01686f7caa88b7b89d6`|
|[back](D:/VSCODE-WorkSpace/Comfy-UI/work/output/l6/l6-m3-20260930-164920-8109160a/back_00001_.png)|232979 /768x768|`2aa7f06a081869b961650498fe77bb19955019b958098156cee42b30bc1f937f`|

Answers to the sufficiency questions:

- Requested eyes/bill/body/poles/feet/flippers are actually visible to differing extents. Back occlusion of face/text is expected.
- Major subject/sign arrangement is coherent across4 images. Right/left pictures show both eyes and the front sign; they are oblique rather than orthographic90-degree views. No measured camera pose, intrinsic calibration, silhouette registration, or actual3D ground truth exists. The conditioning node uses fixed view-position tags; reference naming is not pose validation.
- HY3D is readable in front/right/left; current evidence does not show a source glyph error that explains the output malformed letters. Relief geometry remains ambiguous.
- View-angle/proportion variation and hidden flipper attachment can contribute to ambiguity, but cannot by themselves explain all-view body banding or the loss of clearly separated front eye/bill appearance.
- Face separation and smooth body appearance are clearer in references than in both neutral geometry renders. However textureless output suppresses pupil/albedo contrast; color disappearance is not proof of missing eye vertices.

## Persistent vs Variable Defects

These are read-only inspection observations, not a replacement semantic verdict. Both authoritative actual Reviewer Results remain REVISE.

| Existing diagnostic azimuth | Persistent A/B appearance | What changed with seed | Limitation |
|---|---|---|---|
|0 front | Concentric belly bands; weak eye/bill separation; malformed sign relief | A first letter looks U-like; B becomes horizontal bar-like. Eye lumps, sign relief and beak contour differ. |No claim that black printed glyph fidelity equals3D topology fidelity. |
|90 side | Layered/terraced flank, protruding bill, uneven flipper/pole junction |Body profile, bill projection, near-flipper shape and feet outlines vary. |Existing generated side references are oblique, not this exact90-degree camera. |
|180 back | Concentric back bands; recessed sign back; major body/poles/appendages remain |Band spacing, tail/lower silhouette and back-board details vary. |No obvious large hole in PNG does not establish watertightness. |
|270 side |Layered side body, limited facial detail, sign/body/poles retained |Flipper protrusion, side bill outline and toe/tail silhouette vary. |Neutral studio shading emphasizes faceting. |

Candidate-specific observations concern the exact letter/stair patterns and face/appendage contours. The defect classes are persistent. A Reviewer reported eyes/letters; B Reviewer reported bands/face. A bands not listed in Result does not mean absent; B letters not listed does not mean corrected. No quantified ranking, improvement claim, or new PASS/REVISE was assigned.

### Existing image evidence

| Azimuth | Candidate A | Candidate B |
|---|---|---|
|0|[geometry_azimuth_0.png](D:/VSCODE-WorkSpace/Comfy-UI/work/output/l7/l7-m1-20260930-184618-3703fee4/geometry_review/geometry_azimuth_0.png)|[geometry_azimuth_0.png](D:/VSCODE-WorkSpace/Comfy-UI/work/output/l7/l7-m3-20260930-205145-b6025e96/geometry_review/geometry_azimuth_0.png)|
|90|[geometry_azimuth_90.png](D:/VSCODE-WorkSpace/Comfy-UI/work/output/l7/l7-m1-20260930-184618-3703fee4/geometry_review/geometry_azimuth_90.png)|[geometry_azimuth_90.png](D:/VSCODE-WorkSpace/Comfy-UI/work/output/l7/l7-m3-20260930-205145-b6025e96/geometry_review/geometry_azimuth_90.png)|
|180|[geometry_azimuth_180.png](D:/VSCODE-WorkSpace/Comfy-UI/work/output/l7/l7-m1-20260930-184618-3703fee4/geometry_review/geometry_azimuth_180.png)|[geometry_azimuth_180.png](D:/VSCODE-WorkSpace/Comfy-UI/work/output/l7/l7-m3-20260930-205145-b6025e96/geometry_review/geometry_azimuth_180.png)|
|270|[geometry_azimuth_270.png](D:/VSCODE-WorkSpace/Comfy-UI/work/output/l7/l7-m1-20260930-184618-3703fee4/geometry_review/geometry_azimuth_270.png)|[geometry_azimuth_270.png](D:/VSCODE-WorkSpace/Comfy-UI/work/output/l7/l7-m3-20260930-205145-b6025e96/geometry_review/geometry_azimuth_270.png)|

Front comparison, unchanged source image references above:

![Existing Candidate A front diagnostic](D:/VSCODE-WorkSpace/Comfy-UI/work/output/l7/l7-m1-20260930-184618-3703fee4/geometry_review/geometry_azimuth_0.png)

![Existing Candidate B front diagnostic](D:/VSCODE-WorkSpace/Comfy-UI/work/output/l7/l7-m3-20260930-205145-b6025e96/geometry_review/geometry_azimuth_0.png)

## Geometry Workflow Control Surface

Graph definition: [Hunyuan3D_MV_RTX4060_api.json](D:/VSCODE-WorkSpace/Comfy-UI/workflows/03_Multiview_to_3D/Hunyuan3D_MV_RTX4060_api.json). Adapter allowlist/type/range checks: [codex_to_comfy.py](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/src/scenario_a/codex_to_comfy.py:23). Controller revision construction/expected Plan: [l7_feedback_controller.py](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/src/scenario_a/l7_feedback_controller.py:234).

Patchable means the primitive adapter validate_plan accepts that field. It does not mean the current frozen L7 controller accepts a changed policy: current controller reconstructs the exact prior Plan with seed+1 and rejects alternate values. No parameter override CLI exists for these levers.

| Parameter | Current value | Node | Primitive patchable | Contract/code requirement if changed | Expected impact category / evidence |
|---|---|---|---|---|---|
|seed|A528364197559477;B528364197559478|14 KSampler|Yes|Existing seed+1 policy; no Plan top-level schema change|stochastic sampling diversity; actual variation confirmed, closure unsupported|
|steps|20|14|No|Explicit adapter field permission/validation + new controller policy; Plan top-level shape can remain|sampling convergence; quality impact unknown, Turbo is step-distilled|
|cfg|4.0|14|No|Same bounded field/policy changes|generation guidance; sensitivity not measured|
|sampler_name|euler|14|No|Enum validation/allowlist + policy required|sampling convergence; model/scheduler compatibility unknown|
|scheduler|normal|14|No|Enum validation/allowlist + policy required|sampling convergence; no proof alternate schedule is valid|
|denoise|1.0|14|No|Range validation/allowlist + policy required|unknown; this is generation from empty latent, not localized mesh repair|
|FluxGuidance.guidance|3.5|11|No|Field/allowlist + policy required|generation guidance; distinct from CFG4; checkpoint has guidance embedding weights|
|AuraFlow.shift|1.0|13|No|Field/range policy required|sampling convergence; sensitivity unknown|
|latent resolution|1024|12 EmptyLatentHunyuan3Dv2|No|Field/range allowlist + policy required|latent/shape resolution; tensor shape64x1024, not1024-pixel image or voxel grid|
|batch_size|1|12|No|Field permission plus multi-output/budget contract; outside a minimal single-candidate correction|unknown; not selected|
|octree_resolution|128|15 VAEDecodeHunyuan3D|Yes,16..512|Primitive already supports; L7 policy/expected Plan/evidence guard must explicitly permit; no generic schema redesign needed|voxel/mesh extraction resolution; current decoder evaluates129^3 points|
|num_chunks|8000|15|No|Field/range permission/policy required|unknown as correction; current code uses query batch size, mainly execution/memory behavior|
|algorithm|surface net|16 VoxelToMesh|No|Allowed enum + controller policy; existing graph exposes basic too|unknown within fixed category list; mesh extraction method, not sampling or resolution|
|threshold|0.6|16|No|Float range/allowlist + controller policy|surface extraction threshold; scalar level set, no sensitivity evidence|
|CLIPVisionEncode.crop|none at all4|6/7/8/9|No|Enum/preprocessing policy and input lineage changes|unknown; image-conditioning preprocessing|
|input image filenames|original front; staged left/back/right|1/2/3/4|Yes|Reference/staging/manifest identity validation; actual reference regeneration separate task|unknown; input identity/conditioning, not chosen here|
|checkpoint name|hunyuan3d-dit-v2-mv-turbo_fp16.safetensors|5|No|Workflow/model identity and asset contract; model replacement separate last option|unknown; not chosen|
|filename_prefix|current run geometry namespace|17 SaveGLB|Yes|Required fresh namespace and report identity checks|unknown; identity only, no shape correction|

Conditioning order front/left/back/right and source→1/left→2/back→3/right→4 are wired links, not tunable scalar policy. No ImageScale node exists in this graph even though the adapter has an ImageScale patch rule.

### Meaning and diagnostic confounds

- Local EmptyLatent allocates torch.zeros([batch,64,resolution]); official Turbo configuration also declares VAE num_latents3072. Current1024 differs from local node default3072, but this is not evidence that3072 fixes the defects.
- Local VanillaVolumeDecoder builds a dense linspace grid (octree+1)^3 and batches queries by num_chunks. Despite the parameter name octree, the inspected current decoder uses this dense grid, not a proven adaptive sparse octree.
- Surface net averages threshold intersections within active cells and forms triangles from adjacent active cells. Basic creates voxel boundary box faces. Surface-net topology anomalies in the outputs justify investigation, not a confirmed extraction bug/root-cause verdict.
- Both GLB primitives have POSITION only. SaveGLB accepts optional normals but the current VoxelToMesh graph supplies none. Blender importer set_poly_smoothing marks no-NORMAL primitives flat; diagnostic script does not apply shade_smooth.
- Both texture images and TEXCOORD are absent; diagnostic renderer uses SINGLE neutral color. Eye pupil/white-mask contrast and printed letter color cannot survive as appearance through this path. Real eye/bill mesh shape may still be insufficient; current data cannot separate every color cue from relief geometry.

Missing NORMAL → flat normals is specified by [Khronos glTF2.0](https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc#using-primitive-data). The installed Blender implementation independently confirms this behavior; this does not prove that all observed rings are only shading.

Official [MV Turbo config](https://huggingface.co/tencent/Hunyuan3D-2mv/blob/main/hunyuan3d-dit-v2-mv-turbo/config.yaml) has guidance_embed=true and num_latents3072; current checkpoint header has4 guidance_in keys. The [Tencent repository](https://github.com/Tencent-Hunyuan/Hunyuan3D-2) separates shape and texture generation. These sources provide context, not a replacement for local graph/actual evidence or a claim of native-vs-Comfy equivalence.

Local source anchors:

- [nodes_hunyuan3d.py](D:/VSCODE-WorkSpace/Comfy-UI/runtime/ComfyUI_windows_portable/ComfyUI/comfy_extras/nodes_hunyuan3d.py:10) — latent shape and node schemas;15decode;16extract
- [vae.py](D:/VSCODE-WorkSpace/Comfy-UI/runtime/ComfyUI_windows_portable/ComfyUI/comfy/ldm/hunyuan3d/vae.py:425) — dense volume query grid and chunk batching
- [nodes_save_3d.py](D:/VSCODE-WorkSpace/Comfy-UI/runtime/ComfyUI_windows_portable/ComfyUI/comfy_extras/nodes_save_3d.py:127) — absent normals fallback; export carries optional NORMAL only
- [mesh.py](D:/Blender_5.2/5.2/scripts/addons_core/io_scene_gltf2/blender/imp/mesh.py:865) — actual installed no-NORMAL flat shading
- [l7_blender_diagnostic.py](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/src/scenario_a/l7_blender_diagnostic.py:46) — existing import; neutral Workbench;no smoothing operation

## Seed-Only Revision Assessment

**NOT_SUPPORTED_BY_CURRENT_EVIDENCE** for the currently observed defect classes.

Facts: two actual seeds produce different meshes/letter contours, but both actual Reviews return REVISE; body banding and face/text separation problems persist on direct existing-image inspection. Seed changes sampling noise while holding reference representation, latent size, VAE grid, extraction algorithm/threshold, missing NORMAL export and diagnostic shading constant.

[추론] A policy changing only stochastic initialization has no observed leverage over these persistent failure classes in this pair. This is absence of current empirical support, not proof no possible seed could pass, no estimate of success probability, and not a model-incapability conclusion. Sample size2, no parameter/ablation control, no repeatability baseline.

## Root-Cause Hypothesis Matrix

Confidence is evidence strength for the stated local hypothesis, not a factual root-cause declaration.

| Hypothesis | Supporting evidence | Contradicting / limiting evidence | Unknowns | Confidence |
|---|---|---|---|---|
|H1 reference inconsistency / insufficiency|Oblique named side views; no camera calibration; proportions vary; relief depth/hidden flipper attachment ambiguous|Eye/bill separation is clear in3 images; body appears smooth in4; letters readable in3; existing Reviewer notes coherent major arrangement|Actual camera angles; conditioning resize/token feature loss; relief ground truth|MEDIUM|
|H2 model limit for face/text geometry|Both seeds compress fine facial structure and malformed text relief under same model|Major subject/poles/sign/feet retained; downstream grid/shading confounds; source printed color vs relief ambiguous|Higher-capacity representation/valid model sampling behavior; actual required relief|LOW|
|H3 current generation/sampling settings insufficient|Latent1024 vs default/config3072; current values never ablated|More steps/CFG not inherently better for step-distilled Turbo; same evidence also compatible with extraction/shading|Isolated latent/guidance/step sensitivity and native scheduling compatibility|MEDIUM|
|H4 voxel/mesh extraction contributes artifacts|Grid128; rings/facets on all views; A/B have2225/1446 non-manifold edges; surface-net topology path shared|Final meshes do not retain pre-extraction field; input field itself may already encode distortion; topology count does not localize rings|Fixed latent/voxel snapshot; normals/position residual attribution; alternative extraction on same field|MEDIUM|
|H5 diagnostic rendering exaggerates/misrepresents|NORMAL absent; installed importer forces flat shading; neutral rendering removes color cues and shadows highlight face facets|Actual silhouette/relief varies; source face may still genuinely be merged; changing shading cannot restore absent parts|Magnitude of rings from physical offsets versus face normals; no second render permitted|HIGH for shading contribution; full defect explanation unproven|
|H6 seed changes details but core failure persists|Different hashes/stats/letter and limb contours, same actual REVISE and persistent defect classes|Only2 seeds; cannot generalize to all seeds or claim exact same defect placement|Larger stochastic distribution deliberately not explored|HIGH for this A/B pair only|

## Minimal Correction Policy Candidates

Exactly3 conditional candidates, no execution authorization. Each fixes B seed528364197559478, same references/model/all other quality settings and uses a future fresh namespace. Current controller unconditionally applies seed+1; these proposals require a separately approved bounded policy change before any actual use. No seed search/best-of-N/model replacement proposed.

### P1 — VAE grid resolution only

- Changed parameter: node15.octree_resolution128 →256; no latent/sampler/extraction-algorithm change
- Why/target: coarse field evaluation may contribute to fine face/letter loss and faceted body. Local decoder gives a direct extraction-resolution lever, already supported by primitive adapter.
- Additional compute: query count129^3=2,146,689 →257^3=16,974,593, ratio7.9073. This is grid-point arithmetic, not a measured runtime/VRAM multiplier; sampling unchanged. Runtime/peak memory unknown.
- Contract/code: primitive patch allowed already; explicit controller expected-Plan/policy/evidence permission required, no new generic schema/framework. Existing source Plan/evidence must remain immutable.
- Risk: decoding/extraction time/memory increase on8GB GPU; may leave missing features and no-NORMAL faceting unchanged.
- Evidence strength MEDIUM for testing resolution sensitivity; LOW for predicting semantic closure.

### P2 — Extraction algorithm only (diagnostic control)

- Changed parameter: node16.algorithm surface net →basic; threshold0.6/octree128/all generation settings fixed
- Why/target: distinguish shared surface-net mesh construction contribution from fixed field/model generation. This is a diagnostic contrast, not a claim of cleaner final geometry.
- Additional compute: sampling/field computation unchanged in design; algorithm mesh size/CPU/export cost unknown. If a verified voxel cache/snapshot exists, no inference would be logically necessary; current durable evidence has no reusable voxel snapshot.
- Contract/code: VoxelToMesh already exposes basic; adapter currently blocks algorithm patch. Narrow enum permission + controller policy/evidence validation would be required separately. No current edits.
- Risk: basic deliberately generates box-like voxel boundaries and may look worse/more faceted, expand vertex counts, or obscure small features. Raw index components incomparable without exact-position welding.
- Evidence strength MEDIUM for extraction distinction, LOW as a correction for quality.

### P3 — Latent representation length only

- Changed parameter: node12.resolution1024 →3072; octree128/sampler/extractor/threshold fixed
- Why/target: test whether current latent/shape representation loses face/letter structure before extraction.3072 is current node default and official VAE config context, not guaranteed optimal.
- Additional compute: latent elements64x1024 →64x3072 (3x), increased generation/attention workload and memory expected. Exact time/VRAM multiplier unknown; no benchmark performed.
- Contract/code: primitive allowlist currently lacks EmptyLatentHunyuan3Dv2; narrow resolution/range permission + controller policy needed. Plan top-level shape need not change.
- Risk:RTX4060 memory/time; unchanged voxel128 and flat shading may mask any benefit; no assurance model/training supports a quality gain.
- Evidence strength LOW-to-MEDIUM for hypothesis discrimination; LOW for predicting PASS.

## Information-Value Comparison

| Policy | Information value | What it can distinguish | What it cannot establish |
|---|---|---|---|
|P1 grid128→256|MEDIUM|Sensitivity to field-evaluation density with fixed latent/generation design; tests part of H4|No guaranteed normal/shading isolation; same-seed inference repeatability and fixed pre-decode latent not proved|
|P2 surface net→basic|MEDIUM now; HIGH only with identical verified voxel input|Different extraction topology on fixed field would strongly discriminate H4 downstream from H2/H3 generation|With no saved voxel, fresh inference/caching uncertainty weakens isolation; blocky basic output not a quality metric|
|P3 latent1024→3072|MEDIUM|Representation capacity sensitivity, part of H3|Does not by itself prove model limitation H2 or overcome downstream grid/shading bottleneck|

HIGH conditional information is not high PASS probability. No candidate receives a numerical success prediction. Primary decision uses information value and control availability, not PASS hunting.

## Recommended Next Decision

**C. workflow/model limitation investigation should come first.**

구체적인 범위는 기존 workflow의 extraction → GLB NORMAL export → Blender import/shading 경로와, 눈·문자 형태를 원본의 색상 표현과 분리할 수 있는지 확인하는 것이다. 현재 model replacement를 권고하는 것은 아니다.

Reason: strongest newly verified facts are shared downstream behavior (no NORMAL, forced flat shading, mesh-edge anomalies), while fields/latents were not durably retained. An immediate fresh parameter run would mix generation variability with these confounds. P1 is the most direct later correction lever because primitive adapter already supports it, but is deferred until the evaluation/field-control question is resolved.

Minimal next evidence to decide a later policy:

- Read-only separation of body vertex-position deviations and face-normal discontinuities in fixed B; quantify where bands lie without changing asset/verdict.
- Explicit feature contract: visible eye/bill shape versus pupil/printed sign albedo; retain current authoritative Review outcomes while identifying geometric observability.
- Determine whether exact pre-extraction field/latent reuse is actually available and verifiable. Current Comfy execution_cached event is not a durable voxel snapshot. Any capture/re-extraction/new render would require a separate task.

Uncertainty: it may still turn out generation/latent/model representation is the dominant issue; current evidence does not identify the sole cause. This recommendation prepares a discriminating test rather than requiring a PASS outcome. No next investigation/experiment was executed as part of R1.

## Unknowns / Evidence Gaps

- Actual relief depths / calibrated multi-view geometry / eye vertices ground truth unavailable
- No saved latent or voxel field; cannot replay only one downstream stage with cryptographic identity from current durable files
- No normal-smoothing diagnostic counterpart; no re-render in this milestone
- Reference opacity/background/preprocessing and conditioning feature resolution not causally audited end-to-end
- No scalar-field level-set or decoder-grid sensitivity measurement
- No proof20steps/CFG4/AuraFlow schedule is optimal or inadequate for current Turbo checkpoint
- Two candidates cannot estimate seed distribution or model incapability
- No surface self-intersection, signed volume, semantic feature segmentation, or production topology approval claimed
- Model full hashes unavailable; protection is file stat plus checkpoint-header hash, not a5GB cryptographic weight audit

## Protection / Effects

| Effect | R1 actual count |
|---|---:|
|Comfy submissions|0|
|Blender diagnostic renders|0|
|Frontier semantic Reviewer|0|
|Revision dispatch|0|
|Blender read-only statistics process|0|

Only loopback GET history/queue/object_info, local binary/image/source reads and one-off numpy computations were used. Official public documentation browsing transferred no local images. 기존 PNG는 이번 read-only 진단에서 직접 확인했으며, 새 semantic Reviewer process는 시작하지 않았다.

- 229 prior tracked files protected by SHA snapshot; SHA aggregate `ccf95454806da2a380121bc32eb6723eee9501a97e89f5ee8982a93c431e6971`
- Frozen main/tag and L6 refs unchanged; Core/L6/M1/M2/M3 source/tests/evidence unchanged
- Research HEAD `7e1572a7e35866519b75b767398288396a27f9b0`; sole untracked ac6_f2b_resume.py
- F2B WIP SHA `2a58ab64e8838e8c3da6d8b4d62526e1a8d0d834bb26058d905d80d73dfd9369` unchanged
- Existing GLB/PNG identities rechecked; no artifact modification; workflow hash/model stats unchanged
- New files only: this document and [L7_R1_GEOMETRY_EVIDENCE_AUDIT.json](D:/VSCODE-WorkSpace/Others/Agent-Loop-Core/docs/l7/L7_R1_GEOMETRY_EVIDENCE_AUDIT.json)
- No repository analysis helper or production change. Full regression not rerun, per document-only R1 rule. Pure-parser structural/bounds/connectivity validations PASS.
- Normal commit/push only scenario-a-l7;main/tag/release untouched. Final commit/remote/clean check reported in Codex final response.

## Final Status

```text
AGENT LOOP CORE V1.0.0 = FROZEN / UNCHANGED
LEVEL 6 MULTI-STAGE SUPERVISED PIPELINE = VERIFIED
L7-M0 MANDATORY GATE = PASS
L7-M1 GEOMETRY REVIEW BRIDGE = VERIFIED
L7-M2 MINIMAL FEEDBACK CONTROLLER = READY
L7-M3 ACTUAL CLOSED FEEDBACK PROOF = NOT PASSED
L7-R1 GEOMETRY REVISION DIAGNOSIS = COMPLETE
LEVEL 7 CLOSED FEEDBACK PIPELINE = NOT VERIFIED
HYPOTHESIS BENCHMARK = NOT STARTED
```

R1 does not retry Level7 proof, perform a parameter experiment, overwrite a verdict, or deliver a newly accepted geometry. STOP after diagnosis packaging/commit/push/clean verification.
