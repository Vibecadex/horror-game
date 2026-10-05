"""Held samples of the saved skeletal clips in the actual gameplay view."""
import sys,os,time,json,traceback,math
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from png_evidence import decode_png
from finish_editor import finish_editor
OUT=Path(os.environ['TEDDY_TEST_DIR']);lev=u.get_editor_subsystem(u.LevelEditorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
samples=[('Walk',0),('Walk',.3),('Walk',.6),('Walk',.9),('Attack',.25),('Attack',.8),('Attack',1.15),('Hit',.15),('Defeat',.65),('Defeat',1.5),('Defeat',2.3)]
s={'wall':time.monotonic(),'index':0,'stage':0,'finished':False};r={'passed':False,'method':'Clips staged at explicit time; zero play rate and world pause hold pose, pawn and gameplay camera during complete PNG validation','samples':[]};handle=None
def finish(error=None):
    if s['finished']:return
    s['finished']=True;r['passed']=not error and len(r['samples'])==len(samples)
    if error:r['error']=error
    (OUT/'receipt.json').write_text(json.dumps(r,indent=2));finish_editor(handle)
def pose(mesh,pc):
    result={'animation_time':mesh.get_position(),'camera':str(pc.player_camera_manager.get_camera_location()),'rotation':str(pc.player_camera_manager.get_camera_rotation())}
    for name in ['root','foot_L','foot_R','head','hand_L','hand_R']:
        v=mesh.get_socket_location(name);result[name]=[v.x,v.y,v.z]
    return result
def tick(dt):
    try:
        wall=time.monotonic()
        if wall-s['wall']>220:raise RuntimeError('Animation capture timeout')
        w=ed.get_game_world()
        if not w:return
        p=u.GameplayStatics.get_player_pawn(w,0);pc=u.GameplayStatics.get_player_controller(w,0)
        if not p or not pc:return
        if not s.get('staged'):
            pc.get_hud().set_editor_property('show_hud',False)
            for a in u.GameplayStatics.get_all_actors_of_class(w,u.Character):
                if a!=p:a.set_actor_tick_enabled(False);a.get_component_by_class(u.CharacterMovementComponent).disable_movement()
                if a.get_class().get_name()=='BP_TeddyBoss_C':s['boss']=a
            p.call_method('TouchAim',(.515,-.857));s['staged']=True
        mesh=s['boss'].get_component_by_class(u.SkeletalMeshComponent)
        if s['stage']==0:
            if u.GameplayStatics.get_time_seconds(w)<5:return
            name,t=samples[s['index']];mesh.play_animation(u.load_asset('/Game/TeddyEncounter/Teddy/'+name+'/A_Teddy_'+name),False);mesh.set_play_rate(0);mesh.set_position(t,False)
            for c in s['boss'].get_components_by_class(u.StaticMeshComponent):
                if 'AttackWarning' in c.get_name():c.set_visibility(name=='Attack',False)
            u.AutomationLibrary.finish_loading_before_screenshot();s['ready']=wall;s['stage']=1
        elif s['stage']==1 and wall-s['ready']>.8:
            u.GameplayStatics.set_game_paused(w,True);s['held']=pose(mesh,pc);s['ready']=wall;s['stage']=2;s['held_samples']=0
        elif s['stage'] in (2,3):
            # Stringified structs contain allocation addresses; compare numeric transforms only.
            now=pose(mesh,pc)
            for key in ['animation_time','root','foot_L','foot_R','head','hand_L','hand_R']:assert now[key]==s['held'][key],key
            s['held_samples']+=1
            if s['stage']==2 and wall-s['ready']>.6:
                name,t=samples[s['index']];s['image']=OUT/f'{s["index"]+1:02}-{name}-{t:.2f}.png';assert not s['image'].exists()
                u.SystemLibrary.execute_console_command(w,'HighResShot 1280x720 filename="'+s['image'].as_posix()+'"',pc);s['stage']=3
            elif s['stage']==3 and s['image'].exists():
                try:v=decode_png(s['image'])
                except:return
                r['samples'].append({'clip':samples[s['index']][0],'time':samples[s['index']][1],'pose':s['held'],'held_samples':s['held_samples'],'png':str(s['image']),'validation':v});s['index']+=1
                if s['index']==len(samples):finish();return
                u.GameplayStatics.set_game_paused(w,False);s['stage']=0
    except Exception:finish(traceback.format_exc())
try:
    u.EditorPythonScripting.set_keep_python_script_alive(True);assert lev.load_level('/Game/Maps/TeddyEncounter');lev.editor_request_begin_play();handle=u.register_slate_post_tick_callback(tick)
except Exception:finish(traceback.format_exc())
