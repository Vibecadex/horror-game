"""Original preserved. Editable rig and sampled skeletal clips for the encounter."""
import bpy, math, json, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'Assets/Adapted/Teddy';OUT.mkdir(parents=True,exist_ok=True)
source=ROOT/'Assets/ThirdParty/HorrorTeddyBear/horror-teddy-bear-monster.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');mesh.name='Teddy_Stitched'
coords=[mesh.matrix_world@v.co for v in mesh.data.vertices];lo=min(v.z for v in coords);height=max(v.z for v in coords)-lo
H=4.6
for v,c in zip(mesh.data.vertices,coords):
    z=(c.z-lo)/height; x=c.x/height; y=c.y/height
    # Stronger body width, low centre of gravity and thickened thin shins.
    if .09<z<.33:
        center=math.copysign(.17,x)
        x=center+(x-center)*1.42
    v.co=(x*H*1.16,y*H*1.08,z*H)
mesh.matrix_world.identity()
for p in mesh.data.polygons:p.use_smooth=True
# One subdivision improves the faceted silhouette without replacing original UVs.
bpy.context.view_layer.objects.active=mesh;mesh.select_set(True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=.0005);bpy.ops.object.mode_set(mode='OBJECT')
mod=mesh.modifiers.new('Silhouette refinement','SUBSURF');mod.levels=1;mod.render_levels=1
bpy.ops.object.modifier_apply(modifier=mod.name)
for im in bpy.data.images:
    if im.size[0]>0:
        im.filepath_raw=str(OUT/'Teddy_BaseColor.png');im.file_format='PNG';im.save()
arm=bpy.data.armatures.new('Teddy_Skeleton');rig=bpy.data.objects.new('TeddyRig',arm);bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;mesh.select_set(False);rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
bones={}
def bone(n,a,b,parent=None):
    eb=arm.edit_bones.new(n);eb.head=Vector(a)*H;eb.tail=Vector(b)*H
    if parent:eb.parent=arm.edit_bones[parent]
    bones[n]=(Vector(a)*H,Vector(b)*H)
bone('root',(0,0,0),(0,0,.10))
bone('pelvis',(0,.06,.30),(0,.06,.43),'root')
bone('spine',(0,.06,.43),(0,.02,.64),'pelvis')
bone('head',(0,.02,.64),(0,-.05,.89),'spine')
for side,sign in [('L',1),('R',-1)]:
    bone('upperarm_'+side,(sign*.24,.04,.65),(sign*.30,-.045,.46),'spine')
    bone('forearm_'+side,(sign*.30,-.045,.46),(sign*.33,-.16,.29),'upperarm_'+side)
    bone('hand_'+side,(sign*.33,-.16,.29),(sign*.34,-.19,.20),'forearm_'+side)
    bone('thigh_'+side,(sign*.13,.07,.32),(sign*.18,.045,.17),'pelvis')
    bone('shin_'+side,(sign*.18,.045,.17),(sign*.23,-.015,.055),'thigh_'+side)
    bone('foot_'+side,(sign*.23,-.015,.055),(sign*.23,-.15,.025),'shin_'+side)
bpy.ops.object.mode_set(mode='OBJECT')
groups={n:mesh.vertex_groups.new(name=n) for n in bones}
def dist(v,a,b):
    ab=b-a;t=max(0,min(1,(v-a).dot(ab)/ab.length_squared));return (v-(a+t*ab)).length
for v in mesh.data.vertices:
    z=v.co.z/H; ax=abs(v.co.x/H);side='L' if v.co.x>=0 else 'R'
    if z>.69: candidates=['head','spine']
    elif z<.31: candidates=['pelvis','thigh_'+side,'shin_'+side,'foot_'+side] if ax<.29 else ['hand_'+side,'forearm_'+side,'foot_'+side,'shin_'+side]
    elif ax>.22:candidates=['upperarm_'+side,'forearm_'+side,'hand_'+side,'spine']
    else:candidates=['pelvis','spine','head','thigh_'+side]
    ranked=sorted(((dist(v.co,*bones[n]),n) for n in candidates))[:2]
    weights=[1/max(d,.035)**4 for d,n in ranked];total=sum(weights)
    for (_,n),weight in zip(ranked,weights):groups[n].add([v.index],weight/total,'REPLACE')
mesh.parent=rig;mod=mesh.modifiers.new('Teddy skin','ARMATURE');mod.object=rig
scene=bpy.context.scene;scene.render.fps=30
rig.animation_data_create()
clips={}
for name,count in [('Idle',90),('Walk',48),('Attack',54),('Hit',16),('Defeat',72)]:
    action=bpy.data.actions.new(name);rig.animation_data.action=action;action.use_fake_user=True
    for f in range(1,count+1):
        t=(f-1)/(count-1);cy=math.tau*t
        for pb in rig.pose.bones:pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0);pb.location=(0,0,0)
        if name=='Idle':
            rig.pose.bones['spine'].rotation_euler.x=.022*math.sin(cy)
            rig.pose.bones['head'].rotation_euler.z=.035*math.sin(cy)
        elif name=='Walk':
            for side,phase in [('L',0),('R',math.pi)]:
                sw=math.sin(cy+phase)
                rig.pose.bones['thigh_'+side].rotation_euler.x=.27*sw
                rig.pose.bones['shin_'+side].rotation_euler.x=-.32*max(0,-sw)
                rig.pose.bones['foot_'+side].rotation_euler.x=-.16*sw
                rig.pose.bones['upperarm_'+side].rotation_euler.x=-.20*sw
                rig.pose.bones['forearm_'+side].rotation_euler.x=.12*max(0,sw)
            rig.pose.bones['pelvis'].location.y=.018*H*(1-math.cos(cy*2))
            rig.pose.bones['spine'].rotation_euler.z=.035*math.sin(cy)
        elif name=='Attack':
            # Anticipate 0-.50, strike .50-.65, then recover.
            lift=min(t/.50,1) if t<.50 else max(0,1-(t-.50)/.15)
            slam=max(0,math.sin(math.pi*(t-.50)/.50)) if t>.50 else 0
            for side in ['L','R']:
                rig.pose.bones['upperarm_'+side].rotation_euler.x=-1.65*lift+.35*slam
                rig.pose.bones['forearm_'+side].rotation_euler.x=-.25*lift
            rig.pose.bones['spine'].rotation_euler.x=-.12*lift+.5*slam
            rig.pose.bones['head'].rotation_euler.x=.18*lift
        elif name=='Hit':
            rig.pose.bones['spine'].rotation_euler.x=-.22*math.sin(math.pi*t)
            rig.pose.bones['head'].rotation_euler.z=.12*math.sin(math.pi*t)
        else:
            fall=min(t/.75,1);fall=fall*fall*(3-2*fall)
            rig.pose.bones['root'].rotation_euler.x=math.radians(82)*fall
            rig.pose.bones['root'].location.z=.12*H*fall
            rig.pose.bones['spine'].rotation_euler.x=.30*fall
            for side in ['L','R']:rig.pose.bones['upperarm_'+side].rotation_euler.x=-.5*fall
        for pb in rig.pose.bones:
            pb.keyframe_insert('rotation_euler',frame=f,group=pb.name);pb.keyframe_insert('location',frame=f,group=pb.name)
    scene.frame_start=1;scene.frame_end=count;scene.frame_set(1)
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig
    fbx=OUT/f'Teddy_{name}.fbx'
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE')
    clips[name]={'frames':count,'fps':30,'export':str(fbx)}
rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_end=90;scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Teddy_Encounter.blend'))
(OUT/'adaptation.json').write_text(json.dumps({'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'height_m':H,'bones':list(bones),'clips':clips,'vertices':len(mesh.data.vertices),'triangles':sum(len(p.vertices)-2 for p in mesh.data.polygons),'notes':'Original-derived, smoothed and bulked mesh; custom weighted skeleton and original sampled clips. Ground-contact review pending in Unreal.'},indent=2))
print('TEDDY_RIG_EXPORTED')
