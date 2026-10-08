"""Plain-Python checks for the GAME-016 escalation authoring script.

No Unreal, no git LFS, and no hashing of the real FBX files.

    python -m unittest tools/test_build_boss_escalation_v1.py -v
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import build_boss_escalation_v1 as escalation  # noqa: E402

SCRIPT = TOOLS / 'build_boss_escalation_v1.py'
MANIFEST = ROOT / 'Assets' / 'Adapted' / 'AnimPreprod' / 'manifest.json'

# These needles are searched for in the authoring script. They must stay
# as exact substrings here, and they must not appear in that script.
FORBIDDEN = (
    'remove_nodes(',
    'historical_builder',
    'TEDDY_ALLOW_HISTORICAL_REBUILD',
    'save_current_level',
    'save_dirty_packages',
    'duplicate_asset',
)

MANIFEST_SHA = {
    'AttackLeft': 'c5c923e8359ac82ca3f2056b71259eef0477d8230c871969c644e29565f22f99',
    'Stagger': '7fb167d8d637c0fe657c84d521ee82e617eac2ef7a9e67583face1fbd3e83755',
    'Threat': 'b7340638c4e4ded68910fac62cfe18df342134df45c3c71f92e1d2b0c3af3d76',
}
MANIFEST_FRAMES = {'AttackLeft': 36, 'Stagger': 24, 'Threat': 45}

CREATED_ASSET_KEYS = ('assets_to_save', 'imports', 'variables', 'edits', 'hud', 'steps')
BANNED_ASSET_WORDS = ('animblueprint', 'animmontage', 'blendspace', 'montage')


def _strings_under(node, skip_keys, path=()):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in skip_keys:
                continue
            yield from _strings_under(value, skip_keys, path + (key,))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _strings_under(value, skip_keys, path + (index,))
    elif isinstance(node, str):
        yield path, node


def _stitchling_paths(node, path=()):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _stitchling_paths(value, path + (str(key),))
    elif isinstance(node, list):
        for value in node:
            yield from _stitchling_paths(value, path)
    elif isinstance(node, str) and 'BP_Stitchling' in node:
        yield path


class TimingMath(unittest.TestCase):
    def test_attack_left_rate_from_imported_length(self):
        play_length = 35 / 30
        row = escalation.attack_left_play_rate(play_length)
        self.assertAlmostEqual(row['impact_time'], 19 / 30)
        self.assertAlmostEqual(row['play_rate'], (19 / 30) / 0.92)
        self.assertAlmostEqual(row['play_rate'], 0.688, places=3)
        self.assertNotAlmostEqual(row['play_rate'], 0.73, places=2)
        self.assertAlmostEqual(row['impact_time'] / row['play_rate'], 0.92)
        self.assertAlmostEqual(row['scaled_length'], 0.92 * 35 / 19)
        self.assertLess(row['scaled_length'], 1.72)
        self.assertTrue(row['fits_in_cycle'])
        self.assertAlmostEqual(row['scaled_length'], 1.695, places=3)

    def test_scaled_length_does_not_depend_on_measured_play_length(self):
        measured = escalation.attack_left_play_rate(36 / 30)
        formula = escalation.attack_left_play_rate(35 / 30)
        self.assertAlmostEqual(measured['scaled_length'], formula['scaled_length'])
        self.assertNotAlmostEqual(measured['play_rate'], formula['play_rate'])
        self.assertAlmostEqual(measured['impact_time'] / measured['play_rate'], 0.92)

    def test_attack_cut_and_phase_window(self):
        cut = escalation.attack_cut_seconds()
        self.assertAlmostEqual(cut['attack_seconds'], 53 / 30)
        self.assertAlmostEqual(cut['cycle_seconds'], 1.72)
        self.assertAlmostEqual(cut['cut_seconds'], 53 / 30 - 1.72)
        self.assertAlmostEqual(cut['cut_seconds'], 0.047, places=3)
        self.assertTrue(cut['walk_at_recovery_end'])

        change = escalation.phase_change_timing()
        self.assertEqual(change['frame_count_sum'], 69)
        self.assertEqual(change['doc_frame_count'], 69)
        self.assertTrue(change['doc_frame_count_matches'])
        self.assertAlmostEqual(change['stagger_seconds'], 23 / 30)
        self.assertAlmostEqual(change['threat_seconds'], 44 / 30)
        self.assertAlmostEqual(change['total_seconds'], 67 / 30)
        self.assertAlmostEqual(change['total_seconds'], 2.233, places=3)
        self.assertAlmostEqual(change['doc_seconds'], 2.3)
        self.assertLess(change['total_seconds'], change['doc_seconds'])

    def test_length_basis_prefers_imported_frame_1_at_zero(self):
        self.assertEqual(escalation.length_basis(23 / 30, 24), 'n_minus_1')
        self.assertEqual(escalation.length_basis(24 / 30, 24), 'n')
        self.assertEqual(escalation.length_basis(23 / 30 + 0.01, 24), 'n_minus_1')
        self.assertEqual(escalation.length_basis(23.5 / 30, 24), 'n_minus_1')
        with self.assertRaises(ValueError):
            escalation.length_basis(0.5, 24)
        with self.assertRaises(ValueError):
            escalation.length_basis(1.0, 24)

    def test_compute_timings_matches_the_plan_table(self):
        timings = escalation.compute_timings()
        self.assertAlmostEqual(timings['attack_left']['play_rate'], 0.688, places=3)
        self.assertLess(timings['attack_left']['scaled_length'], timings['phase2_cycle'])
        self.assertAlmostEqual(timings['attack_cut']['cut_seconds'], 0.047, places=3)
        self.assertEqual(timings['phase_change']['frame_count_sum'], 69)
        self.assertEqual(timings['threshold']['hits'], 13)
        self.assertEqual(timings['threshold']['hp'], 144)


class ThresholdMath(unittest.TestCase):
    def test_thirteen_hits_show_144(self):
        row = escalation.hits_to_threshold(300, 12, 150)
        self.assertEqual(row['hits'], 13)
        self.assertEqual(row['hp'], 144)
        self.assertEqual(row['hp_before'], 156)
        self.assertGreater(row['hp_before'], 150)
        self.assertEqual(escalation.hp_after_hits(300, 12, 12), 156)
        self.assertEqual(escalation.hp_after_hits(300, 12, 13), 144)

    def test_exact_and_fractional_quotients(self):
        exact = escalation.hits_to_threshold(300, 12, 156)
        self.assertEqual(exact['hits'], 12)
        self.assertEqual(exact['hp'], 156)
        fractional = escalation.hits_to_threshold(300, 12, 150)
        self.assertEqual(fractional['hits'], 13)

    def test_never_triggers_above_150_and_only_once(self):
        for hits in range(0, 13):
            hp = escalation.hp_after_hits(300, 12, hits)
            self.assertGreater(hp, 150)
            self.assertFalse(escalation.would_enter_phase(hp, False, 0))
        self.assertFalse(escalation.would_enter_phase(150.01, False, 0))
        self.assertTrue(escalation.would_enter_phase(150, False, 0))
        self.assertTrue(escalation.would_enter_phase(144, False, 0))
        for state in (0, 1, 2, 4):
            self.assertTrue(escalation.would_enter_phase(144, False, state))
        self.assertFalse(escalation.would_enter_phase(144, True, 0))
        self.assertFalse(escalation.would_enter_phase(144, False, 3))
        self.assertFalse(escalation.would_enter_phase(144, False, 5))
        self.assertFalse(escalation.would_enter_phase(0, False, 0))
        self.assertTrue(escalation.damage_ignored(5))

        sim = escalation.simulate_rifle_phase(shots=40)
        self.assertEqual(sim['triggers'], [{'shot': 13, 'hp': 144}])
        self.assertEqual(len(sim['ignored']), 4)
        self.assertTrue(all(row['hp'] == 144 for row in sim['ignored']))
        self.assertTrue(sim['b_phase2'])
        self.assertEqual(sim['state'], 3)


class PlanContent(unittest.TestCase):
    def setUp(self):
        self.plan = escalation.build_plan()

    def test_steps_skip_only_the_cue(self):
        by_step = {step['step']: step for step in self.plan['steps']}
        self.assertEqual(set(by_step), set(range(1, 11)))
        for number in (1, 2, 3, 4, 5, 6, 7, 8, 10):
            self.assertNotEqual(by_step[number]['status'], 'skipped', number)
        self.assertEqual(by_step[9]['status'], 'skipped')
        self.assertIn('play rate', by_step[6]['title'].lower())
        self.assertEqual(by_step[6]['choice'], 'play_rate')
        self.assertIn('0.73', by_step[6]['detail'])
        self.assertIn('Do not hard-code 0.73', by_step[6]['detail'])
        self.assertEqual(by_step[7]['blend'], 'cut_to_walk')
        self.assertNotIn('BP_Stitchling', by_step[10]['detail'])

    def test_stitchling_only_under_not_touched(self):
        paths = list(_stitchling_paths(self.plan))
        self.assertGreaterEqual(len(paths), 2)
        for path in paths:
            self.assertEqual(path[0], 'not_touched', path)
        names = self.plan['not_touched']['names']
        hashes = self.plan['not_touched']['byte_hash_paths']
        self.assertIn('BP_Stitchling', names)
        self.assertTrue(any('BP_Stitchling' in item for item in hashes))

    def test_locks_and_no_new_anim_types(self):
        locks = self.plan['locks']['required_before_apply']
        self.assertEqual(list(locks), list(escalation.REQUIRED_LOCKS))
        self.assertIn('BP_TeddyBoss.uasset', locks[0])
        self.assertIn('BP_EncounterHUD.uasset', locks[1])
        after = self.plan['locks']['after_import_before_commit']
        self.assertEqual(len(after), 3)
        for clip in ('Stagger', 'Threat', 'AttackLeft'):
            self.assertTrue(any(f'A_Teddy_{clip}.uasset' in path for path in after))
        created = self.plan['explicitly_not_created']
        self.assertIn('AnimBlueprint', created)
        self.assertIn('AnimMontage', created)
        self.assertIn('BlendSpace', created)
        for path, text in _strings_under(self.plan, skip_keys={'explicitly_not_created', 'single_node', 'open_items'}):
            lowered = text.lower()
            for word in BANNED_ASSET_WORDS:
                self.assertNotIn(word, lowered, path)

    def test_edits_variables_and_phase1_defaults(self):
        ids = [item['id'] for item in self.plan['edits']]
        for edit_id in (
            'damage_ignore', 'phase_entry', 'state5_tick',
            'recovery_switch', 'anticipation_clips', 'attack_left_rate',
        ):
            self.assertIn(edit_id, ids)
        joined = json.dumps(self.plan['edits'])
        self.assertIn('SelectFloat', joined)
        self.assertIn('SetPlayRate', joined)
        self.assertIn('Stagger', joined)
        hud = json.dumps(self.plan['hud'])
        self.assertIn('SelectColor', hud)
        defaults = {item['name']: item['default'] for item in self.plan['variables']}
        self.assertEqual(defaults['bPhase2'], 'false')
        self.assertEqual(defaults['bNextAttackLeft'], 'true')
        self.assertEqual(defaults['bThreatStarted'], 'false')
        self.assertEqual(defaults['PhaseChangeHealth'], '150')
        self.assertEqual(defaults['Phase1Recovery'], '1.15')
        self.assertEqual(defaults['Phase2Recovery'], '0.8')
        self.assertEqual(defaults['PhaseFlashUntil'], '0')
        self.assertAlmostEqual(float(defaults['StaggerSeconds']), 23 / 30)
        self.assertAlmostEqual(float(defaults['ThreatSeconds']), 44 / 30)
        self.assertAlmostEqual(float(defaults['AttackLeftPlayRate']), (19 / 30) / 0.92)
        self.assertNotEqual(defaults['AttackLeftPlayRate'], '0.73')
        self.assertNotEqual(defaults['AttackLeftPlayRate'], '0.688')
        self.assertTrue(all(item['phase1_safe'] for item in self.plan['variables']))
        self.assertEqual(self.plan['tag'], {
            'key': 'TeddyEncounter.Game016',
            'value': 'escalation-v1',
        })

    def test_human_plan_is_console_safe(self):
        text = escalation.format_plan(self.plan)
        text.encode('cp1252')
        self.assertIn('AttackLeft', text)
        self.assertIn('BP_TeddyBoss.uasset', text)
        self.assertIn('[skipped]', text)


class ModeResolution(unittest.TestCase):
    def test_outside_editor_refuses_without_plan(self):
        mode = escalation.resolve_mode(False, [], {})
        self.assertEqual(mode.action, 'refuse')
        self.assertEqual(mode.exit_code, 2)
        mode = escalation.resolve_mode(False, [], {'TEDDY_GAME016_APPLY': '1'})
        self.assertEqual(mode.action, 'refuse')
        self.assertEqual(mode.exit_code, 2)

    def test_plan_outside_and_inside(self):
        mode = escalation.resolve_mode(False, ['--plan'], {})
        self.assertEqual(mode.action, 'plan')
        self.assertEqual(mode.exit_code, 0)
        self.assertFalse(mode.json_out)
        mode = escalation.resolve_mode(False, ['--plan', '--json'], {'TEDDY_GAME016_APPLY': '1'})
        self.assertEqual(mode.action, 'plan')
        self.assertTrue(mode.json_out)
        mode = escalation.resolve_mode(True, ['--plan'], {'TEDDY_GAME016_APPLY': '1'})
        self.assertEqual(mode.action, 'plan')
        self.assertNotEqual(mode.action, 'apply')

    def test_editor_defaults_to_inspect_until_apply_is_exactly_one(self):
        self.assertEqual(escalation.resolve_mode(True, [], {}).action, 'inspect')
        self.assertEqual(
            escalation.resolve_mode(True, ['tools/build_boss_escalation_v1.py'], {}).action,
            'inspect',
        )
        self.assertEqual(
            escalation.resolve_mode(True, [], {'TEDDY_GAME016_APPLY': '1'}).action,
            'apply',
        )
        for value in ('0', 'true', '1 ', 'yes'):
            mode = escalation.resolve_mode(True, [], {'TEDDY_GAME016_APPLY': value})
            self.assertEqual(mode.action, 'inspect', value)

    def test_unknown_args_and_full_argv(self):
        mode = escalation.resolve_mode(True, ['--apply'], {'TEDDY_GAME016_APPLY': '1'})
        self.assertEqual(mode.action, 'refuse')
        self.assertEqual(mode.exit_code, 2)
        mode = escalation.resolve_mode(False, ['--json'], {})
        self.assertEqual(mode.action, 'refuse')
        mode = escalation.resolve_mode(
            False,
            ['python.exe', 'tools/build_boss_escalation_v1.py', '--plan'],
            {},
        )
        self.assertEqual(mode.action, 'plan')
        self.assertEqual(mode.exit_code, 0)
        mode = escalation.resolve_mode(
            True,
            [r'C:\Projects\tools\build_boss_escalation_v1.py'],
            {'TEDDY_GAME016_APPLY': '1'},
        )
        self.assertEqual(mode.action, 'apply')

    def test_editor_script_argv_is_inspect_unless_apply_is_set(self):
        # Unreal's pythonscript commandlet sets sys.argv to the script path and
        # passes no further arguments for `editor-script tools/build_boss_escalation_v1.py`.
        script = r'C:\Projects\to-deploy\worktrees\game-016\tools\build_boss_escalation_v1.py'
        inspect = escalation.resolve_mode(True, [script], {})
        self.assertEqual(inspect.action, 'inspect')
        self.assertEqual(inspect.exit_code, 0)
        apply = escalation.resolve_mode(True, [script], {'TEDDY_GAME016_APPLY': '1'})
        self.assertEqual(apply.action, 'apply')
        quoted = escalation.resolve_mode(True, ['"' + script + '"'], {})
        self.assertEqual(quoted.action, 'inspect')

    def test_loaded_unreal_module_counts_as_the_editor(self):
        sentinel = types.ModuleType('unreal')
        previous = sys.modules.get('unreal')
        sys.modules['unreal'] = sentinel
        try:
            self.assertTrue(escalation.module_has_unreal())
        finally:
            if previous is None:
                sys.modules.pop('unreal', None)
            else:
                sys.modules['unreal'] = previous


class LockParsing(unittest.TestCase):
    def _ours(self, extra_theirs=None):
        return json.dumps({
            'ours': [{'path': path} for path in escalation.REQUIRED_LOCKS],
            'theirs': extra_theirs or [],
        })

    def test_ours_accepts_normalized_paths(self):
        parsed = escalation.parse_lock_verify(self._ours([
            {'path': 'TeddyBlueprint/Content/Some/Other.uasset'},
        ]))
        self.assertTrue(parsed['ok'])
        windows = json.dumps({
            'ours': [
                {'path': escalation.REQUIRED_LOCKS[0].replace('/', '\\')},
                {'path': './' + escalation.REQUIRED_LOCKS[1]},
            ],
            'theirs': [],
        })
        parsed = escalation.parse_lock_verify(windows)
        self.assertEqual(parsed['required'], list(escalation.REQUIRED_LOCKS))

    def test_theirs_missing_and_malformed_fail_closed(self):
        theirs = json.dumps({
            'ours': [{'path': escalation.REQUIRED_LOCKS[0]}],
            'theirs': [{'path': escalation.REQUIRED_LOCKS[1]}],
        })
        with self.assertRaises(escalation.LockCheckError) as caught:
            escalation.parse_lock_verify(theirs)
        self.assertEqual(caught.exception.reason, 'not_ours')

        missing = json.dumps({
            'ours': [{'path': escalation.REQUIRED_LOCKS[0]}],
            'theirs': [],
        })
        with self.assertRaises(escalation.LockCheckError) as caught:
            escalation.parse_lock_verify(missing)
        self.assertEqual(caught.exception.reason, 'not_ours')

        for text in ('', 'not-json', '{}', '{"ours": [], "theirs": "no"}', '{"ours": [{}], "theirs": []}'):
            with self.assertRaises(escalation.LockCheckError) as caught:
                escalation.parse_lock_verify(text)
            self.assertEqual(caught.exception.reason, 'malformed', text)

    def test_git_errors_fail_before_parsing_a_good_body(self):
        good = self._ours()
        with self.assertRaises(escalation.LockCheckError) as caught:
            escalation.interpret_lock_command(1, good, 'lfs down')
        self.assertEqual(caught.exception.reason, 'git_failed')
        with self.assertRaises(escalation.LockCheckError) as caught:
            escalation.interpret_lock_command(0, '', '')
        self.assertEqual(caught.exception.reason, 'malformed')
        self.assertTrue(escalation.interpret_lock_command(0, good)['ok'])

    def test_existing_anim_files_join_the_required_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(escalation.locks_required_for_apply(root), escalation.REQUIRED_LOCKS)
            rel = escalation.NEW_ANIM_LOCKS[0]
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_bytes(b'present')
            required = escalation.locks_required_for_apply(root)
            self.assertEqual(required[0], escalation.REQUIRED_LOCKS[0])
            self.assertEqual(required[1], escalation.REQUIRED_LOCKS[1])
            self.assertIn(rel, required)
            self.assertEqual(len(required), 3)


class ManifestCheck(unittest.TestCase):
    def test_real_manifest_entries(self):
        manifest = escalation.read_manifest(MANIFEST)
        found = escalation.require_manifest_contract(manifest)
        self.assertEqual(set(found), set(MANIFEST_FRAMES))
        for name, frames in MANIFEST_FRAMES.items():
            entry = escalation.manifest_clip(manifest, name)
            self.assertEqual(int(entry['frames']), frames)
            self.assertEqual(int(entry['fps']), 30)
            self.assertEqual(entry['file'], f'Teddy_{name}.fbx')
            self.assertEqual(str(entry['sha256']).lower(), MANIFEST_SHA[name])

    def test_temp_file_mismatch_and_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrong = root / 'wrong.fbx'
            wrong.write_bytes(b'not-the-shipped-clip')
            with self.assertRaises(escalation.Sha256Mismatch) as caught:
                escalation.verify_clip_file(MANIFEST, 'AttackLeft', wrong)
            self.assertEqual(caught.exception.expected, MANIFEST_SHA['AttackLeft'])
            self.assertNotEqual(caught.exception.actual, MANIFEST_SHA['AttackLeft'])

            payload = b'phase-two-clip-bytes'
            digest = hashlib.sha256(payload).hexdigest()
            good = root / 'Teddy_Stagger.fbx'
            good.write_bytes(payload)
            fake_manifest = root / 'manifest.json'
            fake_manifest.write_text(json.dumps({
                'new_clips': [{
                    'name': 'Stagger',
                    'file': 'Teddy_Stagger.fbx',
                    'sha256': digest,
                    'frames': 24,
                    'fps': 30,
                }],
            }), encoding='utf-8')
            checked = escalation.verify_clip_file(fake_manifest, 'Stagger', good)
            self.assertEqual(checked['sha256'], digest)
            self.assertEqual(checked['frames'], 24)


class SavedStateAndReceipt(unittest.TestCase):
    def test_classify_saved_state(self):
        self.assertEqual(escalation.classify_saved_state('escalation-v1', []), 'already_applied')
        self.assertEqual(
            escalation.classify_saved_state('  escalation-v1  ', ['bPhase2']),
            'already_applied',
        )
        self.assertEqual(escalation.classify_saved_state('', ['Health', 'State']), 'ready')
        self.assertEqual(escalation.classify_saved_state(None, []), 'ready')
        self.assertEqual(escalation.classify_saved_state('', ['bPhase2']), 'partial')
        self.assertEqual(escalation.classify_saved_state('', ['ThreatSeconds']), 'partial')
        self.assertEqual(escalation.classify_saved_state('other', []), 'partial')

    def test_receipt_directory_name(self):
        when = datetime(2026, 10, 8, 15, 4, 5, tzinfo=timezone.utc)
        self.assertEqual(
            escalation.receipt_directory_name('inspect', when),
            '20261008T150405Z-inspect',
        )
        shifted = datetime(2026, 10, 8, 11, 4, 5, tzinfo=timezone(timedelta(hours=-4)))
        self.assertEqual(
            escalation.receipt_directory_name('apply', shifted),
            '20261008T150405Z-apply',
        )
        with self.assertRaises(ValueError):
            escalation.receipt_directory_name('inspect', datetime(2026, 10, 8, 15, 4, 5))
        with self.assertRaises(ValueError):
            escalation.receipt_directory_name('mutate', when)


class SourceGuards(unittest.TestCase):
    def test_forbidden_calls_are_absent(self):
        source = SCRIPT.read_text(encoding='utf-8')
        for token in FORBIDDEN:
            self.assertNotIn(token, source)

    def test_stitchling_name_stays_in_the_two_lists(self):
        source = SCRIPT.read_text(encoding='utf-8')
        tree = ast.parse(source)
        spans = []
        for node in tree.body:
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id in ('NOT_TOUCHED_NAMES', 'UNCHANGED_HASH_PATHS'):
                    spans.append((node.lineno, node.end_lineno))
        self.assertEqual(len(spans), 2)
        hits = [index for index, line in enumerate(source.splitlines(), 1) if 'BP_Stitchling' in line]
        self.assertGreaterEqual(len(hits), 2)
        for lineno in hits:
            self.assertTrue(any(start <= lineno <= end for start, end in spans), lineno)

    def test_unreal_import_is_not_at_module_level(self):
        tree = ast.parse(SCRIPT.read_text(encoding='utf-8'))

        class Visitor(ast.NodeVisitor):
            def __init__(self):
                self.function_depth = 0
                self.bad = []

            def visit_FunctionDef(self, node):
                self.function_depth += 1
                self.generic_visit(node)
                self.function_depth -= 1

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_Import(self, node):
                if self.function_depth == 0:
                    for alias in node.names:
                        root = alias.name.split('.')[0]
                        if root in ('unreal', 'encounter_authoring'):
                            self.bad.append(alias.name)
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                if self.function_depth == 0:
                    root = (node.module or '').split('.')[0]
                    if root in ('unreal', 'encounter_authoring'):
                        self.bad.append(node.module)
                self.generic_visit(node)

        visitor = Visitor()
        visitor.visit(tree)
        self.assertEqual(visitor.bad, [])


class SubprocessPlan(unittest.TestCase):
    def _run(self, *args):
        env = os.environ.copy()
        env.pop('TEDDY_GAME016_APPLY', None)
        env['PYTHONIOENCODING'] = 'utf-8'
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding='utf-8',
            env=env,
            check=False,
        )

    def test_plan_exits_zero_and_json_parses(self):
        evidence = ROOT / 'evidence' / 'game-016'
        before = set(evidence.rglob('*')) if evidence.exists() else set()
        human = self._run('--plan')
        self.assertEqual(human.returncode, 0, human.stderr)
        self.assertIn('AttackLeft', human.stdout)
        self.assertIn('BP_TeddyBoss.uasset', human.stdout)
        self.assertIn('BP_EncounterHUD.uasset', human.stdout)
        human.stdout.encode('cp1252')

        parsed = self._run('--plan', '--json')
        self.assertEqual(parsed.returncode, 0, parsed.stderr)
        plan = json.loads(parsed.stdout)
        skipped = [step for step in plan['steps'] if step['step'] == 9]
        self.assertEqual(skipped[0]['status'], 'skipped')
        self.assertIn('AttackLeft', json.dumps(plan['imports']))
        after = set(evidence.rglob('*')) if evidence.exists() else set()
        self.assertEqual(before, after)

    def test_no_args_refuses_when_unreal_is_absent(self):
        if escalation.module_has_unreal():
            self.skipTest('this interpreter can see unreal; a no-arg run would try to inspect')
        refused = self._run()
        self.assertEqual(refused.returncode, 2, refused.stdout)
        self.assertIn('Refusing', refused.stderr)


if __name__ == '__main__':
    unittest.main()


# ---------------------------------------------------------------------------
# Fake graph objects for the anchor dump and compare checks (no Unreal).


class _FakeClass:
    def __init__(self, name):
        self._name = name

    def get_name(self):
        return self._name

    def get_path_name(self):
        return f'/Script/BlueprintGraph.{self._name}'


class _FakeRef:
    def __init__(self, **props):
        self._props = props

    def get_editor_property(self, name):
        if name not in self._props:
            raise AttributeError(f'no property {name}')
        return self._props[name]


class _FakePin:
    def __init__(self, name, direction, ptype, value='', valid=True, raise_value=False):
        self.name = name
        self.direction = direction
        self.ptype = ptype
        self.value = value
        self.valid = valid
        self.raise_value = raise_value
        self.links = []
        self.owner = None

    def is_valid(self):
        return self.valid

    def get_pin_name(self):
        return self.name

    def get_pin_direction(self):
        return self.direction

    def get_pin_type_display_string(self):
        return self.ptype

    def get_pin_value(self):
        if self.raise_value:
            raise RuntimeError('pin value unreadable')
        return self.value

    def list_connected_pins(self):
        return list(self.links)

    def get_owning_node(self):
        return self.owner


_MISSING = _FakePin('missing', 'EGPD_Input', '', valid=False)


class _FakeNode:
    def __init__(self, name, cls, inputs=(), outputs=(), props=None, title=''):
        self.name = name
        self.cls = _FakeClass(cls)
        self.inputs = list(inputs)
        self.outputs = list(outputs)
        self.props = props or {}
        self.title = title
        for pin in self.inputs + self.outputs:
            pin.owner = self

    def get_name(self):
        return self.name

    def get_class(self):
        return self.cls

    def get_editor_property(self, name):
        if name not in self.props:
            raise AttributeError(f'no property {name}')
        return self.props[name]

    def list_input_pins(self):
        return list(self.inputs)

    def list_output_pins(self):
        return list(self.outputs)

    def find_input_pin(self, name):
        return next((pin for pin in self.inputs if pin.name == name), _MISSING)

    def find_output_pin(self, name):
        return next((pin for pin in self.outputs if pin.name == name), _MISSING)


def _link(out_pin, in_pin):
    out_pin.links.append(in_pin)
    in_pin.links.append(out_pin)


class _FakeLibrary:
    @staticmethod
    def get_node_title(node):
        return node.title

    @staticmethod
    def list_output_pins(node):
        return node.list_output_pins()

    @staticmethod
    def list_input_pins(node):
        return node.list_input_pins()


class _FakeEditor:
    L = _FakeLibrary()


def _compare_branch(function='Greater_DoubleDouble', variable='Health', b_value='0.0',
                    function_readable=True, b_raises=False, cls='K2Node_CallFunction', title='>',
                    b_type='real', result_type='boolean'):
    """Branch(Condition <- function(A <- Get variable, B literal))."""
    getter_out = _FakePin(variable, 'EGPD_Output', 'real')
    getter_props = {}
    if variable:
        getter_props['variable_reference'] = _FakeRef(member_name=variable, member_parent=None)
    getter = _FakeNode('K2Node_VariableGet_3', 'K2Node_VariableGet', outputs=[getter_out],
                       props=getter_props, title=f'Get {variable}')
    pin_a = _FakePin('A', 'EGPD_Input', 'real')
    pin_b = _FakePin('B', 'EGPD_Input', b_type, b_value, raise_value=b_raises)
    result = _FakePin('ReturnValue', 'EGPD_Output', result_type)
    compare_props = {}
    if function_readable:
        compare_props['function_reference'] = _FakeRef(member_name=function, member_parent='/Script/Engine.KismetMathLibrary')
    compare = _FakeNode(f'{cls}_7', cls, inputs=[pin_a, pin_b],
                        outputs=[result], props=compare_props, title=title)
    _link(getter_out, pin_a)
    execute = _FakePin('execute', 'EGPD_Input', 'exec')
    condition = _FakePin('Condition', 'EGPD_Input', 'boolean', 'true')
    branch = _FakeNode('K2Node_IfThenElse_10', 'K2Node_IfThenElse',
                       inputs=[execute, condition],
                       outputs=[_FakePin('then', 'EGPD_Output', 'exec'), _FakePin('else', 'EGPD_Output', 'exec')],
                       title='Branch')
    _link(result, condition)
    return branch


def _failed(checks):
    return [check['check'] for check in checks if not check['ok']]


class AnchorDump(unittest.TestCase):
    def setUp(self):
        self.editor = _FakeEditor()

    def test_compare_passes_for_equivalent_literals(self):
        for literal in ('0', '0.0', '0.000000', ' 0.0 '):
            ok, checks = escalation.compare_checks(self.editor, _compare_branch(b_value=literal), 'Health', '>', 0)
            self.assertTrue(ok, (literal, checks))
            self.assertEqual(_failed(checks), [])

    def test_compare_names_the_failed_check(self):
        cases = [
            (dict(function='Less_DoubleDouble'), 'function'),
            (dict(variable='Shield'), 'A variable'),
            (dict(b_value='0.5'), 'B literal'),
            (dict(b_value='', b_type='boolean'), 'B literal'),
            (dict(b_value='zero'), 'B literal'),
            (dict(b_raises=True), 'B literal'),
        ]
        for kwargs, expected in cases:
            ok, checks = escalation.compare_checks(self.editor, _compare_branch(**kwargs), 'Health', '>', 0)
            self.assertFalse(ok, kwargs)
            self.assertEqual(_failed(checks), [expected], (kwargs, checks))

    def test_compare_never_accepts_a_different_operator(self):
        for function in ('GreaterEqual_DoubleDouble', 'LessEqual_DoubleDouble', 'NotEqual_DoubleDouble',
                         'EqualEqual_DoubleDouble', 'Less_DoubleDouble'):
            ok, checks = escalation.compare_checks(self.editor, _compare_branch(function=function), 'Health', '>', 0)
            self.assertFalse(ok, function)
            self.assertEqual(_failed(checks), ['function'])

    def test_non_branch_and_missing_condition_fail_closed(self):
        node = _FakeNode('K2Node_VariableSet_1', 'K2Node_VariableSet')
        ok, checks = escalation.compare_checks(self.editor, node, 'Health', '>', 0)
        self.assertFalse(ok)
        self.assertEqual(_failed(checks), ['branch'])
        lonely = _FakeNode('K2Node_IfThenElse_2', 'K2Node_IfThenElse',
                           inputs=[_FakePin('Condition', 'EGPD_Input', 'boolean', 'true')])
        ok, checks = escalation.compare_checks(self.editor, lonely, 'Health', '>', 0)
        self.assertFalse(ok)
        self.assertEqual(_failed(checks), ['condition'])

    def test_require_compare_raises_with_dump_and_checks(self):
        branch = _compare_branch(b_value='1.5')
        with self.assertRaises(escalation.AnchorError) as caught:
            escalation.require_compare(self.editor, 'ReceiveAnyDamage.then', branch, 'Health', '>', 0)
        error = caught.exception
        self.assertIn('failed check: B literal', str(error))
        self.assertIn("default='1.5'", str(error))
        receipt = error.as_receipt()
        json.dumps(receipt)  # serialisable as-is
        self.assertEqual(receipt['anchor'], 'ReceiveAnyDamage.then')
        self.assertEqual(_failed(receipt['checks']), ['B literal'])
        b_check = receipt['checks'][-1]
        self.assertEqual((b_check['raw'], b_check['parsed'], b_check['expected']), ('1.5', 1.5, 0))

    def test_node_dump_lists_pins_links_and_upstream(self):
        dump = escalation.node_dump(self.editor, _compare_branch(), depth=2)
        self.assertEqual(dump['id'], 'K2Node_IfThenElse_10')
        self.assertEqual(dump['class'], 'K2Node_IfThenElse')
        self.assertEqual(dump['title'], 'Branch')
        names = [(pin['name'], pin['direction'], pin['type']) for pin in dump['pins']]
        self.assertIn(('Condition', 'EGPD_Input', 'boolean'), names)
        condition = next(pin for pin in dump['pins'] if pin['name'] == 'Condition')
        self.assertEqual(condition['links'], ['K2Node_CallFunction_7:ReturnValue'])
        self.assertNotIn('execute', dump['inputs_from'])
        (compare,) = dump['inputs_from']['Condition']
        self.assertEqual(compare['function']['member_name'], 'Greater_DoubleDouble')
        self.assertEqual(compare['function']['member_parent'], '/Script/Engine.KismetMathLibrary')
        self.assertEqual(compare['call_name'], 'Greater_DoubleDouble')
        b_pin = next(pin for pin in compare['pins'] if pin['name'] == 'B')
        self.assertEqual(b_pin['default'], '0.0')
        (getter,) = compare['inputs_from']['A']
        self.assertEqual(getter['var_name'], 'Health')
        self.assertEqual(getter['variable']['member_name'], 'Health')
        text = escalation.format_node_dump(dump)
        for needle in ('K2Node_IfThenElse_10 [K2Node_IfThenElse]', 'Condition <-', 'Greater_DoubleDouble',
                       "var_name: 'Health'", "pin EGPD_Input B : real default='0.0'"):
            self.assertIn(needle, text)

    def test_node_dump_survives_unreadable_api(self):
        branch = _compare_branch(function_readable=False, b_raises=True)
        dump = escalation.node_dump(self.editor, branch, depth=2)
        (compare,) = dump['inputs_from']['Condition']
        self.assertIn('error', compare['function'])
        self.assertEqual(compare['call_name'], '')
        b_pin = next(pin for pin in compare['pins'] if pin['name'] == 'B')
        self.assertTrue(b_pin['default'].startswith('<error RuntimeError'))
        json.dumps(dump)
        escalation.format_node_dump(dump)
        self.assertEqual(escalation.node_dump(self.editor, None), {'node': None})

    def test_unreadable_function_name_uses_the_title_operator(self):
        ok, checks = escalation.compare_checks(self.editor, _compare_branch(function_readable=False), 'Health', '>', 0)
        self.assertTrue(ok, checks)
        function = next(check for check in checks if check['check'] == 'function')
        self.assertEqual((function['via'], function['operator']), ('title', '>'))
        ok, checks = escalation.compare_checks(
            self.editor, _compare_branch(function_readable=False, b_value='0.32'), 'Health', '>', 0)
        self.assertFalse(ok)
        self.assertEqual(_failed(checks), ['B literal'])

    def test_saved_promotable_operator_with_empty_default_matches(self):
        # The real saved shape on 5.8 (inspect 20261008T193333Z): K2Node_PromotableOperator
        # 'float > float', function_reference unreadable, B pin default ''.
        branch = _compare_branch(cls='K2Node_PromotableOperator', title='float > float',
                                 function_readable=False, b_value='', b_type='Float (double-precision)')
        ok, checks = escalation.compare_checks(self.editor, branch, 'Health', '>', 0)
        self.assertTrue(ok, checks)
        b_check = checks[-1]
        self.assertEqual((b_check['raw'], b_check['parsed']), ('', 0.0))
        self.assertIn('empty', b_check['read_as'])
        state = _compare_branch(cls='K2Node_PromotableOperator', title='integer == integer', variable='State',
                                function_readable=False, b_value='', b_type='Integer')
        self.assertTrue(escalation.compare_checks(self.editor, state, 'State', '==', 0)[0])
        self.assertFalse(escalation.compare_checks(self.editor, state, 'State', '==', 1)[0])
        # The saved integer equality node is titled 'Equal (Integer)', not 'integer == integer'.
        equal = _compare_branch(cls='K2Node_PromotableOperator', title='Equal (Integer)', variable='State',
                                function_readable=False, b_value='', b_type='Integer')
        ok, checks = escalation.compare_checks(self.editor, equal, 'State', '==', 0)
        self.assertTrue(ok, checks)
        self.assertEqual(checks[2]['operator'], '==')
        not_equal = _compare_branch(cls='K2Node_PromotableOperator', title='Not Equal (Integer)', variable='State',
                                    function_readable=False, b_value='', b_type='Integer')
        self.assertEqual(_failed(escalation.compare_checks(self.editor, not_equal, 'State', '==', 0)[1]), ['function'])

    def test_promotable_operator_never_matches_a_different_condition(self):
        for title, op in (('float >= float', '>'), ('float < float', '>'), ('float > float', '>='),
                          ('float != float', '=='), ('float > float', '<='), ('Branch', '>'),
                          ('float > float > float', '>'), ('', '>'), ('float>float', '>')):
            branch = _compare_branch(cls='K2Node_PromotableOperator', title=title, function_readable=False,
                                     b_value='', b_type='Float (double-precision)')
            ok, checks = escalation.compare_checks(self.editor, branch, 'Health', op, 0)
            self.assertFalse(ok, (title, op))
            self.assertEqual(_failed(checks), ['function'], (title, op))
        not_bool = _compare_branch(cls='K2Node_PromotableOperator', title='float > float', function_readable=False,
                                   result_type='Float (double-precision)')
        self.assertEqual(_failed(escalation.compare_checks(self.editor, not_bool, 'Health', '>', 0)[1]), ['function'])
        macro = _compare_branch(cls='K2Node_MacroInstance', title='float > float', function_readable=False)
        self.assertEqual(_failed(escalation.compare_checks(self.editor, macro, 'Health', '>', 0)[1]), ['function'])
        # A readable name always wins over the title.
        named = _compare_branch(cls='K2Node_CallFunction', title='float > float', function='Less_DoubleDouble')
        self.assertEqual(_failed(escalation.compare_checks(self.editor, named, 'Health', '>', 0)[1]), ['function'])

    def test_title_operator(self):
        self.assertEqual(escalation.title_operator('float > float'), '>')
        self.assertEqual(escalation.title_operator('>='), '>=')
        self.assertEqual(escalation.title_operator('integer == integer'), '==')
        self.assertEqual(escalation.title_operator('Equal (Integer)'), '==')
        self.assertEqual(escalation.title_operator('Equal (Float)'), '==')
        self.assertEqual(escalation.title_operator('Not Equal (Integer)'), '!=')
        self.assertEqual(escalation.title_operator('Not Equal (Float)'), '!=')
        self.assertEqual(escalation.title_operator('integer > integer'), '>')
        for title in ('', 'Branch', 'float > float > float', 'a b > c', '>float', None):
            self.assertEqual(escalation.title_operator(title), '', title)

    def test_numeric_literal_and_set_literal(self):
        empty_real = _FakePin('B', 'EGPD_Input', 'Float (double-precision)', '')
        self.assertEqual(escalation.numeric_literal(empty_real)[1], 0.0)
        self.assertIsNone(escalation.numeric_literal(_FakePin('B', 'EGPD_Input', 'Boolean', ''))[1])
        self.assertIsNone(escalation.numeric_literal(_FakePin('B', 'EGPD_Input', 'Float', 'x'))[1])
        linked = _FakePin('B', 'EGPD_Input', 'Float', '0')
        _link(_FakePin('ReturnValue', 'EGPD_Output', 'Float'), linked)
        self.assertIsNone(escalation.numeric_literal(linked)[1])
        self.assertIsNone(escalation.numeric_literal(_MISSING)[1])
        for value, expected, accept in (('', 0, True), ('0.000000', 0, True), ('', 1, False), ('3', 3, True),
                                        ('3.5', 3, False)):
            pin = _FakePin('StateAge', 'EGPD_Input', 'Float (double-precision)', value)
            setter = _FakeNode('K2Node_VariableSet_4', 'K2Node_VariableSet', inputs=[
                _FakePin('execute', 'EGPD_Input', 'exec'), pin],
                outputs=[_FakePin('then', 'EGPD_Output', 'exec')],
                props={'variable_reference': _FakeRef(member_name='StateAge')})
            self.assertEqual(escalation.is_set_literal(self.editor, setter, 'StateAge', expected), accept,
                             (value, expected))

    def test_literal_bool_empty_default_is_false_only_on_boolean_pins(self):
        self.assertIs(escalation.literal_bool(_FakePin('bLooping', 'EGPD_Input', 'Boolean', '')), False)
        self.assertIs(escalation.literal_bool(_FakePin('bLooping', 'EGPD_Input', 'Boolean', 'true')), True)
        self.assertIs(escalation.literal_bool(_FakePin('bLooping', 'EGPD_Input', 'Boolean', 'False')), False)
        self.assertIsNone(escalation.literal_bool(_FakePin('Rate', 'EGPD_Input', 'Float', '')))
        self.assertIsNone(escalation.literal_bool(_FakePin('bLooping', 'EGPD_Input', 'Boolean', 'maybe')))
        linked = _FakePin('bLooping', 'EGPD_Input', 'Boolean', '')
        _link(_FakePin('ReturnValue', 'EGPD_Output', 'Boolean'), linked)
        self.assertIsNone(escalation.literal_bool(linked))

    def test_stage_writes_the_editor_log_not_only_stdout(self):
        payload = {}
        seen = []
        escalation.stage(payload, 'refresh boss after variables (compile, no save)', log=seen.append)
        self.assertEqual(seen, ['GAME-016 stage: refresh boss after variables (compile, no save)'])
        self.assertIn('unreal.log_warning(line)', SCRIPT.read_text(encoding='utf-8'))

    def test_stage_breadcrumbs_cover_every_native_apply_step(self):
        payload = {}
        escalation.stage(payload, 'import clips')
        self.assertEqual(payload['stages'], ['import clips'])
        source = SCRIPT.read_text(encoding='utf-8')
        for name in ('anchors', 'locks', 'import clips', 'add variables',
                     'refresh boss after variables (compile, no save)', 're-find anchors',
                     'mutate boss: damage ignore',
                     'mutate boss: phase entry', 'mutate boss: state 5 tick', 'mutate boss: recovery select',
                     'mutate boss: anticipation clips', 'compile boss (in memory)', 'mutate hud',
                     'compile hud (in memory)', 'tag and save', 'saved'):
            self.assertIn(f"stage(payload, '{name}')", source)

    def test_apply_refreshes_and_refinds_anchors_before_spawning_nodes(self):
        source = SCRIPT.read_text(encoding='utf-8')
        body = source[source.index('def run_apply('):source.index('def compile_clean(')]
        order = [body.index(marker) for marker in (
            "stage(payload, 'add variables')",
            "stage(payload, 'refresh boss after variables (compile, no save)')",
            'compile_clean(editor, boss)',
            "stage(payload, 're-find anchors')",
            'reconfirm_anchors(anchors, find_boss_anchors(',
            'mutate_boss(editor, boss_graph, anchors',
            'editor.save(hud)',
        )]
        self.assertEqual(order, sorted(order))
        # Nothing is saved between the variable adds and the final save block.
        between = body[order[0]:order[-1]]
        self.assertNotIn('editor.save(boss)', between)
        self.assertNotIn('save(', between.replace('(compile, no save)', ''))

    def test_reconfirm_anchors_requires_identical_nodes(self):
        a = _FakeNode('K2Node_IfThenElse_10', 'K2Node_IfThenElse')
        b = _FakeNode('K2Node_CallFunction_13', 'K2Node_CallFunction')
        same = {'damage_health': _FakeNode('K2Node_IfThenElse_10', 'K2Node_IfThenElse'),
                'attack_play': _FakeNode('K2Node_CallFunction_13', 'K2Node_CallFunction')}
        self.assertIs(escalation.reconfirm_anchors({'damage_health': a, 'attack_play': b}, same), same)
        moved = {'damage_health': a, 'attack_play': _FakeNode('K2Node_CallFunction_99', 'K2Node_CallFunction')}
        with self.assertRaises(escalation.AnchorError) as caught:
            escalation.reconfirm_anchors({'damage_health': a, 'attack_play': b}, moved)
        self.assertIn('K2Node_CallFunction_99', str(caught.exception))
        with self.assertRaises(escalation.AnchorError):
            escalation.reconfirm_anchors({'damage_health': a, 'attack_play': b}, {'damage_health': a})

    def test_receipt_carries_the_anchor_failure(self):
        error = escalation.AnchorError('lethal', 'mismatch', dump={'id': 'n', 'pins': []},
                                       checks=[{'check': 'branch', 'ok': False, 'found': object()}])
        with tempfile.TemporaryDirectory() as tmp:
            path = escalation.write_receipt(tmp, 'inspect', {'anchor_failure': error.as_receipt()},
                                            when=datetime(2026, 10, 8, 19, 40, tzinfo=timezone.utc))
            data = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(data['anchor_failure']['anchor'], 'lethal')
        self.assertEqual(data['anchor_failure']['checks'][0]['check'], 'branch')
