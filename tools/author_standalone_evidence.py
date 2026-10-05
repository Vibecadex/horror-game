"""Isolated copy for ordinary -game launch evidence; final map remains untouched."""
import sys,json,os,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
OUT=Path(os.environ['TEDDY_STANDALONE_DIR']);QA='/Game/SetupValidation/Encounter_'+OUT.name.replace('-','_');MAP=QA+'/Standalone';r={'passed':False}
try:
    assert not A.does_asset_exist(MAP)
    lev=u.get_editor_subsystem(u.LevelEditorSubsystem);assert lev.new_level_from_template(MAP,'/Game/Maps/TeddyEncounter');assert lev.load_level(MAP);save(own(A.load_asset(MAP)))
    bp=own(L.create_blueprint_asset_with_parent(QA+'/BP_StandaloneProof',u.Actor.static_class()));g=Graph(bp);g.g.remove_nodes(g.g.list_all_nodes())
    begin=g.event('ReceiveBeginPlay');warm=g.call('KismetSystemLibrary.Delay',Duration=3)
    pc=g.call('GameplayStatics.GetPlayerController')
    def command(text):return g.call('KismetSystemLibrary.ExecuteConsoleCommand',Command=text,SpecificPlayer=(pc,'ReturnValue'))
    start=command('csvprofile start');record=g.call('/Script/AudioMixer.AudioMixerBlueprintLibrary.StartRecordingOutput',ExpectedDuration=10)
    wait=g.call('KismetSystemLibrary.Delay',Duration=5);stop=command('csvprofile stop')
    audio=g.call('/Script/AudioMixer.AudioMixerBlueprintLibrary.StopRecordingOutput',ExportType='WavFile',Name='standalone-audio',Path=str(OUT))
    shot=command('Shot filename="'+(OUT/'standalone.png').as_posix()+'" -nosuffix')
    marker=g.call('KismetSystemLibrary.PrintString',InString='TEDDY_STANDALONE_SAVED_BLUEPRINTS_EXECUTED',bPrintToScreen='false',bPrintToLog='true')
    completion=g.call('KismetSystemLibrary.Delay',Duration=5);quit=command('Quit');g.chain(begin,warm,start,record,wait,stop,audio,shot,marker,completion,quit);compile(bp)
    a=u.get_editor_subsystem(u.EditorActorSubsystem).spawn_actor_from_class(L.generated_class(bp),u.Vector(),u.Rotator(),transient=False);a.set_actor_label('Isolated_StandaloneEvidence');assert lev.save_current_level();assert u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
    r.update(passed=True,map=MAP,blueprint=bp.get_path_name(),source_map='/Game/Maps/TeddyEncounter')
except Exception:r['error']=traceback.format_exc();raise
finally:(OUT/'authoring.json').write_text(json.dumps(r,indent=2))
