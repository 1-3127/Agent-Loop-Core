"""Tool-side fresh-import evidence. Never edits the supplied geometry."""
import hashlib
import json
import math
from pathlib import Path
import sys


def render(request):
    import bpy
    from mathutils import Vector
    source = Path(request["source"]["path"])
    if hashlib.sha256(source.read_bytes()).hexdigest() != request["source"]["sha256"]:
        raise ValueError("INPUT_CHANGED")
    directory = Path(request["directory"])
    directory.mkdir()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes or not any(o.data.polygons for o in meshes):
        raise ValueError("NO_GEOMETRY")
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center, extent = (low + high)/2, high - low
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "SINGLE"
    scene.display.shading.single_color = (0.7, 0.72, 0.75)
    scene.render.film_transparent = True
    scene.render.resolution_x, scene.render.resolution_y = request["size"]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = max(extent) * 1.3
    scene.camera = camera
    view_slots = [s for s in request["slots"] if s != "metrics"]
    if len(view_slots) != len(request["azimuths"]) or max(extent) <= 0:
        raise ValueError("DIAGNOSTIC_OUTPUT_CONTRACT")
    outputs = {}
    for slot, angle in zip(view_slots, request["azimuths"]):
        radians = math.radians(angle)
        camera.location = center + Vector((math.sin(radians), -math.cos(radians), 0.2)) * extent.length * 2
        camera.rotation_euler = (center-camera.location).to_track_quat("-Z", "Y").to_euler()
        file = directory / (slot + ".png")
        scene.render.filepath = str(file)
        bpy.ops.render.render(write_still=True)
        outputs[slot] = str(file)
    metrics = directory / "metrics.json"
    metrics.write_text(json.dumps({"blender": bpy.app.version_string, "input_sha256": request["source"]["sha256"],
        "mesh_count": len(meshes), "vertices": sum(len(o.data.vertices) for o in meshes),
        "polygons": sum(len(o.data.polygons) for o in meshes), "bounds_min": list(low), "bounds_max": list(high),
        "semantic_acceptance": None}, indent=2), encoding="utf-8")
    if "metrics" in request["slots"]:
        outputs["metrics"] = str(metrics)
    (directory / "outputs.json").write_text(json.dumps(outputs), encoding="utf-8")


if __name__ == "__main__":
    render(json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text(encoding="utf-8")))
