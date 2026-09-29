# M6 compact refactor report

- Baseline: `3129cf50e5c602f3e9e5bd0194cd46d42b9ddcee`
- Purpose: preserve verified C1–C5 semantics while making the Core/Scenario A dependency direction and the active code path explicit.
- Before: Core `result_review_adapter.py` imported Scenario A `reviewer_adapter.auth_mode`; active imports depended on separate `src/core` and `src/scenario_a` search paths. M0 candidate controller/F2 modules remained beside the active implementation.
- After: Core imports only standard library and Core; Scenario A imports Core. `src` is the single application import root. Active CLI modules run with `python -m scenario_a.<module>`.

## Active and retained

- Core: `worker_port.py`, `result_review_adapter.py`, extracted `reviewer_auth.py`.
- Scenario A: `c1_delegate.py`, `c2_review.py`, `c3_review.py`, `c3_revision.py`, `c4_bounded.py`, `c5_worker_swap.py`, `codex_to_comfy.py`, `comfy_worker_adapter.py`.
- Test-only: `tests/fixtures/deterministic_worker.py`, `tests/fixtures/c5_input.txt`; the deterministic Worker was not promoted to a production backend.
- Support: `result_review_schema.json` and committed review instructions are retained for the active Reviewer boundary. Historical evidence remains in its original paths.

## Removed copied candidates

`ac6_f2_geometry.py`, `ac6_f2_geometry_review.py`, `ac6_f2_image_transition.py`, `ac6_f2_refinement.py`, `ac6_f2_refinement_review.py`, `ac6_f2_review_route.py`, `ac6_f2_view_plan.py`, `dispatch_controller.py`, `dispatch_geometry.py`, `persist_geometry_state.py`, `pipeline_a_controller.py`, `reviewer_adapter.py`, `scenario_a_coverage.py`, `scenario_a_result_review.py`, `validate_adaptive_decision.py`, `validate_review.py`, and `reviewer_result_schema.json`.

These form a separate historical candidate dependency cluster. No active C1–C5 module or current test imports it after the auth extraction. Each source file remains in the committed Research repository; the M0 selection and source hashes remain in `SOURCE_MANIFEST.md` and `PROVENANCE.md`.

## Verification and limits

- Protected evidence: `work_orders/`, `plans/`, `runs/`, `reviewer_requests/`, `reviewer_results/`, `invocation_reports/`, `usage/` — 49 baseline Git files; modified count: **0**.
- `python -m unittest discover -s tests -p 'test_*.py'`: **20/20 PASS**.
- Core-only import, dependency direction, and single-`src` import tests: **PASS**. Active CLI `--help` smoke: **PASS**.
- ComfyUI production calls: **0**. Frontier semantic Reviewer calls: **0**. New production artifacts: **0**.
- Behavior changed: **NO**, within local/unit and import verification. Historical evidence was not rewritten.
- Actual post-refactor C1–C5 regression: **NOT YET RUN**. Core v1 frozen: **NO**.
- Deferred: actual C1–C5 regression, Core freeze decision, hypothesis benchmark, and F2B comprehensive resume. C1–C4 were not migrated wholesale to WorkerPort.
