import bpy,math,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Assets/Adapted/Arena'
bpy.ops.wm.read_factory_settings(use_empty=True)
verts=[];faces=[]
for i in range(128):
    theta=math.tau*i/128
    for radius in [4.62,4.75]:verts.append((radius*math.cos(theta),radius*math.sin(theta),0))
for i in range(128):
    j=(i+1)%128;faces.append((2*i,2*i+1,2*j+1,2*j))
mesh=bpy.data.meshes.new('Anticipation annulus');mesh.from_pydata(verts,[],faces);mesh.update()
o=bpy.data.objects.new('AttackRing',mesh);bpy.context.collection.objects.link(o);o.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.export_scene.fbx(filepath=str(OUT/'AttackRing.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Encounter_Details.blend'))
