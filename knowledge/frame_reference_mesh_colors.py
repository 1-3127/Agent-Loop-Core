"""Current-input landmark correspondence for a horizontal open frame, then real RGB."""
import json,math
import numpy as np


def frame_anchors(vertices, mask, horizontal_axis, vertical_axis, view_angle, mask_threshold):
    axes={'X':0,'Y':1,'Z':2};h,v=axes[horizontal_axis],axes[vertical_axis]
    assert h!=v,'PROJECTION_AXES_MUST_DIFFER'
    d=next(i for i in range(3) if i not in {h,v});rad=math.radians(view_angle)
    xy=np.column_stack([vertices[:,h]*math.cos(rad)-vertices[:,d]*math.sin(rad),vertices[:,v]])
    low=xy.min(0);span=np.ptp(xy,axis=0);assert (span>0).all(),'NONFLAT_FRAME_REQUIRED'
    mesh_points=[]
    for side in [0,1]:
        rows=xy[xy[:,0]<low[0]+.02*span[0]] if not side else xy[xy[:,0]>low[0]+.98*span[0]]
        assert len(rows),'FRAME_CAP_REQUIRED'
        mesh_points.append((np.median(rows,axis=0)-low)/span)
    for side in [0,1]:
        rows=xy[xy[:,0]<low[0]+.5*span[0]] if not side else xy[xy[:,0]>low[0]+.5*span[0]]
        rows=rows[rows[:,1]<rows[:,1].min()+.02*span[1]]
        assert len(rows),'FRAME_FOOT_REQUIRED'
        mesh_points.append((np.median(rows,axis=0)-low)/span)
    mesh_points=np.asarray(mesh_points)
    assert (mesh_points[:2,1]>.6).all() and (mesh_points[2:,1]<.2).all(),'HORIZONTAL_TOP_BAR_TWO_FEET_REQUIRED'
    pixels=np.argwhere(mask>mask_threshold);assert len(pixels),'EMPTY_REFERENCE_MASK'
    lo,hi=pixels.min(0),pixels.max(0);assert (hi>lo).all(),'NONFLAT_REFERENCE_FRAME_REQUIRED'
    image_points=[]
    for side in [0,1]:
        rows=pixels[pixels[:,1]<lo[1]+.025*(hi[1]-lo[1])] if not side else pixels[pixels[:,1]>hi[1]-.025*(hi[1]-lo[1])]
        image_points.append(np.median(rows,axis=0)[::-1])
    for side in [0,1]:
        rows=pixels[pixels[:,1]<(lo[1]+hi[1])/2] if not side else pixels[pixels[:,1]>(lo[1]+hi[1])/2]
        assert len(rows),'REFERENCE_FRAME_FOOT_REQUIRED'
        rows=rows[rows[:,0]>rows[:,0].max()-5]
        image_points.append(np.median(rows,axis=0)[::-1])
    return mesh_points.tolist(),np.asarray(image_points).tolist()


class FrameReferenceMeshColors:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required':{'mesh':('MESH',),'reference_image':('IMAGE',),'foreground_mask':('IMAGE',),
          'horizontal_axis':(['X','Y','Z'],{'default':'X'}),'vertical_axis':(['X','Y','Z'],{'default':'Y'}),
          'view_angle':('FLOAT',{'default':0.,'min':-180.,'max':180.}),
          'mask_threshold':('FLOAT',{'default':.97,'min':0.,'max':1.}),
          'white_threshold':('FLOAT',{'default':.20,'min':0.,'max':1.}),
          'flip_horizontal':('BOOLEAN',{'default':False})}}
    RETURN_TYPES=('MESH',)
    FUNCTION='paint'
    CATEGORY='3d/texturing'
    DESCRIPTION='For horizontal top-bar/two-foot open frames ONLY: derive paired current geometry/mask extrema, project actual masked source RGB using homography. Preserves geometry; hidden surfaces approximate. Independent Review required.'
    def paint(self,mesh,reference_image,foreground_mask,horizontal_axis,vertical_axis,view_angle,mask_threshold,white_threshold,flip_horizontal):
        import nodes
        assert mesh.vertices.shape[0]==1 and mesh.faces.shape[0]==1,'ONE_NATIVE_MESH_REQUIRED'
        mask=foreground_mask[0,...,0].detach().cpu().numpy()
        mp,ip=frame_anchors(mesh.vertices[0].detach().cpu().numpy(),mask,horizontal_axis,vertical_axis,view_angle,mask_threshold)
        if flip_horizontal:ip=[ip[1],ip[0],ip[3],ip[2]]
        color_class=nodes.NODE_CLASS_MAPPINGS['AlignedReferenceMeshColors']
        result=color_class().paint(mesh,reference_image,foreground_mask,json.dumps(mp),json.dumps(ip),horizontal_axis,vertical_axis,view_angle,mask_threshold,white_threshold)
        print(json.dumps({'node':'FrameReferenceMeshColors','current_mesh_points':mp,'current_image_points':ip,'geometry_preserved':True}))
        return result


NODE_CLASS_MAPPINGS={'FrameReferenceMeshColors':FrameReferenceMeshColors}
