import sys,json,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
r={'passed':False}
try:
    boss=existing(NS+'/Blueprints/BP_TeddyBoss');u.get_default_object(L.generated_class(boss)).set_editor_property('Speed',105.);compile(boss)
    child=duplicate(NS+'/Blueprints/BP_TeddyBoss','Blueprints/BP_Stitchling');g=Graph(child)
    assert A.get_metadata_tag(child,'StitchlingAuthored')!='v1','Already authored'
    default=u.get_default_object(L.generated_class(child))
    for name,value in {'Health':24.,'MaxHealth':24.,'Speed':55.,'AttackRange':190.,'StrikeRange':215.,'AttackDamage':10.}.items():default.set_editor_property(name,value)
    for _,c in components(child).values():
        if isinstance(c,u.CapsuleComponent):c.set_capsule_size(110.,160.,False)
        if isinstance(c,u.SkeletalMeshComponent):c.set_editor_property('relative_location',u.Vector(0,0,-160));c.set_editor_property('relative_scale3d',u.Vector(1,1,.65))
        if c.get_name()=='AttackWarning_GEN_VARIABLE':c.set_editor_property('relative_location',u.Vector(0,0,-156));c.set_editor_property('relative_scale3d',u.Vector(1.25,1.25,1))
    for n in g.g.list_all_nodes():
        pin=n.find_input_pin('NewAnimToPlay')
        if pin.is_valid() and 'A_Teddy_Walk' in str(pin.get_pin_value()):g.val(n,'NewAnimToPlay',NS+'/Teddy/Crawl/A_Teddy_Crawl')
    tick=next(n for n in g.g.list_all_nodes() if str(L.get_node_title(n))=='Event Tick');old=tick.find_output_pin('then').list_connected_pins();tick.find_output_pin('then').break_pin_links()
    main=g.call('GameplayStatics.GetActorOfClass',ActorClass=L.generated_class(boss).get_path_name());health=g.get('Health',L.generated_class(boss).get_path_name());g.val(health,'self',(main,'ReturnValue'));alive=g.branch((g.math('Greater_DoubleDouble',A=(health,'Health'),B=0),'ReturnValue'));g.chain(tick,main,alive)
    for pin in old:assert alive.find_output_pin('then').try_create_connection(pin)
    hp=g.set('Health',0);dead=g.set('State',3);anim=g.call('SkeletalMeshComponent.PlayAnimation',self=(g.get('Mesh'),'Mesh'),NewAnimToPlay=NS+'/Teddy/Defeat/A_Teddy_Defeat',bLooping='false');off=g.call('Actor.SetActorEnableCollision',bNewActorEnableCollision='false');stop=g.call('Actor.SetActorTickEnabled',bEnabled='false');hide=g.call('SceneComponent.SetVisibility',self=(g.get('AttackWarning'),'AttackWarning'),bNewVisibility='false',bPropagateToChildren='true');g.link(alive,'else',hp,'execute');g.chain(hp,dead,anim,off,hide,stop)
    compile(child);A.set_metadata_tag(child,'StitchlingAuthored','v1');save(child)
    lev=u.get_editor_subsystem(u.LevelEditorSubsystem);assert lev.load_level('/Game/Maps/TeddyEncounter');actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if a.get_actor_label().startswith('TE_Stitchling'):
            assert 'TeddyEncounterOwned' in [str(t) for t in a.tags];actors.destroy_actor(a)
    for i,loc in enumerate([(650,600,65),(-480,-500,65),(20,1070,65)]):
        a=actors.spawn_actor_from_class(L.generated_class(child),u.Vector(*loc),u.Rotator(yaw=130),transient=False);a.set_actor_label('TE_Stitchling_'+str(i+1));a.set_editor_property('tags',['TeddyEncounterOwned']);a.set_actor_scale3d(u.Vector(.35,.35,.35))
    assert lev.save_current_level();assert u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True);r['passed']=True
except Exception:r['error']=traceback.format_exc();raise
finally:(ROOT/'evidence/implementation/stitchlings-build.json').write_text(json.dumps(r,indent=2))
