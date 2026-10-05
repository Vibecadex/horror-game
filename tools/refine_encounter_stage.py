import sys,json,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
lev=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem);r={'passed':False}
def spawn(cls,label,loc,rot=None):
    a=actors.spawn_actor_from_class(cls,u.Vector(*loc),rot or u.Rotator(),transient=False);a.set_actor_label(label);a.set_editor_property('tags',['TeddyEncounterOwned']);return a
def mesh(label,loc,scale,mat):
    a=spawn(u.StaticMeshActor,label,loc);a.set_actor_scale3d(u.Vector(*scale));c=a.static_mesh_component;c.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'));c.set_material(0,mat);return a
try:
    assert lev.load_level('/Game/Maps/TeddyEncounter')
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    for name in ['T_Concrete_Color','T_Concrete_Normal','T_Concrete_Roughness','AttackRing']:
        previous=existing(NS+'/Arena/'+name)
        t=u.AssetImportTask();t.filename=str(ROOT/'Assets/Adapted/Arena'/(name+('.fbx' if name=='AttackRing' else '.png')));t.destination_path=NS+'/Arena';t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=bool(previous)
        if name=='AttackRing':
            opt=u.FbxImportUI();opt.set_editor_property('automated_import_should_detect_type',False);opt.set_editor_property('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH);opt.set_editor_property('import_materials',False);opt.set_editor_property('import_textures',False);t.options=opt
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);assert t.imported_object_paths;obj=own(A.load_asset(t.imported_object_paths[0]))
        if name.endswith('Normal'):obj.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP);obj.set_editor_property('srgb',False)
        if name.endswith('Roughness'):obj.set_editor_property('srgb',False)
        save(obj)
    for a in actors.get_all_level_actors():
        if a.get_actor_label().startswith('TE_CombatBound') or a.get_actor_label().startswith('TE_Edge') or a.get_actor_label()=='TE_FaceFill':
            assert 'TeddyEncounterOwned' in [str(t) for t in a.tags];actors.destroy_actor(a)
        elif a.get_actor_label()=='TE_CombatView':a.set_actor_location(u.Vector(-1680,0,2100),False,False)
        elif a.get_actor_label()=='TE_LowMist':a.get_component_by_class(u.ExponentialHeightFogComponent).set_editor_property('fog_density',.013)
    dark=existing(NS+'/Materials/M_OxidisedIron');red=existing(NS+'/Materials/M_WarningLamp')
    for label,loc,scale in [('Back',(1480,0,95),(.8,30,2)),('Front',(-1420,0,45),(.8,30,1)),('Left',(0,-1500,95),(30,.8,2)),('Right',(0,1500,95),(30,.8,2))]:mesh('TE_CombatBound'+label,loc,scale,dark)
    for x in [-850,780]:
        for y in [-1445,1445]:
            mesh('TE_EdgePillar',(x,y,160),(1.1,.8,3.3),dark)
            mesh('TE_EdgeLamp',(x-57,y,185),(.035,.11,.45),red)
            a=spawn(u.PointLight,'TE_EdgeGlow',(x-80,y,190));c=a.point_light_component;c.set_editor_property('mobility',u.ComponentMobility.MOVABLE);c.set_editor_property('intensity',230.);c.set_editor_property('attenuation_radius',400.);c.set_light_color(u.LinearColor(1,.02,.009,1))
    a=spawn(u.PointLight,'TE_FaceFill',(-1450,-350,1050));c=a.point_light_component;c.set_editor_property('mobility',u.ComponentMobility.MOVABLE);c.set_editor_property('intensity',6500.);c.set_editor_property('attenuation_radius',3000.);c.set_editor_property('source_radius',240.);c.set_light_color(u.LinearColor(.27,.39,.42,1))
    director=existing(NS+'/Blueprints/BP_CombatCamera');camera=component(director,'CombatCamera',u.CameraComponent);camera.set_editor_property('field_of_view',50.)
    g=Graph(director)
    if A.get_metadata_tag(director,'TrackingAuthored')!='v1':
        # Gentle view translation keeps the combat frame elevated and input axes stable.
        default=[n for n in g.g.list_all_nodes() if str(L.get_node_title(n))=='Event Tick'];g.g.remove_nodes(default)
        tick=g.event('ReceiveTick');player=g.call('GameplayStatics.GetPlayerPawn');loc=g.call('Actor.K2_GetActorLocation',self=(player,'ReturnValue'));xyz=g.math('BreakVector',InVec=(loc,'ReturnValue'))
        offsets=[]
        for axis,limit in [('X',160),('Y',180)]:
            factor=g.math('Multiply_DoubleDouble',A=(xyz,axis),B='.17');offsets.append(g.math('FClamp',Value=(factor,'ReturnValue'),Min=-limit,Max=limit))
        x=g.math('Add_DoubleDouble',A=(offsets[0],'ReturnValue'),B=-1680);target=g.math('MakeVector',X=(x,'ReturnValue'),Y=(offsets[1],'ReturnValue'),Z=2100)
        current=g.call('Actor.K2_GetActorLocation');smooth=g.math('VInterpTo',Current=(current,'ReturnValue'),Target=(target,'ReturnValue'),DeltaTime=(tick,'DeltaSeconds'),InterpSpeed=2)
        move=g.call('Actor.K2_SetActorLocation',NewLocation=(smooth,'ReturnValue'),bSweep='false',bTeleport='false');g.chain(tick,move);A.set_metadata_tag(director,'TrackingAuthored','v1')
    compile(director)
    boss=existing(NS+'/Blueprints/BP_TeddyBoss');ring=component(boss,'AttackWarning',u.StaticMeshComponent,'CapsuleComponent')
    ring.set_static_mesh(existing(NS+'/Arena/AttackRing'));ring.set_editor_property('relative_scale3d',u.Vector(1,1,1));ring.set_editor_property('relative_location',u.Vector(0,0,-226));ring.set_editor_property('cast_shadow',False)
    warning=constmat('M_AttackWarning',(.37,.065,.025),.8,1.8);warning.set_editor_property('two_sided',True);save(warning);ring.set_material(0,warning);compile(boss)
    pawn=existing(NS+'/Blueprints/BP_EncounterPlayer');beam=component(pawn,'AimGuide',u.StaticMeshComponent,'CapsuleComponent')
    beam.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'));beam.set_editor_property('relative_location',u.Vector(525,0,30));beam.set_editor_property('relative_scale3d',u.Vector(9,.007,.007));beam.set_editor_property('cast_shadow',False);beam.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    pale=constmat('M_AimLine',(.06,.16,.17),.8,2);beam.set_material(0,pale);compile(pawn)
    assert lev.save_current_level();assert u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True);r['passed']=True
except Exception:r['error']=traceback.format_exc();raise
finally:(ROOT/'evidence/implementation/stage-refinement.json').write_text(json.dumps(r,indent=2))
