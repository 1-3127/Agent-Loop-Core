import os,sys,json,hashlib,traceback,shlex
from pathlib import Path
ROOT=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final-3'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
os.chdir(ROOT)
from scenario_a import session_binding as bound,l6_pipeline as l6
prepared=l6.read_json(PROOF/'PREPARED_BINDING.json'); ids=prepared['ids']
assert l6.read_json(PROOF/'CP1_READINESS.json')['status']=='READINESS_PASS'
assert not (PROOF/'PRODUCTION_ENTRY_RESERVATION.json').exists()
bound.run_session(prepared['parent'],execute=False)
l6.write_once(PROOF/'PRODUCTION_ENTRY_RESERVATION.json',{'entry':'scenario_a.session_binding.run_session','execute':True,'parent':prepared['parent'],'ids':ids,'created_at':l6.now(),'automatic_retries':0,'delivery':False})
events=[]
def audit(event,args):
    if event=='urllib.Request' and args[0].rstrip('/')==l6.worker.BASE_URL+'/prompt':
        graph=json.loads(args[1])['prompt']
        run=ROOT/'runs/l6'/ids['l6']
        l6.validate_current_staging(run)
        staging=l6.read_json(run/'reference_staging.json')
        assert staging['normalization']==prepared['normalization']
        assert staging['current_reference']==prepared['current_reference']
        _,_,binding=bound.checked_parent(prepared['parent'],execution=True)
        assert binding.specification.identity_sha256==prepared['specification_identity_sha256']
        paths=[node['inputs']['image'] for node in graph.values() if node['class_type']=='LoadImage']
        input_evidence=[]
        for rel in paths:
            assert rel.startswith(('l6/'+ids['l6']+'/','l7/'+ids['correction']+'/')),rel
            p=l6.worker.DEFAULT_COMFY_ROOT/'work/input'/rel
            image=l6.png_identity(p,'input')
            assert (image['width'],image['height'])==(768,768)
            if rel.endswith('/front.png'): assert image['sha256']==prepared['normalization']['normalized_sha256']
            input_evidence.append(image)
        index=1+sum(e['event']=='ACTUAL_COMFY_POST' for e in events)
        record={'event':'ACTUAL_COMFY_POST','index':index,'time':l6.now(),'graph_sha256':hashlib.sha256(args[1]).hexdigest(),'stage':'geometry' if any(n['class_type']=='SaveGLB' for n in graph.values()) else 'multiview','input_images':input_evidence,'parent':prepared['parent'],'reference_staging':l6.reference(run/'reference_staging.json'),'old_source_fallback':0}
        events.append(record); l6.write_once(PROOF/('PRE_SUBMISSION_'+str(index)+'.json'),record)
        print('ACTUAL_COMFY_POST '+str(index)+' '+record['stage'],flush=True)
    if event=='subprocess.Popen':
        command=args[1]
        if isinstance(command,str): command=[v.strip('"') for v in shlex.split(command,posix=False)]
        if isinstance(command,(list,tuple)):
            if 'exec' in command and 'codex' in str(command[0]).lower():
                images=[Path(command[i+1]) for i,v in enumerate(command[:-1]) if v=='-i']
                events.append({'event':'ACTUAL_SEMANTIC_REVIEWER','time':l6.now(),'images':[l6.reference(p) for p in images]})
                print('ACTUAL_SEMANTIC_REVIEWER images='+str(len(images)),flush=True)
            elif 'blender' in str(command[0]).lower() and ('--background' in command or '-b' in command):
                events.append({'event':'ACTUAL_BLENDER_RENDER','time':l6.now()})
                print('ACTUAL_BLENDER_RENDER',flush=True)
sys.addaudithook(audit)
try:
    result=bound.run_session(prepared['parent'],execute=True)
except BaseException as exc:
    result={'state':'EXECUTION_EXCEPTION','exception':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'automatic_retries':0,'delivered':False}
finally:
    l6.write_once(PROOF/'ACTUAL_EFFECT_AUDIT.json',events)
l6.write_once(PROOF/'ACTUAL_ENTRY_RESULT.json',result)
print(json.dumps(result,ensure_ascii=True),flush=True)
