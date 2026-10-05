"""Import reviewed chamber landmarks and a saved camera-aware fourth wall."""
import sys,json,hashlib,traceback,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from chamber_common import *
from datetime import datetime,timezone
SOURCE=ROOT/'Assets/Adapted/ChamberParity'
R={'passed':False,'source_manifest':str(SOURCE/'manifest.json'),'meshes':[],'static_actors':[],'concealed':[],'cutaway_components':[]}
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def collision_off(c):
    c.set_collision_profile_name('NoCollision');c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
def apply_slots(c,mats):
    for i,slot in enumerate(c.static_mesh.get_editor_property('static_materials')):
        key=str(slot.get_editor_property('material_slot_name'));assert key in mats,key;c.set_material(i,mats[key])
def meshes(doc,mats):
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    out={}
    for entry in doc['assets']:
        path=SOURCE/entry['file'];assert path.parent==SOURCE and sha(path)==entry['sha256']
        obj=existing(DEST+'/Meshes/'+entry['name'])
        if not obj:
            options=u.FbxImportUI()
            for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH,'import_as_skeletal':False,'import_materials':False,'import_textures':False}.items():options.set_editor_property(k,v)
            for k,v in {'combine_meshes':True,'auto_generate_collision':False,'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':False}.items():options.static_mesh_import_data.set_editor_property(k,v)
            task=u.AssetImportTask();task.filename=str(path);task.destination_path=DEST+'/Meshes';task.destination_name=entry['name'];task.automated=True;task.save=True;task.options=options
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths
            obj=own(next(A.load_asset(p) for p in task.imported_object_paths if isinstance(A.load_asset(p),u.StaticMesh)))
        slots=obj.get_editor_property('static_materials')
        for i,slot in enumerate(slots):
            key=str(slot.get_editor_property('material_slot_name'));assert key in mats;obj.set_material(i,mats[key])
        bounds=obj.get_bounds();extent=bounds.box_extent;actual=[extent.x*2,extent.y*2,extent.z*2]
        assert max(abs(a-b) for a,b in zip(actual,entry['expected_dimensions_cm']))<.15,(entry['name'],actual)
        save(obj);out[entry['name']]=obj;R['meshes'].append({'path':obj.get_path_name(),'dimensions_cm':actual,'source_sha256':entry['sha256']})
    return out
def hide(a):
    assert 'TeddyEncounterOwned' in [str(t) for t in a.tags],a.get_actor_label()
    a.set_actor_hidden_in_game(True)
    for c in a.get_components_by_class(u.PrimitiveComponent):c.set_editor_property('visible',False);c.set_editor_property('cast_shadow',False)
    R['concealed'].append(a.get_actor_label())
def setup_cutaway(doc,models,mats):
    path=DEST+'/Blueprints/BP_ChamberCutaway';bp=existing(path)
    if not bp:bp=own(L.create_blueprint_asset_with_parent(path,u.Actor.static_class()))
    scene=component(bp,'ChamberRoot',u.SceneComponent)
    specs=[]
    # Backing lies at X-1610 or behind, so the recessed service leaves remain visible.
    wall=existing(NS+'/Parity/RoomExtension/Meshes/SM_ShellWallBay');assert wall
    for i,y in enumerate([-1400,-1000,-600,-200,200,600,1000,1400]):
        specs.append({'name':'FrontPanel_'+str(i),'model':wall,'loc':(-1670,y,-5),'yaw':-90,'scale':(1,1,630/760)})
    narrow=existing(NS+'/Parity/RoomExtension/Meshes/SM_ShellWallBayNarrow');assert narrow
    for sign in [-1,1]:specs.append({'name':'FrontEnd_'+str(sign).replace('-','M'),'model':narrow,'loc':(-1670,sign*1680,-5),'yaw':-90,'scale':(.8,1,630/760)})
    for item in doc['recommended_placements']:
        if item['label'].startswith('ReverseDoor'):
            specs.append({'name':item['label'],'model':models[item['mesh']],'loc':item['location_cm'],'yaw':item['yaw'],'scale':item['scale']})
    cube=u.load_asset('/Engine/BasicShapes/Cube');assert cube
    for i,y in enumerate([-1660,-1130,0,1130,1660]):
        specs.append({'name':'FrontPier_'+str(i),'model':cube,'loc':(-1578,y,310),'yaw':0,'scale':(.78,.78,6.3),'material':'Concrete'})
    specs.append({'name':'FrontHeader','model':cube,'loc':(-1610,0,624),'yaw':0,'scale':(1.3,34.8,.30),'material':'Metal'})
    specs.append({'name':'FrontFooting','model':cube,'loc':(-1640,0,12),'yaw':0,'scale':(.60,34.8,.34),'material':'Concrete'})
    for s in specs:
        c=component(bp,s['name'],u.StaticMeshComponent,parent='ChamberRoot');c.set_static_mesh(s['model'])
        c.set_editor_property('relative_location',u.Vector(*s['loc']));c.set_editor_property('relative_rotation',u.Rotator(yaw=s['yaw']));c.set_editor_property('relative_scale3d',u.Vector(*s['scale']))
        collision_off(c)
        if 'material' in s:c.set_material(0,mats[s['material']])
        else:apply_slots(c,mats)
        R['cutaway_components'].append({'name':s['name'],'mesh':s['model'].get_path_name(),'location':list(s['loc']),'scale':list(s['scale']),'yaw':s['yaw']})
    # Pure environment behavior: leave existing player, camera and game graphs unchanged.
    g=Graph(bp);g.g.remove_nodes(g.g.list_all_nodes());g.var('CutawayActive','bool','false')
    tick=g.event('ReceiveTick');camera=g.call('GameplayStatics.GetPlayerCameraManager',PlayerIndex=0)
    pos=g.call('PlayerCameraManager.GetCameraLocation',self=(camera,'ReturnValue'))
    xyz=g.math('BreakVector',InVec=(pos,'ReturnValue'))
    outside=g.math('Less_DoubleDouble',A=(xyz,'X'),B=P['cutaway_hide_below_camera_x'])
    record=g.set('CutawayActive',(outside,'ReturnValue'))
    hidden=g.call('Actor.SetActorHiddenInGame',bNewHidden=(outside,'ReturnValue'));g.chain(tick,record,hidden)
    compile(bp)
    found=[a for a in ACTORS.get_all_level_actors() if a.get_actor_label()=='TE_Chamber_FrontCutaway']
    assert len(found)<=1
    if found:
        actor=found[0];assert 'ChamberCutawayOwned' in [str(t) for t in actor.tags]
    else:actor=spawn(L.generated_class(bp),'FrontCutaway',(0,0,0))
    actor.set_editor_property('tags',['TeddyEncounterOwned','ChamberOwned','ChamberCutawayOwned']);actor.set_actor_enable_collision(False)
    R['cutaway_blueprint']=bp.get_path_name();R['cutaway_actor']=actor.get_path_name();R['cutaway_hide_below_camera_x']=P['cutaway_hide_below_camera_x']
def main():
    begin();doc=json.loads((SOURCE/'manifest.json').read_text());assert doc['owner']=='teddy-chamber-parity-20261005'
    # Freeze exact source metadata for this integration without altering source ownership.
    pin=OUT/'chamber-kit-reviewed.json'
    if pin.exists():assert pin.read_bytes()==(SOURCE/'manifest.json').read_bytes(),'Source manifest changed after review'
    else:pin.write_bytes((SOURCE/'manifest.json').read_bytes())
    R['source_manifest_sha256']=sha(pin)
    mats={k:existing(DEST+'/Materials/M_Chamber_'+k) for k in doc['material_slots']};assert all(mats.values())
    models=meshes(doc,mats);bylabel={a.get_actor_label():a for a in ACTORS.get_all_level_actors()}
    conceal=['TE_Room_BulkheadDoor','TE_Parity_RoomExt_RearInset_1','TE_Parity_RoomExt_RearInset_2']
    conceal += ['TE_Parity_RoomExt_Cutaway_'+str(i) for i in range(4)]
    conceal += ['TE_Parity_RoomExt_CutawayReturn_'+str(i) for i in [-1,1]]
    for label in conceal:assert label in bylabel,label;hide(bylabel[label])
    for item in doc['recommended_placements']:
        if item['label'].startswith('ReverseDoor'):continue
        label='TE_Chamber_'+item['label'];a=bylabel.get(label)
        if a:assert 'ChamberOwned' in [str(t) for t in a.tags]
        else:a=spawn(u.StaticMeshActor,item['label'],item['location_cm'],u.Rotator(yaw=item['yaw']))
        a.set_actor_location(u.Vector(*item['location_cm']),False,False);a.set_actor_rotation(u.Rotator(yaw=item['yaw']),False);a.set_actor_scale3d(u.Vector(*item['scale']))
        c=a.static_mesh_component;c.set_static_mesh(models[item['mesh']]);collision_off(c);a.set_actor_enable_collision(False);apply_slots(c,mats)
        R['static_actors'].append({'label':label,'mesh':c.static_mesh.get_path_name(),'location':item['location_cm']})
    setup_cutaway(doc,models,mats);finish()
    got=[a for a in ACTORS.get_all_level_actors() if 'ChamberCutawayOwned' in [str(t) for t in a.tags]];assert len(got)==1
    R['saved_cutaway_mesh_component_count']=len(got[0].get_components_by_class(u.StaticMeshComponent));assert R['saved_cutaway_mesh_component_count']==len(R['cutaway_components'])
    R['passed']=True
if __name__=='__main__':
    try:main()
    except Exception:R['error']=traceback.format_exc();raise
    finally:(OUT/('kit-import-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json')).write_text(json.dumps(R,indent=2))
