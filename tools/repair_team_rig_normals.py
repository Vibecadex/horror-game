"""Preserve authored GLB normals on only the owned synthetic review mesh.

The initial default Interchange import recomputed normals at split UV vertices.
Acquire its LFS lock before running. No reimport, skeleton, map or material edits.
"""
import json
import os
from pathlib import Path
import sys
import traceback
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from finish_editor import finish_editor

out = Path(os.environ['TEDDY_TEST_DIR'])
report = {'passed': False, 'saved_map_writes': False, 'synthetic': True}
u.EditorPythonScripting.set_keep_python_script_alive(True)
try:
    asset = u.EditorAssetLibrary.load_asset('/Game/ScannedBears/RigfitReview/SyntheticV1/SkeletalMeshes/Bear')
    manifest = json.loads((ROOT / 'Assets/Adapted/BearRigfitReview/SyntheticV1/manifest.json').read_text())
    A = u.EditorAssetLibrary
    assert A.get_metadata_tag(asset, 'TeamRigReview.Owner') == 'horror-game-team-rig-review'
    assert A.get_metadata_tag(asset, 'TeamRigReview.SourceId') == manifest['id']
    assert A.get_metadata_tag(asset, 'TeamRigReview.SourceSha256') == manifest['files'][manifest['model']]['sha256']
    subsystem = u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
    settings = subsystem.get_lod_build_settings(asset, 0)
    report['before'] = {'recompute_normals': settings.get_editor_property('recompute_normals'),
                        'recompute_tangents': settings.get_editor_property('recompute_tangents')}
    settings.set_editor_property('recompute_normals', False)
    settings.set_editor_property('recompute_tangents', True)
    subsystem.set_lod_build_settings(asset, 0, settings)
    assert A.save_loaded_asset(asset, only_if_is_dirty=False)
    report.update(passed=True, asset=asset.get_path_name(), after={'recompute_normals': False, 'recompute_tangents': True})
    api = {}
    for name in ['IKRetargetBatchOperationInputs', 'IKRetargetBatchOperation', 'IKRigController',
                 'IKRigDefinitionFactory', 'IKRetargeterController', 'IKRetargetFactory']:
        cls = getattr(u, name)
        api[name] = {'doc': cls.__doc__, 'methods': {}}
        for method in dir(cls):
            if any(k in method for k in ('controller', 'ik_rig', 'batch', 'default_ops', 'chain', 'auto_align')):
                api[name]['methods'][method] = getattr(cls, method).__doc__
    (out / 'retarget-api.json').write_text(json.dumps(api, indent=2), encoding='utf-8')
except Exception:
    report.update(passed=False, error=traceback.format_exc())
(out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
finish_editor(None)
