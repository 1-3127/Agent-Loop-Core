"""Scenario A L7-M1: one diagnostic render and one geometry review, then stop."""
import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import sys
import time

from scenario_a import l6_pipeline as l6
from scenario_a import l7_blender_diagnostic as diagnostic
from scenario_a import session_binding as bound

ROOT = l6.ROOT
L6_RUN_ID = 'l6-m3-20260930-164920-8109160a'
L6_DIR = ROOT / 'runs/l6' / L6_RUN_ID
L6_TERMINAL_SHA = 'f595e1dc4834368faba477a0afa1f3412062d9410027800e7b1b5e55e25c4abc'
GLB_SHA = '1cc00067c772f3efdad34f36cb44c4b5d54ed5bfa4b03a4888a3f3de80fca252'
GLB_BYTES = 1139016
REFERENCE_SHAS = ('8a6dd9ca3f8984b31c1243e7698cd5030b423464d80e0ad763609148e0ff4f51',
                  '6c4828c226de954cab7daee8975f4e2f60ee1507bee5c9eb72fd34d9c146bc4d',
                  'd1f6c681ebbee462e26b42e5de710caf34424edfa68eb01686f7caa88b7b89d6',
                  '2aa7f06a081869b961650498fe77bb19955019b958098156cee42b30bc1f937f')
BLENDER = Path('D:/Blender_5.2/blender.exe')
BLENDER_VERSION = '5.2.0 LTS'
SCRIPT = Path(diagnostic.__file__).resolve()
OUTPUT_ROOT = l6.worker.DEFAULT_COMFY_ROOT / 'work/output/l7'
SOURCE_ROLES = tuple('source_' + x for x in l6.ROLES)
ROLES = SOURCE_ROLES + diagnostic.ROLES
read = l6.read_json
ref = l6.reference
write_once = l6.write_once


def validate_l6(l6_dir=None, parent_ref=None):
    legacy = l6_dir is None
    l6_dir = L6_DIR if legacy else Path(l6_dir)
    source_run_id = L6_RUN_ID if legacy else l6_dir.name
    if not legacy:
        child = bound.checked_child(l6_dir, parent_ref=parent_ref)
        if child is None or child[0]['kind'] != 'l6':
            raise ValueError('UNBOUND_L6_SOURCE')
    if legacy and l6.digest(l6_dir / 'terminal.json') != L6_TERMINAL_SHA:
        raise ValueError('L6 terminal identity mismatch')
    terminal = read(l6_dir / 'terminal.json')
    if terminal['state'] != 'GEOMETRY_READY' or terminal['terminal'] is not True:
        raise ValueError('L6 not GEOMETRY_READY')
    for reference in terminal['records'].values():
        l6.reviewer.checked_ref(reference)
    images = l6.validate_manifest(read(l6_dir / 'multiview_manifest.json'), l6_dir)
    if legacy and tuple(a['sha256'] for a in images) != REFERENCE_SHAS:
        raise ValueError('L6 reference identities differ')
    if l6.checked_review(l6_dir)['verdict'] != 'PASS':
        raise ValueError('L6 multiview not PASS')
    l6.validate_staging(l6_dir)
    execution = read(l6_dir / 'geometry_execution.json')
    order = read(l6_dir / 'geometry_work_order.json')
    report = read(l6_dir / 'geometry_worker_report.json')
    l6.validate_worker_report(order, report)
    for suffix in ('plan', 'work_order', 'execution'):
        bound.check_record(l6_dir, l6_dir / ('geometry_' + suffix + '.json'))
    artifact = execution['artifact']
    if (artifact != terminal['artifact'] or artifact != report['outputs'][0]
            or execution['status'] != 'SUCCESS' or execution['run_id'] != source_run_id
            or execution['worker_report'] != ref(l6_dir / 'geometry_worker_report.json')
            or execution['plan'] != ref(l6_dir / 'geometry_plan.json')
            or execution['work_order'] != ref(l6_dir / 'geometry_work_order.json')
            or execution['prompt_id'] != report['prompt_id']):
        raise ValueError('L6 geometry linkage differs')
    data = Path(artifact['path']).read_bytes()
    if ((legacy and (len(data) != GLB_BYTES or hashlib.sha256(data).hexdigest() != GLB_SHA))
            or (not legacy and (len(data) != artifact['bytes'] or hashlib.sha256(data).hexdigest() != artifact['sha256']))):
        raise ValueError('L6 GLB identity mismatch')
    if struct.unpack_from('<4sII', data) != (b'glTF', 2, len(data)):
        raise ValueError('L6 GLB structural mismatch')
    length, kind = struct.unpack_from('<I4s', data, 12)
    if kind != b'JSON':
        raise ValueError('GLB JSON chunk missing')
    embedded = json.loads(json.loads(data[20:20 + length])['asset']['extras']['prompt'])
    plan = read(l6_dir / 'geometry_plan.json')
    for image in images:
        node = l6.MAPPING[image['role']]
        if (embedded[node]['is_changed'] != [image['sha256']]
                or embedded[node]['inputs']['image'] != plan['patches'][node]['image']):
            raise ValueError('GLB embedded input identity differs')
    return {'source_run_id': source_run_id, 'artifact': artifact, 'references': images,
            **{name: ref(l6_dir / (name + '.json')) for name in
               ('geometry_execution', 'geometry_plan', 'geometry_worker_report', 'multiview_manifest', 'terminal')}}


def blender_identity(executable):
    executable = Path(executable).resolve(strict=True)
    if not executable.is_file():
        raise ValueError('Blender executable missing')
    stat = executable.stat()
    return {'executable': str(executable), 'version': BLENDER_VERSION,
            'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns}


def preflight(executable=BLENDER, *, source_l6_run=None, session_binding=None):
    if session_binding is None and source_l6_run is not None:
        raise ValueError('current L6 source requires Session binding')
    return {'status': 'PREFLIGHT_PASS', 'input': validate_l6(source_l6_run, session_binding), 'renderer': blender_identity(executable),
            'script': ref(SCRIPT), 'config': diagnostic.CONFIG, 'effects': 0}



def validate_input(initial):
    reference = initial.get('session_binding')
    if reference is None:
        return validate_l6()
    child = l6.read_ref(reference)
    source = l6.reviewer.checked_ref(child['source']).parent
    return validate_l6(source, child['parent'])


def budgets(run_dir):
    return {key + '_budget': {'limit': 1, 'consumed': int((run_dir / (key + '_reservation.json')).exists()),
                              'remaining': int(not (run_dir / (key + '_reservation.json')).exists())}
            for key in ('renderer', 'reviewer')}


def guard(run_dir):
    bound.effect_guard(run_dir)
    if (run_dir / 'terminal.json').exists():
        raise ValueError('ALREADY_TERMINAL')
    state = read(run_dir / 'state.json')
    initial = l6.read_ref(state['initial_contract'])
    if state['terminal'] or state['state'] == 'UNRESOLVED':
        raise ValueError('ALREADY_TERMINAL or UNRESOLVED')
    if (initial['run_id'] != run_dir.name or initial['terminal'] is not False
            or initial['renderer_budget'] != {'limit': 1, 'consumed': 0, 'remaining': 1}
            or initial['reviewer_budget'] != {'limit': 1, 'consumed': 0, 'remaining': 1}):
        raise ValueError('initial budget differs')
    return initial


def reserve(run_dir, component, source):
    guard(run_dir)
    if component not in ('renderer', 'reviewer'):
        raise ValueError('unsupported component')
    path = run_dir / (component + '_reservation.json')
    if path.exists():
        raise ValueError(component.upper() + '_ALREADY_RESERVED')
    expected = run_dir / ('render_request.json' if component == 'renderer' else 'review_request.json')
    if Path(source) != expected:
        raise ValueError('alternate reservation source forbidden')
    write_once(path, {'run_id': run_dir.name, 'component': component, 'created_at': l6.now(),
                      'initial_contract': ref(run_dir / 'initial.json'), 'request': ref(expected)})


def render_command(run_dir):
    initial = read(run_dir / 'initial.json')
    return [initial['renderer']['executable'], '--background', '--factory-startup', '--python-exit-code', '1',
            '--python', str(SCRIPT), '--', '--request', str(run_dir / 'render_request.json')]


def run_renderer(run_dir, timeout):
    initial = guard(run_dir)
    if (run_dir / 'renderer_reservation.json').exists():
        raise ValueError('RENDERER_ALREADY_RESERVED')
    if validate_input(initial) != initial['input'] or ref(SCRIPT) != initial['script']:
        raise ValueError('input/script changed before render')
    if blender_identity(initial['renderer']['executable']) != initial['renderer']:
        raise ValueError('Blender executable changed')
    request = read(run_dir / 'render_request.json')
    if request != make_render_request(run_dir, initial):
        raise ValueError('render request identity differs')
    if Path(request['output_dir']).exists() or (run_dir / 'render_manifest.json').exists():
        raise ValueError('render namespace exists')
    reserve(run_dir, 'renderer', run_dir / 'render_request.json')
    record = {'run_id': run_dir.name, 'backend': 'Blender', 'command': render_command(run_dir),
              'render_request': ref(run_dir / 'render_request.json'), 'initial_contract': ref(run_dir / 'initial.json'),
              'started_at': l6.now(), 'completed_at': None, 'process_started': True,
              'status': 'UNRESOLVED', 'exit_code': None}
    path = run_dir / 'renderer_invocation.json'
    write_once(path, record)
    start = time.monotonic()
    try:
        process = subprocess.run(record['command'], capture_output=True, text=True,
                                 encoding='utf-8', errors='replace', timeout=timeout)
        record.update(exit_code=process.returncode, status='SUCCESS' if process.returncode == 0 else 'FAILED',
                      stdout_sha256=hashlib.sha256(process.stdout.encode()).hexdigest(),
                      stderr_sha256=hashlib.sha256(process.stderr.encode()).hexdigest(),
                      stdout=process.stdout, stderr=process.stderr)
    except subprocess.TimeoutExpired:
        record.update(status='UNRESOLVED', error='RENDER_TIMEOUT')
    except OSError as exc:
        record.update(status='FAILED', process_started=False, error=str(exc))
    finally:
        record.update(completed_at=l6.now(), duration_seconds=time.monotonic() - start)
        l6.worker.write_report(path, record)
    if record['status'] != 'SUCCESS':
        raise l6.StageFailure(record['status'], 'RENDER_STAGE')
    return validate_render_manifest(run_dir)


def make_render_request(run_dir, initial):
    return {'version': 'l7-m1.0', 'run_id': run_dir.name, 'source_l6_run_id': initial['input']['source_run_id'],
            'source_glb': initial['input']['artifact'], 'blender_version': initial['renderer']['version'],
            'script': initial['script'], 'config': diagnostic.CONFIG,
            'output_dir': str(Path(initial.get('output_root', OUTPUT_ROOT)) / run_dir.name / 'geometry_review'),
            'manifest_path': str(run_dir / 'render_manifest.json')}


def validate_render_manifest(run_dir):
    initial = read(run_dir / 'initial.json')
    if validate_input(initial) != initial['input']:
        raise ValueError('L6 changed after render')
    manifest = read(run_dir / 'render_manifest.json')
    if (manifest['version'] != 'l7-m1.0' or manifest['run_id'] != run_dir.name
            or manifest['source_l6_run_id'] != initial['input']['source_run_id'] or manifest['source_glb'] != initial['input']['artifact']
            or manifest['render_request'] != ref(run_dir / 'render_request.json')
            or manifest['blender_executable'] != initial['renderer']['executable']
            or manifest['blender_version'] != initial['renderer']['version'] or manifest['config'] != diagnostic.CONFIG):
        raise ValueError('render manifest identity/config differs')
    outputs = manifest['outputs']
    if len(outputs) != 4 or [a['role'] for a in outputs] != list(diagnostic.ROLES):
        raise ValueError('diagnostic roles must occur exactly once')
    bounds = manifest['bounding_box']
    if manifest['mesh_count'] < 1 or manifest['object_count'] < manifest['mesh_count']:
        raise ValueError('mesh missing')
    extents = [b - a for a, b in zip(bounds['min'], bounds['max'])]
    if len(extents) != 3 or max(extents) <= 0 or any(x < 0 or not math.isfinite(x) for x in extents):
        raise ValueError('invalid bounds')
    if (not all(math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-7) for a, b in zip(bounds['extents'], extents))
            or not math.isclose(bounds['maximum_dimension'], max(extents), rel_tol=1e-6)
            or not all(math.isclose(c, (a + b) / 2, rel_tol=1e-6, abs_tol=1e-7)
                       for c, a, b in zip(bounds['center'], bounds['min'], bounds['max']))):
        raise ValueError('bounds metadata differs')
    for angle, a in zip((0, 90, 180, 270), outputs):
        expected = Path(initial.get('output_root', OUTPUT_ROOT)) / run_dir.name / 'geometry_review' / (a['role'] + '.png')
        if (a['azimuth'] != angle or Path(a['path']) != expected
                or not math.isclose(a['ortho_scale'], max(extents) * 1.2, rel_tol=1e-6)):
            raise ValueError('diagnostic camera/namespace differs')
        l6.checked_image(a)
        if (a['width'], a['height']) != (512, 512):
            raise ValueError('diagnostic dimensions differ')
    invocation = read(run_dir / 'renderer_invocation.json')
    reservation = read(run_dir / 'renderer_reservation.json')
    if (invocation['status'] != 'SUCCESS' or invocation['process_started'] is not True
            or invocation['exit_code'] != 0 or invocation['command'] != render_command(run_dir)
            or invocation['render_request'] != ref(run_dir / 'render_request.json')
            or reservation['request'] != invocation['render_request']
            or reservation['initial_contract'] != ref(run_dir / 'initial.json')
            or datetime.fromisoformat(invocation['started_at']) < datetime.fromisoformat(reservation['created_at'])):
        raise ValueError('renderer invocation identity differs')
    return manifest


def artifacts(run_dir):
    initial = read(run_dir / 'initial.json')
    if validate_input(initial) != initial['input']:
        raise ValueError('references changed before Review')
    renders = validate_render_manifest(run_dir)['outputs']
    originals = [dict(a, role='source_' + a['role']) for a in initial['input']['references']]
    return [{key: a[key] for key in ('role', 'path', 'sha256')} | {'media_type': 'image/png'} for a in originals + renders]


def prepare_review(run_dir):
    guard(run_dir)
    instructions = (
        'Review eight attached PNGs exactly in this order: source_front, source_right, source_left, source_back, '
        'geometry_azimuth_0, geometry_azimuth_90, geometry_azimuth_180, geometry_azimuth_270. '
        'References are the exact L6 generation inputs. Diagnostics are neutral Workbench orthographic views, '
        'Blender +Z up, azimuth 0 from -Y, then +X,+Y,-X. These axes are NOT measured source camera poses. '
        'Compare major silhouette, body proportions, collapsed/missing/merged major parts, severe stretching, '
        'unsupported asymmetry, visually apparent holes/self-intersections/explosion and major cross-view structure. '
        'Ignore texture/PBR, shading, UV, topology/edge flow, rigging, production optimization and fine artistic quality. '
        'Do not favor any verdict. PASS requires no blockers and NONE/null. REVISE requires blockers: '
        'REGENERATE_VIEW with target right/left/back only when a particular generated reference is the likely cause; '
        'otherwise REGENERATE_GEOMETRY with target geometry when references are coherent and mesh generation is the likely cause. '
        'These are diagnostic suggestions, not causal proof; no action will execute. Original front is authoritative. '
        'If front is insufficient, orientation/defect origin is ambiguous or action confidence is insufficient, '
        'use HUMAN_REQUIRED with HUMAN_REQUIRED/null. Return only requested Result0.3 JSON with concrete visual observations.')
    instructions = bound.review_instruction(run_dir, 'geometry', instructions)
    with (run_dir / 'review_instructions.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(instructions + '\n')
    request = {'request_version': '0.2', 'run_id': run_dir.name, 'review_id': run_dir.name + '-geometry-review',
               'stage': 'GEOMETRY_REVIEW', 'output_kind': 'geometry_diagnostic_images',
               'source_result': ref(run_dir / 'render_manifest.json'), 'work_order': ref(run_dir / 'render_request.json'),
               'worker_report': ref(run_dir / 'renderer_invocation.json'), 'artifacts': artifacts(run_dir),
               'instruction_file': ref(run_dir / 'review_instructions.md'),
               'context': {'initial_contract': ref(run_dir / 'initial.json'),
                           'l6_input': read(run_dir / 'initial.json')['input'], 'diagnostic_config': diagnostic.CONFIG,
                           'dispatch_allowed': False}}
    request['context'] = bound.review_context(run_dir, 'geometry', request['context'])
    l6.reviewer.validate_request(request)
    write_once(run_dir / 'review_request.json', request)
    return request


def validate_review_request(run_dir):
    request = l6.reviewer.validate_request(read(run_dir / 'review_request.json'))
    if (request['run_id'] != run_dir.name or request['review_id'] != run_dir.name + '-geometry-review'
            or request['stage'] != 'GEOMETRY_REVIEW' or request['output_kind'] != 'geometry_diagnostic_images'
            or request['artifacts'] != artifacts(run_dir) or [a['role'] for a in request['artifacts']] != list(ROLES)
            or request['source_result'] != ref(run_dir / 'render_manifest.json')
            or request['work_order'] != ref(run_dir / 'render_request.json')
            or request['worker_report'] != ref(run_dir / 'renderer_invocation.json')
            or request['instruction_file'] != ref(run_dir / 'review_instructions.md')
            or request['context']['initial_contract'] != ref(run_dir / 'initial.json')
            or request['context']['l6_input'] != read(run_dir / 'initial.json')['input']
            or request['context']['dispatch_allowed'] is not False):
        raise ValueError('eight-image Review lineage differs')
    bound.check_request(run_dir, 'geometry', request)
    return request


def run_review(run_dir, timeout):
    guard(run_dir)
    if (run_dir / 'reviewer_reservation.json').exists():
        raise ValueError('REVIEWER_ALREADY_RESERVED')
    validate_review_request(run_dir)
    reserve(run_dir, 'reviewer', run_dir / 'review_request.json')
    report = l6.reviewer.review_once(run_dir / 'review_request.json', run_dir / 'review_result.json',
                                   run_dir / 'review_invocation.json', timeout=timeout, workspace=run_dir)
    if report['invocation_status'] != 'SUCCESS':
        status = 'UNRESOLVED' if report.get('validation_error') or report['invocation_status'] == 'UNRESOLVED' else 'FAILED'
        raise l6.StageFailure(status, 'REVIEW_STAGE')
    return checked_review(run_dir)


def validate_action(result):
    verdict, action = result['verdict'], result['suggested_action']
    if verdict == 'PASS' and not result['blocking_issues'] and action == {'code': 'NONE', 'target': None}:
        return True
    if verdict == 'HUMAN_REQUIRED' and action == {'code': 'HUMAN_REQUIRED', 'target': None}:
        return False
    if verdict == 'REVISE' and result['blocking_issues'] and (
            action == {'code': 'REGENERATE_GEOMETRY', 'target': 'geometry'}
            or action['code'] == 'REGENERATE_VIEW' and action['target'] in ('right', 'left', 'back')):
        return True
    raise ValueError('unsupported diagnostic action/verdict')


def checked_review(run_dir):
    request = validate_review_request(run_dir)
    result_path, invocation_path = run_dir / 'review_result.json', run_dir / 'review_invocation.json'
    source = {'kind': 'RESULT_REVIEW', **ref(result_path), 'request_path': str(run_dir / 'review_request.json'),
              'request_sha256': l6.digest(run_dir / 'review_request.json'),
              'invocation_report_path': str(invocation_path), 'invocation_report_sha256': l6.digest(invocation_path)}
    _, result = l6.reviewer.checked_invocation(source)
    report, reservation = read(invocation_path), read(run_dir / 'reviewer_reservation.json')
    expected = [{key: a[key] for key in ('role', 'path', 'sha256')} for a in request['artifacts']]
    if (report['reviewer_mode'] != 'CODEX_CLI' or report['reviewer_process_started'] is not True
            or report['attached_images'] != expected or reservation['request'] != ref(run_dir / 'review_request.json')
            or reservation['initial_contract'] != ref(run_dir / 'initial.json')
            or datetime.fromisoformat(report['started_at']) < datetime.fromisoformat(reservation['created_at'])):
        raise ValueError('actual Reviewer invocation/attachments differ')
    bound.check_result(run_dir, 'geometry', request, result, run_dir / 'review_result.json', run_dir / 'review_invocation.json')
    validate_action(result)
    return result


def finish(run_dir, status, reason, result=None, error=None):
    guard(run_dir)
    renderer = l6.available_report(run_dir / 'renderer_invocation.json')
    reviewer = l6.available_report(run_dir / 'review_invocation.json')
    initial = read(run_dir / 'initial.json')
    state = {'version': 'l7-m1.0', 'run_id': run_dir.name, 'state': status,
             'terminal': status != 'UNRESOLVED', 'reason': reason, 'finished_at': l6.now(),
             'initial_contract': ref(run_dir / 'initial.json'), 'review_verdict': result['verdict'] if result else None,
             'actionable': validate_action(result) if result else False, 'dispatches': 0,
             'errors': [str(error)] if error else [], **budgets(run_dir)}
    usage = {'run_id': run_dir.name, 'renderer': {'backend': 'Blender', **initial['renderer'],
              'invocations': int(renderer['process_started']) if 'process_started' in renderer else
                             (None if (run_dir / 'renderer_reservation.json').exists() else 0),
              'duration_seconds': renderer.get('duration_seconds'), 'render_engine': diagnostic.CONFIG['engine']},
             'frontier': {'provider': 'OpenAI', 'auth_mode': reviewer.get('auth_mode'),
              'invocations': int(reviewer['reviewer_process_started']) if 'reviewer_process_started' in reviewer else
                             (None if (run_dir / 'reviewer_reservation.json').exists() else 0),
              'duration_seconds': reviewer.get('duration_seconds'),
              **{k: None for k in ('requested_model', 'requested_reasoning_effort', 'actual_model', 'actual_reasoning_effort',
                                   'input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_tokens', 'reported_credits')},
              'unavailable_reason': 'Unobserved existing Reviewer telemetry; no CLI overrides requested.'},
             'comfy': {'invocations': 0}, 'automatic_retries': 0, 'revision_dispatches': 0,
             'final_state': status, 'review_verdict': state['review_verdict'], 'budgets': budgets(run_dir)}
    write_once(run_dir / 'usage.json', usage)
    l6.worker.write_report(run_dir / 'state.json', state)
    if state['terminal']:
        names = ('initial', 'render_request', 'renderer_reservation', 'renderer_invocation', 'render_manifest',
                 'review_request', 'reviewer_reservation', 'review_result', 'review_invocation', 'usage')
        records = {k: ref(run_dir / (k + '.json')) if (run_dir / (k + '.json')).exists() else None for k in names}
        records['review_instructions'] = ref(run_dir / 'review_instructions.md') if (run_dir / 'review_instructions.md').exists() else None
        if initial.get('session_binding'):
            records = {p.stem: ref(p) for p in run_dir.iterdir() if p.is_file() and p.name not in ('state.json', 'terminal.json')}
        write_once(run_dir / 'terminal.json', state | {'records': records, 'l6_input': initial['input']})
    return state


def run_bridge(run_id, executable=BLENDER, render_timeout=600, review_timeout=600, *, execute=False, session_binding=None, source_l6_run=None):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,48}', str(run_id)) or min(render_timeout, review_timeout) <= 0:
        raise ValueError('invalid run ID/timeouts')
    run_dir = ROOT / 'runs/l7' / run_id
    if execute and run_dir.exists():
        if (run_dir / 'terminal.json').exists():
            return {'status': 'ALREADY_TERMINAL', 'terminal': ref(run_dir / 'terminal.json')}
        raise ValueError('L7_RUN_ALREADY_EXISTS')
    if session_binding is not None:
        data, _, _ = bound.checked_parent(session_binding, execution=True)
        if data['child_ids']['bridge'] != run_id or source_l6_run is None:
            raise ValueError('bound bridge child/source identity required')
    checks = preflight(executable, source_l6_run=source_l6_run, session_binding=session_binding)
    if not execute:
        return checks
    output_root = (Path(read(Path(source_l6_run) / 'initial.json')['comfy_root']) / 'work/output/l7'
                   if session_binding is not None else OUTPUT_ROOT)
    if (output_root / run_id).exists():
        raise ValueError('external namespace exists')
    run_dir.parent.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir()
    initial = {'version': 'l7-m1.0', 'run_id': run_id, 'created_at': l6.now(), 'state': 'GEOMETRY_READY',
               'terminal': False, 'input': checks['input'], 'renderer': checks['renderer'], 'script': checks['script'],
               **budgets(run_dir)}
    if session_binding is not None:
        initial['session_binding'] = bound.child_binding(session_binding, 'bridge', run_dir, source_l6_run)
        initial['output_root'] = str(Path(read(Path(source_l6_run) / 'initial.json')['comfy_root']) / 'work/output/l7')
    write_once(run_dir / 'initial.json', initial)
    l6.worker.write_report(run_dir / 'state.json', initial | {'initial_contract': ref(run_dir / 'initial.json')})
    stage = 'RENDER_STAGE'
    try:
        write_once(run_dir / 'render_request.json', make_render_request(run_dir, initial))
        run_renderer(run_dir, render_timeout)
        stage = 'REVIEW_STAGE'
        prepare_review(run_dir)
        result = run_review(run_dir, review_timeout)
        return finish(run_dir, 'GEOMETRY_REVIEWED', 'VALID_GEOMETRY_VERDICT_NO_DISPATCH', result)
    except l6.StageFailure as exc:
        return finish(run_dir, exc.state, exc.reason, error=exc)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        # Reserved effects are never refunded. Uncertain/malformed Review cannot authorize actions.
        return finish(run_dir, 'UNRESOLVED' if stage == 'REVIEW_STAGE' else 'FAILED', stage, error=exc)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--preflight', action='store_true')
    mode.add_argument('--execute', action='store_true')
    parser.add_argument('--run-id', default='l7-preflight')
    parser.add_argument('--blender', type=Path, default=BLENDER)
    parser.add_argument('--render-timeout', type=int, default=600)
    parser.add_argument('--review-timeout', type=int, default=600)
    args = parser.parse_args(argv)
    try:
        result = run_bridge(args.run_id, args.blender, args.render_timeout, args.review_timeout, execute=args.execute)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get('state', result.get('status')) in ('PREFLIGHT_PASS', 'GEOMETRY_REVIEWED', 'ALREADY_TERMINAL') else 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('L7 BLOCKED: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
