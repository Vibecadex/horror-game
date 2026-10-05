"""Read saved mappings and compare FKey parsing in memory; no asset writes."""
from pathlib import Path
import json,traceback
import unreal as u
out=Path(__file__).resolve().parent/'bindings.json'
r={'asset':'/Game/TeddyEncounter/Input/IMC_Encounter','read_only':True,'saved_mappings':[],'parser_cases':[]}
try:
    context=u.load_asset(r['asset'])
    for mapping in context.get_editor_property('default_key_mappings').get_editor_property('mappings'):
        r['saved_mappings'].append({'action':mapping.action.get_name() if mapping.action else None,'exported_key':mapping.key.export_text(),'display_name':str(u.InputLibrary.key_get_display_name(mapping.key)),'valid':u.InputLibrary.key_is_valid(mapping.key)})
    for token in ['SpaceBar','Escape','F5','(KeyName="SpaceBar")','(KeyName="Escape")','(KeyName="F5")']:
        key=u.Key();key.import_text(token)
        r['parser_cases'].append({'input':token,'exported_key':key.export_text(),'display_name':str(u.InputLibrary.key_get_display_name(key)),'valid':u.InputLibrary.key_is_valid(key)})
    required={'IA_Action_Dash':'SpaceBar','IA_Pause':'Escape','IA_Restart':'F5'}
    r['required_bindings']=[{'action':action,'required_key':key,'present_and_valid':any(m['action']==action and m['exported_key']==key and m['valid'] for m in r['saved_mappings'])} for action,key in required.items()]
    r['passed']=all(item['present_and_valid'] for item in r['required_bindings'])
except Exception:r['error']=traceback.format_exc();raise
finally:out.write_text(json.dumps(r,indent=2))
