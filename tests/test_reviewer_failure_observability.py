"""Synthetic Reviewer stream evidence; no production Reviewer or Worker calls."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from core import result_review_adapter as reviewer


class ReviewerFailureObservabilityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.request_path = self.root / 'request.json'
        self.result_path = self.root / 'result.json'
        self.report_path = self.root / 'invocation.json'
        def fixture(name, data):
            path = self.root / name
            path.write_bytes(data)
            return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest()}
        source = fixture('source.json', b'{}')
        instructions = fixture('instructions.md', 'Synthetic review only. \uac80\uc99d'.encode('utf-8'))
        artifact = dict(fixture('image.png', b'synthetic-image'), role='front', media_type='image/png')
        self.request = dict(request_version='0.2', run_id='synthetic-run', review_id='synthetic-review',
                            stage='multiview', output_kind='image', source_result=source,
                            work_order=source, worker_report=source, artifacts=[artifact],
                            instruction_file=instructions, context={'synthetic': True})
        self.request_path.write_text(json.dumps(self.request), encoding='utf-8')
        self.result = dict(review_version='0.3', review_id=self.request['review_id'], stage=self.request['stage'],
                           source_result=source, artifacts=[artifact], verdict='PASS', blocking_issues=[],
                           observations=['Synthetic visible evidence'], suggested_action={'code': 'NONE', 'target': None})
        self.auth = mock.patch.object(reviewer, 'auth_mode', return_value='CHATGPT_ACCOUNT').start()
        self.addCleanup(mock.patch.stopall)

    def invoke(self, stdout=b'', stderr=b'', code=1, exception=None, side_effect=None):
        with mock.patch.object(reviewer.subprocess, 'run',
                               return_value=subprocess.CompletedProcess([], code, stdout, stderr),
                               side_effect=side_effect or exception) as dispatch:
            report = reviewer.review_once(self.request_path, self.result_path, self.report_path,
                                          timeout=37, workspace=self.root)
        dispatch.assert_called_once()
        command, = dispatch.call_args.args
        options = dispatch.call_args.kwargs
        self.assertEqual(options['timeout'], 37)
        self.assertTrue(options['capture_output'])
        self.assertNotIn('text', options)
        expected_prompt = 'Synthetic review only. \uac80\uc99d\n\nREQUEST JSON:\n' + json.dumps(self.request, ensure_ascii=False, indent=2)
        self.assertEqual(options['input'], expected_prompt.replace('\n', os.linesep).encode('utf-8'))
        self.assertEqual(command, ['codex', 'exec', '--ephemeral', '--skip-git-repo-check', '--sandbox',
                                  'read-only', '--output-schema', str(reviewer.SCHEMA), '-C', str(self.root),
                                  '-i', self.request['artifacts'][0]['path'], '-'])
        self.assertEqual(report, json.loads(self.report_path.read_text(encoding='utf-8')))
        self.assertEqual(report['request_sha256'], reviewer.digest(self.request_path))
        self.assertEqual(report['review_id'], self.request['review_id'])
        return report

    def evidence(self, report, name, raw, complete=True):
        record = report[name + '_evidence']
        data = Path(record['path']).read_bytes()
        self.assertEqual(record['raw_bytes'], len(raw))
        self.assertEqual(record['raw_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(record['sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual(record['bytes'], len(data))
        self.assertEqual(record['capture_complete'], complete)
        if complete:
            decoded = raw.decode('utf-8', errors='replace').replace('\r\n', '\n').replace('\r', '\n')
            self.assertEqual(report[name + '_sha256'], hashlib.sha256(decoded.encode()).hexdigest())
        return record, data.decode('utf-8')

    def test_exit1_historical_like_failure_is_readable_and_stays_failed(self):
        raw = b'Synthetic runtime failure: connection unavailable\r\n'
        report = self.invoke(stderr=raw)
        self.assertEqual(report['invocation_status'], 'FAILED')
        self.assertEqual(report['process_exit_code'], 1)
        self.assertTrue(report['reviewer_process_started'])
        self.assertEqual(self.result_path.read_bytes(), b'')
        meta, text = self.evidence(report, 'stderr', raw)
        self.assertIn('connection unavailable', text)
        self.assertFalse(meta['redacted'])
        self.assertFalse(meta['truncated'])
        self.assertFalse(meta['decode_replacement'])
        self.assertEqual(self.evidence(report, 'stdout', b'')[1], '')

    def test_success_pass_revise_and_human_preserve_result_and_authority(self):
        for verdict, action, blockers in [('PASS', {'code': 'NONE', 'target': None}, []),
                                         ('REVISE', {'code': 'REGENERATE_VIEW', 'target': 'right'}, ['Synthetic blocker']),
                                         ('HUMAN_REQUIRED', {'code': 'HUMAN_REQUIRED', 'target': None}, [])]:
            with self.subTest(verdict=verdict):
                self.result_path = self.root / (verdict + '-result.json')
                self.report_path = self.root / (verdict + '-invocation.json')
                result = dict(self.result, verdict=verdict, suggested_action=action, blocking_issues=blockers)
                raw = (json.dumps(result, ensure_ascii=False, indent=2) + '\r\n').encode()
                report = self.invoke(stdout=raw, code=0)
                self.assertEqual(report['invocation_status'], 'SUCCESS')
                self.assertEqual(report['verdict'], verdict)
                expected_bytes = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').replace('\n', os.linesep).encode()
                self.assertEqual(self.result_path.read_bytes(), expected_bytes)
                self.assertEqual(report['result_sha256'], reviewer.digest(self.result_path))
                source = dict(kind='RESULT_REVIEW', path=str(self.result_path), sha256=reviewer.digest(self.result_path),
                              request_path=str(self.request_path), request_sha256=reviewer.digest(self.request_path),
                              invocation_report_path=str(self.report_path), invocation_report_sha256=reviewer.digest(self.report_path))
                self.assertEqual(reviewer.checked_invocation(source), (self.request, result))
                self.evidence(report, 'stdout', raw)
                self.evidence(report, 'stderr', b'')

    def test_secret_redaction_both_streams_retains_raw_identity(self):
        secrets = ['synthetic-api-value-123', 'synthetic-bearer-456', 'synthetic-cookie-789',
                   'synthetic-password-012', 'synthetic-env-345', 'synthetic-access-678',
                   'synthetic-refresh-901', 'synthetic-url-234', 'synthetic-private-567',
                   'sk-syntheticStandaloneSecret123', 'eyJsynthetic.payload.signature', 'synthetic-basic-890']
        text = ('OPENAI_API_KEY=' + secrets[0] + '\nAuthorization: Bearer ' + secrets[1] +
                '\nCookie: session=' + secrets[2] + '; flag=true\npassword: ' + secrets[3] +
                '\nBare inherited value ' + secrets[4] + '\nauth.json payload {"access_token": "' + secrets[5] +
                '", "refresh_token": "' + secrets[6] + '"}\nhttps://user:' + secrets[7] +
                '@example.invalid\n-----BEGIN PRIVATE KEY-----\n' + secrets[8] +
                '\n-----END PRIVATE KEY-----\n' + secrets[9] + '\n' + secrets[10] + '\nBasic ' + secrets[11])
        raw = text.encode()
        with mock.patch.dict(os.environ, {'SYNTHETIC_DIAGNOSTIC_TOKEN': secrets[4]}):
            report = self.invoke(stdout=raw, stderr=raw)
        for name in ('stdout', 'stderr'):
            meta, saved = self.evidence(report, name, raw)
            self.assertTrue(meta['redacted'])
            self.assertIn('[REDACTED]', saved)
            for secret in secrets:
                self.assertNotIn(secret, saved)
                self.assertNotIn(secret, self.report_path.read_text(encoding='utf-8'))
        self.assertEqual(self.result_path.read_bytes(), b'')

    def test_empty_streams_have_deterministic_identity(self):
        report = self.invoke()
        for name in ('stdout', 'stderr'):
            meta, text = self.evidence(report, name, b'')
            self.assertEqual(text, '')
            self.assertEqual(meta['sanitized_bytes'], 0)
            self.assertFalse(meta['redacted'] or meta['truncated'] or meta['decode_replacement'])

    def test_non_utf8_raw_hash_differs_from_legacy_hash_and_marks_replacement(self):
        raw = b'cause: \xff\xfe\r\n'
        report = self.invoke(stderr=raw)
        meta, text = self.evidence(report, 'stderr', raw)
        self.assertTrue(meta['decode_replacement'])
        self.assertEqual(meta['encoding'], 'utf-8')
        self.assertEqual(meta['decode_errors'], 'replace')
        self.assertIn('\ufffd', text)
        self.assertNotEqual(meta['raw_sha256'], report['stderr_sha256'])

    def test_literal_replacement_character_does_not_claim_decode_loss(self):
        raw = 'valid \ufffd'.encode('utf-8')
        report = self.invoke(stderr=raw)
        self.assertFalse(self.evidence(report, 'stderr', raw)[0]['decode_replacement'])

    def test_cap_sanitizes_before_truncating_and_keeps_utf8_boundary(self):
        raw = ('\uac00' * 21844 + ' sk-syntheticBoundarySecret123 ' + '\uac00' * 100).encode()
        report = self.invoke(stderr=raw)
        meta, text = self.evidence(report, 'stderr', raw)
        self.assertTrue(meta['truncated'] and meta['redacted'])
        self.assertLessEqual(meta['bytes'], 65536)
        self.assertEqual(meta['cap_bytes'], 65536)
        self.assertGreater(meta['sanitized_bytes'], meta['bytes'])
        self.assertNotIn('syntheticBoundarySecret123', text)
        self.assertEqual(meta['bytes'], len(text.encode('utf-8')))

    def test_large_valid_result_uses_full_stdout_despite_evidence_cap(self):
        result = dict(self.result, observations=['x' * 70000])
        raw = json.dumps(result).encode()
        report = self.invoke(stdout=raw, code=0)
        self.assertEqual(report['invocation_status'], 'SUCCESS')
        self.assertEqual(json.loads(self.result_path.read_text()), result)
        self.assertTrue(self.evidence(report, 'stdout', raw)[0]['truncated'])

    def test_invalid_success_output_remains_failed(self):
        raw = b'not JSON'
        report = self.invoke(stdout=raw, code=0)
        self.assertEqual(report['invocation_status'], 'FAILED')
        self.assertIn('validation_error', report)
        self.assertEqual(self.evidence(report, 'stdout', raw)[1], 'not JSON')
        self.assertEqual(self.result_path.read_bytes(), b'')

    def test_changed_result_identity_remains_rejected(self):
        result = dict(self.result, review_id='wrong-review')
        report = self.invoke(stdout=json.dumps(result).encode(), code=0)
        self.assertEqual(report['invocation_status'], 'FAILED')
        self.assertEqual(report['validation_error'], 'review source identity differs')

    def test_timeout_partial_evidence_stays_unresolved_and_never_retries(self):
        raw = b'synthetic timeout cause\xff'
        report = self.invoke(exception=subprocess.TimeoutExpired('synthetic', 37, output=b'partial', stderr=raw))
        self.assertEqual(report['invocation_status'], 'UNRESOLVED')
        self.assertIsNone(report['process_exit_code'])
        self.assertTrue(report['reviewer_process_started'])
        self.assertIn('synthetic timeout cause', self.evidence(report, 'stderr', raw, complete=False)[1])
        self.evidence(report, 'stdout', b'partial', complete=False)

    def test_launch_failure_stays_failed_and_capture_is_incomplete(self):
        report = self.invoke(exception=OSError('synthetic launch failure'))
        self.assertEqual(report['invocation_status'], 'FAILED')
        self.assertFalse(report['reviewer_process_started'])
        self.assertIsNone(report['process_exit_code'])
        self.evidence(report, 'stdout', b'', complete=False)
        self.evidence(report, 'stderr', b'', complete=False)

    def test_evidence_collision_blocks_before_auth_or_dispatch(self):
        path = self.report_path.with_name(self.report_path.name + '.stderr.txt')
        path.write_bytes(b'protected')
        with mock.patch.object(reviewer.subprocess, 'run') as dispatch:
            with self.assertRaisesRegex(ValueError, 'refusing repeat'):
                reviewer.review_once(self.request_path, self.result_path, self.report_path)
        dispatch.assert_not_called()
        self.auth.assert_not_called()
        self.assertEqual(path.read_bytes(), b'protected')
        self.assertFalse(self.report_path.exists() or self.result_path.exists())

    def test_second_call_preserves_write_once_evidence(self):
        report = self.invoke(stderr=b'synthetic cause')
        before = {p: p.read_bytes() for p in self.root.iterdir()}
        with mock.patch.object(reviewer.subprocess, 'run') as dispatch:
            with self.assertRaisesRegex(ValueError, 'refusing repeat'):
                reviewer.review_once(self.request_path, self.result_path, self.report_path)
        dispatch.assert_not_called()
        self.assertEqual({p: p.read_bytes() for p in self.root.iterdir()}, before)

    def test_storage_failure_does_not_misreport_process_start_or_exit(self):
        with mock.patch.object(reviewer, '_stream_evidence', side_effect=PermissionError('synthetic storage failure')):
            report = self.invoke(stderr=b'synthetic cause')
        self.assertEqual(report['invocation_status'], 'FAILED')
        self.assertTrue(report['reviewer_process_started'])
        self.assertEqual(report['process_exit_code'], 1)
        self.assertEqual(report['stderr_evidence_error'], 'PermissionError')

    def test_real_local_subprocess_pipe_bytes_and_stdin(self):
        real_run = subprocess.run
        raw = b'synthetic local pipe failure\r\n\xff'
        script = '# reviewer-stream-fixture\nimport sys; assert "\\uac80\\uc99d" in sys.stdin.buffer.read().decode("utf-8"); sys.stderr.buffer.write(' + repr(raw) + '); sys.exit(1)'
        def fixture_process(args, **kwargs):
            return real_run([sys.executable, '-c', script], **kwargs)
        report = self.invoke(side_effect=fixture_process)
        self.assertEqual(report['invocation_status'], 'FAILED')
        self.assertEqual(report['process_exit_code'], 1)
        meta, text = self.evidence(report, 'stderr', raw)
        self.assertTrue(meta['decode_replacement'])
        self.assertIn('synthetic local pipe failure', text)

    def test_real_stdin_bytes_equal_previous_text_mode_policy(self):
        real_run = subprocess.run
        expected_prompt = 'Synthetic review only. \uac80\uc99d\n\nREQUEST JSON:\n' + json.dumps(self.request, ensure_ascii=False, indent=2)
        script = '# reviewer-stream-fixture\nimport sys; sys.stderr.buffer.write(sys.stdin.buffer.read()); sys.exit(1)'
        previous = real_run([sys.executable, '-c', script], input=expected_prompt, capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=37)
        def fixture_process(args, **kwargs):
            return real_run([sys.executable, '-c', script], **kwargs)
        report = self.invoke(side_effect=fixture_process)
        raw = expected_prompt.replace('\n', os.linesep).encode('utf-8')
        self.assertEqual(self.evidence(report, 'stderr', raw)[1], previous.stderr)


if __name__ == '__main__':
    unittest.main()
