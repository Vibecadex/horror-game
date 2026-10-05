"""Explicit chase, anticipation, strike, recovery, hit and dead states as Blueprint graphs."""
import sys,json,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
r={'passed':False}
def val(g,name):return(g.get(name),name)
try:
    boss=existing(NS+'/Blueprints/BP_TeddyBoss');g=Graph(boss);g.g.remove_nodes(g.g.list_all_nodes())
    for name,kind,default in [('Health','real',300),('MaxHealth','real',300),('State','int',0),('StateAge','real',0),('Speed','real',125),('AttackRange','real',380),('StrikeRange','real',475),('AttackDamage','real',24),('HitReady','real',0),('Attacks','int',0),('HitsReceived','int',0)]:g.var(name,kind,default);L.set_blueprint_variable_instance_editable(boss,name,True)
    # A pale/rust ring is revealed only during the anticipation window.
    ring=component(boss,'AttackWarning',u.StaticMeshComponent,'CapsuleComponent');ring.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cylinder'));ring.set_material(0,A.load_asset(NS+'/Materials/M_WarningLamp'));ring.set_editor_property('relative_location',u.Vector(0,0,-225));ring.set_editor_property('relative_scale3d',u.Vector(8.8,8.8,.015));ring.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);ring.set_visibility(False)
    def play(clip,loop=False):return g.call('SkeletalMeshComponent.PlayAnimation',self=val(g,'Mesh'),NewAnimToPlay=NS+'/Teddy/'+clip+'/A_Teddy_'+clip,bLooping=str(loop).lower())
    def warning(show):return g.call('SceneComponent.SetVisibility',self=val(g,'AttackWarning'),bNewVisibility=str(show).lower(),bPropagateToChildren='true')
    def state(n):return g.set('State',n)
    def reset():return g.set('StateAge',0)
    def branch_state(n):return g.branch((g.math('EqualEqual_IntInt',A=val(g,'State'),B=n),'ReturnValue'))
    begin=g.event('ReceiveBeginPlay');walk=play('Walk',True);g.chain(begin,walk)
    tick=g.event('ReceiveTick');age=g.set('StateAge',(g.math('Add_DoubleDouble',A=val(g,'StateAge'),B=(tick,'DeltaSeconds')),'ReturnValue'));g.chain(tick,age)
    alive=g.branch((g.math('Greater_DoubleDouble',A=val(g,'Health'),B=0),'ReturnValue'));g.chain(age,alive)
    player=g.call('GameplayStatics.GetPlayerPawn');ploc=g.call('Actor.K2_GetActorLocation',self=(player,'ReturnValue'));loc=g.call('Actor.K2_GetActorLocation');distance=g.math('Vector_Distance',V1=(ploc,'ReturnValue'),V2=(loc,'ReturnValue'))
    chase=branch_state(0);g.link(alive,'then',chase,'execute')
    far=g.branch((g.math('Greater_DoubleDouble',A=(distance,'ReturnValue'),B=val(g,'AttackRange')),'ReturnValue'));g.link(chase,'then',far,'execute')
    delta=g.math('Subtract_VectorVector',A=(ploc,'ReturnValue'),B=(loc,'ReturnValue'));xyz=g.math('BreakVector',InVec=(delta,'ReturnValue'));flat=g.math('MakeVector',X=(xyz,'X'),Y=(xyz,'Y'),Z=0);normal=g.math('Normal',A=(flat,'ReturnValue'))
    step=g.math('Multiply_DoubleDouble',A=(tick,'DeltaSeconds'),B=val(g,'Speed'));offset=g.math('Multiply_VectorFloat',A=(normal,'ReturnValue'),B=(step,'ReturnValue'))
    look=g.math('FindLookAtRotation',Start=(loc,'ReturnValue'),Target=(ploc,'ReturnValue'));breakrot=g.math('BreakRotator',InRot=(look,'ReturnValue'));rot=g.math('MakeRotator',Yaw=(breakrot,'Yaw'),Pitch=0,Roll=0)
    turn=g.call('Actor.K2_SetActorRotation',NewRotation=(rot,'ReturnValue'),bTeleportPhysics='false');move=g.call('Actor.K2_AddActorWorldOffset',DeltaLocation=(offset,'ReturnValue'),bSweep='true',bTeleport='false');g.link(far,'then',turn,'execute');g.chain(turn,move)
    anticipation=state(1);zero=reset();attackanim=play('Attack');show=warning(True);g.link(far,'else',anticipation,'execute');g.chain(anticipation,zero,attackanim,show)
    windup=branch_state(1);g.link(chase,'else',windup,'execute')
    ready=g.branch((g.math('GreaterEqual_DoubleDouble',A=val(g,'StateAge'),B='.92'),'ReturnValue'));g.link(windup,'then',ready,'execute')
    recover=state(2);zero2=reset();hide=warning(False);attacks=g.set('Attacks',(g.math('Add_IntInt',A=val(g,'Attacks'),B=1),'ReturnValue'));g.link(ready,'then',recover,'execute');g.chain(recover,zero2,hide,attacks)
    inrange=g.branch((g.math('LessEqual_DoubleDouble',A=(distance,'ReturnValue'),B=val(g,'StrikeRange')),'ReturnValue'));g.chain(attacks,inrange)
    owner=g.call('ActorComponent.GetOwner',self=val(g,'CapsuleComponent'));damage=g.call('GameplayStatics.ApplyDamage',DamagedActor=(player,'ReturnValue'),BaseDamage=val(g,'AttackDamage'),DamageCauser=(owner,'ReturnValue'));g.link(inrange,'then',damage,'execute')
    # Recovery completes the same animation; callbacks cannot survive death or a level restart.
    recovery=branch_state(2);g.link(windup,'else',recovery,'execute');done=g.branch((g.math('Greater_DoubleDouble',A=val(g,'StateAge'),B='1.15'),'ReturnValue'));g.link(recovery,'then',done,'execute');chaseagain=state(0);walkagain=play('Walk',True);g.link(done,'then',chaseagain,'execute');g.chain(chaseagain,walkagain)
    hitstate=branch_state(4);g.link(recovery,'else',hitstate,'execute');hitdone=g.branch((g.math('Greater_DoubleDouble',A=val(g,'StateAge'),B='.32'),'ReturnValue'));g.link(hitstate,'then',hitdone,'execute');g.link(hitdone,'then',chaseagain,'execute')
    hit=g.event('ReceiveAnyDamage');canhit=g.branch((g.math('Greater_DoubleDouble',A=val(g,'Health'),B=0),'ReturnValue'));g.chain(hit,canhit)
    minus=g.math('Subtract_DoubleDouble',A=val(g,'Health'),B=(hit,'Damage'));hp=g.set('Health',(g.math('FMax',A=(minus,'ReturnValue'),B=0),'ReturnValue'));count=g.set('HitsReceived',(g.math('Add_IntInt',A=val(g,'HitsReceived'),B=1),'ReturnValue'));g.link(canhit,'then',hp,'execute');g.chain(hp,count)
    lethal=g.branch((g.math('LessEqual_DoubleDouble',A=val(g,'Health'),B=0),'ReturnValue'));g.chain(count,lethal)
    dead=state(3);hide2=warning(False);death=play('Defeat');collision=g.call('Actor.SetActorEnableCollision',bNewActorEnableCollision='false');g.link(lethal,'then',dead,'execute');g.chain(dead,hide2,death,collision)
    # Heavy boss resists stunlock during its attack; a spaced hit reaction interrupts pursuit.
    current=g.call('GameplayStatics.GetTimeSeconds');cool=g.math('Greater_DoubleDouble',A=(current,'ReturnValue'),B=val(g,'HitReady'));chasing=g.math('EqualEqual_IntInt',A=val(g,'State'),B=0);react=g.branch((g.math('BooleanAND',A=(cool,'ReturnValue'),B=(chasing,'ReturnValue')),'ReturnValue'));g.link(lethal,'else',react,'execute')
    hs=state(4);hz=reset();ha=play('Hit');nextreact=g.set('HitReady',(g.math('Add_DoubleDouble',A=(current,'ReturnValue'),B='1.3'),'ReturnValue'));g.link(react,'then',hs,'execute');g.chain(hs,hz,ha,nextreact)
    compile(boss)
    r['passed']=True;r['states']={'0':'chase','1':'anticipation','2':'strike recovery','3':'dead','4':'hit reaction'}
except Exception:r['error']=traceback.format_exc();raise
finally:(ROOT/'evidence/implementation/boss-build.json').write_text(json.dumps(r,indent=2))
