"""Place the V4 concrete recovery sheet and hide the V3 morphology actor.

V2 overlays and the V3 mesh stay in place. New decoration is NoCollision.
Materials are new FloorRecover graphs. Lighting and exposure are not edited.
"""
import sys
import json
import traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from chamber_common import *
from import_chamber_kit import collision_off, apply_slots, sha
import apply_parity_look as look
import apply_parity_combined as combined

SOURCE = ROOT / 'Assets/Adapted/ChamberParity/FloorRecoveryV4'
R = {'passed': False, 'actors': [], 'meshes': [], 'concealed': [], 'morphology_hidden': [],
     'source_assets_preserved': True, 'collision': 'NoCollision',
     'existing_floor_materials_rebuilt': False, 'lighting_unchanged': True}
CONCEAL_TAGS = ('ChamberFloorOwned', 'ChamberSlabsOwned', 'ChamberCrustOwned')
EXPECTED_CONCEALED = 14


def conceal(actor):
    assert 'TeddyEncounterOwned' in [str(tag) for tag in actor.tags], actor.get_actor_label()
    actor.set_actor_hidden_in_game(True)
    for component in actor.get_components_by_class(u.PrimitiveComponent):
        component.set_editor_property('visible', False)
        component.set_editor_property('cast_shadow', False)


def main():
    begin()
    raw = (SOURCE / 'manifest.json').read_bytes()
    doc = json.loads(raw)
    assert doc['owner'] == 'teddy-chamber-floor-recovery-v4-20261005'
    assert doc['status'] == 'source-ready-for-engine-review'
    assert len(doc['assets']) == 1 and len(doc['recommended_placements']) == 1
    assert all(item['passed'] for item in doc['fbx_roundtrip_checks'])
    assert doc['assets'][0]['highest_point_cm'] <= 3.7
    assert doc['assets'][0]['median_plate_area_m2'] <= 3.2
    assert doc['assets'][0]['plate_area_range_m2'][1] < 12
    profile = dict(P['floor_recovery'])
    assert profile['tile_cm'] == 720 and profile['detail_weight'] == 0.28 and profile['normal_mix'] == 0.28
    assert profile['value_scale'] == 0.74
    assert P['floor_morphology']['normal'] == 'flat' and P['floor_morphology']['tile_cm'] == 3200
    assert P['floor']['tile_cm'] == 850 and P['floor']['detail_weight'] == 0.65
    pin = OUT / 'chamber-floor-recovery-reviewed.json'
    pin.write_bytes(raw)
    R['manifest_sha256'] = sha(pin)

    def recover(name, factor, rough_lo, rough_hi, spec, normal_extra=0.):
        material = newmat('FloorRecover' + name)
        world = node(material, u.MaterialExpressionWorldPosition)
        xy = node(material, u.MaterialExpressionComponentMask, r=True, g=True, b=False, a=False)
        link(world, xy, 'Input')
        uv = mul(material, xy, 1 / profile['tile_cm'])
        soft = look.sample(material, 'T_AI_Floor_Color', u.MaterialSamplerType.SAMPLERTYPE_COLOR, uv)
        detailed = look.texture_sample(material, look.parity_texture(), uv)
        color = blend(material, soft, detailed, scalar(material, profile['detail_weight']))
        gray = node(material, u.MaterialExpressionDesaturation)
        link(color, gray, '')
        link(scalar(material, .72), gray, 'Fraction')
        dry = combined.data_sample(material, 'T_Comfy_Floor_Dry', u.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE, mul(material, xy, 1 / 1350.))
        wear = blend(material, scalar(material, .62), scalar(material, 1.), dry)
        gradient = mul(material, look.add(material, mul(material, channel(material, world, 'R'), -1), scalar(material, -250)), 1 / 650.)
        weight = node(material, u.MaterialExpressionClamp, min_default=0., max_default=1.)
        link(gradient, weight, '')
        damp = blend(material, scalar(material, profile['foreground_damp']), scalar(material, profile['foreground_dry']), dry)
        wear = blend(material, wear, damp, weight)
        bind(mul(material, mul(material, gray, profile['value_scale'] * factor), wear), u.MaterialProperty.MP_BASE_COLOR)
        bump = look.floor_bump(material, look.parity_texture(), uv)
        old = look.sample(material, 'T_AI_Floor_Normal', u.MaterialSamplerType.SAMPLERTYPE_NORMAL, uv)
        bind(blend(material, old, bump, scalar(material, profile['normal_mix'] + normal_extra)), u.MaterialProperty.MP_NORMAL)
        rough = blend(material, scalar(material, rough_lo), scalar(material, rough_hi), dry)
        bind(rough, u.MaterialProperty.MP_ROUGHNESS)
        bind(scalar(material, spec), u.MaterialProperty.MP_SPECULAR)
        M.recompile_material(material)
        save(material)
        return material

    mats = {
        'Concrete': recover('Concrete', .82, .40, .93, .16),
        'ConcreteLight': recover('ConcreteLight', .9, .46, .9, .14),
        'ConcreteDark': recover('ConcreteDark', .64, .48, .96, .1),
        'Aggregate': recover('Aggregate', .74, .82, .98, .06, .12),
        'Dark': recover('Dark', .42, .9, 1., .04),
        'Crack': recover('Crack', .55, .84, .98, .05),
    }
    assert all(mats.values())
    u.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
    models = {}
    for entry in doc['assets']:
        source = SOURCE / entry['file']
        assert source.parent == SOURCE and sha(source) == entry['sha256']
        options = u.FbxImportUI()
        for key, value in {'automated_import_should_detect_type': False, 'mesh_type_to_import': u.FBXImportType.FBXIT_STATIC_MESH,
                           'import_as_skeletal': False, 'import_materials': False, 'import_textures': False}.items():
            options.set_editor_property(key, value)
        for key, value in {'combine_meshes': True, 'auto_generate_collision': False, 'convert_scene': True,
                           'convert_scene_unit': True, 'force_front_x_axis': False}.items():
            options.static_mesh_import_data.set_editor_property(key, value)
        task = u.AssetImportTask()
        task.filename = str(source)
        task.destination_path = DEST + '/FloorRecovery'
        task.destination_name = entry['name']
        task.automated = True
        task.save = True
        task.replace_existing = True
        task.options = options
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        assert task.imported_object_paths
        model = own(A.load_asset(task.imported_object_paths[0]))
        assert isinstance(model, u.StaticMesh)
        assert model.get_name() == entry['name']
        for index, slot in enumerate(model.get_editor_property('static_materials')):
            model.set_material(index, mats[str(slot.get_editor_property('material_slot_name'))])
        extent = model.get_bounds().box_extent
        size = [extent.x * 2, extent.y * 2, extent.z * 2]
        assert max(abs(a - b) for a, b in zip(size, entry['expected_dimensions_cm'])) < .15, (entry['name'], size)
        save(model)
        models[entry['name']] = model
        R['meshes'].append({'path': model.get_path_name(), 'bounds_cm': size, 'triangles_source': entry['triangles']})
    bylabel = {actor.get_actor_label(): actor for actor in ACTORS.get_all_level_actors()}
    for placement in doc['recommended_placements']:
        assert placement['scale'][2] == 1 and placement['location_cm'][2] == -5
        label = 'Recover_' + placement['label']
        actor = bylabel.get('TE_Chamber_' + label)
        if actor is None:
            actor = spawn(u.StaticMeshActor, label, placement['location_cm'], u.Rotator(yaw=placement['yaw']))
        actor.set_actor_location(u.Vector(*placement['location_cm']), False, False)
        actor.set_actor_rotation(u.Rotator(yaw=placement['yaw']), False)
        actor.set_actor_scale3d(u.Vector(*placement['scale']))
        actor.set_editor_property('tags', ['TeddyEncounterOwned', 'ChamberOwned', 'ChamberRecoveryOwned'])
        actor.set_actor_hidden_in_game(False)
        actor.set_actor_enable_collision(False)
        component = actor.static_mesh_component
        component.set_static_mesh(models[placement['mesh']])
        collision_off(component)
        apply_slots(component, mats)
        component.set_editor_property('visible', True)
        component.set_lighting_channels(True, False, False)
        readback = []
        for index, slot in enumerate(component.static_mesh.get_editor_property('static_materials')):
            key = str(slot.get_editor_property('material_slot_name'))
            assert component.get_material(index) == mats[key]
            readback.append({'slot': key, 'material': component.get_material(index).get_path_name()})
        R['actors'].append({'label': actor.get_actor_label(), 'placement': placement, 'material_readback': readback})
    concealed = []
    for actor in list(ACTORS.get_all_level_actors()):
        tags = [str(tag) for tag in actor.tags]
        if any(tag in tags for tag in CONCEAL_TAGS):
            before = actor.get_actor_location()
            conceal(actor)
            after = actor.get_actor_location()
            assert abs(before.x - after.x) < .01 and abs(before.y - after.y) < .01 and abs(before.z - after.z) < .01
            concealed.append(actor.get_actor_label())
        elif 'ChamberMorphologyOwned' in tags:
            before = [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z]
            conceal(actor)
            after = actor.get_actor_location()
            assert abs(before[0] - after.x) < .01 and abs(before[1] - after.y) < .01 and abs(before[2] + 5) < .05
            R['morphology_hidden'].append({'label': actor.get_actor_label(), 'location': before})
    assert len(concealed) == EXPECTED_CONCEALED, sorted(concealed)
    assert len(R['morphology_hidden']) == 1, R['morphology_hidden']
    R['concealed'] = concealed
    finish()
    after = {actor.get_actor_label(): actor for actor in ACTORS.get_all_level_actors()}
    for row in R['actors']:
        actor = after[row['label']]
        component = actor.static_mesh_component
        assert component.static_mesh.get_name() == row['placement']['mesh']
        assert component.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION
        assert not actor.get_actor_enable_collision()
        assert actor.get_actor_scale3d().z == 1
        assert not bool(actor.get_editor_property('hidden'))
    for label in concealed + [R['morphology_hidden'][0]['label']]:
        assert bool(after[label].get_editor_property('hidden'))
    R['passed'] = True


if __name__ == '__main__':
    try:
        main()
    except Exception:
        R['error'] = traceback.format_exc()
        raise
    finally:
        (OUT / 'chamber-floor-recovery-import.json').write_text(json.dumps(R, indent=2))
