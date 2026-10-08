"""Phase 2 escalation for the saved boss blueprint.

Outside the editor this module only prints a plan:

    python tools/build_boss_escalation_v1.py --plan
    python tools/build_boss_escalation_v1.py --plan --json

Any other invocation outside the editor refuses with exit code 2.
Inside the editor (no arguments) the default is a read-only inspect.
Mutation runs only when a person has set TEDDY_GAME016_APPLY=1 for that
process. Agents must not set that variable.

The unreal module is imported only on the editor path.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NS = '/Game/TeddyEncounter'
BOSS_ASSET = NS + '/Blueprints/BP_TeddyBoss'
HUD_ASSET = NS + '/Blueprints/BP_EncounterHUD'
SKELETON_ASSET = NS + '/Teddy/Idle/SK_Teddy_Skeleton'
ATTACK_ASSET = NS + '/Teddy/Attack/A_Teddy_Attack'
MANIFEST_PATH = ROOT / 'Assets' / 'Adapted' / 'AnimPreprod' / 'manifest.json'
ANIM_DIR = MANIFEST_PATH.parent

TAG_GAME016 = 'TeddyEncounter.Game016'
TAG_VALUE = 'escalation-v1'
APPLY_ENV = 'TEDDY_GAME016_APPLY'

FPS = 30
ATTACK_LEFT_FRAMES = 36
ATTACK_LEFT_IMPACT_FRAME = 20
STAGGER_FRAMES = 24
THREAT_FRAMES = 45
SHIPPED_ATTACK_FRAMES = 54
EXPECTED_FRAMES = {'Stagger': STAGGER_FRAMES, 'Threat': THREAT_FRAMES, 'AttackLeft': ATTACK_LEFT_FRAMES}
TELEGRAPH_SECONDS = 0.92
PHASE1_RECOVERY = 1.15
PHASE2_RECOVERY = 0.8
PHASE2_CYCLE = TELEGRAPH_SECONDS + PHASE2_RECOVERY
PHASE_CHANGE_HEALTH = 150.0
BOSS_MAX_HEALTH = 300.0
RIFLE_DAMAGE = 12.0
FLASH_SECONDS = 0.15
STRIKE_RADIUS_CM = 475.0
LENGTH_TOLERANCE = 0.025
DOC_PHASE_FRAMES = 69

# Blueprint-declared variables only. `Mesh` is ACharacter's native component and
# `AttackWarning` is an SCS component: ListMemberVariableNames reports neither under
# its plain name (inherited members carry their declaring class path), so they are
# checked through the graph anchors and confirm_component instead. (Tech review.)
REQUIRED_VARS = (
    'Health', 'MaxHealth', 'State', 'StateAge', 'Speed', 'AttackRange',
    'StrikeRange', 'AttackDamage', 'HitReady', 'Attacks', 'HitsReceived',
)
NEW_VARS = (
    'bPhase2', 'bNextAttackLeft', 'bThreatStarted', 'PhaseChangeHealth',
    'Phase1Recovery', 'Phase2Recovery', 'StaggerSeconds', 'ThreatSeconds',
    'AttackLeftPlayRate', 'PhaseFlashUntil',
)

# The copied blueprint name and the three byte-hash paths live only in these
# two tuples. Editor code refers to the tuples and does not repeat the names.
NOT_TOUCHED_NAMES = (
    'BP_Stitchling',
    'TeddyEncounter.umap',
    'SK_Teddy_Skeleton',
    'existing builders',
)
UNCHANGED_HASH_PATHS = (
    'TeddyBlueprint/Content/TeddyEncounter/Blueprints/BP_Stitchling.uasset',
    'TeddyBlueprint/Content/TeddyEncounter/Teddy/Idle/SK_Teddy_Skeleton.uasset',
    'TeddyBlueprint/Content/Maps/TeddyEncounter.umap',
)
REQUIRED_LOCKS = (
    'TeddyBlueprint/Content/TeddyEncounter/Blueprints/BP_TeddyBoss.uasset',
    'TeddyBlueprint/Content/TeddyEncounter/Blueprints/BP_EncounterHUD.uasset',
)
NEW_ANIM_LOCKS = (
    'TeddyBlueprint/Content/TeddyEncounter/Teddy/Stagger/A_Teddy_Stagger.uasset',
    'TeddyBlueprint/Content/TeddyEncounter/Teddy/Threat/A_Teddy_Threat.uasset',
    'TeddyBlueprint/Content/TeddyEncounter/Teddy/AttackLeft/A_Teddy_AttackLeft.uasset',
)

GREY = '(R=.32,G=.32,B=.32,A=1)'
FLASH_RED = '(R=.95,G=.12,B=.08,A=1)'
BOSS_BAR = '(R=.49,G=.08,B=.065,A=1)'
BOSS_BAR_CHANNELS = (0.49, 0.08, 0.065, 1.0)

CUE_EXTENSION_NOTE = (
    'GAME-016 step 9 extension point. Not built. '
    'While State is 5, damage returns on this branch: no health change and no hit reaction. '
    'The no-damage cue waits for approval. Leave this branch unwired.'
)
SINGLE_NODE_NOTE = (
    'The boss mesh stays in single-node animation mode. Every PlayAnimation switch is instant; '
    'there is no crossfade. Phase 2 still ends recovery by playing Walk in a loop at 0.8 s, '
    'which cuts the shipped Attack about 0.047 s early (54 frames = 53/30 s, cycle 1.72 s). '
    'A true blend needs a later decision (an animation blueprint, or a montage driven from '
    'single-node). This script does not create either.'
)
REFUSE_TEXT = (
    'Refusing to change assets. Outside the editor the only accepted command is '
    '`python tools/build_boss_escalation_v1.py --plan [--json]`. '
    'Inside Unreal Editor, run it with no arguments for a read-only inspect. '
    'A person may set TEDDY_GAME016_APPLY=1 for an editor apply. Agents must not set it.'
)
HOW_TO_RUN = {
    'plan': 'python tools/build_boss_escalation_v1.py --plan',
    'plan_json': 'python tools/build_boss_escalation_v1.py --plan --json',
    'inspect': 'python tools/astra_setup.py editor-script tools/build_boss_escalation_v1.py',
    'apply_shell': (
        "$env:TEDDY_GAME016_APPLY = '1'\n"
        'python tools/astra_setup.py editor-script tools/build_boss_escalation_v1.py\n'
        'Remove-Item Env:TEDDY_GAME016_APPLY'
    ),
    'apply_env': APPLY_ENV,
    'agents': 'Agents must not set TEDDY_GAME016_APPLY.',
    'receipt': 'evidence/game-016/<UTC stamp>-<inspect|apply>/escalation-receipt.json',
    'lock_command': 'git lfs locks --verify --json',
}


class Mode:
    def __init__(self, action, exit_code, reason='', json_out=False):
        self.action = action
        self.exit_code = exit_code
        self.reason = reason
        self.json_out = json_out

    def as_dict(self):
        return {
            'action': self.action,
            'exit_code': self.exit_code,
            'reason': self.reason,
            'json_out': self.json_out,
        }


class LockCheckError(Exception):
    def __init__(self, reason, detail=None):
        super().__init__(f'{reason}: {detail}')
        self.reason = reason
        self.detail = detail


class Sha256Mismatch(Exception):
    def __init__(self, name, expected, actual, path):
        super().__init__(f'{name} sha256 mismatch at {path}: {actual} != {expected}')
        self.name = name
        self.expected = expected
        self.actual = actual
        self.path = str(path)


class AnchorError(Exception):
    """A saved graph did not match. ``dump`` and ``checks`` say exactly what was found."""

    def __init__(self, anchor, detail, dump=None, checks=None):
        message = f'{anchor}: {detail}'
        if checks:
            message += '\nchecks: ' + format_checks(checks)
        if dump:
            message += '\nfound node:\n' + format_node_dump(dump)
        super().__init__(message)
        self.anchor = anchor
        self.detail = detail
        self.dump = dump
        self.checks = checks

    def as_receipt(self):
        return {
            'anchor': self.anchor,
            'detail': self.detail,
            'checks': self.checks,
            'node_dump': self.dump,
        }


class PartialStateError(RuntimeError):
    pass


def stage(payload, name, log=None):
    """Record and log an apply/inspect stage before a native step.

    print() does not reach editor.log, and a native crash drops it. unreal.log_warning
    does reach editor.log, which is what survives the crash (apply 20261008T194503).
    """
    payload.setdefault('stages', []).append(name)
    line = f'GAME-016 stage: {name}'
    print(line, flush=True)
    writer = log if log is not None else _unreal_log
    writer(line)
    return name


def _unreal_log(line):
    try:
        import unreal
        unreal.log_warning(line)
    except Exception:
        return False
    return True


def clip_seconds(frames, fps=FPS):
    """Blender frames 1..N import with frame 1 at t=0, so the length is (N-1)/fps."""
    frames = int(frames)
    if frames < 2:
        raise ValueError(f'clip must have at least 2 frames, got {frames}')
    return (frames - 1) / float(fps)


def attack_left_play_rate(play_length, frames=ATTACK_LEFT_FRAMES, impact_frame=ATTACK_LEFT_IMPACT_FRAME,
                          target=TELEGRAPH_SECONDS):
    """impact_time = (k-1)/(N-1) * play_length; rate = impact_time / 0.92."""
    frames = int(frames)
    impact_frame = int(impact_frame)
    play_length = float(play_length)
    if frames < 2 or not (1 <= impact_frame <= frames):
        raise ValueError('AttackLeft frame contract is invalid')
    if play_length <= 0 or target <= 0:
        raise ValueError('play length and target time must be positive')
    impact_time = (impact_frame - 1) / (frames - 1) * play_length
    rate = impact_time / float(target)
    scaled = play_length / rate
    return {
        'frames': frames,
        'impact_frame': impact_frame,
        'play_length': play_length,
        'impact_time': impact_time,
        'target_seconds': float(target),
        'play_rate': rate,
        'scaled_length': scaled,
        'cycle_seconds': PHASE2_CYCLE,
        'fits_in_cycle': scaled <= PHASE2_CYCLE + 1e-9,
        'method': 'play_rate',
    }


def attack_cut_seconds(attack_length=None, attack_frames=SHIPPED_ATTACK_FRAMES, fps=FPS,
                       telegraph=TELEGRAPH_SECONDS, recovery=PHASE2_RECOVERY):
    length = clip_seconds(attack_frames, fps) if attack_length is None else float(attack_length)
    cycle = float(telegraph) + float(recovery)
    return {
        'attack_frames': int(attack_frames),
        'attack_seconds': length,
        'cycle_seconds': cycle,
        'cut_seconds': length - cycle,
        'walk_at_recovery_end': True,
    }


def phase_change_timing(stagger_frames=STAGGER_FRAMES, threat_frames=THREAT_FRAMES, fps=FPS,
                        stagger_length=None, threat_length=None):
    stagger = clip_seconds(stagger_frames, fps) if stagger_length is None else float(stagger_length)
    threat = clip_seconds(threat_frames, fps) if threat_length is None else float(threat_length)
    total = stagger + threat
    frame_sum = int(stagger_frames) + int(threat_frames)
    doc_seconds = DOC_PHASE_FRAMES / float(fps)
    return {
        'stagger_frames': int(stagger_frames),
        'threat_frames': int(threat_frames),
        'frame_count_sum': frame_sum,
        'doc_frame_count': DOC_PHASE_FRAMES,
        'doc_frame_count_matches': frame_sum == DOC_PHASE_FRAMES,
        'stagger_seconds': stagger,
        'threat_seconds': threat,
        'total_seconds': total,
        'doc_seconds': doc_seconds,
        'doc_delta_seconds': total - doc_seconds,
    }


def compute_timings(attack_left_length=None, stagger_length=None, threat_length=None, shipped_attack_length=None):
    left_length = clip_seconds(ATTACK_LEFT_FRAMES) if attack_left_length is None else float(attack_left_length)
    left = attack_left_play_rate(left_length)
    if not left['fits_in_cycle']:
        raise ValueError('AttackLeft retimed clip does not fit in the 1.72 s phase-2 cycle')
    change = phase_change_timing(stagger_length=stagger_length, threat_length=threat_length)
    cut = attack_cut_seconds(attack_length=shipped_attack_length)
    hits = hits_to_threshold(BOSS_MAX_HEALTH, RIFLE_DAMAGE, PHASE_CHANGE_HEALTH)
    return {
        'attack_left': left,
        'phase_change': change,
        'attack_cut': cut,
        'threshold': hits,
        'telegraph_seconds': TELEGRAPH_SECONDS,
        'phase1_recovery': PHASE1_RECOVERY,
        'phase2_recovery': PHASE2_RECOVERY,
        'phase2_cycle': PHASE2_CYCLE,
        'strike_radius_cm': STRIKE_RADIUS_CM,
        'flash_seconds': FLASH_SECONDS,
        'single_node': SINGLE_NODE_NOTE,
    }


def hits_to_threshold(max_health, damage, threshold):
    """Smallest hit count whose remaining health is at or under the threshold."""
    max_health = float(max_health)
    damage = float(damage)
    threshold = float(threshold)
    if damage <= 0:
        raise ValueError('damage must be positive')
    if max_health <= threshold:
        hits = 0
        hp = max_health
    else:
        quotient = (max_health - threshold) / damage
        hits = max(1, math.ceil(quotient - 1e-9))
        hp = max_health - hits * damage
    return {
        'hits': int(hits),
        'hp': _whole(hp),
        'max_health': _whole(max_health),
        'damage': _whole(damage),
        'threshold': _whole(threshold),
        'hp_before': _whole(max_health - (hits - 1) * damage) if hits else _whole(max_health),
    }


def hp_after_hits(max_health, damage, hits):
    return _whole(float(max_health) - float(hits) * float(damage))


def would_enter_phase(hp_after, b_phase2, state, threshold=PHASE_CHANGE_HEALTH):
    """Lethal damage wins. State 5 never reaches this test. Dead state does not enter."""
    if int(state) == 5 or damage_ignored(state):
        return False
    if float(hp_after) <= 0:
        return False
    if int(state) == 3:
        return False
    return (not b_phase2) and float(hp_after) <= float(threshold)


def damage_ignored(state):
    return int(state) == 5


def simulate_rifle_phase(max_health=BOSS_MAX_HEALTH, damage=RIFLE_DAMAGE, threshold=PHASE_CHANGE_HEALTH,
                         shots=20, window_shots=4, state=0):
    """One rifle sequence. State 5 absorbs the next window_shots without changing HP."""
    hp = float(max_health)
    phase2 = False
    current = int(state)
    triggers = []
    ignored = []
    held = 0
    for shot in range(1, int(shots) + 1):
        if current == 5:
            ignored.append({'shot': shot, 'hp': _whole(hp)})
            held += 1
            if held >= int(window_shots):
                phase2 = True
                current = 0
                held = 0
            continue
        if current == 3 or hp <= 0:
            break
        hp = max(0.0, hp - float(damage))
        if would_enter_phase(hp, phase2, current, threshold):
            current = 5
            triggers.append({'shot': shot, 'hp': _whole(hp)})
            held = 0
            continue
        if hp <= 0:
            current = 3
    return {
        'triggers': triggers,
        'ignored': ignored,
        'hp': _whole(hp),
        'b_phase2': phase2,
        'state': current,
    }


def _whole(value):
    value = float(value)
    if abs(value - round(value)) < 1e-6:
        return int(round(value))
    return value


def length_basis(play_length, frames, fps=FPS, tolerance=LENGTH_TOLERANCE):
    """Return 'n_minus_1' or 'n' when play_length is within tolerance of one of them."""
    imported = (int(frames) - 1) / float(fps)
    inclusive = int(frames) / float(fps)
    play_length = float(play_length)
    gap_imported = abs(play_length - imported)
    gap_inclusive = abs(play_length - inclusive)
    if gap_imported <= tolerance and gap_imported <= gap_inclusive:
        return 'n_minus_1'
    if gap_inclusive <= tolerance:
        return 'n'
    raise ValueError(
        f'play length {play_length} is outside {tolerance}s of {imported} and {inclusive}'
    )


def ue_number(value):
    value = float(value)
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f'{value:.12f}'.rstrip('0').rstrip('.')


def read_manifest(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('new_clips'), list):
        raise ValueError('manifest is missing new_clips')
    return data


def manifest_clip(manifest, name):
    matches = [item for item in manifest['new_clips'] if item.get('name') == name]
    if len(matches) != 1:
        raise LookupError(f'{name}: expected one manifest entry, found {len(matches)}')
    entry = matches[0]
    for key in ('file', 'sha256', 'frames', 'fps'):
        if key not in entry:
            raise LookupError(f'{name}: manifest entry missing {key}')
    return entry


def require_manifest_contract(manifest):
    found = {}
    for name, frames in EXPECTED_FRAMES.items():
        entry = manifest_clip(manifest, name)
        if int(entry['frames']) != frames or int(entry['fps']) != FPS:
            raise ValueError(f'{name} manifest is {entry["frames"]} frames at {entry["fps"]} fps')
        if entry['file'] != f'Teddy_{name}.fbx':
            raise ValueError(f'{name} file name is {entry["file"]}')
        found[name] = entry
    return found


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify_clip_file(manifest_path, name, fbx_path):
    entry = manifest_clip(read_manifest(manifest_path), name)
    actual = sha256_file(fbx_path)
    expected = str(entry['sha256']).lower()
    if actual.lower() != expected:
        raise Sha256Mismatch(name, expected, actual, fbx_path)
    return {
        'name': name,
        'file': entry['file'],
        'sha256': actual,
        'frames': int(entry['frames']),
        'fps': int(entry['fps']),
    }


def hash_files(root, paths):
    out = {}
    for rel in paths:
        file_path = Path(root) / rel
        if not file_path.is_file():
            raise FileNotFoundError(rel)
        out[rel.replace('\\', '/')] = sha256_file(file_path)
    return out


def _lock_path(path):
    text = str(path).replace('\\', '/').strip()
    if text.startswith('./'):
        text = text[2:]
    return text


def parse_lock_verify(text, required=None):
    """Accept only git-lfs verify JSON: {"ours":[{"path":...}], "theirs":[{"path":...}]}."""
    required = tuple(required) if required is not None else REQUIRED_LOCKS
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LockCheckError('malformed', str(exc)) from exc
    if not isinstance(data, dict) or 'ours' not in data or 'theirs' not in data:
        raise LockCheckError('malformed', 'expected an object with ours and theirs')
    if not isinstance(data['ours'], list) or not isinstance(data['theirs'], list):
        raise LockCheckError('malformed', 'ours and theirs must be arrays')

    def paths(rows, label):
        found = []
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get('path'), str) or not row['path'].strip():
                raise LockCheckError('malformed', f'{label} entry is missing a path string')
            found.append(_lock_path(row['path']))
        return found

    ours = paths(data['ours'], 'ours')
    theirs = paths(data['theirs'], 'theirs')
    our_set = set(ours)
    their_set = set(theirs)
    held_by_them = [item for item in required if item in their_set]
    missing = [item for item in required if item not in our_set and item not in their_set]
    if held_by_them or missing or any(item not in our_set for item in required):
        raise LockCheckError('not_ours', {'missing': missing, 'theirs': held_by_them})
    return {'ok': True, 'ours': ours, 'theirs': theirs, 'required': list(required)}


def interpret_lock_command(returncode, stdout, stderr='', required=None):
    if returncode != 0:
        raise LockCheckError('git_failed', {
            'returncode': returncode,
            'stderr': (stderr or '')[-2000:],
            'stdout': (stdout or '')[-2000:],
        })
    return parse_lock_verify(stdout if stdout is not None else '', required)


def locks_required_for_apply(root):
    """The two saved blueprints, plus any phase-2 clips that are already on disk."""
    required = list(REQUIRED_LOCKS)
    for rel in NEW_ANIM_LOCKS:
        if (Path(root) / rel).is_file():
            required.append(rel)
    return tuple(required)


def classify_saved_state(tag_value, variable_names):
    tag = (tag_value or '').strip()
    names = set(variable_names)
    if tag == TAG_VALUE:
        return 'already_applied'
    if tag or 'bPhase2' in names or any(name in names for name in NEW_VARS):
        return 'partial'
    return 'ready'


def cli_args(argv):
    args = [str(item) for item in argv]
    if args and not args[0].startswith('-') and not args[0].replace('\\', '/').lower().endswith('build_boss_escalation_v1.py'):
        args = args[1:]
    if args and args[0].replace('\\', '/').lower().endswith('build_boss_escalation_v1.py'):
        args = args[1:]
    return args


def resolve_mode(has_unreal, argv, env):
    args = cli_args(argv)
    plan = False
    json_out = False
    unknown = []
    for arg in args:
        if arg == '--plan':
            plan = True
        elif arg == '--json':
            json_out = True
        else:
            unknown.append(arg)
    if unknown:
        return Mode(
            'refuse', 2,
            'Unknown arguments: ' + ' '.join(unknown) + '. ' + REFUSE_TEXT,
        )
    if json_out and not plan:
        return Mode('refuse', 2, '--json is only valid with --plan. ' + REFUSE_TEXT)
    if plan:
        return Mode('plan', 0, '', json_out=json_out)
    if not has_unreal:
        return Mode('refuse', 2, REFUSE_TEXT)
    if env.get(APPLY_ENV) == '1':
        return Mode('apply', 0, '')
    return Mode('inspect', 0, '')


def module_has_unreal():
    """True inside Unreal's Python, including the editor-script commandlet.

    The commandlet executes this file inside the interpreter that already
    loaded `unreal`. `find_spec` covers a normal import. `sys.modules` covers
    the case where the plugin has registered the module without a spec.
    """
    if 'unreal' in sys.modules:
        return True
    try:
        return importlib.util.find_spec('unreal') is not None
    except (ImportError, ValueError):
        return False


def anim_object_path(clip):
    return f'{NS}/Teddy/{clip}/A_Teddy_{clip}'


def receipt_directory_name(mode, when=None):
    when = when or datetime.now(timezone.utc)
    if when.tzinfo is None:
        raise ValueError('receipt stamp requires a timezone-aware UTC time')
    if mode not in ('inspect', 'apply', 'plan'):
        raise ValueError(f'bad receipt mode {mode}')
    stamp = when.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    return f'{stamp}-{mode}'


def write_receipt(root, mode, payload, when=None):
    base = receipt_directory_name(mode, when)
    parent = Path(root) / 'evidence' / 'game-016'
    parent.mkdir(parents=True, exist_ok=True)
    folder = parent / base
    suffix = 2
    while folder.exists():
        folder = parent / f'{base}-{suffix}'
        suffix += 1
    folder.mkdir()
    path = folder / 'escalation-receipt.json'
    path.write_text(json.dumps(payload, indent=2, default=str) + '\n', encoding='utf-8')
    return path


def variable_plan(timings):
    left = timings['attack_left']
    change = timings['phase_change']
    rows = [
        ('bPhase2', 'bool', 'false', 'phase 1'),
        ('bNextAttackLeft', 'bool', 'true', 'phase 2 opens on AttackLeft; phase 1 does not read it'),
        ('bThreatStarted', 'bool', 'false', 'phase 1'),
        ('PhaseChangeHealth', 'real', ue_number(PHASE_CHANGE_HEALTH), 'phase 1 until health crosses it'),
        ('Phase1Recovery', 'real', ue_number(PHASE1_RECOVERY), 'selected while bPhase2 is false'),
        ('Phase2Recovery', 'real', ue_number(PHASE2_RECOVERY), 'selected while bPhase2 is true'),
        ('StaggerSeconds', 'real', ue_number(change['stagger_seconds']), 'apply writes get_play_length()'),
        ('ThreatSeconds', 'real', ue_number(change['threat_seconds']), 'apply writes get_play_length()'),
        ('AttackLeftPlayRate', 'real', ue_number(left['play_rate']), 'impact_time / 0.92 from the imported length'),
        ('PhaseFlashUntil', 'real', '0', 'no flash until the phase window ends'),
    ]
    return [
        {'name': name, 'type': kind, 'default': default, 'note': note, 'phase1_safe': True}
        for name, kind, default, note in rows
    ]


def build_plan(manifest_path=None):
    manifest = read_manifest(manifest_path or MANIFEST_PATH)
    entries = require_manifest_contract(manifest)
    timings = compute_timings()
    imports = []
    for name in ('Stagger', 'Threat', 'AttackLeft'):
        entry = entries[name]
        imports.append({
            'name': name,
            'frames': int(entry['frames']),
            'fps': int(entry['fps']),
            'file': entry['file'],
            'sha256': entry['sha256'],
            'source': f'Assets/Adapted/AnimPreprod/{entry["file"]}',
            'destination': anim_object_path(name),
            'sample_rate': 30,
            'skeleton': SKELETON_ASSET,
            'reuse_if_owned': True,
        })
    steps = [
        {
            'step': 1, 'status': 'build', 'title': 'Import Stagger, Threat and AttackLeft',
            'detail': (
                'Animation-only FBX onto the owned teddy skeleton, sample rate 30, '
                'no mesh, materials, textures, physics or custom attributes. '
                'Destinations follow /Game/TeddyEncounter/Teddy/<Clip>/A_Teddy_<Clip>. '
                'Confirm the 24+45 frame counts (69) and store the imported play lengths.'
            ),
        },
        {
            'step': 2, 'status': 'build', 'title': 'Add state 5 and bPhase2',
            'detail': (
                'Enter on the first damage that leaves HP at or under 150 while bPhase2 is false, '
                'from any live state. Hide the warning ring, leave state 1 so a pending slam cannot fire, '
                'play Stagger then Threat, then return to state 0 and set bPhase2.'
            ),
        },
        {
            'step': 3, 'status': 'build', 'title': 'Ignore damage in state 5',
            'detail': (
                'Insert a State==5 branch in front of ReceiveAnyDamage. '
                'The then pin returns with no health change and no hit reaction. '
                'The cue itself is not wired.'
            ),
        },
        {
            'step': 4, 'status': 'build', 'title': 'Switch recovery duration',
            'detail': 'Feed the existing StateAge > recovery compare from SelectFloat(bPhase2 ? 0.8 : 1.15).',
        },
        {
            'step': 5, 'status': 'build', 'title': 'Alternate AttackLeft and Attack',
            'detail': (
                'In phase 2, each anticipation entry toggles AttackLeft and Attack, starting with AttackLeft. '
                'The 0.92 s timer, ring, slam sound and 475 cm radius stay as they are.'
            ),
        },
        {
            'step': 6, 'status': 'build', 'title': 'Retime AttackLeft with play rate',
            'choice': 'play_rate',
            'detail': (
                'PlayAnimation(AttackLeft) then SetPlayRate(AttackLeftPlayRate). '
                'Rate is impact_time/0.92, and impact_time is (20-1)/(36-1) times the imported length. '
                'Do not hard-code 0.73. Other PlayAnimation calls reset the rate to 1.'
            ),
        },
        {
            'step': 7, 'status': 'build', 'title': 'Cut Attack into Walk',
            'blend': 'cut_to_walk',
            'detail': (
                'Keep the existing recovery-end path. At 0.8 s it sets state 0 and plays looping Walk, '
                'cutting Attack about 0.047 s early. Do not lengthen recovery. No crossfade in this pass.'
            ),
        },
        {
            'step': 8, 'status': 'build', 'title': 'Grey then flash the boss bar',
            'detail': (
                'While the boss state is 5, draw the boss bar grey. '
                'For 0.15 s after the window, draw it bright red. Otherwise keep the original colour. '
                'The width math stays.'
            ),
        },
        {
            'step': 9, 'status': 'skipped', 'title': 'No-damage cue',
            'detail': (
                'Awaiting approval. The state-5 damage branch is a marked no-op. '
                'No muzzle sibling and no pitched ClothHit are created.'
            ),
        },
        {
            'step': 10, 'status': 'build', 'title': 'Leave the copied blueprint alone',
            'detail': (
                'That actor is a copy of the boss graph, not a child. '
                'This script does not edit it and does not make another copy of the boss. '
                'It keeps the 1.15 s recovery literal.'
            ),
        },
    ]
    edits = [
        {
            'id': 'damage_ignore',
            'anchor': 'ReceiveAnyDamage then -> Branch(Health > 0)',
            'change': (
                'Insert Branch(State==5) on that exec wire. '
                'else continues the original health chain. '
                'then is unwired and carries the step-9 extension note.'
            ),
        },
        {
            'id': 'phase_entry',
            'anchor': 'Branch(Health <= 0) else -> hit-reaction branch',
            'change': (
                'Insert Branch(NOT bPhase2 AND Health <= PhaseChangeHealth AND State != 5 AND State != 3). '
                'then sets State 5, StateAge 0, hides AttackWarning, plays Stagger once, clears bThreatStarted. '
                'Leaving state 1 is what cancels a pending slam: the strike only fires from the state-1 tick branch. '
                'else continues the original hit-reaction branch.'
            ),
        },
        {
            'id': 'state5_tick',
            'anchor': 'Branch(State==4) else, which is unwired',
            'change': (
                'Attach Branch(State==5). Exit is tested first so the exec input stays single: '
                'StateAge >= StaggerSeconds+ThreatSeconds sets bPhase2, bNextAttackLeft true, '
                'PhaseFlashUntil = now+0.15, State 0, StateAge 0, and plays looping Walk. '
                'Otherwise, StateAge >= StaggerSeconds and not bThreatStarted plays Threat once. '
                'State 5 does not move the boss. Stagger and Threat do not loop.'
            ),
        },
        {
            'id': 'recovery_switch',
            'anchor': 'Greater_DoubleDouble whose A is StateAge and whose B literal is 1.15',
            'change': (
                'Connect B to SelectFloat A=Phase2Recovery(0.8) B=Phase1Recovery(1.15) bPickA=bPhase2. '
                'The compare stays strict greater-than, so phase 1 still waits just past 1.15 s.'
            ),
        },
        {
            'id': 'anticipation_clips',
            'anchor': 'Set State 1 -> Set StateAge 0 -> PlayAnimation(A_Teddy_Attack, false) -> SetVisibility true',
            'change': (
                'After Set StateAge 0, Branch(bPhase2 AND bNextAttackLeft). '
                'then: PlayAnimation(AttackLeft, false), SetPlayRate(AttackLeftPlayRate), '
                'set bNextAttackLeft false, show the ring. '
                'else: the existing Attack play, set bNextAttackLeft = bPhase2, show the ring.'
            ),
        },
        {
            'id': 'attack_left_rate',
            'anchor': 'PlayAnimation(AttackLeft) then',
            'change': (
                'SetPlayRate immediately after that PlayAnimation. '
                'PlayAnimation resets the single-node rate to 1, so the set has to follow it. '
                'Every other PlayAnimation is left to restore 1.0 by itself.'
            ),
        },
    ]
    return {
        'script': 'tools/build_boss_escalation_v1.py',
        'tag': {'key': TAG_GAME016, 'value': TAG_VALUE},
        'steps': steps,
        'imports': imports,
        'variables': variable_plan(timings),
        'edits': edits,
        'hud': {
            'anchor': 'HUD.DrawRect whose RectColor literal is (R=.49,G=.08,B=.065,A=1)',
            'boss_actor': 'GameplayStatics.GetActorOfClass whose ActorClass is BP_TeddyBoss',
            'change': (
                'Feed RectColor from nested SelectColor. '
                'State==5 picks grey (R=.32,G=.32,B=.32,A=1). '
                'Else GetTimeSeconds < PhaseFlashUntil picks (R=.95,G=.12,B=.08,A=1). '
                'Else keep the original colour. ScreenW and the rest of the width math stay.'
            ),
            'grey': GREY,
            'flash': FLASH_RED,
            'original': BOSS_BAR,
            'width': 'unchanged',
        },
        'assets_to_save': [
            anim_object_path('Stagger'),
            anim_object_path('Threat'),
            anim_object_path('AttackLeft'),
            BOSS_ASSET,
            HUD_ASSET,
        ],
        'not_touched': {
            'names': list(NOT_TOUCHED_NAMES),
            'byte_hash_paths': list(UNCHANGED_HASH_PATHS),
        },
        'explicitly_not_created': ['AnimBlueprint', 'AnimMontage', 'BlendSpace'],
        'locks': {
            'required_before_apply': list(REQUIRED_LOCKS),
            'after_import_before_commit': list(NEW_ANIM_LOCKS),
            'also_if_already_on_disk': (
                'If a phase-2 clip asset already exists, apply also requires that path in ours.'
            ),
            'command': HOW_TO_RUN['lock_command'],
            'fail_closed': 'Non-zero git, unreadable JSON, a required path in theirs, or a missing path aborts before edits.',
        },
        'timings': timings,
        'how_to_run': HOW_TO_RUN,
        'single_node': {
            'implemented_as': (
                'In phase 2 the existing recovery-end path (state 2 to 0, PlayAnimation Walk looping) '
                'fires at 0.8 s and cuts Attack.'
            ),
            'out_of_scope': SINGLE_NODE_NOTE,
            'cut_seconds': timings['attack_cut']['cut_seconds'],
        },
        'open_items': [
            'A true blend needs a later animation-blueprint or single-node montage decision.',
            'The no-damage cue (step 9) waits for approval.',
            'Warning-ring readability on FloorRecoveryV4 still needs an in-editor capture.',
        ],
        'qa': [
            'Triggers once, on the 13th 12-damage hit from 300, and the bar shows 144.',
            'No boss health is removed while state is 5. Stagger does not loop.',
            'A pending slam is cancelled because state 1 is left and the ring is hidden.',
            'Phase-2 slam gap is at least about 1.72 s. AttackLeft impact matches the 0.92 s timer.',
            'F5 reloads class defaults: bPhase2 false and boss health 300.',
            'The copied blueprint stays damageable during the window and keeps a 1.15 s recovery.',
        ],
    }


def format_plan(plan):
    lines = [
        'GAME-016 phase 2 escalation plan (no assets are changed by --plan)',
        '',
        'How Luther runs it',
        f"  plan:    {plan['how_to_run']['plan']}",
        f"  json:    {plan['how_to_run']['plan_json']}",
        f"  inspect: {plan['how_to_run']['inspect']}",
        '  apply, from the repo root, in the same shell:',
        *[f'    {line}' for line in plan['how_to_run']['apply_shell'].splitlines()],
        f"  {plan['how_to_run']['agents']}",
        f"  receipt: {plan['how_to_run']['receipt']}",
        '',
        'LFS locks',
        f"  check: {plan['locks']['command']}",
        '  required before apply:',
        *[f'    {path}' for path in plan['locks']['required_before_apply']],
        '  lock these after import and before commit:',
        *[f'    {path}' for path in plan['locks']['after_import_before_commit']],
        f"  {plan['locks']['also_if_already_on_disk']}",
        f"  {plan['locks']['fail_closed']}",
        '',
        'Timing',
    ]
    left = plan['timings']['attack_left']
    change = plan['timings']['phase_change']
    cut = plan['timings']['attack_cut']
    hits = plan['timings']['threshold']
    lines.extend([
        f"  AttackLeft frames {left['frames']}, impact frame {left['impact_frame']}, "
        f"length {left['play_length']:.6f}s, impact {left['impact_time']:.6f}s, "
        f"rate {left['play_rate']:.6f}, scaled length {left['scaled_length']:.6f}s, "
        f"cycle {left['cycle_seconds']:.2f}s, fits {left['fits_in_cycle']}",
        f"  Stagger {change['stagger_seconds']:.6f}s ({change['stagger_frames']} frames), "
        f"Threat {change['threat_seconds']:.6f}s ({change['threat_frames']} frames), "
        f"sum {change['total_seconds']:.6f}s, frame-count sum {change['frame_count_sum']} "
        f"(doc {change['doc_frame_count']} frames, about {change['doc_seconds']:.1f}s)",
        f"  shipped Attack {cut['attack_seconds']:.6f}s, phase-2 cycle {cut['cycle_seconds']:.2f}s, "
        f"cut {cut['cut_seconds']:.6f}s, then Walk",
        f"  threshold hit {hits['hits']} shows HP {hits['hp']} "
        f"(from {hits['max_health']} by {hits['damage']}, line {hits['threshold']})",
        '',
        'Checklist',
    ])
    for step in plan['steps']:
        lines.append(f"  {step['step']}. [{step['status']}] {step['title']}")
        lines.append(f"     {step['detail']}")
    lines.extend(['', 'Imports'])
    for item in plan['imports']:
        lines.append(
            f"  {item['name']}: {item['source']} sha256 {item['sha256']} -> {item['destination']}"
        )
    lines.extend(['', 'Variables (phase-1 defaults)'])
    for item in plan['variables']:
        lines.append(f"  {item['name']} ({item['type']}) = {item['default']}  {item['note']}")
    lines.extend(['', 'Graph edits'])
    for item in plan['edits']:
        lines.append(f"  {item['id']}")
        lines.append(f"    anchor: {item['anchor']}")
        lines.append(f"    change: {item['change']}")
    lines.extend([
        '',
        'HUD',
        f"  anchor: {plan['hud']['anchor']}",
        f"  actor:  {plan['hud']['boss_actor']}",
        f"  change: {plan['hud']['change']}",
        '',
        'Assets to save',
        *[f"  {path}" for path in plan['assets_to_save']],
        '',
        'Not touched',
        *[f"  {name}" for name in plan['not_touched']['names']],
        '  byte hashes before and after:',
        *[f"    {path}" for path in plan['not_touched']['byte_hash_paths']],
        '',
        'Not created',
        *[f"  {name}" for name in plan['explicitly_not_created']],
        '',
        'Single-node limit',
        f"  {plan['single_node']['implemented_as']}",
        f"  {plan['single_node']['out_of_scope']}",
        '',
        'Open items',
        *[f'  - {item}' for item in plan['open_items']],
        '',
        'QA this design is meant to satisfy',
        *[f'  - {item}' for item in plan['qa']],
        '',
    ])
    return '\n'.join(lines)


def main(argv=None):
    if argv is None:
        argv = sys.argv
    mode = resolve_mode(module_has_unreal(), argv, os.environ)
    if mode.action == 'plan':
        plan = build_plan()
        if mode.json_out:
            print(json.dumps(plan, indent=2), flush=True)
        else:
            print(format_plan(plan), flush=True)
        return 0
    if mode.action == 'refuse':
        print(mode.reason, file=sys.stderr, flush=True)
        return mode.exit_code
    return editor_main(mode)


def editor_main(mode):
    payload = {
        'script': 'tools/build_boss_escalation_v1.py',
        'mode': mode.action,
        'passed': False,
        'tag': {'key': TAG_GAME016, 'value': TAG_VALUE},
        'cue_extension_point': CUE_EXTENSION_NOTE,
        'single_node_blend': SINGLE_NODE_NOTE,
        'not_touched': list(NOT_TOUCHED_NAMES),
        'unchanged_hash_paths': list(UNCHANGED_HASH_PATHS),
    }
    code = 1
    try:
        editor = Editor()
        if mode.action == 'inspect':
            run_inspect(editor, payload)
        elif mode.action == 'apply':
            run_apply(editor, payload)
        else:
            raise RuntimeError(f'unexpected editor action {mode.action}')
        code = 0 if payload.get('passed') else 1
    except Exception as error:
        payload['error'] = traceback.format_exc()
        if isinstance(error, AnchorError):
            payload['anchor_failure'] = error.as_receipt()
        payload['passed'] = False
        code = 1
    try:
        path = write_receipt(ROOT, mode.action, payload)
        print(
            f"GAME-016 {mode.action} passed={payload.get('passed')} "
            f"receipt={path.relative_to(ROOT).as_posix()}",
            flush=True,
        )
    except Exception:
        traceback.print_exc()
        return 1
    if payload.get('error'):
        print(payload['error'], file=sys.stderr, flush=True)
    return code


class Editor:
    """Imported unreal helpers. Constructing this is the editor-only import boundary."""

    def __init__(self):
        import unreal as unreal_module
        tools = str(ROOT / 'tools')
        if tools not in sys.path:
            sys.path.insert(0, tools)
        from encounter_authoring import A, L, Graph, compile, components, existing, own, save
        self.u = unreal_module
        self.A = A
        self.L = L
        self.Graph = Graph
        self.compile = compile
        self.components = components
        self.existing = existing
        self.own = own
        self.save = save


def run_inspect(editor, payload):
    boss, hud, skeleton, names, tag, state = load_targets(editor)
    payload['saved_state'] = state
    payload['tag_value'] = tag
    payload['variables_present'] = sorted(names)
    payload['compile_results'] = {'BP_TeddyBoss': 'not_run', 'BP_EncounterHUD': 'not_run'}
    payload['imports'] = manifest_inventory()
    if state == 'partial':
        raise PartialStateError(partial_message(tag, names))
    if state == 'already_applied':
        missing = [name for name in NEW_VARS if name not in names]
        if missing:
            raise AnchorError('tag', f'completed tag is set but variables are missing: {missing}')
        payload['already_applied'] = True
        payload['anchors_found'] = {'skipped': 'already applied; pre-edit anchors are not required'}
    else:
        boss_graph = editor.Graph(boss)
        hud_graph = editor.Graph(hud)
        anchors = find_boss_anchors(editor, boss, boss_graph.g, names)
        hud_anchors = find_hud_anchors(editor, hud_graph.g)
        confirm_component(editor, boss)
        payload['anchors_found'] = describe_anchors(anchors, hud_anchors)
        payload['already_applied'] = False
    payload['computed_timings'] = compute_timings(shipped_attack_length=read_attack_length(editor))
    payload['unchanged_hashes'] = {'before': hash_files(ROOT, UNCHANGED_HASH_PATHS), 'after': None, 'unchanged': None}
    payload['skeleton'] = skeleton.get_path_name()
    payload['passed'] = True


def run_apply(editor, payload):
    boss, hud, skeleton, names, tag, state = load_targets(editor)
    payload['saved_state'] = state
    payload['tag_value'] = tag
    payload['variables_present'] = sorted(names)
    if state == 'already_applied':
        missing = [name for name in NEW_VARS if name not in names]
        if missing:
            raise AnchorError('tag', f'completed tag is set but variables are missing: {missing}')
        before = hash_files(ROOT, UNCHANGED_HASH_PATHS)
        payload['already_applied'] = True
        payload['anchors_found'] = {'skipped': 'already applied'}
        payload['compile_results'] = {'BP_TeddyBoss': 'skipped', 'BP_EncounterHUD': 'skipped'}
        payload['variables_added'] = []
        payload['nodes_added'] = []
        payload['nodes_relinked'] = []
        payload['imports'] = manifest_inventory()
        payload['computed_timings'] = compute_timings()
        payload['unchanged_hashes'] = {'before': before, 'after': before, 'unchanged': True}
        payload['passed'] = True
        print('GAME-016 apply: escalation-v1 is already on the boss. No assets saved.', flush=True)
        return
    if state == 'partial':
        raise PartialStateError(partial_message(tag, names))
    stage(payload, 'anchors')
    boss_graph = editor.Graph(boss)
    anchors = find_boss_anchors(editor, boss, boss_graph.g, names)
    hud_graph = editor.Graph(hud)
    hud_anchors = find_hud_anchors(editor, hud_graph.g)
    confirm_component(editor, boss)
    payload['anchors_found'] = describe_anchors(anchors, hud_anchors)
    payload['already_applied'] = False
    stage(payload, 'locks')
    required = locks_required_for_apply(ROOT)
    payload['locks'] = read_locks(required)
    before = hash_files(ROOT, UNCHANGED_HASH_PATHS)
    payload['unchanged_hashes'] = {'before': before}
    stage(payload, 'import clips')
    imported = import_clips(editor, skeleton)
    payload['imports'] = imported
    lengths = {item['name']: item['play_length'] for item in imported}
    timings = compute_timings(
        attack_left_length=lengths['AttackLeft'],
        stagger_length=lengths['Stagger'],
        threat_length=lengths['Threat'],
        shipped_attack_length=read_attack_length(editor),
    )
    payload['computed_timings'] = timings
    stage(payload, 'add variables')
    added_vars = add_variables(editor, boss, boss_graph, timings)
    payload['variables_added'] = added_vars
    # Hardening after the 21:37 native crash (no node had spawned yet): bring the
    # skeleton class up to date with the ten new variables before any node is
    # spawned against it, then re-find the anchors on a fresh graph wrapper and
    # require the very same nodes. In memory only; nothing is saved here, and the
    # authored graph is unchanged.
    stage(payload, 'refresh boss after variables (compile, no save)')
    compile_clean(editor, boss)
    stage(payload, 're-find anchors')
    boss_graph = editor.Graph(boss)
    anchors = reconfirm_anchors(anchors, find_boss_anchors(editor, boss, boss_graph.g, names))
    relinked, added_nodes, comment = mutate_boss(editor, boss_graph, anchors, timings, payload)
    payload['nodes_relinked'] = relinked
    payload['nodes_added'] = added_nodes
    payload['cue_marker'] = comment
    # Compile both blueprints in memory first and save nothing until both are clean,
    # so a HUD failure cannot leave a saved, untagged half-edit of the boss. The HUD
    # needs the compiled boss class to read PhaseFlashUntil. (Tech review.)
    stage(payload, 'compile boss (in memory)')
    compile_clean(editor, boss)
    payload['compile_results'] = {'BP_TeddyBoss': 'clean (not yet saved)'}
    stage(payload, 'mutate hud')
    hud_graph = editor.Graph(hud)
    hud_added, hud_relinked = mutate_hud(editor, hud_graph, hud_anchors, boss)
    payload['nodes_added'].extend(hud_added)
    payload['nodes_relinked'].extend(hud_relinked)
    stage(payload, 'compile hud (in memory)')
    compile_clean(editor, hud)
    payload['compile_results'] = {'BP_TeddyBoss': 'clean', 'BP_EncounterHUD': 'clean'}
    stage(payload, 'tag and save')
    editor.A.set_metadata_tag(boss, TAG_GAME016, TAG_VALUE)
    editor.save(hud)
    editor.save(boss)
    stage(payload, 'saved')
    after = hash_files(ROOT, UNCHANGED_HASH_PATHS)
    payload['unchanged_hashes']['after'] = after
    payload['unchanged_hashes']['unchanged'] = after == before
    if after != before:
        changed = [key for key in after if after[key] != before.get(key)]
        raise RuntimeError('files that must stay byte-for-byte unchanged were rewritten: ' + ', '.join(changed))
    payload['passed'] = True


def compile_clean(editor, blueprint):
    """encounter_authoring.compile without its save: compile, then refuse any error node."""
    if not editor.L.compile_blueprint(blueprint):
        raise RuntimeError('compile failed: ' + blueprint.get_path_name())
    errors = []
    for graph in editor.L.list_graphs(blueprint):
        for node in editor.u.BlueprintGraphEditor.get_graph_editor(graph).list_nodes_with_errors():
            errors.append((node.get_name(), str(editor.L.get_node_title(node))))
    if errors:
        raise RuntimeError(f'compile errors in {blueprint.get_path_name()}: {errors}')


def partial_message(tag, names):
    present = [name for name in NEW_VARS if name in names]
    return (
        'Refusing a partial or unknown boss graph. '
        f'Tag {TAG_GAME016!r} is {tag!r}; new variables already present: {present}. '
        'A completed run is tagged escalation-v1. Restore the boss blueprint before retrying.'
    )


def load_targets(editor):
    boss = editor.existing(BOSS_ASSET)
    hud = editor.existing(HUD_ASSET)
    skeleton = editor.existing(SKELETON_ASSET)
    if not boss or not hud or not skeleton:
        raise AnchorError('assets', f'missing boss={bool(boss)} hud={bool(hud)} skeleton={bool(skeleton)}')
    names = member_names(editor, boss)
    missing = [name for name in REQUIRED_VARS if name not in names]
    if missing:
        raise AnchorError('variables', f'missing {missing}')
    tag = editor.A.get_metadata_tag(boss, TAG_GAME016) or ''
    return boss, hud, skeleton, names, tag, classify_saved_state(tag, names)


def member_names(editor, blueprint):
    return {plain_name(item) for item in editor.L.list_member_variable_names(blueprint)}


def confirm_component(editor, blueprint):
    mapping = editor.components(blueprint)
    keys = [key for key in mapping if key in ('AttackWarning', 'AttackWarning_GEN_VARIABLE')]
    if len(keys) != 1:
        raise AnchorError('AttackWarning', f'expected one component, found {sorted(mapping)}')
    component = mapping[keys[0]][1]
    class_name = component.get_class().get_name()
    if 'StaticMeshComponent' not in class_name:
        raise AnchorError('AttackWarning', f'class is {class_name}')
    return component


def manifest_inventory():
    manifest = read_manifest(MANIFEST_PATH)
    entries = require_manifest_contract(manifest)
    rows = []
    for name in ('Stagger', 'Threat', 'AttackLeft'):
        entry = entries[name]
        source = ANIM_DIR / entry['file']
        checked = verify_clip_file(MANIFEST_PATH, name, source)
        rows.append({
            'name': name,
            'path': anim_object_path(name),
            'sha256': checked['sha256'],
            'frames': checked['frames'],
            'fps': checked['fps'],
            'imported': False,
            'play_length': None,
            'frames_basis': None,
        })
    return rows


def read_locks(required):
    try:
        proc = subprocess.run(
            ['git', 'lfs', 'locks', '--verify', '--json'],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LockCheckError('git_failed', str(exc)) from exc
    return interpret_lock_command(proc.returncode, proc.stdout, proc.stderr, required)


def import_clips(editor, skeleton):
    manifest = read_manifest(MANIFEST_PATH)
    entries = require_manifest_contract(manifest)
    editor.u.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
    rows = []
    for name in ('Stagger', 'Threat', 'AttackLeft'):
        entry = entries[name]
        source = ANIM_DIR / entry['file']
        checked = verify_clip_file(MANIFEST_PATH, name, source)
        destination = anim_object_path(name)
        created = False
        if editor.A.does_asset_exist(destination):
            clip = editor.existing(destination)
            if clip is None:
                raise AnchorError(name, 'destination path did not load')
        else:
            clip = import_anim(editor, skeleton, name, source, destination)
            editor.own(clip)
            editor.save(clip)
            created = True
        if not isinstance(clip, editor.u.AnimSequence):
            raise AnchorError(name, f'imported object is {clip.get_class().get_name()}')
        if clip.get_editor_property('skeleton') != skeleton:
            raise AnchorError(name, 'skeleton does not match SK_Teddy_Skeleton')
        length = float(clip.get_play_length())
        basis = length_basis(length, checked['frames'], checked['fps'])
        object_path = clip.get_path_name().split('.')[0]
        if object_path != destination:
            raise AnchorError(name, f'path {object_path} != {destination}')
        rows.append({
            'name': name,
            'path': destination,
            'sha256': checked['sha256'],
            'frames': checked['frames'],
            'fps': checked['fps'],
            'play_length': length,
            'frames_basis': basis,
            'imported': created,
            'length': length,
        })
    return rows


def import_anim(editor, skeleton, name, source, destination):
    unreal_module = editor.u
    options = unreal_module.FbxImportUI()
    for key, value in {
        'automated_import_should_detect_type': False,
        'import_as_skeletal': True,
        'import_mesh': False,
        'mesh_type_to_import': unreal_module.FBXImportType.FBXIT_ANIMATION,
        'import_animations': True,
        'import_materials': False,
        'import_textures': False,
        'create_physics_asset': False,
        'skeleton': skeleton,
        'override_animation_name': f'A_Teddy_{name}',
    }.items():
        options.set_editor_property(key, value)
    for data in (options.skeletal_mesh_import_data, options.anim_sequence_import_data):
        for key in ('convert_scene', 'convert_scene_unit', 'force_front_x_axis'):
            data.set_editor_property(key, True)
    anim_data = options.anim_sequence_import_data
    anim_data.set_editor_property('use_default_sample_rate', False)
    anim_data.set_editor_property('custom_sample_rate', 30)
    anim_data.set_editor_property('import_custom_attribute', False)
    anim_data.set_editor_property('add_curve_metadata_to_skeleton', False)
    task = unreal_module.AssetImportTask()
    task.filename = str(source)
    task.destination_path = destination.rsplit('/', 1)[0]
    task.destination_name = f'A_Teddy_{name}'
    task.automated = True
    task.save = False
    task.replace_existing = False
    task.options = options
    unreal_module.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(task.imported_object_paths)
    if len(imported) != 1:
        raise AnchorError(name, f'import returned {imported}')
    clip = editor.A.load_asset(imported[0])
    if clip is None:
        raise AnchorError(name, 'import returned an empty asset')
    return clip


def read_attack_length(editor):
    if not editor.A.does_asset_exist(ATTACK_ASSET):
        return None
    clip = editor.A.load_asset(ATTACK_ASSET)
    if clip is None:
        return None
    try:
        return float(clip.get_play_length())
    except Exception:
        return None


def add_variables(editor, blueprint, graph, timings):
    change = timings['phase_change']
    rate = timings['attack_left']['play_rate']
    specs = [
        ('bPhase2', 'bool', 'false'),
        ('bNextAttackLeft', 'bool', 'true'),
        ('bThreatStarted', 'bool', 'false'),
        ('PhaseChangeHealth', 'real', ue_number(PHASE_CHANGE_HEALTH)),
        ('Phase1Recovery', 'real', ue_number(PHASE1_RECOVERY)),
        ('Phase2Recovery', 'real', ue_number(PHASE2_RECOVERY)),
        ('StaggerSeconds', 'real', ue_number(change['stagger_seconds'])),
        ('ThreatSeconds', 'real', ue_number(change['threat_seconds'])),
        ('AttackLeftPlayRate', 'real', ue_number(rate)),
        ('PhaseFlashUntil', 'real', '0'),
    ]
    added = []
    for name, kind, value in specs:
        if editor.L.get_member_variable_type(blueprint, name) is not None:
            raise PartialStateError(f'{name} appeared during apply before it was added')
        graph.var(name, kind, value)
        editor.L.set_blueprint_variable_instance_editable(blueprint, name, True)
        added.append({'name': name, 'type': kind, 'default': value})
    return added


def mutate_boss(editor, graph, anchors, timings, payload=None):
    del timings  # durations and the rate are read from the new variables at runtime
    payload = {} if payload is None else payload
    stage(payload, 'mutate boss: damage ignore')
    added = []
    relinked = []
    damage_links = pin_endpoints(anchors['damage_event'], 'Damage', 'out')

    ignore = graph.branch((graph.math('EqualEqual_IntInt', A=val(graph, 'State'), B=5), 'ReturnValue'))
    rewire_exec(anchors['damage_event'], 'then', ignore, 'else', anchors['damage_health'])
    comment = mark_extension(editor, graph, ignore)
    added.append(node_id(ignore))
    relinked.append({
        'id': 'damage_ignore',
        'anchor': node_id(anchors['damage_event']),
        'inserted': node_id(ignore),
        'continues': node_id(anchors['damage_health']),
    })

    stage(payload, 'mutate boss: phase entry')
    not_phase = graph.math('Not_PreBool', A=val(graph, 'bPhase2'))
    low_health = graph.math(
        'LessEqual_DoubleDouble', A=val(graph, 'Health'), B=val(graph, 'PhaseChangeHealth'),
    )
    not_five = graph.math('NotEqual_IntInt', A=val(graph, 'State'), B=5)
    not_dead = graph.math('NotEqual_IntInt', A=val(graph, 'State'), B=3)
    enter_flag = graph.math('BooleanAND', A=(not_phase, 'ReturnValue'), B=(low_health, 'ReturnValue'))
    enter_state = graph.math('BooleanAND', A=(not_five, 'ReturnValue'), B=(not_dead, 'ReturnValue'))
    enter_all = graph.math('BooleanAND', A=(enter_flag, 'ReturnValue'), B=(enter_state, 'ReturnValue'))
    enter = graph.branch((enter_all, 'ReturnValue'))
    rewire_exec(anchors['lethal'], 'else', enter, 'else', anchors['react'])
    set_five = graph.set('State', 5)
    clear_age = graph.set('StateAge', 0)
    hide = warning(graph, False)
    stagger = play(graph, 'Stagger', False)
    clear_threat = graph.set('bThreatStarted', 'false')
    graph.link(enter, 'then', set_five, 'execute')
    graph.chain(set_five, clear_age, hide, stagger, clear_threat)
    added.extend(node_id(node) for node in (enter, set_five, clear_age, hide, stagger, clear_threat))
    relinked.append({
        'id': 'phase_entry',
        'anchor': node_id(anchors['lethal']),
        'inserted': node_id(enter),
        'continues': node_id(anchors['react']),
        'stagger_loops': False,
    })

    stage(payload, 'mutate boss: state 5 tick')
    phase = graph.branch((graph.math('EqualEqual_IntInt', A=val(graph, 'State'), B=5), 'ReturnValue'))
    graph.link(anchors['hit_state'], 'else', phase, 'execute')
    total = graph.math('Add_DoubleDouble', A=val(graph, 'StaggerSeconds'), B=val(graph, 'ThreatSeconds'))
    exit_ready = graph.branch((
        graph.math('GreaterEqual_DoubleDouble', A=val(graph, 'StateAge'), B=(total, 'ReturnValue')),
        'ReturnValue',
    ))
    graph.link(phase, 'then', exit_ready, 'execute')
    set_phase = graph.set('bPhase2', 'true')
    set_next = graph.set('bNextAttackLeft', 'true')
    now = graph.call('GameplayStatics.GetTimeSeconds')
    flash = graph.math('Add_DoubleDouble', A=(now, 'ReturnValue'), B=ue_number(FLASH_SECONDS))
    set_flash = graph.set('PhaseFlashUntil', (flash, 'ReturnValue'))
    set_chase = graph.set('State', 0)
    set_age = graph.set('StateAge', 0)
    walk = play(graph, 'Walk', True)
    graph.link(exit_ready, 'then', set_phase, 'execute')
    graph.chain(set_phase, set_next, set_flash, set_chase, set_age, walk)
    not_started = graph.math('Not_PreBool', A=val(graph, 'bThreatStarted'))
    age_ok = graph.math('GreaterEqual_DoubleDouble', A=val(graph, 'StateAge'), B=val(graph, 'StaggerSeconds'))
    threat_and = graph.math('BooleanAND', A=(age_ok, 'ReturnValue'), B=(not_started, 'ReturnValue'))
    threat_branch = graph.branch((threat_and, 'ReturnValue'))
    graph.link(exit_ready, 'else', threat_branch, 'execute')
    mark_started = graph.set('bThreatStarted', 'true')
    threat = play(graph, 'Threat', False)
    graph.link(threat_branch, 'then', mark_started, 'execute')
    graph.chain(mark_started, threat)
    added.extend(node_id(node) for node in (
        phase, exit_ready, set_phase, set_next, set_flash, set_chase, set_age, walk, threat_branch, mark_started, threat,
    ))
    relinked.append({
        'id': 'state5_tick',
        'anchor': node_id(anchors['hit_state']),
        'inserted': node_id(phase),
        'exit_first': True,
        'threat_loops': False,
        'walk_loops': True,
    })

    stage(payload, 'mutate boss: recovery select')
    select = graph.math(
        'SelectFloat',
        A=val(graph, 'Phase2Recovery'),
        B=val(graph, 'Phase1Recovery'),
        bPickA=val(graph, 'bPhase2'),
    )
    graph.link(select, 'ReturnValue', anchors['recovery_compare'], 'B')
    added.append(node_id(select))
    relinked.append({
        'id': 'recovery_switch',
        'anchor': node_id(anchors['recovery_compare']),
        'inserted': node_id(select),
    })

    stage(payload, 'mutate boss: anticipation clips')
    choice_and = graph.math('BooleanAND', A=val(graph, 'bPhase2'), B=val(graph, 'bNextAttackLeft'))
    choice = graph.branch((choice_and, 'ReturnValue'))
    rewire_exec(anchors['anticipation_age'], 'then', choice, 'else', anchors['attack_play'])
    play_left = play(graph, 'AttackLeft', False)
    # PlayAnimation resets the single-node rate to 1. Set the retimed rate after it starts.
    set_rate = graph.call(
        'SkeletalMeshComponent.SetPlayRate',
        self=val(graph, 'Mesh'),
        Rate=val(graph, 'AttackLeftPlayRate'),
    )
    clear_left = graph.set('bNextAttackLeft', 'false')
    show_left = warning(graph, True)
    graph.link(choice, 'then', play_left, 'execute')
    graph.chain(play_left, set_rate, clear_left, show_left)
    break_exec(anchors['attack_play'], 'then')
    set_follow = graph.set('bNextAttackLeft', val(graph, 'bPhase2'))
    graph.link(anchors['attack_play'], 'then', set_follow, 'execute')
    graph.link(set_follow, 'then', anchors['attack_show'], 'execute')
    added.extend(node_id(node) for node in (choice, play_left, set_rate, clear_left, show_left, set_follow))
    relinked.append({
        'id': 'anticipation_clips',
        'anchor': node_id(anchors['anticipation_age']),
        'inserted': node_id(choice),
        'attack_play': node_id(anchors['attack_play']),
        'attack_left_rate_node': node_id(set_rate),
    })

    if pin_endpoints(anchors['damage_event'], 'Damage', 'out') != damage_links:
        raise AnchorError('ReceiveAnyDamage', 'Damage output links changed')
    return relinked, added, comment


def mutate_hud(editor, graph, anchors, boss):
    bar = anchors['boss_bar']
    before = {pin: pin_endpoints(bar, pin, 'in') for pin in ('ScreenX', 'ScreenY', 'ScreenW', 'ScreenH')}
    if pin_endpoints(bar, 'RectColor', 'in'):
        raise AnchorError('boss bar', 'RectColor was already connected')
    boss_class = editor.L.generated_class(boss)
    class_path = boss_class.get_path_name()
    boss_node = anchors['boss_actor']
    state = graph.get('State', class_path)
    graph.val(state, 'self', (boss_node, 'ReturnValue'))
    flash_until = graph.get('PhaseFlashUntil', class_path)
    graph.val(flash_until, 'self', (boss_node, 'ReturnValue'))
    is_five = graph.math('EqualEqual_IntInt', A=(state, 'State'), B=5)
    now = graph.call('GameplayStatics.GetTimeSeconds')
    flashing = graph.math('Less_DoubleDouble', A=(now, 'ReturnValue'), B=(flash_until, 'PhaseFlashUntil'))
    inner = graph.math('SelectColor', A=FLASH_RED, B=BOSS_BAR, bPickA=(flashing, 'ReturnValue'))
    outer = graph.math('SelectColor', A=GREY, B=(inner, 'ReturnValue'), bPickA=(is_five, 'ReturnValue'))
    graph.link(outer, 'ReturnValue', bar, 'RectColor')
    after = {pin: pin_endpoints(bar, pin, 'in') for pin in ('ScreenX', 'ScreenY', 'ScreenW', 'ScreenH')}
    if after != before:
        raise AnchorError('boss bar', f'width math changed from {before} to {after}')
    if not pin_endpoints(bar, 'RectColor', 'in'):
        raise AnchorError('boss bar', 'RectColor did not connect')
    added = [node_id(node) for node in (state, flash_until, is_five, inner, outer)]
    relinked = [{
        'id': 'hud_bar',
        'anchor': node_id(bar),
        'boss_actor': node_id(boss_node),
        'width': 'unchanged',
    }]
    return added, relinked


def find_boss_anchors(editor, blueprint, graph, names):
    del blueprint, names
    nodes = k2_nodes(graph)
    damage = find_event(editor, graph, 'ReceiveAnyDamage')
    tick = find_event(editor, graph, 'ReceiveTick')
    damage_health = exec_one(damage, 'then', 'ReceiveAnyDamage.then')
    require_compare(editor, 'ReceiveAnyDamage.then', damage_health, 'Health', '>', 0)
    set_health = exec_one(damage_health, 'then', 'damage health then')
    if not is_set(editor, set_health, 'Health'):
        raise AnchorError('Set Health', 'unexpected node', dump=node_dump(editor, set_health))
    health_pin = set_health.find_input_pin('Health')
    health_source = linked_call(editor, health_pin)
    if call_name(editor, health_source) not in ('', 'FMax'):
        raise AnchorError('Set Health', 'value is not FMax')
    set_hits = exec_one(set_health, 'then', 'Set Health.then')
    if not is_set(editor, set_hits, 'HitsReceived'):
        raise AnchorError('Set HitsReceived', 'unexpected node', dump=node_dump(editor, set_hits))
    lethal = exec_one(set_hits, 'then', 'HitsReceived.then')
    require_compare(editor, 'lethal', lethal, 'Health', '<=', 0)
    dead = exec_one(lethal, 'then', 'lethal.then')
    if not is_set_literal(editor, dead, 'State', 3):
        raise AnchorError('lethal.then', 'unexpected node', dump=node_dump(editor, dead))
    react = exec_one(lethal, 'else', 'lethal.else')
    if react.get_class().get_name() != 'K2Node_IfThenElse':
        raise AnchorError('hit reaction', 'unexpected node', dump=node_dump(editor, react))
    react_call = call_name(editor, condition_node(react))
    if react_call not in ('', 'BooleanAND'):
        raise AnchorError('hit reaction', f'condition is {react_call}')

    set_age = exec_one(tick, 'then', 'ReceiveTick.then')
    if not is_set(editor, set_age, 'StateAge'):
        raise AnchorError('tick age', 'unexpected node', dump=node_dump(editor, set_age))
    alive = exec_one(set_age, 'then', 'StateAge.then')
    require_compare(editor, 'tick alive', alive, 'Health', '>', 0)
    chase = exec_one(alive, 'then', 'alive.then')
    require_compare(editor, 'state 0', chase, 'State', '==', 0)
    windup = exec_one(chase, 'else', 'state 0 else')
    require_compare(editor, 'state 1', windup, 'State', '==', 1)
    ready = exec_one(windup, 'then', 'state 1 then')
    require_compare(editor, 'windup 0.92', ready, 'StateAge', '>=', TELEGRAPH_SECONDS)
    recovery = exec_one(windup, 'else', 'state 1 else')
    require_compare(editor, 'state 2', recovery, 'State', '==', 2)
    done = exec_one(recovery, 'then', 'state 2 then')
    require_compare(editor, 'recovery 1.15', done, 'StateAge', '>', PHASE1_RECOVERY)
    hit_state = exec_one(recovery, 'else', 'state 2 else')
    require_compare(editor, 'state 4', hit_state, 'State', '==', 4)
    hit_done = exec_one(hit_state, 'then', 'state 4 then')
    require_compare(editor, 'hit 0.32', hit_done, 'StateAge', '>', 0.32)
    if exec_nodes(hit_state, 'else'):
        raise AnchorError('state 4 else', 'expected an unwired else pin')

    recovery_compare = condition_node(done)
    recovery_b = recovery_compare.find_input_pin('B')
    if list(recovery_b.list_connected_pins()):
        raise AnchorError('recovery B', 'already connected')
    state_sets = [node for node in nodes if is_set_literal(editor, node, 'State', 1)]
    if len(state_sets) != 1:
        raise AnchorError('Set State 1', f'found {len(state_sets)}')
    anticipation_age = exec_one(state_sets[0], 'then', 'Set State 1.then')
    if not is_set_literal(editor, anticipation_age, 'StateAge', 0):
        raise AnchorError('anticipation age', 'unexpected node', dump=node_dump(editor, anticipation_age))
    attack_play = exec_one(anticipation_age, 'then', 'anticipation age.then')
    if not is_play(editor, attack_play, 'Attack', False):
        raise AnchorError('Attack play', 'unexpected node', dump=node_dump(editor, attack_play))
    attack_show = exec_one(attack_play, 'then', 'Attack.then')
    if not is_warning(editor, attack_show, True):
        raise AnchorError('Attack show', 'unexpected node', dump=node_dump(editor, attack_show))
    state_fives = [node for node in nodes if is_state_branch(editor, node, 5)]
    if state_fives:
        raise AnchorError('State==5', f'already present: {[describe(editor, node) for node in state_fives]}')
    recovery_nodes = [
        node for node in nodes
        if is_compare_node(editor, node, '>') and linked_var(editor, node.find_input_pin('A')) == 'StateAge'
        and near(numeric_literal(node.find_input_pin('B'))[1], PHASE1_RECOVERY)
    ]
    if recovery_nodes != [recovery_compare]:
        raise AnchorError('recovery compare', f'found {len(recovery_nodes)}')
    return {
        'damage_event': damage,
        'damage_health': damage_health,
        'lethal': lethal,
        'react': react,
        'hit_state': hit_state,
        'recovery_compare': recovery_compare,
        'anticipation_age': anticipation_age,
        'attack_play': attack_play,
        'attack_show': attack_show,
    }


def find_hud_anchors(editor, graph):
    nodes = k2_nodes(graph)
    bars = []
    for node in nodes:
        if call_name(editor, node) not in ('', 'DrawRect'):
            continue
        pin = node.find_input_pin('RectColor')
        if not pin.is_valid() or list(pin.list_connected_pins()):
            continue
        parsed = parse_linear_color(pin.get_pin_value())
        if parsed and color_close(parsed, BOSS_BAR_CHANNELS):
            bars.append(node)
    if len(bars) != 1:
        raise AnchorError('boss bar', f'found {len(bars)} DrawRect nodes with the boss colour')
    actors = []
    for node in nodes:
        if call_name(editor, node) not in ('', 'GetActorOfClass'):
            continue
        pin = node.find_input_pin('ActorClass')
        if pin.is_valid() and 'BP_TeddyBoss' in str(pin.get_pin_value()):
            actors.append(node)
    if len(actors) != 1:
        raise AnchorError('boss actor', f'found {len(actors)} GetActorOfClass nodes for the boss')
    return {'boss_bar': bars[0], 'boss_actor': actors[0]}


def reconfirm_anchors(before, after):
    """Return ``after`` only if every anchor is the same node (name and class) as ``before``."""
    old_ids = {key: node_id(node) for key, node in before.items()}
    new_ids = {key: node_id(node) for key, node in after.items()}
    if old_ids != new_ids:
        changed = {key: (old_ids.get(key), new_ids.get(key))
                   for key in sorted(set(old_ids) | set(new_ids)) if old_ids.get(key) != new_ids.get(key)}
        raise AnchorError('anchors after variables', f'anchors moved after the variable refresh: {changed}')
    return after


def describe_anchors(boss_anchors, hud_anchors):
    found = {key: node_id(node) for key, node in boss_anchors.items()}
    found.update({key: node_id(node) for key, node in hud_anchors.items()})
    return found


def k2_nodes(graph):
    return [node for node in graph.list_all_nodes() if node.get_class().get_name().startswith('K2Node')]


def find_event(editor, graph, name):
    direct = None
    try:
        direct = graph.find_event_node(name)
    except Exception:
        direct = None
    matches = [node for node in graph.list_all_nodes() if event_member(editor, node) == name]
    if direct is not None and not any(node.get_name() == direct.get_name() for node in matches):
        matches.append(direct)
    if len(matches) != 1:
        raise AnchorError(name, f'expected one event, found {len(matches)}')
    return matches[0]


def exec_nodes(node, pin_name):
    pin = node.find_output_pin(pin_name)
    if not pin.is_valid():
        raise AnchorError(pin_name, f'{node.get_name()} has no {pin_name} pin')
    return [link.get_owning_node() for link in pin.list_connected_pins()]


def exec_one(node, pin_name, label):
    found = exec_nodes(node, pin_name)
    if len(found) != 1:
        raise AnchorError(label, f'{pin_name} has {len(found)} links')
    return found[0]


def break_exec(node, pin_name):
    pin = node.find_output_pin(pin_name)
    if not pin.is_valid():
        raise AnchorError(pin_name, f'{node.get_name()} has no {pin_name}')
    if not pin.break_pin_links():
        raise AnchorError(pin_name, f'could not disconnect {node.get_name()}.{pin_name}')


def rewire_exec(source, source_pin, inserted, inserted_else_pin, original_target):
    found = exec_nodes(source, source_pin)
    if found != [original_target] and not (len(found) == 1 and found[0].get_name() == original_target.get_name()):
        raise AnchorError(source_pin, 'exec target changed before the edit')
    break_exec(source, source_pin)
    if not source.find_output_pin(source_pin).try_create_connection(inserted.find_input_pin('execute')):
        raise AnchorError(source_pin, 'could not enter the inserted branch')
    if not inserted.find_output_pin(inserted_else_pin).try_create_connection(original_target.find_input_pin('execute')):
        raise AnchorError(inserted_else_pin, 'could not restore the original exec chain')


def condition_node(branch):
    pin = branch.find_input_pin('Condition')
    links = list(pin.list_connected_pins()) if pin.is_valid() else []
    if len(links) != 1:
        raise AnchorError('Condition', f'{branch.get_name()} condition links: {len(links)}')
    return links[0].get_owning_node()


# Function names that mean the same comparison on a saved graph. UE 5 math
# nodes are Kismet *_DoubleDouble calls; *_FloatFloat is the pre-5.0 name that
# a redirect may still report. Nothing else is accepted for an operator.
COMPARE_FUNCTIONS = {
    '>': ('Greater_DoubleDouble', 'Greater_FloatFloat'),
    '>=': ('GreaterEqual_DoubleDouble', 'GreaterEqual_FloatFloat'),
    '<=': ('LessEqual_DoubleDouble', 'LessEqual_FloatFloat'),
    '==': ('EqualEqual_IntInt',),
}


def compare_checks(editor, node, variable, op, value):
    """Check one single-condition branch ``variable <op> value``.

    Returns (ok, checks). ``checks`` is an ordered list of dicts, one per test,
    so a mismatch names the test that failed and what it saw. Any exception
    inside a test is recorded as that test failing; nothing is accepted on error.
    """
    checks = []

    def record(name, ok, **seen):
        checks.append(dict(check=name, ok=bool(ok), **seen))
        return bool(ok)

    def guarded(name, fn):
        try:
            return fn()
        except Exception as error:  # fail closed and say why
            record(name, False, error=f'{type(error).__name__}: {error}')
            return None

    kind = guarded('branch', lambda: node.get_class().get_name())
    if kind is None or not record('branch', kind == 'K2Node_IfThenElse', found=kind):
        return False, checks
    compare = guarded('condition', lambda: _compare_of(node))
    if compare is None:
        if not checks or checks[-1]['check'] != 'condition':
            record('condition', False, found='no single Condition link')
        return False, checks
    record('condition', True, found=node_id(compare))

    expected = COMPARE_FUNCTIONS[op]
    found = guarded('function', lambda: compare_operator(editor, compare))
    if found is None:
        return False, checks
    symbol, via, seen = found
    if not record('function', symbol == op, found=seen, operator=symbol, expected=[op, *expected], via=via):
        return False, checks

    found_var = guarded('A variable', lambda: linked_var(editor, compare.find_input_pin('A')))
    if found_var is None:
        return False, checks
    if not record('A variable', found_var == variable, found=found_var, expected=variable):
        return False, checks

    b = guarded('B literal', lambda: numeric_literal(compare.find_input_pin('B')))
    if b is None:
        return False, checks
    raw, parsed, how = b
    if op == '==':
        ok = parsed is not None and abs(parsed - round(parsed)) <= 1e-6 and int(round(parsed)) == int(value)
    else:
        ok = near(parsed, value)
    record('B literal', ok, raw=raw, parsed=parsed, read_as=how, expected=value)
    return ok, checks


OPERATOR_SYMBOLS = ('>=', '<=', '==', '!=', '>', '<')
FUNCTION_OPERATORS = {name: symbol for symbol, names in COMPARE_FUNCTIONS.items() for name in names}
# Saved UE 5 graphs show math compares as K2Node_PromotableOperator ("float > float").
# Its function reference is not readable from Python, so its operator comes from the
# node title. Only these node classes may be identified by title.
TITLED_OPERATOR_CLASSES = ('K2Node_PromotableOperator', 'K2Node_CallFunction')


def compare_pin_shape(node):
    pin_a = node.find_input_pin('A')
    pin_b = node.find_input_pin('B')
    result = node.find_output_pin('ReturnValue')
    return bool(pin_a.is_valid() and pin_b.is_valid() and result.is_valid())


# UE 5 titles equality in words (KismetMathLibrary DisplayName) and every other
# compare as "float > float" / "integer >= integer". Only these exact phrases.
TITLE_PHRASES = {
    'equal (integer)': '==',
    'equal (float)': '==',
    'not equal (integer)': '!=',
    'not equal (float)': '!=',
}


def title_operator(title):
    """Return the comparison a promotable-operator title names, else ''.

    'float > float' -> '>', '>=' -> '>=', 'Equal (Integer)' -> '==',
    'Not Equal (Integer)' -> '!='. A title with no operator, or with more than one, yields ''.
    """
    text = str(title or '').strip()
    phrase = TITLE_PHRASES.get(text.lower())
    if phrase:
        return phrase
    tokens = text.split()
    found = [token for token in tokens if token in OPERATOR_SYMBOLS]
    if len(found) != 1:
        return ''
    if len(tokens) == 1 or (len(tokens) == 3 and tokens[1] == found[0]):
        return found[0]
    return ''


def compare_operator(editor, node):
    """Identify a compare node's operator. Returns (symbol, via, seen); symbol '' if unknown.

    Accepted: a readable Kismet function name from COMPARE_FUNCTIONS, or, when the name
    cannot be read, the title of a promotable/math node with A, B and a boolean result.
    Anything else is unknown and fails the check.
    """
    kind = node.get_class().get_name()
    name = call_name(editor, node)
    if name:
        return FUNCTION_OPERATORS.get(name, ''), 'name', name
    if kind not in TITLED_OPERATOR_CLASSES or not compare_pin_shape(node):
        return '', 'unidentified', kind
    result_type = str(node.find_output_pin('ReturnValue').get_pin_type_display_string()).strip().lower()
    if result_type != 'boolean':
        return '', 'title', f'{kind} returns {result_type}'
    title = str(editor.L.get_node_title(node))
    return title_operator(title), 'title', f'{kind} {title!r}'


NUMERIC_PIN_TYPES = ('float', 'double', 'real', 'integer', 'int', 'byte')


def numeric_literal(pin):
    """Read an unlinked numeric pin. Returns (raw, value, how).

    An empty default on an unlinked numeric pin is the type default, 0, which is what the
    Blueprint compiler uses (saved promotable-operator pins store ''). A linked pin, a
    non-numeric type or unparsable text gives value None.
    """
    if pin is None or not pin.is_valid():
        return '<no pin>', None, 'missing'
    if list(pin.list_connected_pins()):
        return '<linked>', None, 'linked'
    raw = str(pin.get_pin_value())
    text = raw.strip()
    if text:
        try:
            return raw, float(text), 'text'
        except ValueError:
            return raw, None, 'unparsable'
    ptype = str(pin.get_pin_type_display_string()).lower()
    if any(word in ptype for word in NUMERIC_PIN_TYPES):
        return raw, 0.0, f'empty {ptype} default = 0'
    return raw, None, f'empty non-numeric ({ptype})'


def require_compare(editor, label, node, variable, op, value):
    ok, checks = compare_checks(editor, node, variable, op, value)
    if not ok:
        failed = next((check['check'] for check in checks if not check['ok']), 'unknown')
        raise AnchorError(
            label,
            f'expected branch on {variable} {op} {value}; failed check: {failed}',
            dump=node_dump(editor, node),
            checks=checks,
        )
    return checks


def is_state_branch(editor, node, value):
    return compare_checks(editor, node, 'State', '==', value)[0]


def is_health_compare_branch(editor, node, op, threshold):
    return compare_checks(editor, node, 'Health', op, threshold)[0]


def is_stateage_compare_branch(editor, node, op, threshold):
    return compare_checks(editor, node, 'StateAge', op, threshold)[0]


def _compare_of(node):
    """Return the condition call, or None when this node is not a single-condition branch."""
    if node.get_class().get_name() != 'K2Node_IfThenElse':
        return None
    pin = node.find_input_pin('Condition')
    if not pin.is_valid():
        return None
    links = list(pin.list_connected_pins())
    if len(links) != 1:
        return None
    return links[0].get_owning_node()


def is_set(editor, node, name):
    return node.get_class().get_name() == 'K2Node_VariableSet' and var_name(editor, node) == name


def is_set_literal(editor, node, name, value):
    if not is_set(editor, node, name):
        return False
    pin = node.find_input_pin(name)
    if not pin.is_valid() or list(pin.list_connected_pins()):
        return False
    number = numeric_literal(pin)[1]
    return number is not None and abs(number - round(number)) <= 1e-6 and int(round(number)) == int(value)


def is_compare_node(editor, node, op):
    try:
        if not node.get_class().get_name().startswith('K2Node'):
            return False
        return compare_operator(editor, node)[0] == op
    except Exception:
        return False


def is_play(editor, node, clip, looping):
    # An unreadable function name still matches on the PlayAnimation pins.
    # A different function name does not.
    if node.get_class().get_name() != 'K2Node_CallFunction':
        return False
    if call_name(editor, node) not in ('', 'PlayAnimation'):
        return False
    anim = node.find_input_pin('NewAnimToPlay')
    loop = node.find_input_pin('bLooping')
    self_pin = node.find_input_pin('self')
    if not (anim.is_valid() and loop.is_valid() and self_pin.is_valid()):
        return False
    if clip_from_anim_pin(anim.get_pin_value()) != clip:
        return False
    if literal_bool(loop) is not looping:
        return False
    return linked_var(editor, self_pin) == 'Mesh'


def is_warning(editor, node, visible):
    if call_name(editor, node) not in ('', 'SetVisibility'):
        return False
    show = node.find_input_pin('bNewVisibility')
    self_pin = node.find_input_pin('self')
    if not (show.is_valid() and self_pin.is_valid()):
        return False
    if literal_bool(show) is not visible:
        return False
    return linked_var(editor, self_pin) == 'AttackWarning'


def linked_var(editor, pin):
    if pin is None or not pin.is_valid():
        return ''
    links = list(pin.list_connected_pins())
    if len(links) != 1:
        return ''
    return var_name(editor, links[0].get_owning_node())


def linked_call(editor, pin):
    links = list(pin.list_connected_pins()) if pin.is_valid() else []
    if len(links) != 1:
        raise AnchorError(str(pin.get_pin_name()) if pin.is_valid() else 'pin', 'expected one data link')
    return links[0].get_owning_node()


def call_name(editor, node):
    del editor
    if node.get_class().get_name() != 'K2Node_CallFunction':
        return ''
    try:
        ref = node.get_editor_property('function_reference')
        value = ref.get_editor_property('member_name')
    except Exception:
        return ''
    return plain_name(value)


def var_name(editor, node):
    kind = node.get_class().get_name()
    if kind not in ('K2Node_VariableGet', 'K2Node_VariableSet'):
        return ''
    try:
        ref = node.get_editor_property('variable_reference')
        value = plain_name(ref.get_editor_property('member_name'))
        if value and value != 'None':
            return value
    except Exception:
        pass
    pins = editor.L.list_output_pins(node) if kind == 'K2Node_VariableGet' else editor.L.list_input_pins(node)
    skip = {'execute', 'then', 'else', 'self', 'OutputDelegate'}
    names = [plain_name(pin.get_pin_name()) for pin in pins if plain_name(pin.get_pin_name()) not in skip]
    if len(names) == 1:
        return names[0]
    return ''


def event_member(editor, node):
    del editor
    if node.get_class().get_name() != 'K2Node_Event':
        return ''
    try:
        ref = node.get_editor_property('event_reference')
        return plain_name(ref.get_editor_property('member_name'))
    except Exception:
        return ''


def plain_name(value):
    text = str(value).strip()
    if text.startswith('Name(') and text.endswith(')'):
        text = text[5:-1].strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in '\'"':
        text = text[1:-1]
    return text


def literal_number(pin):
    if pin is None or not pin.is_valid() or list(pin.list_connected_pins()):
        return None
    text = str(pin.get_pin_value()).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def literal_int(pin):
    value = literal_number(pin)
    if value is None or abs(value - round(value)) > 1e-6:
        return None
    return int(round(value))


def literal_bool(pin):
    if pin is None or not pin.is_valid() or list(pin.list_connected_pins()):
        return None
    text = str(pin.get_pin_value()).strip().lower()
    if text in ('true', '1'):
        return True
    if text in ('false', '0'):
        return False
    if not text and str(pin.get_pin_type_display_string()).strip().lower() == 'boolean':
        # An empty default on an unlinked Boolean pin is the type default, false.
        return False
    return None


def near(value, target, tolerance=1e-3):
    return value is not None and abs(float(value) - float(target)) <= tolerance


def parse_linear_color(value):
    import re
    numbers = {channel.upper(): float(number) for channel, number in re.findall(r'([RGBA])\s*=\s*([-+0-9.]+)', str(value), re.I)}
    if not set('RGBA') <= set(numbers):
        return None
    return tuple(numbers[channel] for channel in 'RGBA')


def color_close(left, right, tolerance=0.002):
    return all(abs(a - b) <= tolerance for a, b in zip(left, right))


def clip_from_anim_pin(value):
    text = str(value)
    marker = 'A_Teddy_'
    index = text.rfind(marker)
    if index < 0:
        return ''
    rest = text[index + len(marker):]
    name = []
    for char in rest:
        if char.isalnum() or char == '_':
            name.append(char)
        else:
            break
    return ''.join(name)


def pin_endpoints(node, pin_name, direction):
    pin = node.find_input_pin(pin_name) if direction == 'in' else node.find_output_pin(pin_name)
    if not pin.is_valid():
        return None
    return sorted(
        f'{link.get_owning_node().get_name()}:{plain_name(link.get_pin_name())}'
        for link in pin.list_connected_pins()
    )


def val(graph, name):
    return (graph.get(name), name)


def play(graph, clip, looping):
    return graph.call(
        'SkeletalMeshComponent.PlayAnimation',
        self=val(graph, 'Mesh'),
        NewAnimToPlay=anim_object_path(clip),
        bLooping='true' if looping else 'false',
    )


def warning(graph, show):
    return graph.call(
        'SceneComponent.SetVisibility',
        self=val(graph, 'AttackWarning'),
        bNewVisibility='true' if show else 'false',
        bPropagateToChildren='true',
    )


def node_id(node):
    return f'{node.get_name()}:{node.get_class().get_name()}'


def _safe(fn):
    try:
        value = fn()
    except Exception as error:
        return f'<error {type(error).__name__}: {error}>'
    return value


def _ref_info(node, prop):
    """Read a member reference (function/variable/event) without trusting the API."""
    info = {}
    ref = _safe(lambda: node.get_editor_property(prop))
    if isinstance(ref, str) and ref.startswith('<error'):
        info['error'] = ref
        return info
    for key in ('member_name', 'member_parent', 'member_guid', 'self_context'):
        value = _safe(lambda key=key: ref.get_editor_property(key))
        if isinstance(value, str) and value.startswith('<error'):
            info[key] = value
            continue
        if key == 'member_parent' and value is not None and hasattr(value, 'get_path_name'):
            value = _safe(value.get_path_name)
        info[key] = plain_name(value) if key == 'member_name' else str(value)
    return info


def pin_dump(pin):
    links = _safe(lambda: [
        f'{link.get_owning_node().get_name()}:{plain_name(link.get_pin_name())}'
        for link in pin.list_connected_pins()
    ])
    return {
        'name': _safe(lambda: plain_name(pin.get_pin_name())),
        'direction': _safe(lambda: str(pin.get_pin_direction())),
        'type': _safe(lambda: str(pin.get_pin_type_display_string())),
        'default': _safe(lambda: str(pin.get_pin_value())),
        'links': links,
    }


def node_dump(editor, node, depth=1):
    """Structured, read-only description of a graph node and its pins.

    ``depth`` follows data links on input pins (not exec) so a branch dump also
    shows its condition node and that node's inputs. Never raises.
    """
    if node is None:
        return {'node': None}
    kind = _safe(lambda: node.get_class().get_name())
    dump = {
        'id': _safe(lambda: node.get_name()),
        'class': kind,
        'class_path': _safe(lambda: node.get_class().get_path_name()),
        'title': _safe(lambda: str(editor.L.get_node_title(node))),
    }
    if isinstance(kind, str) and 'CallFunction' in kind or kind in ('K2Node_PromotableOperator', 'K2Node_CommutativeAssociativeBinaryOperator'):
        dump['function'] = _ref_info(node, 'function_reference')
        dump['call_name'] = _safe(lambda: call_name(editor, node))
    if kind in ('K2Node_VariableGet', 'K2Node_VariableSet'):
        dump['variable'] = _ref_info(node, 'variable_reference')
        dump['var_name'] = _safe(lambda: var_name(editor, node))
    if kind in ('K2Node_Event',):
        dump['event'] = _ref_info(node, 'event_reference')
    inputs = _safe(lambda: list(node.list_input_pins()))
    outputs = _safe(lambda: list(node.list_output_pins()))
    dump['pins'] = []
    for group in (inputs, outputs):
        if isinstance(group, str):
            dump['pins'].append({'error': group})
            continue
        dump['pins'].extend(pin_dump(pin) for pin in group)
    if depth > 0 and not isinstance(inputs, str):
        linked = {}
        for pin in inputs:
            ptype = _safe(lambda pin=pin: str(pin.get_pin_type_display_string()))
            if isinstance(ptype, str) and 'exec' in ptype.lower():
                continue
            name = _safe(lambda pin=pin: plain_name(pin.get_pin_name()))
            if name in ('execute',):
                continue
            others = _safe(lambda pin=pin: [link.get_owning_node() for link in pin.list_connected_pins()])
            if isinstance(others, str):
                linked[str(name)] = others
                continue
            linked[str(name)] = [node_dump(editor, other, depth - 1) for other in others]
        dump['inputs_from'] = linked
    return dump


def format_checks(checks):
    parts = []
    for check in checks or []:
        seen = {key: value for key, value in check.items() if key not in ('check', 'ok')}
        parts.append(f"{check.get('check')}={'ok' if check.get('ok') else 'FAIL'} {json.dumps(seen, default=str, sort_keys=True)}")
    return '; '.join(parts)


def format_node_dump(dump, indent=0):
    """Human-readable text for a node_dump() dict (also written to the editor log)."""
    pad = '  ' * indent
    if not isinstance(dump, dict) or dump.get('node', 1) is None:
        return f'{pad}<none>'
    lines = [f"{pad}{dump.get('id')} [{dump.get('class')}] title={dump.get('title')!r}"]
    for key in ('function', 'variable', 'event'):
        if key in dump:
            lines.append(f'{pad}  {key}: {json.dumps(dump[key], default=str, sort_keys=True)}')
    for key in ('call_name', 'var_name'):
        if key in dump:
            lines.append(f'{pad}  {key}: {dump[key]!r}')
    for pin in dump.get('pins', []):
        if 'error' in pin:
            lines.append(f"{pad}  pins: {pin['error']}")
            continue
        lines.append(
            f"{pad}  pin {pin.get('direction')} {pin.get('name')!s} : {pin.get('type')} "
            f"default={pin.get('default')!r} links={pin.get('links')}"
        )
    for name, upstream in (dump.get('inputs_from') or {}).items():
        if isinstance(upstream, str):
            lines.append(f'{pad}  {name} <- {upstream}')
            continue
        for item in upstream:
            lines.append(f'{pad}  {name} <-')
            lines.append(format_node_dump(item, indent + 2))
    return '\n'.join(lines)


def describe(editor, node):
    return f'{node_id(node)} {call_name(editor, node)} {var_name(editor, node)}'


def mark_extension(editor, graph, node):
    marked = []
    error = ''
    try:
        node.set_editor_property('node_comment', CUE_EXTENSION_NOTE)
        for prop in ('comment_bubble_visible', 'b_comment_bubble_visible'):
            try:
                node.set_editor_property(prop, True)
                break
            except Exception:
                continue
        marked.append('node_comment')
    except Exception as exc:
        error = str(exc)
    try:
        x, y = 0, 0
        try:
            x = int(node.get_editor_property('node_pos_x'))
            y = int(node.get_editor_property('node_pos_y'))
        except Exception:
            x, y = 0, 0
        graph.g.add_comment_node(
            CUE_EXTENSION_NOTE,
            editor.u.Vector2D(float(x), float(y + 200)),
            editor.u.Vector2D(780.0, 180.0),
        )
        marked.append('comment_node')
    except Exception as exc:
        error = (error + ' ' + str(exc)).strip()
    return {'marked': marked, 'error': error, 'note': CUE_EXTENSION_NOTE}


if __name__ == '__main__':
    exit_code = main()
    # A successful editor run must not raise. The commandlet treats SystemExit as a failed script.
    # Outside the editor, SystemExit is the process status the tests check.
    if module_has_unreal():
        if exit_code != 0:
            raise SystemExit(exit_code)
    else:
        raise SystemExit(exit_code)
