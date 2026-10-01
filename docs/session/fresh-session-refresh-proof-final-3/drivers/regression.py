import os,sys,tempfile,unittest,time,json,subprocess,ast
from pathlib import Path
ROOT=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final-3'
scratch=Path(__file__).parent/'test-temp'; scratch.mkdir(exist_ok=True)
tempfile.tempdir=str(scratch)
os.environ.update(PYTHONPATH=str(ROOT/'src'),PYTHONDONTWRITEBYTECODE='1',TEMP=tempfile.tempdir,TMP=tempfile.tempdir)
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
os.chdir(ROOT)
counts={'network':0,'production_process':0,'allowed_local_fixture_process':0}
tree=ast.parse((ROOT/'tests/test_package_boundary.py').read_text(encoding='utf-8'))
package_script=next(n.value.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='script' for x in n.targets))
pipe_script='# reviewer-stream-fixture\nimport sys; assert "\\uac80\\uc99d" in sys.stdin.buffer.read().decode("utf-8"); sys.stderr.buffer.write('+repr(b'synthetic local pipe failure\r\n\xff')+'); sys.exit(1)'
stdin_script='# reviewer-stream-fixture\nimport sys; sys.stderr.buffer.write(sys.stdin.buffer.read()); sys.exit(1)'
allowed={subprocess.list2cmdline([sys.executable,'-c',s]) for s in (package_script,pipe_script,stdin_script)}
def audit(event,args):
    if event in ('socket.connect','socket.getaddrinfo','socket.gethostbyname'):
        counts['network']+=1; raise RuntimeError('Regression network denied')
    if event=='subprocess.Popen':
        cmd=args[1]; encoded=subprocess.list2cmdline(cmd) if isinstance(cmd,(list,tuple)) else cmd
        if encoded in allowed: counts['allowed_local_fixture_process']+=1
        else: counts['production_process']+=1; raise RuntimeError('Regression production process denied')
sys.addaudithook(audit)
t=time.monotonic()
with (PROOF/'REGRESSION.log').open('x',encoding='utf-8') as f:
    result=unittest.TextTestRunner(stream=f,verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py'))
summary={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'pass':result.wasSuccessful(),'seconds':time.monotonic()-t,'tripwires':counts,'runtime':sys.executable,'python':sys.version,'temporary_root':tempfile.tempdir,'evidence_scope':'Synthetic regression; not actual production proof','source_test_changes':0}
with (PROOF/'REGRESSION_RESULT.json').open('x',encoding='utf-8') as f: json.dump(summary,f,indent=2)
print(json.dumps(summary),flush=True)
sys.exit(0 if result.wasSuccessful() else 1)
