"""Repair only the three independently identified invalid FKey mappings."""
import json
import sys
import traceback
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from encounter_authoring import existing, save

OUT = ROOT / 'evidence/qa-repair/20261005T042900Z'
required = {'IA_Action_Dash': 'SpaceBar', 'IA_Pause': 'Escape', 'IA_Restart': 'F5'}
result = {'passed': False, 'asset': '/Game/TeddyEncounter/Input/IMC_Encounter', 'changed': []}

def describe(entries):
    return [{'action': e.action.get_name(), 'key': e.key.export_text(),
             'valid': u.InputLibrary.key_is_valid(e.key),
             'modifiers': [x.get_class().get_name() for x in e.modifiers],
             'triggers': [x.get_class().get_name() for x in e.triggers]} for e in entries]

try:
    context = existing(result['asset'])
    defaults = context.get_editor_property('default_key_mappings')
    entries = list(defaults.get_editor_property('mappings'))
    result['before'] = describe(entries)
    for entry in entries:
        if u.InputLibrary.key_is_valid(entry.key):
            continue
        name = entry.action.get_name()
        assert name in required and entry.key.export_text() == '(', 'Unexpected invalid mapping'
        key = u.Key()
        key.import_text(required[name])
        assert u.InputLibrary.key_is_valid(key) and key.export_text() == required[name]
        entry.set_editor_property('key', key)
        result['changed'].append({'action': name, 'key': required[name]})
    after = describe(entries)
    assert all(row['valid'] for row in after)
    for action, key in required.items():
        assert sum(row['action'] == action and row['key'] == key for row in after) == 1
    assert len(entries) == len(result['before'])
    for before, row in zip(result['before'], after):
        assert before['action'] == row['action']
        assert before['modifiers'] == row['modifiers'] and before['triggers'] == row['triggers']
        if before['valid']:
            assert before == row
    if result['changed']:
        defaults.set_editor_property('mappings', entries)
        context.set_editor_property('default_key_mappings', defaults)
        save(context)
    result.update(after=after, passed=True)
except Exception:
    result['error'] = traceback.format_exc()
    raise
finally:
    (OUT / 'key-repair.json').write_text(json.dumps(result, indent=2))
