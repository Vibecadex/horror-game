"""Actual unteleported encounter play, driven only by input actions after shader warmup.
Writes runtime PNGs; the host fully decodes/encodes them before signalling completion.
"""
import sys,os,time,json,traceback,math,struct,zlib,hashlib
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from finish_editor import finish_editor
OUT=Path(os.environ['TEDDY_TEST_DIR']);FRAMES=OUT/'frames';FRAMES.mkdir(exist_ok=True)
CAPTURE_INTERVAL=float(os.environ.get('TEDDY_CAPTURE_INTERVAL','.1'))
assert 1/240 <= CAPTURE_INTERVAL <= 1
lev=u.get_editor_subsystem(u.LevelEditorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
r={'passed':False,'map':'/Game/Maps/TeddyEncounter','method':'Unmodified saved encounter, Enhanced Input actions, no staging teleports, no health edits or AI freezes after initial loading pause','audio':'Unreal master-submix output attempted with a process-only UnfocusedVolumeMultiplier=1 override. Encoder measures samples and omits an empty track; native game audio separately verified. Proposed original sounds, not a match to the unauditioned reference.','frame_identity':'Request-time telemetry is contextual, not asserted as exact rendered-frame identity','frames':[],'events':[],'physical_device_verified':False}
r['requested_capture_interval_seconds']=CAPTURE_INTERVAL
s={'wall':time.monotonic(),'stage':0,'finished':False,'index':0,'previous_state':None,'last_capture':0,'last_dash':-99};handle=None
def pos(a):v=a.get_actor_location();return[v.x,v.y,v.z]
def prop(a,n):return a.get_editor_property(n)
def finish(error=None):
    if s['finished']:return
    s['finished']=True
    if error:r['error']=error
    r['passed']=not error and bool(r.get('encoding')) and len(r['frames'])>40
    (OUT/'receipt.json').write_text(json.dumps(r,indent=2,default=str));finish_editor(handle)
def complete_png(path):
    if not path.exists():return False
    data=path.read_bytes()
    if not data.endswith(b'\x00\x00\x00\x00IEND\xaeB`\x82'):return False
    assert data[:8]==b'\x89PNG\r\n\x1a\n';offset=8;compressed=[]
    while offset<len(data):
        size=struct.unpack_from('>I',data,offset)[0];kind=data[offset+4:offset+8];block=data[offset+8:offset+8+size];crc=struct.unpack_from('>I',data,offset+8+size)[0];assert zlib.crc32(kind+block)&0xffffffff==crc
        if kind==b'IHDR':width,height=struct.unpack_from('>II',block);assert width>900 and height>500;r['resolution']=[width,height]
        if kind==b'IDAT':compressed.append(block)
        offset+=size+12
    assert len(zlib.decompress(b''.join(compressed))) in (height*(width*3+1),height*(width*4+1))
    return hashlib.sha256(data).hexdigest()
def tick(dt):
    try:
        wall=time.monotonic()
        if (OUT/'stop-recording').exists():raise RuntimeError('Recording stopped by host for review')
        if wall-s['wall']>350:raise RuntimeError('Recording timeout at phase '+str(s['stage']))
        w=ed.get_game_world()
        if not w:return
        p=u.GameplayStatics.get_player_pawn(w,0);pc=u.GameplayStatics.get_player_controller(w,0)
        if not p or not pc:return
        bosses=u.GameplayStatics.get_all_actors_of_class(w,s['bossclass'])
        if not bosses:return
        b=bosses[0];game=u.GameplayStatics.get_time_seconds(w)
        inp=next(x for x in u.ObjectIterator(u.EnhancedInputLocalPlayerSubsystem) if x.get_world()==w)
        def inject(name,x,y=0):inp.inject_input_vector_for_action(s['actions'][name],u.Vector(x,y,0),[],[])
        def event(name):r['events'].append({'name':name,'wall':wall-s.get('started',wall),'game':game,'player_health':prop(p,'Health'),'boss_health':prop(b,'Health'),'boss_state':prop(b,'State')})
        def advance(n):s['stage']=n;s['phase_t']=game;s['phase_wall']=wall
        d=b.get_actor_location()-p.get_actor_location();dist=max(1,math.hypot(d.x,d.y));ux,uy=d.x/dist,d.y/dist
        if s['stage']==0:
            u.GameplayStatics.set_game_paused(w,True);u.AutomationLibrary.finish_loading_before_screenshot();s['warm']=wall;s['stage']=-1
        elif s['stage']==-1:
            if wall-s['warm']<3:return
            u.GameplayStatics.set_game_paused(w,False);u.AudioMixerLibrary.start_recording_output(w,120);s['started']=wall;advance(1);event('start');r['engine']=u.SystemLibrary.get_engine_version()
        elif s['stage']==1:
            inject('StickAim',-ux,uy)
            if dist>315:inject('Move',ux,uy)
            if prop(b,'State')==1 and prop(b,'StateAge')>.65:
                inject('Move',-ux,-uy);inject('Dash',1);event('first_strike_dodge');advance(2)
        elif s['stage']==2:
            inject('StickAim',-ux,uy)
            if prop(b,'Attacks')>=1:advance(3)
        elif s['stage']==3:
            inject('StickAim',-ux,uy)
            if dist>310:inject('Move',ux,uy)
            if prop(b,'Attacks')>=2:event('second_strike_taken');advance(4)
        elif s['stage']==4:
            # Circle in the combat area and fire; all enemy movement, health and responses are normal Blueprint behavior.
            target=b
            threats=[a for a in u.GameplayStatics.get_all_actors_of_class(w,s['minionclass']) if prop(a,'Health')>0]
            nearby=sorted(threats,key=lambda a:(a.get_actor_location()-p.get_actor_location()).length())
            if nearby and (nearby[0].get_actor_location()-p.get_actor_location()).length()<270:target=nearby[0]
            aim=target.get_actor_location()-p.get_actor_location();m=max(1,math.hypot(aim.x,aim.y));inject('StickAim',-aim.x/m,aim.y/m);inject('Fire',1)
            radial=max(-1,min(1,(dist-670)/220));mx=ux*radial-uy*.72;my=uy*radial+ux*.72
            location=p.get_actor_location()
            if abs(location.x)>1100:mx-=math.copysign(.85,location.x)
            if abs(location.y)>1170:my-=math.copysign(.85,location.y)
            n=max(1,math.hypot(mx,my));inject('Move',mx/n,my/n)
            if prop(b,'State')==1 and prop(b,'StateAge')>.68 and dist<500 and game-s['last_dash']>1:
                inject('Move',-ux,-uy);inject('Dash',1);s['last_dash']=game;event('combat_dodge')
            if prop(b,'Health')<=0:event('boss_defeat');advance(5)
            if prop(p,'Health')<=0:raise RuntimeError('Recorded play ended in player defeat before boss defeat')
            if game-s['phase_t']>40:raise RuntimeError('Boss did not fall during recorded play')
        elif s['stage']==5 and game-s['phase_t']>2.8:
            r['minions_after_victory']=[prop(a,'Health') for a in u.GameplayStatics.get_all_actors_of_class(w,s['minionclass'])];inject('Pause',1);event('pause');advance(6)
        elif s['stage']==6 and wall-s['phase_wall']>1.1:
            inject('Pause',1);event('unpause');advance(7)
        elif s['stage']==7 and game-s['phase_t']>.5:
            s['old_world']=w;inject('Restart',1);event('restart');advance(8)
        elif s['stage']==8 and (w!=s['old_world'] or game<s['phase_t']):
            r['restart_health']={'player':prop(p,'Health'),'boss':prop(b,'Health')};advance(9)
        elif s['stage']==9 and game-s['phase_t']>1.3:
            u.AudioMixerLibrary.stop_recording_output(w,u.AudioRecordingExportType.WAV_FILE,'gameplay-audio',str(OUT));u.GameplayStatics.set_game_paused(w,True);advance(10)
        if s['stage']<1:return
        state=(prop(b,'State'),prop(p,'Health'),prop(b,'Health'))
        if state!=s['previous_state']:event('state_or_damage');s['previous_state']=state
        if s.get('pending'):
            result=complete_png(s['pending'])
            if result:
                r['frames'].append(dict(s['telemetry'],path=str(s['pending']),sha256=result,crc_and_stream_complete=True));s['pending']=None
                (OUT/'progress.json').write_text(json.dumps({'last_frame':r['frames'][-1],'events':r['events'],'phase':s['stage']},indent=2))
        if s['stage']==10 and not s.get('pending') and (OUT/'gameplay-audio.wav').exists():
            r['duration_wall_seconds']=wall-s['started'];(OUT/'recording-ready.json').write_text(json.dumps(r,indent=2,default=str));s['stage']=11
        if s['stage']==11:
            signal=OUT/'encoded.json'
            if signal.exists():r['encoding']=json.loads(signal.read_text());finish()
            return
        if wall-s['last_capture']>=CAPTURE_INTERVAL and not s.get('pending'):
            image=FRAMES/f'frame-{s["index"]:05}.png';s['index']+=1;s['pending']=image;s['last_capture']=wall
            s['telemetry']={'index':s['index']-1,'wall_time':wall-s['started'],'game_time':game,'phase':s['stage'],'player':pos(p),'boss':pos(b),'player_health':prop(p,'Health'),'boss_health':prop(b,'Health'),'boss_state':prop(b,'State'),'player_yaw':p.get_actor_rotation().yaw}
            u.SystemLibrary.execute_console_command(w,'Shot filename="'+image.as_posix()+'" -nosuffix',pc)
    except Exception:finish(traceback.format_exc())
try:
    u.EditorPythonScripting.set_keep_python_script_alive(True);assert lev.load_level(r['map']);s['bossclass']=u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_TeddyBoss');s['minionclass']=u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_Stitchling')
    s['actions']={n:u.load_asset('/Game/Variant_TwinStick/Input/Actions/IA_Action_'+n) for n in ['Move','StickAim','Fire','Dash']};s['actions'].update({n:u.load_asset('/Game/TeddyEncounter/Input/IA_'+n) for n in ['Pause','Restart']})
    lev.editor_request_begin_play();handle=u.register_slate_post_tick_callback(tick)
except Exception:finish(traceback.format_exc())
