import sys,json,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
r={'passed':False}
try:
    pc=existing(NS+'/Blueprints/BP_EncounterController');g=Graph(pc)
    begin=next(n for n in g.g.list_all_nodes() if str(L.get_node_title(n))=='Event BeginPlay')
    links=begin.find_output_pin('then').list_connected_pins();begin.find_output_pin('then').break_pin_links()
    rotation=g.math('MakeRotator',Pitch=0,Yaw=0,Roll=0)
    orientation=g.call('Controller.SetControlRotation',NewRotation=(rotation,'ReturnValue'));delay=g.call('KismetSystemLibrary.Delay',Duration='.3');g.chain(begin,delay,orientation)
    for p in links:assert orientation.find_output_pin('then').try_create_connection(p)
    # Use Enhanced Input for pause/restart so tests can exercise exactly the input bindings.
    context=existing(NS+'/Input/IMC_Encounter');defaults=context.get_editor_property('default_key_mappings');entries=list(defaults.get_editor_property('mappings'))
    keys={}
    for name,keyname in [('Pause','Escape'),('Restart','F5')]:
        action=duplicate('/Game/Variant_TwinStick/Input/Actions/IA_Action_Dash','Input/IA_'+name);action.set_editor_property('value_type',u.InputActionValueType.BOOLEAN);action.set_editor_property('trigger_when_paused',True)
        trigger=u.new_object(u.InputTriggerPressed,outer=action);action.set_editor_property('triggers',[trigger]);save(action)
        entries=[e for e in entries if e.action!=action]
        key=u.Key();key.import_text(keyname)
        assert u.InputLibrary.key_is_valid(key) and key.export_text()==keyname
        entries.append(u.EnhancedActionKeyMapping(action=action,key=key));keys[name]=action
    defaults.set_editor_property('mappings',entries);context.set_editor_property('default_key_mappings',defaults);save(context)
    available=g.g.list_available_nodes([]);r['actions']=[str(x) for x in available if 'IA_Pause' in str(x) or 'IA_Restart' in str(x)]
    for name,keyname in [('Pause','Escape'),('Restart','F5')]:
        keynode=next(n for n in g.g.list_all_nodes() if n.get_class().get_name()=='K2Node_InputKey' and str(u.InputLibrary.key_get_display_name(n.get_editor_property('input_key'))).lower() in ([keyname.lower()] if name=='Restart' else ['escape','esc']))
        old=keynode.find_output_pin('Pressed').list_connected_pins()
        actionname=next(str(x) for x in available if 'EnhancedActionEvents' in str(x) and ('IA_'+name) in str(x))
        event=g.node(g.g.create_node_from_name(actionname,u.Vector2D(0,0),[]))
        for p in old:assert event.find_output_pin('Started').try_create_connection(p)
        g.g.remove_nodes([keynode])
    compile(pc)
    r['passed']=True
except Exception:r['error']=traceback.format_exc();raise
finally:(ROOT/'evidence/implementation/control-refinement.json').write_text(json.dumps(r,indent=2))
