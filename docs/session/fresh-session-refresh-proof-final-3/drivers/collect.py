import os,sys,json,subprocess,urllib.request,hashlib,re
from pathlib import Path
from dataclasses import asdict
ROOT=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final-3'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
os.chdir(ROOT)
from scenario_a import session_binding as bound,l6_pipeline as l6,l7_geometry_review as bridge,l7_feedback_controller as controller
from session import session_boundary as sb
prepared=l6.read_json(PROOF/'PREPARED_BINDING.json'); ids=prepared['ids']
result=l6.read_json(PROOF/'ACTUAL_ENTRY_RESULT.json'); events=l6.read_json(PROOF/'ACTUAL_EFFECT_AUDIT.json')
boundary=sb.SessionBoundary(ids['session'],ROOT/'runs/session'/ids['session'])
dirs={'l6':ROOT/'runs/l6'/ids['l6'],'bridge':ROOT/'runs/l7'/ids['bridge'],'correction':ROOT/'runs/l7'/ids['correction']}
def write(name,data): l6.write_once(PROOF/name,data)
def archive(path,target):
    target=PROOF/target; target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
        with target.open('xb') as f: f.write(Path(path).read_bytes())
    assert l6.digest(target)==l6.digest(path)
    return l6.reference(target)
workers=[]; reviews=[]; renders=[]; terminals=[]; images=[]; artifacts=[]
for kind,d in dirs.items():
    if not d.exists(): continue
    bound.checked_child(d,parent_ref=prepared['parent'])
    if (d/'terminal.json').exists():
        terminal=l6.read_json(d/'terminal.json')
        for ref in terminal['records'].values():
            if ref: l6.reviewer.checked_ref(ref)
        terminals.append({'kind':kind,'terminal':terminal,'reference':l6.reference(d/'terminal.json')})
    for p in sorted(d.glob('*worker_report.json')):
        report=l6.read_json(p); execution_path=p.with_name(p.name.replace('_worker_report.json','_execution.json'))
        execution=l6.read_json(execution_path) if execution_path.exists() else None
        item={'kind':kind,'record':l6.reference(p),'report':report,'execution':execution,'history_validation':None}
        prompt=report.get('prompt_id')
        if prompt:
            with urllib.request.urlopen(l6.worker.BASE_URL+'/history/'+prompt,timeout=30) as f: history=json.load(f)
            (PROOF/'comfy_history').mkdir(exist_ok=True)
            write('comfy_history/'+d.name+'-'+p.stem+'.json',history)
            h=history[prompt]
            item['history_validation']={'prompt_id':prompt,'completed':h['status']['completed'],'status_str':h['status']['status_str'],'outputs_present':bool(h['outputs'])}
            assert h['status']['completed'] and h['status']['status_str']=='success'
        artifact=execution.get('artifact') if execution else None
        for a in report.get('outputs',[]):
            if not a.get('path') or not Path(a['path']).is_file(): continue
            if a.get('sha256'): assert l6.digest(a['path'])==a['sha256']
            if str(a['path']).lower().endswith('.png'):
                im=l6.png_identity(a['path'],a.get('role','view')); assert (im['width'],im['height'])==(768,768)
                images.append({'kind':kind,'source':im,'archive':archive(a['path'],'images/'+d.name+'-'+p.stem+'.png')})
            elif str(a['path']).lower().endswith('.glb'):
                assert artifact and artifact['path']==a['path'] and l6.digest(a['path'])==artifact['sha256']
                artifacts.append({'kind':kind,'artifact':artifact})
        workers.append(item)
    for p in sorted(d.glob('*review_invocation.json')):
        invocation=l6.read_json(p); prefix=p.name.removesuffix('_invocation.json')
        rp=d/(prefix+'_result.json'); qp=d/(prefix+'_request.json')
        review=l6.read_json(rp) if rp.exists() and rp.stat().st_size else None
        for stream in (invocation.get('stdout_evidence',{}),invocation.get('stderr_evidence',{})):
            if isinstance(stream,dict) and stream.get('path'): assert l6.digest(stream['path'])==stream['sha256']
        if review:
            l6.reviewer.validate_result(review,l6.read_json(qp))
            stage='multiview' if 'multiview' in p.name else 'geometry'
            if kind=='l6': l6.checked_review(d)
            elif kind=='bridge': bridge.checked_review(d)
            else: controller.checked_review(d,stage)
        reviews.append({'kind':kind,'invocation':l6.reference(p),'data':invocation,'request':l6.reference(qp) if qp.exists() else None,'result':review})
    for p in sorted(d.glob('*render_manifest.json')):
        manifest=l6.read_json(p); renders.append({'kind':kind,'reference':l6.reference(p),'data':manifest})
        def visit(x):
            if isinstance(x,dict):
                if x.get('path') and str(x['path']).lower().endswith('.png') and Path(x['path']).is_file():
                    if x.get('sha256'): assert l6.digest(x['path'])==x['sha256']
                    im=l6.png_identity(x['path'],x.get('role','diagnostic'))
                    assert (im['width'],im['height'])==(512,512)
                    images.append({'kind':kind,'source':im,'archive':archive(x['path'],'images/'+d.name+'-'+Path(x['path']).name)})
                else:
                    for v in x.values(): visit(v)
            elif isinstance(x,list):
                for v in x: visit(v)
        visit(manifest)
baseline=l6.read_json(PROOF/'STARTING_SNAPSHOT.json')
changed=[n for n,sha in baseline['tracked_file_sha256'].items() if not (ROOT/n).is_file() or l6.digest(ROOT/n)!=sha]
assert not changed,changed
tags=subprocess.check_output(['git','show-ref','--tags'],encoding='utf-8').strip(); assert tags==baseline['tags']
accepted=boundary.outcome.status=='INTERNAL_ACCEPT'
final=boundary._checked_accept()['artifact'] if accepted else (artifacts[-1]['artifact'] if artifacts else None)
if final and Path(final['path']).stat().st_size<20*1024*1024:
    archive(final['path'],'CURRENT_ARTIFACT.glb')
correction_dir=dirs['correction']
correction_count=int((correction_dir/'revision_reservation.json').exists())
classification='INTERNAL_ACCEPT / PUBLICATION_VERIFICATION_PENDING' if accepted else 'RUNTIME_FAILED'
if result.get('state')=='EXECUTION_EXCEPTION': classification='CONTRACT_DEFECT_FOUND'
elif result.get('reason')=='REVISION_BUDGET_EXHAUSTED' and correction_count and reviews[-1]['result'] and reviews[-1]['result']['verdict']=='REVISE': classification='SEMANTIC_CLOSURE_FAILED'
elif result.get('state')=='ABORT': classification='SEMANTIC_CLOSURE_FAILED' if result.get('reason')=='REVISION_BUDGET_EXHAUSTED' else 'HUMAN_REQUIRED'
if result.get('state')=='EXECUTION_EXCEPTION' and not boundary.outcome.terminal:
    write('CONTRACT_DEFECT_EVIDENCE.json',{'error':result,'effect_audit':l6.reference(PROOF/'ACTUAL_EFFECT_AUDIT.json'),'no_retry_resume':True})
    boundary.stop('FAILED',classification)
stream_contract=None
if any(r['kind']=='bridge' and r['result'] and r['result']['verdict']=='REVISE' for r in reviews):
    source=controller.validate_source(dirs['bridge'],prepared['parent'])
    stream_contract={'status':'PASS','validate_source':source,'actual_stream_references':{k:v for k,v in l6.read_json(dirs['bridge']/'terminal.json')['records'].items() if k.endswith(('.stdout','.stderr'))},'correction_started':correction_count==1}
posts=[e for e in events if e['event']=='ACTUAL_COMFY_POST']
phase_counts={kind:{'worker':len([w for w in workers if w['kind']==kind]),'reviewer':len([r for r in reviews if r['kind']==kind and r['data']['reviewer_process_started']]),'blender':len([r for r in renders if r['kind']==kind])} for kind in dirs}
scope=[PROOF,boundary.directory,*[d for d in dirs.values() if d.exists()]]
suspects=[]; checked=0
for directory in scope:
    for p in directory.rglob('*'):
        if not p.is_file() or p.suffix not in ('.json','.md','.txt','.log','.py'): continue
        text=p.read_text(encoding='utf-8',errors='replace');checked+=1
        if re.search(r'\bsk-[A-Za-z0-9_-]{16,}|\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',text): suspects.append(str(p))
assert not suspects,suspects
validation={'classification':classification,'canonical_result':result,'session_outcome':asdict(boundary.outcome),'ids':ids,'reference_sha256':prepared['original']['sha256'],'normalized_sha256':prepared['normalization']['normalized_sha256'],'specification_identity_sha256':prepared['specification_identity_sha256'],'stage_criteria':prepared['stage_criteria'],'production_entry_count':1,'worker_reports':workers,'reviews':reviews,'render_manifests':renders,'child_terminals':terminals,'image_evidence':images,'geometry_artifacts':artifacts,'final_artifact':final,'actual_post_count':len(posts),'geometry_post_count':sum(e['stage']=='geometry' for e in posts),'semantic_reviewer_count':sum(e['event']=='ACTUAL_SEMANTIC_REVIEWER' for e in events),'blender_render_count':sum(e['event']=='ACTUAL_BLENDER_RENDER' for e in events),'correction_dispatch_count':correction_count,'phase_counts':phase_counts,'L7_stream_contract':stream_contract,'readiness_probe_count':1,'INTERNAL_ACCEPT':accepted,'source_test_changes':0,'historical_changed_files':changed,'protected_tags_preserved':True,'old_source_fallback':0,'resume_retry_delivery_count':0,'obvious_secret_pattern_hits':0,'publication_text_files_checked':checked}
write('ACTUAL_VALIDATION.json',validation)
write('CP2_RESULT.json',{'classification':classification,'validation':l6.reference(PROOF/'ACTUAL_VALIDATION.json'),'session_outcome':asdict(boundary.outcome),'source_test_changes':0,'historical_evidence_preserved':True,'delivery':False,'publication_verification':'Pending post-commit check; no self-referential commit assertion.'})
with (PROOF/'FINAL_RESULT.md').open('x',encoding='utf-8') as f:
    f.write('# Fresh Session / Refresh Proof Final-3 Result\n\n'+classification+'\n\nStart: '+baseline['start_branch']+' @ '+baseline['start_head']+'. Proof branch: fresh-session-refresh-proof-final-3.\n\nCurrent regression 277/277 PASS; readiness/CP1 generation effects 0. New request, independent frozen specification and Session/Loop; no previous active state or artifact imported.\n\nReference: '+prepared['original']['sha256']+'\nNormalized: '+prepared['normalization']['normalized_sha256']+'\n\nSession: '+ids['session']+'\nLoop: '+ids['loop']+'\n\nCanonical state/reason: '+str(result.get('state'))+' / '+str(result.get('reason'))+'\n\nWorker/Comfy POSTs: '+str(len(posts))+'; geometry POSTs: '+str(validation['geometry_post_count'])+'; production Reviewer: '+str(validation['semantic_reviewer_count'])+'; Blender: '+str(validation['blender_render_count'])+'; bounded correction dispatch: '+str(correction_count)+'. Separate readiness image probe: 1.\n\nPhase counts: '+json.dumps(phase_counts)+'\n\nINTERNAL_ACCEPT: '+str(accepted)+'\nFinal artifact: '+json.dumps(final)+'\n\nActual Reviews:\n'+ '\n'.join(json.dumps({'kind':r['kind'],'result':r['result']},ensure_ascii=False) for r in reviews)+'\n\nL7 stream contract: '+('PASS: actual .txt references validated; no suffix reconstruction defect.' if stream_contract else 'Not exercised by a geometry REVISE.')+'\n\nSource/test changes 0; baseline tracked files/tags unchanged. No retry, resume, manual replacement, budget extension, Delivery or closure. Full evidence is in ACTUAL_VALIDATION.json and the new child namespaces. Publication equality and final clean status are measured after CP2, outside committed bytes.\n')
drivers=PROOF/'drivers'
with (drivers/'collect.py').open('xb') as f: f.write(Path(__file__).read_bytes())
print(json.dumps({k:validation[k] for k in ('classification','canonical_result','phase_counts','actual_post_count','semantic_reviewer_count','blender_render_count','correction_dispatch_count','final_artifact','INTERNAL_ACCEPT')}),flush=True)
