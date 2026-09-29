# Provenance — M0

- Created: 2026-09-30 (Asia/Seoul)
- Source repository: `D:\VSCODE-WorkSpace\Others\Agent-Loop`
- Source HEAD: `7e1572a7e35866519b75b767398288396a27f9b0`
- Source branch: `main`
- Source `origin/main`: `7e1572a7e35866519b75b767398288396a27f9b0`
- Source working tree: dirty; sole untracked file `ac6_f2b_resume.py` (excluded). No tracked modification.
- Source was read only throughout M0. All copied bytes came from committed HEAD files.
- Historical reference: `D:\VSCODE-WorkSpace\Others\Agent-Comfy-Model`; no code copied.
- F2B comprehensive resume excluded as post-Core reliability research.
- Selection authority: [SOURCE_MANIFEST.md](SOURCE_MANIFEST.md). The Agent-Loop Direction Gate v1 governs project direction.

| Committed source path | M0 destination | Source SHA-256 |
|---|---|---|
| `result_review_adapter.py` | `src/core/result_review_adapter.py` | `7bdc5a3fa8dad662f72f96f6ca434dded4a280b1162a94b56d25e7359499796c` |
| `result_review_schema.json` | `result_review_schema.json` | `7bd920455bd10959180aa9d25c848ceba2c779ae42ea2b1d7385112255dbc084` |
| `reviewer_result_schema.json` | `reviewer_result_schema.json` | `4f4408b71249133d2aa6e8be3d8e96cd5fb26d5863faa05624d76ffc1543b71d` |
| `codex_to_comfy.py` | `src/scenario_a/codex_to_comfy.py` | `ce401060a36d940fc339401239706a16a9624f2dd7028cb7b63e4bb462af10c1` |
| `dispatch_controller.py` | `src/scenario_a/dispatch_controller.py` | `465120f06da780fcdb6757286a7f5158645b8c3c4f1f7d211648a76ae1af1c73` |
| `dispatch_geometry.py` | `src/scenario_a/dispatch_geometry.py` | `a999b4274cf2e71554bfdd747bfab4a918c235e2f55e645e51d263230c9b548e` |
| `persist_geometry_state.py` | `src/scenario_a/persist_geometry_state.py` | `6b8d7723ddbd747d00cc144a7a38ac941a522a074aa6e933e9fe33f057efa078` |
| `pipeline_a_controller.py` | `src/scenario_a/pipeline_a_controller.py` | `8b972a4855318fab4a187019e8791aa20e602758c6af82bcab4420be36edb19f` |
| `reviewer_adapter.py` | `src/scenario_a/reviewer_adapter.py` | `f7aa33df175bc4d5bb5ffc4a127df35ab40a8900dffc5ef34147333c5c48bb4b` |
| `scenario_a_result_review.py` | `src/scenario_a/scenario_a_result_review.py` | `35b0fd7772a3604fff70304b9325042cbfeffc423842c146b9d776c8a02f6f2b` |
| `scenario_a_coverage.py` | `src/scenario_a/scenario_a_coverage.py` | `f86dd74bf25e758717d13bdac6efabc2cfacd3b15d0f4b6bb42cdd8cc16cc487` |
| `validate_review.py` | `src/scenario_a/validate_review.py` | `39ea0235de291743e2ddde5951c0a15997aeff42f22636c28c208112c6eab2ab` |
| `validate_adaptive_decision.py` | `src/scenario_a/validate_adaptive_decision.py` | `0d95bc3b6929166ccc0ad809044ccd1d20f46813bfeb6642c6c3b6ec87e09000` |
| `ac6_f2_image_transition.py` | `src/scenario_a/ac6_f2_image_transition.py` | `8b233ae7f75f215894b594660b6469fd4f8e2e004eacdbc0b26d1fc521aa8738` |
| `ac6_f2_view_plan.py` | `src/scenario_a/ac6_f2_view_plan.py` | `1ec5d4e68a9465976fe430ca9cee1ebe472da8b7357c43796222256a3cdfff2b` |
| `ac6_f2_review_route.py` | `src/scenario_a/ac6_f2_review_route.py` | `c19142fa18004ce9827e2d92563ec6dd5d5575a01d3e70f26719374ae4d5b714` |
| `ac6_f2_geometry.py` | `src/scenario_a/ac6_f2_geometry.py` | `bd144fcbd6ce40c26d98ee66a0b59b0f58dcc420f202ea18b8bf159c0fcc06e4` |
| `ac6_f2_geometry_review.py` | `src/scenario_a/ac6_f2_geometry_review.py` | `1ff75c25a5ded2d6c3a8ca140c1d1f1ddad25167fd2566dfde64afed8ecae4b1` |
| `ac6_f2_refinement.py` | `src/scenario_a/ac6_f2_refinement.py` | `324e7f281e85d759570c33dc81cc8e44cc55a434d0340576bfd42a608c177f9b` |
| `ac6_f2_refinement_review.py` | `src/scenario_a/ac6_f2_refinement_review.py` | `d94eba85c2c8e0d8f32d8a37410dff59f2311c2a05fc3ad13ed3ecb40bdde4ec` |
| `tests/test_execution.py` | `tests/test_execution.py` | `064be7b7c74f702fea0eb3d2794c55f9b67bb43522addcb4517555727af2c8a3` |

## Copy-local adaptations

- Python module repository roots changed from their original flat directory to this repository root (`Path(__file__).resolve().parents[2]`).
- `codex_to_comfy.DEFAULT_COMFY_ROOT` changed to `parents[4] / "Comfy-UI"` so the existing workspace ComfyUI location resolves from the new nested location.
- Validator `PROJECT` paths changed to the new repository root.
- The copied executor test imports from `src/scenario_a` and uses the system temporary directory because creating Python temporary directories inside this repository was denied by the current sandbox.
- The schemas were copied byte-for-byte. The listed SHA-256 values identify source bytes; adapted destination Python files intentionally have different hashes.

## Evidence scope

Historical PNG, GLB, plans, reports, reviews, and controller states remain in the source repository or ComfyUI workspace. None was migrated. M0 import and synthetic unit tests do not establish actual C1–C5 proof.

## M6 refactor provenance

Refactor baseline: `3129cf50e5c602f3e9e5bd0194cd46d42b9ddcee`. The M0 source identities above remain the historical copy record. M6 removed unused copied candidates from this Compact repository; the committed Research `Agent-Loop` at `7e1572a7e35866519b75b767398288396a27f9b0` remains their canonical historical source. The `auth_mode` function moved from the copied Scenario A `reviewer_adapter.py` to `src/core/reviewer_auth.py` without a behavior change. C1–C5 proof evidence was left unchanged.
