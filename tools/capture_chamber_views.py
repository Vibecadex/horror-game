"""Two chamber-reference architectural views; PIE-only staging, no asset/map saves.

Root runs: python tools/run_encounter_test.py tools/capture_chamber_views.py
Offline review: python tools/capture_chamber_views.py --describe
Optional TEDDY_CHAMBER_WIDTH/HEIGHT retain a 3:2 ratio. Architectural cameras are
explicitly separate from normal gameplay. Exposure and lighting remain saved values.
"""
import json
import os
from pathlib import Path
import sys
import time
import traceback

CAPTURE_SIZE = (int(os.environ.get('TEDDY_CHAMBER_WIDTH', '1920')), int(os.environ.get('TEDDY_CHAMBER_HEIGHT', '1280')))
assert 0 < min(CAPTURE_SIZE) and max(CAPTURE_SIZE) <= 8192
assert CAPTURE_SIZE[0] * 2 == CAPTURE_SIZE[1] * 3, 'Use a native 3:2 resolution; no warped or cropped comparison.'

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
CAMERA_REVISION = 'chamber-03-reverse-services'
# Baseline chamber-01 is preserved in the 095951 and 101028 receipts.
# Reframe the architectural views only: front fills more of the native frame;
# reverse is lower and less steep, with both service bays retained in view.
# Revision03 widens only the reverse FOV64->70 after saved-bounds projection
# showed clipped electrical cabinets and most of the near-end pipe rack.
VIEWS = [
    {'name': '01-chamber-front', 'caption': 'ARCHITECTURAL FRONT: looks +X toward pressure bulkhead; saved actors/art/exposure. Camera outside front wall; native owned tall-wall cutaway may hide, retained sill remains. Reframed camera revision chamber-02.', 'kind': 'architecture', 'location': (-4050, 180, 2780), 'target': (100, 180, 80), 'fov': 41.5},
    {'name': '02-chamber-reverse', 'caption': 'ARCHITECTURAL REVERSE: looks -X toward complete reverse service wall; camera inside far wall. Saved actors/art/exposure; native reverse wall must be visible. Revision03 retains the approximately35-degree pose and widens FOV to70 to include the electrical cabinets and near-end pipe rack.', 'kind': 'architecture', 'location': (1450, 100, 1450), 'target': (-600, 100, 0), 'fov': 70.0},
]

if '--describe' in sys.argv:
    print(json.dumps({'resolution': CAPTURE_SIZE, 'camera_revision': CAMERA_REVISION, 'views': VIEWS, 'asset_writes': False,
        'camera_kind': 'architectural only', 'reference_front': 'study/visuals/chamber-target-front.png',
        'reference_reverse': 'study/visuals/chamber-target-reverse.png'}, indent=2))
    raise SystemExit(0)

import unreal as u
from png_evidence import decode_png
from finish_editor import finish_editor

OUT = Path(os.environ['TEDDY_TEST_DIR'])
LEVEL = u.get_editor_subsystem(u.LevelEditorSubsystem)
EDITOR = u.get_editor_subsystem(u.UnrealEditorSubsystem)

report = {'passed': False, 'map': '/Game/Maps/TeddyEncounter', 'engine': u.SystemLibrary.get_engine_version(),
          'captures': [], 'asset_writes': False, 'physical_device_verified': False,
          'method': 'Editor PIE architectural comparison only; saved actors frozen, HUD hidden. Native 3:2 HighResShot viewport, no crop/warp. Lighting/exposure unchanged. Environment Blueprint ticks remain enabled so the native camera-dependent cutaway can react; visibility is recorded, never forced.',
          'resolution': list(CAPTURE_SIZE), 'camera_revision': CAMERA_REVISION, 'reference_front': 'study/visuals/chamber-target-front.png',
          'reference_reverse': 'study/visuals/chamber-target-reverse.png'}
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
        component.set_editor_property('aspect_ratio', CAPTURE_SIZE[0] / CAPTURE_SIZE[1])
        component.set_editor_property('constrain_aspect_ratio', True)
        component.set_editor_property('post_process_blend_weight', 0.)
        # The controller already views this director from the gameplay shots.
    u.AutomationLibrary.finish_loading_before_screenshot()
    state['settle_game'] = u.GameplayStatics.get_time_seconds(world)
    state['phase'] = 'settle'


def cutaway_observation(world):
    """Read-only record: never conceal geometry to improve a comparison."""
    rows = []
    for actor in u.GameplayStatics.get_all_actors_of_class(world, u.Actor):
        label = actor.get_actor_label()
        tags = [str(tag) for tag in actor.tags]
        identity = ' '.join([label, actor.get_class().get_path_name(), *tags]).lower()
        if not any(token in identity for token in ('cutaway', 'reversewall', 'chamber')):
            continue
        row = {'label': label, 'class': actor.get_class().get_path_name(),
               'tags': tags, 'components': []}
        try:
            row['actor_hidden_in_game'] = bool(actor.get_editor_property('hidden'))
        except Exception as error:
            row['actor_hidden_in_game_unavailable'] = str(error)
        for component in actor.get_components_by_class(u.PrimitiveComponent):
            values = {'name': component.get_name()}
            for key in ('visible', 'hidden_in_game'):
                try:
                    values[key] = bool(component.get_editor_property(key))
                except Exception as error:
                    values[key + '_unavailable'] = str(error)
            row['components'].append(values)
        rows.append(row)
    return rows


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
                    f'HighResShot {CAPTURE_SIZE[0]}x{CAPTURE_SIZE[1]} filename="' + state['image'].as_posix() + '"', pc)
            elif state['phase'] == 'capture':
                if now - state['requested'] > 35:
                    raise RuntimeError('Capture completion timeout')
                if not state['image'].is_file():
                    return
                try:
                    validation = decode_png(state['image'], expected=CAPTURE_SIZE)
                except Exception:
                    return  # Timeout remains active for incomplete/invalid files.
                validation.pop('chunks', None)
                report['captures'].append({**VIEWS[state['index']], 'path': str(state['image']),
                    'held_state': state['held'], 'held_samples': state['held_samples'],
                    'game_time': u.GameplayStatics.get_time_seconds(world), 'validation': validation,
                    'cutaway_observation': cutaway_observation(world)})
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
