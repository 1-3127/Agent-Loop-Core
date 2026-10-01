import pathlib,json,sys,shutil,hashlib,subprocess
ROOT=pathlib.Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
WORK=pathlib.Path(__file__).resolve().parent
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final'
sys.path.insert(0,str(ROOT/'src'))
from scenario_a import session_binding as bound,l6_pipeline as l6
prepared=json.loads((PROOF/'PREPARED_BINDING.json').read_text(encoding='utf-8'))
initial=json.loads((WORK/'regression_result.json').read_text(encoding='utf-8'))
smoke=json.loads((WORK/'import_smoke_check.json').read_text(encoding='utf-8'))
log=(WORK/'regression.log').read_text(encoding='utf-8')
assert initial['tests']==244 and initial['errors']==1 and initial['failures']==initial['skips']==0
assert log.count('\nERROR: ')==1 and 'ERROR: test_single_src_root_imports_core_and_active_scenario' in log
assert 'RuntimeError: Regression production process denied' in log
assert initial['tripwires']=={'network':0,'production_process':1,'import_smoke_process':0}
assert smoke['pass'] and smoke['tests']==1 and smoke['tripwires']=={'network':0,'production_process':0,'import_smoke_process':1}
regression={'pass':True,'tests':244,'resolved_failures':0,'resolved_errors':0,'skips':0,'full_discovery':initial,'targeted_import_smoke_rerun':smoke,'basis':'243 passed in full discovery; exactly one import-only subprocess was denied by the proof wrapper before start because Windows audit supplies command as str. Exact existing test passes with list2cmdline-aware allowlist. No source/test change; no production subprocess executed. Initial raw error preserved.'}
probe=json.loads((PROOF/'REVIEWER_READINESS_PROBE.json').read_text(encoding='utf-8'))
assert probe['pass'] and probe['image_transfer'] is False
for name in ('regression.log','regression_result.json','import_smoke_check.log','import_smoke_check.json','import_smoke_check.py','prepare_proof.py','regression.py','execute_proof.py','reviewer_transport_probe.py'):
    shutil.copyfile(WORK/name,PROOF/name)
baseline=json.loads((PROOF/'starting_snapshot.json').read_text(encoding='utf-8'))
changed=[name for name,h in baseline['tracked_hashes'].items() if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=h]
assert not changed, changed
checks=bound.run_session(prepared['parent'],execute=False)
live=subprocess.check_output(['git','-c','safe.directory='+str(ROOT),'-C',str(ROOT),'ls-remote','origin','refs/heads/stabilization-reference-dimension-normalization'],encoding='utf-8').split()[0]
assert live==baseline['head']
cp1={'status':'READINESS_PASS','time':l6.now(),'generation_effects':0,'delivery_effects':0,'entry':'scenario_a.session_binding.run_session(parent, execute=True)','parent':prepared['parent'],'ids':prepared['ids'],'specification_identity_sha256':prepared['specification_identity_sha256'],'original':prepared['original'],'normalization':prepared['normalization'],'stage_criteria':prepared['stage_criteria'],'canonical_preflight':checks,'regression':regression,'reviewer_readiness':probe,'source_test_changes':0,'starting_tracked_changed':changed,'live_starting_branch':live,'normalized_staging':'Canonical entry will exclusively stage exact preview bytes after I-03 and before first Worker POST. Pre-submission audit verifies real staging and Work Order lineage. No precreated attempt namespace or validator bypass.'}
with (PROOF/'CP1_READINESS.json').open('x',encoding='utf-8') as stream: json.dump(cp1,stream,ensure_ascii=False,indent=2); stream.write('\n')
text='# CP1 final fresh-session readiness\n\nREADINESS_PASS; generation effects 0; Delivery 0.\n\nNew current request, original attachment authority, independently frozen Specification and all fresh identities are in PREPARED_BINDING.json. Original 467x539; normalized execution preview 768x768 with padding only and unchanged original pixel rectangle. All current criterion selections and budgets are frozen.\n\nRegression resolved: all 244 existing tests verified. Initial full discovery: 243 PASS plus one audit-wrapper error (Windows import-only subprocess command is str). Exact existing import smoke rerun with correct command comparison: 1/1 PASS. Both original logs/results preserved; no single clean full run is claimed. Production subprocess executed 0 and network 0; import-only subprocess executed 1. C-01/I-03 and current reference binding/normalization are included. All starting tracked bytes remain identical.\n\nCanonical full-capability preflight PASS; 3 child and 7 external namespaces absent; pinned 4 workflows / 6 models available; registered node classes available; ComfyUI live queue empty; Blender version verified; ChatGPT auth and non-image Codex CLI structured transport PASS. No independent vision diagnostic was performed: automatic approval review rejected the separate attached-PNG readiness transmission. This boundary is preserved; canonical production semantic Review is the expressly requested proof operation and remains to be observed.\n\nActual entry consumes the frozen original authority and stages its normalized derivative itself before its first Worker dispatch. CP1 preview is expected-byte evidence, not an external precreated attempt. The read-only pre-submission audit verifies actual Session/Spec/attempt/staging/Work Order lineage without replacing adapters or modifying source.\n\nNext authorized operation: the one canonical production entry, bounded caps unchanged, stop at INTERNAL_ACCEPT or actual failure. Delivery is excluded.\n'
with (PROOF/'CP1_READINESS.md').open('x',encoding='utf-8') as stream: stream.write(text)
print(json.dumps({'cp1':'READINESS_PASS','ids':prepared['ids'],'regression':regression}),flush=True)
