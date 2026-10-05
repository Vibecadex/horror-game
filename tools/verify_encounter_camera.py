"""Saved camera framing at arena edges; staged placement is explicit, not input evidence."""
import sys,os,time,json,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from finish_editor import finish_editor
from png_evidence import decode_png
OUT=Path(os.environ['TEDDY_TEST_DIR']);lev=u.get_editor_subsystem(u.LevelEditorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
r={'passed':False,'map':'/Game/Maps/TeddyEncounter','method':'Frozen NPCs, staged player/boss positions, 2.5 seconds camera settling; projected conservative body bounds in native PIE viewport; held native screenshots at three edge cases, HUD hidden only for these plates','cases':[],'images':[]}
s={'wall':time.monotonic(),'index':0,'placed':False,'done':False};handle=None
positions=[(-1000,230),(0,0),(-1300,0),(1300,0),(0,-1350),(0,1350),(-1300,-1350),(-1300,1350),(1300,-1350),(1300,1350)]
cases=[(p,(250,-230)) for p in positions]+[((-1300,-1350),(1250,1300)),((1300,1350),(-1250,-1300))]
def finish(error=None):
    if s['done']:return
    s['done']=True;r['passed']=not error and len(r['cases'])==len(cases) and all(c['visible'] for c in r['cases'])
    if error:r['error']=error
    (OUT/'receipt.json').write_text(json.dumps(r,indent=2));finish_editor(handle)
def tick(dt):
    try:
        if time.monotonic()-s['wall']>140:raise RuntimeError('Framing test timeout')
        w=ed.get_game_world()
        if not w:return
        p=u.GameplayStatics.get_player_pawn(w,0);pc=u.GameplayStatics.get_player_controller(w,0)
        if not p or not pc:return
        b=u.GameplayStatics.get_actor_of_class(w,s['bossclass']);game=u.GameplayStatics.get_time_seconds(w)
        if s.get('pending'):
            try:validation=decode_png(s['pending'],expected=tuple(pc.get_viewport_size()))
            except Exception:
                if time.monotonic()-s['capture_wall']>20:raise
                return
            validation.pop('chunks',None);r['images'].append({'case':s['index'],'path':str(s['pending']),'validation':validation})
            s['pending']=None;u.GameplayStatics.set_game_paused(w,False);s['index']+=1;s['placed']=False
            if s['index']==len(cases):finish()
            return
        if not s.get('frozen'):
            for a in u.GameplayStatics.get_all_actors_of_class(w,u.Character):
                a.get_component_by_class(u.CharacterMovementComponent).disable_movement()
                if a!=p:a.set_actor_tick_enabled(False)
            s['frozen']=True
        if not s['placed']:
            pp,bp=cases[s['index']];p.set_actor_location(u.Vector(*pp,96),False,False);b.set_actor_location(u.Vector(*bp,230),False,False)
            s['time']=game;s['placed']=True;return
        if game-s['time']<2.5:return
        width,height=pc.get_viewport_size();bounds={};visible=True
        for name,a,radius,tall in [('player',p,42,190),('boss',b,190,465)]:
            loc=a.get_actor_location();base=loc.z-(96 if name=='player' else 230);points=[]
            for dx in [-radius,radius]:
                for dy in [-radius,radius]:
                    for z in [base,base+tall]:
                        screen=pc.project_world_location_to_screen(u.Vector(loc.x+dx,loc.y+dy,z),False)
                        assert isinstance(screen,u.Vector2D);points.append([screen.x/width,screen.y/height])
            box=[min(q[0] for q in points),min(q[1] for q in points),max(q[0] for q in points),max(q[1] for q in points)]
            bounds[name]=box;visible=visible and box[0]>.025 and box[1]>.035 and box[2]<.975 and box[3]<.91
        r['cases'].append({'player':cases[s['index']][0],'boss':cases[s['index']][1],'bounds_normalized':bounds,'visible':visible,'viewport':[width,height]})
        if s['index'] in [0,6,11]:
            pc.get_hud().set_editor_property('show_hud',False);u.GameplayStatics.set_game_paused(w,True)
            s['pending']=OUT/f'framing-{s["index"]:02}.png';s['capture_wall']=time.monotonic()
            u.SystemLibrary.execute_console_command(w,'Shot filename="'+s['pending'].as_posix()+'" -nosuffix',pc);return
        s['index']+=1;s['placed']=False
        if s['index']==len(cases):finish()
    except Exception:finish(traceback.format_exc())
try:
    u.EditorPythonScripting.set_keep_python_script_alive(True);assert lev.load_level(r['map']);s['bossclass']=u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_TeddyBoss')
    lev.editor_request_begin_play();handle=u.register_slate_post_tick_callback(tick)
except Exception:finish(traceback.format_exc())
