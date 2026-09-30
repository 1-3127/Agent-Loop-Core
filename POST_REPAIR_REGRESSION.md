# M7 post-repair actual C1-C5 regression

## Verdict

POST-REPAIR C1-C5 ACTUAL REGRESSION VERIFIED. C1, C2, C3, C4, C5 = PASS. F01 runtime bypass probe = PASS. F03 runtime validation = PASS. Freeze requires the separate subsequent metadata commit/tag.

## Baselines and source candidate

- Original M6.5 baseline: `b13da2ea8c334fffbeb458e1a8894f4e3c4457a4`
- Direction Gate provenance/regression baseline: `1dd3c160b8f82e1cb17a88787b75b38ac00b6b77`
- Source changed during actual regression: false; existing tests/schema/requirements/AGENTS unchanged.

- `src` Git identity: `4505e60e978100666e5bd65b99514c90c2d891e2`
- `tests` Git identity: `70d1c3a38b28ae0bb7d308e12e18b285bf8ebc5b`
- `result_review_schema.json` Git identity: `deed0fddfe39486cb8d7a6aca63e97029029c52c`
- `requirements.txt` Git identity: `1ca121177af1a7a27869030c5c1452806e269273`
- `AGENTS.md` Git identity: `42168a1c70aeed568d9e909ca6b4d97cce988f4b`

## Direction Gate and contract scope

- Canonical: `docs/Agent-Loop_Direction_Gate_v1.md`
- Provenance: `docs/DIRECTION_GATE_PROVENANCE.md`
- Original: `C:/Users/Worker/.codex/attachments/9eb20a17-24a4-46f1-b47e-77f9345f809f/붙여넣은 텍스트.txt`
- Original and repository SHA-256: `1b43f3ddad27f6da003530c2d83db34eee53289cacfa403524b375b6a2623862`; 19242 bytes; byte-identical true.
- F07 = KNOWN NON-BLOCKING LIMITATION / HARDENING. Gate sections 4/5/10 require bounded run and explicit terminal; section 6 excludes comprehensive restart/resume, every crash-point recovery, and Reviewer reservation recovery. No explicit all-infrastructure-failure terminalization freeze requirement. Arbitrary failure/uncertain lifecycle terminalization and production-grade recovery are not claimed. Uncertain submission is not automatically retried.
- F05 = NON-BLOCKING ARCHITECTURAL DEBT. Gate section 10 C5 requires a minimal swap smoke; C1-C4 and C5 do not share a generic WorkerPort orchestration path. No migration performed.

## Frontier execution context / F04

- Codex and both Reviewer requested model display: GPT-6.1 Sol; requested reasoning effort: High.
- Git text normalization is disabled for the project config and hashed M7 reports to keep durable hash references stable.
- Requested Reviewer config: `.codex/config.toml`, model `gpt-6.1-sol`, reasoning `high`; source unchanged, global user config unchanged.
- Supported identifier/effort observed in local `models_cache.json`; installed CLI `codex-cli 0.159.0` help supports model/config selection. Fresh pre-invocation sidecars bind the exact project config hash and command.
- Independently observed actual model = UNKNOWN; actual reasoning effort = UNKNOWN. Adapter preserves stderr hash, not independently inspectable backend model identity. Requested config does not prove backend identity. F04 remains a reproducibility limitation.
- Reviewer auth = CHATGPT_ACCOUNT; no API key usage. User explicitly approved Chain A images and preauthorized subsequent Agent-Loop Core image transfers to Codex.
- Both actual invocations attached fresh generated output and original source, validated against request hashes; no historical verdict supplied.

## Chain A — C1 / C2 / C3

- Run: `m3-c3-reg-20260930-121432-28868f80`
- C1 Work Order: `m3-c3-reg-20260930-121432-28868f80-initial-right`; prompt_id `1154e4e9-02fe-4c16-8661-5de2d1fec553`.
- C2 Review ID: `m3-c3-reg-20260930-121432-28868f80-review`; verdict REVISE; action `{'code': 'REGENERATE_VIEW', 'target': 'right'}`.
- Concrete fresh blocker: The generated subject is clearly enlarged: it spans approximately y=85–680 versus y=168–596 in the source, about 39% more canvas height. This blocks the requested approximately equal visible scale.
- C3 revision Work Order: `m3-c3-reg-20260930-121432-28868f80-revision-right`; prompt_id `25d52a67-617e-4d83-be75-6439a70ee291`.
- Fresh Review request/result/invocation and Artifact A are bound directly in revision Work Order and execution evidence. Same source, workflow, model and seed 29481; prompt adapts the actual blocker. Artifact B was not reviewed.
- Initial and revision SUCCESS went through current `verify_images()` full remote/local byte equality, PNG CRC/integrity, IDAT decode, canonical IEND, and decoded dimensions. F03_RUNTIME_PATH_EXERCISED = true.

## Chain B — C4 / F01

- Run: `m4-c4-reg-20260930-122819-6f5c4427`; Worker prompt_id `ebee7f6e-8814-4901-bac8-af9b5e5c4839`.
- Initial immutable budget: `runs/m4-c4-reg-20260930-122819-6f5c4427_initial_budget.json`, SHA-256 `22c193c95c543f8c6126f6900f010f538e25d0fb72456d55001e20c84e7a49db`. SOURCE_READY; terminal false; Worker and Reviewer each 1/0/1.
- Initial contract created before actual Worker started; exact contract hash bound through Work Order, execution, worker state, request, reservation, terminal.
- Durable reservation created/fsynced before Reviewer started; run-level identity remains consumed after first invocation.
- Review ID: `m4-c4-reg-20260930-122819-6f5c4427-review`; actual verdict PASS; blocking issues none; action NONE.
- Before terminal, same Request with different result/report paths rejected REVIEW_BUDGET_ALREADY_RESERVED. Python runtime audit hook observed zero subprocess.Popen and zero urllib.Request events; alternative output files absent; reservation bytes unchanged. Existing run_review executed directly, no mock/stub.
- F01_RUNTIME_BYPASS_PROBE_BLOCKED = true; second Reviewer process/external dispatch = 0.
- Terminal: INTERNAL_ACCEPT -> DELIVERED; termination_reason INTERNAL_ACCEPT; internal_accept true; delivered artifact fixed.
- Final Worker budget 1/1/0; Reviewer 1/1/0. Limits not exceeded; remaining nonnegative.
- Terminal resolver re-entry ALREADY_TERMINAL; additional run_review rejected ALREADY_TERMINAL; no process/network effect; terminal bytes/hash unchanged.
- Delivered PNG will be submitted with original Input in the final user response. User verdict remains outside Core terminal/freeze and cannot reopen this run.

## Chain C — C5

- Proof: `m5-c5-reg-20260930-123412-ff1e9bee`; adapters `scenario_a_comfy` and `deterministic_test_worker`.
- Adapter A invocation `38c0a312-a890-4be8-bbae-1de0148519e4`; Adapter B invocation `cba98ecf-cd45-408f-a274-4ce640ace88a`.
- Both use the same `core.worker_port.execute(adapter, work_order)` and common Result/artifact validation.
- WorkerPort SHA before A/before B/after B: `bb25d1d69761c0e59ca3477045b61e073c00040480d752b142fdb2e82c681296` (all equal).
- Core modified between swaps false; semantic Reviewer calls 0. Test Worker remains test-only.

## Fresh artifacts

| Stage | Path | Bytes | SHA-256 |
|---|---|---:|---|
| A initial | `D:\VSCODE-WorkSpace\Comfy-UI\work\output\codex_to_comfy\m3-c3-reg-20260930-121432-28868f80_00001_.png` | 233510 | `98d5819f11fe5a509fcb49af18814512722c956aa6698f288ea05cd7b216ba81` |
| A revision | `D:\VSCODE-WorkSpace\Comfy-UI\work\output\codex_to_comfy\m3-c3-reg-20260930-121432-28868f80-revision_00001_.png` | 242980 | `1fb72a416a3094e0a226d9826938c0690293b598b89de851f664bb0f653f6abf` |
| B C4 | `D:\VSCODE-WorkSpace\Comfy-UI\work\output\codex_to_comfy\m4-c4-reg-20260930-122819-6f5c4427_00001_.png` | 252802 | `77aa25b6723ec427dd53365b5f7a8ba6c4041029cc1f435e20f3a0713f026be7` |
| C Comfy | `D:\VSCODE-WorkSpace\Comfy-UI\work\output\codex_to_comfy\m5-c5-reg-20260930-123412-ff1e9bee-comfy_00001_.png` | 252808 | `59386e3cf0ee437ad64900315e5445adcab9035d227941add8dd9387192aa870` |
| C deterministic | `D:\VSCODE-WorkSpace\Others\Agent-Loop-Core\runs\m5-c5-reg-20260930-123412-ff1e9bee-deterministic.txt` | 97 | `570a9422b12d4dc800924cf8df574462fb0634da89a3025871ce7421412f7409` |

## Actual effect counts and cache evidence

- ComfyUI = 4 (four distinct prompt_ids), semantic Frontier Reviewer = 2 (two actual account-mode processes), deterministic Worker = 1 (actual local UUID invocation). All at declared caps.
- Live Comfy history confirmed success and fresh output filenames for all four invocations. SaveImage node 13 was not cached for any invocation. C5 reused cached upstream graph computation; it still invoked ComfyUI and executed SaveImage for its fresh namespace. It is not a historical output replay.

## Usage

- `usage/m3-c3-reg-20260930-121432-28868f80_regression.json`: {"run_id": "m3-c3-reg-20260930-121432-28868f80", "frontier": {"provider": "OpenAI", "model": null, "invocations": 1, "input_tokens": null, "cached_input_tokens": null, "output_tokens": null, "reasoning_tokens": null, "reported_credits": null, "auth_mode": "CHATGPT_ACCOUNT", "review_duration_seconds": 40.03100000000086}, "workers": [{"worker_id": "scenario-a-qwen-right", "backend": "ComfyUI", "model": "Qwen-Image-Edit-2509-Q4_K_S.gguf", "invocations": 1, "execution_seconds": 146.990467}, {"worker_id": "scenario-a-qwen-right-revision", "backend": "ComfyUI", "model": "Qwen-Image-Edit-2509-Q4_K_S.gguf", "invocations": 1, "execution_seconds": 119.872644}], "note": "Actual model/token/credits not independently exposed; no estimates. Artifact B not reviewed."}
- `usage/m4-c4-reg-20260930-122819-6f5c4427_regression.json`: {"run_id": "m4-c4-reg-20260930-122819-6f5c4427", "frontier": {"provider": "OpenAI", "model": null, "invocations": 1, "input_tokens": null, "cached_input_tokens": null, "output_tokens": null, "reasoning_tokens": null, "reported_credits": null, "auth_mode": "CHATGPT_ACCOUNT", "review_duration_seconds": 18.85900000000038}, "workers": [{"worker_id": "scenario-a-qwen-right", "backend": "ComfyUI", "model": "Qwen-Image-Edit-2509-Q4_K_S.gguf", "invocations": 1, "execution_seconds": 117.5161}], "run": {"terminal_status": "DELIVERED", "worker_budget": {"limit": 1, "consumed": 1, "remaining": 0}, "reviewer_budget": {"limit": 1, "consumed": 1, "remaining": 0}}, "unavailable_reason": "Actual model/token/credits not independently exposed; requested configuration in Frontier sidecar."}
- `usage/m5-c5-reg-20260930-123412-ff1e9bee.json`: {"proof_id": "m5-c5-reg-20260930-123412-ff1e9bee", "workers": [{"adapter_id": "scenario_a_comfy", "backend": "ComfyUI", "model": "Qwen-Image-Edit-2509-Q4_K_S.gguf", "invocations": 1, "execution_seconds": 2.121619}, {"adapter_id": "deterministic_test_worker", "backend": "deterministic local worker", "model": null, "invocations": 1, "execution_seconds": 0.01600000000144064}], "frontier_reviewer": {"invocations": 0, "model": null, "tokens": null, "credits": null}}
- Unknown actual model/token/credits are null; no estimates. Measured execution/review durations come from actual reports.

## Tests and source/historical integrity

- `PYTHONPATH=src; python -m unittest discover -s tests -p 'test_*.py' -v`: 38/38 PASS using existing Python 3.12.14 and Pillow 12.3.0.
- C4 PASS/REVISE/HUMAN_REQUIRED branch and terminal re-entry tests PASS; F01 collision/changed output/uncertain/failure tests PASS; F03 integrity/decode/payload tests PASS.
- Core independence and single src import root tests PASS. Active CLI help smoke: 8/8 PASS.
- Protected pre-M7 evidence/reports: 51 files; modified count 0. Git diff for src/tests/schema/requirements/AGENTS empty.
- Research HEAD remains `7e1572a7e35866519b75b767398288396a27f9b0`; sole untracked F2B WIP `ac6_f2b_resume.py` remains SHA-256 `2a58ab64e8838e8c3da6d8b4d62526e1a8d0d834bb26058d905d80d73dfd9369`. No Research changes/commit/push.

## Fresh evidence references

| Path | SHA-256 |
|---|---|
| `.codex/config.toml` | `f9caaf0c19849f3ce6f8b3d273db20190b7a8e63375f8a7f641b321a2193186a` |
| `plans/m3-c3-reg-20260930-121432-28868f80-initial-right.json` | `5f732bd97a94255215b7d40b6966274ce1bca8da6e73f9d5dd8804fd87dcf1c0` |
| `plans/m3-c3-reg-20260930-121432-28868f80-revision-right.json` | `2e889e364f7604ff571d9a701d9e34d2f05fceb072d4dcc6fb306af5d505beb1` |
| `plans/m4-c4-reg-20260930-122819-6f5c4427-initial-right.json` | `ac31676c28ca286a508993e28284ae5c140d356bcf77a1f75e7d50336e8981c8` |
| `plans/m5-c5-reg-20260930-123412-ff1e9bee-comfy-initial-right.json` | `f74ec10d64ad3220a841181e3dd7a4931092dc33aabd3e27e49f494e240f52fa` |
| `reviewer_requests/m3-c3-reg-20260930-121432-28868f80-review.json` | `c5ada0dc342b8828941b29a9e5df2ea3cfd493c9c94de1c14b30239d78909d8c` |
| `reviewer_requests/m4-c4-reg-20260930-122819-6f5c4427-review.json` | `3001674df349de40775b640402acc3b40b5a1e5507f254a1811809c59d6e8dd5` |
| `reviews/m3-c3-reg-20260930-121432-28868f80-review.json` | `5ef9644b79eb3dc8525c95808acec4d12b13025ac1d996ca4e79a4c494b40a1c` |
| `reviews/m4-c4-reg-20260930-122819-6f5c4427-review.json` | `f1f4f51d53e0c28eb19983cdb50f82f01d2c166d5f84418d59655bd60854be08` |
| `runs/m3-c3-reg-20260930-121432-28868f80-review_frontier_request.json` | `1d083025179c7491f6410190c5035cfe11d22b256c52f40095a08867e7c82bd7` |
| `runs/m3-c3-reg-20260930-121432-28868f80_initial_execution.json` | `48d1ca3ad23d6580715030df77fb682c0afe657261c5dac47a0ff926316b031a` |
| `runs/m3-c3-reg-20260930-121432-28868f80_initial_worker_report.json` | `93a070d5dd2b4af0279fd1a1b2748af912b77c7978c26ee5265783f418ed95f7` |
| `runs/m3-c3-reg-20260930-121432-28868f80_m7_source_snapshot.json` | `0d80f1a5d4a22e0a9057cc5a3351013cd5b1049654f8d78f6fbb2bfd3adfc9bd` |
| `runs/m3-c3-reg-20260930-121432-28868f80_m7_validation.json` | `483a943a513556336b8012ede01d1e01da9c40a0c6645f75f4448428b51b31cc` |
| `runs/m3-c3-reg-20260930-121432-28868f80_review_invocation.json` | `490a1a8f3a12552726572c0493b4f27986a5dca65ba3116f591d772e74536e59` |
| `runs/m3-c3-reg-20260930-121432-28868f80_revision_execution.json` | `67b97d7e128e4e76e4758dc247153641f133b63dec50b1229cec9829256a1013` |
| `runs/m3-c3-reg-20260930-121432-28868f80_revision_worker_report.json` | `4a4a1b3266ebc2134d7357a93b153ba72717c706855193eca4b667bc3e291f4c` |
| `runs/m4-c4-reg-20260930-122819-6f5c4427-review_frontier_request.json` | `11d9485680bb8cdccf9cc4bd9e54a1d394d5a0148a4c821d8834c367417d700e` |
| `runs/m4-c4-reg-20260930-122819-6f5c4427_execution.json` | `10984f8e6c166bb717f7fbc004cbf8417d2a50aa9b51c66b408042028576f190` |
| `runs/m4-c4-reg-20260930-122819-6f5c4427_guard_probe.json` | `a5ee6918eb9cf338412ae962fde632af5e35a5074933e62c8ff4f0c9141cbdc6` |
| `runs/m4-c4-reg-20260930-122819-6f5c4427_initial_budget.json` | `22c193c95c543f8c6126f6900f010f538e25d0fb72456d55001e20c84e7a49db` |
| `runs/m4-c4-reg-20260930-122819-6f5c4427_review_invocation.json` | `b27e00e6cf96c7f429ce01d472e0d97aebd0143d5d4e3209aa712ec4bf337044` |
| `runs/m4-c4-reg-20260930-122819-6f5c4427_review_reservation.json` | `70a58cc30dbadc1ec4b3d4e18568e8853ac711deece117cc1eae1d15df99722a` |
| `runs/m4-c4-reg-20260930-122819-6f5c4427_terminal.json` | `4b8f494872a9191cb2c29727be49a2ed34a5439226346845871d635bf48c43d1` |
| `runs/m4-c4-reg-20260930-122819-6f5c4427_worker_report.json` | `b2d1e3751156bb7d3b655c0cd2a2f1cb0971a4f6a805d40db6377d1d1c630a5c` |
| `runs/m4-c4-reg-20260930-122819-6f5c4427_worker_state.json` | `6a3cbfe644f053a446f70331c435da2a21688bf79cec67428a47434b17f4f6cd` |
| `runs/m5-c5-reg-20260930-123412-ff1e9bee-comfy_c1_execution.json` | `4417a1ef90c2de9e947688d223e79543128aa266b5fdeb75f2d982d22ce9acc3` |
| `runs/m5-c5-reg-20260930-123412-ff1e9bee-comfy_worker_report.json` | `bc35884b7d4492266200858e7f2b8d2eccfe664d7ece71d556a6944db121c19f` |
| `runs/m5-c5-reg-20260930-123412-ff1e9bee-comfy_worker_result.json` | `e308f880d78ef57ebbb147a790401bbcdbce3f1ec2bf34693368fa9061c75452` |
| `runs/m5-c5-reg-20260930-123412-ff1e9bee-deterministic.txt` | `570a9422b12d4dc800924cf8df574462fb0634da89a3025871ce7421412f7409` |
| `runs/m5-c5-reg-20260930-123412-ff1e9bee-deterministic_worker_result.json` | `a02fdfff19b2dd195bd0080aa7336f597c98fecedc98dcf8d2c3d969aee8316e` |
| `runs/m5-c5-reg-20260930-123412-ff1e9bee_c5_boundary.json` | `507a8425c16c82764ed159c13b6733100517c5b83a1adab90e352ff2bfbf80bf` |
| `usage/m3-c3-reg-20260930-121432-28868f80_initial.json` | `44138571920b3df384d9763a2298d82eb17321736b793db81ab47aa26dd40c81` |
| `usage/m3-c3-reg-20260930-121432-28868f80_regression.json` | `0508dfd00b51a12132ad16c7981fca4b9a30ad76a6247802944fd1e70ec96a47` |
| `usage/m4-c4-reg-20260930-122819-6f5c4427_regression.json` | `9913a6786dd465dd8a388a066caba3b3af9c9fecb57b798bb7bb070911e5d02a` |
| `usage/m4-c4-reg-20260930-122819-6f5c4427_worker.json` | `a4adea8edfb0075b5535b1b0d9ccd0180d77106882eca45db01f46dcdc712fcc` |
| `usage/m5-c5-reg-20260930-123412-ff1e9bee-comfy.json` | `d566130dfbb0f13194a1b78bc2c0aa855651377e8ef956ed69e878a141d33732` |
| `usage/m5-c5-reg-20260930-123412-ff1e9bee.json` | `fb47c0685e49fe33395e0c343753edbdfbb03805e56f246fb39bb0b234612243` |
| `work_orders/m3-c3-reg-20260930-121432-28868f80-revision-right.json` | `7986b4f9b1d8350117d4bc709eec8b5953540309d80f832ef1ed4cd2ae50c598` |
| `work_orders/m3-c3-reg-20260930-121432-28868f80.json` | `304d2f5795c2908f685567cb93f199a3639529718e6553ff59ec63fdbd9b29bf` |
| `work_orders/m4-c4-reg-20260930-122819-6f5c4427.json` | `7d3cb51278473ba2ae92a72367c40e419f7559f3d8a7f24508b997bc8d98f515` |
| `work_orders/m5-c5-reg-20260930-123412-ff1e9bee-comfy-delegate.json` | `13b5c20f9d85d4fe9f39329a8440ecc44d234d718a16efa88583dd69667f6406` |
| `work_orders/m5-c5-reg-20260930-123412-ff1e9bee-comfy.json` | `85bf116113be74ce5d9b52f283350570ba1513a8b6510a36d4dbf685ba41750d` |
| `work_orders/m5-c5-reg-20260930-123412-ff1e9bee-deterministic.json` | `a23934b8a370f2c5f17830a436c031adc26b4a0a1c70072ed0e0adfd673fc8f5` |

## Deferred work

- F04 actual identity telemetry; F05 generic integration; F07 arbitrary failure/uncertain lifecycle hardening.
- F2B comprehensive resume is Hardening Backlog. Hypothesis Benchmark is next phase / not started. No Scenario B, geometry, benchmark, production recovery or new orchestration implemented.
