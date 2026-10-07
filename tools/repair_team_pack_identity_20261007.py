"""Repair only the review mesh authored in this run, after its failed identity audit."""
import hashlib
import json
import os
from pathlib import Path
import unreal as u

root = Path(__file__).resolve().parents[1]
pack = json.loads((root / 'Assets/ThirdParty/BearScannerPackSample/manifest.json').read_text())
path = '/Game/ScannedBears/TeamPackSample/Real_bear_example_scan_exampl/SM_Bear_Real_bear_example_scan'
assets = u.EditorAssetLibrary
mesh = assets.load_asset(path)
assert isinstance(mesh, u.StaticMesh)
assert assets.get_metadata_tag(mesh, 'BearScanner.Owner') == 'bear-scanner'
assert assets.get_metadata_tag(mesh, 'BearPackRevision') == pack['revision']
assert assets.get_metadata_tag(mesh, 'BearModelSha256') == pack['files'][pack['model']['file']]['sha256']
previous = assets.get_metadata_tag(mesh, 'BearScanId')
assert previous in ('example_real_bear', pack['id']), previous
changed = previous != pack['id']
if changed:
    assets.set_metadata_tag(mesh, 'BearScanId', pack['id'])
    assert assets.save_loaded_asset(mesh)
receipt = {'passed': True, 'mesh': path, 'previous_identity': previous, 'identity': pack['id'],
           'changed': changed, 'chamber_writes': False, 'reason': 'Preserve the original opaque bear-pack identity'}
(Path(os.environ['TEDDY_TEST_DIR']) / 'receipt.json').write_text(json.dumps(receipt, indent=2))
