import unreal as u,os,time,json,sys,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from finish_editor import finish_editor
OUT=Path(os.environ['TEDDY_TEST_DIR']);lev=u.get_editor_subsystem(u.LevelEditorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);s={'stage':0,'wall':time.monotonic()};r={'passed':False};handle=None
def finish(error=None):
    r['passed']=error is None
    if error:r['error']=error
    (OUT/'receipt.json').write_text(json.dumps(r,indent=2,default=str));finish_editor(handle)
def tick(dt):
    try:
        w=ed.get_game_world()
        if not w:return
        game=u.GameplayStatics.get_time_seconds(w)
        if s['stage']==0 and game>1:
            r['components']=[{'name':x.get_path_name(),'sound':str(x.sound),'volume':x.volume_multiplier,'playing':x.is_playing(),'active':x.is_active()} for x in u.ObjectIterator(u.AudioComponent) if x.get_world()==w]
            r['sounds']=[]
            for name in ['Rifle','Slam','RoomTone']:
                obj=u.load_asset('/Game/TeddyEncounter/Audio/'+name);r['sounds'].append({'name':name,'duration':obj.duration})
            settings=u.get_default_object(u.load_class(None,'/Script/UnrealEd.LevelEditorPlaySettings'));r['game_sound_enabled']=settings.get_editor_property('EnableGameSound')
            u.AudioMixerLibrary.start_recording_output(w,10);s['stage']=1;s['t']=game
        elif s['stage']==1 and game-s['t']>.25:
            u.GameplayStatics.play_sound2d(w,u.load_asset('/Game/TeddyEncounter/Audio/Rifle'),1.,1.);s['stage']=2
        elif s['stage']==2 and game-s['t']>3:
            u.AudioMixerLibrary.stop_recording_output(w,u.AudioRecordingExportType.WAV_FILE,'probe',str(OUT));s['stage']=3
        elif s['stage']==3 and (OUT/'probe.wav').exists():finish()
        if time.monotonic()-s['wall']>50:finish('timeout')
    except Exception:finish(traceback.format_exc())
try:
    u.EditorPythonScripting.set_keep_python_script_alive(True);assert lev.load_level('/Game/Maps/TeddyEncounter')
    settings=u.get_default_object(u.load_class(None,'/Script/UnrealEd.LevelEditorPlaySettings'));r['game_sound_before']=settings.get_editor_property('EnableGameSound');settings.set_editor_property('EnableGameSound',True)
    lev.editor_request_begin_play();handle=u.register_slate_post_tick_callback(tick)
except Exception:finish(traceback.format_exc())
