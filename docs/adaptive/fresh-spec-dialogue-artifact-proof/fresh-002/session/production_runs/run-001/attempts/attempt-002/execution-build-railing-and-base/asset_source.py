import bpy
import math
from mathutils import Vector


def build_asset():
    P = {
        'base_width': 3.0,
        'base_depth': 0.44,
        'base_height': 0.32,
        'railing_span': 2.86,
        'railing_height': 0.55,
        'post_radius': 0.027,
        'rail_radius': 0.021,
        'decoration_radius': 0.016,
        'bottom_rail_height': 0.397,
        'middle_rail_height': 0.620,
        'central_vertical_height': 0.316,
        'fan_outer_control_points': [(0.035, 0.397), (0.115, 0.570), (0.335, 0.770), (0.610, 0.870)],
        'fan_inner_control_points': [(0.080, 0.397), (0.115, 0.490), (0.255, 0.600), (0.390, 0.620)],
        'recess_centers': [-0.270, 0.270],
        'recess_width': 0.250,
        'recess_height': 0.090,
        'recess_depth': 0.135,
    }
    objects = []

    def material(name, color, metallic, roughness):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        mat.diffuse_color = (*color, 1.0)
        shader = mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (*color, 1.0)
        shader.inputs['Metallic'].default_value = metallic
        shader.inputs['Roughness'].default_value = roughness
        return mat

    paint = material('Railing_White_Painted_Metal', (0.84, 0.855, 0.825), 0.16, 0.36)
    concrete = material('Base_Gray_White_Concrete', (0.59, 0.605, 0.575), 0.0, 0.88)

    def mesh_object(name, vertices, faces, mat):
        mesh = bpy.data.meshes.new(name + '_Mesh')
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.data.materials.append(mat)
        objects.append(obj)
        return obj

    def bevel(obj, width):
        mod = obj.modifiers.new('Small_Manufactured_Edge_Rounding', 'BEVEL')
        mod.width = width
        mod.segments = 3
        mod.limit_method = 'ANGLE'
        mod.angle_limit = math.radians(35.0)
        mod.use_clamp_overlap = True

    def tube(name, points, radius, segments=32):
        points = [Vector(p) for p in points]
        vertices = []
        faces = []
        for i, point in enumerate(points):
            if i == 0:
                tangent = (points[1] - point).normalized()
            elif i == len(points) - 1:
                tangent = (point - points[i - 1]).normalized()
            else:
                tangent = (points[i + 1] - points[i - 1]).normalized()
            normal = Vector((0.0, 1.0, 0.0))
            binormal = tangent.cross(normal).normalized()
            for j in range(segments):
                angle = 2.0 * math.pi * j / segments
                vertex = point + radius * (math.cos(angle) * normal + math.sin(angle) * binormal)
                vertices.append(tuple(vertex))
        for i in range(len(points) - 1):
            for j in range(segments):
                next_j = (j + 1) % segments
                faces.append((i * segments + j, i * segments + next_j,
                              (i + 1) * segments + next_j, (i + 1) * segments + j))
        side_count = len(faces)
        start_center = len(vertices)
        vertices.append(tuple(points[0]))
        end_center = len(vertices)
        vertices.append(tuple(points[-1]))
        last_ring = (len(points) - 1) * segments
        for j in range(segments):
            next_j = (j + 1) % segments
            faces.append((start_center, next_j, j))
            faces.append((end_center, last_ring + j, last_ring + next_j))
        obj = mesh_object(name, vertices, faces, paint)
        for polygon in obj.data.polygons:
            polygon.use_smooth = polygon.index < side_count
        return obj

    def bezier(control_points, t):
        a, b, c, d = [Vector(p) for p in control_points]
        u = 1.0 - t
        return u * u * u * a + 3.0 * u * u * t * b + 3.0 * u * t * t * c + t * t * t * d

    def curved_tube(name, control_points, radius):
        points = [bezier(control_points, i / 64.0) for i in range(65)]
        return tube(name, points, radius)

    # One continuous solid with two bottom-edge recesses on its -Y front.
    half_width = P['base_width'] / 2.0
    half_depth = P['base_depth'] / 2.0
    half_recess = P['recess_width'] / 2.0
    left_center, right_center = P['recess_centers']
    xs = [-half_width, left_center - half_recess, left_center + half_recess,
          right_center - half_recess, right_center + half_recess, half_width]
    ys = [-half_depth, -half_depth + P['recess_depth'], half_depth]
    zs = [0.0, P['recess_height'], P['base_height']]
    solid = set()
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            for k in range(len(zs) - 1):
                if not (j == 0 and k == 0 and i in (1, 3)):
                    solid.add((i, j, k))
    base_vertices = []
    base_faces = []
    vertex_indices = {}

    def base_vertex(index):
        if index not in vertex_indices:
            i, j, k = index
            vertex_indices[index] = len(base_vertices)
            base_vertices.append((xs[i], ys[j], zs[k]))
        return vertex_indices[index]

    for i, j, k in sorted(solid):
        surfaces = [
            ((i - 1, j, k), [(i, j, k), (i, j, k + 1), (i, j + 1, k + 1), (i, j + 1, k)]),
            ((i + 1, j, k), [(i + 1, j, k), (i + 1, j + 1, k), (i + 1, j + 1, k + 1), (i + 1, j, k + 1)]),
            ((i, j - 1, k), [(i, j, k), (i + 1, j, k), (i + 1, j, k + 1), (i, j, k + 1)]),
            ((i, j + 1, k), [(i, j + 1, k), (i, j + 1, k + 1), (i + 1, j + 1, k + 1), (i + 1, j + 1, k)]),
            ((i, j, k - 1), [(i, j, k), (i, j + 1, k), (i + 1, j + 1, k), (i + 1, j, k)]),
            ((i, j, k + 1), [(i, j, k + 1), (i + 1, j, k + 1), (i + 1, j + 1, k + 1), (i, j + 1, k + 1)]),
        ]
        for neighbor, corners in surfaces:
            if neighbor not in solid:
                base_faces.append(tuple(base_vertex(corner) for corner in corners))
    base = mesh_object('Concrete_Base_With_Two_Front_Bottom_Recesses', base_vertices, base_faces, concrete)
    bevel(base, 0.003)

    post_x = P['railing_span'] / 2.0
    top_z = P['base_height'] + P['railing_height']
    bottom_z = P['bottom_rail_height']
    middle_z = P['middle_rail_height']
    apex_z = bottom_z + P['central_vertical_height']

    for side, label in [(-1.0, 'Left'), (1.0, 'Right')]:
        x = side * post_x
        post = tube('Railing_' + label + '_End_Post',
                    [(x, 0.0, P['base_height'] - 0.024), (x, 0.0, top_z + 0.012)],
                    P['post_radius'])
        bevel(post, 0.0012)
        sleeve = tube('Railing_' + label + '_Base_Socket',
                      [(x, 0.0, P['base_height'] - 0.008), (x, 0.0, P['base_height'] + 0.043)],
                      P['post_radius'] + 0.004)
        bevel(sleeve, 0.0010)

    tube('Railing_Top_Horizontal', [(-post_x, 0.0, top_z), (post_x, 0.0, top_z)], P['rail_radius'])
    tube('Railing_Bottom_Horizontal', [(-post_x, 0.0, bottom_z), (post_x, 0.0, bottom_z)], P['rail_radius'])

    outer_positive = [(x, 0.0, z) for x, z in P['fan_outer_control_points']]
    low, high = 0.0, 1.0
    for _ in range(48):
        mid = (low + high) / 2.0
        if bezier(outer_positive, mid).z < middle_z:
            low = mid
        else:
            high = mid
    middle_join_x = bezier(outer_positive, (low + high) / 2.0).x

    # The middle member stops at the fan on each side, leaving the center open.
    tube('Railing_Left_Middle_Horizontal',
         [(-post_x, 0.0, middle_z), (-middle_join_x, 0.0, middle_z)], P['rail_radius'])
    tube('Railing_Right_Middle_Horizontal',
         [(middle_join_x, 0.0, middle_z), (post_x, 0.0, middle_z)], P['rail_radius'])

    for side, label in [(-1.0, 'Left'), (1.0, 'Right')]:
        outer = [(side * x, 0.0, z) for x, z in P['fan_outer_control_points']]
        inner = [(side * x, 0.0, z) for x, z in P['fan_inner_control_points']]
        curved_tube('Fan_' + label + '_Outer_Curved_Tube', outer, P['decoration_radius'])
        curved_tube('Fan_' + label + '_Inner_Curved_Tube', inner, P['decoration_radius'])
        crown_link = [
            (0.0, 0.0, apex_z),
            (side * 0.060, 0.0, apex_z - 0.016),
            (side * middle_join_x * 0.79, 0.0, middle_z + 0.035),
            (side * middle_join_x, 0.0, middle_z),
        ]
        curved_tube('Fan_' + label + '_Central_Sloping_Join', crown_link, P['decoration_radius'])

    tube('Fan_Central_Vertical', [(0.0, 0.0, bottom_z), (0.0, 0.0, apex_z)], P['decoration_radius'])
    return {'objects': [obj.name for obj in objects], 'construction_parameters': P}
