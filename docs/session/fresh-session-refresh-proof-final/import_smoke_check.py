import pathlib,sys,os,tempfile,unittest,ast,subprocess,json
ROOT=pathlib.Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
WORK=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
os.environ.update(PYTHONPATH=str(ROOT/'src'),PYTHONDONTWRITEBYTECODE='1',TEMP=str(WORK/'test-temp'),TMP=str(WORK/'test-temp'))
tempfile.tempdir=str(WORK/'test-temp')
tree=ast.parse((ROOT/'tests/test_package_boundary.py').read_text(encoding='utf-8'))
script=next(n.value.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='script' for t in n.targets))
command=[sys.executable,'-c',script]
expected_string=subprocess.list2cmdline(command)
counts={'network':0,'production_process':0,'import_smoke_process':0}
types=[]
def audit(event,args):
    if event in ('socket.connect','socket.getaddrinfo','socket.gethostbyname'):
        counts['network']+=1; raise RuntimeError('network denied')
    if event=='subprocess.Popen':
        actual=args[1]; types.append(type(actual).__name__)
        if actual==command or actual==expected_string:
            counts['import_smoke_process']+=1
        else:
            counts['production_process']+=1; raise RuntimeError('production denied')
sys.addaudithook(audit)
suite=unittest.defaultTestLoader.loadTestsFromName('tests.test_package_boundary.PackageBoundaryTests.test_single_src_root_imports_core_and_active_scenario')
with (WORK/'import_smoke_check.log').open('x',encoding='utf-8') as stream:
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
summary={'tests':result.testsRun,'pass':result.wasSuccessful(),'errors':len(result.errors),'failures':len(result.failures),'tripwires':counts,'audit_command_types':types,'scope':'Exact existing test rerun with Windows list2cmdline-aware import-only allowlist; source/test unchanged'}
(WORK/'import_smoke_check.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary))
