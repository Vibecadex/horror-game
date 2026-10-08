"""B5 soft-lock matrix. Frame-driven, read-only, no asset or map saves.

Run only through tools/run_encounter_test.py, with no other editor or game open.

Every case performs an action, then F5 (the saved IA_Restart action), and must
recover within 2 s of game time after the reload:
  not paused; held Move input shifts the player more than 100 cm;
  boss 300 HP; player 100 HP; 3 living stitchlings; the camera tracks the player.

Recovery checks (11, expected true):
   1 idle_f5                      F5 from an idle start
   2 dash_f5                      F5 mid-dash
   3 boss_windup_f5               F5 while the boss is in State 1 (wind-up)
   4 boss_strike_f5               F5 while the boss is in State 2 (strike recovery)
   5 player_dead_f5               F5 after player death
   6 boss_dead_f5                 F5 after boss death
   7 all_stitchlings_dead_f5      F5 after all three stitchlings die
   8 paused_f5                    F5 while paused
   9 victory_escape               boss dead; Esc pauses, Esc resumes, then F5 recovers
  10 defeat_escape                player dead; Esc pauses, Esc resumes, then F5 recovers
  11 f5_burst_five_in_two_seconds five F5 presses inside 2 s wall time, then recovery

Known-bug checks (2, from the PR #1 review). Expected FALSE until fixed. They
are ordinary failing checks, not waived, so today's receipt should read 11/13
with passed=false:
  12 known_bug_boss_does_not_attack_dead_player
  13 known_bug_dead_stitchlings_do_not_replay_death

Total 13. A clean pass (13/13) needs both bugs fixed.

Observation, not a check: F5 opens '/Game/Maps/TeddyEncounter' (build_combat.py
hard-codes it).
"""
import sys, os, time, json, math, traceback
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from finish_editor import finish_editor

OUT = Path(os.environ['TEDDY_TEST_DIR'])
MAP = '/Game/Maps/TeddyEncounter'
RECOVER_S = 2.
levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
boss_class = u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_TeddyBoss')
minion_class = u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_Stitchling')
actions = {n: u.load_asset('/Game/Variant_TwinStick/Input/Actions/IA_Action_' + n) for n in ['Move', 'Dash']}
actions.update({n: u.load_asset('/Game/TeddyEncounter/Input/IA_' + n) for n in ['Pause', 'Restart']})
result = {'passed': False, 'map': MAP, 'checks': {}, 'cases': [],
          'expected_to_fail_until_fixed': ['known_bug_boss_does_not_attack_dead_player',
                                           'known_bug_dead_stitchlings_do_not_replay_death'],
          'asset_writes': False, 'physical_device_verified': False,
          'method': 'Enhanced Input injection of the saved Move/Dash/Pause/Restart actions; '
                    'labelled apply_damage calls to reach death states; creatures frozen between cases.',
          'observation': "F5 runs GameplayStatics.OpenLevel(LevelName='/Game/Maps/TeddyEncounter') per "
                         'tools/build_combat.py, so F5 from TeddyChamberParity or a copied map lands on '
                         'TeddyEncounter. Open question for Design/Tech; not a check.'}
state = {'start': time.monotonic(), 'done': False}
handle = None

def view():
    world = editor.get_game_world()
    if not world:
        return None
    pawn = u.GameplayStatics.get_player_pawn(world, 0)
    pc = u.GameplayStatics.get_player_controller(world, 0)
    bosses = u.GameplayStatics.get_all_actors_of_class(world, boss_class)
    if not pawn or not pc or not bosses:
        return None
    return world, pawn, pc, bosses[0]

def now():
    return u.GameplayStatics.get_time_seconds(view()[0])

def pos(actor):
    v = actor.get_actor_location()
    return (v.x, v.y, v.z)

def hp(actor):
    return actor.get_editor_property('Health')

def stitchlings(world):
    return list(u.GameplayStatics.get_all_actors_of_class(world, minion_class))

def inject(name, value=1.):
    world = view()[0]
    sub = next(x for x in u.ObjectIterator(u.EnhancedInputLocalPlayerSubsystem) if x.get_world() == world)
    sub.inject_input_vector_for_action(actions[name], u.Vector(value, 0, 0), [], [])

def freeze(boss=True, minions=True):
    world, pawn, pc, b = view()
    for a in u.GameplayStatics.get_all_actors_of_class(world, u.Character):
        if a == pawn:
            continue
        is_boss = a.get_class() == b.get_class()
        if (is_boss and boss) or (not is_boss and minions):
            a.set_actor_tick_enabled(False)

def wait(seconds):
    start = now()
    while not view() or now() - start < seconds:
        yield

def reload():
    """Inject F5; return True once a new PIE world has a possessed pawn, False after 10 s."""
    old = view()[0]
    inject('Restart')
    wall = time.monotonic()
    while True:
        yield
        found = view()
        if found and found[0] != old:
            return True
        if time.monotonic() - wall > 10:
            return False

def f5_case(name, extra=None):
    """F5, then the recovery gate. A dead F5 is a failed case, not an aborted run."""
    if (yield from reload()):
        yield from recovery(name, extra)
        return
    result['cases'].append({'name': name, 'passed': False, 'extra': extra,
                            'reason': 'F5 produced no new PIE world within 10 s wall time'})
    result['checks'][name] = False
    if u.GameplayStatics.is_game_paused(view()[0]):
        inject('Pause')
        wall = time.monotonic()
        while time.monotonic() - wall < .4:
            yield
    if not (yield from reload()):
        raise RuntimeError(name + ': F5 failed twice; cannot continue the matrix')

def recovery(name, extra=None):
    """After a reload: hold Move for up to RECOVER_S game seconds and record the gate."""
    yield from wait(.05)
    world, pawn, pc, boss = view()
    freeze()
    cam = pc.player_camera_manager
    start, began = pos(pawn), now()
    cam_start = cam.get_camera_location()
    hp_at_reload = {'boss': hp(boss), 'player': hp(pawn),
                    'living_stitchlings': len([a for a in stitchlings(world) if hp(a) > 0])}
    paused_at_reload = u.GameplayStatics.is_game_paused(world)
    moved = 0.
    while now() - began < RECOVER_S:
        inject('Move', 1.)
        moved = math.dist(pos(pawn)[:2], start[:2])
        if moved > 100:
            break
        yield
    cam_end = cam.get_camera_location()
    cam_moved = math.dist((cam_end.x, cam_end.y), (cam_start.x, cam_start.y))
    # Tracking = the player camera manager's location (as verify_parity_runtime.py reads it)
    # moved more than 10 cm in XY while the player walked more than 100 cm.
    # TODO(Tech): confirm BP_CombatCamera follows the pawn in XY rather than holding a fixed
    # framing. If it is fixed by design, this criterion has to change.
    rec = {'not_paused': not paused_at_reload and not u.GameplayStatics.is_game_paused(world),
           'moved_cm': round(moved, 1), 'seconds_to_100_cm': round(now() - began, 3),
           'boss_hp': hp_at_reload['boss'], 'player_hp': hp_at_reload['player'],
           'living_stitchlings': hp_at_reload['living_stitchlings'],
           'camera_moved_cm': round(cam_moved, 1), 'camera_tracks': cam_moved > 10}
    passed = (rec['not_paused'] and rec['moved_cm'] > 100 and rec['boss_hp'] == 300 and rec['player_hp'] == 100
              and rec['living_stitchlings'] == 3 and rec['camera_tracks'])
    if extra:
        rec.update(extra)
        passed = passed and all(v for k, v in extra.items() if k.endswith('_ok'))
    result['cases'].append({'name': name, 'recovery': rec, 'passed': passed})
    result['checks'][name] = passed

def kill(actor, causer):
    u.GameplayStatics.apply_damage(actor, 1000, None, causer, u.DamageType)

def run():
    while not view():
        yield
    yield from wait(1)
    freeze()

    # 1 idle
    yield from f5_case('idle_f5')

    # 2 mid-dash
    yield from wait(.2)
    inject('Move', 1.)
    inject('Dash', 1.)
    yield
    yield
    yield from f5_case('dash_f5')

    # 3 boss wind-up
    world, pawn, pc, boss = view()
    pawn.set_actor_location(boss.get_actor_location() + u.Vector(-300, 0, -142), False, False)
    boss.set_actor_tick_enabled(True)
    start = now()
    while view()[3].get_editor_property('State') != 1:
        if now() - start > 15:
            raise RuntimeError('boss never entered wind-up')
        yield
    yield from f5_case('boss_windup_f5')

    # 4 boss strike recovery (State 2)
    world, pawn, pc, boss = view()
    pawn.set_actor_location(boss.get_actor_location() + u.Vector(-300, 0, -142), False, False)
    boss.set_actor_tick_enabled(True)
    start = now()
    while view()[3].get_editor_property('State') != 2:
        if now() - start > 15:
            raise RuntimeError('boss never reached strike recovery')
        yield
    yield from f5_case('boss_strike_f5')

    # 5 player dead, plus known bug 1: boss keeps attacking a dead player
    world, pawn, pc, boss = view()
    pawn.set_actor_location(boss.get_actor_location() + u.Vector(-300, 0, -142), False, False)
    kill(pawn, boss)
    yield from wait(.2)
    boss.set_actor_tick_enabled(True)
    attacks_before = boss.get_editor_property('Attacks')
    yield from wait(3)
    world, pawn, pc, boss = view()
    attacks_after = boss.get_editor_property('Attacks')
    result['checks']['known_bug_boss_does_not_attack_dead_player'] = hp(pawn) <= 0 and attacks_after == attacks_before
    result['known_bug_detail_dead_player'] = {'player_hp': hp(pawn), 'attacks_before': attacks_before,
                                              'attacks_after_3s': attacks_after, 'boss_state': boss.get_editor_property('State')}
    freeze()
    yield from f5_case('player_dead_f5')

    # 6 boss dead
    world, pawn, pc, boss = view()
    kill(boss, pawn)
    yield from wait(.5)
    yield from f5_case('boss_dead_f5')

    # 7 all stitchlings dead
    world, pawn, pc, boss = view()
    for a in stitchlings(world):
        kill(a, pawn)
    yield from wait(.5)
    yield from f5_case('all_stitchlings_dead_f5')

    # 8 paused
    inject('Pause')
    wall = time.monotonic()
    while time.monotonic() - wall < .4:
        yield
    paused_ok = u.GameplayStatics.is_game_paused(view()[0])
    yield from f5_case('paused_f5', {'was_paused_ok': paused_ok})

    # 9 victory screen Esc
    world, pawn, pc, boss = view()
    kill(boss, pawn)
    yield from wait(.6)
    inject('Pause')
    wall = time.monotonic()
    while time.monotonic() - wall < .4:
        yield
    esc_pauses = u.GameplayStatics.is_game_paused(view()[0])
    inject('Pause')
    wall = time.monotonic()
    while time.monotonic() - wall < .4:
        yield
    esc_resumes = not u.GameplayStatics.is_game_paused(view()[0])
    yield from f5_case('victory_escape', {'esc_pauses_ok': esc_pauses, 'esc_resumes_ok': esc_resumes})

    # 10 defeat screen Esc
    world, pawn, pc, boss = view()
    kill(pawn, boss)
    yield from wait(.6)
    inject('Pause')
    wall = time.monotonic()
    while time.monotonic() - wall < .4:
        yield
    esc_pauses = u.GameplayStatics.is_game_paused(view()[0])
    inject('Pause')
    wall = time.monotonic()
    while time.monotonic() - wall < .4:
        yield
    esc_resumes = not u.GameplayStatics.is_game_paused(view()[0])
    yield from f5_case('defeat_escape', {'esc_pauses_ok': esc_pauses, 'esc_resumes_ok': esc_resumes})

    # 11 five F5 presses inside 2 s of wall time
    # TODO(Tech): confirm IA_Restart can be injected during the PIE OpenLevel hand-off.
    # Presses are skipped while no world exists; fewer than 5 fails five_presses_ok,
    # which would be a harness limit, not a game soft-lock. Read presses_s before filing.
    yield from wait(.3)
    wall = time.monotonic()
    presses = []
    while len(presses) < 5 and time.monotonic() - wall < 2:
        if view():
            inject('Restart')
            presses.append(round(time.monotonic() - wall, 3))
        target = time.monotonic() + .35
        while time.monotonic() < target:
            yield
    burst_s = time.monotonic() - wall
    settle = time.monotonic()
    while time.monotonic() - settle < 3:
        yield
    while not view():
        yield
    yield from recovery('f5_burst_five_in_two_seconds',
                        {'presses_s': presses, 'burst_wall_s': round(burst_s, 3),
                         'five_presses_ok': len(presses) == 5, 'inside_two_seconds_ok': presses[-1] <= 2 if presses else False})

    # Known bug 2: already-dead stitchlings replay Defeat when the boss dies.
    # BP_Stitchling's tick runs the boss-dead branch (Health 0, State 3, PlayAnimation
    # A_Teddy_Defeat, collision off, hide warning, stop tick) once the boss dies,
    # without checking whether the stitchling was already dead.
    world, pawn, pc, boss = view()
    victims = stitchlings(world)
    for a in victims:
        a.set_actor_tick_enabled(True)
        kill(a, pawn)
    yield from wait(2.5)
    before = {}
    for a in victims:
        mesh = a.get_component_by_class(u.SkeletalMeshComponent)
        before[a.get_name()] = {'tick': a.is_actor_tick_enabled(), 'anim_position_s': mesh.get_position() if mesh else None}
    kill(boss, pawn)
    yield from wait(.3)
    after = {}
    replayed = False
    for a in victims:
        mesh = a.get_component_by_class(u.SkeletalMeshComponent)
        row = {'tick': a.is_actor_tick_enabled(), 'anim_position_s': mesh.get_position() if mesh else None}
        b = before[a.get_name()]
        # TODO(Tech): confirm SkeletalMeshComponent.get_position() reads the single-node
        # clip time in Python. A restart reads as a position that jumped back toward 0;
        # tick switching from on to off is the second signal that the dead branch ran.
        restarted = (b['anim_position_s'] is not None and row['anim_position_s'] is not None
                     and row['anim_position_s'] + .05 < b['anim_position_s'])
        tick_flipped = b['tick'] and not row['tick']
        row['replay_detected'] = restarted or tick_flipped
        replayed = replayed or row['replay_detected']
        after[a.get_name()] = row
    result['checks']['known_bug_dead_stitchlings_do_not_replay_death'] = not replayed
    result['known_bug_detail_death_replay'] = {'before_boss_death': before, 'after_boss_death': after}

def finish(error=None):
    if state['done']:
        return
    state['done'] = True
    if error:
        result['error'] = error
    result['expected_check_count'] = 13
    result['passed'] = not error and len(result['checks']) == 13 and all(result['checks'].values())
    result['wall_seconds'] = time.monotonic() - state['start']
    (OUT / 'receipt.json').write_text(json.dumps(result, indent=2, default=str))
    finish_editor(handle)

test = run()

def tick(dt):
    try:
        if time.monotonic() - state['start'] > 300:
            raise RuntimeError('Soft-lock matrix timed out after ' + str(len(result['cases'])) + ' cases')
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
