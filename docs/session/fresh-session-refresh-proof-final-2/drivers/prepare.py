import os, sys, json, hashlib, subprocess, shutil, datetime, uuid, urllib.request, tempfile, unittest, time
from pathlib import Path
from dataclasses import asdict
ROOT=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final-2'
DIRECT=Path(r'C:\Users\Worker\AppData\Local\Temp\codex-clipboard-28be2078-6a5d-4129-b231-8450fd077f76.png')
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
os.chdir(ROOT)
from scenario_a import session_binding as bound, l6_pipeline as l6, reference_normalization as norm
from session import session_boundary as session
from core import reviewer_auth
from PIL import Image
def git(*args):
    p=subprocess.run(['git',*args],capture_output=True,encoding='utf-8',errors='replace',check=True)
    return p.stdout.strip()
def write(name,data):
    l6.write_once(PROOF/name,data)
assert git('branch','--show-current')=='stabilization-reviewer-failure-observability'
assert git('rev-parse','HEAD')=='93d9dfc7d29c9ffe54886f0f3b34a0248fde410e'
assert git('status','--porcelain')==''
assert git('rev-parse','@{u}')==git('rev-parse','HEAD')
remote=git('ls-remote','origin','refs/heads/stabilization-reviewer-failure-observability')
assert remote.split()[0]==git('rev-parse','HEAD')
assert l6.digest(DIRECT)=='9da5ed9e7f3490d058673122a7bd50b46635d4f0b5a36ca3199f0c1636cd17e5'
assert not PROOF.exists()
baseline={p:l6.digest(ROOT/p) for p in git('ls-files','-z').split('\0') if p}
tags=git('show-ref','--tags')
start={'branch':git('branch','--show-current'),'head':git('rev-parse','HEAD'),'tracking':git('rev-parse','@{u}'),'live':remote,'tree_clean':True,'origin':git('remote','get-url','origin'),'created_at':l6.now()}
assert not git('branch','--list','fresh-session-refresh-proof-final-2')
git('switch','-c','fresh-session-refresh-proof-final-2')
PROOF.mkdir()
write('STARTING_SNAPSHOT.json',start)
write('HISTORICAL_PROTECTION.json',{'tracked_file_sha256':baseline,'tags':tags})
suffix=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8]
ids={k:'fsf2-'+k+'-'+suffix for k in ('session','loop','l6','bridge','correction')}
assert all(len(ids[k])<=48 for k in ('l6','bridge','correction'))
write('IDENTITIES.json',ids)
shutil.copyfile(DIRECT,PROOF/'CURRENT_REFERENCE.png')
request='레퍼런스 이미지에 있는 석등을 제작하라.\n석등은 중앙의 사각형 구멍을 포함한 실루엣이 명확히 나와야 한다.'
(PROOF/'CURRENT_REQUEST.md').write_text(request+'\n',encoding='utf-8')
ref=session.file_identity(PROOF/'CURRENT_REFERENCE.png','CURRENT_DIRECT_USER_REFERENCE')
assert ref.sha256==l6.digest(DIRECT)
goal='Create a 3D stone lantern faithful to the directly attached reference, with a clear silhouette and central square opening.'
must=(
 'Preserve the broad low roof with projecting eaves, central lantern chamber, and raised leg-like stone support shown in the reference.',
 'The central square aperture must be an actual open cavity in the 3D geometry, with readable boundaries; a dark surface patch is insufficient.',
 'Produce a current GLB through the fixed four-view pipeline and evaluate its current diagnostic renders before INTERNAL_ACCEPT.'
)
criteria=(
 session.AcceptanceCriterion('LANTERN_FORM','reference',True,'Recognizable stone-lantern silhouette: broad low eaved roof, central chamber, and raised leg-like support, consistent with the current reference. Exclude the foreground post, person, and garden scene.'),
 session.AcceptanceCriterion('APERTURE_VISUAL','request',True,'The lantern chamber has a clearly bounded square aperture readable in the visible generated views; do not mistake the openings between base legs for the chamber aperture. Occluded views need coherent completion, not invented exact historical detail.'),
 session.AcceptanceCriterion('MULTIVIEW_IDENTITY','reference',True,'Right, left, and back depict the same stone lantern with coherent proportions and structural arrangement; scene clutter must not become part of the target.'),
 session.AcceptanceCriterion('APERTURE_GEOMETRY','request',True,'Current 3D diagnostic renders show the central square chamber aperture as a real recessed/open cavity with spatial depth and empty volume, not merely a flat dark square texture. If current renders cannot establish this, do not PASS.'),
 session.AcceptanceCriterion('GLB_READABILITY','request',True,'The current GLB is a coherent readable lantern in diagnostic views, preserving the reference silhouette without gross merged clutter or broken essential components.')
)
stages={'multiview':('LANTERN_FORM','APERTURE_VISUAL','MULTIVIEW_IDENTITY'),'geometry':('LANTERN_FORM','APERTURE_GEOMETRY','GLB_READABILITY')}
fields=session.FinalizedFields(ids['session'],'1.0','NEW_WORK',True,(),criteria,
 (session.AuthorityReference('request',bound.reference_authority(session.file_identity(PROOF/'CURRENT_REQUEST.md','CURRENT_DIRECT_USER_REQUEST'))),session.AuthorityReference('reference',bound.reference_authority(ref))),
 ('Occluded backside completion consistent with observed lantern structure is an internal technical choice.', 'Sampler, seeds, cameras, and staging are internal choices within existing fixed capability and budgets.','No exact physical scale, texture production, surrounding scene, Delivery, or Session closure is required.'))
dialogue={'current_request':request,'observed':'Broad stone roof, chamber with square aperture, elevated support; foreground post partly occludes the target.','interpretation':'Only the lantern is the target. Complete occluded structure coherently. The square aperture means actual spatial opening in geometry.','blocking_ambiguities':[],'user_questions':0,'independent_derivation':True,'previous_session_resume':0,'previous_artifact_reuse':0,'previous_active_reasoning_reuse':0}
write('SPECIFICATION_DIALOGUE.json',dialogue)
spec='# Fresh Session Final-2 — Frozen Work Specification v1\n\n'+request+'\n\nTarget/deliverable: one current 3D stone-lantern GLB, multiview images and diagnostic evidence. Stop at INTERNAL_ACCEPT.\n\nGoal: '+goal+'\n\n'+'\n'.join('Must-have: '+m for m in must)+'\n\nDirect reference: '+bound.reference_authority(ref)+'\n\nNon-goals: foreground post, person, garden, exact unseen details, physical scale, texture production, source/test changes, historical resume, Delivery and closure.\n\nSpecification Dialogue: no blocking ambiguity; occluded backside completion follows observed structure. All criteria independently derived from current request/reference.\n\nCriteria (all mandatory blocking):\n'+'\n'.join(c.criterion_id+' | authority='+c.authority_ref+' | stages='+','.join(k for k,v in stages.items() if c.criterion_id in v)+' | '+c.description for c in criteria)+'\n\nPASS means every selected criterion is SATISFIED with current evidence. REVISE requires an observed blocker and an action within the existing fixed capability. Unobservable mandatory evidence cannot be assumed SATISFIED. Fixed budgets: worker 6, reviewer 4, renderer 2, revision 1. No hidden retry or manual replacement.\n'
(PROOF/'FROZEN_WORK_SPECIFICATION_v1.md').write_text(spec,encoding='utf-8')
frozen=session.freeze_specification(PROOF/'FROZEN_WORK_SPECIFICATION_v1.md',fields)
boundary=session.SessionBoundary(ids['session'],ROOT/'runs/session'/ids['session'])
binding=boundary.create_binding(frozen,ids['loop'])
current=bound.freeze_current_reference(binding,ref,'reference')
parent=bound.prepare(boundary,binding,goal={'text':goal,'authority_ref':'request'},must_haves=tuple({'text':m,'authority_ref':'request' if i else 'reference'} for i,m in enumerate(must)),stage_criteria=stages,child_ids={k:ids[k] for k in bound.KINDS},current_reference=current)
encoded,normalization=norm.normalize_reference(DIRECT.read_bytes())
assert normalization['original_dimensions']==[467,539]
assert normalization['normalized_sha256']=='93c081f086bc91821c8aa0ed61e012109d5eb13fd1358c7ef123598dd6574b00'
(PROOF/'NORMALIZED_PREVIEW.png').write_bytes(encoded)
write('PREPARED_BINDING.json',{'ids':ids,'parent':parent,'current_reference':asdict(current),'normalization':normalization,'specification_identity_sha256':frozen.identity_sha256,'stage_criteria':stages,'direct_attachment':asdict(session.file_identity(DIRECT,'DIRECT_ATTACHMENT'))})
context=session.build_startup_context(session.ContextRecord('CURRENT_REQUEST',str(PROOF/'CURRENT_REQUEST.md')),(session.ContextRecord('CURRENT_REFERENCE',str(PROOF/'CURRENT_REFERENCE.png')),),())
l6.write_once(boundary.directory/'startup_context.json',{'records':[asdict(c) for c in context],'host_context_reset_scope':'New user chat per task context; Core does not attest host memory reset. Only durable implementation facts were consulted.'})
print(json.dumps({'stage':'prepared','ids':ids,'parent':parent,'normalization':normalization}),flush=True)
