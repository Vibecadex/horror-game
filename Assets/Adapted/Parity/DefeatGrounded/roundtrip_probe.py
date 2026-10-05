import bpy,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Teddy_DefeatGrounded.blend'))
s=bpy.context.scene;r=bpy.data.objects['TeddyRig'];m=bpy.data.objects['Teddy_Stitched']
before=set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(OUT/'Teddy_DefeatGrounded.fbx'),use_anim=True)
loaded=list(set(bpy.data.objects)-before);a=next(o for o in loaded if o.type=='ARMATURE');b=next(o for o in loaded if o.type=='MESH')
result={'fps':s.render.fps,'rig_matrix':list(map(list,r.matrix_world)),'loaded_matrix':list(map(list,a.matrix_world)),'source_action':r.animation_data.action.name,'loaded_action':a.animation_data.action.name,'source_range':list(r.animation_data.action.frame_range),'loaded_range':list(a.animation_data.action.frame_range),'samples':[]}
def p(o):
 bpy.context.view_layer.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());g=e.to_mesh();q=[e.matrix_world@v.co for v in g.vertices];e.to_mesh_clear();return q
for f in (1,2,18,36.5,54,72):
 s.frame_set(int(f),subframe=f-int(f));pa=p(m);pb=p(b)
 bones=[{'name':n.name,'src':list(n.head),'dst':list(a.pose.bones[n.name].head),'error':(n.head-a.pose.bones[n.name].head).length} for n in r.pose.bones]
 result['samples'].append({'frame':f,'src_min':min(v.z for v in pa),'dst_min':min(v.z for v in pb),'max_bone_error':max(v['error'] for v in bones),'bones':bones,'source_root_location':list(r.pose.bones['root'].location),'target_root_location':list(a.pose.bones['root'].location)})
(OUT/'roundtrip-diagnostic.json').write_text(json.dumps(result,indent=2))
print('ROUNDTRIP_DIAGNOSTIC',json.dumps(result))
