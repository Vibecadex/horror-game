"""Open the saved service-bay mesh, restrain side reds, and lower the overhead shaft.

The floor recovery actor stays. Exposure is not written. Original kit FBX stays.
The visible door keeps the path /Game/TeddyEncounter/Chamber/Meshes/SM_ChamberServiceDoorBay.
"""
import json
import sys
import traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from chamber_common import *
from import_chamber_kit import collision_off, sha

SOURCE = ROOT / 'Assets/Adapted/ChamberParity/BayDepth'
KIT_FBX = ROOT / 'Assets/Adapted/ChamberParity/SM_ChamberServiceDoorBay.fbx'
MESH_NAME = 'SM_ChamberServiceDoorBay'
R = {'passed': False, 'floor_untouched': True, 'exposure_written': False,
     'original_kit_fbx_untouched': True}


def try_set(obj, key, value):
    try:
        obj.set_editor_property(key, value)
        return True
    except Exception as error:
        return str(error)


def hidden(actor):
    return bool(actor.get_editor_property('hidden'))


def main():
    begin()
    kit_before = sha(KIT_FBX)
    raw = (SOURCE / 'manifest.json').read_bytes()
    doc = json.loads(raw)
    assert doc['owner'] == 'teddy-chamber-bay-depth-20261005'
    assert doc['status'] == 'source-ready-for-engine-review'
    entry = doc['assets'][0]
    source = SOURCE / entry['file']
    assert sha(source) == entry['sha256']
    assert P['revision'] == 'chamber-12-bay-atmosphere'
    assert P['floor_recovery']['tile_cm'] == 720 and P['floor']['tile_cm'] == 850
    actors = {actor.get_actor_label(): actor for actor in ACTORS.get_all_level_actors()}
    floor = actors['TE_Chamber_Recover_Main']
    morph = actors['TE_Chamber_Morph_Main']
    floor_before = [floor.get_actor_location().z, floor.get_actor_scale3d().z, hidden(floor)]
    assert floor_before[0] == -5 and abs(floor_before[1] - 1) < 1e-4 and floor_before[2] is False
    assert hidden(morph) is True

    u.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
    options = u.FbxImportUI()
    for key, value in {'automated_import_should_detect_type': False, 'mesh_type_to_import': u.FBXImportType.FBXIT_STATIC_MESH,
                       'import_as_skeletal': False, 'import_materials': False, 'import_textures': False}.items():
        options.set_editor_property(key, value)
    for key, value in {'combine_meshes': True, 'auto_generate_collision': False, 'convert_scene': True,
                       'convert_scene_unit': True, 'force_front_x_axis': False}.items():
        options.static_mesh_import_data.set_editor_property(key, value)
    task = u.AssetImportTask()
    task.filename = str(source)
    task.destination_path = DEST + '/Meshes'
    task.destination_name = MESH_NAME
    task.automated = True
    task.save = True
    task.replace_existing = True
    task.options = options
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    assert task.imported_object_paths, task.imported_object_paths
    model = own(A.load_asset(DEST + '/Meshes/' + MESH_NAME))
    assert model.get_path_name().startswith(DEST + '/Meshes/' + MESH_NAME)
    mats = {name: existing(DEST + '/Materials/M_Chamber_' + name) for name in entry['material_slots']}
    assert all(mats.values())
    for index, slot in enumerate(model.get_editor_property('static_materials')):
        model.set_material(index, mats[str(slot.get_editor_property('material_slot_name'))])
    extent = model.get_bounds().box_extent
    size = [extent.x * 2, extent.y * 2, extent.z * 2]
    assert max(abs(a - b) for a, b in zip(size, entry['expected_dimensions_cm'])) < .15, (size, entry['expected_dimensions_cm'])
    save(model)
    indicator = existing(DEST + '/Materials/M_Chamber_ServiceIndicator')
    assert indicator
    bp = existing(DEST + '/Blueprints/BP_ChamberCutaway')
    for name in ('ReverseDoorL', 'ReverseDoorR'):
        piece = component(bp, name, u.StaticMeshComponent)
        piece.set_static_mesh(model)
        collision_off(piece)
        for index, slot in enumerate(piece.static_mesh.get_editor_property('static_materials')):
            if str(slot.get_editor_property('material_slot_name')) == 'Emissive':
                piece.set_material(index, indicator)
    compile(bp)
    cutaway = actors['TE_Chamber_FrontCutaway']
    placed = list(cutaway.get_components_by_class(u.StaticMeshComponent))
    assert len(placed) == 19
    for piece in placed:
        if piece.get_name() in ('ReverseDoorL', 'ReverseDoorR'):
            piece.set_static_mesh(model)
            collision_off(piece)
            for index, slot in enumerate(piece.static_mesh.get_editor_property('static_materials')):
                if str(slot.get_editor_property('material_slot_name')) == 'Emissive':
                    piece.set_material(index, indicator)
    R['door_dimensions_cm'] = size

    spec = P['side_practical']
    for index in (0, 1):
        lens = actors['TE_Room_BeaconLens_' + str(index)]
        light = actors['TE_Room_BeaconLight_' + str(index)]
        assert 'TeddyEncounterOwned' in [str(tag) for tag in lens.tags]
        assert 'TeddyEncounterOwned' in [str(tag) for tag in light.tags]
        before = lens.get_actor_scale3d()
        lens.set_actor_scale3d(u.Vector(*spec['lens_scale']))
        point = light.get_component_by_class(u.PointLightComponent)
        point.set_editor_property('intensity', float(spec['intensity']))
        point.set_editor_property('attenuation_radius', float(spec['radius']))
        point.set_editor_property('source_radius', float(spec['source']))
        point.set_editor_property('volumetric_scattering_intensity', 0.05)
        R.setdefault('side_practicals', []).append({
            'lens': lens.get_actor_label(),
            'before_scale': [before.x, before.y, before.z],
            'scale': spec['lens_scale'],
            'intensity': spec['intensity']})

    mist = P['overhead_mist']
    fog_actor = actors['TE_Parity_FarFog_Light']
    assert 'ParityOwned' in [str(tag) for tag in fog_actor.tags]
    fog_actor.set_actor_location(u.Vector(*mist['location']), False, False)
    fog_actor.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(*mist['location']), u.Vector(*mist['target'])), False)
    fog = fog_actor.get_component_by_class(u.RectLightComponent)
    for prop, key in (('intensity', 'intensity'), ('attenuation_radius', 'radius'), ('source_width', 'width'),
                      ('source_height', 'height'), ('volumetric_scattering_intensity', 'scattering')):
        fog.set_editor_property(prop, float(mist[key]))
    fog.set_editor_property('diffuse_scale', 0.)
    fog.set_editor_property('specular_scale', 0.)
    fog.set_editor_property('indirect_lighting_intensity', 0.)
    fog.set_light_color(u.LinearColor(0.55, 0.84, 0.82, 1))
    R['barn_door'] = {key: try_set(fog, key, value) for key, value in (('barn_door_angle', 88.), ('barn_door_length', 1.))}
    R['overhead_mist'] = mist

    height = actors['TE_LowMist'].get_component_by_class(u.ExponentialHeightFogComponent)
    assert bool(height.get_editor_property('enable_volumetric_fog')) is True
    for key, value in P['height_fog'].items():
        height.set_editor_property(key, float(value))
    R['volumetric_fog_distance'] = try_set(height, 'volumetric_fog_distance', 12000.)
    R['height_fog'] = P['height_fog']

    fill = P['bay_fill']
    planned = {'TE_Chamber_' + item['name'] for item in fill['placements']}
    for actor in list(ACTORS.get_all_level_actors()):
        if actor.get_actor_label() in planned:
            assert 'ChamberOwned' in [str(tag) for tag in actor.tags]
            assert ACTORS.destroy_actor(actor)
    for item in fill['placements']:
        actor = spawn(u.SpotLight, item['name'], item['location'],
                      u.MathLibrary.find_look_at_rotation(u.Vector(*item['location']), u.Vector(*item['target'])))
        light = actor.get_component_by_class(u.SpotLightComponent)
        for key, value in {'mobility': u.ComponentMobility.MOVABLE, 'intensity_units': u.LightUnits.CANDELAS,
                           'intensity': float(fill['intensity']), 'attenuation_radius': float(fill['radius']),
                           'inner_cone_angle': float(fill['inner']), 'outer_cone_angle': float(fill['outer']),
                           'source_radius': float(fill['source']), 'volumetric_scattering_intensity': float(fill['scattering']),
                           'indirect_lighting_intensity': 0., 'specular_scale': 0.15}.items():
            light.set_editor_property(key, value)
        light.set_light_color(u.LinearColor(*fill['color'], 1))
        light.set_cast_shadows(True)
        light.set_lighting_channels(False, False, True)
    R['bay_fill'] = fill

    assert sha(KIT_FBX) == kit_before
    assert floor.get_actor_location().z == -5 and abs(floor.get_actor_scale3d().z - 1) < 1e-4 and hidden(floor) is False
    assert hidden(morph) is True
    finish()
    reloaded = {actor.get_actor_label(): actor for actor in ACTORS.get_all_level_actors()}
    door_pieces = [piece for piece in reloaded['TE_Chamber_FrontCutaway'].get_components_by_class(u.StaticMeshComponent)
                   if piece.get_name() in ('ReverseDoorL', 'ReverseDoorR')]
    assert {piece.get_name() for piece in door_pieces} == {'ReverseDoorL', 'ReverseDoorR'}
    assert all(piece.static_mesh.get_name() == MESH_NAME for piece in door_pieces)
    for piece in door_pieces:
        origin, extent, _ = u.SystemLibrary.get_component_bounds(piece)
        hi_x = origin.x + extent.x
        assert hi_x <= -1400, (piece.get_name(), hi_x)
        assert origin.z + extent.z < 700
    assert len(reloaded['TE_Chamber_FrontCutaway'].get_components_by_class(u.StaticMeshComponent)) == 19
    assert all(('TE_Chamber_' + item['name']) in reloaded for item in fill['placements'])
    R['reloaded'] = True
    R['passed'] = True


if __name__ == '__main__':
    try:
        main()
    except Exception:
        R['error'] = traceback.format_exc()
        raise
    finally:
        (OUT / (P['revision'] + '-bay-atmosphere.json')).write_text(json.dumps(R, indent=2), encoding='utf-8')
