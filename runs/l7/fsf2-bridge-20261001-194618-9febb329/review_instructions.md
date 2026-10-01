Bound Scenario A review. The criteria below are the only user quality acceptance authority.
Inspect the exact attached evidence. Identity, schema, role order, camera configuration and invocation hashes are technical contracts, not additional quality criteria.
Do not invent goals or quality blockers; do not favor a verdict. Return exact Result0.3 JSON.
Every selected criterion needs exactly one observations entry formatted [criterion_id@authority_ref] SATISFIED: evidence, UNMET: evidence, or UNCERTAIN: evidence.
blocking_issues entries use [criterion_id@authority_ref] UNMET: evidence and may only name selected blocking_when_unmet=true criteria. Nonblocking UNMET stays an observation.
PASS requires every blocking criterion SATISFIED, no blocking_issues, NONE/null. REVISE requires valid blockers and REGENERATE_VIEW with right/left/back or REGENERATE_GEOMETRY with geometry. HUMAN_REQUIRED uses HUMAN_REQUIRED/null; it is not by itself Specification ambiguity. Correction is bounded seed-only, no quality guarantee.
Criteria and declared authority sources:
{
  "authorities": {
    "reference": "{\"bytes\":362412,\"identity\":\"CURRENT_DIRECT_USER_REFERENCE\",\"path\":\"D:\\\\VSCODE-WorkSpace\\\\Others\\\\Agent-Loop-Core\\\\docs\\\\session\\\\fresh-session-refresh-proof-final-2\\\\CURRENT_REFERENCE.png\",\"sha256\":\"9da5ed9e7f3490d058673122a7bd50b46635d4f0b5a36ca3199f0c1636cd17e5\"}",
    "request": "{\"bytes\":150,\"identity\":\"CURRENT_DIRECT_USER_REQUEST\",\"path\":\"D:\\\\VSCODE-WorkSpace\\\\Others\\\\Agent-Loop-Core\\\\docs\\\\session\\\\fresh-session-refresh-proof-final-2\\\\CURRENT_REQUEST.md\",\"sha256\":\"1d8778a4439361c1882e78b40b76f83d8423804ff3332852eae108b03439b829\"}"
  },
  "criteria": [
    {
      "authority_ref": "reference",
      "blocking_when_unmet": true,
      "criterion_id": "LANTERN_FORM",
      "description": "Recognizable stone-lantern silhouette: broad low eaved roof, central chamber, and raised leg-like support, consistent with the current reference. Exclude the foreground post, person, and garden scene."
    },
    {
      "authority_ref": "request",
      "blocking_when_unmet": true,
      "criterion_id": "APERTURE_GEOMETRY",
      "description": "Current 3D diagnostic renders show the central square chamber aperture as a real recessed/open cavity with spatial depth and empty volume, not merely a flat dark square texture. If current renders cannot establish this, do not PASS."
    },
    {
      "authority_ref": "request",
      "blocking_when_unmet": true,
      "criterion_id": "GLB_READABILITY",
      "description": "The current GLB is a coherent readable lantern in diagnostic views, preserving the reference silhouette without gross merged clutter or broken essential components."
    }
  ]
}
