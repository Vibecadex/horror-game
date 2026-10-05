import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Assets/Adapted/Parity/TeddyV2/Teddy_ParityV2.blend'))
s=bpy.context.scene;r=bpy.data.objects['TeddyRig'];m=bpy.data.objects['Teddy_Stitched']
r.animation_data.action=None;r.data.pose_position='POSE'
core=[v.index for v in m.data.vertices[:10982] if 1.35<v.co.z<2.8 and abs(v.co.x)<.8]
head=[v.index for v in m.data.vertices[:10982] if v.co.z>3.25]
def points():
 bpy.context.view_layer.update();e=m.evaluated_get(bpy.context.evaluated_depsgraph_get());g=e.to_mesh();p=[e.matrix_world@v.co for v in g.vertices];e.to_mesh_clear();return p
world=bpy.data.worlds.new('Ground pose studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Strength'].default_value=.4;s.world=world
mat=bpy.data.materials.new('Ground pose floor');mat.diffuse_color=(.15,.19,.19,1)
bpy.ops.mesh.primitive_plane_add(size=40);bpy.context.object.data.materials.append(mat)
for name,loc,power in [('Key',(-4,-5,8),1900),('Fill',(7,2,6),1500)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=5;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,1.3,1))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Rest pose camera');cam=bpy.data.objects.new('Rest pose camera',d);s.collection.objects.link(cam);s.camera=cam;cam.location=(9,-5,5);cam.rotation_euler=(Vector((0,1,1.2))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=7
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.resolution_x=1100;s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
variants=[('support_side_back',(-.617076,-.735403,-.28)),('support_low_side',(-.71844,-.69379,-.05)),('support_flat_side',(-.76,-.64,.10))]
rows=[]
for name,normal in variants:
 for pb in r.pose.bones:pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0);pb.location=(0,0,0)
 n=Vector(normal).normalized();q=n.rotation_difference(Vector((0,0,1)));rest=r.data.bones['root'].matrix_local.to_3x3()
 pb=r.pose.bones['root'];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(rest.inverted()@q.to_matrix()@rest).to_quaternion()
 p=points();dz=.012-min(v.z for v in p);pb.location+=rest.inverted()@Vector((0,0,dz));p=points()
 lo=Vector([min(v[i] for v in p) for i in range(3)]);hi=Vector([max(v[i] for v in p) for i in range(3)]);center=(lo+hi)/2
 cam.location=center+Vector((8,-9,6));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();d.ortho_scale=7
 row={'name':name,'normal':list(n),'min_height':min(v.z for v in p),'max_height':max(v.z for v in p),'core_min':min(p[i].z for i in core),'head_min':min(p[i].z for i in head),'near_ground_5cm':sum(v.z<.05 for v in p[:10982]),'root_vertical':dz}
 rows.append(row);s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);print('POSE',json.dumps(row),flush=True)
(OUT/'support-poses.json').write_text(json.dumps(rows,indent=2))
