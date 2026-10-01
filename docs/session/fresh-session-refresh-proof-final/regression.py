import os, sys, pathlib, tempfile, unittest, time, json

ROOT = pathlib.Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
WORK = pathlib.Path(__file__).resolve().parent
temp_root = WORK / 'test-temp'
temp_root.mkdir(exist_ok=True)
os.environ.update(PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1', TEMP=str(temp_root), TMP=str(temp_root))
tempfile.tempdir = str(temp_root)
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
os.chdir(ROOT)
counts = {'network': 0, 'production_process': 0, 'import_smoke_process': 0}
def audit(event, args):
    if event in ('socket.connect', 'socket.getaddrinfo', 'socket.gethostbyname'):
        counts['network'] += 1
        raise RuntimeError('Regression network effect denied')
    if event == 'subprocess.Popen':
        command = args[1]
        if (isinstance(command, (list, tuple)) and len(command) == 3
                and pathlib.Path(command[0]) == pathlib.Path(sys.executable)
                and command[1] == '-c' and command[2].startswith('import sys, core.worker_port, core.result_review_adapter, core.reviewer_auth; ')):
            counts['import_smoke_process'] += 1
        else:
            counts['production_process'] += 1
            raise RuntimeError('Regression production process denied')
sys.addaudithook(audit)
started = time.monotonic()
with (WORK / 'regression.log').open('x', encoding='utf-8') as stream:
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_*.py')
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
summary = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skips': len(result.skipped), 'pass': result.wasSuccessful(), 'seconds': time.monotonic()-started, 'tripwires': counts, 'python': sys.version, 'executable': sys.executable}
(WORK / 'regression_result.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
print(json.dumps(summary), flush=True)
sys.exit(0 if result.wasSuccessful() else 1)
