"""Bind separately reviewed connected shallow fields; preserve every old asset."""
import sys,json,hashlib,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from chamber_common import *
from import_chamber_kit import collision_off,apply_slots,sha,hide
from chamber_floor_materials import floor
SOURCE=ROOT/'Assets/Adapted/ChamberParity/Floor'
R={'passed':False,'actors':[],'meshes':[],'concealed':[],'original_assets_preserved':True}
def material_set():
    # The same immutable world mapping and surface inputs join new tops to base.
    out={'Concrete':floor('Concrete')}
    for key,factor in [('ConcreteLight',1.14),('ConcreteDark',.82),('Aggregate',.85)]:
        out[key]=floor(key,factor)
        if key=='Aggregate':
            m=out[key];bind(scalar(m,.98),u.MaterialProperty.MP_ROUGHNESS);bind(scalar(m,.07),u.MaterialProperty.MP_SPECULAR)
            M.recompile_material(m);save(m)
    for key,color in [('Crack',(.012,.016,.014)),('Dark',(.023,.027,.024))]:
        m=newmat('Floor'+key);bind(rgb(m,color),u.MaterialProperty.MP_BASE_COLOR)
        bind(scalar(m,1),u.MaterialProperty.MP_ROUGHNESS);bind(scalar(m,0),u.MaterialProperty.MP_SPECULAR)
        M.recompile_material(m);save(m);out[key]=m
    assert all(out.values());return out
def main():
    begin();doc=json.loads((SOURCE/'manifest.json').read_text());assert doc['owner']=='teddy-chamber-connected-floor-20261005'
    pin=OUT/'chamber-floor-reviewed.json'
    if pin.exists():assert pin.read_bytes()==(SOURCE/'manifest.json').read_bytes()
    else:pin.write_bytes((SOURCE/'manifest.json').read_bytes())
    R['manifest_sha256']=sha(pin);mats=material_set();models={}
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    for entry in doc['assets']:
        source=SOURCE/entry['file'];assert source.parent==SOURCE and sha(source)==entry['sha256']
        obj=existing(DEST+'/Floor/'+entry['name'])
        if not obj:
            options=u.FbxImportUI()
            for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH,'import_as_skeletal':False,'import_materials':False,'import_textures':False}.items():options.set_editor_property(k,v)
            for k,v in {'combine_meshes':True,'auto_generate_collision':False,'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':False}.items():options.static_mesh_import_data.set_editor_property(k,v)
            t=u.AssetImportTask();t.filename=str(source);t.destination_path=DEST+'/Floor';t.destination_name=entry['name'];t.automated=True;t.save=True;t.options=options
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);assert t.imported_object_paths;obj=own(A.load_asset(t.imported_object_paths[0]))
        for i,slot in enumerate(obj.get_editor_property('static_materials')):
            key=str(slot.get_editor_property('material_slot_name'));assert key in mats;obj.set_material(i,mats[key])
        ext=obj.get_bounds().box_extent;actual=[ext.x*2,ext.y*2,ext.z*2]
        assert max(abs(a-b) for a,b in zip(actual,entry['expected_dimensions_cm']))<.1
        save(obj);models[entry['name']]=obj;R['meshes'].append({'path':obj.get_path_name(),'bounds_cm':actual,'sha256':entry['sha256']})
    bylabel={a.get_actor_label():a for a in ACTORS.get_all_level_actors()}
    bylabel['TE_ArenaFloor'].static_mesh_component.set_material(0,mats['Concrete'])
    for a in bylabel.values():
        if a.get_actor_label().startswith('TE_Parity_Floor_'):
            apply_slots(a.static_mesh_component,mats)
    # Connected fields replace old isolated crack islands and fine interior grit.
    # Keep original actor transforms/collision and mesh packages available.
    conceal=list(range(4))+list(range(23,45))+[11,12,13,14,16,18,19,20]
    for index in conceal:
        label='TE_Parity_Floor_'+str(index).zfill(3);a=bylabel[label];hide(a);R['concealed'].append(label)
    for item in doc['recommended_placements']:
        label='Floor_'+item['label'];a=bylabel.get('TE_Chamber_'+label)
        if a:assert 'ChamberFloorOwned' in [str(t) for t in a.tags]
        else:a=spawn(u.StaticMeshActor,label,item['location_cm'],u.Rotator(yaw=item['yaw']))
        a.set_actor_location(u.Vector(*item['location_cm']),False,False);a.set_actor_rotation(u.Rotator(yaw=item['yaw']),False);a.set_actor_scale3d(u.Vector(*item['scale']))
        a.set_editor_property('tags',['TeddyEncounterOwned','ChamberOwned','ChamberFloorOwned']);a.set_actor_enable_collision(False)
        c=a.static_mesh_component;c.set_static_mesh(models[item['mesh']]);collision_off(c);apply_slots(c,mats);c.set_lighting_channels(True,False,False)
        R['actors'].append({'label':a.get_actor_label(),'placement':item})
    finish()
    found=[a for a in ACTORS.get_all_level_actors() if 'ChamberFloorOwned' in [str(t) for t in a.tags]];assert len(found)==len(doc['recommended_placements'])
    for a in found:assert a.static_mesh_component.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION
    R['passed']=True
if __name__=='__main__':
    try:main()
    except Exception:R['error']=traceback.format_exc();raise
    finally:(OUT/'chamber-floor-import.json').write_text(json.dumps(R,indent=2))
