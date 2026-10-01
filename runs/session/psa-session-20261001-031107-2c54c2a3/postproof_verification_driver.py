"""Post-attempt validation and evidence recording; never dispatch or accept."""
import dataclasses, json, os, pathlib, subprocess, sys, urllib.request
ROOT=pathlib.Path('D:/VSCODE-WorkSpace/Others/Agent-Loop-Core')
WORK=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from scenario_a import session_binding as bound, l6_pipeline as l6, l7_geometry_review as bridge, l7_feedback_controller as correction
from session import session_boundary as session
d=ROOT/'runs/session/psa-session-20261001-031107-2c54c2a3'
ready=l6.read_json(d/'checkpoint1_ready.json');ids=ready['identities'];parent=ready['session_binding']
children={k:ROOT/('runs/l6' if k=='l6' else 'runs/l7')/ids[k] for k in bound.KINDS}
dirs=[d]+[p for p in children.values() if p.exists()]
def snapshot():return {str(p):l6.digest(p) for q in dirs for p in q.rglob('*') if p.is_file()}
before=snapshot();phase='validation'
def audit(event,args):
    if phase=='validation':
        if event in ('subprocess.Popen','urllib.Request','socket.connect'):raise RuntimeError('PURE_VALIDATION_NO_EFFECT: '+event)
        if event=='open' and (isinstance(args[1],str) and any(c in args[1] for c in ('w','a','x','+')) or args[2]& (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
            raise RuntimeError('PURE_VALIDATION_NO_WRITE: '+str(args[0]))
sys.addaudithook(audit)
data,boundary,binding=bound.checked_parent(parent)
assert binding.specification.identity_sha256==ready['specification_identity_sha256']
assert binding.identity_sha256==ready['binding_identity_sha256']
assert l6.png_identity(ready['source']['path'],'front')==ready['source']
assert binding.specification.reference.specification_sha256==ready['specification']['sha256']
checked_refs={}
def check_refs(x):
    if isinstance(x,dict):
        if isinstance(x.get('path'),str) and isinstance(x.get('sha256'),str) and len(x['sha256'])==64:
            p=l6.reviewer.checked_ref({k:x[k] for k in ('path','sha256')})
            if isinstance(x.get('bytes'),int):assert p.stat().st_size==x['bytes']
            checked_refs[str(p)]=x['sha256']
        for v in x.values():check_refs(v)
    elif isinstance(x,list):
        for v in x:check_refs(v)
for q in dirs:
    for p in q.glob('*.json'):
        if p.stat().st_size:
            check_refs(l6.read_json(p))
states={};terminals={};reviews=[];artifacts=[];renderers=[];reports=[]
for k,q in children.items():
    if not q.exists():continue
    bound.checked_child(q,parent_ref=parent)
    states[k]=l6.read_json(q/'state.json')
    if (q/'terminal.json').exists():
        terminals[k]=l6.reference(q/'terminal.json')
        for ref in l6.read_json(q/'terminal.json')['records'].values():
            if ref is not None:l6.reviewer.checked_ref(ref)
    for p in q.glob('*_worker_report.json'):
        x=l6.read_json(p);reports.append((p,x))
        order=l6.read_json(q/(p.name.replace('_worker_report.json','_work_order.json')))
        if x['status']=='SUCCESS':l6.validate_worker_report(order,x)
    for p in q.glob('*_execution.json'):
        x=l6.read_json(p)
        if x.get('artifact') is not None:artifacts.append(x['artifact'])
    if (q/'renderer_invocation.json').exists():renderers.append({'record':l6.reference(q/'renderer_invocation.json'),'data':l6.read_json(q/'renderer_invocation.json')})
    prefixes=[('review','multiview')] if k=='l6' else [('review','geometry')] if k=='bridge' else [('multiview_review','multiview'),('geometry_review','geometry')]
    for prefix,stage in prefixes:
        ip=q/(prefix+'_invocation.json');rp=q/(prefix+'_result.json');qp=q/(prefix+'_request.json')
        if not ip.exists():continue
        inv=l6.read_json(ip)
        item={'invocation':l6.reference(ip),'request':l6.reference(qp),'invocation_status':inv['invocation_status'],'semantic_process_started':inv.get('reviewer_process_started',False)}
        if inv['invocation_status']=='SUCCESS':
            assert inv['reviewer_mode']=='CODEX_CLI' and inv['auth_mode']=='CHATGPT_ACCOUNT' and inv['reviewer_process_started'] and inv['process_exit_code']==0
            req=l6.read_json(qp);raw=l6.read_json(rp)
            assert inv['attached_images']==[{key:a[key] for key in ('role','path','sha256')} for a in req['artifacts']]
            cp=q/(prefix+'_result_coverage.json')
            assert cp.is_file(), 'success stage must already have coverage'
            result=l6.checked_review(q) if k=='l6' else bridge.checked_review(q) if k=='bridge' else correction.checked_review(q,stage)
            assert result==raw
            cov=bound.validate_coverage(bound.review_contract(q,stage),raw)
            assert cov==l6.read_json(cp)['coverage']
            item.update(review_id=raw['review_id'],stage=stage,child=k,verdict=raw['verdict'],blocking_issues=raw['blocking_issues'],observations=raw['observations'],action=raw['suggested_action'],result=l6.reference(rp),coverage=l6.reference(cp),criteria_coverage=cov,attached_images=inv['attached_images'])
        reviews.append(item)
if (children['l6']/'multiview_manifest.json').exists():
    l6.validate_manifest(l6.read_json(children['l6']/'multiview_manifest.json'),children['l6'])
if states.get('l6',{}).get('state')=='GEOMETRY_READY':bridge.validate_l6(children['l6'],parent)
for k in ('bridge','correction'):
    q=children[k]
    if (q/'render_manifest.json').exists():
        manifest=bridge.validate_render_manifest(q) if k=='bridge' else correction.validate_render_manifest(q)
        assert manifest['source_glb']==l6.read_json(q/'render_request.json')['source_glb']
correction_action=None
if (children['correction']/'revision_action.json').exists():
    correction_action=l6.read_json(children['correction']/'revision_action.json')
    assert correction_action['revision_ordinal']==1 and correction_action['revision_seed']==correction_action['previous_seed']+1
    assert (children['correction']/'revision_reservation.json').is_file()
    assert correction_action['source_review']==l6.reference(children['bridge']/'review_result.json')
    source_review=l6.read_json(children['bridge']/'review_result.json')
    assert source_review['verdict']=='REVISE' and source_review['suggested_action']=={'code':correction_action['action_code'],'target':correction_action['target']}
accepted=(d/'internal_accept.json').exists()
if accepted:
    accept=boundary._checked_accept(); candidate=l6.read_json(d/'scenario_a_accept.json')
    assert boundary.outcome.status=='INTERNAL_ACCEPT' and not boundary.outcome.terminal and not boundary.outcome.delivered
    mandatory={c.criterion_id for c in binding.specification.fields.acceptance_criteria if c.blocking_when_unmet}
    assert set(candidate['mandatory_criterion_ids'])==mandatory and not candidate['delivered']
    for stage,ref in candidate['stage_coverage'].items():
        cov=l6.read_ref(ref)
        assert cov['verdict']=='PASS'
        assert all(cov['coverage'][cid]=='SATISFIED' for cid in data['stage_criteria'][stage] if cid in mandatory)
    assert candidate['artifact']['sha256']==accept['artifact']['sha256']
    assert candidate['result']['sha256']==accept['final_review']['sha256']
else:
    assert not (d/'scenario_a_accept.json').exists()
assert not (d/'delivery_package.json').exists() and not boundary.outcome.delivered
protected=l6.read_json(d/'protection_before.json')
changed=[p for p,h in protected['tracked'].items() if l6.digest(ROOT/p)!=h]
assert not changed,changed
external_changes=[]
for p,identity in protected['external'].items():
    q=pathlib.Path(p);s=q.stat();current={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':l6.digest(q) if identity['sha256'] else None}
    if current!=identity:external_changes.append(p)
assert not external_changes,external_changes
assert snapshot()==before,'existing proof bytes changed during validation'
phase='record'
actual=l6.read_json(d/'actual_result.json') if (d/'actual_result.json').exists() else l6.read_json(d/'actual_exception.json')
counts=actual['observed_attempt_counts']
events=[json.loads(x) for x in (d/'actual_events.jsonl').read_text(encoding='utf-8').splitlines()]
submissions=[e for e in events if e.get('method')=='POST' and e['url'].endswith('/prompt')]
assert len(submissions)==counts['comfy_prompt_attempts']
assert len([e for e in events if e.get('category')=='semantic_reviewer'])==counts['semantic_process_attempts']
assert len([e for e in events if e.get('category')=='blender_production'])==counts['blender_process_attempts']
assert counts['comfy_prompt_attempts']<=6 and counts['semantic_process_attempts']<=4 and counts['blender_process_attempts']<=2
histories=[]
for i,(p,report) in enumerate(reports,1):
    if not report.get('prompt_id'):continue
    url='http://127.0.0.1:8188/history/'+report['prompt_id']
    with urllib.request.urlopen(url,timeout=20) as r:raw=json.load(r)
    entry=raw.get(report['prompt_id'])
    if report['status']=='SUCCESS':
        assert entry['status']['completed'] and entry['status']['status_str']=='success' and report['output_node'] in entry['outputs']
        cached=[node for event in entry['status']['messages'] if event[0]=='execution_cached' for node in event[1]['nodes']]
        assert report['output_node'] not in cached,'Save output must actually execute'
        event_body=next(l6.read_ref(e['body']) for e in submissions if l6.read_ref(e['body'])['client_id']==report['client_id'])
        assert event_body['prompt']==entry['prompt'][2], 'observed submission/history graph linkage'
    hp=d/('actual_history_%02d.json'%i)
    l6.write_once(hp,{'observed_at':l6.now(),'url':url,'response':raw})
    histories.append({'task_id':report['task_id'],'prompt_id':report['prompt_id'],'client_id':report['client_id'],'worker_status':report['status'],'report':l6.reference(p),'history':l6.reference(hp),'save_node_executed':report['status']=='SUCCESS'})
def git(*args):return subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),*args],cwd=ROOT,text=True,encoding='utf-8').strip()
refs=dict((b,a) for a,b in (line.split() for line in git('show-ref').splitlines()))
assert all(refs[b]==a for a,b in (line.split() for line in protected['refs'].splitlines()))
reason=states.get('correction',states.get('bridge',states.get('l6',{}))).get('reason')
verdicts=[x.get('verdict') for x in reviews]
if accepted:classification='POST-STABILIZATION ACTUAL LOOP = VERIFIED'
elif reason=='REVIEW_CONTRACT_VIOLATION' or 'type' in actual:classification='CONTRACT_DEFECT_FOUND'
elif any(x.get('state')=='FAILED' for x in states.values()):classification='RUNTIME_FAILED'
elif any(x.get('state')=='UNRESOLVED' for x in states.values()):classification='RUNTIME_UNRESOLVED'
elif 'REVISE' in verdicts:classification='SEMANTIC_CLOSURE_FAILED'
else:classification='ABORT / '+str(reason)
summary={'classification':classification,'session_status':boundary.outcome.status,'session_terminal':boundary.outcome.terminal,'identities':ids,'specification':ready['specification'],'specification_identity_sha256':ready['specification_identity_sha256'],'binding_identity_sha256':ready['binding_identity_sha256'],'applicability':data['stage_criteria'],'actual_counts':counts|{'comfy_accepted_submissions':sum(bool(x.get('prompt_id')) for _,x in reports),'correction_dispatch':int(correction_action is not None),'run_session_execute_true':1,'automatic_retries':0,'user_delivery':0},'child_states':{k:{f:v.get(f) for f in ('state','reason','terminal','review_verdict','final_verdict','errors')} for k,v in states.items()},'child_terminals':terminals,'reviews':reviews,'correction_action':correction_action,'artifacts':artifacts,'renderer_invocations':renderers,'histories':histories,'internal_accept':accepted,'delivery_package':False,'delivered':False,'hash_references_verified':len(checked_refs),'protection':{'starting_tracked_unchanged':len(protected['tracked']),'external_unchanged':len(protected['external']),'large_model_full_hash':False,'protected_local_refs_unchanged':True,'runtime_source_changes':0,'historical_evidence_changes':0,'pure_validation_proof_bytes_unchanged':True},'checkpoint1_commit':git('rev-parse','HEAD'),'completed_at':actual['finished_at'],'actual_backend_model':None,'actual_backend_reasoning_effort':None,'tokens':None,'credits':None}
l6.write_once(d/'checkpoint2_verified.json',summary)
with (d/'postproof_verification_driver.py').open('xb') as f:f.write(pathlib.Path(__file__).read_bytes())
doc=ROOT/'docs/session/POST_STABILIZATION_ACTUAL_LOOP_PROOF.md'
text=doc.read_text(encoding='utf-8')
text=text.replace('CP2: 아직 실행하지 않음. INTERNAL_ACCEPT 및 DELIVERED 미생성.','CP2: actual one-shot 완료; 아래 결과와 evidence를 참조한다.')
text+='\n\n## CP2 — One Actual Loop Result\n\n'
text+=classification+'\n\n'
text+=f"Session state: {boundary.outcome.status}; INTERNAL_ACCEPT: {accepted}; delivered=false.\nCP1 commit: {summary['checkpoint1_commit']}.\nActual counts: {json.dumps(summary['actual_counts'],ensure_ascii=False)}.\n\n"
text+='| Review | stage | verdict | applicable coverage |\n|---|---|---|---|\n'
for r in reviews:text+=f"| {r.get('review_id','unresolved')} | {r.get('stage','unknown')} | {r.get('verdict',r['invocation_status'])} | {json.dumps(r.get('criteria_coverage',{}))} |\n"
text+='\nCorrection: '+json.dumps(correction_action,ensure_ascii=False)+'\n\n'
text+='Final blockers: '+json.dumps(reviews[-1].get('blocking_issues',[]) if reviews else [],ensure_ascii=False)+'\n\n'
text+='Artifact/Request/Result/Invocation/coverage/Session/Spec/child lineage는 기존 production validators와 recorded hashes로 검증했다. Pure validation의 network/process/write는 차단하고 기존 proof bytes 불변을 확인했다. Actual /prompt body와 independent GET /history 응답의 client/prompt graph, execution success 및 Save output node 실제 실행도 확인했다.\n\n'
text+=f"기존 tracked {len(protected['tracked'])}개 SHA-256 불변; source/test/historical evidence 변경0; external reference {len(protected['external'])}개 metadata/작은-file SHA 불변. Large model full hashes는 미측정이다. Protected local refs 불변. Evidence details: runs/session/{ids['session']}/checkpoint2_verified.json.\n\n"
text+='INTERNAL_ACCEPT와 User Delivery는 구분한다. Delivery Package/DELIVERED/closure/fresh Session 생성0. 추가 actual/retry/seed reroll/source repair0. 실패 evidence는 그대로 유지한다. CP2 normal commit과 push 후 local/tracking/live remote equality는 별도 final verification 기록에서 확인한다.\n'
doc.write_text(text,encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('reviews','artifacts','renderer_invocations','histories','child_terminals')},ensure_ascii=False,indent=2))
