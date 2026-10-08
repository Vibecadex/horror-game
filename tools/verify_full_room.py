"""Independent saved-room QA; transient PIE staging only, never saves assets.

Host with run_encounter_test.py. The room author does not supply pass results.
Collision traces cannot see NO_COLLISION dressing, so actual captured views still
require an independent visual review. Conservative dressing-box intersections are
reported as review hints, never misrepresented as exact rendered occlusion.
"""
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
from png_evidence import decode_png

OUT = Path(os.environ['TEDDY_TEST_DIR'])
MAP = os.environ.get('TEDDY_CHAMBER_MAP', '/Game/Maps/TeddyEncounter')
assert MAP in ('/Game/Maps/TeddyEncounter', '/Game/Maps/TeddyChamberParity')
# The separate candidate deliberately raises the 690 cm far shell by 1.35.
# Its actual top is 926.5 cm. Keep the original 700 cm contract for the original map.
ROOM_HEIGHT_LIMIT_CM = 935 if MAP.endswith('/TeddyChamberParity') else 700
levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
result = {
    'passed': False, 'map': MAP, 'independent_qa': True, 'asset_writes': False,
    'physical_device_verified': False, 'checks': {}, 'room_actors': [],
    'room_extension_actors': [], 'room_extension_mesh_reuse': [],
    'capsule_probes': [], 'walls': [], 'cases': [], 'images': [],
    'method': 'Fresh saved-map readback, transient PIE staging, saved key-route movement/dash, '
              'Pawn-profile capsule sweeps, projected character bounds and Visibility traces.',
    'limitations': [
        'NPC ticking/movement disabled for deterministic room checks; this is not a combat recording.',
        'Player and boss are deliberately staged for edge/corner camera coverage.',
        'NO_COLLISION decoration does not block traces. Its box intersections are hints; inspect the images.',
        'Held screenshots hide the HUD to exclude the pause tint. They retain saved lighting/materials.',
        'Passing geometry checks do not establish visual fidelity, physical input or user acceptance.',
    ],
}
state = {'start': time.monotonic(), 'done': False, 'pressed': set()}
handle = None

SPAWNS = {
    'TE_PlayerStart': (-230, 570), 'TE_MainTeddy': (250, -230),
    'TE_Stitchling_1': (650, 600), 'TE_Stitchling_2': (-480, -500),
    'TE_Stitchling_3': (20, 1070),
}
BOUNDARIES = {
    'TE_CombatBoundFront': ((-1420, 0, 45), (.8, 30, 1)),
    'TE_CombatBoundBack': ((1480, 0, 95), (.8, 30, 2)),
    'TE_CombatBoundLeft': ((0, -1500, 95), (30, .8, 2)),
    'TE_CombatBoundRight': ((0, 1500, 95), (30, .8, 2)),
}
WALLS = [
    ('front', 'S', 0, -1, -1346, 0), ('back', 'W', 0, 1, 1406, 0),
    ('left', 'A', 1, -1, -1426, 0),
    # The saved stitchling is at (20,1070). A right-wall dash along x=0
    # would begin inside that pawn and test depenetration, not the wall.
    ('right', 'D', 1, 1, 1426, -450),
]
PAIRS = [
    ((-230, 570), (250, -230)), ((0, 0), (250, -230)),
    ((-1300, 0), (250, -230)), ((1300, 0), (250, -230)),
    ((0, -1350), (250, -230)), ((0, 1350), (250, -230)),
    ((-1300, -1350), (250, -230)), ((-1300, 1350), (250, -230)),
    ((1300, -1350), (250, -230)), ((1300, 1350), (250, -230)),
    ((-1300, -1350), (1250, 1300)), ((1300, 1350), (-1250, -1300)),
]
CAPTURE_CASES = {0, 2, 3, 6, 9, 11}
EXTENSION_PREFIX = 'TE_Parity_RoomExt_'
EXTENSION_NAMESPACE = '/Game/TeddyEncounter/Parity/RoomExtension/'
EXTENSION_TAGS = {'ParityRoomExtensionV1', 'ParityOwned', 'TeddyEncounterOwned'}
CHAMBER_CUTAWAY_LABEL = 'TE_Chamber_FrontCutaway'
CHAMBER_CUTAWAY_CLASS = '/Game/TeddyEncounter/Chamber/Blueprints/BP_ChamberCutaway.BP_ChamberCutaway_C'
CHAMBER_CUTAWAY_TAGS = {'ChamberCutawayOwned', 'ChamberOwned', 'TeddyEncounterOwned'}


def vec(value):
    return [float(value.x), float(value.y), float(value.z)]


def position(actor):
    return vec(actor.get_actor_location())


def tags(actor):
    return {str(t) for t in actor.tags}


def actor_name(actor):
    return actor.get_actor_label() if actor else None


def check(name, passed):
    result['checks'][name] = bool(passed)


def mesh_bounds(component):
    origin, extent, radius = u.SystemLibrary.get_component_bounds(component)
    return {'min': vec(origin - extent), 'max': vec(origin + extent)}


def saved_extension_audit(loaded):
    """Independent saved bounds/collision readback, not the importer's plan."""
    for actor in loaded:
        components = list(actor.get_components_by_class(u.StaticMeshComponent))
        namespace_hit = any(c.static_mesh and c.static_mesh.get_path_name().startswith(
            EXTENSION_NAMESPACE) for c in components)
        if not (actor_name(actor).startswith(EXTENSION_PREFIX) or
                'ParityRoomExtensionV1' in tags(actor) or namespace_hit):
            continue
        row = {'label': actor_name(actor), 'object_path': actor.get_path_name(),
               'class': actor.get_class().get_path_name(),
               'tags': sorted(tags(actor)),
               'actor_collision_enabled': bool(actor.get_actor_enable_collision()),
               'meshes': [], 'primitive_components': []}
        for component in actor.get_components_by_class(u.PrimitiveComponent):
            row['primitive_components'].append({
                'name': component.get_name(),
                'collision_profile': str(component.get_collision_profile_name()),
                'collision_enabled': str(component.get_collision_enabled()),
                'no_collision': component.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION,
            })
        for component in components:
            if not component.static_mesh:
                continue
            bound = mesh_bounds(component)
            lo, hi = bound['min'], bound['max']
            finite = all(math.isfinite(value) for value in lo + hi) and all(
                lo[axis] <= hi[axis] for axis in range(3))
            # 0.05 cm tolerates floating-point boundary noise. These are actual
            # conservative component bounds; no source-plan bounds are reused.
            overlaps = (lo[0] < 1480 - .05 and hi[0] > -1400 + .05 and
                        lo[1] < 1500 - .05 and hi[1] > -1500 + .05)
            row['meshes'].append({
                'mesh': component.static_mesh.get_path_name(), 'bounds': bound,
                'visible': bool(component.get_editor_property('visible')),
                'bounds_finite_and_ordered': finite,
                'bounds_top_within_declared_room_height': finite and hi[2] <= ROOM_HEIGHT_LIMIT_CM + .05,
                'bounds_outside_combat_interior': finite and not overlaps,
            })
        names = [m['mesh'].rsplit('/', 1)[-1] for m in row['meshes']]
        row['kind'] = ('shell' if len(names) == 1 and names[0].startswith('SM_Shell')
                       else 'dressing' if len(names) == 1 and names[0].startswith('SM_Dress')
                       else 'unexpected')
        # The separately audited native chamber cutaway intentionally reuses
        # retained wall meshes. Exclude this exact identity only; any other
        # namespace user must still enter the strict 84-actor extension audit.
        if (namespace_hit and row['label'] == CHAMBER_CUTAWAY_LABEL and
                row['class'] == CHAMBER_CUTAWAY_CLASS and
                set(row['tags']) == CHAMBER_CUTAWAY_TAGS):
            row['classification'] = 'explicit_chamber_cutaway_reuse'
            row['independent_audit'] = 'evidence/chamber-qa/verify_chamber_runtime.py'
            result['room_extension_mesh_reuse'].append(row)
            continue
        result['room_extension_actors'].append(row)
    rows = result['room_extension_actors']
    meshes = [m for row in rows for m in row['meshes']]
    check('saved_84_extension_actors_46_shell_38_dressing', len(rows) == 84 and
          sum(row['kind'] == 'shell' for row in rows) == 46 and
          sum(row['kind'] == 'dressing' for row in rows) == 38)
    check('room_extension_ownership_namespace_and_labels', bool(rows) and
          len({row['label'] for row in rows}) == len(rows) and all(
              row['label'].startswith(EXTENSION_PREFIX) and
              EXTENSION_TAGS <= set(row['tags']) and len(row['meshes']) == 1 and
              all(m['mesh'].startswith(EXTENSION_NAMESPACE) for m in row['meshes'])
              for row in rows))
    check('saved_room_extension_uses_21_owned_meshes', bool(meshes) and
          len({m['mesh'] for m in meshes}) == 21 and all(
              m['mesh'].startswith(EXTENSION_NAMESPACE) for m in meshes))
    check('room_extension_actor_and_components_have_no_collision', bool(rows) and all(
        not row['actor_collision_enabled'] and bool(row['primitive_components']) and all(
            c['no_collision'] and c['collision_profile'] == 'NoCollision'
            for c in row['primitive_components']) for row in rows))
    check('room_extension_world_bounds_finite_and_below_' + str(ROOM_HEIGHT_LIMIT_CM) + '_cm', bool(meshes) and all(
        m['bounds_finite_and_ordered'] and m['bounds_top_within_declared_room_height'] for m in meshes))
    check('room_extension_world_bounds_keep_combat_interior_open', bool(meshes) and all(
        m['bounds_outside_combat_interior'] for m in meshes))
    result['room_extension_bounds_method'] = {
        'source': 'Saved StaticMeshComponent world-space conservative bounds before PIE',
        'combat_interior_xy_cm': [[-1400, -1500], [1480, 1500]],
        'maximum_world_z_cm': ROOM_HEIGHT_LIMIT_CM, 'floating_point_tolerance_cm': .05,
        'source_plan_or_import_receipt_used_as_pass_result': False,
    }


def saved_audit():
    """Read the level loaded from disk before any transient staging begins."""
    loaded = list(actors.get_all_level_actors())
    by_name = {a.get_actor_label(): a for a in loaded}
    saved = {name: {'position': position(by_name[name]),
                    'class': by_name[name].get_class().get_path_name()}
             for name in SPAWNS if name in by_name}
    result['saved_spawns'] = saved
    check('saved_five_spawn_locations_preserved', len(saved) == len(SPAWNS) and
          all(math.dist(saved[n]['position'][:2], xy) < .1 for n, xy in SPAWNS.items()))
    check('saved_one_boss_three_stitchlings',
          sum(a.get_class().get_path_name().endswith('/BP_TeddyBoss.BP_TeddyBoss_C') for a in loaded) == 1 and
          sum(a.get_class().get_path_name().endswith('/BP_Stitchling.BP_Stitchling_C') for a in loaded) == 3)
    boundary_rows = []
    for name, (loc, scale) in BOUNDARIES.items():
        actor = by_name.get(name)
        row = {'label': name, 'present': actor is not None}
        if actor:
            component = actor.get_component_by_class(u.StaticMeshComponent)
            row.update(position=position(actor), scale=vec(actor.get_actor_scale3d()),
                       collision=str(component.get_collision_enabled()),
                       pawn_response=str(component.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN)))
            row['preserved'] = (math.dist(row['position'], loc) < .1 and
                                math.dist(row['scale'], scale) < .001 and
                                component.get_collision_enabled() != u.CollisionEnabled.NO_COLLISION and
                                component.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN) == u.CollisionResponseType.ECR_BLOCK)
        else:
            row['preserved'] = False
        boundary_rows.append(row)
    result['saved_boundaries'] = boundary_rows
    check('original_four_collision_bounds_preserved', all(a['preserved'] for a in boundary_rows))

    room = [a for a in loaded if a.get_actor_label().startswith('TE_Room_') or 'FullRoomOwned' in tags(a)]
    check('new_room_ownership_is_explicit', bool(room) and all(
        a.get_actor_label().startswith('TE_Room_') and {'FullRoomOwned', 'TeddyEncounterOwned'} <= tags(a)
        for a in room))
    intrusions, colliding_decor, floor_errors = [], [], []
    for actor in room:
        actor_tags = tags(actor)
        row = {'label': actor_name(actor), 'tags': sorted(actor_tags), 'meshes': []}
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            if not component.static_mesh:
                continue
            bound = mesh_bounds(component)
            entry = {'mesh': component.static_mesh.get_path_name(), 'bounds': bound,
                     'visible': bool(component.get_editor_property('visible')),
                     'collision': str(component.get_collision_enabled())}
            row['meshes'].append(entry)
            lo, hi = bound['min'], bound['max']
            inner = lo[0] < 1440 and hi[0] > -1380 and lo[1] < 1460 and hi[1] > -1460
            if inner and ('RoomFloorDetail' not in actor_tags or hi[2] > 3.05):
                intrusions.append({'actor': actor_name(actor), **entry})
            if 'RoomDecor' in actor_tags and component.get_collision_enabled() != u.CollisionEnabled.NO_COLLISION:
                colliding_decor.append(actor_name(actor))
            if 'RoomFloorDetail' in actor_tags and (hi[2] > 3.05 or component.get_collision_enabled() != u.CollisionEnabled.NO_COLLISION):
                floor_errors.append({'actor': actor_name(actor), **entry})
        result['room_actors'].append(row)
    result['intruding_room_geometry'] = intrusions
    result['colliding_decoration'] = colliding_decor
    result['invalid_floor_details'] = floor_errors
    check('new_room_geometry_keeps_combat_interior_open', not intrusions)
    check('room_decoration_has_no_collision', not colliding_decor)
    check('floor_details_are_flush_and_non_colliding', not floor_errors)
    shells = [m['bounds'] for a in result['room_actors'] if 'RoomShell' in a['tags'] for m in a['meshes']]
    sides = {
        'back': any(b['min'][0] > 1400 and b['max'][0] > 1500 and b['max'][2] >= 400 for b in shells),
        'left': any(b['max'][1] < -1450 and b['min'][1] < -1500 and b['max'][2] >= 400 for b in shells),
        'right': any(b['min'][1] > 1450 and b['max'][1] > 1500 and b['max'][2] >= 400 for b in shells),
        'front_cutaway': any(b['max'][0] <= -1380 and b['min'][0] < -1400 and 20 < b['max'][2] <= 90 for b in shells),
    }
    result['shell_sides'] = sides
    check('room_has_three_tall_sides_and_foreground_cutaway', all(sides.values()))
    saved_extension_audit(loaded)


def view():
    world = editor.get_game_world()
    if not world:
        return None
    pawn = u.GameplayStatics.get_player_pawn(world, 0)
    controller = u.GameplayStatics.get_player_controller(world, 0)
    bosses = u.GameplayStatics.get_all_actors_of_class(world, state['boss_class'])
    # Python UClass wrappers are not a reliable identity comparison across PIE.
    # Match the saved generated-class path and wait for the real boss to exist.
    boss = next((a for a in bosses if a.get_class().get_path_name().endswith(
        '/BP_TeddyBoss.BP_TeddyBoss_C')), None)
    return (world, pawn, controller, boss) if pawn and controller and boss else None


def wait_game(seconds):
    world = view()[0]
    until = u.GameplayStatics.get_time_seconds(world) + seconds
    while u.GameplayStatics.get_time_seconds(world) < until:
        yield


def key(name, down=True):
    world, pawn, controller, boss = view()
    u.SystemLibrary.execute_console_command(world, 'Input.' + ('+key ' if down else '-key ') + name, controller)
    (state['pressed'].add if down else state['pressed'].discard)(name)


def decode_hit(returned):
    """Use the reflected trace contract: first blocking HitResult, otherwise None.

    HitResult's C++ members are not exposed as Python editor properties here.
    Keep its complete serialized form for inspection instead of guessing names.
    """
    if returned is None:
        return {'blocking': False}
    if not isinstance(returned, u.HitResult):
        raise TypeError('Trace returned an unexpected type: ' + str(type(returned)))
    return {'blocking': True, 'raw_serialized_hit': returned.export_text()}


def sweep(world, start, end, radius, half_height, profile, ignore):
    return decode_hit(u.SystemLibrary.capsule_trace_single_by_profile(
        world, start, end, radius, half_height, profile, False, ignore,
        u.DrawDebugTrace.NONE, True))


def capsule_probes(world, pawn, characters):
    capsule = pawn.get_component_by_class(u.CapsuleComponent)
    radius = capsule.get_scaled_capsule_radius() - 1
    half_height = capsule.get_scaled_capsule_half_height() - 3
    profile = capsule.get_collision_profile_name()
    height = pawn.get_actor_location().z + 4
    probes = []
    for x in [-1200, -600, 0, 600, 1200]:
        for y in [-1250, -650, 0, 650, 1250]:
            probes.append(('grid', u.Vector(x, y, height), u.Vector(x, y, height + .1), radius, half_height, profile))
    for y in [-1100, 0, 1100]:
        probes.append(('across_x', u.Vector(-1250, y, height), u.Vector(1250, y, height), radius, half_height, profile))
    for x in [-1150, 0, 1150]:
        probes.append(('across_y', u.Vector(x, -1300, height), u.Vector(x, 1300, height), radius, half_height, profile))
    for actor in characters:
        cap = actor.get_component_by_class(u.CapsuleComponent)
        if cap:
            start = actor.get_actor_location() + u.Vector(0, 0, 4)
            probes.append(('spawn:' + actor_name(actor), start, start + u.Vector(0, 0, .1),
                           cap.get_scaled_capsule_radius() - 1, cap.get_scaled_capsule_half_height() - 3,
                           cap.get_collision_profile_name()))
    for label, start, end, rad, high, profile in probes:
        hit = sweep(world, start, end, rad, high, profile, characters)
        result['capsule_probes'].append({'label': label, 'start': vec(start), 'end': vec(end),
                                         'radius': rad, 'half_height': high, 'profile': str(profile), 'hit': hit})
    check('interior_grid_and_crossing_routes_clear', all(not row['hit']['blocking'] for row in result['capsule_probes'] if not row['label'].startswith('spawn:')))
    check('all_five_spawn_capsules_clear_of_environment', len([row for row in result['capsule_probes'] if row['label'].startswith('spawn:')]) == 5 and all(not row['hit']['blocking'] for row in result['capsule_probes'] if row['label'].startswith('spawn:')))


def trace_positive_controls(world, pawn, characters):
    """A no-hit answer only counts after proving active PIE collision queries."""
    controls = []
    for label, start, end, expected in [
        ('floor', u.Vector(0, 0, 300), u.Vector(0, 0, -200), 'TE_ArenaFloor'),
        ('original_front_wall', u.Vector(-1200, 0, 50), u.Vector(-1500, 0, 50), 'TE_CombatBoundFront'),
    ]:
        hit = decode_hit(u.SystemLibrary.line_trace_single(
            world, start, end, u.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
            characters, u.DrawDebugTrace.NONE, True))
        controls.append({'label': label, 'kind': 'Visibility line', 'start': vec(start),
                         'end': vec(end), 'known_geometry_crossed': expected, 'hit': hit,
                         'actor_identity_from_trace': False, 'passed': hit['blocking']})
    capsule = pawn.get_component_by_class(u.CapsuleComponent)
    hit = sweep(world, u.Vector(-1200, 0, 95), u.Vector(-1500, 0, 95),
                capsule.get_scaled_capsule_radius() - 1,
                capsule.get_scaled_capsule_half_height() - 3,
                capsule.get_collision_profile_name(), characters)
    controls.append({'label': 'original_front_wall_capsule', 'kind': 'Pawn capsule sweep',
                     'known_geometry_crossed': 'TE_CombatBoundFront', 'hit': hit,
                     'actor_identity_from_trace': False, 'passed': hit['blocking']})
    result['trace_positive_controls'] = controls
    check('active_pie_trace_queries_hit_known_floor_and_wall', all(row['passed'] for row in controls))
    assert all(row['passed'] for row in controls), 'Collision positive control failed; clear queries would be inconclusive'


def segment_box(start, end, bound):
    """Conservative box test for visible NO_COLLISION props; not a mesh raycast."""
    low, high = 0., 1.
    for axis in range(3):
        delta = end[axis] - start[axis]
        if abs(delta) < 1e-8:
            if start[axis] < bound['min'][axis] or start[axis] > bound['max'][axis]:
                return False
            continue
        a = (bound['min'][axis] - start[axis]) / delta
        b = (bound['max'][axis] - start[axis]) / delta
        low, high = max(low, min(a, b)), min(high, max(a, b))
        if high < low:
            return False
    return high >= 0 and low < .999


def camera_case(world, pawn, controller, boss, characters, index):
    width, height = controller.get_viewport_size()
    manager = controller.player_camera_manager
    camera = manager.get_camera_location()
    row = {'index': index, 'player': position(pawn), 'boss': position(boss),
           'camera': vec(camera), 'viewport': [width, height], 'fov': manager.get_fov_angle(),
           'bounds_normalized': {}, 'traces': [], 'decoration_box_review_hints': []}
    in_frame = True
    for name, actor, radius, tall, samples in [
        ('player', pawn, 42, 190, [45, 110, 170]), ('boss', boss, 190, 465, [80, 250, 430])
    ]:
        location = actor.get_actor_location()
        base = location.z - actor.get_component_by_class(u.CapsuleComponent).get_scaled_capsule_half_height()
        points = []
        for dx in [-radius, radius]:
            for dy in [-radius, radius]:
                for z in [base, base + tall]:
                    screen = controller.project_world_location_to_screen(u.Vector(location.x + dx, location.y + dy, z), False)
                    if isinstance(screen, tuple):
                        screen = next((x for x in screen if isinstance(x, u.Vector2D)), None)
                    assert isinstance(screen, u.Vector2D), 'Body bound could not project'
                    points.append([screen.x / width, screen.y / height])
        box = [min(q[0] for q in points), min(q[1] for q in points), max(q[0] for q in points), max(q[1] for q in points)]
        row['bounds_normalized'][name] = box
        in_frame = in_frame and box[0] > .025 and box[1] > .035 and box[2] < .975 and box[3] < .91
        for offset in samples:
            endpoint = u.Vector(location.x, location.y, base + offset)
            hit = decode_hit(u.SystemLibrary.line_trace_single(
                world, camera, endpoint, u.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
                characters, u.DrawDebugTrace.NONE, True))
            row['traces'].append({'target': name, 'height_above_base': offset, 'hit': hit})
            for item in result['room_actors'] + result['room_extension_actors']:
                if 'RoomFloorDetail' in item['tags']:
                    continue
                if any(m.get('visible', True) and segment_box(vec(camera), vec(endpoint), m['bounds'])
                       for m in item['meshes']):
                    row['decoration_box_review_hints'].append({
                        'actor': item['label'], 'target': name, 'height_above_base': offset,
                        'room_extension': 'ParityRoomExtensionV1' in item['tags'],
                    })
    row['in_frame'] = bool(in_frame)
    row['collision_trace_clear'] = all(not t['hit']['blocking'] for t in row['traces'])
    result['cases'].append(row)


def capture(index):
    world, pawn, controller, boss = view()
    if controller.get_hud():
        controller.get_hud().set_editor_property('show_hud', False)
    u.GameplayStatics.set_game_paused(world, True)
    path = OUT / f'room-case-{index:02}.png'
    assert not path.exists()
    u.SystemLibrary.execute_console_command(world, 'HighResShot 1280x720 filename="' + path.as_posix() + '"', controller)
    started = time.monotonic()
    while True:
        try:
            validation = decode_png(path, expected=(1280, 720))
            break
        except Exception:
            if time.monotonic() - started > 25:
                raise
            yield
    validation.pop('chunks', None)
    result['images'].append({'case': index, 'path': str(path), 'validation': validation})
    u.GameplayStatics.set_game_paused(world, False)
    yield


def run():
    while not view():
        yield
    world, pawn, controller, boss = view()
    result['engine'] = u.SystemLibrary.get_engine_version()
    result['trace_api_docs'] = {
        'capsule': str(u.SystemLibrary.capsule_trace_single_by_profile.__doc__),
        'line': str(u.SystemLibrary.line_trace_single.__doc__),
        'hit_result': str(u.HitResult.__doc__),
    }
    characters = list(u.GameplayStatics.get_all_actors_of_class(world, u.Character))
    for actor in characters:
        if actor.get_path_name() != pawn.get_path_name():
            actor.set_actor_tick_enabled(False)
            actor.get_component_by_class(u.CharacterMovementComponent).disable_movement()
    yield from wait_game(6)
    trace_positive_controls(world, pawn, characters)
    capsule_probes(world, pawn, characters)
    movement = pawn.get_component_by_class(u.CharacterMovementComponent)
    for name, direction_key, axis, sign, limit, cross_axis_lane in WALLS:
        start = [0., 0., 95.]
        start[axis] = limit - sign * 160
        start[1 - axis] = cross_axis_lane
        movement.stop_movement_immediately()
        pawn.set_actor_location(u.Vector(*start), False, False)
        yield from wait_game(.2)
        key(direction_key)
        yield from wait_game(.9)
        key(direction_key, False)
        walked = position(pawn)
        walk_pass = abs(walked[axis] - limit) < 18 and abs(walked[1 - axis] - cross_axis_lane) < 10
        start[axis] = limit - sign * 375
        movement.stop_movement_immediately()
        pawn.set_actor_location(u.Vector(*start), False, False)
        yield from wait_game(.15)
        actual_dash_start = position(pawn)
        dash_fixture_clear = math.dist(actual_dash_start[:2], start[:2]) < 5
        key(direction_key)
        yield from wait_game(.05)
        key('SpaceBar')
        until = u.GameplayStatics.get_time_seconds(world) + .45
        release_at = u.GameplayStatics.get_time_seconds(world) + .1
        samples = []
        while u.GameplayStatics.get_time_seconds(world) < until:
            samples.append({'position': position(pawn), 'speed': pawn.get_velocity().length()})
            if 'SpaceBar' in state['pressed'] and u.GameplayStatics.get_time_seconds(world) >= release_at:
                key('SpaceBar', False)
            yield
        if 'SpaceBar' in state['pressed']:
            key('SpaceBar', False)
        key(direction_key, False)
        dashed = position(pawn)
        dash_pass = (dash_fixture_clear and abs(dashed[axis] - limit) < 18 and
                     abs(dashed[1 - axis] - cross_axis_lane) < 10 and
                     max(a['speed'] for a in samples) > 900 and
                     all(sign * (a['position'][axis] - limit) < 18 for a in samples))
        result['walls'].append({'side': name, 'key': direction_key, 'expected_limit': limit,
                                'cross_axis_lane': cross_axis_lane,
                                'dash_start_requested': list(start), 'dash_start_actual': actual_dash_start,
                                'dash_fixture_clear': dash_fixture_clear,
                                'walk_end': walked, 'dash_end': dashed, 'dash_samples': samples,
                                'walk_passed': walk_pass, 'dash_passed': dash_pass})
        check(name + '_wall_blocks_walk', walk_pass)
        check(name + '_wall_blocks_real_dash_without_tunnelling', dash_pass)
        yield from wait_game(.4)

    movement.stop_movement_immediately()
    movement.disable_movement()
    player_z, boss_z = pawn.get_actor_location().z, boss.get_actor_location().z
    for index, (player_xy, boss_xy) in enumerate(PAIRS):
        pawn.set_actor_location(u.Vector(*player_xy, player_z), False, False)
        boss.set_actor_location(u.Vector(*boss_xy, boss_z), False, False)
        direction = boss.get_actor_location() - pawn.get_actor_location()
        length = max(1., math.hypot(direction.x, direction.y))
        pawn.call_method('TouchAim', (direction.x / length, direction.y / length))
        pawn.set_actor_rotation(u.Rotator(yaw=math.degrees(math.atan2(direction.y, direction.x))), False)
        yield from wait_game(2.5)
        camera_case(world, pawn, controller, boss, characters, index)
        if index in CAPTURE_CASES:
            yield from capture(index)
    check('all_twelve_camera_pairs_keep_bodies_in_frame', len(result['cases']) == len(PAIRS) and all(c['in_frame'] for c in result['cases']))
    check('all_twelve_camera_pairs_have_clear_body_collision_traces', len(result['cases']) == len(PAIRS) and all(c['collision_trace_clear'] for c in result['cases']))
    check('six_gameplay_view_images_decoded', len(result['images']) == len(CAPTURE_CASES))


def finish(error=None):
    if state['done']:
        return
    state['done'] = True
    if view():
        for name in list(state['pressed']):
            key(name, False)
        u.GameplayStatics.set_game_paused(view()[0], False)
    if error:
        result['error'] = error
    result['passed'] = not error and bool(result['checks']) and all(result['checks'].values())
    result['wall_seconds'] = time.monotonic() - state['start']
    (OUT / 'receipt.json').write_text(json.dumps(result, indent=2, default=str), encoding='utf-8')
    finish_editor(handle)


def tick(dt):
    try:
        if time.monotonic() - state['start'] > 330:
            raise RuntimeError('Full-room QA timeout')
        next(state['runner'])
    except StopIteration:
        finish()
    except Exception:
        finish(traceback.format_exc())


try:
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    assert levels.load_level(MAP)
    # ECollisionResponse has ScriptName=CollisionResponseType in this engine;
    # CollisionResponse names the distinct FCollisionResponse struct.
    result['api_preflight'] = {
        'block_response': str(u.CollisionResponseType.ECR_BLOCK),
        'pawn_channel': str(u.CollisionChannel.ECC_PAWN),
        'no_collision': str(u.CollisionEnabled.NO_COLLISION),
        'visibility_trace_channel': str(u.TraceTypeQuery.TRACE_TYPE_QUERY1),
        'debug_none': str(u.DrawDebugTrace.NONE),
        'capsule_trace_available': callable(u.SystemLibrary.capsule_trace_single_by_profile),
        'line_trace_available': callable(u.SystemLibrary.line_trace_single),
        'trace_return_contract': 'Reflected first-blocking-hit HitResult or None; serialize HitResult without inspecting unexposed fields',
        'component_bounds_available': callable(u.SystemLibrary.get_component_bounds),
    }
    saved_audit()
    state['boss_class'] = u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_TeddyBoss')
    assert state['boss_class']
    state['runner'] = run()
    levels.editor_request_begin_play()
    handle = u.register_slate_post_tick_callback(tick)
except Exception:
    finish(traceback.format_exc())
