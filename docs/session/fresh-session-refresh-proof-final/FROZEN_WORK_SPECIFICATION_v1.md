# Final fresh-session stone-lantern Work Specification v1

FROZEN independently for this new request.

Session: fsf-session-20261001-165330-6b5962c4
Logical Loop: fsf-loop-20261001-165330-6b5962c4

## Request and goal

레퍼런스 이미지에 있는 석등을 제작하라.
석등은 중앙의 사각형 구멍을 포함한 실루엣이 명확히 나와야 한다.

Create a 3D stone lantern from the directly attached current reference with a clear silhouette and actual central square chamber opening.

## Deliverable and scope

A current generated GLB stone lantern plus the canonical multiview and Blender diagnostic evidence. Stop at production INTERNAL_ACCEPT. No Delivery or Session closure.

The lantern includes its broad low roof, finial, chamber, platform and arched base. The foreground pole, person and background scenery are occluders or context, not model parts. Hidden sides may be completed reasonably. No exact scale, PBR, texture fidelity, UV/topology optimization, rigging, fine artistic finish or manual replacement is requested.

## Must-Haves

Preserve the visible reference lantern major silhouette.
Represent the central square chamber opening as an actual geometric aperture.

## Direct authority

USER: Current chat request: 레퍼런스 이미지에 있는 석등을 제작하라.
석등은 중앙의 사각형 구멍을 포함한 실루엣이 명확히 나와야 한다.

REF: {"bytes":362412,"identity":"USER_CURRENT_REFERENCE","path":"C:\\Users\\Worker\\AppData\\Local\\Temp\\codex-clipboard-56c3ee39-4031-47aa-a5ef-ebede4edfb9c.png","sha256":"9da5ed9e7f3490d058673122a7bd50b46635d4f0b5a36ca3199f0c1636cd17e5"}

The original attachment bytes remain authority. The saved original is archival evidence only. The 768-square derivative is execution input only, never replacement user authority.

## Criteria and applicability

{
  "criteria": [
    {
      "criterion_id": "MV_SILHOUETTE",
      "authority_ref": "REF",
      "blocking_when_unmet": true,
      "description": "The current front and generated views depict a coherent recognizable stone lantern with the reference major silhouette: wide low roof and top finial, square chamber, horizontal platform, and arched pedestal or legs. Use visible reference features; plausibly infer occluded sides. Scene people, pole, trees and background are not parts of the lantern."
    },
    {
      "criterion_id": "MV_OPENING",
      "authority_ref": "USER",
      "blocking_when_unmet": true,
      "description": "The central square chamber opening is visibly represented in the front and observable generated orientations. This image-stage appearance alone does not establish a geometric hole; do not demand topology from images."
    },
    {
      "criterion_id": "GEO_SILHOUETTE",
      "authority_ref": "REF",
      "blocking_when_unmet": true,
      "description": "The current 3D diagnostic renders show the stone lantern major silhouette clearly: broad low roof and finial, square chamber, horizontal platform, and arched pedestal or legs. Exact hidden details and scene occluders are not required."
    },
    {
      "criterion_id": "GEO_OPENING",
      "authority_ref": "USER",
      "blocking_when_unmet": true,
      "description": "The 3D lantern has a real central square or rectangular opening in the chamber under the roof, observably supported by the current geometry diagnostics through its rim, depth or visible interior/background. A flat dark square texture, painted marking or superficial panel is insufficient. Evaluate only current diagnostic evidence; uncertainty must remain uncertainty."
    }
  ],
  "stage_criteria": {
    "multiview": [
      "MV_SILHOUETTE",
      "MV_OPENING"
    ],
    "geometry": [
      "GEO_SILHOUETTE",
      "GEO_OPENING"
    ]
  }
}

C-01: each stage evaluates only its own observable criteria. All four criteria are mandatory and blocking when unmet. Multiview appearance does not establish the actual geometry aperture. Geometry review uses the current canonical Blender geometry diagnostics.

PASS: every selected blocking criterion SATISFIED with current observations and no blocker. REVISE: selected mandatory criterion observably UNMET; only fixed seed correction within existing caps. UNCERTAIN cannot become SATISFIED automatically; preserve HUMAN_REQUIRED. No additional aesthetic or unrequested quality blocker.

## Execution constraints

Fixed capability fixed_four_view_glb_seed_only; budgets {"worker": 6, "reviewer": 4, "renderer": 2, "revision": 1}. No enlargement, source/test/contract changes, brute-force retries, history reuse, manual artifact substitution or same-Session rerun. I-03 checks all fresh namespaces before any staging or generation. Smaller input receives centered padding only; no upscale/crop/stretch. Canonical entry stages normalized bytes in its fresh attempt before Worker dispatch. CP1 preview is independently recorded execution-readiness evidence, not an attempt namespace pre-created outside the entry.

## Stop conditions

Stop at INTERNAL_ACCEPT, an actual bounded runtime/semantic failure, or a newly discovered source/contract defect. Preserve raw verdicts and evidence. Delivery remains zero.
