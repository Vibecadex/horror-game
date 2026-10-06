"""Read-only runtime API reflection for the room verification tool."""
import unreal as u
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/json.loads((ROOT/'evidence/full-room/current-run.json').read_text())['out'];assert OUT.is_dir(),f'Run directory missing: {OUT}'
u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Maps/TeddyEncounter')
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
r={'hit_dir':dir(u.HitResult),'docs':str(u.HitResult.__doc__), 'hit':{}}
for name in ['line_trace_single','capsule_trace_single_by_profile','break_hit_result']:
    for owner in [u.SystemLibrary,u.GameplayStatics]:
        value=getattr(owner,name,None)
        r[str(owner)+'.'+name]=str(getattr(value,'__doc__',None))
try:
    hit=u.SystemLibrary.line_trace_single(world,u.Vector(0,0,300),u.Vector(0,0,-150),u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],u.DrawDebugTrace.NONE,True)
    r['return_type']=str(type(hit));r['return_string']=str(hit)
    if isinstance(hit,tuple):hit=next(x for x in hit if isinstance(x,u.HitResult))
    r['instance_dir']=dir(hit)
    for name in ['blocking_hit','initial_overlap','start_penetrating','distance','location','impact_point','actor','hit_actor','hit_object_handle','component','face_index']:
        try:r['hit'][name]=str(hit.get_editor_property(name))
        except Exception as e:r['hit'][name]='ERROR: '+str(e)
    for name in ['to_tuple','get_actor','break_hit_result','to_dict']:
        try:r[name]=str(getattr(hit,name)())
        except Exception as e:r[name]='ERROR: '+str(e)
except Exception as e:r['error']=str(e)
(OUT/'trace-api-probe.json').write_text(json.dumps(r,indent=2))
