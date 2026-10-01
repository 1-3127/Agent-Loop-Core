# Post-Stabilization Actual Loop — Work Specification v1

## Identity / Dialogue
Session: psa-session-20261001-031107-2c54c2a3; logical Loop: psa-loop-20261001-031107-2c54c2a3; request_type: NEW_WORK; version: v1.
Previous Session: null. Existing S3C is historical reference, not a resumed attempt.
Children: L6 psa-l6-20261001-031107-2c54c2a3, bridge psa-bridge-20261001-031107-2c54c2a3, optional correction psa-correction-20261001-031107-2c54c2a3.

Specification Dialogue: 현재 새 요청, historical original Request, canonical source와
현재 fixed capability를 다시 확인했다. [추론] 동일 Scenario A validation objective는
기존 두 identity/major-structure 기준으로 구체화할 수 있다. 별도 의도 질문은 필요하지 않다.
새 명세와 current stage evidence를 사용하며, 이전 reasoning trajectory와 active failure state를 복원하지 않는다.

## Goal
현재 canonical Scenario A input으로 실제 Single Image → Multiview → 3D Geometry Loop를 한 번 실행하고, 고정 명세에 따른 실제 검수와 허용된 bounded correction으로 INTERNAL_ACCEPT 도달 여부를 검증한다.

## References / Authority
| reference_id | source_ref | role / preserved scope |
|---|---|---|
| USER_CURRENT_REQUEST | D:\VSCODE-WorkSpace\Others\Agent-Loop-Core\runs\session\psa-session-20261001-031107-2c54c2a3\user_request.md#sha256=37bda4fe4f126dd56af0afed412c30411cf77e9169e68b7e79134e2c8a7cfa49 | 이번 execution scope, 동일 validation objective, bounds, stop-at-INTERNAL_ACCEPT |
| CANONICAL_SOURCE | D:\VSCODE-WorkSpace\Comfy-UI\work\input\hunyuan-official-demo-padded.png#sha256=8a6dd9ca3f8984b31c1243e7698cd5030b423464d80e0ad763609148e0ff4f51 | front object identity, recognizable silhouette, proportions, major structural parts |
| ORIGINAL_REQUEST_REFERENCE | D:\VSCODE-WorkSpace\Others\Agent-Loop-Core\runs\session\psa-session-20261001-031107-2c54c2a3\original_request_reference.md#sha256=1bf8a65e31b67f72f4511783cdad97906e695af20ea2602731eb5b8e8960dfb6 | historical objective/Must-Haves의 durable reference; 과거 실행/Delivery 승인은 비활성 |

Reference의 세부 문자, 색상, texture, smoothness, eye/sign detail 자체는 추가 acceptance authority가 아니다.
그런 결함이 선언된 identity/major structure를 위반하는 경우만 해당 criterion의 blocker가 될 수 있다.

## Intended Use / Deliverables
현재 architecture가 실제 production path로 내부 수락 가능한 GLB를 제작·검수할 수 있는지 검증한다.
Production platform/performance 목표는 관련성이 없어 제외한다.
One actual GLB candidate, current multiview/geometry semantic Review, diagnostic PNGs,
Request/Specification/Session/child/tool/invocation/artifact/hash evidence를 보존한다.
미수락 artifact는 diagnostic candidate로 유지한다. User Delivery는 이번 checkpoint에 포함하지 않는다.

## Must-Haves
- right/left/back multiview는 canonical front source와 동일한 대상을 유지하고, 주요 실루엣과 구조 파츠를 보존하며, 심각한 crop, missing/detached major part, cross-view identity contradiction이 없어야 한다.
- final GLB는 canonical source와 동일한 대상으로 인식 가능하도록 주요 실루엣, 비율, 주요 구조 파츠를 보존해야 하며 심각한 변형이나 분리된 주요 파츠가 없어야 한다.

위 Must-Haves는 현재 요청의 동일 validation objective를 historical Request와 canonical source에서 다시 도출한 최종 해석이다.
Should-Haves: [].

## Acceptance Criteria / Applicability
| criterion_id | description | authority_ref | blocking_when_unmet | supported stage | intended evidence |
|---|---|---|---|---|---|
| AC-MULTIVIEW-COHERENCE | Generated multiview images must depict the same canonical source object, preserve its recognizable major silhouette and structural parts, and contain no severe crop, missing/detached major part, or cross-view identity contradiction. | USER_CURRENT_REQUEST | true | multiview | exact current front/right/left/back PNGs, source identity, actual semantic Review Request/Result/Invocation and coverage |
| AC-GEOMETRY-IDENTITY | The final GLB must remain recognizable as the canonical source object by preserving its major silhouette, proportions, and structural parts without severe deformation or detached major parts. | USER_CURRENT_REQUEST | true | geometry | exact current GLB, its linked Blender neutral four-view diagnostics, current input references, actual semantic Review and coverage |

multiview = AC-MULTIVIEW-COHERENCE; geometry = AC-GEOMETRY-IDENTITY.
Geometry does not re-judge the multiview criterion. Final acceptance aggregates the two current applicable stage evidence sets.
Each blocking criterion is assigned to a supported observable stage; no unsupported mandatory criterion exists.
Raw Review verdict is authoritative current evidence. PASS requires applicable blocking criteria SATISFIED, no blockers, NONE/null.
REVISE requires criterion-scoped authorized blocker and supported action. No expected-PASS fixture, no hidden quality criterion.

## Constraints / Interpretation Envelope
Capability: fixed_four_view_glb_seed_only.
Aggregate maxima: Worker6 / semantic Reviewer4 / Renderer2 / revision1 / automatic retries0.
Exactly one run_session(execute=True), after CP1 commit and readiness PASS.
Worker/review/render timeouts: 600 seconds each, existing defaults.
Existing workflow/model parameters and source bytes are fixed. Correction is at most one
authorized existing seed-only action, based on current evidence; no quality improvement guarantee.
ComfyUI endpoint http://127.0.0.1:8188; current manifest workflows/models; Blender 5.2.0 LTS;
existing account-mode semantic Reviewer with actual attached PNG evidence.
Deadline/cost limit: null (unspecified). Actual model/effort/tokens/credits unknown unless independently observable.
No credentials recorded. Existing canonical source used solely for this authorized proof.

## Non-Goals / Explicit Boundaries
Production source/test modifications, bug fixes, contract changes, new verifier/correction algorithm,
namespace architecture changes, I-01/I-02 repair, geometry quality research, UV/PBR/texture/benchmark,
manual artifact replacement, extra seeds, brute force, retries, historical evidence changes,
protected ref changes, history rewrite, User Delivery/DELIVERED/close-for-delivery/fresh-context proof.

## Known Unknowns / Ready Gate
Actual semantic closure is unknown. Current capability can inspect both stated criteria using existing evidence;
it does not guarantee that generated geometry passes. Historical failure is retained as knowledge, not new Review authority.
SPECIFICATION_READY: true; unresolved_blocking_ambiguities: [].
Readiness reason: Goal, Reference authority, intended use, deliverable, Must-Haves, criteria,
bounds and effect boundary are sufficiently defined by current context.
Technical choices remain within the existing fixed capability; no User intent ambiguity remains.

## Freeze / Stop
This new document and finalized typed projection are frozen before effects.
Specification/Session/Loop/children/authority/capability/namespaces remain immutable for this attempt.
Fail/abort/unresolved/contract defect evidence is preserved without in-place repair or fresh retry.
Acceptance must be produced by existing internal_accept_candidate()/Session gate.
At actual INTERNAL_ACCEPT, stop with delivered=false. No Delivery Package, submission record,
DELIVERED, Session delivery closure or fresh Session will be created.
