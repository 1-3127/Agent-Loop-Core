import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
WORK = Path(__file__).resolve().parent
temp = WORK / 'test-temp'
temp.mkdir(exist_ok=True)
tempfile.tempdir = str(temp)
os.environ.update(PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1', TEMP=str(temp), TMP=str(temp))
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
os.chdir(ROOT)
counts = {'network': 0, 'production_process': 0, 'allowed_local_fixture_process': 0}
tree = ast.parse((ROOT / 'tests/test_package_boundary.py').read_text(encoding='utf-8'))
package_script = next(n.value.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                      and any(isinstance(x, ast.Name) and x.id == 'script' for x in n.targets))
pipe_script = '# reviewer-stream-fixture\nimport sys; assert "\\uac80\\uc99d" in sys.stdin.buffer.read().decode("utf-8"); sys.stderr.buffer.write(' + repr(b'synthetic local pipe failure\r\n\xff') + '); sys.exit(1)'
stdin_script = '# reviewer-stream-fixture\nimport sys; sys.stderr.buffer.write(sys.stdin.buffer.read()); sys.exit(1)'
allowed = {subprocess.list2cmdline([sys.executable, '-c', s]) for s in (package_script, pipe_script, stdin_script)}
def audit(event, args):
    if event in ('socket.connect', 'socket.getaddrinfo', 'socket.gethostbyname'):
        counts['network'] += 1
        raise RuntimeError('Regression network denied')
    if event == 'subprocess.Popen':
        command = args[1]
        encoded = subprocess.list2cmdline(command) if isinstance(command, (list, tuple)) else command
        if encoded in allowed:
            counts['allowed_local_fixture_process'] += 1
        else:
            counts['production_process'] += 1
            raise RuntimeError('Regression production process denied')
sys.addaudithook(audit)
mode = sys.argv[1]
label = sys.argv[2] if len(sys.argv) > 2 else mode
loader = unittest.defaultTestLoader
if mode == 'pre-fix':
    suite = loader.loadTestsFromName('tests.test_l7_review_stream_contract.ReviewStreamContractTests.test_final2_structure_canonical_preflight_action_and_identity')
elif mode == 'focused':
    suite = loader.loadTestsFromNames(['tests.test_l7_review_stream_contract', 'tests.test_l7_feedback_controller',
        'tests.test_l7_geometry_review', 'tests.test_reviewer_failure_observability', 'tests.test_session_scenario_binding',
        'tests.test_session_boundary', 'tests.test_l6_pipeline', 'tests.test_current_reference_binding',
        'tests.test_reference_dimension_normalization'])
elif mode == 'full':
    suite = loader.discover(str(ROOT / 'tests'), top_level_dir=str(ROOT))
else:
    raise ValueError(mode)
started = time.monotonic()
with (WORK / (label + '.log')).open('x', encoding='utf-8') as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
summary = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
    'skips': len(result.skipped), 'pass': result.wasSuccessful(), 'seconds': time.monotonic() - started,
    'tripwires': counts, 'python': sys.version, 'runtime': sys.executable,
    'scope': 'Synthetic regression, not Session E2E or fresh-context proof'}
with (WORK / (label + '.json')).open('x', encoding='utf-8') as stream:
    json.dump(summary, stream, indent=2)
print(json.dumps(summary), flush=True)
if not result.wasSuccessful():
    print((WORK / (label + '.log')).read_text(encoding='utf-8')[-15000:])
sys.exit(0 if result.wasSuccessful() else 1)
