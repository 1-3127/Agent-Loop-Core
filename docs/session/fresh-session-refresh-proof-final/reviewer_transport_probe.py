import subprocess, pathlib, json, time, os
ROOT=pathlib.Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final'
schema=PROOF/'reviewer_transport_schema.json'
with schema.open('x',encoding='utf-8') as stream: json.dump({'type':'object','properties':{'ready':{'type':'boolean'}},'required':['ready'],'additionalProperties':False},stream)
args=['codex','exec','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--output-schema',str(schema),'-C',str(PROOF),'-']
prompt='Transport readiness check only. No images, private content or production task are included. Do not use tools or inspect files. Return JSON with ready true.'
start=time.monotonic()
proc=subprocess.run(args,input=prompt,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180,env=dict(os.environ,CODEX_HOME=os.environ.get('CODEX_HOME') or 'C:/Users/Worker/.codex'))
try: output=json.loads(proc.stdout)
except ValueError: output=None
record={'mode':'CODEX_CLI_NO_IMAGE_TRANSPORT_READINESS','production_reviewer_invocations':0,'diagnostic_transport_invocations':1,'image_diagnostic_invocations':0,'image_transfer':False,'vision_preflight':'not independently probed; private-image diagnostic explicitly rejected; actual production evidence remains required','process_started':True,'exit_code':proc.returncode,'seconds':time.monotonic()-start,'args':args,'output':output,'pass':proc.returncode==0 and output=={'ready':True},'rejected_action':'separate current attached PNG vision readiness probe','rejection_reason':'auto-review: general proof authorization did not clearly cover separate private-image diagnostic to Codex CLI'}
with (PROOF/'REVIEWER_READINESS_PROBE.json').open('x',encoding='utf-8') as stream: json.dump(record,stream,indent=2); stream.write('\n')
print(json.dumps(record),flush=True)
