# Fresh Session Retry — Stone Lantern Work Specification v1

Created independently in this chat, 2026-10-01T15:28:46.254963+09:00.
Semantic status: READY, NEW_WORK; unresolved blocking intent ambiguity: none.
Session: `fsr-session-20261001-152846-ccab2a25`. Logical Loop: `fsr-loop-20261001-152846-ccab2a25`.

## Current Request and authority

USER: 레퍼런스 이미지에 있는 석등을 제작하라. 석등은 중앙의 사각형 구멍을 포함한 실루엣이 명확히 나와야 한다.
The current direct photograph identifies REF, rather than any historical fixed image.
REF canonical FileIdentity authority source:
```json
{"bytes":362412,"identity":"USER_CURRENT_REFERENCE","path":"C:\\Users\\Worker\\AppData\\Local\\Temp\\codex-clipboard-cccea437-5ac5-4e4e-8009-43493507bd03.png","sha256":"9da5ed9e7f3490d058673122a7bd50b46635d4f0b5a36ca3199f0c1636cd17e5"}
```
Original photo SHA-256: `9da5ed9e7f3490d058673122a7bd50b46635d4f0b5a36ca3199f0c1636cd17e5`; bytes: 362412.
CurrentReference will bind this identity to this frozen document and this Session.

## Goal / deliverable / must-haves

Create one recognizable stone-lantern GLB from the current direct photograph.
Planned primary deliverable: one GLB. Supporting evidence: generated views, GLB diagnostic renders and current semantic Review records. This proof stops at INTERNAL_ACCEPT or bounded failure, without Delivery.

- Preserve the broad roof, compact square chamber, shelf and low splayed arched supports in reference proportions.
- Show a clearly identifiable central square opening as actual visible geometry.
- Model the stone lantern alone; exclude the photographed person, foreground post and background scenery.

## Dialogue and interpretation

No further intent question: the object and required aperture are identified by current Request and photo. A roof with low broad eaves and top ornament covers a compact square chamber above a shelf and splayed supports. The foreground vertical post partially occludes it but is a separate non-target object. Complete occluded structure conservatively from visible structure; no invented backside decoration requirement. Internal model parameters and diagnostic cameras follow the fixed capability.

## Acceptance and applicability

| ID | Authority | Blocking | Supported stage | Observable criterion |
|---|---|---|---|---|
| LANTERN_VIEW_IDENTITY | REF | YES | multiview | Generated right/left/back views depict the same stone lantern as the supplied front photograph, preserving the wide roof, compact chamber and low splayed supports in consistent proportions. Non-target people, foreground posts and scenery must not be fused into or replace the lantern. |
| LANTERN_GLB_SILHOUETTE | REF | YES | geometry | Current GLB diagnostic views clearly identify the reference stone lantern: broad low roof with small top ornament, square chamber, supporting shelf and low splayed arched legs. Major part loss/collapse or attached foreground post/person fails. |
| LANTERN_SQUARE_APERTURE | USER | YES | geometry | Current GLB diagnostic views clearly show a square opening in the central chamber, bounded by a frame. A dark painted square or sealed surface is insufficient. Obscured or ambiguous evidence is UNCERTAIN and cannot authorize PASS. |

Each assigned criterion must have exactly one current stage observation with [ID@authority] SATISFIED/UNMET/UNCERTAIN and evidence. PASS requires applicable mandatory criteria SATISFIED. REVISE requires an authorized UNMET blocker and existing stage action. UNCERTAIN cannot become SATISFIED by assumption. Multiview does not validate final geometry. Image diagnostics do not prove watertight topology, physical dimensions or engine performance.

## Bounds and non-goals

Capability `fixed_four_view_glb_seed_only`; Worker6 / Reviewer4 / Renderer2 / revision1 / automatic retry0. Only existing bounded seed correction is allowed. Non-goals: source/test/contract changes, cropping or editing the current image, manual mesh replacement, new validators/stages, budget expansion, brute force, I-01/I-02 cleanup, previous Session reopen and Delivery. Exact surface stains, measured size, texture reconstruction and hidden ornaments are not blocking criteria.

## Isolation and freeze

This document and finalized projection were authored from current Request/photo and inspected durable contracts, not copied from the historical candidate or penguin Specification. Similar criterion categories in the candidate are historical comparison only. Prior verdicts/artifacts/correction state and reasoning are not execution inputs. The chat is the projectless chat containing the initial attachments and the user's explicit retry request; no earlier closed Session was reopened. No external host context-reset mechanism is claimed.

Freeze binds these document bytes and finalized fields before parent preparation. Operational execution readiness remains separately gated by regression, runtime, binding and I-03 preflight. Any required source/contract fix ends this attempt before further effects.
