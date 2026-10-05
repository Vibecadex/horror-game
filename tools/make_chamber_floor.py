"""Original asymmetric connected concrete fractures for the chamber references.

Blender background authoring only; writes Assets/Adapted/ChamberParity/Floor.
Never imports/edits Unreal assets or existing parity floor sources.
Metres, floor Z=0, exported via the established -Y/+Z static-FBX convention.
"""
import bpy
import bmesh
import hashlib
import itertools
import json
import math
import random
from collections import Counter
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Assets/Adapted/ChamberParity/Floor'
OWNER='teddy-chamber-connected-floor-20261005'
if OUT.exists() and any(OUT.iterdir()):
    marker=OUT/'manifest.json'
    if not marker.exists() or json.loads(marker.read_text(encoding='utf-8')).get('owner')!=OWNER:
        raise RuntimeError('Refusing to overwrite unowned chamber floor')
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'manifest.json').write_text(json.dumps({'owner':OWNER,'status':'authoring'}),encoding='utf-8')
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1
SLOTS=['Concrete','ConcreteLight','ConcreteDark','Aggregate','Dark','Crack']
MATS={}
for name,lo,hi in [
    ('Concrete',(.16,.177,.169,1),(.25,.26,.24,1)),
    ('ConcreteLight',(.17,.184,.171,1),(.265,.275,.250,1)),
    ('ConcreteDark',(.133,.148,.144,1),(.22,.232,.217,1)),
    ('Aggregate',(.145,.153,.143,1),(.235,.244,.225,1)),
    ('Dark',(.02,.027,.025,1),(.043,.05,.043,1)),
    ('Crack',(.012,.017,.015,1),(.021,.028,.022,1)),
]:
    mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.diffuse_color=hi
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    shader=nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value=.96
    shader.inputs['Specular IOR Level'].default_value=.12 if name not in ('Dark','Crack') else 0
    coords=nodes.new('ShaderNodeNewGeometry')
    noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=14;noise.inputs['Detail'].default_value=4
    links.new(coords.outputs['Position'],noise.inputs['Vector'])
    ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=lo;ramp.color_ramp.elements[1].color=hi
    links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],shader.inputs['Base Color'])
    fine=nodes.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=125;fine.inputs['Detail'].default_value=3
    links.new(coords.outputs['Position'],fine.inputs['Vector'])
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.004
    links.new(fine.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],shader.inputs['Normal'])
    MATS[name]=mat


def area(poly):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1])))/2


def centre(poly):
    return (sum(x for x,y in poly)/len(poly),sum(y for x,y in poly)/len(poly))


def clip(poly,nx,ny,d):
    result=[]
    a=poly[-1];da=a[0]*nx+a[1]*ny-d
    for b in poly:
        db=b[0]*nx+b[1]*ny-d
        if (da<=0)!=(db<=0):
            t=da/(da-db)
            result.append((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t))
        if db<=0:
            result.append(b)
        a,da=b,db
    return result


def split_cells(boundary,count,rng,kind):
    """Hierarchical stress splits yield mixed spans and T junctions, not cells
    of near-uniform radius. A primary crack continues across many child plates.
    """
    cells=[boundary]
    attempts=0
    while len(cells)<count and attempts<count*20:
        attempts+=1
        scores=[]
        for cell in cells:
            x,y=centre(cell)
            density=1.2+.65*math.sin(x*.85+kind)+.38*math.cos(y*1.4-kind)
            scores.append(area(cell)*density*rng.uniform(.8,1.2))
        index=max(range(len(cells)),key=lambda i:scores[i])
        poly=cells[index];cx,cy=centre(poly)
        spanx=max(x for x,y in poly)-min(x for x,y in poly)
        spany=max(y for x,y in poly)-min(y for x,y in poly)
        angle=rng.uniform(0,math.pi)
        if spanx>spany*1.7:angle=rng.uniform(-.44,.44)
        elif spany>spanx*1.7:angle=math.pi/2+rng.uniform(-.44,.44)
        nx,ny=math.cos(angle),math.sin(angle)
        d=nx*cx+ny*cy+rng.uniform(-.16,.16)*min(spanx,spany)
        left,right=clip(poly,nx,ny,d),clip(poly,-nx,-ny,-d)
        if min(len(left),len(right))<3 or min(area(left),area(right))<.095:
            continue
        if min(area(left),area(right))/max(area(left),area(right))<.13:
            continue
        cells[index:index+1]=[left,right]
    return cells


def canonical(p):return (round(p[0],6),round(p[1],6))


def subdivide_t_junctions(cells):
    points=sorted(set(canonical(p) for cell in cells for p in cell))
    result=[]
    for poly in cells:
        refined=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            ax,ay=a;dx,dy=b[0]-ax,b[1]-ay;length2=dx*dx+dy*dy
            if length2<1e-10:continue
            on=[]
            for p in points:
                t=((p[0]-ax)*dx+(p[1]-ay)*dy)/length2
                cross=abs((p[0]-ax)*dy-(p[1]-ay)*dx)
                if -1e-6<=t<1-1e-6 and cross<2e-5:
                    on.append((t,p))
            refined.extend(p for t,p in sorted(on))
        result.append(refined)
    return result


def distort(p,kind):
    x,y=p
    return (x+.066*math.sin(y*2.0+kind)+.024*math.sin(x*3.1-y),
            y+.058*math.sin(x*2.35-kind)+.021*math.cos(y*3.2+x))


def distance_segment(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)))
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)


def boundary_distance(p,boundary):
    return min(distance_segment(p,a,b) for a,b in zip(boundary,boundary[1:]+boundary[:1]))


class Geometry:
    def __init__(self):self.vertices=[];self.faces=[];self.indices=[];self.pieces=0
    def polygon(self,points,material):
        if len(points)<3:return
        vectors=[Vector(p) for p in points]
        start=len(self.vertices)
        self.vertices.extend(points)
        lookup={tuple(v):start+i for i,v in enumerate(vectors)}
        for tri in tessellate_polygon([vectors]):
            # Installed Blender5.2 returns vertex indices here; older local
            # versions returned Vector objects. Both identify this one loop.
            self.faces.append(tuple(start+v if isinstance(v,int) else lookup[tuple(v)] for v in tri))
            self.indices.append(SLOTS.index(material))
    def quad(self,a,b,c,d,material):self.polygon([a,b,c,d],material)
    def ribbon(self,points,widths,z,material='Crack'):
        for i,(a,b) in enumerate(zip(points,points[1:])):
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            if length<1e-5:continue
            nx,ny=-dy/length,dx/length
            wa,wb=widths[i]/2,widths[i+1]/2
            self.quad((a[0]-nx*wa,a[1]-ny*wa,z),(b[0]-nx*wb,b[1]-ny*wb,z),
                      (b[0]+nx*wb,b[1]+ny*wb,z),(a[0]+nx*wa,a[1]+ny*wa,z),material)
    def slab(self,poly,height,bevel,material='Concrete',tilt=(0,0),rng=None,base=.0013,edge_material='Concrete',height_fade=None):
        cx,cy=centre(poly);n=len(poly)
        lower=[];outer=[];inner=[]
        for x,y in poly:
            vx,vy=cx-x,cy-y;length=max(.01,math.hypot(vx,vy))
            ix,iy=x+vx/length*bevel,y+vy/length*bevel
            z=max(base+.00035,min(.0396,height+(x-cx)*tilt[0]+(y-cy)*tilt[1]))
            if height_fade is not None:
                z=.00045+(z-.00045)*height_fade((x,y))
            lower.append((x,y,base));outer.append((x,y,max(base+.0002,z-bevel*.45)));inner.append((ix,iy,z))
        self.polygon(inner,material)
        for i in range(n):
            j=(i+1)%n
            self.quad(inner[i],outer[i],outer[j],inner[j],edge_material)
            self.quad(outer[i],lower[i],lower[j],outer[j],'Dark' if edge_material=='Aggregate' else edge_material)
        self.polygon(list(reversed(lower)),material)
        self.pieces+=1


ASSETS,OBJECTS=[],[]


def make_field(name,kind,seed,count):
    rng=random.Random(seed)
    boundary=[(-4.7,-3.25),(-4.00,-4.10),(2.55,-3.92),(4.72,-2.96),
              (4.48,2.96),(3.40,4.04),(-3.30,3.80),(-4.67,1.14)]
    if kind==1:
        boundary=[(x*.95,y*1.055) for x,y in boundary]
    elif kind==2:
        boundary=[(x*1.025,y*.98) for x,y in boundary]
    cells=subdivide_t_junctions(split_cells(boundary,count,rng,kind))
    edges={}
    for cell_index,cell in enumerate(cells):
        for a,b in zip(cell,cell[1:]+cell[:1]):
            key=tuple(sorted((a,b)))
            if a!=b:edges.setdefault(key,{'owners':[]})['owners'].append(cell_index)
    for key,edge in edges.items():
        a,b=key;dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        local=random.Random(int(hashlib.sha256(repr((seed,key)).encode()).hexdigest()[:14],16))
        n=max(2,min(22,int(length/.18)+1))
        points=[]
        for i in range(n+1):
            t=i/n
            jitter=math.sin(t*math.pi)*local.uniform(-1,1)*min(.060,length*.12)
            p=(a[0]+t*dx-dy/length*jitter,a[1]+t*dy+dx/length*jitter)
            points.append(distort(p,kind))
        edge['points']=points
        edge['length']=length
        edge['width']=local.uniform(.012,.028) if length>.45 else local.uniform(.005,.013)
    outer_segments=[]
    for edge in edges.values():
        if len(edge['owners'])==1:
            outer_segments.extend(zip(edge['points'],edge['points'][1:]))
    def actual_edge_fade(p):
        distance=min(distance_segment(p,a,b) for a,b in outer_segments)
        return min(1,distance/.64)**1.3
    geo=Geometry();surface_counts=Counter();plate_heights=[]
    # All height fades approach the existing floor along the outer border;
    # no dark ellipse/card perimeter is authored around the patch.
    for ci,cell in enumerate(cells):
        poly=[]
        for a,b in zip(cell,cell[1:]+cell[:1]):
            key=tuple(sorted((a,b)))
            if key not in edges:continue
            path=edges[key]['points']
            if a!=key[0]:path=list(reversed(path))
            poly.extend(path[:-1])
        if len(poly)<3:continue
        cx,cy=centre(poly)
        fade=min(1,boundary_distance((cx,cy),boundary)/.75)
        wave=math.sin(cx*.59+kind)+.55*math.sin(cy*.88+kind*2)+.28*math.cos(cx*.8-cy*.7)
        top=.0030+fade*(.0045+.0030*(wave+1.8)/3.6)
        if rng.random()<.055:top+=rng.uniform(.004,.007)*fade
        inset= rng.uniform(.0028,.0090)*fade
        pp=[]
        for x,y in poly:
            vx,vy=cx-x,cy-y;length=max(.01,math.hypot(vx,vy))
            pp.append((x+vx/length*inset,y+vy/length*inset))
        material='Concrete'
        if wave>1.35:material='ConcreteDark'
        elif wave<-.95:material='ConcreteLight'
        geo.slab(pp,top,.0045*fade,material,tilt=(0,0),base=.0001,
                 edge_material='Concrete',height_fade=actual_edge_fade)
        surface_counts[material]+=1;plate_heights.append(top)
    internal=[(key,edge) for key,edge in edges.items() if len(edge['owners'])>1]
    visible_cracks=0
    for key,edge in internal:
        points=edge['points'];mid=points[len(points)//2]
        fade=min(1,boundary_distance(mid,boundary)/.66)
        # Broken widths and short buried portions avoid uniformly bright or
        # dark complete polygon outlines, while primary paths remain connected.
        if edge['length']<.28 and rng.random()<.37:continue
        widths=[edge['width']*fade*rng.uniform(.5,1.1) for p in points]
        if fade<.12:continue
        geo.ribbon(points,widths,.00165)
        visible_cracks+=1
    # Small transverse secondary fissures terminate within plates, softening
    # the recursive subdivision's long stress lines without a regular grid.
    for i in range(22):
        key,edge=rng.choice(internal)
        path=edge['points'];p=path[rng.randrange(1,len(path))]
        a=rng.uniform(0,math.tau);length=rng.uniform(.15,.65)
        pts=[p]
        for j in range(1,5):
            t=j/4
            pts.append((p[0]+math.cos(a)*length*t+rng.uniform(-.018,.018),
                        p[1]+math.sin(a)*length*t+rng.uniform(-.018,.018)))
        geo.ribbon(pts,[.006,.005,.0038,.0024,.0004],.0118,'Crack')
    # Larger detached fragments are concentrated at two fracture-bank lobes,
    # not spread as uniform confetti. Every slab has real thickness and bevel.
    fragments=[]
    lobes=[(-2.9,-1.8),(2.6,2.0)] if kind!=1 else [(-3.0,1.7),(1.7,-2.5)]
    for i in range(24 if kind==1 else 18):
        lx,ly=lobes[i%2]
        x,y=lx+rng.gauss(0,.63),ly+rng.gauss(0,.73)
        x=max(-4.05,min(4.05,x));y=max(-3.5,min(3.5,y))
        span=rng.uniform(.14,.30) if i%5 else rng.uniform(.42,.60)
        radius=span*.5;n=rng.randint(4,7);angle=rng.uniform(0,math.tau)
        poly=[]
        for j in range(n):
            a=angle+j*math.tau/n+rng.uniform(-.13,.13)
            r=radius*rng.uniform(.73,1.11)
            poly.append((x+math.cos(a)*r,y+math.sin(a)*r*rng.uniform(.65,.95)))
        h=rng.uniform(.018,.034)
        tx,ty=rng.uniform(-.018,.018),rng.uniform(-.018,.018)
        geo.slab(poly,h,.008,'Concrete',tilt=(tx,ty),base=.009,
                 edge_material='Aggregate')
        fragments.append({'centre_m':[x,y],'nominal_span_cm':span*100,'top_cm':h*100})
    # Isolated chips follow the same lobes and remain subordinate to slabs.
    for i in range(30):
        lx,ly=lobes[i%2];x,y=lx+rng.gauss(0,.85),ly+rng.gauss(0,.80)
        if abs(x)>4.3 or abs(y)>3.7:continue
        radius=rng.uniform(.023,.055);a=rng.uniform(0,math.tau)
        poly=[(x+radius*math.cos(a+j*math.tau/4)*rng.uniform(.7,1.2),
               y+radius*math.sin(a+j*math.tau/4)*rng.uniform(.7,1.2)) for j in range(4)]
        geo.slab(poly,rng.uniform(.013,.024),.004,'Concrete',base=.010,edge_material='Aggregate')
    mesh=bpy.data.meshes.new(name+'_Geometry');mesh.from_pydata(geo.vertices,[],geo.faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj)
    for mat in MATS.values():mesh.materials.append(mat)
    for p,index in zip(mesh.polygons,geo.indices):p.material_index=index
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    uv=mesh.uv_layers.new(name='FloorMetres_4m')
    for loop in mesh.loops:
        p=mesh.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(p.x/4,p.y/4)
    mesh.calc_loop_triangles()
    minimum=[min(v.co[i] for v in mesh.vertices) for i in range(3)]
    maximum=[max(v.co[i] for v in mesh.vertices) for i in range(3)]
    assert minimum[2]>=0 and maximum[2]<=.04,(name,minimum,maximum)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},
        axis_forward='-Y',axis_up='Z',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',
        use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,path_mode='AUTO')
    entry={'name':name,'file':name+'.fbx','triangles':len(mesh.loop_triangles),'vertices':len(mesh.vertices),
           'bounds_m':{'min':minimum,'max':maximum},'dimensions_m':[maximum[i]-minimum[i] for i in range(3)],
           'expected_dimensions_cm':[(maximum[i]-minimum[i])*100 for i in range(3)],
           'highest_point_cm':maximum[2]*100,
           'material_slots':SLOTS,'plate_count':len(cells),'detached_slabs':fragments,'surface_material_counts':dict(surface_counts),
           'internal_crack_edges':len(internal),'visible_crack_edges':visible_cracks,'connected_shared_edge_topology':True,
           'plate_top_range_cm':[min(plate_heights)*100,max(plate_heights)*100],
           'origin':'Underlying floor Z=0; field centred on XY. NoCollision decoration; never scale Z.',
           'sha256':hashlib.sha256((OUT/(name+'.fbx')).read_bytes()).hexdigest()}
    ASSETS.append(entry);OBJECTS.append(obj)
    obj['owner']=OWNER;obj['underlying_floor_z']=0
    print('CHAMBER_FLOOR_ASSET',name,entry['triangles'],entry['dimensions_m'],flush=True)


make_field('SM_ChamberFractureFork_A',0,922745,139)
make_field('SM_ChamberFractureBank_B',1,937151,167)
make_field('SM_ChamberFractureDrift_C',2,971489,99)

checks=[]
for entry in ASSETS:
    before=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(OUT/entry['file']),use_anim=False)
    loaded=[o for o in set(bpy.data.objects)-before if o.type=='MESH'];assert len(loaded)==1
    obj=loaded[0];pts=[obj.matrix_world@v.co for v in obj.data.vertices]
    dims=[max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3)]
    error=max(abs(a-b) for a,b in zip(dims,entry['dimensions_m']))
    obj.data.calc_loop_triangles();names=[s.material.name.split('.')[0] for s in obj.material_slots]
    assert error<.000025 and len(obj.data.loop_triangles)==entry['triangles'] and names==SLOTS
    assert len(obj.data.uv_layers)==1
    checks.append({'name':entry['name'],'max_dimension_error_m':error,'triangles':len(obj.data.loop_triangles),'slots':names,'passed':True})
    bpy.data.objects.remove(obj,do_unlink=True)
assert sum(a['triangles'] for a in ASSETS)<110000


def placement(label,index,loc,yaw,xy=1):
    entry=ASSETS[index];c,s=math.cos(math.radians(yaw)),math.sin(math.radians(yaw));pts=[]
    for p in itertools.product(*zip(entry['bounds_m']['min'],entry['bounds_m']['max'])):
        x,y,z=p[0]*100*xy,-p[1]*100*xy,p[2]*100
        pts.append((loc[0]+c*x-s*y,loc[1]+s*x+c*y,loc[2]+z))
    b={'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]}
    assert b['min'][0]>=-1400 and b['max'][0]<=1480 and b['min'][1]>=-1500 and b['max'][1]<=1500
    return {'label':label,'mesh':entry['name'],'location_cm':loc,'yaw':yaw,'scale':[xy,xy,1],
            'collision':'NoCollision','world_bounds_cm':b}


placements=[placement('ForegroundLeft',0,[-800,-700,-5],0),
            placement('ForegroundRight',1,[-780,480,-5],9),
            placement('MidLeftDrift',2,[230,-740,-5],-12),
            placement('RearRightFork',0,[820,600,-5],177),
            placement('RightSideBank',1,[10,920,-5],87,.70)]

# Three neutral construction renders. Shader preview contains no baked teal,
# highlights or player light pool; parent uses aligned existing floor material.
for obj,loc in zip(OBJECTS,[(-10.2,0,0),(0,0,0),(10.2,0,0)]):obj.location=loc
bpy.ops.mesh.primitive_plane_add(size=100,location=(0,0,0))
ground=bpy.context.object;ground.name='Underlying floor preview - not exported';ground.data.materials.append(MATS['Concrete'])
world=bpy.data.worlds.new('Neutral floor study');world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.17,.18,.17,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45;scene.world=world
for name,loc,power,size in [('Raking key',(-6,-12,8),3000,7),('Soft overhead',(5,4,15),3400,8)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector((0,0,0))-obj.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Floor kit study');camera=bpy.data.objects.new('Floor kit study',data);scene.collection.objects.link(camera)
data.type='ORTHO';data.ortho_scale=33;camera.location=(0,-15,24)
camera.rotation_euler=(Vector((0,0,0))-camera.location).to_track_quat('-Z','Y').to_euler();scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=28;scene.cycles.use_denoising=True
scene.render.resolution_x=2000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.render.filepath=str(OUT/'fields-overview.png')
blend=OUT/'ChamberFloor_Kit.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend));bpy.ops.render.render(write_still=True)
for index,obj in enumerate(OBJECTS):
    for other in OBJECTS:other.hide_render=other!=obj
    camera.location=(obj.location.x+1.2,-8,8)
    camera.rotation_euler=(Vector((obj.location.x,0,0))-camera.location).to_track_quat('-Z','Y').to_euler()
    data.ortho_scale=10.8;scene.render.resolution_x=1300;scene.render.resolution_y=1100
    scene.render.filepath=str(OUT/('field-'+chr(97+index)+'-detail.png'));bpy.ops.render.render(write_still=True)
for other in OBJECTS:other.hide_render=False
manifest={'owner':OWNER,'status':'source-ready-for-engine-review','generator':'tools/make_chamber_floor.py',
          'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'editable_blend':'Assets/Adapted/ChamberParity/Floor/ChamberFloor_Kit.blend',
          'blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),
          'source':'Original deterministic geometry from hierarchical stress splits with shared meandering paths and T-junctions, not a texture/card or downloaded scan.',
          'references':['study/visuals/chamber-target-front.png','study/visuals/chamber-target-reverse.png'],
          'preserved':'All previous Floor/FloorV3 meshes, materials, placements, characters and Unreal assets are unchanged.',
          'coordinate_system':'Metres,+Z up, localZ0 underlying floor. StaticFBX mirrors Y in project importer.',
          'fbx_settings':{'axis_forward':'-Y','axis_up':'Z','global_scale':1,'apply_unit_scale':True,'apply_scale_options':'FBX_SCALE_NONE'},
          'material_slots':SLOTS,'material_guidance':{
              'Concrete':'Existing world-aligned base-floor material, identical texture scale and world coordinates.',
              'ConcreteLight':'Existing world-aligned floor with subtle lift. Keep within about1.05–1.10 of base, not bright tiles.',
              'ConcreteDark':'Existing world-aligned floor slightly darker; cohesive wear regions, not alternating tiles.',
              'Aggregate':'Sparse detached slab edges only; muted rough concrete, not bright outlines.',
              'Dark':'Low-reflectance vertical sides of detached chips; no emission.',
              'Crack':'Nonemissive very dark, rough, zero-specular narrow recesses. Avoid reflective filament artifacts.'},
          'uv0':'SourceXYmetres/4. World-aligned base-floor binding recommended to eliminate patch seams.',
          'assets':ASSETS,'total_unique_triangles':sum(a['triangles'] for a in ASSETS),'fbx_roundtrip_checks':checks,
          'recommended_placements':placements,
          'construction_limits':'Actual shallow relief0.01–3.6cm. No displacement below original floor. Thin dark valley meshes mask the underlying floor in incised seams; real plate bevels and detached slabs provide depth. Neutral source renders do not establish recess-depth parity.',
          'integration_notes':['Use actorZ=-5cm, XYscales as listed, Zscale exactly1 and NoCollision.',
              'New fields are alternatives to old isolated A/B fracturefields and many fine-grain scatter clusters. Preserve originals and hide only overlapping old dressing after live review.',
              'Broad worn/damp mass separation remains a material/lighting job. Do not brighten every fracture edge to create detail.',
              'Exterior relief tapers toward basefloor; no surrounding black boundary/card is authored. Use same world-aligned floor colour to conceal the patch edge.',
              'Five recommendations keep broad central passages open; rotated near-border field overlap is shallow and requires actual engine z-fighting review.',
              'Root integrates and captures both chamber directions; Blender proof is source QA, not final rendered parity.'],
          'renders':['fields-overview.png','field-a-detail.png','field-b-detail.png','field-c-detail.png']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('CHAMBER_FLOOR_COMPLETE',json.dumps({'assets':3,'triangles':manifest['total_unique_triangles'],'roundtrips':len(checks)}),flush=True)
