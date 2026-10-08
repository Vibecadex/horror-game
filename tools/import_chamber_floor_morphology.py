"""Place the coarse morphology floor and hide the fine V2 overlays.

Original floor, slab, and crust actors keep their meshes and transforms.
New decoration is NoCollision and uses new material graphs only.
"""
import sys
import json
import traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from chamber_common import *
from import_chamber_kit import collision_off, apply_slots, sha
import apply_parity_look as look

SOURCE = ROOT / 'Assets/Adapted/ChamberParity/FloorMorphologyV3'
R = {'passed': False, 'actors': [], 'meshes': [], 'concealed': [],
     'source_assets_preserved': True, 'collision': 'NoCollision',
     'existing_floor_materials_rebuilt': False}
CONCEAL_TAGS = ('ChamberFloorOwned', 'ChamberSlabsOwned', 'ChamberCrustOwned')
EXPECTED_CONCEALED = 14


def conceal(actor):
    assert 'TeddyEncounterOwned' in [str(tag) for tag in actor.tags], actor.get_actor_label()
    actor.set_actor_hidden_in_game(True)
    for component in actor.get_components_by_class(u.PrimitiveComponent):
        component.set_editor_property('visible', False)
        component.set_editor_property('cast_shadow', False)
    R['concealed'].append(actor.get_actor_label())


def main():
    begin()
    raw = (SOURCE / 'manifest.json').read_bytes()
    doc = json.loads(raw)
    assert doc['owner'] == 'teddy-chamber-floor-morphology-v3-20261005'
    assert doc['status'] == 'source-ready-for-engine-review'
    assert len(doc['assets']) == 1 and len(doc['recommended_placements']) == 1
    assert all(item['passed'] for item in doc['fbx_roundtrip_checks'])
    assert doc['assets'][0]['highest_point_cm'] <= 3.9
    profile = dict(P['floor_morphology'])
    assert profile['tile_cm'] == 3200 and profile['texture_weight'] == 0.22 and profile['normal'] == 'flat'
    assert profile['detail_weight'] == 0.0
    assert P['floor']['tile_cm'] == 850 and P['floor']['detail_weight'] == 0.65
    pin = OUT / 'chamber-floor-morphology-reviewed.json'
    pin.write_bytes(raw)
    R['manifest_sha256'] = sha(pin)
    R['material_note'] = 'Morphology graphs only. Flat tangent normal. Texture is a 22 percent large-scale stain. Crack is recessed concrete, not a black card.'

    def quiet(name, factor, rough=.94, spec=.08):
        material = newmat('FloorMorph' + name)
        world = node(material, u.MaterialExpressionWorldPosition)
        xy = node(material, u.MaterialExpressionComponentMask, r=True, g=True, b=False, a=False)
        link(world, xy, 'Input')
        sampled = look.sample(material, 'T_AI_Floor_Color', u.MaterialSamplerType.SAMPLERTYPE_COLOR, mul(material, xy, 1 / profile['tile_cm']))
        gray = node(material, u.MaterialExpressionDesaturation)
        link(sampled, gray, '')
        link(scalar(material, .88), gray, 'Fraction')
        color = blend(material, rgb(material, profile['flat_color']), gray, scalar(material, profile['texture_weight']))
        bind(mul(material, color, factor), u.MaterialProperty.MP_BASE_COLOR)
        bind(scalar(material, rough), u.MaterialProperty.MP_ROUGHNESS)
        bind(scalar(material, spec), u.MaterialProperty.MP_SPECULAR)
        bind(rgb(material, (0, 0, 1)), u.MaterialProperty.MP_NORMAL)
        M.recompile_material(material)
        save(material)
        return material

    mats = {key: quiet(key, factor, rough, spec) for key, factor, rough, spec in [
        ('Concrete', .78, .94, .08),
        ('ConcreteLight', .86, .92, .09),
        ('ConcreteDark', .62, .96, .05),
        ('Aggregate', .7, .97, .05),
        ('Dark', .4, 1, 0),
        ('Crack', .62, .98, .03),
    ]}
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
        task.destination_path = DEST + '/FloorMorphology'
        task.destination_name = entry['name']
        task.automated = True
        task.save = True
        task.replace_existing = True
        task.options = options
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        assert task.imported_object_paths
        model = own(A.load_asset(task.imported_object_paths[0]))
        assert isinstance(model, u.StaticMesh)
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
        label = 'Morph_' + placement['label']
        actor = bylabel.get('TE_Chamber_' + label)
        if actor is None:
            actor = spawn(u.StaticMeshActor, label, placement['location_cm'], u.Rotator(yaw=placement['yaw']))
        actor.set_actor_location(u.Vector(*placement['location_cm']), False, False)
        actor.set_actor_rotation(u.Rotator(yaw=placement['yaw']), False)
        actor.set_actor_scale3d(u.Vector(*placement['scale']))
        actor.set_editor_property('tags', ['TeddyEncounterOwned', 'ChamberOwned', 'ChamberMorphologyOwned'])
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
    for actor in ACTORS.get_all_level_actors():
        tags = [str(tag) for tag in actor.tags]
        if any(tag in tags for tag in CONCEAL_TAGS):
            conceal(actor)
            concealed.append(actor.get_actor_label())
    assert len(concealed) == EXPECTED_CONCEALED, sorted(concealed)
    finish()
    after = {actor.get_actor_label(): actor for actor in ACTORS.get_all_level_actors()}
    for row in R['actors']:
        actor = after[row['label']]
        component = actor.static_mesh_component
        assert component.static_mesh.get_name() == row['placement']['mesh']
        assert component.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION
        assert not actor.get_actor_enable_collision()
        assert actor.get_actor_scale3d().z == 1
    for label in concealed:
        actor = after[label]
        assert bool(actor.get_editor_property('hidden'))
        loc = actor.get_actor_location()
        assert abs(loc.z + 5) < .05
    R['passed'] = True


if __name__ == '__main__':
    try:
        main()
    except Exception:
        R['error'] = traceback.format_exc()
        raise
    finally:
        (OUT / 'chamber-floor-morphology-import.json').write_text(json.dumps(R, indent=2))
