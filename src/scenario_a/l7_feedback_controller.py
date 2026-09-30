"""Scenario A L7: one structured correction and re-review; default is effect-free."""
import argparse
import copy
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import struct
import time

from scenario_a import l6_pipeline as l6
from scenario_a import l7_geometry_review as bridge
from scenario_a import l7_blender_diagnostic as diagnostic

ROOT = l6.ROOT
SOURCE_DIR = ROOT / 'runs/l7/l7-m1-20260930-184618-3703fee4'
SOURCE_TERMINAL_SHA = '24c2dfe9fca91a016a7a7ada4d3c3a68c7d27952b1c8bfa8832c79aa88cd433b'
LIMITS = {'revision': 1, 'worker': 2, 'reviewer': 2, 'renderer': 1}
COMPONENT = {'revision': 'revision', 'view': 'worker', 'geometry': 'worker',
             'multiview_review': 'reviewer', 'geometry_review': 'reviewer', 'renderer': 'renderer'}
read, ref, write_once = l6.read_json, l6.reference, l6.write_once


def next_seed(seed):
    if type(seed) is not int or not 0 <= seed < 2**64 - 1:
        raise l6.StageFailure('FAILED', 'REVISION_POLICY')
    return seed + 1


def resolve_action(result):
    try: bridge.validate_action(result)
    except (ValueError, KeyError, TypeError) as exc:
        raise l6.StageFailure('FAILED', 'REVISION_POLICY') from exc
    return result['suggested_action'] if result['verdict'] == 'REVISE' else None


def validate_source(source_dir):
    source_dir = Path(source_dir).resolve()
    terminal = read(source_dir / 'terminal.json')
    if source_dir == SOURCE_DIR.resolve() and l6.digest(source_dir / 'terminal.json') != SOURCE_TERMINAL_SHA:
        raise ValueError('source terminal hash differs')
    if (terminal['run_id'] != source_dir.name or terminal['state'] != 'GEOMETRY_REVIEWED'
            or terminal['terminal'] is not True or terminal['dispatches'] != 0):
        raise ValueError('source terminal/run differs')
    required = {'initial', 'render_request', 'renderer_reservation', 'renderer_invocation', 'render_manifest',
                'review_request', 'reviewer_reservation', 'review_result', 'review_invocation', 'usage', 'review_instructions'}
    if set(terminal['records']) != required or read(source_dir / 'initial.json')['run_id'] != source_dir.name:
        raise ValueError('source evidence set/run differs')
    for name, item in terminal['records'].items():
        expected = source_dir / (name + ('.md' if name == 'review_instructions' else '.json'))
        if item != ref(expected):
            raise ValueError('source record path/hash differs: ' + name)
        l6.reviewer.checked_ref(item)
    # Schema and evidence identity precede executable-action policy.
    raw_result = l6.reviewer.validate_result(read(source_dir / 'review_result.json'), read(source_dir / 'review_request.json'))
    resolve_action(raw_result)
    result = bridge.checked_review(source_dir)
    inputs = bridge.validate_l6()
    if (terminal['l6_input'] != inputs or terminal['review_verdict'] != result['verdict']
            or terminal['initial_contract'] != ref(source_dir / 'initial.json')):
        raise ValueError('source geometry/review linkage differs')
    geometry = read(inputs['geometry_plan']['path'])
    views = {role: ref(Path(image['execution_report']['path']).parent / (role + '_plan.json'))
             for role, image in zip(l6.VIEWS, inputs['references'][1:])}
    return {'run_id': source_dir.name, 'terminal': ref(source_dir / 'terminal.json'),
            'result': ref(source_dir / 'review_result.json'),
            'invocation': ref(source_dir / 'review_invocation.json'),
            'request': ref(source_dir / 'review_request.json'),
            'render_manifest': ref(source_dir / 'render_manifest.json'),
            'instructions': ref(source_dir / 'review_instructions.md'),
            'input': inputs, 'verdict': result['verdict'], 'action': resolve_action(result),
            'previous_geometry_seed': geometry['patches']['14']['seed'], 'view_plans': views}


def preflight(source_review_run=SOURCE_DIR, comfy_root=l6.worker.DEFAULT_COMFY_ROOT, blender_executable=bridge.BLENDER):
    source = validate_source(source_review_run)
    assets = l6.preflight(comfy_root)
    prior = l6.read_ref(source['input']['geometry_plan'])
    if prior != l6.make_plan(source['input']['source_run_id'], 'geometry', assets, staged=True):
        raise ValueError('prior geometry plan differs from verified contract')
    for role, item in source['view_plans'].items():
        if l6.read_ref(item) != l6.make_plan(source['input']['source_run_id'], role, assets):
            raise ValueError('prior view plan differs from verified contract')
    action = source['action']
    seed = source['previous_geometry_seed']
    predicted = next_seed(seed) if action else None
    target_seed = None
    if action and action['code'] == 'REGENERATE_VIEW':
        target_seed = next_seed(l6.read_ref(source['view_plans'][action['target']])['patches']['11']['seed'])
    return {'status': 'PREFLIGHT_PASS', 'source': source, 'asset_manifest': ref(l6.ASSET_MANIFEST),
            'renderer': bridge.blender_identity(blender_executable), 'script': ref(bridge.SCRIPT),
            'action': action, 'revision_seed': predicted, 'view_revision_seed': target_seed,
            'limits': LIMITS, 'effects': {'comfy': 0, 'blender': 0, 'frontier': 0}}


def budgets(run_dir):
    return {kind: {'limit': limit, 'consumed': sum((run_dir / (stage + '_reservation.json')).exists()
                for stage, component in COMPONENT.items() if component == kind),
                'remaining': limit - sum((run_dir / (stage + '_reservation.json')).exists()
                for stage, component in COMPONENT.items() if component == kind)} for kind, limit in LIMITS.items()}


def guard(run_dir, *, check_source=True):
    if (run_dir / 'terminal.json').exists():
        raise ValueError('ALREADY_TERMINAL')
    state = read(run_dir / 'state.json')
    initial = l6.read_ref(state['initial_contract'])
    if state['terminal'] or state['state'] == 'UNRESOLVED':
        raise ValueError('ALREADY_TERMINAL or UNRESOLVED')
    if initial['run_id'] != run_dir.name or initial['terminal'] is not False or initial['limits'] != LIMITS:
        raise ValueError('initial run/budget differs')
    # Full source proof is validated at preflight. Check its frozen hashes here
    # without recursively replaying the historical PNG/Review validators.
    source = initial['source']
    if not check_source:
        return initial
    for name in ('terminal', 'result', 'invocation', 'request', 'render_manifest', 'instructions'):
        l6.reviewer.checked_ref(source[name])
    for name in ('geometry_execution', 'geometry_plan', 'geometry_worker_report', 'multiview_manifest', 'terminal', 'artifact'):
        l6.reviewer.checked_ref({k: source['input'][name][k] for k in ('path', 'sha256')})
    if (run_dir / 'revision_action.json').exists():
        action = read(run_dir / 'revision_action.json')
        target = initial['action']['target']
        prior_seed = source['previous_geometry_seed'] if target == 'geometry' else l6.read_ref(source['view_plans'][target])['patches']['11']['seed']
        if (action['run_id'] != run_dir.name or action['action_code'] != initial['action']['code'] or action['target'] != target
                or action['source_review'] != source['result'] or action['source_verdict'] != 'REVISE'
                or action['revision_ordinal'] != 1 or action['previous_seed'] != prior_seed
                or action['revision_seed'] != next_seed(prior_seed)):
            raise ValueError('revision action identity/seed differs')
    for b in budgets(run_dir).values():
        if b['remaining'] < 0: raise ValueError('budget exceeded')
    return initial


def update(run_dir, state):
    guard(run_dir)
    current = read(run_dir / 'state.json')
    l6.worker.write_report(run_dir / 'state.json', current | {'state': state, 'budgets': budgets(run_dir)})


def stage_path(run_dir, stage):
    if stage == 'revision': return run_dir / 'revision_action.json'
    if stage == 'renderer': return run_dir / 'render_request.json'
    if stage.endswith('_review'): return run_dir / (stage + '_request.json')
    role = read(run_dir / 'revision_action.json')['target'] if stage == 'view' else 'geometry'
    return run_dir / (role + '_work_order.json')


def reserve(run_dir, stage, source_path):
    initial = guard(run_dir)
    if stage not in COMPONENT: raise ValueError('unknown stage')
    if Path(source_path) != stage_path(run_dir, stage): raise ValueError('alternate reservation path forbidden')
    if stage in ('view', 'multiview_review') and initial['action']['code'] != 'REGENERATE_VIEW':
        raise ValueError('geometry action cannot use view stages')
    if stage != 'revision' and not (run_dir / 'revision_reservation.json').exists():
        raise ValueError('revision action not reserved')
    path = run_dir / (stage + '_reservation.json')
    if path.exists() or budgets(run_dir)[COMPONENT[stage]]['remaining'] < 1:
        raise ValueError('STAGE_ALREADY_RESERVED or BUDGET_EXHAUSTED')
    write_once(path, {'run_id': run_dir.name, 'stage': stage, 'source': ref(source_path),
                     'created_at': l6.now(), 'initial_contract': ref(run_dir / 'initial.json')})
    update(run_dir, read(run_dir / 'state.json')['state'])


def current_images(run_dir):
    initial = guard(run_dir)
    manifest = read(run_dir / 'multiview_manifest.json')
    images = manifest['references']
    if (manifest['run_id'] != run_dir.name or manifest['source_manifest'] != initial['source']['input']['multiview_manifest']
            or manifest['revision_action'] != ref(run_dir / 'revision_action.json')
            or len(images) != 4 or [i['role'] for i in images] != list(l6.ROLES)):
        raise ValueError('current manifest lineage differs')
    action = initial['action']
    for image, prior in zip(images, initial['source']['input']['references']):
        l6.checked_image(image)
        if action['code'] == 'REGENERATE_VIEW' and image['role'] == action['target']:
            execution = l6.read_ref(image['execution_report'])
            order = l6.read_ref(execution['work_order'])
            report = l6.read_ref(execution['worker_report'])
            l6.validate_worker_report(order, report)
            if (execution['run_id'] != run_dir.name or execution['stage'] != image['role']
                    or execution['artifact'] != {k: v for k, v in image.items() if k != 'execution_report'}
                    or execution['prompt_id'] != report['prompt_id']):
                raise ValueError('revised target execution differs')
        elif image != prior:
            raise ValueError('unchanged reference differs')
    return images


def approved_images(run_dir):
    images = current_images(run_dir)
    initial = read(run_dir / 'initial.json')
    if initial['action']['code'] == 'REGENERATE_VIEW' and checked_review(run_dir, 'multiview')['verdict'] != 'PASS':
        raise ValueError('Geometry requires current multiview PASS')
    return images


def stage_bytes(run_dir):
    images = approved_images(run_dir)
    root = Path(read(run_dir / 'initial.json')['comfy_root'])
    destination = root / 'work/input/l7' / run_dir.name
    destination.parent.mkdir(parents=True, exist_ok=True); destination.mkdir()
    staged = []
    for image in images[1:]:
        data = Path(image['path']).read_bytes()
        if hashlib.sha256(data).hexdigest() != image['sha256'] or len(data) != image['bytes']:
            raise ValueError('reference changed before staging')
        path = destination / (image['role'] + '.png')
        with path.open('xb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        staged.append({'original': image, 'staged': l6.png_identity(path, image['role'])})
    write_once(run_dir / 'staging.json', {'run_id': run_dir.name, 'manifest': ref(run_dir / 'multiview_manifest.json'), 'views': staged})
    validate_staging(run_dir)


def validate_staging(run_dir):
    images = approved_images(run_dir)
    staging = read(run_dir / 'staging.json'); initial = read(run_dir / 'initial.json')
    if staging['run_id'] != run_dir.name or staging['manifest'] != ref(run_dir / 'multiview_manifest.json') or len(staging['views']) != 3:
        raise ValueError('staging lineage differs')
    for image, item in zip(images[1:], staging['views']):
        l6.checked_image(item['staged'])
        if (item['original'] != image or Path(item['staged']['path']) != Path(initial['comfy_root']) / 'work/input/l7' / run_dir.name / (image['role'] + '.png')
                or any(item['staged'][k] != image[k] for k in ('role', 'sha256', 'bytes', 'width', 'height'))):
            raise ValueError('staging bytes/mapping differs')
    return images


def revised_plan(run_dir, role):
    initial = guard(run_dir); source = initial['source']; action = initial['action']
    if role != 'geometry' and (action['code'] != 'REGENERATE_VIEW' or role != action['target']):
        raise ValueError('only selected target allowed')
    prior = source['input']['geometry_plan'] if role == 'geometry' else source['view_plans'][role]
    plan = copy.deepcopy(l6.read_ref(prior))
    seed_node, output = ('14', '17') if role == 'geometry' else ('11', '13')
    plan['task_id'] = run_dir.name + '-' + role
    plan['patches'][seed_node]['seed'] = next_seed(plan['patches'][seed_node]['seed'])
    plan['patches'][output]['filename_prefix'] = ('mesh/' if role == 'geometry' else '') + f'l7/{run_dir.name}/{role}'
    if role == 'geometry':
        validate_staging(run_dir)
        for name, node in l6.MAPPING.items():
            plan['patches'][node]['image'] = 'hunyuan-official-demo-padded.png' if name == 'front' else f'l7/{run_dir.name}/{name}.png'
    return plan


def publish_order(run_dir, role):
    initial = guard(run_dir); assets = l6.read_ref(initial['asset_manifest'])
    model = assets['geometry'] if role == 'geometry' else assets['view_generation'][role]
    inputs = {'source': initial['source']['input']['references'][0]}
    if role == 'geometry':
        inputs = {'artifacts': validate_staging(run_dir), 'staging': ref(run_dir / 'staging.json'),
                  'multiview': ref(run_dir / 'multiview_manifest.json'),
                  'approved_review': ref(run_dir / 'multiview_review_result.json') if initial['action']['code'] == 'REGENERATE_VIEW'
                                     else ref(bridge.L6_DIR / 'review_result.json')}
    write_once(run_dir / (role + '_plan.json'), revised_plan(run_dir, role))
    prior_plan = initial['source']['input']['geometry_plan'] if role == 'geometry' else initial['source']['view_plans'][role]
    seed_node = '14' if role == 'geometry' else '11'
    order = {'version': 'l7-feedback.0', 'run_id': run_dir.name, 'work_order_id': run_dir.name + '-' + role,
             'stage': role, 'iteration': 1, 'worker_type': 'ComfyUI', 'adapter': 'src/scenario_a/codex_to_comfy.py',
             'requested_task': 'Apply one seed-only correction for ' + role,
             'expected_output_kind': 'geometry' if role == 'geometry' else 'image',
             'workflow': {'path': model['workflow'], 'sha256': model['sha256']},
             'plan': ref(run_dir / (role + '_plan.json')), 'inputs': inputs,
             'initial_contract': ref(run_dir / 'initial.json'), 'source_review': initial['source']['result'],
             'revision_action': ref(run_dir / 'revision_action.json'), 'previous_plan': prior_plan,
             'previous_seed': l6.read_ref(prior_plan)['patches'][seed_node]['seed'],
             'revision_seed': read(run_dir / (role + '_plan.json'))['patches'][seed_node]['seed'],
             'previous_execution': initial['source']['input']['geometry_execution'] if role == 'geometry'
                                   else initial['source']['input']['references'][l6.ROLES.index(role)]['execution_report'],
             'worker_report_path': str(run_dir / (role + '_worker_report.json')),
             'execution_report_path': str(run_dir / (role + '_execution.json'))}
    write_once(run_dir / (role + '_work_order.json'), order)
    return run_dir / (role + '_work_order.json')


def run_worker(run_dir, role, timeout):
    initial = guard(run_dir); stage = 'geometry' if role == 'geometry' else 'view'
    path = run_dir / (role + '_work_order.json'); order = read(path)
    plan = l6.read_ref(order['plan']); l6.reviewer.checked_ref(order['workflow'])
    expected = revised_plan(run_dir, role)
    if (plan != expected or order['run_id'] != run_dir.name or order['work_order_id'] != expected['task_id']
            or order['initial_contract'] != ref(run_dir / 'initial.json')
            or order['revision_action'] != ref(run_dir / 'revision_action.json')
            or order['source_review'] != initial['source']['result']):
        raise ValueError('Worker order/plan lineage differs')
    root = Path(initial['comfy_root']); assets = l6.preflight(root); l6.worker.validate_plan(plan, root)
    model = assets['geometry'] if role == 'geometry' else assets['view_generation'][role]
    expected_inputs = {'source': initial['source']['input']['references'][0]}
    if role == 'geometry':
        expected_inputs = {'artifacts': validate_staging(run_dir), 'staging': ref(run_dir / 'staging.json'),
                           'multiview': ref(run_dir / 'multiview_manifest.json'),
                           'approved_review': ref(run_dir / 'multiview_review_result.json') if initial['action']['code'] == 'REGENERATE_VIEW'
                                              else ref(bridge.L6_DIR / 'review_result.json')}
    prior_plan = initial['source']['input']['geometry_plan'] if role == 'geometry' else initial['source']['view_plans'][role]
    prior_execution = initial['source']['input']['geometry_execution'] if role == 'geometry' else initial['source']['input']['references'][l6.ROLES.index(role)]['execution_report']
    seed_node = '14' if role == 'geometry' else '11'
    if (order['stage'] != role or order['iteration'] != 1 or order['inputs'] != expected_inputs
            or order['workflow'] != {'path': model['workflow'], 'sha256': model['sha256']}
            or order['previous_plan'] != prior_plan or order['previous_execution'] != prior_execution
            or order['previous_seed'] != l6.read_ref(prior_plan)['patches'][seed_node]['seed']
            or order['revision_seed'] != plan['patches'][seed_node]['seed']):
        raise ValueError('Worker input/prior lineage differs')
    report_path, execution_path = [run_dir / (role + suffix) for suffix in ('_worker_report.json', '_execution.json')]
    if order['worker_report_path'] != str(report_path) or order['execution_report_path'] != str(execution_path) or report_path.exists() or execution_path.exists():
        raise ValueError('alternate or existing Worker records forbidden')
    prefix = expected['patches']['17' if role == 'geometry' else '13']['filename_prefix']
    output_prefix = l6.worker.within(root / 'work/output', l6.worker.safe_relative(prefix, 'prefix'))
    if any(output_prefix.parent.glob(output_prefix.name + '_*')): raise ValueError('artifact namespace exists')
    reserve(run_dir, stage, path)
    try:
        l6.worker.run(run_dir / (role + '_plan.json'), report_path, root, timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise l6.StageFailure('UNRESOLVED', 'REVISION_WORKER_STAGE') from exc
    report = read(report_path)
    try: output = l6.validate_worker_report(order, report)
    except l6.StageFailure as exc:
        l6.record_execution(path, report, None, exc.state, report.get('errors', []))
        raise l6.StageFailure(exc.state, 'REVISION_WORKER_STAGE') from exc
    artifact_path = Path(output['path']).resolve()
    if not Path(output['path']).is_absolute() or artifact_path.parent != output_prefix.parent or not artifact_path.name.startswith(output_prefix.name + '_'):
        raise ValueError('fresh artifact namespace differs')
    if role == 'geometry':
        history = {'outputs': {'17': {'3d': [{'filename': artifact_path.name,
                   'subfolder': artifact_path.parent.relative_to(root / 'work/output').as_posix(), 'type': 'output'}]}}}
        artifact = l6.worker.verify_glb(history, '17', root, prefix)[0]
        if artifact != output or artifact['sha256'] == initial['source']['input']['artifact']['sha256']:
            raise ValueError('old GLB replay or report mismatch')
        validate_embedded_inputs(artifact, plan, expected_inputs['artifacts'])
    else:
        artifact = l6.png_identity(artifact_path, role)
        if (output.get('type') != 'image' or artifact_path.suffix.lower() != '.png'
                or (artifact['width'], artifact['height']) != (768, 768)
                or (output.get('width'), output.get('height')) != (768, 768)):
            raise ValueError('invalid revised PNG')
    l6.record_execution(path, report, artifact, 'SUCCESS', [])
    return artifact | {'execution_report': ref(execution_path)}


def validate_embedded_inputs(artifact, plan, images):
    data = Path(artifact['path']).read_bytes()
    length, kind = struct.unpack_from('<I4s', data, 12)
    if kind != b'JSON': raise ValueError('GLB JSON chunk missing')
    graph = json.loads(json.loads(data[20:20 + length])['asset']['extras']['prompt'])
    for image in images:
        node = l6.MAPPING[image['role']]
        if (graph[node]['is_changed'] != [image['sha256']]
                or graph[node]['inputs']['image'] != plan['patches'][node]['image']):
            raise ValueError('GLB embedded current references differ')
    if graph['14']['inputs']['seed'] != plan['patches']['14']['seed']:
        raise ValueError('GLB embedded revision seed differs')


def validate_geometry(run_dir):
    initial = guard(run_dir)
    execution = read(run_dir / 'geometry_execution.json')
    order = read(run_dir / 'geometry_work_order.json')
    report = l6.read_ref(execution['worker_report'])
    artifact = execution['artifact']; plan = l6.read_ref(order['plan'])
    output = l6.validate_worker_report(order, report)
    if (execution['run_id'] != run_dir.name or execution['status'] != 'SUCCESS'
            or execution['work_order_id'] != order['work_order_id'] or execution['artifact'] != output
            or execution['work_order'] != ref(run_dir / 'geometry_work_order.json')
            or execution['plan'] != order['plan'] or execution['prompt_id'] != report['prompt_id']
            or execution['client_id'] != report['client_id'] or execution['initial_contract'] != ref(run_dir / 'initial.json')
            or artifact['sha256'] == initial['source']['input']['artifact']['sha256']):
        raise ValueError('current geometry execution lineage differs')
    l6.reviewer.checked_ref({k: artifact[k] for k in ('path', 'sha256')})
    validate_embedded_inputs(artifact, plan, validate_staging(run_dir))
    return artifact


def render_command(run_dir):
    initial = read(run_dir / 'initial.json')
    return [initial['renderer']['executable'], '--background', '--factory-startup', '--python-exit-code', '1',
            '--python', str(bridge.SCRIPT), '--', '--request', str(run_dir / 'render_request.json')]


def validate_render_manifest(run_dir):
    initial = guard(run_dir); validate_staging(run_dir)
    execution = read(run_dir / 'geometry_execution.json'); request = read(run_dir / 'render_request.json')
    artifact = validate_geometry(run_dir)
    manifest = read(run_dir / 'render_manifest.json')
    if (manifest['version'] != 'l7-m1.0' or manifest['run_id'] != run_dir.name
            or manifest['source_l6_run_id'] != initial['source']['input']['source_run_id']
            or manifest['source_glb'] != artifact or request['source_glb'] != artifact
            or manifest['render_request'] != ref(run_dir / 'render_request.json')
            or manifest['blender_executable'] != initial['renderer']['executable']
            or manifest['blender_version'] != initial['renderer']['version'] or manifest['config'] != diagnostic.CONFIG):
        raise ValueError('render manifest lineage differs')
    outputs = manifest['outputs']; bounds = manifest['bounding_box']
    extents = [b-a for a,b in zip(bounds['min'], bounds['max'])]
    if len(outputs) != 4 or [a['role'] for a in outputs] != list(diagnostic.ROLES): raise ValueError('four diagnostic roles differ')
    if (len(extents) != 3 or any(x < 0 or not math.isfinite(x) for x in extents) or max(extents) <= 0
            or manifest['mesh_count'] < 1 or manifest['object_count'] < manifest['mesh_count']
            or not all(math.isclose(a,b,rel_tol=1e-6,abs_tol=1e-7) for a,b in zip(bounds['extents'],extents))
            or not math.isclose(bounds['maximum_dimension'],max(extents),rel_tol=1e-6)
            or not all(math.isclose(c,(a+b)/2,rel_tol=1e-6,abs_tol=1e-7) for c,a,b in zip(bounds['center'],bounds['min'],bounds['max']))):
        raise ValueError('bounds metadata differs')
    for azimuth, image in zip((0,90,180,270), outputs):
        l6.checked_image(image)
        if (Path(image['path']) != Path(initial['comfy_root']) / 'work/output/l7' / run_dir.name / 'geometry_review' / (image['role']+'.png')
                or (image['width'],image['height']) != (512,512) or image['azimuth'] != azimuth
                or not math.isclose(image['ortho_scale'],max(extents)*1.2,rel_tol=1e-6)):
            raise ValueError('diagnostic camera/namespace differs')
    invocation = read(run_dir / 'renderer_invocation.json'); reservation = read(run_dir / 'renderer_reservation.json')
    if (invocation['status'] != 'SUCCESS' or invocation['process_started'] is not True or invocation['exit_code'] != 0
            or invocation['command'] != render_command(run_dir) or invocation['render_request'] != ref(run_dir / 'render_request.json')
            or reservation['source'] != invocation['render_request']
            or datetime.fromisoformat(invocation['started_at']) < datetime.fromisoformat(reservation['created_at'])):
        raise ValueError('renderer invocation differs')
    return manifest


def run_renderer(run_dir, timeout):
    initial = guard(run_dir); validate_staging(run_dir)
    if ref(bridge.SCRIPT) != initial['script'] or bridge.blender_identity(initial['renderer']['executable']) != initial['renderer']:
        raise ValueError('renderer executable/script changed')
    artifact = validate_geometry(run_dir)
    request = {'version': 'l7-m1.0', 'run_id': run_dir.name,
               'source_l6_run_id': initial['source']['input']['source_run_id'], 'source_glb': artifact,
               'blender_version': initial['renderer']['version'], 'script': initial['script'], 'config': diagnostic.CONFIG,
               'output_dir': str(Path(initial['comfy_root']) / 'work/output/l7' / run_dir.name / 'geometry_review'),
               'manifest_path': str(run_dir / 'render_manifest.json')}
    if Path(request['output_dir']).exists(): raise ValueError('render namespace exists')
    write_once(run_dir / 'render_request.json', request)
    reserve(run_dir, 'renderer', run_dir / 'render_request.json')
    record = {'run_id':run_dir.name,'command':render_command(run_dir),'render_request':ref(run_dir/'render_request.json'),
              'initial_contract':ref(run_dir/'initial.json'),'started_at':l6.now(),'process_started':True,'status':'UNRESOLVED','exit_code':None}
    write_once(run_dir/'renderer_invocation.json',record); start=time.monotonic()
    try:
        process=subprocess.run(record['command'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
        record.update(status='SUCCESS' if process.returncode==0 else 'FAILED',exit_code=process.returncode,
                      stdout_sha256=hashlib.sha256(process.stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(process.stderr.encode()).hexdigest())
    except subprocess.TimeoutExpired: record.update(status='UNRESOLVED',error='RENDER_TIMEOUT')
    except OSError as exc: record.update(status='FAILED',process_started=False,error=str(exc))
    finally:
        record.update(completed_at=l6.now(),duration_seconds=time.monotonic()-start)
        l6.worker.write_report(run_dir/'renderer_invocation.json',record)
    if record['status']!='SUCCESS': raise l6.StageFailure(record['status'],'RENDER_STAGE')
    return validate_render_manifest(run_dir)


def review_artifacts(run_dir, kind):
    images = current_images(run_dir) if kind == 'multiview' else validate_staging(run_dir)
    if kind == 'geometry':
        images = [dict(a,role='source_'+a['role']) for a in images] + validate_render_manifest(run_dir)['outputs']
    return [{k:a[k] for k in ('role','path','sha256')} | {'media_type':'image/png'} for a in images]


def prepare_review(run_dir, kind):
    initial = guard(run_dir)
    if kind == 'geometry':
        instructions = l6.reviewer.checked_ref(initial['source']['instructions']).read_text(encoding='utf-8')
        instructions = instructions.replace('References are the exact L6 generation inputs.', 'References are the exact CURRENT geometry generation inputs.')
        instructions += '\nReferences are the exact CURRENT geometry inputs. This review follows one correction; no second correction is permitted.\n'
        source_result, order, report = [ref(run_dir / (name + '.json')) for name in ('render_manifest','render_request','renderer_invocation')]
    else:
        instructions = ('Review front/right/left/back once for same subject/major structure/direction consistency, '
                        'severe crop, missing/detached major parts, contradictions and downstream geometry blockers. '
                        'PASS requires no blockers and NONE/null; REVISE requires blockers and MULTIVIEW_REVISE/right,left,back or null. '
                        'HUMAN_REQUIRED uses HUMAN_REQUIRED/null. Do not favor any verdict; no further correction will execute. Return Result0.3 JSON.\n')
        source_result=ref(run_dir/'multiview_manifest.json'); order=ref(run_dir/'revision_action.json')
        target=initial['action']['target']; report=ref(run_dir/(target+'_execution.json'))
    prefix=kind+'_review'
    with (run_dir/(prefix+'_instructions.md')).open('x',encoding='utf-8',newline='\n') as stream: stream.write(instructions)
    request={'request_version':'0.2','run_id':run_dir.name,'review_id':run_dir.name+'-'+prefix,
             'stage':'GEOMETRY_REVIEW' if kind=='geometry' else 'MULTIVIEW_REVIEW',
             'output_kind':'geometry_diagnostic_images' if kind=='geometry' else 'multiview_images',
             'source_result':source_result,'work_order':order,'worker_report':report,
             'artifacts':review_artifacts(run_dir,kind),'instruction_file':ref(run_dir/(prefix+'_instructions.md')),
             'context':{'initial_contract':ref(run_dir/'initial.json'),'current_manifest':ref(run_dir/'multiview_manifest.json'),
                        'revision_action':ref(run_dir/'revision_action.json'),'dispatch_allowed':False}}
    l6.reviewer.validate_request(request);write_once(run_dir/(prefix+'_request.json'),request)
    return request


def validate_request(run_dir, kind):
    request=l6.reviewer.validate_request(read(run_dir/(kind+'_review_request.json')))
    expected_source=ref(run_dir/('render_manifest.json' if kind=='geometry' else 'multiview_manifest.json'))
    expected_order=ref(run_dir/('render_request.json' if kind=='geometry' else 'revision_action.json'))
    expected_report=ref(run_dir/('renderer_invocation.json' if kind=='geometry' else read(run_dir/'revision_action.json')['target']+'_execution.json'))
    if (request['run_id']!=run_dir.name or request['review_id']!=run_dir.name+'-'+kind+'_review'
            or request['stage']!=('GEOMETRY_REVIEW' if kind=='geometry' else 'MULTIVIEW_REVIEW')
            or request['output_kind']!=('geometry_diagnostic_images' if kind=='geometry' else 'multiview_images')
            or request['source_result']!=expected_source or request['artifacts']!=review_artifacts(run_dir,kind)
            or request['work_order']!=expected_order or request['worker_report']!=expected_report
            or request['instruction_file']!=ref(run_dir/(kind+'_review_instructions.md'))
            or request['context']!={'initial_contract':ref(run_dir/'initial.json'), 'current_manifest':ref(run_dir/'multiview_manifest.json'),
                                   'revision_action':ref(run_dir/'revision_action.json'),'dispatch_allowed':False}):
        raise ValueError('current Review lineage differs')
    return request


def checked_review(run_dir, kind):
    request=validate_request(run_dir,kind);prefix=kind+'_review'
    result_path,report_path=[run_dir/(prefix+s) for s in ('_result.json','_invocation.json')]
    _,result=l6.reviewer.checked_invocation({'kind':'RESULT_REVIEW',**ref(result_path),
       'request_path':str(run_dir/(prefix+'_request.json')),'request_sha256':l6.digest(run_dir/(prefix+'_request.json')),
       'invocation_report_path':str(report_path),'invocation_report_sha256':l6.digest(report_path)})
    report=read(report_path);reservation=read(run_dir/(prefix+'_reservation.json'))
    if (report['reviewer_mode']!='CODEX_CLI' or report['reviewer_process_started'] is not True
            or report['attached_images']!=[{k:a[k] for k in ('role','path','sha256')} for a in request['artifacts']]
            or reservation['source']!=ref(run_dir/(prefix+'_request.json'))
            or datetime.fromisoformat(report['started_at'])<datetime.fromisoformat(reservation['created_at'])):
        raise ValueError('Reviewer invocation differs')
    if kind=='geometry':bridge.validate_action(result)
    elif not ((result['verdict']=='PASS' and not result['blocking_issues'] and result['suggested_action']=={'code':'NONE','target':None})
              or (result['verdict']=='HUMAN_REQUIRED' and result['suggested_action']=={'code':'HUMAN_REQUIRED','target':None})
              or (result['verdict']=='REVISE' and result['blocking_issues'] and result['suggested_action']['code']=='MULTIVIEW_REVISE'
                  and result['suggested_action']['target'] in (*l6.VIEWS,None))):
        raise ValueError('multiview verdict/action differs')
    return result


def run_review(run_dir, kind, timeout):
    guard(run_dir);validate_request(run_dir,kind);prefix=kind+'_review'
    result_path,report_path=[run_dir/(prefix+s) for s in ('_result.json','_invocation.json')]
    if result_path.exists() or report_path.exists():raise ValueError('Review records already exist')
    reserve(run_dir,prefix,run_dir/(prefix+'_request.json'))
    try:
        report=l6.reviewer.review_once(run_dir/(prefix+'_request.json'),result_path,report_path,timeout=timeout,workspace=run_dir)
    except (subprocess.TimeoutExpired,OSError) as exc:raise l6.StageFailure('UNRESOLVED',kind.upper()+'_REVIEW_STAGE') from exc
    if report['invocation_status']!='SUCCESS':
        raise l6.StageFailure('UNRESOLVED' if report.get('validation_error') or report['invocation_status']=='UNRESOLVED' else 'FAILED',kind.upper()+'_REVIEW_STAGE')
    return checked_review(run_dir,kind)


def finish(run_dir,status,reason,result=None,error=None):
    # Evidence corruption must still permit a durable failure record, never a new effect.
    guard(run_dir, check_source=False)
    state=read(run_dir/'state.json')|{'state':status,'terminal':status!='UNRESOLVED','reason':reason,
              'finished_at':l6.now(),'budgets':budgets(run_dir),'final_verdict':result['verdict'] if result else None,
              'errors':[str(error)] if error else [],'delivered':False}
    workers=[];reviewers=[]
    for stage in ('view','geometry','multiview_review','geometry_review','renderer'):
        if not (run_dir/(stage+'_reservation.json')).exists():continue
        role=read(run_dir/'revision_action.json')['target'] if stage=='view' else stage
        report=l6.available_report(run_dir/(role+('_worker_report.json' if stage in ('view','geometry') else '_invocation.json')))
        if stage in ('view','geometry'):
            assets=l6.read_ref(read(run_dir/'initial.json')['asset_manifest'])
            model=assets['geometry']['model'] if stage=='geometry' else assets['view_generation'][role]['model']
            duration=None
            if report.get('started_at') and report.get('completed_at'):
                duration=(datetime.fromisoformat(report['completed_at'])-datetime.fromisoformat(report['started_at'])).total_seconds()
            workers.append({'stage':role,'backend':'ComfyUI','model':model,'invocations':int(bool(report['prompt_id'])) if report.get('status')=='SUCCESS' else None,
                            'duration_seconds':duration})
        elif stage!='renderer':reviewers.append({'stage':stage,'invocations':int(report['reviewer_process_started']) if 'reviewer_process_started' in report else None,'duration_seconds':report.get('duration_seconds')})
    renderer=l6.available_report(run_dir/'renderer_invocation.json')
    action=read(run_dir/'revision_action.json') if (run_dir/'revision_action.json').exists() else None
    usage={'run_id':run_dir.name,'revision':action,'workers':workers,'reviewers':reviewers,
           'renderer':{'invocations':int(renderer['process_started']) if 'process_started' in renderer else None if (run_dir/'renderer_reservation.json').exists() else 0,'duration_seconds':renderer.get('duration_seconds')},
           'frontier':{k:None for k in ('requested_model','requested_reasoning_effort','actual_model','actual_reasoning_effort','input_tokens','cached_input_tokens','output_tokens','reasoning_tokens','reported_credits')},
           'budgets':budgets(run_dir),'automatic_retries':0,'final_state':status}
    write_once(run_dir/'usage.json',usage);l6.worker.write_report(run_dir/'state.json',state)
    records={p.stem:ref(p) for p in run_dir.iterdir() if p.is_file() and p.name not in ('state.json','terminal.json')}
    if state['terminal']:write_once(run_dir/'terminal.json',state|{'records':records})
    return state


def reject_initial(run_dir, source_review_run, reason, error):
    """Durable zero-effect rejection; no unvalidated source can authorize stages."""
    run_dir.parent.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir()
    initial = {'version': 'l7-feedback.0', 'run_id': run_dir.name, 'created_at': l6.now(),
               'state': 'SOURCE_REVIEW_READY', 'terminal': False, 'limits': LIMITS,
               'budgets': budgets(run_dir), 'source_review_run': str(Path(source_review_run).resolve()),
               'source_validated': False}
    write_once(run_dir / 'initial.json', initial)
    state = {'run_id': run_dir.name, 'state': 'FAILED', 'terminal': True, 'reason': reason,
             'initial_contract': ref(run_dir / 'initial.json'), 'finished_at': l6.now(),
             'budgets': budgets(run_dir), 'errors': [str(error)], 'delivered': False}
    usage = {'run_id': run_dir.name, 'workers': [], 'reviewers': [], 'renderer': {'invocations': 0, 'duration_seconds': None},
             'budgets': budgets(run_dir), 'automatic_retries': 0, 'final_state': 'FAILED',
             'frontier': {k: None for k in ('requested_model', 'requested_reasoning_effort', 'actual_model',
                         'actual_reasoning_effort', 'input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_tokens', 'reported_credits')}}
    write_once(run_dir / 'usage.json', usage)
    l6.worker.write_report(run_dir / 'state.json', state)
    write_once(run_dir / 'terminal.json', state | {'records': {'initial': ref(run_dir / 'initial.json'), 'usage': ref(run_dir / 'usage.json')}})
    return state


def run_feedback(run_id='l7-feedback-preflight',source_review_run=SOURCE_DIR,comfy_root=l6.worker.DEFAULT_COMFY_ROOT,
                 blender_executable=bridge.BLENDER,worker_timeout=600,review_timeout=600,render_timeout=600,*,execute=False):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,48}',str(run_id)) or min(worker_timeout,review_timeout,render_timeout)<=0:
        raise ValueError('invalid run ID/timeouts')
    run_dir=ROOT/'runs/l7'/run_id
    if execute and run_dir.exists():
        if (run_dir/'terminal.json').exists():return {'status':'ALREADY_TERMINAL','terminal':ref(run_dir/'terminal.json')}
        raise ValueError('CONTROLLER_RUN_ALREADY_EXISTS: no automatic resume')
    try:
        checks=preflight(source_review_run,comfy_root,blender_executable)
    except l6.StageFailure as exc:
        if not execute: raise
        return reject_initial(run_dir, source_review_run, exc.reason, exc)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        if not execute: raise
        try: validate_source(source_review_run)
        except (OSError, ValueError, KeyError, TypeError):
            return reject_initial(run_dir, source_review_run, 'SOURCE_REVIEW_INVALID', exc)
        raise  # Missing/changed infrastructure is a preflight blocker, not a fake run failure.
    if not execute:return checks
    root=Path(comfy_root).resolve()
    if any(p.exists() for p in (root/'work/input/l7'/run_id,root/'work/output/l7'/run_id,root/'work/output/mesh/l7'/run_id)):
        raise ValueError('external namespace exists')
    run_dir.parent.mkdir(parents=True,exist_ok=True);run_dir.mkdir()
    initial={k:v for k,v in checks.items() if k not in ('status','effects')}|{'preflight': {'status': 'PREFLIGHT_PASS', 'effects': checks['effects']}, 'version':'l7-feedback.0','run_id':run_id,'created_at':l6.now(),'state':'SOURCE_REVIEW_READY',
                   'terminal':False,'comfy_root':str(root),'budgets':budgets(run_dir)}
    write_once(run_dir/'initial.json',initial)
    l6.worker.write_report(run_dir/'state.json',initial|{'initial_contract':ref(run_dir/'initial.json')})
    if checks['source']['verdict']=='PASS':return finish(run_dir,'INTERNAL_ACCEPT','SOURCE_GEOMETRY_PASS')
    if checks['source']['verdict']=='HUMAN_REQUIRED':return finish(run_dir,'ABORT','HUMAN_REQUIRED')
    stage='REVISION_POLICY'
    try:
        action=checks['action'];role=action['target']
        seed=checks['source']['previous_geometry_seed'] if role=='geometry' else l6.read_ref(checks['source']['view_plans'][role])['patches']['11']['seed']
        write_once(run_dir/'revision_action.json',{'version':'l7-feedback.0','run_id':run_id,'source_review':checks['source']['result'],
                   'source_verdict':'REVISE','action_code':action['code'],'target':role,'revision_ordinal':1,'previous_seed':seed,
                   'revision_seed':next_seed(seed),'budget':{'limit':1,'consumed':0},'status':'REVISION_PLANNED'})
        reserve(run_dir,'revision',run_dir/'revision_action.json');update(run_dir,'REVISION_RUNNING')
        images=copy.deepcopy(checks['source']['input']['references'])
        if action['code']=='REGENERATE_VIEW':
            stage='REVISION_WORKER_STAGE';publish_order(run_dir,role);images[l6.ROLES.index(role)]=run_worker(run_dir,role,worker_timeout)
        write_once(run_dir/'multiview_manifest.json',{'version':'l7-feedback.0','run_id':run_id,'references':images,
                   'source_manifest':checks['source']['input']['multiview_manifest'],'revision_action':ref(run_dir/'revision_action.json'),
                   'replaced_role':role if action['code']=='REGENERATE_VIEW' else None})
        if action['code']=='REGENERATE_VIEW':
            stage='MULTIVIEW_REVIEW_STAGE';update(run_dir,'MULTIVIEW_REVIEWING');prepare_review(run_dir,'multiview')
            verdict=run_review(run_dir,'multiview',review_timeout)
            if verdict['verdict']!='PASS':return finish(run_dir,'ABORT','HUMAN_REQUIRED' if verdict['verdict']=='HUMAN_REQUIRED' else 'REVISION_BUDGET_EXHAUSTED',verdict)
        stage='REVISION_WORKER_STAGE';update(run_dir,'GEOMETRY_RUNNING');stage_bytes(run_dir);publish_order(run_dir,'geometry');run_worker(run_dir,'geometry',worker_timeout)
        stage='RENDER_STAGE';update(run_dir,'GEOMETRY_RENDERING');run_renderer(run_dir,render_timeout)
        stage='GEOMETRY_REVIEW_STAGE';update(run_dir,'GEOMETRY_REVIEWING');prepare_review(run_dir,'geometry');result=run_review(run_dir,'geometry',review_timeout)
        status='INTERNAL_ACCEPT' if result['verdict']=='PASS' else 'ABORT'
        reason={'PASS':'GEOMETRY_PASS','REVISE':'REVISION_BUDGET_EXHAUSTED','HUMAN_REQUIRED':'HUMAN_REQUIRED'}[result['verdict']]
        return finish(run_dir,status,reason,result)
    except l6.StageFailure as exc:return finish(run_dir,exc.state,exc.reason,error=exc)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        return finish(run_dir,'UNRESOLVED' if stage.endswith('REVIEW_STAGE') else 'FAILED',stage,error=exc)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group();mode.add_argument('--preflight',action='store_true');mode.add_argument('--execute',action='store_true')
    parser.add_argument('--run-id',default='l7-feedback-preflight');parser.add_argument('--source-review-run',type=Path,default=SOURCE_DIR)
    parser.add_argument('--comfy-root',type=Path,default=l6.worker.DEFAULT_COMFY_ROOT);parser.add_argument('--blender',type=Path,default=bridge.BLENDER)
    for name in ('worker','review','render'):parser.add_argument('--'+name+'-timeout',type=int,default=600)
    args=parser.parse_args(argv)
    try:
        result=run_feedback(args.run_id,args.source_review_run,args.comfy_root,args.blender,args.worker_timeout,args.review_timeout,args.render_timeout,execute=args.execute)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result.get('state',result.get('status')) in ('PREFLIGHT_PASS','INTERNAL_ACCEPT','ALREADY_TERMINAL') else 1
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('L7-M2 BLOCKED: '+str(exc),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
