"""Read-only current lineage revalidation and a new closure evidence note."""
import dataclasses, json, os, pathlib, sys
ROOT=pathlib.Path('D:/VSCODE-WorkSpace/Others/Agent-Loop-Core')
D=ROOT/'runs/session/psa-session-20261001-031107-2c54c2a3';P=D/'delivery_proof'
sys.path.insert(0,str(ROOT/'src'))
from scenario_a import session_binding as bound, l6_pipeline as l6, l7_geometry_review as bridge
from session import session_boundary as sb
phase='validation'
def audit(event,args):
    if event in ('subprocess.Popen','urllib.Request','socket.connect'):raise RuntimeError('FINAL_CLOSURE_REVALIDATION_NO_EFFECT: '+event)
    if event=='open' and (isinstance(args[1],str) and any(c in args[1] for c in ('w','a','x','+')) or args[2]& (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
        if phase!='record' or not pathlib.Path(args[0]).resolve().is_relative_to(P.resolve()):raise RuntimeError('FINAL_CLOSURE_VALIDATION_NO_WRITE')
sys.addaudithook(audit)
s=l6.read_json(P/'closure_verified.json');start=l6.read_json(P/'closure_start_gate.json')
fixture=l6.read_json(P/'negative_fixture_tests.json')
assert fixture['successful'] and fixture['tests_run']==5 and not fixture['actual_delivery_proof']
assert all(l6.digest(ROOT/p)==h for p,h in start['tracked'].items())
data,boundary,binding=bound.checked_parent(l6.reference(D/'scenario_a.json'))
accept=boundary._checked_accept()
assert boundary.outcome.status=='CLOSED' and boundary.outcome.terminal and boundary.outcome.delivered
term=l6.read_json(D/'terminal.json')
assert term['transitions']==['DELIVERED','CLOSED'] and term['submission_evidence']==s['submission_evidence']
package=sb.FileIdentity(**s['delivery_package']);package.validate()
evidence=sb.SubmissionEvidence(**s['submission_evidence']);evidence.validate(package)
sb.FileIdentity(**s['receipt']).validate();sb.FileIdentity(**s['terminal_record']).validate()
ack=l6.read_json(P/'external_receipt_acknowledgement.json')
assert ack['source_kind']=='DIRECT_CURRENT_USER_CHAT_MESSAGE' and ack['receipt_acknowledged']
assert ack['receipt_token']==evidence.receipt_id=='delivery-bc10c46a19d18566'
assert evidence.artifact_sha256==accept['artifact']['sha256'] and evidence.specification_sha256==accept['specification']['specification_sha256']
candidate=l6.read_json(D/'scenario_a_accept.json')
mandatory={c.criterion_id for c in binding.specification.fields.acceptance_criteria if c.blocking_when_unmet}
assert set(candidate['mandatory_criterion_ids'])==mandatory
for stage,ref in candidate['stage_coverage'].items():
    cov=l6.read_ref(ref)
    assert cov['verdict']=='PASS' and all(cov['coverage'][cid]=='SATISFIED' for cid in data['stage_criteria'][stage] if cid in mandatory)
child_dirs=[ROOT/'runs/l6'/data['child_ids']['l6'],ROOT/'runs/l7'/data['child_ids']['bridge']]
assert l6.checked_review(child_dirs[0])['verdict']=='PASS'
assert bridge.checked_review(child_dirs[1])['verdict']=='PASS'
checked={}
def refs(x):
    if isinstance(x,dict):
        if isinstance(x.get('path'),str) and isinstance(x.get('sha256'),str) and len(x['sha256'])==64:
            p=l6.reviewer.checked_ref({k:x[k] for k in ('path','sha256')})
            if isinstance(x.get('bytes'),int):assert p.stat().st_size==x['bytes']
            checked[str(p)]=x['sha256']
        for v in x.values():refs(v)
    elif isinstance(x,list):
        for v in x:refs(v)
for q in [D]+child_dirs:
    for p in q.rglob('*.json'):refs(l6.read_json(p))
historical=l6.read_json(D/'protection_before.json')
for p,v in historical['external'].items():
    q=pathlib.Path(p);st=q.stat()
    assert {'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'sha256':l6.digest(q) if v['sha256'] else None}==v
assert all(l6.digest(ROOT/p)==h for p,h in start['tracked'].items())
phase='record'
summary={'closure_verification':'PASS','session':boundary.session_id,'status':'CLOSED','terminal':True,'delivered':True,'receipt_id':evidence.receipt_id,'receipt_provenance':s['receipt'],'terminal_record':s['terminal_record'],'current_hash_references_verified':len(checked),'mandatory_coverage':'ALL_SATISFIED','actual_closed_session_guards_rejected':len(s['actual_closed_session_guards']),'existing_negative_fixture_tests':{'passed':5,'effects':0,'actual_delivery_proof':False},'source_test_changes':0,'starting_tracked_unchanged':len(start['tracked']),'historical_external_unchanged':len(historical['external']),'artifact_bytes_hash_unchanged':True,'frozen_specification_unchanged':True,'actual_effects':s['actual_effects'],'git_finalization':'PENDING_NORMAL_COMMIT_PUSH_EQUALITY','completed_at':l6.now()}
l6.write_once(P/'closure_final_validation.json',summary)
with (P/'closure_validation_driver.py').open('xb') as f:f.write(pathlib.Path(__file__).read_bytes())
note=f'''# Actual Delivery & Session Closure — Current Evidence

Canonical actual closure and current evidence verification: PASS. Final proof declaration additionally requires normal commit/push/local-tracking-live equality, recorded in the final output report.

Same Session `{boundary.session_id}`, Loop `{binding.loop_run_id}`, branch delivery-closure-post-stabilization. Preparation checkpoint `{start['head']}` began clean/local=tracking=live. The previous Chat final response supplied the accepted GLB and package links with Input/Output. This turn's direct User acknowledgement `Recived delivery-bc10c46a19d18566.` is the authentic receipt source; literal spelling is retained. It is not a predicted receipt or quality-approval prerequisite.

Receipt `{evidence.receipt_id}` binds package SHA `{package.sha256}`, artifact SHA `{evidence.artifact_sha256}`, frozen Spec SHA `{evidence.specification_sha256}`, actual observed channel/timestamp, and SHA-pinned `external_receipt_acknowledgement.json`. Host message ID/server timestamp is not exposed; timestamp scope is executor observation, not a fabricated server event time. Provenance is the direct actual human User message.

`SessionBoundary.record_submission(package, SubmissionEvidence)` was called once after the acknowledgement. The production terminal record has status CLOSED and transitions DELIVERED/CLOSED. Its scope remains LOCAL_CALLER_SUPPLIED_EVIDENCE_CONTRACT_ONLY; external authenticity comes from the actual User acknowledgement. Current outcome: CLOSED / terminal=true / delivered=true.

Accepted artifact remains 1,139,020 bytes, SHA `{accept['artifact']['sha256']}`; output copy matches. INTERNAL_ACCEPT record, Frozen Specification, actual stage PASS/coverage, CP1/CP2 and preparation checkpoint files stay immutable. All {summary['current_hash_references_verified']} current hash references and both mandatory criteria were revalidated using existing production validators. No semantic Reviewer subprocess was run.

Fourteen actual closed-session negative operations were rejected with effects0: reopened boundary/parent/child effect guards, bound correction registration, default run_session preflight/resume, binding/child/accept/package/submission/stop reentry, and wrong Session-directory ownership. The old Session has no permitted bound resume or new effect. Probes preserved record bytes and created no correction namespace.

Existing negative tests: 5/5 PASS, errors/failures/skips0. These synthetic scratch fixtures prove missing/invalid receipt, wrong package/artifact/Spec, terminal reentry and malformed receipt rejection; they are explicitly separate from actual delivery evidence. Actual closure receipt never uses those fixtures.

Worker/Comfy generation/Blender/semantic Reviewer/correction dispatch/repeated delivery transport0. Source/test changes0; {len(start['tracked'])} starting tracked working-byte hashes unchanged; {len(historical['external'])} historical external references unchanged. Protected refs will be compared after push. No reset/amend/force push/history rewrite.

External User evaluation: 승인. User intends to add lettering themselves and reports penguin eyes/beak, hands holding the sign, and webbed feet rendered normally. Raw feedback is stored in `external_user_evaluation.json`, outside Core/Reviewer state. It does not trigger REVISE, artifact modification, or a new Request/Session. No fresh-context Session/Refresh is started.
'''
with (P/'ACTUAL_DELIVERY_CLOSURE_PROOF.md').open('x',encoding='utf-8',newline='\n') as f:f.write(note)
print(json.dumps(summary,ensure_ascii=False,indent=2))
