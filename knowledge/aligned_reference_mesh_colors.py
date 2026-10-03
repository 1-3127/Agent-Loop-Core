"""Planar projective correspondence for actual masked source RGB; shape unchanged."""
import copy,json,math
import numpy as np
import torch
from scipy.spatial import cKDTree


def projective_map(source, target, points):
    source, target = np.asarray(source,dtype=float), np.asarray(target,dtype=float)
    assert source.shape == target.shape and source.ndim==2 and source.shape[1]==2 and len(source)>=4, 'FOUR_CORRESPONDENCES_REQUIRED'
    assert np.isfinite(source).all() and np.isfinite(target).all(), 'FINITE_CORRESPONDENCES_REQUIRED'
    rows, rhs = [], []
    for (x,y),(u,v) in zip(source,target):
        rows.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]])
        rhs.extend([u,v])
    h,_,rank,_=np.linalg.lstsq(rows,rhs,rcond=None)
    assert rank==8, 'DEGENERATE_CORRESPONDENCES'
    matrix=np.append(h,1).reshape(3,3)
    fitted=np.column_stack([source,np.ones(len(source))])@matrix.T
    assert (np.abs(fitted[:,2])>1e-8).all(), 'INVALID_CALIBRATION_DENOMINATOR'
    residual=np.linalg.norm(fitted[:,:2]/fitted[:,2:]-target,axis=1).max()
    assert residual<2., 'CORRESPONDENCE_RESIDUAL_OVER_TWO_PIXELS'
    mapped=np.column_stack([points,np.ones(len(points))])@matrix.T
    assert (np.abs(mapped[:,2])>1e-8).all(), 'INVALID_PROJECTION_DENOMINATOR'
    return mapped[:,:2]/mapped[:,2:]


class AlignedReferenceMeshColors:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required':{'mesh':('MESH',),'reference_image':('IMAGE',),'foreground_mask':('IMAGE',),
          'mesh_points':('STRING',{'default':'[]','multiline':True}), 'image_points':('STRING',{'default':'[]','multiline':True}),
          'horizontal_axis':(['X','Y','Z'],{'default':'X'}),'vertical_axis':(['X','Y','Z'],{'default':'Y'}),
          'view_angle':('FLOAT',{'default':0.,'min':-180.,'max':180.}),
          'mask_threshold':('FLOAT',{'default':.97,'min':0.,'max':1.}),
          'white_threshold':('FLOAT',{'default':.20,'min':0.,'max':1.})}}
    RETURN_TYPES=('MESH',)
    FUNCTION='paint'
    CATEGORY='3d/texturing'
    DESCRIPTION='Projects real mask-filtered RGB using Frontier-selected planar landmark correspondences. No manual colors, shape edits or calibrated 3D claim; independent Review required.'
    def paint(self,mesh,reference_image,foreground_mask,mesh_points,image_points,horizontal_axis,vertical_axis,view_angle,mask_threshold,white_threshold):
        assert horizontal_axis!=vertical_axis and mesh.vertices.shape[0]==1, 'ONE_NONFLAT_NATIVE_MESH_REQUIRED'
        rgb=reference_image[0,...,:3].detach().cpu().numpy();mask=foreground_mask[0,...,0].detach().cpu().numpy()
        assert rgb.shape[:2]==mask.shape and np.isfinite(rgb).all() and np.isfinite(mask).all(), 'MASK_IMAGE_ALIGNMENT'
        pixels=np.argwhere((mask>mask_threshold)&(rgb.min(-1)<white_threshold))
        assert len(pixels), 'NO_MASKED_SOURCE_RGB'
        vertices=mesh.vertices[0].detach().cpu().numpy();axes={'X':0,'Y':1,'Z':2};h,v=axes[horizontal_axis],axes[vertical_axis];d=next(i for i in range(3) if i not in {h,v})
        rad=math.radians(view_angle);x=vertices[:,h]*math.cos(rad)-vertices[:,d]*math.sin(rad);y=vertices[:,v]
        assert np.ptp(x)>0 and np.ptp(y)>0, 'NONFLAT_PROJECTION_REQUIRED'
        uv=np.column_stack([(x-x.min())/np.ptp(x),(y-y.min())/np.ptp(y)])
        mesh_anchors=np.asarray(json.loads(mesh_points),dtype=float);image_anchors=np.asarray(json.loads(image_points),dtype=float)
        assert image_anchors.ndim==2 and image_anchors.shape[1]==2, 'IMAGE_ANCHORS_COL_ROW_REQUIRED'
        assert (image_anchors>=0).all() and (image_anchors[:,0]<rgb.shape[1]).all() and (image_anchors[:,1]<rgb.shape[0]).all(), 'IMAGE_ANCHORS_OUT_OF_BOUNDS'
        assert (mesh_anchors>=0).all() and (mesh_anchors<=1).all(), 'MESH_ANCHORS_NORMALIZED_UV_REQUIRED'
        projected=projective_map(mesh_anchors,image_anchors,uv)
        _, nearest=cKDTree(pixels).query(projected[:,::-1]);sample=pixels[nearest]
        result=copy.copy(mesh)
        result.vertex_colors=torch.from_numpy(rgb[sample[:,0],sample[:,1]].copy()).clamp(0,1).pow(2.2).unsqueeze(0)
        assert torch.equal(result.vertices,mesh.vertices) and torch.equal(result.faces,mesh.faces),'GEOMETRY_CHANGED'
        return (result,)


NODE_CLASS_MAPPINGS={'AlignedReferenceMeshColors':AlignedReferenceMeshColors}
