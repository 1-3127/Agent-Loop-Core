# Reconstruction validation

| Step | Evidence | Result |
|---|---|---|
| 1. Contract | `CONTRACT.md`, `PROVENANCE.md`, clean tree descended from `12366d9` | Host and domain boundaries defined; historical proof retained in Git history |
| 2. Minimal loop | `agent_loop/` and deterministic demo | User start, frozen spec, Skill/Workflow, bounded Worker → Artifact → independent Review → Frontier Decision, restart/reworkflow, presentation receipt |
| 3. Portability checks | `python -m unittest discover -s tests -v` | 12/12 PASS: two artifact domains, Worker/Frontier substitution, fresh-engine resume, candidate Skill promotion, workflow reuse, lineage hash, budget, sandbox denial, duplicate start, uncertain effect |

The domain tests are deterministic contract checks. The mesh example uses `image → views → mesh` type labels and byte fixtures; it does **not** execute the original ComfyUI workflow or reproduce its actual 3D output. This environment does not contain the original models/ComfyUI runtime, real Codex transcript, or a live Frontier Reviewer. Accordingly there is no claim of a new actual C1–C5 run, a quality comparison, or a production-ready sandbox. The Host must enforce process isolation in addition to `SandboxHost.authorize`. The earlier actual proof remains at `core-v1.0.0` in Git history.
