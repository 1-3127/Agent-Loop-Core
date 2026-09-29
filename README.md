# Agent-Loop-Core

Compact workspace for proving a fixed Frontier Supervisor's bounded delegation to replaceable Local Workers. The Frontier issues work, reviews the resulting artifact, and decides whether to revise or deliver it. Scenario A (single image → multiview → 3D) is the first reference path, under `src/scenario_a/`.

The technical proof targets C1 real delegation, C2 semantic review of the real artifact, C3 an actual revise and worker rerun, C4 bounded `DELIVERED`/`FAILED`/`ABORT` termination, and C5 a worker adapter swap without changing Core logic. **M0 only bootstraps the workspace; none of C1–C5 is claimed here.** The Agent-Loop Direction Gate v1 governs scope.

`src/core/` holds the copied generic result Review boundary. The existing controller and F2 route still contain Scenario A policy and remain in `src/scenario_a/`; this placement is a source selection, not a completed generic Core. Python modules retain their original flat imports. For a smoke import on Windows, set `PYTHONPATH` to both `src/core` and `src/scenario_a`. The active ComfyUI workflows are referenced from `../../Comfy-UI`; no workflow or model is stored here.

Source decisions and exact identities are in [SOURCE_MANIFEST.md](SOURCE_MANIFEST.md) and [PROVENANCE.md](PROVENANCE.md).
