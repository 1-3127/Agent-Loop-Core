# Post-Stabilization Actual Loop Proof

CP1: ACTUAL_EXECUTION_READY; generation effects0.

적용 AGENTS.md와 Agents/workflow.md, Design Philosophy → Direction/Contract → Current Source/Evidence 순서로 확인했다. 현재 사용자 요청만 실행 승인으로 적용한다.

시작: stabilization-i03-namespace-preflight / f212bcdc3749edf96e9e0b68b5cb4e458f9c6770; clean; local=tracking=live remote.
새 proof branch: actual-loop-post-stabilization.
Session: psa-session-20261001-031107-2c54c2a3; Loop: psa-loop-20261001-031107-2c54c2a3.

Frozen Spec: POST_STABILIZATION_WORK_SPECIFICATION_v1.md; SHA-256 73da08888221bf1e2e9b19d66716c09315edc343a8cd40ebcec6c74a23c73f34; projection identity 52e5df408164f80465c628f051909dc5ae02f6d2f0c3fd9af4acb58ac9b7592e.

Specification Dialogue: 충분한 context, 결정적 ambiguity 없음. 동일 historical validation objective를 독립적으로 재도출했다. Multiview criterion은 multiview, geometry criterion은 geometry에만 배정한다. C-01 final mandatory aggregation과 I-03 3+7 namespace gate를 실제 zero-effect production preflight로 통과했다.

현재 full regression 213/213 PASS; network0/production process0/import smoke1. 첫 검사 harness의 root import 경로 누락은 실패 기록으로 보존하며, harness만 수정한 재검사다. source/test 변경0.

ComfyUI live devices/required nodes/queue, 4 workflow hashes, 6 model file sizes, canonical PNG hash/decode/dimensions, Blender --version, Codex CLI 및 CHATGPT_ACCOUNT 인증 확인. Actual backend model/effort는 UNKNOWN.

기존 capability fixed_four_view_glb_seed_only; Worker6/Reviewer4/Renderer2/revision1/retries0. One existing production entry, at most one current-evidence correction. CP1 기록/commit 후 actual을 시작한다.

CP1 evidence: runs/session/psa-session-20261001-031107-2c54c2a3/checkpoint1_ready.json.

CP2: actual one-shot 완료; 아래 결과와 evidence를 참조한다.

Delivery/close-for-delivery/fresh Session은 이번 proof 범위 밖이다. 기존 S3C ABORT/REVISION_BUDGET_EXHAUSTED와 INTERNAL_ACCEPT NONE, Frozen Core/S3A/모든 historical evidence는 보존한다. I-01/I-02는 변경하지 않는다.


## CP2 — One Actual Loop Result

POST-STABILIZATION ACTUAL LOOP = VERIFIED

Session state: INTERNAL_ACCEPT; INTERNAL_ACCEPT: True; delivered=false.
CP1 commit: 7e9ea67c300c0c2816cd3253700aa55942cdfd58.
Actual counts: {"comfy_prompt_attempts": 4, "semantic_process_attempts": 2, "blender_process_attempts": 1, "comfy_accepted_submissions": 4, "correction_dispatch": 0, "run_session_execute_true": 1, "automatic_retries": 0, "user_delivery": 0}.

| Review | stage | verdict | applicable coverage |
|---|---|---|---|
| psa-l6-20261001-031107-2c54c2a3-multiview-review | multiview | PASS | {"AC-MULTIVIEW-COHERENCE": "SATISFIED"} |
| psa-bridge-20261001-031107-2c54c2a3-geometry-review | geometry | PASS | {"AC-GEOMETRY-IDENTITY": "SATISFIED"} |

Correction: null

Final blockers: []

Artifact/Request/Result/Invocation/coverage/Session/Spec/child lineage는 기존 production validators와 recorded hashes로 검증했다. Pure validation의 network/process/write는 차단하고 기존 proof bytes 불변을 확인했다. Actual /prompt body와 independent GET /history 응답의 client/prompt graph, execution success 및 Save output node 실제 실행도 확인했다.

기존 tracked 372개 SHA-256 불변; source/test/historical evidence 변경0; external reference 44개 metadata/작은-file SHA 불변. Large model full hashes는 미측정이다. Protected local refs 불변. Evidence details: runs/session/psa-session-20261001-031107-2c54c2a3/checkpoint2_verified.json.

INTERNAL_ACCEPT와 User Delivery는 구분한다. Delivery Package/DELIVERED/closure/fresh Session 생성0. 추가 actual/retry/seed reroll/source repair0. 실패 evidence는 그대로 유지한다. CP2 normal commit과 push 후 local/tracking/live remote equality는 별도 final verification 기록에서 확인한다.
