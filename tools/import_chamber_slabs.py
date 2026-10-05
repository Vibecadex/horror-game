"""Add four sparse large-fragment groups without modifying prior floor sources."""
import sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from chamber_common import *
from import_chamber_kit import collision_off,apply_slots,sha
from chamber_floor_materials import floor
SOURCE=ROOT/'Assets/Adapted/ChamberParity/Slabs'
R={'passed':False,'actors':[],'meshes':[],'collision':'NoCollision','source_assets_preserved':True}
def main():
    begin();doc=json.loads((SOURCE/'manifest.json').read_text());assert doc['owner']=='teddy-chamber-sparse-slabs-20261005'
    pin=OUT/'chamber-slabs-reviewed.json'
    if pin.exists():assert pin.read_bytes()==(SOURCE/'manifest.json').read_bytes()
    else:pin.write_bytes((SOURCE/'manifest.json').read_bytes())
    R['manifest_sha256']=sha(pin)
    slab=floor('SlabSurface',1.4);bind(scalar(slab,.96),u.MaterialProperty.MP_ROUGHNESS);bind(scalar(slab,.06),u.MaterialProperty.MP_SPECULAR);M.recompile_material(slab);save(slab)
    mats={'Concrete':slab,**{k:existing(DEST+'/Materials/M_Chamber_Floor'+k) for k in ['Aggregate','Dark']}};assert all(mats.values())
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0');models={}
    for entry in doc['assets']:
        source=SOURCE/entry['file'];assert source.parent==SOURCE and sha(source)==entry['sha256']
        model=existing(DEST+'/Floor/'+entry['name'])
        if not model:
            options=u.FbxImportUI()
            for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH,'import_as_skeletal':False,'import_materials':False,'import_textures':False}.items():options.set_editor_property(k,v)
            for k,v in {'combine_meshes':True,'auto_generate_collision':False,'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':False}.items():options.static_mesh_import_data.set_editor_property(k,v)
            t=u.AssetImportTask();t.filename=str(source);t.destination_path=DEST+'/Floor';t.destination_name=entry['name'];t.automated=True;t.save=True;t.options=options
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);assert t.imported_object_paths;model=own(A.load_asset(t.imported_object_paths[0]))
        for i,slot in enumerate(model.get_editor_property('static_materials')):model.set_material(i,mats[str(slot.get_editor_property('material_slot_name'))])
        ext=model.get_bounds().box_extent;size=[ext.x*2,ext.y*2,ext.z*2];assert max(abs(a-b) for a,b in zip(size,entry['expected_dimensions_cm']))<.1
        save(model);models[entry['name']]=model;R['meshes'].append({'path':model.get_path_name(),'bounds_cm':size,'triangles_source':entry['triangles']})
    bylabel={a.get_actor_label():a for a in ACTORS.get_all_level_actors()}
    for p in doc['recommended_placements']:
        label='Slabs_'+p['label'];a=bylabel.get('TE_Chamber_'+label)
        if a:assert 'ChamberSlabsOwned' in [str(t) for t in a.tags]
        else:a=spawn(u.StaticMeshActor,label,p['location_cm'],u.Rotator(yaw=p['yaw']))
        a.set_actor_location(u.Vector(*p['location_cm']),False,False);a.set_actor_rotation(u.Rotator(yaw=p['yaw']),False);a.set_actor_scale3d(u.Vector(*p['scale']))
        a.set_editor_property('tags',['TeddyEncounterOwned','ChamberOwned','ChamberSlabsOwned']);a.set_actor_enable_collision(False)
        c=a.static_mesh_component;c.set_static_mesh(models[p['mesh']]);collision_off(c);apply_slots(c,mats);c.set_lighting_channels(True,False,False)
        R['actors'].append({'label':a.get_actor_label(),'placement':p})
    finish();got=[a for a in ACTORS.get_all_level_actors() if 'ChamberSlabsOwned' in [str(t) for t in a.tags]];assert len(got)==4
    for a in got:
        c=a.static_mesh_component;o,e,_=u.SystemLibrary.get_component_bounds(c);assert o.z+e.z<1.0;assert c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION
    R['passed']=True
if __name__=='__main__':
    try:main()
    except Exception:R['error']=traceback.format_exc();raise
    finally:(OUT/'chamber-slabs-import.json').write_text(json.dumps(R,indent=2))
