"""Fresh saved skeletal readback, source-pose comparison and held native renders.

No assets or maps are saved. This verifies isolated PIE animation playback, not encounter gameplay,
real scanned bear quality, physical input, retargeting or packaged performance.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from finish_editor import finish_editor
from png_evidence import decode_png
from team_rig_source_pose import SourcePose

OUT = Path(os.environ['TEDDY_TEST_DIR'])
SOURCE = ROOT / 'Assets/Adapted/BearRigfitReview/SyntheticV1'
DEST = '/Game/ScannedBears/RigfitReview/SyntheticV1'
A = u.EditorAssetLibrary
ACTORS = u.get_editor_subsystem(u.EditorActorSubsystem)
report = {'passed': False, 'synthetic': True, 'asset_writes': False, 'saved_map_writes': False,
          'engine': u.SystemLibrary.get_engine_version(), 'checks': {}, 'clips': [], 'captures': [],
          'mode': 'Fresh editor; saved assets, independent source positions, isolated PIE playback and held poses.',
          'axis_conversion': 'glTF (x,y,z) metres -> Unreal (x,z,y) centimetres; front +Y, left +X, up +Z.',
          'actor_scale': 1, 'retargeting_verified': False, 'real_scan_verified': False,
          'retarget_review_requested': os.environ.get('TEAM_RIG_RETARGET') == '1'}
state = {'started': time.monotonic(), 'finished': False, 'index': 0, 'phase': 'warmup'}
handle = None


def vector(v):
    return [float(v.x), float(v.y), float(v.z)]


def distance(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))


def check(name, passed):
    report['checks'][name] = bool(passed)
    assert passed, name


def finish(error=None):
    if state['finished']:
        return
    state['finished'] = True
    if error:
        report['error'] = error
    report['passed'] = not error and len(report['captures']) == len(state.get('shots', [])) and bool(report['captures'])
    (OUT / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    finish_editor(handle)


def spawn(cls, pos, rot=None):
    # Ordinary actors duplicate into PIE; the review world is never saved.
    return ACTORS.spawn_actor_from_class(cls, u.Vector(*pos), rot or u.Rotator(), transient=False)


def pose_positions(pose):
    return {b: vector(u.AnimPoseExtensions.get_bone_pose(pose, b, u.AnimPoseSpaces.WORLD).translation)
            for b in state['manifest']['bones']}


def evaluated_positions(animation, t):
    opts = u.AnimPoseEvaluationOptions()
    opts.set_editor_property('optional_skeletal_mesh', state['mesh'])
    opts.set_editor_property('should_retarget', True)
    opts.set_editor_property('evaluation_type', u.AnimDataEvalType.COMPRESSED)
    opts.set_editor_property('extract_root_motion', animation.get_editor_property('enable_root_motion'))
    # The editor API defaults to ignoring root locks. The single-node runtime player
    # honours the saved source clip's root lock; compare like-for-like playback.
    opts.set_editor_property('incorporate_root_motion_into_pose', False)
    return pose_positions(u.AnimPoseExtensions.get_anim_pose_at_time(animation, t, opts))


def expected_positions(name, t):
    if name and name.startswith('RET_'):
        return evaluated_positions(state['animations'][name], t)
    return state['source'].positions(name, t)


def inspect():
    manifest = json.loads((SOURCE / 'manifest.json').read_text(encoding='utf-8'))
    state['manifest'] = manifest
    digest = hashlib.sha256((SOURCE / manifest['model']).read_bytes()).hexdigest()
    check('source_hash_matches', digest == manifest['files'][manifest['model']]['sha256'])
    state['source'] = SourcePose(SOURCE / manifest['model'])
    assets = [A.load_asset(p) for p in A.list_assets(DEST, recursive=True, include_folder=False)]
    check('nine_saved_assets', len(assets) == 9 and all(assets))
    check('all_assets_owned', all(A.get_metadata_tag(a, 'TeamRigReview.Owner') == 'horror-game-team-rig-review' for a in assets))
    check('all_assets_source_bound', all(A.get_metadata_tag(a, 'TeamRigReview.SourceSha256') == digest for a in assets))
    meshes = [a for a in assets if isinstance(a, u.SkeletalMesh)]
    check('one_skeletal_mesh', len(meshes) == 1)
    mesh = state['mesh'] = meshes[0]
    build = u.SkeletalMeshEditorSubsystem.get_lod_build_settings(mesh, 0)
    check('authored_normals_preserved', not build.get_editor_property('recompute_normals'))
    skeleton = mesh.get_editor_property('skeleton')
    ref = skeleton.get_reference_pose()
    bones = [str(b) for b in u.AnimPoseExtensions.get_bone_names(ref)]
    report['bones'] = bones
    check('exactly_21_expected_bones', len(bones) == 21 and set(bones) == set(manifest['bones']))
    parents = {b: str(mesh.get_bone_parent(b)) for b in bones}
    report['parents'] = parents
    check('hierarchy_preserved_no_extra_root', all(parents[b] == (manifest['parents'][b] or 'None') for b in bones))
    reference = pose_positions(ref)
    expected = state['source'].positions()
    report['reference_positions_cm'] = reference
    report['reference_max_error_cm'] = max(distance(reference[b], expected[b]) for b in bones)
    check('reference_pose_and_axes_match_source', report['reference_max_error_cm'] < 0.02)
    bounds = mesh.get_imported_bounds()
    extent, origin = vector(bounds.box_extent), vector(bounds.origin)
    report['imported_size_cm'] = [v*2 for v in extent]
    report['imported_base_z_cm'] = origin[2]-extent[2]
    report['forward_axis'] = str(mesh.get_editor_property('forward_axis'))
    check('height_preserved_metres_to_cm', abs(extent[2]*2-manifest['rest_height_cm']) < 0.02)
    check('rest_mesh_grounded', abs(report['imported_base_z_cm']) < 0.02)
    materials = [m.get_editor_property('material_interface') for m in mesh.get_editor_property('materials')]
    report['materials'] = [m.get_path_name() for m in materials if m]
    check('saved_material_resolves', len(materials) == 1 and all(materials))
    textures = [a for a in assets if isinstance(a, u.Texture2D)]
    check('saved_texture_present', len(textures) == 1)
    animations = state['animations'] = {a.get_name(): a for a in assets if isinstance(a, u.AnimSequence)}
    state['review_clips'] = list(manifest['clips'])
    check('four_named_clips', set(animations) == set(manifest['clips']))
    opts = u.AnimPoseEvaluationOptions()
    opts.set_editor_property('optional_skeletal_mesh', mesh)
    opts.set_editor_property('should_retarget', False)
    for name, animation in animations.items():
        check(name + '_same_skeleton', animation.get_editor_property('skeleton') == skeleton)
        length = animation.get_play_length()
        check(name + '_two_seconds', abs(length-2) < 0.001)
        samples = []
        for t in [0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]:
            observed = pose_positions(u.AnimPoseExtensions.get_anim_pose_at_time(animation, t, opts))
            expected = state['source'].positions(name, t)
            error = max(distance(observed[b], expected[b]) for b in bones)
            samples.append({'seconds': t, 'max_source_error_cm': error, 'positions_cm': observed})
        maximum = max(s['max_source_error_cm'] for s in samples)
        report['clips'].append({'name': name, 'length': length, 'max_source_error_cm': maximum, 'samples': samples})
        check(name + '_source_motion_preserved', maximum < 0.2)
    if report['retarget_review_requested']:
        retarget_assets = [A.load_asset(p) for p in A.list_assets('/Game/ScannedBears/RigfitReview/RetargetV1', recursive=True)]
        check('six_retarget_review_assets', len(retarget_assets) == 6 and all(retarget_assets))
        check('retarget_assets_owned', all(A.get_metadata_tag(a, 'TeamRigReview.Owner') == 'horror-game-team-rig-review'
                                           for a in retarget_assets))
        clips = {a.get_name(): a for a in retarget_assets if isinstance(a, u.AnimSequence)}
        check('idle_walk_attack_retargeted', set(clips) == {'RET_MM_Idle', 'RET_MF_Unarmed_Walk_Fwd', 'RET_MM_Attack_01'})
        report['retarget_clips'] = []
        for name, animation in clips.items():
            check(name + '_target_skeleton', animation.get_editor_property('skeleton') == skeleton)
            length = animation.get_play_length()
            check(name + '_nonempty', length > 0.5)
            samples = []
            segment_error = 0
            for fraction in [0, 0.25, 0.5, 0.75, 0.99]:
                positions = evaluated_positions(animation, fraction*length)
                check(name + f'_finite_pose_{fraction}', all(math.isfinite(v) and abs(v) < manifest['rest_height_cm']*4
                                                            for p in positions.values() for v in p))
                segment_error = max(segment_error, max(abs(distance(positions[b], positions[parent])-distance(reference[b], reference[parent]))
                                                       for b, parent in manifest['parents'].items() if parent))
                samples.append({'seconds': fraction*length, 'positions_cm': positions})
            check(name + '_bone_lengths_preserved', segment_error < 0.2)
            report['retarget_clips'].append({'name': name, 'length': length,
                                             'max_segment_length_error_cm': segment_error, 'samples': samples,
                                             'foot_ik': False, 'root_motion_operation': False,
                                             'source_root_settings_retained': {
                                                 key: str(animation.get_editor_property(key)) for key in
                                                 ('enable_root_motion', 'force_root_lock', 'root_motion_root_lock')}})
        state['animations'].update(clips)
        state['review_clips'].extend(sorted(clips))
        report['retargeting_verified'] = 'Basic saved FK/pelvis retarget only; foot planting and production quality unaccepted.'


def stage():
    assert u.EditorLoadingAndSavingUtils.new_blank_map(False)
    editor_world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    editor_world.get_world_settings().set_editor_property('default_game_mode', u.GameModeBase)
    actor = spawn(u.SkeletalMeshActor, (0, 0, 0))
    actor.set_actor_label('TeamRigReviewBear')
    component = actor.get_component_by_class(u.SkeletalMeshComponent)
    component.set_skinned_asset_and_update(state['mesh'], True)
    component.set_update_animation_in_editor(True)
    component.set_editor_property('visibility_based_anim_tick_option', u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    ground = spawn(u.StaticMeshActor, (0, 0, -2.5))
    ground.static_mesh_component.set_static_mesh(A.load_asset('/Engine/BasicShapes/Cube'))
    ground.set_actor_scale3d(u.Vector(5, 5, 0.05))
    for intensity, pitch, yaw in ((6, -50, -80), (2, -30, 95)):
        light = spawn(u.DirectionalLight, (0, 0, 200), u.Rotator(pitch=pitch, yaw=yaw))
        light.light_component.set_editor_property('intensity', intensity)
    pos = u.Vector(85, 150, 75)
    rot = u.MathLibrary.find_look_at_rotation(pos, u.Vector(0, 0, 24))
    camera = spawn(u.CameraActor, vector(pos), rot)
    camera.set_actor_label('TeamRigReviewCamera')
    camera.camera_component.set_editor_property('field_of_view', 32)
    pp = spawn(u.PostProcessVolume, (0, 0, 0))
    pp.set_editor_property('unbound', True)
    settings = pp.get_editor_property('settings')
    for name, value in {'override_auto_exposure_min_brightness': True, 'override_auto_exposure_max_brightness': True,
                        'override_auto_exposure_bias': True, 'auto_exposure_min_brightness': 1.0,
                        'auto_exposure_max_brightness': 1.0, 'auto_exposure_bias': 0.0}.items():
        settings.set_editor_property(name, value)
    pp.set_editor_property('settings', settings)
    u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(pos, rot)
    state.update(staged=time.monotonic(), phase='begin_play',
                 shots=[(None, 0), ('Test_Wave', 0.25), ('Test_Wave', 0.75),
                        ('Test_Walk', 0.5), ('Test_Walk', 1.5),
                        ('Test_LookAround', 0.5), ('Test_LookAround', 1.5),
                        ('Test_Bend', 0), ('Test_Bend', 1)])
    for name in state['review_clips']:
        if name.startswith('RET_'):
            length = state['animations'][name].get_play_length()
            state['shots'].extend([(name, length*0.25), (name, length*0.7)])
    u.get_editor_subsystem(u.LevelEditorSubsystem).editor_request_begin_play()


def tick(dt):
    try:
        now = time.monotonic()
        if now-state['started'] > 240:
            raise RuntimeError('Native rig verification timeout')
        if state['phase'] == 'begin_play':
            world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
            if not world:
                return
            pc = u.GameplayStatics.get_player_controller(world, 0)
            if not pc:
                return
            actors = u.GameplayStatics.get_all_actors_of_class(world, u.SkeletalMeshActor)
            actor = next(a for a in actors if a.get_actor_label() == 'TeamRigReviewBear')
            camera = next(a for a in u.GameplayStatics.get_all_actors_of_class(world, u.CameraActor)
                          if a.get_actor_label() == 'TeamRigReviewCamera')
            pawn = u.GameplayStatics.get_player_pawn(world, 0)
            if pawn:
                pawn.set_actor_hidden_in_game(True)
                pawn.set_actor_enable_collision(False)
            pc.set_view_target_with_blend(camera, 0)
            if pc.get_hud():
                pc.get_hud().set_editor_property('show_hud', False)
            state.update(component=actor.get_component_by_class(u.SkeletalMeshComponent),
                         camera=camera, world=world, pc=pc, phase='warmup', staged=now)
        comp = state['component']
        if state['phase'] == 'warmup':
            if now-state['staged'] < 15:
                return
            state['phase'] = 'set'
        if state['phase'] == 'set':
            name, t = state['shots'][state['index']]
            if name:
                comp.play_animation(state['animations'][name], False)
                comp.set_play_rate(0)
                comp.set_position(t, False)
            state.update(ready=now, phase='settle')
        elif state['phase'] == 'settle' and now-state['ready'] > 1:
            name, t = state['shots'][state['index']]
            observed = {b: vector(comp.get_bone_transform(b).translation) for b in state['manifest']['bones']}
            expected = expected_positions(name, t)
            maximum = max(distance(observed[b], expected[b]) for b in observed)
            state['held'] = {'clip': name or 'Rest', 'seconds': t, 'positions_cm': observed, 'max_expected_pose_error_cm': maximum,
                             'comparison': 'saved retarget evaluation' if name and name.startswith('RET_') else 'independent source GLB'}
            report['last_held_pose'] = state['held']
            check(f'held_pose_{state["index"]}_matches_expected', maximum < 0.2)
            path = OUT / f'{state["index"]:02}-{name or "Rest"}-{t:.2f}.png'
            state['image'] = path
            u.SystemLibrary.execute_console_command(state['world'], 'HighResShot 1280x720 filename="' + path.as_posix() + '"', state['pc'])
            state['phase'] = 'capture'
        elif state['phase'] == 'capture' and state['image'].exists():
            try:
                validation = decode_png(state['image'])
            except Exception:
                return
            validation.pop('chunks', None)
            report['captures'].append({**state['held'], 'path': str(state['image']), 'validation': validation})
            state['index'] += 1
            if state['index'] == len(state['shots']):
                for name in state['review_clips']:
                    hashes = [c['validation']['pixel_sha256'] for c in report['captures'] if c['clip'] == name]
                    check(name + '_distinct_rendered_poses', len(hashes) == 2 and len(set(hashes)) == 2)
                state.update(phase='play_start', playback_index=0)
                report['playback'] = []
            else:
                state['phase'] = 'set'
        elif state['phase'] == 'play_start':
            name = state['review_clips'][state['playback_index']]
            comp.play_animation(state['animations'][name], True)
            comp.set_play_rate(1)
            comp.set_position(0, False)
            state.update(play_clip=name, play_started=now, phase='play_tick')
        elif state['phase'] == 'play_tick' and now-state['play_started'] > 0.2:
            state.update(play_before=comp.get_position(),
                         play_bones_before={b: vector(comp.get_bone_transform(b).translation) for b in state['manifest']['bones']},
                         play_started=now, phase='play_verify')
        elif state['phase'] == 'play_verify' and now-state['play_started'] > 0.7:
            clip_length = state['animations'][state['play_clip']].get_play_length()
            advanced = (comp.get_position()-state['play_before']) % clip_length
            moved = max(distance(vector(comp.get_bone_transform(b).translation), state['play_bones_before'][b])
                        for b in state['manifest']['bones'])
            report['playback'].append({'clip': state['play_clip'], 'advanced_seconds': advanced, 'max_bone_movement_cm': moved})
            check(state['play_clip'] + '_PIE_playback_advances', 0.1 < advanced < 1.8)
            check(state['play_clip'] + '_PIE_bones_move', moved > (0.005 if 'Idle' in state['play_clip'] else 0.1))
            state['playback_index'] += 1
            if state['playback_index'] == len(state['review_clips']):
                finish()
            else:
                state['phase'] = 'play_start'
    except Exception:
        finish(traceback.format_exc())


try:
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    inspect()
    stage()
    handle = u.register_slate_post_tick_callback(tick)
except Exception:
    finish(traceback.format_exc())
