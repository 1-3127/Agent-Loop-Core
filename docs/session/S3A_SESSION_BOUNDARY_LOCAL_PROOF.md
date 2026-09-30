# S3A Session Boundary Local Proof

## Scope

**S3A SESSION BOUNDARY PRIMITIVE = IMPLEMENTED / LOCAL-VERIFIED**.

Session boundary의 typed records, validation, hash/identity binding과 terminal guards에 대한 **local fixture contract proof**다. Scenario 실행이나 실제 User Delivery proof가 아니다. 지정된 신규 파일4개만 추가했다.

Authority를 요청 순서로 읽었다: [S1 Contract](S1_SESSION_CONTRACT_v0.md), [Specification Template](S1_WORK_SPECIFICATION_TEMPLATE_v0.md), [Handoff Template](S1_SESSION_HANDOFF_TEMPLATE_v0.md), [S2 Audit](S2_SESSION_INTEGRATION_SEAM_AUDIT.md), [Direction Gate](../Agent-Loop_Direction_Gate_v1.md), [Core Freeze](../../CORE_V1_FREEZE.md).

## Baseline

| Item | Verified |
|---|---|
| Repository | D:\VSCODE-WorkSpace\Others\Agent-Loop-Core |
| Remote | https://github.com/1-3127/Agent-Loop-Core.git |
| Start branch | session-integration-s2 |
| HEAD / tracking / live remote | acf69d8cff633e046bfb364aed8d101dc620c1b5 |
| Parent S1 | ba04e8c127c92163f686cd07695ae3e16d8c11cc |
| S2 diff from S1 | docs/session/S2_SESSION_INTEGRATION_SEAM_AUDIT.md 신규1개만 |
| Start working tree | clean |
| main / origin/main / core-v1.0.0 target | 7eee393801f4d8c14278b43ebcbaabaec7ccc9df |
| Annotated tag object | 8b962c5d94828af852d020237554606c305ef01e |
| scenario-a-l6 / origin / live remote | 840b138cc023c623108c44c3944948b065300f99 |
| scenario-a-l7 / origin / live remote | 1da2bef094d2cc3f4bd70bbc266d99dc955460bb |
| S3A branch | exact S2 HEAD에서 session-boundary-s3a 신규 생성 |
| Instructions | root/Others/repo AGENTS.md, Agents/workflow.md |

신규 branch가 local/remote에 없음을 확인했다. main/S1/S2/L6/L7/tag를 움직이지 않았다.

## Implemented Primitive

| New file | Role |
|---|---|
| [src/session/__init__.py](../../src/session/__init__.py) | single src import root의 local package |
| [src/session/session_boundary.py](../../src/session/session_boundary.py) | typed records, freeze/binding/context/evidence validation, single Session write-once guard |
| [tests/test_session_boundary.py](../../tests/test_session_boundary.py) | T1–T16 및 negative cases, temp-file fixtures |
| docs/session/S3A_SESSION_BOUNDARY_LOCAL_PROOF.md | 본 proof와 한계 |

주요 API: freeze_specification, build_startup_context, file_identity, SessionBoundary.create_binding / internal_accept / prepare_delivery / record_submission / stop_for_ambiguity / stop / assert_open / register_child_evidence.

register_child_evidence는 caller evidence reference를 기록할 뿐 Worker/child callable을 실행하지 않는다. 기존 L6의 exclusive-open → flush → fsync 패턴을 read-only로 조사했고, 독립 generic utility가 없어 작은 local helper를 사용했다. Frozen Core/Scenario import0, dependency0. CLI/service/DB/registry/graph/manager/resume engine 없음.

## Specification Freeze

입력은 dialogue에서 이미 확정한 S1 Specification document와 명시적 FinalizedFields projection이다. 자연어/Markdown을 자동 해석하지 않고 기존 문서를 rewrite하지 않는다.

Projection은 session_id/version, supported request_type, explicit bool readiness, typed blocking ambiguities, criteria/authority refs, 최소 interpretation envelope를 가진다. SpecificationRef는 document regular-file 존재/가독성과 SHA-256, absolute path, session/version을 고정한다.

FrozenSpecification.identity_sha256은 document reference와 **전체 finalized projection**의 canonical JSON hash다. projection은 document를 대체하지 않는다. frozen dataclasses 및 tuple로 criterion description/authority/blocking flag를 immutable하게 보존한다.

Ready=false 또는 blocking ambiguity가 있는 ref는 기록용으로 freeze 가능하다. require_ready validation과 binding constructor는 이를 거절한다. 같은 path의 document bytes가 변경되면 기존 ref/binding validation은 SPECIFICATION_CONTENT_CHANGED로 실패한다. 문서와 projection의 semantic fidelity는 caller 확정 책임이다.

## Binding Contract

SessionRunBinding은 FrozenSpecification, 별개의 logical loop_run_id, fixed scenario_a를 포함한다. constructor 및 create_binding은 document hash, readiness, ambiguity 부재, unique criteria/authorities, declared authority membership, required values를 검증한다.

session_id == loop_run_id, unsupported Scenario, 다른 Session의 binding을 거절한다. criterion/authority/envelope는 내부 FrozenSpecification에 보존되고 canonical binding hash에 포함된다.

Caller가 정한 하나의 stable Session record directory에 session.json 및 binding.json을 exclusive write한다. 같은 directory의 다른 Session identity는 거절한다. 기존 binding은 loop ID/criteria를 바꾸어 overwrite할 수 없다.

이 binding은 계약이지 execution proof가 아니다. Scenario budget/capability/child routing은 S3B 이후 별도 연결 대상이다.

## Acceptance Criterion Authority

AcceptanceCriterion은 criterion_id, authority_ref, blocking_when_unmet(bool), description을 보존한다. AuthorityReference는 reference_id/source_ref를 연결한다. duplicate IDs, blank/undeclared authority, malformed bool을 거절한다.

Binding hash에 description과 authority source가 포함된다. INTERNAL_ACCEPT는 binding file hash, canonical identity, criterion IDs와 artifact/final evidence를 연결한다. non-blocking criterion도 false로 보존한다.

향후 Reviewer blocker의 authority trace에 필요한 identity만 고정했다. Reviewer semantic correctness, criterion coverage 및 실제 품질은 검증하지 않는다.

## Durable Context Selection

build_startup_context는 Current Request → Current References → 명시적 durable selection 순서의 immutable tuple을 반환한다. references의 내용을 자동 읽지 않는다.

Allowlist: CURRENT_REQUEST, CURRENT_REFERENCE, PREVIOUS_SPECIFICATION, DELIVERED_ARTIFACT, USER_FEEDBACK, VERIFIED_FACT, EXECUTION_RESULT, KNOWN_FAILURE, FINAL_DECISION, UNRESOLVED_ISSUE, ENVIRONMENT_STATE, EVIDENCE_REFERENCE, ARCHIVE_REFERENCE.

CHAIN_OF_THOUGHT, THOUGHT_TRAJECTORY, RAW_SPECULATION, ACTIVE_REASONING_STATE, HYPOTHESIS_CHRONOLOGY 및 unknown category를 거절한다. durable selection으로 Current Request/References를 대신 넣는 것도 거절한다.

Archive는 reference만 허용하며 content를 자동 startup injection하지 않는다. category만 검사하고 내용이 사고 흐름인지 semantic하게 분류하지 않는다. relevance/category truth는 caller 책임이다.

**selected input contract만 검증하며 external host가 실제 fresh context를 제공했는지는 증명하지 않는다.** Chat/process/context reset을 실행하지 않고 FRESH_CONTEXT_VERIFIED status도 만들지 않았다.

## Session Outcomes

| Local outcome | Gate / meaning |
|---|---|
| REQUEST_RECEIVED | owner record만 존재 |
| LOOP_READY | Ready binding이 기록됨; actual execution 아님 |
| INTERNAL_ACCEPT | caller의 내부 제출 가능 선언과 identity 기록; delivered=false |
| BLOCKED_SPECIFICATION_AMBIGUITY | typed ambiguity + relevant SpecificationRef terminal |
| FAILED / ABORT | caller-defined failure/stop reason으로 terminal |
| DELIVERED → CLOSED | matching external submission evidence 구조 gate 후 terminal record에 두 단계를 기록; outcome은 CLOSED/delivered=true |

SpecificationAmbiguity는 description, artifact/result impact, context insufficiency 및 optional alternatives를 검증한다. alternatives가 있으면 서로 다른 해석 최소2개를 요구한다. technical uncertainty/HUMAN_REQUIRED를 자동 변환하지 않는다.

Binding 전 unresolved Spec로 stop 가능하며, binding 후에는 같은 frozen Spec를 요구한다. clarification은 향후 새 Request/Session input이다.

SessionOutcome은 immutable read-only view다. 임의 status constructor로 DELIVERED/CLOSED를 만들 수 없고 stop()도 두 status를 거절한다.

## INTERNAL_ACCEPT / Delivery Boundary

Fixture flow: completed Spec+fields → freeze → binding → fixture artifact/review → INTERNAL_ACCEPT → Delivery Package → fixture structured external evidence → local DELIVERED/CLOSED.

INTERNAL_ACCEPT에는 Spec ref, loop ID, binding file/canonical hash, criterion IDs, artifact path/bytes/hash, final review/evidence와 해당하는 initial refs가 연결된다. internal_accept는 caller acceptance declaration의 identity gate이며 semantic quality judge가 아니다.

prepare_delivery는 INTERNAL_ACCEPT가 없으면 실패한다. accept/binding/document/artifact/evidence hash를 다시 검사한다. package는 Spec/loop/artifact/initial references/final evidence/accept identity를 보존하며 visual Input+Output와 승인 / 자연어 피드백 / 사용하지 않음 요청을 presentation contract로 담는다. 실제 제시는 하지 않는다.

SubmissionEvidence: delivery_package_sha256, specification_sha256, artifact_sha256, receipt_id, observed_channel, timezone가 있는 observed_timestamp, provenance_ref.

record_submission은 matching package path/identity/hash, accept lineage, Spec/artifact hashes, structured receipt를 검증한다. submitted=true 하나, missing evidence, mismatched hashes, blank receipt/channel/provenance, malformed timestamp를 거절한다. User approval은 필요하지 않다.

Terminal verification_scope: LOCAL_CALLER_SUPPLIED_EVIDENCE_CONTRACT_ONLY. **Caller evidence 구조의 유효성만 검증한다. 실제 Chat/UI/host가 제출했다는 사실을 module/fixture가 관측했다고 주장하지 않는다.** real receipt authenticity/provenance 관측은 미확인이다.

## Terminal Guards

session.json, binding.json, internal_accept.json, delivery_package.json, terminal.json 및 optional child evidence는 write-once다. terminal.json 존재를 모든 mutation 앞에서 확인한다.

terminal 이후 binding 생성, child evidence 등록, accept 변경, package/submission 재기록, stop 변경, assert_open은 ALREADY_TERMINAL로 거절한다. 같은 directory의 새 handle에서도 guard가 유지된다. T14는 모든 재진입 후 record bytes/terminal hash 불변을 확인한다.

INTERNAL_ACCEPT 이후에도 새 binding/child registration/accept replacement를 차단한다. T16은 feedback을 새 Request/Session input으로 사용하고 old terminal 불변을 확인한다. 자동 Session execution/resume은 없다.

Guard 범위는 caller-retained stable directory와 single-process local API다. records를 외부에서 삭제/위조하거나 다른 directory로 identity를 복제하는 것을 방어하는 global registry/tamper-proof store가 아니다. concurrency/comprehensive recovery는 구현하지 않았다. partial write는 정상 proof로 재분류하지 않는다.

## Test Evidence

Runtime: bundled Python 3.12.14. 기존 tests 수정0. repo 내 TemporaryDirectory에서 fixtures만 생성하고 종료 시 정리했다.

아래 runner를 PowerShell here-string으로 bundled python.exe -B -에 전달했다. focused에서는 pattern을 test_session_boundary.py로 바꿨다. 기존 package test의 정확한 Python import-only command만 Windows string/list 양쪽으로 허용한다.

```python
import ast,pathlib,subprocess,sys,tempfile,unittest
root=pathlib.Path.cwd();sys.path.insert(0,str(root/'src'))
effects={'network':0,'production_process':0,'import_smoke_process':0}
tree=ast.parse((root/'tests/test_package_boundary.py').read_text(encoding='utf-8'))
smoke_script=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='script' for t in n.targets))
smoke_args=[sys.executable,'-c',smoke_script]
smoke_command=subprocess.list2cmdline(smoke_args)
def gate(event,args):
 if event in ('socket.connect','socket.connect_ex','urllib.Request'):
  effects['network']+=1
  raise AssertionError('S3A actual network forbidden')
 if event=='subprocess.Popen':
  command=args[1]
  if command==smoke_command or command==smoke_args:
   effects['import_smoke_process']+=1
  else:
   effects['production_process']+=1
   raise AssertionError('S3A actual production process forbidden')
sys.addaudithook(gate)
with tempfile.TemporaryDirectory(prefix='s3a-local-tests-',dir=root) as scratch:
 tempfile.tempdir=scratch
 suite=unittest.defaultTestLoader.discover('tests',pattern='test_*.py')
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 print('EXTERNAL_EFFECT_TRIPWIRES',effects)
 print('COUNTS',result.testsRun,len(result.failures),len(result.errors),len(result.skipped))
 sys.exit(0 if result.wasSuccessful() and not effects['network'] and not effects['production_process'] else 1)
```

| Suite | Result | Failures / Errors / Skips |
|---|---|---|
| Focused new tests | 23/23 PASS | 0 / 0 / 0 |
| Full existing + new unittest | 172/172 PASS (238.079 seconds) | 0 / 0 / 0 |

| Requirement | Test evidence |
|---|---|
| T1 | Ready freeze/binding PASS |
| T2 | Not Ready binding/constructor reject, binding file0 |
| T3 | Ready 표시에도 blocking ambiguity reject |
| T4 | same-path document mutation reject |
| T5 | session/loop 분리, equal IDs reject |
| T6 | duplicate criterion IDs reject |
| T7 | blank/undeclared authority reject |
| T8 | durable refs/order PASS; archive content loading0 |
| T9 | transient/unknown categories reject |
| T10 | immutable criteria + accept lineage; delivered=false |
| T11 | no receipt/dummy flag/direct Delivery constructor reject |
| T12 | fixture/local matching evidence → DELIVERED/CLOSED; User approval 불필요 |
| T13 | package/spec/artifact mismatch reject |
| T14 | same-directory new handle도 terminal 재진입 reject; bytes/hash 불변 |
| T15 | typed ambiguity Session terminal + Spec linkage |
| T16 | feedback은 new Session input; old terminal 불변 |

추가7개 tests: invalid projection/document, ambiguity structure/no classifier, write-once binding, artifact/review/package mutation, FAILED/ABORT/premature delivery, receipt namespace/timestamp, no execution/Core/Scenario import.

실행 중 문제를 숨기지 않는다:

1. 최초 sandbox attempt는 temp directory 생성 전에 진행이 멈춰 완료되지 않았다. 해당 Python path/parent PID를 확인해 종료했고, 쓰기 권한을 확보하여 같은 fixture runner로 다시 실행했다. PASS로 세지 않는다.
2. 첫 full run은 172개 중171개 PASS, import-smoke1개 실패였다. Windows audit event가 command line을 string으로 전달해 runner의 list-only allow rule에 걸렸다. child process는 시작되지 않았다. guard의 정확한 command comparison만 수정하고 full suite를 재실행했다. source/기존 tests 수정0.

Focused tripwires: network0 / production process0 / import-smoke process0.
Final full tripwires: network0 / production process0 / import-smoke process1.
Mock Worker/Reviewer invocations는 actual effects로 세지 않는다.

## External Effects

| Actual effect | Count |
|---|---|
| Worker execution | 0 |
| Comfy submission | 0 |
| Blender process | 0 |
| semantic Reviewer | 0 |
| revision dispatch | 0 |
| User delivery transport | 0 |

요청된 Git commit/push는 repository 게시 행위이며 artifact User Delivery proof가 아니다. Full suite의 Python import-smoke child도 Worker/Blender/Reviewer가 아니다.

## Known Unverified Boundaries

- Scenario A integration NOT STARTED.
- actual User Delivery NOT VERIFIED.
- external fresh-context reset NOT VERIFIED.
- L7 closed-feedback NOT VERIFIED.
- actual Session E2E, Reviewer criterion semantics/quality, real receipt authenticity는 미검증.
- document/projection semantic fidelity 및 typed category의 진실성은 caller 확정 책임.
- stable directory 밖의 global identity/recovery/concurrency는 미구현.

## Protection

- 기존 tracked files235개 시작/종료 SHA-256 동일, 변경0. Core/C1–C5/L6/L7/기존 tests/S1/S2/runs/evidence 포함.
- Research HEAD 7e1572a7e35866519b75b767398288396a27f9b0.
- Research tracked files+F2B WIP186개 hash 동일, 변경0. sole untracked ac6_f2b_resume.py SHA-256 2a58ab64e8838e8c3da6d8b4d62526e1a8d0d834bb26058d905d80d73dfd9369 유지. Research commit/push0.
- L6 manifest external asset18개 size/mtime 및 작은 파일 hash 동일. 대형 model 전체 hash는 측정하지 않음.
- main/S1/S2/L6/L7 refs와 frozen tag object/target 유지.
- src/core / src/scenario_a / 기존 test diff0.
- 신규 허용 파일4개 외 unexpected diff0. tests scratch paths는 정리됨.

정상 S3A commit/push 후 local HEAD == origin/session-boundary-s3a == live remote 및 clean을 확인하여 STOP한다. main merge/tag/release 없음.

## Final Status

```text
AGENT LOOP CORE V1.0.0 = FROZEN / UNCHANGED
LEVEL 6 MULTI-STAGE SUPERVISED PIPELINE = VERIFIED
L7-M0 MANDATORY GATE = PASS
L7-M1 GEOMETRY REVIEW BRIDGE = VERIFIED
L7-M2 MINIMAL FEEDBACK CONTROLLER = READY
L7-M3 ACTUAL CLOSED FEEDBACK PROOF = NOT PASSED
L7-R1 GEOMETRY REVISION DIAGNOSIS = COMPLETE
S1 SESSION / REQUEST / WORK SPECIFICATION CONTRACT = COMPLETE
S2 SESSION INTEGRATION SEAM AUDIT = COMPLETE
S3A SESSION BOUNDARY PRIMITIVE = IMPLEMENTED / LOCAL-VERIFIED
S3B SCENARIO BINDING = NOT STARTED
ACTUAL SESSION E2E = NOT VERIFIED
ACTUAL USER DELIVERY RECEIPT = NOT VERIFIED
EXTERNAL FRESH-CONTEXT RESET = NOT VERIFIED
LEVEL 7 CLOSED FEEDBACK PIPELINE = NOT VERIFIED
HYPOTHESIS BENCHMARK = NOT STARTED
```
