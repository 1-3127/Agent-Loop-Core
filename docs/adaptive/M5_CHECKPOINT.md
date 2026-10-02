# M5 checkpoint

- Implemented: Evidence-bound workflow revision and separately inferred restart; current mandatory-criterion acceptance; diagnostic acquisition stays in current Run.
- Module contracts touched: Diagnosis, Production Run, Attempt, Acceptance
- Source/tests/docs changed: src/core/adaptive_loop.py; src/core/frontier.py; tests/test_adaptive_loop.py; tests/test_adaptive_transitions.py; this checkpoint, focused log and validation JSON.
- Focused/related: 39/39 PASS; zero failures/errors/skips. Relevant earlier module tests included.
- Full regression: M0 baseline 277/277; final augmented suite deferred to M7.
- Actual effects: none; SYNTHETIC only. Tripwires: {"network": 0, "production_process": 0, "allowed_local_fixture_process": 1, "repository_write": 0}.
- Artifacts/logs: `M5_FOCUSED.log`, `M5_VALIDATION.json`; temporary fixtures are not actual business artifacts or promotions.
- Git commit/push: normal dedicated checkpoint commit; final immutable SHA and local/tracking/live equality recorded by external checkpoint report after commit.
- Protected validation: baseline historical files and pre-existing branch/tag refs checked after publication; no history rewriting.
- Known limits: No live effects. One local key mismatch was corrected before checkpoint; no semantic inference is fabricated from deterministic transition rules.
- Next: next sequential milestone under adopted Work Specification v1.2. No same-Session human approval gate.
