import os,sys,json
from pathlib import Path
ROOT=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final-3'
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
os.environ['PYTHONDONTWRITEBYTECODE']='1'
from scenario_a import l6_pipeline as l6,l7_feedback_controller as controller
v=l6.read_json(PROOF/'ACTUAL_VALIDATION.json'); ids=v['ids']; c=ROOT/'runs/l7'/ids['correction']
assert v['classification']=='SEMANTIC_CLOSURE_FAILED' and not v['INTERNAL_ACCEPT']
assert (v['actual_post_count'],v['geometry_post_count'],v['semantic_reviewer_count'],v['blender_render_count'],v['correction_dispatch_count'])==(5,2,3,2,1)
assert len(v['image_evidence'])==11
assert all(r['data']['process_exit_code']==0 and r['data']['invocation_status']=='SUCCESS' for r in v['reviews'])
assert [r['result']['verdict'] for r in v['reviews']]==['PASS','REVISE','REVISE']
assert all(w['history_validation']['completed'] and w['history_validation']['status_str']=='success' for w in v['worker_reports'])
assert v['L7_stream_contract']['status']=='PASS' and v['L7_stream_contract']['correction_started']
budget=controller.budgets(c)
assert budget['revision']=={'limit':1,'consumed':1,'remaining':0}
assert v['canonical_result']['reason']=='REVISION_BUDGET_EXHAUSTED' and not v['canonical_result']['errors']
assert v['source_test_changes']==0 and not v['historical_changed_files'] and v['obvious_secret_pattern_hits']==0
l6.write_once(PROOF/'POSTPROOF_VERIFICATION.json',{'status':'PASS','classification':'SEMANTIC_CLOSURE_FAILED','FRESH_SESSION_REFRESH_PROOF':'NOT_VERIFIED','production_entry_count':1,'actual_worker_comfy_count':5,'geometry_count':2,'reviewer_count':3,'reviewer_exits':[0,0,0],'reviewer_verdicts':['PASS','REVISE','REVISE'],'blender_count':2,'correction_dispatch_count':1,'correction_budget':budget,'image_evidence_count':11,'current_history_success':5,'current_artifact_lineage_and_terminal_references':'Validated by canonical checked_child/checked_review/validate_source and hash checks','L7_stream_contract':'Actual .stdout.txt and .stderr.txt FileReferences validate; correction preflight and dispatch succeeded','mandatory_criteria_final':{'FORM_SILHOUETTE':'UNMET','GEO_APERTURE':'UNCERTAIN','GEO_READABILITY':'UNMET'},'INTERNAL_ACCEPT':False,'geometry_generation_root_cause':'UNKNOWN; semantic failure does not establish a new source/contract defect','source_test_changes':0,'historical_changes':0,'retry_resume_delivery_count':0,'publication_policy':'CP2 stages only fresh authorized namespaces with command-local core.autocrlf=false, preserving exact current evidence bytes without persistent Git setting or history rewrite.'})
with (PROOF/'FINAL_RESULT.md').open('a',encoding='utf-8') as f:
    f.write('\nFinal geometry criteria: FORM_SILHOUETTE UNMET, GEO_APERTURE UNCERTAIN, GEO_READABILITY UNMET. The square surfaces in diagnostics do not establish an actual chamber aperture. Geometry-generation root cause is UNKNOWN. All three production semantic Reviewer invocations succeeded with exit 0; this is not Reviewer runtime failure. All five Worker histories completed with success. L7 actual stream references and correction preflight/dispatch/re-review worked. Revision consumed 1/1, remaining 0; no additional action follows the final suggested_action. FRESH SESSION / REFRESH PROOF = NOT VERIFIED.\n')
with (PROOF/'drivers/finalize_cp2.py').open('xb') as f: f.write(Path(__file__).read_bytes())
print(json.dumps({'postproof_verification':'PASS','classification':v['classification'],'revision_budget':budget['revision'],'source_test_changes':0,'INTERNAL_ACCEPT':False}),flush=True)
