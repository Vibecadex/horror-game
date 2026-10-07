"""One-time recovery of THIS pass's unsaved map ownership after failed first import.

Only the exact new-map bytes created by the failed 135658 authoring run qualify.
No general adoption of existing maps or materials is permitted.
"""
import hashlib
import json
import os
import runpy
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
map_file = ROOT / 'TeddyBlueprint/Content/Maps/TeddyChamberParity.umap'
failed = json.loads((ROOT / 'evidence/implementation/20261007T135658-author_chamber_parity_20261007/receipt.json').read_text())
assert failed['map'] == '/Game/Maps/TeddyChamberParity' and not failed['passed']
assert "KeyError: 'Concrete_001'" in failed['error']
assert hashlib.sha256(map_file.read_bytes()).hexdigest() == 'be17d1fc0449d134b911b3a40cca432a805d30e0fa55d27e35dac8c61934720e'
baseline = json.loads((ROOT / 'evidence/chamber-parity/20261007/baseline.json').read_text())
assert 'TeddyBlueprint/Content/Maps/TeddyChamberParity.umap' not in baseline['files']
level = u.get_editor_subsystem(u.LevelEditorSubsystem)
assert level.load_level(failed['map'])
world = u.EditorAssetLibrary.load_asset(failed['map'])
assert u.EditorAssetLibrary.get_metadata_tag(world, 'ChamberParity.Owner') in ('', 'chamber-parity-20261007')
u.EditorAssetLibrary.set_metadata_tag(world, 'ChamberParity.Owner', 'chamber-parity-20261007')
assert level.save_current_level()
(Path(os.environ['TEDDY_TEST_DIR']) / 'ownership-recovery.json').write_text(json.dumps({
    'map': failed['map'], 'creation_run': '20261007T135658-author_chamber_parity_20261007',
    'pre_recovery_sha256': 'be17d1fc0449d134b911b3a40cca432a805d30e0fa55d27e35dac8c61934720e',
    'purpose': 'Persist the ownership tag on this run\'s newly created map before continuing its failed import.'}, indent=2))
runpy.run_path(str(ROOT / 'tools/author_chamber_parity_20261007.py'), run_name='__main__')
