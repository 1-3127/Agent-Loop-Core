# M4 checkpoint

- Implemented: Immutable stage artifacts and independent criterion-bound reviews with invocation lineage; semantic REVISE remains nonterminal.
- Module contracts touched: Artifact Store, Reviewer, Frontier diagnostic input
- Source/tests/docs changed: src/core/adaptive_artifacts.py; src/core/artifact_review.py; src/core/frontier.py; tests/test_artifact_review.py; this checkpoint, focused log and validation JSON.
- Focused/related: 34/34 PASS; zero failures/errors/skips. Relevant earlier module tests included.
- Full regression: M0 baseline 277/277; final augmented suite deferred to M7.
- Actual effects: none; SYNTHETIC only. Tripwires: {"network": 0, "production_process": 0, "allowed_local_fixture_process": 1, "repository_write": 0}.
- Artifacts/logs: `M4_FOCUSED.log`, `M4_VALIDATION.json`; temporary fixtures are not actual business artifacts or promotions.
- Git commit/push: normal dedicated checkpoint commit; final immutable SHA and local/tracking/live equality recorded by external checkpoint report after commit.
- Protected validation: baseline historical files and pre-existing branch/tag refs checked after publication; no history rewriting.
- Known limits: Review content is supplied by the injected model boundary; authentic semantic proof is deferred to M8. Cross-Run reuse requires a new explicit producer record; no silent adoption.
- Next: next sequential milestone under adopted Work Specification v1.2. No same-Session human approval gate.
