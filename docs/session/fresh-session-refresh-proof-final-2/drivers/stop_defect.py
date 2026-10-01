import os,sys,json
from pathlib import Path
ROOT=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final-2'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from scenario_a import session_binding as bound,l6_pipeline as l6
p=l6.read_json(PROOF/'PREPARED_BINDING.json'); result=l6.read_json(PROOF/'ACTUAL_ENTRY_RESULT.json')
assert result['exception']=='FileNotFoundError' and 'review_invocation.json.stderr.json' in result['error']
data,boundary,binding=bound.checked_parent(p['parent'])
bridge=ROOT/'runs/l7'/p['ids']['bridge']; terminal=l6.read_json(bridge/'terminal.json')
records={k:v for k,v in terminal['records'].items() if 'stdout' in k or 'stderr' in k}
for record in records.values(): l6.reviewer.checked_ref(record)
assert any(v['path'].endswith('.stderr.txt') for v in records.values())
assert not (ROOT/'runs/l7'/p['ids']['correction']).exists()
stopped=boundary.stop('FAILED','CONTRACT_DEFECT_FOUND: correction source validation assumes .json for Reviewer .txt stream evidence')
l6.write_once(PROOF/'CONTRACT_DEFECT_EVIDENCE.json',{'classification':'CONTRACT_DEFECT_FOUND','trigger':'Current geometry REVISE -> canonical controller.run_feedback -> validate_source','actual_entry_result':l6.reference(PROOF/'ACTUAL_ENTRY_RESULT.json'),'bridge_terminal':l6.reference(bridge/'terminal.json'),'observed_stream_records':records,'expected_wrong_path':str(bridge/'review_invocation.json.stderr.json'),'actual_existing_path':str(bridge/'review_invocation.json.stderr.txt'),'source_identity':l6.reference(ROOT/'src/scenario_a/l7_feedback_controller.py'),'source_lines':'validate_source lines 55-63: p.stem record keys followed by hard-coded .json except review_instructions','correction_dispatches':0,'source_test_changes':0,'workaround':0,'retry':0,'same_session_resume':0,'session_stop':{'identity':stopped.identity,'path':stopped.path,'sha256':stopped.sha256},'historical_failure_root_cause_inference':'None; this is current attempt evidence only'})
print(json.dumps({'classification':'CONTRACT_DEFECT_FOUND','session_outcome':boundary.outcome.status,'terminal':str(boundary.directory/'terminal.json')}),flush=True)
