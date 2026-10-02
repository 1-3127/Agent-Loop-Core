"""SYNTHETIC factory cube diagnostic; no actual proof or Core Session."""
import bpy
import hashlib
import json
from pathlib import Path
import runpy
import sys

root=Path(sys.argv[sys.argv.index('--')+1]).resolve(); root.mkdir()
here=Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add(size=2,location=(0,0,0))
cube=bpy.context.object; cube.name='SYNTHETIC_RECTANGULAR_SOLID'; cube.scale=(5,.04,.6)
material=bpy.data.materials.new('SYNTHETIC_GOLD'); material.use_nodes=True
material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.5,.4,.25,1)
cube.data.materials.append(material)
source=root/'synthetic.glb'
bpy.ops.export_scene.gltf(filepath=str(source),export_format='GLB',export_apply=True)
digest=hashlib.sha256(source.read_bytes()).hexdigest()
request=dict(source_glb=str(source),source_sha256=digest,output=str(root/'views'),manifest=str(root/'manifest.json'),pixel_scale=10/626,image_width=800,image_height=400,parameters={'scope':'SYNTHETIC_ONLY'})
(root/'request.json').write_text(json.dumps(request),encoding='utf-8')
sys.argv=['fresh_import_diagnostics.py','--',str(root/'request.json')]
runpy.run_path(str(here/'fresh_import_diagnostics.py'),run_name='__main__')
camera=bpy.context.scene.camera
frame=camera.data.view_frame(scene=bpy.context.scene)
span_x=max(v.x for v in frame)-min(v.x for v in frame)
span_y=max(v.y for v in frame)-min(v.y for v in frame)
assert abs(span_x-800*10/626)<1e-5,(span_x,span_y)
assert abs(span_x/span_y-2)<1e-5
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
assert len(manifest['framing'])==5 and all(v['all_vertices_in_frame'] for v in manifest['framing'])
metrics=json.loads((root/'views/geometry-metrics.json').read_text(encoding='utf-8'))
assert metrics['objects'][0]['materials'][0]['color_space']=='scene_linear'
assert metrics['objects'][0]['dimensions'][0]>9.99
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(root/'probe-result.json').write_text(json.dumps(dict(scope='SYNTHETIC_ONLY',pass_result=True,all_views_in_frame=True,horizontal_camera_span=span_x,vertical_camera_span=span_y,source_unchanged=True,component_bounds_and_materials_observed=True,Session_starts=0,actual_reference_reads=0),indent=2),encoding='utf-8')
