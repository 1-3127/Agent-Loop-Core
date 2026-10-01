import pathlib,sys,json,hashlib,subprocess,shutil
ROOT=pathlib.Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final'
sys.path.insert(0,str(ROOT/'src'))
from scenario_a import session_binding as bound,l6_pipeline as l6,l7_geometry_review as bridge
from PIL import Image
prepared=l6.read_json(PROOF/'PREPARED_BINDING.json')
result=l6.read_json(PROOF/'ACTUAL_ENTRY_RESULT.json')
ids=prepared['ids']
events=l6.read_json(PROOF/'ACTUAL_EFFECT_AUDIT.json')
children={'l6':ROOT/'runs/l6'/ids['l6'],'bridge':ROOT/'runs/l7'/ids['bridge'],'correction':ROOT/'runs/l7'/ids['correction']}
workers=[]; reviewers=[]; renderers=[]; histories=[]; current_images=[]
archives=[]
archive_dir=PROOF/'artifact_archive'
def archive(path,role):
    p=pathlib.Path(path)
    archive_dir.mkdir(exist_ok=True)
    dest=archive_dir/(role+p.suffix)
    assert not dest.exists()
    shutil.copyfile(p,dest)
    assert l6.digest(dest)==l6.digest(p)
    archives.append({'role':role,'original':l6.reference(p),'archive':l6.reference(dest),'bytes':p.stat().st_size})
for kind,directory in children.items():
    if not directory.exists(): continue
    for path in directory.glob('*worker_report.json'):
        report=l6.read_json(path)
        workers.append({'kind':kind,'record':l6.reference(path),'report':report})
        if report.get('prompt_id'):
            history=l6.worker.request_json('/history/'+report['prompt_id'])
            dest=PROOF/'comfy_history'/f"{kind}-{path.stem}.json"
            dest.parent.mkdir(exist_ok=True)
            l6.write_once(dest,history)
            raw=history.get(report['prompt_id'],{})
            histories.append({'prompt_id':report['prompt_id'],'status':raw.get('status'),'record':l6.reference(dest)})
            for output in raw.get('outputs',{}).values():
                for image in output.get('images',[]):
                    p=l6.worker.DEFAULT_COMFY_ROOT/'work/output'/image.get('subfolder','')/image['filename']
                    current_images.append(l6.png_identity(p,path.stem))
                    archive(p,kind+'-'+path.stem+'-'+p.stem)
            for artifact in report.get('outputs',[]):
                p=pathlib.Path(artifact['path'])
                if p.suffix=='.glb': archive(p,kind+'-'+path.stem+'-'+p.stem)
    for path in directory.glob('*invocation.json'):
        data=l6.read_json(path)
        if 'reviewer_mode' in data:
            entry={'kind':kind,'record':l6.reference(path),'invocation':data}
            rp=path.with_name(path.name.replace('invocation','result'))
            if rp.exists() and rp.stat().st_size:
                try: entry['result']=l6.read_json(rp)
                except ValueError: pass
            reviewers.append(entry)
        if 'process_started' in data and 'reviewer_mode' not in data:
            renderers.append({'kind':kind,'record':l6.reference(path),'invocation':data})
    manifest=directory/'render_manifest.json'
    if manifest.exists():
        for a in l6.read_json(manifest)['outputs']:
            current_images.append(l6.png_identity(a['path'],a['role']))
            archive(a['path'],kind+'-'+a['role'])
baseline=l6.read_json(PROOF/'starting_snapshot.json')
changed=[name for name,h in baseline['tracked_hashes'].items() if not (ROOT/name).is_file() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=h]
assert not changed, changed
staging_path=children['l6']/'reference_staging.json'
staging=l6.read_json(staging_path) if staging_path.exists() else None
if staging:
    l6.validate_current_staging(children['l6'])
    assert staging['normalization']==prepared['normalization']
    assert staging['current_reference']==prepared['current_reference']
    assert staging['normalized_execution']['sha256']==prepared['normalization']['normalized_sha256']
work_orders=[]
for directory in children.values():
    if directory.exists():
        for path in directory.glob('*_work_order.json'):
            work_orders.append({'record':l6.reference(path),'work_order':l6.read_json(path)})
worker_count=len([w for w in workers if w['report'].get('prompt_id')])
reviewer_count=sum(x['invocation'].get('reviewer_process_started') is True for x in reviewers)
renderer_count=sum(x['invocation'].get('process_started') is True for x in renderers)
accepted=result.get('state')=='INTERNAL_ACCEPT'
runtime=l6.read_json(PROOF/'RUNTIME_READINESS.json')
for model in runtime['models']:
    p=pathlib.Path(model['path'])
    assert p.stat().st_size==model['bytes'] and p.stat().st_mtime_ns==model['mtime_ns']
for workflow in runtime['workflow_pins']: assert l6.digest(workflow['path'])==workflow['sha256']
validation={'entry_result':result,'ids':ids,'workers':workers,'histories':histories,'reviewers':reviewers,'renderers':renderers,'actual_images':current_images,'archived_artifacts':archives,'work_orders':work_orders,'staging':staging,'counts':{'worker':worker_count,'comfy_submissions':worker_count,'blender':renderer_count,'production_semantic_reviewer':reviewer_count,'correction':int(children['correction'].exists()),'delivery':0},'starting_tracked_bytes_unchanged':not changed,'changed_starting_files':changed,'source_test_changes':0,'workflow_pins_unchanged':True,'model_size_mtime_unchanged':True,'previous_session_reuse':False,'old_source_fallback':0 if staging else None,'internal_accept':accepted,'same_session_reruns':0,'automatic_retries':0}
if accepted:
    bound.checked_parent(prepared['parent'])
    validation['accept_record']=l6.read_json(ROOT/'runs/session'/ids['session']/'scenario_a_accept.json')
verdict='VERIFIED' if accepted else ('SEMANTIC_CLOSURE_FAILED' if any(x.get('result',{}).get('verdict') in ('REVISE','HUMAN_REQUIRED') for x in reviewers) else 'RUNTIME_FAILED')
if result.get('reason')=='REVIEW_CONTRACT_VIOLATION': verdict='CONTRACT_DEFECT_FOUND'
validation['proof_verdict']=verdict
l6.write_once(PROOF/'ACTUAL_VALIDATION.json',validation)
refs=[]
for directory in [ROOT/'runs/session'/ids['session'],*children.values()]:
    if directory.exists(): refs.extend(l6.reference(p) for p in directory.rglob('*') if p.is_file())
l6.write_once(PROOF/'CURRENT_EVIDENCE_INDEX.json',refs)
print(json.dumps({'proof_verdict':verdict,'entry_state':result.get('state'),'counts':validation['counts'],'images':[{k:i[k] for k in ('role','width','height','sha256')} for i in current_images],'reviews':[{'kind':x['kind'],'invocation':x['invocation'].get('invocation_status'),'verdict':x.get('result',{}).get('verdict')} for x in reviewers]}),flush=True)
