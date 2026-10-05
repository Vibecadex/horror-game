"""Author a separate grounded defeat while preserving the skin and source clips.

Only Assets/Adapted/Parity/DefeatGrounded is written. Original/V2 sources and
animation exports are preserved. No Unreal process is launched.
"""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Assets/Adapted/Parity/TeddyV2/Teddy_ParityV2.blend'
OUT=ROOT/'Assets/Adapted/Parity/DefeatGrounded'
OWNER='teddy-defeat-contact-audit-20261005'
OUT.mkdir(parents=True,exist_ok=True)
if (OUT/'manifest.json').exists():
    assert json.loads((OUT/'manifest.json').read_text()).get('owner')==OWNER
source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
rig=bpy.data.objects['TeddyRig']
mesh=bpy.data.objects['Teddy_Stitched']
rig.animation_data.action=bpy.data.actions['Defeat']
rig.data.pose_position='POSE'
body_count=10982
core=[v.index for v in mesh.data.vertices[:body_count]
      if 1.35<v.co.z<2.8 and abs(v.co.x)<.8]
assert core
rows=[]
for half_frame in range(2,145):
    frame=half_frame/2
    scene.frame_set(int(frame),subframe=frame-int(frame))
    bpy.context.view_layer.update()
    evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    geometry=evaluated.to_mesh()
    points=[evaluated.matrix_world@v.co for v in geometry.vertices]
    heights=sorted(p.z for p in points[:body_count])
    core_heights=sorted(points[i].z for i in core)
    rows.append({'frame':frame,'seconds':(frame-1)/30,
        'body_minimum_m':heights[0],'all_geometry_minimum_m':min(p.z for p in points),
        'body_p01_m':heights[int(body_count*.01)],'body_p05_m':heights[int(body_count*.05)],
        'body_vertices_below_5cm':sum(z<=.05 for z in heights),
        'body_vertices_below_10cm':sum(z<=.10 for z in heights),
        'torso_region_minimum_m':core_heights[0],
        'torso_region_p10_m':core_heights[int(len(core_heights)*.1)],
        'root_location':list(rig.pose.bones['root'].location),
        'root_head_world_m':list(rig.pose.bones['root'].head)})
    evaluated.to_mesh_clear()
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
manifest={'owner':OWNER,'status':'diagnosis_no_animation_change',
    'source':str(SOURCE.relative_to(ROOT)),'source_sha256_before':source_hash,'source_sha256_after':source_hash,
    'generator':'tools/make_parity_defeat.py','animation':'Defeat','frame_count':72,'fps':30,
    'deformed_body_vertices':body_count,'samples':rows,
    'source_minimum_range_m':[min(r['body_minimum_m'] for r in rows),max(r['body_minimum_m'] for r in rows)],
    'last_frame':rows[-1],
    'torso_region_definition':'Original rest vertices with Z between1.35 and2.8m, |X|<.8m; descriptive body-core subset, not a collision proxy.',
    'runtime_offset':'Saved actor227.150002cm minus mesh230cm gives mesh origin -2.849998cm. Arena floor is -5cm, so add2.150002cm to local source height for floor clearance.',
    'finding':'At integer frames the original deformation is already minimum-height corrected to1.2cm. Final pose rests on a small head surface area while torso and limbs remain high. Root-Z lowering alone cannot lower the torso without head penetration.',
    'correction_applied':False,'unreal_writes':False,
    'next_action':'Integration owner to distinguish tiny clearance adjustment from a substantive collapse-pose revision; no misleading root-only grounded export is produced.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')

# Render the final source pose with a level ground plane and clear side lighting.
scene.frame_set(72)
world=bpy.data.worlds.new('Contact audit studio')
world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.17,.2,.22,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
scene.world=world
mat=bpy.data.materials.new('Contact audit floor')
mat.diffuse_color=(.13,.18,.18,1)
bpy.ops.mesh.primitive_plane_add(size=40,location=(0,0,0))
plane=bpy.context.object
plane.name='Audit ground Z0 - never exported'
plane.data.materials.append(mat)
for name,loc,power,size in [('Audit key',(-6,-6,8),1800,5),('Audit fill',(5,2,5),900,4)]:
    data=bpy.data.lights.new(name,'AREA')
    data.energy=power;data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector((0,-1.8,1.1))-obj.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Contact audit side')
camera=bpy.data.objects.new('Contact audit side',data);scene.collection.objects.link(camera)
camera.location=(9,-5,4)
camera.rotation_euler=(Vector((0,-1.8,1.2))-camera.location).to_track_quat('-Z','Y').to_euler()
data.type='ORTHO';data.ortho_scale=7
scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1400;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.render.filepath=str(OUT/'source-defeat-contact-side.png')
bpy.ops.render.render(write_still=True)
print('DEFEAT_CONTACT_AUDIT',json.dumps({'minimum_range_m':manifest['source_minimum_range_m'],'last_frame':rows[-1],'manifest':str(OUT/'manifest.json')}),flush=True)

# The integration owner approved an animation-only pose revision after this
# audit proved that translation alone would preserve the headstand failure.
(OUT/'source-audit.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
source_audit=manifest
original_scene_fps=scene.render.fps
assert original_scene_fps==30
source_files=[SOURCE,ROOT/'Assets/Adapted/Teddy/Teddy_Encounter.blend']+list((ROOT/'Assets/Adapted/Teddy').glob('Teddy_*.fbx'))
source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
body_vertices=[tuple(v.co) for v in mesh.data.vertices]
body_polygons=[tuple(p.vertices) for p in mesh.data.polygons]
body_uvs={layer.name:[tuple(uv.uv) for uv in layer.data] for layer in mesh.data.uv_layers}
body_weights=[[(g.group,g.weight) for g in v.groups] for v in mesh.data.vertices]
bone_names=[b.name for b in rig.data.bones]
bone_parents={b.name:b.parent.name if b.parent else None for b in rig.data.bones}
CLIPS={'Idle':90,'Walk':37,'Crawl':37,'Attack':54,'Hit':16,'Defeat':72}

def geometry_points(obj=mesh):
    bpy.context.view_layer.update()
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    gm=ev.to_mesh()
    result=[ev.matrix_world@v.co for v in gm.vertices]
    ev.to_mesh_clear()
    return result

source_poses={}
for name,count in CLIPS.items():
    rig.animation_data.action=bpy.data.actions[name]
    for frame in (1,(count+1)//2,count):
        scene.frame_set(frame)
        source_poses[(name,frame)]=geometry_points()
rig.animation_data.action=bpy.data.actions['Defeat']
scene.frame_set(1)
start_pose={p.name:{'location':p.location.copy(),'rotation':p.rotation_euler.copy(),'scale':p.scale.copy()} for p in rig.pose.bones}
start_points=geometry_points()
action=bpy.data.actions.new('DefeatGrounded')
action.use_fake_user=True
rig.animation_data.action=action

# A broad torso-supporting plane replaces the original head-first inversion.
# Only small secondary joint changes are used: the preserved source skinning
# does not support the large folded-leg trial poses without visible distortion.
normal=Vector((-.71844,-.69379,-.05)).normalized()
world_rest_quaternion=normal.rotation_difference(Vector((0,0,1)))
rest_basis=rig.data.bones['root'].matrix_local.to_3x3()
end_quaternion=(rest_basis.inverted()@world_rest_quaternion.to_matrix()@rest_basis).to_quaternion()
start_quaternion=start_pose['root']['rotation'].to_quaternion()
previous_euler=start_pose['root']['rotation'].copy()

def smooth(value):
    x=max(0,min(1,value))
    return x*x*x*(x*(x*6-15)+10)

authored=[]
for half in range(2,145):
    frame=half/2
    seconds=(frame-1)/30
    scene.frame_set(int(frame),subframe=frame-int(frame))
    fall=smooth((seconds-.10)/1.48)
    settle=smooth((seconds-1.18)/.95)
    for p in rig.pose.bones:
        p.rotation_mode='XYZ'
        p.location=start_pose[p.name]['location']
        p.rotation_euler=start_pose[p.name]['rotation']
        p.scale=start_pose[p.name]['scale']
    root=rig.pose.bones['root']
    root.rotation_euler=start_quaternion.slerp(end_quaternion,fall).to_euler('XYZ',previous_euler)
    previous_euler=root.rotation_euler.copy()
    rig.pose.bones['head'].rotation_euler.x-=.14*settle
    rig.pose.bones['head'].rotation_euler.z-=.08*settle
    rig.pose.bones['upperarm_R'].rotation_euler.z-=.08*settle
    rig.pose.bones['forearm_R'].rotation_euler.z-=.025*settle
    rig.pose.bones['thigh_R'].rotation_euler.z-=.06*settle
    rig.pose.bones['shin_R'].rotation_euler.z-=.035*settle
    # True deformed geometry is measured at every 1/60 second authoring sample.
    points=geometry_points()
    correction=.012-min(p.z for p in points)
    root.location+=rest_basis.inverted()@Vector((0,0,correction))
    for p in rig.pose.bones:
        p.keyframe_insert('rotation_euler',frame=frame,group=p.name)
        p.keyframe_insert('location',frame=frame,group=p.name)
    points=geometry_points()
    authored.append({'frame':frame,'seconds':seconds,'body_minimum_m':min(p.z for p in points[:body_count]),
        'all_geometry_minimum_m':min(p.z for p in points),'torso_minimum_m':min(points[i].z for i in core),
        'root_location':list(root.location),'root_world_z_m':root.head.z,
        'fall_fraction':fall,'settle_fraction':settle})

# Linear dense samples avoid Bezier overshoot of the corrected support height.
slot=rig.animation_data.action_slot
for layer in action.layers:
    for strip in layer.strips:
        bag=strip.channelbag(slot)
        if bag:
            for curve in bag.fcurves:
                for key in curve.keyframe_points:
                    key.interpolation='LINEAR'
scene.frame_start=1
scene.frame_end=72
scene.frame_set(1)
start_error=max((a-b).length for a,b in zip(geometry_points(),start_points))
assert start_error<.000002,start_error

verified=[]
previous_points=None
max_quarter_step=0
for quarter in range(4,289):
    frame=quarter/4
    scene.frame_set(int(frame),subframe=frame-int(frame))
    points=geometry_points()
    low=min(p.z for p in points)
    if previous_points:
        max_quarter_step=max(max_quarter_step,max((a-b).length for a,b in zip(points,previous_points)))
    previous_points=points
    verified.append({'frame':frame,'seconds':(frame-1)/30,'minimum_m':low,
        'body_minimum_m':min(p.z for p in points[:body_count]),
        'torso_minimum_m':min(points[i].z for i in core),'maximum_m':max(p.z for p in points)})
assert min(p['minimum_m'] for p in verified)>.005, min(p['minimum_m'] for p in verified)
assert max(p['minimum_m'] for p in verified)<.023, max(p['minimum_m'] for p in verified)
assert verified[-1]['torso_minimum_m']<.08,verified[-1]
assert max_quarter_step<.12,max_quarter_step

# Older source actions must continue to deform this copied skin identically.
pose_checks=[]
for (name,frame),expected in source_poses.items():
    rig.animation_data.action=bpy.data.actions[name]
    scene.frame_set(frame)
    error=max((a-b).length for a,b in zip(geometry_points(),expected))
    assert error<.000002,(name,frame,error)
    pose_checks.append({'clip':name,'frame':frame,'max_surface_error_m':error,'passed':True})
rig.animation_data.action=action
scene.frame_set(1)
assert [tuple(v.co) for v in mesh.data.vertices]==body_vertices
assert [tuple(p.vertices) for p in mesh.data.polygons]==body_polygons
assert [[(g.group,g.weight) for g in v.groups] for v in mesh.data.vertices]==body_weights
for name,uvs in body_uvs.items():
    assert [tuple(uv.uv) for uv in mesh.data.uv_layers[name].data]==uvs
assert [b.name for b in rig.data.bones]==bone_names
assert {b.name:b.parent.name if b.parent else None for b in rig.data.bones}==bone_parents

bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig
export=OUT/'Teddy_DefeatGrounded.fbx'
bpy.ops.export_scene.fbx(filepath=str(export),use_selection=True,object_types={'ARMATURE','MESH'},
    add_leaf_bones=False,bake_anim=True,bake_anim_step=.5,bake_anim_use_all_actions=False,
    bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z',
    apply_unit_scale=True,mesh_smooth_type='FACE')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Teddy_DefeatGrounded.blend'))

# Round-trip the animation and check actual animated surface heights/shape.
before=set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(export),use_anim=True,anim_offset=0)
loaded=list(set(bpy.data.objects)-before)
loaded_rig=next(o for o in loaded if o.type=='ARMATURE')
loaded_mesh=next(o for o in loaded if o.type=='MESH')
assert [b.name for b in loaded_rig.data.bones]==bone_names
assert {b.name:b.parent.name if b.parent else None for b in loaded_rig.data.bones}==bone_parents
roundtrip_samples=[]
for frame in (1,18,36.5,54,72):
    scene.frame_set(int(frame),subframe=frame-int(frame))
    expected=geometry_points()
    actual=geometry_points(loaded_mesh)
    # FBX can split UV vertices; compare height and bone heads, not vertex index.
    minimum_error=abs(min(v.z for v in expected)-min(v.z for v in actual))
    bone_error=max((rig.pose.bones[b].head-loaded_rig.pose.bones[b].head).length for b in bone_names)
    assert minimum_error<.001,(frame,minimum_error)
    assert bone_error<.001,(frame,bone_error)
    roundtrip_samples.append({'frame':frame,'minimum_height_error_m':minimum_error,
        'maximum_bone_head_error_m':bone_error,'passed':True})
for obj in loaded:
    bpy.data.objects.remove(obj,do_unlink=True)
preservation=[]
for relative,expected in source_hashes.items():
    actual=hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
    assert actual==expected,relative
    preservation.append({'path':relative,'sha256':actual,'unchanged':True})

manifest={'owner':OWNER,'status':'corrected_collapse_animation_ready_for_unreal',
    'source':str(SOURCE.relative_to(ROOT)),'source_sha256_before':source_hash,'source_sha256_after':source_hash,
    'generator':'tools/make_parity_defeat.py','animation':'DefeatGrounded','fbx':export.name,
    'fbx_sha256':hashlib.sha256(export.read_bytes()).hexdigest(),'frames':72,'fps':30,'duration_seconds':71/30,
    'authored_samples_per_second':60,'authoring_sample_count':len(authored),'verification_samples_per_second':120,
    'verification_sample_count':len(verified),'minimum_height_range_m':[min(p['minimum_m'] for p in verified),max(p['minimum_m'] for p in verified)],
    'final_torso_minimum_m':verified[-1]['torso_minimum_m'],'source_final_torso_minimum_m':source_audit['last_frame']['torso_region_minimum_m'],
    'start_pose_max_surface_error_m':start_error,'maximum_surface_displacement_per_1_120_second_m':max_quarter_step,
    'motion':'Small initial hold, smooth side/back fall, then delayed gentle head/limb settling. Height is corrected from evaluated skin at60Hz; final0.23s holds the resting pose. No physics or body/rig edits.',
    'reason':'Original Defeat was mathematically floor-corrected but balanced on its head, leaving torso core1.395m high. The revised support direction puts the torso on the ground without burying the head.',
    'transition_observations':['Starts at the exact original Defeat surface pose.','Whole-body rotation follows a smooth quaternion path, baked to compatible Euler tracks.','Secondary rotations stay below8degrees to avoid stressing the preserved procedural skin weights.','Ground contact uses actual deformed vertices, not bone or render bounds.','The final pose remains still rather than snapping into a second rest pose.'],
    'body_geometry_uvs_weights_and_skeleton_unchanged':True,'original_action_pose_checks':pose_checks,
    'authored_heights':authored,'verified_heights':verified,'fbx_roundtrip':{'passed':True,'bone_count':len(bone_names),'samples':roundtrip_samples},
    'preservation':preservation,'unreal_writes':False,
    'unreal_import':'Import only animation onto the existing teddy Skeleton, force_front_x_axis=True as original imports; import_mesh=False, do not update reference pose. Use custom_sample_rate60 if available to retain dense samples. Save as a new owned A_Teddy_DefeatGrounded and update only the intended defeat reference.',
    'limits':'Blender contact and FBX motion verified. Runtime mesh offset adds about2.15cm above local source heights; actual Unreal capture and gameplay transition remain required. Existing rig/character anatomy remains stylized.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')

# Same copied skin/materials, distinct mid/end views; studio objects never export.
for filename,frame,view in [('corrected-mid-side.png',36.5,'side'),('corrected-end-side.png',72,'side'),('corrected-end-game-angle.png',72,'game')]:
    scene.frame_set(int(frame),subframe=frame-int(frame))
    points=geometry_points()
    lo=Vector([min(p[i] for p in points) for i in range(3)]);hi=Vector([max(p[i] for p in points) for i in range(3)])
    center=(lo+hi)/2
    camera.location=center+(Vector((8,-9,5.5)) if view=='side' else Vector((-8,-5,10)))
    camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    data.ortho_scale=9.2 if view=='game' else 7
    scene.render.filepath=str(OUT/filename)
    bpy.ops.render.render(write_still=True)
print('DEFEAT_GROUNDED_COMPLETE',json.dumps({'file':str(export),'minimum_height_range_m':manifest['minimum_height_range_m'],
    'final_torso_minimum_m':manifest['final_torso_minimum_m'],'preserved_pose_checks':len(pose_checks),'roundtrip':True}),flush=True)
