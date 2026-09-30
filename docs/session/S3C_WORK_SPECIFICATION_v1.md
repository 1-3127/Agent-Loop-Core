# S3C Work Specification v1

## 1. Identity / Lineage
- session_id: s3c-session-20261001-024950-502243f0
- specification_version: v1
- request_type: NEW_WORK
- previous_session_id: null; S3B handoff is durable reference, not a resumed Session.
- lineage: S3B baseline 89201d2511985a054cfc3045768e6b29ef62e5cf; current User Request: D:\VSCODE-WorkSpace\Others\Agent-Loop-Core\runs\session\s3c-session-20261001-024950-502243f0\user_request.md#sha256=1bf8a65e31b67f72f4511783cdad97906e695af20ea2602731eb5b8e8960dfb6
- logical_loop_run_id: s3c-loop-20261001-024950-502243f0
- l6_child_id: s3c-l6-20261001-024950-502243f0
- bridge_child_id: s3c-bridge-20261001-024950-502243f0
- correction_child_id: s3c-correction-20261001-024950-502243f0
- stable Session directory: D:\VSCODE-WorkSpace\Others\Agent-Loop-Core\runs\session\s3c-session-20261001-024950-502243f0

## 2. User Goal
현재 canonical Scenario A input을 사용하여 실제 Single Image → Multiview → 3D Geometry Session을 한 번 실행하고, 최종 GLB를 사용자 평가 가능한 상태까지 만든다.

Original request summary: one actual fixed Scenario A bound Session, proving lifecycle up to the observable delivery boundary.
Project context: Core v1 frozen, S3B LOCAL-VERIFIED. This is a fresh actual proof; historical outcomes retain their original scope.

## 3. References / Acceptance Authority
| reference_id | exact source_ref | role / authority | preserved scope |
|---|---|---|---|
| USER_CURRENT_REQUEST | D:\VSCODE-WorkSpace\Others\Agent-Loop-Core\runs\session\s3c-session-20261001-024950-502243f0\user_request.md#sha256=1bf8a65e31b67f72f4511783cdad97906e695af20ea2602731eb5b8e8960dfb6 | Goal, both Must-Haves, acceptance criteria, execution authorization and bounds | The current User Request controls acceptance |
| CANONICAL_SOURCE | D:\VSCODE-WorkSpace\Comfy-UI\work\input\hunyuan-official-demo-padded.png#sha256=8a6dd9ca3f8984b31c1243e7698cd5030b423464d80e0ad763609148e0ff4f51 | canonical front identity; 768 x 768 PNG | recognizable silhouette, proportions and major structural parts |

The source image is identity/major-structure authority. Texture, color, PBR, UV, isolated eye/sign detail, smoothness, topology aesthetics, normals and benchmark are not additional acceptance criteria. An observed defect can matter only where it violates a declared identity/major-structure criterion.

## 4. Intended Use
User evaluation of an actual generated GLB and diagnostic evidence. Production platform/performance targets are irrelevant to this proof and are not acceptance requirements.

## 5. Deliverables
One actual final GLB; actual final geometry Review; diagnostic renders and references; immutable Request/Spec/Session/execution lineage. Delivery Package only after INTERNAL_ACCEPT. A failed/aborted candidate remains diagnostic evidence.

## 6. Must-Have
- right/left/back multiview는 canonical front source와 동일한 대상을 유지하고, 주요 실루엣과 구조 파츠를 보존하며, 심각한 crop, missing/detached major part, cross-view identity contradiction이 없어야 한다.
- final GLB는 canonical source와 동일한 대상으로 인식 가능하도록 주요 실루엣, 비율, 주요 구조 파츠를 보존해야 하며 심각한 변형이나 분리된 주요 파츠가 없어야 한다.
Both derive from USER_CURRENT_REQUEST and use CANONICAL_SOURCE for object identity.

## 7. Should-Have
[]

## 8. Non-Goals
Texture, PBR, UV, benchmark quality, generalized geometry quality research, correction policy redesign, new transport, fresh-context infrastructure, Core refactor.

## 9. Acceptance Criteria
| criterion_id | description | authority_ref / reference evidence | blocking_when_unmet |
|---|---|---|---|
| AC-MULTIVIEW-COHERENCE | Generated multiview images must depict the same canonical source object, preserve its recognizable major silhouette and structural parts, and contain no severe crop, missing/detached major part, or cross-view identity contradiction. | USER_CURRENT_REQUEST / CANONICAL_SOURCE, MH1 | true |
| AC-GEOMETRY-IDENTITY | The final GLB must remain recognizable as the canonical source object by preserving its major silhouette, proportions, and structural parts without severe deformation or detached major parts. | USER_CURRENT_REQUEST / CANONICAL_SOURCE, MH2 | true |

Stage projection: multiview = AC-MULTIVIEW-COHERENCE; geometry = AC-MULTIVIEW-COHERENCE + AC-GEOMETRY-IDENTITY. Final geometry covers every declared criterion.
Evidence: exact canonical/source-view image attachments, current GLB-linked diagnostic renders, structured actual Review with authority tags and coverage.
PASS requires mandatory criteria satisfied, no blockers and NONE/null. REVISE requires a declared blocker and supported existing action. No additional criterion is authorized.

## 10. Constraints
- loop_budget: Worker 6 / semantic Reviewer 4 / Renderer 2 / correction 1 / automatic retries 0; conservative aggregate maximum, not a quota.
- actual Session attempts: exactly one run_session(execute=True), after Ready Gate and checkpoint commit.
- deadline: null; no deadline supplied.
- cost: null; no monetary/token estimate; account auth must be CHATGPT_ACCOUNT.
- runtime: existing ComfyUI at http://127.0.0.1:8188, current manifest workflows/models, existing Blender diagnostic.
- format: actual GLB; PNG diagnostic/reference evidence.
- legal/usage: canonical existing source for authorized proof; no new download or usage expansion.
- first production effect makes this attempt immutable. No rerun, extra Review, blind retry, seed reroll, namespace replacement or in-place runtime repair.
- first effect after readiness may occur only while canonical source/manifest/workflow/model/Spec identities still match.

## 11. Interpretation Envelope
fixed_four_view_glb_seed_only
Use current fixed topology and current parameters. Seed-only correction policy remains at most one supported correction and makes no quality improvement guarantee. Frontier selects technical invocation details within this existing capability.

## 12. Explicit User Decisions
The attached current prompt authorizes S3C readiness, genuine freeze, checkpoint commit, and immediate one-shot actual execution after PASS without further permission. Acceptance is limited to the two specified criteria. Stop conditions and proof integrity rules remain binding.

## 13. Known Unknowns
Runtime readiness is probed before execution. Actual semantic closure is unknown. Backend model identity/tokens/credits are recorded only if observable. Authentic post-submission receipt and external fresh-context reset are NOT VERIFIED. These unknowns do not add quality criteria.

## 14. Readiness
- SPECIFICATION_READY: true
- unresolved_blocking_ambiguities: []
- readiness_reason: Current Request explicitly supplies Goal, reference authority, intended deliverable, Must-Haves, criteria, interpretation envelope and execution bounds; no decision-critical intent ambiguity remains.

## 15. Freeze / Delivery Boundary
Document bytes, finalized projection and all five identities are fixed before execution. INTERNAL_ACCEPT is not DELIVERED. prepare_delivery only after actual final acceptance evidence validation. Authentic observable submission receipt is required for DELIVERED/CLOSED. No receipt prediction. Input and final Output are presented together for external User evaluation, which stays outside Core state.
