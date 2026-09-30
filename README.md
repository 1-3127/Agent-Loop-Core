# Agent-Loop-Core

Compact workspace for proving a fixed Frontier Supervisor's bounded delegation to replaceable Local Workers. The Frontier issues work, reviews the resulting artifact, and decides whether to revise or deliver it. Scenario A (single image → multiview → 3D) is the first reference path, under `src/scenario_a/`.

The C1–C5 technical proofs are complete: real delegation, semantic review, actual revision, bounded termination, and a Worker adapter swap through the same Core entry point. The C5 evidence is `runs/m5-c5-20260930-050343-eecc84cd_c5_boundary.json`. The compact refactor, F01/F03 audit repairs, and post-repair actual C1–C5 regression are complete. Core v1 is frozen at annotated tag `core-v1.0.0`; see [POST_REPAIR_REGRESSION.md](POST_REPAIR_REGRESSION.md) and [CORE_V1_FREEZE.md](CORE_V1_FREEZE.md). The [Agent-Loop Direction Gate v1](docs/Agent-Loop_Direction_Gate_v1.md) governs scope, with [verbatim provenance](docs/DIRECTION_GATE_PROVENANCE.md).

`src/core/` contains `worker_port.py`, `result_review_adapter.py`, and `reviewer_auth.py`; it does not import Scenario A. The active `src/scenario_a/` path is `c1_delegate.py`, `c2_review.py`, `c3_review.py`, `c3_revision.py`, `c4_bounded.py`, `c5_worker_swap.py`, `codex_to_comfy.py`, and `comfy_worker_adapter.py`. `tests/fixtures/deterministic_worker.py` is test-only. From the repository root, set `PYTHONPATH=src` and run a CLI as `python -m scenario_a.c1_delegate --help` (or another active module); tests run with `python -m unittest discover -s tests -p 'test_*.py'`. The active ComfyUI workflows are referenced from `../../Comfy-UI`; no workflow or model is stored here.

Source decisions and exact identities are in [SOURCE_MANIFEST.md](SOURCE_MANIFEST.md) and [PROVENANCE.md](PROVENANCE.md).
The post-COMPLETE cleanup and its validation limits are in [REFACTOR_REPORT.md](REFACTOR_REPORT.md).

PNG validation requires the Pillow version declared in [requirements.txt](requirements.txt); use a Python runtime that provides it. Audit reproductions and local repair validation are in [AUDIT_REPAIR_REPORT.md](AUDIT_REPAIR_REPORT.md).

Deferred: Hypothesis Benchmark (not started), F2B comprehensive resume, production hardening, F05 generic integration, and F07 arbitrary failure/uncertain lifecycle hardening. F04 actual Frontier model/effort identity remains UNKNOWN.
