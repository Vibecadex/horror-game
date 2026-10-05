"""Test saved key-to-action routing through PlayerController input, not action injection."""
import json
import math
import os
import sys
import time
import traceback
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from finish_editor import finish_editor

OUT = Path(os.environ['TEDDY_TEST_DIR'])
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
boss_class = u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_TeddyBoss')
shot_class = u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_EncounterProjectile')
result = {'passed': False, 'map': '/Game/Maps/TeddyEncounter', 'checks': {}, 'events': [],
          'method': 'Input.+key / Input.-key console commands -> PlayerController::InputKey -> saved mapping -> Enhanced Input action -> saved gameplay Blueprint; no action injection',
          'physical_device_verified': False, 'asset_writes': False}
state = {'start': time.monotonic(), 'done': False, 'pressed': set()}
handle = None

def view():
    world = editor.get_game_world()
    if not world:
        return None
    pawn = u.GameplayStatics.get_player_pawn(world, 0)
    pc = u.GameplayStatics.get_player_controller(world, 0)
    boss = u.GameplayStatics.get_actor_of_class(world, boss_class)
    return (world, pawn, pc, boss) if pawn and pc and boss else None

def position(actor):
    vec = actor.get_actor_location()
    return [vec.x, vec.y, vec.z]

def key(name, down=True):
    world, pawn, pc, boss = view()
    command = 'Input.' + ('+key ' if down else '-key ') + name
    u.SystemLibrary.execute_console_command(world, command, pc)
    (state['pressed'].add if down else state['pressed'].discard)(name)
    result['events'].append({'command': command, 'game_time': u.GameplayStatics.get_time_seconds(world), 'wall_time': time.monotonic() - state['start']})

def wait(seconds):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        yield

def tap(name):
    key(name)
    yield from wait(.09)
    if view():
        key(name, False)
    yield from wait(.12)

def owned_shots(pawn, world):
    return {s.get_path_name() for s in u.GameplayStatics.get_all_actors_of_class(world, shot_class) if s.get_owner() == pawn and s.get_instigator() == pawn}

def run():
    while not view() or u.GameplayStatics.get_time_seconds(view()[0]) < 1.0:
        yield
    world, pawn, pc, boss = view()
    result['engine'] = u.SystemLibrary.get_engine_version()
    result['viewport'] = list(pc.get_viewport_size())
    context = u.load_asset('/Game/TeddyEncounter/Input/IMC_Encounter')
    rows = [{'action': m.action.get_name(), 'key': m.key.export_text(), 'valid': u.InputLibrary.key_is_valid(m.key)} for m in context.get_editor_property('default_key_mappings').get_editor_property('mappings')]
    result['saved_mappings'] = rows
    result['checks']['all_saved_keys_valid_after_reopen'] = all(m['valid'] for m in rows)
    required = {'IA_Action_Dash': 'SpaceBar', 'IA_Pause': 'Escape', 'IA_Restart': 'F5'}
    result['checks']['required_bindings_present_once'] = all(sum(m['action'] == action and m['key'] == name and m['valid'] for m in rows) == 1 for action, name in required.items())
    start = position(pawn)
    key('S')
    yield from wait(.3)
    key('S', False)
    result['movement_distance'] = math.dist(start, position(pawn))
    result['checks']['movement_key_routes_to_saved_action'] = result['movement_distance'] > 35
    key('S')
    yield from wait(.06)
    start = position(pawn)
    key('SpaceBar')
    until = time.monotonic() + .26
    peak = 0
    while time.monotonic() < until:
        peak = max(peak, pawn.get_velocity().length())
        yield
    key('SpaceBar', False)
    key('S', False)
    result['dash_peak_speed'] = peak
    result['dash_distance'] = math.dist(start, position(pawn))
    result['checks']['space_triggers_dash'] = peak > 900 and result['dash_distance'] > 120
    yield from wait(.2)
    yield from tap('Escape')
    world, pawn, pc, boss = view()
    paused_time = u.GameplayStatics.get_time_seconds(world)
    paused_position = position(pawn)
    old_shots = owned_shots(pawn, world)
    result['checks']['escape_pauses'] = u.GameplayStatics.is_game_paused(world)
    key('W')
    key('LeftMouseButton')
    yield from wait(.35)
    key('W', False)
    key('LeftMouseButton', False)
    result['checks']['pause_freezes_time_and_movement'] = abs(u.GameplayStatics.get_time_seconds(world) - paused_time) < .01 and math.dist(position(pawn), paused_position) < .01
    result['checks']['pause_suppresses_fire'] = not (owned_shots(pawn, world) - old_shots)
    yield from tap('Escape')
    yield from wait(.25)
    result['checks']['escape_resumes'] = not u.GameplayStatics.is_game_paused(world) and u.GameplayStatics.get_time_seconds(world) > paused_time + .1
    old_shots = owned_shots(pawn, world)
    key('LeftMouseButton')
    until = time.monotonic() + .5
    new_shots = set()
    while time.monotonic() < until:
        new_shots.update(owned_shots(pawn, world) - old_shots)
        yield
    key('LeftMouseButton', False)
    result['owned_projectiles_created'] = len(new_shots)
    result['checks']['mouse_button_routes_to_fire'] = bool(new_shots)
    old_world = world
    key('F5')
    until = time.monotonic() + 8
    while (not view() or view()[0] == old_world) and time.monotonic() < until:
        yield
    assert view() and view()[0] != old_world, 'F5 did not reload the encounter'
    key('F5', False)
    world, pawn, pc, boss = view()
    result['checks']['f5_restarts_with_fresh_possession'] = pawn.get_class().get_name() == 'BP_EncounterPlayer_C' and pawn.get_editor_property('Health') == 100 and boss.get_editor_property('Health') == 300
    yield from wait(.8)
    key('S')
    yield from wait(.2)
    key('S', False)
    yield from tap('Escape')
    world, pawn, pc, boss = view()
    result['checks']['escape_still_works_after_restart'] = u.GameplayStatics.is_game_paused(world)
    old_world = world
    key('F5')
    until = time.monotonic() + 8
    while (not view() or view()[0] == old_world) and time.monotonic() < until:
        yield
    assert view() and view()[0] != old_world, 'F5 did not restart while paused'
    key('F5', False)
    world, pawn, pc, boss = view()
    result['checks']['f5_restarts_while_paused'] = not u.GameplayStatics.is_game_paused(world) and pawn.get_editor_property('Health') == 100 and boss.get_editor_property('Health') == 300

def finish(error=None):
    if state['done']:
        return
    state['done'] = True
    if error:
        result['error'] = error
    if view():
        for name in list(state['pressed']):
            key(name, False)
    result['passed'] = not error and bool(result['checks']) and all(result['checks'].values())
    result['wall_seconds'] = time.monotonic() - state['start']
    (OUT / 'receipt.json').write_text(json.dumps(result, indent=2))
    finish_editor(handle)

test = run()

def tick(dt):
    try:
        if time.monotonic() - state['start'] > 100:
            raise RuntimeError('Key routing test timed out')
        next(test)
    except StopIteration:
        finish()
    except Exception:
        finish(traceback.format_exc())

try:
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    assert levels.load_level(result['map'])
    levels.editor_request_begin_play()
    handle = u.register_slate_post_tick_callback(tick)
except Exception:
    finish(traceback.format_exc())
