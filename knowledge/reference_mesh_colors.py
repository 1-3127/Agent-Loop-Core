"""Reference RGB projection on an existing native mesh; no shape/model changes."""
import copy
import math
import numpy as np
import torch
from scipy.spatial import cKDTree


class ReferenceImageMeshColors:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'mesh': ('MESH',), 'front_image': ('IMAGE',),
                'horizontal_axis': (['X', 'Y', 'Z'], {'default': 'X'}),
                'vertical_axis': (['X', 'Y', 'Z'], {'default': 'Y'}),
                'white_threshold': ('FLOAT', {'default': 0.97, 'min': 0.5, 'max': 1.0}),
                'left_angle': ('FLOAT', {'default': 45.0, 'min': -180.0, 'max': 180.0}),
                'right_angle': ('FLOAT', {'default': -45.0, 'min': -180.0, 'max': 180.0})},
                'optional': {'left_image': ('IMAGE',), 'back_image': ('IMAGE',), 'right_image': ('IMAGE',)}}

    RETURN_TYPES = ('MESH',)
    FUNCTION = 'paint'
    CATEGORY = '3d/texturing'
    DESCRIPTION = ('Projects actual foreground RGB from white-background current reference views onto existing mesh vertices. '
                   'Preserves vertices/faces; hidden and occluded colors are approximations, not texture-model inference or quality proof.')

    def paint(self, mesh, front_image, horizontal_axis, vertical_axis, white_threshold,
              left_angle, right_angle, left_image=None, back_image=None, right_image=None):
        assert horizontal_axis != vertical_axis, 'PROJECTION_AXES_MUST_DIFFER'
        assert isinstance(mesh.vertices, torch.Tensor) and mesh.vertices.shape[0] == 1, 'ONE_NATIVE_MESH_REQUIRED'
        vertices = mesh.vertices[0].detach().cpu().float()
        faces = mesh.faces[0].detach().cpu().long()
        assert vertices.shape[0] and faces.shape[0], 'EMPTY_NATIVE_MESH'
        axis = {'X': 0, 'Y': 1, 'Z': 2}
        h, v = axis[horizontal_axis], axis[vertical_axis]
        d = next(i for i in range(3) if i not in {h, v})
        normals = torch.zeros_like(vertices)
        tri = vertices[faces]
        face_normals = torch.linalg.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0])
        for corner in range(3): normals.index_add_(0, faces[:, corner], face_normals)
        normals = torch.nn.functional.normalize(normals, dim=-1)
        y = vertices[:, v].numpy()
        yspan = float(np.ptp(y))
        assert yspan > 0, 'FLAT_VERTICAL_PROJECTION'
        rgb_candidates, confidence = [], []
        views = [(front_image, 0.0), (left_image, left_angle), (back_image, 180.0), (right_image, right_angle)]
        for image, angle in views:
            if image is None: continue
            rgb = image[0, ..., :3].detach().cpu().numpy()
            assert np.isfinite(rgb).all(), 'NONFINITE_REFERENCE_RGB'
            foreground = rgb.min(axis=-1) < white_threshold
            pixels = np.argwhere(foreground)
            assert len(pixels) > 0, 'NO_REFERENCE_FOREGROUND'
            lo, hi = pixels.min(axis=0), pixels.max(axis=0)
            rad = math.radians(angle)
            x = (vertices[:, h]*math.cos(rad) - vertices[:, d]*math.sin(rad)).numpy()
            xspan = float(np.ptp(x))
            assert xspan > 0, 'FLAT_HORIZONTAL_PROJECTION'
            row = lo[0] + (1-(y-y.min())/yspan)*(hi[0]-lo[0])
            col = lo[1] + (x-x.min())/xspan*(hi[1]-lo[1])
            # A vertex projected into a white gap samples the closest real foreground pixel.
            distance, nearest = cKDTree(pixels).query(np.column_stack([row, col]))
            sample = pixels[nearest]
            rgb_candidates.append(rgb[sample[:, 0], sample[:, 1]])
            view_direction = torch.zeros(3)
            view_direction[h], view_direction[d] = -math.sin(rad), -math.cos(rad)
            visibility = (normals @ view_direction).clamp(min=0).numpy()
            confidence.append((visibility+0.03)/(1+distance))
        candidates = np.stack(rgb_candidates)
        weight = np.stack(confidence)
        winner = weight.argmax(axis=0)
        projected = candidates[winner, np.arange(len(vertices))]
        out_mesh = copy.copy(mesh)
        # Matches installed native PaintMesh's sRGB -> linear GLTF convention.
        out_mesh.vertex_colors = torch.from_numpy(np.clip(projected, 0, 1).copy()).pow(2.2).unsqueeze(0)
        assert torch.equal(out_mesh.vertices, mesh.vertices) and torch.equal(out_mesh.faces, mesh.faces)
        return (out_mesh,)


NODE_CLASS_MAPPINGS = {'ReferenceImageMeshColors': ReferenceImageMeshColors}
NODE_DISPLAY_NAME_MAPPINGS = {'ReferenceImageMeshColors': 'Project Reference RGB to Mesh'}
