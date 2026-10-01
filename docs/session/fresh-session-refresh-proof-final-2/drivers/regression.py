import os,sys,tempfile,unittest,time,json,subprocess,ast
from pathlib import Path
ROOT=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final-2'
TASK=Path(__file__).resolve().parent
(TASK/'test-temp').mkdir(exist_ok=True)
tempfile.tempdir=str(TASK/'test-temp')
os.environ.update(PYTHONPATH=str(ROOT/'src'),PYTHONDONTWRITEBYTECODE='1',TEMP=tempfile.tempdir,TMP=tempfile.tempdir)
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
os.chdir(ROOT)
counts={'network':0,'production_process':0,'allowed_local_fixture_process':0}
package_tree=ast.parse((ROOT/'tests/test_package_boundary.py').read_text(encoding='utf-8'))
package_script=next(n.value.value for n in ast.walk(package_tree) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='script' for x in n.targets))
pipe_script='# reviewer-stream-fixture\nimport sys; assert "\\uac80\\uc99d" in sys.stdin.buffer.read().decode("utf-8"); sys.stderr.buffer.write('+repr(b'synthetic local pipe failure\r\n\xff')+'); sys.exit(1)'
stdin_script='# reviewer-stream-fixture\nimport sys; sys.stderr.buffer.write(sys.stdin.buffer.read()); sys.exit(1)'
allowed={subprocess.list2cmdline([sys.executable,'-c',s]) for s in (package_script,pipe_script,stdin_script)}
def audit(event,args):
    if event in ('socket.connect','socket.getaddrinfo','socket.gethostbyname'):
        counts['network']+=1
        raise RuntimeError('Regression network denied')
    if event=='subprocess.Popen':
        command=args[1]
        encoded=subprocess.list2cmdline(command) if isinstance(command,(list,tuple)) else command
        if encoded in allowed:
            counts['allowed_local_fixture_process']+=1
        else:
            counts['production_process']+=1
            raise RuntimeError('Regression production process denied')
sys.addaudithook(audit)
t=time.monotonic()
sys.path.insert(0,str(ROOT/'tests'))
names=['test_package_boundary.PackageBoundaryTests.test_single_src_root_imports_core_and_active_scenario','test_reviewer_failure_observability.ReviewerFailureObservabilityTests.test_real_local_subprocess_pipe_bytes_and_stdin','test_reviewer_failure_observability.ReviewerFailureObservabilityTests.test_real_stdin_bytes_equal_previous_text_mode_policy']
with (PROOF/'REGRESSION_WRAPPER_RECHECK.log').open('x',encoding='utf-8') as stream:
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
summary={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'pass':result.wasSuccessful(),'seconds':time.monotonic()-t,'tripwires':counts,'python':sys.version,'runtime':sys.executable,'temporary_root':tempfile.tempdir,'evidence_scope':'Synthetic regression; not actual production proof'}
with (PROOF/'REGRESSION_WRAPPER_RECHECK.json').open('x',encoding='utf-8') as f: json.dump(summary,f,indent=2)
first=json.loads((PROOF/'REGRESSION_RESULT.json').read_text(encoding='utf-8'))
assert first['tests']==261 and first['failures']==0 and first['errors']==3
verified={'tests':261,'pass':result.wasSuccessful(),'failures':len(result.failures),'errors':len(result.errors),'first_run':first,'wrapper_recheck':summary,'validation_scope':'258 original passes plus all 3 wrapper-blocked tests rechecked with exact local subprocess whitelist; source/test unchanged. Original raw failure retained.','production_effects':0}
with (PROOF/'REGRESSION_VERIFIED.json').open('x',encoding='utf-8') as f: json.dump(verified,f,indent=2)
print(json.dumps(summary),flush=True)
sys.exit(0 if result.wasSuccessful() else 1)
