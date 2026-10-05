"""One original sparse, large concrete slab cluster. No Unreal writes.

Only Assets/Adapted/ChamberParity/Slabs is written. Metres, floorZ=0,
existing static-FBX -Y/+Z convention. Previous source kits stay untouched.
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
OUT=ROOT/'Assets/Adapted/ChamberParity/Slabs'
OWNER='teddy-chamber-sparse-slabs-20261005'
if OUT.exists() and any(OUT.iterdir()):
    marker=OUT/'manifest.json'
    if not marker.exists() or json.loads(marker.read_text(encoding='utf-8')).get('owner')!=OWNER:
        raise RuntimeError('Refusing to overwrite unowned slab folder')
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'manifest.json').write_text(json.dumps({'owner':OWNER,'status':'authoring'}),encoding='utf-8')
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
SLOTS=['Concrete','Aggregate','Dark'];MATS={}
for name,lo,hi in [('Concrete',(.13,.146,.137,1),(.245,.251,.227,1)),
                   ('Aggregate',(.12,.128,.117,1),(.215,.220,.198,1)),
                   ('Dark',(.012,.018,.014,1),(.039,.048,.038,1))]:
    mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.diffuse_color=hi
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    shader=nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.98
    shader.inputs['Specular IOR Level'].default_value=0
    coords=nodes.new('ShaderNodeNewGeometry')
    noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=27;noise.inputs['Detail'].default_value=4
    links.new(coords.outputs['Position'],noise.inputs['Vector'])
    ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=lo;ramp.color_ramp.elements[1].color=hi
    links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs['Color'],shader.inputs['Base Color'])
    fine=nodes.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=160;fine.inputs['Detail'].default_value=3
    links.new(coords.outputs['Position'],fine.inputs['Vector'])
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.28;bump.inputs['Distance'].default_value=.003
    links.new(fine.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],shader.inputs['Normal'])
    MATS[name]=mat

verts=[];faces=[];indices=[];pieces=[]


def polygon(points,material):
    start=len(verts);verts.extend(points);vectors=[Vector(v) for v in points]
    lookup={tuple(v):start+i for i,v in enumerate(vectors)}
    for tri in tessellate_polygon([vectors]):
        faces.append(tuple(start+i if isinstance(i,int) else lookup[tuple(i)] for i in tri))
        indices.append(SLOTS.index(material))


# Hand-composed uneven gaps: no ring, repeated grid, circular chips or gravel.
# Size denotes actual maximum footprint chord, not an unverified radius.
PLACEMENT=[(-1.39,-.85,.63,23),(-.62,-.82,.33,-20),(.13,-.96,.48,71),
           (1.12,-.82,.65,-31),(1.52,-.23,.32,-62),(.72,-.10,.46,14),
           (-.23,-.38,.61,-15),(-1.24,-.03,.42,43),(-1.40,.76,.54,-8),
           (-.53,.62,.31,120),(.32,.37,.56,57),(1.08,.72,.48,45),
           (.25,1.08,.29,-60),(-.94,1.10,.26,90),(.85,1.15,.29,0),
           (-1.54,.36,.27,12)]
rng=random.Random(1065187)
for index,(cx,cy,span,angle) in enumerate(PLACEMENT):
    triangle=index in (1,9,14)
    if triangle:
        profile=[(-.57,-.30),(.51,-.20),(-.09,.55)]
    else:
        profile=[(-.51,-.39),(.47,-.31),(.38,.47),(-.42,.36)]
    profile=[(x+rng.uniform(-.11,.09),y+rng.uniform(-.10,.08)) for x,y in profile]
    # A single deep edge bite plus chipped corners preserve each slab's broad
    # quadrilateral/triangular identity rather than rounding it into a pebble.
    contour=[]
    for j,a in enumerate(profile):
        b=profile[(j+1)%len(profile)]
        contour.append(a)
        if j==(index%len(profile)):
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            u=rng.uniform(.31,.67);depth=rng.uniform(.025,.064)
            contour.extend([(a[0]+dx*(u-.08),a[1]+dy*(u-.08)),
                            (a[0]+dx*u-dy/length*depth,a[1]+dy*u+dx/length*depth),
                            (a[0]+dx*(u+.09),a[1]+dy*(u+.09))])
    chord=max(math.dist(a,b) for a in contour for b in contour)
    scale=span/chord;c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle))
    local=[(scale*(c*x-s*y),scale*(s*x+c*y)) for x,y in contour]
    poly=[(cx+x,cy+y) for x,y in local]
    tilt_angle=rng.uniform(0,math.tau)
    projections=[x*math.cos(tilt_angle)+y*math.sin(tilt_angle) for x,y in local]
    low,high=min(projections),max(projections)
    thickness=rng.uniform(.014,.021)
    lift=rng.uniform(.007,.027)
    # Every slab physically touches near one edge: lowest underside0.06cm.
    top_heights=[.0006+thickness+lift*(p-low)/(high-low) for p in projections]
    bevel=rng.uniform(.006,.012)
    bottom=[];outside=[];inside=[]
    for (x,y),z in zip(poly,top_heights):
        vx,vy=cx-x,cy-y;length=max(.01,math.hypot(vx,vy))
        bottom.append((x,y,z-thickness))
        outside.append((x,y,z-bevel*.50))
        inside.append((x+vx/length*bevel,y+vy/length*bevel,z))
    polygon(inside,'Concrete')
    n=len(poly)
    for j in range(n):
        k=(j+1)%n
        polygon([inside[j],outside[j],outside[k],inside[k]],'Concrete' if j%3 else 'Aggregate')
        polygon([outside[j],bottom[j],bottom[k],outside[k]],'Aggregate')
    polygon(list(reversed(bottom)),'Dark')
    pieces.append({'index':index,'centre_m':[cx,cy],'footprint_chord_cm':max(math.dist(a,b) for a in poly for b in poly)*100,
                   'base_shape':'broken triangle' if triangle else 'broken irregular quadrilateral',
                   'top_min_cm':min(top_heights)*100,'top_max_cm':max(top_heights)*100,
                   'lowest_underside_cm':min(p[2] for p in bottom)*100,'angle_degrees':angle})

mesh=bpy.data.meshes.new('SM_ChamberSparseSlabs_Geometry');mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new('SM_ChamberSparseSlabs',mesh);scene.collection.objects.link(obj)
for mat in MATS.values():mesh.materials.append(mat)
for p,index in zip(mesh.polygons,indices):p.material_index=index
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
uv=mesh.uv_layers.new(name='FloorMetres_4m')
for loop in mesh.loops:
    p=mesh.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(p.x/4,p.y/4)
mesh.calc_loop_triangles()
minimum=[min(v.co[i] for v in mesh.vertices) for i in range(3)]
maximum=[max(v.co[i] for v in mesh.vertices) for i in range(3)]
dimensions=[maximum[i]-minimum[i] for i in range(3)]
assert len(pieces)==16 and min(p['footprint_chord_cm'] for p in pieces)>=25
assert max(p['footprint_chord_cm'] for p in pieces)<=65.0001
assert minimum[2]>=0 and maximum[2]<=.05
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
fbx=OUT/'SM_ChamberSparseSlabs.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',
    global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',use_mesh_modifiers=True,
    mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,path_mode='AUTO')
before=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(fbx),use_anim=False)
loaded=[o for o in set(bpy.data.objects)-before if o.type=='MESH'];assert len(loaded)==1
readback=loaded[0];points=[readback.matrix_world@v.co for v in readback.data.vertices]
actual=[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
readback.data.calc_loop_triangles();names=[s.material.name.split('.')[0] for s in readback.material_slots]
error=max(abs(a-b) for a,b in zip(actual,dimensions))
assert error<.000025 and len(readback.data.loop_triangles)==len(mesh.loop_triangles) and names==SLOTS
assert len(readback.data.uv_layers)==1
bpy.data.objects.remove(readback,do_unlink=True)


def placement(label,location,yaw):
    c,s=math.cos(math.radians(yaw)),math.sin(math.radians(yaw));points=[]
    for p in itertools.product(*zip(minimum,maximum)):
        x,y,z=p[0]*100,-p[1]*100,p[2]*100
        points.append((location[0]+c*x-s*y,location[1]+s*x+c*y,location[2]+z))
    bounds={'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
    assert bounds['min'][0]>=-1400 and bounds['max'][0]<=1480 and bounds['min'][1]>=-1500 and bounds['max'][1]<=1500
    return {'label':label,'mesh':'SM_ChamberSparseSlabs','location_cm':location,'yaw':yaw,'scale':[1,1,1],
            'collision':'NoCollision','world_bounds_cm':bounds}


placements=[placement('SparseForegroundLeft',[-1070,-720,-5],15),
            placement('SparseForegroundRight',[-1030,760,-5],-28),
            placement('SparseMidLeft',[120,-1190,-5],63),
            placement('SparseRearRight',[980,870,-5],-14)]
obj['owner']=OWNER;obj['floor_origin_m']=0;obj['piece_count']=16
bpy.ops.mesh.primitive_plane_add(size=50,location=(0,0,0))
ground=bpy.context.object;ground.name='Underlying floor preview - not exported';ground.data.materials.append(MATS['Concrete'])
world=bpy.data.worlds.new('Neutral slab study');world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.17,.18,.17,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.32;scene.world=world
for name,location,power,size in [('Raking soft key',(-3,-4,4),650,3),('Soft fill',(2,3,5),370,3)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=size
    light=bpy.data.objects.new(name,data);scene.collection.objects.link(light);light.location=location
    light.rotation_euler=(Vector((0,0,0))-light.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Sparse slab overview');camera=bpy.data.objects.new('Sparse slab overview',data)
scene.collection.objects.link(camera);camera.location=(1.2,-3.5,5)
camera.rotation_euler=(Vector((0,0,0))-camera.location).to_track_quat('-Z','Y').to_euler()
data.type='ORTHO';data.ortho_scale=4.6;scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1450;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.render.filepath=str(OUT/'slabs-overview.png')
blend=OUT/'ChamberSparseSlabs.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend));bpy.ops.render.render(write_still=True)
camera.location=(1.7,-3,1.30)
camera.rotation_euler=(Vector((-.10,-.12,.015))-camera.location).to_track_quat('-Z','Y').to_euler()
data.ortho_scale=4.0;scene.render.filepath=str(OUT/'slabs-depth.png');bpy.ops.render.render(write_still=True)
entry={'name':'SM_ChamberSparseSlabs','file':fbx.name,'sha256':hashlib.sha256(fbx.read_bytes()).hexdigest(),
       'triangles':len(mesh.loop_triangles),'vertices':len(mesh.vertices),'bounds_m':{'min':minimum,'max':maximum},
       'dimensions_m':dimensions,'expected_dimensions_cm':[100*x for x in dimensions],'highest_point_cm':100*maximum[2],
       'origin':'Underlying floor atZ0, centred cluster inXY. Floor level UEZ=-5; noZscale.',
       'material_slots':SLOTS,'slab_count':16,'slabs':pieces}
manifest={'owner':OWNER,'status':'source-ready-for-engine-review','generator':'tools/make_chamber_slabs.py',
          'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'editable_blend':'Assets/Adapted/ChamberParity/Slabs/ChamberSparseSlabs.blend',
          'blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),
          'source':'Original deterministic broken concrete geometry, hand-composed irregular sparse distribution. No external assets or textures.',
          'preserved':'Previous ChamberParity, Floor, FloorV3, room, creature and Unreal assets were read only.',
          'coordinate_system':'Metres,+Z up, floorZ0. Project static import mirrors sourceY.',
          'fbx_settings':{'axis_forward':'-Y','axis_up':'Z','global_scale':1,'apply_unit_scale':True,'apply_scale_options':'FBX_SCALE_NONE'},
          'material_slots':SLOTS,'material_guidance':{'Concrete':'Existing world-aligned floor top, neutral worn concrete.',
              'Aggregate':'Matte broken sides, subdued darker value. Roughness>=.95,specular0; avoid pale filament highlights.',
              'Dark':'Undersides only, matte near-black; no emission.'},
          'assets':[entry],'total_unique_triangles':entry['triangles'],'recommended_placements':placements,
          'fbx_roundtrip_checks':[{'name':entry['name'],'actual_dimensions_cm':[100*x for x in actual],
              'max_dimension_error_m':error,'triangles':entry['triangles'],'material_slots':names,'passed':True}],
          'renders':['slabs-overview.png','slabs-depth.png'],
          'integration':'Add at most these four margin groups asNoCollision. Preserve existingassets. These16broad slabs supplement fine rubble; do not scaleZ or scatter repeated rows.',
          'limits':'Source FBX/Blender construction verified; root owns integration, floor contact and actual two-direction chamber review.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('SPARSE_SLABS_COMPLETE',json.dumps({'pieces':16,'triangles':entry['triangles'],'dimensions_cm':entry['expected_dimensions_cm'],
                                       'max_height_cm':entry['highest_point_cm'],'fbx_error_m':error}),flush=True)
