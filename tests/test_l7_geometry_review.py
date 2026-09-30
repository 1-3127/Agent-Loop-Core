"""L7 policy/identity tests. Blender, Reviewer and Comfy effects are synthetic."""
import contextlib
import copy
import io
import json
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

from PIL import Image, ImageDraw
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'src'))
from scenario_a import l7_geometry_review as bridge
from scenario_a import l7_blender_diagnostic as diagnostic
import tests.test_l6_pipeline as baseline_tests


class GeometryBridgeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = baseline_tests.L6PipelineTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f, p = self.fixture, bridge.l6
        def embedded_geometry(role, path):
            if role != 'geometry':
                return
            report = p.read_json(path)
            plan = p.read_json(f.run_dir / 'geometry_plan.json')
            graph = {node: {'inputs': plan['patches'][node],
                           'is_changed': [p.digest(f.source if role == 'front' else f.comfy / f'work/input/l6/{f.run_id}/{role}.png')]}
                     for role, node in p.MAPPING.items()}
            payload = json.dumps({'asset': {'version': '2.0', 'extras': {'prompt': json.dumps(graph)}}}).encode()
            payload += b' ' * (-len(payload) % 4)
            data = struct.pack('<4sII', b'glTF', 2, 20 + len(payload)) + struct.pack('<I4s', len(payload), b'JSON') + payload
            output = Path(report['outputs'][0]['path']); output.write_bytes(data)
            report['outputs'][0].update(bytes=len(data), sha256=p.digest(output), declared_length=len(data))
            p.worker.write_report(path, report)
        f.worker_after = embedded_geometry
        self.assertEqual(f.run_fixture()['state'], 'GEOMETRY_READY')
        self.fixture.worker_mock.reset_mock()
        self.run_id = 'l7-test'
        self.run_dir = f.repo / 'runs/l7' / self.run_id
        self.executable = f.root / 'blender.exe'; self.executable.write_bytes(b'SYNTHETIC_EXECUTABLE_NOT_RUN')
        images = p.validate_manifest(p.read_json(f.run_dir / 'multiview_manifest.json'), f.run_dir)
        artifact = p.read_json(f.run_dir / 'geometry_execution.json')['artifact']
        for key, value in [('ROOT', f.repo), ('L6_DIR', f.run_dir), ('L6_RUN_ID', f.run_id),
                           ('L6_TERMINAL_SHA', p.digest(f.run_dir / 'terminal.json')),
                           ('GLB_SHA', artifact['sha256']), ('GLB_BYTES', artifact['bytes']),
                           ('REFERENCE_SHAS', tuple(a['sha256'] for a in images)),
                           ('OUTPUT_ROOT', f.comfy / 'work/output/l7')]:
            patch = mock.patch.object(bridge, key, value); patch.start(); self.addCleanup(patch.stop)
        self.renderer = mock.patch.object(bridge.subprocess, 'run', side_effect=self.fake_render).start()
        self.reviewer = mock.patch.object(p.reviewer, 'review_once', side_effect=self.fake_review).start()
        self.addCleanup(mock.patch.stopall)
        self.verdict = 'PASS'
        self.action = None
        self.render_mutation = None
        self.review_mutation = None
        self.return_code = 0

    def fake_render(self, command, **kwargs):
        p = bridge.l6
        self.assertIn('--background', command); self.assertIn('--factory-startup', command)
        self.assertNotIn('--python-expr', command)
        request_path = Path(command[-1]); request = p.read_json(request_path)
        output = Path(request['output_dir']); output.mkdir(parents=True)
        outputs = []
        for azimuth, role in zip((0, 90, 180, 270), diagnostic.ROLES):
            path = output / (role + '.png')
            image = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
            ImageDraw.Draw(image).rectangle((100, 100, 400, 400), fill=(160, 170, 180, 255))
            image.save(path)
            outputs.append(p.png_identity(path, role) | {'azimuth': azimuth, 'ortho_scale': 2.4})
        manifest = {'version': 'l7-m1.0', 'run_id': self.run_id, 'source_l6_run_id': bridge.L6_RUN_ID,
                    'source_glb': request['source_glb'], 'render_request': p.reference(request_path),
                    'blender_executable': str(self.executable), 'blender_version': bridge.BLENDER_VERSION,
                    'config': diagnostic.CONFIG, 'mesh_count': 1, 'object_count': 1,
                    'bounding_box': {'min': [-1, -1, -1], 'max': [1, 1, 1], 'center': [0, 0, 0],
                                     'extents': [2, 2, 2], 'maximum_dimension': 2}, 'outputs': outputs}
        if self.render_mutation:
            self.render_mutation(manifest)
        p.write_once(Path(request['manifest_path']), manifest)
        return SimpleNamespace(returncode=self.return_code, stdout='SYNTHETIC_RENDER', stderr='')

    def fake_review(self, request_path, result_path, report_path, **kwargs):
        p = bridge.l6
        request = p.read_json(request_path)
        actions = {'PASS': {'code': 'NONE', 'target': None},
                   'REVISE': {'code': 'REGENERATE_GEOMETRY', 'target': 'geometry'},
                   'HUMAN_REQUIRED': {'code': 'HUMAN_REQUIRED', 'target': None}}
        result = {'review_version': '0.3', 'review_id': request['review_id'], 'stage': request['stage'],
                  'source_result': request['source_result'], 'artifacts': request['artifacts'], 'verdict': self.verdict,
                  'blocking_issues': ['synthetic blocker'] if self.verdict == 'REVISE' else [],
                  'observations': ['Synthetic local fixture; no actual semantic review.'],
                  'suggested_action': self.action or actions[self.verdict]}
        p.write_once(result_path, result)
        report = {'review_id': request['review_id'], 'reviewer_mode': 'CODEX_CLI', 'invocation_status': 'SUCCESS',
                  'request_sha256': p.digest(request_path), 'result_sha256': p.digest(result_path),
                  'result_path': str(result_path), 'verdict': self.verdict, 'reviewer_process_started': True,
                  'auth_mode': 'SYNTHETIC_TEST', 'started_at': p.now(), 'finished_at': p.now(), 'duration_seconds': 0.01,
                  'attached_images': [{k: a[k] for k in ('role', 'path', 'sha256')} for a in request['artifacts']]}
        if self.review_mutation:
            self.review_mutation(request, result, report)
        p.write_once(report_path, report)
        return report

    def execute(self):
        return bridge.run_bridge(self.run_id, self.executable, 1, 1, execute=True)

    def assert_effects(self, render=1, review=1):
        self.assertEqual(self.renderer.call_count, render)
        self.assertEqual(self.reviewer.call_count, review)
        self.fixture.worker_mock.assert_not_called()
        self.fixture.network.assert_not_called()

    def test_preflight_and_default_callable_effect_free(self):
        self.assertEqual(bridge.run_bridge(self.run_id, self.executable)['status'], 'PREFLIGHT_PASS')
        self.assertFalse(self.run_dir.exists()); self.assert_effects(0, 0)

    def test_cli_help_default_preflight_effect_free(self):
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as code: bridge.main(['--help'])
            self.assertEqual(code.exception.code, 0)
            for mode in ([], ['--preflight']):
                self.assertEqual(bridge.main(mode + ['--blender', str(self.executable)]), 0)
        self.assert_effects(0, 0)

    def test_blender_argument_parsing_and_command(self):
        path = diagnostic.parse_args(['--request', 'request.json']).request
        self.assertEqual(path, Path('request.json'))
        self.execute()
        command = bridge.render_command(self.run_dir)
        self.assertEqual(command[-2:], ['--request', str(self.run_dir / 'render_request.json')])
        self.assertIn(str(bridge.SCRIPT), command); self.assertNotIn('--python-expr', command)

    def test_exact_l6_input_and_embedded_hashes(self):
        item = bridge.validate_l6()
        self.assertEqual(item['artifact']['sha256'], bridge.GLB_SHA)
        self.assertEqual(len(item['references']), 4)
        self.assert_effects(0, 0)

    def test_mutated_glb_rejected_no_effect(self):
        path = Path(bridge.validate_l6()['artifact']['path']); path.write_bytes(path.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'GLB identity'): self.execute()
        self.assert_effects(0, 0)

    def test_wrong_glb_pin_rejected(self):
        with mock.patch.object(bridge, 'GLB_SHA', '0' * 64):
            with self.assertRaises(ValueError): self.execute()
        self.assert_effects(0, 0)

    def test_mutated_reference_rejected_no_effect(self):
        path = Path(bridge.validate_l6()['references'][1]['path']); path.write_bytes(b'broken PNG')
        with self.assertRaises(ValueError): self.execute()
        self.assert_effects(0, 0)

    def test_wrong_terminal_identity_rejected(self):
        with mock.patch.object(bridge, 'L6_TERMINAL_SHA', '0' * 64):
            with self.assertRaisesRegex(ValueError, 'terminal identity'): self.execute()
        self.assert_effects(0, 0)

    def test_pass_records_exact_eight_attachments_and_stops(self):
        state = self.execute(); self.assertEqual(state['state'], 'GEOMETRY_REVIEWED')
        request = bridge.read(self.run_dir / 'review_request.json')
        self.assertEqual([a['role'] for a in request['artifacts']], list(bridge.ROLES))
        self.assertEqual(len(request['artifacts']), 8)
        self.assertEqual(state['dispatches'], 0); self.assert_effects()
        self.assertEqual(bridge.read(self.run_dir / 'initial.json')['reviewer_budget']['consumed'], 0)

    def test_revise_geometry_records_diagnostic_no_dispatch(self):
        self.verdict = 'REVISE'; state = self.execute()
        self.assertEqual(state['state'], 'GEOMETRY_REVIEWED'); self.assertTrue(state['actionable'])
        self.assertEqual(state['dispatches'], 0); self.assert_effects()

    def test_revise_each_generated_view_allowed_no_dispatch(self):
        # Policy validation only; one fixture run still consumes at most one render/review.
        for target in ('right', 'left', 'back'):
            self.assertTrue(bridge.validate_action({'verdict': 'REVISE', 'blocking_issues': ['blocker'],
                                                   'suggested_action': {'code': 'REGENERATE_VIEW', 'target': target}}))
        self.verdict = 'REVISE'; self.action = {'code': 'REGENERATE_VIEW', 'target': 'left'}
        self.assertEqual(self.execute()['state'], 'GEOMETRY_REVIEWED'); self.assert_effects()

    def test_human_required_valid_not_actionable(self):
        self.verdict = 'HUMAN_REQUIRED'; state = self.execute()
        self.assertEqual(state['state'], 'GEOMETRY_REVIEWED'); self.assertFalse(state['actionable'])
        self.assert_effects()

    def test_front_regeneration_rejected(self):
        self.verdict = 'REVISE'; self.action = {'code': 'REGENERATE_VIEW', 'target': 'front'}
        self.assertEqual(self.execute()['state'], 'UNRESOLVED'); self.assert_effects()

    def test_geometry_action_wrong_target_rejected(self):
        self.verdict = 'REVISE'; self.action = {'code': 'REGENERATE_GEOMETRY', 'target': 'left'}
        self.assertEqual(self.execute()['state'], 'UNRESOLVED'); self.assert_effects()

    def test_malformed_action_and_pass_action_rejected(self):
        for verdict, action in [('PASS', {'code': 'REGENERATE_GEOMETRY', 'target': 'geometry'}),
                                ('REVISE', {'code': 'UNKNOWN', 'target': 'geometry'}),
                                ('HUMAN_REQUIRED', {'code': 'NONE', 'target': None})]:
            with self.assertRaises(ValueError):
                bridge.validate_action({'verdict': verdict, 'blocking_issues': [], 'suggested_action': action})
        self.assert_effects(0, 0)

    def test_missing_diagnostic_view_rejected(self):
        self.render_mutation = lambda m: m['outputs'].pop()
        self.assertEqual(self.execute()['state'], 'FAILED'); self.assert_effects(1, 0)

    def test_duplicate_diagnostic_role_rejected(self):
        self.render_mutation = lambda m: m['outputs'][1].update(role=diagnostic.ROLES[0])
        self.assertEqual(self.execute()['state'], 'FAILED'); self.assert_effects(1, 0)

    def test_invalid_png_rejected(self):
        self.render_mutation = lambda m: Path(m['outputs'][0]['path']).write_bytes(b'not PNG')
        self.assertEqual(self.execute()['state'], 'FAILED'); self.assert_effects(1, 0)

    def test_wrong_dimensions_and_namespace_rejected(self):
        self.render_mutation = lambda m: m['outputs'][0].update(path=m['outputs'][1]['path'])
        self.assertEqual(self.execute()['state'], 'FAILED'); self.assert_effects(1, 0)

    def test_non_512_render_rejected(self):
        def resize_fixture(manifest):
            item = manifest['outputs'][0]
            Image.new('RGBA', (256, 256), (170, 170, 170, 255)).save(item['path'])
            item.update(bridge.l6.png_identity(item['path'], item['role']))
        self.render_mutation = resize_fixture
        self.assertEqual(self.execute()['state'], 'FAILED'); self.assert_effects(1, 0)

    def test_unequal_camera_scale_rejected(self):
        self.render_mutation = lambda m: m['outputs'][1].update(ortho_scale=3.0)
        self.assertEqual(self.execute()['state'], 'FAILED'); self.assert_effects(1, 0)

    def test_renderer_reservation_bypass_no_second_process(self):
        def probe(manifest):
            with self.assertRaisesRegex(ValueError, 'ALREADY_RESERVED'):
                bridge.run_renderer(self.run_dir, 1)
            with self.assertRaisesRegex(ValueError, 'ALREADY_RESERVED'):
                bridge.reserve(self.run_dir, 'renderer', self.run_dir / 'alternate_render.json')
        self.render_mutation = probe
        self.assertEqual(self.execute()['state'], 'GEOMETRY_REVIEWED'); self.assert_effects()

    def test_changed_attachment_blocks_review(self):
        original = bridge.prepare_review
        def prepare_then_mutate(run_dir):
            request = original(run_dir)
            Path(request['artifacts'][-1]['path']).write_bytes(b'changed')
            return request
        with mock.patch.object(bridge, 'prepare_review', side_effect=prepare_then_mutate):
            self.assertEqual(self.execute()['state'], 'UNRESOLVED')
        self.assert_effects(1, 0)

    def test_invocation_attachment_order_mismatch(self):
        self.review_mutation = lambda q, r, i: i['attached_images'].reverse()
        self.assertEqual(self.execute()['state'], 'UNRESOLVED'); self.assert_effects()

    def test_result_hash_mismatch_is_unresolved(self):
        self.review_mutation = lambda q, r, i: i.update(result_sha256='0' * 64)
        self.assertEqual(self.execute()['state'], 'UNRESOLVED'); self.assert_effects()

    def test_renderer_failure_no_reviewer_retry(self):
        self.return_code = 1
        self.assertEqual(self.execute()['state'], 'FAILED'); self.assert_effects(1, 0)

    def test_renderer_timeout_stops_uncertain_no_refund(self):
        self.renderer.side_effect = bridge.subprocess.TimeoutExpired('synthetic', 1)
        state = self.execute(); self.assertEqual(state['state'], 'UNRESOLVED')
        self.assertEqual(state['renderer_budget']['consumed'], 1); self.assert_effects(1, 0)

    def test_review_timeout_no_second_call(self):
        self.review_mutation = lambda q, r, i: i.update(invocation_status='UNRESOLVED')
        self.assertEqual(self.execute()['state'], 'UNRESOLVED'); self.assert_effects()

    def test_review_malformed_marked_unresolved(self):
        self.review_mutation = lambda q, r, i: i.update(invocation_status='FAILED', validation_error='malformed')
        self.assertEqual(self.execute()['state'], 'UNRESOLVED'); self.assert_effects()

    def test_reservation_bypass_blocked_with_alternate_identity(self):
        original = self.fake_review
        def probe(*args, **kwargs):
            for path in (self.run_dir / 'review_request.json', self.run_dir / 'alternate_request.json'):
                with self.assertRaisesRegex(ValueError, 'ALREADY_RESERVED'):
                    bridge.reserve(self.run_dir, 'reviewer', path)
            with self.assertRaisesRegex(ValueError, 'ALREADY_RESERVED'):
                bridge.run_review(self.run_dir, 1)
            return original(*args, **kwargs)
        self.reviewer.side_effect = probe
        self.assertEqual(self.execute()['state'], 'GEOMETRY_REVIEWED'); self.assert_effects()

    def test_terminal_reentry_blocks_render_review_and_writes(self):
        self.execute(); before = {f.name: bridge.l6.digest(f) for f in self.run_dir.iterdir()}
        self.assertEqual(self.execute()['status'], 'ALREADY_TERMINAL')
        for probe in (lambda: bridge.run_renderer(self.run_dir, 1), lambda: bridge.run_review(self.run_dir, 1),
                      lambda: bridge.finish(self.run_dir, 'FAILED', 'probe'), lambda: bridge.prepare_review(self.run_dir)):
            with self.assertRaisesRegex(ValueError, 'ALREADY_TERMINAL'): probe()
        self.assertEqual(before, {f.name: bridge.l6.digest(f) for f in self.run_dir.iterdir()}); self.assert_effects()

    def test_incomplete_namespace_no_resume(self):
        self.run_dir.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'L7_RUN_ALREADY_EXISTS'): self.execute()
        self.assert_effects(0, 0)

    def test_usage_null_budgets_and_comfy_zero(self):
        self.execute(); usage = bridge.read(self.run_dir / 'usage.json')
        self.assertEqual(usage['comfy']['invocations'], 0)
        for key in ('requested_model', 'actual_model', 'input_tokens', 'reported_credits'):
            self.assertIsNone(usage['frontier'][key])
        for item in usage['budgets'].values():
            self.assertEqual(item, {'limit': 1, 'consumed': 1, 'remaining': 0})
        self.assertEqual(usage['revision_dispatches'], 0); self.assert_effects()


if __name__ == '__main__':
    unittest.main()
