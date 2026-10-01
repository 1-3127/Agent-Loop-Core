"""Close the same Session only after the actual current User receipt."""
import dataclasses, datetime, json, os, pathlib, subprocess, sys
ROOT=pathlib.Path('D:/VSCODE-WorkSpace/Others/Agent-Loop-Core')
WORK=pathlib.Path(__file__).resolve().parent
D=ROOT/'runs/session/psa-session-20261001-031107-2c54c2a3'
P=D/'delivery_proof'
sys.path.insert(0,str(ROOT/'src'))
from session import session_boundary as sb
from scenario_a import session_binding as bound, l6_pipeline as l6
USER_MESSAGE='Recived delivery-bc10c46a19d18566.\n외부 평가로는 승인: 글씨의 경우 직접 추가하여 사용하겠다. 펭귄 눈과 부리, 피켓을 들고 있는 손, 물갈퀴가 정상적으로 렌더링됐다.'
TOKEN='delivery-bc10c46a19d18566'
BASE='335051becf0f25601f1584a729c6e00e7302b203'
def git(*args):return subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),*args],cwd=ROOT,text=True,encoding='utf-8').strip()
def refs(text):return {b:a for a,b in (line.split() for line in text.splitlines())}
assert git('branch','--show-current')=='delivery-closure-post-stabilization'
assert git('rev-parse','HEAD')==git('rev-parse','@{upstream}')==BASE
assert not git('status','--porcelain=v1')
remote=git('ls-remote','origin','refs/heads/*','refs/tags/*')
assert refs(remote)['refs/heads/delivery-closure-post-stabilization']==BASE
tracked={p:l6.digest(ROOT/p) for p in git('ls-files').splitlines()}
local=git('show-ref')
phase='validation'
def audit(event,args):
    if event in ('subprocess.Popen','urllib.Request','socket.connect'):
        raise RuntimeError('DELIVERY_CLOSURE_NO_GENERATION_OR_TRANSPORT: '+event)
    if event=='open' and (isinstance(args[1],str) and any(c in args[1] for c in ('w','a','x','+')) or args[2]& (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
        p=pathlib.Path(args[0]).resolve()
        if phase!='record' or not (p.is_relative_to(P.resolve()) or p==(D/'terminal.json').resolve()):
            raise RuntimeError('DELIVERY_CLOSURE_WRITE_OUT_OF_SCOPE: '+str(p))
sys.addaudithook(audit)
ready=l6.read_json(P/'delivery_ready.json');before_gate=l6.read_json(P/'start_gate.json')
assert ready['receipt_token']==TOKEN and TOKEN in USER_MESSAGE
assert all(l6.digest(ROOT/p)==h for p,h in before_gate['tracked'].items())
assert not (D/'terminal.json').exists()
parent=l6.reference(D/'scenario_a.json')
data,boundary,binding=bound.checked_parent(parent)
assert boundary.outcome.status=='INTERNAL_ACCEPT' and not boundary.outcome.terminal and not boundary.outcome.delivered
accept=boundary._checked_accept()
package=sb.FileIdentity(**ready['package']);package.validate();payload=l6.read_json(package.path)
assert accept['artifact']==ready['accepted_artifact']==before_gate['artifact']
assert payload['artifact']==accept['artifact'] and payload['specification']==accept['specification']
assert payload['internal_accept']==ready['internal_accept'] and payload['final_review']==accept['final_review']
assert payload['initial_references']==accept['initial_references']
assert binding.specification.identity_sha256==before_gate['specification_identity_sha256']
for pair in ready['copy_lineage'].values():
    for name in ('original','copy'):sb.FileIdentity(**pair[name]).validate()
    assert pair['copy']['sha256']==pair['original']['sha256'] and pair['copy']['bytes']==pair['original']['bytes']
candidate=l6.read_json(D/'scenario_a_accept.json')
mandatory={c.criterion_id for c in binding.specification.fields.acceptance_criteria if c.blocking_when_unmet}
assert set(candidate['mandatory_criterion_ids'])==mandatory
for stage,ref in candidate['stage_coverage'].items():
    cov=l6.read_ref(ref)
    assert cov['verdict']=='PASS' and all(cov['coverage'][cid]=='SATISFIED' for cid in data['stage_criteria'][stage] if cid in mandatory)
assert candidate['artifact']['sha256']==accept['artifact']['sha256']
assert all(l6.digest(ROOT/p)==h for p,h in tracked.items())
phase='record'
start={'head':BASE,'branch':'delivery-closure-post-stabilization','clean':True,'local_tracking_live_equal':True,'tracked':tracked,'local_refs':local,'live_remote_refs':remote,'session_status':'INTERNAL_ACCEPT','terminal':False,'delivered':False,'accepted_artifact':accept['artifact'],'specification':accept['specification'],'mandatory_coverage_verified':True,'observed_at':l6.now()}
l6.write_once(P/'closure_start_gate.json',start)
with (P/'close_session_driver.py').open('xb') as f:f.write(pathlib.Path(__file__).read_bytes())
observed=l6.now()
ack={'source_kind':'DIRECT_CURRENT_USER_CHAT_MESSAGE','message_text':USER_MESSAGE,'receipt_token':TOKEN,'receipt_acknowledged':True,'literal_spelling_preserved':'Recived','observed_channel':'codex_chat_user_acknowledgement_after_final_delivery','observed_timestamp':observed,'timestamp_scope':'Executor observation of actual User acknowledgement; server message timestamp not exposed','host_message_id':None,'host_message_id_unavailable_reason':'No host/server message identifier is exposed for this current User turn','delivery_event':'Previous assistant final response supplied the GLB and Delivery Package links and original Input/current accepted geometry diagnostic; current User explicitly acknowledges the matching token','delivery_package':dataclasses.asdict(package),'artifact':accept['artifact'],'specification':accept['specification'],'session':boundary.session_id,'loop':binding.loop_run_id,'copy_lineage':ready['copy_lineage'],'authenticity_basis':'Actual human User message in the same ongoing Codex chat; not simulated, predicted, or fixture receipt','quality_approval_is_not_closure_requirement':True}
l6.write_once(P/'external_receipt_acknowledgement.json',ack)
ack_identity=sb.file_identity(P/'external_receipt_acknowledgement.json','external-user-receipt')
l6.write_once(P/'external_user_evaluation.json',{'source_receipt':dataclasses.asdict(ack_identity),'evaluation':'승인','literal_feedback':'글씨의 경우 직접 추가하여 사용하겠다. 펭귄 눈과 부리, 피켓을 들고 있는 손, 물갈퀴가 정상적으로 렌더링됐다.','scope':'External User evaluation, outside Core Run/Reviewer state','new_request':False,'old_loop_revise':False,'executor_artifact_modification':False,'note':'User will add lettering themselves; no additional work or fresh Session is started'})
evidence=sb.SubmissionEvidence(package.sha256,accept['specification']['specification_sha256'],accept['artifact']['sha256'],TOKEN,ack['observed_channel'],observed,str(P/'external_receipt_acknowledgement.json')+'#sha256='+ack_identity.sha256)
evidence.validate(package)
l6.write_once(P/'submission_evidence.json',dataclasses.asdict(evidence))
terminal=boundary.record_submission(package,evidence)
terminal.validate()
term=l6.read_json(terminal.path)
assert term['status']=='CLOSED' and term['transitions']==['DELIVERED','CLOSED']
assert term['submission_evidence']==dataclasses.asdict(evidence)
assert boundary.outcome.status=='CLOSED' and boundary.outcome.terminal and boundary.outcome.delivered
assert term['verification_scope']=='LOCAL_CALLER_SUPPLIED_EVIDENCE_CONTRACT_ONLY'

# Actual closed Session guards: no network/process/write allowed while probing.
phase='validation'
snapshot={str(p):l6.digest(p) for p in D.rglob('*') if p.is_file()}
reopened=sb.SessionBoundary(boundary.session_id,D)
l6_dir=ROOT/'runs/l6'/data['child_ids']['l6']
bridge_dir=ROOT/'runs/l7'/data['child_ids']['bridge']
correction_dir=ROOT/'runs/l7'/data['child_ids']['correction']
guards=[]
operations=[
    ('reopened.assert_open',reopened.assert_open),
    ('reopened._execution_open',reopened._execution_open),
    ('bound.checked_parent(execution=True)',lambda:bound.checked_parent(parent,execution=True)),
    ('L6 bound Worker/Review effect_guard',lambda:bound.effect_guard(l6_dir)),
    ('bridge bound renderer/Review effect_guard',lambda:bound.effect_guard(bridge_dir)),
    ('new bound correction registration',lambda:bound.child_binding(parent,'correction',correction_dir,bridge_dir)),
    ('same Session run_session preflight/resume',lambda:bound.run_session(parent,execute=False)),
    ('reopened.create_binding',lambda:reopened.create_binding(binding.specification,binding.loop_run_id)),
    ('reopened.register_child_evidence',lambda:reopened.register_child_evidence(data['child_ids']['l6'],ack_identity)),
    ('reopened.internal_accept',lambda:reopened.internal_accept(binding,sb.FileIdentity(**accept['artifact']),sb.FileIdentity(**accept['final_review']))),
    ('reopened.prepare_delivery',reopened.prepare_delivery),
    ('reopened.record_submission',lambda:reopened.record_submission(package,evidence)),
    ('reopened.stop',lambda:reopened.stop('ABORT','negative guard probe'))]
for label,operation in operations:
    try:operation()
    except ValueError as exc:
        assert str(exc)=='ALREADY_TERMINAL',(label,str(exc))
        guards.append({'operation':label,'result':'REJECTED','reason':str(exc),'effects':0})
    else:raise AssertionError('CLOSED_SESSION_GUARD_FAILED: '+label)
try:sb.SessionBoundary('wrong-session-for-negative-verification',D)
except ValueError as exc:
    assert str(exc)=='Session directory identity mismatch'
    guards.append({'operation':'wrong Session handle using actual directory','result':'REJECTED','reason':str(exc),'effects':0})
else:raise AssertionError('Session directory guard failed')
assert not correction_dir.exists()
assert {str(p):l6.digest(p) for p in D.rglob('*') if p.is_file()}==snapshot
assert all(l6.digest(ROOT/p)==h for p,h in tracked.items())
boundary._checked_accept();package.validate();ack_identity.validate();terminal.validate()
phase='record'
summary={'verdict_before_git_finalization':'ACTUAL_DELIVERY_AND_SESSION_CLOSURE_RECORDED','session':boundary.session_id,'loop':binding.loop_run_id,'starting_head':BASE,'receipt':dataclasses.asdict(ack_identity),'receipt_id':TOKEN,'submission_evidence':dataclasses.asdict(evidence),'delivery_package':dataclasses.asdict(package),'terminal_record':dataclasses.asdict(terminal),'status':boundary.outcome.status,'transitions':term['transitions'],'terminal':True,'delivered':True,'accepted_artifact':accept['artifact'],'specification':accept['specification'],'internal_accept_preserved':ready['internal_accept'],'mandatory_coverage_verified':True,'actual_closed_session_guards':guards,'guard_probe_bytes_unchanged':True,'starting_tracked_unchanged':len(tracked),'source_test_changes':0,'historical_evidence_changes':0,'actual_effects':{'worker':0,'comfy_generation':0,'blender':0,'semantic_reviewer':0,'correction_dispatch':0,'repeat_delivery_transport':0},'external_evaluation':'승인','external_evaluation_scope':'Outside Core state; no new Request/Session','completed_at':l6.now(),'negative_fixture_tests':'PENDING_EXISTING_TESTS_ONLY','fresh_session_started':False}
l6.write_once(P/'closure_verified.json',summary)
print(json.dumps({k:v for k,v in summary.items() if k not in ('actual_closed_session_guards','submission_evidence')},ensure_ascii=False,indent=2))
