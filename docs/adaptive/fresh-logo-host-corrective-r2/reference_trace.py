"""Local Worker reference segmentation and measured contour extraction."""
import json,sys,math
from host_geometry_contract import validate_fixed_trace_stage, verify_trace_tolerance
from pathlib import Path
import numpy as np
from PIL import Image
source,out=Path(sys.argv[1]),Path(sys.argv[2])
stage=json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
epsilon=validate_fixed_trace_stage(stage)  # validate before output/image effects
out.mkdir(exist_ok=True)
rgb=np.array(Image.open(source).convert('RGB'))
mask=(rgb[:,:,0]>120)&(rgb[:,:,1]>110)&(rgb[:,:,2]>85)
Image.fromarray((mask*255).astype('uint8')).save(out/'logo-mask.png')
height,width=mask.shape
if not mask.any():raise ValueError('REFERENCE_FOREGROUND_EMPTY')
edges={}
def add(a,b): edges.setdefault(a,[]).append(b)
for y,x in np.argwhere(mask):
 x,y=int(x),int(y)
 if y==0 or not mask[y-1,x]:add((x,y),(x+1,y))
 if x==width-1 or not mask[y,x+1]:add((x+1,y),(x+1,y+1))
 if y==height-1 or not mask[y+1,x]:add((x+1,y+1),(x,y+1))
 if x==0 or not mask[y,x-1]:add((x,y+1),(x,y))
directions={(1,0):0,(0,1):1,(-1,0):2,(0,-1):3}
def dp(points,eps):
 if len(points)<3:return points
 a,b=np.array(points[0]),np.array(points[-1]); d=b-a
 q=np.array(points); length=np.linalg.norm(d)
 dist=np.linalg.norm(q-a,axis=1) if length==0 else np.abs(d[0]*(q[:,1]-a[1])-d[1]*(q[:,0]-a[0]))/length
 i=int(np.argmax(dist))
 if dist[i]<=eps:return [points[0],points[-1]]
 return dp(points[:i+1],eps)[:-1]+dp(points[i:],eps)
loops=[]
while edges:
 start=next(iter(edges)); current=start; ring=[start]; incoming=0
 while True:
  choices=edges[current]
  priority={1:0,0:1,3:2,2:3}
  nxt=min(choices,key=lambda q:priority[(directions[(q[0]-current[0],q[1]-current[1])]-incoming)%4])
  choices.remove(nxt)
  if not choices:del edges[current]
  incoming=directions[(nxt[0]-current[0],nxt[1]-current[1])];current=nxt
  ring.append(current)
  if current==start:break
 ring=ring[:-1]
 signed=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:]+ring[:1]))/2
 if abs(signed)<2:continue
 split=max(range(len(ring)),key=lambda i:(ring[i][0]-ring[0][0])**2+(ring[i][1]-ring[0][1])**2)
 simplified=dp(ring[:split+1],epsilon)[:-1]+dp(ring[split:]+ring[:1],epsilon)[:-1]
 loops.append(dict(points=simplified,area=signed))
def contains(poly,p):
 x,y=p;hit=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:hit=not hit
 return hit
shapes=[dict(outer=l['points'],holes=[]) for l in loops if l['area']>0]
for l in loops:
 if l['area']<0:
  candidates=[s for s in shapes if contains(s['outer'],l['points'][0])]
  assert candidates,'Unassigned negative-space contour'
  min(candidates,key=lambda s:len(s['outer']))['holes'].append(l['points'])
xs=np.where(mask)[1];ys=np.where(mask)[0]
verify_trace_tolerance(stage,epsilon)
record=dict(simplification_pixels=epsilon,coordinate_mapping='X=(pixel_x-width/2)*scale; Z=(height/2-pixel_y)*scale; front=-Y',source=str(source),image_width=width,image_height=height,foreground_pixels=int(mask.sum()),
 bounds_pixels=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],
 gold_rgb=[float(v)/255 for v in rgb[mask].mean(axis=0)],shapes=shapes,
 scale=10.0/(int(xs.max()+1)-int(xs.min())),shape_count=len(shapes),hole_count=sum(len(s['holes']) for s in shapes),
 assumptions='Depth is a technical extrusion choice, not an observed hidden dimension; source silhouette and holes are measured',
 algorithm=f'Color-region binary segmentation; oriented pixel-boundary rings; {epsilon} px Douglas-Peucker contour simplification')
with (out/'logo-contours.json').open('x',encoding='utf-8') as f:json.dump(record,f)
print(json.dumps({k:v for k,v in record.items() if k!='shapes'}))
