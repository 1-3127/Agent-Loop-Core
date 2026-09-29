# Agent-Loop-Core

Compact workspace for proving a fixed Frontier Supervisor's bounded delegation to replaceable Local Workers. The Frontier issues work, reviews the resulting artifact, and decides whether to revise or deliver it. Scenario A (single image → multiview → 3D) is the first reference path, under `src/scenario_a/`.

The C1–C5 technical proofs are complete: real delegation, semantic review, actual revision, bounded termination, and a Worker adapter swap through the same Core entry point. The C5 evidence is `runs/m5-c5-20260930-050343-eecc84cd_c5_boundary.json`. This is `LOOP CORE V1 TECHNICAL COMPLETE`; it does not claim a frozen Core, completed refactor, regression campaign, benchmark, or production reliability. The Agent-Loop Direction Gate v1 governs scope.

`src/core/` holds the copied result Review boundary and the C5 Worker entry point. The existing controller and F2 route still contain Scenario A policy and remain in `src/scenario_a/`. Python modules retain their original flat imports. For a smoke import on Windows, set `PYTHONPATH` to both `src/core` and `src/scenario_a`. The active ComfyUI workflows are referenced from `../../Comfy-UI`; no workflow or model is stored here.

Source decisions and exact identities are in [SOURCE_MANIFEST.md](SOURCE_MANIFEST.md) and [PROVENANCE.md](PROVENANCE.md).
