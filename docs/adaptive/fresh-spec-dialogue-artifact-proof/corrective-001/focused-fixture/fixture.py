import bpy
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for name,x,color,roughness,metallic in [('WhitePaint',-1.8,(0.86,0.87,0.83),0.38,0.12),('GrayConcrete',1.8,(0.38,0.40,0.36),0.91,0.0)]:
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    s=mat.node_tree.nodes['Principled BSDF']
    s.inputs['Base Color'].default_value=(*color,1)
    s.inputs['Roughness'].default_value=roughness;s.inputs['Metallic'].default_value=metallic
    bpy.ops.mesh.primitive_cube_add(size=2,location=(x,0,1));o=bpy.context.object;o.name=name
    o.data.materials.append(mat)
bpy.ops.export_scene.gltf(filepath='C:\\Users\\Worker\\Documents\\Codex\\2026-10-02\\codex-specification-dialogue-human-blocking-text\\work\\diagnostic-host-fix-fixture\\fixture.glb',export_format='GLB',export_apply=True)
