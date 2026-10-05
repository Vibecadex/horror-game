"""Six held views of the saved room; PIE-only staging, no asset/map saves.

Run with run_encounter_test.py after the room build. Architectural cameras are
explicitly separate from normal gameplay. Exposure and lighting remain saved values.
"""
import json
import os
from pathlib import Path
import sys
import time
import traceback
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from png_evidence import decode_png
from finish_editor import finish_editor

OUT = Path(os.environ['TEDDY_TEST_DIR'])
LEVEL = u.get_editor_subsystem(u.LevelEditorSubsystem)
EDITOR = u.get_editor_subsystem(u.UnrealEditorSubsystem)
VIEWS = [
    {'name': '01-gameplay-initial', 'caption': 'Saved initial gameplay composition; normal combat camera, NPCs held and HUD hidden.', 'kind': 'gameplay'},
    {'name': '02-gameplay-wide', 'caption': 'Normal adaptive gameplay camera at staged opposite-corner separation; this is a coverage view, not an input test.', 'kind': 'gameplay-staged'},
    {'name': '03-architecture-overview', 'caption': 'Cutaway architectural overview: existing PIE camera temporarily staged; not the playable framing.', 'kind': 'architecture', 'location': (-4300, -2300, 4100), 'target': (0, 0, 180), 'fov': 53.},
    {'name': '04-rear-bulkhead', 'caption': 'Rear bulkhead and service-door detail at saved lighting/exposure; existing PIE camera temporarily staged.', 'kind': 'architecture', 'location': (650, -300, 600), 'target': (1650, 180, 320), 'fov': 62.},
    {'name': '05-side-services', 'caption': 'Side machinery and pipework detail at saved lighting/exposure; existing PIE camera temporarily staged.', 'kind': 'architecture', 'location': (-950, 100, 600), 'target': (450, -1680, 310), 'fov': 60.},
    {'name': '06-electrical-bay', 'caption': 'Electrical service bay at saved lighting/exposure; existing PIE camera temporarily staged.', 'kind': 'architecture', 'location': (-1100, 550, 430), 'target': (-420, 1640, 250), 'fov': 64.},
]
report = {'passed': False, 'map': '/Game/Maps/TeddyEncounter', 'engine': u.SystemLibrary.get_engine_version(),
          'captures': [], 'asset_writes': False, 'physical_device_verified': False,
          'method': 'Editor PIE; NPC/player movement frozen, HUD hidden; game paused through capture completion. Saved exposure/lighting unchanged. Views explicitly identify gameplay versus architectural camera.'}
state = {'wall': time.monotonic(), 'index': 0, 'phase': 'wait', 'done': False}
handle = None


def snapshot(player, pc):
    pos = player.get_actor_location()
    cam = pc.player_camera_manager
    loc = cam.get_camera_location()
    rot = cam.get_camera_rotation()
    return {'player': [pos.x, pos.y, pos.z], 'camera': [loc.x, loc.y, loc.z],
            'rotation': [rot.pitch, rot.yaw, rot.roll], 'fov': cam.get_fov_angle()}


def finish(error=None):
    if state['done']:
        return
    state['done'] = True
    report['passed'] = not error and len(report['captures']) == len(VIEWS)
    if error:
        report['error'] = error
    report['wall_seconds'] = time.monotonic() - state['wall']
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'receipt.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    finish_editor(handle)


def stage(world, player, pc):
    view = VIEWS[state['index']]
    if view['kind'] == 'gameplay-staged':
        player.set_actor_location(u.Vector(-1300, -1350, 96), False, False)
        state['boss'].set_actor_location(u.Vector(1250, 1300, 230), False, False)
    elif view['kind'] == 'architecture':
        for actor, location, rotation in state['originals']:
            actor.set_actor_location(location, False, False)
            actor.set_actor_rotation(rotation, False)
        for actor in state['directors']:
            actor.set_actor_tick_enabled(False)
        if 'camera_actor' not in state:
            # Reuse only the PIE copy of the active director. No spawning API,
            # editor-world mutation or saved asset change is needed.
            state['camera_actor'] = state['directors'][0]
            camera = state['camera_actor']
            assert camera.get_world() == world
            original_location = camera.get_actor_location()
            original_rotation = camera.get_actor_rotation()
            report['architectural_camera_original'] = {
                'location': [original_location.x, original_location.y, original_location.z],
                'rotation': [original_rotation.pitch, original_rotation.yaw, original_rotation.roll],
                'fov': camera.get_component_by_class(u.CameraComponent).get_editor_property('field_of_view'),
                'method': 'PIE director tick disabled and transform/FOV staged; PIE teardown discards changes'}
        camera = state['camera_actor']
        location = u.Vector(*view['location'])
        camera.set_actor_location(location, False, False)
        camera.set_actor_rotation(u.MathLibrary.find_look_at_rotation(location, u.Vector(*view['target'])), False)
        component = camera.get_component_by_class(u.CameraComponent)
        component.set_editor_property('field_of_view', view['fov'])
        component.set_editor_property('constrain_aspect_ratio', False)
        component.set_editor_property('post_process_blend_weight', 0.)
        # The controller already views this director from the gameplay shots.
    u.AutomationLibrary.finish_loading_before_screenshot()
    state['settle_game'] = u.GameplayStatics.get_time_seconds(world)
    state['phase'] = 'settle'


def tick(delta):
    try:
        now = time.monotonic()
        if now - state['wall'] > 280:
            raise RuntimeError('Room gallery timeout')
        world = EDITOR.get_game_world()
        if not world:
            return
        player = u.GameplayStatics.get_player_pawn(world, 0)
        pc = u.GameplayStatics.get_player_controller(world, 0)
        if not player or not pc:
            return
        if not state.get('initialized'):
            characters = u.GameplayStatics.get_all_actors_of_class(world, u.Character)
            # PIE can expose the controller/pawn before the placed actor set is
            # complete. Resolve by saved actor label, not Python UClass identity.
            bosses = [a for a in characters if a.get_actor_label() == 'TE_MainTeddy']
            directors = [a for a in u.GameplayStatics.get_all_actors_of_class(world, u.Actor)
                         if a.get_actor_label() == 'TE_CombatView']
            minions = [a for a in characters if a.get_actor_label().startswith('TE_Stitchling')]
            ready = len(bosses) == 1 and len(directors) == 1 and len(minions) == 3 and player in characters
            if not ready:
                report['initialization_observation'] = {
                    'game_time': u.GameplayStatics.get_time_seconds(world),
                    'characters': [{'label': a.get_actor_label(), 'class': a.get_class().get_path_name()}
                                   for a in characters],
                    'boss_count': len(bosses), 'director_count': len(directors), 'minion_count': len(minions)}
                if u.GameplayStatics.get_time_seconds(world) < 7:
                    return
                raise RuntimeError('Saved encounter actor set incomplete after seven game seconds: '
                                   + json.dumps(report['initialization_observation']))
            state['boss'] = bosses[0]
            state['directors'] = directors
            state['originals'] = [(a, a.get_actor_location(), a.get_actor_rotation()) for a in characters]
            for actor in characters:
                actor.set_actor_tick_enabled(False)
                movement = actor.get_component_by_class(u.CharacterMovementComponent)
                if movement:
                    movement.stop_movement_immediately()
                    movement.disable_movement()
            if pc.get_hud():
                pc.get_hud().set_editor_property('show_hud', False)
            report['world'] = world.get_path_name()
            report['postprocess'] = [{key: str(a.settings.get_editor_property(key)) for key in
                ['auto_exposure_method', 'auto_exposure_bias', 'auto_exposure_apply_physical_camera_exposure',
                 'vignette_intensity', 'bloom_intensity']} for a in
                u.GameplayStatics.get_all_actors_of_class(world, u.PostProcessVolume)]
            state['initialized'] = True
        if state['phase'] == 'wait':
            if u.GameplayStatics.get_time_seconds(world) < 7:
                return
            stage(world, player, pc)
        elif state['phase'] == 'settle':
            if u.GameplayStatics.get_time_seconds(world) - state['settle_game'] < 3:
                return
            u.GameplayStatics.set_game_paused(world, True)
            state['held'] = snapshot(player, pc)
            state['held_at'] = now
            state['held_samples'] = 0
            state['phase'] = 'hold'
        elif state['phase'] in ['hold', 'capture']:
            assert snapshot(player, pc) == state['held'], 'Held camera/player drift'
            state['held_samples'] += 1
            if state['phase'] == 'hold' and now - state['held_at'] > 1.5:
                state['image'] = OUT / (VIEWS[state['index']]['name'] + '.png')
                assert not state['image'].exists(), 'Refusing stale image evidence'
                state['requested'] = now
                state['phase'] = 'capture'
                u.SystemLibrary.execute_console_command(world,
                    'HighResShot 1280x720 filename="' + state['image'].as_posix() + '"', pc)
            elif state['phase'] == 'capture':
                if now - state['requested'] > 35:
                    raise RuntimeError('Capture completion timeout')
                if not state['image'].is_file():
                    return
                try:
                    validation = decode_png(state['image'], expected=(1280, 720))
                except Exception:
                    return  # Timeout remains active for incomplete/invalid files.
                validation.pop('chunks', None)
                report['captures'].append({**VIEWS[state['index']], 'path': str(state['image']),
                    'held_state': state['held'], 'held_samples': state['held_samples'],
                    'game_time': u.GameplayStatics.get_time_seconds(world), 'validation': validation})
                state['index'] += 1
                if state['index'] == len(VIEWS):
                    finish()
                    return
                u.GameplayStatics.set_game_paused(world, False)
                stage(world, player, pc)
    except Exception:
        finish(traceback.format_exc())


try:
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    assert LEVEL.load_level(report['map'])
    LEVEL.editor_request_begin_play()
    handle = u.register_slate_post_tick_callback(tick)
except Exception:
    finish(traceback.format_exc())
