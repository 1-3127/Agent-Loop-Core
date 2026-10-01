Bound Scenario A review. The criteria below are the only user quality acceptance authority.
Inspect the exact attached evidence. Identity, schema, role order, camera configuration and invocation hashes are technical contracts, not additional quality criteria.
Do not invent goals or quality blockers; do not favor a verdict. Return exact Result0.3 JSON.
Every selected criterion needs exactly one observations entry formatted [criterion_id@authority_ref] SATISFIED: evidence, UNMET: evidence, or UNCERTAIN: evidence.
blocking_issues entries use [criterion_id@authority_ref] UNMET: evidence and may only name selected blocking_when_unmet=true criteria. Nonblocking UNMET stays an observation.
PASS requires every blocking criterion SATISFIED, no blocking_issues, NONE/null. REVISE requires valid blockers and REGENERATE_VIEW with right/left/back or REGENERATE_GEOMETRY with geometry. HUMAN_REQUIRED uses HUMAN_REQUIRED/null; it is not by itself Specification ambiguity. Correction is bounded seed-only, no quality guarantee.
Criteria and declared authority sources:
{
  "authorities": {
    "REFERENCE": "{\"bytes\":362412,\"identity\":\"USER_DIRECT_CURRENT_REFERENCE\",\"path\":\"C:\\\\Users\\\\Worker\\\\AppData\\\\Local\\\\Temp\\\\codex-clipboard-08627ccb-773a-4ec0-9b6e-3dd1bcde0524.png\",\"sha256\":\"9da5ed9e7f3490d058673122a7bd50b46635d4f0b5a36ca3199f0c1636cd17e5\"}",
    "REQUEST": "Current direct user request: 레퍼런스 이미지에 있는 석등을 제작하라. 석등은 중앙의 사각형 구멍을 포함한 실루엣이 명확히 나와야 한다."
  },
  "criteria": [
    {
      "authority_ref": "REFERENCE",
      "blocking_when_unmet": true,
      "criterion_id": "FORM_SILHOUETTE",
      "description": "The target is recognizable as the reference stone lantern: a wide, low overhanging roof with a small top cap, a roughly square chamber, a projecting horizontal platform, and substantial arched supports or legs. Judge observable form in the selected stage. Complete occluded sides reasonably; exclude the person, foreground pole, vegetation, and scene surfaces from the lantern."
    },
    {
      "authority_ref": "REQUEST",
      "blocking_when_unmet": true,
      "criterion_id": "GEO_APERTURE",
      "description": "The current 3D chamber includes an actual square or approximately rectangular aperture or open cavity below the roof. Current geometry diagnostics must support spatial depth, a rim and inner surfaces, or visible empty space/background. A flat dark square, texture mark, shallow decorative panel, or base arch alone does not satisfy this requirement. Preserve uncertainty when diagnostics cannot establish it."
    },
    {
      "authority_ref": "REQUEST",
      "blocking_when_unmet": true,
      "criterion_id": "GEO_READABILITY",
      "description": "The current GLB and its diagnostic renders are readable as a coherent lantern with separable roof, chamber, platform, and raised support. The user-required silhouette and central chamber opening are assessable from the current geometry evidence; an undifferentiated solid or featureless surface is insufficient."
    }
  ]
}
