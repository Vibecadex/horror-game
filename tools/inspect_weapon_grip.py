import unreal as u,os,json,time,sys,traceback,itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from finish_editor import finish_editor
OUT=Path(os.environ['TEDDY_TEST_DIR']);lev=u.get_editor_subsystem(u.LevelEditorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);handle=None;s={'done':False};r={'passed':False}
def tick(dt):
    try:
        w=ed.get_game_world()
        if not w:return
        p=u.GameplayStatics.get_player_pawn(w,0)
        if not p or u.GameplayStatics.get_time_seconds(w)<3:return
        if s['done']:return
        s['done']=True
        c=next(c for c in p.get_components_by_class(u.StaticMeshComponent) if c.get_name()=='ServiceRifle')
        aim=p.get_actor_forward_vector()
        def alignment():
            f=c.get_forward_vector();z=c.get_up_vector()
            return {'forward_dot_aim':f.x*aim.x+f.y*aim.y+f.z*aim.z,'up_dot_vertical':z.z,'world_rotation':str(c.get_world_rotation())}
        r['current']=alignment();r['candidates']=[]
        for pitch,yaw,roll in itertools.product([0,90,180,270],repeat=3):
            c.set_relative_rotation(u.Rotator(pitch=pitch,yaw=yaw,roll=roll),False,False);item=alignment();item['rotation']={'pitch':pitch,'yaw':yaw,'roll':roll};item['score']=item['forward_dot_aim']+.5*item['up_dot_vertical'];r['candidates'].append(item)
        r['candidates']=sorted(r['candidates'],key=lambda x:x['score'],reverse=True)[:5];r['passed']=True
    except Exception:r['error']=traceback.format_exc();s['done']=True
    (OUT/'receipt.json').write_text(json.dumps(r,indent=2));finish_editor(handle)
u.EditorPythonScripting.set_keep_python_script_alive(True);assert lev.load_level('/Game/Maps/TeddyEncounter');lev.editor_request_begin_play();handle=u.register_slate_post_tick_callback(tick)
