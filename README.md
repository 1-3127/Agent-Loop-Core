# Agent-Loop — host-independent reconstruction

This branch is a new implementation based on the verified invariants of `Agent-Loop-Core` v1. The historical source and actual C1–C5 evidence remain at `core-v1.0.0` and in the parent history. This branch does not claim a new live ComfyUI/Frontier run.

## Contract

The Host verifies an explicit User start and owns side-effect policy. Core consumes one verified ingress once, then owns one Session with a frozen specification, bounded Runs and Attempts. A Frontier selects or composes a sequential Workflow of Skills and chooses the next transition after an independent Reviewer examines the exact Worker Artifact. Worker, Frontier, Reviewer, and Host implementations are replaceable. Core contains no media or tool names.

Durable state consists of the original request, frozen specification, current workflow, selected checkpoints with hashes and lineage, current Review and Frontier Decision, and a compact event index. Transport data and routine logs are transient. An interrupted in-flight call is `BLOCKED_UNCERTAIN` until the Host resolves it explicitly; Core does not duplicate an expensive call.

The public Python entry points are `SessionEngine.start`, `provide_user_input`, `run`, `inspect`, and `deliver`. `run` stops at `INTERNAL_ACCEPT` for a final PASS; the Host calls `deliver` with the accepted Artifact hash and a receipt after actually presenting it. `VerifiedStartGrant` is an attestation made by a trusted Host, not a text token that Core can issue. A Host must verify its own User ingress before constructing it; see `agent_loop/host.py`. Core persists single-use consumption in a stable ledger outside individual session directories. The ledger must remain stable across all Sessions of one Host. Production needs a real Host ingress implementation and live Worker/Frontier/Reviewer adapters.

## Quick check

```bash
python -m unittest discover -s tests -v
python -m examples.demo
```

The example uses deterministic local adapters and demonstrates revision and checkpoint restart. The tests cover workflow reuse and sandbox denial. This is not an actual 3D production regression.

## Scope and provenance

See [CONTRACT.md](CONTRACT.md) for lifecycle and [PROVENANCE.md](PROVENANCE.md) for the historical reference. The previous implementation's code, proof and raw evidence are intentionally absent from this branch's tree. This rebuild does not preserve its internal API or file layout.
