# M7 bounded promotion contract correction

The M1 implementation checked the outer actual-success attestation and file hashes, but did not inspect whether those referenced reviews and invocations were actual. That allowed an ACTUAL label to conceal synthetic accepted evidence. This was discovered during M7 structural review before any actual Stone Lantern execution or promotion.

`checked_actual_success()` now validates the current acceptance gate, CLOSED Session, accepted Workflow containing the exact Skill/VCS/hash ref, current stage Reviews and mandatory MET coverage, actual successful Review/Frontier invocation records and their request/result bindings, and the accepted Frontier Decision. `record_validation()` and `validation_status()` both use that boundary. Packages and prior historical reports remain immutable; no Skill was promoted by the synthetic proof.

The complete synthetic two-Run test also presents a mislabelled ACTUAL success and a forged VALIDATED record. Both must fail before promotion. This remains a local caller-supplied evidence contract, not a tamper-proof attestation of an operating system or remote service.

The pre-correction augmented full suite passed 324/324 and is retained separately. Focused/related validation after correction passed 72/72. Final full regression on the corrected code passed 324/324 with zero failures, errors or skips; network, production-process and repository-write tripwires all remained zero. Test-helper and interrupted preliminary regression logs are retained as development diagnostics; none is an actual production attempt.
