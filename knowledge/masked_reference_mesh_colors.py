"""Bound native SaveGLB checkpoint import and mask-driven reference RGB projection."""
import copy
import json
import math
from pathlib import Path
import struct
import numpy as np
import torch
from scipy.spatial import cKDTree


def read_native_glb(path):
    """Read only the single, untransformed triangle mesh emitted by native SaveGLB."""
    raw = Path(path).read_bytes()
    magic, version, length = struct.unpack_from('<III', raw)
    assert magic == 0x46546C67 and version == 2 and length == len(raw), 'NATIVE_GLB_HEADER'
    offset, chunks = 12, {}
    while offset < len(raw):
        size, kind = struct.unpack_from('<II', raw, offset)
        offset += 8
        assert offset + size <= len(raw) and kind not in chunks, 'NATIVE_GLB_CHUNKS'
        chunks[kind] = raw[offset:offset+size]
        offset += size
    data = json.loads(chunks[0x4E4F534A])
    assert data['nodes'] == [{'mesh': 0}] and len(data['meshes']) == 1, 'NATIVE_UNTRANSFORMED_MESH_REQUIRED'
    primitive, = data['meshes'][0]['primitives']
    assert primitive.get('mode', 4) == 4, 'NATIVE_TRIANGLES_REQUIRED'
    blob = chunks[0x004E4942]
    def accessor(index, types, components):
        a = data['accessors'][index]
        assert a['type'] == types and a['componentType'] in components and 'sparse' not in a, 'NATIVE_ACCESSOR'
        view = data['bufferViews'][a['bufferView']]
        assert view.get('buffer', 0) == 0 and 'byteStride' not in view, 'NATIVE_CONTIGUOUS_BUFFER_REQUIRED'
        dtype, width = components[a['componentType']], {'VEC3': 3, 'SCALAR': 1}[types]
        start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
        count = a['count'] * width
        assert start + count*np.dtype(dtype).itemsize <= len(blob), 'NATIVE_BUFFER_RANGE'
        return np.frombuffer(blob, dtype=dtype, count=count, offset=start).copy().reshape(-1, width)
    vertices = accessor(primitive['attributes']['POSITION'], 'VEC3', {5126: '<f4'})
    faces = accessor(primitive['indices'], 'SCALAR', {5125: '<u4', 5123: '<u2'}).reshape(-1, 3).astype(np.int64)
    assert len(vertices) and len(faces) and np.isfinite(vertices).all(), 'NATIVE_NONEMPTY_MESH'
    assert faces.min() >= 0 and faces.max() < len(vertices), 'NATIVE_FACE_RANGE'
    return torch.from_numpy(vertices).unsqueeze(0), torch.from_numpy(faces).unsqueeze(0)


class LoopCoreLoadMesh:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'geometry_file': ('STRING', {'default': ''})}}
    RETURN_TYPES = ('MESH',)
    FUNCTION = 'load'
    CATEGORY = '3d/loading'
    def load(self, geometry_file):
        import folder_paths
        from comfy_api.latest import Types
        root = Path(folder_paths.get_input_directory()).resolve()
        path = (root / geometry_file).resolve()
        assert path.is_relative_to(root) and path.suffix.lower() == '.glb', 'BOUND_INPUT_GLB_REQUIRED'
        vertices, faces = read_native_glb(path)
        return (Types.MESH(vertices, faces),)
    @classmethod
    def IS_CHANGED(cls, geometry_file):
        import folder_paths, hashlib
        root = Path(folder_paths.get_input_directory()).resolve()
        path = (root / geometry_file).resolve()
        assert path.is_relative_to(root), 'BOUND_INPUT_GLB_REQUIRED'
        return hashlib.sha256(path.read_bytes()).hexdigest()


class MaskedReferenceMeshColors:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'mesh': ('MESH',), 'reference_image': ('IMAGE',), 'foreground_mask': ('IMAGE',),
            'horizontal_axis': (['X', 'Y', 'Z'], {'default': 'X'}),
            'vertical_axis': (['X', 'Y', 'Z'], {'default': 'Y'}),
            'view_angle': ('FLOAT', {'default': 0.0, 'min': -180.0, 'max': 180.0}),
            'mask_threshold': ('FLOAT', {'default': 0.8, 'min': 0.0, 'max': 1.0}),
            'white_threshold': ('FLOAT', {'default': 0.65, 'min': 0.0, 'max': 1.0}),
            'flip_horizontal': ('BOOLEAN', {'default': False})}}
    RETURN_TYPES = ('MESH',)
    FUNCTION = 'paint'
    CATEGORY = '3d/texturing'
    DESCRIPTION = 'Projects actual masked source RGB onto existing geometry without shape changes. Orthographic bbox approximation; hidden surfaces share source projection. Independent Review required.'
    def paint(self, mesh, reference_image, foreground_mask, horizontal_axis, vertical_axis,
              view_angle, mask_threshold, white_threshold, flip_horizontal):
        assert horizontal_axis != vertical_axis, 'PROJECTION_AXES_MUST_DIFFER'
        assert mesh.vertices.shape[0] == 1 and mesh.faces.shape[0] == 1, 'ONE_NATIVE_MESH_REQUIRED'
        rgb = reference_image[0, ..., :3].detach().cpu().numpy()
        mask = foreground_mask[0, ..., 0].detach().cpu().numpy()
        assert rgb.shape[:2] == mask.shape and np.isfinite(rgb).all() and np.isfinite(mask).all(), 'MASK_IMAGE_ALIGNMENT'
        foreground = mask > mask_threshold
        bounds = np.argwhere(foreground)
        assert len(bounds), 'EMPTY_REFERENCE_MASK'
        lo, hi = bounds.min(axis=0), bounds.max(axis=0)
        # Bright antialiased background pixels cannot become projection candidates.
        pixels = np.argwhere(foreground & (rgb.min(axis=-1) < white_threshold))
        assert len(pixels), 'NO_MASKED_SOURCE_RGB'
        vertices = mesh.vertices[0].detach().cpu().numpy()
        axes = {'X': 0, 'Y': 1, 'Z': 2}
        h, v = axes[horizontal_axis], axes[vertical_axis]
        d = next(i for i in range(3) if i not in {h, v})
        angle = math.radians(view_angle)
        x = vertices[:, h]*math.cos(angle) - vertices[:, d]*math.sin(angle)
        y = vertices[:, v]
        assert np.ptp(x) > 0 and np.ptp(y) > 0, 'NONFLAT_PROJECTION_REQUIRED'
        u = (x-x.min()) / np.ptp(x)
        if flip_horizontal: u = 1-u
        row = lo[0] + (1-(y-y.min())/np.ptp(y))*(hi[0]-lo[0])
        col = lo[1] + u*(hi[1]-lo[1])
        _, nearest = cKDTree(pixels).query(np.column_stack([row, col]))
        sample = pixels[nearest]
        result = copy.copy(mesh)
        result.vertex_colors = torch.from_numpy(rgb[sample[:, 0], sample[:, 1]].copy()).clamp(0, 1).pow(2.2).unsqueeze(0)
        assert torch.equal(result.vertices, mesh.vertices) and torch.equal(result.faces, mesh.faces), 'GEOMETRY_CHANGED'
        return (result,)


NODE_CLASS_MAPPINGS = {'LoopCoreLoadMesh': LoopCoreLoadMesh, 'MaskedReferenceMeshColors': MaskedReferenceMeshColors}
