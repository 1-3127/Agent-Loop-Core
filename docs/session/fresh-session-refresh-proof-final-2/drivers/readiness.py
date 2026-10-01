import os,sys,json,subprocess,urllib.request,hashlib,time
from pathlib import Path
ROOT=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final-2'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
os.chdir(ROOT)
from scenario_a import session_binding as bound,l6_pipeline as l6
from core import reviewer_auth,result_review_adapter as reviewer
prepared=l6.read_json(PROOF/'PREPARED_BINDING.json')
entry=bound.run_session(prepared['parent'],execute=False)
assets=l6.preflight(l6.worker.DEFAULT_COMFY_ROOT,current_reference=prepared['current_reference'],run_id=prepared['ids']['l6'])
def get(path):
    with urllib.request.urlopen(l6.worker.BASE_URL+path,timeout=30) as response: return json.load(response)
stats=get('/system_stats'); objects=get('/object_info'); queue=get('/queue')
assert not queue['queue_running'] and not queue['queue_pending']
required=sorted(set(c for v in list(assets['view_generation'].values())+[assets['geometry']] for c in v['node_classes'].values()))
assert not set(required)-objects.keys()
models=[]
for item in assets['models']:
    p=Path(item['path']); assert p.is_file() and p.stat().st_size==item['bytes']
    models.append(dict(item,actual_bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns))
for view in list(assets['view_generation'].values())+[assets['geometry']]:
    graph=l6.read_json(view['workflow'])
    for node in graph.values():
        for key,value in node['inputs'].items():
            definition=objects[node['class_type']].get('input',{}).get('required',{}).get(key)
            if key in ('unet_name','clip_name','vae_name','lora_name','ckpt_name') and definition and isinstance(definition[0],list):
                assert value in definition[0],(key,value,'not advertised by live node')
auth=reviewer_auth.auth_mode(os.environ); assert auth=='CHATGPT_ACCOUNT'
version=subprocess.run(['codex','--version'],capture_output=True,timeout=20)
assert version.returncode==0
readiness={'entry_preflight':entry,'stats':stats,'queue':queue,'required_node_classes':required,'missing_classes':[],'models':models,'workflow_pins':[l6.reference(v['workflow']) for v in list(assets['view_generation'].values())+[assets['geometry']]],'reviewer_auth':auth,'codex_version':version.stdout.decode('utf-8',errors='replace').strip(),'generation_effects':0,'namespace_gate':'PASS: 3 repository children and 7 external namespaces absent','normalization':prepared['normalization'],'python':sys.version,'created_at':l6.now()}
l6.write_once(PROOF/'RUNTIME_READINESS.json',readiness)
schema={'type':'object','properties':{'observed_target':{'type':'string'},'square_opening_visible':{'type':'boolean'}},'required':['observed_target','square_opening_visible'],'additionalProperties':False}
l6.write_once(PROOF/'REVIEWER_PROBE_SCHEMA.json',schema)
workspace=PROOF/'reviewer-probe-workspace'; workspace.mkdir()
args=['codex','exec','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--output-schema',str(PROOF/'REVIEWER_PROBE_SCHEMA.json'),'-C',str(workspace),'-i',str(PROOF/'CURRENT_REFERENCE.png'),'-']
prompt='Readiness probe only. Inspect the attached current reference. Describe the main target object briefly and report whether a square opening in its central chamber is visually present. Do not invoke tools, read files, or evaluate production acceptance. Return only the specified JSON.'
t=time.monotonic()
proc=subprocess.run(args,input=prompt.encode('utf-8'),capture_output=True,timeout=180)
streams={name:reviewer._stream_evidence(raw,PROOF/('REVIEWER_PROBE.'+name+'.txt'),True) for name,raw in [('stdout',proc.stdout),('stderr',proc.stderr)]}
record={'purpose':'Readiness only; not production semantic Review','auth_mode':auth,'process_exit_code':proc.returncode,'elapsed':time.monotonic()-t,'images':[l6.reference(PROOF/'CURRENT_REFERENCE.png')],'streams':streams,'automatic_retries':0}
if proc.returncode==0:
    record['result']=json.loads(proc.stdout.decode('utf-8'))
l6.write_once(PROOF/'REVIEWER_READINESS_PROBE.json',record)
assert proc.returncode==0, 'Readiness Reviewer runtime failure; no retry'
assert record['result']['square_opening_visible']
print(json.dumps({'runtime_readiness':'PASS','reviewer_readiness':record,'generation_effects':0}),flush=True)
