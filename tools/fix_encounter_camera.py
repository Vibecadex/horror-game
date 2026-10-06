"""Frame the player and boss together, with measured room for their full silhouettes."""
import sys, json, traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
historical_builder(__file__)
r={'passed':False};lev=u.get_editor_subsystem(u.LevelEditorSubsystem)
try:
    assert lev.load_level('/Game/Maps/TeddyEncounter')
    bp=existing(NS+'/Blueprints/BP_CombatCamera');g=Graph(bp);g.g.remove_nodes(g.g.list_all_nodes())
    begin=g.event('ReceiveBeginPlay');delay=g.call('KismetSystemLibrary.Delay',Duration='.2');pc=g.call('GameplayStatics.GetPlayerController')
    camera=g.get('CombatCamera');owner=g.call('ActorComponent.GetOwner',self=(camera,'CombatCamera'))
    view=g.call('PlayerController.SetViewTargetWithBlend',self=(pc,'ReturnValue'),NewViewTarget=(owner,'ReturnValue'),BlendTime=0);g.chain(begin,delay,view)
    tick=g.event('ReceiveTick');player=g.call('GameplayStatics.GetPlayerPawn')
    boss=g.call('GameplayStatics.GetActorOfClass',ActorClass=L.generated_class(existing(NS+'/Blueprints/BP_TeddyBoss')).get_path_name())
    p=g.call('Actor.K2_GetActorLocation',self=(player,'ReturnValue'));b=g.call('Actor.K2_GetActorLocation',self=(boss,'ReturnValue'))
    pv=g.math('BreakVector',InVec=(p,'ReturnValue'));bv=g.math('BreakVector',InVec=(b,'ReturnValue'))
    centers=[]
    for axis in ['X','Y']:
        total=g.math('Add_DoubleDouble',A=(pv,axis),B=(bv,axis));mid=g.math('Multiply_DoubleDouble',A=(total,'ReturnValue'),B=.5);centers.append(mid)
    # Perspective makes the foreground silhouette larger. Bias the view towards
    # that end of the pair rather than losing the boss's feet behind the HUD.
    separation=g.math('Subtract_DoubleDouble',A=(pv,'X'),B=(bv,'X'))
    magnitude=g.math('Abs',A=(separation,'ReturnValue'))
    bias=g.math('Multiply_DoubleDouble',A=(magnitude,'ReturnValue'),B=.07)
    center_x=g.math('Subtract_DoubleDouble',A=(centers[0],'ReturnValue'),B=(bias,'ReturnValue'))
    side_delta=g.math('Subtract_DoubleDouble',A=(pv,'Y'),B=(bv,'Y'))
    side_abs=g.math('Abs',A=(side_delta,'ReturnValue'))
    longitudinal=g.math('Multiply_DoubleDouble',A=(magnitude,'ReturnValue'),B=1.42)
    lateral=g.math('Multiply_DoubleDouble',A=(side_abs,'ReturnValue'),B=.8)
    extent=g.math('FMax',A=(longitudinal,'ReturnValue'),B=(lateral,'ReturnValue'))
    padded=g.math('Add_DoubleDouble',A=(extent,'ReturnValue'),B=1200)
    height=g.math('FClamp',Value=(padded,'ReturnValue'),Min=2100,Max=5600)
    back=g.math('Multiply_DoubleDouble',A=(height,'ReturnValue'),B=-.809784)
    x=g.math('Add_DoubleDouble',A=(center_x,'ReturnValue'),B=(back,'ReturnValue'))
    z=g.math('Add_DoubleDouble',A=(height,'ReturnValue'),B=160)
    target=g.math('MakeVector',X=(x,'ReturnValue'),Y=(centers[1],'ReturnValue'),Z=(z,'ReturnValue'))
    current=g.call('Actor.K2_GetActorLocation')
    smooth=g.math('VInterpTo',Current=(current,'ReturnValue'),Target=(target,'ReturnValue'),DeltaTime=(tick,'DeltaSeconds'),InterpSpeed=5)
    move=g.call('Actor.K2_SetActorLocation',NewLocation=(smooth,'ReturnValue'),bSweep='false',bTeleport='false');g.chain(tick,boss,move)
    A.set_metadata_tag(bp,'TrackingAuthored','pair-framing-v2');compile(bp)
    assert lev.save_current_level();assert u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True);assert lev.load_level('/Game/Maps/TeddyEncounter')
    r.update(passed=True,pitch=-51,fov=50,tracking='Player/boss midpoint with foreground perspective bias 0.07*abs(deltaX), target z160; height=max(2100, abs(deltaX)*1.42+1200, abs(deltaY)*0.8+1200), capped5600; constant elevation angle; interpolation5')
except Exception:r['error']=traceback.format_exc();raise
finally:(ROOT/'evidence/implementation/camera-framing.json').write_text(json.dumps(r,indent=2))
