"""Host-only preservation and evidence audit, independent of the Unreal authoring run."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--capture', required=True)
parser.add_argument('--room-check', required=True)
args = parser.parse_args()
OUT = ROOT / 'evidence/chamber-parity/20261007'
baseline = json.loads((OUT / 'baseline.json').read_text())
capture = (ROOT / args.capture).resolve()
room = (ROOT / args.room_check).resolve()
assert capture.is_relative_to(ROOT / 'evidence') and room.is_relative_to(ROOT / 'evidence')
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
cap, runtime = read(capture / 'receipt.json'), read(room / 'receipt.json')
actors = {a['label']: a for a in read(capture / 'saved-scene.json')}
runtime_scene = {a['label']: a for a in read(ROOT / 'evidence/implementation/20261007T140736-capture_chamber_views/saved-scene.json')}
original = {a['label']: a for a in read(ROOT / baseline['baseline_capture'] / 'saved-scene.json')}
checks = {}
changed = [p for p, h in baseline['files'].items() if not (ROOT / p).is_file() or sha(ROOT / p) != h]
checks['all_original_content_config_and_teddy_bytes_preserved'] = not changed
checks['fresh_capture_passed'] = cap['passed'] and read(capture / 'host-result.json')['passed']
checks['fresh_room_runtime_passed'] = runtime['passed'] and read(room / 'host-result.json')['passed']
checks['candidate_map_verified'] = cap['map'] == runtime['map'] == '/Game/Maps/TeddyChamberParity'
geometry = lambda rows: {n: {k: a[k] for k in ['class', 'location', 'rotation', 'scale', 'hidden', 'meshes']}
                         for n, a in rows.items() if a['meshes']}
checks['saved_geometry_unchanged_since_native_room_checks'] = geometry(runtime_scene) == geometry(actors)
for name in ['TE_MainTeddy', 'TE_PlayerStart', 'TE_Stitchling_1', 'TE_Stitchling_2', 'TE_Stitchling_3', 'TE_CombatView',
             'TE_ArenaFloor', 'TE_CombatBoundFront', 'TE_CombatBoundBack', 'TE_CombatBoundLeft', 'TE_CombatBoundRight']:
    before, after = original[name], actors[name]
    checks[name + '_preserved'] = all(before[k] == after[k] for k in ['class', 'location', 'rotation', 'scale', 'hidden', 'meshes'])
new = [a for n, a in actors.items() if n.startswith('TE_Parity20261007_') and a['meshes']]
checks['new_decoration_has_no_collision'] = bool(new) and all('NO_COLLISION' in m['collision'] for a in new for m in a['meshes'])
visible = [a for n, a in actors.items() if n.startswith('TE_Parity20261007_SM_') and not a['hidden']]
checks['four_visible_v2_debris_banks'] = len(visible) == 4 and all('_V2.' in a['meshes'][0]['mesh'] for a in visible)
checks['debris_stays_below_8_cm_world_height'] = all(m['bounds_origin'][2] + m['bounds_extent'][2] <= 8 for a in visible for m in a['meshes'])
checks['new_floor_materials_resolve'] = all('/ChamberParity20261007/Materials/' in m for m in actors['TE_Chamber_Recover_Main']['meshes'][0]['materials'])
observations = {}
for shot in cap['captures']:
    rows = [a for a in shot['cutaway_observation'] if a['label'] == 'TE_Chamber_FrontCutaway']
    assert len(rows) == 1
    hidden = rows[0]['actor_hidden_in_game']
    observations[shot['name']] = hidden
    expected = shot['name'] != '02-chamber-reverse'
    checks[shot['name'] + '_native_cutaway'] = hidden == expected
checks['gameplay_camera_preserved'] = cap['architectural_camera_original']['fov'] == 54 and abs(cap['architectural_camera_original']['rotation'][0] + 46) < .001
checks['manual_exposure_preserved'] = all(abs(float(p['auto_exposure_bias']) - 3.8) < .001 for p in cap['postprocess'])
report = {'passed': all(checks.values()), 'checks': checks, 'count': len(checks), 'changed_originals': changed,
          'preserved_files': len(baseline['files']), 'capture': args.capture, 'room_check': args.room_check,
          'cutaway_observations': observations, 'runtime_checks': runtime.get('checks'),
          'physical_device_verified': False, 'visual_parity_accepted': False,
          'runtime_scope': 'Room checks use revision 2 geometry. Revisions 3 and 4 change only lighting, materials and non-colliding fog. All saved mesh transforms, visibility, assignments and collision modes are compared above to retain that coverage.',
          'method': 'Separate host process audits captured saved state, preservation hashes, fresh native runtime and cutaway observations. Same author performs the visual review; no independent agent approval is claimed.'}
(OUT / 'qa.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({'passed': report['passed'], 'checks': report['count'], 'failed': [k for k,v in checks.items() if not v], 'preserved_files': report['preserved_files']}, indent=2))
raise SystemExit(0 if report['passed'] else 1)
