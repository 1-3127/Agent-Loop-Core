import ast
import hashlib
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
scratch = WORK / 'fresh-focused-test-temp'
scratch.mkdir(exist_ok=True)
tempfile.tempdir = str(scratch)
os.environ.update(PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1', TEMP=str(scratch), TMP=str(scratch))
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
os.chdir(ROOT)
counts = {'network': 0, 'production_process': 0, 'allowed_local_fixture_process': 0, 'repository_write': 0}
tree = ast.parse((ROOT / 'tests/test_package_boundary.py').read_text(encoding='utf-8'))
package_script = next(n.value.value for n in ast.walk(tree) if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) and x.id == 'script' for x in n.targets))
pipe_script = '# reviewer-stream-fixture\nimport sys; assert "\\uac80\\uc99d" in sys.stdin.buffer.read().decode("utf-8"); sys.stderr.buffer.write(' + repr(b'synthetic local pipe failure\r\n\xff') + '); sys.exit(1)'
stdin_script = '# reviewer-stream-fixture\nimport sys; sys.stderr.buffer.write(sys.stdin.buffer.read()); sys.exit(1)'
allowed = {subprocess.list2cmdline([sys.executable, '-c', s]) for s in (package_script, pipe_script, stdin_script)}

def in_repository(path):
    if not isinstance(path, (str, bytes, os.PathLike)):
        return False
    return Path(os.fsdecode(path)).resolve().is_relative_to(ROOT)

def audit(event, args):
    if event in ('socket.connect', 'socket.getaddrinfo', 'socket.gethostbyname'):
        counts['network'] += 1
        raise RuntimeError('Baseline regression network denied')
    if event == 'subprocess.Popen':
        cmd = args[1]
        encoded = subprocess.list2cmdline(cmd) if isinstance(cmd, (list, tuple)) else cmd
        if encoded in allowed:
            counts['allowed_local_fixture_process'] += 1
        else:
            counts['production_process'] += 1
            raise RuntimeError('Baseline regression production process denied')
    if event == 'open' and in_repository(args[0]):
        mode, flags = args[1], args[2]
        if (mode and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
            counts['repository_write'] += 1
            raise RuntimeError('Read-only baseline repository write denied')
    if event in ('os.remove', 'os.rmdir', 'os.mkdir', 'os.rename') and any(in_repository(p) for p in args[:2]):
        counts['repository_write'] += 1
        raise RuntimeError('Read-only baseline repository mutation denied')

sys.addaudithook(audit)
started = time.monotonic()
with (WORK / 'host-defect-related-regression.log').open('x', encoding='utf-8') as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(['tests.test_skill_artifact','tests.test_workflow_artifact','tests.test_frontier','tests.test_adaptive_loop','tests.test_adaptive_transitions','tests.test_adaptive_adapter','tests.test_adaptive_end_to_end','tests.test_artifact_review','tests.test_event_logging','tests.test_session_boundary','tests.test_local_handoff']))
summary = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skips': len(result.skipped), 'pass': result.wasSuccessful(), 'seconds': time.monotonic() - started, 'tripwires': counts, 'runtime': sys.executable, 'python': sys.version, 'temporary_root': tempfile.tempdir, 'scope': 'Read-only focused existing contract regression; synthetic evidence only; isolated from actual production Session'}
with (WORK / 'host-defect-related-regression-result.json').open('x', encoding='utf-8') as stream:
    json.dump(summary, stream, indent=2)
print(json.dumps(summary), flush=True)
sys.exit(0 if result.wasSuccessful() else 1)
