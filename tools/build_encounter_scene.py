"""Owned scene composition; preserves source maps and all third-party originals."""
import sys,json,math,random,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
historical_builder(__file__)
r={'passed':False};lev=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
MAP='/Game/Maps/TeddyEncounter'
def spawn(cls,label,loc=(0,0,0),rot=(0,0,0),scale=None):
    a=actors.spawn_actor_from_class(cls,u.Vector(*loc),u.Rotator(pitch=rot[0],yaw=rot[1],roll=rot[2]),transient=False);assert a
    a.set_actor_label('TE_'+label);a.set_editor_property('tags',['TeddyEncounterOwned'])
    if scale:a.set_actor_scale3d(u.Vector(*scale))
    return a
def mesh(label,model,loc,scale,mat,rot=(0,0,0)):
    a=spawn(u.StaticMeshActor,label,loc,rot,scale);c=a.static_mesh_component;c.set_static_mesh(u.load_asset(model) if isinstance(model,str) else model);c.set_material(0,mat);return a
try:
    if A.does_asset_exist(MAP):
        world=A.load_asset(MAP);assert A.get_metadata_tag(world,TAG)==OWNER
        assert lev.load_level(MAP)
        for a in actors.get_all_level_actors():
            if 'TeddyEncounterOwned' in [str(t) for t in a.tags]:assert actors.destroy_actor(a)
    else:
        assert lev.new_level(MAP);assert lev.load_level(MAP);save(own(A.load_asset(MAP)));assert lev.save_current_level()
    # Import separately owned texture maps and rifle.
    envtex={}
    for name in ['T_Concrete_Color','T_Concrete_Normal','T_Concrete_Roughness','ServiceRifle']:
        path=NS+'/Arena/'+name;o=existing(path)
        if not o:
            t=u.AssetImportTask();t.filename=str(ROOT/'Assets/Adapted/Arena'/(name+('.fbx' if name=='ServiceRifle' else '.png')));t.destination_path=NS+'/Arena';t.destination_name=name;t.automated=True;t.save=True
            if name=='ServiceRifle':
                u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
                opt=u.FbxImportUI();opt.set_editor_property('automated_import_should_detect_type',False);opt.set_editor_property('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH);opt.set_editor_property('import_materials',False);opt.set_editor_property('import_textures',False);t.options=opt
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);assert t.imported_object_paths;o=own(A.load_asset(t.imported_object_paths[0]))
        if isinstance(o,u.Texture):
            if name.endswith('Normal'):o.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP);o.set_editor_property('srgb',False)
            if name.endswith('Roughness'):o.set_editor_property('srgb',False)
        save(o);envtex[name]=o
    floor=asset('Materials/M_WornConcrete',u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(floor)
    uv=M.create_material_expression(floor,u.MaterialExpressionTextureCoordinate);uv.set_editor_property('u_tiling',4.0);uv.set_editor_property('v_tiling',4.0)
    for name,prop,sampler in [('Color',u.MaterialProperty.MP_BASE_COLOR,u.MaterialSamplerType.SAMPLERTYPE_COLOR),('Normal',u.MaterialProperty.MP_NORMAL,u.MaterialSamplerType.SAMPLERTYPE_NORMAL),('Roughness',u.MaterialProperty.MP_ROUGHNESS,u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)]:
        sample=M.create_material_expression(floor,u.MaterialExpressionTextureSample);sample.set_editor_property('texture',envtex['T_Concrete_'+name]);sample.set_editor_property('sampler_type',sampler);M.connect_material_expressions(uv,'',sample,'UVs');M.connect_material_property(sample,'RGB' if name!='Roughness' else 'R',prop)
    M.recompile_material(floor);save(floor)
    wall=constmat('M_OxidisedIron',(.045,.057,.061),.9);dark=constmat('M_Charcoal',(.015,.023,.03),.76);red=constmat('M_WarningLamp',(.8,.015,.008),.5,3);cyan=constmat('M_Muzzle',(.10,.68,.8),.3,5)
    # Duplicate movement/aim core. Only owned copies receive changes.
    pawn=duplicate('/Game/Variant_TwinStick/Blueprints/BP_TwinStickCharacter','Blueprints/BP_EncounterPlayer')
    pc=duplicate('/Game/Variant_TwinStick/Blueprints/BP_TwinStickPlayerController','Blueprints/BP_EncounterController')
    gm=blueprint('BP_EncounterGameMode',u.GameModeBase)
    cd=u.get_default_object(L.generated_class(gm));cd.set_editor_property('default_pawn_class',L.generated_class(pawn));cd.set_editor_property('player_controller_class',L.generated_class(pc));compile(gm)
    pcm=u.get_default_object(L.generated_class(pc));pcm.set_editor_property('show_mouse_cursor',True);pcm.set_editor_property('auto_manage_active_camera_target',False);compile(pc)
    cs=components(pawn)
    for _,c in cs.values():
        if isinstance(c,u.CharacterMovementComponent):c.set_editor_property('max_walk_speed',420.)
        if isinstance(c,u.SpringArmComponent):c.set_editor_property('target_arm_length',2300.);c.set_editor_property('camera_lag_speed',4.)
    rifle=component(pawn,'ServiceRifle',u.StaticMeshComponent,'CharacterMesh0');rifle.set_static_mesh(envtex['ServiceRifle']);rifle.set_material(0,dark);rifle.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    rifle.set_editor_property('relative_location',u.Vector(22,42,126));rifle.set_editor_property('relative_rotation',u.Rotator(yaw=90))
    compile(pawn)
    boss=blueprint('BP_TeddyBoss',u.Character);bcs=components(boss)
    sk=u.load_asset(NS+'/Teddy/Idle/SK_Teddy');idle=u.load_asset(NS+'/Teddy/Idle/A_Teddy_Idle')
    for _,c in bcs.values():
        if isinstance(c,u.CapsuleComponent):c.set_capsule_size(135,230,False)
        if isinstance(c,u.SkeletalMeshComponent):
            c.set_skeletal_mesh_asset(sk);c.set_editor_property('relative_location',u.Vector(0,0,-230));c.set_editor_property('relative_rotation',u.Rotator(0,0,0));c.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
            ad=c.get_editor_property('animation_data');ad.set_editor_property('anim_to_play',idle);ad.set_editor_property('saved_looping',True);ad.set_editor_property('saved_playing',True);c.set_editor_property('animation_data',ad)
        if isinstance(c,u.CharacterMovementComponent):c.set_editor_property('max_walk_speed',140.)
    compile(boss)
    # A separate director owns the elevated gameplay view.
    director=blueprint('BP_CombatCamera');camera=component(director,'CombatCamera',u.CameraComponent)
    camera.set_editor_property('field_of_view',55.);camera.set_editor_property('constrain_aspect_ratio',False)
    g=Graph(director)
    g.g.remove_nodes(g.g.list_all_nodes())
    begin=g.event('ReceiveBeginPlay');delay=g.call('KismetSystemLibrary.Delay',Duration='.2');getpc=g.call('GameplayStatics.GetPlayerController')
    camget=g.get('CombatCamera');selfnode=g.call('ActorComponent.GetOwner',self=(camget,'CombatCamera'))
    target=g.call('PlayerController.SetViewTargetWithBlend',self=(getpc,'ReturnValue'),NewViewTarget=(selfnode,'ReturnValue'),BlendTime='0');g.chain(begin,delay,target)
    compile(director)
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();world.get_world_settings().set_editor_property('default_game_mode',L.generated_class(gm))
    cube='/Engine/BasicShapes/Cube';cyl='/Engine/BasicShapes/Cylinder'
    mesh('ArenaFloor',cube,(0,0,-55),(60,60,1),floor)
    # Dark peripheral architecture: retaining walls, pillars, inset floor ribs and grates.
    for side,loc,scale in [('North',(2450,0,180),(1,50,4)),('South',(-2450,0,180),(1,50,4)),('West',(0,-2450,180),(50,1,4)),('East',(0,2450,180),(50,1,4))]:mesh('Wall'+side,cube,loc,scale,wall)
    for x in [-2200,0,2200]:
        for y in [-2180,2180]:
            mesh('Buttress',cube,(x,y,230),(1.8,2.6,5),wall)
            mesh('BeaconHousing',cube,(x-80,y,170),(.4,.8,.6),dark)
            mesh('RedSlit',cube,(x-105,y,172),(.1,.08,.38),red)
            a=spawn(u.PointLight,'RedPractical',(x-160,y,190));lc=a.point_light_component;lc.set_light_color(u.LinearColor(1,.025,.012,1));lc.set_intensity(3500);lc.set_attenuation_radius(470);lc.set_cast_shadows(True)
    random.seed(74)
    for i in range(40):
        theta=random.uniform(0,math.tau);rad=random.uniform(1950,2280);x,y=math.cos(theta)*rad,math.sin(theta)*rad
        mesh('Rubble',cube,(x,y,random.uniform(3,20)),(random.uniform(.15,.8),random.uniform(.2,.65),random.uniform(.06,.3)),wall,(0,random.uniform(0,180),random.uniform(-12,12)))
    for y in [-1530,1530]:
        mesh('DrainRecess',cube,(0,y,1),(33,.48,.05),dark)
        for x in range(-1600,1650,60):mesh('DrainGrille',cube,(x,y,5),(.05,.52,.04),wall)
    # Localised physically lit stage; all values persist in the actual level.
    for label,loc,color,intensity,radius in [('Key',(-150,-420,1000),(.32,.69,.79),115000,2200),('Rim',(760,580,750),(.24,.55,.72),65000,1750),('PlayerFill',(-780,550,650),(.23,.45,.58),26000,1500)]:
        a=spawn(u.PointLight,label,loc);c=a.point_light_component;c.set_light_color(u.LinearColor(*color,1));c.set_intensity(intensity);c.set_attenuation_radius(radius);c.set_source_radius(35);c.set_editor_property('contact_shadow_length',.15);c.set_cast_shadows(True)
    a=spawn(u.ExponentialHeightFog,'LowMist',(0,0,-150));fc=a.get_component_by_class(u.ExponentialHeightFogComponent);fc.set_editor_property('fog_density',.018);fc.set_editor_property('fog_height_falloff',.35);fc.set_editor_property('fog_inscattering_luminance',u.LinearColor(.018,.038,.055,1))
    fc.set_editor_property('enable_volumetric_fog',True)
    pp=spawn(u.PostProcessVolume,'Exposure');pp.set_editor_property('unbound',True)
    settings=pp.get_editor_property('settings')
    for k,v in {'auto_exposure_method':u.AutoExposureMethod.AEM_MANUAL,'auto_exposure_bias':7.5,'auto_exposure_apply_physical_camera_exposure':False,'vignette_intensity':.6,'bloom_intensity':.25,'motion_blur_amount':.15}.items():
        settings.set_editor_property('override_'+k,True);settings.set_editor_property(k,v)
    pp.set_editor_property('settings',settings)
    spawn(u.PlayerStart,'PlayerStart',(-230,570,95),(0,-145,0))
    spawn(L.generated_class(boss),'MainTeddy',(250,-230,232),(0,-135,0))
    spawn(L.generated_class(director),'CombatView',(-1980,0,2450),(-51,0,0))
    assert lev.save_current_level();assert u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
    assert lev.load_level(MAP)
    r.update(passed=True,map=MAP,actors=len(actors.get_all_level_actors()),boss_bounds=str(sk.get_bounds()))
except Exception:r['error']=traceback.format_exc();raise
finally:(ROOT/'evidence/implementation/scene-build.json').write_text(json.dumps(r,indent=2))
