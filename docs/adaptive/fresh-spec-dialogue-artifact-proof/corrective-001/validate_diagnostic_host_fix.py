"""Development-only rendering regression fixture, outside every Core Session."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageStat

WORK=Path(__file__).resolve().parent
OUT=WORK/'diagnostic-host-fix-fixture'
OUT.mkdir(exist_ok=False)
BLENDER=r'D:\Blender_5.2\blender.exe'
OLD=Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core\docs\adaptive\fresh-spec-dialogue-artifact-proof\host\fresh_mesh_diagnostics.py')
NEW=WORK/'fresh_mesh_diagnostics.py'

def process(arguments,name):
    r=subprocess.run(arguments,capture_output=True,timeout=300)
    (OUT/(name+'.stdout.txt')).write_bytes(r.stdout);(OUT/(name+'.stderr.txt')).write_bytes(r.stderr)
    assert r.returncode==0,(name,r.returncode)

fixture=OUT/'fixture.py'
fixture.write_text('''import bpy
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for name,x,color,roughness,metallic in [('WhitePaint',-1.8,(0.86,0.87,0.83),0.38,0.12),('GrayConcrete',1.8,(0.38,0.40,0.36),0.91,0.0)]:
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    s=mat.node_tree.nodes['Principled BSDF']
    s.inputs['Base Color'].default_value=(*color,1)
    s.inputs['Roughness'].default_value=roughness;s.inputs['Metallic'].default_value=metallic
    bpy.ops.mesh.primitive_cube_add(size=2,location=(x,0,1));o=bpy.context.object;o.name=name
    o.data.materials.append(mat)
bpy.ops.export_scene.gltf(filepath=GLB_PATH,export_format='GLB',export_apply=True)
'''.replace('GLB_PATH',repr(str(OUT/'fixture.glb'))),encoding='utf-8')
process([BLENDER,'--background','--factory-startup','--python',str(fixture)],'fixture-build')
source=OUT/'fixture.glb';h=hashlib.sha256(source.read_bytes()).hexdigest()
for name,script in [('before',OLD),('after',NEW)]:
    request=OUT/(name+'-request.json')
    request.write_text(json.dumps({'source_glb':str(source),'source_sha256':h,'output':str(OUT/name),
        'manifest':str(OUT/(name+'-manifest.json')),'parameters':{}}),encoding='utf-8')
    process([BLENDER,'--background','--factory-startup','--python',str(script),'--',str(request)],name+'-render')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==h
before=Image.open(OUT/'before/material-front.png').convert('RGB')
after=Image.open(OUT/'after/material-front.png').convert('RGB')
regions=[(150,300,290,450),(734,300,874,450)]
def stats(image):
    means=[];clips=[]
    for region in regions:
        crop=image.crop(region);means.append(sum(ImageStat.Stat(crop).mean)/3)
        clips.append(sum(min(pixel)>=250 for pixel in crop.getdata())/(crop.width*crop.height))
    return {'mean_luminance_regions':means,'near_white_saturation_ratios':clips,'material_region_difference':abs(means[0]-means[1])}
b,a=stats(before),stats(after)
assert max(b['near_white_saturation_ratios'])>0.8,'Fixture must reproduce pre-fix white clipping'
assert max(a['near_white_saturation_ratios'])<0.1,'Corrected evidence must preserve headroom'
assert a['material_region_difference']>20,'Exported white/gray material distinction must be observable'
summary={'pass':True,'scope':'Development-only synthetic fixture; no Core Session, Worker, Reviewer, acceptance or delivery',
    'development_blender_processes':3,'production_effects':0,'source_glb_unchanged':True,
    'old_renderer_sha256':hashlib.sha256(OLD.read_bytes()).hexdigest(),'corrected_renderer_sha256':hashlib.sha256(NEW.read_bytes()).hexdigest(),
    'before':b,'after':a,'fix':'Remove scale-squared light energy; use AgX highlight compression',
    'images':[str(OUT/'before/material-front.png'),str(OUT/'after/material-front.png')]}
(OUT/'FOCUSED_VALIDATION.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary),flush=True)
