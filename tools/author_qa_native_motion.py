"""Create an isolated capture map with a normal-input driver; never alter the playable map."""
import json
import os
import sys
import traceback
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from encounter_authoring import A, L, Graph, own, save, compile, existing

OUT = Path(os.environ['TEDDY_NATIVE_MOTION_DIR'])
QA = '/Game/SetupValidation/NativeMotion_' + OUT.name.replace('-', '_')
MAP = QA + '/Encounter'
result = {'passed': False, 'map': MAP, 'source_map': '/Game/Maps/TeddyEncounter',
          'method': 'Isolated map copy; original saved gameplay, normal AI and health. Driver emits key events and continuous aim action, with no actor teleports, health editing or AI freezes.'}
try:
    assert not A.does_asset_exist(MAP)
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    assert levels.new_level_from_template(MAP, result['source_map'])
    assert levels.load_level(MAP)
    save(own(A.load_asset(MAP)))
    bp = own(L.create_blueprint_asset_with_parent(QA + '/BP_CaptureDriver', u.Actor.static_class()))
    g = Graph(bp)
    g.g.remove_nodes(g.g.list_all_nodes())
    pc = g.call('GameplayStatics.GetPlayerController')

    def command(text):
        return g.call('KismetSystemLibrary.ExecuteConsoleCommand', Command=text, SpecificPlayer=(pc, 'ReturnValue'))

    def delay(seconds):
        return g.call('KismetSystemLibrary.Delay', Duration=seconds)

    # Direct aim action is explicitly separated from the movement/fire/dodge key path.
    tick = g.event('ReceiveTick')
    player = g.call('GameplayStatics.GetPlayerPawn')
    boss = g.call('GameplayStatics.GetActorOfClass', ActorClass=L.generated_class(existing('/Game/TeddyEncounter/Blueprints/BP_TeddyBoss')).get_path_name())
    ploc = g.call('Actor.K2_GetActorLocation', self=(player, 'ReturnValue'))
    bloc = g.call('Actor.K2_GetActorLocation', self=(boss, 'ReturnValue'))
    delta = g.math('Subtract_VectorVector', A=(bloc, 'ReturnValue'), B=(ploc, 'ReturnValue'))
    xyz = g.math('BreakVector', InVec=(delta, 'ReturnValue'))
    negative = g.math('Multiply_DoubleDouble', A=(xyz, 'X'), B=-1)
    aim = g.math('MakeVector', X=(negative, 'ReturnValue'), Y=(xyz, 'Y'), Z=0)
    unit = g.math('Normal', A=(aim, 'ReturnValue'))
    text = g.call('KismetStringLibrary.Conv_VectorToString', InVec=(unit, 'ReturnValue'))
    text = g.call('KismetStringLibrary.Concat_StrStr', A='Input.+action IA_Action_StickAim ', B=(text, 'ReturnValue'))
    aim_command = command((text, 'ReturnValue'))
    g.chain(tick, boss, aim_command)

    begin = g.event('ReceiveBeginPlay')
    sound = g.call('/Script/AudioMixer.AudioMixerBlueprintLibrary.StartRecordingOutput', ExpectedDuration=30)
    marker = g.call('KismetSystemLibrary.PrintString', InString='QA_NATIVE_MOTION_AUDIO_BEGIN', bPrintToScreen='false', bPrintToLog='true')
    nodes = [begin, delay(2.5), sound, marker, delay(1), command('Input.+key W'), delay(.45), command('Input.-key W'),
             delay(.35), command('Input.+key S'), command('Input.+key SpaceBar'), delay(.1), command('Input.-key SpaceBar'),
             delay(.3), command('Input.-key S'), delay(.7), command('Input.+key D'), delay(.65), command('Input.-key D'),
             command('Input.+key W'), delay(.45), command('Input.-key W'), delay(.5), command('Input.+key LeftMouseButton'),
             delay(1.1), command('Input.+key A'), delay(.65), command('Input.-key A'), delay(1), command('Input.+key S'),
             command('Input.+key SpaceBar'), delay(.1), command('Input.-key SpaceBar'), delay(.25), command('Input.-key S'),
             delay(5), command('Input.-key LeftMouseButton'), command('Input.-action IA_Action_StickAim'), delay(4)]
    stop_sound = g.call('/Script/AudioMixer.AudioMixerBlueprintLibrary.StopRecordingOutput', ExportType='WavFile', Name='native-game-audio', Path=str(OUT))
    done = g.call('KismetSystemLibrary.PrintString', InString='QA_NATIVE_MOTION_FINISHED', bPrintToScreen='false', bPrintToLog='true')
    nodes.extend([stop_sound, done, delay(3), command('Quit')])
    g.chain(*nodes)
    compile(bp)
    actor = u.get_editor_subsystem(u.EditorActorSubsystem).spawn_actor_from_class(L.generated_class(bp), u.Vector(), u.Rotator(), transient=False)
    actor.set_actor_label('QA_NativeMotionDriver')
    assert levels.save_current_level()
    # The driver Blueprint and isolated level were saved explicitly above.
    # Do not save other loaded packages while verifying a shared art handoff.
    result.update(passed=True, driver=bp.get_path_name(), expected_seconds=22.15,
                  final_observation_seconds=4,
                  final_observation_reason='Retain the settled collapse after the normal-input firing sequence; no gameplay changes.')
except Exception:
    result['error'] = traceback.format_exc()
    raise
finally:
    (OUT / 'authoring.json').write_text(json.dumps(result, indent=2))
