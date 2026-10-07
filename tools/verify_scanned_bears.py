"""Reopen scanned props and render each LOD of the first bear in an unsaved review world.

Run with tools/run_encounter_test.py. Does not import, save assets or change a map.
Checks saved ownership, LOD geometry, material/texture references, collision and scale.
The review enlarges the first bear 10x for inspection; its saved scale is unchanged.
"""
import json
import os
from pathlib import Path
import sys
import time
import traceback

import unreal as u

sys.path.insert(0, str(Path(__file__).resolve().parent))
from finish_editor import finish_editor
from png_evidence import decode_png

OUT = Path(os.environ['TEDDY_TEST_DIR'])
DEST = os.environ.get('BEAR_VERIFY_DEST', '/Game/ScannedBears').rstrip('/')
assert DEST == '/Game/ScannedBears' or DEST.startswith('/Game/ScannedBears/'), 'Review must stay in ScannedBears'
EXPECTED_PACK = json.loads(Path(os.environ['BEAR_EXPECT_PACK']).read_text(encoding='utf-8')) if os.environ.get('BEAR_EXPECT_PACK') else None
ASSETS = u.EditorAssetLibrary
MESHES = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
ACTORS = u.get_editor_subsystem(u.EditorActorSubsystem)
REPORT = {'passed': False, 'engine': u.SystemLibrary.get_engine_version(),
          'asset_writes': False, 'saved_map_writes': False, 'physical_device_verified': False,
          'method': 'Fresh editor saved-asset readback; forced LOD renders in an unsaved blank world.',
          'review_actor_scale': 10, 'review_camera_cm': [250, 200, 160],
          'review_target_cm': [0, 0, 43], 'bears': [], 'captures': []}
STATE = {'started': time.monotonic(), 'phase': 'warmup', 'index': 0, 'finished': False}
HANDLE = None


def finish(error=None):
    if STATE['finished']:
        return
    STATE['finished'] = True
    if error:
        REPORT['error'] = error
    REPORT['passed'] = not error and len(REPORT['captures']) == 3 and bool(REPORT['bears'])
    (OUT / 'receipt.json').write_text(json.dumps(REPORT, indent=2) + '\n', encoding='utf-8')
    finish_editor(HANDLE)


def inspect_mesh(mesh):
    path = mesh.get_path_name().split('.')[0]
    lods = MESHES.get_lod_count(mesh)
    triangles = [mesh.get_num_triangles(i) for i in range(lods)]
    materials = [slot.get_editor_property('material_interface')
                 for slot in mesh.get_editor_property('static_materials')]
    textures = []
    for material in materials:
        if isinstance(material, u.MaterialInstanceConstant):
            for parameter in material.get_editor_property('texture_parameter_values'):
                texture = parameter.get_editor_property('parameter_value')
                if texture:
                    textures.append(texture.get_path_name())
    box = mesh.get_bounding_box()
    size = box.max - box.min
    hulls = MESHES.get_convex_collision_count(mesh) + MESHES.get_simple_collision_count(mesh)
    nanite = bool(mesh.get_editor_property('nanite_settings').get_editor_property('enabled'))
    checks = {
        'owned': ASSETS.get_metadata_tag(mesh, 'BearScanner.Owner') == 'bear-scanner',
        'scan_identity_saved': bool(ASSETS.get_metadata_tag(mesh, 'BearScanId')),
        'scan_version_saved': bool(ASSETS.get_metadata_tag(mesh, 'BearScanVersion')),
        'three_lods': lods == 3,
        'nonempty_decreasing_geometry': len(triangles) == 3 and triangles[0] > triangles[1] > triangles[2] > 0,
        'all_material_slots_resolve': bool(materials) and all(materials),
        'shared_material': bool(materials) and len({m.get_path_name() for m in materials if m}) == 1,
        'saved_scan_texture': bool(textures) and all(t.startswith('/Game/ScannedBears/') for t in textures),
        'collision_present': hulls > 0,
        'feet_pivot': abs(box.min.z) < 0.25,
        'finite_physical_size': 0 < size.x < 1000 and 0 < size.y < 1000 and 0 < size.z < 1000,
        'nanite_disabled_for_lods': not nanite,
    }
    if EXPECTED_PACK:
        checks.update(pack_identity_matches=ASSETS.get_metadata_tag(mesh, 'BearScanId') == EXPECTED_PACK['id'],
                      pack_version_matches=ASSETS.get_metadata_tag(mesh, 'BearScanVersion') == str(EXPECTED_PACK['version']),
                      pack_revision_matches=ASSETS.get_metadata_tag(mesh, 'BearPackRevision') == EXPECTED_PACK['revision'],
                      pack_model_hash_matches=ASSETS.get_metadata_tag(mesh, 'BearModelSha256') == EXPECTED_PACK['files'][EXPECTED_PACK['model']['file']]['sha256'])
    result = {'mesh': path, 'scan_id': ASSETS.get_metadata_tag(mesh, 'BearScanId'),
              'lod_triangles': triangles, 'collision_hulls': hulls,
              'size_cm': [size.x, size.y, size.z], 'base_z_cm': box.min.z,
              'materials': sorted({m.get_path_name() for m in materials if m}),
              'textures': sorted(set(textures)), 'checks': checks}
    REPORT['bears'].append(result)
    assert all(checks.values()), result


def spawn(cls, location, rotation=None):
    actor = ACTORS.spawn_actor_from_class(cls, u.Vector(*location), rotation or u.Rotator(), transient=True)
    assert actor
    return actor


def stage(mesh):
    assert u.EditorLoadingAndSavingUtils.new_blank_map(False)
    actor = spawn(u.StaticMeshActor, (0, 0, 0))
    actor.set_actor_scale3d(u.Vector(10, 10, 10))
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_editor_property('forced_lod_model', 1)
    ground = spawn(u.StaticMeshActor, (0, 0, -5))
    ground.static_mesh_component.set_static_mesh(ASSETS.load_asset('/Engine/BasicShapes/Cube'))
    ground.set_actor_scale3d(u.Vector(8, 8, 0.1))
    for intensity, pitch, yaw in ((6.0, -45, 155), (2.0, -30, -25)):
        light = spawn(u.DirectionalLight, (0, 0, 250), u.Rotator(pitch=pitch, yaw=yaw))
        light.light_component.set_editor_property('intensity', intensity)
    camera_pos = u.Vector(*REPORT['review_camera_cm'])
    camera_rot = u.MathLibrary.find_look_at_rotation(camera_pos, u.Vector(0, 0, 43))
    camera = spawn(u.CameraActor, REPORT['review_camera_cm'], camera_rot)
    camera.camera_component.set_editor_property('field_of_view', 35.0)
    pp = spawn(u.PostProcessVolume, (0, 0, 0))
    pp.set_editor_property('unbound', True)
    settings = pp.get_editor_property('settings')
    for key, value in {'override_auto_exposure_min_brightness': True,
                       'override_auto_exposure_max_brightness': True,
                       'override_auto_exposure_bias': True,
                       'auto_exposure_min_brightness': 1.0,
                       'auto_exposure_max_brightness': 1.0,
                       'auto_exposure_bias': 0.0}.items():
        settings.set_editor_property(key, value)
    pp.set_editor_property('settings', settings)
    u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(camera_pos, camera_rot)
    STATE.update(component=component, camera=camera, staged=time.monotonic())


def tick(delta):
    try:
        now = time.monotonic()
        if now - STATE['started'] > 180:
            raise RuntimeError('Scanned-bear review capture timed out')
        if STATE['phase'] == 'warmup':
            if now - STATE['staged'] < 15:
                return
            STATE['phase'] = 'request'
        if STATE['phase'] == 'request':
            path = OUT / f"bear-lod{STATE['index']}.png"
            assert not path.exists()
            STATE['image'] = path
            STATE['task'] = u.AutomationLibrary.take_high_res_screenshot(
                1280, 720, str(path), camera=STATE['camera'], delay=2.0)
            STATE['phase'] = 'capture'
        elif STATE['phase'] == 'capture':
            path = STATE['image']
            if not path.exists():
                return
            try:
                validation = decode_png(path)
            except Exception:
                return
            validation.pop('chunks', None)
            REPORT['captures'].append({'lod': STATE['index'], 'path': str(path), 'validation': validation})
            STATE['index'] += 1
            if STATE['index'] == 3:
                finish()
            else:
                STATE['component'].set_editor_property('forced_lod_model', STATE['index'] + 1)
                STATE['phase'] = 'request'
    except Exception:
        finish(traceback.format_exc())


try:
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    REPORT['destination'] = DEST
    meshes = [ASSETS.load_asset(path) for path in ASSETS.list_assets(DEST, recursive=True, include_folder=False)]
    meshes = [mesh for mesh in meshes if isinstance(mesh, u.StaticMesh)]
    assert meshes, 'No saved scanned-bear meshes found'
    for mesh in meshes:
        inspect_mesh(mesh)
    stage(meshes[0])
    HANDLE = u.register_slate_post_tick_callback(tick)
except Exception:
    finish(traceback.format_exc())
