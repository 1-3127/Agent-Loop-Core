"""Bind an actual clarification, infer fresh finalized fields, freeze only if ready."""
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
work=Path(__file__).resolve().parent

ROOT = pathlib.Path(r"D:\VSCODE-WorkSpace\Others\Agent-Loop-Core")
PROOF = ROOT / "docs/adaptive/fresh-spec-dialogue-artifact-proof/fresh-002"
OUTPUT = pathlib.Path(r"C:\Users\Worker\Documents\Codex\2026-10-02\codex-specification-dialogue-human-blocking-text\outputs\fresh-spec-dialogue-artifact-proof\fresh-002")
SID = "fresh-spec-dialogue-artifact-002"
RESPONSE = '흰색 금속 난간과 콘크리트 받침을 둘 다 제작한다. 아래의 연석은 포함하지 않고, 양 옆에 연결되어 있는 노란색 사슬도 포함하지 않는다.'
CLI = r"C:\Users\Worker\AppData\Local\OpenAI\Codex\bin\c6fe824d725f02d7\codex.exe"
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "src"))
from core.frontier import CodexInferenceAdapter
from core.skill_artifact import canonical_bytes, write_once
from core.skill_registry import SkillRegistry
from core.workflow_artifact import freeze_workflow_scope
from session.session_boundary import AcceptanceCriterion, AuthorityReference, FinalizedFields, file_identity, freeze_specification

def stamp(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p): return json.loads(p.read_text(encoding="utf-8"))
def publish(relative, data):
    write_once(PROOF / relative, data)
    write_once(OUTPUT / relative, data)
def exact(relative, data):
    for root in (PROOF, OUTPUT):
        p=root/relative; p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f: f.write(data)


prior=read(PROOF/'intake/round-001/DIALOGUE_STATE.json')
assert not (PROOF/'session').exists() and not (PROOF/'frozen.json').exists()
response_ref=file_identity(PROOF/'authority/USER_RESPONSE_001.txt','actual-user-clarification-001')
request_ref=file_identity(PROOF/'authority/ORIGINAL_REQUEST.txt','original-user-request')
reference_ref=file_identity(PROOF/'authority/ORIGINAL_REFERENCE.png','original-user-reference')
context=read(PROOF/'intake/round-002/request.json')
authority=context['authority_references']
draft=read(PROOF/'intake/round-002/invocation/result.json')
limits=json.loads(draft['resource_limits_json'])
resolutions=json.loads(draft['ambiguity_resolution_json'])
issues=[]
if limits['frontier_calls']<8: issues.append('Six frontier calls cannot cover initial plan/start, diagnosis, local correction, workflow revision, explicit Run restart, next Attempt and ACCEPT. Supply at least eight (and adequate margin) within a meaningful bounded envelope.')
if any(r['user_response_ref']!=asdict(response_ref) for r in resolutions): issues.append('user_response_ref must exactly match supplied FileIdentity, including literal Windows path separators. Do not double literal backslashes in parsed JSON.')
publish('intake/round-002/PREFREEZE_DRAFT_VALIDATION.json',{'status':'DRAFT_REQUIRES_TECHNICAL_REFINEMENT','issues':issues,'frozen':False,'production_session_bound':False,'production_effects':0,'no_additional_user_intent_needed':draft['ready'] and draft['unresolved_question'] is None,'draft_result_ref':asdict(file_identity(PROOF/'intake/round-002/invocation/result.json','unfrozen-draft'))})
context['technical_prefreeze_validation']={'issues':issues,'minimum_resource_limits':{'production_runs':2,'attempts':3,'worker_calls':3,'reviewer_calls':3,'frontier_calls':8,'diagnostic_calls':3},'exact_response_ref':asdict(response_ref),'previous_unfrozen_draft':draft,'instruction':'Only original request, original reference and actual user response define subject authority. Prior draft is unfrozen technical output, not new intent authority. Return a full consistent corrected unfrozen Specification result. Resolve technical budget and exact evidence-reference defects; do not ask user about technical choices. Do not change grounded scope or invent user responses.'}
schema=read(PROOF/'intake/round-002/invocation/schema.json')
exact('host/specification-technical-refinement-003.py',Path(__file__).read_bytes())
publish('intake/round-003/request.json',context)
adapter=CodexInferenceAdapter(work,timeout=900,executable=CLI)
invocation=adapter(file_identity(PROOF/'intake/round-003/request.json','technical-prefreeze-refinement'),schema,PROOF/'intake/round-003/invocation',(reference_ref,))
result=read(Path(invocation.result.path))
for p in sorted((PROOF/'intake/round-003/invocation').iterdir()):
    target=OUTPUT/'intake/round-003/invocation'/p.name;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream:stream.write(p.read_bytes())
assert result['ready'] and result['unresolved_question'] is None,'ACTUAL_FRONTIER_DETECTED_REMAINING_AMBIGUITY'
data=json.loads(result['finalized_fields_json'])

assert data['unresolved_blocking_ambiguities']==[] and data['authority_references']==authority and data['session_id']==SID
data['acceptance_criteria']=tuple(AcceptanceCriterion(**v) for v in data['acceptance_criteria'])
data['authority_references']=tuple(AuthorityReference(**v) for v in data['authority_references'])
data['unresolved_blocking_ambiguities']=();data['interpretation_envelope']=tuple(data['interpretation_envelope'])
fields=FinalizedFields(**data);fields.validate()
limits=json.loads(result['resource_limits_json'])
minimum={'production_runs':2,'attempts':3,'worker_calls':3,'reviewer_calls':3,'frontier_calls':8,'diagnostic_calls':3}
assert set(limits)==set(minimum) and all(type(limits[k]) is int and limits[k]>=v for k,v in minimum.items())
assert type(result['deadline_seconds']) is int and result['deadline_seconds']>0
selection=json.loads(result['skill_selection_json'])
assert selection=={'reuse':['blender-modeling-workflow'],'new_skills':[]}
resolutions=json.loads(result['ambiguity_resolution_json'])
assert {r['ambiguity_id'] for r in resolutions}=={r['ambiguity_id'] for r in prior['detected_decisive_ambiguities']}
assert all(r['user_response_ref']==asdict(response_ref) for r in resolutions)
publish('authority/AMBIGUITY_RESOLUTION_BINDING.json',{'intake_result_ref':asdict(invocation.result),'actual_user_response_ref':asdict(response_ref),'resolutions':resolutions})
mapping=json.loads(result['criterion_applicability_json'])
document=(result['specification_markdown']+'\n\nFresh finalized authority fields:\n'+canonical_bytes(asdict(fields)).decode()+'\n\n'+
    canonical_bytes({'criterion_applicability':mapping,'deliverable_type':result['deliverable_type']}).decode()+'\n\n'+
    canonical_bytes({'resource_limits':limits,'deadline_seconds':result['deadline_seconds']}).decode()+'\n').encode('utf-8')
exact('SPECIFICATION.md',document)
frozen=freeze_specification(PROOF/'SPECIFICATION.md',fields)
publish('frozen.json',asdict(frozen))
scope=freeze_workflow_scope(frozen,PROOF/'scope.json',mapping,result['deliverable_type'])
with (OUTPUT/'scope.json').open('xb') as stream:stream.write((PROOF/'scope.json').read_bytes())
publish('INTAKE_RESULT.json',{'status':'READY','session_id':SID,'specification':asdict(frozen),'scope_ref':asdict(scope),
    'reference_ref':asdict(reference_ref),'request_ref':asdict(request_ref),'clarification_ref':asdict(response_ref),
    'intake_invocation_ref':asdict(invocation.invocation),'initial_intake_invocation_ref':prior['invocation_ref'],
    'reference_observations':result['reference_observations'],'resource_limits':limits,'deadline_seconds':result['deadline_seconds'],
    'skill_selection':selection,'actual_user_wait_resolved':True,'frozen_specification_count':1,'production_session_bindings':0})
print(json.dumps({'status':'READY','session_id':SID,'frozen_identity':frozen.identity_sha256,'limits':limits,
    'deadline_seconds':result['deadline_seconds'],'criteria':[asdict(c) for c in fields.acceptance_criteria],
    'reference_observations':result['reference_observations']},ensure_ascii=False),flush=True)
