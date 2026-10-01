Bound Scenario A review. The criteria below are the only user quality acceptance authority.
Inspect the exact attached evidence. Identity, schema, role order, camera configuration and invocation hashes are technical contracts, not additional quality criteria.
Do not invent goals or quality blockers; do not favor a verdict. Return exact Result0.3 JSON.
Every selected criterion needs exactly one observations entry formatted [criterion_id@authority_ref] SATISFIED: evidence, UNMET: evidence, or UNCERTAIN: evidence.
blocking_issues entries use [criterion_id@authority_ref] UNMET: evidence and may only name selected blocking_when_unmet=true criteria. Nonblocking UNMET stays an observation.
PASS requires every blocking criterion SATISFIED, no blocking_issues, NONE/null. REVISE requires valid blockers and MULTIVIEW_REVISE with right/left/back/null. HUMAN_REQUIRED uses HUMAN_REQUIRED/null; it is not by itself Specification ambiguity. Correction is bounded seed-only, no quality guarantee.
Criteria and declared authority sources:
{
  "authorities": {
    "REF": "{\"bytes\":362412,\"identity\":\"USER_CURRENT_REFERENCE\",\"path\":\"C:\\\\Users\\\\Worker\\\\AppData\\\\Local\\\\Temp\\\\codex-clipboard-56c3ee39-4031-47aa-a5ef-ebede4edfb9c.png\",\"sha256\":\"9da5ed9e7f3490d058673122a7bd50b46635d4f0b5a36ca3199f0c1636cd17e5\"}",
    "USER": "Current chat request: 레퍼런스 이미지에 있는 석등을 제작하라.\n석등은 중앙의 사각형 구멍을 포함한 실루엣이 명확히 나와야 한다."
  },
  "criteria": [
    {
      "authority_ref": "REF",
      "blocking_when_unmet": true,
      "criterion_id": "MV_SILHOUETTE",
      "description": "The current front and generated views depict a coherent recognizable stone lantern with the reference major silhouette: wide low roof and top finial, square chamber, horizontal platform, and arched pedestal or legs. Use visible reference features; plausibly infer occluded sides. Scene people, pole, trees and background are not parts of the lantern."
    },
    {
      "authority_ref": "USER",
      "blocking_when_unmet": true,
      "criterion_id": "MV_OPENING",
      "description": "The central square chamber opening is visibly represented in the front and observable generated orientations. This image-stage appearance alone does not establish a geometric hole; do not demand topology from images."
    }
  ]
}
