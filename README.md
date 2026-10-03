# Agent-Loop-Core — Ponytail reconstruction

Python Core와 local stdio MCP로 구성한 독립 active tree다. Specification은
`RECONSTRUCTION_SPECIFICATION.md`, 구현 전 전수점검은 `RECONSTRUCTION_SPECIFICATION_AUDIT.md`에 있다.
현재 branch는 `ponytail-reconstruction-codex`, 비클라우드 출발 commit은
`12366d9f2e377cfda898790f65c5033306905a99`다. 과거 proof와 실패 판단은 `HISTORY.md`의 immutable refs에 보존한다.

## 구조

- `app/loopcore/core.py`: Session/grant ledger, frozen authority, Artifact/Skill/Workflow, budget/lineage/acceptance/terminal guards.
- `host.py`: Codex User provenance, trusted grant inbox, allowed paths, verified local handoff.
- `models.py`: 독립 Frontier/Reviewer inference. 요청 model과 실제 관측 identity를 구분.
- `tools.py`, `blender_diagnostic.py`: Tool-native ComfyUI 경로, current Reference, fresh-import diagnostics 및 read-only source discovery.
- `runtime.py`: Host가 concrete ports를 조합하는 bounded loop. Core에는 Domain/model/transport 분기 없음.
- `mcp_server.py`, `__main__.py`: MCP와 local CLI entry.
- `knowledge/`: candidate Skills 및 native binding 예시. 실제 성공 attestation이 아니다.

## 설치와 부작용 없는 Smoke

프로젝트 Root에서 실행한다. 구성 경로는 `config/local.json`에 있으며 Tool 경로를 임의 이동하지 않는다.

```powershell
uv venv .venv --python C:\Python314\python.exe
uv pip install --python .venv\Scripts\python.exe -e .
.venv\Scripts\python.exe -m loopcore --config config/local.json smoke
```

Smoke는 import/config/catalog bootstrap만 확인한다. ACTUAL Session, CLI inference, ComfyUI prompt 및 Blender 실행을 시작하지 않는다.
Frontier/Reviewer는 각각 `gpt-6.1-sol` / `low`를 명시한다. `.codex/config.toml`의 현재 Host 설정과 독립적이다.

## MCP 연결

`config/codex-mcp.example.toml`은 Host 등록 예시다. 이번 개발 중 현재 Host에 자동 설치하지 않는다.
다른 Host도 같은 stdio launch command를 사용할 수 있다. concrete provenance issuer는 해당 Host가 제공한다.

```powershell
.venv\Scripts\python.exe -m loopcore --config config/local.json mcp
```

MCP tools: `loop_start`, `loop_advance`, `loop_status`, `loop_clarify`, `loop_recover`, `loop_deliver`, `loop_retention`.
grant 발급은 MCP와 모델 port 밖의 trusted Host 동작이다. 표준 protocol 자료는 [공식 MCP SDK](https://py.sdk.modelcontextprotocol.io/run/)를 참고한다.
긴 Tool 수행에는 Host timeout 설정이 필요하다. 한 advance는 하나의 Frontier 판단과 선택한 하위 동작을 수행한다.

## 실제 Session 시작 — 공동 검증 단계에서만

1. 실제 User Request/Reference와 별도 명시적 Session start 허가를 확보한다. 개발 완료나 같은 대화는 허가가 아니다.
2. Host가 original Request/Reference를 허용된 immutable 입력 경로에 보존한다. trusted inbox는 하위 실행체에 write 권한을 주지 않는다.
3. Host가 실제 Codex User record의 immutable snapshot과 evidence `{file:{path,sha256,bytes}, line, text}`를 보존한다.
   full transcript/hidden reasoning을 복사하지 말고 해당 User record만 snapshot한다. User origin 확인만으로 consent를 자동 추론하지 않는다.
4. trusted Host가 해당 직접 메시지의 Session 시작 허가를 판단한 후 `LocalHost.issue_grant(...)`를 호출한다.
   Host CLI는 `issue-grant ... --host-confirmed-explicit-user-start`를 제공하며, 해당 flag는 trusted Host의 결정이다.
   untrusted model이 자체 발급하도록 노출하지 않는다. Core는 issuer/binding/ledger만 검증한다.
5. `loop_start`로 기존 grant를 소비한다. `loop_advance`를 반복하며 필요한 dialogue 질문은 Host가 User에게 전달한다.
   응답은 `.local/host/clarifications/<receipt-id>.json`의 검증된 User evidence와 response ref로 연결한다.
6. freeze 후 Frontier가 Skill/Workflow를 구성하고 Worker/Reviewer를 호출한다. ComfyUI segmentation도 Core Workflow 내부 Tool/Skill이다.
7. `ACCEPTED` 후 Host가 허용된 새 delivery directory로 export하고 원본과 최종 산출물을 User에게 제시한다.
   local hash 확인은 User 실제 수신/품질 승인과 다르다. 전달 실패 terminal에는 미전달 refs 안내가 필요하다.

## 복구와 종료 정리

비종료 상태의 중단만 같은 Session에서 복구한다. 하위 Tool의 receipt/history를 Frontier가 관측할 수 있고,
Frontier 또는 그 위 중단은 Host가 판단한다. `loop_status`의 pending/unresolved를 확인한 후
trusted inbox `.local/host/recovery/<id>.json`에 `{session_id,owner:"HOST",reason,action,ticket_id}`를 기록한다.
action은 `OBSERVE_TOOL`, `OBSERVE_MODEL`, `CLEAR_HOST_REQUEST`, `STOP` 중 하나다. 정확한 원래 effect 결과만 관측하며 재호출하지 않는다.
같은 Session에서 Goal 변경/새 grant 발급/terminal 재실행은 허용하지 않는다.

Session 끝의 Core 기본 보존 목록을 Frontier의 정리 제안과 함께 `loop_retention`으로 결정한다.
active authority, 현재/최종 산출물, Review/Decision 및 dependency는 보호한다. 정리 대상은 소유된 불필요한 TRANSIENT만 허용하며
apply 시 삭제 대신 Session 안의 `retired/`로 옮겨 복구 경로를 보존한다. 공유 Tool outputs/models나 User originals는 정리하지 않는다.

## 검증 상태

이번 reconstruction 중에는 Smoke만 수행한다. 실제 Scenario A 품질, actual model identity,
delivery, arbitrary interruption recovery, 다른 Host/Domain 및 lower Frontier의 자원 절감은 사용자 공동 검증 대상으로 남는다.
candidate Skill이나 binding 예시, import 성공을 actual proof로 해석하지 않는다.
