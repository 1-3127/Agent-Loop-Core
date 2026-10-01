"""Bound L7 evidence contract; synthetic fixtures and zero correction effects."""
import copy
from pathlib import Path
import sys
import unittest
from unittest import mock

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'src'))
from scenario_a import l7_feedback_controller as controller
from scenario_a import l7_geometry_review as bridge
from tests import test_session_scenario_binding as session_tests
from tests import test_l7_feedback_controller as feedback_tests


class ReviewStreamContractTests(unittest.TestCase):
    def setUp(self):
        self.s = session_tests.SessionScenarioTests()
        self.s.setUp()
        self.addCleanup(self.s.doCleanups)
        self.s.geometry_fixture()
        self.s.g.verdict = 'REVISE'
        self.s.g.action = {'code': 'REGENERATE_GEOMETRY', 'target': 'geometry'}
        original = self.s.g.review_mutation
        def observability(request, result, report):
            original(request, result, report)
            for name, raw in (('stdout', b'Synthetic REVISE result\r\n'),
                              ('stderr', b'Synthetic diagnostic\r\n')):
                path = Path(report['result_path']).with_name('review_invocation.json.' + name + '.txt')
                report[name + '_evidence'] = controller.l6.reviewer._stream_evidence(raw, path, True)
        self.s.g.review_mutation = observability
        self.assertEqual(self.s.execute_bridge()['state'], 'GEOMETRY_REVIEWED')
        self.source = self.s.f.repo / 'runs/l7' / self.s.ids['bridge']
        self.terminal = controller.read(self.source / 'terminal.json')
        self.before = {p.name: p.read_bytes() for p in self.source.iterdir() if p.is_file()}
        for effect in (self.s.f.worker_mock, self.s.renderer, self.s.reviewer):
            effect.reset_mock()
            effect.side_effect = AssertionError('Correction production dispatch forbidden')

    def validate(self):
        return controller.validate_source(self.source, self.s.parent)

    def save_terminal(self):
        controller.l6.worker.write_report(self.source / 'terminal.json', self.terminal)

    def zero_effects(self):
        for effect in (self.s.f.worker_mock, self.s.renderer, self.s.reviewer, self.s.f.network):
            effect.assert_not_called()
        self.assertFalse((self.source.parent / self.s.ids['correction']).exists())

    def rejected(self):
        with self.assertRaises((ValueError, OSError)):
            self.validate()
        self.zero_effects()

    def test_current_observability_records_and_checked_refs(self):
        with mock.patch.object(controller.l6.reviewer, 'checked_ref', wraps=controller.l6.reviewer.checked_ref) as check:
            source = self.validate()
        self.assertEqual(source['verdict'], 'REVISE')
        for name in ('stdout', 'stderr'):
            item = self.terminal['records']['review_invocation.json.' + name]
            self.assertEqual(Path(item['path']).suffix, '.txt')
            self.assertIn(mock.call(item), check.call_args_list)
        self.zero_effects()

    def test_final2_structure_canonical_preflight_action_and_identity(self):
        # Safe synthetic reproduction of every Final-2 terminal record key.
        expected = {'geometry_criteria', 'initial', 'renderer_invocation', 'renderer_reservation',
                    'render_manifest', 'render_request', 'reviewer_reservation', 'review_instructions',
                    'review_invocation', 'review_invocation.json.stderr', 'review_invocation.json.stdout',
                    'review_request', 'review_result', 'review_result_coverage', 'session_binding', 'usage'}
        self.assertEqual(set(self.terminal['records']), expected)
        self.assertFalse((self.source / 'review_invocation.json.stderr.json').exists())
        checks = controller.run_feedback(self.s.ids['correction'], self.source, self.s.f.comfy,
            self.s.g.executable, session_binding=self.s.parent)
        self.assertEqual(checks['status'], 'PREFLIGHT_PASS')
        self.assertEqual(checks['action'], {'code': 'REGENERATE_GEOMETRY', 'target': 'geometry'})
        self.assertEqual(checks['source']['run_id'], self.s.ids['bridge'])
        self.assertEqual(checks['source']['terminal'], controller.ref(self.source / 'terminal.json'))
        self.assertEqual(checks['revision_seed'], checks['source']['previous_geometry_seed'] + 1)
        self.assertEqual(checks['effects'], {'comfy': 0, 'blender': 0, 'frontier': 0})
        self.assertEqual(self.before, {p.name: p.read_bytes() for p in self.source.iterdir() if p.is_file()})
        self.zero_effects()

    def test_missing_stream_rejected(self):
        (self.source / 'review_invocation.json.stderr.txt').unlink()
        self.rejected()

    def test_mutated_stream_rejected(self):
        (self.source / 'review_invocation.json.stderr.txt').write_bytes(b'mutated')
        self.rejected()

    def test_wrong_directory_same_bytes_rejected(self):
        other = self.s.f.root / 'other.txt'
        other.write_bytes((self.source / 'review_invocation.json.stderr.txt').read_bytes())
        self.terminal['records']['review_invocation.json.stderr'] = controller.ref(other)
        self.save_terminal()
        self.rejected()

    def test_wrong_same_directory_file_rejected(self):
        self.terminal['records']['review_invocation.json.stderr'] = controller.ref(self.source / 'review_invocation.json.stdout.txt')
        self.save_terminal()
        self.rejected()

    def test_forged_extension_even_rehashed_and_only_file_rejected(self):
        old = self.source / 'review_invocation.json.stderr.txt'
        forged = self.source / 'review_invocation.json.stderr.json'
        old.rename(forged)
        self.terminal['records']['review_invocation.json.stderr'] = controller.ref(forged)
        self.save_terminal()
        self.rejected()

    def test_duplicate_stem_cannot_hide_evidence(self):
        duplicate = self.source / 'review_invocation.json.stderr.json'
        duplicate.write_bytes(b'{}')
        self.rejected()

    def test_unrecorded_evidence_cannot_be_ignored(self):
        (self.source / 'unexpected.json').write_bytes(b'{}')
        self.rejected()

    def test_wrong_stream_hash_rejected(self):
        self.terminal['records']['review_invocation.json.stderr']['sha256'] = '0' * 64
        self.save_terminal()
        self.rejected()

    def test_ordinary_json_hash_still_checked(self):
        (self.source / 'usage.json').write_bytes(b'{}')
        self.rejected()

    def test_instructions_md_and_hash_still_checked(self):
        self.assertEqual(self.terminal['records']['review_instructions'], controller.ref(self.source / 'review_instructions.md'))
        self.validate()
        (self.source / 'review_instructions.md').write_text('mutated', encoding='utf-8')
        self.rejected()

    def test_wrong_terminal_identity_rejected(self):
        self.terminal['run_id'] = 'wrong-run'
        self.save_terminal()
        self.rejected()

    def test_wrong_parent_binding_rejected(self):
        parent = copy.deepcopy(self.s.parent)
        parent['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            controller.validate_source(self.source, parent)
        self.zero_effects()

    def test_no_stream_bound_fixture_remains_compatible(self):
        # Earlier bound fixtures had no observability files.
        for name in ('stdout', 'stderr'):
            (self.source / ('review_invocation.json.' + name + '.txt')).unlink()
            del self.terminal['records']['review_invocation.json.' + name]
        self.save_terminal()
        self.assertEqual(self.validate()['verdict'], 'REVISE')
        self.zero_effects()


class LegacyStreamContractTests(unittest.TestCase):
    def test_legacy_unbound_required_set_remains_exact(self):
        fixture = feedback_tests.FeedbackControllerTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        source = controller.validate_source(fixture.source)
        self.assertEqual(source['verdict'], 'REVISE')
        checks = controller.run_feedback(fixture.run_id, fixture.source, fixture.comfy, fixture.fixture.executable)
        self.assertEqual(checks['status'], 'PREFLIGHT_PASS')
        fixture.counts(0, 0, 0)
        self.assertEqual(fixture.source_snapshot, {p.name: p.read_bytes() for p in fixture.source.iterdir() if p.is_file()})


if __name__ == '__main__':
    unittest.main()
