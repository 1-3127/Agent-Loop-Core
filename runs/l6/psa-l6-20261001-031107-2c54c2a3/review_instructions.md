Bound Scenario A review. The criteria below are the only user quality acceptance authority.
Inspect the exact attached evidence. Identity, schema, role order, camera configuration and invocation hashes are technical contracts, not additional quality criteria.
Do not invent goals or quality blockers; do not favor a verdict. Return exact Result0.3 JSON.
Every selected criterion needs exactly one observations entry formatted [criterion_id@authority_ref] SATISFIED: evidence, UNMET: evidence, or UNCERTAIN: evidence.
blocking_issues entries use [criterion_id@authority_ref] UNMET: evidence and may only name selected blocking_when_unmet=true criteria. Nonblocking UNMET stays an observation.
PASS requires every blocking criterion SATISFIED, no blocking_issues, NONE/null. REVISE requires valid blockers and MULTIVIEW_REVISE with right/left/back/null. HUMAN_REQUIRED uses HUMAN_REQUIRED/null; it is not by itself Specification ambiguity. Correction is bounded seed-only, no quality guarantee.
Criteria and declared authority sources:
{
  "authorities": {
    "CANONICAL_SOURCE": "D:\\VSCODE-WorkSpace\\Comfy-UI\\work\\input\\hunyuan-official-demo-padded.png#sha256=8a6dd9ca3f8984b31c1243e7698cd5030b423464d80e0ad763609148e0ff4f51",
    "ORIGINAL_REQUEST_REFERENCE": "D:\\VSCODE-WorkSpace\\Others\\Agent-Loop-Core\\runs\\session\\psa-session-20261001-031107-2c54c2a3\\original_request_reference.md#sha256=1bf8a65e31b67f72f4511783cdad97906e695af20ea2602731eb5b8e8960dfb6",
    "USER_CURRENT_REQUEST": "D:\\VSCODE-WorkSpace\\Others\\Agent-Loop-Core\\runs\\session\\psa-session-20261001-031107-2c54c2a3\\user_request.md#sha256=37bda4fe4f126dd56af0afed412c30411cf77e9169e68b7e79134e2c8a7cfa49"
  },
  "criteria": [
    {
      "authority_ref": "USER_CURRENT_REQUEST",
      "blocking_when_unmet": true,
      "criterion_id": "AC-MULTIVIEW-COHERENCE",
      "description": "Generated multiview images must depict the same canonical source object, preserve its recognizable major silhouette and structural parts, and contain no severe crop, missing/detached major part, or cross-view identity contradiction."
    }
  ]
}
