"""Bind reviewed broad concrete plates and retire only the superseded spall look.

Original assets and transforms remain preserved; new decoration has no collision.
"""
import sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from chamber_common import *
from import_chamber_kit import collision_off,apply_slots,sha,hide
from chamber_floor_materials import floor

SOURCE=ROOT/'Assets/Adapted/ChamberParity/CrustNormalsV2'
R={'passed':False,'actors':[],'meshes':[],'concealed':[],
   'source_assets_preserved':True,'collision':'NoCollision'}

def main():
    begin();doc=json.loads((SOURCE/'manifest.json').read_text())
    assert doc['owner']=='teddy-chamber-crust-normals-v2-20261005'
    assert len(doc['assets'])==2 and len(doc['recommended_placements'])==5
    assert all(c['passed'] for c in doc['fbx_roundtrip_checks'])
    assert all(e['highest_point_cm']<=4.8 for e in doc['assets'])
    pin=OUT/'chamber-crust-v2-reviewed.json'
    if pin.exists():assert pin.read_bytes()==(SOURCE/'manifest.json').read_bytes()
    else:pin.write_bytes((SOURCE/'manifest.json').read_bytes())
    R['manifest_sha256']=sha(pin)
    mats={}
    # Quieter coherent tops allow geometry to carry the broken-plate silhouette.
    profile={'detail_weight':.30,'normal_mix':.20}
    for key,factor in [('Concrete',1.),('ConcreteLight',1.15),('ConcreteDark',.85)]:
        m=floor('Crust'+key,factor,profile)
        bind(scalar(m,.95),u.MaterialProperty.MP_ROUGHNESS)
        bind(scalar(m,.06),u.MaterialProperty.MP_SPECULAR)
        M.recompile_material(m);save(m);mats[key]=m
    for key in ['Aggregate','Dark','Crack']:
        mats[key]=existing(DEST+'/Materials/M_Chamber_Floor'+key)
    assert all(mats.values())
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    models={}
    for entry in doc['assets']:
        source=SOURCE/entry['file'];assert source.parent==SOURCE and sha(source)==entry['sha256']
        model=existing(DEST+'/Crust/'+entry['name'])
        if not model:
            options=u.FbxImportUI()
            for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH,'import_as_skeletal':False,'import_materials':False,'import_textures':False}.items():options.set_editor_property(k,v)
            for k,v in {'combine_meshes':True,'auto_generate_collision':False,'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':False}.items():options.static_mesh_import_data.set_editor_property(k,v)
            task=u.AssetImportTask();task.filename=str(source);task.destination_path=DEST+'/Crust';task.destination_name=entry['name'];task.automated=True;task.save=True;task.options=options
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths
            model=own(A.load_asset(task.imported_object_paths[0]));assert isinstance(model,u.StaticMesh)
        for i,slot in enumerate(model.get_editor_property('static_materials')):
            model.set_material(i,mats[str(slot.get_editor_property('material_slot_name'))])
        ext=model.get_bounds().box_extent;size=[ext.x*2,ext.y*2,ext.z*2]
        assert max(abs(a-b) for a,b in zip(size,entry['expected_dimensions_cm']))<.1
        save(model);models[entry['name']]=model
        R['meshes'].append({'path':model.get_path_name(),'bounds_cm':size,'triangles_source':entry['triangles']})
    bylabel={a.get_actor_label():a for a in ACTORS.get_all_level_actors()}
    for p in doc['recommended_placements']:
        assert p['scale'][2]==1 and p['location_cm'][2]==-5
        label='Crust_'+p['label'];a=bylabel.get('TE_Chamber_'+label)
        if a:assert 'ChamberCrustOwned' in [str(t) for t in a.tags]
        else:a=spawn(u.StaticMeshActor,label,p['location_cm'],u.Rotator(yaw=p['yaw']))
        a.set_actor_location(u.Vector(*p['location_cm']),False,False)
        a.set_actor_rotation(u.Rotator(yaw=p['yaw']),False)
        a.set_actor_scale3d(u.Vector(*p['scale']))
        a.set_editor_property('tags',['TeddyEncounterOwned','ChamberOwned','ChamberCrustOwned'])
        a.set_actor_enable_collision(False)
        c=a.static_mesh_component;c.set_static_mesh(models[p['mesh']]);collision_off(c);apply_slots(c,mats)
        c.set_lighting_channels(True,False,False)
        material_readback=[]
        for i,slot in enumerate(c.static_mesh.get_editor_property('static_materials')):
            key=str(slot.get_editor_property('material_slot_name'))
            assert c.get_material(i)==mats[key]
            material_readback.append({'slot':key,'material':c.get_material(i).get_path_name()})
        R['actors'].append({'label':a.get_actor_label(),'placement':p,'material_readback':material_readback})
    for index in list(range(4,11))+[15,17]:
        label='TE_Parity_Floor_'+str(index).zfill(3);hide(bylabel[label]);R['concealed'].append(label)
    finish()
    got=[a for a in ACTORS.get_all_level_actors() if 'ChamberCrustOwned' in [str(t) for t in a.tags]]
    assert {a.get_actor_label() for a in got}=={'TE_Chamber_Crust_'+p['label'] for p in doc['recommended_placements']}
    for a in got:
        c=a.static_mesh_component;o,e,_=u.SystemLibrary.get_component_bounds(c)
        assert o.z+e.z<0.0 and o.z-e.z>=-5.1
        assert not a.get_actor_enable_collision() and c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION
    R['passed']=True

if __name__=='__main__':
    try:main()
    except Exception:R['error']=traceback.format_exc();raise
    finally:(OUT/'chamber-crust-import.json').write_text(json.dumps(R,indent=2))
