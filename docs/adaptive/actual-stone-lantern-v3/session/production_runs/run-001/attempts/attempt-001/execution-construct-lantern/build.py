import bpy, runpy, json
from pathlib import Path
out = Path('D:\\VSCODE-WorkSpace\\Others\\Agent-Loop-Core\\docs\\adaptive\\actual-stone-lantern-v3\\session\\production_runs\\run-001\\attempts\\attempt-001\\execution-construct-lantern')
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
runpy.run_path(str(out / "asset_source.py"))["build_asset"]()
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
assert meshes and sum(len(o.data.polygons) for o in meshes) > 0
bpy.ops.wm.save_as_mainfile(filepath=str(out / "asset.blend"))
bpy.ops.export_scene.gltf(filepath=str(out / "asset.glb"), export_format="GLB", export_apply=True)
with (out / "build_metrics.json").open("x", encoding="utf-8") as f: json.dump({"mesh_count":len(meshes),"polygon_count_authored":sum(len(o.data.polygons) for o in meshes),"objects":[o.name for o in meshes]},f)
