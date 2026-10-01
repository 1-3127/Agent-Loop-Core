import os, sys, json, hashlib, subprocess, datetime, uuid
from pathlib import Path
from dataclasses import asdict
from io import BytesIO
ROOT = Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
PROOF = ROOT/'docs/session/fresh-session-refresh-proof-final-3'
ORIGINAL = Path(r'C:\Users\Worker\AppData\Local\Temp\codex-clipboard-08627ccb-773a-4ec0-9b6e-3dd1bcde0524.png')
BASE = '94e55ac0f66fe376e2711526f90dd758e6879ce0'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
os.chdir(ROOT)
from PIL import Image
from session import session_boundary as sb
from scenario_a import session_binding as bound, l6_pipeline as l6, reference_normalization as norm
def git(*args): return subprocess.check_output(['git',*args],encoding='utf-8').strip()
def write(name,data):
    path=PROOF/name; path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(data if isinstance(data,str) else json.dumps(data,ensure_ascii=False,indent=2)+'\n')
assert git('branch','--show-current')=='fresh-session-refresh-proof-final-3'
assert git('rev-parse','HEAD')==BASE and not git('status','--porcelain')
assert git('rev-parse','refs/remotes/origin/stabilization-l7-review-stream-evidence-contract')==BASE
assert git('ls-remote','origin','refs/heads/stabilization-l7-review-stream-evidence-contract').split()[0]==BASE
assert not PROOF.exists()
original=sb.file_identity(ORIGINAL,'USER_DIRECT_CURRENT_REFERENCE')
assert original.sha256=='9da5ed9e7f3490d058673122a7bd50b46635d4f0b5a36ca3199f0c1636cd17e5'
assert Image.open(ORIGINAL).size==(467,539)
tracked=git('ls-files','-z').split('\0')
protection={'start_branch':'stabilization-l7-review-stream-evidence-contract','start_head':BASE,'tracking':BASE,'live_remote':BASE,'start_clean':True,'tracked_file_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in tracked if n},'tags':git('show-ref','--tags'),'refs':git('show-ref')}
PROOF.mkdir()
write('STARTING_SNAPSHOT.json',protection)
stamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y%m%d-%H%M%S')
nonce=uuid.uuid4().hex[:8]
ids={k:f'fsf3-{k}-{stamp}-{nonce}' for k in ('session','loop','l6','bridge','correction')}
assert len(set(ids.values()))==5
request='레퍼런스 이미지에 있는 석등을 제작하라. 석등은 중앙의 사각형 구멍을 포함한 실루엣이 명확히 나와야 한다.'
write('CURRENT_REQUEST.md','# Current request\n\n'+request+'\n\nAuthority: the user request pasted in this new chat and the directly attached current PNG. One fresh attempt, at most one canonical correction; stop at INTERNAL_ACCEPT or the actual failure.\n')
source_request=Path(r'C:\Users\Worker\.codex\attachments\a81da97a-0ffd-4ebc-a52a-ab29538c6d43\붙여넣은 텍스트.txt')
write('USER_EXECUTION_REQUEST.txt',source_request.read_text(encoding='utf-8').replace('\r\n','\n').replace('\r',''))
with (PROOF/'CURRENT_REFERENCE.png').open('xb') as f: f.write(ORIGINAL.read_bytes())
derivative,transform=norm.normalize_reference(ORIGINAL.read_bytes())
assert transform['normalized_sha256']=='93c081f086bc91821c8aa0ed61e012109d5eb13fd1358c7ef123598dd6574b00'
assert transform['resized_dimensions']==[467,539] and transform['operation']=='pad'
assert Image.open(BytesIO(derivative)).size==(768,768)
assert Image.open(BytesIO(derivative)).crop((150,114,617,653)).tobytes()==Image.open(ORIGINAL).tobytes()
with (PROOF/'NORMALIZED_PREVIEW.png').open('xb') as f: f.write(derivative)
authority='Current direct user request: '+request
criteria=(
 sb.AcceptanceCriterion('FORM_SILHOUETTE','REFERENCE',True,'The target is recognizable as the reference stone lantern: a wide, low overhanging roof with a small top cap, a roughly square chamber, a projecting horizontal platform, and substantial arched supports or legs. Judge observable form in the selected stage. Complete occluded sides reasonably; exclude the person, foreground pole, vegetation, and scene surfaces from the lantern.'),
 sb.AcceptanceCriterion('MV_APERTURE','REQUEST',True,'In the current multiview images, the chamber below the roof has a clearly framed central square or approximately rectangular opening where observable. This criterion concerns visual appearance only; a visible dark opening in an image does not establish an actual geometric cavity.'),
 sb.AcceptanceCriterion('MV_COHERENCE','REFERENCE',True,'The current front, right, left, and back remain plausible views of one stone lantern, with a compatible roof, chamber, platform, and support arrangement. Occlusion and inferred hidden surfaces may vary, but the target identity and major proportions remain coherent.'),
 sb.AcceptanceCriterion('GEO_APERTURE','REQUEST',True,'The current 3D chamber includes an actual square or approximately rectangular aperture or open cavity below the roof. Current geometry diagnostics must support spatial depth, a rim and inner surfaces, or visible empty space/background. A flat dark square, texture mark, shallow decorative panel, or base arch alone does not satisfy this requirement. Preserve uncertainty when diagnostics cannot establish it.'),
 sb.AcceptanceCriterion('GEO_READABILITY','REQUEST',True,'The current GLB and its diagnostic renders are readable as a coherent lantern with separable roof, chamber, platform, and raised support. The user-required silhouette and central chamber opening are assessable from the current geometry evidence; an undifferentiated solid or featureless surface is insufficient.')
)
stage={'multiview':('FORM_SILHOUETTE','MV_APERTURE','MV_COHERENCE'),'geometry':('FORM_SILHOUETTE','GEO_APERTURE','GEO_READABILITY')}
goal='Produce a current 3D stone lantern matching the attached reference major silhouette and containing a real central square chamber opening.'
must=('Retain the roof, chamber, platform, and arched supports visible in the reference.', 'Make the central square chamber opening an actual aperture or cavity in the geometry.')
fields=sb.FinalizedFields(ids['session'],'v1','NEW_WORK',True,(),criteria,(sb.AuthorityReference('REQUEST',authority),sb.AuthorityReference('REFERENCE',bound.reference_authority(original))),('Target the lantern itself; photographic scene occluders are outside the model.','Infer hidden sides consistently from the current image.','Use the fixed single-PNG/four-view/GLB capability and existing bounded seed correction.'))
spec='# Fresh Session Final-3 — Stone Lantern Work Specification v1\n\n'+request+'\n\nGoal: '+goal+'\n\nSession: '+ids['session']+'\nLoop: '+ids['loop']+'\n\nTarget/deliverable: one generated current stone-lantern GLB with canonical multiview, Blender diagnostics, and current semantic Reviews. This proof stops at INTERNAL_ACCEPT; Delivery and Session closure are outside scope.\n\nMust-Haves:\n'+ '\n'.join(must)+'\n\nAuthority REQUEST: '+authority+'\nAuthority REFERENCE: '+bound.reference_authority(original)+'\n\nThe direct attachment bytes are authoritative. The archival original and centered 768-square execution derivative have separate roles. No historical reference, specification, artifact, Review, binding, or active attempt is substituted.\n\nThe broad roof and small top cap, framed chamber, projecting platform, and arched supports define the major silhouette. The foreground pole/person and garden are scene occluders; hidden sides can be inferred reasonably. No scale, fine texture fidelity, UV optimization, rigging, artistic polish, or manual mesh editing is required.\n\nAcceptance criteria (all mandatory/blocking) and explicit applicability:\n'+json.dumps({'criteria':[asdict(c) for c in criteria],'stage_criteria':stage},ensure_ascii=False,indent=2)+'\n\nC-01: FORM_SILHOUETTE must be satisfied independently in both assigned stages. Image aperture appearance is separate from actual cavity evidence. PASS requires each selected mandatory criterion SATISFIED on current evidence; REVISE identifies an observed unmet mandatory criterion. Do not force a verdict or treat uncertainty as PASS. Supported suggested_action and existing correction budgets govern correction.\n\nExecution policy: '+bound.CAPABILITY+'; caps '+json.dumps(bound.CAPS)+'. One fresh canonical run_session entry, at most one reserved canonical correction. No budget extension, hidden retry, brute force, failed Session resume, source/test/contract changes, or manual artifact replacement. I-03 checks all three repository child and seven external namespaces before first effects. Centered padding only; no upscale/crop/stretch.\n\nStop: actual INTERNAL_ACCEPT, actual runtime failure, contract defect, or exhausted semantic correction. A normal REVISE after exhausted correction is SEMANTIC_CLOSURE_FAILED. Preserve all evidence. No Delivery, record_submission, or Session closure.\n'
write('FROZEN_WORK_SPECIFICATION_v1.md',spec)
frozen=sb.freeze_specification(PROOF/'FROZEN_WORK_SPECIFICATION_v1.md',fields)
directory=ROOT/'runs/session'/ids['session']; assert not directory.exists()
boundary=sb.SessionBoundary(ids['session'],directory)
binding=boundary.create_binding(frozen,ids['loop'])
current=bound.freeze_current_reference(binding,original,'REFERENCE')
parent=bound.prepare(boundary,binding,goal={'text':goal,'authority_ref':'REQUEST'},must_haves=tuple({'text':m,'authority_ref':'REFERENCE' if i==0 else 'REQUEST'} for i,m in enumerate(must)),stage_criteria=stage,child_ids={k:ids[k] for k in bound.KINDS},current_reference=current)
startup=sb.build_startup_context(sb.ContextRecord('CURRENT_REQUEST',str(PROOF/'CURRENT_REQUEST.md')),(sb.ContextRecord('CURRENT_REFERENCE',bound.reference_authority(original)),),tuple(sb.ContextRecord('VERIFIED_FACT',s) for s in ('Baseline 94e55ac includes C-01, I-03, reference binding/normalization, Reviewer observability and L7 stream contracts; verify current readiness.','Previous attempts are historical, never active state.','I-01 and I-02 remain deferred.')))
l6.write_once(directory/'startup_context.json',[asdict(x) for x in startup])
write('SPECIFICATION_DIALOGUE.json',{'request':request,'reference':asdict(original),'interpretation':'Generate the lantern itself, with visible major silhouette and a real central chamber cavity. Scene occluders are excluded.','decisive_ambiguity':False,'user_question_needed':False,'previous_active_state_imported':False,'fresh_chat':'Current chat has a newly supplied request and direct attachment; no historical Session reopened. Host memory erasure is not measurable by the Session API.'})
write('PREPARED_BINDING.json',{'ids':ids,'parent':parent,'frozen_specification':asdict(frozen),'specification_identity_sha256':frozen.identity_sha256,'binding_identity_sha256':binding.identity_sha256,'original':asdict(original),'current_reference':asdict(current),'normalization':transform,'stage_criteria':stage,'generation_effects':0,'source_test_changes':0,'previous_session_resume':0,'delivery':False})
print(json.dumps({'ids':ids,'parent':parent,'reference':original.sha256,'normalized':transform['normalized_sha256'],'new_specification':frozen.identity_sha256,'generation_effects':0}),flush=True)
