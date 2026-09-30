# Agent Loop Core v1 freeze

## Frozen scope

Core v1 fixes the verified source, contracts, and proof scope for bounded Frontier delegation to replaceable Local Workers. C1 actual delegation, C2 semantic review, C3 actual revision, C4 bounded terminal, and C5 minimal adapter swap were freshly regressed against the M6.5 repaired source. Freeze is identified by annotated Git tag `core-v1.0.0`, on the documentation-only freeze commit immediately following the regression commit below.

## Authority and provenance

- Authoritative document: `docs/Agent-Loop_Direction_Gate_v1.md`.
- SHA-256: `1b43f3ddad27f6da003530c2d83db34eee53289cacfa403524b375b6a2623862`; 19242 bytes; byte-identical to original user attachment.
- Provenance and F05/F07 scope decision: `docs/DIRECTION_GATE_PROVENANCE.md`.
- M6.5 repair baseline: `b13da2ea8c334fffbeb458e1a8894f4e3c4457a4`.
- Direction Gate provenance / regression baseline commit: `1dd3c160b8f82e1cb17a88787b75b38ac00b6b77`.
- Regression evidence commit: `51336bda00dc56db940f6b6dd96759c70add7861`.
- Regression report: `POST_REPAIR_REGRESSION.md`; SHA-256 `61b2405be5ed6cc2c67fe51f5ff4d4b3618befc76edd3618b8146da12bc97d8c`.

## Source candidate identities

- `src` Git identity: `4505e60e978100666e5bd65b99514c90c2d891e2`.
- `tests` Git identity: `70d1c3a38b28ae0bb7d308e12e18b285bf8ebc5b`.
- `result_review_schema.json` Git identity: `deed0fddfe39486cb8d7a6aca63e97029029c52c`.
- `requirements.txt` Git identity: `1ca121177af1a7a27869030c5c1452806e269273`.
- `AGENTS.md` Git identity: `42168a1c70aeed568d9e909ca6b4d97cce988f4b`.

Source/tests/schema/requirements were unchanged throughout actual regression and freeze. Core independence and single src import root verified.

## Actual regression

- Chain A `m3-c3-reg-20260930-121432-28868f80`: C1 PASS; C2 actual Review REVISE on excessive subject scale; action REGENERATE_VIEW/right; C3 fresh actual revision and artifact B lineage PASS. No review of B.
- Chain B `m4-c4-reg-20260930-122819-6f5c4427`: C4 PASS. Worker/Reviewer limits each 1 predeclared before effects; actual Review PASS -> INTERNAL_ACCEPT -> DELIVERED. Final budgets each 1/1/0.
- F01 actual runtime probe: same C4 Request, different result/report paths, before terminal; REVIEW_BUDGET_ALREADY_RESERVED, zero second process/dispatch, reservation unchanged. Terminal re-entry ALREADY_TERMINAL, no effect, immutable terminal bytes.
- F03 current verify_images runtime exercised on all actual Comfy invocations: full remote/local payload equality, PNG integrity/CRC, decode, IEND, dimensions before SUCCESS.
- Chain C `m5-c5-reg-20260930-123412-ff1e9bee`: C5 PASS. Comfy and deterministic Worker share core.worker_port.execute; common Results/artifacts validated; WorkerPort SHA before A/before B/after B all `bb25d1d69761c0e59ca3477045b61e073c00040480d752b142fdb2e82c681296`.
- Actual effects: ComfyUI 4, semantic Frontier Reviewer 2, deterministic local Worker 1; at declared caps. Comfy history confirms fresh output node 13 execution for all four; C5 upstream graph cache reused, SaveImage not cached.
- Validation evidence: `runs/m3-c3-reg-20260930-121432-28868f80_m7_validation.json`; SHA-256 `483a943a513556336b8012ede01d1e01da9c40a0c6645f75f4448428b51b31cc`.
- Unit tests: `PYTHONPATH=src; python -m unittest discover -s tests -p 'test_*.py' -v`: 38/38 PASS (Python 3.12.14, Pillow 12.3.0). Active CLI help smoke 8/8 PASS.
- Historical evidence/reports protected: 51; modified count 0.

## Frontier identity / usage limitations

- Requested execution/Reviewer model display GPT-6.1 Sol; requested reasoning High.
- Project config requests supported identifier gpt-6.1-sol and reasoning high; two pre-invocation Frontier sidecars bind config hash and exact command.
- Actual model = UNKNOWN; actual reasoning effort = UNKNOWN. No inference from requested setting to backend identity. Adapter preserves stderr hash rather than independently observable model identity.
- Actual account-mode process counts and durations measured; model/token/credits unknown values null. No estimates.

## Known non-blocking limitations

- F04: actual backend model/effort identity is not independently verified; reproducibility limitation.
- F05: C1-C4 and C5 do not constitute a generic WorkerPort orchestration path; NON-BLOCKING ARCHITECTURAL DEBT. Gate C5 is minimal swap proof.
- F07: KNOWN NON-BLOCKING LIMITATION / HARDENING. Gate sections 4/5/10 define bounded run terminal proof; section 6 excludes comprehensive restart/resume, every crash-point recovery, and Reviewer reservation recovery. Arbitrary infrastructure failure/uncertain lifecycle terminalization is not claimed. Uncertain submission is not automatically retried; production-grade recovery is not claimed.
- Deterministic Worker remains test-only. Scenario A proof does not establish the full multiview/3D production pipeline or quality/cost superiority.

## Research protection and deferred work

- Research repository `D:/VSCODE-WorkSpace/Others/Agent-Loop` remains read-only.
- HEAD `7e1572a7e35866519b75b767398288396a27f9b0`.
- Sole untracked F2B WIP ac6_f2b_resume.py SHA-256 `2a58ab64e8838e8c3da6d8b4d62526e1a8d0d834bb26058d905d80d73dfd9369`, unchanged. No Research commit/push.
- Hypothesis Benchmark = NEXT PHASE / NOT STARTED.
- F2B comprehensive resume = HARDENING BACKLOG.
- Production hardening, F05 generic integration, F07 failure lifecycle work deferred.
- C4 original Input and final Delivered Output are submitted together in the final user response; user verdict stays outside Core state and freeze, and cannot reopen the terminal run.

## Final technical state

LOOP CORE V1 TECHNICAL COMPLETE
CORE V1 REFACTOR COMPLETE
M6.5 AUDIT DEFECT REPAIR PASS
POST-REPAIR C1-C5 ACTUAL REGRESSION VERIFIED
CORE V1 FROZEN = YES (immutable reference: core-v1.0.0)
