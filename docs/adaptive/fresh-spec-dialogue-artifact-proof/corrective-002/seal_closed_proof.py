from pathlib import Path
import json,hashlib,sys,datetime,subprocess
from dataclasses import asdict
ROOT=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
BASE=ROOT/'docs/adaptive/fresh-spec-dialogue-artifact-proof'
P=BASE/'fresh-002'
O=Path(r'C:\Users\Worker\Documents\Codex\2026-10-02\codex-specification-dialogue-human-blocking-text\outputs\fresh-spec-dialogue-artifact-proof\fresh-002')
WORK=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from core.event_logging import reconstruct
from core.skill_artifact import write_once,SkillRef,validation_status
from session.session_boundary import FileIdentity,file_identity
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(data)
def jput(p,d):put(p,json.dumps(d,ensure_ascii=False,indent=2).encode('utf-8'))
actual=read(P/'ACTUAL_RESULT.json');terminal=read(P/'session/terminal.json')
assert actual['status']==terminal['status']=='CLOSED' and actual['INTERNAL_ACCEPT'] and actual['delivered']
b=read(P/'BASELINE_GATE.json')
assert all(sha(ROOT/n)==h for n,h in b['tracked_file_sha256'].items())
assert all(subprocess.check_output(['git','rev-parse',n],cwd=ROOT,text=True).strip()==h for n,h in b['protected_refs'].items())
refs={}
def visit(value):
    if isinstance(value,dict):
        if set(value)=={'identity','path','bytes','sha256'}:
            r=FileIdentity(**value);r.validate();refs[(r.path,r.sha256)]=value
        for v in value.values():visit(v)
    elif isinstance(value,list):
        for v in value:visit(v)
for p in P.rglob('*.json'):
    if p.name!='BASELINE_GATE.json':visit(read(p))
events=reconstruct(P/'session/logs',actual['session_id']);assert len(events)==actual['event_count']
prior={p.relative_to(P).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in P.rglob('*') if p.is_file()}
copyroot=O/'delivery/evidence'
differences=[];missing=[]
for n,e in prior.items():
    target=copyroot/n
    if not target.exists():missing.append(n)
    elif sha(target)!=e['sha256']:differences.append({'path':n,'pre_close_snapshot_sha256':sha(target),'closed_source_sha256':e['sha256']})
assert len(differences)==1 and differences[0]['path']=='session/logs/event_index.jsonl'
final=O/'delivery/railing-and-concrete-base.glb'
gate=read(P/'session/acceptance_gate.json')
artifactmeta=read(Path(gate['final_artifact_ref']['metadata']['path']))
assert sha(final)==artifactmeta['files'][0]['sha256']
failure={'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'POST_CLOSE_OUTPUT_EVIDENCE_HOST_DEFECT','error':'AssertionError: OUTPUT_SNAPSHOT_CHANGED','internal_accept':True,'terminal':'CLOSED','delivered':True,'session_resumed':False,'proof_package_integrity':'FAILED','differences':differences,'missing_from_incomplete_package':missing,'cause':'Pre-close evidence snapshot copies append-only event_index; LOCAL_HANDOFF_CLOSED then changes source before final snapshot','required_next':'Preserve CLOSED Session and incomplete package exactly; minimal host fix, focused/related/full regression, checkpoint normal push, equality/clean, then fresh Original Request/Reference intake; do not auto reuse terminal-session clarification'}
jput(P/'POST_CLOSE_HOST_FAILURE.json',failure)
reviews=[read(p) for p in sorted(P.glob('session/production_runs/*/attempts/*/review*/review.json'))]
decisions=[read(p) for p in sorted(P.glob('decisions/*/decision.json'))]
executions=[read(p) for p in sorted(P.glob('session/production_runs/*/attempts/*/execution-*/execution_report.json'))]
intake=read(P/'INTAKE_RESULT.json');wait=read(P/'intake/round-001/DIALOGUE_STATE.json')
dims={k:'PASS' for k in ['A Specification Dialogue','B Actual User wait','C User clarification binding','D Work Specification','E Frontier planning','F actual Skill/Workflow execution','G production Artifact lineage','H Independent Reviewer','I Frontier decision lineage','K INTERNAL_ACCEPT / CLOSED']}
dims.update({'J Adaptive Attempt/Run':'Local Attempt correction EXERCISED; actual multi-run adaptation = NOT EXERCISED','L Deliverable creation':'Final GLB/preview delivered locally, but complete output/evidence package FAILED','M Regression/integrity':'Historical bytes/refs PASS; final package integrity FAILED; correction regression pending'})
record={'proof_name':'FRESH_SPEC_DIALOGUE_TO_ARTIFACT_E2E_PROOF','dimensions':dims,'01_new_request':{'text':(P/'authority/ORIGINAL_REQUEST.txt').read_text(encoding='utf-8'),'ref':intake['request_ref']},'02_new_reference':intake['reference_ref'],'03_frontier_intake':[str(p) for p in sorted(P.glob('intake/round-*/invocation/invocation.json'))],'04_detected_ambiguity':wait['detected_decisive_ambiguities'],'05_actual_question':wait['clarification_question'],'06_actual_user_response':{'text':(P/'authority/USER_RESPONSE_001.txt').read_text(encoding='utf-8'),'ref':intake['clarification_ref']},'07_binding':read(P/'authority/AMBIGUITY_RESOLUTION_BINDING.json'),'08_frozen_specification':intake['specification'],'09_resource_envelope':actual['resource_usage'],'10_workflow_skills':{'workflow':read(P/'workflows/workflow-001.json'),'skills':actual['skill_refs']},'11_run_attempt_chronology':{'runs':1,'attempts':2,'execution_reports':executions},'12_actual_worker_effects':read(P/'FINAL_EFFECT_COUNTERS.json'),'13_artifacts':[read(p) for p in P.glob('session/production_runs/*/artifacts/*.json')],'14_reviews':reviews,'15_frontier_decisions':decisions,'16_adaptation':{'workflow_revision':0,'restart':0,'local_correction':1,'actual_multi_run_adaptation':'NOT EXERCISED'},'17_final_artifact':asdict(file_identity(final,'delivered-railing-and-base')),'18_terminal':terminal,'19_delivery_package':{'path':str(O/'delivery'),'status':'INCOMPLETE_EVIDENCE_PACKAGE','defect':failure},'20_skill_validation_records':[read(p) for p in P.glob('skill-validation-*.json')],'21_regression':'Corrective-001 focused/related72/full326 PASS; corrective-002 snapshot fixture PASS; related/full pending','22_git':{'branch':b['branch'],'pre_proof_head':'192f793e7a58655478cf6ffcd4d9d31b0ac6f53c','checkpoint_push':'pending correction regression'},'23_preserved_failures':{'prior_session':'fresh-spec-dialogue-artifact-001 FAILED','current_unfrozen_draft':'round-002 technical validation rejected before freeze','worker_attempt_001':'Code guard rejected before Blender','post_close_host_failure':failure},'24_known_limitations':actual['known_limitations']+['Output package event_index contains pre-close state; two final records missing; do not claim package integrity PASS'],'25_human_judge':'NOT PERFORMED; internal semantic acceptance is true, human quality judgment remains outside CLOSED Core Session','bound_refs_verified':len(refs),'events_verified':len(events),'historical_integrity':{'baseline_files':len(b['tracked_file_sha256']),'protected_refs':len(b['protected_refs'])}}
jput(P/'CLOSED_PROOF_REPORT.json',record)
report='''# Fresh-002 — semantic CLOSED, post-close package host defect

**INTERNAL_ACCEPT=true / CLOSED / local final GLB delivered. Complete evidence package integrity FAILED.**

사용자 범위는 난간·콘크리트 받침 포함, 연석·양옆 노란 사슬 제외다. Actual intake가 범위 ambiguity를 탐지했고 실제 응답 전 production effects=0으로 기다렸다. 이번 응답 원문·hash를 frozen criteria에 바인딩했다.

미동결 초안의 기술 budget/ref gate 실패를 보존하고 actual Frontier technical refinement 후 명세를 freeze했다. Run 1 / Attempts 2 / Worker 2 / independent Reviewer 1 / Blender production 2 / ComfyUI 0 / ArtifactStore 1이다. 첫 Worker는 코드 guard에서 거부되어 Blender를 실행하지 않았다. Actual Frontier가 같은 Run에서 국소 수정 Attempt를 선택했고 두 번째 Worker는 GLB를 생성했다. Independent Review에서 C01–C07 모두 MET; actual Frontier ACCEPT 후 local handoff/CLOSED였다. Actual multi-run adaptation = NOT EXERCISED.

Close 전 evidence snapshot을 복사한 뒤 LOCAL_HANDOFF_CLOSED를 event_index에 추가하여, 최종 snapshot이 이전 복사본과의 해시 충돌로 중단됐다. Core semantic outcome을 FAILED로 바꾸거나 Session을 reopen하지 않았다. Final GLB와 preview는 accepted/delivered 파일이며, 최종 package integrity PASS는 주장하지 않는다. Pre-close event_index 복사본과 post-close source 원문을 둘 다 보존한다.

수정은 pre-close snapshot 호출 한 줄 삭제다. 별도 synthetic fixture에서 collision 재현 및 post-close 단일 snapshot의 exact-byte 복사를 검증했다. 사용자 protocol section 13에 따라 related/full regression, checkpoint/normal push/equality/clean 후 Original New Request/Reference로 새 actual intake를 시작한다. 현재 terminal Session의 clarification/spec/artifact/review를 새 authority로 자동 재사용하지 않는다.

`CLOSED_PROOF_REPORT.json`에 A–M 판정과 1–25 필수 항목, actual effects/decisions/reviews/hash/lineage를 보존했다. Human Judge는 미수행이며 이미 CLOSED인 Session 밖의 품질 평가다.
'''
put(P/'CLOSED_PROOF_REPORT.md',report.encode('utf-8'))
jput(P/'CLOSED_PROOF_SEAL.json',{'terminal':'CLOSED','internal_accept':True,'delivered':True,'package_integrity':'FAILED','sealed_original_files':prior,'original_bytes_unchanged':all(sha(P/n)==e['sha256'] for n,e in prior.items()),'same_terminal_session_resumed':False,'clarification_auto_reuse':False,'bound_refs_verified':len(refs),'events':len(events)})
for p in P.rglob('*'):
    if p.is_file():put(O/'preserved-closed-proof'/p.relative_to(P),p.read_bytes())
print(json.dumps({'sealed':True,'terminal':'CLOSED','internal_accept':True,'package_integrity':'FAILED','bound_refs':len(refs),'events':len(events),'final_artifact_sha256':sha(final)},ensure_ascii=False))
