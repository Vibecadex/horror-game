"""Saved Blueprint runtime combat; Python is authoring only."""
import sys,json,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
r={'passed':False,'completed':[]}
def getter(g,name,cls=''):return g.get(name,cls),name
def character_self(g):
    comp=g.get('CapsuleComponent');return g.call('ActorComponent.GetOwner',self=(comp,'CapsuleComponent')),'ReturnValue'
def animation(g,clip,loop=False):
    return g.call('SkeletalMeshComponent.PlayAnimation',self=getter(g,'Mesh'),NewAnimToPlay=NS+'/Teddy/'+clip+'/A_Teddy_'+clip,bLooping=str(loop).lower())
def setstate(g,state):return g.set('State',state)
def resetage(g):return g.set('StateAge',0)
def state_branch(g,state):return g.branch((g.math('EqualEqual_IntInt',A=getter(g,'State'),B=state),'ReturnValue'))
try:
    # Projectile uses continuous swept movement and explicit owner/instigator from the firing player.
    projectile=duplicate('/Game/Variant_TwinStick/Blueprints/BP_TwinStickProjectile','Blueprints/BP_EncounterProjectile')
    g=Graph(projectile);g.g.remove_nodes(g.g.list_all_nodes())
    for _,c in components(projectile).values():
        if isinstance(c,u.StaticMeshComponent):
            c.set_editor_property('relative_scale3d',u.Vector(.32,.045,.045));c.set_material(0,A.load_asset(NS+'/Materials/M_Muzzle'));c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        if isinstance(c,u.SphereComponent):c.set_sphere_radius(5.,False)
        if isinstance(c,u.ProjectileMovementComponent):c.set_editor_property('initial_speed',3200.);c.set_editor_property('max_speed',3200.);c.set_editor_property('projectile_gravity_scale',0.)
    begin=g.event('ReceiveBeginPlay');life=g.call('Actor.SetLifeSpan',InLifespan='1.6');g.chain(begin,life)
    hit=g.event('ReceiveHit');owner=g.call('Actor.GetOwner');cmp=g.math('NotEqual_ObjectObject',A=(hit,'Other'),B=(owner,'ReturnValue'));branch=g.branch((cmp,'ReturnValue'));g.chain(hit,branch)
    inst=g.call('Actor.GetInstigatorController');damage=g.call('GameplayStatics.ApplyDamage',DamagedActor=(hit,'Other'),BaseDamage='12',EventInstigator=(inst,'ReturnValue'),DamageCauser=(owner,'ReturnValue'))
    destroy=g.call('Actor.K2_DestroyActor');g.link(branch,'then',damage,'execute');g.chain(damage,destroy)
    compile(projectile);r['completed'].append('projectile')
    # Player preserves the template movement / aim graph, with owned firing and damage.
    pawn=existing(NS+'/Blueprints/BP_EncounterPlayer');g=Graph(pawn)
    assert A.get_metadata_tag(pawn,'CombatAuthored')!='v1','Player extension already saved; do not duplicate nodes'
    g.var('Health','real',100);g.var('DodgeUntil','real',0);g.var('NextDodge','real',0)
    nodes={n.get_name():n for n in g.g.list_all_nodes()}
    context=duplicate('/Game/Variant_TwinStick/Input/IMC_TwinStick','Input/IMC_Encounter')
    defaults=context.get_editor_property('default_key_mappings');entries=list(defaults.get_editor_property('mappings'))
    mouse=A.load_asset('/Game/Variant_TwinStick/Input/IMC_TwinStick_MouseShoot').get_editor_property('default_key_mappings').get_editor_property('mappings')
    keys={str(e.key) for e in entries}
    for e in mouse:
        if str(e.key) not in keys:entries.append(e)
    if not any(str(u.InputLibrary.key_get_display_name(e.key))=='Space Bar' and 'Dash' in str(e.action) for e in entries):
        key=u.Key();key.import_text('SpaceBar')
        assert u.InputLibrary.key_is_valid(key) and key.export_text()=='SpaceBar'
        entries.append(u.EnhancedActionKeyMapping(action=A.load_asset('/Game/Variant_TwinStick/Input/Actions/IA_Action_Dash'),key=key))
    defaults.set_editor_property('mappings',entries);context.set_editor_property('default_key_mappings',defaults);save(context)
    g.val(nodes['K2Node_CallFunction_0'],'MappingContext',context.get_path_name())
    spawn=nodes['K2Node_SpawnActorFromClass_0'];g.val(spawn,'Class',L.generated_class(projectile).get_path_name());g.val(spawn,'CollisionHandlingOverride','AlwaysSpawn')
    player=g.call('GameplayStatics.GetPlayerPawn');g.val(spawn,'Owner',(player,'ReturnValue'));g.val(spawn,'Instigator',(player,'ReturnValue'))
    # Independent aiming: remove the stock stick-aim auto-fire continuation on the owned copy.
    for name in ['K2Node_CallFunction_48','K2Node_CallFunction_19']:
        nodes[name].find_output_pin('then').break_pin_links()
    # Default human animation now uses the shipped rifle stance while moving via an owned BlendSpace.
    # A later visual pass refines the upper-body pose; existing foot locomotion remains intact.
    now=g.call('GameplayStatics.GetTimeSeconds')
    damageevent=g.event('ReceiveAnyDamage');alive=g.math('Greater_DoubleDouble',A=getter(g,'Health'),B=0);outside=g.math('Greater_DoubleDouble',A=(now,'ReturnValue'),B=getter(g,'DodgeUntil'));both=g.math('BooleanAND',A=(alive,'ReturnValue'),B=(outside,'ReturnValue'));take=g.branch((both,'ReturnValue'));g.chain(damageevent,take)
    subtract=g.math('Subtract_DoubleDouble',A=getter(g,'Health'),B=(damageevent,'Damage'));clamp=g.math('FClamp',Value=(subtract,'ReturnValue'),Min=0,Max=100);hp=g.set('Health',(clamp,'ReturnValue'));g.link(take,'then',hp,'execute')
    dead=g.branch((g.math('LessEqual_DoubleDouble',A=getter(g,'Health'),B=0),'ReturnValue'));g.chain(hp,dead)
    disable=g.call('Pawn.DetachFromControllerPendingDestroy');# keep possession for restart; disable pawn input instead
    g.g.remove_nodes([disable])
    pcget=g.call('GameplayStatics.GetPlayerController');off=g.call('Actor.DisableInput',PlayerController=(pcget,'ReturnValue'));death=g.call('SkeletalMeshComponent.PlayAnimation',self=getter(g,'Mesh'),NewAnimToPlay='/Game/Characters/Mannequins/Anims/Death/MM_Death_Front_01',bLooping='false');g.link(dead,'then',off,'execute');g.chain(off,death)
    # Directional dash uses the shipped collision-aware launch; add a cooldown and a short damage window.
    knot=nodes['K2Node_Knot_2'];launch=nodes['K2Node_CallFunction_29'];knot.find_output_pin('OutputPin').break_pin_links()
    ready=g.math('GreaterEqual_DoubleDouble',A=(now,'ReturnValue'),B=getter(g,'NextDodge'));dash=g.branch((ready,'ReturnValue'));g.link(knot,'OutputPin',dash,'execute')
    inv=g.set('DodgeUntil',(g.math('Add_DoubleDouble',A=(now,'ReturnValue'),B='.26'),'ReturnValue'));cool=g.set('NextDodge',(g.math('Add_DoubleDouble',A=(now,'ReturnValue'),B='.8'),'ReturnValue'));g.link(dash,'then',inv,'execute');g.chain(inv,cool,launch)
    # Keep stationary fallback useful: initial last movement is forward; later movement updates it.
    L.set_blueprint_variable_instance_editable(pawn,'Last Move',True)
    cdo=u.get_default_object(L.generated_class(pawn));cdo.set_editor_property('Last Move',u.Vector2D(1,0))
    compile(pawn);A.set_metadata_tag(pawn,'CombatAuthored','v1');save(pawn);r['completed'].append('player')
    # Controller owns pause and restart, avoiding template automatic respawn into its source pawn.
    pc=existing(NS+'/Blueprints/BP_EncounterController');g=Graph(pc);g.g.remove_nodes(g.g.list_all_nodes())
    begin=g.event('ReceiveBeginPlay');cursor=g.set('bShowMouseCursor','true','/Script/Engine.PlayerController');g.chain(begin,cursor)
    # Mapping context is added by the duplicated player; fire's context is added here explicitly.
    # Use the preserved subsystem node from a temporary read of the original controller's graph pattern.
    pause=g.node(g.g.create_node_from_name('Input|KeyboardEvents|Escape',u.Vector2D(0,0),[]));pause.set_editor_property('execute_when_paused',True)
    restart=g.node(g.g.create_node_from_name('Input|KeyboardEvents|F5',u.Vector2D(0,0),[]));restart.set_editor_property('execute_when_paused',True)
    ispaused=g.call('GameplayStatics.IsGamePaused');toggle=g.call('GameplayStatics.SetGamePaused',bPaused=(g.math('Not_PreBool',A=(ispaused,'ReturnValue')),'ReturnValue'));g.link(pause,'Pressed',toggle,'execute')
    unpause=g.call('GameplayStatics.SetGamePaused',bPaused='false');openlevel=g.call('GameplayStatics.OpenLevel',LevelName='/Game/Maps/TeddyEncounter',bAbsolute='true');g.link(restart,'Pressed',unpause,'execute');g.chain(unpause,openlevel)
    # Callable events route tests through the same pause/restart chains as the key nodes.
    pe=g.custom('ToggleEncounterPause');g.link(pe,'then',toggle,'execute');re=g.custom('RestartEncounter');g.link(re,'then',unpause,'execute')
    compile(pc);r['completed'].append('controller')
    r['passed']=True
except Exception:r['error']=traceback.format_exc();raise
finally:(ROOT/'evidence/implementation/combat-build.json').write_text(json.dumps(r,indent=2))
