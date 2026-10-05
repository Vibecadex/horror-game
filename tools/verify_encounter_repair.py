"""Independent read-only gameplay probe. Only transient PIE state is exercised."""
from pathlib import Path
import sys,os,time,json,math,traceback
import unreal as u
ROOT=Path(r'C:\Projects\to-deploy\horror-game');sys.path.insert(0,str(ROOT/'tools'))
from png_evidence import decode_png
OUT=Path(os.environ['TEDDY_TEST_DIR']);OUT.mkdir(exist_ok=True)
editor=u.get_editor_subsystem(u.UnrealEditorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
result={'map':'/Game/Maps/TeddyEncounter','independent_qa':True,'input_method':'Enhanced Input actions in a fresh PIE instance; physical keys not verified','staging':'No teleporting, health editing, asset saving or AI disabling. World paused temporarily for held screenshots.','checks':{},'states':[],'captures':[]}
state={'stage':0,'start':time.monotonic(),'done':False,'capture':None};callback=None
actions={n:u.load_asset('/Game/Variant_TwinStick/Input/Actions/IA_Action_'+n) for n in ['Move','StickAim','Fire','Dash']}
actions.update({n:u.load_asset('/Game/TeddyEncounter/Input/IA_'+n) for n in ['Pause','Restart']})
boss_class=u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_TeddyBoss')
shot_class=u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_EncounterProjectile')

def position(a):
    v=a.get_actor_location();return [v.x,v.y,v.z]
def snapshot(w,p,pc,b,label):
    cm=pc.player_camera_manager;rot=cm.get_camera_rotation()
    row={'label':label,'wall_seconds':time.monotonic()-state['start'],'game_seconds':u.GameplayStatics.get_time_seconds(w),'pawn':position(p),'yaw':p.get_actor_rotation().yaw,'health':p.get_editor_property('Health'),'boss':position(b),'boss_health':b.get_editor_property('Health'),'boss_state':b.get_editor_property('State'),'camera':position(cm),'camera_rotation':[rot.pitch,rot.yaw,rot.roll],'fov':cm.get_fov_angle(),'paused':u.GameplayStatics.is_game_paused(w)}
    # Camera manager actor location is not necessarily the view location.
    v=cm.get_camera_location();row['camera']=[v.x,v.y,v.z]
    result['states'].append(row);return row
def advance(stage,w):
    state['stage']=stage;state['phase_time']=u.GameplayStatics.get_time_seconds(w);state['phase_wall']=time.monotonic()
def inject(sub,name,x=1,y=0):sub.inject_input_vector_for_action(actions[name],u.Vector(x,y,0),[],[])
def begin_capture(w,p,pc,b,label,next_stage,hide_hud=False):
    u.GameplayStatics.set_game_paused(w,True)
    if hide_hud and pc.get_hud():pc.get_hud().set_editor_property('show_hud',False)
    state['capture']={'label':label,'path':OUT/(label+'.png'),'start':time.monotonic(),'next':next_stage,'hide_hud':hide_hud,'held':snapshot(w,p,pc,b,label+'-held')}
def finish(error=None):
    if state['done']:return
    state['done']=True
    if error:result['error']=error
    result['passed']=not error and bool(result['checks']) and all(result['checks'].values())
    result['wall_seconds']=time.monotonic()-state['start']
    (OUT/'receipt.json').write_text(json.dumps(result,indent=2,default=str))
    from finish_editor import finish_editor
    finish_editor(callback)

def tick(dt):
    try:
        now=time.monotonic()
        if now-state['start']>140:raise RuntimeError('Independent QA timeout at stage '+str(state['stage']))
        world=editor.get_game_world()
        if not world:return
        pawn=u.GameplayStatics.get_player_pawn(world,0);pc=u.GameplayStatics.get_player_controller(world,0)
        bosses=u.GameplayStatics.get_all_actors_of_class(world,boss_class)
        if not pawn or not pc or not bosses:return
        boss=next((a for a in bosses if a.get_class()==boss_class),bosses[0])
        sub=next(a for a in u.ObjectIterator(u.EnhancedInputLocalPlayerSubsystem) if a.get_world()==world)
        t=u.GameplayStatics.get_time_seconds(world)
        if state['capture']:
            cap=state['capture']
            assert u.GameplayStatics.is_game_paused(world)
            assert math.dist(cap['held']['pawn'],position(pawn))<.01
            if now-cap['start']>.7 and not cap.get('requested'):
                assert not cap['path'].exists();u.SystemLibrary.execute_console_command(world,'HighResShot 1280x720 filename="'+cap['path'].as_posix()+'"',pc);cap['requested']=now
            if cap.get('requested') and cap['path'].exists():
                try:decoded=decode_png(cap['path'])
                except Exception:
                    if now-cap['requested']>15:raise
                    return
                decoded.pop('chunks',None);result['captures'].append({'path':str(cap['path']),'validation':decoded,'state':cap['held'],'hud_hidden':cap['hide_hud']})
                if cap['hide_hud'] and pc.get_hud():pc.get_hud().set_editor_property('show_hud',True)
                u.GameplayStatics.set_game_paused(world,False);advance(cap['next'],world);state['capture']=None
            return
        stage=state['stage'];elapsed=t-state.get('phase_time',t)
        if stage==0:
            if t<2:return
            result['engine']=u.SystemLibrary.get_engine_version();result['viewport']=list(pc.get_viewport_size());result['pawn_class']=pawn.get_class().get_path_name()
            context=u.load_asset('/Game/TeddyEncounter/Input/IMC_Encounter')
            result['saved_bindings']=[{'key':str(u.InputLibrary.key_get_display_name(m.key)),'action':m.action.get_name() if m.action else None,'modifiers':[a.get_class().get_name() for a in m.modifiers]} for m in context.get_editor_property('default_key_mappings').get_editor_property('mappings')]
            state['idle']=snapshot(world,pawn,pc,boss,'no-input-before');advance(1,world)
        elif stage==1 and elapsed>.45:
            result['checks']['no_input_stationary']=math.dist(position(pawn),state['idle']['pawn'])<1
            begin_capture(world,pawn,pc,boss,'01-initial-composition',2,True)
        elif stage==2:
            state['move_start']=snapshot(world,pawn,pc,boss,'move-before');advance(3,world)
        elif stage==3:
            inject(sub,'Move',1);inject(sub,'StickAim',0,1)
            if elapsed>.55:
                row=snapshot(world,pawn,pc,boss,'move-and-independent-aim')
                result['movement_distance']=math.dist(row['pawn'],state['move_start']['pawn'])
                result['checks']['movement_responds']=result['movement_distance']>100
                result['checks']['aim_independent_of_movement']=abs((row['yaw']-90+180)%360-180)<10
                state['shot_ids']={a.get_path_name() for a in u.GameplayStatics.get_all_actors_of_class(world,shot_class)};state['new_owned_shots']=set();state['boss_health']=boss.get_editor_property('Health');advance(4,world)
        elif stage==4:
            d=boss.get_actor_location()-pawn.get_actor_location();length=max(1,math.hypot(d.x,d.y));inject(sub,'StickAim',-d.x/length,d.y/length);inject(sub,'Fire')
            for shot in u.GameplayStatics.get_all_actors_of_class(world,shot_class):
                if shot.get_path_name() not in state['shot_ids'] and shot.get_owner()==pawn and shot.get_instigator()==pawn:state['new_owned_shots'].add(shot.get_path_name())
            if elapsed>1.1:
                result['checks']['firing_creates_player_owned_shots']=bool(state['new_owned_shots']);result['owned_projectiles_observed']=len(state['new_owned_shots']);result['boss_health_before_fire']=state['boss_health'];result['boss_health_after_fire']=boss.get_editor_property('Health')
                begin_capture(world,pawn,pc,boss,'02-after-firing',5,False)
        elif stage==5:
            inject(sub,'Move',-1);state['dash_start']=position(pawn);state['dash_peak']=0;inject(sub,'Dash');advance(6,world)
        elif stage==6:
            state['dash_peak']=max(state['dash_peak'],pawn.get_velocity().length())
            if elapsed>.28:
                result['dash_peak_speed']=state['dash_peak'];result['dash_distance']=math.dist(position(pawn),state['dash_start'])
                result['checks']['dash_accelerates']=state['dash_peak']>900 and result['dash_distance']>120
                snapshot(world,pawn,pc,boss,'after-dash');inject(sub,'Pause');advance(7,world)
        elif stage==7:
            if now-state['phase_wall']>.6:
                result['checks']['pause_action_freezes_time']=u.GameplayStatics.is_game_paused(world) and elapsed<.05
                snapshot(world,pawn,pc,boss,'input-pause');inject(sub,'Pause',0);advance(8,world)
        elif stage==8:
            if now-state['phase_wall']>.12:inject(sub,'Pause');advance(9,world)
        elif stage==9:
            if elapsed>.25:
                result['checks']['pause_action_resumes_time']=not u.GameplayStatics.is_game_paused(world)
                state['old_world']=world;inject(sub,'Restart');advance(10,world)
        elif stage==10:
            if world!=state['old_world']:
                result['checks']['restart_action_restores_health']=pawn.get_editor_property('Health')==100 and boss.get_editor_property('Health')==300
                snapshot(world,pawn,pc,boss,'restart');advance(11,world)
        elif stage==11 and elapsed>.5:begin_capture(world,pawn,pc,boss,'03-after-restart',12,False)
        elif stage==12:finish()
    except Exception:finish(traceback.format_exc())

try:
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    assert levels.load_level(result['map']);levels.editor_request_begin_play();callback=u.register_slate_post_tick_callback(tick)
except Exception:finish(traceback.format_exc())
