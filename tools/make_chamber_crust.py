"""Final bounded chamber floor geometry: two shallow asymmetric crust banks.

Only Assets/Adapted/ChamberParity/Crust is written. Earlier kits and all Unreal
assets remain untouched. Metres, floorZ0, standard project static-FBX axes.
"""
import bpy
import bmesh
import hashlib
import itertools
import json
import math
import random
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Assets/Adapted/ChamberParity/Crust'
OWNER='teddy-chamber-crust-20261005'
if OUT.exists() and any(OUT.iterdir()):
    marker=OUT/'manifest.json'
    if not marker.exists() or json.loads(marker.read_text(encoding='utf-8')).get('owner')!=OWNER:
        raise RuntimeError('Refusing to overwrite unowned Crust directory')
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'manifest.json').write_text(json.dumps({'owner':OWNER,'status':'authoring'}),encoding='utf-8')
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
SLOTS=['Concrete','ConcreteLight','ConcreteDark','Aggregate','Dark','Crack']
MATS={}
for name,color in [('Concrete',(.215,.227,.209,1)),('ConcreteLight',(.251,.261,.237,1)),
                   ('ConcreteDark',(.164,.180,.168,1)),('Aggregate',(.174,.183,.164,1)),
                   ('Dark',(.021,.027,.022,1)),('Crack',(.015,.023,.018,1))]:
    mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.diffuse_color=color
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    shader=nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.98
    shader.inputs['Specular IOR Level'].default_value=0;shader.inputs['Base Color'].default_value=color
    geom=nodes.new('ShaderNodeNewGeometry')
    noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=58;noise.inputs['Detail'].default_value=3
    links.new(geom.outputs['Position'],noise.inputs['Vector'])
    ramp=nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=tuple(v*.90 for v in color[:3])+(1,)
    ramp.color_ramp.elements[1].color=tuple(v*1.08 for v in color[:3])+(1,)
    links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],shader.inputs['Base Color'])
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.17;bump.inputs['Distance'].default_value=.003
    links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],shader.inputs['Normal'])
    MATS[name]=mat


def centroid(poly):return (sum(x for x,y in poly)/len(poly),sum(y for x,y in poly)/len(poly))


def clip(poly,nx,ny,d):
    result=[];a=poly[-1];da=a[0]*nx+a[1]*ny-d
    for b in poly:
        db=b[0]*nx+b[1]*ny-d
        if (da<=0)!=(db<=0):
            t=da/(da-db);result.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
        if db<=0:result.append(b)
        a,da=b,db
    return result


class Geometry:
    def __init__(self):self.vertices=[];self.faces=[];self.mats=[]
    def polygon(self,points,material):
        if len(points)<3:return
        vectors=[Vector(p) for p in points];start=len(self.vertices);self.vertices.extend(points)
        lookup={tuple(v):start+i for i,v in enumerate(vectors)}
        for tri in tessellate_polygon([vectors]):
            self.faces.append(tuple(start+v if isinstance(v,int) else lookup[tuple(v)] for v in tri))
            self.mats.append(SLOTS.index(material))
    def bank_plate(self,poly,top_height,material,rng,taper=True):
        cx,cy=centroid(poly);n=len(poly);lower=[];outer=[];inner=[]
        # Broad bevels are eroded surface, not bright one-pixel rim decoration.
        for j,(x,y) in enumerate(poly):
            vx,vy=cx-x,cy-y;distance=max(.02,math.hypot(vx,vy))
            bevel=rng.uniform(.025,.052)
            fade=max(.10,min(1,(1.14-y)/.49)) if taper else 1
            z=.003+(top_height-.003)*fade
            z=max(.003,min(.032,z+rng.uniform(-.0018,.0018)*fade))
            inner.append((x+vx/distance*bevel,y+vy/distance*bevel,z))
            outer.append((x,y,max(.0025,z-rng.uniform(.006,.013)*fade)))
            # Eroded overhang sits on its own dark underside, no painted shadow.
            undercut=rng.uniform(.010,.024)*fade
            lower.append((x+vx/distance*undercut,y+vy/distance*undercut,.0012))
        # Triangulate a subtly irregular face, preserving broad calm areas.
        self.polygon(inner,material)
        for j in range(n):
            k=(j+1)%n
            self.polygon([inner[j],outer[j],outer[k],inner[k]],'Aggregate' if j%4==0 else material)
            self.polygon([outer[j],lower[j],lower[k],outer[k]],'Aggregate')
        self.polygon(list(reversed(lower)),'Dark')
        return min(p[2] for p in inner),max(p[2] for p in inner)
    def fragment(self,poly,height,rng):
        cx,cy=centroid(poly);n=len(poly);a=rng.uniform(0,math.tau)
        projection=[(x-cx)*math.cos(a)+(y-cy)*math.sin(a) for x,y in poly]
        low,high=min(projection),max(projection);lower=[];outer=[];inner=[]
        for j,((x,y),p) in enumerate(zip(poly,projection)):
            lift=.010*(p-low)/max(.001,high-low)
            z=min(.0475,height+lift);base=.0013+lift
            vx,vy=cx-x,cy-y;d=max(.01,math.hypot(vx,vy));bevel=.010
            inner.append((x+vx/d*bevel,y+vy/d*bevel,z))
            outer.append((x,y,z-.005));lower.append((x,y,base))
        self.polygon(inner,'ConcreteLight' if rng.random()<.3 else 'Concrete')
        for j in range(n):
            k=(j+1)%n
            self.polygon([inner[j],outer[j],outer[k],inner[k]],'Aggregate')
            self.polygon([outer[j],lower[j],lower[k],outer[k]],'Aggregate')
        self.polygon(list(reversed(lower)),'Dark')
        return max(p[2] for p in inner)
    def valley(self,points,width):
        for a,b in zip(points,points[1:]):
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            if length<1e-7:continue
            nx,ny=-dy/length*width/2,dx/length*width/2
            self.polygon([(a[0]-nx,a[1]-ny,.0015),(b[0]-nx,b[1]-ny,.0015),
                          (b[0]+nx,b[1]+ny,.0015),(a[0]+nx,a[1]+ny,.0015)],'Crack')


ASSETS=[];OBJECTS=[]


def build(name,seed,variant):
    rng=random.Random(seed);geo=Geometry()
    boundary=[(-1.94,-.72),(-1.23,-1.13),(.68,-1.03),(1.91,-.57),
              (1.91,.41),(1.24,1.10),(-.48,1.26),(-1.75,.79)]
    base=[(-1.26,.84),(-.26,.92),(.58,.73),(1.49,.66),
          (-1.48,.08),(-.58,.18),(.26,-.04),(1.14,.08),
          (-1.24,-.58),(-.32,-.66),(.57,-.56),(1.45,-.36)]
    sites=[(x+rng.uniform(-.13,.13),y+rng.uniform(-.11,.11)) for x,y in base]
    cells=[];edges={}
    for sx,sy in sites:
        poly=boundary[:]
        for ox,oy in sites:
            if (ox,oy)==(sx,sy):continue
            poly=clip(poly,ox-sx,oy-sy,(ox*ox+oy*oy-sx*sx-sy*sy)/2)
        poly=[(round(x,6),round(y,6)) for x,y in poly]
        cells.append(poly)
        for a,b in zip(poly,poly[1:]+poly[:1]):
            key=tuple(sorted((a,b)));edges.setdefault(key,{'owners':0})['owners']+=1
    for key,edge in edges.items():
        a,b=key;dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        local=random.Random(int(hashlib.sha256(repr((seed,key)).encode()).hexdigest()[:12],16))
        steps=max(3,min(10,int(length/.13)+1));points=[]
        for i in range(steps+1):
            t=i/steps;offset=math.sin(math.pi*t)*local.uniform(-.035,.035)
            points.append((a[0]+dx*t-dy/length*offset,a[1]+dy*t+dx/length*offset))
        edge['points']=points;edge['width']=local.uniform(.025,.051)
    plate_rows=[]
    for index,cell in enumerate(cells):
        loop=[]
        for a,b in zip(cell,cell[1:]+cell[:1]):
            key=tuple(sorted((a,b)));path=edges[key]['points']
            if a!=key[0]:path=list(reversed(path))
            loop.extend(path[:-1])
        cx,cy=centroid(loop);inset=rng.uniform(.014,.031);poly=[]
        for j,(x,y) in enumerate(loop):
            vx,vy=cx-x,cy-y;d=max(.01,math.hypot(vx,vy))
            # Occasional damaged corners create wide notches amongst narrower
            # 3–7cm joints, instead of uniform ink outlines.
            amount=inset+(rng.uniform(.025,.070) if j%9==index%9 else rng.uniform(0,.008))
            if y>.87:amount*=.4
            poly.append((x+vx/d*amount,y+vy/d*amount))
        top=rng.uniform(.021,.031)
        material='ConcreteLight' if cx<.15 and cy<.45 else 'Concrete'
        if cx>.62 and cy>.1:material='ConcreteDark'
        lo,hi=geo.bank_plate(poly,top,material,rng)
        plate_rows.append({'index':index,'centre_m':[cx,cy],'footprint_chord_cm':max(math.dist(a,b) for a in poly for b in poly)*100,
                           'top_height_cm':[lo*100,hi*100],'material':material,'rear_outer_taper':True})
    for edge in edges.values():
        if edge['owners']>1:geo.valley(edge['points'],edge['width'])
    # Irregular sparse debris is concentrated at three broken lips on one side.
    # Its footprint, not a complete rim, extends the group to about4.8×3.6m.
    fragments=[];occupied=[]
    lobes=[(-1.25,-1.17),(.23,-1.44),(1.98,-.55)]
    for i in range(27):
        lx,ly=lobes[0 if i<8 else 1 if i<19 else 2]
        span=rng.uniform(.13,.26) if i%5 else rng.uniform(.29,.45)
        for attempt in range(100):
            x=max(-2.23,min(2.23,lx+rng.gauss(0,.32)))
            y=max(-1.93,min(.85,ly+rng.gauss(0,.24)))
            if all(math.hypot(x-ox,y-oy)>(span+os)*.42+.015 for ox,oy,os in occupied):break
        occupied.append((x,y,span))
        angle=rng.uniform(0,math.tau)
        local=[(-.52,-.32),(.49,-.39),(.33,.44),(-.37,.38)] if i%6 else [(-.53,-.33),(.48,-.24),(.01,.47)]
        local=[(px+rng.uniform(-.10,.10),py+rng.uniform(-.08,.08)) for px,py in local]
        chord=max(math.dist(a,b) for a in local for b in local);scale=span/chord;c,s=math.cos(angle),math.sin(angle)
        poly=[(x+scale*(c*px-s*py),y+scale*(s*px+c*py)) for px,py in local]
        top=geo.fragment(poly,rng.uniform(.021,.036),rng)
        fragments.append({'centre_m':[x,y],'footprint_chord_cm':span*100,'top_cm':top*100})
    # Shift/stretch only the layout for the alternate bank, preserving all slab
    # relief. There is no second identical silhouette under another filename.
    if variant:
        geo.vertices=[(-x+.10*math.sin(y*3.3),y*.97+.085*math.sin(x*2.4),z) for x,y,z in geo.vertices]
    mesh=bpy.data.meshes.new(name+'_Geometry');mesh.from_pydata(geo.vertices,[],geo.faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj)
    for material in MATS.values():mesh.materials.append(material)
    for face,index in zip(mesh.polygons,geo.mats):face.material_index=index
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    uv=mesh.uv_layers.new(name='FloorMetres_4m')
    for loop in mesh.loops:
        p=mesh.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(p.x/4,p.y/4)
    mesh.calc_loop_triangles();minimum=[min(v.co[i] for v in mesh.vertices) for i in range(3)]
    maximum=[max(v.co[i] for v in mesh.vertices) for i in range(3)]
    assert minimum[2]>=0 and maximum[2]<=.048
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    file=OUT/(name+'.fbx')
    bpy.ops.export_scene.fbx(filepath=str(file),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',
        global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',use_mesh_modifiers=True,
        mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,path_mode='AUTO')
    entry={'name':name,'file':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'triangles':len(mesh.loop_triangles),
           'vertices':len(mesh.vertices),'bounds_m':{'min':minimum,'max':maximum},'dimensions_m':[maximum[i]-minimum[i] for i in range(3)],
           'expected_dimensions_cm':[(maximum[i]-minimum[i])*100 for i in range(3)],'highest_point_cm':maximum[2]*100,
           'material_slots':SLOTS,'plate_count':12,'fragment_count':27,'plates':plate_rows,'fragments':fragments,
           'coordinate_note':'VariantB component coordinates above are pre-warp composition data; exported bounds/placement use actual vertices.' if variant else 'Component coordinates match exported layout.',
           'origin':'Underlying floorZ0; XYnearcentre. NoCollision, actorZ-5cm,Zscale1.'}
    ASSETS.append(entry);OBJECTS.append(obj);obj['owner']=OWNER
    print('CRUST_ASSET',name,entry['triangles'],entry['expected_dimensions_cm'],flush=True)


build('SM_ChamberCrustBank_A',179241,False)
build('SM_ChamberCrustBank_B',197538,True)
checks=[]
for entry in ASSETS:
    before=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(OUT/entry['file']),use_anim=False)
    loaded=[o for o in set(bpy.data.objects)-before if o.type=='MESH'];assert len(loaded)==1
    obj=loaded[0];points=[obj.matrix_world@v.co for v in obj.data.vertices]
    dimensions=[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
    error=max(abs(a-b) for a,b in zip(dimensions,entry['dimensions_m']));obj.data.calc_loop_triangles()
    names=[slot.material.name.split('.')[0] for slot in obj.material_slots]
    assert error<.000025 and names==SLOTS and len(obj.data.loop_triangles)==entry['triangles'] and len(obj.data.uv_layers)==1
    checks.append({'name':entry['name'],'max_dimension_error_m':error,'actual_dimensions_cm':[100*x for x in dimensions],
                   'triangles':entry['triangles'],'material_slots':names,'passed':True})
    bpy.data.objects.remove(obj,do_unlink=True)


def placement(label,index,location,yaw):
    entry=ASSETS[index];c,s=math.cos(math.radians(yaw)),math.sin(math.radians(yaw));points=[]
    for p in itertools.product(*zip(entry['bounds_m']['min'],entry['bounds_m']['max'])):
        x,y,z=p[0]*100,-p[1]*100,p[2]*100
        points.append((location[0]+c*x-s*y,location[1]+s*x+c*y,location[2]+z))
    bounds={'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
    assert bounds['min'][0]>=-1400 and bounds['max'][0]<=1480 and bounds['min'][1]>=-1500 and bounds['max'][1]<=1500
    return {'label':label,'mesh':entry['name'],'location_cm':location,'yaw':yaw,'scale':[1,1,1],
            'collision':'NoCollision','world_bounds_cm':bounds}


placements=[placement('LeftFront',0,[-500,-950,-5],30),placement('ForegroundCentre',1,[-1040,20,-5],-8),
            placement('RightSide',0,[-300,1170,-5],90),placement('RearRight',1,[1080,160,-5],100),
            placement('RearLeft',0,[780,-900,-5],-35)]

# Neutral source proof with intentionally quiet tops. Root may bind its lower-
# frequency floor sibling; a granular wet floor shader would conceal relief.
for obj,x in zip(OBJECTS,[-2.75,2.75]):obj.location=(x,0,0)
bpy.ops.mesh.primitive_plane_add(size=100,location=(0,0,0))
ground=bpy.context.object;ground.name='Underlying floor preview - not exported';ground.data.materials.append(MATS['ConcreteDark'])
world=bpy.data.worlds.new('Crust material study');world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.17,.18,.17,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.32;scene.world=world
for name,location,power,size in [('Raking key',(-4,-6,7),1200,4),('Soft fill',(5,5,9),800,5)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=location
    obj.rotation_euler=(Vector((0,0,0))-obj.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Two crust banks');camera=bpy.data.objects.new('Two crust banks',data);scene.collection.objects.link(camera)
camera.location=(0,-7,10);camera.rotation_euler=(Vector((0,-.3,0))-camera.location).to_track_quat('-Z','Y').to_euler()
data.type='ORTHO';data.ortho_scale=11.6;scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1700;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.render.filepath=str(OUT/'crust-overview.png')
blend=OUT/'ChamberCrust_Kit.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend));bpy.ops.render.render(write_still=True)
for index,obj in enumerate(OBJECTS):
    OBJECTS[1-index].hide_render=True
    camera.location=(obj.location.x+1.6,-4.0,2.7)
    camera.rotation_euler=(Vector((obj.location.x,-.35,.02))-camera.location).to_track_quat('-Z','Y').to_euler()
    data.ortho_scale=5.5;scene.render.resolution_x=1450;scene.render.resolution_y=1100
    scene.render.filepath=str(OUT/('crust-'+chr(97+index)+'-depth.png'));bpy.ops.render.render(write_still=True)
    OBJECTS[1-index].hide_render=False
manifest={'owner':OWNER,'status':'source-ready-for-engine-review','generator':'tools/make_chamber_crust.py',
          'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'editable_blend':'Assets/Adapted/ChamberParity/Crust/ChamberCrust_Kit.blend','blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),
          'source':'Original deterministic connected eroded-crust geometry for final floor correction. Quiet broad plates, actual chipped overhangs, broken joints and sparse one-sided debris; no external assets.',
          'preserved':'All previous ChamberParity, floor, slab, wall, creature and Unreal assets remain untouched.',
          'coordinate_system':'Metres,+Z up,floorZ0. Existing project staticFBX mirrorsY.',
          'fbx_settings':{'axis_forward':'-Y','axis_up':'Z','global_scale':1,'apply_unit_scale':True,'apply_scale_options':'FBX_SCALE_NONE'},
          'material_slots':SLOTS,'assets':ASSETS,'total_unique_triangles':sum(a['triangles'] for a in ASSETS),
          'fbx_roundtrip_checks':checks,'recommended_placements':placements,
          'material_guidance':{'Concrete':'Quiet mineral floor base, keep broad values visible. Suggested granular detailweight.25–.35,normal.15–.25.',
             'ConcreteLight':'Coherent dry crust tops about1.15–1.20basevalue, matte; no per-edge glow.',
             'ConcreteDark':'Coherent darker crust region about.80–.85basevalue, matte.',
             'Aggregate':'Eroded broad bevel/side faces; mutedmatte roughness>=.95,specular0.',
             'Dark':'Dark undersides only,noemission.',
             'Crack':'Broken joint troughs only,veryrough zero specular,noemission.'},
          'integration':['Five new NoCollision margin actors atZ-5cm,Zscale1. All rotated AABBs remain inside reviewed combatguard.',
              'Visually conceal original TE_Parity_Floor_004 through010 EdgeSpall arcs, preserving their transforms/assets/collision.',
              'Consider hiding original scatter015/017 where new foreground/right crust banks occupythe same region. Retain scatter021/022 only if useful context afterrender.',
              'New crust is a bounded morphology correction; retain five quieter connectedfields and four sparse-slab groups.',
              'Proposed bank placements avoid the four sparse-slab centres; root can adjust only after checking exact rotatedbounds and bothcameraviews.',
              'Root owns actual Unrealsaves, materialcontrast and finalframe/motion inspection. Sourcepreviews donotprove renderedparity.'],
          'renders':['crust-overview.png','crust-a-depth.png','crust-b-depth.png']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('CRUST_COMPLETE',json.dumps({'meshes':2,'placements':len(placements),'triangles':manifest['total_unique_triangles'],
                                 'max_height_cm':max(a['highest_point_cm'] for a in ASSETS)}),flush=True)
