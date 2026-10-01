import os,sys,json,shutil,re,subprocess
from pathlib import Path
ROOT=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final-2'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from scenario_a import session_binding as bound,l6_pipeline as l6,l7_geometry_review as bridge
p=l6.read_json(PROOF/'PREPARED_BINDING.json');v=l6.read_json(PROOF/'ACTUAL_VALIDATION.json')
assert v['final_verdict']=='CONTRACT_DEFECT_FOUND' and not v['INTERNAL_ACCEPT']
assert v['actual_post_count']==4 and v['semantic_reviewer_count']==2 and v['blender_render_count']==1
assert len(v['image_evidence'])==7
assert all(r['data']['process_exit_code']==0 and r['data']['invocation_status']=='SUCCESS' for r in v['reviews'])
assert all(w['history_validation']['completed'] and w['history_validation']['status_str']=='success' for w in v['worker_reports'])
for d in (ROOT/'runs/l6'/p['ids']['l6'],ROOT/'runs/l7'/p['ids']['bridge']):
    bound.checked_child(d,parent_ref=p['parent'])
    for ref in l6.read_json(d/'terminal.json')['records'].values():
        if ref: l6.reviewer.checked_ref(ref)
assert l6.checked_review(ROOT/'runs/l6'/p['ids']['l6'])['verdict']=='PASS'
assert bridge.checked_review(ROOT/'runs/l7'/p['ids']['bridge'])['verdict']=='REVISE'
for name in ('execute.py','collect.py','stop_defect.py','finalize_cp2.py'):
    shutil.copyfile(Path(__file__).parent/name,PROOF/'drivers'/name)
with (PROOF/'FINAL_RESULT.md').open('a',encoding='utf-8',newline='\n') as f:
    f.write('\nCurrent contract defect: bound bridge terminal records include review_invocation.json.stderr.txt and .stdout.txt. Controller validate_source reconstructs every non-instruction record as name + .json, so the geometry REVISE -> correction path requests the nonexistent review_invocation.json.stderr.json. Exact stack trace and identities are in CONTRACT_DEFECT_EVIDENCE.json and ACTUAL_ENTRY_RESULT.json. Correction directory/reservation/dispatch were never created. SessionBoundary.stop preserved a FAILED terminal with CONTRACT_DEFECT_FOUND. No patch, workaround, retry or resume.\n\nBoth production Reviewer processes completed SUCCESS / exit 0, with captured raw byte counts/hashes and sanitized stream metadata; this was not a Reviewer runtime failure. Geometry quality failed: all four diagnostic views are nearly featureless square surfaces, and LANTERN_FORM/APERTURE_GEOMETRY/GLB_READABILITY are UNMET. Geometry-generation root cause is not established by this proof.\n\nRegression clarification: first full run had 258 passes and 3 proof-wrapper errors; all 3 exact local import/pipe tests then passed. REGRESSION_VERIFIED.json records the combined 261-test coverage, while the original raw errors are retained.\n')
scope=[PROOF,ROOT/'runs/session'/p['ids']['session'],ROOT/'runs/l6'/p['ids']['l6'],ROOT/'runs/l7'/p['ids']['bridge']]
suspects=[];checked=0
for root in scope:
    for file in root.rglob('*'):
        if not file.is_file() or file.suffix not in ('.json','.md','.txt','.log','.py'): continue
        text=file.read_text(encoding='utf-8',errors='replace');checked+=1
        if re.search(r'\bsk-[A-Za-z0-9_-]{16,}|\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',text): suspects.append(str(file))
assert not suspects,suspects
l6.write_once(PROOF/'POSTPROOF_VERIFICATION.json',{'status':'PASS','source_test_changes':0,'historical_evidence_preserved':True,'terminal_record_hashes_valid':True,'current_review_lineage_valid':True,'worker_history_completed_success':4,'generated_views':[768,768],'diagnostic_renders':[512,512],'reviewer_exits':[0,0],'reviewer_verdicts':['PASS','REVISE'],'production_entry_count':1,'correction_dispatch_count':0,'retry_resume_delivery_count':0,'publication_text_files_checked':checked,'obvious_secret_pattern_hits':0,'final_verdict':'CONTRACT_DEFECT_FOUND'})
print(json.dumps({'postproof_verification':'PASS','final_verdict':'CONTRACT_DEFECT_FOUND','evidence_images':len(v['image_evidence']),'source_test_changes':0}),flush=True)
