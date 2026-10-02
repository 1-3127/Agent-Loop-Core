# M3 checkpoint

- Implemented: Frozen Session owns sequential Workflow-bound Runs and local Attempts; reservations/deadline/terminal/collision guards.
- Module contracts touched: Session, Production Run, Attempt, resource envelope
- Source/tests/docs changed: src/core/adaptive_loop.py; tests/test_adaptive_loop.py; this checkpoint, focused log and validation JSON.
- Focused/related: 29/29 PASS; zero failures/errors/skips. Relevant earlier module tests included.
- Full regression: M0 baseline 277/277; final augmented suite deferred to M7.
- Actual effects: none; SYNTHETIC only. Tripwires: {"network": 0, "production_process": 0, "allowed_local_fixture_process": 1, "repository_write": 0}.
- Artifacts/logs: `M3_FOCUSED.log`, `M3_VALIDATION.json`; temporary fixtures are not actual business artifacts or promotions.
- Git commit/push: normal dedicated checkpoint commit; final immutable SHA and local/tracking/live equality recorded by external checkpoint report after commit.
- Protected validation: baseline historical files and pre-existing branch/tag refs checked after publication; no history rewriting.
- Known limits: No recovery or live tool dispatch. Semantic review/acceptance and revision transitions arrive in M4-M5.
- Next: next sequential milestone under adopted Work Specification v1.2. No same-Session human approval gate.
