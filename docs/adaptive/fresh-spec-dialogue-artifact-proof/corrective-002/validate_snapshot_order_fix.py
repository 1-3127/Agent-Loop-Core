"""Development-only synthetic snapshot ordering fixture. No Core Session/effects."""
from pathlib import Path
import ast,hashlib,json,types
work=Path(__file__).resolve().parent
root=work/'focused-fixture'
root.mkdir()
old=work.parent/'fresh-002-host/fresh_execution_host.py'
new=work/'fresh_execution_host.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def functions(path):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    module=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'copy_once','snapshot'}],type_ignores=[])
    scope={'Path':Path}
    exec(compile(module,str(path),'exec'),scope)
    return scope
def has_early_snapshot(path):
    deliver=next(n for n in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='deliver')
    return any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='snapshot' for n in ast.walk(deliver))
assert has_early_snapshot(old) and not has_early_snapshot(new)
for label,host in [('before',old),('after',new)]:
    scope=functions(host)
    source=root/label/'source';output=root/label/'output'
    (source/'session/logs').mkdir(parents=True)
    index=source/'session/logs/event_index.jsonl'
    index.write_bytes(b'{"fixture_event":"INTERNAL_ACCEPT"}\n')
    scope['DIRECTORY']=source
    if label=='before':scope['snapshot'](output)
    with index.open('ab') as stream:stream.write(b'{"fixture_event":"LOCAL_HANDOFF_CLOSED"}\n')
    (source/'session/terminal.json').write_text('{"fixture_only":true,"terminal":"CLOSED"}',encoding='utf-8')
    (source/'skill-validation-fixture.json').write_text('{"fixture_only":true,"promotion":false}',encoding='utf-8')
    stable={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
    failure=None
    try:scope['snapshot'](output)
    except AssertionError as exc:failure=str(exc)
    if label=='before':assert failure=='OUTPUT_SNAPSHOT_CHANGED'
    else:
        assert failure is None
        assert all((output/n).read_bytes()==(source/n).read_bytes() for n in stable)
    assert all(sha(source/n)==h for n,h in stable.items())
record={'pass':True,'scope':'Development-only synthetic host snapshot ordering; no Core Session, model, Blender, ComfyUI or promotion','old_collision_reproduced':True,'corrected_post_close_snapshot_exact':True,'source_evidence_unchanged':True,'fix':'Remove pre-close evidence snapshot; take exactly one evidence snapshot after handoff/CLOSED, actual-success record, validation record, result and counters','old_host_sha256':sha(old),'corrected_host_sha256':sha(new),'production_effects':0,'new_core_sessions':0}
with (root/'FOCUSED_VALIDATION.json').open('x',encoding='utf-8') as stream:json.dump(record,stream,indent=2)
print(json.dumps(record))
