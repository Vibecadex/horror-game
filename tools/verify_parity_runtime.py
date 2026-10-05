"""Read-only saved-art audit plus bounded transient PIE verification.

Run only through run_encounter_test.py, with no other editor/game process open.
Does not save assets. It supplements, rather than repeats, the room/key suites.
Six original clips plus the new grounded collapse advance on the new skin; poses need
independent inspection for seams/skin/contact. Bone and broad bounds checks do
not establish per-vertex skin correctness or visual parity.
"""
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

OUT = Path(os.environ['TEDDY_TEST_DIR'])
MAP = '/Game/Maps/TeddyEncounter'
NAMESPACE = '/Game/TeddyEncounter'
EXPECTED_MESH = NAMESPACE + '/Parity/Teddy/SK_TeddyParityV2'
EXPECTED_BONES = ['root', 'pelvis', 'spine', 'head', 'upperarm_L', 'forearm_L',
                  'hand_L', 'upperarm_R', 'forearm_R', 'hand_R', 'thigh_L',
                  'shin_L', 'foot_L', 'thigh_R', 'shin_R', 'foot_R']
# The original Blender armature object is TeddyRig. The existing Unreal FBX
# skeleton exposes that import wrapper before the 16 authored deform bones.
# Verify its parent links against the original mesh rather than silently
# accepting arbitrary additional bones or changing the source skeleton.
EXPECTED_IMPORTED_BONES = ['TeddyRig'] + EXPECTED_BONES
ORIGINAL_CLIPS = [('Idle', .5), ('Walk', .55), ('Crawl', .55), ('Attack', .6),
                  ('Hit', .6), ('Defeat', .96)]
GROUNDED_CLIP = NAMESPACE + '/Parity/Animation/A_Teddy_DefeatGrounded'
CLIPS = ORIGINAL_CLIPS + [('DefeatGrounded', .96)]
EDITOR = u.get_editor_subsystem(u.UnrealEditorSubsystem)
LEVELS = u.get_editor_subsystem(u.LevelEditorSubsystem)
ACTORS = u.get_editor_subsystem(u.EditorActorSubsystem)
report = {
    'passed': False, 'map': MAP, 'engine': u.SystemLibrary.get_engine_version(),
    'independent_qa': True, 'asset_writes': False, 'physical_device_verified': False,
    'checks': {}, 'floor_actors': [], 'saved_creatures': [], 'clips': [],
    'light_samples': [], 'animation_samples': [], 'captures': [], 'death_events': [],
    'method': 'Fresh saved-map audit, transient PIE input injection for the saved player light, '
              'then original clips and new grounded collapse advance on the saved stitched skin. '
              'NPC actor ticks/movement disabled; mesh component animation continues. '
              'Player is restored to its initial transform and held for seven animation captures. '
              'Finally ApplyDamage executes direct minion death, boss death, and surviving-minion boss-death cascades; '
              'no health variables or Blueprint pins are assigned. '
              'HUD hidden; saved camera, lighting and exposure retained; game paused only to capture.',
    'limitations': [
        'This tests the added art and spotlight attachment, not all gameplay or physical input.',
        'Clip inspection is staged; subsequent death-route checks inject damage and do not prove weapon-hit delivery.',
        'Bone transforms and component bounds detect gross failures, not detached individual stitched vertices.',
        'Render bounds are conservative culling bounds, not an exact deformed surface or foot-contact measurement.',
        'All seven pose images and the saved-death-route image require visual review for skin/stitches/contact.',
        'Passing these checks does not establish visual parity, performance or user acceptance.',
    ],
    'api_evidence': [
        'Context7 official Unreal Engine SkeletalMeshComponent PlayAnimation/GetPosition/SetPosition documentation.',
        'Installed UE 5.8 SceneComponent.h reflected GetSocketLocation, GetWorldLocation, GetWorldRotation and GetAttachParent.',
        'Installed SkinnedMeshComponent.h reflected GetNumBones/GetBoneName; unreflected GetBoneLocation is avoided.',
        'Installed AnimSingleNodeInstance.h reflected GetAnimationAsset; unreflected GetSingleNodeInstance is avoided.',
    ],
}
state = {'wall_start': time.monotonic(), 'phase': 'initialize', 'done': False,
         'clip_index': 0, 'sample_index': 0}
callback = None


def path(obj):
    return obj.get_path_name() if obj else None


def vec(value):
    return [float(value.x), float(value.y), float(value.z)]


def rotation(value):
    return [float(value.pitch), float(value.yaw), float(value.roll)]


def distance(first, second):
    return math.dist(first, second)


def delta_angle(a, b):
    return (a - b + 180.) % 360. - 180.


def check(name, passed):
    report['checks'][name] = bool(passed)


def component_bounds(component):
    origin, extent, radius = u.SystemLibrary.get_component_bounds(component)
    return {'origin': vec(origin), 'extent': vec(extent),
            'min': vec(origin - extent), 'max': vec(origin + extent),
            'sphere_radius': float(radius)}


def saved_audit():
    """Executed before PIE or any transient staging; never modifies the map."""
    all_actors = list(ACTORS.get_all_level_actors())
    dressing = [a for a in all_actors if 'ParityFloorDecor' in {str(t) for t in a.tags}]
    for actor in dressing:
        meshes = actor.get_components_by_class(u.StaticMeshComponent)
        report['floor_actors'].append({
            'label': actor.get_actor_label(), 'tags': [str(t) for t in actor.tags],
            'actor_collision_enabled': actor.get_actor_enable_collision(),
            'meshes': [{'mesh': path(c.static_mesh),
                        'collision_profile': str(c.get_collision_profile_name()),
                        'collision_enabled': str(c.get_collision_enabled()),
                        'no_collision': c.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION,
                        'bounds': component_bounds(c)} for c in meshes],
        })
    check('saved_45_parity_floor_actors', len(dressing) == 45)
    check('parity_floor_ownership_explicit', bool(dressing) and all(
        a.get_actor_label().startswith('TE_Parity_Floor_') and
        {'TeddyEncounterOwned', 'ParityOwned', 'ParityFloorDecor'} <= {str(t) for t in a.tags}
        for a in dressing))
    check('saved_parity_floor_collision_disabled', bool(dressing) and all(
        not a['actor_collision_enabled'] and a['meshes'] and all(
            c['mesh'] and c['no_collision'] and c['collision_profile'] == 'NoCollision'
            for c in a['meshes']) for a in report['floor_actors']))
    old_mesh = u.load_asset(NAMESPACE + '/Teddy/Idle/SK_Teddy')
    new_mesh = u.load_asset(EXPECTED_MESH)
    if not old_mesh or not new_mesh:
        raise RuntimeError('Original or expected V2 skeletal mesh is missing; do not substitute V1')
    skeleton = old_mesh.get_editor_property('skeleton')
    report['original_skeleton'] = path(skeleton)
    report['expected_mesh'] = path(new_mesh)
    report['mesh_slots'] = [
        {'name': str(slot.get_editor_property('material_slot_name')),
         'material': path(slot.get_editor_property('material_interface'))}
        for slot in new_mesh.get_editor_property('materials')]
    check('v2_skin_uses_original_skeleton', new_mesh.get_editor_property('skeleton') == skeleton)
    report['original_and_v2_bone_parents'] = [
        {'bone': bone,
         'original_parent': str(u.SkeletalMeshEditorSubsystem.get_bone_parent(old_mesh, bone)),
         'v2_parent': str(u.SkeletalMeshEditorSubsystem.get_bone_parent(new_mesh, bone))}
        for bone in EXPECTED_IMPORTED_BONES]
    report['original_wrapper_children'] = [str(bone) for bone in
        u.SkeletalMeshEditorSubsystem.get_bone_children(old_mesh, 'TeddyRig')]
    check('v2_bone_hierarchy_matches_original_import_wrapper',
          report['original_wrapper_children'] == ['root'] and
          all(row['original_parent'] == row['v2_parent'] for row in report['original_and_v2_bone_parents']) and
          next(row for row in report['original_and_v2_bone_parents'] if row['bone'] == 'root')['original_parent'] == 'TeddyRig')
    check('stitched_skin_material_slots_present', len(report['mesh_slots']) >= 3 and
          any('seam' in row['name'].lower() for row in report['mesh_slots']) and
          any('thread' in row['name'].lower() for row in report['mesh_slots']) and
          all(row['material'] for row in report['mesh_slots']))
    creatures = [a for a in all_actors if a.get_actor_label() == 'TE_MainTeddy' or
                 a.get_actor_label().startswith('TE_Stitchling')]
    for actor in creatures:
        mesh = actor.get_component_by_class(u.SkeletalMeshComponent)
        report['saved_creatures'].append({
            'label': actor.get_actor_label(), 'class': path(actor.get_class()),
            'mesh': path(mesh.get_editor_property('skeletal_mesh_asset')) if mesh else None,
            'materials': [path(m) for m in mesh.get_materials()] if mesh else [],
        })
    check('all_four_saved_creatures_use_v2_skin', len(creatures) == 4 and
          all(a['mesh'] == path(new_mesh) for a in report['saved_creatures']))
    state['clip_assets'] = {}
    for name, _ in ORIGINAL_CLIPS:
        clip = u.load_asset(NAMESPACE + '/Teddy/' + name + '/A_Teddy_' + name)
        if not clip:
            raise RuntimeError('Missing original runtime clip: ' + name)
        state['clip_assets'][name] = clip
        report['clips'].append({'name': name, 'path': path(clip),
                                'skeleton': path(clip.get_editor_property('skeleton')),
                                'length_seconds': float(clip.get_play_length())})
    check('six_original_clips_share_original_skeleton', len(report['clips']) == 6 and
          all(c['skeleton'] == path(skeleton) and c['length_seconds'] > .1 for c in report['clips']))
    grounded = u.load_asset(GROUNDED_CLIP)
    if not grounded:
        raise RuntimeError('New grounded collapse is missing')
    state['clip_assets']['DefeatGrounded'] = grounded
    report['grounded_clip'] = {'path': path(grounded),
                               'skeleton': path(grounded.get_editor_property('skeleton')),
                               'length_seconds': float(grounded.get_play_length())}
    check('grounded_clip_uses_original_skeleton', grounded.get_editor_property('skeleton') == skeleton and
          abs(grounded.get_play_length() - state['clip_assets']['Defeat'].get_play_length()) < .025)
    report['saved_death_bindings'] = []
    for blueprint_name, expected in [('BP_TeddyBoss', 1), ('BP_Stitchling', 2)]:
        blueprint = u.load_asset(NAMESPACE + '/Blueprints/' + blueprint_name)
        if not blueprint:
            raise RuntimeError('Missing saved creature Blueprint: ' + blueprint_name)
        pins = []
        for graph in u.BlueprintEditorLibrary.list_graphs(blueprint):
            for node in u.BlueprintGraphEditor.get_graph_editor(graph).list_all_nodes():
                pin = node.find_input_pin('NewAnimToPlay')
                if pin.is_valid():
                    pins.append({'graph': graph.get_name(), 'node': node.get_name(),
                                 'value': str(pin.get_pin_value()),
                                 'connected': bool(pin.list_connected_pins())})
        replaced = [p for p in pins if GROUNDED_CLIP in p['value'] and not p['connected']]
        obsolete = [p for p in pins if NAMESPACE + '/Teddy/Defeat/A_Teddy_Defeat' in p['value']]
        report['saved_death_bindings'].append({'blueprint': path(blueprint), 'expected_count': expected,
                                               'grounded_bindings': replaced, 'obsolete_death_bindings': obsolete,
                                               'all_animation_pins': pins})
        check(blueprint_name + '_saved_grounded_death_bindings', len(replaced) == expected and not obsolete)
    directors = [a for a in all_actors if a.get_actor_label() == 'TE_CombatView']
    fovs = [float(a.get_component_by_class(u.CameraComponent).get_editor_property('field_of_view'))
            for a in directors]
    report['saved_camera_fov'] = fovs
    check('saved_gameplay_camera_fov54', len(fovs) == 1 and abs(fovs[0] - 54.) < .01)
    floor = next(a for a in all_actors if a.get_actor_label() == 'TE_ArenaFloor')
    report['arena_floor_bounds'] = component_bounds(floor.get_component_by_class(u.StaticMeshComponent))


def light_snapshot(world, pawn, spot, label):
    pp, lp = pawn.get_actor_location(), spot.get_world_location()
    actor_rot, light_rot = pawn.get_actor_rotation(), spot.get_world_rotation()
    radians = math.radians(actor_rot.yaw)
    dx, dy = lp.x-pp.x, lp.y-pp.y
    parent = spot.get_attach_parent()
    return {'label': label, 'game_seconds': float(u.GameplayStatics.get_time_seconds(world)),
            'pawn': vec(pp), 'pawn_rotation': rotation(actor_rot), 'light': vec(lp),
            'light_rotation': rotation(light_rot), 'light_forward': vec(spot.get_forward_vector()),
            'offset_in_pawn_space': [dx*math.cos(radians)+dy*math.sin(radians),
                                     -dx*math.sin(radians)+dy*math.cos(radians), lp.z-pp.z],
            'relative_location': vec(spot.get_editor_property('relative_location')),
            'relative_rotation': rotation(spot.get_editor_property('relative_rotation')),
            'yaw_relative_to_pawn': delta_angle(light_rot.yaw, actor_rot.yaw),
            'owner': path(spot.get_owner()), 'parent': path(parent),
            'parent_owner': path(parent.get_owner()) if parent else None,
            'intensity': float(spot.get_editor_property('intensity')),
            'volumetric_scattering_intensity': float(spot.get_editor_property('volumetric_scattering_intensity'))}


def mesh_snapshot(world, mesh, boss, pc):
    instance = mesh.get_anim_instance()
    animation = instance.get_animation_asset() if isinstance(instance, u.AnimSingleNodeInstance) else None
    bones = [str(mesh.get_bone_name(i)) for i in range(mesh.get_num_bones())]
    # GetSocketLocation resolves bone names through the skinned component and is
    # reflected. GetBoneLocation itself lacks UFUNCTION in this installation.
    positions = {name: vec(mesh.get_socket_location(name)) for name in bones}
    camera = pc.player_camera_manager
    bound = component_bounds(mesh)
    return {'game_seconds': float(u.GameplayStatics.get_time_seconds(world)),
            'animation_position': float(mesh.get_position()), 'playing': bool(mesh.is_playing()),
            'animation': path(animation), 'anim_instance_class': path(instance.get_class()) if instance else None,
            'animation_mode': str(mesh.get_animation_mode()),
            'mesh': path(mesh.get_editor_property('skeletal_mesh_asset')),
            'actor_location': vec(boss.get_actor_location()), 'actor_rotation': rotation(boss.get_actor_rotation()),
            'bone_names': bones, 'bone_world_positions': positions, 'render_bounds': bound,
            'bounds_min_z_relative_to_floor': bound['min'][2]-report['arena_floor_bounds']['max'][2],
            'foot_bone_z_relative_to_floor': {name: positions[name][2]-report['arena_floor_bounds']['max'][2]
                                            for name in ['foot_L', 'foot_R'] if name in positions},
            'camera': vec(camera.get_camera_location()), 'camera_rotation': rotation(camera.get_camera_rotation()),
            'fov': float(camera.get_fov_angle())}


def finite_snapshot(sample):
    values = [v for point in sample['bone_world_positions'].values() for v in point]
    values += sample['render_bounds']['origin'] + sample['render_bounds']['extent']
    extents = sample['render_bounds']['extent']
    return all(math.isfinite(v) for v in values) and all(.1 < v < 1500 for v in extents)


def finish(error=None):
    if state['done']:
        return
    state['done'] = True
    if error:
        report['error'] = error
    report['wall_seconds'] = time.monotonic() - state['wall_start']
    report['passed'] = not error and bool(report['checks']) and all(report['checks'].values())
    (OUT / 'receipt.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    finish_editor(callback)


def begin_clip(world, mesh):
    name, _ = CLIPS[state['clip_index']]
    clip = state['clip_assets'][name]
    mesh.play_animation(clip, False)
    mesh.set_play_rate(1.)
    state['clip_start_game'] = float(u.GameplayStatics.get_time_seconds(world))
    state['sample_index'] = 0
    state['clip_samples'] = []
    state['phase'] = 'animate'


def death_snapshot(world, actor, label):
    mesh = actor.get_component_by_class(u.SkeletalMeshComponent)
    instance = mesh.get_anim_instance()
    animation = instance.get_animation_asset() if isinstance(instance, u.AnimSingleNodeInstance) else None
    return {'label': label, 'actor': actor.get_actor_label(),
            'game_seconds': float(u.GameplayStatics.get_time_seconds(world)),
            'health': float(actor.get_editor_property('Health')),
            'state': int(actor.get_editor_property('State')),
            'collision_enabled': bool(actor.get_actor_enable_collision()),
            'animation': path(animation), 'animation_position': float(mesh.get_position()),
            'actor_tick_enabled': bool(actor.is_actor_tick_enabled())}


def dead_on_grounded_clip(sample):
    return sample['health'] <= 0 and sample['state'] == 3 and not sample['collision_enabled'] and \
           sample['animation'] == path(state['clip_assets']['DefeatGrounded']) and sample['animation_position'] > .03


def tick(delta):
    try:
        wall = time.monotonic()
        if wall - state['wall_start'] > 200:
            raise RuntimeError('Parity runtime timeout at ' + state['phase'])
        world = EDITOR.get_game_world()
        if not world:
            return
        pawn = u.GameplayStatics.get_player_pawn(world, 0)
        pc = u.GameplayStatics.get_player_controller(world, 0)
        if not pawn or not pc:
            return
        game = float(u.GameplayStatics.get_time_seconds(world))
        if not state.get('ready'):
            characters = list(u.GameplayStatics.get_all_actors_of_class(world, u.Character))
            bosses = [a for a in characters if a.get_actor_label() == 'TE_MainTeddy']
            minions = [a for a in characters if a.get_actor_label().startswith('TE_Stitchling')]
            spots = [c for c in pawn.get_components_by_class(u.SpotLightComponent) if 'ParityPlayerLight' in c.get_name()]
            if len(bosses) != 1 or len(minions) != 3 or len(spots) != 1:
                if game < 7:
                    return
                raise RuntimeError('Expected one boss, three minions and one saved ParityPlayerLight')
            state['boss'], state['spot'] = bosses[0], spots[0]
            state['minions'] = sorted(minions, key=lambda actor: actor.get_actor_label())
            state['mesh'] = bosses[0].get_component_by_class(u.SkeletalMeshComponent)
            state['pawn_initial_location'], state['pawn_initial_rotation'] = pawn.get_actor_location(), pawn.get_actor_rotation()
            for actor in characters:
                if actor != pawn:
                    actor.set_actor_tick_enabled(False)
                    movement = actor.get_component_by_class(u.CharacterMovementComponent)
                    movement.stop_movement_immediately()
                    movement.disable_movement()
            if pc.get_hud():
                pc.get_hud().set_editor_property('show_hud', False)
            state['subsystem'] = next(a for a in u.ObjectIterator(u.EnhancedInputLocalPlayerSubsystem) if a.get_world() == world)
            state['actions'] = {name: u.load_asset('/Game/Variant_TwinStick/Input/Actions/IA_Action_' + name)
                                for name in ['Move', 'StickAim']}
            state['ready'] = True
            report['world'] = world.get_path_name()
            report['postprocess'] = [{key: str(a.settings.get_editor_property(key)) for key in
                ['auto_exposure_method', 'auto_exposure_bias', 'vignette_intensity', 'bloom_intensity']}
                for a in u.GameplayStatics.get_all_actors_of_class(world, u.PostProcessVolume)]
        boss, mesh, spot = state['boss'], state['mesh'], state['spot']
        if state['phase'] == 'initialize':
            if game < 6:
                return
            sample = light_snapshot(world, pawn, spot, 'before_input')
            report['light_samples'].append(sample)
            check('saved_player_spot_owned_and_attached', sample['owner'] == path(pawn) and
                  sample['parent_owner'] == path(pawn) and sample['intensity'] > 0)
            check('player_spot_does_not_scatter_into_fog', abs(sample['volumetric_scattering_intensity']) < .001)
            check('runtime_camera_fov54', abs(pc.player_camera_manager.get_fov_angle() - 54) < .01)
            check('runtime_boss_uses_v2_skin', path(mesh.get_editor_property('skeletal_mesh_asset')) == report['expected_mesh'])
            state['phase'] = 'light_first'
            state['phase_game'] = game
        elif state['phase'] in ['light_first', 'light_second']:
            first = state['phase'] == 'light_first'
            state['subsystem'].inject_input_vector_for_action(state['actions']['Move'], u.Vector(1 if first else -1, 0, 0), [], [])
            state['subsystem'].inject_input_vector_for_action(state['actions']['StickAim'], u.Vector(0 if first else 1, 1 if first else 0, 0), [], [])
            if game - state['phase_game'] > .4:
                report['light_samples'].append(light_snapshot(world, pawn, spot, state['phase']))
                if first:
                    state['phase'] = 'light_second'; state['phase_game'] = game
                else:
                    samples = report['light_samples']
                    check('player_light_moves_with_player', distance(samples[0]['pawn'], samples[1]['pawn']) > 50 and
                          distance(samples[0]['light'], samples[1]['light']) > 50)
                    check('player_light_rotates_with_aim', abs(delta_angle(samples[1]['pawn_rotation'][1], samples[2]['pawn_rotation'][1])) > 60 and
                          all(abs(delta_angle(s['yaw_relative_to_pawn'], samples[0]['yaw_relative_to_pawn'])) < .1 for s in samples))
                    check('player_light_preserves_attached_offset', all(distance(s['offset_in_pawn_space'], samples[0]['offset_in_pawn_space']) < .1 and
                          distance(s['relative_location'], samples[0]['relative_location']) < .01 for s in samples))
                    check('player_light_parent_remains_owned', all(s['parent'] == samples[0]['parent'] and s['parent_owner'] == path(pawn) for s in samples))
                    movement = pawn.get_component_by_class(u.CharacterMovementComponent)
                    movement.stop_movement_immediately(); movement.disable_movement()
                    pawn.set_actor_tick_enabled(False)
                    pawn.set_actor_location(state['pawn_initial_location'], False, False)
                    aim = u.MathLibrary.find_look_at_rotation(pawn.get_actor_location(), boss.get_actor_location())
                    pawn.set_actor_rotation(u.Rotator(pitch=0, yaw=aim.yaw, roll=0), False)
                    state['phase'] = 'settle'; state['phase_game'] = game
                    u.AutomationLibrary.finish_loading_before_screenshot()
        elif state['phase'] == 'settle':
            if game - state['phase_game'] > 1.2:
                begin_clip(world, mesh)
        elif state['phase'] == 'resume_for_clip':
            # The first game tick after a held screenshot can have a clamped
            # 0.4 s delta. Drain that tick before starting a short clip such as
            # Hit, otherwise its early and middle poses are skipped.
            if game - state['resume_game'] > .05:
                begin_clip(world, mesh)
        elif state['phase'] == 'animate':
            name, fraction = CLIPS[state['clip_index']]
            length = float(state['clip_assets'][name].get_play_length())
            targets = [.05, .25, fraction]
            position = float(mesh.get_position())
            if position >= length * targets[state['sample_index']]:
                sample = mesh_snapshot(world, mesh, boss, pc)
                state['clip_samples'].append(sample)
                state['sample_index'] += 1
                if state['sample_index'] == 3:
                    samples = state['clip_samples']
                    displacement = max(distance(samples[0]['bone_world_positions'][bone], samples[-1]['bone_world_positions'][bone])
                                       for bone in EXPECTED_BONES if bone in samples[0]['bone_world_positions'])
                    row = {'clip': name, 'length_seconds': length, 'samples': samples,
                           'max_bone_displacement_cm': displacement,
                           'target_capture_fraction': fraction}
                    report['animation_samples'].append(row)
                    check(name + '_original_clip_identity_and_progression', all(s['animation'] == path(state['clip_assets'][name]) for s in samples) and
                          samples[0]['animation_position'] < samples[1]['animation_position'] < samples[2]['animation_position'])
                    check(name + '_original_imported_bone_hierarchy_and_pose_motion',
                          all(s['bone_names'] == EXPECTED_IMPORTED_BONES for s in samples) and displacement > .005)
                    check(name + '_finite_bones_and_bounded_skin', all(finite_snapshot(s) and s['mesh'] == report['expected_mesh'] for s in samples))
                    u.GameplayStatics.set_game_paused(world, True)
                    state['held'] = mesh_snapshot(world, mesh, boss, pc)
                    state['held_wall'], state['held_samples'] = wall, 0
                    state['phase'] = 'hold'
            elif game - state['clip_start_game'] > length + 5:
                raise RuntimeError('Clip did not advance to its capture pose: ' + name)
        elif state['phase'] in ['hold', 'capture']:
            sample = mesh_snapshot(world, mesh, boss, pc)
            for key in ['animation_position', 'bone_world_positions', 'actor_location', 'camera', 'camera_rotation', 'fov']:
                if sample[key] != state['held'][key]:
                    raise RuntimeError('Held animation capture drift: ' + key)
            state['held_samples'] += 1
            if state['phase'] == 'hold' and wall - state['held_wall'] > .6:
                name = CLIPS[state['clip_index']][0]
                state['image'] = OUT / f'{state["clip_index"]+1:02}-{name}.png'
                if state['image'].exists():
                    raise RuntimeError('Refusing stale animation image')
                u.SystemLibrary.execute_console_command(world, 'HighResShot 1280x720 filename="' + state['image'].as_posix() + '"', pc)
                state['capture_wall'] = wall
                state['phase'] = 'capture'
            elif state['phase'] == 'capture':
                if wall - state['capture_wall'] > 25:
                    raise RuntimeError('Animation PNG completion timeout')
                if not state['image'].is_file():
                    return
                try:
                    validation = decode_png(state['image'], expected=(1280, 720))
                except Exception:
                    return
                validation.pop('chunks', None)
                report['captures'].append({'clip': CLIPS[state['clip_index']][0], 'path': str(state['image']),
                                           'held_state': state['held'], 'held_samples': state['held_samples'],
                                           'validation': validation, 'kind': 'staged-animation-on-saved-gameplay-camera'})
                state['clip_index'] += 1
                if state['clip_index'] == len(CLIPS):
                    check('six_original_plus_grounded_pose_images_fully_decoded', len(report['captures']) == 7 and
                          {c['clip'] for c in report['captures']} == {name for name, _ in CLIPS})
                    u.GameplayStatics.set_game_paused(world, False)
                    state['phase'] = 'death_prepare'
                    state['resume_game'] = game
                else:
                    u.GameplayStatics.set_game_paused(world, False)
                    state['phase'] = 'resume_for_clip'
                    state['resume_game'] = game
        elif state['phase'] == 'death_prepare':
            if game - state['resume_game'] <= .05:
                return
            direct = state['minions'][0]
            report['death_events'].append(death_snapshot(world, direct, 'direct_minion_before_damage'))
            check('death_fixture_starts_with_healthy_creatures', boss.get_editor_property('Health') > 0 and
                  all(a.get_editor_property('Health') > 0 for a in state['minions']))
            damage = float(direct.get_editor_property('Health')) + 1.
            returned = u.GameplayStatics.apply_damage(direct, damage, pc, pawn, u.DamageType)
            report['death_events'].append({'event': 'ApplyDamage direct minion', 'amount': damage,
                                           'returned_damage': float(returned), 'actor': direct.get_actor_label()})
            state['phase'] = 'death_direct_minion'; state['phase_game'] = game
        elif state['phase'] == 'death_direct_minion':
            if game - state['phase_game'] < .25:
                return
            direct = death_snapshot(world, state['minions'][0], 'direct_minion_after_damage')
            report['death_events'].append(direct)
            check('direct_minion_damage_executes_saved_grounded_death', dead_on_grounded_clip(direct) and boss.get_editor_property('Health') > 0)
            report['death_events'].append(death_snapshot(world, boss, 'boss_before_damage'))
            for actor in state['minions'][1:]:
                actor.set_actor_tick_enabled(True)
            damage = float(boss.get_editor_property('Health')) + 1.
            returned = u.GameplayStatics.apply_damage(boss, damage, pc, pawn, u.DamageType)
            report['death_events'].append({'event': 'ApplyDamage boss', 'amount': damage,
                                           'returned_damage': float(returned), 'actor': boss.get_actor_label()})
            state['phase'] = 'death_boss_and_cascade'; state['phase_game'] = game
        elif state['phase'] == 'death_boss_and_cascade':
            if game - state['phase_game'] < .3:
                return
            boss_row = death_snapshot(world, boss, 'boss_after_lethal_damage')
            cascade = [death_snapshot(world, actor, 'minion_saved_boss_death_cascade') for actor in state['minions'][1:]]
            report['death_events'].extend([boss_row, *cascade])
            check('boss_damage_executes_saved_grounded_death', dead_on_grounded_clip(boss_row))
            check('both_surviving_minions_execute_saved_boss_death_cascade', len(cascade) == 2 and
                  all(dead_on_grounded_clip(row) and not row['actor_tick_enabled'] for row in cascade))
            state['phase'] = 'death_finish_animation'
        elif state['phase'] == 'death_finish_animation':
            if game - state['phase_game'] < state['clip_assets']['DefeatGrounded'].get_play_length() + .2:
                return
            report['runtime_death_final_poses'] = [
                {'actor': actor.get_actor_label(),
                 'state': death_snapshot(world, actor, 'settled_saved_death'),
                 'pose': mesh_snapshot(world, actor.get_component_by_class(u.SkeletalMeshComponent), actor, pc)}
                for actor in [boss, *state['minions']]]
            check('all_four_runtime_deaths_reach_grounded_clip_end', all(
                dead_on_grounded_clip(row['state']) and
                abs(row['state']['animation_position'] - state['clip_assets']['DefeatGrounded'].get_play_length()) < .04
                for row in report['runtime_death_final_poses']))
            u.GameplayStatics.set_game_paused(world, True)
            state['death_image'] = OUT / '08-saved-death-routes.png'
            if state['death_image'].exists():
                raise RuntimeError('Refusing stale runtime-death image')
            state['phase'] = 'death_capture_wait'; state['death_capture_start'] = wall
        elif state['phase'] == 'death_capture_wait':
            if wall - state['death_capture_start'] < .6:
                return
            u.SystemLibrary.execute_console_command(world, 'HighResShot 1280x720 filename="' + state['death_image'].as_posix() + '"', pc)
            state['phase'] = 'death_capture'; state['death_capture_start'] = wall
        elif state['phase'] == 'death_capture':
            if wall - state['death_capture_start'] > 25:
                raise RuntimeError('Saved death-routes PNG timeout')
            if not state['death_image'].is_file():
                return
            try:
                validation = decode_png(state['death_image'], expected=(1280, 720))
            except Exception:
                return
            validation.pop('chunks', None)
            report['captures'].append({'clip': 'SavedDeathRoutes', 'path': str(state['death_image']),
                                       'validation': validation, 'kind': 'actual-saved-damage-and-cascade-events'})
            check('saved_death_route_image_fully_decoded', len(report['captures']) == 8)
            finish()
    except Exception:
        finish(traceback.format_exc())


try:
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    if not LEVELS.load_level(MAP):
        raise RuntimeError('Cannot load saved encounter map')
    saved_audit()
    LEVELS.editor_request_begin_play()
    callback = u.register_slate_post_tick_callback(tick)
except Exception:
    finish(traceback.format_exc())
