import json
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
L=u.BlueprintEditorLibrary; A=u.EditorAssetLibrary
r={}
for name in ['BlueprintEditorLibrary','BlueprintGraphEditor','AddNewSubobjectParams','FbxImportUI','FbxSkeletalMeshImportData','FbxAnimSequenceImportData','PostProcessSettings','MaterialExpressionNoise','HUD']:
    c=getattr(u,name)
    r[name]={'doc':c.__doc__,'methods':{x:str(getattr(c,x).__doc__) for x in dir(c) if any(s in x for s in ['type_by','variable_default','member_variables','list_functions','create_node_from_name','get_all_actions','available','draw_rect','draw_text'])}}
for suffix in ['Move','MouseAim','StickAim','Fire','Dash']:
    obj=A.load_asset('/Game/Variant_TwinStick/Input/Actions/IA_Action_'+suffix)
    r[suffix]={k:str(obj.get_editor_property(k)) for k in ['value_type','triggers','modifiers','trigger_when_paused']}
bp=A.load_asset('/Game/Variant_TwinStick/Blueprints/BP_TwinStickCharacter')
ge=u.BlueprintGraphEditor.get_graph_editor(L.find_event_graph(bp))
r['actions']=ge.get_available_actions([]) if hasattr(ge,'get_available_actions') else [x for x in dir(ge) if 'action' in x]
r['cdo_variables']={}
cdo=u.get_default_object(L.generated_class(bp))
for gr in L.list_graphs(bp):
    for n in u.BlueprintGraphEditor.get_graph_editor(gr).list_all_nodes():
        if 'VariableGet' in n.get_class().get_name():
            for p in n.list_output_pins():
                k=str(p.get_pin_name())
                try:r['cdo_variables'][k]=str(cdo.get_editor_property(k))
                except Exception:pass
(ROOT/'evidence/implementation/api.json').write_text(json.dumps(r,indent=2,default=str))
