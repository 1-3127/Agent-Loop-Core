"""Independent imported-GLB evidence; no subject-specific construction or edits."""
import hashlib
import json
import math
from pathlib import Path
import sys

def render(request_path):
    import bpy
    from mathutils import Vector
    request=json.loads(Path(request_path).read_text(encoding='utf-8'))
    source=Path(request['source_glb']);output=Path(request['output'])
    assert source.is_file() and not output.exists()
    assert hashlib.sha256(source.read_bytes()).hexdigest()==request['source_sha256']
    output.mkdir(parents=True)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert meshes and sum(len(o.data.polygons) for o in meshes)>0
    graph=bpy.context.evaluated_depsgraph_get()
    points=[o.evaluated_get(graph).matrix_world@Vector(p) for o in meshes for p in o.evaluated_get(graph).bound_box]
    low=Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high=Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center,extents=(low+high)/2,high-low
    metrics={'source_glb':str(source),'source_sha256':request['source_sha256'],'mesh_count':len(meshes),
        'polygon_count':sum(len(o.data.polygons) for o in meshes),'bounds_min':list(low),'bounds_max':list(high),
        'extents':list(extents),'objects':[{'name':o.name,'polygons':len(o.data.polygons),
        'materials':[m.name for m in o.data.materials if m]} for o in meshes],
        'scope':'Fresh GLB import; bounds/material names do not certify contact, manifoldness, hidden-side accuracy or semantic acceptance'}
    metrics_path=output/'imported-geometry-metrics.json'
    with metrics_path.open('x',encoding='utf-8') as f:json.dump(metrics,f,indent=2)
    scene=bpy.context.scene
    scene.render.resolution_x=1024;scene.render.resolution_y=768;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.render.engine='BLENDER_EEVEE';scene.view_settings.view_transform='Standard'
    world=scene.world;world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.18,0.20,0.23,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=0.8
    camera=bpy.data.objects.new('IndependentEvidenceCamera',bpy.data.cameras.new('IndependentEvidenceCamera'))
    scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO'
    camera.data.clip_start=0.001;camera.data.clip_end=max(extents.length*20,100)
    for name,position,energy in [('Key',(2,-3,4),1600),('Fill',(-3,-2,2),1000),('Rim',(2,3,4),1400)]:
        lamp=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));scene.collection.objects.link(lamp)
        lamp.location=center+Vector(position)*max(extents)
        lamp.data.energy=energy*max(extents)**2;lamp.data.size=max(extents)*2
        lamp.rotation_euler=(center-lamp.location).to_track_quat('-Z','Y').to_euler()
    params=request.get('parameters',{})
    az=float(params.get('camera_azimuth',0));el=float(params.get('camera_elevation',8))
    ratio=float(params.get('target_height_ratio',0.5));factor=float(params.get('orthographic_scale_factor',1.15))
    assert -360<=az<=360 and -80<=el<=80 and 0<=ratio<=1 and 0.25<=factor<=2
    views=[('material-front',0,8,False,center,1.12),('material-perspective',18,18,False,center,1.18),
        ('requested-evidence',az,el,False,Vector((center.x,center.y,low.z+extents.z*ratio)),factor),
        ('neutral-front',0,0,True,center,1.12),('neutral-back',180,0,True,center,1.12),
        ('neutral-side',90,0,True,center,1.12),('neutral-elevated',20,38,True,center,1.18)]
    neutral=bpy.data.materials.new('IndependentNeutralDiagnostic');neutral.diffuse_color=(0.55,0.57,0.6,1)
    neutral.use_nodes=True;neutral.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=0.65
    outputs=[];neutral_applied=False
    for name,angle,height,use_neutral,target,scale in views:
        if use_neutral and not neutral_applied:
            for o in meshes:
                o.data.materials.clear();o.data.materials.append(neutral)
                for polygon in o.data.polygons:polygon.material_index=0
            neutral_applied=True
        theta,phi=math.radians(angle),math.radians(height)
        direction=Vector((math.sin(theta)*math.cos(phi),-math.cos(theta)*math.cos(phi),math.sin(phi)))
        camera.location=target+direction*max(extents.length*2,1)
        camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale=max(extents)*scale
        scene.render.filepath=str(output/(name+'.png'));bpy.ops.render.render(write_still=True)
        outputs.append({'path':scene.render.filepath,'view':name,'sha256':hashlib.sha256(Path(scene.render.filepath).read_bytes()).hexdigest(),
            'camera':list(camera.location),'target':list(target),'ortho_scale':camera.data.ortho_scale,'neutral_material':use_neutral})
    manifest={'source_glb':str(source),'source_sha256':request['source_sha256'],'outputs':outputs,
        'geometry_metrics':str(metrics_path),'scope':'Independent fresh-import diagnostic evidence; source GLB unchanged'}
    assert hashlib.sha256(source.read_bytes()).hexdigest()==request['source_sha256']
    with Path(request['manifest']).open('x',encoding='utf-8') as stream:json.dump(manifest,stream,indent=2)

if __name__=='__main__':render(sys.argv[sys.argv.index('--')+1])
