"""Bind an actual clarification, infer fresh finalized fields, freeze only if ready."""
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys
from dataclasses import asdict

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

baseline=read(PROOF/'BASELINE_GATE.json')
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in baseline['tracked_file_sha256'].items())
prior=read(PROOF/'intake/round-001/DIALOGUE_STATE.json')
assert prior['semantic_state']=='WAITING_FOR_USER_SPECIFICATION_CLARIFICATION'
assert not (PROOF/'session').exists() and not (PROOF/'frozen.json').exists()
exact('authority/USER_RESPONSE_001.txt',RESPONSE.encode('utf-8'))
response_ref=file_identity(PROOF/'authority/USER_RESPONSE_001.txt','actual-user-clarification-001')
exact('host/specification-intake-002.py',pathlib.Path(__file__).read_bytes())
publish('authority/CLARIFICATION_RECEIPT_001.json',{
    'received_at_utc':stamp(),'actual_user_response_exact_text':RESPONSE,'response_ref':asdict(response_ref),
    'question':prior['clarification_question'],'intake_result_ref':prior['result_ref'],
    'prior_wait_state_ref':asdict(file_identity(PROOF/'intake/round-001/DIALOGUE_STATE.json','actual-wait-state')),
    'no_production_before_actual_response':True,'pre_response_effect_counters':prior['effect_counters'],
    'source':'Actual subsequent human message in this proof chat; no synthetic response',
})
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
skills=SkillRegistry(ROOT/'skills',revision).search('reference')
assert skills
skill_data=[]
for skill in skills:
    metadata=skill.validate(); package=pathlib.Path(skill.metadata.path).parent
    for name,h in metadata['files'].items():
        rel=(package/name).relative_to(ROOT).as_posix()
        committed=subprocess.check_output(['git','show',revision+':'+rel],cwd=ROOT)
        assert hashlib.sha256(committed).hexdigest()==h
        exact('skills-used/'+skill.skill_id+'/'+name,(package/name).read_bytes())
    exact('skills-used/'+skill.skill_id+'/core.json',(package/'core.json').read_bytes())
    skill_data.append({'ref':asdict(skill),'metadata':metadata,
        'guidance':(package/'SKILL.md').read_text(encoding='utf-8'),
        'supporting_guidance':{n:(package/n).read_text(encoding='utf-8') for n in metadata['files'] if n.startswith('references/') and n.endswith('.md')}})
publish('SKILL_DISCOVERY.json',{'local_registry_first':True,'reviewed_local_reusable_packages':skill_data,
    'community_investigation_required':False,'reason':'Reviewed local exact-version guidance covers installed Blender geometry/export/fresh-import boundaries',
    'subject_authority':False,'vcs_revision':revision,'license_content_provenance_verified':True,
    'historical_validation_used_as_new_task_acceptance':False})
version=subprocess.check_output([r'D:\Blender_5.2\blender.exe','--version'],text=True)
publish('RUNTIME_READINESS.json',{'blender_version':version.splitlines()[0],
    'blender_executable':r'D:\Blender_5.2\blender.exe','blender_geometry_available':True,
    'comfy_production_required':False,'runtime_probe_is_production_effect':False,
    'available_diagnostics':'Independent fresh-import GLB mesh/material/bounds metrics, front/back/side/elevated/material-perspective renders and adjustable view',
    'renderer_output':'1024x768 PNG; neutral and exported-material evidence; no pixel-match/calibrated scale guarantee'})
request_ref=file_identity(PROOF/'authority/ORIGINAL_REQUEST.txt','original-user-request')
reference_ref=file_identity(PROOF/'authority/ORIGINAL_REFERENCE.png','original-user-reference')
authority=[{'reference_id':'request','source_ref':canonical_bytes(asdict(request_ref)).decode()},
           {'reference_id':'reference','source_ref':canonical_bytes(asdict(reference_ref)).decode()},
           {'reference_id':'clarification-001','source_ref':canonical_bytes(asdict(response_ref)).decode()}]
names=['specification_markdown','finalized_fields_json','criterion_applicability_json','resource_limits_json',
       'deliverable_type','reference_observations','skill_selection_json','ambiguity_resolution_json']
schema={'type':'object','additionalProperties':False,'required':['ready','unresolved_question','deadline_seconds']+names,
    'properties':{'ready':{'type':'boolean'},'unresolved_question':{'type':['string','null']},
    'deadline_seconds':{'type':['integer','null']},**{n:{'type':'string'} for n in names}}}
context={'role':'SPECIFICATION_DIALOGUE_FRONTIER','session_id':SID,'stage':'UNFROZEN_DIALOGUE_AFTER_ACTUAL_USER_RESPONSE',
    'original_request':(PROOF/'authority/ORIGINAL_REQUEST.txt').read_text(encoding='utf-8'),
    'current_reference':asdict(reference_ref),'authority_references':authority,
    'prior_decisive_ambiguities':prior['detected_decisive_ambiguities'],'actual_clarification_question':prior['clarification_question'],
    'actual_user_responses':[{'exact_text':RESPONSE,'ref':asdict(response_ref)}],
    'available_execution_knowledge_not_subject_authority':skill_data,
    'available_runtime':read(PROOF/'RUNTIME_READINESS.json'),
    'instructions':(
        'Resolve remaining decisive User Intent ambiguities only from the exact original request, image and actual user response. '
        'The user explicitly includes the white metal railing and concrete base and excludes the curb and the yellow chains connected at both sides. Preserve this exact inclusion/exclusion. '
        'Ask only if a consequential competing intent is still unresolved. If unresolved set ready=false and ask necessary natural Korean question; '
        'do not freeze, default unresolved intent, invent an answer or produce a provisional specification. Technical choices are your responsibility. '
        'If ready, author a fresh Work Specification with Goal, inspectable 3D mesh Deliverable (select appropriate installed export), '
        'mandatory acceptance grounded in visible reference features and actual scope response, reference and clarification authority, '
        'bounded Resource Envelope, observable evidence requirements and uncertainty/interpretation limits. '
        'Do not add hidden topology/accuracy requirements that one photograph cannot support, arbitrary polish/surface blemish thresholds, '
        'or task-specific requirements from execution guidance examples. User input is subject authority; Skill guidance is execution knowledge. '
        'State lack of calibrated absolute scale and inferred unseen thickness/backside. Distinct materials and photographed primary structure '
        'are observable; technical presentation/format/mesh naming/budgets are yours. Do not require mask/multiview generation unless chosen for actual execution. '
        'Use only actual supplied authority_references exactly and in supplied order. finalized_fields_json must contain exactly '
        'session_id:'+SID+', specification_version:v1, request_type:NEW_WORK, specification_ready:true, '
        'unresolved_blocking_ambiguities:[], acceptance_criteria:[{criterion_id,authority_ref,blocking_when_unmet,description}], '
        'authority_references:the supplied three records, interpretation_envelope:[nonempty strings]. '
        'criterion authority_ref must be a supplied reference_id. criterion_applicability_json maps artifact type to criterion IDs, '
        'all mandatory criteria must be covered and deliverable_type must be present. The reviewed local Skill supports reference -> glb geometry. '
        'resource_limits_json exact positive-integer keys: production_runs, attempts, worker_calls, reviewer_calls, frontier_calls, diagnostic_calls. '
        'Choose meaningful bounded counts allowing initial planning, independent review, review-driven Frontier diagnosis, local corrections '
        'and if necessary Workflow revision and explicit new Run (at least two Runs and enough calls for these paths; not seed-plus-one stop). '
        'Do not force adaptation when first result passes. Provide a meaningful positive deadline_seconds for this task, not a chat timeout. '
        'skill_selection_json is {reuse:[skill_id],new_skills:[]}; reuse reviewed installed knowledge when sufficient. '
        'ambiguity_resolution_json is a list of {ambiguity_id,resolved_specification_fields,resolution_summary,user_response_ref}; '
        'bind every detected ambiguity to the exact actual response ref and describe inclusion/exclusion. '
        'Do not invoke tools, change files, start production, or store private chain-of-thought. Return concise decision/reason/evidence only.')}
publish('intake/round-002/request.json',context)
adapter=CodexInferenceAdapter(pathlib.Path(__file__).parent,timeout=900,executable=CLI)
invocation=adapter(file_identity(PROOF/'intake/round-002/request.json','clarification-and-specification-intake'),schema,
    PROOF/'intake/round-002/invocation',(reference_ref,))
result=read(pathlib.Path(invocation.result.path))
for p in sorted((PROOF/'intake/round-002/invocation').iterdir()):
    target=OUTPUT/'intake/round-002/invocation'/p.name;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream:stream.write(p.read_bytes())
if not result['ready'] or result['unresolved_question']:
    publish('intake/round-002/DIALOGUE_PENDING.json',result)
    print(json.dumps({'state':'WAITING_FOR_USER_SPECIFICATION_CLARIFICATION','question':result['unresolved_question']},ensure_ascii=False),flush=True)
    sys.exit(0)
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
