import os,sys,json,shutil,subprocess
from pathlib import Path
ROOT=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final-3'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
os.chdir(ROOT)
from scenario_a import session_binding as bound,l6_pipeline as l6
p=l6.read_json(PROOF/'PREPARED_BINDING.json'); r=l6.read_json(PROOF/'REGRESSION_RESULT.json')
assert r['pass'] and r['tests']==277 and r['failures']==r['errors']==0
assert r['tripwires']['network']==r['tripwires']['production_process']==0
runtime=l6.read_json(PROOF/'RUNTIME_READINESS.json'); probe=l6.read_json(PROOF/'REVIEWER_READINESS_PROBE.json')
assert runtime['reviewer_auth']=='CHATGPT_ACCOUNT' and probe['process_exit_code']==0
preflight=bound.run_session(p['parent'],execute=False)
baseline=l6.read_json(PROOF/'STARTING_SNAPSHOT.json')
assert all(l6.digest(ROOT/n)==sha for n,sha in baseline['tracked_file_sha256'].items())
assert subprocess.check_output(['git','rev-parse','HEAD'],encoding='utf-8').strip()==baseline['start_head']
drivers=PROOF/'drivers'; drivers.mkdir()
for name in ('prepare.py','regression.py','readiness.py','freeze_cp1.py','execute.py'):
    with (drivers/name).open('xb') as f: f.write((Path(__file__).parent/name).read_bytes())
data={'status':'READINESS_PASS','ids':p['ids'],'request':l6.reference(PROOF/'CURRENT_REQUEST.md'),'reference':p['original'],'current_reference':p['current_reference'],'frozen_specification':p['frozen_specification'],'specification_identity_sha256':p['specification_identity_sha256'],'binding_identity_sha256':p['binding_identity_sha256'],'stage_criteria':p['stage_criteria'],'normalization':p['normalization'],'regression':r,'runtime':l6.reference(PROOF/'RUNTIME_READINESS.json'),'reviewer_probe':l6.reference(PROOF/'REVIEWER_READINESS_PROBE.json'),'entry_preflight':preflight,'C01':'PASS: all five blocking criteria explicitly assigned to observable stages','I03':'PASS: 3 repository children and 7 external namespaces absent','generation_effects':0,'readiness_image_transport_probe':1,'previous_session_resume':0,'source_test_changes':0,'delivery':False}
l6.write_once(PROOF/'READINESS_ENVIRONMENT_INCIDENTS.json',{'incidents':[{'step':'Initial sandbox Git ls-remote','exit_code':1,'error':'schannel: AcquireCredentialsHandle failed: SEC_E_NO_CREDENTIALS (0x8009030e)','resolution':'Same read-only query in authorized host context succeeded; expected live HEAD verified.'},{'step':'Initial C:\\Python314 Python inspection','exit_code':1,'error':"ModuleNotFoundError: No module named 'PIL'",'resolution':'Used existing bundled Python runtime with Pillow; no installation or system modification.'},{'step':'PowerShell text display','error':'UTF-8 output displayed incorrectly; attempted .NET decoding blocked by constrained language.','resolution':'Read existing UTF-8 files through bundled Python with PYTHONIOENCODING=utf-8.'}],'production_effects':0,'same_attempt_reviewer_retry':0})
l6.write_once(PROOF/'CP1_READINESS.json',data)
with (PROOF/'CP1_READINESS.md').open('x',encoding='utf-8') as f:
    f.write('# CP1 — Fresh Session Final-3 Readiness\n\nREADINESS_PASS. Full current regression: 277/277 PASS; synthetic tests with production effects zero. Actual generation effects: 0. One separate current-reference CHATGPT_ACCOUNT readiness probe succeeded.\n\nNew Session/Loop and independently frozen specification; current attachment bytes are authority. Original and newly computed normalized identities match expected hashes. C-01 applicability and I-03 whole-entry namespace gates passed. Live Comfy endpoint, required nodes/model advertisements, pinned workflows/models and Blender executable/script checked. L7 stream handling is included in current regression.\n\nCanonical production entry may now be dispatched once after CP1 commit/publication. Existing worker/reviewer/renderer/revision caps are unchanged. Stop at INTERNAL_ACCEPT or actual failure; no Delivery or closure. No source/test or historical evidence modifications.\n')
print(json.dumps({'CP1':'READINESS_PASS','tests':r['tests'],'ids':p['ids'],'generation_effects':0}),flush=True)
