"""B6 AI pathing probe. Frame-driven, read-only, no asset or map saves.

Run only through tools/run_encounter_test.py with TEDDY_TEST_TIMEOUT=720. The
script stops itself at 480 s wall (INTERNAL_LIMIT_S), well inside the runner's
720 s, which also has to cover editor start-up; a slow run therefore still writes
its own receipt. A partial receipt (passed=false, partial=true) is also written
after every placement, so even a runner kill leaves the finished placements on disk.
Worst-case game time is about 15 x (0.5 + 10 + reload) s, roughly 3-4 minutes.

The creatures already chase on their own when ticked. BP_TeddyBoss's Tick
graph (build_boss.py) yaws to the player and calls a swept
K2_AddActorWorldOffset at Speed; BP_Stitchling inherits it with its own values.
There is no navmesh path and no slide: the swept move stops at the first
blocking hit. All 9 kit props sit outside the walls and the legacy pillars have
collision off, so the arena interior is an empty box and the only obstacles are
other characters (Tech review P1). The real stall is a stitchling whose straight
line to the player passes through the boss (capsule radius 135). This script
measures that and does NOT call any builder.

Thresholds are Tech's proposal, PENDING DESIGN (ROOM_QA_PLAN B6 is OPEN):
  T = 10 s of active time (paused while State is 1 wind-up, 2 strike recovery or 4 hit reaction)
  boss passes on reaching 380 cm XY or closing 700 cm
  each stitchling passes on reaching 190 cm XY or closing 350 cm
  stuck = net movement under 20 cm across a span while out of range; a span over 3 s fails
  every sample inside x[-1380, 1440] y[-1460, 1460] (verify_full_room.py interior)
  stitchling centres at least r_i + r_j - 2 cm apart at every sample (touching
  capsules block each other and stop at ~77 cm; only a real overlap fails)
  player within 5 cm XY of its placement after 0.2 s, else the placement is invalid
  and its reach checks are recorded false as skipped
  A creature that passes is frozen and becomes an obstacle for the others; that is
  realistic (a creature in range stands in wind-up) and is noted in the receipt.

Per-placement traces are kept under `cases`, which run_encounter_test.py leaves
out of its stdout summary.

Each placement, including the first, starts from a fresh F5 world, so damage
and start positions don't carry over. A failed F5 fails that placement (all six
checks false, with a reason) and the run moves on; two in a row abort.

Placements (15):
  4 corners (verify_full_room PAIRS)
  8 edge points (formerly "prop-side"; they are edge coverage, not prop avoidance)
  3 occlusion cases: the player stands 300 cm XY from the live boss (inside 380, so
    the boss passes at once and stands still), and the nearest stitchling is moved,
    at runtime only, to 320 cm behind the boss on the same line. It meets the boss's
    capsule after ~146 cm, before it can close the 350 cm pass distance.

Checks (4 + 6 x 15 = 94):
  boss_speed_is_105, boss_attack_range_is_380,
  stitchling_speed_is_55, stitchling_attack_range_is_190
  per placement P: P_placement_valid, P_boss_reaches, P_stitchlings_reach, P_no_stuck,
                   P_in_bounds, P_no_stitchling_overlap
Expected first run: from source the occlusion stitchling stops dead, so the three
occlusion_*_stitchlings_reach and occlusion_*_no_stuck checks (6) are likely false:
88/94, passed=false. Listed in likely_false_until_avoidance; not waived.

Review: Horror Unreal Tech, 2026-10-08 (P1-P6 applied).
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
INTERNAL_LIMIT_S = 480.   # runner: TEDDY_TEST_TIMEOUT=720, which also covers editor start-up
PLACEMENT_TOLERANCE_CM = 5.
OVERLAP_SLACK_CM = 2.
OCCLUSION_PLAYER_CM = 300.   # player to boss, XY; 3D ~332 < 380, so the boss stands in wind-up
OCCLUSION_GAP_CM = 320.      # boss centre to the moved stitchling; contact at 135 + 38.5 = 173.5
STITCHLING_2_SPAWN = (-480., -500.)   # build_stitchlings.py:29
CHECKS_PER_PLACEMENT = ('placement_valid', 'boss_reaches', 'stitchlings_reach', 'no_stuck',
                        'in_bounds', 'no_stitchling_overlap')
STUCK_CM, STUCK_LIMIT_S = 20., 3.
BOUNDS = (-1380., 1440., -1460., 1460.)
SAMPLE_S = .25
PAUSE_STATES = {1, 2, 4}
EXPECTED = {'boss': {'speed': 105., 'range': 380., 'close': 700.},
            'stitchling': {'speed': 55., 'range': 190., 'close': 350.}}
PLAYER_Z = 95.

# Corners: verify_full_room.py PAIRS. Edge points: inward of the kit placements in
# evidence/chamber/20261005T170149Z/chamber-kit-reviewed.json. Tech: the kit positions
# are current on 0387fe4 (map unchanged since 0a20f9f), but every kit prop sits outside
# the walls, so these are edge coverage, not prop avoidance. |x| = 1250/1300 and
# |y| = 1350 lie outside the room probe grid, hence P5's placement_valid check.
# Each entry: (name, px, py, occlusion). occlusion is None, or a dict with 'dir' (unit
# XY from the boss towards the player) or 'from' (a spawn whose line through the boss
# sets the direction).
PLACEMENTS = [
    ('corner_sw', -1300, -1350, None), ('corner_se', 1300, -1350, None),
    ('corner_nw', -1300, 1350, None), ('corner_ne', 1300, 1350, None),
    ('edge_w_s700', -1250, -700, None),   # was reverse_door_l (ReverseDoorL at -1580,-700)
    ('edge_w_n700', -1250, 700, None),    # was reverse_door_r (ReverseDoorR at -1580, 700)
    ('edge_w_n980', -1250, 980, None),    # was reverse_drum_r (ReverseDrumR at -1565, 980)
    ('edge_w_s450', -1250, -450, None),   # was reverse_drum_l (ReverseDrumL at -1565,-450)
    ('edge_n_x130', 130, 1250, None),     # was right_service_drums (130, 1590)
    ('edge_s_x850', 850, -1250, None),    # was left_service_drums (850,-1590)
    ('edge_e_s435', 1250, -435, None),    # was rear_drum (1570,-435)
    ('edge_e_n180', 1250, 180, None),     # was rear_bulkhead (1630, 180)
    # Boss between a stitchling and the player (P1). Player = boss + 300 * dir,
    # stitchling = boss - 320 * dir; positions come from the live boss each time.
    ('occlusion_east', None, None, {'dir': (1., 0.)}),
    ('occlusion_north', None, None, {'dir': (0., 1.)}),
    ('occlusion_s2_line', None, None, {'from': STITCHLING_2_SPAWN}),
]
LIKELY_FALSE = [p[0] + '_' + c for p in PLACEMENTS if p[3] for c in ('stitchlings_reach', 'no_stuck')]

levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
boss_class = u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_TeddyBoss')
minion_class = u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_Stitchling')
restart = u.load_asset('/Game/TeddyEncounter/Input/IA_Restart')
result = {'passed': False, 'map': MAP, 'checks': {}, 'cases': [], 'asset_writes': False,
          'thresholds': {'active_limit_s': ACTIVE_LIMIT_S, 'stuck_cm': STUCK_CM, 'stuck_limit_s': STUCK_LIMIT_S,
                         'bounds': BOUNDS, 'expected': EXPECTED, 'placement_tolerance_cm': PLACEMENT_TOLERANCE_CM,
                         'overlap': 'gap < r_i + r_j - %.1f cm' % OVERLAP_SLACK_CM,
                         'occlusion': {'player_cm': OCCLUSION_PLAYER_CM, 'gap_cm': OCCLUSION_GAP_CM},
                         'status': 'Tech proposal, pending Design'},
          'likely_false_until_avoidance': LIKELY_FALSE,
          'note': 'A creature that passes is frozen and becomes an obstacle for the others, as a creature '
                  'standing in wind-up would be.',
          'method': 'Teleport the player per placement (and, for occlusion cases, one stitchling, runtime '
                    'only), tick the existing creature graphs, sample XY traces every 0.25 s. '
                    'No builders, no saves.'}
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
    """Inject F5; True once a new world has a pawn, False after 10 s wall (P4: no raise)."""
    while not view():
        yield
    old = view()[0]
    sub = next(x for x in u.ObjectIterator(u.EnhancedInputLocalPlayerSubsystem) if x.get_world() == old)
    sub.inject_input_vector_for_action(restart, u.Vector(1, 0, 0), [], [])
    wall = time.monotonic()
    while True:
        yield
        found = view()
        if found and found[0] != old:
            return True
        if time.monotonic() - wall > 10:
            return False

def record_failed(name, reason, extra=None):
    """Record every per-placement check false with a reason, keeping the check count fixed."""
    for c in CHECKS_PER_PLACEMENT:
        result['checks'][name + '_' + c] = False
    case = {'name': name, 'passed': False, 'reason': reason}
    case.update(extra or {})
    result['cases'].append(case)

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

def run_placement(name, px, py, occlusion=None):
    yield from wait(.3)
    world, pawn, boss = view()
    creatures = [('boss', boss)] + [('stitchling_%d' % i, a) for i, a in
                                    enumerate(u.GameplayStatics.get_all_actors_of_class(world, minion_class))]
    for _, a in creatures:
        a.set_actor_tick_enabled(False)
    # Re-enabling tick resumes the chase from State 0; nothing but player fire causes State 4
    # (kept in PAUSE_STATES as documentation). No shots are fired here.
    occ = None
    if occlusion:
        bx, by = xy(boss)
        if 'from' in occlusion:
            fx, fy = occlusion['from']
            n = math.hypot(bx - fx, by - fy)
            dx, dy = (bx - fx) / n, (by - fy) / n
        else:
            dx, dy = occlusion['dir']
        px, py = bx + OCCLUSION_PLAYER_CM * dx, by + OCCLUSION_PLAYER_CM * dy
        spot = (bx - OCCLUSION_GAP_CM * dx, by - OCCLUSION_GAP_CM * dy)
        label, mover = min(creatures[1:], key=lambda c: math.dist(xy(c[1]), spot))
        z = mover.get_actor_location().z
        mover.set_actor_location(u.Vector(spot[0], spot[1], z), False, True)
        occ = {'boss_xy': [bx, by], 'dir': [dx, dy], 'stitchling': label, 'stitchling_target_xy': list(spot),
               'contact_after_cm': round(OCCLUSION_GAP_CM - boss.get_component_by_class(u.CapsuleComponent)
                                         .get_scaled_capsule_radius() - mover.get_component_by_class(
                                             u.CapsuleComponent).get_scaled_capsule_radius(), 1)}
    pawn.get_component_by_class(u.CharacterMovementComponent).stop_movement_immediately()
    pawn.set_actor_location(u.Vector(px, py, PLAYER_Z), False, True)
    yield from wait(.2)
    target = xy(pawn)
    # P5: the player must still be on the placement, else the creatures chase a displaced player.
    player_off = math.dist(target, (px, py))
    valid = player_off <= PLACEMENT_TOLERANCE_CM
    if occ:
        occ['stitchling_xy_after'] = list(xy(mover))
        occ['stitchling_off_cm'] = round(math.dist(xy(mover), spot), 1)
        valid = valid and occ['stitchling_off_cm'] <= PLACEMENT_TOLERANCE_CM
    if not valid:
        record_failed(name, 'placement invalid: player %.1f cm off (px, py)%s' % (
            player_off, '' if not occ else ', occlusion stitchling %.1f cm off' % occ['stitchling_off_cm']),
            {'player_xy': [px, py], 'player_actual_xy': list(target), 'occlusion': occ})
        return
    rows = {}
    for label, a in creatures:
        kind = 'boss' if label == 'boss' else 'stitchling'
        start_d = math.dist(xy(a), target)
        rows[label] = {'kind': kind, 'start_xy': xy(a), 'start_distance_cm': round(start_d, 1),
                       'range_cm': prop(a, 'AttackRange'), 'close_needed_cm': EXPECTED[kind]['close'],
                       'active_s': 0., 'passed': False, 'trace': [], 'in_range': [], 'out_of_bounds': []}
        a.set_actor_tick_enabled(True)
    # Tech (confirmed): get_scaled_capsule_radius() is 38.5 (110 x 0.35). Read per actor (P2).
    radii = {}
    for label, a in creatures:
        capsule = a.get_component_by_class(u.CapsuleComponent)
        radii[label] = capsule.get_scaled_capsule_radius() if capsule else 0.
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
            minions = [(label, a) for label, a in creatures if label != 'boss' and prop(a, 'Health') > 0]
            for i in range(len(minions)):
                for j in range(i + 1, len(minions)):
                    (li, ai), (lj, aj) = minions[i], minions[j]
                    gap = math.dist(xy(ai), xy(aj))
                    # P2: blocking capsules stop at contact (~77 cm); '<=' flagged mere contact.
                    if gap < radii[li] + radii[lj] - OVERLAP_SLACK_CM:
                        overlaps.append({'t': round(t, 2), 'pair': [li, lj], 'gap_cm': round(gap, 1)})
        if all(r['passed'] or r.get('timed_out') for r in rows.values()):
            break
    for row in rows.values():
        row['longest_stuck_s'] = longest_stuck(row['trace'], row['in_range'])
        row.pop('in_range')
    stitch = [r for k, r in rows.items() if k != 'boss']
    result['checks'][name + '_placement_valid'] = True
    result['checks'][name + '_boss_reaches'] = rows['boss']['passed']
    result['checks'][name + '_stitchlings_reach'] = len(stitch) == 3 and all(r['passed'] for r in stitch)
    result['checks'][name + '_no_stuck'] = all(r['longest_stuck_s'] <= STUCK_LIMIT_S for r in rows.values())
    result['checks'][name + '_in_bounds'] = not any(r['out_of_bounds'] for r in rows.values())
    result['checks'][name + '_no_stitchling_overlap'] = not overlaps
    result['cases'].append({'name': name, 'player_xy': [px, py], 'player_actual_xy': list(target),
                            'effective_capsule_radius_cm': radii, 'occlusion': occ,
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
    failed_reloads = 0
    for name, px, py, occlusion in PLACEMENTS:
        # P6: every placement, including the first, starts 0.3 s after a fresh F5.
        if not (yield from reload()):
            failed_reloads += 1
            record_failed(name, 'F5 produced no new PIE world within 10 s wall time')
            write_receipt(partial=True)
            if failed_reloads >= 2:
                raise RuntimeError('F5 failed twice in a row; cannot continue the placements')
            continue
        failed_reloads = 0
        yield from run_placement(name, px, py, occlusion)
        write_receipt(partial=True)

def write_receipt(partial):
    result['expected_check_count'] = 4 + len(CHECKS_PER_PLACEMENT) * len(PLACEMENTS)
    result['partial'] = partial
    result['passed'] = (not partial and not result.get('error')
                        and len(result['checks']) == result['expected_check_count']
                        and all(result['checks'].values()))
    result['wall_seconds'] = time.monotonic() - state['start']
    (OUT / 'receipt.json').write_text(json.dumps(result, indent=2, default=str))

def finish(error=None):
    if state['done']:
        return
    state['done'] = True
    if error:
        result['error'] = error
    write_receipt(partial=False)
    finish_editor(handle)

test = run()

def tick(dt):
    try:
        if time.monotonic() - state['start'] > INTERNAL_LIMIT_S:
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
