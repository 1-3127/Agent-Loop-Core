"""Prepare the existing acceptance via the public boundary; never submit or close."""
import dataclasses, hashlib, json, os, pathlib, subprocess, sys
ROOT=pathlib.Path('D:/VSCODE-WorkSpace/Others/Agent-Loop-Core')
WORK=pathlib.Path(__file__).resolve().parent
OUT=WORK.parent/'outputs/delivery'
D=ROOT/'runs/session/psa-session-20261001-031107-2c54c2a3'
PROOF=D/'delivery_proof'
sys.path.insert(0,str(ROOT/'src'))
from session import session_boundary as sb
from scenario_a import session_binding as bound, l6_pipeline as l6
gate=l6.read_json(WORK/'delivery_start_gate.json')
def git(*args):return subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),*args],cwd=ROOT,text=True,encoding='utf-8').strip()
assert git('branch','--show-current')=='delivery-closure-post-stabilization'
assert git('rev-parse','HEAD')==gate['head'] and not git('status','--porcelain=v1')
assert not PROOF.exists() and not OUT.exists() and not (D/'delivery_package.json').exists()
assert all(l6.digest(ROOT/p)==h for p,h in gate['tracked'].items())
PROOF.mkdir();OUT.mkdir()
effects={'worker':0,'comfy_generation':0,'blender':0,'semantic_reviewer':0,'correction':0,'submission':0}
allowed_dirs=(PROOF.resolve(),OUT.resolve())
package_path=(D/'delivery_package.json').resolve()
def audit(event,args):
    if event in ('subprocess.Popen','urllib.Request','socket.connect'):
        raise RuntimeError('DELIVERY_PREP_NO_PROCESS_OR_NETWORK: '+event)
    if event=='open' and (isinstance(args[1],str) and any(c in args[1] for c in ('w','a','x','+')) or args[2]& (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
        p=pathlib.Path(args[0]).resolve()
        if p!=package_path and not any(p.is_relative_to(q) for q in allowed_dirs):
            raise RuntimeError('DELIVERY_PREP_WRITE_OUT_OF_SCOPE: '+str(p))
sys.addaudithook(audit)
parent=l6.reference(D/'scenario_a.json')
data,boundary,binding=bound.checked_parent(parent)
assert boundary.outcome.status=='INTERNAL_ACCEPT' and not boundary.outcome.terminal and not boundary.outcome.delivered
accept=boundary._checked_accept()
assert accept['artifact']==gate['artifact'] and binding.specification.identity_sha256==gate['specification_identity_sha256']
accepted_guard=[]
for label,operation in [('boundary._execution_open',boundary._execution_open),('bound.checked_parent(execution=True)',lambda:bound.checked_parent(parent,execution=True))]:
    try:operation()
    except ValueError as exc:
        assert str(exc)=='ALREADY_INTERNAL_ACCEPTED'
        accepted_guard.append({'operation':label,'rejected':str(exc),'actual_effects':0})
    else:raise AssertionError('Accepted Session execution guard failed')
request_path=pathlib.Path('C:/Users/Worker/.codex/attachments/43732ab0-bc96-467e-aedc-cb86d2c0d987/붙여넣은 텍스트.txt')
request_bytes=request_path.read_bytes()
l6.write_once(PROOF/'current_request.json',{'source_path':str(request_path),'source_sha256':hashlib.sha256(request_bytes).hexdigest(),'request_text':request_bytes.decode('utf-8'),'authority':'CURRENT_USER_REQUEST','scope':'Same architectural Session; delivery follow-on authorization supersedes prior checkpoint stop only; Frozen Specification/evidence unchanged'})
l6.write_once(PROOF/'start_gate.json',gate)
with (PROOF/'delivery_start_gate_driver.py').open('xb') as f:f.write((WORK/'delivery_start_gate.py').read_bytes())
with (PROOF/'prepare_delivery_driver.py').open('xb') as f:f.write(pathlib.Path(__file__).read_bytes())
package=boundary.prepare_delivery()
package.validate();payload=l6.read_json(package.path)
assert payload['session_id']==gate['session'] and payload['specification']==accept['specification']
assert payload['artifact']==accept['artifact'] and payload['internal_accept']==gate['internal_accept']
assert payload['final_review']==accept['final_review'] and payload['initial_references']==accept['initial_references']
assert boundary.outcome.status=='INTERNAL_ACCEPT' and not boundary.outcome.delivered and not boundary.outcome.terminal

def copy_unchanged(source,name,identity):
    src=pathlib.Path(source);dst=OUT/name
    raw=src.read_bytes()
    with dst.open('xb') as f:f.write(raw)
    original=sb.file_identity(src,identity);copy=sb.file_identity(dst,identity)
    assert original.bytes==copy.bytes and original.sha256==copy.sha256
    return {'original':dataclasses.asdict(original),'copy':dataclasses.asdict(copy),'bytes_equal':True}
copies={
    'accepted_artifact':copy_unchanged(accept['artifact']['path'],'accepted_geometry.glb','final-glb'),
    'delivery_package':copy_unchanged(package.path,'delivery_package.json',package.identity),
    'initial_input':copy_unchanged('D:/VSCODE-WorkSpace/Comfy-UI/work/input/hunyuan-official-demo-padded.png','initial_input.png','source-front'),
    'final_output_view':copy_unchanged('D:/VSCODE-WorkSpace/Comfy-UI/work/output/l7/psa-bridge-20261001-031107-2c54c2a3/geometry_review/geometry_azimuth_0.png','accepted_geometry_view.png','existing-geometry-diagnostic-azimuth-0')
}
assert copies['accepted_artifact']['copy']['sha256']==gate['artifact']['sha256']
token='delivery-'+package.sha256[:16]
assert not (D/'terminal.json').exists() and all(l6.digest(ROOT/p)==h for p,h in gate['tracked'].items())
ready={'verdict':'DELIVERY_READY_AWAITING_EXTERNAL_RECEIPT','session':gate['session'],'loop':gate['loop'],'proof_branch':'delivery-closure-post-stabilization','base_commit':gate['head'],'canonical_path':'SessionBoundary.prepare_delivery()','package':dataclasses.asdict(package),'accepted_artifact':accept['artifact'],'internal_accept':payload['internal_accept'],'specification':payload['specification'],'final_review':payload['final_review'],'copy_lineage':copies,'receipt_token':token,'destination':'User in the current Codex chat','planned_transport':'Chat final response with clickable artifact/package links and original input/current accepted geometry diagnostic image','submission_occurred_before_final_response':False,'actual_submission_evidence':None,'host_atomic_transport_receipt_available':False,'receipt_required':'After the response, user confirms actual receipt with RECEIVED '+token,'record_submission_called':False,'delivered':False,'terminal':False,'session_status':boundary.outcome.status,'accepted_session_execution_guards':accepted_guard,'closed_session_guard_actual':'DEFERRED_UNTIL_REAL_RECEIPT_AND_CLOSURE','effects':effects,'starting_tracked_unchanged':len(gate['tracked']),'source_test_changes':0,'historical_evidence_changes':0,'prepared_at':l6.now()}
l6.write_once(PROOF/'delivery_ready.json',ready)
l6.write_once(OUT/'delivery_ready.json',ready)
note=f'''# Actual Delivery — Prepared, Awaiting External Receipt

Verdict: DELIVERY_READY_AWAITING_EXTERNAL_RECEIPT.

Same Session `{gate['session']}`, same Loop `{gate['loop']}`; branch `delivery-closure-post-stabilization` from CP2 `{gate['head']}`. No architectural Session/frozen Spec/child acceptance is recreated.

The current user follow-on request authorizes Delivery after the previous checkpoint stop. Frozen Specification and all CP1/CP2 records remain unchanged. Start Gate: expected branch/HEAD/clean/local=tracking=live, acceptance/mandatory stage coverage and 100 path/hash references PASS.

Public `SessionBoundary.prepare_delivery()` was called once. Package hash: `{package.sha256}`. It retains the same Session/Spec/GLB/internal acceptance/final Review references and presentation contract. Package creation is preparation, not submission.

Accepted GLB: 1,139,020 bytes, SHA-256 `{gate['artifact']['sha256']}`. Delivery copy bytes/hash equal; package, original source PNG, and existing diagnostic PNG copies also byte-identical. No generation/render/Review/correction or artifact modification.

Current source has no transport emitter. `record_submission()` only validates caller-supplied external evidence and would write CLOSED with transitions DELIVERED/CLOSED. This turn's final Chat response has not yet been sent when this preparation record is written. No authentic post-send receipt exists yet; no `SubmissionEvidence` or terminal is fabricated, and `record_submission()` is not called.

The final response will present the clickable GLB/package and original input/current geometry diagnostic. Receipt token: `{token}`. Only the user's actual receipt acknowledgement after that response can provide external provenance for the next turn. It is receipt evidence, not quality approval or a new modification Request. Existing external evaluation options remain 승인 / 자연어 피드백 / 사용하지 않음, outside Core state.

Current Session: INTERNAL_ACCEPT, terminal=false, delivered=false. Actual accepted-state execution guards reject both boundary execution and bound-parent execution with ALREADY_INTERNAL_ACCEPTED. Closed-session guard verification is pending actual receipt/closure; existing fixture tests do not establish actual delivery. All Worker/Comfy/Blender/Reviewer/correction/submission effects are 0 during preparation; network/process audit guard enforced.

All {len(gate['tracked'])} starting tracked working bytes including CP1/CP2 and source/tests are unchanged; protected refs are checked again after normal preparation commit/push. New evidence only: canonical delivery_package.json and this delivery_proof directory. Closure final checkpoint is pending real receipt; no fresh Session starts.
'''
with (PROOF/'DELIVERY_PREPARATION.md').open('x',encoding='utf-8',newline='\n') as f:f.write(note)
print(json.dumps({'verdict':ready['verdict'],'package':dataclasses.asdict(package),'receipt_token':token,'session_status':boundary.outcome.status,'delivered':False,'terminal':False,'effects':effects},ensure_ascii=False,indent=2))
