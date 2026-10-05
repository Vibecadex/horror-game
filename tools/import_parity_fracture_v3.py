"""Import separately preserved interrupted fracture geometry with aligned wear."""
from pathlib import Path
import json,sys,traceback
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import A,NS,existing,own,save
from apply_parity_combined import floor,OUT
R={'passed':False,'actors':[],'prior_fracture_mesh_preserved':True}
def main():
    lev=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    assert lev.load_level('/Game/Maps/TeddyEncounter')
    folder=ROOT/'Assets/Adapted/Parity/FloorV3';entry=json.loads((folder/'manifest.json').read_text())['assets'][0]
    name=entry['name'];path=NS+'/Parity/Floor/'+name;model=existing(path)
    if not model:
        u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
        task=u.AssetImportTask();task.filename=str(folder/entry['file']);task.destination_path=NS+'/Parity/Floor';task.destination_name=name;task.automated=True;task.save=True
        options=u.FbxImportUI()
        for k,v in {'import_mesh':True,'import_as_skeletal':False,'import_materials':False,'import_textures':False,'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH}.items():options.set_editor_property(k,v)
        for k,v in {'combine_meshes':True,'auto_generate_collision':False,'convert_scene':True,'convert_scene_unit':True}.items():options.static_mesh_import_data.set_editor_property(k,v)
        task.options=options;u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths
        model=own(A.load_asset(task.imported_object_paths[0]))
    materials={'Concrete':existing(NS+'/Parity/Materials/M_Parity_CombinedFloor'),
        'Aggregate':existing(NS+'/Parity/Materials/M_Parity_Aggregate'),'Dark':existing(NS+'/Parity/Materials/M_Parity_Crack'),
        'ConcreteLight':floor('M_Parity_CombinedFloorLight',1.18),'ConcreteDark':floor('M_Parity_CombinedFloorDark',.82)}
    for i,slot in enumerate(model.get_editor_property('static_materials')):
        key=str(slot.get_editor_property('material_slot_name'));assert key in materials;model.set_material(i,materials[key])
    save(model);b=model.get_bounds();actual=[b.box_extent.x*2,b.box_extent.y*2,b.box_extent.z*2]
    assert all(abs(a-b)<max(.06,b*.01) for a,b in zip(actual,entry['expected_dimensions_cm']))
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label() in ['TE_Parity_Floor_000','TE_Parity_Floor_001']:
            assert 'ParityOwned' in [str(t) for t in actor.tags]
            c=actor.static_mesh_component;c.set_static_mesh(model);c.set_collision_profile_name('NoCollision');c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);actor.set_actor_enable_collision(False)
            R['actors'].append(actor.get_actor_label())
    assert len(R['actors'])==2;assert lev.save_current_level();assert lev.load_level('/Game/Maps/TeddyEncounter')
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label() in R['actors']:assert actor.static_mesh_component.static_mesh==model and actor.static_mesh_component.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION
    R.update(passed=True,dimensions_cm=actual,mesh=model.get_path_name(),saved_reload=True)
try:main()
except Exception:R['error']=traceback.format_exc();raise
finally:(OUT/'fracture-v3-import.json').write_text(json.dumps(R,indent=2))
