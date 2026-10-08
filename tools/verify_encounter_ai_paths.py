"""B6 AI pathing probe. Frame-driven, read-only, no asset or map saves.

Run only through tools/run_encounter_test.py. Set TEDDY_TEST_TIMEOUT=600, since
12 placements need about 4-5 minutes of game time on top of editor start-up.

The creatures already chase on their own when ticked. BP_TeddyBoss's Tick
graph (build_boss.py) yaws to the player and calls a swept
K2_AddActorWorldOffset at Speed; BP_Stitchling inherits it with its own values.
There is no navmesh path, so a creature that hits a prop can stall. This
script measures that and does NOT call any builder.

Thresholds are Tech's proposal, PENDING DESIGN (ROOM_QA_PLAN B6 is OPEN):
  T = 10 s of active time (paused while State is 1 wind-up, 2 strike recovery or 4 hit reaction)
  boss passes on reaching 380 cm XY or closing 700 cm
  each stitchling passes on reaching 190 cm XY or closing 350 cm
  stuck = net movement under 20 cm across a span while out of range; a span over 3 s fails
  every sample inside x[-1380, 1440] y[-1460, 1460] (verify_full_room.py interior)
  stitchling centres more than 2 x effective capsule radius apart at every sample

Per-placement traces are kept under `cases`, which run_encounter_test.py leaves
out of its stdout summary.

Each placement starts from a fresh F5 world, so damage from one doesn't carry over.

Checks (4 + 5 x 12 = 64, all expected true):
  boss_speed_is_105, boss_attack_range_is_380,
  stitchling_speed_is_55, stitchling_attack_range_is_190
  per placement P: P_boss_reaches, P_stitchlings_reach, P_no_stuck, P_in_bounds, P_no_stitchling_overlap
"""
import sys, os, time, json, math, traceback
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from finish_editor import finish_editor

OUT = Path(os.environ['TEDDY_TEST_DIR'])
MAP = '/Game/Maps/TeddyEncounter'
ACTIVE_LIMIT_S = 10.
STUCK_CM, STUCK_LIMIT_S = 20., 3.
BOUNDS = (-1380., 1440., -1460., 1460.)
SAMPLE_S = .25
PAUSE_STATES = {1, 2, 4}
EXPECTED = {'boss': {'speed': 105., 'range': 380., 'close': 700.},
            'stitchling': {'speed': 55., 'range': 190., 'close': 350.}}
PLAYER_Z = 95.

# Corners: verify_full_room.py PAIRS. Prop-side points: 300+ cm inward of the
# placements in evidence/chamber/20261005T170149Z/chamber-kit-reviewed.json
# (current-run.json at main 0387fe4).
# TODO(Tech): confirm these placements are still in the shipped TeddyEncounter
# (manifest is 5 Oct; the ChamberParity20261007 kit is not on main) and that
# each point is walkable floor rather than inside a prop's collision.
PLACEMENTS = [
    ('corner_sw', -1300, -1350), ('corner_se', 1300, -1350),
    ('corner_nw', -1300, 1350), ('corner_ne', 1300, 1350),
    ('reverse_door_l', -1250, -700),      # ReverseDoorL  SM_ChamberServiceDoorBay (-1580,-700)
    ('reverse_door_r', -1250, 700),       # ReverseDoorR  SM_ChamberServiceDoorBay (-1580, 700)
    ('reverse_drum_r', -1250, 980),       # ReverseDrumR  SM_ChamberDrum (-1565, 980)
    ('reverse_drum_l', -1250, -450),      # ReverseDrumL  SM_ChamberDrum (-1565,-450)
    ('right_service_drums', 130, 1250),   # RightServiceDrums SM_ChamberDrumPair (130, 1590)
    ('left_service_drums', 850, -1250),   # LeftServiceDrums  SM_ChamberDrumPair (850,-1590)
    ('rear_drum', 1250, -435),            # RearDrum      SM_ChamberDrum (1570,-435)
    ('rear_bulkhead', 1250, 180),         # RearBulkhead  SM_ChamberBulkhead (1630, 180)
]

levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
boss_class = u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_TeddyBoss')
minion_class = u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_Stitchling')
restart = u.load_asset('/Game/TeddyEncounter/Input/IA_Restart')
result = {'passed': False, 'map': MAP, 'checks': {}, 'cases': [], 'asset_writes': False,
          'thresholds': {'active_limit_s': ACTIVE_LIMIT_S, 'stuck_cm': STUCK_CM, 'stuck_limit_s': STUCK_LIMIT_S,
                         'bounds': BOUNDS, 'expected': EXPECTED, 'status': 'Tech proposal, pending Design'},
          'method': 'Teleport the player per placement, tick the existing creature graphs, '
                    'sample XY traces every 0.25 s. No builders, no saves.'}
state = {'start': time.monotonic(), 'done': False}
handle = None

def view():
    world = editor.get_game_world()
    if not world:
        return None
    pawn = u.GameplayStatics.get_player_pawn(world, 0)
    bosses = u.GameplayStatics.get_all_actors_of_class(world, boss_class)
    if not pawn or not bosses:
        return None
    return world, pawn, bosses[0]

def now():
    return u.GameplayStatics.get_time_seconds(view()[0])

def xy(actor):
    v = actor.get_actor_location()
    return (v.x, v.y)

def prop(actor, name):
    return actor.get_editor_property(name)

def wait(seconds):
    start = now()
    while not view() or now() - start < seconds:
        yield

def reload():
    old = view()[0]
    sub = next(x for x in u.ObjectIterator(u.EnhancedInputLocalPlayerSubsystem) if x.get_world() == old)
    sub.inject_input_vector_for_action(restart, u.Vector(1, 0, 0), [], [])
    wall = time.monotonic()
    while True:
        yield
        found = view()
        if found and found[0] != old:
            return
        if time.monotonic() - wall > 10:
            raise RuntimeError('F5 did not produce a new world')

def longest_stuck(trace, in_range_flags):
    """Longest span (s) whose points all stay within STUCK_CM of the span start, out of range."""
    best = 0.
    for i in range(len(trace)):
        if in_range_flags[i]:
            continue
        t0, p0 = trace[i][0], trace[i][1:]
        for j in range(i + 1, len(trace)):
            if in_range_flags[j] or math.dist(trace[j][1:], p0) >= STUCK_CM:
                break
            best = max(best, trace[j][0] - t0)
    return round(best, 3)

def run_placement(name, px, py):
    yield from wait(.3)
    world, pawn, boss = view()
    creatures = [('boss', boss)] + [('stitchling_%d' % i, a) for i, a in
                                    enumerate(u.GameplayStatics.get_all_actors_of_class(world, minion_class))]
    for _, a in creatures:
        a.set_actor_tick_enabled(False)
    # TODO(Tech): confirm re-enabling actor tick resumes the chase branch from State 0
    # in the same frame (no hidden BeginPlay gate), and that nothing but player fire
    # puts a creature into State 4. No shots are fired here.
    pawn.get_component_by_class(u.CharacterMovementComponent).stop_movement_immediately()
    pawn.set_actor_location(u.Vector(px, py, PLAYER_Z), False, True)
    yield from wait(.2)
    target = xy(pawn)
    rows = {}
    for label, a in creatures:
        kind = 'boss' if label == 'boss' else 'stitchling'
        start_d = math.dist(xy(a), target)
        rows[label] = {'kind': kind, 'start_xy': xy(a), 'start_distance_cm': round(start_d, 1),
                       'range_cm': prop(a, 'AttackRange'), 'close_needed_cm': EXPECTED[kind]['close'],
                       'active_s': 0., 'passed': False, 'trace': [], 'in_range': [], 'out_of_bounds': []}
        a.set_actor_tick_enabled(True)
    capsule = creatures[1][1].get_component_by_class(u.CapsuleComponent) if len(creatures) > 1 else None
    # TODO(Tech): confirm get_scaled_capsule_radius() is the effective 110 x 0.35 = 38.5 cm
    # the build authors (capsule radius 110 on a 0.35-scaled actor).
    radius = capsule.get_scaled_capsule_radius() if capsule else 0.
    overlaps = []
    last, last_sample = now(), -1.
    while True:
        yield
        if not view():
            continue
        t = now()
        dt, last = t - last, t
        target = xy(view()[1])
        sample = t - last_sample >= SAMPLE_S
        if sample:
            last_sample = t
        for label, a in creatures:
            row = rows[label]
            if row['passed'] or row.get('timed_out'):
                continue
            here = xy(a)
            d = math.dist(here, target)
            closed = row['start_distance_cm'] - d
            st = prop(a, 'State')
            if st not in PAUSE_STATES:
                row['active_s'] += dt
            inside = d <= row['range_cm']
            if sample:
                row['trace'].append((round(row['active_s'], 3), round(here[0], 1), round(here[1], 1)))
                row['in_range'].append(inside)
                if not (BOUNDS[0] <= here[0] <= BOUNDS[1] and BOUNDS[2] <= here[1] <= BOUNDS[3]):
                    row['out_of_bounds'].append((round(t, 2), here))
            if inside or closed >= row['close_needed_cm']:
                row.update(passed=True, end_distance_cm=round(d, 1), closed_cm=round(closed, 1),
                           pass_reason='in_range' if inside else 'closed_distance')
                a.set_actor_tick_enabled(False)
            elif row['active_s'] >= ACTIVE_LIMIT_S:
                row.update(timed_out=True, end_distance_cm=round(d, 1), closed_cm=round(closed, 1))
                a.set_actor_tick_enabled(False)
        if sample:
            minions = [a for label, a in creatures if label != 'boss' and prop(a, 'Health') > 0]
            for i in range(len(minions)):
                for j in range(i + 1, len(minions)):
                    gap = math.dist(xy(minions[i]), xy(minions[j]))
                    if gap <= 2 * radius:
                        overlaps.append({'t': round(t, 2), 'pair': [i, j], 'gap_cm': round(gap, 1)})
        if all(r['passed'] or r.get('timed_out') for r in rows.values()):
            break
    for row in rows.values():
        row['longest_stuck_s'] = longest_stuck(row['trace'], row['in_range'])
        row.pop('in_range')
    stitch = [r for k, r in rows.items() if k != 'boss']
    result['checks'][name + '_boss_reaches'] = rows['boss']['passed']
    result['checks'][name + '_stitchlings_reach'] = len(stitch) == 3 and all(r['passed'] for r in stitch)
    result['checks'][name + '_no_stuck'] = all(r['longest_stuck_s'] <= STUCK_LIMIT_S for r in rows.values())
    result['checks'][name + '_in_bounds'] = not any(r['out_of_bounds'] for r in rows.values())
    result['checks'][name + '_no_stitchling_overlap'] = not overlaps
    result['cases'].append({'name': name, 'player_xy': [px, py], 'effective_capsule_radius_cm': radius,
                                 'overlaps': overlaps[:20], 'creatures': rows})

def run():
    while not view():
        yield
    yield from wait(1)
    world, pawn, boss = view()
    minions = list(u.GameplayStatics.get_all_actors_of_class(world, minion_class))
    result['live_values'] = {'boss': {'speed': prop(boss, 'Speed'), 'attack_range': prop(boss, 'AttackRange')},
                             'stitchlings': [{'speed': prop(a, 'Speed'), 'attack_range': prop(a, 'AttackRange'),
                                              'scale': a.get_actor_scale3d().x} for a in minions]}
    result['checks']['boss_speed_is_105'] = prop(boss, 'Speed') == EXPECTED['boss']['speed']
    result['checks']['boss_attack_range_is_380'] = prop(boss, 'AttackRange') == EXPECTED['boss']['range']
    result['checks']['stitchling_speed_is_55'] = len(minions) == 3 and all(prop(a, 'Speed') == EXPECTED['stitchling']['speed'] for a in minions)
    result['checks']['stitchling_attack_range_is_190'] = len(minions) == 3 and all(prop(a, 'AttackRange') == EXPECTED['stitchling']['range'] for a in minions)
    for index, (name, px, py) in enumerate(PLACEMENTS):
        if index:
            yield from reload()
        yield from run_placement(name, px, py)

def finish(error=None):
    if state['done']:
        return
    state['done'] = True
    if error:
        result['error'] = error
    result['expected_check_count'] = 4 + 5 * len(PLACEMENTS)
    result['passed'] = (not error and len(result['checks']) == result['expected_check_count']
                        and all(result['checks'].values()))
    result['wall_seconds'] = time.monotonic() - state['start']
    (OUT / 'receipt.json').write_text(json.dumps(result, indent=2, default=str))
    finish_editor(handle)

test = run()

def tick(dt):
    try:
        if time.monotonic() - state['start'] > 540:
            raise RuntimeError('AI path probe timed out after %d placements' % len(result['cases']))
        next(test)
    except StopIteration:
        finish()
    except Exception:
        finish(traceback.format_exc())

try:
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    assert levels.load_level(MAP)
    levels.editor_request_begin_play()
    handle = u.register_slate_post_tick_callback(tick)
except Exception:
    finish(traceback.format_exc())
