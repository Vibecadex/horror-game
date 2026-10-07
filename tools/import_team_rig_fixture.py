"""Import the synthetic team rig once into an isolated native review namespace.

Run through run_encounter_test.py, then verify_team_rig_fixture.py in a fresh editor.
Never edits an existing package, level, source scan or production character.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from finish_editor import finish_editor

OUT = Path(os.environ['TEDDY_TEST_DIR'])
SOURCE = ROOT / 'Assets/Adapted/BearRigfitReview/SyntheticV1'
DEST = '/Game/ScannedBears/RigfitReview/SyntheticV1'
A = u.EditorAssetLibrary
report = {'passed': False, 'synthetic': True, 'saved_map_writes': False,
          'destination': DEST, 'engine': u.SystemLibrary.get_engine_version(),
          'assets': [], 'warnings': [], 'method': 'Interchange glTF skeletal import with explicit animation and skin settings.'}
try:
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    manifest = json.loads((SOURCE / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['synthetic'] is True
    model = SOURCE / manifest['model']
    digest = hashlib.sha256(model.read_bytes()).hexdigest()
    assert digest == manifest['files'][manifest['model']]['sha256']
    assert not A.does_directory_exist(DEST), 'Existing namespace: inspect it; never overwrite a previous import'
    pipeline = u.InterchangeGenericAssetsPipeline()
    pipeline.set_editor_property('use_source_name_for_asset', False)
    pipeline.set_editor_property('asset_type_sub_folders', True)
    common = pipeline.get_editor_property('common_meshes_properties')
    common.set_editor_property('recompute_normals', False)
    common.set_editor_property('recompute_tangents', True)
    mesh_options = pipeline.get_editor_property('mesh_pipeline')
    for name, value in {'import_skeletal_meshes': True, 'import_static_meshes': False,
                        'build_nanite': False, 'bone_influence_limit': 4,
                        'use_high_precision_skin_weights': True}.items():
        mesh_options.set_editor_property(name, value)
    animation_options = pipeline.get_editor_property('animation_pipeline')
    animation_options.set_editor_property('import_animations', True)
    animation_options.set_editor_property('import_bone_tracks', True)
    options = u.ImportAssetParameters()
    options.set_editor_property('is_automated', True)
    options.set_editor_property('replace_existing', False)
    options.set_editor_property('override_pipelines', [u.SoftObjectPath(pipeline.get_path_name())])
    manager = u.InterchangeManager.get_interchange_manager_scripted()
    source = u.InterchangeManager.create_source_data(str(model))
    imported = manager.import_asset(DEST, source, options)
    assert imported, 'Interchange returned no assets'
    for asset in imported:
        assert asset.get_path_name().startswith(DEST + '/'), asset.get_path_name()
        A.set_metadata_tag(asset, 'TeamRigReview.Owner', 'horror-game-team-rig-review')
        A.set_metadata_tag(asset, 'TeamRigReview.SourceId', manifest['id'])
        A.set_metadata_tag(asset, 'TeamRigReview.SourceSha256', digest)
        A.set_metadata_tag(asset, 'TeamRigReview.Synthetic', 'true')
        assert A.save_loaded_asset(asset, only_if_is_dirty=False), asset.get_path_name()
        report['assets'].append({'path': asset.get_path_name(), 'class': asset.get_class().get_name()})
    assert A.save_directory(DEST, only_if_is_dirty=False, recursive=True)
    counts = {kind: sum(a['class'] == kind for a in report['assets']) for kind in ('SkeletalMesh', 'Skeleton', 'AnimSequence')}
    report.update(counts=counts, source_sha256=digest,
                  import_settings={'skeletal_meshes': True, 'static_meshes': False, 'animations': True,
                                   'bone_tracks': True, 'nanite': False, 'bone_influence_limit': 4,
                                   'high_precision_skin_weights': True, 'recompute_normals': False,
                                   'recompute_tangents': True})
    assert counts == {'SkeletalMesh': 1, 'Skeleton': 1, 'AnimSequence': 4}, counts
    report['passed'] = True
except Exception:
    report['error'] = traceback.format_exc()
(OUT / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
finish_editor(None)
