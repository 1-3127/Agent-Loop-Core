"""Fresh Stone Lantern host using public adaptive contracts; no historical retry.

Run intake once, commit the reviewed Skill, then run once. A terminal namespace
cannot resume. All semantic planning/diagnosis/review/code authoring uses actual
saved-account model inference. Host code enforces invariants and selected tools.
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
import urllib.request
from datetime import datetime, timezone

ROOT = Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
WORK = Path(__file__).resolve().parent
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
from scenario_a import l7_blender_diagnostic as diagnostic
from session.session_boundary import AcceptanceCriterion, AuthorityReference, FinalizedFields, FileIdentity, file_identity, freeze_specification

DIRECTORY = ROOT / 'docs/adaptive/actual-stone-lantern-v1'
SID = 'actual-adaptive-stone-lantern-v1'
REQUEST = '\ub808\ud37c\ub7f0\uc2a4 \uc774\ubbf8\uc9c0\uc5d0 \uc788\ub294 \uc11d\ub4f1\uc744 \uc81c\uc791\ud558\ub77c. \uc11d\ub4f1\uc740 \uc911\uc559\uc758 \uc0ac\uac01\ud615 \uad6c\uba4d\uc744 \ud3ec\ud568\ud55c \uc2e4\ub8e8\uc5e3\uc774 \uba85\ud655\ud788 \ub098\uc640\uc57c \ud55c\ub2e4.'
ORIGINAL = ROOT / 'docs/session/fresh-session-refresh-proof-final-3/CURRENT_REFERENCE.png'
ORIGINAL_HASH = '9da5ed9e7f3490d058673122a7bd50b46635d4f0b5a36ca3199f0c1636cd17e5'
BLENDER = Path(r'D:\Blender_5.2\blender.exe')
CLI = r'C:\Users\Worker\AppData\Local\OpenAI\Codex\bin\c6fe824d725f02d7\codex.exe'
ADAPTER = CodexInferenceAdapter(WORK, timeout=900, executable=CLI)


def current_runtime_readiness():
    """Observe user-started ComfyUI; never start or classify it as a defect."""
    checks = []
    for suffix in ('system_stats', 'object_info'):
        url = 'http://127.0.0.1:8188/' + suffix
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                value = json.loads(response.read())
                checks.append({'url': url, 'status': response.status, 'json_response': True,
                    'node_count': len(value) if suffix == 'object_info' else None})
        except Exception as exc:
            checks.append({'url': url, 'json_response': False, 'error_type': type(exc).__name__})
    return {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'checks': checks,
        'ready': all(c['json_response'] for c in checks), 'scope': 'READ_ONLY_API_NOT_GENERATION_PROOF',
        'automatic_runtime_start': False, 'architecture_failure': False}


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


def intake():
    assert not DIRECTORY.exists(), 'FRESH_NAMESPACE_REQUIRED'
    readiness = current_runtime_readiness()
    if not readiness['ready']:
        print(json.dumps({'status': 'WAITING_FOR_USER_RUNTIME_DEPENDENCY: COMFYUI_NOT_RUNNING',
            'readiness': readiness}), flush=True)
        return
    assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() == ORIGINAL_HASH
    DIRECTORY.mkdir(parents=True)
    (DIRECTORY / 'host').mkdir()
    for name in ('actual_host.py', 'actual_extra_views.py'):
        shutil.copyfile(WORK / name, DIRECTORY / 'host' / name)
    write_once(DIRECTORY / 'HOST_SCRIPT_MANIFEST.json', {'files': [asdict(file_identity(DIRECTORY / 'host' / n, n))
        for n in ('actual_host.py', 'actual_extra_views.py')], 'policy': 'Immutable host source copies before fresh intake; never edit a bound Session source'})
    reference_path = DIRECTORY / 'CURRENT_REFERENCE.png'
    shutil.copyfile(ORIGINAL, reference_path)
    reference = file_identity(reference_path, 'current-reference')
    discovery = json.loads((WORK / 'discovery/report.json').read_text(encoding='utf-8'))
    discovery['historical_comfy_observation'] = discovery['comfy']
    discovery['comfy'] = readiness
    discovery['capabilities'].append({'id': 'comfy_existing_workflows', 'tool': 'comfy-api',
        'availability': 'CURRENT_READ_ONLY_API_OBSERVED_NOT_GENERATION_PROOF',
        'supported_boundary': 'Installed API observed; this fresh host binds a reviewed Blender geometry runner. '
            'Comfy model generation is optional and is not asserted from endpoint readiness.'})
    # Source/license/content review was performed before this import. Nothing
    # from the community package is executed or allowed to override authority.
    source = discovery['community_candidates'][0]
    source_files = {}
    prefix = 'plugins/blender-agent-studio/skills/blender-modeling-workflow/'
    for item in source['files']:
        content = Path(item['local_path']).read_bytes()
        assert hashlib.sha256(content).hexdigest() == item['sha256']
        name = item['source_path'][len(prefix):] if item['source_path'].startswith(prefix) else item['source_path']
        source_files[name] = content
    review = {'source_url': source['source_url'], 'source_revision': source['source_revision'],
        'source_files': {n: hashlib.sha256(b).hexdigest() for n, b in source_files.items()}, 'license': 'MIT',
        'copy_allowed': True, 'content_reviewed': True,
        'review_summary': 'Reviewed all eight files, MIT notice, portable frontmatter and referenced guidance. '
            'No executable script included. No external command executed. Optional MCP/benchmark helpers are unavailable; '
            'use installed headless Blender counterpart. Source model names are guidance and do not select the runtime. '
            'User-adopted frozen specification and no-resume boundaries override community examples.'}
    write_once(DIRECTORY / 'COMMUNITY_REVIEW.json', review)
    write_once(DIRECTORY / 'DISCOVERY.json', discovery)
    authority = [{'reference_id': 'request', 'source_ref': REQUEST},
        {'reference_id': 'current-reference', 'source_ref': canonical_bytes(asdict(reference)).decode()}]
    names = ['specification_markdown', 'finalized_fields_json', 'criterion_applicability_json', 'resource_limits_json',
        'deliverable_type', 'reference_observations', 'skill_selection_json']
    schema = {'type': 'object', 'additionalProperties': False, 'required': ['ready', 'unresolved_question', 'deadline_seconds'] + names,
        'properties': {'ready': {'type': 'boolean'}, 'unresolved_question': {'type': ['string', 'null']},
            'deadline_seconds': {'type': ['integer', 'null']}, **{n: {'type': 'string'} for n in names}}}
    context = {'role': 'SPECIFICATION_DIALOGUE_FRONTIER', 'original_request': REQUEST,
        'current_reference': asdict(reference), 'session_id': SID, 'authority_references': authority,
        'installed_capabilities': discovery['capabilities'], 'comfy_availability': discovery['comfy'],
        'community_review': review, 'available_reusable_skill': {'skill_id': 'blender-modeling-workflow', 'version': 'v1',
            'description': 'Reviewed community portable guidance for reference-driven headless bpy modeling and GLB fresh-import review.'},
        'instructions': 'Infer a fresh Work Specification only from the original request and supplied image. No old specification, '
            'criteria, generated views, GLB or Reviews were supplied. Separate observed reference features from inferred hidden sides. '
            'Routine dimensions/style/evidence/budget are your responsibility. Ask a concise natural-language unresolved_question only '
            'if a consequential competing intent cannot be resolved; then ready=false. Do not ask generic purpose confirmation. '
            'FinalizedFields JSON must exactly contain session_id, specification_version:v1, request_type:NEW_WORK, specification_ready:true, '
            'unresolved_blocking_ambiguities:[], acceptance_criteria:[{criterion_id,authority_ref,blocking_when_unmet,description}], '
            'authority_references exactly the supplied two records, interpretation_envelope:[strings]. '
            'Choose an inspectable geometry deliverable and map every mandatory criterion to appropriate artifact type(s). '
            'The installed headless Blender execution boundary can author meshes from reference, export GLB and blend, and fresh-import/render independent evidence. '
            'Comfy API currently responds, as shown in the readiness observation. Do not infer generation/model readiness from that alone or acquire models. '
            'The reviewed execution runner currently bound to this host is headless Blender geometry. Select a strategy that actually satisfies the original target '
            'and square opening; API readiness is runtime context, not user-task authority or a reason to change the frozen criteria. '
            'Use meaningful bounded resources, not a development-chat deadline. '
            'resource_limits_json has positive integer production_runs, attempts, worker_calls, reviewer_calls, frontier_calls, diagnostic_calls; '
            'worker_calls means one logical code-authoring plus Blender build operation. Independent fresh-import diagnostics consume diagnostic_calls. '
            'criterion_applicability_json maps artifact type to criterion IDs; deliverable_type must be included. '
            'skill_selection_json is {reuse:[skill_id], new_skills:[]}; prefer reviewed reusable community knowledge. '
            'If that capability cannot satisfy the request, explain an actual limitation rather than weaken criteria.'}
    write_once(DIRECTORY / 'intake/request.json', context)
    invocation = ADAPTER(file_identity(DIRECTORY / 'intake/request.json', 'specification-intake'), schema,
        DIRECTORY / 'intake/invocation', (reference,))
    result = json.loads(Path(invocation.result.path).read_text(encoding='utf-8'))
    if not result['ready'] or result['unresolved_question']:
        write_once(DIRECTORY / 'DIALOGUE_PENDING.json', result)
        print(json.dumps({'state': 'DIALOGUE_PENDING', 'question': result['unresolved_question']}, ensure_ascii=True), flush=True)
        return
    fields = fields_from(json.loads(result['finalized_fields_json']))
    assert asdict(fields)['authority_references'] == tuple(authority)
    assert fields.session_id == SID and fields.specification_ready and not fields.unresolved_blocking_ambiguities
    mapping, limits = json.loads(result['criterion_applicability_json']), json.loads(result['resource_limits_json'])
    selection = json.loads(result['skill_selection_json'])
    assert selection == {'reuse': ['blender-modeling-workflow'], 'new_skills': []}, 'UNSUPPORTED_INTAKE_SELECTION_REQUIRES_EXPLICIT_IMPLEMENTATION'
    spec = DIRECTORY / 'SPECIFICATION.md'
    spec.write_bytes((result['specification_markdown'] + '\n\nFresh finalized authority fields:\n' + canonical_bytes(asdict(fields)).decode() + '\n\n' +
        canonical_bytes({'criterion_applicability': mapping, 'deliverable_type': result['deliverable_type']}).decode() + '\n' +
        canonical_bytes({'resource_limits': limits, 'deadline_seconds': result['deadline_seconds']}).decode() + '\n').encode('utf-8'))
    frozen = freeze_specification(spec, fields)
    write_once(DIRECTORY / 'frozen.json', asdict(frozen))
    scope = freeze_workflow_scope(frozen, DIRECTORY / 'scope.json', mapping, result['deliverable_type'])
    write_once(DIRECTORY / 'INTAKE_RESULT.json', {'status': 'READY', 'original_request': REQUEST, 'reference_ref': asdict(reference),
        'specification': asdict(frozen), 'scope_ref': asdict(scope), 'intake_invocation_ref': asdict(invocation.invocation),
        'reference_observations': result['reference_observations'], 'resource_limits': limits, 'deadline_seconds': result['deadline_seconds']})
    metadata = {'skill_id': 'blender-modeling-workflow', 'version': 'v1', 'content_hash': '', 'status': 'CANDIDATE',
        'provenance': {'kind': 'REVIEWED_COPY'}, 'community_sources': [], 'input_artifact_types': ['reference', result['deliverable_type']],
        'output_artifact_types': [result['deliverable_type']], 'required_capabilities': ['blender_geometry'], 'candidate_tools': ['blender-cli'],
        'candidate_models': [], 'callable_skills': [], 'review_gates': ['independent artifact criterion review', 'fresh GLB import and diagnostic views'],
        'known_failure_modes': ['single image hidden-side uncertainty', 'unsupported optional community MCP helpers', 'geometry mismatch despite successful export'],
        'restart_conditions': ['Frontier evidence-bound strategy revision and explicit new Run'], 'created_from_session': SID,
        'created_from_production_run': None, 'validated_scenarios': [], 'last_validated': None, 'files': {}}
    # Resolve the VCS pin only after the package has been committed.
    registry = SkillRegistry(ROOT / 'skills', '1' * 40)
    package = registry.import_reviewed_copy(metadata, source_files, file_identity(DIRECTORY / 'COMMUNITY_REVIEW.json', 'community-review'))
    print(json.dumps({'status': 'READY', 'session_id': SID, 'specification': str(spec), 'skill_path': str(package),
        'skill_hash': json.loads((package / 'core.json').read_text())['content_hash'], 'limits': limits,
        'observations': result['reference_observations']}, ensure_ascii=True), flush=True)


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
    if not readiness['ready']:
        print(json.dumps({'status': 'WAITING_FOR_USER_RUNTIME_DEPENDENCY: COMFYUI_NOT_RUNNING',
            'readiness': readiness}), flush=True)
        return
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
                        'Each stage produces an inspectable geometry artifact. The host supplies fresh-import diagnostics and an independent Review. '
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
            'previous_code': previous_code, 'previous_source_ref': asdict(previous_source) if previous_source else None,
            'prior_review_refs': [asdict(r) for r in previous_reviews],
            'prior_reviews_for_explicit_local_correction': [json.loads(Path(r.path).read_text(encoding='utf-8')) for r in previous_reviews],
            'frontier_decision': current_decision,
            'instructions': 'Return code with imports limited to bpy, math, mathutils, random and a build_asset() function. '
                'Construct the reference subject according to the selected immutable Workflow stage parameters and current correction instruction. '
                'Do not read or write files, export/save, load images, contact network, execute processes, use eval/exec/open, or change criteria. '
                'The host starts a clean Blender 5.2 scene and owns export, saving and diagnostics. You may remove your temporary cutters. '
                'Produce named meshes with genuine requested negative space, connected/consistent structure, stone material and faithful proportions. '
                'Use actual supported bpy APIs. Apply needed geometry modifiers or leave them for host GLB export with export_apply. '
                'Reference image contains occluding background/foreground objects; interpret the target from the original frozen specification. '
                'No camera or light is needed. Return observations_json as concise factual construction notes, not semantic acceptance.'}
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
        request_path = directory / 'request.json'
        request = {'config': diagnostic.CONFIG, 'script': {'sha256': hashlib.sha256(Path(diagnostic.__file__).read_bytes()).hexdigest()},
            'source_glb': asdict(source), 'output_dir': str(directory / 'views'), 'manifest_path': str(directory / 'manifest.json'),
            'blender_version': '5.2.0 LTS', 'run_id': session.state()['production_run_id'], 'source_l6_run_id': 'ADAPTIVE_NOT_LEGACY_L6'}
        write_once(request_path, request)
        observed = process([str(BLENDER), '--background', '--factory-startup', '--python', diagnostic.__file__, '--', '--request', str(request_path)], directory, 'render')
        if observed['exit_code'] != 0:
            raise ValueError('DIAGNOSTIC_EXECUTION_FAILED')
        manifest = file_identity(directory / 'manifest.json', 'fresh-glb-diagnostics')
        content = json.loads(Path(manifest.path).read_text(encoding='utf-8'))
        if content['source_glb']['sha256'] != source.sha256:
            raise ValueError('DIAGNOSTIC_SOURCE_MISMATCH')
        images = tuple(file_identity(o['path'], o['role']) for o in content['outputs'])
        for image in images:
            image.validate()
        session.logger.emit('production_runs/' + session.run['production_run_id'] + '/execution', 'FRESH_IMPORT_DIAGNOSTICS',
            state=session.state(), input_refs=(source,), output_refs=(manifest,) + images, reason_code='EXPORTED_GLB_INDEPENDENT_IMPORT')
        extra_script = DIRECTORY / 'host/actual_extra_views.py'
        extra_request = directory / 'extra-request.json'
        write_once(extra_request, {'source_glb': source.path, 'output': str(directory / 'extra-views'),
            'manifest': str(directory / 'extra-manifest.json'), 'parameters': parameters or {}})
        extra = process([str(BLENDER), '--background', '--factory-startup', '--python', str(extra_script), '--', str(extra_request)], directory, 'extra-render')
        if extra['exit_code'] != 0:
            raise ValueError('EXTRA_DIAGNOSTIC_EXECUTION_FAILED')
        extra_manifest = file_identity(directory / 'extra-manifest.json', 'fresh-material-evidence')
        content = json.loads(Path(extra_manifest.path).read_text(encoding='utf-8'))
        extra_images = tuple(file_identity(o['path'], o['view']) for o in content['outputs'])
        session.logger.emit('production_runs/' + session.run['production_run_id'] + '/execution', 'MATERIAL_AND_REQUESTED_EVIDENCE',
            state=session.state(), input_refs=(source, file_identity(extra_script, 'extra-diagnostic-script'), file_identity(extra_request, 'extra-diagnostic-request')),
            output_refs=(extra_manifest,) + extra_images, reason_code='INDEPENDENT_GLTF_IMPORT')
        images += extra_images
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
                    session.attempt['directory'] / ('review-evidence-%03d' % count), images=(reference,) + images_extra, supporting_refs=(manifest,))
                session.register_review(latest_artifact, latest_review)
                continue
            if action not in ('CONTINUE', 'REVISE_ARTIFACT'):
                raise ValueError('UNSUPPORTED_ACTION')
            params = json.loads(data['action_parameters_json'] or '{}')
            correction = params.get('instruction')
            if session.attempt is None or session.attempt['finished']:
                previous_reviews = tuple(r.file for _, r in session.current_reviews.values())
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
                supporting_refs=(manifest, outputs[3]))
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
    print(json.dumps({'status': session.boundary.outcome.status, 'events': len(events)}, ensure_ascii=True), flush=True)


def deliver(session, skills, reference, worker_invocations):
    package = session.boundary.prepare_delivery()
    data = json.loads(Path(package.path).read_text(encoding='utf-8'))
    destination = WORK.parent / 'outputs' / SID
    assert not destination.exists(), 'DELIVERY_NAMESPACE_COLLISION'
    destination.mkdir(parents=True)
    source = FileIdentity(**data['artifact'])
    exported = destination / 'stone-lantern.glb'
    assert not exported.exists()
    shutil.copyfile(source.path, exported)
    ref_export = destination / 'original-reference.png'
    assert not ref_export.exists()
    shutil.copyfile(reference.path, ref_export)
    for file in Path(source.path).parent.iterdir():
        if file.name in ('asset.blend', 'asset_source.py'):
            shutil.copyfile(file, destination / file.name)
    for item in session.current_reviews.values():
        review_data = json.loads(Path(item[1].file.path).read_text(encoding='utf-8'))
        review_request = json.loads(Path(review_data['request_ref']['path']).read_text(encoding='utf-8'))
        for image_data in review_request['image_refs'][1:]:
            image = FileIdentity(**image_data)
            shutil.copyfile(image.path, destination / Path(image.path).name)
    record_path = DIRECTORY / 'handoff.json'
    write_once(record_path, {'session_id': SID, 'delivery_package': asdict(package), 'boundary': 'LOCAL_DELIVERABLE_EXPORT',
        'delivered_artifact': asdict(file_identity(exported, 'delivered-stone-lantern')),
        'delivered_references': [asdict(file_identity(ref_export, 'delivered-original-reference'))],
        'observation_scope': 'LOCAL_FILES_VERIFIED_HUMAN_RECEIPT_NOT_OBSERVED'})
    terminal = session.boundary.record_local_handoff(package, file_identity(record_path, 'actual-handoff'))
    session.logger.emit('acceptance/delivery', 'LOCAL_HANDOFF_CLOSED', output_refs=(terminal,), reason_code='LOCAL_DELIVERABLE_FILES_VERIFIED')
    frontier_invocations = [FileIdentity(**json.loads(p.read_text(encoding='utf-8'))['frontier_invocation_ref'])
        for p in (DIRECTORY / 'decisions').glob('*/decision.json')]
    success = DIRECTORY / 'ACTUAL_SUCCESS.json'
    used = session.run['workflow'].validate(session.frozen, session.scope)['skill_refs']
    write_once(success, {'scope': 'ACTUAL', 'INTERNAL_ACCEPT': True, 'session_terminal': 'CLOSED', 'session_id': SID,
        'production_run_id': session.state()['production_run_id'], 'skill_refs': used,
        'review_refs': [asdict(r.file) for _, r in session.current_reviews.values()],
        'frontier_invocation_refs': [asdict(r) for r in frontier_invocations],
        'known_limitations': ['Validated for this one original-reference task, not arbitrary subjects; hidden surfaces inferred'],
        'terminal_ref': asdict(terminal), 'acceptance_gate_ref': asdict(file_identity(session.directory / 'acceptance_gate.json', 'acceptance-gate'))})
    for skill in skills:
        if asdict(skill) not in used:
            continue
        record_validation(skill, file_identity(success, 'actual-success'), DIRECTORY / ('skill-validation-' + skill.skill_id + '.json'))


if __name__ == '__main__':
    {'intake': intake, 'run': run}[sys.argv[1]]()
