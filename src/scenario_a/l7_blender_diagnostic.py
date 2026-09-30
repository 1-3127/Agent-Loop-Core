"""Standalone Blender diagnostic renderer; four fixed azimuths, no GLB edits."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROLES = tuple('geometry_azimuth_' + str(a) for a in (0, 90, 180, 270))
DIRECTIONS = ((0, -1, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0))
CONFIG = {'engine': 'BLENDER_WORKBENCH', 'projection': 'ORTHO', 'resolution': [512, 512],
          'margin': 1.2, 'up_axis': '+Z', 'color_mode': 'SINGLE', 'neutral_color': [0.7, 0.72, 0.75],
          'background': 'TRANSPARENT', 'scale_rule': 'max(world XYZ extents) * 1.2',
          'distance_rule': '2 * world bounds diagonal', 'azimuth_zero_direction': '-Y'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    return parser.parse_args(argv)


def render(request_path):
    import bpy
    from mathutils import Vector

    request_path = request_path.resolve(strict=True)
    request = json.loads(request_path.read_text(encoding='utf-8'))
    if request['config'] != CONFIG or request['script']['sha256'] != digest(__file__):
        raise ValueError('render configuration/script differs')
    source = Path(request['source_glb']['path']).resolve(strict=True)
    if digest(source) != request['source_glb']['sha256']:
        raise ValueError('GLB changed')
    output = Path(request['output_dir']).resolve()
    manifest_path = Path(request['manifest_path']).resolve()
    if output.exists() or manifest_path.exists():
        raise ValueError('render output namespace exists')
    if bpy.app.version_string != request['blender_version']:
        raise ValueError('Blender version differs')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    if 'FINISHED' not in bpy.ops.import_scene.gltf(filepath=str(source)):
        raise ValueError('GLB import failed')
    objects = list(bpy.context.scene.objects)
    meshes = [obj for obj in objects if obj.type == 'MESH']
    if not meshes or not any(len(obj.data.polygons) for obj in meshes):
        raise ValueError('no mesh surfaces')
    # Keep parent transforms; imported lights/cameras cannot control diagnostics.
    for obj in objects:
        if obj.type in ('LIGHT', 'CAMERA'):
            bpy.data.objects.remove(obj, do_unlink=True)
    graph = bpy.context.evaluated_depsgraph_get()
    points = [obj.evaluated_get(graph).matrix_world @ Vector(corner)
              for obj in meshes for corner in obj.evaluated_get(graph).bound_box]
    low = Vector(tuple(min(v[i] for v in points) for i in range(3)))
    high = Vector(tuple(max(v[i] for v in points) for i in range(3)))
    center, extents = (low + high) / 2, high - low
    maximum, diagonal = max(extents), extents.length
    if maximum <= 0 or not all(math.isfinite(x) for x in (*low, *high)):
        raise ValueError('invalid geometry bounds')
    scene = bpy.context.scene
    scene.render.engine = CONFIG['engine']
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.film_transparent = True
    shade = scene.display.shading
    shade.light, shade.color_type = 'STUDIO', 'SINGLE'
    shade.single_color = CONFIG['neutral_color']
    shade.show_shadows = True
    shade.show_cavity = False
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    camera_data = bpy.data.cameras.new('L7_Diagnostic')
    camera = bpy.data.objects.new('L7_Diagnostic', camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = maximum * CONFIG['margin']
    camera_data.clip_start = max(diagonal * 0.001, 0.000001)
    camera_data.clip_end = diagonal * 4
    distance = diagonal * 2
    output.mkdir(parents=True, exist_ok=False)
    outputs = []
    for azimuth, role, direction in zip((0, 90, 180, 270), ROLES, DIRECTIONS):
        outward = Vector(direction)
        camera.location = center + outward * distance
        camera.rotation_euler = (-outward).to_track_quat('-Z', 'Y').to_euler()
        path = output / (role + '.png')
        if path.exists():
            raise ValueError('render file collision')
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        image = bpy.data.images.load(str(path), check_existing=False)
        try:
            if tuple(image.size) != (512, 512):
                raise ValueError('render dimensions differ')
            from array import array
            pixels = array('f', [0]) * (512 * 512 * 4)
            image.pixels.foreach_get(pixels)
            foreground = sum(a > 0.5 for a in pixels[3::4])
            border = [pixels[(y * 512 + x) * 4 + 3] for y in range(512) for x in (0, 511)]
            border += [pixels[(y * 512 + x) * 4 + 3] for y in (0, 511) for x in range(512)]
            if foreground == 0 or any(a > 0.5 for a in border):
                raise ValueError('geometry invisible or touches image border')
        finally:
            bpy.data.images.remove(image)
        outputs.append({'role': role, 'azimuth': azimuth, 'path': str(path), 'sha256': digest(path),
                        'bytes': path.stat().st_size, 'width': 512, 'height': 512,
                        'foreground_pixels': foreground, 'camera_location': list(camera.location),
                        'camera_rotation_euler': list(camera.rotation_euler),
                        'ortho_scale': camera_data.ortho_scale, 'distance': distance,
                        'clip': [camera_data.clip_start, camera_data.clip_end]})
    if digest(source) != request['source_glb']['sha256']:
        raise ValueError('source GLB changed during render')
    manifest = {'version': 'l7-m1.0', 'run_id': request['run_id'],
                'source_l6_run_id': request['source_l6_run_id'], 'source_glb': request['source_glb'],
                'render_request': {'path': str(request_path), 'sha256': digest(request_path)},
                'blender_executable': str(Path(bpy.app.binary_path).resolve()),
                'blender_version': bpy.app.version_string, 'config': CONFIG,
                'bounding_box': {'min': list(low), 'max': list(high), 'center': list(center),
                                 'extents': list(extents), 'maximum_dimension': maximum},
                'object_count': len(objects), 'mesh_count': len(meshes),
                'import_transforms': [{'name': o.name, 'matrix_world': [list(row) for row in o.matrix_world]} for o in meshes],
                'studio_light': shade.studio_light,
                'outputs': outputs}
    with manifest_path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(manifest, stream, indent=2)
        stream.write('\n')
    print('L7_DIAGNOSTIC_RENDER_COMPLETE ' + str(manifest_path))


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    render(parse_args(args).request)
