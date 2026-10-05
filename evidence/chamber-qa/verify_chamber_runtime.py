"""Independent saved chamber/cutaway audit; root runs with run_encounter_test.py.

No asset or map saves. Only the PIE camera/actors are staged. Existing 28 room
checks remain separate; this audit covers new chamber decoration and the native
camera-dependent opposite wall. Actual screenshots still require visual review.
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from finish_editor import finish_editor

OUT = Path(os.environ['TEDDY_TEST_DIR'])
MAP = '/Game/Maps/TeddyEncounter'
NAMESPACE = '/Game/TeddyEncounter/Chamber/'
PREFIX = 'TE_Chamber_'
CUTAWAY_LABEL = PREFIX + 'FrontCutaway'
CUTAWAY_CLASS = NAMESPACE + 'Blueprints/BP_ChamberCutaway.BP_ChamberCutaway_C'
BEACON_LABELS = {PREFIX + 'BulkheadBeacon' + side + part for side in ('L', 'R') for part in ('Housing', 'Lens')}
ENGINE_CUBE = '/Engine/BasicShapes/Cube.Cube'
PILASTER_COMPONENTS = {'FrontPier_' + str(index) for index in range(5)}
REUSED_ROOM_PILASTER = '/Game/TeddyEncounter/Room/Meshes/SM_RoomPilaster.SM_RoomPilaster'
REUSED_CUTAWAY_MESHES = {
    '/Game/TeddyEncounter/Parity/RoomExtension/Meshes/SM_ShellWallBay.SM_ShellWallBay',
    '/Game/TeddyEncounter/Parity/RoomExtension/Meshes/SM_ShellWallBayNarrow.SM_ShellWallBayNarrow',
    ENGINE_CUBE,
}
levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
result = {
    'passed': False, 'map': MAP, 'engine': u.SystemLibrary.get_engine_version(),
    'independent_qa': True, 'asset_writes': False, 'physical_device_verified': False,
    'checks': {}, 'saved_actors': [], 'runtime_cases': [],
    'method': 'Independent saved-world component readback followed by frame-driven PIE camera changes. Native chamber Blueprint ticks are never disabled and visibility is never forced.',
    'limitations': ['Conservative component boxes establish placement, not exact mesh contact or visual parity.',
                   'Architectural camera staging and held subjects are test-only and discarded with PIE.',
                   'The old full-room/input suites remain separate. This narrow audit does not duplicate or replace them.',
                   'Passing native cutaway state transitions does not establish that the pop/cutaway is artistically acceptable; inspect architectural and ordinary gameplay captures.'],
}
state = {'start': time.monotonic(), 'phase': 'wait', 'done': False}
handle = None


def vec(v):
    return [float(v.x), float(v.y), float(v.z)]


def check(name, value):
    result['checks'][name] = bool(value)


def tagset(actor):
    return {str(tag) for tag in actor.tags}


def hidden(actor):
    # Reflected Actor.bHidden: inspect actor-level state in addition to components.
    return bool(actor.get_editor_property('hidden'))


def identity(actor):
    return {'label': actor.get_actor_label(), 'path': actor.get_path_name(),
            'class': actor.get_class().get_path_name(), 'tags': sorted(tagset(actor))}


def bounds(component):
    origin, extent, _ = u.SystemLibrary.get_component_bounds(component)
    lo, hi = vec(origin - extent), vec(origin + extent)
    finite = all(math.isfinite(v) for v in lo + hi) and all(lo[a] <= hi[a] for a in range(3))
    overlap = (lo[0] < 1480 - .05 and hi[0] > -1400 + .05 and
               lo[1] < 1500 - .05 and hi[1] > -1500 + .05)
    return {'min': lo, 'max': hi, 'finite_ordered': finite, 'overlaps_open_combat_xy': overlap}


def camera_snapshot(pc):
    camera = pc.player_camera_manager
    rotation = camera.get_camera_rotation()
    return {'location': vec(camera.get_camera_location()),
            'rotation': [rotation.pitch, rotation.yaw, rotation.roll], 'fov': camera.get_fov_angle()}


def finish(error=None):
    if state['done']:
        return
    state['done'] = True
    if error:
        result['error'] = error
    result['passed'] = not error and bool(result['checks']) and all(result['checks'].values())
    result['wall_seconds'] = time.monotonic() - state['start']
    OUT.mkdir(parents=True, exist_ok=True)
    detail_path = OUT / 'details.json'
    detail_path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    # The standard runner prints receipt keys. Keep complete independent readback
    # in a hashed companion instead of flooding the console with 60 repeated arrays.
    summary = {key: value for key, value in result.items() if key not in
               {'saved_actors', 'new_geometry_placement_audit', 'runtime_cases', 'ordinary_initial'}}
    summary['details'] = {'path': str(detail_path), 'sha256': hashlib.sha256(detail_path.read_bytes()).hexdigest(),
                          'saved_actor_count': len(result['saved_actors']),
                          'placement_component_count': len(result.get('new_geometry_placement_audit', [])),
                          'runtime_case_count': len(result['runtime_cases'])}
    (OUT / 'receipt.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    finish_editor(handle)


def saved_audit():
    settings_path = ROOT / 'study/chamber-settings.json'
    settings_bytes = settings_path.read_bytes()
    settings = json.loads(settings_bytes)
    state['threshold'] = float(settings['cutaway_hide_below_camera_x'])
    result['declared_cutaway_threshold_cm'] = state['threshold']
    result['settings_sha256'] = hashlib.sha256(settings_bytes).hexdigest()
    run_meta = json.loads((ROOT / 'evidence/chamber/current-run.json').read_text(encoding='utf-8-sig'))
    run_dir = (ROOT / Path(run_meta['out'])).resolve()
    assert run_dir.is_relative_to(ROOT)
    manifest_path = run_dir / 'chamber-kit-reviewed.json'
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    assert manifest['owner'] == 'teddy-chamber-parity-20261005'
    result['source_manifest_sha256'] = hashlib.sha256(manifest_bytes).hexdigest()
    result['frozen_source_manifest'] = str(manifest_path)
    floor_manifest_path = run_dir / 'chamber-floor-v2-reviewed.json'
    floor_manifest_bytes = floor_manifest_path.read_bytes()
    floor_manifest = json.loads(floor_manifest_bytes)
    assert floor_manifest['owner'] == 'teddy-chamber-floor-normals-v2-20261005'
    result['frozen_floor_manifest'] = str(floor_manifest_path)
    result['floor_manifest_sha256'] = hashlib.sha256(floor_manifest_bytes).hexdigest()
    expected_floor_placements = {PREFIX + 'Floor_' + item['label']: item for item in floor_manifest['recommended_placements']}
    expected_floor = {label: item['mesh'] for label, item in expected_floor_placements.items()}
    expected_floor_meshes = {item['name'] for item in floor_manifest['assets']}
    assert expected_floor_meshes == {'SM_ChamberFractureFork_A_V2', 'SM_ChamberFractureBank_B_V2', 'SM_ChamberFractureDrift_C_V2'}
    assert len(expected_floor) == len(floor_manifest['recommended_placements']) == 5
    result['expected_floor_placement_count'] = len(expected_floor)
    result['expected_floor_unique_mesh_count'] = len(expected_floor_meshes)
    slab_manifest_path = run_dir / 'chamber-slabs-v2-reviewed.json'
    slab_manifest_bytes = slab_manifest_path.read_bytes()
    slab_manifest = json.loads(slab_manifest_bytes)
    assert slab_manifest['owner'] == 'teddy-chamber-slabs-normals-v2-20261005'
    result['frozen_slab_manifest'] = str(slab_manifest_path)
    result['slab_manifest_sha256'] = hashlib.sha256(slab_manifest_bytes).hexdigest()
    expected_slabs = {PREFIX + 'Slabs_' + item['label']: item for item in slab_manifest['recommended_placements']}
    expected_slab_meshes = {NAMESPACE + 'Floor/' + item['name'] + '.' + item['name'] for item in slab_manifest['assets']}
    assert len(expected_slabs) == len(slab_manifest['recommended_placements']) == 4
    assert expected_slab_meshes == {NAMESPACE + 'Floor/SM_ChamberSparseSlabs_V2.SM_ChamberSparseSlabs_V2'}
    result['expected_slab_placement_count'] = len(expected_slabs)
    result['expected_slab_unique_mesh_count'] = len(expected_slab_meshes)
    crust_manifest_path = run_dir / 'chamber-crust-v2-reviewed.json'
    crust_manifest_bytes = crust_manifest_path.read_bytes()
    crust_manifest = json.loads(crust_manifest_bytes)
    assert crust_manifest['owner'] == 'teddy-chamber-crust-normals-v2-20261005'
    result['frozen_crust_manifest'] = str(crust_manifest_path)
    result['crust_manifest_sha256'] = hashlib.sha256(crust_manifest_bytes).hexdigest()
    expected_crust = {PREFIX + 'Crust_' + item['label']: item for item in crust_manifest['recommended_placements']}
    expected_crust_names = {item['name'] for item in crust_manifest['assets']}
    assert expected_crust_names == {'SM_ChamberCrustBank_A_V2', 'SM_ChamberCrustBank_B_V2'}
    expected_crust_meshes = {NAMESPACE + 'Crust/' + name + '.' + name for name in expected_crust_names}
    assert len(expected_crust) == len(crust_manifest['recommended_placements']) == 5
    result['expected_crust_placement_count'] = len(expected_crust)
    result['expected_crust_unique_mesh_count'] = len(expected_crust_meshes)
    expected_static = {PREFIX + item['label']: item['mesh'] for item in manifest['recommended_placements']
                       if not item['label'].startswith('ReverseDoor')}
    expected_doors = {item['label']: item['mesh'] for item in manifest['recommended_placements']
                      if item['label'].startswith('ReverseDoor')}
    loaded = list(actors.get_all_level_actors())
    for actor in loaded:
        components = list(actor.get_components_by_class(u.StaticMeshComponent))
        is_owned = actor.get_actor_label().startswith(PREFIX) or 'ChamberOwned' in tagset(actor)
        has_owned_mesh = any(c.static_mesh and c.static_mesh.get_path_name().startswith(NAMESPACE) for c in components)
        if not (is_owned or has_owned_mesh):
            continue
        row = identity(actor)
        rotation = actor.get_actor_rotation()
        row.update(actor_hidden=hidden(actor), actor_collision_enabled=bool(actor.get_actor_enable_collision()),
                   location=vec(actor.get_actor_location()), rotation=[rotation.pitch, rotation.yaw, rotation.roll],
                   scale=vec(actor.get_actor_scale3d()), meshes=[], primitive_components=[], lights=[])
        for component in actor.get_components_by_class(u.LightComponent):
            owner = component.get_owner()
            row['lights'].append({'name': component.get_name(), 'class': component.get_class().get_path_name(),
                'is_spot_light': isinstance(component, u.SpotLightComponent), 'owner_path': owner.get_path_name(),
                'owner_is_this_actor': owner == actor, 'owner_hidden': hidden(owner),
                'visible': bool(component.get_editor_property('visible')),
                'hidden_in_game': bool(component.get_editor_property('hidden_in_game'))})
        for component in actor.get_components_by_class(u.PrimitiveComponent):
            row['primitive_components'].append({'name': component.get_name(),
                'collision_profile': str(component.get_collision_profile_name()),
                'no_collision': component.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION,
                'visible': bool(component.get_editor_property('visible')),
                'hidden_in_game': bool(component.get_editor_property('hidden_in_game'))})
        for component in components:
            if not component.static_mesh:
                continue
            row['meshes'].append({'name': component.get_name(), 'mesh': component.static_mesh.get_path_name(),
                'bounds': bounds(component), 'materials': [component.get_material(i).get_path_name() if component.get_material(i) else None for i in range(component.get_num_materials())]})
        result['saved_actors'].append(row)
    rows = result['saved_actors']
    geometry = [row for row in rows if row['meshes']]
    by_label = {row['label']: row for row in rows}
    cutaways = [row for row in geometry if row['label'] == CUTAWAY_LABEL or 'ChamberCutawayOwned' in row['tags']]
    check('new_chamber_geometry_present_and_labels_unique', bool(geometry) and len({row['label'] for row in rows}) == len(rows))
    check('new_geometry_ownership_explicit', bool(geometry) and all(row['label'].startswith(PREFIX) and {'ChamberOwned', 'TeddyEncounterOwned'} <= set(row['tags']) for row in geometry))
    check('exactly_one_saved_native_cutaway_actor', len(cutaways) == 1 and cutaways[0]['label'] == CUTAWAY_LABEL and cutaways[0]['class'] == CUTAWAY_CLASS)
    check('new_geometry_actual_actor_and_component_collision_disabled', bool(geometry) and all(not row['actor_collision_enabled'] and row['primitive_components'] and all(c['no_collision'] and c['collision_profile'] == 'NoCollision' for c in row['primitive_components']) for row in geometry))
    check('source_kit_static_landmarks_present_once', all(label in by_label and len(by_label[label]['meshes']) == 1 and by_label[label]['meshes'][0]['mesh'] == NAMESPACE + 'Meshes/' + mesh + '.' + mesh for label, mesh in expected_static.items()))
    all_meshes = [m for row in geometry for m in row['meshes']]
    check('exactly_one_new_bulkhead_body_and_one_wheel', all(sum(m['mesh'] == NAMESPACE + 'Meshes/' + name + '.' + name for m in all_meshes) == 1 for name in ['SM_ChamberBulkhead', 'SM_ChamberBulkheadWheel']))
    cutaway_meshes = cutaways[0]['meshes'] if len(cutaways) == 1 else []
    check('saved_cutaway_has_exact_19_mesh_components', len(cutaway_meshes) == 19)
    check('cutaway_contains_both_actual_service_door_meshes', len(expected_doors) == 2 and all(sum(m['name'] == name and m['mesh'] == NAMESPACE + 'Meshes/' + mesh + '.' + mesh for m in cutaway_meshes) == 1 for name, mesh in expected_doors.items()))
    check('cutaway_includes_wall_panels_piers_header_and_footing', all(any(m['name'].startswith(prefix) for m in cutaway_meshes) for prefix in ['FrontPanel_', 'FrontEnd_', 'FrontPier_', 'FrontHeader', 'FrontFooting']))
    check('five_exact_cutaway_piers_use_retained_room_pilaster', all(sum(m['name'] == name and m['mesh'] == REUSED_ROOM_PILASTER for m in cutaway_meshes) == 1 for name in PILASTER_COMPONENTS))
    cutaway_lights = cutaways[0]['lights'] if len(cutaways) == 1 else []
    check('saved_reverse_overhead_spot_is_owned_by_cutaway', len(cutaway_lights) == 1 and cutaway_lights[0]['name'] == 'ReverseOverheadPool' and cutaway_lights[0]['is_spot_light'] and cutaway_lights[0]['owner_is_this_actor'])
    check('four_owned_rear_beacon_shapes_are_exact_allowlisted_cubes', all(label in by_label and len(by_label[label]['meshes']) == 1 and by_label[label]['meshes'][0]['mesh'] == ENGINE_CUBE for label in BEACON_LABELS))
    check('new_static_mesh_sources_owned_or_explicitly_allowlisted', all(m['mesh'].startswith(NAMESPACE) or (row['label'] == CUTAWAY_LABEL and m['mesh'] in REUSED_CUTAWAY_MESHES) or (row['label'] == CUTAWAY_LABEL and m['name'] in PILASTER_COMPONENTS and m['mesh'] == REUSED_ROOM_PILASTER) or (row['label'] in BEACON_LABELS and m['mesh'] == ENGINE_CUBE) for row in geometry for m in row['meshes']))
    # Fields and sparse slabs share an asset folder but are independently owned
    # groups. Unknown floor meshes still enter the strict field audit; slab mesh
    # reuse anywhere else enters the slab audit and fails its exact label check.
    floor_rows = [row for row in geometry if 'ChamberFloorOwned' in row['tags'] or row['label'].startswith(PREFIX + 'Floor_') or any(m['mesh'].startswith(NAMESPACE + 'Floor/') and m['mesh'] not in expected_slab_meshes for m in row['meshes'])]
    actual_floor_by_label = {row['label']: row for row in floor_rows}
    floor_identity_ok = (set(actual_floor_by_label) == set(expected_floor) and all(
        'ChamberFloorOwned' in row['tags'] and len(row['meshes']) == 1 and
        row['meshes'][0]['mesh'] == NAMESPACE + 'Floor/' + expected_floor[row['label']] + '.' + expected_floor[row['label']]
        for row in floor_rows))
    check('saved_owned_floor_placements_and_unique_meshes_match_frozen_manifest', floor_identity_ok and len(floor_rows) == len(expected_floor) and len({m['mesh'] for row in floor_rows for m in row['meshes']}) == len(expected_floor_meshes))
    check('saved_floor_transforms_match_frozen_placements_without_vertical_scale', floor_identity_ok and all(
        math.dist(row['location'], expected_floor_placements[row['label']]['location_cm']) < .1 and
        math.dist(row['scale'], expected_floor_placements[row['label']]['scale']) < .0001 and abs(row['scale'][2] - 1.) < .0001 and
        abs(row['rotation'][0]) < .01 and abs(row['rotation'][2]) < .01 and
        abs((row['rotation'][1] - expected_floor_placements[row['label']]['yaw'] + 180) % 360 - 180) < .01
        for row in floor_rows))
    slab_rows = [row for row in geometry if 'ChamberSlabsOwned' in row['tags'] or row['label'].startswith(PREFIX + 'Slabs_') or any(m['mesh'] in expected_slab_meshes for m in row['meshes'])]
    actual_slabs_by_label = {row['label']: row for row in slab_rows}
    slab_identity_ok = (set(actual_slabs_by_label) == set(expected_slabs) and all(
        'ChamberSlabsOwned' in row['tags'] and len(row['meshes']) == 1 and
        row['meshes'][0]['mesh'] == NAMESPACE + 'Floor/' + expected_slabs[row['label']]['mesh'] + '.' + expected_slabs[row['label']]['mesh']
        for row in slab_rows))
    check('saved_four_sparse_slab_groups_match_separate_frozen_manifest', slab_identity_ok and
          len(slab_rows) == len(expected_slabs) and {m['mesh'] for row in slab_rows for m in row['meshes']} == expected_slab_meshes)
    check('saved_sparse_slab_transforms_match_frozen_placements_without_vertical_scale', slab_identity_ok and all(
        math.dist(row['location'], expected_slabs[row['label']]['location_cm']) < .1 and
        math.dist(row['scale'], expected_slabs[row['label']]['scale']) < .0001 and abs(row['scale'][2] - 1.) < .0001 and
        abs(row['rotation'][0]) < .01 and abs(row['rotation'][2]) < .01 and
        abs((row['rotation'][1] - expected_slabs[row['label']]['yaw'] + 180) % 360 - 180) < .01
        for row in slab_rows))
    check('saved_sparse_slab_bounds_remain_grounded_low_relief', bool(slab_rows) and all(
        m['bounds']['finite_ordered'] and m['bounds']['min'][2] >= -5.05 and m['bounds']['max'][2] <= 1.05
        for row in slab_rows for m in row['meshes']))
    crust_rows = [row for row in geometry if 'ChamberCrustOwned' in row['tags'] or row['label'].startswith(PREFIX + 'Crust_') or any(m['mesh'].startswith(NAMESPACE + 'Crust/') for m in row['meshes'])]
    actual_crust_by_label = {row['label']: row for row in crust_rows}
    crust_identity_ok = (set(actual_crust_by_label) == set(expected_crust) and all(
        'ChamberCrustOwned' in row['tags'] and len(row['meshes']) == 1 and
        row['meshes'][0]['mesh'] == NAMESPACE + 'Crust/' + expected_crust[row['label']]['mesh'] + '.' + expected_crust[row['label']]['mesh']
        for row in crust_rows))
    check('saved_five_crust_banks_match_separate_frozen_manifest', crust_identity_ok and
          len(crust_rows) == len(expected_crust) and {m['mesh'] for row in crust_rows for m in row['meshes']} == expected_crust_meshes)
    check('saved_crust_transforms_match_frozen_placements_without_vertical_scale', crust_identity_ok and all(
        math.dist(row['location'], expected_crust[row['label']]['location_cm']) < .1 and
        math.dist(row['scale'], expected_crust[row['label']]['scale']) < .0001 and abs(row['scale'][2] - 1.) < .0001 and
        abs(row['rotation'][0]) < .01 and abs(row['rotation'][2]) < .01 and
        abs((row['rotation'][1] - expected_crust[row['label']]['yaw'] + 180) % 360 - 180) < .01
        for row in crust_rows))
    check('saved_crust_bounds_remain_grounded_low_relief', bool(crust_rows) and all(
        m['bounds']['finite_ordered'] and m['bounds']['min'][2] >= -5.05 and m['bounds']['max'][2] <= 1.05
        for row in crust_rows for m in row['meshes']))
    check('fine_floor_slab_and_crust_overlays_preserved_and_hidden', floor_identity_ok and slab_identity_ok and crust_identity_ok and
          all(row['actor_hidden'] for row in floor_rows + slab_rows + crust_rows) and
          len(floor_rows) == 5 and len(slab_rows) == 4 and len(crust_rows) == 5)
    morph_manifest_path = run_dir / 'chamber-floor-morphology-reviewed.json'
    morph_manifest_bytes = morph_manifest_path.read_bytes()
    morph_manifest = json.loads(morph_manifest_bytes)
    assert morph_manifest['owner'] == 'teddy-chamber-floor-morphology-v3-20261005'
    result['frozen_morphology_manifest'] = str(morph_manifest_path)
    result['morphology_manifest_sha256'] = hashlib.sha256(morph_manifest_bytes).hexdigest()
    expected_morph = {PREFIX + 'Morph_' + item['label']: item for item in morph_manifest['recommended_placements']}
    expected_morph_meshes = {NAMESPACE + 'FloorMorphology/' + item['name'] + '.' + item['name'] for item in morph_manifest['assets']}
    assert len(expected_morph) == len(morph_manifest['recommended_placements']) == 1
    assert expected_morph_meshes == {NAMESPACE + 'FloorMorphology/SM_ChamberFractureMorph_Main.SM_ChamberFractureMorph_Main'}
    morph_rows = [row for row in geometry if 'ChamberMorphologyOwned' in row['tags'] or row['label'].startswith(PREFIX + 'Morph_') or any(m['mesh'].startswith(NAMESPACE + 'FloorMorphology/') for m in row['meshes'])]
    actual_morph = {row['label']: row for row in morph_rows}
    morph_identity_ok = (set(actual_morph) == set(expected_morph) and all(
        'ChamberMorphologyOwned' in row['tags'] and not row['actor_hidden'] and len(row['meshes']) == 1 and
        row['meshes'][0]['mesh'] == NAMESPACE + 'FloorMorphology/' + expected_morph[row['label']]['mesh'] + '.' + expected_morph[row['label']]['mesh']
        for row in morph_rows))
    check('saved_floor_morphology_matches_reviewed_manifest', morph_identity_ok and
          len(morph_rows) == 1 and {m['mesh'] for row in morph_rows for m in row['meshes']} == expected_morph_meshes)
    check('saved_floor_morphology_transform_is_grounded_without_vertical_scale', morph_identity_ok and all(
        math.dist(row['location'], expected_morph[row['label']]['location_cm']) < .1 and
        math.dist(row['scale'], expected_morph[row['label']]['scale']) < .0001 and abs(row['scale'][2] - 1.) < .0001 and
        abs(row['rotation'][0]) < .01 and abs(row['rotation'][2]) < .01 and
        abs((row['rotation'][1] - expected_morph[row['label']]['yaw'] + 180) % 360 - 180) < .01 and
        all(m['bounds']['finite_ordered'] and m['bounds']['min'][2] >= -5.05 and m['bounds']['max'][2] <= 6.05 for m in row['meshes'])
        for row in morph_rows))
    placement_rows = []
    for row in geometry:
        for mesh in row['meshes']:
            bound = mesh['bounds']
            # New low floor relief may occupy combat XY, but wall/prop geometry may not.
            is_floor = '/Floor/' in mesh['mesh'] or mesh['mesh'] in expected_crust_meshes or mesh['mesh'].rsplit('/', 1)[-1].startswith(('SM_ChamberFloor', 'SM_ChamberFracture'))
            passed = bound['finite_ordered'] and (bound['max'][2] <= 6.05 if is_floor else not bound['overlaps_open_combat_xy'] and bound['max'][2] <= 700.05)
            placement_rows.append({'actor': row['label'], 'component': mesh['name'], 'low_floor_relief': is_floor, 'bounds': bound, 'passed': passed})
    result['new_geometry_placement_audit'] = placement_rows
    check('new_geometry_world_bounds_keep_combat_space_open', bool(placement_rows) and all(row['passed'] for row in placement_rows))
    result['bounds_method'] = {'combat_open_xy_cm': [[-1400, -1500], [1480, 1500]], 'floor_maximum_world_z_cm': 6, 'wall_and_prop_maximum_world_z_cm': 700, 'tolerance_cm': .05, 'source': 'Actual loaded component world bounds, not importer pass flags or manifest bounds.'}


def stage_case(world, pc):
    case = state['cases'][state['case_index']]
    director = state['director']
    # Reacquire the live component for every stage. Editor-property writes can
    # reconstruct components; a cached reference must not become the test camera.
    camera_component = director.get_component_by_class(u.CameraComponent)
    if case['kind'] == 'ordinary-return':
        director.set_actor_location(state['director_original_location'], False, False)
        director.set_actor_rotation(state['director_original_rotation'], False)
        camera_component.set_field_of_view(state['director_original_fov'])
        director.set_actor_tick_enabled(True)
    else:
        director.set_actor_tick_enabled(False)
        location = u.Vector(*case['location'])
        director.set_actor_location(location, False, False)
        director.set_actor_rotation(u.MathLibrary.find_look_at_rotation(location, u.Vector(*case['target'])), False)
        camera_component.set_field_of_view(case['fov'])
    state['settle_game'] = u.GameplayStatics.get_time_seconds(world)
    state['samples'] = []
    state['phase'] = 'settle'


def cutaway_sample(pc):
    actor = state['cutaway']
    camera = camera_snapshot(pc)
    camera_component = state['director'].get_component_by_class(u.CameraComponent)
    components = list(actor.get_components_by_class(u.PrimitiveComponent))
    lights = [c for c in actor.get_components_by_class(u.SpotLightComponent) if c.get_name() == 'ReverseOverheadPool']
    light_state = {'present_once': len(lights) == 1}
    if len(lights) == 1:
        owner = lights[0].get_owner()
        light_state.update(owner_is_cutaway=owner == actor, owner_hidden=hidden(owner),
                           visible=bool(lights[0].get_editor_property('visible')),
                           hidden_in_game=bool(lights[0].get_editor_property('hidden_in_game')))
    return {'camera': camera, 'camera_component': {'path': camera_component.get_path_name(),
            'field_of_view': float(camera_component.get_editor_property('field_of_view'))},
            'actor_hidden': hidden(actor),
            'reverse_overhead_light': light_state,
            'expected_hidden': camera['location'][0] < state['threshold'],
            'actor_tick_enabled': bool(actor.is_actor_tick_enabled()),
            'actor_collision_enabled': bool(actor.get_actor_enable_collision()),
            'all_component_collision_disabled': all(c.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION for c in components),
            'component_visibility': [{'name': c.get_name(), 'visible': bool(c.get_editor_property('visible')), 'hidden_in_game': bool(c.get_editor_property('hidden_in_game'))} for c in components]}


def tick(delta):
    try:
        if time.monotonic() - state['start'] > 240:
            raise RuntimeError('Chamber QA timeout')
        world = editor.get_game_world()
        if not world:
            return
        pc = u.GameplayStatics.get_player_controller(world, 0)
        player = u.GameplayStatics.get_player_pawn(world, 0)
        if not pc or not player:
            return
        game_time = u.GameplayStatics.get_time_seconds(world)
        if not state.get('initialized'):
            live = list(u.GameplayStatics.get_all_actors_of_class(world, u.Actor))
            directors = [a for a in live if a.get_actor_label() == 'TE_CombatView']
            cutaways = [a for a in live if a.get_actor_label() == CUTAWAY_LABEL]
            characters = list(u.GameplayStatics.get_all_actors_of_class(world, u.Character))
            ready = len(directors) == len(cutaways) == 1 and len(characters) == 5 and player in characters
            if not ready:
                if game_time < 7:
                    return
                raise RuntimeError('Saved chamber actor set was not ready after seven game seconds.')
            state['director'], state['cutaway'] = directors[0], cutaways[0]
            state['camera_component'] = state['director'].get_component_by_class(u.CameraComponent)
            for actor in characters:
                actor.set_actor_tick_enabled(False)
                movement = actor.get_component_by_class(u.CharacterMovementComponent)
                if movement:
                    movement.stop_movement_immediately()
                    movement.disable_movement()
            state['initialized'] = True
        if state['phase'] == 'wait':
            if game_time < 7:
                return
            state['director_original_location'] = state['director'].get_actor_location()
            state['director_original_rotation'] = state['director'].get_actor_rotation()
            state['director_original_fov'] = state['camera_component'].get_editor_property('field_of_view')
            result['ordinary_initial'] = cutaway_sample(pc)
            check('ordinary_initial_native_cutaway_matches_camera', result['ordinary_initial']['actor_hidden'] == result['ordinary_initial']['expected_hidden'] and result['ordinary_initial']['actor_tick_enabled'])
            threshold = state['threshold']
            state['cases'] = [
                {'name': 'architectural-front-outside', 'kind': 'staged', 'location': [-4460, 180, 2820], 'target': [200, 180, 30], 'fov': 41.5, 'expected_hidden': True},
                {'name': 'architectural-reverse-inside', 'kind': 'staged', 'location': [1450, 100, 1800], 'target': [-500, 100, 0], 'fov': 68, 'expected_hidden': False},
                {'name': 'threshold-outside', 'kind': 'staged', 'location': [threshold - 25, 100, 1800], 'target': [200, 100, 0], 'fov': 54, 'expected_hidden': True},
                {'name': 'threshold-inside', 'kind': 'staged', 'location': [threshold + 25, 100, 1800], 'target': [200, 100, 0], 'fov': 54, 'expected_hidden': False},
                {'name': 'ordinary-gameplay-return', 'kind': 'ordinary-return'},
            ]
            state['case_index'] = 0
            stage_case(world, pc)
        elif state['phase'] == 'settle':
            if game_time - state['settle_game'] < 1:
                return
            state['phase'] = 'sample'
        elif state['phase'] == 'sample':
            sample = cutaway_sample(pc)
            state['samples'].append(sample)
            if len(state['samples']) < 12:
                return
            case = state['cases'][state['case_index']]
            samples = state['samples']
            valid = all(s['actor_tick_enabled'] and s['actor_hidden'] == s['expected_hidden'] and not s['actor_collision_enabled'] and s['all_component_collision_disabled'] and s['reverse_overhead_light']['present_once'] and s['reverse_overhead_light']['owner_is_cutaway'] and s['reverse_overhead_light']['owner_hidden'] == s['actor_hidden'] for s in samples)
            if 'expected_hidden' in case:
                valid = valid and all(s['actor_hidden'] == case['expected_hidden'] and math.dist(s['camera']['location'], case['location']) < .1 and abs(s['camera']['fov'] - case['fov']) < .01 and abs(s['camera_component']['field_of_view'] - case['fov']) < .01 for s in samples)
            else:
                valid = valid and state['director'].is_actor_tick_enabled() and all(abs(s['camera']['fov'] - result['ordinary_initial']['camera']['fov']) < .01 and abs(s['camera_component']['field_of_view'] - state['director_original_fov']) < .01 for s in samples)
            result['runtime_cases'].append({'case': case, 'samples': samples, 'passed': bool(valid)})
            check('native_cutaway_' + case['name'].replace('-', '_'), valid)
            state['case_index'] += 1
            if state['case_index'] == len(state['cases']):
                finish()
            else:
                stage_case(world, pc)
    except Exception:
        finish(traceback.format_exc())


try:
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    assert levels.load_level(MAP)
    saved_audit()
    levels.editor_request_begin_play()
    handle = u.register_slate_post_tick_callback(tick)
except Exception:
    finish(traceback.format_exc())
