import os,sys,json,shutil,subprocess
from pathlib import Path
ROOT=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final-2'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
os.chdir(ROOT)
from scenario_a import session_binding as bound,l6_pipeline as l6
p=l6.read_json(PROOF/'PREPARED_BINDING.json')
reg=l6.read_json(PROOF/'REGRESSION_VERIFIED.json'); assert reg['pass'] and reg['tests']==261
assert l6.read_json(PROOF/'REVIEWER_READINESS_PROBE.json')['process_exit_code']==0
entry=bound.run_session(p['parent'],execute=False)
checkpoint={'status':'READINESS_PASS','generation_effects':0,'ids':p['ids'],'parent':p['parent'],'reference_sha256':p['current_reference']['file']['sha256'],'normalized_sha256':p['normalization']['normalized_sha256'],'specification_identity_sha256':p['specification_identity_sha256'],'criteria':p['stage_criteria'],'regression':l6.reference(PROOF/'REGRESSION_VERIFIED.json'),'runtime':l6.reference(PROOF/'RUNTIME_READINESS.json'),'reviewer_readiness':l6.reference(PROOF/'REVIEWER_READINESS_PROBE.json'),'namespace_preflight':entry,'delivery':False}
l6.write_once(PROOF/'CP1_READINESS.json',checkpoint)
(PROOF/'CP1_READINESS.md').write_text('# CP1 — READINESS_PASS\n\nCurrent direct request/reference, independently derived frozen specification, new Session/Loop, C-01 applicability, I-03 namespaces, pinned workflows/models, ComfyUI API and CHATGPT_ACCOUNT image probe validated. Regression: 258 original passes plus 3 wrapper-blocked tests successfully rechecked = 261/261 covered; first raw 3-error result retained. Generation effects: 0. Probe is readiness evidence only. Stop at INTERNAL_ACCEPT or actual terminal failure; no retry or Delivery.\n',encoding='utf-8')
drivers=PROOF/'drivers';drivers.mkdir()
for name in ('prepare.py','regression.py','readiness.py','freeze_cp1.py','execute.py','collect.py'):
    shutil.copyfile(Path(__file__).parent/name,drivers/name)
protection=l6.read_json(PROOF/'HISTORICAL_PROTECTION.json')
assert all(l6.digest(ROOT/k)==v for k,v in protection['tracked_file_sha256'].items())
print(json.dumps(checkpoint),flush=True)
