from pathlib import Path
import json,hashlib,subprocess,datetime
ROOT=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
BASE=ROOT/'docs/adaptive/fresh-spec-dialogue-artifact-proof'
P=BASE/'fresh-002';FIX=BASE/'corrective-002'
OUT=Path(r'C:\Users\Worker\Documents\Codex\2026-10-02\codex-specification-dialogue-human-blocking-text\outputs\fresh-spec-dialogue-artifact-proof')
WORK=Path(__file__).resolve().parent
BRANCH='feature/adaptive-skill-orchestration'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(d)
def jput(p,d):put(p,json.dumps(d,ensure_ascii=False,indent=2).encode('utf-8'))
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT).decode('utf-8').strip()
def live():return git('-c','http.sslBackend=openssl','ls-remote','origin','refs/heads/'+BRANCH).split()[0]
focused=read(WORK/'focused-fixture/FOCUSED_VALIDATION.json');related=read(WORK/'host-defect-related-regression-result.json');full=read(WORK/'host-defect-full-regression-result.json')
assert focused['pass'] and related['pass'] and related['tests']==72 and full['pass'] and full['tests']==326
seal=read(P/'CLOSED_PROOF_SEAL.json')
assert all(sha(P/n)==e['sha256'] for n,e in seal['sealed_original_files'].items())
b=read(P/'BASELINE_GATE.json')
assert all(sha(ROOT/n)==h for n,h in b['tracked_file_sha256'].items())
assert all(git('rev-parse',n)==h for n,h in b['protected_refs'].items())
assert git('branch','--show-current')==BRANCH
previous=git('rev-parse','HEAD');assert previous=='192f793e7a58655478cf6ffcd4d9d31b0ac6f53c'==git('rev-parse','@{u}')==live()
assert not FIX.exists()
for name in ['fresh_execution_host.py','OUTPUT_SNAPSHOT_ORDER_FIX.diff','validate_snapshot_order_fix.py','host_defect_related_regression.py','host_defect_full_regression.py','seal_closed_proof.py','publish_correction.py','host-defect-related-regression-result.json','host-defect-related-regression.log','host-defect-full-regression-result.json','host-defect-full-regression.log']:
    put(FIX/name,(WORK/name).read_bytes())
for p in (WORK/'focused-fixture').rglob('*'):
    if p.is_file():put(FIX/'focused-fixture'/p.relative_to(WORK/'focused-fixture'),p.read_bytes())
correction={'pass':True,'scope':'Proof host post-close snapshot ordering only; Core source/tests unchanged','terminal_session_id':'fresh-spec-dialogue-artifact-002','terminal':'CLOSED','internal_accept':True,'delivered':True,'prior_complete_package_integrity':'FAILED','session_resumed':False,'fix':'One line removal: defer evidence snapshot until after local handoff/CLOSED, actual-success/validation, result and final counters','old_host_sha256':focused['old_host_sha256'],'corrected_host_sha256':sha(FIX/'fresh_execution_host.py'),'focused_validation':focused,'related_regression':related,'full_regression':full,'original_terminal_proof_bytes_unchanged':True,'baseline_files_unchanged':len(b['tracked_file_sha256']),'protected_refs_unchanged':len(b['protected_refs']),'new_clarification_auto_reuse':False,'next':'normal push, local/tracking/live equality+clean, then fresh-003 original Request/Reference-only actual intake'}
jput(FIX/'CORRECTION_VERIFICATION.json',correction)
for p in FIX.rglob('*'):
    if p.is_file():put(OUT/'corrective-002'/p.relative_to(FIX),p.read_bytes())
allowed=['docs/adaptive/fresh-spec-dialogue-artifact-proof/fresh-002/','docs/adaptive/fresh-spec-dialogue-artifact-proof/corrective-002/']
status=subprocess.check_output(['git','status','--porcelain=v1','-z'],cwd=ROOT).decode('utf-8')
assert all(any(s[3:].replace('\\','/').startswith(n) for n in allowed) for s in status.split('\0') if s),status
assert not git('diff','--cached','--name-only')
subprocess.run(['git','-c','core.autocrlf=false','add','--',*allowed],cwd=ROOT,check=True)
names=git('diff','--cached','--name-only').splitlines();assert names and all(any(n.startswith(a) for a in allowed) for n in names)
subprocess.run(['git','-c','core.whitespace=cr-at-eol','diff','--cached','--check'],cwd=ROOT,check=True)
subprocess.run(['git','commit','-m','fix(proof-host): snapshot evidence after terminal closure'],cwd=ROOT,check=True)
head=git('rev-parse','HEAD')
for n in names:assert subprocess.check_output(['git','show',head+':'+n],cwd=ROOT)==(ROOT/n).read_bytes(),n
subprocess.run(['git','-c','http.sslBackend=openssl','push','origin','HEAD:refs/heads/'+BRANCH],cwd=ROOT,check=True)
tracking=git('rev-parse','@{u}');remote=live();assert head==tracking==remote and not git('status','--porcelain=v1')
record={'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'branch':BRANCH,'local_head':head,'tracking_head':tracking,'live_remote_head':remote,'clean_tree':True,'normal_push':True,'previous_head':previous,'committed_blob_bytes_verified':len(names),'focused_pass':True,'related_tests':72,'full_tests':326,'terminal_proof':'fresh-002 CLOSED/internal_accept true; package integrity FAILED; preserved unchanged','next':'fresh-003 original request/reference intake; no terminal clarification authority reused','history_rewrite':False}
jput(OUT/'ARCHIVE_CORRECTION_PUBLICATION.json',record)
print(json.dumps(record,ensure_ascii=False))
