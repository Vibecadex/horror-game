"""New, versioned irregular concrete for the isolated chamber candidate.

Blender background script. No imported source is changed. Shared, jagged Voronoi
edges keep fractures connected without the room-spanning binary split lines of
the recovery sheet. The original collision floor remains authoritative in UE.
"""
import bpy
import bmesh
import hashlib
import json
import math
import os
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = int(os.environ.get('CHAMBER_FLOOR_REVISION', '2'))
assert REVISION in (1,2)
OUT = ROOT / ('Assets/Adapted/ChamberParity/Parity20261007/FloorV' + str(REVISION))
OWNER = 'chamber-parity-20261007'
assert not OUT.exists() or not any(OUT.iterdir()), 'Export a new revision; never overwrite existing art.'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.
rng = random.Random(7102601)
SLOTS = ['Concrete', 'ConcreteLight', 'ConcreteDark', 'Aggregate', 'Dark', 'Crack']
LIMITS = [-16.6, 17.4, -15.3, 15.3]
boundary = [(LIMITS[0], LIMITS[2]), (LIMITS[1], LIMITS[2]),
            (LIMITS[1], LIMITS[3]), (LIMITS[0], LIMITS[3])]


def area(poly):
    return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly, poly[1:]+poly[:1])) / 2)


def clip(poly, nx, ny, d):
    if not poly: return []
    out = []
    a = poly[-1]; da = a[0]*nx + a[1]*ny - d
    for b in poly:
        db = b[0]*nx + b[1]*ny - d
        if (da <= 0) != (db <= 0):
            t = da / (da-db)
            out.append((a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t))
        if db <= 0: out.append(b)
        a, da = b, db
    return out


def near_edge(x, y):
    return min(x-LIMITS[0], LIMITS[1]-x, y-LIMITS[2], LIMITS[3]-y)


# Blue-noise seed field: larger intact slabs in the center, smaller fracture
# networks near drainage and two stress bands. No grid or recursive bisectors.
seeds = []
attempt = 0
coarse_count = 540 if REVISION == 1 else 260
while len(seeds) < coarse_count and attempt < 60000:
    attempt += 1
    x, y = rng.uniform(LIMITS[0], LIMITS[1]), rng.uniform(LIMITS[2], LIMITS[3])
    edge = near_edge(x, y)
    belt = abs(y - 3.0 * math.sin(x*.23) - 2.8)
    sep = .65 if edge < 3 or belt < 1.8 else 1.10
    if REVISION == 2: sep = 1.42
    if all(math.hypot(x-a, y-b) > (sep+s)*.5 for a,b,s in seeds):
        seeds.append((x,y,sep))
assert len(seeds) == coarse_count
if REVISION == 2:
    # Local stress and eroded banks, rather than uniform paving-sized cells.
    clusters = [(-13,-9,2.8,2.5,90),(-12,0,2.4,3.0,75),(-8,8,3.2,2.4,90),
                (-3,-8,3.0,2.6,95),(2,-3,2.5,2.3,95),(7,4,2.8,2.4,75),
                (12,10,2.6,3.0,95),(12,-10,2.8,2.6,95),(0,12,3.4,1.7,90),
                (-4,2,2.5,2.5,80)]
    for cx,cy,sx,sy,count in clusters:
        accepted=0
        for _ in range(30000):
            if accepted==count: break
            x,y=rng.gauss(cx,sx),rng.gauss(cy,sy)
            if not (LIMITS[0]+.03<x<LIMITS[1]-.03 and LIMITS[2]+.03<y<LIMITS[3]-.03): continue
            if any(math.hypot(x-a,y-b)<.38 for a,b,_ in seeds): continue
            seeds.append((x,y,.38)); accepted+=1
        assert accepted==count
cells = []
for i, (x,y,_) in enumerate(seeds):
    poly = list(boundary)
    neighbors = sorted((j for j in range(len(seeds)) if j != i),
                       key=lambda j: (seeds[j][0]-x)**2 + (seeds[j][1]-y)**2)
    for j in neighbors:
        a,b,_ = seeds[j]
        # Once twice the furthest corner is nearer than a neighbor, later
        # bisectors cannot intersect this convex cell.
        distance = math.hypot(a-x,b-y)
        if distance > 2*max(math.hypot(px-x,py-y) for px,py in poly)+1e-6: break
        poly = clip(poly, a-x, b-y, (a*a+b*b-x*x-y*y)/2)
    assert len(poly) >= 3 and area(poly) > .03
    cells.append([(round(a,5),round(b,5)) for a,b in poly])
assert abs(sum(area(c) for c in cells) - area(boundary)) < .01


def warp(p):
    x,y = p
    fade = min(1., max(0., near_edge(x,y)/.6))
    return (x + fade*(.10*math.sin(y*1.65)+.042*math.sin(x*3.7+y)),
            y + fade*(.11*math.sin(x*1.32)+.04*math.cos(y*3.1-x)))


edges = {}
for cell in cells:
    for a,b in zip(cell,cell[1:]+cell[:1]):
        key = tuple(sorted((a,b)))
        if key in edges: continue
        a,b = key; dx,dy=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dy)
        local = random.Random(int(hashlib.sha256(repr(key).encode()).hexdigest()[:12],16))
        count=max(2,math.ceil(length/.23)); points=[]
        for n in range(count+1):
            t=n/count
            jitter=math.sin(math.pi*t)*local.uniform(-.068,.068)
            p=(a[0]+dx*t-dy/length*jitter,a[1]+dy*t+dx/length*jitter)
            points.append(warp(p))
        edges[key]=points

verts, faces, materials = [], [], []
def face(indices, material):
    faces.append(indices); materials.append(SLOTS.index(material))


def slab(poly, cx, cy, thickness, gap, mat, underlay=False):
    poly = sorted(poly, key=lambda p: math.atan2(p[1]-cy, p[0]-cx))
    start=len(verts); n=len(poly)
    outer=[]; inner=[]
    mean_radius = sum(math.hypot(x-cx,y-cy) for x,y in poly)/n
    for x,y in poly:
        r=max(.04, mean_radius)
        bx,by=x+(cx-x)*gap/r,y+(cy-y)*gap/r
        ix,iy=x+(cx-x)*(gap+.012)/r,y+(cy-y)*(gap+.012)/r
        # Sub-centimeter continuous relief; erosion sits in the joints.
        z=thickness + (.0018*math.sin(x*2.3+y)+.001*math.cos(y*3.7))*(not underlay)
        outer.append((bx,by,z-.003 if not underlay else z))
        inner.append((ix,iy,z))
    verts.extend([(x,y,-.009) for x,y,z in outer]+outer+inner)
    face([start+i for i in reversed(range(n))], 'ConcreteDark')
    face([start+2*n+i for i in range(n)], mat)
    for i in range(n):
        j=(i+1)%n
        face([start+i,start+j,start+n+j,start+n+i], 'ConcreteDark')
        face([start+n+i,start+n+j,start+2*n+j,start+2*n+i], 'Aggregate')


slab(boundary, .4, 0, -.002, 0, 'ConcreteDark', True)
dropped=[]; kept=[]
for i,cell in enumerate(cells):
    x,y,_=seeds[i]
    # Connected spalls cluster at edges; the central play space remains intact.
    spall = (near_edge(x,y)<2.6 and area(cell)<1.7 and rng.random()<.18)
    if spall:
        dropped.append(i); continue
    ring=[]
    for a,b in zip(cell,cell[1:]+cell[:1]):
        key=tuple(sorted((a,b))); points=edges[key]
        if a != key[0]: points=list(reversed(points))
        ring.extend(points[:-1])
    wx,wy=warp((x,y))
    # Rare wider, chipped joints avoid evenly outlined paving slabs.
    gap = rng.uniform(.0025,.0065) if rng.random()<.82 else rng.uniform(.012,.022)
    mat = rng.choices(['Concrete','ConcreteLight','ConcreteDark'], [.80,.12,.08])[0]
    slab(ring,wx,wy,rng.uniform(.013,.028),gap,mat)
    kept.append({'site':[x,y], 'area_m2':area(cell), 'joint_half_width_m':gap})

name='SM_Parity20261007_IrregularFloor_V' + str(REVISION)
mesh=bpy.data.meshes.new(name)
mesh.from_pydata(verts,[],faces)
assert not mesh.validate(), 'Authored geometry needed repair'
for index,slot in enumerate(SLOTS):
    m=bpy.data.materials.new(slot);m.diffuse_color=(.25,.26,.24,1)
    mesh.materials.append(m)
for p,mi in zip(mesh.polygons,materials): p.material_index=mi
bm=bmesh.new(); bm.from_mesh(mesh)
assert all(e.is_manifold for e in bm.edges)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bmesh.ops.triangulate(bm,faces=list(bm.faces))
bm.to_mesh(mesh); bm.free(); mesh.update()
down_tops=sum(1 for p in mesh.polygons if min(mesh.vertices[i].co.z for i in p.vertices)>.008 and p.normal.z<-.001)
assert down_tops==0, down_tops
uv=mesh.uv_layers.new(name='WorldMetres')
for loop in mesh.loops:
    p=mesh.vertices[loop.vertex_index].co; uv.data[loop.index].uv=(p.x/4,p.y/4)
mesh.calc_loop_triangles()
obj=bpy.data.objects.new(name,mesh); bpy.context.scene.collection.objects.link(obj)
obj.select_set(True); bpy.context.view_layer.objects.active=obj
path=OUT/(name+'.fbx')
bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},
    axis_forward='-Y',axis_up='Z',global_scale=1,apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_NONE',bake_anim=False,use_mesh_modifiers=True)
mins=[min(v.co[j] for v in mesh.vertices) for j in range(3)]
maxs=[max(v.co[j] for v in mesh.vertices) for j in range(3)]
entry={'name':name,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
       'triangles':len(mesh.loop_triangles),'dimensions_cm':[(b-a)*100 for a,b in zip(mins,maxs)],
       'bounds_blender_m':[mins,maxs],'material_slots':SLOTS,'manifold':True,'downward_tops':down_tops}
before=set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=str(path),use_anim=False)
loaded=[o for o in set(bpy.data.objects)-before if o.type=='MESH']; assert len(loaded)==1
back=loaded[0]; pts=[back.matrix_world@v.co for v in back.data.vertices]
back.data.calc_loop_triangles()
dims=[(max(p[j] for p in pts)-min(p[j] for p in pts))*100 for j in range(3)]
assert max(abs(a-b) for a,b in zip(dims,entry['dimensions_cm']))<.02
assert len(back.data.loop_triangles)==entry['triangles']
entry['fbx_roundtrip_passed']=True
bpy.data.objects.remove(back,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/('ChamberParityFloor_V' + str(REVISION) + '.blend')))
manifest={'owner':OWNER,'generator':'tools/make_chamber_parity_floor.py',
          'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'assets':[entry],'plates':len(kept),'spalls':len(dropped),'plate_area_m2':[min(p['area_m2'] for p in kept),max(p['area_m2'] for p in kept)],
          'triangles':entry['triangles'],'placement_cm':[0,0,-5],'collision':'NoCollision',
          'top_world_cm':maxs[2]*100-5,'provenance':'Original deterministic geometry; no reference image pixels used.',
          'units':'metres; FBX -Y/+Z; Unreal mirrors Y','shared_jagged_edges':len(edges)}
assert -5<manifest['top_world_cm']<0
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('PARITY_FLOOR_COMPLETE',json.dumps(manifest))
