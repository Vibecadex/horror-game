"""Reframe the owned preview only; do not rewrite the validated FBX or blend."""
import bpy
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Teddy_DefeatGrounded.blend'))
s=bpy.context.scene;r=bpy.data.objects['TeddyRig'];m=bpy.data.objects['Teddy_Stitched']
r.animation_data.action=bpy.data.actions['DefeatGrounded'];s.frame_set(72)
bpy.context.view_layer.update();ev=m.evaluated_get(bpy.context.evaluated_depsgraph_get());geo=ev.to_mesh()
points=[ev.matrix_world@v.co for v in geo.vertices];ev.to_mesh_clear()
lo=Vector([min(p[i] for p in points) for i in range(3)]);hi=Vector([max(p[i] for p in points) for i in range(3)])
center=(lo+hi)/2;cam=s.camera;cam.location=center+Vector((-8,-5,10))
cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=9.2
s.render.filepath=str(OUT/'corrected-end-game-angle.png');bpy.ops.render.render(write_still=True)
