# Fresh Session Final-3 — Stone Lantern Work Specification v1

레퍼런스 이미지에 있는 석등을 제작하라. 석등은 중앙의 사각형 구멍을 포함한 실루엣이 명확히 나와야 한다.

Goal: Produce a current 3D stone lantern matching the attached reference major silhouette and containing a real central square chamber opening.

Session: fsf3-session-20261001-223651-6baf886b
Loop: fsf3-loop-20261001-223651-6baf886b

Target/deliverable: one generated current stone-lantern GLB with canonical multiview, Blender diagnostics, and current semantic Reviews. This proof stops at INTERNAL_ACCEPT; Delivery and Session closure are outside scope.

Must-Haves:
Retain the roof, chamber, platform, and arched supports visible in the reference.
Make the central square chamber opening an actual aperture or cavity in the geometry.

Authority REQUEST: Current direct user request: 레퍼런스 이미지에 있는 석등을 제작하라. 석등은 중앙의 사각형 구멍을 포함한 실루엣이 명확히 나와야 한다.
Authority REFERENCE: {"bytes":362412,"identity":"USER_DIRECT_CURRENT_REFERENCE","path":"C:\\Users\\Worker\\AppData\\Local\\Temp\\codex-clipboard-08627ccb-773a-4ec0-9b6e-3dd1bcde0524.png","sha256":"9da5ed9e7f3490d058673122a7bd50b46635d4f0b5a36ca3199f0c1636cd17e5"}

The direct attachment bytes are authoritative. The archival original and centered 768-square execution derivative have separate roles. No historical reference, specification, artifact, Review, binding, or active attempt is substituted.

The broad roof and small top cap, framed chamber, projecting platform, and arched supports define the major silhouette. The foreground pole/person and garden are scene occluders; hidden sides can be inferred reasonably. No scale, fine texture fidelity, UV optimization, rigging, artistic polish, or manual mesh editing is required.

Acceptance criteria (all mandatory/blocking) and explicit applicability:
{
  "criteria": [
    {
      "criterion_id": "FORM_SILHOUETTE",
      "authority_ref": "REFERENCE",
      "blocking_when_unmet": true,
      "description": "The target is recognizable as the reference stone lantern: a wide, low overhanging roof with a small top cap, a roughly square chamber, a projecting horizontal platform, and substantial arched supports or legs. Judge observable form in the selected stage. Complete occluded sides reasonably; exclude the person, foreground pole, vegetation, and scene surfaces from the lantern."
    },
    {
      "criterion_id": "MV_APERTURE",
      "authority_ref": "REQUEST",
      "blocking_when_unmet": true,
      "description": "In the current multiview images, the chamber below the roof has a clearly framed central square or approximately rectangular opening where observable. This criterion concerns visual appearance only; a visible dark opening in an image does not establish an actual geometric cavity."
    },
    {
      "criterion_id": "MV_COHERENCE",
      "authority_ref": "REFERENCE",
      "blocking_when_unmet": true,
      "description": "The current front, right, left, and back remain plausible views of one stone lantern, with a compatible roof, chamber, platform, and support arrangement. Occlusion and inferred hidden surfaces may vary, but the target identity and major proportions remain coherent."
    },
    {
      "criterion_id": "GEO_APERTURE",
      "authority_ref": "REQUEST",
      "blocking_when_unmet": true,
      "description": "The current 3D chamber includes an actual square or approximately rectangular aperture or open cavity below the roof. Current geometry diagnostics must support spatial depth, a rim and inner surfaces, or visible empty space/background. A flat dark square, texture mark, shallow decorative panel, or base arch alone does not satisfy this requirement. Preserve uncertainty when diagnostics cannot establish it."
    },
    {
      "criterion_id": "GEO_READABILITY",
      "authority_ref": "REQUEST",
      "blocking_when_unmet": true,
      "description": "The current GLB and its diagnostic renders are readable as a coherent lantern with separable roof, chamber, platform, and raised support. The user-required silhouette and central chamber opening are assessable from the current geometry evidence; an undifferentiated solid or featureless surface is insufficient."
    }
  ],
  "stage_criteria": {
    "multiview": [
      "FORM_SILHOUETTE",
      "MV_APERTURE",
      "MV_COHERENCE"
    ],
    "geometry": [
      "FORM_SILHOUETTE",
      "GEO_APERTURE",
      "GEO_READABILITY"
    ]
  }
}

C-01: FORM_SILHOUETTE must be satisfied independently in both assigned stages. Image aperture appearance is separate from actual cavity evidence. PASS requires each selected mandatory criterion SATISFIED on current evidence; REVISE identifies an observed unmet mandatory criterion. Do not force a verdict or treat uncertainty as PASS. Supported suggested_action and existing correction budgets govern correction.

Execution policy: fixed_four_view_glb_seed_only; caps {"worker": 6, "reviewer": 4, "renderer": 2, "revision": 1}. One fresh canonical run_session entry, at most one reserved canonical correction. No budget extension, hidden retry, brute force, failed Session resume, source/test/contract changes, or manual artifact replacement. I-03 checks all three repository child and seven external namespaces before first effects. Centered padding only; no upscale/crop/stretch.

Stop: actual INTERNAL_ACCEPT, actual runtime failure, contract defect, or exhausted semantic correction. A normal REVISE after exhausted correction is SEMANTIC_CLOSURE_FAILED. Preserve all evidence. No Delivery, record_submission, or Session closure.
