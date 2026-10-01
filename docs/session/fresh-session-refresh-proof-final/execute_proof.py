import pathlib, sys, json, os, datetime, hashlib, traceback
from dataclasses import asdict
ROOT=pathlib.Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final'
sys.path.insert(0,str(ROOT/'src'))
from scenario_a import session_binding as bound, l6_pipeline as l6
prepared=json.loads((PROOF/'PREPARED_BINDING.json').read_text(encoding='utf-8'))
cp1=json.loads((PROOF/'CP1_READINESS.json').read_text(encoding='utf-8'))
assert cp1['status']=='READINESS_PASS' and cp1['generation_effects']==0
ids=prepared['ids']
run_dir=ROOT/'runs/l6'/ids['l6']
comfy=l6.worker.DEFAULT_COMFY_ROOT
assert not run_dir.exists()
bound.run_session(prepared['parent'],execute=False)
reservation=PROOF/'PRODUCTION_ENTRY_RESERVATION.json'
with reservation.open('x',encoding='utf-8') as stream:
    json.dump({'entry':'scenario_a.session_binding.run_session','execute':True,'ids':ids,'parent':prepared['parent'],'created_at':l6.now(),'automatic_retries':0,'delivery':False},stream,indent=2)
events=[]
def audit(event,args):
    if event=='urllib.Request' and args[0].rstrip('/')==l6.worker.BASE_URL+'/prompt':
        l6.validate_current_staging(run_dir)
        staging=l6.read_json(run_dir/'reference_staging.json')
        parent,boundary,binding=bound.checked_parent(prepared['parent'],execution=True)
        graph=json.loads(args[1])['prompt']
        expected='l6/'+ids['l6']+'/front.png'
        assert graph['1']['inputs']['image']==expected
        assert staging['normalization']==prepared['normalization']
        assert staging['current_reference']==prepared['current_reference']
        assert staging['normalized_execution']['sha256']==prepared['normalization']['normalized_sha256']
        assert staging['staged']['width']==768 and staging['staged']['height']==768
        assert binding.specification.identity_sha256==prepared['specification_identity_sha256']
        orders=list(run_dir.glob('*_work_order.json'))
        record={'event':'COMFY_PROMPT_BEFORE_SUBMISSION','time':l6.now(),'index':1+sum(e['event']=='COMFY_PROMPT_BEFORE_SUBMISSION' for e in events),'front_input':expected,'graph_sha256':hashlib.sha256(args[1]).hexdigest(),'staging':l6.reference(run_dir/'reference_staging.json'),'normalized_input':staging['normalized_execution'],'specification_identity_sha256':binding.specification.identity_sha256,'parent':prepared['parent'],'work_orders':[l6.reference(p) for p in orders],'old_source_fallback':0}
        events.append(record)
        with (PROOF/f"pre_submission_{record['index']}.json").open('x',encoding='utf-8') as stream: json.dump(record,stream,indent=2)
        print('ACTUAL_FRONT_INPUT_VERIFIED '+str(record['index'])+' '+expected,flush=True)
    if event=='subprocess.Popen':
        command=args[1]
        if isinstance(command,(list,tuple)):
            if 'exec' in command and 'codex' in str(command[0]).lower():
                image_paths=[pathlib.Path(command[i+1]) for i,v in enumerate(command[:-1]) if v=='-i']
                events.append({'event':'CANONICAL_SEMANTIC_REVIEWER_PROCESS','time':l6.now(),'images':[{'path':str(p),'sha256':l6.digest(p)} for p in image_paths],'count':len(image_paths)})
                print('CANONICAL_SEMANTIC_REVIEWER_START images='+str(len(image_paths)),flush=True)
            elif 'blender' in str(command[0]).lower():
                events.append({'event':'CANONICAL_BLENDER_PROCESS','time':l6.now()})
                print('CANONICAL_BLENDER_START',flush=True)
sys.addaudithook(audit)
try:
    result=bound.run_session(prepared['parent'],execute=True)
except BaseException as exc:
    result={'state':'EXECUTION_EXCEPTION','exception':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'automatic_retries':0,'delivered':False}
finally:
    with (PROOF/'ACTUAL_EFFECT_AUDIT.json').open('x',encoding='utf-8') as stream: json.dump(events,stream,indent=2); stream.write('\n')
with (PROOF/'ACTUAL_ENTRY_RESULT.json').open('x',encoding='utf-8') as stream: json.dump(result,stream,ensure_ascii=False,indent=2); stream.write('\n')
print(json.dumps(result,ensure_ascii=True),flush=True)
