"""Create a bounded FK retarget probe from the preserved mannequin to the synthetic bear.

Creates new IK rigs, a retargeter and three animation copies. This establishes basic
compatibility only: no foot IK, root-motion production setup or chamber replacement.
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

OUT = Path(os.environ['TEDDY_TEST_DIR'])
DEST = '/Game/ScannedBears/RigfitReview/RetargetV1'
A = u.EditorAssetLibrary
T = u.AssetToolsHelpers.get_asset_tools()
report = {'passed': False, 'synthetic': True, 'saved_map_writes': False,
          'destination': DEST, 'assets': [], 'foot_ik': False, 'root_motion_operation': False,
          'source_root_settings_retained': True,
          'method': 'New source/target IK rigs, six mapped chains, automatic target pose alignment, pelvis and FK operations.'}


def own(asset):
    assert asset and asset.get_path_name().startswith(DEST + '/')
    A.set_metadata_tag(asset, 'TeamRigReview.Owner', 'horror-game-team-rig-review')
    A.set_metadata_tag(asset, 'TeamRigReview.Synthetic', 'true')
    assert A.save_loaded_asset(asset, only_if_is_dirty=False)
    report['assets'].append({'path': asset.get_path_name(), 'class': asset.get_class().get_name()})
    return asset


def make_rig(name, mesh, root, chains):
    rig = T.create_asset(name, DEST, u.IKRigDefinition, u.IKRigDefinitionFactory())
    assert rig
    controller = u.IKRigController.get_controller(rig)
    assert controller.set_skeletal_mesh(mesh)
    assert controller.set_retarget_root(root)
    bones = {str(b) for b in u.AnimPoseExtensions.get_bone_names(mesh.get_editor_property('skeleton').get_reference_pose())}
    for label, (start, end) in chains.items():
        assert {start, end} <= bones, (name, label, start, end)
        assert str(controller.add_retarget_chain(label, start, end, 'None')) == label
    own(rig)
    return rig


try:
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    assert not A.does_directory_exist(DEST), 'Existing retarget review namespace; never overwrite it'
    source = A.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple')
    target = A.load_asset('/Game/ScannedBears/RigfitReview/SyntheticV1/SkeletalMeshes/Bear')
    assert isinstance(source, u.SkeletalMesh) and isinstance(target, u.SkeletalMesh)
    assert A.get_metadata_tag(target, 'TeamRigReview.Owner') == 'horror-game-team-rig-review'
    source_chains = {'Spine': ('spine_01', 'spine_05'), 'Head': ('neck_01', 'head'),
                     'LeftArm': ('upperarm_l', 'hand_l'), 'RightArm': ('upperarm_r', 'hand_r'),
                     'LeftLeg': ('thigh_l', 'foot_l'), 'RightLeg': ('thigh_r', 'foot_r')}
    target_chains = {'Spine': ('Spine', 'Spine2'), 'Head': ('Neck', 'Head'),
                     'LeftArm': ('LeftArm', 'LeftHand'), 'RightArm': ('RightArm', 'RightHand'),
                     'LeftLeg': ('LeftUpLeg', 'LeftFoot'), 'RightLeg': ('RightUpLeg', 'RightFoot')}
    source_rig = make_rig('IK_ReviewManny', source, 'pelvis', source_chains)
    target_rig = make_rig('IK_ReviewBear', target, 'Hips', target_chains)
    retargeter = T.create_asset('RTG_ReviewMannyToBear', DEST, u.IKRetargeter, u.IKRetargetFactory())
    controller = u.IKRetargeterController.get_controller(retargeter)
    controller.set_ik_rig(u.RetargetSourceOrTarget.SOURCE, source_rig)
    controller.set_ik_rig(u.RetargetSourceOrTarget.TARGET, target_rig)
    controller.add_default_ops()
    report['operations'] = []
    for i in range(controller.get_num_retarget_ops()):
        name = str(controller.get_op_name(i))
        enabled = 'ik' not in name.lower() and 'root' not in name.lower()
        assert controller.set_retarget_op_enabled(i, enabled)
        report['operations'].append({'name': name, 'enabled': enabled})
    for name in target_chains:
        assert controller.set_source_chain(name, name), name
    controller.auto_align_all_bones(u.RetargetSourceOrTarget.TARGET)
    own(retargeter)
    source_paths = [
        '/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle',
        '/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd',
        '/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_01',
    ]
    source_animations = [A.load_asset(p) for p in source_paths]
    assert all(isinstance(a, u.AnimSequence) for a in source_animations)
    options = u.IKRetargetBatchOperationInputs()
    for key, value in {'assets_to_retarget': [A.find_asset_data(p) for p in source_paths],
                       'source_mesh': source, 'target_mesh': target, 'ik_retarget_asset': retargeter,
                       'target_path': DEST + '/Animations', 'prefix': 'RET_',
                       'use_source_path': False, 'include_referenced_assets': False,
                       'overwrite_existing_files': False}.items():
        options.set_editor_property(key, value)
    outputs = u.IKRetargetBatchOperation.run_batch_retarget(options)
    assert len(outputs) == 3, len(outputs)
    for data in outputs:
        clip = own(data.get_asset())
        assert clip.get_editor_property('skeleton') == target.get_editor_property('skeleton')
        assert clip.get_play_length() > 0
    report.update(passed=True, source_mesh=source.get_path_name(), target_mesh=target.get_path_name(),
                  source_animations=source_paths, source_chains=source_chains, target_chains=target_chains,
                  pose_alignment='Automatic chain-to-chain target alignment; no hand-edited rotations.')
except Exception:
    report['error'] = traceback.format_exc()
(OUT / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
finish_editor(None)
