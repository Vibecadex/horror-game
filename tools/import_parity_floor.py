"""Import additive physical floor dressing; all new decoration is non-colliding."""
import json,sys,traceback,math
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import A,M,NS,asset,own,save,existing
from apply_parity_look import node,scalar,rgb,bind,mul,noise,blend
SRC=ROOT/'Assets/Adapted/Parity/Floor';KIT=json.loads((SRC/'manifest.json').read_text())
OUT=Path(json.loads((ROOT/'evidence/parity/current-run.json').read_text())['out'])
R={'passed':False,'meshes':[],'actors':[],'new_mesh_collision':'NoCollision','source_unchanged':True,'revision':'placements-v2'}
def simple(name,a,b):
    m=asset('Parity/Materials/'+name,u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(m)
    world=node(m,u.MaterialExpressionWorldPosition);n=noise(m,world,.11)
    bind(blend(m,rgb(m,a),rgb(m,b),n),u.MaterialProperty.MP_BASE_COLOR)
    bind(scalar(m,.92),u.MaterialProperty.MP_ROUGHNESS);bind(scalar(m,.13),u.MaterialProperty.MP_SPECULAR)
    M.recompile_material(m);save(m);return m
def main():
    lev=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    assert lev.load_level('/Game/Maps/TeddyEncounter')
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    materials={'Concrete':existing(NS+'/Parity/Materials/M_Parity_Floor'),'Aggregate':simple('M_Parity_Aggregate',(.15,.155,.14),(.23,.235,.21)),'Dark':simple('M_Parity_Crack',(.009,.012,.01),(.025,.029,.024))}
    models={}
    for entry in KIT['assets']:
        name=entry['name'];path=NS+'/Parity/Floor/'+name;model=existing(path)
        if not model:
            t=u.AssetImportTask();t.filename=str(SRC/entry['file']);t.destination_path=NS+'/Parity/Floor';t.destination_name=name;t.automated=True;t.save=True
            options=u.FbxImportUI();options.set_editor_property('import_mesh',True);options.set_editor_property('import_as_skeletal',False)
            options.set_editor_property('import_materials',False);options.set_editor_property('import_textures',False)
            options.set_editor_property('automated_import_should_detect_type',False);options.set_editor_property('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH)
            options.static_mesh_import_data.set_editor_property('combine_meshes',True);options.static_mesh_import_data.set_editor_property('auto_generate_collision',False)
            options.static_mesh_import_data.set_editor_property('convert_scene',True);options.static_mesh_import_data.set_editor_property('convert_scene_unit',True)
            t.options=options;u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);assert t.imported_object_paths;model=own(A.load_asset(t.imported_object_paths[0]));assert isinstance(model,u.StaticMesh)
        for i,s in enumerate(model.get_editor_property('static_materials')):
            slot=str(s.get_editor_property('material_slot_name'));assert slot in materials,slot;model.set_material(i,materials[slot])
        save(model);bounds=model.get_bounds();size=[bounds.box_extent.x*2,bounds.box_extent.y*2,bounds.box_extent.z*2]
        assert all(abs(a-b)<max(.05,b*.01) for a,b in zip(size,entry['expected_dimensions_cm'])),(name,size,entry['expected_dimensions_cm'])
        models[name]=model;R['meshes'].append({'name':name,'dimensions_cm':size})
    for a in list(actors.get_all_level_actors()):
        if a.get_actor_label().startswith('TE_Parity_Floor_'):
            assert 'ParityOwned' in [str(t) for t in a.tags];actors.destroy_actor(a)
    placements=json.loads((SRC/'placements-v2.json').read_text())['recommended_placements']
    assert placements
    for i,p in enumerate(placements):
        model=models[p.get('asset',p.get('mesh'))];loc=p.get('location_cm',p.get('location'))
        scale=p.get('scale',[1,1,1]);yaw=p['rotation_deg'][1]
        a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*loc),u.Rotator(yaw=yaw),transient=False)
        a.set_actor_label('TE_Parity_Floor_'+str(i).zfill(3));a.set_folder_path('TeddyEncounter/Parity/Floor')
        a.set_editor_property('tags',['TeddyEncounterOwned','ParityOwned','ParityFloorDecor']);a.set_actor_scale3d(u.Vector(*scale))
        c=a.static_mesh_component;c.set_static_mesh(model);c.set_collision_profile_name('NoCollision');c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);a.set_actor_enable_collision(False)
        R['actors'].append({'label':a.get_actor_label(),'mesh':model.get_name(),'location':loc,'scale':scale,'yaw':yaw})
    assert lev.save_current_level();assert lev.load_level('/Game/Maps/TeddyEncounter')
    saved=[a for a in actors.get_all_level_actors() if a.get_actor_label().startswith('TE_Parity_Floor_')]
    assert len(saved)==len(placements)
    R['saved_readback']=[{'label':a.get_actor_label(),'profile':str(a.static_mesh_component.get_collision_profile_name()),'enabled':str(a.static_mesh_component.get_collision_enabled())} for a in saved]
    assert all(a.static_mesh_component.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION for a in saved)
    R['passed']=True
try:main()
except Exception:R['error']=traceback.format_exc();raise
finally:(OUT/'floor-import-v2.json').write_text(json.dumps(R,indent=2))
