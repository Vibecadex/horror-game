"""B5 soft-lock matrix. Frame-driven, read-only, no asset or map saves.

Run only through tools/run_encounter_test.py, with no other editor or game open.

Every case performs an action, then F5 (the saved IA_Restart action), and must
recover after the reload:
  not paused; BP_CombatCamera becomes the view target within 1 s of game time
  (it is set after a 0.2 s Delay); then held Move input shifts the player more
  than 100 cm within 2 s of game time; boss 300 HP; player 100 HP; 3 living
  stitchlings; the BP_CombatCamera actor itself moves more than 10 cm in XY
  (measured from after the view-target hand-off, with Move held 0.4 s past the
  100 cm walk because VInterpTo speed 5 lags).
BP_CombatCamera frames the player/boss midpoint, not the player (Tech, from
fix_encounter_camera.py), so a +100 cm walk moves its target about +57 cm and
the actor about 35-50 cm: the 10 cm threshold holds when measured this way.
Each wait also has a wall-clock cap (4 s past the requested game time), so a
reload that stalls fails the case instead of hanging the matrix; a paused world
fails the wait at once. The startup wait(1) alone gets a 60 s cap, because the
first PIE game second costs ~5 s wall on a cold worktree (receipt field
startup_wall_s_for_1_game_s).

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
                                 The resume press is a separate key press: release Pause
                                 (inject 0), wait one frame plus RESUME_RELEASE_S real time
                                 (the world is paused, so no game-time waits), then press.
                                 Rerun aced6f9 pressed again on the frame the pause was
                                 seen and never resumed (esc_resumes_ok false). The press
                                 gap is receipt data (esc_press_gap_s).
  11 f5_burst_five_in_two_seconds up to five F5 presses inside 2 s wall time, injected on
                                 alternate frames whenever a world exists (view() None =
                                 loading, skipped, not a failure); then wait out the
                                 blocking OpenLevel reload and grade the final recovery only.
                                 presses_s and the world each press landed in are data.

Known-bug checks (2, from the PR #1 review). Expected FALSE until fixed. They
are ordinary failing checks, not waived, so today's receipt should read 11/13
with passed=false:
  12 known_bug_boss_does_not_attack_dead_player
  13 known_bug_dead_stitchlings_do_not_replay_death

Total 13. A clean pass (13/13) needs both bugs fixed.

Observation, not a check: F5 opens '/Game/Maps/TeddyEncounter' (build_combat.py
hard-codes it).

Review: Horror Unreal Tech, 2026-10-08 (S1-S6 applied).
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
VIEW_TARGET_S = 1.      # BP_CombatCamera becomes the view target after Delay .2
CAMERA_SETTLE_S = .4    # keep holding Move after the 100 cm walk; VInterpTo speed 5 lags
WALL_CAP_S = 4.         # wall-clock cap on game-time waits, so a paused world cannot hang a case
RESUME_RELEASE_S = .12  # real-time gap after releasing Pause before the resume press
                         # (verify_encounter_repair.py: inject 0, then press after > .12 s wall)
STARTUP_WALL_CAP_S = 60. # first PIE game second costs ~4-5 s wall on a cold worktree (DDC/asset compile);
                         # ai_paths 20261008: 4.81 s from PIE start to its first F5 after wait(1)
# Loaded inside the try at the bottom (S6), so a load failure still writes a receipt.
boss_class = minion_class = camera_class = None
actions = {}

def load_classes():
    global boss_class, minion_class, camera_class
    boss_class = u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_TeddyBoss')
    minion_class = u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_Stitchling')
    camera_class = u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_CombatCamera')
    actions.update({n: u.load_asset('/Game/Variant_TwinStick/Input/Actions/IA_Action_' + n) for n in ['Move', 'Dash']})
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
    v = view()
    return u.GameplayStatics.get_time_seconds(v[0]) if v else None

def same(a, b):
    return bool(a) and bool(b) and a.get_path_name() == b.get_path_name()

def wait_view(limit=10.):
    """Yield until a world with a pawn exists (a reload in progress is loading, not a failure)."""
    wall = time.monotonic()
    while not view():
        if time.monotonic() - wall > limit:
            raise RuntimeError('no PIE world with a pawn for %.0f s' % limit)
        yield

def pos(actor):
    v = actor.get_actor_location()
    return (v.x, v.y, v.z)

def hp(actor):
    return actor.get_editor_property('Health')

def stitchlings(world):
    return list(u.GameplayStatics.get_all_actors_of_class(world, minion_class))

def inject(name, value=1.):
    v = view()
    if not v:
        return False
    world = v[0]
    sub = next(x for x in u.ObjectIterator(u.EnhancedInputLocalPlayerSubsystem) if x.get_world() == world)
    sub.inject_input_vector_for_action(actions[name], u.Vector(value, 0, 0), [], [])
    return True

def freeze(boss=True, minions=True):
    world, pawn, pc, b = view()
    for a in u.GameplayStatics.get_all_actors_of_class(world, u.Character):
        if a == pawn:
            continue
        is_boss = a.get_class().get_path_name() == b.get_class().get_path_name()
        if (is_boss and boss) or (not is_boss and minions):
            a.set_actor_tick_enabled(False)

def wait(seconds, wall_cap=WALL_CAP_S):
    yield from wait_view()
    start = now()
    wall = time.monotonic()
    while True:
        v = view()
        t = u.GameplayStatics.get_time_seconds(v[0]) if v else None
        if t is not None and t - start >= seconds:
            return
        if v and u.GameplayStatics.is_game_paused(v[0]):
            raise RuntimeError('wait(%s): world is paused' % seconds)
        if time.monotonic() - wall > seconds + wall_cap:
            raise RuntimeError('wait(%s): game time advanced %s s in %.1f s wall (world %s)' % (
                seconds, None if t is None else round(t - start, 3), time.monotonic() - wall,
                'present' if v else 'missing'))
        yield

def until_paused(want, limit=1.):
    """S5: poll is_game_paused for up to `limit` wall seconds instead of a fixed wait."""
    wall = time.monotonic()
    while time.monotonic() - wall < limit:
        v = view()
        if v and u.GameplayStatics.is_game_paused(v[0]) == want:
            return True
        yield
    v = view()
    return bool(v) and u.GameplayStatics.is_game_paused(v[0]) == want

def esc_pause_resume():
    """Esc pauses, then a distinct Esc resumes. Returns the extra fields for the case.

    The resume press must not land while the pause press still reads as held: release
    Pause (inject 0), yield one frame, then wait RESUME_RELEASE_S of wall time (the world
    is paused, so game time does not advance), then press. The unpause poll keeps its
    real-time cap (until_paused, 1 s wall)."""
    inject('Pause')
    first_press = time.monotonic()
    esc_pauses = yield from until_paused(True)
    released = inject('Pause', 0.)
    release_wall = time.monotonic()
    frames = 0
    yield
    frames += 1
    gap_start = time.monotonic()
    while time.monotonic() - gap_start < RESUME_RELEASE_S:
        yield
        frames += 1
    second_injected = inject('Pause')
    second_press = time.monotonic()
    esc_resumes = yield from until_paused(False)
    return {'esc_pauses_ok': esc_pauses, 'esc_resumes_ok': esc_resumes,
            'esc_press_gap_s': round(second_press - first_press, 3),
            'esc_release_to_press_s': round(second_press - release_wall, 3),
            'esc_release_frames': frames,
            'esc_release_injected': released, 'esc_resume_press_injected': second_injected}

def reload():
    """Inject F5; return True once a new PIE world has a possessed pawn, False after 10 s."""
    yield from wait_view()
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
    yield from wait_view()
    if u.GameplayStatics.is_game_paused(view()[0]):
        inject('Pause')
        yield from until_paused(False)
    if not (yield from reload()):
        raise RuntimeError(name + ': F5 failed twice; cannot continue the matrix')

def recovery(name, extra=None):
    """After a reload: hold Move for up to RECOVER_S game seconds and record the gate."""
    yield from wait_view()
    world, pawn, pc, boss = view()
    freeze()
    reload_t = now()
    hp_at_reload = {'boss': hp(boss), 'player': hp(pawn),
                    'living_stitchlings': len([a for a in stitchlings(world) if hp(a) > 0])}
    paused_at_reload = u.GameplayStatics.is_game_paused(world)
    # S1: the camera manager reports the pawn's view until BP_CombatCamera becomes the view
    # target after Delay .2, then snaps ~1,700-2,100 cm. Wait for the hand-off and measure
    # the camera actor, or '> 10 cm' passes without any tracking.
    def combat_camera():
        cams = list(u.GameplayStatics.get_all_actors_of_class(world, camera_class)) if camera_class else []
        return cams[0] if cams else None
    cam = combat_camera()
    wall = time.monotonic()
    while not (cam and same(pc.get_view_target(), cam)):
        t = now()
        if (t is not None and t - reload_t >= VIEW_TARGET_S) or time.monotonic() - wall > VIEW_TARGET_S + WALL_CAP_S:
            break
        yield
        cam = cam or combat_camera()
    view_target_ok = bool(cam) and same(pc.get_view_target(), cam)
    t = now()
    seconds_to_view_target = round(t - reload_t, 3) if t is not None else None
    start, began = pos(pawn), now()
    cam_start = cam.get_actor_location() if cam else None
    moved = 0.
    walked_at = None
    wall = time.monotonic()
    while time.monotonic() - wall < RECOVER_S + CAMERA_SETTLE_S + WALL_CAP_S:
        t = now()
        if t is None:
            yield
            continue
        t -= began
        if walked_at is None:
            if t >= RECOVER_S:
                break
            moved = math.dist(pos(pawn)[:2], start[:2])
            if moved > 100:
                walked_at = t
        elif t - walked_at >= CAMERA_SETTLE_S:
            break
        inject('Move', 1.)
        yield
    cam_end = cam.get_actor_location() if cam else None
    cam_moved = math.dist((cam_end.x, cam_end.y), (cam_start.x, cam_start.y)) if cam else 0.
    rec = {'not_paused': not paused_at_reload and not u.GameplayStatics.is_game_paused(world),
           'moved_cm': round(moved, 1),
           'seconds_to_100_cm': round(walked_at, 3) if walked_at is not None else None,
           'boss_hp': hp_at_reload['boss'], 'player_hp': hp_at_reload['player'],
           'living_stitchlings': hp_at_reload['living_stitchlings'],
           'combat_camera_found': bool(cam), 'view_target_is_combat_camera': view_target_ok,
           'seconds_to_view_target': seconds_to_view_target,
           'view_target': pc.get_view_target().get_name() if pc.get_view_target() else None,
           'camera_moved_cm': round(cam_moved, 1), 'camera_tracks': view_target_ok and cam_moved > 10}
    passed = (rec['not_paused'] and rec['moved_cm'] > 100 and rec['boss_hp'] == 300 and rec['player_hp'] == 100
              and rec['living_stitchlings'] == 3 and rec['view_target_is_combat_camera'] and rec['camera_tracks'])
    if extra:
        rec.update(extra)
        passed = passed and all(v for k, v in extra.items() if k.endswith('_ok'))
    result['cases'].append({'name': name, 'recovery': rec, 'passed': passed})
    result['checks'][name] = passed

def anim_asset(mesh):
    """verify_parity_runtime.py's pattern: the single-node instance's animation asset path."""
    if not mesh:
        return None
    instance = mesh.get_anim_instance()
    asset = instance.get_animation_asset() if isinstance(instance, u.AnimSingleNodeInstance) else None
    return asset.get_path_name() if asset else None

def kill(actor, causer):
    u.GameplayStatics.apply_damage(actor, 1000, None, causer, u.DamageType)

def run():
    yield from wait_view(60.)
    warm = time.monotonic()
    yield from wait(1, wall_cap=STARTUP_WALL_CAP_S)
    result['startup_wall_s_for_1_game_s'] = round(time.monotonic() - warm, 3)
    freeze()

    # 1 idle
    yield from f5_case('idle_f5')

    # 2 mid-dash. S4: prove a dash actually started (DodgeUntil changed or speed > 900 cm/s,
    # the keys suite's threshold) before F5.
    yield from wait(.2)
    pawn = view()[1]
    du_before = pawn.get_editor_property('DodgeUntil')
    inject('Move', 1.)
    inject('Dash', 1.)
    peak = 0.
    for _ in range(2):
        yield
        peak = max(peak, pawn.get_velocity().length())
    dash_started = pawn.get_editor_property('DodgeUntil') != du_before or peak > 900
    yield from f5_case('dash_f5', {'dash_started_ok': dash_started, 'dash_peak_speed': round(peak, 1)})

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
    paused_ok = yield from until_paused(True)
    yield from f5_case('paused_f5', {'was_paused_ok': paused_ok})

    # 9 victory screen Esc
    world, pawn, pc, boss = view()
    kill(boss, pawn)
    yield from wait(.6)
    esc = yield from esc_pause_resume()
    yield from f5_case('victory_escape', esc)

    # 10 defeat screen Esc
    world, pawn, pc, boss = view()
    kill(pawn, boss)
    yield from wait(.6)
    esc = yield from esc_pause_resume()
    yield from f5_case('defeat_escape', esc)

    # 11 F5 burst. S2 (Tech): OpenLevel on PIE is a blocking travel, view() is None across it,
    # and IA_Restart uses InputTriggerPressed, so consecutive-frame injection is one press.
    # Inject on alternate frames whenever a world exists, up to five presses inside 2 s wall
    # time; None means loading, not failure. A press in the hand-off frame is probably dropped.
    # The case is graded on the final recovery only; press count and worlds are data.
    yield from wait(.3)
    wall = time.monotonic()
    presses, press_world, worlds, k = [], [], [], 0
    while len(presses) < 5 and time.monotonic() - wall < 2:
        v = view()
        if v:
            k += 1
            if k % 2 and inject('Restart'):
                idx = next((i for i, x in enumerate(worlds) if x == v[0]), None)
                if idx is None:
                    worlds.append(v[0])
                    idx = len(worlds) - 1
                presses.append(round(time.monotonic() - wall, 3))
                press_world.append(idx)
        yield
    burst_s = time.monotonic() - wall
    # Wait out the last reload: a world with a pawn that stays the same world for 1 s wall.
    settle, stable_since, last = time.monotonic(), None, None
    while True:
        v = view()
        if v and last is not None and v[0] == last:
            if time.monotonic() - stable_since >= 1.:
                break
        else:
            last, stable_since = (v[0] if v else None), time.monotonic()
        if time.monotonic() - settle > 15:
            raise RuntimeError('F5 burst: no stable world 15 s after the burst')
        yield
    yield from recovery('f5_burst_five_in_two_seconds',
                        {'presses_s': presses, 'press_world_index': press_world,
                         'distinct_worlds_pressed': len(worlds), 'burst_wall_s': round(burst_s, 3),
                         'presses_landed': len(presses)})

    # Known bug 2: already-dead stitchlings replay Defeat when the boss dies.
    # BP_Stitchling's tick checks only the boss's health (build_stitchlings.py:20-23); the
    # boss-dead branch (Health 0, State 3, PlayAnimation A_Teddy_DefeatGrounded, collision
    # off, hide warning, stop tick) has no own-health check, and the stitchling's own damage
    # death does not stop its tick. Deterministic from source (Tech S3).
    world, pawn, pc, boss = view()
    victims = stitchlings(world)
    for a in victims:
        a.set_actor_tick_enabled(True)
        kill(a, pawn)
    yield from wait(2.5)
    before = {}
    for a in victims:
        mesh = a.get_component_by_class(u.SkeletalMeshComponent)
        before[a.get_name()] = {'tick': a.is_actor_tick_enabled(), 'anim_position_s': mesh.get_position() if mesh else None,
                                'anim_asset': anim_asset(mesh)}
    kill(boss, pawn)
    yield from wait(.3)
    after = {}
    replayed = False
    for a in victims:
        mesh = a.get_component_by_class(u.SkeletalMeshComponent)
        row = {'tick': a.is_actor_tick_enabled(), 'anim_position_s': mesh.get_position() if mesh else None,
               'anim_asset': anim_asset(mesh)}
        b = before[a.get_name()]
        # Tech (confirmed): get_position() reads the single-node clip time; after 2.5 s it sits
        # at the clip end (2.367 s) and a replay reads ~0.3 at +0.3 s. The tick on->off flip
        # is the stronger, source-level signal that the dead branch ran.
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
    load_classes()
    assert levels.load_level(MAP)
    levels.editor_request_begin_play()
    handle = u.register_slate_post_tick_callback(tick)
except Exception:
    finish(traceback.format_exc())
