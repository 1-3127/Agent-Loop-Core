# Semantic Reviewer Failure Observability Corrective

로컬 판정: **LOCAL_VALIDATION_PASS**. 최종 `REVIEWER FAILURE OBSERVABILITY = STABILIZED`는 이 checkpoint의 단일 commit / 정상 push / local=tracking=live remote / clean 검증 후 선언한다. Publication 결과는 최종 사용자 보고에 기록하며 self-referential commit identity를 이 문서에 넣지 않는다.

## 기준점과 범위

- 시작: `diagnosis-semantic-reviewer-exit1` / `63a9fd6f38d245f96e9db8f69b3eaa2f54ac1928`. Clean, local=tracking=live remote 확인 후 `stabilization-reviewer-failure-observability` 생성. Origin: `https://github.com/1-3127/Agent-Loop-Core.git`.
- 현재 corrective 요청이 source/test/docs 수정 및 동일 branch 정상 push의 명시적 승인이다. 과거 proof의 실행 지시는 신규 승인으로 사용하지 않았다.
- 적용 지침: workspace/Others/Core `AGENTS.md`, human-managed `D:/VSCODE-WorkSpace/Agents/workflow.md`; Direction Gate의 Design Philosophy → Direction/Contract, Core Freeze, L6 Reviewer contract, 현재 source/auth/schema, historical Fresh Session failure, exit1 diagnosis 순으로 확인했다.
- Source 변경은 `src/core/result_review_adapter.py`만이다. 기존 C4 budget mock 3개를 bytes로 맞춘 `tests/test_c4_review_budget.py`, 신규 focused `tests/test_reviewer_failure_observability.py`, 이 corrective의 신규 docs evidence만 추가했다. Generic logging/DLP subsystem, dependencies/config/model/effort/timeout/retry/prompt/schema/Session 변경은 없다.

## 결함 재확인과 구현

현재 source에서도 기존 subprocess는 `capture_output=True,text=True,encoding=utf-8,errors=replace`이며 실패 시 stdout/stderr SHA만 보존했다. 수정 전 synthetic process-started/exit1/empty-stdout/nonempty-stderr에서 `FAILED`와 읽을 수 있는 stderr 증거 부재를 재현했다. **REVIEWER_FAILURE_OBSERVABILITY_GAP** 확인이다. Historical exact root cause **UNKNOWN**과 diagnosis `TRANSIENT_REVIEWER_RUNTIME_FAILURE_SUPPORTED`를 강화하거나 재판정하지 않는다.

같은 `codex exec` argv, account auth, 반복 `-i` attachments, timeout과 한 번의 dispatch를 유지한다. Stdin은 이전 text-mode와 동일한 native newline translation 후 UTF-8 bytes로 전달하며 Windows의 기존 LF→CRLF 동작도 실제 local pipe로 대조했다. Subprocess를 bytes capture로 바꾸고 원본 byte 수/SHA를 먼저 확보한다. Result validation 및 기존 `stdout_sha256`/`stderr_sha256`에는 이전과 동일한 UTF-8 `errors=replace`와 universal newline 변환 후 문자열을 사용한다. Legacy hash를 raw hash로 재정의하지 않는다.

Invocation report와 함께 `<report filename>.stdout.txt`, `<report filename>.stderr.txt`를 `xb`로 write-once한다. 기존 result/report 및 새 evidence 경로가 존재하면 auth/process 전에 repeat를 거절한다. Report의 `stdout_evidence`/`stderr_evidence`는 다음을 연결한다.

- sanitized file path / bytes / SHA-256
- original captured `raw_bytes` / `raw_sha256`
- decoded / sanitized byte 수
- UTF-8 encoding, replacement 정책과 실제 decode loss 여부, newline normalization
- redacted / truncated, cap 65536 bytes, capture_complete
- 기존 review_id / request SHA / process_started / exit_code를 통한 invocation identity

Sanitizer는 credential 이름의 assignment/JSON string, authorization/Bearer/Basic, cookies/passwords, API-key/JWT 형태, URL credential, PEM private-key payload, credential 이름의 inherited environment 값 직접 출현을 deterministic하게 제거한다. Credential 파일은 읽지 않고, 출력에 나타난 payload만 처리한다. Raw secret text는 evidence 파일이나 report에 저장하지 않는다. Sanitization은 잘라내기 전에 전체 decoded capture에 적용하며, 저장은 UTF-8 문자 경계를 지킨 64 KiB prefix다. Full stdout은 cap과 별도로 Result 검증에 사용한다. Sanitizer는 이 Reviewer evidence를 위한 최소 pattern 정책이며 generic DLP를 도입하지 않았다.

exit1은 그대로 `FAILED`; exit0 valid PASS/REVISE/HUMAN_REQUIRED는 그대로 `SUCCESS`; invalid Result는 `FAILED`; timeout은 `UNRESOLVED`; launch failure는 process_started=false/FAILED다. Timeout의 부분 capture는 `capture_complete=false`로 명시해 전체 원본인 것처럼 보고하지 않는다. Evidence storage OSError는 예외 class만 `*_evidence_error`에 남기고, 실제 process 시작/exit/status를 바꾸지 않는다. 저장 실패까지 복구하는 lifecycle/retry를 추가하지 않았다.

## 검증

| 검증 | 결과 |
|---|---|
| focused observability | 17/17 PASS |
| 기존 Reviewer, Session/L6/L7 등 관련 회귀 | 225/225 PASS |
| full unittest | 261/261 PASS; failures/errors/skips0 |
| C-01 / I-03 | 10/10 / 7/7 PASS |
| Current Reference / Dimension Normalization | 18/18 / 13/13 PASS |
| 기존 C2 Reviewer / C4 budget | 12/12 PASS |
| binding-first / L6-first import smoke | 2/2 PASS |
| git diff --check / changed-surface review | PASS |

Bundled Python 3.12.14/Pillow를 사용했다. 기본 Python3.14에는 Pillow가 없어 관련 test import가 실패했고, dependency 설치나 환경 변경 대신 기존 bundled runtime으로 전환했다. 초기 focused 16개는 기본 Python에서도 통과했다.

필수 exit1/success/secret/empty/non-UTF8/historical-like/semantic preservation 외에도 UTF-8 cap, large valid stdout, identity rejection, timeout partial evidence, launch failure, collision/repeat guard, storage failure를 검증했다. 실제 local Python fixture subprocess는 UTF-8 stdin과 non-UTF8 stderr bytes pipe를 검증하며 production Reviewer가 아니다. Full suite audit: {"network": 0, "production_process": 0, "import_smoke_process": 1, "synthetic_pipe_process": 3}. 각 focused/related/full 검증의 network/production-process 시도0이며, import smoke와 synthetic local fixture만 allowlist로 허용했다. Optional Codex CLI diagnostic model request **0**. Actual Worker/ComfyUI/Blender/semantic Reviewer/correction/Delivery/Fresh Session retry **모두0**.

AST 비교에서 `digest`, `checked_ref`, `validate_request`, `validate_result`, `checked_invocation`, `main`은 동일하다. PASS/REVISE/HUMAN_REQUIRED의 Result bytes/hash와 checked invocation authority도 검증했다. C4 failure/timeout/launch/invalid 결과는 budget을 복원하거나 재시도하지 않는다.

## 보호와 한계

기준 tracked 664개 중 허용된 기존 파일2개 외 **662개 byte SHA 불변**. Protected manifest 전/후 SHA: `b2f7e9f6cab63854fe6b6b8be56bf3081e6763752a2e4c80123109234b13c9eb`. 기존 local refs/tags **19개 불변**. Historical actual Reviewer의 외부 이미지4개는 기록된 SHA와 일치한다. 기존 S3B/S3C, actual Loop/Delivery, Fresh Session failure proof, exit1 diagnosis, Frozen Core의 unrelated source/schema/auth/config, C-01/I-03/Reference/Normalization은 변경하지 않았다.

`FAILED / REVIEW_STAGE`, Fresh Session `NOT VERIFIED`, historical exact root cause `UNKNOWN`은 유지한다. I-01/I-02는 미수정 범위 밖의 부채다. 이 corrective는 semantic Reviewer reliability 개선, root cause 발견, actual Session E2E, 자동 retry 또는 User Delivery proof를 주장하지 않는다. 새 Fresh Session proof를 자동 실행하지 않았다.

상세 계수와 hashes: `VALIDATION.json`. 테스트 증거: `focused.log`, `related.log`, `full.log`.
