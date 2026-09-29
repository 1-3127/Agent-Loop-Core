# Source selection — M0

Source: `D:\VSCODE-WorkSpace\Others\Agent-Loop` at `7e1572a7e35866519b75b767398288396a27f9b0`. A `COPY` means the file supports an eventual C1–C5 path; it does not mean that path is currently executable end to end. SHA-256 identities are in `PROVENANCE.md`. Existing ComfyUI workflows remain in their own workspace.

| Source | Classification | Destination | C1–C5 reason |
|---|---|---|---|
| `result_review_adapter.py`, `result_review_schema.json` | COPY | `src/core/`, repository root | Generic artifact identity and structured semantic Review boundary, C2. |
| `codex_to_comfy.py` | COPY | `src/scenario_a/` | Real local worker execution and durable report, C1/C3. |
| `reviewer_adapter.py`, `reviewer_result_schema.json` | COPY | `src/scenario_a/`, repository root | Existing image Review dependency of result adapter/controller, C2. |
| `pipeline_a_controller.py`, `validate_review.py`, `validate_adaptive_decision.py` | COPY | `src/scenario_a/` | Current bounded Scenario A decision and validator dependencies, C3/C4. |
| `dispatch_controller.py`, `dispatch_geometry.py` | COPY | `src/scenario_a/` | Existing Decision-to-Worker invocation, receipts and duplicate guard, C1/C3. |
| `persist_geometry_state.py`, `scenario_a_result_review.py`, `scenario_a_coverage.py` | COPY | `src/scenario_a/` | Durable bounded state, provenance and view coverage dependencies, C2–C4. |
| `ac6_f2_image_transition.py`, `ac6_f2_view_plan.py`, `ac6_f2_review_route.py` | COPY | `src/scenario_a/` | Candidate real image execution-to-Review-to-next-work path, C1–C3. |
| `ac6_f2_geometry.py`, `ac6_f2_geometry_review.py`, `ac6_f2_refinement.py`, `ac6_f2_refinement_review.py` | COPY | `src/scenario_a/` | Candidate geometry execution and revision path, C1–C3. |
| `tests/test_execution.py` | COPY | `tests/` | Small no-network smoke of worker execution contract. |
| `ac6_f1_bootstrap.py`, `ac6_resume_runner.py`, `ac6_terminal_tail.py`, `tests/test_ac6_f1_bootstrap.py`, `tests/test_ac6_resume_runner.py`, `tests/test_ac6_terminal_tail.py` | REFERENCE_ONLY | — | Fixed historical run/state namespaces; the runner does not run the fresh first execution. Consult before C1/C4 proof, but do not copy its old terminal semantics as Core. |
| `p2_geometry_review.py`, `review_to_controller.py`, `tests/test_review_to_controller.py`, `tests/test_p2_geometry_review.py`, `tests/test_result_review_boundary.py`, other focused `tests/test_*.py` | REFERENCE_ONLY | — | Historical contracts and regression cases require source fixtures and artifact paths; select later for actual proof regression. |
| `controller_states/`, `controller_inputs/`, `decisions/`, `reviews/`, `reviewer_requests/`, `reviewer_results/`, `invocation_reports/`, `dispatch_requests/`, `dispatch_receipts/`, `runs/`, `plans/`, `coverage_configs/`, `coverage_states/`, `bootstrap_requests/`, `evidence_requests/`, `evidence_manifests/`, `bridge_requests/`, `requests/`, `state_requests/` | REFERENCE_ONLY | — | Historical evidence stays in research repo. New proof needs fresh identities; wholesale copying risks replaying old runs. |
| `README.md`, `work_log.md`, `AGENTS/`, `ac6_*_audit.md`, `stabilization_*.md`, `decisions/*.json` | REFERENCE_ONLY | — | Research rationale and evidence; Direction Gate governs new scope. |
| `ac6_f2b_resume.py` (untracked), `ac6_f2b_resume_audit.md` | HARDENING_BACKLOG | — | Comprehensive resume and crash recovery are beyond Core v1 safety floor. Untracked source is excluded. |
| `render_p1_geometry_evidence.py`, `render_fresh_geometry_evidence.py`, `validate_blender_handoff.py`, `m7c_blender_roundtrip.py`, related media and Blender artifacts | EXCLUDE | — | Evidence rendering and Blender handoff are outside the minimum C1–C5 proof path. |
| `D:\VSCODE-WorkSpace\Others\Agent-Comfy-Model` Core | OLD_CORE_REFERENCE | — | Hash, atomic persistence, run identity and adapter boundary are conceptual references; no wholesale migration. |

## Known coupling

The copied controller and F2 route contain Scenario A actions (`ADD_VIEW`, roles, `GEOMETRY_REVIEW`, refinement) and fixed historical namespaces. `src/core/result_review_adapter.py` still imports `reviewer_adapter.auth_mode`. Thus the folders mark the current source boundary, while an actual Core loop and replaceable WorkerPort remain future proof work. This is technical debt, not an M0 refactor authorization. The source `ac6_resume_runner.py` is insufficient for a new actual loop: its fresh `EXECUTION` branch deliberately blocks `--run`, and its terminal path is bound to a historical state. The old `ACCEPTED`/`HUMAN_REQUIRED` semantics also do not establish Direction Gate v1 `DELIVERED`/`FAILED`/`ABORT`.

Only the copied executor test uses a temporary synthetic workflow. Real workflows were found under `D:\VSCODE-WorkSpace\Comfy-UI\workflows\02_Image_to_Multiview` and `03_Multiview_to_3D`, but M0 performs no production generation or semantic Review.

## Post-COMPLETE Refactor Update — M6

The M0 table above remains the selection record at M0, not the current active graph. At baseline `3129cf50e5c602f3e9e5bd0194cd46d42b9ddcee`, C1–C5 active source is `src/core/{worker_port,result_review_adapter}.py` and `src/scenario_a/{c1_delegate,c2_review,c3_review,c3_revision,c4_bounded,c5_worker_swap,codex_to_comfy,comfy_worker_adapter}.py`. M6 added `src/core/reviewer_auth.py` by extracting the unchanged auth-mode probe from `reviewer_adapter.py`, plus package initializers. The test-only C5 Worker remains under `tests/fixtures/`.

The copied `ac6_f2_*` modules, previous controller/geometry/state/coverage/validation route, `reviewer_adapter.py`, and its unused `reviewer_result_schema.json` were removed from the Compact repo: no C1–C5 active entry point or test depends on them. Their M0 source bytes and provenance remain recorded below and in the read-only Research repository. Current evidence files and their historical source references were not edited.
