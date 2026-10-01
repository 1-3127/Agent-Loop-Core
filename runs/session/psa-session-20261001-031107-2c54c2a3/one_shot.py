"""Proof-only one-shot driver; existing production entry and observation only."""
import json, os, pathlib, sys, traceback
from urllib.parse import urlsplit
ROOT=pathlib.Path('D:/VSCODE-WorkSpace/Others/Agent-Loop-Core')
sys.path.insert(0,str(ROOT/'src'))
from scenario_a import session_binding as bound, l6_pipeline as l6
from core import reviewer_auth
d=pathlib.Path(__file__).resolve().parent
ready=l6.read_json(d/'checkpoint1_ready.json')
assert ready['verdict']=='ACTUAL_EXECUTION_READY'
data,boundary,binding=bound.checked_parent(ready['session_binding'],execution=True)
assert reviewer_auth.auth_mode(os.environ)=='CHATGPT_ACCOUNT'
for p,h in ready['source_contracts'].items(): assert l6.digest(ROOT/p)==h
assert binding.specification.identity_sha256==ready['specification_identity_sha256']
assert not (d/'actual_invocation.json').exists()
assert bound.run_session(ready['session_binding'],execute=False)['status']=='PREFLIGHT_PASS'
events=(d/'actual_events.jsonl').open('x',encoding='utf-8')
counts={'comfy_prompt_attempts':0,'semantic_process_attempts':0,'blender_process_attempts':0}
def log(item):
    item['observed_at']=l6.now()
    events.write(json.dumps(item,ensure_ascii=False)+'\n');events.flush();os.fsync(events.fileno())
def audit(event,args):
    if event=='urllib.Request':
        url,payload,headers,method=args
        item={'event':event,'url':url,'method':method}
        if method=='POST' and urlsplit(url).path=='/prompt':
            counts['comfy_prompt_attempts']+=1
            p=d/('actual_http_submission_%02d.json'%counts['comfy_prompt_attempts'])
            with p.open('xb') as f:f.write(payload)
            item['body']=l6.reference(p)
        log(item)
    elif event=='subprocess.Popen':
        executable,command,cwd,environment=args
        label=(str(executable)+' '+str(command)).lower()
        if 'codex' in label and 'exec' in label:
            counts['semantic_process_attempts']+=1;category='semantic_reviewer'
        elif 'blender.exe' in label:
            counts['blender_process_attempts']+=1;category='blender_production'
        else:category='administrative_or_other'
        log({'event':event,'category':category,'executable':str(executable),'command':command,'cwd':str(cwd) if cwd else None})
sys.addaudithook(audit)
l6.write_once(d/'actual_invocation.json',{'started_at':l6.now(),'entry':'scenario_a.session_binding.run_session','execute':True,'session_binding':ready['session_binding'],'driver':l6.reference(__file__),'automatic_retries':0,'worker_timeout':600,'review_timeout':600,'render_timeout':600})
try:
    result=bound.run_session(ready['session_binding'],execute=True)
    l6.write_once(d/'actual_result.json',{'finished_at':l6.now(),'result':result,'observed_attempt_counts':counts})
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
except BaseException as exc:
    l6.write_once(d/'actual_exception.json',{'finished_at':l6.now(),'type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'observed_attempt_counts':counts})
    print('ONE_SHOT_EXCEPTION '+type(exc).__name__+': '+str(exc),flush=True)
    raise
finally:events.close()
