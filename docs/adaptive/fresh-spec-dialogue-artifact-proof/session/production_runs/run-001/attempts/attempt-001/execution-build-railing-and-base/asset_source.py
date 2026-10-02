import bpy
import math
from mathutils import Vector


def build_asset():
    BASE_WIDTH = 6.15
    BASE_HEIGHT = 0.55
    BASE_DEPTH = 0.65
    RAIL_WIDTH = 6.0
    RAIL_HEIGHT = 1.05
    TUBE_DIAMETER = 0.065
    OPENING_WIDTH = 0.48
    OPENING_HEIGHT = 0.18
    OPENING_CENTERS = (-0.55, 0.55)
    TOP_Z = BASE_HEIGHT + RAIL_HEIGHT - TUBE_DIAMETER / 2
    MIDDLE_Z = 1.015
    BOTTOM_Z = 0.675
    POST_X = RAIL_WIDTH / 2 - 0.04
    INSET_X = POST_X - 0.145
    APEX_Z = 1.315

    collection = bpy.data.collections.new('White_railing_and_concrete_base')
    bpy.context.scene.collection.children.link(collection)
    root = bpy.data.objects.new('Railing_base_assembly', None)
    collection.objects.link(root)
    root['dimension_authority'] = 'Nominal meters inferred from photograph; not measured dimensions'
    root['base_dimensions_m'] = [BASE_WIDTH, BASE_DEPTH, BASE_HEIGHT]
    root['rail_width_m'] = RAIL_WIDTH
    root['rail_height_above_base_m'] = RAIL_HEIGHT
    root['horizontal_rail_heights_m'] = [BOTTOM_Z, MIDDLE_Z, TOP_Z]
    root['opening_width_m'] = OPENING_WIDTH
    root['opening_height_m'] = OPENING_HEIGHT
    root['opening_center_x_m'] = list(OPENING_CENTERS)
    root['hidden_geometry'] = 'Inferred constant base depth, full-depth bottom passages, cylindrical tubes and embedded post joints'
    root['orientation'] = 'Width X; height Z; front negative Y; base bottom Z=0'
    root['scope'] = 'White railing and concrete base only; curb and surroundings excluded'

    def material(name, color, roughness, metallic):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        mat.diffuse_color = (*color, 1.0)
        shader = mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (*color, 1.0)
        shader.inputs['Metallic'].default_value = metallic
        shader.inputs['Roughness'].default_value = roughness
        return mat

    metal = material('Metal_off_white_painted', (0.86, 0.87, 0.83), 0.38, 0.12)
    concrete = material('Concrete_gray_white', (0.62, 0.635, 0.60), 0.91, 0.0)
    concrete_top = material('Concrete_subtle_top_tone', (0.52, 0.54, 0.505), 0.94, 0.0)

    def mesh_object(name, vertices, faces, mat=None):
        mesh = bpy.data.meshes.new(name + '_mesh')
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        obj.parent = root
        if mat is not None:
            mesh.materials.append(mat)
        return obj

    def box(name, dimensions, location, mat=None):
        x, y, z = (d / 2 for d in dimensions)
        vertices = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
                    (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
        faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                 (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        obj = mesh_object(name, vertices, faces, mat)
        obj.location = location
        return obj

    def apply_modifier(obj, modifier):
        for selected in list(bpy.context.selected_objects):
            selected.select_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        obj.select_set(False)

    base = box('Concrete_base_two_open_passages',
               (BASE_WIDTH, BASE_DEPTH, BASE_HEIGHT),
               (0, 0, BASE_HEIGHT / 2), concrete)
    base.data.materials.append(concrete_top)
    for index, center in enumerate(OPENING_CENTERS, 1):
        cutter = box('Temporary_passage_cutter_' + str(index),
                     (OPENING_WIDTH, BASE_DEPTH + 0.30, OPENING_HEIGHT + 0.08),
                     (center, 0, (OPENING_HEIGHT - 0.08) / 2))
        modifier = base.modifiers.new('Actual_bottom_open_passage_' + str(index), 'BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.solver = 'EXACT'
        modifier.object = cutter
        apply_modifier(base, modifier)
        cutter_mesh = cutter.data
        bpy.data.objects.remove(cutter, do_unlink=True)
        if cutter_mesh.users == 0:
            bpy.data.meshes.remove(cutter_mesh)

    bevel = base.modifiers.new('Modest_concrete_edge_refinement', 'BEVEL')
    bevel.width = 0.006
    bevel.segments = 3
    bevel.limit_method = 'ANGLE'
    apply_modifier(base, bevel)
    base.data.update()
    for polygon in base.data.polygons:
        polygon.material_index = 1 if polygon.normal.z > 0.995 else 0
        polygon.use_smooth = False
    uv = base.data.uv_layers.new(name='Concrete_planar_UV')
    for polygon in base.data.polygons:
        normal = polygon.normal
        axis = max(range(3), key=lambda i: abs(normal[i]))
        for loop_index in polygon.loop_indices:
            point = base.data.vertices[base.data.loops[loop_index].vertex_index].co
            if axis == 2:
                value = (point.x, point.y)
            elif axis == 1:
                value = (point.x, point.z)
            else:
                value = (point.y, point.z)
            uv.data[loop_index].uv = value
    base['passage_construction'] = 'Two boolean voids open at bottom and through the full inferred depth; no black inserts'

    def tube(name, points, radius, sides=32):
        points = [Vector(point) for point in points]
        vertices = []
        distances = [0.0]
        for i in range(1, len(points)):
            distances.append(distances[-1] + (points[i] - points[i - 1]).length)
        for i, point in enumerate(points):
            if i == 0:
                tangent = points[1] - point
            elif i == len(points) - 1:
                tangent = point - points[i - 1]
            else:
                tangent = points[i + 1] - points[i - 1]
            tangent.normalize()
            radial_a = Vector((0, 1, 0))
            radial_b = tangent.cross(radial_a).normalized()
            for j in range(sides):
                angle = 2 * math.pi * j / sides
                offset = radius * (math.cos(angle) * radial_a + math.sin(angle) * radial_b)
                vertices.append(tuple(point + offset))
        faces = []
        face_uvs = []
        for i in range(len(points) - 1):
            for j in range(sides):
                following = (j + 1) % sides
                faces.append((i * sides + j, i * sides + following,
                              (i + 1) * sides + following, (i + 1) * sides + j))
                face_uvs.append([(j / sides, distances[i]),
                                 ((j + 1) / sides, distances[i]),
                                 ((j + 1) / sides, distances[i + 1]),
                                 (j / sides, distances[i + 1])])
        start_cap = tuple(reversed(range(sides)))
        end_cap = tuple((len(points) - 1) * sides + j for j in range(sides))
        faces.extend([start_cap, end_cap])
        for cap in (start_cap, end_cap):
            face_uvs.append([(0.5 + 0.5 * math.cos(2 * math.pi * (v % sides) / sides),
                              0.5 + 0.5 * math.sin(2 * math.pi * (v % sides) / sides)) for v in cap])
        obj = mesh_object(name, vertices, faces, metal)
        uv_layer = obj.data.uv_layers.new(name='Tube_length_and_circumference_UV')
        for polygon, values in zip(obj.data.polygons, face_uvs):
            polygon.use_smooth = polygon.index < len(faces) - 2
            for loop_index, value in zip(polygon.loop_indices, values):
                uv_layer.data[loop_index].uv = value
        return obj

    for side, label in ((-1, 'Left'), (1, 'Right')):
        x = side * POST_X
        tube('Metal_' + label + '_main_post',
             [(x, 0, BASE_HEIGHT - 0.035), (x, 0, BASE_HEIGHT + RAIL_HEIGHT)], 0.04)
        tube('Metal_' + label + '_embedded_foot_collar',
             [(x, 0, BASE_HEIGHT - 0.008), (x, 0, BASE_HEIGHT + 0.048)], 0.051)
        tube('Metal_' + label + '_inset_end_upright',
             [(side * INSET_X, 0, BOTTOM_Z), (side * INSET_X, 0, TOP_Z)], 0.027)

    tube('Metal_top_horizontal_rail', [(-POST_X, 0, TOP_Z), (POST_X, 0, TOP_Z)], TUBE_DIAMETER / 2)
    tube('Metal_middle_horizontal_rail', [(-POST_X, 0, MIDDLE_Z), (POST_X, 0, MIDDLE_Z)], 0.028)
    tube('Metal_bottom_horizontal_rail', [(-POST_X, 0, BOTTOM_Z), (POST_X, 0, BOTTOM_Z)], TUBE_DIAMETER / 2)

    def bezier_points(controls, segments):
        a, b, c, d = [Vector(value) for value in controls]
        result = []
        for i in range(segments + 1):
            t = i / segments
            q = 1 - t
            result.append(tuple(q ** 3 * a + 3 * q * q * t * b + 3 * q * t * t * c + t ** 3 * d))
        return result

    for side, label in ((-1, 'Left'), (1, 'Right')):
        outer = [(side * 1.36, 0, TOP_Z),
                 (side * 0.98, 0, 1.455),
                 (side * 0.40, 0, 1.13),
                 (side * 0.11, 0, BOTTOM_Z)]
        inner = [(0, 0, APEX_Z),
                 (side * 0.06, 0, 1.245),
                 (side * 0.38, 0, 1.09),
                 (side * 0.058, 0, BOTTOM_Z)]
        outer_obj = tube('Metal_center_' + label + '_broad_sweeping_curve',
                         bezier_points(outer, 72), 0.023)
        inner_obj = tube('Metal_center_' + label + '_inner_rising_branch',
                         bezier_points(inner, 56), 0.023)
        outer_obj['control_points_xz'] = [coordinate for point in outer for coordinate in (point[0], point[2])]
        inner_obj['control_points_xz'] = [coordinate for point in inner for coordinate in (point[0], point[2])]

    tube('Metal_center_slender_vertical_connection',
         [(0, 0, BOTTOM_Z), (0, 0, APEX_Z + 0.006)], 0.021)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.031,
                                       location=(0, 0, APEX_Z))
    junction = bpy.context.object
    junction.name = 'Metal_center_rounded_apex_junction'
    junction.data.name = junction.name + '_mesh'
    for existing_collection in list(junction.users_collection):
        existing_collection.objects.unlink(junction)
    collection.objects.link(junction)
    junction.parent = root
    junction.data.materials.append(metal)
    for polygon in junction.data.polygons:
        polygon.use_smooth = True
    junction.select_set(False)
    root['ornament_interpretation'] = 'Paired broad upper-to-lower sweeps, paired inner branches rising to an elevated central junction, and slender descending center connection; open spaces remain unfilled'
    bpy.context.view_layer.update()
    return root
