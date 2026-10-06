"""Reviewed, bounded room extension; PREPARED SOURCE, NOT EXECUTED IN UNREAL.

The 303-record preproduction plan is a catalogue, not a safe scene replacement.
This imports 46 fitted shell and 38 wall-dressing instances only. Existing 41
kit instances, platforms/gutters/cornices, floor, lights, characters and clips
remain. All new actors are non-colliding. 27 superseded boxes are concealed;
their collision and transforms stay intact. Original meshes are never replaced.

Corrections: preserve existing wall heights/coverage; fit four cutaway spans;
use floor-origin recesses and saddles correctly; attach power drops to trays;
mount details on walls/panels. Exclude speculative foundations, duplicate kit,
old floor placements, taller walls, third beacon, and AnimPreprod assignments.

Optional read-only review: python tools/import_parity_room_shell.py --describe
Engine execution belongs to the sole integration owner after source review.
"""
import collections
import copy
import hashlib
import itertools
import json
import math
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = '/Game/Maps/TeddyEncounter'
DEST = '/Game/TeddyEncounter/Parity/RoomExtension'
PREFIX = 'TE_Parity_RoomExt_'
EXT_OWNER = 'parity-room-extension-v1-20261005'
EXT_TAG = 'TeddyEncounter.RoomExtension.Owner'
HASH_TAG = 'TeddyEncounter.RoomExtension.SourceSHA256'
ACTOR_TAG = 'ParityRoomExtensionV1'
SLOTS = ['Metal', 'Concrete', 'Rust', 'Dark', 'Emissive']
REVIEWED = 'evidence/parity/20261005T070301Z/room-extension-inputs/'
PINNED = {
    REVIEWED+'layout-reviewed.json': '3f4870a8bf1e837b87a45ecefb8f071b6e6434298aee5993c2d0bb530df1d57a',
    REVIEWED+'room-shell-manifest-reviewed.json': 'abe8843a265ace7ad7956ad542c4eb0ee395d51aeb2fc9f55d605479c5bd5e76',
    REVIEWED+'room-dressing-manifest-reviewed.json': '02870ec9170954dbe5d4195dd3d89e5bc110feaf08654416f3df1c6fca8fe16c',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def world_bounds(row, entry):
    """Static-FBX convention verified by the existing room import: flip Y."""
    angle = math.radians(row['yaw']); c, s = math.cos(angle), math.sin(angle)
    points = []
    for source in itertools.product(*zip(entry['bounds_m']['min'], entry['bounds_m']['max'])):
        x, y, z = [v * 100 * scale for v, scale in zip(source, row['scale'])]
        y = -y
        points.append([row['location_cm'][0] + c*x - s*y,
                       row['location_cm'][1] + s*x + c*y,
                       row['location_cm'][2] + z])
    return [[min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)]]


def source_plan():
    for relative, expected in PINNED.items():
        assert sha(ROOT/relative) == expected, 'Source changed; review again: ' + relative
    layout = json.loads((ROOT/REVIEWED/'layout-reviewed.json').read_text(encoding='utf-8'))
    assert layout['owner'] == 'teddy-preprod-layout-20261005'
    assert (layout['units'], layout['up'], layout['far']) == ('cm', '+Z', '+X')
    assert layout['counts'] == {'total':303, 'shell':107, 'kit':41, 'dressing':110, 'floor':45, 'lights':5}
    assert collections.Counter(p['kind'] for p in layout['placements']) == {'shell':107,'kit':41,'dressing':110,'floor':45}
    catalog = {}
    for folder, reviewed_file, owner, count in [('RoomShell', 'room-shell-manifest-reviewed.json', 'teddy-room-shell-20261005',17),
                                                ('RoomDressing', 'room-dressing-manifest-reviewed.json', 'teddy-room-dressing-20261005',36)]:
        directory = ROOT/'Assets/Adapted'/folder
        doc = json.loads((ROOT/REVIEWED/reviewed_file).read_text(encoding='utf-8'))
        assert doc['owner'] == owner and len(doc['assets']) == count
        assert doc['material_slots'] == SLOTS
        assert doc['fbx_settings']['axis_forward'] == '-Y' and doc['fbx_settings']['axis_up'] == 'Z'
        for entry in doc['assets']:
            assert entry['name'] not in catalog
            assert entry['file'] == entry['name']+'.fbx' and entry['material_slots'] == SLOTS
            catalog[entry['name']] = dict(entry, source_directory=str(directory))

    plan = []
    def add(key, mesh, loc, yaw=0, scale=(1,1,1), kind='shell', reason=''):
        plan.append({'key':key, 'mesh':mesh, 'location_cm':list(loc), 'yaw':yaw,
                     'scale':list(scale), 'kind':kind, 'collision':False, 'reason':reason})
    # Fit the old far-wall box exactly: X1720, Y[-1740,1740], Z[-5,685].
    for i,y in enumerate([-1400,-1000,-600,-200,200,600,1000,1400]):
        add('FarBay_'+str(i),'SM_ShellWallBay',(1720,y,-5),90,(1,1,690/760))
    for sign in (-1,1):
        add('FarEnd_'+str(sign),'SM_ShellWallBayNarrow',(1720,sign*1670,-5),90,(.7,1,690/760))
        # Old side-wall span X[-1540,1720], Z[-5,625]; retain the cornice.
        for i,x in enumerate([-1400,-1000,-600,-200,200,600,1000,1400]):
            add('SideBay_'+str(sign)+'_'+str(i),'SM_ShellWallBay',
                (-1370 if i==0 else x,sign*1740,-5),0 if sign<0 else 180,
                (.85 if i==0 else 1,1,630/760))
        add('SideEnd_'+str(sign),'SM_ShellWallBayNarrow',(1660,sign*1740,-5),
            0 if sign<0 else 180,(.6,1,630/760))
    for i,y in enumerate([-1270,-480,400,1220]):
        add('Cutaway_'+str(i),'SM_ShellCutawaySill',(-1530,y,-5),90,(650/340,170/122,1),
            reason='Fit existing 650cm sill span and 170cm depth; keep low broken top.')
    for sign in (-1,1):
        add('CutawayReturn_'+str(sign),'SM_ShellCutawayReturn',(-1540,sign*1680,-5),0 if sign<0 else 180)
    # Mesh origin is opening floor, not its centre. Preserve four original bays.
    inset=catalog['SM_ShellRearInset']; zmin,zmax=inset['bounds_m']['min'][2],inset['bounds_m']['max'][2]
    zscale=374/(100*(zmax-zmin)); zbase=165-100*zmin*zscale
    for i,y in enumerate([-1120,-540,870,1360]):
        add('RearInset_'+str(i),'SM_ShellRearInset',(1651,y,zbase),90,(456/428,1,zscale),
            reason='Recess/header union Z165..539; plan Z340 would raise its top to707.')
    for i,x in enumerate([-1000,-500,0,500,1000]):
        add('PipeSaddle_'+str(i),'SM_ShellPipeStandoff',(x,-1620,425),
            reason='Saddle is local Z36cm; seat at existing rack Z461.')
    for i,x in enumerate([-600,100,800]):
        add('CableTray_'+str(i),'SM_ShellCableTray',(x,1660,520),180)

    allowed = {'SM_DressPanel','SM_DressPanelNarrow','SM_DressRepairPlate','SM_DressWallSpall',
               'SM_DressJunctionBox','SM_DressCableLoop','SM_DressCableDrop','SM_DressBreaker',
               'SM_DressGangBox','SM_DressLouver','SM_DressHatch','SM_DressMeter','SM_DressDownspout'}
    dressing=[]; panels=[]; panel_number=0; drop_number=0; box_number=0
    for index,item in enumerate(layout['placements']):
        if item['kind']!='dressing' or item['mesh'] not in allowed:
            continue
        # Rear patches would be concealed behind the retained/new recess panels.
        if item['mesh']=='SM_DressRepairPlate' and item['location_cm'][0]>1500:
            continue
        row=copy.deepcopy(item);row['key']='Dress_'+str(index).zfill(3)
        row['reason']='Selected wall-mounted detail; recomputed mounting depth.'
        if row['mesh']=='SM_DressPanel':
            if panel_number%2:row['mesh']='SM_DressPanelAlt'
            panel_number+=1
        if row['mesh']=='SM_DressCableDrop':
            row['location_cm'][0]=[-650,100,850][drop_number];drop_number+=1
            row['location_cm'][2]=522-catalog[row['mesh']]['bounds_m']['max'][2]*100
            row['reason']='Top clip meets tray underside at Z522.'
        if row['mesh']=='SM_DressJunctionBox':
            row['location_cm'][0]=[-650,100,850][box_number];box_number+=1
            row['location_cm'][2]=355
            row['reason']='Under corresponding tray/drop, with cable entering upper box.'
        entry=catalog[row['mesh']]; sign=-1 if row['location_cm'][1]<0 else 1
        # Main wall face is at |Y|1692; bury the back by 1cm, retaining detail.
        row['location_cm'][1]=sign*(1693-entry['bounds_m']['max'][1]*100)
        dressing.append(row)
        if row['mesh'] in ['SM_DressPanel','SM_DressPanelAlt','SM_DressPanelNarrow']:
            panels.append(row)
    for row in dressing:
        if row in panels:continue
        lo,hi=world_bounds(row,catalog[row['mesh']]); sign=-1 if row['location_cm'][1]<0 else 1
        for panel in panels:
            if panel['location_cm'][1]*sign<0:continue
            pmin,pmax=world_bounds(panel,catalog[panel['mesh']])
            if lo[0]<pmax[0] and hi[0]>pmin[0] and lo[2]<pmax[2] and hi[2]>pmin[2]:
                face=pmax[1] if sign<0 else pmin[1]
                row['location_cm'][1]=face+sign*(1-catalog[row['mesh']]['bounds_m']['max'][1]*100)
                row['reason']+=' Mounted on panel face where footprints overlap.'
                break
    plan.extend(dressing)
    assert collections.Counter(r['kind'] for r in plan)=={'shell':46,'dressing':38}
    assert len({r['key'] for r in plan})==len(plan)
    used={r['mesh'] for r in plan}
    for name in used:
        e=catalog[name];p=Path(e['source_directory'])/e['file']
        assert p.resolve().parent==Path(e['source_directory']).resolve()
        assert sha(p)==e['sha256'], 'Changed FBX: '+name
    for row in plan:
        assert all(math.isfinite(v) for v in [*row['location_cm'],*row['scale'],row['yaw']])
        assert all(.1<=s<=2.1 for s in row['scale']) and row['collision'] is False
        lo,hi=world_bounds(row,catalog[row['mesh']]);row['expected_world_bounds_cm']=[lo,hi]
        assert not (lo[0]<1480-.05 and hi[0]>-1400+.05 and lo[1]<1500-.05 and hi[1]>-1500+.05), row
        assert lo[2]>=-5.1 and hi[2]<=700, row
    hidden=['FarWall','SideWall_-1','SideWall_1','FarLowerDamp','SideLowerDamp_-1','SideLowerDamp_1']
    hidden += [prefix+str(i) for prefix,count in [('CutawaySill_',4),('CutawayCap_',4),('RearInset_',4),('RearHeader_',4),('PipeStandoff_',5)] for i in range(count)]
    assert len(hidden)==27
    return catalog,plan,['TE_Room_'+s for s in hidden]


def main():
    catalog,plan,conceal=source_plan()  # Complete source preflight before engine mutation.
    if '--describe' in sys.argv:
        print(json.dumps({'scope':'source review only','meshes':len({p['mesh'] for p in plan}),
                          'counts':dict(collections.Counter(p['kind'] for p in plan)),
                          'placements':plan,'conceal_preserve_collision':conceal},indent=2))
        return
    import unreal as u
    sys.path.insert(0,str(ROOT/'tools'))
    from encounter_authoring import A, TAG, OWNER, existing, own, save
    run=json.loads((ROOT/'evidence/parity/current-run.json').read_text())
    out=(ROOT/run['out']).resolve();assert out.is_relative_to((ROOT/'evidence').resolve()) and out.is_dir()
    report={'passed':False,'source_pins':PINNED,'plan':plan,'concealed':[],'new_meshes':[],
            'scope':'shell and wall dressing only; no new collision, materials, lights, kit, floor or animation'}
    receipt=out/('room-extension-import-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    lev=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    try:
        # Filesystem metadata only: this encounter has no external actor storage.
        # If that changes, review a targeted external-package save before mutation.
        for folder in ['__ExternalActors__','__ExternalObjects__']:
            assert not (ROOT/'TeddyBlueprint/Content'/folder/'Maps/TeddyEncounter').exists(), 'Map external storage changed; scoped save review required'
        report['external_actor_storage_detected']=False
        assert lev.load_level(MAP)
        current=list(actors.get_all_level_actors());bylabel={a.get_actor_label():a for a in current}
        # Historical RedPractical actors intentionally share an editor label.
        # Only labels used for this bounded replacement must be unambiguous;
        # preserve every other actor by its unique object path below.
        owned_labels=[a.get_actor_label() for a in current if a.get_actor_label().startswith(('TE_Room_',PREFIX))]
        assert len(owned_labels)==len(set(owned_labels)), ('Duplicate room labels',[(label,count) for label,count in collections.Counter(owned_labels).items() if count>1])
        expected={PREFIX+p['key'] for p in plan}
        for a in current:
            label=a.get_actor_label()
            if label.startswith(PREFIX):
                assert label in expected and ACTOR_TAG in [str(t) for t in a.tags], 'Unowned/unplanned extension actor: '+label
        assert all(label in bylabel for label in conceal), 'Missing expected original room box'
        for label in conceal:
            a=bylabel[label];assert isinstance(a,u.StaticMeshActor)
            assert 'FullRoomOwned' in [str(t) for t in a.tags]
            assert a.static_mesh_component.static_mesh.get_path_name().startswith('/Engine/BasicShapes/Cube.'),label
        # Fail if the scene no longer matches the preserved wall anchors we fit.
        anchors={'TE_Room_FarWall':((1720,0,340),(1.2,34.8,6.9)),
                 'TE_Room_SideWall_-1':((90,-1740,310),(32.6,1.2,6.3)),
                 'TE_Room_SideWall_1':((90,1740,310),(32.6,1.2,6.3))}
        for i,y in enumerate([-1270,-480,400,1220]):
            anchors['TE_Room_CutawaySill_'+str(i)]=((-1530,y,25),(1.7,6.5,.6))
        for label,(position,scale) in anchors.items():
            a=bylabel[label];v=a.get_actor_location();s=a.get_actor_scale3d();r=a.get_actor_rotation()
            assert max(abs(x-y) for x,y in zip([v.x,v.y,v.z],position))<.05,label
            assert max(abs(x-y) for x,y in zip([s.x,s.y,s.z],scale))<.001,label
            assert max(abs(r.pitch),abs(r.yaw),abs(r.roll))<.01,label
        # Retained kit is already in this room. Never replay its preprod records.
        kit=[a for a in current if isinstance(a,u.StaticMeshActor) and a.static_mesh_component.static_mesh
             and a.static_mesh_component.static_mesh.get_path_name().startswith('/Game/TeddyEncounter/Room/Meshes/')]
        assert len(kit)==41, ('Review changed kit census',len(kit))
        def state(a):
            v=a.get_actor_location();s=a.get_actor_scale3d();r=a.get_actor_rotation()
            return {'location':[v.x,v.y,v.z],'scale':[s.x,s.y,s.z],'rotation':[r.pitch,r.yaw,r.roll],
                    'collision':a.get_actor_enable_collision(),
                    'components':{c.get_name():[str(c.get_collision_enabled()),str(c.get_collision_profile_name())]
                                  for c in a.get_components_by_class(u.PrimitiveComponent)}}
        protected={a.get_path_name():state(a) for a in current if a.get_actor_label().startswith('TE_') and not a.get_actor_label().startswith(PREFIX)}
        report['protected_collision_and_transform_before']=protected
        materials={k:existing('/Game/TeddyEncounter/Room/Materials/M_Room_'+v) for k,v in
                   {'Metal':'PaintedSteel','Concrete':'Concrete','Rust':'Oxide','Dark':'Recess','Emissive':'CoolFixture'}.items()}
        assert all(materials.values()), 'Existing room material dependency missing'
        models={}
        # Fail on any pre-existing foreign asset before importing the first file.
        for name in sorted({p['mesh'] for p in plan}):
            path=DEST+'/Meshes/'+name
            if A.does_asset_exist(path):
                obj=A.load_asset(path)
                assert A.get_metadata_tag(obj,TAG)==OWNER and A.get_metadata_tag(obj,EXT_TAG)==EXT_OWNER,path
                assert A.get_metadata_tag(obj,HASH_TAG)==catalog[name]['sha256'],path
        u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
        for name in sorted({p['mesh'] for p in plan}):
            e=catalog[name];path=DEST+'/Meshes/'+name;model=A.load_asset(path) if A.does_asset_exist(path) else None
            if not model:
                options=u.FbxImportUI()
                for k,v in {'import_mesh':True,'import_as_skeletal':False,'import_materials':False,'import_textures':False,
                            'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH}.items():options.set_editor_property(k,v)
                for k,v in {'combine_meshes':True,'auto_generate_collision':False,'convert_scene':True,
                            'convert_scene_unit':True,'force_front_x_axis':False}.items():options.static_mesh_import_data.set_editor_property(k,v)
                task=u.AssetImportTask();task.filename=str(Path(e['source_directory'])/e['file']);task.destination_path=DEST+'/Meshes'
                task.destination_name=name;task.automated=True;task.save=False;task.replace_existing=False;task.options=options
                u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
                assert len(task.imported_object_paths)==1,list(task.imported_object_paths)
                model=own(A.load_asset(task.imported_object_paths[0]));assert isinstance(model,u.StaticMesh)
                assert model.get_path_name().split('.')[0]==path
                A.set_metadata_tag(model,EXT_TAG,EXT_OWNER);A.set_metadata_tag(model,HASH_TAG,e['sha256'])
                report['new_meshes'].append(path)
            assert isinstance(model,u.StaticMesh)
            names=[str(s.get_editor_property('material_slot_name')) for s in model.get_editor_property('static_materials')]
            # FBX omits unused source slots; require every surviving slot to
            # have an explicit owned material mapping, never assume its index.
            assert names and len(names)==len(set(names)) and set(names).issubset(SLOTS),(name,names)
            for i,slot in enumerate(names):model.set_material(i,materials[slot])
            b=model.get_bounds();actual=[b.box_extent.x*2,b.box_extent.y*2,b.box_extent.z*2]
            assert all(abs(a-b)<max(.06,b*.01) for a,b in zip(actual,e['expected_dimensions_cm'])),(name,actual)
            origin=[b.origin.x,b.origin.y,b.origin.z]
            midpoint=[(a+b)*50 for a,b in zip(e['bounds_m']['min'],e['bounds_m']['max'])];midpoint[1]*=-1
            assert max(abs(a-b) for a,b in zip(origin,midpoint))<.1,(name,'Unexpected static-FBX axes',origin,midpoint)
            save(model);models[name]=model
        for p in plan:
            label=PREFIX+p['key'];a=bylabel.get(label)
            if a is None:
                a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*p['location_cm']),u.Rotator(yaw=p['yaw']),transient=False)
                assert a;a.set_actor_label(label)
                a.set_editor_property('tags',['TeddyEncounterOwned','ParityOwned',ACTOR_TAG])
            assert isinstance(a,u.StaticMeshActor)
            a.set_actor_location(u.Vector(*p['location_cm']),False,False);a.set_actor_rotation(u.Rotator(yaw=p['yaw']),False)
            a.set_actor_scale3d(u.Vector(*p['scale']));a.set_folder_path('TeddyEncounter/Parity/RoomExtension/'+p['kind'])
            c=a.static_mesh_component;c.set_static_mesh(models[p['mesh']]);c.set_collision_profile_name('NoCollision')
            c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);a.set_actor_enable_collision(False)
            c.set_visibility(True);a.set_actor_hidden_in_game(False)
        # Conceal originals only after every replacement imported and was placed.
        for label in conceal:
            a=bylabel[label];c=a.static_mesh_component
            report['concealed'].append({'label':label,'visible_before':bool(c.get_editor_property('visible')),
                                       'cast_shadow_before':bool(c.get_editor_property('cast_shadow'))})
            a.set_actor_hidden_in_game(True);c.set_visibility(False);c.set_editor_property('cast_shadow',False)
            assert state(a)==protected[a.get_path_name()], 'Collision/transform changed while concealing '+label
        # Imported owned meshes were explicitly saved above; save this map only.
        assert lev.save_current_level()
        assert lev.load_level(MAP)
        saved={a.get_actor_label():a for a in actors.get_all_level_actors()}
        assert sum(label.startswith(PREFIX) for label in saved)==len(plan)
        saved_paths={a.get_path_name():a for a in actors.get_all_level_actors()}
        for object_path,before in protected.items():assert object_path in saved_paths and state(saved_paths[object_path])==before,object_path
        for p in plan:
            a=saved[PREFIX+p['key']];c=a.static_mesh_component
            assert ACTOR_TAG in [str(t) for t in a.tags] and c.static_mesh==models[p['mesh']]
            assert c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION and not a.get_actor_enable_collision()
            assert str(c.get_collision_profile_name())=='NoCollision'
            v=a.get_actor_location();s=a.get_actor_scale3d();r=a.get_actor_rotation()
            assert max(abs(x-y) for x,y in zip([v.x,v.y,v.z],p['location_cm']))<.05
            assert max(abs(x-y) for x,y in zip([s.x,s.y,s.z],p['scale']))<.0001
            assert abs((r.yaw-p['yaw']+180)%360-180)<.01 and abs(r.pitch)<.01 and abs(r.roll)<.01
        for label in conceal:assert not saved[label].static_mesh_component.get_editor_property('visible')
        report.update(passed=True,saved_reload=True,new_actor_count=len(plan),retained_kit_count=len(kit),
                      protected_collision_and_transforms_unchanged=True,visual_acceptance=False)
    except Exception:
        report['error']=traceback.format_exc();raise
    finally:
        receipt.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
