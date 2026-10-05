"""Index existing repair evidence and validate local delivery links; no game mutation."""
import ast
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from datetime import datetime, timezone

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'evidence/qa-repair/20261005T042900Z'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()

runs = {
    'key_route': '20261005T043241-verify_encounter_keys',
    'independent_behavior': '20261005T044114-verify_encounter_repair',
    'camera': '20261005T043927-verify_encounter_camera',
    'combat_edges': '20261005T044153-verify_encounter_edges',
    'full_encounter_movie': '20261005T044237-record_encounter',
}
verified = {}
for name, run in runs.items():
    folder = ROOT/'evidence/implementation'/run
    receipt = read(folder/'receipt.json')
    host = read(folder/'host-result.json')
    assert receipt['passed'] and host['passed'], (name, receipt.get('error'), host)
    count = len(receipt.get('checks', receipt.get('cases', [])))
    verified[name] = {'passed': True, 'checks': count or None,
                      'receipt': (folder/'receipt.json').relative_to(ROOT).as_posix(),
                      'host_receipt': (folder/'host-result.json').relative_to(ROOT).as_posix()}
native = read(OUT/'native-motion-044641/receipt.json')
assert native['passed'] and native['all_frames_decoded']
assert read(OUT/'preservation.json')['passed']
assert read(OUT/'visual-authoring-05.json')['passed']
assert read(OUT/'key-repair.json')['passed']

status = '''# Teddy Encounter working status

Updated 5 October 2026 after the independent QA repair.

## Current result

The user authorized continuing after the independent comparison. Space, Escape and F5 are now repaired and verified through saved key mappings. The visual pass tightens framing, concentrates lighting, adds peripheral haze, reduces floor repetition, adds subtle cloth detail and softens the warning ring. The scene is ready for another visual review; exact fidelity and user acceptance remain separate.

Use **PLAY.cmd** for the updated encounter, **EDIT.cmd** for the editable map, and **PLAY_BASELINE.cmd** for the preserved starter. Project: `TeddyBlueprint/TeddyBlueprint.uproject`; map: `/Game/Maps/TeddyEncounter`; engine: Unreal5.8.3. [Current review](evidence/qa-repair/20261005T042900Z/review.html), [repair report](evidence/qa-repair/20261005T042900Z/REPAIR_REPORT.md), [controls](ENCOUNTER.md).

## Repair and verification

The original independent QA found invalid `(` FKeys created by struct-style text import. Corrected `tools/build_combat.py`, `tools/refine_player_controls.py` and the saved input mapping using `tools/repair_encounter_keys.py`. Modifiers, triggers and existing device mappings were preserved. The new test routes simulated key presses through PlayerController and the saved context, closing the coverage gap in action-only tests.

| Fresh run under evidence/implementation | Result |
| --- | --- |
| `20261005T043144-verify_encounter_keys` | Preserved expected pre-repair failure: Space/Escape failed and F5 did not restart. |
| `20261005T043241-verify_encounter_keys` | 12/12 key-route checks, including pause suppression, resume and restart while paused. |
| `20261005T044114-verify_encounter_repair` | 8/8 independent action-level behavior checks, three fresh decoded captures, no teleporting/health edits/disabled AI. |
| `20261005T043927-verify_encounter_camera` | 12/12 conservative body-bounds cases at arena edges and opposite corners. |
| `20261005T044153-verify_encounter_edges` | 13/13 cursor aiming, wall collision, weapon alignment, evasion, defeat and restart checks. Cursor-aim error0.62degrees. |
| `20261005T044237-record_encounter` | Full encounter, boss/minion defeat, pause and restart recorded. About12.6unique captures/sec; use native video below for motion review. |

All these final runs have successful host receipts and clean exits. Methods differ: key simulation, action injection, cursor placement, and staged edge cases are explicitly identified in each receipt. Physical keyboard/mouse/gamepad play is not claimed.

The fresh ordinary-game capture is `evidence/qa-repair/20261005T042900Z/native-motion-044641/native-motion.mp4`:1280x720,17.1seconds,512decoded frames, about30fps. It captures only the owned game-window client area. Its separate QA map copies the current encounter and adds a normal-input driver; gameplay, AI, health and animation are unchanged. No OS input events were sent. The native audio master is nonzero; a separate stereo preview is available. The movie is silent and no audio synchronization or reference match is claimed.

## Current visual settings and limits

Camera pitch−46°, FOV48, height=clamp(max(1.8*abs(deltaX),1.0*abs(deltaY))+850,1700,5600), backoffset=−cot46°*height. Existing midpoint, foreground bias, Z160 target and interpolation5 remain. Saved manual exposure+3.8EV, Lumen and virtual shadows retained.

`tools/refine_qa_visuals.py` makes three new owned `M_QA_*` materials, retaining original materials/textures. Broad fill is reduced; key/rim/fill lights are more localized. Fog density.035 and warning material changes are visual only; attack timing/radius/collision are preserved. An over-bright procedural-floor trial and an overly plain trial were rejected before the retained worn-floor blend.

Largest remaining differences: simpler teddy anatomy, procedural creature motion, and regular arena boundaries/some floor seams. Exact atmospheric fidelity still needs visual feedback. Audio matching, physical controls, packaged delivery and sustained performance remain unverified; no old performance number is presented as current.

## Preservation and ownership

Root desktop Codex integrated and independently checked the repair; the requested Astra agent drafted and advised on visual/camera settings without concurrent engine writes. No editor or native game process is left running at handoff. No new Codex CLI session, installer, global setting change or Windows protection change was used.

Pre-repair142-file backup: `evidence/qa-repair/20261005T042900Z/before-repair.zip`, verified in `baseline.json`. All555 original baseline files, source video, source ZIP and original teddy are unchanged. Only five existing encounter assets changed; three new owned materials and isolated QA capture assets were added. Adapted source files remain unchanged. A concurrent AGENTS.md context-guidance addition was preserved. Original independent QA and delivery evidence remain intact.

The current repair manifest is `evidence/qa-repair/20261005T042900Z/manifest.json`; the older `evidence/delivery/manifest.json` describes the preserved pre-repair delivery. Ownership remains `TeddyEncounter.Owner=encounter-20261004`; use one writer for the map/assets.

## Continuation notes

- Use the current comparison and fresh native movie for feedback. Further visual refinement should target a concrete remaining discrepancy and retain these receipts.
- Run an authoring script with `python tools/astra_setup.py editor-script tools/<script>.py --render`; run a relevant test with `python tools/run_encounter_test.py tools/<test>.py`. Do not rerun broad historical builders over the final scene or repeat the full Astra setup probe for routine edits.
- Unreal5.8 material input display names can differ from C++ fields. Noise's position uses its reflected world-position name; single unnamed sockets accept an empty input name. The refinement helper now resolves these through MaterialEditingLibrary.
- Repeated PNG screenshot capture remains too slow for a smooth gameplay recording. The scoped native-window capture route is in `tools/capture_qa_native_motion.py` and `tools/author_qa_native_motion.py`; it does not alter the playable level or send global input.
- Reuse installed tools and cached Context7. Hand installation/update commands to the user. Keep Windows protection and global Codex settings unchanged.

Earlier status documents are preserved in the pre-repair archive and `evidence/revisions/`. The historical native BossShot DLL restriction and low-angle BossArena are not the active Blueprint target.
'''
for old, new in {
    'Unreal5.8': 'Unreal 5.8', 'error0.62degrees': 'error 0.62 degrees',
    'About12.6unique': 'About 12.6 unique', 'about12.6unique': 'about 12.6 unique',
    ':1280x720,17.1seconds,512decoded frames, about30fps': ': 1280 x 720, 17.1 seconds, 512 decoded frames, about 30 fps',
    'pitch−46°': 'pitch −46°', 'FOV48': 'FOV 48', 'Z160': 'Z 160',
    'interpolation5': 'interpolation 5', 'exposure+3.8EV': 'exposure +3.8 EV',
    'density.035': 'density .035', 'Pre-repair142-file': 'Pre-repair 142-file',
    'All555': 'All 555',
}.items():
    status = status.replace(old, new)
(ROOT/'WORK_STATUS.md').write_text(status, encoding='utf-8')

baseline = read(OUT/'baseline.json')
changed = []
for entry in baseline['files']:
    path = ROOT/entry['path']
    if sha(path) != entry['sha256']:
        changed.append(entry['path'])
allowed_assets = {
    'TeddyBlueprint/Content/Maps/TeddyEncounter.umap',
    'TeddyBlueprint/Content/TeddyEncounter/Blueprints/BP_CombatCamera.uasset',
    'TeddyBlueprint/Content/TeddyEncounter/Blueprints/BP_TeddyBoss.uasset',
    'TeddyBlueprint/Content/TeddyEncounter/Blueprints/BP_Stitchling.uasset',
    'TeddyBlueprint/Content/TeddyEncounter/Input/IMC_Encounter.uasset',
}
changed_assets = [name for name in changed if name.endswith(('.uasset', '.umap'))]
assert set(changed_assets) == allowed_assets, changed_assets
allowed_other = {'AGENTS.md', 'WORK_STATUS.md', 'ENCOUNTER.md', 'tools/build_combat.py', 'tools/refine_player_controls.py', 'tools/record_encounter.py'}
assert set(changed) <= allowed_assets | allowed_other, changed
paths = set((ROOT/'TeddyBlueprint/Content/TeddyEncounter').rglob('*.uasset'))
paths.add(ROOT/'TeddyBlueprint/Content/Maps/TeddyEncounter.umap')
asset_paths = sorted(paths)
for name in ['WORK_STATUS.md', 'ENCOUNTER.md', 'tools/build_combat.py', 'tools/refine_player_controls.py', 'tools/record_encounter.py',
             'tools/repair_encounter_keys.py', 'tools/verify_encounter_keys.py', 'tools/refine_qa_visuals.py', 'tools/verify_encounter_repair.py',
             'tools/author_qa_native_motion.py', 'tools/capture_qa_native_motion.py', 'tools/finalize_qa_repair.py']:
    path = ROOT/name
    paths.add(path)
    if path.suffix == '.py':
        ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
paths.update(OUT.rglob('*.html'))
paths.update(OUT.glob('*.md'))
manifest = {'created_at_utc': datetime.now(timezone.utc).isoformat(), 'playable_map': '/Game/Maps/TeddyEncounter',
            'owned_gameplay_asset_count': len(asset_paths), 'existing_gameplay_assets_changed': changed_assets,
            'changed_preexisting_paths': changed,
            'concurrent_external_guidance': 'AGENTS.md addition retained; not authored by root',
            'verification': verified, 'native_motion_receipt': 'native-motion-044641/receipt.json',
            'files': [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(paths)]}
(OUT/'manifest.json').write_text(json.dumps(manifest, indent=2))

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = set()
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src', 'poster') and value and not value.startswith(('http:', 'https:', '#', 'data:')):
                self.paths.add(value)

page = (OUT/'review.html').read_text(encoding='utf-8')
links = Links(); links.feed(page)
links.paths.update(re.findall(r"path:'([^']+)'", page))
for sec in ['05', '10', '16']:
    links.paths.add('../../independent-qa/20261005T034938Z/derived/original-gameplay-'+sec+'.png')
links.paths.update(re.findall(r'\]\(([^)]+)\)', (OUT/'REPAIR_REPORT.md').read_text(encoding='utf-8')))
for name in links.paths:
    assert (OUT/name).is_file(), name
images = []
for name in sorted(links.paths):
    if Path(name).suffix == '.png':
        with Image.open(OUT/name) as img:
            img.load(); images.append({'path': name, 'size': list(img.size)})
script = re.search(r'<script>([\s\S]*?)</script>', page).group(1)
(OUT/'review-script.js').write_text(script, encoding='utf-8')
validation = {'passed': True, 'checked_at_utc': datetime.now(timezone.utc).isoformat(),
              'local_links_checked': len(links.paths), 'images_fully_decoded': images,
              'changed_assets_match_authorized_scope': True, 'python_syntax_valid': True,
              'successful_final_engine_runs': len(verified), 'gameplay_assets_in_manifest': len(asset_paths)}
(OUT/'delivery-validation.json').write_text(json.dumps(validation, indent=2))
print(json.dumps({k:v for k,v in validation.items() if k != 'images_fully_decoded'}, indent=2))
