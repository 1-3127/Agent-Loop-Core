# M2 Checkpoint

- Implemented: frozen Workflow scope projection, sequential versioned Workflow Artifact, exact Skill/capability/tool/model preflight, evidence-bound strategy revision, replaceable Frontier inference adapter, model-result → planned Workflow → Decision Artifact linkage, non-blocking Workflow disclosure metadata.
- Module contracts touched: Frontier Supervisor; Workflow Planner; Workflow Artifact; Diagnosis decision boundary (action vocabulary only). core.frontier contains the initial Codex adapter implementation; controller/routing integration follows M3–M6.
- Source/tests/docs changed: core/workflow_artifact.py, core/frontier.py, test_workflow_artifact.py, test_frontier.py; M2 report/log/validation/runtime sources/local defect evidence.
- Focused tests: 11/11 PASS (Workflow 6 + Frontier 5); frozen applicability cannot be weakened, model/tool/pin preflight, immutable evidence-linked revisions, seed-only tuning remains an Attempt, current Review/Skill guidance inputs, context mutation rejection, wrong auth mode blocks before invocation.
- Related regression: M1 10/10 and package boundary 2/2 PASS; total 23/23.
- Full regression if run: baseline 277/277 PASS; M7 full regression remains required before actual GPU proof.
- Actual external effects: production Worker/ComfyUI/Blender/semantic Reviewer/Frontier = 0. Official documentation read and codex exec --help only; one local synthetic import-smoke process.
- New Artifacts / logs: M2_FOCUSED.log, M2_VALIDATION.json, M2_LOCAL_DEFECT.log, INFERENCE_RUNTIME_SOURCES.md. Workflow/Decision fixtures are synthetic and temporary; no actual intelligence claim or Skill promotion.
- Git commit: this M2 checkpoint commit.
- Push status: normal push after stable checkpoint; equality verified after publication.
- Protected-state validation: historical source/evidence/refs retained; baseline tracked-byte/ref comparison performed at checkpoints.
- Known limitations: actual Codex adapter execution is implemented but not live-verified until M8. Raw inference stdout/stderr contents and reasoning events are not persisted; invocation hashes, structured result, observable model header when present, thread identity and numeric usage are retained. Resource reservation, stage routing, runtime execution, logs and delivery integration follow M3–M6.
- Local defect: an incorrectly inserted test block failed once; failure evidence retained, block placement fixed, final 23/23 PASS. Early test fixture inheritance/import duplicate counting was removed; final counts are unique tests.
- Next checkpoint: M3 Session → Production Run → Attempt hierarchy and resource/namespace ownership.
