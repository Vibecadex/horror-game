"""Import corrected floor winding into new assets; preserve shading and layout."""
import sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from chamber_common import *
from import_chamber_kit import collision_off,sha

R={'passed':False,'material_graphs_changed':False,'actor_transforms_changed':False,'groups':[]}
SPECS=[
    {'folder':'FloorNormalsV2','original':'Floor','owner':'teddy-chamber-floor-normals-v2-20261005',
     'pin':'chamber-floor-v2-reviewed.json','tag':'ChamberFloorOwned','prefix':'Floor_', 'count':5,'meshes':3},
    {'folder':'SlabsNormalsV2','original':'Slabs','owner':'teddy-chamber-slabs-normals-v2-20261005',
     'pin':'chamber-slabs-v2-reviewed.json','tag':'ChamberSlabsOwned','prefix':'Slabs_','count':4,'meshes':1},
]

def main():
    begin();bylabel={a.get_actor_label():a for a in ACTORS.get_all_level_actors()}
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    for spec in SPECS:
        source=ROOT/'Assets/Adapted/ChamberParity'/spec['folder']
        raw=(source/'manifest.json').read_bytes();doc=json.loads(raw)
        assert doc['owner']==spec['owner'] and doc['normal_audits_passed']
        assert len(doc['assets'])==spec['meshes'] and len(doc['recommended_placements'])==spec['count']
        assert all(v['passed'] and v['normal_signs_passed'] for v in doc['fbx_roundtrip_checks'])
        original=json.loads((source.parent/spec['original']/'manifest.json').read_bytes())
        expected=[]
        for p in original['recommended_placements']:
            expected.append({**p,'mesh':p['mesh']+'_V2'})
        assert doc['recommended_placements']==expected, 'Correction must preserve every placement'
        pin=OUT/spec['pin']
        if pin.exists():assert pin.read_bytes()==raw
        else:pin.write_bytes(raw)
        group={'manifest':str(pin),'sha256':sha(pin),'meshes':[],'actors':[]}
        # Retain actual component material overrides, mapped by their slot names.
        bindings={};models={}
        for p in doc['recommended_placements']:
            actor=bylabel['TE_Chamber_'+spec['prefix']+p['label']]
            assert spec['tag'] in [str(t) for t in actor.tags]
            c=actor.static_mesh_component
            original_name=p['mesh'].removesuffix('_V2')
            assert c.static_mesh.get_name() in [original_name,p['mesh']]
            mats={str(s.get_editor_property('material_slot_name')):c.get_material(i) for i,s in enumerate(c.static_mesh.get_editor_property('static_materials'))}
            assert all(mats.values())
            if p['mesh'] in bindings:assert bindings[p['mesh']]==mats
            bindings[p['mesh']]=mats
        for entry in doc['assets']:
            file=source/entry['file'];assert file.parent==source and sha(file)==entry['sha256']
            model=existing(DEST+'/Floor/'+entry['name'])
            if not model:
                options=u.FbxImportUI()
                for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH,'import_as_skeletal':False,'import_materials':False,'import_textures':False}.items():options.set_editor_property(k,v)
                for k,v in {'combine_meshes':True,'auto_generate_collision':False,'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':False}.items():options.static_mesh_import_data.set_editor_property(k,v)
                task=u.AssetImportTask();task.filename=str(file);task.destination_path=DEST+'/Floor';task.destination_name=entry['name'];task.automated=True;task.save=True;task.options=options
                u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths
                model=own(A.load_asset(task.imported_object_paths[0]));assert isinstance(model,u.StaticMesh)
            mats=bindings[entry['name']]
            for i,s in enumerate(model.get_editor_property('static_materials')):model.set_material(i,mats[str(s.get_editor_property('material_slot_name'))])
            ext=model.get_bounds().box_extent;dimensions=[ext.x*2,ext.y*2,ext.z*2]
            assert max(abs(a-b) for a,b in zip(dimensions,entry['expected_dimensions_cm']))<.1
            save(model);models[entry['name']]=model
            group['meshes'].append({'path':model.get_path_name(),'dimensions_cm':dimensions})
        for p in doc['recommended_placements']:
            actor=bylabel['TE_Chamber_'+spec['prefix']+p['label']];c=actor.static_mesh_component
            loc=actor.get_actor_location();scale=actor.get_actor_scale3d();rot=actor.get_actor_rotation()
            assert max(abs(a-b) for a,b in zip([loc.x,loc.y,loc.z],p['location_cm']))<.05
            assert max(abs(a-b) for a,b in zip([scale.x,scale.y,scale.z],p['scale']))<.001
            assert abs((rot.yaw-p['yaw']+180)%360-180)<.01 and abs(rot.pitch)<.01 and abs(rot.roll)<.01
            c.set_static_mesh(models[p['mesh']]);collision_off(c)
            mats=bindings[p['mesh']];readback=[]
            for i,s in enumerate(c.static_mesh.get_editor_property('static_materials')):
                key=str(s.get_editor_property('material_slot_name'));c.set_material(i,mats[key]);assert c.get_material(i)==mats[key]
                readback.append({'slot':key,'material':c.get_material(i).get_path_name()})
            assert not actor.get_actor_enable_collision()
            group['actors'].append({'label':actor.get_actor_label(),'mesh':c.static_mesh.get_path_name(),'material_readback':readback})
        R['groups'].append(group)
    finish()
    after={a.get_actor_label():a for a in ACTORS.get_all_level_actors()}
    for group in R['groups']:
        for row in group['actors']:
            a=after[row['label']];c=a.static_mesh_component
            assert c.static_mesh.get_path_name()==row['mesh']
            assert c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION and not a.get_actor_enable_collision()
    R['passed']=True

if __name__=='__main__':
    try:main()
    except Exception:R['error']=traceback.format_exc();raise
    finally:(OUT/'chamber-surface-normals-import.json').write_text(json.dumps(R,indent=2))
