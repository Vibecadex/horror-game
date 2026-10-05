"""Bake planted IK strides and floor-corrected reactions into the owned rig; no runtime Python."""
import bpy,math,json,zipfile
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Assets/Adapted/Teddy'
backup=ROOT/'evidence/implementation/teddy-before-contact-refinement.zip'
if not backup.exists():
    with zipfile.ZipFile(backup,'w',zipfile.ZIP_DEFLATED) as z:
        for p in OUT.iterdir():
            if p.suffix in ['.blend','.fbx','.json']:z.write(p,p.name)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Teddy_Encounter.blend'))
rig=bpy.data.objects['TeddyRig'];mesh=bpy.data.objects['Teddy_Stitched'];scene=bpy.context.scene;scene.render.fps=30
metrics={}
for clip,speed,stride in [('Walk',105,.756),('Crawl',55,1.13)]:
    if clip in bpy.data.actions:bpy.data.actions[clip].name=clip+'_PreContact'
    action=bpy.data.actions.new(clip);action.use_fake_user=True;rig.animation_data.action=action
    targets={};helpers=[]
    for side in ['L','R']:
        target=bpy.data.objects.new(clip+'_Ankle_'+side,None);bpy.context.collection.objects.link(target);targets[side]=target;helpers.append(target)
        ik=rig.pose.bones['shin_'+side].constraints.new('IK');ik.target=target;ik.chain_count=2;ik.use_stretch=False
        orient=bpy.data.objects.new(clip+'_FootPlane_'+side,None);bpy.context.collection.objects.link(orient);orient.rotation_mode='QUATERNION';orient.rotation_quaternion=rig.data.bones['foot_'+side].matrix_local.to_quaternion();helpers.append(orient)
        flat=rig.pose.bones['foot_'+side].constraints.new('COPY_ROTATION');flat.target=orient;flat.owner_space='WORLD';flat.target_space='WORLD'
    for f in range(1,38):
        t=(f-1)/36;phase=math.tau*t
        for pb in rig.pose.bones:pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0);pb.location=(0,0,0)
        rig.pose.bones['pelvis'].location.y=(-.12 if clip=='Walk' else -.48)+.025*math.cos(phase*2)
        rig.pose.bones['spine'].rotation_euler.x=.06 if clip=='Walk' else .38
        rig.pose.bones['spine'].rotation_euler.z=.025*math.sin(phase)
        rig.pose.bones['head'].rotation_euler.x=-.03 if clip=='Walk' else -.15
        for side,shift in [('L',0),('R',.5)]:
            q=(t+shift)%1;ankle=rig.data.bones['shin_'+side].tail_local.copy()
            if q<.6:advance=-stride*.5+stride*q/.6;lift=0
            else:
                swing=(q-.6)/.4;smooth=swing*swing*(3-2*swing);advance=stride*.5-stride*smooth;lift=.21*math.sin(math.pi*swing)
            targets[side].location=ankle+Vector((0,advance,lift));targets[side].keyframe_insert('location',frame=f)
            rig.pose.bones['upperarm_'+side].rotation_euler.x=-.22*math.sin(phase+shift*math.tau)+(0 if clip=='Walk' else .35)
            rig.pose.bones['forearm_'+side].rotation_euler.x=-.08 if clip=='Walk' else .2
        for pb in rig.pose.bones:
            pb.keyframe_insert('rotation_euler',frame=f,group=pb.name);pb.keyframe_insert('location',frame=f,group=pb.name)
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
    bpy.ops.nla.bake(frame_start=1,frame_end=37,step=1,only_selected=False,visual_keying=True,clear_constraints=True,use_current_action=True,bake_types={'POSE'})
    for ob in helpers:bpy.data.objects.remove(ob,do_unlink=True)
    metrics[clip]={'stride_cm_local':stride*100,'cycle_seconds':1.2,'stance_fraction':.6,'matched_world_speed_cm_s':speed,'scale_for_speed':1 if clip=='Walk' else .35}
# Correct the actual skinned surface against the floor, including the fall; retain every clip.
for name,count in [('Idle',90),('Walk',37),('Crawl',37),('Attack',54),('Hit',16),('Defeat',72)]:
    rig.animation_data.action=bpy.data.actions[name];scene.frame_start=1;scene.frame_end=count;offsets=[]
    for f in range(1,count+1):
        scene.frame_set(f);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();evaluated=mesh.evaluated_get(deps);geo=evaluated.to_mesh()
        lowest=min((evaluated.matrix_world@v.co).z for v in geo.vertices);evaluated.to_mesh_clear()
        correction=.012-lowest;pb=rig.pose.bones['root'];pb.location+=rig.data.bones['root'].matrix_local.to_3x3().inverted()@Vector((0,0,correction));pb.keyframe_insert('location',frame=f,group='root');offsets.append(correction)
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig;scene.frame_set(1)
    bpy.ops.export_scene.fbx(filepath=str(OUT/('Teddy_'+name+'.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE')
    metrics.setdefault(name,{}).update(frames=count,ground_correction_range_m=[min(offsets),max(offsets)])
rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_end=90;scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Teddy_Encounter.blend'))
(OUT/'motion-refinement.json').write_text(json.dumps(metrics,indent=2))
print('CONTACT_MOTION_EXPORTED')
