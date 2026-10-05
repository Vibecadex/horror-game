"""Build the authorized industrial chamber without replacing encounter gameplay.

New room assets and tagged actors are owned here. Original collision boundaries,
characters, input, camera, floor and exposure are retained. Run after backup.
"""
import json
import math
import random
import sys
import traceback
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from encounter_authoring import A, L, M, NS, TAG, OWNER, existing, asset, own, save

OUT = Path(json.loads((ROOT/'evidence/full-room/current-run.json').read_text())['out'])
MAP = '/Game/Maps/TeddyEncounter'
ROOM = NS+'/Room'
lev = u.get_editor_subsystem(u.LevelEditorSubsystem)
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
report = {'passed': False, 'map': MAP, 'actors': [], 'meshes': [], 'legacy_dressing_hidden': [],
          'design': 'Industrial containment and pump chamber; near-wall/ceiling cutaway for elevated gameplay.'}

def expr(mat, cls, **props):
    n = M.create_material_expression(mat, cls)
    assert n
    for k,v in props.items(): n.set_editor_property(k,v)
    return n

def link(a,b,pin,output=''):
    names = list(M.get_material_expression_input_names(b))
    if len(names)==1 and names[0] in ('None',''): pin=''
    assert M.connect_material_expressions(a,output,b,pin), (str(b),pin,names)

def scalar(mat,v): return expr(mat,u.MaterialExpressionConstant,r=v)
def rgb(mat,v): return expr(mat,u.MaterialExpressionConstant3Vector,constant=u.LinearColor(*v,1))
def out(n,prop): assert M.connect_material_property(n,'',prop)

def material(name,c1,c2,rough=.85,metal=.0,emission=0,scale=.02):
    mat=asset('Room/Materials/M_Room_'+name,u.Material,u.MaterialFactoryNew())
    M.delete_all_material_expressions(mat)
    if emission:
        c=rgb(mat,c1); out(c,u.MaterialProperty.MP_BASE_COLOR)
        mul=expr(mat,u.MaterialExpressionMultiply,const_b=emission);link(c,mul,'A');out(mul,u.MaterialProperty.MP_EMISSIVE_COLOR)
    else:
        pos=expr(mat,u.MaterialExpressionWorldPosition)
        n=expr(mat,u.MaterialExpressionNoise,scale=scale,quality=1,levels=2,output_min=0.,output_max=1.,turbulence=False)
        link(pos,n,list(M.get_material_expression_input_names(n))[0])
        blend=expr(mat,u.MaterialExpressionLinearInterpolate)
        link(rgb(mat,c1),blend,'A');link(rgb(mat,c2),blend,'B');link(n,blend,'Alpha');out(blend,u.MaterialProperty.MP_BASE_COLOR)
    out(scalar(mat,rough),u.MaterialProperty.MP_ROUGHNESS)
    out(scalar(mat,metal),u.MaterialProperty.MP_METALLIC)
    out(scalar(mat,.24),u.MaterialProperty.MP_SPECULAR)
    M.recompile_material(mat);save(mat);return mat

def stain_material():
    mat=asset('Room/Materials/M_Room_DampStain',u.Material,u.MaterialFactoryNew())
    M.delete_all_material_expressions(mat)
    mat.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED)
    mat.set_editor_property('two_sided',True)
    uv=expr(mat,u.MaterialExpressionTextureCoordinate)
    centre=expr(mat,u.MaterialExpressionConstant2Vector,r=.5,g=.5)
    mask=expr(mat,u.MaterialExpressionSphereMask,attenuation_radius=.46,hardness_percent=18.)
    link(uv,mask,'A');link(centre,mask,'B')
    n=expr(mat,u.MaterialExpressionNoise,scale=4.,quality=1,levels=2,output_min=.55,output_max=1.,turbulence=False)
    uv3=expr(mat,u.MaterialExpressionAppendVector);link(uv,uv3,'A');link(scalar(mat,0.),uv3,'B')
    link(uv3,n,list(M.get_material_expression_input_names(n))[0])
    multiply=expr(mat,u.MaterialExpressionMultiply);link(mask,multiply,'A');link(n,multiply,'B')
    out(multiply,u.MaterialProperty.MP_OPACITY_MASK)
    out(rgb(mat,(.029,.037,.038)),u.MaterialProperty.MP_BASE_COLOR)
    out(scalar(mat,.82),u.MaterialProperty.MP_ROUGHNESS)
    out(scalar(mat,.05),u.MaterialProperty.MP_METALLIC)
    out(scalar(mat,.1),u.MaterialProperty.MP_SPECULAR)
    M.recompile_material(mat);save(mat);return mat

def spawn(cls,label,loc,rot=None,scale=None,tag='RoomDecor'):
    a=actors.spawn_actor_from_class(cls,u.Vector(*loc),rot or u.Rotator(),transient=False)
    assert a
    a.set_actor_label('TE_Room_'+label)
    a.set_editor_property('tags',['TeddyEncounterOwned','FullRoomOwned',tag])
    a.set_folder_path('TeddyEncounter/IndustrialRoom/'+tag)
    if scale:a.set_actor_scale3d(u.Vector(*scale))
    report['actors'].append({'label':a.get_actor_label(),'tag':tag,'location':list(loc)})
    return a

def mesh(label,model,loc,scale=(1,1,1),mat=None,yaw=0,tag='RoomDecor',collision=False):
    a=spawn(u.StaticMeshActor,label,loc,u.Rotator(yaw=yaw),scale,tag)
    c=a.static_mesh_component;c.set_static_mesh(model)
    c.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
    c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS if collision else u.CollisionEnabled.NO_COLLISION)
    a.set_actor_enable_collision(collision)
    if mat:
        for i in range(max(1,c.get_num_materials())):c.set_material(i,mat)
    if tag=='RoomFloorDetail': c.set_editor_property('cast_shadow',False)
    return a

def box(label,loc,size,mat,tag='RoomDecor',collision=False):
    return mesh(label,cube,loc,tuple(x/100 for x in size),mat,tag=tag,collision=collision)

def light(label,loc,color,intensity,radius,source=30):
    a=spawn(u.PointLight,label,loc,tag='RoomLight');c=a.point_light_component
    c.set_editor_property('mobility',u.ComponentMobility.MOVABLE)
    c.set_light_color(u.LinearColor(*color,1))
    for k,v in {'intensity':float(intensity),'attenuation_radius':float(radius),'source_radius':float(source),
                'volumetric_scattering_intensity':.15}.items():c.set_editor_property(k,v)
    c.set_cast_shadows(True)
    return a

def import_kit(materials):
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    models={}
    for path in sorted((ROOT/'Assets/Adapted/Room').glob('SM_*.fbx')):
        name=path.stem
        obj=existing(ROOM+'/Meshes/'+name)
        if not obj:
            opt=u.FbxImportUI()
            for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH,
                        'import_as_skeletal':False,'import_materials':False,'import_textures':False}.items():opt.set_editor_property(k,v)
            data=opt.static_mesh_import_data
            for k,v in {'combine_meshes':True,'auto_generate_collision':False,'convert_scene':True,
                        'convert_scene_unit':True,'force_front_x_axis':False}.items():data.set_editor_property(k,v)
            task=u.AssetImportTask();task.filename=str(path);task.destination_path=ROOM+'/Meshes';task.destination_name=name
            task.automated=True;task.save=True;task.options=opt
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths,name
            imported=[A.load_asset(p) for p in task.imported_object_paths]
            obj=next(x for x in imported if isinstance(x,u.StaticMesh));own(obj)
        slots=obj.get_editor_property('static_materials')
        slot_report=[]
        for slot in slots:
            key=str(slot.get_editor_property('material_slot_name'))
            key=next((n for n in materials if n.lower() in key.lower()),'Metal')
            slot.set_editor_property('material_interface',materials[key]);slot_report.append(key)
        obj.set_editor_property('static_materials',slots);save(obj)
        b=obj.get_bounds();models[name]=obj
        report['meshes'].append({'name':name,'bounds':str(b),'material_slots':slot_report,'path':obj.get_path_name()})
    assert len(models)>=9,list(models)
    for short,full in {'Pilaster':'RoomPilaster','BulkheadDoor':'RoomBulkhead','WallFan':'RoomVentFan',
                       'UtilityTank':'RoomUtilityTank','ServiceCabinet':'RoomServiceCabinet',
                       'PipeRack':'RoomPipeRack','FloorGrate':'RoomFloorGrate',
                       'CableSpool':'RoomCableSpool','CargoCrate':'RoomCargoCrate'}.items():
        models['SM_'+short]=models['SM_'+full]
    return models

try:
    assert (OUT/'baseline.json').is_file(),'Back up current encounter first'
    assert existing(MAP);assert lev.load_level(MAP)
    original=list(actors.get_all_level_actors())
    for a in original:
        if 'FullRoomOwned' in [str(t) for t in a.tags]:assert actors.destroy_actor(a)
    # Retire the sparse old outer dressing visually; retain the four tested blockers.
    old_prefix=('TE_Wall','TE_Buttress','TE_BeaconHousing','TE_RedSlit','TE_RedPractical',
                'TE_Rubble','TE_Drain','TE_EdgePillar','TE_EdgeLamp','TE_EdgeGlow')
    for a in original:
        label=a.get_actor_label()
        if label.startswith(old_prefix):
            assert 'TeddyEncounterOwned' in [str(t) for t in a.tags]
            a.set_actor_hidden_in_game(True);a.set_actor_enable_collision(False)
            for c in a.get_components_by_class(u.PrimitiveComponent):c.set_editor_property('cast_shadow',False)
            for c in a.get_components_by_class(u.LightComponent):c.set_editor_property('intensity',0.)
            report['legacy_dressing_hidden'].append(label)
        elif label.startswith('TE_CombatBound'):
            a.set_actor_hidden_in_game(True)
            a.static_mesh_component.set_editor_property('cast_shadow',False)
    mats={
        'Concrete':material('Concrete',(.038,.042,.043),(.045,.049,.048),.92,scale=.085),
        'Metal':material('PaintedSteel',(.030,.040,.042),(.068,.075,.072),.66,.38,scale=.035),
        'Rust':material('Oxide',(.037,.026,.021),(.074,.049,.035),.91,.12,scale=.045),
        'Dark':material('Recess',(.008,.012,.014),(.018,.021,.022),.87,.16),
        'Emissive':material('CoolFixture',(.05,.17,.19),(.05,.17,.19),.55,emission=1.3),
    }
    red=material('WarningLens',(.40,.012,.006),(.40,.012,.006),.6,emission=1.4)
    trim=material('EdgeSteel',(.075,.083,.080),(.105,.11,.106),.6,.55)
    stains=stain_material()
    models=import_kit(mats)
    cube=u.load_asset('/Engine/BasicShapes/Cube');plane=u.load_asset('/Engine/BasicShapes/Plane')
    concrete,metal,dark=mats['Concrete'],mats['Metal'],mats['Dark']
    # Complete three tall walls, structural returns and low foreground cutaway.
    box('FarWall',(1720,0,340),(120,3480,690),concrete,'RoomShell',True)
    for sign in [-1,1]:
        box('SideWall_'+str(sign),(90,sign*1740,310),(3260,120,630),concrete,'RoomShell',True)
        box('SideLowerDamp_'+str(sign),(90,sign*1674,65),(3260,8,140),dark)
        box('SideCornice_'+str(sign),(90,sign*1645,620),(3260,110,45),metal)
        box('SideFoundation_'+str(sign),(90,sign*1575,28),(3180,210,66),concrete)
        box('SideGutter_'+str(sign),(90,sign*1550,63),(3180,108,4),dark)
    box('FarLowerDamp',(1656,0,65),(8,3350,140),dark)
    box('FarCornice',(1630,0,678),(160,3510,44),metal)
    box('FarFoundation',(1570,0,28),(180,3350,66),concrete)
    for i,(yc,width) in enumerate([(-1270,650),(-480,650),(400,650),(1220,650)]):
        box('CutawaySill_'+str(i),(-1530,yc,25),(170,width,60),concrete,'RoomShell',True)
        box('CutawayCap_'+str(i),(-1530,yc,57),(190,width+10,8),metal)
    # Rear door is a composed landmark; asymmetrical wall recesses and upper paneling.
    # FBX readback confirms Unreal flips source Y: detailed fronts face UE +Y.
    mesh('BulkheadDoor',models['SM_BulkheadDoor'],(1630,180,62),(1,1,1),yaw=90)
    for y in [-1360,-780,780,1380]:
        mesh('RearPilaster_'+str(y),models['SM_Pilaster'],(1635,y,-5),(1,1,1.32),yaw=90)
    for i,y in enumerate([-1120,-540,870,1360]):
        box('RearInset_'+str(i),(1651,y,340),(20,440,350),dark)
        box('RearHeader_'+str(i),(1620,y,529),(62,456,20),metal)
    mesh('RearFan',models['SM_WallFan'],(1612,-1100,365),yaw=90)
    mesh('RearTank',models['SM_UtilityTank'],(1570,1080,62),(.76,.76,1),yaw=90)
    # The two sides share structural vocabulary but have different service functions.
    for sign,xs in [(-1,[-1180,-460,420,1350]),(1,[-1150,-120,680,1360])]:
        for i,x in enumerate(xs):
            mesh('SidePilaster_'+str(sign)+'_'+str(i),models['SM_Pilaster'],(x,sign*1650,-5),(1,1,1.2),yaw=0 if sign<0 else 180)
    for i,x in enumerate([-1000,-500,0,500,1000]):
        mesh('LeftPipeRun_'+str(i),models['SM_PipeRack'],(x,-1550,460),yaw=0)
        box('PipeStandoff_'+str(i),(x,-1620,461),(24,110,84),metal)
    mesh('LeftFan',models['SM_WallFan'],(-20,-1630,275),yaw=0)
    mesh('RightCabinetA',models['SM_ServiceCabinet'],(-770,1580,62),yaw=180)
    mesh('RightCabinetB',models['SM_ServiceCabinet'],(-545,1580,62),(.9,.95,1.1),yaw=180)
    mesh('RightTank',models['SM_UtilityTank'],(970,1555,62),(.8,.8,.95),yaw=180)
    mesh('RightPipeRun',models['SM_PipeRack'],(890,1550,470),yaw=180)
    mesh('RightFan',models['SM_WallFan'],(225,1630,340),yaw=180)
    mesh('LeftCrate',models['SM_CargoCrate'],(-825,-1565,65),(.6,.55,.62),yaw=5)
    mesh('RightSpool',models['SM_CableSpool'],(-50,1580,65),(.55,.55,.6))
    mesh('RearCrate',models['SM_CargoCrate'],(1530,-585,65),(.65,.48,.68),yaw=-90)
    # Discontinuous flush floor grates, rather than stripes crossing the arena.
    for sign in [-1,1]:
        for i,x in enumerate([-1070,-550,-10,550,1090]):
            mesh('DrainGrate_'+str(sign)+'_'+str(i),models['SM_FloorGrate'],(x,sign*1548,65),(1,.85,.7))
    # Small sparse practicals, with local spill and believable fixture housings.
    for i,(x,y) in enumerate([(740,-1530),(-920,1530)]):
        box('BeaconHousing_'+str(i),(x,y,230),(44,36,84),dark)
        box('BeaconLens_'+str(i),(x-24,y,232),(5,17,52),red)
        light('BeaconLight_'+str(i),(x-58,y,235),(1,.034,.014),180,380,12)
    for i,y in enumerate([-620,720]):
        mesh('RearFixture_'+str(i),models['SM_RoomStripLight'],(1630,y,545),(.9,1,1),yaw=90)
        light('RearGrazing_'+str(i),(1430,y,510),(.35,.59,.63),3600,980,95)
    light('LeftServiceLight',(-280,-1440,470),(.27,.49,.53),4100,1020,85)
    light('RightServiceLight',(180,1430,450),(.26,.43,.48),3600,930,85)
    # Dim bounce pools keep extreme-edge bodies legible without lifting exposure.
    for i,(x,y) in enumerate([(-1050,-1050),(-1050,1050),(1080,-1080),(1080,1080)]):
        light('CornerBounce_'+str(i),(x,y,850),(.25,.39,.43),14500,1380,240)
    # Low floor wear: alpha-masked, no physical obstruction or cast shadows.
    for i,(x,y,sx,sy,angle) in enumerate([(1080,-790,3.5,1.8,14),(740,1180,4.0,2.1,-17),(-750,-1120,3.5,1.6,32),
             (-990,1010,2.8,1.7,20),(1110,350,3.1,1.2,80),(-540,1050,2.0,1.1,10),(350,-1100,2.9,1.3,7),(-790,160,2.2,.9,55)]):
        mesh('FloorDamp_'+str(i),plane,(x,y,-4.6),(sx,sy,1),stains,angle,'RoomFloorDetail')
    random.seed(512)
    for i in range(28):
        sign=-1 if i%2 else 1
        x=random.uniform(-1250,1420);y=sign*random.uniform(1500,1570)
        box('FootDebris_'+str(i),(x,y,68),(random.uniform(10,32),random.uniform(10,30),random.uniform(5,15)),concrete)
    # Document unchanged actors, then save all owned room resources and reopen.
    report['preserved_gameplay']=[a.get_actor_label() for a in actors.get_all_level_actors()
                                 if a.get_actor_label() in ['TE_PlayerStart','TE_MainTeddy','TE_CombatView'] or a.get_actor_label().startswith('TE_Stitchling')]
    assert lev.save_current_level();assert u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
    assert lev.load_level(MAP)
    saved=[a for a in actors.get_all_level_actors() if 'FullRoomOwned' in [str(t) for t in a.tags]]
    assert len(saved)==len(report['actors']),(len(saved),len(report['actors']))
    for a in saved:
        if any(t in [str(x) for x in a.tags] for t in ['RoomDecor','RoomFloorDetail']):
            for c in a.get_components_by_class(u.StaticMeshComponent):
                assert c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION,(a.get_actor_label(),str(c.get_collision_enabled()))
                assert str(c.get_collision_profile_name())=='NoCollision',a.get_actor_label()
    report.update(passed=True,saved_room_actor_count=len(saved),saved_reopened=True,
                  decoration_collision_profile_saved=True,
                  gameplay_assets_changed=False,rendered_fidelity_verified=False)
except Exception:
    report['error']=traceback.format_exc()
    raise
finally:
    path=OUT/'authoring.json'
    if path.exists():path=OUT/('authoring-'+str(len(list(OUT.glob('authoring*.json')))+1)+'.json')
    path.write_text(json.dumps(report,indent=2))
