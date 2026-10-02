"""Bounded independent exported-GLB evidence; scene geometry is never edited."""
import json
import math
from pathlib import Path
import sys


def render(path):
    import bpy
    from mathutils import Vector
    request = json.loads(Path(path).read_text(encoding='utf-8'))
    source, output = Path(request['source_glb']), Path(request['output'])
    assert not output.exists()
    output.mkdir()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    assert meshes
    graph = bpy.context.evaluated_depsgraph_get()
    points = [o.evaluated_get(graph).matrix_world @ Vector(p) for o in meshes for p in o.evaluated_get(graph).bound_box]
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center, extents = (low + high) / 2, high - low
    scene = bpy.context.scene
    scene.render.resolution_x = scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'Standard'
    camera = bpy.data.objects.new('EvidenceCamera', bpy.data.cameras.new('EvidenceCamera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = 'ORTHO'
    camera.data.clip_end = extents.length * 10
    camera.data.clip_start = 0.001
    scene.world.color = (0.5, 0.5, 0.5)
    for name, position, energy, size in [('Key', (4, -5, 6), 1000, 5), ('Fill', (-4, -1, 4), 600, 4), ('Rim', (2, 4, 6), 800, 3)]:
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, 'AREA'))
        light.location = center + Vector(position) * max(extents)
        light.data.energy, light.data.shape, light.data.size = energy, 'DISK', size * max(extents)
        light.rotation_euler = (center - light.location).to_track_quat('-Z', 'Y').to_euler()
        scene.collection.objects.link(light)
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.film_transparent = False
    params = request.get('parameters', {})
    azimuth = float(params.get('camera_azimuth', 30))
    elevation = float(params.get('camera_elevation', 10))
    ratio = float(params.get('target_height_ratio', 0.64))
    scale = float(params.get('orthographic_scale_factor', 0.6))
    assert -360 <= azimuth <= 360 and -80 <= elevation <= 80 and 0 <= ratio <= 1 and 0.25 <= scale <= 2
    outputs = []
    views = [('perspective-stone', 30, 12, center, 1.25),
        ('aperture-detail', 0, 0, Vector((center.x, center.y, low.z + extents.z * ratio)), scale),
        ('requested-evidence', azimuth, elevation, Vector((center.x, center.y, low.z + extents.z * ratio)), scale)]
    for name, angle, height, target, factor in views:
        theta, phi = math.radians(angle), math.radians(height)
        direction = Vector((math.sin(theta) * math.cos(phi), -math.cos(theta) * math.cos(phi), math.sin(phi)))
        camera.location = target + direction * extents.length * 2
        camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.ortho_scale = max(extents) * factor
        scene.render.filepath = str(output / (name + '.png'))
        bpy.ops.render.render(write_still=True)
        outputs.append({'path': scene.render.filepath, 'view': name, 'camera': list(camera.location),
            'target': list(target), 'ortho_scale': camera.data.ortho_scale})
    with Path(request['manifest']).open('x', encoding='utf-8') as stream:
        json.dump({'source_glb': str(source), 'outputs': outputs, 'scope': 'Independent fresh-import material and aperture evidence; no authored-geometry mutation'}, stream, indent=2)


if __name__ == '__main__':
    render(sys.argv[sys.argv.index('--') + 1])
