import pathlib, sys, os, json, hashlib, subprocess, uuid, datetime, urllib.request
from dataclasses import asdict
from io import BytesIO
ROOT = pathlib.Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
WORK = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'src'))
from session import session_boundary as sb
from scenario_a import session_binding as bound, l6_pipeline as l6, l7_geometry_review as bridge, reference_normalization as norm
from core.reviewer_auth import auth_mode
from PIL import Image, __version__ as pillow_version
PROOF = ROOT/'docs/session/fresh-session-refresh-proof-final'
ORIGINAL = pathlib.Path(r'C:\Users\Worker\AppData\Local\Temp\codex-clipboard-56c3ee39-4031-47aa-a5ef-ebede4edfb9c.png')
def git(*args):
    return subprocess.check_output(['git','-c','safe.directory='+str(ROOT),'-C',str(ROOT),*args],encoding='utf-8').strip()
def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n' if not isinstance(data,str) else data)
assert git('branch','--show-current') == 'fresh-session-refresh-proof-final'
assert git('rev-parse','HEAD') == '5b1a3c8a918cb9fcabaa7c7c7824b3755b2e5a2c'
assert not git('status','--porcelain')
PROOF.mkdir()
tracked = git('ls-files','-z').split('\0')
write(PROOF/'starting_snapshot.json', {'branch':'stabilization-reference-dimension-normalization','head':git('rev-parse','HEAD'),'tracking':git('rev-parse','refs/remotes/origin/stabilization-reference-dimension-normalization'),'live_remote':git('ls-remote','origin','refs/heads/stabilization-reference-dimension-normalization').split()[0],'clean':True,'protected_refs':git('show-ref'),'tracked_hashes':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in tracked if n}})
stamp = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y%m%d-%H%M%S')
nonce = uuid.uuid4().hex[:8]
ids = {kind:f'fsf-{kind}-{stamp}-{nonce}' for kind in ('session','loop','l6','bridge','correction')}
assert len(set(ids.values())) == 5
request = '레퍼런스 이미지에 있는 석등을 제작하라.\n석등은 중앙의 사각형 구멍을 포함한 실루엣이 명확히 나와야 한다.'
write(PROOF/'CURRENT_REQUEST.md', '# Current user request\n\n'+request+'\n\nAuthority: new pasted request and directly attached PNG in this chat.\nNo previous Session is resumed.\n')
current_file = sb.file_identity(ORIGINAL,'USER_CURRENT_REFERENCE')
payload = ORIGINAL.read_bytes()
with (PROOF/'REFERENCE_ORIGINAL.png').open('xb') as stream: stream.write(payload)
derivative, transform = norm.normalize_reference(payload)
with (PROOF/'NORMALIZATION_PREVIEW.png').open('xb') as stream: stream.write(derivative)
assert Image.open(BytesIO(derivative)).size == (768,768)
assert transform['resized_dimensions'] == [467,539]
assert transform['operation'] == 'pad' and not transform['contract']['upscale'] and not transform['contract']['crop']
assert Image.open(BytesIO(derivative)).crop((150,114,617,653)).tobytes() == Image.open(BytesIO(payload)).tobytes()
user_authority = 'Current chat request: '+request
criteria = (
 sb.AcceptanceCriterion('MV_SILHOUETTE','REF',True,'The current front and generated views depict a coherent recognizable stone lantern with the reference major silhouette: wide low roof and top finial, square chamber, horizontal platform, and arched pedestal or legs. Use visible reference features; plausibly infer occluded sides. Scene people, pole, trees and background are not parts of the lantern.'),
 sb.AcceptanceCriterion('MV_OPENING','USER',True,'The central square chamber opening is visibly represented in the front and observable generated orientations. This image-stage appearance alone does not establish a geometric hole; do not demand topology from images.'),
 sb.AcceptanceCriterion('GEO_SILHOUETTE','REF',True,'The current 3D diagnostic renders show the stone lantern major silhouette clearly: broad low roof and finial, square chamber, horizontal platform, and arched pedestal or legs. Exact hidden details and scene occluders are not required.'),
 sb.AcceptanceCriterion('GEO_OPENING','USER',True,'The 3D lantern has a real central square or rectangular opening in the chamber under the roof, observably supported by the current geometry diagnostics through its rim, depth or visible interior/background. A flat dark square texture, painted marking or superficial panel is insufficient. Evaluate only current diagnostic evidence; uncertainty must remain uncertainty.')
)
goal = 'Create a 3D stone lantern from the directly attached current reference with a clear silhouette and actual central square chamber opening.'
must = ('Preserve the visible reference lantern major silhouette.', 'Represent the central square chamber opening as an actual geometric aperture.')
stage_criteria = {'multiview':('MV_SILHOUETTE','MV_OPENING'),'geometry':('GEO_SILHOUETTE','GEO_OPENING')}
fields = sb.FinalizedFields(ids['session'],'v1','NEW_WORK',True,(),criteria,
 (sb.AuthorityReference('USER',user_authority),sb.AuthorityReference('REF',bound.reference_authority(current_file))),
 ('Single current PNG to fixed four-view GLB capability.', 'Infer hidden lantern sides reasonably; ignore photographic scene occluders.', 'No decisive ambiguity; technical choices and diagnostic cameras use the current fixed contract.'))
doc = '# Final fresh-session stone-lantern Work Specification v1\n\nFROZEN independently for this new request.\n\nSession: '+ids['session']+'\nLogical Loop: '+ids['loop']+'\n\n## Request and goal\n\n'+request+'\n\n'+goal+'\n\n## Deliverable and scope\n\nA current generated GLB stone lantern plus the canonical multiview and Blender diagnostic evidence. Stop at production INTERNAL_ACCEPT. No Delivery or Session closure.\n\nThe lantern includes its broad low roof, finial, chamber, platform and arched base. The foreground pole, person and background scenery are occluders or context, not model parts. Hidden sides may be completed reasonably. No exact scale, PBR, texture fidelity, UV/topology optimization, rigging, fine artistic finish or manual replacement is requested.\n\n## Must-Haves\n\n'+ '\n'.join(must)+'\n\n## Direct authority\n\nUSER: '+user_authority+'\n\nREF: '+bound.reference_authority(current_file)+'\n\nThe original attachment bytes remain authority. The saved original is archival evidence only. The 768-square derivative is execution input only, never replacement user authority.\n\n## Criteria and applicability\n\n'+json.dumps({'criteria':[asdict(c) for c in criteria],'stage_criteria':stage_criteria},ensure_ascii=False,indent=2)+'\n\nC-01: each stage evaluates only its own observable criteria. All four criteria are mandatory and blocking when unmet. Multiview appearance does not establish the actual geometry aperture. Geometry review uses the current canonical Blender geometry diagnostics.\n\nPASS: every selected blocking criterion SATISFIED with current observations and no blocker. REVISE: selected mandatory criterion observably UNMET; only fixed seed correction within existing caps. UNCERTAIN cannot become SATISFIED automatically; preserve HUMAN_REQUIRED. No additional aesthetic or unrequested quality blocker.\n\n## Execution constraints\n\nFixed capability '+bound.CAPABILITY+'; budgets '+json.dumps(bound.CAPS)+'. No enlargement, source/test/contract changes, brute-force retries, history reuse, manual artifact substitution or same-Session rerun. I-03 checks all fresh namespaces before any staging or generation. Smaller input receives centered padding only; no upscale/crop/stretch. Canonical entry stages normalized bytes in its fresh attempt before Worker dispatch. CP1 preview is independently recorded execution-readiness evidence, not an attempt namespace pre-created outside the entry.\n\n## Stop conditions\n\nStop at INTERNAL_ACCEPT, an actual bounded runtime/semantic failure, or a newly discovered source/contract defect. Preserve raw verdicts and evidence. Delivery remains zero.\n'
write(PROOF/'FROZEN_WORK_SPECIFICATION_v1.md',doc)
frozen = sb.freeze_specification(PROOF/'FROZEN_WORK_SPECIFICATION_v1.md',fields)
directory = ROOT/'runs/session'/ids['session']
assert not directory.exists()
boundary = sb.SessionBoundary(ids['session'],directory)
binding = boundary.create_binding(frozen,ids['loop'])
current = bound.freeze_current_reference(binding,current_file,'REF')
parent = bound.prepare(boundary,binding,goal={'text':goal,'authority_ref':'USER'},must_haves=tuple({'text':m,'authority_ref':'REF' if i==0 else 'USER'} for i,m in enumerate(must)),stage_criteria=stage_criteria,child_ids={k:ids[k] for k in bound.KINDS},current_reference=current)
startup = sb.build_startup_context(sb.ContextRecord('CURRENT_REQUEST',str(PROOF/'CURRENT_REQUEST.md')),(sb.ContextRecord('CURRENT_REFERENCE',bound.reference_authority(current_file)),),tuple(sb.ContextRecord('VERIFIED_FACT',x) for x in ['C-01 criterion applicability stabilized','I-03 namespace preflight stabilized','Current Reference binding stabilized','Current Reference normalization stabilized','Previous actual acceptance and Delivery/Closure are historical verified facts; no current state is imported','I-01 and I-02 deferred P2']))
write(directory/'startup_context.json',[asdict(x) for x in startup])
prepared={'ids':ids,'parent':parent,'frozen_specification':asdict(frozen),'specification_identity_sha256':frozen.identity_sha256,'binding_identity_sha256':binding.identity_sha256,'original':asdict(current_file),'current_reference':asdict(current),'normalization':transform,'preview':l6.png_identity(PROOF/'NORMALIZATION_PREVIEW.png','execution_preview'),'stage_criteria':stage_criteria,'no_previous_state_reuse':True,'source_test_changes':0,'generation_effects':0,'delivery':False}
write(PROOF/'PREPARED_BINDING.json',prepared)
checks = bound.run_session(parent,execute=False)
stats = l6.worker.request_json('/system_stats')
nodes = l6.worker.request_json('/object_info')
assets = l6.preflight(l6.worker.DEFAULT_COMFY_ROOT,current_reference=asdict(current),run_id=ids['l6'])
required=set().union(*(set(x['node_classes'].values()) for x in [*assets['view_generation'].values(),assets['geometry']]))
missing=sorted(required-set(nodes))
assert not missing, missing
queue = l6.worker.request_json('/queue')
assert not queue.get('queue_running') and not queue.get('queue_pending'), 'Existing queue work; no generation authorized yet'
models=[]
for model in assets['models']:
    p=pathlib.Path(model['path']); models.append(model|{'mtime_ns':p.stat().st_mtime_ns})
blender=subprocess.run([str(bridge.BLENDER),'--version'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=20)
assert blender.returncode==0 and bridge.BLENDER_VERSION in blender.stdout
runtime={'entry_preflight':checks,'stats':stats,'required_node_classes':sorted(required),'missing_classes':missing,'models':models,'workflow_pins':[{'path':x['workflow'],'sha256':x['sha256']} for x in [*assets['view_generation'].values(),assets['geometry']]],'queue':queue,'blender_version':blender.stdout.splitlines()[0],'reviewer_auth':auth_mode(os.environ),'python':sys.version,'pillow':pillow_version,'generation_effects':0,'preview_pixel_rectangle_unchanged':True,'namespace_gate':'PASS; 3 repository child + 7 external namespaces absent'}
assert runtime['reviewer_auth']=='CHATGPT_ACCOUNT'
write(PROOF/'RUNTIME_READINESS.json',runtime)
print(json.dumps({'ids':ids,'parent':parent,'original':asdict(current_file),'normalization':transform,'readiness':'STATIC_RUNTIME_PASS; full regression and semantic CLI probe pending'},ensure_ascii=True))
