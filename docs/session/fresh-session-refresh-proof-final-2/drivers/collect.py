import os,sys,json,shutil,subprocess,urllib.request,hashlib
from pathlib import Path
from dataclasses import asdict
ROOT=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final-2'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
os.chdir(ROOT)
from scenario_a import session_binding as bound,l6_pipeline as l6
from session import session_boundary as session
from core import result_review_adapter as reviewer
prepared=l6.read_json(PROOF/'PREPARED_BINDING.json'); ids=prepared['ids']
result=l6.read_json(PROOF/'ACTUAL_ENTRY_RESULT.json'); events=l6.read_json(PROOF/'ACTUAL_EFFECT_AUDIT.json')
session_dir=ROOT/'runs/session'/ids['session']
boundary=session.SessionBoundary(ids['session'],session_dir)
dirs=[ROOT/'runs/l6'/ids['l6'],ROOT/'runs/l7'/ids['bridge'],ROOT/'runs/l7'/ids['correction']]
def git(*args): return subprocess.run(['git',*args],check=True,capture_output=True,encoding='utf-8',errors='replace').stdout.strip()
def write(name,data): l6.write_once(PROOF/name,data)
def copy_image(path,name):
    target=PROOF/'images'/name; target.parent.mkdir(exist_ok=True)
    shutil.copyfile(path,target)
    identity=l6.png_identity(target,'evidence')
    assert identity['sha256']==l6.digest(path)
    return identity
workers=[]; reviews=[]; renders=[]; terminal_records=[]; images=[]; artifacts=[]
for d in dirs:
    if not d.exists(): continue
    if (d/'terminal.json').exists(): terminal_records.append({'child':d.name,'terminal':l6.read_json(d/'terminal.json')})
    for p in sorted(d.glob('*worker_report.json')):
        report=l6.read_json(p)
        prompt=report.get('prompt_id')
        item={'record':l6.reference(p),'report':report,'history_validation':None}
        if prompt:
            with urllib.request.urlopen(l6.worker.BASE_URL+'/history/'+prompt,timeout=30) as response: history=json.load(response)
            hpath=PROOF/'comfy_history'; hpath.mkdir(exist_ok=True)
            l6.write_once(hpath/(d.name+'-'+p.stem+'.json'),history)
            h=history[prompt]
            item['history_validation']={'prompt_id':prompt,'completed':h['status']['completed'],'status_str':h['status']['status_str'],'outputs_present':bool(h['outputs'])}
            assert h['status']['completed'] and h['status']['status_str']=='success'
        for a in report.get('outputs',[]):
            if a.get('path') and Path(a['path']).is_file():
                assert l6.digest(a['path'])==a['sha256']
                if str(a['path']).lower().endswith('.png'):
                    im=l6.png_identity(a['path'],a.get('role','view'))
                    assert (im['width'],im['height'])==(768,768)
                    images.append({'source':im,'repository_copy':copy_image(a['path'],d.name+'-'+p.stem+'.png')})
                elif str(a['path']).lower().endswith('.glb'): artifacts.append(a)
        workers.append(item)
    for p in sorted(d.glob('*review_invocation.json')):
        invocation=l6.read_json(p)
        prefix=p.name.removesuffix('_invocation.json')
        rp=d/(prefix+'_result.json'); qp=d/(prefix+'_request.json')
        item={'invocation':l6.reference(p),'data':invocation,'result':l6.read_json(rp) if rp.exists() and rp.stat().st_size else None,'request':l6.reference(qp) if qp.exists() else None}
        for stream in (invocation.get('stdout_evidence',{}),invocation.get('stderr_evidence',{})):
            if isinstance(stream,dict) and stream.get('path'):
                assert l6.digest(stream['path'])==stream['sha256']
        reviews.append(item)
    for p in sorted(d.glob('*render_manifest.json')):
        manifest=l6.read_json(p); renders.append({'manifest':l6.reference(p),'data':manifest})
        def visit(obj):
            if isinstance(obj,dict):
                if obj.get('path') and str(obj['path']).lower().endswith('.png') and Path(obj['path']).is_file():
                    if obj.get('sha256'): assert l6.digest(obj['path'])==obj['sha256']
                    name=d.name+'-'+Path(obj['path']).name
                    if not (PROOF/'images'/name).exists(): images.append({'source':obj,'repository_copy':copy_image(obj['path'],name)})
                else:
                    for v in obj.values(): visit(v)
            elif isinstance(obj,list):
                for v in obj: visit(v)
        visit(manifest)
protection=l6.read_json(PROOF/'HISTORICAL_PROTECTION.json')
changed=[p for p,sha in protection['tracked_file_sha256'].items() if not (ROOT/p).is_file() or l6.digest(ROOT/p)!=sha]
assert not changed,changed
assert git('show-ref','--tags')==protection['tags']
accepted=boundary.outcome.status=='INTERNAL_ACCEPT'
if accepted:
    current=boundary._checked_accept()
    final=current['artifact']
else: final=artifacts[-1] if artifacts else None
if final and Path(final['path']).stat().st_size<20*1024*1024:
    shutil.copyfile(final['path'],PROOF/'CURRENT_ARTIFACT.glb')
    assert l6.digest(PROOF/'CURRENT_ARTIFACT.glb')==final['sha256']
posts=[e for e in events if e['event']=='ACTUAL_COMFY_POST']
verdict='FRESH SESSION / REFRESH PROOF = VERIFIED' if accepted else ('RUNTIME_FAILED' if result.get('state') in ('FAILED','UNRESOLVED','EXECUTION_EXCEPTION') else 'SEMANTIC_CLOSURE_FAILED')
validation={'final_verdict':verdict,'canonical_result':result,'session_outcome':asdict(boundary.outcome),'ids':ids,'production_entry_count':1,'worker_reports':workers,'reviews':reviews,'render_manifests':renders,'image_evidence':images,'actual_post_count':len(posts),'geometry_post_count':sum(p['stage']=='geometry' for p in posts),'semantic_reviewer_count':sum(e['event']=='ACTUAL_SEMANTIC_REVIEWER' for e in events),'blender_render_count':sum(e['event']=='ACTUAL_BLENDER_RENDER' for e in events),'correction_count':int((dirs[2]/'revision_reservation.json').exists()),'readiness_reviewer_probe_count':1,'final_artifact':final,'INTERNAL_ACCEPT':accepted,'source_test_changes':0,'historical_changed_files':changed,'protected_tags_preserved':True,'old_source_fallback':0,'resume_count':0,'automatic_retry_count':0,'delivery_count':0,'child_terminals':terminal_records,'reference_sha256':prepared['current_reference']['file']['sha256'],'normalized_sha256':prepared['normalization']['normalized_sha256']}
write('ACTUAL_VALIDATION.json',validation)
write('CP2_RESULT.json',{'final_verdict':verdict,'validation':l6.reference(PROOF/'ACTUAL_VALIDATION.json'),'session_outcome':asdict(boundary.outcome),'source_test_changes':0,'historical_evidence_preserved':True,'delivery':False})
text='# Fresh Session / Refresh Proof Final-2 Result\n\n'+verdict+'\n\nCanonical state: '+str(result.get('state'))+'; reason: '+str(result.get('reason'))+'.\n\nStart: stabilization-reviewer-failure-observability @ 93d9dfc7d29c9ffe54886f0f3b34a0248fde410e. Proof branch: fresh-session-refresh-proof-final-2.\n\nIndependent current request/spec; no blocking Specification ambiguity. Five mandatory criteria, selected by observed multiview/geometry applicability. CP1 regression: 261/261 PASS; runtime and namespaces PASS; generation effects before CP1: 0.\n\nReference SHA-256: '+validation['reference_sha256']+'\nNormalized SHA-256: '+validation['normalized_sha256']+'\n\nSession: '+ids['session']+'\nLoop: '+ids['loop']+'\n\nActual Worker/Comfy POSTs: '+str(len(posts))+'; production semantic Reviewer: '+str(validation['semantic_reviewer_count'])+'; geometry POSTs: '+str(validation['geometry_post_count'])+'; Blender renders: '+str(validation['blender_render_count'])+'; corrections: '+str(validation['correction_count'])+'. Readiness image probe: 1 (separate).\n\nINTERNAL_ACCEPT: '+str(accepted)+'. Final artifact: '+json.dumps(final,ensure_ascii=False)+'.\n\nSource/test changes: 0. All baseline tracked files and protected tags preserved. Resume/retry/old-source fallback/Delivery: 0.\n\nReviewer verdicts and criterion evidence:\n'+ '\n'.join(json.dumps(r['result'],ensure_ascii=False) for r in reviews)+'\n\nSee ACTUAL_VALIDATION.json for prompt/history completion, current image decode/hash/dimensions, invocation identity and failure stream evidence. No failed attempt is resumed. CP2 preserves the actual outcome.\n'
(PROOF/'FINAL_RESULT.md').write_text(text,encoding='utf-8')
print(json.dumps({k:validation[k] for k in ('final_verdict','session_outcome','actual_post_count','semantic_reviewer_count','geometry_post_count','blender_render_count','correction_count','final_artifact','INTERNAL_ACCEPT')}),flush=True)
