"""Read installed skeletal/import APIs without writing any Unreal assets."""
import json
import os
from pathlib import Path
import sys
import unreal as u

sys.path.insert(0, str(Path(__file__).resolve().parent))
from finish_editor import finish_editor

out = Path(os.environ['TEDDY_TEST_DIR'])
names = [
    'AssetImportTask', 'InterchangeManager', 'ImportAssetParameters',
    'InterchangeGenericAssetsPipeline', 'InterchangeGenericMeshPipeline',
    'InterchangeGenericAnimationPipeline', 'SkeletalMeshEditorSubsystem',
    'SkeletalMesh', 'Skeleton', 'SkeletalMeshComponent', 'AnimSequence',
    'AnimationLibrary', 'AnimPoseExtensions', 'AnimPoseEvaluationOptions',
    'AnimationBlueprintLibrary', 'IKRigController', 'IKRigDefinitionFactory',
    'IKRetargeterController', 'IKRetargetFactory', 'IKRetargetBatchOperation',
]
result = {}
for name in names:
    cls = getattr(u, name, None)
    if cls is None:
        result[name] = {'available': False}
        continue
    result[name] = {'available': True, 'doc': cls.__doc__, 'methods': {}}
    for method in dir(cls):
        if method.startswith('_'):
            continue
        if any(k in method for k in ('bone', 'anim', 'skeleton', 'skeletal', 'import',
                                     'pose', 'position', 'retarget', 'chain', 'preview',
                                     'mesh', 'play', 'tick', 'refresh', 'length')):
            result[name]['methods'][method] = getattr(cls, method).__doc__
(out / 'api.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
(out / 'receipt.json').write_text(json.dumps({
    'passed': True, 'asset_writes': False, 'saved_map_writes': False,
    'engine': u.SystemLibrary.get_engine_version(), 'classes': len(result),
}, indent=2), encoding='utf-8')
u.EditorPythonScripting.set_keep_python_script_alive(True)
finish_editor(None)
