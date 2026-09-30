import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
import uuid

ROOT = Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
REQUEST = Path(r'C:\Users\Worker\.codex\attachments\38fe8b88-5a10-4378-8af5-6ca46db889f9\붙여넣은 텍스트.txt')
sys.path.insert(0, str(ROOT / 'src'))
from session import session_boundary as sb
from scenario_a import session_binding as bound
from scenario_a import l6_pipeline as l6
from core import reviewer_auth

def git(*args, root=ROOT):
    return subprocess.check_output(['git', '-c', 'safe.directory=' + root.as_posix(), '-C', str(root), *args], text=True, encoding='utf-8').strip()

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def once(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    l6.write_once(path, data)

def snapshot(root):
    paths = git('ls-files', root=root).splitlines()
    return {p: sha(root / p) for p in paths if (root / p).is_file()}

baseline = '89201d2511985a054cfc3045768e6b29ef62e5cf'
assert git('rev-parse', 'HEAD') == baseline
assert git('rev-parse', 'origin/session-bound-scenario-s3b') == baseline
assert git('branch', '--show-current') == 'session-e2e-s3c'
assert not git('status', '--porcelain=v1')
assert not list((ROOT / 'runs').rglob('*s3c*'))
assert not (ROOT / 'docs/session/S3C_WORK_SPECIFICATION_v1.md').exists()

stamp = datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d-%H%M%S')
suffix = stamp + '-' + uuid.uuid4().hex[:8]
ids = {'session': 's3c-session-' + suffix, 'loop': 's3c-loop-' + suffix,
       'l6': 's3c-l6-' + suffix, 'bridge': 's3c-bridge-' + suffix,
       'correction': 's3c-correction-' + suffix}
assert len(set(ids.values())) == 5
session_dir = ROOT / 'runs/session' / ids['session']
paths = [session_dir, ROOT / 'runs/l6' / ids['l6'], ROOT / 'runs/l7' / ids['bridge'], ROOT / 'runs/l7' / ids['correction']]
comfy = l6.worker.DEFAULT_COMFY_ROOT
paths += [comfy / 'work/input/l6' / ids['l6'], comfy / 'work/output/l6' / ids['l6'],
          comfy / 'work/output/mesh/l6' / ids['l6'], comfy / 'work/output/l7' / ids['bridge'],
          comfy / 'work/input/l7' / ids['correction'], comfy / 'work/output/l7' / ids['correction'],
          comfy / 'work/output/mesh/l7' / ids['correction']]
assert all(not p.exists() for p in paths)
research = Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop')
assets = l6.read_json(l6.ASSET_MANIFEST)
external = [assets['source']['path']] + [v['workflow'] for v in assets['view_generation'].values()] + [assets['geometry']['workflow']] + [v['path'] for v in assets['models']] + [v['path'] for v in assets['inspected_files'] if not Path(v['path']).is_relative_to(ROOT)]
external_snapshot = {}
for p in sorted(set(external)):
    q = Path(p); s = q.stat()
    external_snapshot[p] = {'bytes': s.st_size, 'mtime_ns': s.st_mtime_ns,
                            'sha256': sha(q) if s.st_size < 32 * 1024 * 1024 else None}
protected = {'baseline': baseline, 'refs': git('show-ref'), 'tracked': snapshot(ROOT),
             'research': {'head': git('rev-parse', 'HEAD', root=research),
                          'status': git('status', '--porcelain=v1', root=research),
                          'tracked': snapshot(research), 'wip_sha256': sha(research / 'ac6_f2b_resume.py')},
             'external': external_snapshot}
session_dir.mkdir(parents=True)
once(session_dir / 'protection_before.json', protected)
request_path = session_dir / 'user_request.md'
with request_path.open('xb') as f: f.write(REQUEST.read_bytes())
assert sha(request_path) == sha(REQUEST)
once(session_dir / 'identities.json', ids)

goal = '현재 canonical Scenario A input을 사용하여 실제 Single Image → Multiview → 3D Geometry Session을 한 번 실행하고, 최종 GLB를 사용자 평가 가능한 상태까지 만든다.'
mh1 = 'right/left/back multiview는 canonical front source와 동일한 대상을 유지하고, 주요 실루엣과 구조 파츠를 보존하며, 심각한 crop, missing/detached major part, cross-view identity contradiction이 없어야 한다.'
mh2 = 'final GLB는 canonical source와 동일한 대상으로 인식 가능하도록 주요 실루엣, 비율, 주요 구조 파츠를 보존해야 하며 심각한 변형이나 분리된 주요 파츠가 없어야 한다.'
ac1 = 'Generated multiview images must depict the same canonical source object, preserve its recognizable major silhouette and structural parts, and contain no severe crop, missing/detached major part, or cross-view identity contradiction.'
ac2 = 'The final GLB must remain recognizable as the canonical source object by preserving its major silhouette, proportions, and structural parts without severe deformation or detached major parts.'
source_ref = assets['source']['path'] + '#sha256=' + assets['source']['sha256']
request_ref = str(request_path) + '#sha256=' + sha(request_path)
spec_path = ROOT / 'docs/session/S3C_WORK_SPECIFICATION_v1.md'
spec = f'''# S3C Work Specification v1

## 1. Identity / Lineage
- session_id: {ids['session']}
- specification_version: v1
- request_type: NEW_WORK
- previous_session_id: null; S3B handoff is durable reference, not a resumed Session.
- lineage: S3B baseline {baseline}; current User Request: {request_ref}
- logical_loop_run_id: {ids['loop']}
- l6_child_id: {ids['l6']}
- bridge_child_id: {ids['bridge']}
- correction_child_id: {ids['correction']}
- stable Session directory: {session_dir}

## 2. User Goal
{goal}

Original request summary: one actual fixed Scenario A bound Session, proving lifecycle up to the observable delivery boundary.
Project context: Core v1 frozen, S3B LOCAL-VERIFIED. This is a fresh actual proof; historical outcomes retain their original scope.

## 3. References / Acceptance Authority
| reference_id | exact source_ref | role / authority | preserved scope |
|---|---|---|---|
| USER_CURRENT_REQUEST | {request_ref} | Goal, both Must-Haves, acceptance criteria, execution authorization and bounds | The current User Request controls acceptance |
| CANONICAL_SOURCE | {source_ref} | canonical front identity; 768 x 768 PNG | recognizable silhouette, proportions and major structural parts |

The source image is identity/major-structure authority. Texture, color, PBR, UV, isolated eye/sign detail, smoothness, topology aesthetics, normals and benchmark are not additional acceptance criteria. An observed defect can matter only where it violates a declared identity/major-structure criterion.

## 4. Intended Use
User evaluation of an actual generated GLB and diagnostic evidence. Production platform/performance targets are irrelevant to this proof and are not acceptance requirements.

## 5. Deliverables
One actual final GLB; actual final geometry Review; diagnostic renders and references; immutable Request/Spec/Session/execution lineage. Delivery Package only after INTERNAL_ACCEPT. A failed/aborted candidate remains diagnostic evidence.

## 6. Must-Have
- {mh1}
- {mh2}
Both derive from USER_CURRENT_REQUEST and use CANONICAL_SOURCE for object identity.

## 7. Should-Have
[]

## 8. Non-Goals
Texture, PBR, UV, benchmark quality, generalized geometry quality research, correction policy redesign, new transport, fresh-context infrastructure, Core refactor.

## 9. Acceptance Criteria
| criterion_id | description | authority_ref / reference evidence | blocking_when_unmet |
|---|---|---|---|
| AC-MULTIVIEW-COHERENCE | {ac1} | USER_CURRENT_REQUEST / CANONICAL_SOURCE, MH1 | true |
| AC-GEOMETRY-IDENTITY | {ac2} | USER_CURRENT_REQUEST / CANONICAL_SOURCE, MH2 | true |

Stage projection: multiview = AC-MULTIVIEW-COHERENCE; geometry = AC-MULTIVIEW-COHERENCE + AC-GEOMETRY-IDENTITY. Final geometry covers every declared criterion.
Evidence: exact canonical/source-view image attachments, current GLB-linked diagnostic renders, structured actual Review with authority tags and coverage.
PASS requires mandatory criteria satisfied, no blockers and NONE/null. REVISE requires a declared blocker and supported existing action. No additional criterion is authorized.

## 10. Constraints
- loop_budget: Worker 6 / semantic Reviewer 4 / Renderer 2 / correction 1 / automatic retries 0; conservative aggregate maximum, not a quota.
- actual Session attempts: exactly one run_session(execute=True), after Ready Gate and checkpoint commit.
- deadline: null; no deadline supplied.
- cost: null; no monetary/token estimate; account auth must be CHATGPT_ACCOUNT.
- runtime: existing ComfyUI at http://127.0.0.1:8188, current manifest workflows/models, existing Blender diagnostic.
- format: actual GLB; PNG diagnostic/reference evidence.
- legal/usage: canonical existing source for authorized proof; no new download or usage expansion.
- first production effect makes this attempt immutable. No rerun, extra Review, blind retry, seed reroll, namespace replacement or in-place runtime repair.
- first effect after readiness may occur only while canonical source/manifest/workflow/model/Spec identities still match.

## 11. Interpretation Envelope
fixed_four_view_glb_seed_only
Use current fixed topology and current parameters. Seed-only correction policy remains at most one supported correction and makes no quality improvement guarantee. Frontier selects technical invocation details within this existing capability.

## 12. Explicit User Decisions
The attached current prompt authorizes S3C readiness, genuine freeze, checkpoint commit, and immediate one-shot actual execution after PASS without further permission. Acceptance is limited to the two specified criteria. Stop conditions and proof integrity rules remain binding.

## 13. Known Unknowns
Runtime readiness is probed before execution. Actual semantic closure is unknown. Backend model identity/tokens/credits are recorded only if observable. Authentic post-submission receipt and external fresh-context reset are NOT VERIFIED. These unknowns do not add quality criteria.

## 14. Readiness
- SPECIFICATION_READY: true
- unresolved_blocking_ambiguities: []
- readiness_reason: Current Request explicitly supplies Goal, reference authority, intended deliverable, Must-Haves, criteria, interpretation envelope and execution bounds; no decision-critical intent ambiguity remains.

## 15. Freeze / Delivery Boundary
Document bytes, finalized projection and all five identities are fixed before execution. INTERNAL_ACCEPT is not DELIVERED. prepare_delivery only after actual final acceptance evidence validation. Authentic observable submission receipt is required for DELIVERED/CLOSED. No receipt prediction. Input and final Output are presented together for external User evaluation, which stays outside Core state.
'''
with spec_path.open('x', encoding='utf-8', newline='\n') as f: f.write(spec)
fields = sb.FinalizedFields(ids['session'], 'v1', 'NEW_WORK', True, (),
    (sb.AcceptanceCriterion('AC-MULTIVIEW-COHERENCE', 'USER_CURRENT_REQUEST', True, ac1),
     sb.AcceptanceCriterion('AC-GEOMETRY-IDENTITY', 'USER_CURRENT_REQUEST', True, ac2)),
    (sb.AuthorityReference('USER_CURRENT_REQUEST', request_ref), sb.AuthorityReference('CANONICAL_SOURCE', source_ref)),
    (bound.CAPABILITY,))
frozen = sb.freeze_specification(spec_path, fields)
boundary = sb.SessionBoundary(ids['session'], session_dir)
binding = boundary.create_binding(frozen, ids['loop'])
parent_ref = bound.prepare(boundary, binding,
    goal={'text': goal, 'authority_ref': 'USER_CURRENT_REQUEST'},
    must_haves=({'text': mh1, 'authority_ref': 'USER_CURRENT_REQUEST'}, {'text': mh2, 'authority_ref': 'USER_CURRENT_REQUEST'}),
    stage_criteria={'multiview': ('AC-MULTIVIEW-COHERENCE',), 'geometry': ('AC-MULTIVIEW-COHERENCE', 'AC-GEOMETRY-IDENTITY')},
    child_ids={k: ids[k] for k in bound.KINDS})

blocked = []
phase = 'preflight'
def audit(event, args):
    if phase == 'preflight' and event in ('subprocess.Popen', 'urllib.Request', 'socket.connect'):
        raise RuntimeError('ZERO_EFFECT_PREFLIGHT_VIOLATION: ' + event)
sys.addaudithook(audit)
source = l6.png_identity(assets['source']['path'], 'front')
assert source == assets['source'], 'BLOCKED_INPUT_IDENTITY_CHANGED'
preflight = bound.run_session(parent_ref, execute=False)
assert preflight['status'] == 'PREFLIGHT_PASS' and preflight['effects'] == 0
phase = 'readiness'
once(session_dir / 'preflight.json', preflight)
comfy_status = {}
try:
    with urllib.request.urlopen('http://127.0.0.1:8188/system_stats', timeout=20) as r:
        comfy_status = json.load(r)
    if not comfy_status.get('devices'):
        blocked.append('BLOCKED_RUNTIME_UNAVAILABLE: no actual devices')
except Exception as e:
    blocked.append('BLOCKED_RUNTIME_UNAVAILABLE: ' + type(e).__name__ + ': ' + str(e))
once(session_dir / 'comfy_system_stats.json', {'observed_at': l6.now(), 'response': comfy_status})
auth = reviewer_auth.auth_mode(os.environ)
if auth != 'CHATGPT_ACCOUNT': blocked.append('BLOCKED_BY_AUTH_MODE: ' + auth)
cp1 = {'baseline': baseline, 'identities': ids, 'specification': {'path': str(spec_path), 'sha256': sha(spec_path), 'identity_sha256': frozen.identity_sha256},
       'session_binding': parent_ref, 'source': source, 'preflight': preflight,
       'comfy_devices': comfy_status.get('devices'), 'reviewer_auth': auth,
       'actual_counts': {'comfy_submissions': 0, 'semantic_reviewer': 0, 'blender_production': 0, 'correction_dispatch': 0},
       'blockers': blocked, 'verdict': 'S3C ACTUAL_EXECUTION_READY' if not blocked else 'S3C READINESS BLOCKED'}
once(session_dir / 'checkpoint1.json', cp1)
print(json.dumps(cp1, ensure_ascii=False, indent=2))
print('SESSION_DIRECTORY=' + str(session_dir))
