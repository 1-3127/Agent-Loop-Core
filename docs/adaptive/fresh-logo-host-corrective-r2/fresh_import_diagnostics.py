"""Independent fresh-import geometry and multiview observation."""
import bpy,bmesh,json,sys,hashlib,math
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from host_geometry_contract import reference_orthographic_scale, fitted_orthographic_scale
request=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text(encoding='utf-8'))
reference_scale=reference_orthographic_scale(request['image_width'],request['pixel_scale'])
out=Path(request['output']);out.mkdir()
source=Path(request['source_glb']);assert hashlib.sha256(source.read_bytes()).hexdigest()==request['source_sha256']
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(source))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert objects
vertices=[];nonmanifold=0;faces=0;uv_objects=0;details=[]
for o in objects:
 vertices.extend(o.matrix_world@v.co for v in o.data.vertices)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
 bad=sum(not e.is_manifold for e in bm.edges);nonmanifold+=bad;faces+=len(bm.faces)
 points=[o.matrix_world@v.co for v in o.data.vertices]
 bounds_min=[min(v[i] for v in points) for i in range(3)];bounds_max=[max(v[i] for v in points) for i in range(3)]
 materials=[]
 for material in o.data.materials:
  if material is None:materials.append(None);continue
  principled=next((n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if material.use_nodes else None
  socket=principled.inputs.get('Base Color') if principled else None
  materials.append(dict(name=material.name,base_color=list(socket.default_value) if socket else list(material.diffuse_color),color_space='scene_linear',base_color_is_linked=bool(socket and socket.is_linked)))
 details.append(dict(name=o.name,welded_vertices=len(bm.verts),faces=len(bm.faces),nonmanifold_edges=bad,bounds_min=bounds_min,bounds_max=bounds_max,dimensions=[bounds_max[i]-bounds_min[i] for i in range(3)],matrix_world=[list(row) for row in o.matrix_world],materials=materials,polygon_material_indices=sorted(set(p.material_index for p in o.data.polygons))));bm.free()
 uv_objects+=bool(o.data.uv_layers)
mins=[min(v[i] for v in vertices) for i in range(3)];maxs=[max(v[i] for v in vertices) for i in range(3)]
metrics=dict(source_sha256=request['source_sha256'],fresh_import=True,mesh_count=len(objects),faces=faces,
 bounds_min=mins,bounds_max=maxs,dimensions=[maxs[i]-mins[i] for i in range(3)],nonmanifold_edges_after_welding=nonmanifold,
 objects_with_uv=uv_objects,objects=details,interpretation='Separate glyph/ribbon solids intentionally reproduce disconnected logo elements; no backing card is added')
with (out/'geometry-metrics.json').open('x',encoding='utf-8') as f:json.dump(metrics,f,indent=2)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16
scene.render.resolution_x=request['image_width'];scene.render.resolution_y=request['image_height'];scene.render.resolution_percentage=100
scene.render.pixel_aspect_x=1;scene.render.pixel_aspect_y=1
scene.render.image_settings.file_format='PNG';scene.world.color=(.06,.06,.06)
scene.view_settings.view_transform='Standard';scene.render.film_transparent=False
world=scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.035,.033,.03,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
for name,pos,power,size in [('Key',(-3,-8,7),1000,8),('Fill',(6,-4,3),650,6),('Rear',(-4,4,5),900,7)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
camera_data=bpy.data.cameras.new('DiagnosticCamera');camera=bpy.data.objects.new('DiagnosticCamera',camera_data);scene.collection.objects.link(camera);scene.camera=camera;camera_data.type='ORTHO';camera_data.sensor_fit='HORIZONTAL'
outputs=[]
center=Vector([(a+b)/2 for a,b in zip(mins,maxs)])
framing=[]
def place_camera(view):
 if view in ('front','silhouette'):
  camera.location=(0,-20,0);target=Vector((0,0,0));size=reference_scale
 else:
  direction={'perspective':Vector((6,-14,6)),'rear':Vector((0,20,0)),'side':Vector((20,0,0))}[view]
  camera.location=center+direction;target=center;size=None
 camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
 rotation=camera.rotation_euler.to_quaternion().inverted()
 points=[rotation@(v-target) for v in vertices]
 if size is None:size=fitted_orthographic_scale([(v.x,v.y) for v in points],scene.render.resolution_x,scene.render.resolution_y)
 camera_data.ortho_scale=size
 half_y=size*scene.render.resolution_y/scene.render.resolution_x/2
 if any(abs(v.x)>size/2+1e-6 or abs(v.y)>half_y+1e-6 for v in points):raise ValueError('DIAGNOSTIC_FRAME_CLIPS_SOURCE')
 framing.append(dict(view=view,sensor_fit='HORIZONTAL',ortho_scale=size,target=list(target),all_vertices_in_frame=True))
for view in ('front','perspective','rear','side'):
 place_camera(view)
 scene.render.filepath=str(out/(view+'.png'));bpy.ops.render.render(write_still=True);outputs.append(dict(view=view,path=str(out/(view+'.png'))))
saved=[(o,list(o.data.materials)) for o in objects]
white=bpy.data.materials.new('DiagnosticSilhouette');white.use_nodes=True;n=white.node_tree.nodes;n.clear();e=n.new('ShaderNodeEmission');e.inputs[0].default_value=(1,1,1,1);output=n.new('ShaderNodeOutputMaterial');white.node_tree.links.new(e.outputs[0],output.inputs[0])
for o,_ in saved:
 o.data.materials.clear();o.data.materials.append(white)
place_camera('silhouette')
world.node_tree.nodes['Background'].inputs['Color'].default_value=(0,0,0,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=0
scene.render.filepath=str(out/'silhouette.png');bpy.ops.render.render(write_still=True);outputs.append(dict(view='silhouette',path=str(out/'silhouette.png')))
assert hashlib.sha256(source.read_bytes()).hexdigest()==request['source_sha256'],'SOURCE_CHANGED_DURING_DIAGNOSTICS'
with Path(request['manifest']).open('x',encoding='utf-8') as f:json.dump(dict(source_sha256=request['source_sha256'],outputs=outputs,geometry_metrics=str(out/'geometry-metrics.json'),fresh_import=True,framing=framing,requested_parameters=request.get('parameters',{}),evidence_scope='Full fixed-reference front/silhouette, fitted other views, all component bounds/transforms/material values; no semantic glyph labels inferred'),f)
