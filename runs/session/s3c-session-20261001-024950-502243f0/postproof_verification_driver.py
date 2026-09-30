"""Read completed actual evidence; preserve failed acceptance and bounded stop."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
sys.path.insert(0,str(ROOT/'src'))
from scenario_a import l6_pipeline as l6
from scenario_a import l7_geometry_review as bridge
from scenario_a import l7_feedback_controller as correction
from scenario_a import session_binding as bound

d=ROOT/'runs/session/s3c-session-20261001-024950-502243f0'
ready=l6.read_json(d/'checkpoint1_ready.json')
ids=ready['identities']
l6d=ROOT/'runs/l6'/ids['l6']; bd=ROOT/'runs/l7'/ids['bridge']; cd=ROOT/'runs/l7'/ids['correction']
directories=[d,l6d,bd,cd]
def files_snapshot():
    return {str(p):l6.digest(p) for q in directories for p in q.rglob('*') if p.is_file()}
before_validation=files_snapshot()
phase='validation'
def audit(event,args):
    if phase=='validation' and event in ('subprocess.Popen','urllib.Request','socket.connect'):
        raise RuntimeError('POST_PROOF_VALIDATION_MUST_BE_EFFECT_FREE: '+event)
sys.addaudithook(audit)
data,boundary,binding=bound.checked_parent(ready['session_binding'])
assert binding.specification.reference.specification_sha256==ready['specification']['sha256']
assert binding.specification.identity_sha256==ready['specification']['identity_sha256']
assert l6.png_identity(ready['source']['path'],'front')==ready['source']
for q in [l6d,bd,cd]:bound.checked_child(q,parent_ref=ready['session_binding'])
mv=l6.checked_review(l6d)
initial_review=bridge.checked_review(bd)
final_review=correction.checked_review(cd,'geometry')
initial_source=bridge.validate_l6(l6d,ready['session_binding'])
initial_render=bridge.validate_render_manifest(bd)
final_glb=correction.validate_geometry(cd)
final_render=correction.validate_render_manifest(cd)
assert initial_render['source_glb']==initial_source['artifact']
assert final_render['source_glb']==final_glb
assert mv['verdict']=='PASS'
assert initial_review['verdict']==final_review['verdict']=='REVISE'
assert initial_review['suggested_action']=={'code':'REGENERATE_GEOMETRY','target':'geometry'}
assert (cd/'revision_reservation.json').is_file()
action=l6.read_json(cd/'revision_action.json')
assert action['revision_ordinal']==1 and action['revision_seed']==action['previous_seed']+1
assert action['previous_seed']==528364197559477
terminals=[l6.read_json(q/'terminal.json') for q in [l6d,bd,cd]]
assert [t['state'] for t in terminals]==['GEOMETRY_READY','GEOMETRY_REVIEWED','ABORT']
assert terminals[-1]['reason']=='REVISION_BUDGET_EXHAUSTED'
assert boundary.outcome.status=='ABORT' and boundary.outcome.terminal and not boundary.outcome.delivered
assert not any((d/name).exists() for name in ['internal_accept.json','scenario_a_accept.json','delivery_package.json'])
assert files_snapshot()==before_validation, 'existing actual proof evidence changed during validation'
phase='post_validation'

reports=[]
for q in [l6d,cd]:
    for p in sorted(q.glob('*_worker_report.json')):
        x=l6.read_json(p)
        assert x['status']=='SUCCESS' and x['prompt_id']
        reports.append((p,x))
reviews=[]
for q,prefix,stage in [(l6d,'review','multiview'),(bd,'review','geometry'),(cd,'geometry_review','geometry')]:
    inv=l6.read_json(q/(prefix+'_invocation.json')); result=l6.read_json(q/(prefix+'_result.json'))
    req=l6.read_json(q/(prefix+'_request.json'))
    assert inv['invocation_status']=='SUCCESS' and inv['reviewer_process_started'] is True
    assert inv['reviewer_mode']=='CODEX_CLI' and inv['auth_mode']=='CHATGPT_ACCOUNT' and inv['process_exit_code']==0
    assert inv['attached_images']==[{k:a[k] for k in ('role','path','sha256')} for a in req['artifacts']]
    coverage=l6.read_json(q/(prefix+'_result_coverage.json'))
    assert coverage['coverage']==bound.validate_coverage(bound.review_contract(q,stage),result)
    reviews.append({'review_id':result['review_id'],'verdict':result['verdict'],'action':result['suggested_action'],
                    'request':l6.reference(q/(prefix+'_request.json')),'result':l6.reference(q/(prefix+'_result.json')),
                    'invocation':l6.reference(q/(prefix+'_invocation.json')),'coverage':l6.reference(q/(prefix+'_result_coverage.json')),
                    'criteria_coverage':coverage['coverage'],'attached_images':inv['attached_images'],
                    'duration_seconds':inv['duration_seconds']})
renderers=[l6.read_json(q/'renderer_invocation.json') for q in [bd,cd]]
assert all(x['status']=='SUCCESS' and x['process_started'] and x['exit_code']==0 for x in renderers)
actual=l6.read_json(d/'actual_result.json')
assert actual['result']['state']=='ABORT'
assert actual['observed_attempt_counts']=={'comfy_prompt_attempts':5,'semantic_process_attempts':3,'blender_process_attempts':2}
assert len(reports)==5 and len(reviews)==3 and len(renderers)==2
events=[json.loads(line) for line in (d/'actual_events.jsonl').read_text(encoding='utf-8').splitlines()]
submissions=[x for x in events if x.get('method')=='POST' and x['url'].endswith('/prompt')]
assert len(submissions)==5

histories=[]
for index,(path,report) in enumerate(reports,1):
    url='http://127.0.0.1:8188/history/'+report['prompt_id']
    with urllib.request.urlopen(url,timeout=20) as response:raw=json.load(response)
    entry=raw[report['prompt_id']]
    assert entry['status']['completed'] and entry['status']['status_str']=='success'
    assert report['output_node'] in entry['outputs']
    cached=[node for event in entry['status']['messages'] if event[0]=='execution_cached' for node in event[1]['nodes']]
    assert report['output_node'] not in cached, 'Save output node cached'
    hp=d/('actual_history_%02d.json'%index)
    l6.write_once(hp,{'observed_at':l6.now(),'url':url,'response':raw})
    histories.append({'stage':report['task_id'],'prompt_id':report['prompt_id'],'client_id':report['client_id'],
                      'report':l6.reference(path),'history':l6.reference(hp),'save_node_executed':True,
                      'started_at':report['started_at'],'completed_at':report['completed_at']})

protected=l6.read_json(d/'protection_before.json')
changed=[p for p,h in protected['tracked'].items() if l6.digest(ROOT/p)!=h]
assert not changed, changed
research=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop')
research_changed=[p for p,h in protected['research']['tracked'].items() if l6.digest(research/p)!=h]
assert not research_changed,research_changed
assert l6.digest(research/'ac6_f2b_resume.py')==protected['research']['wip_sha256']
def git(*args,root=ROOT):
    return subprocess.check_output(['git','-c','safe.directory='+root.as_posix(),'-C',str(root),*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD',root=research)==protected['research']['head']
assert git('status','--porcelain=v1',root=research)==protected['research']['status']
refs={line.split()[1]:line.split()[0] for line in git('show-ref').splitlines()}
for line in protected['refs'].splitlines():
    value,ref=line.split()
    if ref!='refs/heads/session-e2e-s3c':assert refs[ref]==value
external_changes=[]
for p,identity in protected['external'].items():
    q=Path(p); s=q.stat()
    now={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':l6.digest(q) if identity['sha256'] else None}
    if now!=identity:external_changes.append(p)
assert not external_changes, external_changes
protection_result={'existing_tracked_unchanged':len(protected['tracked']),
                   'research_tracked_unchanged':len(protected['research']['tracked']),
                   'research_wip_sha256':protected['research']['wip_sha256'],
                   'external_unchanged':len(protected['external']),'large_model_full_hash':False,
                   'protected_local_refs_unchanged':True,'runtime_source_diff':0,
                   'proof_evidence_validation_unchanged':True}

summary={'classification':'C — Semantic closure failure','actual_runtime_path':'EXECUTED',
         'actual_bound_loop':'NOT PASSED','actual_session_e2e':'NOT VERIFIED',
         'session_terminal':l6.reference(d/'terminal.json'),'session_status':boundary.outcome.status,
         'stop_reason':'REVISION_BUDGET_EXHAUSTED','specification':ready['specification'],
         'session_binding':ready['session_binding'],'identities':ids,'source':ready['source'],
         'actual_counts':{'worker_calls':5,'comfy_submissions':5,'semantic_reviewer':3,'blender_production':2,'correction_dispatch':1,'run_session_execute_true':1,'automatic_retries':0,'user_delivery_transport':0},
         'histories':histories,'reviews':reviews,'initial_glb':initial_source['artifact'],
         'final_candidate_glb':final_glb,'final_render_manifest':l6.reference(cd/'render_manifest.json'),
         'final_render_outputs':final_render['outputs'],'final_blockers':final_review['blocking_issues'],
         'internal_accept':False,'delivery_package':False,'authentic_receipt':'NOT VERIFIED / not reached',
         'external_fresh_context_reset':'NOT VERIFIED','protection':protection_result,
         'actual_backend_model':None,'actual_backend_reasoning_effort':None,'tokens':None,'credits':None,
         'checkpoint1_commit':git('rev-parse','HEAD'), 'completed_at':actual['finished_at']}
l6.write_once(d/'checkpoint2_verified.json',summary)
l6.write_once(d/'protection_after.json',protection_result)

doc=ROOT/'docs/session/S3C_ACTUAL_SESSION_E2E_PROOF.md'
text=doc.read_text(encoding='utf-8')
text=text.replace('**S3C ACTUAL_EXECUTION_READY**','**S3C ACTUAL RUNTIME PATH = EXECUTED**\n\n**S3C ACTUAL BOUND LOOP = NOT PASSED**\n\n**ACTUAL SESSION E2E = NOT VERIFIED**',1)
text=text.replace('## Checkpoint 2 — Pending\nrun_session(execute=True) has not been invoked at this checkpoint.\nOne invocation is authorized immediately after Checkpoint 1 commit.', '## Checkpoint 2 — Actual evidence below\nThe frozen existing entry was invoked exactly once after the Checkpoint 1 commit.')
rows='\n'.join('| '+h['stage']+' | '+h['prompt_id']+' | SUCCESS; Save output node executed |' for h in histories)
review_rows='\n'.join('| '+x['review_id']+' | '+x['verdict']+' | '+x['result']['sha256']+' | '+x['invocation']['sha256']+' |' for x in reviews)
text+=f'''

## S3C Checkpoint 2 — One Actual Bound Session
- actual entry: existing run_session(parent_ref, execute=True), exactly once; proof driver hash and call parameters in actual_invocation.json
- actual Worker calls / accepted Comfy submissions: 5 / 5
- actual Reviewer calls: 3; CODEX_CLI / CHATGPT_ACCOUNT, process started, exit0, exact actual attachments verified
- actual Blender calls: 2; actual process invocation exit0, exact GLB-linked four-view renders
- L6: GEOMETRY_READY; right/left/back successful 768x768 PNGs, multiview Review PASS, actual Hunyuan3D GLB
- multiview criterion: AC-MULTIVIEW-COHERENCE SATISFIED
- initial geometry Review: REVISE; AC-GEOMETRY-IDENTITY UNMET; authorized REGENERATE_GEOMETRY/geometry
- correction: exactly1; seed {action['previous_seed']} → {action['revision_seed']}; same approved multiview bytes; view correction0
- final geometry Review: REVISE; geometry criterion UNMET; multiview criterion SATISFIED
- child terminal: ABORT / REVISION_BUDGET_EXHAUSTED; no second correction or extra Review
- outer Session terminal: ABORT; outer reason=ABORT references existing runner outcome; concrete budget reason remains in child terminal
- INTERNAL_ACCEPT: false; scenario_a_accept/internal_accept records absent
- delivered: false; actual user delivery transport0
- completed_at (UTC): {actual['finished_at']}; timestamps are timezone-aware, local date is 2026-10-01 Asia/Seoul
- post-run evidence verification: existing Request/Invocation/coverage/sidecar/GLB/render validators PASS with network/process forbidden during pure validation; existing evidence bytes unchanged
- independent actual history: five GET /history/<prompt_id> responses retained; all completed success and output Save nodes not cached
- actual evidence: runs/session/{ids['session']}/checkpoint2_verified.json plus immutable child directories
- Checkpoint 1 commit: {summary['checkpoint1_commit']}
- Checkpoint 2 commit subject: docs(s3c): record actual bound session and semantic closure failure
- verdict: classification C — semantic closure failure

### Actual prompt identities
| producing task | actual prompt_id | history verification |
|---|---|---|
{rows}

### Actual Review identities / hashes
| Review ID | verdict | raw Result SHA-256 | Invocation SHA-256 |
|---|---|---|---|
{review_rows}

Requests, exact attached image lists, authority-validated criterion coverage, compiled instructions and all corresponding SHA-256 refs are in checkpoint2_verified.json and child records. Raw Results are preserved without coercion. The Reviewer attributes torso/face deformation to AC-GEOMETRY-IDENTITY; no new smoothness/eye/sign criterion was added.

### Actual GLBs
- initial GLB: {initial_source['artifact']['path']}
- initial bytes / SHA-256: {initial_source['artifact']['bytes']} / {initial_source['artifact']['sha256']}
- final attempted GLB (NOT accepted, diagnostic candidate): {final_glb['path']}
- final bytes / SHA-256: {final_glb['bytes']} / {final_glb['sha256']}
- producing prompt/report/Plan/Work Order: correction geometry execution records and actual_history records above
- final render manifest: {cd/'render_manifest.json'}; SHA {l6.digest(cd/'render_manifest.json')}
- exact render source_glb matches final GLB bytes/hash; four camera views/dimensions/renderer invocation validated

### Final semantic blocker
{final_review['blocking_issues'][0]}

This is the actual Review's criterion-scoped finding. It does not establish a single technical root cause or quality improvement policy. Seed-only correction did not achieve acceptance in this attempt.

## S3C Checkpoint 3 — Delivery Boundary Not Entered
INTERNAL_ACCEPT did not occur. prepare_delivery() was not called; no Delivery Package or submission receipt was fabricated. Diagnostic candidate export is evidence/debug material, not an accepted DELIVERED payload. Actual Session E2E remains NOT VERIFIED.

## Final protection / scope
- original tracked files: {len(protected['tracked'])} SHA-256 unchanged, including Frozen Core, schemas, S3A/S3B runtime, tests, historical docs/runs/evidence
- runtime source diff: 0; workflow/model/input parameters unchanged
- Research tracked files: {len(protected['research']['tracked'])} unchanged; HEAD/status unchanged; sole untracked F2B WIP hash {protected['research']['wip_sha256']}
- external manifest references: {len(protected['external'])} unchanged by small-file SHA/size/mtime, large-model size/mtime; full large-model hashes not measured
- protected local refs unchanged; live protected refs matched at readiness; final live recheck is recorded after checkpoint commit
- actual generated PNG/GLB/render assets remain in canonical Comfy work paths; hashes/bytes/producing evidence are committed, models/cache/workspace were not copied into Git
- tests: no repeated full/focused suite; existing runtime source diff0. Required checks were actual execution and evidence integrity validation.
- requested Reviewer config remains gpt-6.1-sol/high; independently observed backend model/effort, tokens and credits remain null/unavailable
- Git whitespace check: preserved byte-identical user_request.md has its original Markdown two-space hard break; generated proof/source files introduce no such whitespace exception
- no geometry quality research/repair, additional seed reroll, transport implementation, main merge/tag/release or history rewrite

## Final classification
```text
S3C ACTUAL RUNTIME PATH = EXECUTED
S3C ACTUAL BOUND LOOP = NOT PASSED
INTERNAL_ACCEPT = false
FINAL SESSION = ABORT
reason = REVISION_BUDGET_EXHAUSTED (child)
ACTUAL SESSION E2E = NOT VERIFIED
ACTUAL USER DELIVERY RECEIPT = NOT VERIFIED / not reached
EXTERNAL FRESH-CONTEXT RESET = NOT VERIFIED
S3B SESSION-BOUND SCENARIO INTEGRATION = LOCAL-VERIFIED
AGENT LOOP CORE V1.0.0 = FROZEN / UNCHANGED
L7-M3 ACTUAL CLOSED FEEDBACK PROOF = NOT PASSED (historical)
LEVEL 7 CLOSED FEEDBACK PIPELINE = NOT VERIFIED
HYPOTHESIS BENCHMARK = NOT STARTED
```

The authorized S3C proof stops here. Fresh actual evidence may inform a separately assigned Scenario A quality/L7 milestone.
'''
doc.write_text(text,encoding='utf-8',newline='\n')
with (d/'postproof_verification_driver.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print(json.dumps({'classification':summary['classification'],'counts':summary['actual_counts'],
                  'final_glb':final_glb,'protection':protection_result},ensure_ascii=False,indent=2))
