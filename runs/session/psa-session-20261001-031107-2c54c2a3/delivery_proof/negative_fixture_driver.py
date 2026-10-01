"""Existing negative contract tests only; fixtures are not actual delivery evidence."""
import io, json, os, pathlib, sys, tempfile, unittest
ROOT=pathlib.Path('D:/VSCODE-WorkSpace/Others/Agent-Loop-Core')
WORK=pathlib.Path(__file__).resolve().parent
P=ROOT/'runs/session/psa-session-20261001-031107-2c54c2a3/delivery_proof'
SCRATCH=WORK/'closure_negative_fixture_tmp'
SCRATCH.mkdir(exist_ok=False)
assert SCRATCH.resolve().is_relative_to(WORK.resolve())
tempfile.tempdir=str(SCRATCH)
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
effects={'network':0,'production_process':0,'generation':0}
def audit(event,args):
    if event in ('subprocess.Popen','urllib.Request','socket.connect'):
        raise RuntimeError('NEGATIVE_FIXTURE_NO_NETWORK_OR_PROCESS: '+event)
    if event=='shutil.rmtree' and not pathlib.Path(args[0]).resolve().is_relative_to(SCRATCH.resolve()):
        raise RuntimeError('FIXTURE_CLEANUP_OUT_OF_SCOPE')
    if event=='open' and (isinstance(args[1],str) and any(c in args[1] for c in ('w','a','x','+')) or args[2]& (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
        p=pathlib.Path(args[0]).resolve()
        if not p.is_relative_to(SCRATCH.resolve()) and not p.is_relative_to(P.resolve()):raise RuntimeError('FIXTURE_WRITE_OUT_OF_SCOPE')
sys.addaudithook(audit)
from scenario_a import l6_pipeline as l6
before={str(p):l6.digest(p) for p in P.parent.rglob('*') if p.is_file()}
names=[
 'test_t11_delivery_without_structured_submission_evidence_rejected',
 'test_t13_submission_package_artifact_and_specification_mismatch_rejected',
 'test_t14_terminal_reentry_all_mutations_rejected_and_bytes_unchanged',
 'test_fail_abort_guards_and_premature_delivery_rejected',
 'test_receipt_structure_namespace_and_timestamp_validation']
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName('tests.test_session_boundary.SessionBoundaryTests.'+n) for n in names)
log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
assert {str(p):l6.digest(p) for p in P.parent.rglob('*') if p.is_file()}==before
summary={'scope':'SYNTHETIC_EXISTING_LOCAL_NEGATIVE_CONTRACT_TESTS_ONLY','actual_delivery_proof':False,'test_names':names,'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'successful':result.wasSuccessful(),'effects':effects,'actual_session_records_unchanged':True,'fixture_directory':str(SCRATCH),'completed_at':l6.now()}
with (P/'negative_fixture_tests.log').open('x',encoding='utf-8',newline='\n') as f:f.write(log.getvalue())
l6.write_once(P/'negative_fixture_tests.json',summary)
with (P/'negative_fixture_driver.py').open('xb') as f:f.write(pathlib.Path(__file__).read_bytes())
print(json.dumps(summary,ensure_ascii=False,indent=2))
assert result.wasSuccessful() and result.testsRun==5
