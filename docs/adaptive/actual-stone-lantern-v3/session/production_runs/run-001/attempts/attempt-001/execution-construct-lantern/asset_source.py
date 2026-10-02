import bpy
import math
import random


def build_asset():
    rng = random.Random(137)
    root = bpy.data.objects.new('Stone_Lantern', None)
    bpy.context.scene.collection.objects.link(root)
    root['front_axis'] = '-Y'

    def stone(name, color, roughness=0.90):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        mat.diffuse_color = (*color, 1.0)
        shader = mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (*color, 1.0)
        shader.inputs['Metallic'].default_value = 0.0
        shader.inputs['Roughness'].default_value = roughness
        shader.inputs['Specular IOR Level'].default_value = 0.26
        return mat

    body_mat = stone('Stone_Chamber_Gray', (0.330, 0.340, 0.325))
    rim_mat = stone('Stone_Frame_Gray', (0.355, 0.365, 0.350))
    interior_mat = stone('Stone_Interior_Gray', (0.350, 0.360, 0.345))
    platform_mat = stone('Stone_Platform_Gray', (0.335, 0.345, 0.330))
    base_mats = [
        stone('Stone_Base_Gray', (0.310, 0.320, 0.305)),
        stone('Stone_Base_Subtle_Light', (0.316, 0.326, 0.311), 0.88),
        stone('Stone_Base_Subtle_Dark', (0.304, 0.314, 0.299), 0.93),
    ]
    roof_mats = [
        stone('Stone_Roof_Gray', (0.285, 0.295, 0.280)),
        stone('Stone_Roof_Subtle_Light', (0.291, 0.301, 0.286), 0.88),
        stone('Stone_Roof_Subtle_Dark', (0.279, 0.289, 0.274), 0.93),
    ]

    def activate(obj):
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

    def mesh_object(name, vertices, faces, materials, smooth=False):
        mesh = bpy.data.meshes.new(name + '_Mesh')
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = root
        for mat in materials:
            mesh.materials.append(mat)
        for poly in mesh.polygons:
            poly.use_smooth = smooth
        return obj

    def finish(obj, width=0.006, segments=3, weighted=False):
        activate(obj)
        for poly in obj.data.polygons:
            poly.use_smooth = True
        bevel = obj.modifiers.new('Small_Worn_Edge_Bevel', 'BEVEL')
        bevel.width = width
        bevel.segments = segments
        bevel.limit_method = 'ANGLE'
        bevel.angle_limit = math.radians(35.0)
        bevel.use_clamp_overlap = True
        bevel.harden_normals = True
        bpy.ops.object.modifier_apply(modifier=bevel.name)
        obj.data.update()
        adjacency = {}
        for poly in obj.data.polygons:
            vertices = list(poly.vertices)
            for i in range(len(vertices)):
                key = tuple(sorted((vertices[i], vertices[(i + 1) % len(vertices)])))
                adjacency.setdefault(key, []).append(poly)
        for edge in obj.data.edges:
            linked = adjacency.get(tuple(sorted(edge.vertices)), [])
            edge.use_edge_sharp = (
                len(linked) != 2 or
                linked[0].normal.angle(linked[1].normal, 0.0) > math.radians(55.0)
            )
        if weighted:
            normals = obj.modifiers.new('Architectural_Weighted_Normals', 'WEIGHTED_NORMAL')
            normals.keep_sharp = True
            normals.weight = 50
            bpy.ops.object.modifier_apply(modifier=normals.name)
        return obj

    def block(name, center, dimensions, material, bevel=0.006):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=center)
        obj = bpy.context.object
        obj.name = name
        obj.data.name = name + '_Mesh'
        obj.scale = dimensions
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.parent = root
        obj.data.materials.append(material)
        return finish(obj, bevel, weighted=True)

    def loft(name, profiles, power, materials, wear=0.0):
        count = 96
        phase = rng.uniform(0.0, math.tau)
        vertices = []
        for radius, z, corner_lift in profiles:
            for i in range(count):
                angle = math.tau * i / count
                c, s = math.cos(angle), math.sin(angle)
                variation = wear * (
                    0.55 * math.sin(7.0 * angle + phase) +
                    0.30 * math.sin(13.0 * angle - phase) +
                    0.15 * math.sin(23.0 * angle + 0.4)
                )
                r = radius + variation
                x = r * math.copysign(abs(c) ** (2.0 / power), c)
                y = r * math.copysign(abs(s) ** (2.0 / power), s)
                height = z + corner_lift * math.sin(2.0 * angle) ** 4
                vertices.append((x, y, height))
        faces = [tuple(reversed(range(count)))]
        for row in range(len(profiles) - 1):
            for i in range(count):
                j = (i + 1) % count
                faces.append((row * count + i, row * count + j,
                              (row + 1) * count + j, (row + 1) * count + i))
        last = (len(profiles) - 1) * count
        faces.append(tuple(last + i for i in range(count)))
        obj = mesh_object(name, vertices, faces, materials, True)
        obj.data.polygons[0].use_smooth = False
        obj.data.polygons[-1].use_smooth = False
        return obj

    def subtle_tones(obj):
        if len(obj.data.materials) < 3:
            return
        for poly in obj.data.polygons:
            p = poly.center
            value = (math.sin(7.0 * p.x + 0.7) +
                     math.sin(6.0 * p.y - 0.3) +
                     0.45 * math.sin(9.0 * p.z))
            poly.material_index = 1 if value > 1.05 else (2 if value < -1.05 else 0)

    # A rounded, splayed pedestal becomes four connected supports after
    # subtracting two perpendicular, full-through arch tunnels.
    base_profiles = [
        (0.764, 0.000, 0.0), (0.775, 0.034, 0.0),
        (0.760, 0.080, 0.0), (0.740, 0.135, 0.0),
        (0.716, 0.205, 0.0), (0.688, 0.280, 0.0),
        (0.658, 0.360, 0.0), (0.619, 0.440, 0.0),
        (0.582, 0.505, 0.0), (0.554, 0.565, 0.0),
        (0.536, 0.620, 0.0), (0.523, 0.670, 0.0),
        (0.500, 0.712, 0.0),
    ]
    base = loft('Base_Four_Arched_Supports', base_profiles, 3.8, base_mats, 0.0018)

    def arch_cutter(axis):
        radius = 0.285
        spring = 0.255
        profile = [(-0.355, -0.10), (0.355, -0.10), (radius, spring)]
        for i in range(1, 41):
            angle = math.pi * i / 40
            profile.append((radius * math.cos(angle), spring + radius * math.sin(angle)))
        count = len(profile)
        vertices = []
        for axial in (-1.30, 1.30):
            for u, z in profile:
                vertices.append((u, axial, z) if axis == 'Y' else (axial, -u, z))
        faces = [tuple(range(count)), tuple(reversed(range(count, 2 * count)))]
        for i in range(count):
            j = (i + 1) % count
            faces.append((i, count + i, count + j, j))
        cutter = mesh_object('_Temporary_Arch_' + axis, vertices, faces, [base_mats[0]])
        for i in range(count):
            cutter.data.polygons[2 + i].use_smooth = 2 <= i < count - 1
        return cutter

    for axis in ('Y', 'X'):
        cutter = arch_cutter(axis)
        activate(base)
        modifier = base.modifiers.new('Through_Arch_' + axis, 'BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.solver = 'EXACT'
        modifier.object = cutter
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        cutter_mesh = cutter.data
        bpy.data.objects.remove(cutter, do_unlink=True)
        bpy.data.meshes.remove(cutter_mesh)
    finish(base, 0.008, 3)
    subtle_tones(base)

    block('Platform_Lower_Bearing', (0.0, 0.0, 0.731),
          (1.29, 1.25, 0.072), platform_mat, 0.012)
    block('Platform_Projecting_Slab', (0.0, 0.0, 0.806),
          (1.42, 1.36, 0.110), platform_mat, 0.014)

    # The front wall is a closed annular solid, not a panel with painted darkness.
    # Front faces point toward -Y. The aperture remains square through its depth.
    def rectangular_ring(name, width, z_low, z_high, opening, center_z,
                         y_front, y_back, materials, bevel):
        outer = [(-width / 2, z_low), (width / 2, z_low),
                 (width / 2, z_high), (-width / 2, z_high)]
        inner = [(-opening / 2, center_z - opening / 2),
                 (opening / 2, center_z - opening / 2),
                 (opening / 2, center_z + opening / 2),
                 (-opening / 2, center_z + opening / 2)]
        vertices = []
        for y in (y_front, y_back):
            vertices.extend((x, y, z) for x, z in outer)
            vertices.extend((x, y, z) for x, z in inner)
        faces = []
        for i in range(4):
            j = (i + 1) % 4
            faces.extend([
                (i, j, 4 + j, 4 + i),
                (8 + i, 12 + i, 12 + j, 8 + j),
                (i, 8 + i, 8 + j, j),
                (4 + i, 4 + j, 12 + j, 12 + i),
            ])
        obj = mesh_object(name, vertices, faces, materials)
        if len(materials) > 1:
            for i in range(4):
                obj.data.polygons[4 * i + 3].material_index = 1
        return finish(obj, bevel, weighted=True)

    rectangular_ring('Chamber_Front_Full_Depth_Aperture_Wall',
                     0.830, 0.853, 1.415, 0.345, 1.155,
                     -0.415, -0.305, [body_mat, interior_mat], 0.005)
    rectangular_ring('Chamber_Square_Aperture_Stone_Frame',
                     0.490, 0.910, 1.400, 0.345, 1.155,
                     -0.446, -0.404, [rim_mat], 0.0035)

    # Solid side and rear walls conservatively close a spacious hollow chamber.
    # The rear wall is 0.72 units behind the front wall's outer face.
    block('Chamber_Left_Wall', (-0.360, 0.0475, 1.134),
          (0.110, 0.735, 0.562), body_mat, 0.005)
    block('Chamber_Right_Wall', (0.360, 0.0475, 1.134),
          (0.110, 0.735, 0.562), body_mat, 0.005)
    block('Chamber_Rear_Wall', (0.0, 0.360, 1.134),
          (0.830, 0.110, 0.562), interior_mat, 0.005)
    block('Chamber_Interior_Floor', (0.0, 0.0, 0.886),
          (0.660, 0.660, 0.064), interior_mat, 0.003)
    block('Chamber_Ceiling_Roof_Bearing', (0.0, 0.0, 1.406),
          (0.904, 0.904, 0.044), body_mat, 0.006)
    for sx in (-1, 1):
        for sy in (-1, 1):
            block('Chamber_Corner_Pier_' + ('L' if sx < 0 else 'R') +
                  ('_Front' if sy < 0 else '_Rear'),
                  (sx * 0.397, sy * 0.397, 1.133),
                  (0.089, 0.089, 0.554), body_mat, 0.007)

    # Low swept roof: a thin broad eave, modest corner lift and rounded hips.
    roof_profiles = [
        (0.450, 1.391, 0.000), (0.650, 1.398, 0.002),
        (0.860, 1.414, 0.005), (1.015, 1.433, 0.015),
        (1.030, 1.457, 0.020), (0.970, 1.464, 0.017),
        (0.860, 1.474, 0.013), (0.730, 1.507, 0.010),
        (0.600, 1.557, 0.006), (0.480, 1.615, 0.003),
        (0.350, 1.672, 0.000), (0.240, 1.711, 0.000),
        (0.170, 1.728, 0.000),
    ]
    roof = loft('Roof_Broad_Flared_Stone_Eaves', roof_profiles, 3.4, roof_mats, 0.0012)
    finish(roof, 0.003, 2)
    subtle_tones(roof)

    disc = loft('Cap_Low_Stacked_Stone_Disc', [
        (0.230, 1.700, 0.0), (0.300, 1.717, 0.0),
        (0.327, 1.735, 0.0), (0.331, 1.756, 0.0),
        (0.310, 1.777, 0.0), (0.220, 1.794, 0.0),
        (0.170, 1.797, 0.0),
    ], 2.0, roof_mats, 0.0006)
    finish(disc, 0.002, 2)
    subtle_tones(disc)
    finial = loft('Cap_Small_Rounded_Finial', [
        (0.146, 1.782, 0.0), (0.151, 1.815, 0.0),
        (0.128, 1.855, 0.0), (0.132, 1.890, 0.0),
        (0.116, 1.938, 0.0), (0.075, 1.976, 0.0),
        (0.026, 2.000, 0.0),
    ], 2.0, roof_mats, 0.0005)
    finish(finial, 0.002, 2)
    subtle_tones(finial)

    activate(root)
    return root
