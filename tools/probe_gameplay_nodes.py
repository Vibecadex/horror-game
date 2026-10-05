from pathlib import Path
import sys,json
import unreal as u
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from encounter_authoring import *
r={}
for name in ['BP_EncounterController','BP_EncounterPlayer','BP_TeddyBoss']:
    bp=A.load_asset(NS+'/Blueprints/'+name);ge=u.BlueprintGraphEditor.get_graph_editor(L.find_event_graph(bp))
    r[name]=[str(x) for x in ge.list_available_nodes([]) if any(s in str(x) for s in ['Escape','F5','Cast To BP_','Self','EnhancedInputAction','DrawText','DrawRect'])]
fire=A.load_asset('/Game/Variant_TwinStick/Input/Actions/IA_Action_Fire');r['fire_triggers']=[]
for t in fire.triggers:
    r['fire_triggers'].append({k:str(t.get_editor_property(k)) for k in ['interval','trigger_limit','trigger_on_start','actuation_threshold']})
for cls in ['K2Node_InputKey','K2Node_EnhancedInputAction','K2Node_DynamicCast','DrawToRenderTargetContext','PostProcessSettings']:
    if hasattr(u,cls):r[cls]=getattr(u,cls).__doc__
(R/'evidence/implementation/gameplay-api.json').write_text(json.dumps(r,indent=2))
