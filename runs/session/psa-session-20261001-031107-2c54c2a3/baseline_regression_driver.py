import ast, json, pathlib, subprocess, sys, tempfile, time, unittest
root = pathlib.Path('D:/VSCODE-WorkSpace/Others/Agent-Loop-Core')
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / 'src'))
effects = {'network': 0, 'production_process': 0, 'import_smoke_process': 0}
tree = ast.parse((root / 'tests/test_package_boundary.py').read_text(encoding='utf-8'))
smoke = next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'script' for t in n.targets))
smoke_args = [sys.executable, '-c', smoke]
smoke_command = subprocess.list2cmdline(smoke_args)
def gate(event, args):
    if event in ('socket.connect', 'socket.connect_ex', 'urllib.Request'):
        effects['network'] += 1
        raise AssertionError('Actual proof baseline: network forbidden')
    if event == 'subprocess.Popen':
        if args[1] == smoke_command or args[1] == smoke_args:
            effects['import_smoke_process'] += 1
        else:
            effects['production_process'] += 1
            raise AssertionError('Actual proof baseline: production process forbidden')
sys.addaudithook(gate)
started = time.monotonic()
with tempfile.TemporaryDirectory(prefix='baseline-', dir=pathlib.Path(__file__).parent) as scratch:
    tempfile.tempdir = scratch
    suite = unittest.defaultTestLoader.discover(str(root / 'tests'), pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped), 'seconds': time.monotonic()-started, 'effects': effects, 'successful': result.wasSuccessful(), 'python': sys.version}
    (pathlib.Path(__file__).parent / 'baseline_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary))
sys.exit(0 if result.wasSuccessful() and effects['network'] == effects['production_process'] == 0 else 1)
