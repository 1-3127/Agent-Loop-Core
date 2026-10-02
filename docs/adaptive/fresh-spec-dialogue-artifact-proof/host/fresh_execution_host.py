"""Fresh clarification-to-artifact host. Historical subjects are not authority.
Generic controller/runner glue reused from published M8 host; new diagnostic and
delivery hosts. No Core source changes. Each terminal Session is immutable.
"""
from dataclasses import asdict
from pathlib import Path
import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
ROOT = Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
WORK = Path(__file__).resolve().parent
DIRECTORY = ROOT / 'docs/adaptive/fresh-spec-dialogue-artifact-proof'
OUTPUT = Path(r'C:\Users\Worker\Documents\Codex\2026-10-02\codex-specification-dialogue-human-blocking-text\outputs\fresh-spec-dialogue-artifact-proof')
SID = 'fresh-spec-dialogue-artifact-001'
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
from core.adaptive_loop import AdaptiveSession
from core.adaptive_artifacts import ArtifactStore, ArtifactRef
from core.artifact_review import ArtifactReviewer
from core.event_logging import reconstruct
from core.frontier import CodexInferenceAdapter, FrontierSupervisor
from core.skill_artifact import canonical_bytes, create_skill, record_validation, write_once
from core.skill_registry import SkillRegistry
from core.workflow_artifact import WorkflowPlanner, WorkflowRef, freeze_workflow_scope
from scenario_a.adaptive_adapter import ExecutionAdapter
from session.session_boundary import AcceptanceCriterion, AuthorityReference, FinalizedFields, FileIdentity, file_identity, freeze_specification
REQUEST = (DIRECTORY / 'authority/ORIGINAL_REQUEST.txt').read_text(encoding='utf-8')
RESPONSE = (DIRECTORY / 'authority/USER_RESPONSE_001.txt').read_text(encoding='utf-8')
BLENDER = Path(r'D:\Blender_5.2\blender.exe')
CLI = r'C:\Users\Worker\AppData\Local\OpenAI\Codex\bin\c6fe824d725f02d7\codex.exe'
ADAPTER = CodexInferenceAdapter(WORK, timeout=900, executable=CLI)

def current_runtime_readiness():
    assert BLENDER.is_file() and Path(CLI).is_file()
    return json.loads((DIRECTORY / 'RUNTIME_READINESS.json').read_text(encoding='utf-8'))

def copy_once(source, target):
    target = Path(target); target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == Path(source).read_bytes(), 'OUTPUT_SNAPSHOT_CHANGED'
        return
    with target.open('xb') as stream: stream.write(Path(source).read_bytes())

def snapshot(destination):
    for source in sorted(DIRECTORY.rglob('*')):
        if source.is_file(): copy_once(source, destination / source.relative_to(DIRECTORY))

def complete_output_snapshot(session):
    counters = {'Production Run': session.run_count, 'Attempt': session.attempt_count,
        'Worker': len(list(DIRECTORY.glob('session/production_runs/*/attempts/*/execution-*/worker_invocation/reservation.json'))),
        'Production Reviewer': len(list(DIRECTORY.glob('session/production_runs/*/attempts/*/review*/invocation/reservation.json'))),
        'ComfyUI production': 0,
        'Blender production': len(list(DIRECTORY.glob('session/production_runs/*/attempts/*/execution-*/build.stdout.txt'))) + len(list(DIRECTORY.glob('session/production_runs/*/attempts/*/diagnostics-*/render.stdout.txt'))),
        'Artifact generation': len(list(DIRECTORY.glob('session/production_runs/*/artifacts/*.json'))),
        'Frontier production': len(list(DIRECTORY.glob('decisions/*/invocation/reservation.json'))),
        'Frontier intake': 2}
    write_once(DIRECTORY / 'FINAL_EFFECT_COUNTERS.json', {'actual_dispatch_counters': counters,
        'diagnostic_episodes': len(list(DIRECTORY.glob('session/production_runs/*/attempts/*/diagnostics-*/manifest.json'))),
        'artifact_counter_scope': 'ArtifactStore production records; all generated diagnostic images/metrics individually listed in delivery/audit manifest',
        'session_terminal': session.boundary.outcome.status})
    destination = OUTPUT / 'delivery' / 'evidence'
    snapshot(destination)
    manifest = {str(p.relative_to(OUTPUT / 'delivery')).replace('\\','/'): {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in sorted((OUTPUT / 'delivery').rglob('*')) if p.is_file()}
    write_once(OUTPUT / 'delivery' / 'FINAL_AUDIT_MANIFEST.json', {'session_id': SID,
        'terminal':session.boundary.outcome.status, 'files':manifest, 'effect_counters':counters,
        'human_post_session_quality_judgment':'NOT PERFORMED; outside the CLOSED Core Session',
        'all_generated_intermediates_preserved':True})
    write_once(DIRECTORY / 'OUTPUT_AUDIT_MANIFEST.json', {'manifest_ref':asdict(file_identity(OUTPUT / 'delivery' / 'FINAL_AUDIT_MANIFEST.json','user-output-manifest'))})

def deliver(session, skills, reference, worker_invocations):
    package = session.boundary.prepare_delivery()
    data = json.loads(Path(package.path).read_text(encoding='utf-8'))
    destination = OUTPUT / 'delivery'
    assert not destination.exists(), 'DELIVERY_NAMESPACE_COLLISION'
    destination.mkdir(parents=True)
    source = FileIdentity(**data['artifact'])
    exported = destination / 'railing-and-concrete-base.glb'
    copy_once(source.path, exported)
    copy_once(reference.path, destination / 'original-reference.png')
    copy_once(DIRECTORY / 'SPECIFICATION.md', destination / 'Frozen-Work-Specification.md')
    copy_once(session.run['workflow'].file.path, destination / 'Workflow-used.json')
    for name in ('asset.blend','asset_source.py','build_metrics.json'):
        copy_once(Path(source.path).parent/name,destination/name)
    for artifact,review in session.current_reviews.values():
        review_data=json.loads(Path(review.file.path).read_text(encoding='utf-8'))
        copy_once(review.file.path,destination/('final-review-'+artifact.metadata.identity+'.json'))
        review_request=json.loads(Path(review_data['request_ref']['path']).read_text(encoding='utf-8'))
        for entry in review_request['image_refs'][1:]:
            image=FileIdentity(**entry)
            if Path(image.path).stem in ('material-perspective','material-front'):
                copy_once(image.path,destination/Path(image.path).name)
    snapshot(destination/'evidence')
    record_path=DIRECTORY/'handoff.json'
    write_once(record_path,{'session_id':SID,'delivery_package':asdict(package),'boundary':'LOCAL_DELIVERABLE_EXPORT',
        'delivered_artifact':asdict(file_identity(exported,'delivered-railing-and-base')),
        'delivered_references':[asdict(file_identity(destination/'original-reference.png','delivered-original-reference'))],
        'observation_scope':'LOCAL_FILES_VERIFIED_HUMAN_RECEIPT_NOT_OBSERVED'})
    terminal=session.boundary.record_local_handoff(package,file_identity(record_path,'actual-handoff'))
    session.logger.emit('acceptance/delivery','LOCAL_HANDOFF_CLOSED',output_refs=(terminal,),reason_code='LOCAL_DELIVERABLE_FILES_VERIFIED')
    frontier_invocations=[FileIdentity(**json.loads(p.read_text(encoding='utf-8'))['frontier_invocation_ref']) for p in (DIRECTORY/'decisions').glob('*/decision.json')]
    success=DIRECTORY/'ACTUAL_SUCCESS.json'
    used=session.run['workflow'].validate(session.frozen,session.scope)['skill_refs']
    write_once(success,{'scope':'ACTUAL','INTERNAL_ACCEPT':True,'session_terminal':'CLOSED','session_id':SID,
        'production_run_id':session.state()['production_run_id'],'skill_refs':used,
        'review_refs':[asdict(r.file) for _,r in session.current_reviews.values()],
        'frontier_invocation_refs':[asdict(r) for r in frontier_invocations],
        'known_limitations':['One photograph; absolute scale and unseen surfaces inferred; validation applies only to observed successful use'],
        'terminal_ref':asdict(terminal),'acceptance_gate_ref':asdict(file_identity(session.directory/'acceptance_gate.json','acceptance-gate'))})
    for skill in skills:
        if asdict(skill) in used:record_validation(skill,file_identity(success,'actual-success'),DIRECTORY/('skill-validation-'+skill.skill_id+'.json'))

def prepare():
    assert not (DIRECTORY/'session').exists()
    baseline=json.loads((DIRECTORY/'BASELINE_GATE.json').read_text(encoding='utf-8'))
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in baseline['tracked_file_sha256'].items())
    for name in ('fresh_execution_host.py','fresh_mesh_diagnostics.py'):
        copy_once(WORK/name,DIRECTORY/'host'/name)
    write_once(DIRECTORY/'EXECUTION_HOST_MANIFEST.json',{'host_refs':[asdict(file_identity(DIRECTORY/'host'/n,n)) for n in ('fresh_execution_host.py','fresh_mesh_diagnostics.py')],
        'reused_execution_knowledge_source':asdict(file_identity(ROOT/'docs/adaptive/M8_CONTRACT_HOST_V3.py','published-host-execution-glue')),
        'reuse_scope':'Public contract orchestration/guarded runner only; no historical Request/Reference/Specification/Artifact/Review/criteria passed as new subject authority',
        'core_source_changes':False})


def fields_from(data):
    data = dict(data)
    assert data['unresolved_blocking_ambiguities'] == [], 'UNRESOLVED_SPECIFICATION_AMBIGUITY'
    data['acceptance_criteria'] = tuple(AcceptanceCriterion(**v) for v in data['acceptance_criteria'])
    data['authority_references'] = tuple(AuthorityReference(**v) for v in data['authority_references'])
    data['unresolved_blocking_ambiguities'] = ()
    data['interpretation_envelope'] = tuple(data['interpretation_envelope'])
    return FinalizedFields(**data)

def workflow_from(data):
    data = dict(data)
    data['file'] = FileIdentity(**data['file'])
    return WorkflowRef(**data)

def checked_worker_code(code):
    tree = ast.parse(code)
    if not any(isinstance(n, ast.FunctionDef) and n.name == 'build_asset' for n in tree.body):
        raise ValueError('WORKER_BUILD_FUNCTION_REQUIRED')
    banned = {'open', 'eval', 'exec', 'compile', '__import__', 'input', 'breakpoint', 'save_as_mainfile', 'open_mainfile',
        'read_homefile', 'gltf', 'load', 'system', 'popen'}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(n.name not in ('bpy', 'math', 'random', 'mathutils') for n in node.names):
            raise ValueError('WORKER_IMPORT_NOT_REVIEWED')
        if isinstance(node, ast.ImportFrom) and node.module not in ('math', 'mathutils', 'random'):
            raise ValueError('WORKER_IMPORT_NOT_REVIEWED')
        if isinstance(node, ast.Name) and (node.id in banned or node.id.startswith('__')):
            raise ValueError('WORKER_CODE_OUTSIDE_GEOMETRY_AUTHORITY')
        if isinstance(node, ast.Attribute) and (node.attr in banned or node.attr.startswith('__')):
            raise ValueError('WORKER_CODE_OUTSIDE_GEOMETRY_AUTHORITY')
    return tree

def process(args, directory, name, timeout=900):
    result = subprocess.run(args, capture_output=True, timeout=timeout)
    (directory / (name + '.stdout.txt')).write_bytes(result.stdout)
    (directory / (name + '.stderr.txt')).write_bytes(result.stderr)
    return {'exit_code': result.returncode, 'command': args,
        'stdout_ref': asdict(file_identity(directory / (name + '.stdout.txt'), name + '-stdout')),
        'stderr_ref': asdict(file_identity(directory / (name + '.stderr.txt'), name + '-stderr'))}

def run():
    readiness = current_runtime_readiness()
    write_once(DIRECTORY / 'PRE_EXECUTION_READINESS.json', readiness)
    intake = json.loads((DIRECTORY / 'INTAKE_RESULT.json').read_text(encoding='utf-8'))
    fields = fields_from(intake['specification']['fields'])
    frozen = freeze_specification(DIRECTORY / 'SPECIFICATION.md', fields)
    assert canonical_bytes(asdict(frozen)) == canonical_bytes(intake['specification']), 'INTAKE_SPECIFICATION_CHANGED'
    scope, reference = FileIdentity(**intake['scope_ref']), FileIdentity(**intake['reference_ref'])
    scope.validate(); reference.validate()
    revision = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD']).decode().strip()
    skill_path = 'skills/v1/blender-modeling-workflow/core.json'
    committed = subprocess.check_output(['git', '-C', str(ROOT), 'show', revision + ':' + skill_path])
    assert committed == (ROOT / skill_path).read_bytes(), 'SKILL_NOT_COMMITTED_AT_PIN'
    registry = SkillRegistry(ROOT / 'skills', revision)
    skills = registry.search('reference')
    for skill in skills:
        metadata = skill.validate()
        package = Path(skill.metadata.path).parent
        for name, digest in metadata['files'].items():
            relative = (package / name).relative_to(ROOT).as_posix()
            committed = subprocess.check_output(['git', '-C', str(ROOT), 'show', revision + ':' + relative])
            assert hashlib.sha256(committed).hexdigest() == digest, 'SKILL_SUPPORT_NOT_RECOVERABLE_AT_VCS_PIN'
    planner = WorkflowPlanner(registry, ('blender_geometry',))
    session = AdaptiveSession(frozen, scope, DIRECTORY / 'session', intake['resource_limits'], seconds=intake['deadline_seconds'], mode='ACTUAL')
    session.logger.emit('skills', 'USER_WORKFLOW_REVIEW_REQUESTED_NON_BLOCKING', output_refs=tuple(s.metadata for s in skills),
        reason_code='REVIEWED_CANDIDATE_SKILL_VERSION_HASH_DISCLOSED_NO_REPLY_REQUIRED')
    count, previous_code, latest_artifact, latest_review = 0, None, None, None
    previous_source, previous_reviews, current_decision = None, (), None
    evidence_extra, images_extra, worker_invocations = (), (), []

    def diagnose():
        nonlocal count
        count += 1
        reserved = session.resources.reserve('frontier_calls', session.state())
        workflow = session.run['workflow'] if session.run else None
        reviews = tuple(r.file for _, r in session.current_reviews.values())
        artifacts = tuple(a.metadata for a, _ in session.current_reviews.values()) + evidence_extra
        decision = FrontierSupervisor(ADAPTER).decide(frozen, scope, state=session.state(), workflow=workflow,
            artifacts=artifacts, reviews=reviews, skills=skills,
            capabilities={'available': ['blender_geometry'], 'tools': {'blender-cli': 'Model-authored bpy geometry; immutable GLB/blend; independent fresh-import evidence'},
                'runtime_observations': readiness,
                'models': 'Saved-account configured model, actual identity recorded only if observable',
                'planning_interface': {'proposal_fields': ['workflow_id', 'version', 'selected_skills', 'stages'],
                    'stage_fields': ['stage_id', 'skill_id', 'skill_version', 'capability', 'tool', 'model', 'input_artifact_types', 'output_artifact_type', 'criterion_ids', 'parameters'],
                    'initial_workflow_version': 1, 'model_for_blender_cli': None,
                    'evidence_parameters': {'camera_azimuth': 'degrees, -360..360', 'camera_elevation': 'degrees, -80..80',
                        'target_height_ratio': 'relative to exported GLB Z bounds, 0..1', 'orthographic_scale_factor': '0.25..2'},
                    'selected_skills_shape': '{skill_id,version,content_hash}',
                    'stage_semantics': 'Use parameters for actual construction strategy, reference interpretation, geometry instructions and local_parameter_names. '
                        'The frozen Specification allows at most two Attempts per Run; after two finished Attempts use evidence acquisition or Workflow revision/new Run rather than a third local Attempt. Each stage produces an inspectable geometry artifact. The host supplies fresh-import diagnostics and an independent Review. '
                        'CONTINUE starts an Attempt when none exists, otherwise executes the next incomplete stage; '
                        'REVISE_ARTIFACT starts a local correction Attempt under the same Workflow. '
                        'REVISE_WORKFLOW materializes a candidate; a separate RESTART_PRODUCTION_RUN must select it. '
                        'ACCEPT requires all mandatory current outcomes MET. Seed-only changes must use an Attempt. '
                        'STOP needs a justified resource/capability/technical reason. Do not invent user approval gates. '
                        'action_parameters_json may specify stage_id, instruction, local_parameters. '
                        'New Skill proposals are a JSON list of {guidance,metadata}; metadata uses the existing available Skill metadata field schema '
                        'with new skill_id/version, empty files/content_hash to be computed by the host, CANDIDATE status and no validation claims. '
                        'They may not include external executable code. Request Skill creation with CONTINUE and no workflow_proposal_json first; '
                        'then plan using the actual hashes supplied in the next invocation.'}},
            envelope=session.resources.remaining(), directory=DIRECTORY / ('decisions/decision-%03d' % count),
            images=(reference,) + images_extra, planner=planner, workflow_output=DIRECTORY / ('workflows/workflow-%03d.json' % count),
            candidate_workflow=session.pending_workflow)
        data = json.loads(Path(decision.path).read_text(encoding='utf-8'))
        session.logger.emit('frontier', 'FRONTIER_DECISION', state=session.state(), input_refs=(reserved,), output_refs=(decision,),
            decision=data['selected_action'], reason_code='ACTUAL_MODEL_INFERENCE')
        if data['workflow_proposal_json']:
            selected = workflow_from(data['selected_workflow_ref'])
            session.logger.emit('workflow', 'USER_WORKFLOW_REVIEW_REQUESTED_NON_BLOCKING', output_refs=(selected.file,),
                reason_code='ACTUAL_FRONTIER_VERSIONED_PLAN_NO_REPLY_REQUIRED',
                identities={'workflow_id': selected.workflow_id, 'workflow_version': selected.version})
            print(json.dumps({'event': 'WORKFLOW_DISCLOSED_NON_BLOCKING', 'ref': asdict(selected),
                'stages': selected.validate(frozen, scope)['stages'], 'reason': data['reason_summary']}, ensure_ascii=True), flush=True)
        print(json.dumps({'decision': count, 'action': data['selected_action'], 'reason': data['reason_summary'], 'state': session.state()}, ensure_ascii=True), flush=True)
        return decision, data

    def runner(order):
        nonlocal previous_code, previous_source
        directory = Path(order['output_directory'])
        if previous_source:
            previous_source.validate()
        for prior in previous_reviews:
            prior.validate()
        context = {'role': 'BLENDER_WORKER_CODE_AUTHOR', 'original_request': REQUEST, 'frozen_specification': asdict(frozen),
            'specification_document': Path(frozen.reference.specification_path).read_text(encoding='utf-8'),
            'work_order': order, 'skill_guidance': [Path(s.metadata.path).with_name('SKILL.md').read_text(encoding='utf-8') for s in skills],
            'current_reviews': [json.loads(Path(r.file.path).read_text(encoding='utf-8')) for _, r in session.current_reviews.values()],
            'actual_user_clarification': RESPONSE,
            'supporting_skill_guidance': {n: (Path(s.metadata.path).parent / n).read_text(encoding='utf-8') for s in skills for n in s.validate()['files'] if n.startswith('references/') and n.endswith('.md')},
            'previous_code': previous_code, 'previous_source_ref': asdict(previous_source) if previous_source else None,
            'prior_review_refs': [asdict(r) for r in previous_reviews],
            'prior_reviews_for_explicit_local_correction': [json.loads(Path(r.path).read_text(encoding='utf-8')) for r in previous_reviews],
            'frontier_decision': current_decision,
            'instructions': 'Return code with imports limited to bpy, math, mathutils, random and a build_asset() function. '
                'Construct the reference subject according to the selected immutable Workflow stage parameters and current correction instruction. '
                'Do not read or write files, export/save, load images, contact network, execute processes, use eval/exec/open, or change criteria. '
                'The host starts a clean Blender 5.2 scene and owns export, saving and diagnostics. You may remove your temporary cutters. '
                'Produce named meshes with genuine requested negative space, connected/consistent requested structure, the reference material regions and faithful proportions. '
                'Use actual supported bpy APIs. Apply needed geometry modifiers or leave them for host GLB export with export_apply. '
                'Reference image contains occluding background/foreground objects; interpret the target from the original frozen specification. '
                'Orient reference front toward -Y, railing width along X and height along Z for the installed diagnostic cameras. Use only export-supported materials or actual mesh details; procedural shader detail may not survive GLB. No camera or light is needed. Return observations_json as concise factual construction notes, not semantic acceptance.'}
        write_once(directory / 'worker_request.json', context)
        schema = {'type': 'object', 'additionalProperties': False, 'required': ['reason_summary', 'code', 'observations_json'],
            'properties': {k: {'type': 'string'} for k in ('reason_summary', 'code', 'observations_json')}}
        inference = ADAPTER(file_identity(directory / 'worker_request.json', 'worker-code-request'), schema, directory / 'worker_invocation', (reference,) + images_extra)
        worker_invocations.append(inference.invocation)
        generated = json.loads(Path(inference.result.path).read_text(encoding='utf-8'))
        code = generated['code']
        try:
            checked_worker_code(code)
        except ValueError as exc:
            return {'status': 'FAILED', 'outputs': [], 'observations': {'reason_code': str(exc), 'worker_invocation_ref': asdict(inference.invocation)}}
        script = directory / 'asset_source.py'
        script.write_text(code, encoding='utf-8')
        previous_code = code
        previous_source = file_identity(script, 'previous-authored-source')
        wrapper = directory / 'build.py'
        wrapper.write_text('import bpy, runpy, json\nfrom pathlib import Path\n' +
            'out = Path(' + repr(str(directory)) + ')\n' +
            'bpy.ops.object.select_all(action="SELECT")\nbpy.ops.object.delete(use_global=False)\n' +
            'runpy.run_path(str(out / "asset_source.py"))["build_asset"]()\n' +
            'meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]\n' +
            'assert meshes and sum(len(o.data.polygons) for o in meshes) > 0\n' +
            'bpy.ops.wm.save_as_mainfile(filepath=str(out / "asset.blend"))\n' +
            'bpy.ops.export_scene.gltf(filepath=str(out / "asset.glb"), export_format="GLB", export_apply=True)\n' +
            'with (out / "build_metrics.json").open("x", encoding="utf-8") as f: json.dump({"mesh_count":len(meshes),"polygon_count_authored":sum(len(o.data.polygons) for o in meshes),"objects":[o.name for o in meshes]},f)\n', encoding='utf-8')
        build = process([str(BLENDER), '--background', '--factory-startup', '--python', str(wrapper)], directory, 'build')
        if build['exit_code'] != 0 or not (directory / 'asset.glb').exists():
            return {'status': 'FAILED', 'outputs': [], 'observations': {'build': build, 'worker_invocation_ref': asdict(inference.invocation)}}
        return {'status': 'SUCCESS', 'outputs': [str(directory / 'asset.glb'), str(directory / 'asset.blend'), str(script), str(directory / 'build_metrics.json')],
            'observations': {'build': build, 'worker_invocation_ref': asdict(inference.invocation), 'notes': json.loads(generated['observations_json'])}}

    def diagnostics(artifact, number, parameters=None):
        data = artifact.validate(frozen, scope, session.run['workflow'], state=session.state())
        source = FileIdentity(**data['files'][0])
        directory = session.attempt['directory'] / ('diagnostics-%03d' % number)
        directory.mkdir()
        script = DIRECTORY / 'host/fresh_mesh_diagnostics.py'
        request_path = directory / 'request.json'
        request = {'source_glb': source.path, 'source_sha256': source.sha256,
            'output': str(directory / 'views'), 'manifest': str(directory / 'manifest.json'),
            'parameters': parameters or {}, 'state': session.state(),
            'workflow_ref': asdict(session.run['workflow']), 'source_artifact_ref': asdict(artifact)}
        write_once(request_path, request)
        observed = process([str(BLENDER), '--background', '--factory-startup', '--python', str(script), '--', str(request_path)], directory, 'render')
        if observed['exit_code'] != 0:
            raise ValueError('DIAGNOSTIC_EXECUTION_FAILED')
        manifest = file_identity(directory / 'manifest.json', 'fresh-glb-diagnostics')
        content = json.loads(Path(manifest.path).read_text(encoding='utf-8'))
        assert content['source_sha256'] == source.sha256
        images = tuple(file_identity(o['path'], o['view']) for o in content['outputs'])
        metric = file_identity(content['geometry_metrics'], 'imported-geometry-metrics')
        for item in images + (metric,): item.validate()
        write_once(directory / 'EVIDENCE_ARTIFACT_INDEX.json', {
            'artifact_id': session.state()['attempt_id'] + '-diagnostics-' + str(number), **session.state(),
            'producer': 'independent fresh-import Blender diagnostic host',
            'workflow_ref': asdict(session.run['workflow']), 'skill_refs': data['skill_refs'],
            'source_refs': [asdict(source), asdict(artifact.metadata), asdict(file_identity(script, 'diagnostic-host')), asdict(file_identity(request_path, 'diagnostic-request'))],
            'files': [asdict(i) for i in images + (metric, manifest)],
            'artifact_type': 'diagnostic-evidence', 'source_specification_ref': asdict(frozen.reference),
            'output_package_policy': 'Preserve every generated file under delivery/evidence with the same relative path and bytes'})
        session.logger.emit('production_runs/' + session.run['production_run_id'] + '/execution', 'FRESH_IMPORT_DIAGNOSTICS',
            state=session.state(), input_refs=(source,), output_refs=(manifest, metric) + images,
            reason_code='EXPORTED_GLB_INDEPENDENT_IMPORT')
        return images, manifest

    try:
        while True:
            decision, data = diagnose()
            current_decision = data
            action = data['selected_action']
            if data['new_skill_proposals_json'] and json.loads(data['new_skill_proposals_json']):
                session.checked_decision(decision, {'CONTINUE'})
                for proposal in json.loads(data['new_skill_proposals_json']):
                    assert set(proposal) == {'guidance', 'metadata'}
                    metadata = dict(proposal['metadata'])
                    assert metadata['status'] == 'CANDIDATE' and not metadata['validated_scenarios'] and metadata['last_validated'] is None
                    metadata['created_from_session'], metadata['created_from_production_run'] = SID, session.state()['production_run_id']
                    metadata['provenance'] = {'kind': 'FRONTIER_AUTHORED', 'decision_ref': asdict(decision)}
                    package = create_skill(registry.directory, metadata, {'SKILL.md': proposal['guidance'].encode('utf-8')})
                    relative = package.relative_to(ROOT).as_posix()
                    subprocess.run(['git', '-C', str(ROOT), '-c', 'core.autocrlf=false', 'add', '--', relative], check=True)
                    subprocess.run(['git', '-C', str(ROOT), '-c', 'core.autocrlf=false', 'commit', '-m',
                        'feat(skill): preserve frontier-authored candidate ' + metadata['skill_id']], check=True)
                    registry.vcs_revision = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD']).decode().strip()
                    created = registry.resolve(metadata['skill_id'], metadata['version'])
                    session.logger.emit('skills', 'USER_WORKFLOW_REVIEW_REQUESTED_NON_BLOCKING', input_refs=(decision,), output_refs=(created.metadata,),
                        identities={'skill_id': created.skill_id, 'skill_version': created.version}, reason_code='FRONTIER_AUTHORED_CANDIDATE_NO_REPLY_REQUIRED')
                    print(json.dumps({'event': 'SKILL_DISCLOSED_NON_BLOCKING', 'ref': asdict(created)}, ensure_ascii=True), flush=True)
                skills = registry.search()
                session.decisions_consumed.add(decision.sha256)
                continue
            if action == 'PLAN_WORKFLOW':
                session.start_run(workflow_from(data['selected_workflow_ref']), decision)
                continue
            if action == 'REVISE_WORKFLOW':
                session.revise_workflow(workflow_from(data['selected_workflow_ref']), decision)
                continue
            if action == 'RESTART_PRODUCTION_RUN':
                session.start_run(workflow_from(data['selected_workflow_ref']), decision)
                evidence_extra, images_extra, latest_artifact, latest_review, previous_code = (), (), None, None, None
                previous_source, previous_reviews = None, ()
                continue
            if action == 'STOP':
                session.stop('ABORT', data['reason_summary'])
                break
            if action == 'ACCEPT':
                session.accept(decision, latest_artifact, latest_review, initial_references=(reference,))
                deliver(session, skills, reference, worker_invocations)
                break
            if action == 'ACQUIRE_EVIDENCE':
                session.acquire_evidence(decision)
                images_extra, manifest = diagnostics(latest_artifact, count, json.loads(data['action_parameters_json'] or '{}'))
                reserved = session.resources.reserve('reviewer_calls', session.state())
                latest_review = ArtifactReviewer(ADAPTER).review(frozen, scope, session.run['workflow'], latest_artifact,
                    session.attempt['directory'] / ('review-evidence-%03d' % count), images=(reference,) + images_extra, supporting_refs=(manifest, file_identity(Path(manifest.path).parent / 'views/imported-geometry-metrics.json', 'imported-geometry-metrics')))
                session.register_review(latest_artifact, latest_review)
                continue
            if action not in ('CONTINUE', 'REVISE_ARTIFACT'):
                raise ValueError('UNSUPPORTED_ACTION')
            params = json.loads(data['action_parameters_json'] or '{}')
            correction = params.get('instruction')
            if session.attempt is None or session.attempt['finished']:
                previous_reviews = tuple(r.file for _, r in session.current_reviews.values())
                if len(list((session.run['directory'] / 'attempts').glob('attempt-*'))) >= 2:
                    raise ValueError('ENVELOPE_EXHAUSTED: per-Run Attempt limit')
                session.start_attempt(decision)
                latest_artifact, latest_review, evidence_extra = None, None, ()
            else:
                session.checked_decision(decision, {'CONTINUE'})
                session.checked_current_evidence(data)
                session.decisions_consumed.add(decision.sha256)
            workflow = session.run['workflow']
            configured = workflow.validate(frozen, scope)
            stage = next((s for s in configured['stages'] if s['stage_id'] not in session.current_reviews), None)
            if stage is None:
                raise ValueError('ALL_STAGES_REVIEWED_USE_ACCEPT_OR_REVISION')
            reservation = session.reserve_effect('worker_calls')
            # The correction instruction is a bound Decision input, not a
            # mutation of the immutable Workflow. Worker receives it separately.
            work_inputs = (reference, decision) + tuple(a.metadata for a, _ in session.current_reviews.values())
            output_dir = session.attempt['directory'] / ('execution-' + stage['stage_id'])
            outputs, execution = ExecutionAdapter({'blender-cli': runner}, mode='ACTUAL').execute(frozen, scope, workflow,
                session.state(), stage['stage_id'], work_inputs, reservation, output_dir, local_parameters=params.get('local_parameters', {}))
            session.logger.emit('production_runs/' + session.run['production_run_id'] + '/execution', 'EXECUTION_RESULT',
                state=session.state(), input_refs=work_inputs + (reservation,), output_refs=(execution,) + outputs)
            execution_data = json.loads(Path(execution.path).read_text(encoding='utf-8'))
            if execution_data['status'] != 'SUCCESS':
                session.finish_attempt(execution_data['status'], (execution,))
                evidence_extra = (execution,)
                if execution_data['status'] == 'UNRESOLVED':
                    session.stop('FAILED', 'UNRESOLVED_EXECUTION')
                    break
                continue
            latest_artifact = ArtifactStore(frozen, scope, workflow, session.state(), session.run['directory'] / 'artifacts', mode='ACTUAL').register(
                session.state()['attempt_id'] + '-' + stage['stage_id'], stage['stage_id'], outputs, work_inputs, execution)
            session.reserve_effect('diagnostic_calls')
            images_extra, manifest = diagnostics(latest_artifact, count)
            session.reserve_effect('reviewer_calls')
            latest_review = ArtifactReviewer(ADAPTER).review(frozen, scope, workflow, latest_artifact,
                session.attempt['directory'] / ('review-' + stage['stage_id']), images=(reference,) + images_extra,
                supporting_refs=(manifest, outputs[3], file_identity(Path(manifest.path).parent / 'views/imported-geometry-metrics.json', 'imported-geometry-metrics')))
            session.register_review(latest_artifact, latest_review)
            reviewed = latest_review.validate(frozen, scope, workflow, latest_artifact, state=session.state(), mode='ACTUAL')
            print(json.dumps({'review': reviewed['verdict'], 'criteria': json.loads(reviewed['criterion_results_json']), 'state': session.state()}, ensure_ascii=True), flush=True)
            if reviewed['verdict'] != 'PASS' or len(session.current_reviews) == len(configured['stages']):
                session.finish_attempt('REVIEWED', (latest_artifact.metadata, latest_review.file))
    except Exception as exc:
        if not session.boundary.outcome.terminal:
            if session.boundary.outcome.status == 'INTERNAL_ACCEPT':
                terminal = session.boundary.stop('FAILED', 'DELIVERY_FAILED: ' + str(exc))
                session.logger.emit('acceptance/delivery', 'SESSION_TERMINAL', output_refs=(terminal,), reason_code='DELIVERY_FAILED')
            else:
                session.stop('ABORT' if 'ENVELOPE_EXHAUSTED' in str(exc) else 'FAILED', str(exc))
        write_once(DIRECTORY / 'HOST_FAILURE.json', {'error_type': type(exc).__name__, 'message': str(exc), 'state': session.state(),
            'policy': 'Preserve terminal Session; no resume. Architecture defects require corrective checkpoint and wholly new fresh Session.'})
        print(json.dumps({'failure': str(exc), 'state': session.state()}, ensure_ascii=True), flush=True)
    events = reconstruct(session.directory / 'logs', SID)
    write_once(DIRECTORY / 'ACTUAL_RESULT.json', {'scope': 'ACTUAL', 'session_id': SID, 'status': session.boundary.outcome.status,
        'INTERNAL_ACCEPT': (session.directory / 'internal_accept.json').exists(), 'delivered': session.boundary.outcome.delivered,
        'event_count': len(events), 'resource_usage': session.resources.remaining(), 'skill_refs': [asdict(s) for s in skills],
        'known_limitations': ['One reference image; hidden geometry inferred', 'Exact account model identity may be unobservable',
            'Local export confirms files; human receipt/quality assessment is outside Session'], 'worker_invocation_refs': [asdict(r) for r in worker_invocations]})
    complete_output_snapshot(session)
    print(json.dumps({'status': session.boundary.outcome.status, 'events': len(events)}, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    prepare()
    run()
