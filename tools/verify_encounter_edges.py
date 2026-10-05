"""Mapped cursor aiming, collision, evasion/invulnerability, player defeat and pause HUD proof."""
import sys,os,time,json,traceback,math
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from png_evidence import decode_png
from finish_editor import finish_editor
OUT=Path(os.environ['TEDDY_TEST_DIR']);lev=u.get_editor_subsystem(u.LevelEditorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
r={'passed':False,'checks':{},'physical_device_verified':False,'method':'Enhanced Input action injection; cursor positioning through PlayerController; staged positions; one explicitly labelled damage call inside dodge window','images':[]}
s={'wall':time.monotonic(),'stage':0,'finished':False};handle=None
def pos(a):v=a.get_actor_location();return[v.x,v.y,v.z]
def prop(a,n):return a.get_editor_property(n)
def finish(error=None):
    if s['finished']:return
    s['finished']=True;r['passed']=not error and all(r['checks'].values())
    if error:r['error']=error
    (OUT/'receipt.json').write_text(json.dumps(r,indent=2,default=str));finish_editor(handle)
def tick(dt):
    try:
        wall=time.monotonic()
        if wall-s['wall']>180:raise RuntimeError('Edge test timeout at '+str(s['stage']))
        w=ed.get_game_world()
        if not w:return
        p=u.GameplayStatics.get_player_pawn(w,0);pc=u.GameplayStatics.get_player_controller(w,0)
        if not p or not pc:return
        bosses=u.GameplayStatics.get_all_actors_of_class(w,s['bossclass'])
        if not bosses:return
        b=bosses[0];game=u.GameplayStatics.get_time_seconds(w)
        inp=next(x for x in u.ObjectIterator(u.EnhancedInputLocalPlayerSubsystem) if x.get_world()==w)
        def inject(name,x,y=0):inp.inject_input_vector_for_action(s['actions'][name],u.Vector(x,y,0),[],[])
        def advance(n):s['stage']=n;s['t']=game;s['wall_t']=wall
        def place(loc):p.get_component_by_class(u.CharacterMovementComponent).stop_movement_immediately();p.set_actor_location(loc,False,False)
        def screenshot(name):
            s['image']=OUT/(name+'.png');u.SystemLibrary.execute_console_command(w,'HighResShot 1280x720 filename="'+s['image'].as_posix()+'"',pc)
        def image_complete():
            if not s['image'].exists():return False
            try:v=decode_png(s['image'])
            except:return False
            v.pop('chunks',None);r['images'].append({'path':str(s['image']),'validation':v});return True
        if s['stage']==0:
            for a in u.GameplayStatics.get_all_actors_of_class(w,u.Character):
                if a!=p:a.set_actor_tick_enabled(False);a.get_component_by_class(u.CharacterMovementComponent).disable_movement()
            minions=u.GameplayStatics.get_all_actors_of_class(w,s['minionclass'])
            r['saved_defaults']={'boss_speed':prop(b,'Speed'),'boss_health':prop(b,'Health'),'minions':[{'health':prop(a,'Health'),'speed':prop(a,'Speed'),'position':pos(a)} for a in minions]}
            r['checks']['three_stitchlings_with_own_health']=len(minions)==3 and all(prop(a,'Health')==24 for a in minions)
            r['checks']['walk_speed_matches_animation']=prop(b,'Speed')==105
            r['warning_components']=[{'mesh':str(c.static_mesh),'collision':str(c.get_collision_enabled())} for c in b.get_components_by_class(u.StaticMeshComponent)]
            advance(1)
        elif s['stage']==1 and game-s['t']>2:
            place(u.Vector(-1250,0,95));advance(2)
        elif s['stage']==2:
            inject('Move',-1)
            if game-s['t']>1:
                r['walk_wall_position']=pos(p);r['checks']['walk_blocked_by_arena_wall']=-1365<pos(p)[0]<-1310;inject('Dash',1);advance(3)
        elif s['stage']==3:
            inject('Move',-1)
            if game-s['t']>.4:
                r['dash_wall_position']=pos(p);r['checks']['dash_does_not_tunnel_wall']=pos(p)[0]>-1365
                place(u.Vector(-230,570,95));advance(4)
        elif s['stage']==4 and game-s['t']>.8:
            rifle=next(c for c in p.get_components_by_class(u.StaticMeshComponent) if c.get_name()=='ServiceRifle')
            forward=rifle.get_forward_vector();aim=p.get_actor_forward_vector();dot=forward.x*aim.x+forward.y*aim.y+forward.z*aim.z
            r['rifle_forward_dot_aim']=dot;r['checks']['rifle_forward_agrees_with_aim']=dot>.9
            # Cursor targets the floor beyond the boss, so the stock visibility trace has a stable target.
            target=u.Vector(800,-400,1);screen=pc.project_world_location_to_screen(target,False)
            if isinstance(screen,tuple):screen=next(x for x in screen if isinstance(x,u.Vector2D))
            assert screen is not None;pc.set_mouse_location(int(screen.x),int(screen.y));pc.set_editor_property('show_mouse_cursor',True);inject('MouseAim',1,1);s['target']=target;r['mouse_screen']=[screen.x,screen.y];advance(5)
        elif s['stage']==5:
            inject('MouseAim',1,1)
            if game-s['t']>.7:
                d=s['target']-p.get_actor_location();expected=math.degrees(math.atan2(d.y,d.x));actual=p.get_actor_rotation().yaw;r['mouse_aim']={'expected':expected,'actual':actual,'wrapped_error':abs((actual-expected+180)%360-180)};r['checks']['mouse_cursor_aims_at_projected_world_target']=r['mouse_aim']['wrapped_error']<8
                place(b.get_actor_location()+u.Vector(-300,0,-142));p.call_method('TouchAim',(1.,0.));b.set_actor_tick_enabled(True);b.get_component_by_class(u.CharacterMovementComponent).set_movement_mode(u.MovementMode.MOVE_WALKING);s['before_evade']=prop(p,'Health');advance(6)
        elif s['stage']==6:
            if prop(b,'State')==1 and prop(b,'StateAge')>.70:inject('Move',-1);inject('Dash',1);s['attacks_before']=prop(b,'Attacks');advance(7)
        elif s['stage']==7:
            inject('Move',-1)
            if game<prop(p,'DodgeUntil') and not s.get('inv_checked'):
                before=prop(p,'Health');u.GameplayStatics.apply_damage(p,10,None,b,u.DamageType);r['checks']['dodge_invulnerability_blocks_damage']=prop(p,'Health')==before;s['inv_checked']=True
            if prop(b,'Attacks')>s['attacks_before']:
                r['checks']['evades_actual_boss_strike']=prop(p,'Health')==s['before_evade'];r['evade_end']={'player':pos(p),'boss':pos(b),'health':prop(p,'Health')};advance(8)
        elif s['stage']==8 and game-s['t']>.6:
            place(b.get_actor_location()+u.Vector(-300,0,-142));s['death_start']=game;advance(9)
        elif s['stage']==9:
            if prop(p,'Health')<=0:
                r['checks']['boss_attacks_can_defeat_player']=True;r['attacks_to_defeat']=prop(b,'Attacks');s['dead_pos']=pos(p);s['shots_before']={a.get_path_name() for a in u.GameplayStatics.get_all_actors_of_class(w,s['projectile'])};advance(10)
            elif game-s['t']>18:raise RuntimeError('Player defeat did not occur')
        elif s['stage']==10:
            inject('Move',1);inject('Fire',1)
            if game-s['t']>.6:
                r['checks']['defeated_player_cannot_move']=math.dist(s['dead_pos'],pos(p))<2;r['checks']['defeated_player_cannot_fire']=not ({a.get_path_name() for a in u.GameplayStatics.get_all_actors_of_class(w,s['projectile'])}-s['shots_before']);screenshot('player-defeat');advance(11)
        elif s['stage']==11 and image_complete():
            s['old_world']=w;inject('Restart',1);advance(12)
        elif s['stage']==12:
            if w!=s['old_world'] or game<s['t']:
                minions=u.GameplayStatics.get_all_actors_of_class(w,s['minionclass']);r['checks']['restart_from_player_defeat']=prop(p,'Health')==100 and prop(b,'Health')==300 and len(minions)==3 and all(prop(a,'Health')==24 for a in minions);advance(13)
        elif s['stage']==13 and game-s['t']>1:
            inject('Pause',1);advance(14)
        elif s['stage']==14 and wall-s['wall_t']>.5:
            r['checks']['pause_action_after_restart']=u.GameplayStatics.is_game_paused(w);screenshot('paused');advance(15)
        elif s['stage']==15 and image_complete():finish()
    except Exception:finish(traceback.format_exc())
try:
    u.EditorPythonScripting.set_keep_python_script_alive(True);assert lev.load_level('/Game/Maps/TeddyEncounter')
    s['bossclass']=u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_TeddyBoss');s['minionclass']=u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_Stitchling');s['projectile']=u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_EncounterProjectile')
    s['actions']={n:u.load_asset('/Game/Variant_TwinStick/Input/Actions/IA_Action_'+n) for n in ['Move','MouseAim','Fire','Dash']};s['actions'].update({n:u.load_asset('/Game/TeddyEncounter/Input/IA_'+n) for n in ['Pause','Restart']})
    lev.editor_request_begin_play();handle=u.register_slate_post_tick_callback(tick)
except Exception:finish(traceback.format_exc())
