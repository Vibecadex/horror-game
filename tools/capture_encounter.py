"""Three held gameplay plates at saved rendering settings, with complete image evidence."""
import sys,os,time,json,traceback,statistics,math
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from png_evidence import decode_png
OUT=Path(os.environ['TEDDY_TEST_DIR']);lev=u.get_editor_subsystem(u.LevelEditorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
s={'wall':time.monotonic(),'stage':0,'index':0,'finished':False,'frame_ms':[]};h=None
r={'passed':False,'map':'/Game/Maps/TeddyEncounter','engine':u.SystemLibrary.get_engine_version(),'captures':[],'physical_device_verified':False}
positions=[(-230,570,95),(-550,-650,95),(-100,650,95)]
def snap(p,pc):
    v=p.get_actor_location();cm=pc.player_camera_manager;c=cm.get_camera_location();rot=cm.get_camera_rotation()
    return {'pawn':[v.x,v.y,v.z],'yaw':p.get_actor_rotation().yaw,'camera':[c.x,c.y,c.z],'rotation':[rot.pitch,rot.yaw,rot.roll],'fov':cm.get_fov_angle()}
def end(error=None):
    if s['finished']:return
    s['finished']=True;r['passed']=not error and len(r['captures'])==3
    if error:r['error']=error
    if s['frame_ms']:r['frame_timing_ms']={'samples':len(s['frame_ms']),'median':statistics.median(s['frame_ms']),'p95':sorted(s['frame_ms'])[int(len(s['frame_ms'])*.95)]}
    (OUT/'receipt.json').write_text(json.dumps(r,indent=2))
    from finish_editor import finish_editor
    finish_editor(h)
def tick(dt):
    try:
        now=time.monotonic()
        if now-s['wall']>200:raise RuntimeError('Capture timeout')
        w=ed.get_game_world()
        if not w:return
        p=u.GameplayStatics.get_player_pawn(w,0);pc=u.GameplayStatics.get_player_controller(w,0)
        if not p or not pc:return
        if not s.get('frozen'):
            hud=pc.get_hud()
            if hud:hud.set_editor_property('show_hud',False)
            r['hud']='Hidden only for static reference plates, to exclude pause overlay during held-state capture; gameplay recording retains HUD'
            for a in u.GameplayStatics.get_all_actors_of_class(w,u.Character):
                if a!=p:
                    a.set_actor_tick_enabled(False);a.get_component_by_class(u.CharacterMovementComponent).disable_movement()
                    mesh=a.get_component_by_class(u.SkeletalMeshComponent);mesh.play_animation(u.load_asset('/Game/TeddyEncounter/Teddy/Idle/A_Teddy_Idle'),True)
            s['frozen']=True
        if s['stage']==0:
            if u.GameplayStatics.get_time_seconds(w)<7:return
            r['world']=w.get_path_name();r['pawn_class']=p.get_class().get_path_name()
            r['actors']=[a.get_class().get_path_name() for a in u.GameplayStatics.get_all_actors_of_class(w,u.Actor)]
            p.get_component_by_class(u.CharacterMovementComponent).stop_movement_immediately()
            p.set_actor_location(u.Vector(*positions[s['index']]),False,False)
            direction=u.Vector(250,-230,95)-p.get_actor_location();magnitude=max(1,math.hypot(direction.x,direction.y));yaw=math.degrees(math.atan2(direction.y,direction.x))
            p.call_method('TouchAim',(direction.x/magnitude,direction.y/magnitude))
            p.set_actor_rotation(u.Rotator(yaw=yaw),False)
            if os.environ.get('TEDDY_EXPOSURE_SWEEP'):
                for ppactor in u.GameplayStatics.get_all_actors_of_class(w,u.PostProcessVolume):
                    pp=ppactor.settings;pp.set_editor_property('auto_exposure_bias',[3.,4.5,6.][s['index']]);ppactor.set_editor_property('settings',pp)
            # Hold a review composition; this staging is separate from input verification.
            for a in u.GameplayStatics.get_all_actors_of_class(w,u.Character):
                if a!=p:a.set_actor_tick_enabled(False);a.get_component_by_class(u.CharacterMovementComponent).disable_movement()
            u.AutomationLibrary.finish_loading_before_screenshot();s['ready']=now;s['stage']=1
            r['postprocess']=[]
            for a in u.GameplayStatics.get_all_actors_of_class(w,u.PostProcessVolume):
                pp=a.settings;r['postprocess'].append({k:str(pp.get_editor_property(k)) for k in ['auto_exposure_method','auto_exposure_bias','auto_exposure_apply_physical_camera_exposure','vignette_intensity','bloom_intensity','motion_blur_amount']})
            r['rendering']={k:u.SystemLibrary.get_console_variable_int_value(k) for k in ['r.Shadow.Virtual.Enable','r.DynamicGlobalIlluminationMethod','r.ReflectionMethod','sg.ShadowQuality','sg.PostProcessQuality']}
        elif s['stage']==1:
            s['frame_ms'].append(dt*1000)
            if now-s['ready']>3:
                u.GameplayStatics.set_game_paused(w,True);s['hold']=snap(p,pc);s['ready']=now;s['samples']=0;s['stage']=2
        elif s['stage'] in (2,3):
            assert snap(p,pc)==s['hold'],'Held camera/pawn drift'
            s['samples']+=1
            if s['stage']==2 and now-s['ready']>2:
                s['image']=OUT/f'position-{s["index"]+1:02}.png';assert not s['image'].exists();s['requested']=now
                u.SystemLibrary.execute_console_command(w,f'HighResShot 1280x720 filename="{s["image"].as_posix()}"',pc);s['stage']=3
            elif s['stage']==3 and s['image'].exists():
                try:validation=decode_png(s['image'])
                except Exception:
                    if now-s['requested']>20:raise
                    return
                validation.pop('chunks',None)
                r['captures'].append({'path':str(s['image']),'held_state':s['hold'],'held_samples':s['samples'],'game_time':u.GameplayStatics.get_time_seconds(w),'validation':validation})
                s['index']+=1
                if s['index']==3:end();return
                u.GameplayStatics.set_game_paused(w,False);s['stage']=0
    except Exception:end(traceback.format_exc())
try:
    u.EditorPythonScripting.set_keep_python_script_alive(True);assert lev.load_level(r['map']);lev.editor_request_begin_play();h=u.register_slate_post_tick_callback(tick)
except Exception:end(traceback.format_exc())
