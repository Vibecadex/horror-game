"""Bounded input causality and held-state gameplay capture; no starter assets edited."""
from pathlib import Path
import os,sys,json,time,math,traceback
import unreal as u
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'tools'))
from png_evidence import decode_png
OUT=Path(os.environ['TEDDY_TEST_DIR']); MAP='/Game/SetupValidation/Evidence_20261004/StarterEvidence'
lev=u.get_editor_subsystem(u.LevelEditorSubsystem); ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
r={'passed':False,'checks':{},'phases':{},'map':MAP,'engine':u.SystemLibrary.get_engine_version(),'physical_device_verified':False,'input_method':'Enhanced Input actions; separate no-input, movement, aim, fire and dash windows','images':[]}
s={'wall':time.monotonic(),'stage':0,'finished':False,'projectiles':{}}; handle=None
def vec(v): return [v.x,v.y,v.z]
def snap(p,pc):
    cm=pc.player_camera_manager
    return {'pawn':vec(p.get_actor_location()),'yaw':p.get_actor_rotation().yaw,'camera':vec(cm.get_camera_location()),'camera_rotation':[cm.get_camera_rotation().pitch,cm.get_camera_rotation().yaw,cm.get_camera_rotation().roll],'fov':cm.get_fov_angle()}
def finish(error=None):
    if s['finished']:return
    s['finished']=True
    if error:r['error']=error
    r['passed']=not error and all(r['checks'].values()); r['wall_seconds']=time.monotonic()-s['wall']
    (OUT/'receipt.json').write_text(json.dumps(r,indent=2))
    from finish_editor import finish_editor
    finish_editor(handle)
def tick(dt):
    try:
        now=time.monotonic()
        if now-s['wall']>160:raise RuntimeError('Evidence timed out')
        w=ed.get_game_world()
        if not w:return
        p=u.GameplayStatics.get_player_pawn(w,0); pc=u.GameplayStatics.get_player_controller(w,0)
        if not p or not pc:return
        game=u.GameplayStatics.get_time_seconds(w)
        if 'start' not in s:
            s['start']=game
            s['input']=next(x for x in u.ObjectIterator(u.EnhancedInputLocalPlayerSubsystem) if x.get_world()==w)
            s['actions']={n:u.load_asset('/Game/Variant_TwinStick/Input/Actions/IA_Action_'+n) for n in ['Move','MouseAim','StickAim','Fire','Dash']}
            s['projectile']=u.EditorAssetLibrary.load_blueprint_class('/Game/Variant_TwinStick/Blueprints/BP_TwinStickProjectile')
            r['checks']['possession']=p.get_controller()==pc
            r['world']=w.get_path_name()
            r['rendering']={k:u.SystemLibrary.get_console_variable_int_value(k) for k in ['r.Shadow.Virtual.Enable','r.DynamicGlobalIlluminationMethod','r.ReflectionMethod','r.DefaultFeature.AutoExposure','sg.ShadowQuality','sg.PostProcessQuality','r.ScreenPercentage']}
        elapsed=game-s['start']
        def inject(n,x,y=0):s['input'].inject_input_vector_for_action(s['actions'][n],u.Vector(x,y,0),[],[])
        def phase(name):r['phases'][name]=dict(snap(p,pc),game_time=game)
        if s['stage']==0 and elapsed>2:
            phase('no_input_start');s['stage']=1
        elif s['stage']==1 and elapsed>3:
            phase('no_input_end');s['stage']=2;s['phase_start']=game
        elif s['stage']==2:
            inject('Move',1)
            if game-s['phase_start']>0.6:phase('move_end');s['stage']=3;s['phase_start']=game
        elif s['stage']==3:
            inject('StickAim',1,0)
            if game-s['phase_start']>0.7:phase('aim_180');s['stage']=4;s['phase_start']=game
        elif s['stage']==4:
            inject('StickAim',0,1)
            if game-s['phase_start']>0.7:phase('aim_90');s['stage']=5;s['phase_start']=game
        elif s['stage']==5:
            # Stock stick aiming also auto-fires. Let those shots expire before fire-only attribution.
            pc.set_editor_property('show_mouse_cursor',True)
            if not s.get('mouse_fire_context'):
                s['input'].add_mapping_context(u.load_asset('/Game/Variant_TwinStick/Input/IMC_TwinStick_MouseShoot'),1,u.ModifyContextOptions())
                s['mouse_fire_context']=True
                r['mouse_fire_context']='Explicitly activated the shipped IMC_TwinStick_MouseShoot before fire-only phase'
            if game-s['phase_start']>3:
                # Move to the starter's open floor so nearby obstacles cannot consume a shot between frames.
                p.set_actor_location(u.Vector(700,1500,100),False,False)
                p.set_actor_rotation(u.Rotator(0,0,0),False)
                p.call_method('TouchAim',(1.,0.))
                pc.set_editor_property('show_mouse_cursor',False)
                phase('fire_start'); s['before_shots']={x.get_path_name() for x in u.GameplayStatics.get_all_actors_of_class(w,s['projectile'])};s['stage']=6;s['phase_start']=game
        elif s['stage']==6:
            inject('Fire',1)
            for x in u.GameplayStatics.get_all_actors_of_class(w,s['projectile']):
                if x.get_path_name() not in s['before_shots']:
                    d=(x.get_actor_location()-p.get_actor_location()).length()
                    s['projectiles'][x.get_path_name()]={'distance_at_first_observation':d,'owner':str(x.get_owner()),'instigator':str(x.get_instigator()),'yaw_error':abs((x.get_actor_rotation().yaw-p.get_actor_rotation().yaw+180)%360-180)}
            if game-s['phase_start']>0.6:phase('fire_end');s['stage']=7;s['phase_start']=game
        elif s['stage']==7:
            inject('Move',-1)
            if game-s['phase_start']>0.25:phase('dash_start');s['stage']=8;s['phase_start']=game;inject('Dash',1)
        elif s['stage']==8:
            s['dash_speed']=max(s.get('dash_speed',0),p.get_velocity().length())
            if game-s['phase_start']>0.3:phase('dash_end');s['stage']=9;s['phase_start']=game
        elif s['stage']==9 and game-s['phase_start']>1:
            u.AutomationLibrary.finish_loading_before_screenshot()
            u.GameplayStatics.set_game_paused(w,True)
            s['hold_time']=now;s['hold']=snap(p,pc);s['held_samples']=0;s['stage']=10
            r['capture_contract']={'method':'World paused; pawn and gameplay camera sampled every Slate tick across warmup, request and full PNG completion','loading_barrier':'AutomationLibrary.finish_loading_before_screenshot','additional_paused_history_warmup_seconds':3,'exact_dynamic_frame_identity_claimed':False,'held_state':s['hold']}
        elif s['stage']>=10:
            current=snap(p,pc)
            assert current==s['hold'], 'Camera/pawn changed during held capture'
            s['held_samples']+=1
            if s['stage']==10 and now-s['hold_time']>3:
                s['image']=OUT/'starter-held.png';assert not s['image'].exists();s['requested']=now
                u.SystemLibrary.execute_console_command(w,f'HighResShot 1280x720 filename="{s["image"].as_posix()}"',pc);s['stage']=11
            elif s['stage']==11 and s['image'].exists():
                try: valid=decode_png(s['image'])
                except Exception:
                    if now-s['requested']>15:raise
                    return
                r['images']=[dict(path=str(s['image']),**valid)];r['capture_contract']['held_samples']=s['held_samples']
                ph=r['phases']; movement=[b-a for a,b in zip(ph['no_input_end']['pawn'],ph['move_end']['pawn'])]
                r['movement_delta']=movement;r['new_projectiles']=s['projectiles'];r['dash_peak_speed']=s.get('dash_speed',0)
                r['checks']['no_input_stationary']=math.dist(ph['no_input_start']['pawn'],ph['no_input_end']['pawn'])<2
                r['checks']['mapped_move_positive_x']=movement[0]>100 and abs(movement[1])<20
                for label,expected in [('aim_180',180),('aim_90',90)]:r['checks'][label]=abs((ph[label]['yaw']-expected+180)%360-180)<5
                r['checks']['fire_new_player_origin_projectiles']=any(v['distance_at_first_observation']<350 and v['yaw_error']<5 for v in s['projectiles'].values())
                r['projectile_attribution']='New names during fire-only phase, spawned near player in player facing direction; stock owner/instigator values recorded separately'
                r['checks']['dash_faster_than_walk']=s.get('dash_speed',0)>900 and math.dist(ph['dash_start']['pawn'],ph['dash_end']['pawn'])>100
                r['checks']['held_complete_png']=True
                finish()
    except Exception:finish(traceback.format_exc())
try:
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    assert lev.load_level(MAP)
    lev.editor_request_begin_play();handle=u.register_slate_post_tick_callback(tick)
except Exception:finish(traceback.format_exc())
