"""Read-only current acceptance and repository gate; no generation or delivery."""
import hashlib, json, pathlib, subprocess
ROOT=pathlib.Path('D:/VSCODE-WorkSpace/Others/Agent-Loop-Core')
WORK=pathlib.Path(__file__).resolve().parent
def git(*args):
    return subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),*args],cwd=ROOT,text=True,encoding='utf-8').strip()
assert git('branch','--show-current')=='actual-loop-post-stabilization'
assert git('rev-parse','HEAD')==git('rev-parse','@{upstream}')=='b4211581bb79986de76cebb12d0e5b48b2829443'
assert not git('status','--porcelain=v1')
remote=git('ls-remote','origin','refs/heads/*','refs/tags/*')
assert 'b4211581bb79986de76cebb12d0e5b48b2829443\trefs/heads/actual-loop-post-stabilization' in remote
tracked={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in git('ls-files').splitlines()}
local_refs=git('show-ref')
original=(WORK/'verify_actual.py').read_text(encoding='utf-8')
prefix=original.split("phase='record'",1)[0]
exec(compile(prefix,str(WORK/'verify_actual.py'),'exec'),globals())
assert accepted and boundary.outcome.status=='INTERNAL_ACCEPT'
assert not boundary.outcome.terminal and not boundary.outcome.delivered
assert accept['artifact']['bytes']==1139020
assert accept['artifact']['sha256']=='1ee1c6b28f56499e8e83d810b038d0b1736952563744cc2416e04efddeb0c770'
assert not (d/'terminal.json').exists()
phase='record'
gate={'verdict':'PASS','repository':str(ROOT),'branch':'actual-loop-post-stabilization','head':'b4211581bb79986de76cebb12d0e5b48b2829443','clean':True,'local_tracking_live_equal':True,'local_refs':local_refs,'live_remote_refs':remote,'tracked':tracked,'session':ids['session'],'loop':ids['loop'],'status':boundary.outcome.status,'terminal':False,'delivered':False,'specification_identity_sha256':binding.specification.identity_sha256,'specification':accept['specification'],'artifact':accept['artifact'],'internal_accept':dataclasses.asdict(session.file_identity(d/'internal_accept.json',ids['session']+':internal_accept')),'mandatory_coverage_verified':True,'references_verified':len(checked_refs),'historical_external_protected':len(protected['external']),'effects':{'worker':0,'comfy_generation':0,'blender':0,'semantic_reviewer':0,'correction':0,'submission':0},'observed_at':l6.now()}
l6.write_once(WORK/'delivery_start_gate.json',gate)
print(json.dumps({k:v for k,v in gate.items() if k not in ('tracked','local_refs','live_remote_refs')},ensure_ascii=False,indent=2))
