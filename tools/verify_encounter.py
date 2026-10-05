"""Frame-driven runtime acceptance for saved encounter Blueprints. No physical-device claim."""
import sys,os,time,json,traceback,math,statistics
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.environ['TEDDY_TEST_DIR']);sys.path.insert(0,str(ROOT/'tools'))
from png_evidence import decode_png
lev=u.get_editor_subsystem(u.LevelEditorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
r={'passed':False,'checks':{},'phases':{},'physical_device_verified':False,'input_method':'Enhanced Input action injection including pause/restart; staging teleports isolate phases','map':'/Game/Maps/TeddyEncounter'}
s={'wall':time.monotonic(),'stage':0,'finished':False,'shots':{},'frames':[],'restart_count':0};handle=None
def pos(a):v=a.get_actor_location();return[v.x,v.y,v.z]
def prop(a,n):return a.get_editor_property(n)
def finish(err=None):
    if s['finished']:return
    s['finished']=True
    if err:r['error']=err
    r['passed']=not err and len(r['checks'])>0 and all(r['checks'].values());r['wall_seconds']=time.monotonic()-s['wall'];r['shots']=s['shots'];r['restarts']=s['restart_count']
    if s['frames']:r['frame_ms']={'median':statistics.median(s['frames']),'p95':sorted(s['frames'])[int(.95*len(s['frames']))],'samples':len(s['frames'])}
    (OUT/'receipt.json').write_text(json.dumps(r,indent=2,default=str))
    from finish_editor import finish_editor
    finish_editor(handle)
def tick(dt):
    try:
        wall=time.monotonic()
        if wall-s['wall']>230:raise RuntimeError('Encounter test timeout at stage '+str(s['stage']))
        w=ed.get_game_world()
        if not w:return
        p=u.GameplayStatics.get_player_pawn(w,0);pc=u.GameplayStatics.get_player_controller(w,0)
        if not p or not pc:return
        bosses=u.GameplayStatics.get_all_actors_of_class(w,s['bossclass'])
        if not bosses:return
        b=next((x for x in bosses if x.get_class()==s['bossclass']),bosses[0]);game=u.GameplayStatics.get_time_seconds(w)
        s['input']=next(x for x in u.ObjectIterator(u.EnhancedInputLocalPlayerSubsystem) if x.get_world()==w)
        def phase(name):r['phases'][name]={'time':game,'player':pos(p),'health':prop(p,'Health'),'boss':pos(b),'boss_health':prop(b,'Health'),'state':prop(b,'State'),'yaw':p.get_actor_rotation().yaw}
        def advance(stage):s['stage']=stage;s['t']=game
        def inject(n,x,y=0):s['input'].inject_input_vector_for_action(s['actions'][n],u.Vector(x,y,0),[],[])
        def aim():
            d=b.get_actor_location()-p.get_actor_location();m=max(1,math.hypot(d.x,d.y));inject('StickAim',-d.x/m,d.y/m)
        if s['stage']==0:
            s['input']=next(x for x in u.ObjectIterator(u.EnhancedInputLocalPlayerSubsystem) if x.get_world()==w)
            s['actions']={n:u.load_asset('/Game/Variant_TwinStick/Input/Actions/IA_Action_'+n) for n in ['Move','StickAim','Fire','Dash']}
            s['actions'].update({n:u.load_asset('/Game/TeddyEncounter/Input/IA_'+n) for n in ['Pause','Restart']})
            for a in u.GameplayStatics.get_all_actors_of_class(w,u.Character):
                if a!=p:a.set_actor_tick_enabled(False);a.get_component_by_class(u.CharacterMovementComponent).disable_movement()
            r['engine']=u.SystemLibrary.get_engine_version();r['viewport_dimensions']=list(pc.get_viewport_size());r['checks']['saved_map_and_possession']=p.get_controller()==pc and 'BP_EncounterPlayer' in p.get_class().get_name();advance(1)
        elif s['stage']==1 and game-s['t']>2:
            phase('no_input_start');advance(2)
        elif s['stage']==2 and game-s['t']>.6:
            phase('no_input_end');r['checks']['no_input_stationary']=math.dist(r['phases']['no_input_start']['player'],pos(p))<1;advance(3)
        elif s['stage']==3:
            inject('Move',1,0);inject('StickAim',0,1)
            if game-s['t']>.6:
                phase('move_aim');start=r['phases']['no_input_end']['player'];r['checks']['move_in_mapped_direction']=pos(p)[0]-start[0]>100 and abs(pos(p)[1]-start[1])<10;r['checks']['independent_aim_while_moving']=abs((p.get_actor_rotation().yaw-90+180)%360-180)<6;advance(4)
        elif s['stage']==4:
            aim()
            if game-s['t']>.5:
                phase('fire_start');s['before']={x.get_path_name() for x in u.GameplayStatics.get_all_actors_of_class(w,s['projectile'])};advance(5)
        elif s['stage']==5:
            aim();inject('Fire',1)
            for shot in u.GameplayStatics.get_all_actors_of_class(w,s['projectile']):
                if shot.get_path_name() not in s['before']:s['shots'][shot.get_path_name()]={'owner_is_player':shot.get_owner()==p,'instigator_is_player':shot.get_instigator()==p,'location':pos(shot)}
            if game-s['t']>1.5:
                phase('fire_end');r['checks']['fire_spawns_owned_projectiles']=any(x['owner_is_player'] and x['instigator_is_player'] for x in s['shots'].values());r['checks']['projectiles_damage_boss']=prop(b,'Health')<r['phases']['fire_start']['boss_health'];advance(6)
        elif s['stage']==6:
            inject('Move',-1,0)
            if game-s['t']>.2:
                phase('dash_start');inject('Dash',1);advance(7)
        elif s['stage']==7:
            s['dash_speed']=max(s.get('dash_speed',0),p.get_velocity().length())
            if game-s['t']>.28:
                phase('dash_end');r['checks']['dodge_displaces_player']=math.dist(r['phases']['dash_start']['player'],pos(p))>150 and s.get('dash_speed',0)>900
                # Stage near the boss to measure its actual telegraph and hit without human positioning noise.
                p.get_component_by_class(u.CharacterMovementComponent).stop_movement_immediately();p.set_actor_location(b.get_actor_location()+u.Vector(-300,0,-140),False,False)
                b.set_actor_tick_enabled(True);b.get_component_by_class(u.CharacterMovementComponent).set_movement_mode(u.MovementMode.MOVE_WALKING)
                phase('attack_wait');advance(8)
        elif s['stage']==8:
            state=prop(b,'State')
            if state==1 and 'telegraph_start' not in s:s['telegraph_start']=game;s['pre_strike_health']=prop(p,'Health')
            if prop(p,'Health')<r['phases']['attack_wait']['health']:
                phase('boss_strike');r['telegraph_seconds']=game-s.get('telegraph_start',game);r['checks']['telegraph_precedes_damage']=r['telegraph_seconds']>=.85;r['checks']['boss_attack_damages_player']=True
                b.set_actor_tick_enabled(False);advance(9)
            elif game-s['t']>8:raise RuntimeError('Boss did not land its telegraphed attack')
        elif s['stage']==9:
            if game-s['t']>.5:
                phase('pause_before');s['pause_wall']=wall;inject('Pause',1);advance(10)
        elif s['stage']==10:
            inject('Move',1);inject('Fire',1)
            if wall-s['pause_wall']>.65:
                r['checks']['pause_freezes_world']=u.GameplayStatics.is_game_paused(w) and abs(game-s['t'])<.04 and math.dist(r['phases']['pause_before']['player'],pos(p))<.1
                inject('Pause',1);advance(11)
        elif s['stage']==11:
            if game-s['t']>.3:
                r['checks']['unpause_resumes_time']=not u.GameplayStatics.is_game_paused(w);p.set_actor_location(b.get_actor_location()+u.Vector(-750,0,-140),False,False);advance(12)
        elif s['stage']==12:
            aim();inject('Fire',1)
            # Boss tick must run to process death state and animation but it cannot move during this firing fixture.
            if prop(b,'Health')<=0:
                phase('boss_defeated');r['checks']['boss_defeat_state']=prop(b,'State')==3;r['checks']['dead_boss_no_collision']=not b.get_actor_enable_collision();advance(13)
            elif game-s['t']>18:raise RuntimeError('Sustained firing did not defeat boss')
        elif s['stage']==13 and game-s['t']>.3:
            s['old_pawn']=p.get_path_name();s['old_world']=w;inject('Restart',1);s['restart_wall']=wall;advance(14)
        elif s['stage']==14:
            if w!=s['old_world'] or game<s['t']:
                s['restart_count']+=1;r['checks']['restart_resets_health_'+str(s['restart_count'])]=prop(p,'Health')==100 and prop(b,'Health')==300
                if s['restart_count']<2:advance(15)
                else:advance(16)
            elif wall-s['restart_wall']>20:raise RuntimeError('Restart did not load a fresh world')
        elif s['stage']==15 and game-s['t']>1:
            s['old_world']=w;inject('Restart',1);s['restart_wall']=wall;advance(14)
        elif s['stage']==16 and game-s['t']>1:finish()
        if 2<s['stage']<13 and not u.GameplayStatics.is_game_paused(w):s['frames'].append(dt*1000)
    except Exception:finish(traceback.format_exc())
try:
    u.EditorPythonScripting.set_keep_python_script_alive(True);assert lev.load_level(r['map']);s['bossclass']=u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_TeddyBoss');s['projectile']=u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_EncounterProjectile');lev.editor_request_begin_play();handle=u.register_slate_post_tick_callback(tick)
except Exception:finish(traceback.format_exc())
