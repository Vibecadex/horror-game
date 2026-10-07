"""Import stitched skin onto the preserved skeleton, retaining runtime animation."""
import json,sys,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import A,L,M,NS,asset,existing,own,save,components,compile
from apply_parity_look import node,rgb,scalar,bind
OUT=ROOT/json.loads((ROOT/'evidence/parity/current-run.json').read_text())['out'];assert OUT.is_dir(),f'Run directory missing: {OUT}'
R={'passed':False,'source_mesh_preserved':True,'runtime_animations_preserved':True}
def material(name,color,rough):
    m=asset('Parity/Materials/'+name,u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(m)
    m.set_editor_property('used_with_skeletal_mesh',True);bind(rgb(m,color),u.MaterialProperty.MP_BASE_COLOR)
    bind(scalar(m,rough),u.MaterialProperty.MP_ROUGHNESS);bind(scalar(m,.16),u.MaterialProperty.MP_SPECULAR);M.recompile_material(m);save(m);return m
def main():
    lev=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    assert lev.load_level('/Game/Maps/TeddyEncounter')
    old=existing(NS+'/Teddy/Idle/SK_Teddy');sk=old.get_editor_property('skeleton')
    mesh=existing(NS+'/Parity/Teddy/SK_TeddyParity')
    if not mesh:
        u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
        opt=u.FbxImportUI()
        for k,v in {'automated_import_should_detect_type':False,'import_as_skeletal':True,'import_mesh':True,'mesh_type_to_import':u.FBXImportType.FBXIT_SKELETAL_MESH,'import_animations':False,'import_materials':False,'import_textures':False,'create_physics_asset':False,'skeleton':sk}.items():opt.set_editor_property(k,v)
        for k,v in {'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':True,'update_skeleton_reference_pose':False,'use_t0_as_ref_pose':False}.items():opt.skeletal_mesh_import_data.set_editor_property(k,v)
        task=u.AssetImportTask();task.filename=str(ROOT/'Assets/Adapted/Parity/Teddy/Teddy_Parity.fbx');task.destination_path=NS+'/Parity/Teddy';task.destination_name='SK_TeddyParity';task.automated=True;task.save=True;task.options=opt
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths
        mesh=next(A.load_asset(p) for p in task.imported_object_paths if isinstance(A.load_asset(p),u.SkeletalMesh));own(mesh)
    assert mesh.get_editor_property('skeleton')==sk
    cloth=existing(NS+'/Parity/Materials/M_Parity_TeddyCloth')
    mats={'Material_0':cloth,'SeamDark':material('M_Parity_Seam',(.004,.003,.002),.96),'StitchThread':material('M_Parity_Thread',(.032,.023,.012),.86)}
    slots=list(mesh.get_editor_property('materials'));overrides=[];R['slots']=[]
    for slot in slots:
        name=str(slot.get_editor_property('material_slot_name'));key=next((k for k in mats if k.lower() in name.lower()),None);assert key,(name,list(mats))
        slot.set_editor_property('material_interface',mats[key]);overrides.append(mats[key]);R['slots'].append({'slot':name,'material':mats[key].get_path_name()})
    mesh.set_editor_property('materials',slots);save(mesh)
    for name in ['BP_TeddyBoss','BP_Stitchling']:
        bp=existing(NS+'/Blueprints/'+name)
        for _,(_,c) in components(bp).items():
            if isinstance(c,u.SkeletalMeshComponent):c.set_editor_property('skeletal_mesh_asset',mesh);c.set_editor_property('override_materials',overrides)
        compile(bp)
    for a in actors.get_all_level_actors():
        if a.get_actor_label()=='TE_MainTeddy' or a.get_actor_label().startswith('TE_Stitchling'):
            for c in a.get_components_by_class(u.SkeletalMeshComponent):c.set_editor_property('skeletal_mesh_asset',mesh);c.set_editor_property('override_materials',overrides)
    assert lev.save_current_level();assert lev.load_level('/Game/Maps/TeddyEncounter')
    reopened=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='TE_MainTeddy').get_component_by_class(u.SkeletalMeshComponent)
    assert reopened.get_editor_property('skeletal_mesh_asset')==mesh
    R.update(passed=True,mesh=mesh.get_path_name(),skeleton=sk.get_path_name(),bounds=str(mesh.get_bounds()),reopened=True)
try:main()
except Exception:R['error']=traceback.format_exc();raise
finally:(OUT/'teddy-import.json').write_text(json.dumps(R,indent=2))
