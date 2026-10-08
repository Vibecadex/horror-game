"""v2 of the edge suite. Adds an in-radius evasion proof, the slam timer,
dodge cooldown and i-frame window, plus a negative control at the evade's end point.

Does not edit or import tools/verify_encounter_edges.py. Same frame-driven
pattern and receipt shape as that script. Run only through
tools/run_encounter_test.py. No asset or map saves.

v1's 13 checks are reproduced first (stages 0-15, same staging as v1). The new checks follow:

  14 strike_radius_is_475_cm            StrikeRange read from the live boss (CDO also logged)
  15 evade_inside_strike_radius         dash accepted, XY and 3D distance < radius at the
                                        Attacks increment, strike inside the i-frame window
                                        (game <= first DodgeUntil), HP unchanged (distances logged)
  16 slam_timer_0_92_s                  game time from first State==1 frame to the Attacks
                                        increment, in [0.92 - 0.005, 0.92 + max(0.05, max_dt + 0.005)].
                                        One-sided by construction (reads in [0.92, 0.92 + dt)),
                                        max_dt is the largest measured frame time. This is the
                                        Blueprint timer, not the clip's visual impact (Attack peaks ~0.67 s).
  17 dodge_cooldown                     Blueprint-time gap between two accepted dashes
                                        (DodgeUntil - 0.26 each), in [0.8 - 0.001, 0.8 + 2 * max_dt + 0.01],
                                        and >= 3 Dash presses logged before the first NextDodge
                                        (so the cooldown rejected at least one press)
  18 iframes_block_damage_inside_window 10 damage on the second dash's first frame, HP unchanged
  19 iframes_expire                     10 damage 0.02 s after DodgeUntil, HP falls
  20 undodged_strike_at_evade_end_reduces_hp   negative control: F5, boss wound up from 200 cm,
                                        then at the same StateAge the player is moved (no dash)
                                        to the offset where check 15's evade ended. The strike
                                        must land within 15 cm of that 3D separation and HP must fall.

Data only (not checks): undodged_strike_at_200cm (the old 245 cm 3D control, kept as a
record), v2_dash (dash start/end and direction, runtime evidence for Move Y -> world +Y).
If the first v2 dash is not accepted, checks 17-19 are recorded false and the run continues.

v1's evades_actual_boss_strike is kept for parity. It can pass with the
player out of range (622 cm XY / 638 cm 3D on 2026-10-08); its distance is logged as evade_end.

Measured dodge (Tech, 5 Oct telemetry): about 300 cm per dash, not ENCOUNTER.md's 345-350 cm.
At 200 cm XY (245 cm 3D) a sideways dash ends at about 370-405 cm 3D, inside 475.

Expected: 13 + 7 = 20 checks, all true.
Review: Horror Unreal Tech, 2026-10-08 (E1-E6 applied).
"""
import sys, os, time, json, traceback, math
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from png_evidence import decode_png
from finish_editor import finish_editor

OUT = Path(os.environ['TEDDY_TEST_DIR'])
lev = u.get_editor_subsystem(u.LevelEditorSubsystem)
ed = u.get_editor_subsystem(u.UnrealEditorSubsystem)
r = {'passed': False, 'checks': {}, 'physical_device_verified': False, 'asset_writes': False,
     'method': 'v1 edge suite plus in-radius evasion, frame-aware slam timer, Blueprint-time dodge '
               'cooldown, i-frame window and an undodged negative control at the evade end point. '
               'Enhanced Input injection and staged positions; no asset or map saves.',
     'images': [], 'suite': 'verify_encounter_edges_v2'}
s = {'wall': time.monotonic(), 'stage': 0, 'finished': False, 'max_dt': {}}
handle = None

EXPECTED_STRIKE_RADIUS_CM = 475.
SLAM_WARNING_S, SLAM_TOLERANCE_S = .92, .05
DODGE_COOLDOWN_S = .8
# build_combat.py sets DodgeUntil = now + .26 on the player dash branch.
IFRAME_WINDOW_S = .26
# The negative control must reproduce the evade's 3D separation at the strike frame.
NEG_MATCH_TOLERANCE_CM = 15.

def pos(a):
    v = a.get_actor_location()
    return [v.x, v.y, v.z]

def prop(a, n):
    return a.get_editor_property(n)

def dist(a, b):
    return math.dist(a, b)

def finish(error=None):
    if s['finished']:
        return
    s['finished'] = True
    r['expected_check_count'] = 20
    r['passed'] = not error and len(r['checks']) == 20 and all(r['checks'].values())
    if error:
        r['error'] = error
    r['wall_seconds'] = time.monotonic() - s['wall']
    (OUT / 'receipt.json').write_text(json.dumps(r, indent=2, default=str))
    finish_editor(handle)

def tick(dt):
    try:
        wall = time.monotonic()
        if wall - s['wall'] > 300:
            raise RuntimeError('Edge v2 timeout at stage ' + str(s['stage']))
        w = ed.get_game_world()
        if not w:
            return
        p = u.GameplayStatics.get_player_pawn(w, 0)
        pc = u.GameplayStatics.get_player_controller(w, 0)
        if not p or not pc:
            return
        bosses = u.GameplayStatics.get_all_actors_of_class(w, s['bossclass'])
        if not bosses:
            return
        b = bosses[0]
        game = u.GameplayStatics.get_time_seconds(w)
        # Largest frame time per v2 stage (E3/E4): tolerances use the worst frame, not an average.
        if s['stage'] >= 18 and s.get('prev_world') == w and game >= s.get('prev_game', game):
            s['max_dt'][s['stage']] = max(s['max_dt'].get(s['stage'], 0.), game - s['prev_game'])
        s['prev_game'], s['prev_world'] = game, w
        inp = next(x for x in u.ObjectIterator(u.EnhancedInputLocalPlayerSubsystem) if x.get_world() == w)

        def inject(name, x, y=0):
            inp.inject_input_vector_for_action(s['actions'][name], u.Vector(x, y, 0), [], [])

        def advance(n):
            s['stage'] = n
            s['t'] = game
            s['wall_t'] = wall

        def place(loc):
            p.get_component_by_class(u.CharacterMovementComponent).stop_movement_immediately()
            p.set_actor_location(loc, False, False)

        def screenshot(name):
            s['image'] = OUT / (name + '.png')
            u.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="' + s['image'].as_posix() + '"', pc)

        def image_complete():
            if not s['image'].exists():
                return False
            try:
                v = decode_png(s['image'])
            except Exception:
                return False
            v.pop('chunks', None)
            r['images'].append({'path': str(s['image']), 'validation': v})
            return True

        def separation():
            pp, bp = pos(p), pos(b)
            return {'player': pp, 'boss': bp, 'xy_cm': math.dist(pp[:2], bp[:2]), 'distance_3d_cm': dist(pp, bp)}

        # --- v1 stages 0-15, unchanged in intent ---------------------------------
        if s['stage'] == 0:
            for a in u.GameplayStatics.get_all_actors_of_class(w, u.Character):
                if a != p:
                    a.set_actor_tick_enabled(False)
                    a.get_component_by_class(u.CharacterMovementComponent).disable_movement()
            minions = u.GameplayStatics.get_all_actors_of_class(w, s['minionclass'])
            r['saved_defaults'] = {'boss_speed': prop(b, 'Speed'), 'boss_health': prop(b, 'Health'),
                                   'minions': [{'health': prop(a, 'Health'), 'speed': prop(a, 'Speed'),
                                                'position': pos(a)} for a in minions]}
            r['checks']['three_stitchlings_with_own_health'] = len(minions) == 3 and all(prop(a, 'Health') == 24 for a in minions)
            r['checks']['walk_speed_matches_animation'] = prop(b, 'Speed') == 105
            r['warning_components'] = [{'mesh': str(c.static_mesh), 'collision': str(c.get_collision_enabled())}
                                       for c in b.get_components_by_class(u.StaticMeshComponent)]
            advance(1)
        elif s['stage'] == 1 and game - s['t'] > 2:
            place(u.Vector(-1250, 0, 95))
            advance(2)
        elif s['stage'] == 2:
            inject('Move', -1)
            if game - s['t'] > 1:
                r['walk_wall_position'] = pos(p)
                r['checks']['walk_blocked_by_arena_wall'] = -1365 < pos(p)[0] < -1310
                inject('Dash', 1)
                advance(3)
        elif s['stage'] == 3:
            inject('Move', -1)
            if game - s['t'] > .4:
                r['dash_wall_position'] = pos(p)
                r['checks']['dash_does_not_tunnel_wall'] = pos(p)[0] > -1365
                place(u.Vector(-230, 570, 95))
                advance(4)
        elif s['stage'] == 4 and game - s['t'] > .8:
            rifle = next(c for c in p.get_components_by_class(u.StaticMeshComponent) if c.get_name() == 'ServiceRifle')
            forward = rifle.get_forward_vector()
            aim = p.get_actor_forward_vector()
            dot = forward.x * aim.x + forward.y * aim.y + forward.z * aim.z
            r['rifle_forward_dot_aim'] = dot
            r['checks']['rifle_forward_agrees_with_aim'] = dot > .9
            target = u.Vector(800, -400, 1)
            screen = pc.project_world_location_to_screen(target, False)
            if isinstance(screen, tuple):
                screen = next(x for x in screen if isinstance(x, u.Vector2D))
            assert screen is not None
            pc.set_mouse_location(int(screen.x), int(screen.y))
            pc.set_editor_property('show_mouse_cursor', True)
            inject('MouseAim', 1, 1)
            s['target'] = target
            r['mouse_screen'] = [screen.x, screen.y]
            advance(5)
        elif s['stage'] == 5:
            inject('MouseAim', 1, 1)
            if game - s['t'] > .7:
                d = s['target'] - p.get_actor_location()
                expected = math.degrees(math.atan2(d.y, d.x))
                actual = p.get_actor_rotation().yaw
                r['mouse_aim'] = {'expected': expected, 'actual': actual,
                                  'wrapped_error': abs((actual - expected + 180) % 360 - 180)}
                r['checks']['mouse_cursor_aims_at_projected_world_target'] = r['mouse_aim']['wrapped_error'] < 8
                # v1 staging kept as-is for parity (300 cm, dash backwards). That ended
                # 622 cm away on 2026-10-08, outside the 475 cm radius, so
                # evades_actual_boss_strike is kept for parity only. The real proof is
                # evade_inside_strike_radius below. The distance is now logged.
                place(b.get_actor_location() + u.Vector(-300, 0, -142))
                p.call_method('TouchAim', (1., 0.))
                b.set_actor_tick_enabled(True)
                b.get_component_by_class(u.CharacterMovementComponent).set_movement_mode(u.MovementMode.MOVE_WALKING)
                s['before_evade'] = prop(p, 'Health')
                advance(6)
        elif s['stage'] == 6:
            if prop(b, 'State') == 1 and prop(b, 'StateAge') > .70:
                inject('Move', -1)
                inject('Dash', 1)
                s['attacks_before'] = prop(b, 'Attacks')
                advance(7)
        elif s['stage'] == 7:
            inject('Move', -1)
            if game < prop(p, 'DodgeUntil') and not s.get('inv_checked'):
                before = prop(p, 'Health')
                u.GameplayStatics.apply_damage(p, 10, None, b, u.DamageType)
                r['checks']['dodge_invulnerability_blocks_damage'] = prop(p, 'Health') == before
                s['inv_checked'] = True
            if prop(b, 'Attacks') > s['attacks_before']:
                r['checks']['evades_actual_boss_strike'] = prop(p, 'Health') == s['before_evade']
                r['evade_end'] = dict(separation(), health=prop(p, 'Health'),
                                      note='v1 parity staging; distance logged, not asserted')
                advance(8)
        elif s['stage'] == 8 and game - s['t'] > .6:
            place(b.get_actor_location() + u.Vector(-300, 0, -142))
            s['death_start'] = game
            advance(9)
        elif s['stage'] == 9:
            if prop(p, 'Health') <= 0:
                r['checks']['boss_attacks_can_defeat_player'] = True
                r['attacks_to_defeat'] = prop(b, 'Attacks')
                s['dead_pos'] = pos(p)
                s['shots_before'] = {a.get_path_name() for a in u.GameplayStatics.get_all_actors_of_class(w, s['projectile'])}
                advance(10)
            elif game - s['t'] > 18:
                raise RuntimeError('Player defeat did not occur')
        elif s['stage'] == 10:
            inject('Move', 1)
            inject('Fire', 1)
            if game - s['t'] > .6:
                r['checks']['defeated_player_cannot_move'] = math.dist(s['dead_pos'], pos(p)) < 2
                r['checks']['defeated_player_cannot_fire'] = not ({a.get_path_name() for a in u.GameplayStatics.get_all_actors_of_class(w, s['projectile'])} - s['shots_before'])
                screenshot('player-defeat')
                advance(11)
        elif s['stage'] == 11 and image_complete():
            s['old_world'] = w
            inject('Restart', 1)
            advance(12)
        elif s['stage'] == 12:
            if w != s['old_world'] or game < s['t']:
                minions = u.GameplayStatics.get_all_actors_of_class(w, s['minionclass'])
                r['checks']['restart_from_player_defeat'] = (prop(p, 'Health') == 100 and prop(b, 'Health') == 300
                                                             and len(minions) == 3 and all(prop(a, 'Health') == 24 for a in minions))
                advance(13)
        elif s['stage'] == 13 and game - s['t'] > 1:
            inject('Pause', 1)
            advance(14)
        elif s['stage'] == 14 and wall - s['wall_t'] > .5:
            r['checks']['pause_action_after_restart'] = u.GameplayStatics.is_game_paused(w)
            screenshot('paused')
            advance(15)
        elif s['stage'] == 15 and image_complete():
            # v1 finished here. v2 unpauses (IA_Pause runs while paused) and restarts.
            inject('Pause', 1)
            advance(16)
        elif s['stage'] == 16 and wall - s['wall_t'] > .5:
            if u.GameplayStatics.is_game_paused(w):
                raise RuntimeError('Second Pause press did not resume the game')
            s['old_world'] = w
            inject('Restart', 1)
            advance(17)

        # --- v2 checks ------------------------------------------------------------
        elif s['stage'] == 17:
            if not (w != s['old_world'] or game < s['t']):
                return
            r['strike_radius_cm'] = prop(b, 'StrikeRange')
            r['strike_radius_cdo_cm'] = prop(s['boss_cdo'], 'StrikeRange')
            r['checks']['strike_radius_is_475_cm'] = abs(r['strike_radius_cm'] - EXPECTED_STRIKE_RADIUS_CM) < .01
            for a in u.GameplayStatics.get_all_actors_of_class(w, u.Character):
                if a != p:
                    a.set_actor_tick_enabled(False)
                    a.get_component_by_class(u.CharacterMovementComponent).disable_movement()
            advance(18)
        elif s['stage'] == 18 and game - s['t'] > .5:
            # 200 cm XY (245 cm 3D, already inside AttackRange 380, so the boss winds up on
            # its first tick and stands still), then a sideways dash. The measured dodge is
            # about 300 cm (5 Oct telemetry), so the strike-frame separation is about 370-405 cm 3D.
            place(b.get_actor_location() + u.Vector(-200, 0, -142))
            p.call_method('TouchAim', (1., 0.))
            b.set_actor_tick_enabled(True)
            b.get_component_by_class(u.CharacterMovementComponent).set_movement_mode(u.MovementMode.MOVE_WALKING)
            s['v2_before'] = prop(p, 'Health')
            s['frames'] = 0
            s['frames_from'] = game
            advance(19)
        elif s['stage'] == 19:
            s['frames'] += 1
            if prop(b, 'State') == 1 and 'windup_seen' not in s:
                s['windup_seen'] = game
            # Dash late in the wind-up so the 0.26 s window covers the 0.92 s strike.
            if prop(b, 'State') == 1 and prop(b, 'StateAge') > .78 and 'v2_dash_at' not in s:
                s['du_prev'] = prop(p, 'DodgeUntil')
                # Tech: Move Y -> world +Y is likely (5 Oct recording, dot 1.00); a Move injected
                # in the same frame as Dash sets the dash direction. v2_dash logs it (E6).
                s['dash_from'] = pos(p)
                inject('Move', 0, 1)
                inject('Dash', 1)
                s['v2_dash_at'] = game
                s['v2_attacks_before'] = prop(b, 'Attacks')
                s['accepts'] = []
                # Every injected Dash press from here on (E4).
                s['attempts'] = [game]
            if 'v2_dash_at' in s and not s['accepts'] and prop(p, 'DodgeUntil') != s['du_prev']:
                s['accepts'].append({'game_s': game, 'dodge_until': prop(p, 'DodgeUntil'), 'next_dodge': prop(p, 'NextDodge')})
            if 'v2_dash_at' in s and prop(b, 'Attacks') > s['v2_attacks_before']:
                sep = separation()
                warning = game - s['windup_seen']
                strike_in_window = bool(s['accepts']) and game <= s['accepts'][0]['dodge_until']
                r['evade_inside_radius'] = dict(sep, health_before=s['v2_before'], health_after=prop(p, 'Health'),
                                                strike_radius_cm=r['strike_radius_cm'], dash_accepted=bool(s['accepts']),
                                                strike_s=game, strike_in_window=strike_in_window,
                                                dodge_until=s['accepts'][0]['dodge_until'] if s['accepts'] else None)
                r['checks']['evade_inside_strike_radius'] = (bool(s['accepts'])
                                                             and strike_in_window
                                                             and sep['xy_cm'] < r['strike_radius_cm']
                                                             and sep['distance_3d_cm'] < r['strike_radius_cm']
                                                             and prop(p, 'Health') == s['v2_before'])
                end = pos(p)
                delta = [end[i] - s['dash_from'][i] for i in range(3)]
                planar = math.hypot(delta[0], delta[1])
                r['v2_dash'] = {'from': s['dash_from'], 'at_strike': end, 'delta': delta, 'planar_cm': planar,
                                'unit_xy': [delta[0] / planar, delta[1] / planar] if planar > 1e-3 else None,
                                'move_input': [0, 1], 'note': 'data only; +Y unit_xy is runtime proof of Move Y -> world +Y'}
                # E3: the post-tick reads State==1 on the transition frame and Attacks on the strike
                # frame, so elapsed reads in [0.92, 0.92 + dt). Lower bound 5 ms, upper bound frame-aware.
                max_dt = s['max_dt'].get(19, 0.)
                lo = SLAM_WARNING_S - .005
                hi = SLAM_WARNING_S + max(SLAM_TOLERANCE_S, max_dt + .005)
                r['slam_warning'] = {'state1_first_seen_s': s['windup_seen'], 'strike_seen_s': game,
                                     'elapsed_s': round(warning, 4), 'expected_s': SLAM_WARNING_S,
                                     'accepted_range_s': [round(lo, 4), round(hi, 4)], 'max_frame_dt_s': round(max_dt, 4),
                                     'boss_state_age_at_strike_frame': prop(b, 'StateAge'),
                                     'frame_dt_estimate_s': round((game - s['frames_from']) / max(s['frames'], 1), 4),
                                     'note': 'Blueprint timer; the Attack clip peaks visually around 0.67 s'}
                r['checks']['slam_timer_0_92_s'] = lo <= warning <= hi
                b.set_actor_tick_enabled(False)
                s['mash'] = 0
                advance(20)
            elif game - s['t'] > 20:
                raise RuntimeError('v2 strike did not land')
        elif s['stage'] == 20:
            # Second dash: press on alternate frames so each press is an edge.
            # Tech: Dash fires on press (confirmed, keys suite); alternate-frame injection gives
            # one edge per press for Pressed or Down triggers, and the 0.8 s cooldown gates the rest.
            if not s['accepts']:
                # E5: no first accept means no cooldown or i-frame baseline. Record false, keep going.
                r['dodge_timing'] = {'error': 'first v2 dash not accepted', 'attempts_s': s['attempts']}
                for k in ('dodge_cooldown', 'iframes_block_damage_inside_window', 'iframes_expire'):
                    r['checks'][k] = False
                advance(21)
            elif len(s['accepts']) < 2:
                s['mash'] += 1
                if s['mash'] % 2:
                    inject('Move', 0, -1)
                    inject('Dash', 1)
                    s['attempts'].append(game)
                if prop(p, 'DodgeUntil') != s['accepts'][-1]['dodge_until']:
                    s['accepts'].append({'game_s': game, 'dodge_until': prop(p, 'DodgeUntil'), 'next_dodge': prop(p, 'NextDodge')})
                    # Inside the new window: struck now, HP must not move.
                    before = prop(p, 'Health')
                    u.GameplayStatics.apply_damage(p, 10, None, b, u.DamageType)
                    r['iframe_inside'] = {'game_s': game, 'dodge_until': prop(p, 'DodgeUntil'),
                                          'health_before': before, 'health_after': prop(p, 'Health')}
                    r['checks']['iframes_block_damage_inside_window'] = game < prop(p, 'DodgeUntil') and prop(p, 'Health') == before
                    # E4: Blueprint time (DodgeUntil - 0.26 is the Blueprint's own 'now' at each
                    # accept), not the frame Python noticed. Injection lag plus alternate-frame
                    # mashing can make the second accept up to two frames late, never early.
                    t0 = s['accepts'][0]['dodge_until'] - IFRAME_WINDOW_S
                    t1 = s['accepts'][1]['dodge_until'] - IFRAME_WINDOW_S
                    gap = t1 - t0
                    max_dt = max(s['max_dt'].get(19, 0.), s['max_dt'].get(20, 0.))
                    lo, hi = DODGE_COOLDOWN_S - 1e-3, DODGE_COOLDOWN_S + 2 * max_dt + .01
                    attempts_before = [t for t in s['attempts'] if t < s['accepts'][0]['next_dodge']]
                    r['dodge_timing'] = {'accepts': s['accepts'], 'blueprint_accept_s': [t0, t1],
                                         'measured_cooldown_s': round(gap, 4),
                                         'python_seen_gap_s': round(s['accepts'][1]['game_s'] - s['accepts'][0]['game_s'], 4),
                                         'expected_s': DODGE_COOLDOWN_S, 'accepted_range_s': [round(lo, 4), round(hi, 4)],
                                         'max_frame_dt_s': round(max_dt, 4), 'attempts_s': s['attempts'],
                                         'attempts_before_next_dodge': len(attempts_before),
                                         'authored_window_s': [round(x['next_dodge'] - x['dodge_until'] + IFRAME_WINDOW_S, 4) for x in s['accepts']]}
                    r['checks']['dodge_cooldown'] = len(attempts_before) >= 3 and lo <= gap <= hi
                elif game - s['t'] > 3:
                    # E5 spirit: record false with a reason rather than aborting the receipt.
                    r['dodge_timing'] = {'error': 'second dash never accepted within 3 s', 'accepts': s['accepts'],
                                         'attempts_s': s['attempts']}
                    for k in ('dodge_cooldown', 'iframes_block_damage_inside_window', 'iframes_expire'):
                        r['checks'][k] = False
                    advance(21)
            elif game > s['accepts'][1]['dodge_until'] + .02:
                before = prop(p, 'Health')
                u.GameplayStatics.apply_damage(p, 10, None, b, u.DamageType)
                r['iframe_outside'] = {'game_s': game, 'dodge_until': s['accepts'][1]['dodge_until'],
                                       'measured_window_s': round(s['accepts'][1]['dodge_until'] - s['accepts'][1]['game_s'], 4),
                                       'health_before': before, 'health_after': prop(p, 'Health')}
                r['checks']['iframes_expire'] = prop(p, 'Health') < before
                advance(21)
        elif s['stage'] == 21 and game - s['t'] > .4:
            s['old_world'] = w
            inject('Restart', 1)
            advance(22)
        elif s['stage'] == 22:
            if not (w != s['old_world'] or game < s['t']):
                return
            for a in u.GameplayStatics.get_all_actors_of_class(w, u.Character):
                if a != p:
                    a.set_actor_tick_enabled(False)
                    a.get_component_by_class(u.CharacterMovementComponent).disable_movement()
            advance(23)
        elif s['stage'] == 23 and game - s['t'] > .5:
            # Negative control (E1): wind the boss up from 200 cm exactly as stage 18, then at the
            # same StateAge move the player, without a dash, to where check 15's evade ended.
            # Placing the player straight at the end point would not work: if it is beyond
            # AttackRange 380 the boss chases first and strikes from a different separation.
            place(b.get_actor_location() + u.Vector(-200, 0, -142))
            p.call_method('TouchAim', (1., 0.))
            b.set_actor_tick_enabled(True)
            b.get_component_by_class(u.CharacterMovementComponent).set_movement_mode(u.MovementMode.MOVE_WALKING)
            s['neg_before'] = prop(p, 'Health')
            s['neg_attacks'] = prop(b, 'Attacks')
            advance(24)
        elif s['stage'] == 24:
            if prop(b, 'State') == 1 and prop(b, 'StateAge') > .78 and 'neg_moved_s' not in s:
                ev = r['evade_inside_radius']
                s['neg_offset'] = [ev['player'][i] - ev['boss'][i] for i in range(3)]
                place(b.get_actor_location() + u.Vector(*s['neg_offset']))
                s['neg_moved_s'] = game
            if prop(b, 'Attacks') > s['neg_attacks']:
                sep = separation()
                target = r['evade_inside_radius']['distance_3d_cm']
                matched = 'neg_moved_s' in s and abs(sep['distance_3d_cm'] - target) <= NEG_MATCH_TOLERANCE_CM
                r['negative_control'] = dict(sep, health_before=s['neg_before'], health_after=prop(p, 'Health'),
                                             offset_from_boss=s.get('neg_offset'), moved_at_s=s.get('neg_moved_s'),
                                             strike_s=game, evade_distance_3d_cm=target,
                                             match_tolerance_cm=NEG_MATCH_TOLERANCE_CM, separation_matches_evade=matched)
                r['checks']['undodged_strike_at_evade_end_reduces_hp'] = (matched
                                                                           and sep['distance_3d_cm'] < r['strike_radius_cm']
                                                                           and prop(p, 'Health') < s['neg_before'])
                # Keep the old 200 cm (245 cm 3D) control as a record, not a check.
                place(b.get_actor_location() + u.Vector(-200, 0, -142))
                s['c200_before'] = prop(p, 'Health')
                s['c200_attacks'] = prop(b, 'Attacks')
                advance(25)
            elif game - s['t'] > 20:
                raise RuntimeError('Negative control strike did not land')
        elif s['stage'] == 25:
            if prop(b, 'Attacks') > s['c200_attacks']:
                r['undodged_strike_at_200cm'] = dict(separation(), health_before=s['c200_before'],
                                                     health_after=prop(p, 'Health'),
                                                     reduces_hp=prop(p, 'Health') < s['c200_before'],
                                                     note='data only: the original 245 cm 3D control')
                finish()
            elif game - s['t'] > 6:
                r['undodged_strike_at_200cm'] = {'observed': False, 'note': 'no strike within 6 s; data only'}
                finish()
    except Exception:
        finish(traceback.format_exc())

try:
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    assert lev.load_level('/Game/Maps/TeddyEncounter')
    s['bossclass'] = u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_TeddyBoss')
    s['minionclass'] = u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_Stitchling')
    s['projectile'] = u.EditorAssetLibrary.load_blueprint_class('/Game/TeddyEncounter/Blueprints/BP_EncounterProjectile')
    s['boss_cdo'] = u.get_default_object(s['bossclass'])
    s['actions'] = {n: u.load_asset('/Game/Variant_TwinStick/Input/Actions/IA_Action_' + n)
                    for n in ['Move', 'MouseAim', 'Fire', 'Dash']}
    s['actions'].update({n: u.load_asset('/Game/TeddyEncounter/Input/IA_' + n) for n in ['Pause', 'Restart']})
    lev.editor_request_begin_play()
    handle = u.register_slate_post_tick_callback(tick)
except Exception:
    finish(traceback.format_exc())
