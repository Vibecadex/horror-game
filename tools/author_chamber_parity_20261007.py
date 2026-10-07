"""Incremental isolated room candidate. Never rebuilds or saves the shared encounter.

Run with run_encounter_test.py. Existing assets are read-only; only the new map,
new material graphs and new debris packages carry this pass's ownership marker.
"""
import hashlib
import json
import os
import sys
import traceback
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from finish_editor import finish_editor
from chamber_parity_snapshot import snapshot_level
OUT = Path(os.environ['TEDDY_TEST_DIR'])
P = json.loads((ROOT / 'study/chamber-parity-20261007.json').read_text())
NS, MAP, OWNER = P['namespace'], P['map'], P['owner']
A, M = u.EditorAssetLibrary, u.MaterialEditingLibrary
LEV = u.get_editor_subsystem(u.LevelEditorSubsystem)
ACT = u.get_editor_subsystem(u.EditorActorSubsystem)
R = {'passed': False, 'map': MAP, 'settings': P, 'changed_assets': [], 'asset_writes': True,
     'shared_encounter_saved': False, 'gameplay_changes': False}
BASE = json.loads((ROOT / 'evidence/implementation/20261007T134917-capture_chamber_views/saved-scene.json').read_text())
BASE = {a['label']: a for a in BASE}

def owned(path, cls, factory):
    if A.does_asset_exist(path):
        obj = A.load_asset(path)
        assert A.get_metadata_tag(obj, 'ChamberParity.Owner') == OWNER, path
    else:
        obj = u.AssetToolsHelpers.get_asset_tools().create_asset(path.rsplit('/', 1)[1], path.rsplit('/', 1)[0], cls, factory)
        assert obj
        A.set_metadata_tag(obj, 'ChamberParity.Owner', OWNER)
    return obj

def save(obj):
    assert obj.get_path_name().startswith(NS + '/'), obj
    assert A.save_loaded_asset(obj, False)
    R['changed_assets'].append(obj.get_path_name())

def node(m, cls, **props):
    n = M.create_material_expression(m, cls)
    for k, v in props.items(): n.set_editor_property(k, v)
    return n

def link(a, b, pin, output=''):
    names = list(M.get_material_expression_input_names(b))
    if len(names) == 1 and names[0] in ('', 'None'): pin = ''
    assert M.connect_material_expressions(a, output, b, pin), (pin, names)

def scalar(m, v): return node(m, u.MaterialExpressionConstant, r=float(v))
def rgb(m, v): return node(m, u.MaterialExpressionConstant3Vector, constant=u.LinearColor(*v, 1))
def mul(m, a, b):
    n = node(m, u.MaterialExpressionMultiply)
    link(a, n, 'A'); link(scalar(m, b) if isinstance(b, (int, float)) else b, n, 'B')
    return n
def add(m, a, b):
    n = node(m, u.MaterialExpressionAdd); link(a, n, 'A'); link(b, n, 'B'); return n
def lerp(m, a, b, t):
    n = node(m, u.MaterialExpressionLinearInterpolate)
    link(a, n, 'A'); link(b, n, 'B'); link(t, n, 'Alpha'); return n
def bind(n, p): assert M.connect_material_property(n, '', p)
def tex(m, path, uv, kind=u.MaterialSamplerType.SAMPLERTYPE_COLOR):
    texture = A.load_asset(path); assert texture, path
    n = node(m, u.MaterialExpressionTextureSample, texture=texture, sampler_type=kind)
    link(uv, n, 'UVs'); return n

def floor_material(name, factor=1., debris=False, rough=None):
    p = P['floor']
    m = owned(NS + '/Materials/M_Parity_' + name, u.Material, u.MaterialFactoryNew())
    M.delete_all_material_expressions(m)
    world = node(m, u.MaterialExpressionWorldPosition)
    xy = node(m, u.MaterialExpressionComponentMask, r=True, g=True, b=False, a=False)
    link(world, xy, 'Input')
    uv = mul(m, xy, 1 / (270 if debris else p['tile_cm']))
    detailed = tex(m, '/Game/TeddyEncounter/Parity/Textures/T_ParityConcrete_Diffuse', uv)
    soft = tex(m, '/Game/TeddyEncounter/Arena/T_AI_Floor_Color', uv)
    col = lerp(m, soft, detailed, scalar(m, .55 if debris else p['detail_weight']))
    gray = node(m, u.MaterialExpressionDesaturation)
    link(col, gray, ''); link(scalar(m, .8), gray, 'Fraction')
    noise = node(m, u.MaterialExpressionNoise, scale=.00165, quality=1, levels=3,
                 output_min=0., output_max=1., turbulence=False)
    link(world, noise, list(M.get_material_expression_input_names(noise))[0])
    contrast = mul(m, add(m, noise, scalar(m, -.31)), 2.8)
    dry = node(m, u.MaterialExpressionClamp, min_default=0., max_default=1.)
    link(contrast, dry, '')
    variation = lerp(m, scalar(m, .74 if debris else p['wet_min']), scalar(m, 1.06), dry)
    bind(mul(m, mul(m, gray, p['value_scale'] * factor), variation), u.MaterialProperty.MP_BASE_COLOR)
    normal = tex(m, '/Game/TeddyEncounter/Arena/T_AI_Floor_Normal', uv, u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    bind(lerp(m, rgb(m, (0, 0, 1)), normal, scalar(m, .35 if debris else .38)), u.MaterialProperty.MP_NORMAL)
    bind(scalar(m, rough) if rough is not None else lerp(m, scalar(m, p['rough_wet']), scalar(m, p['rough_dry']), dry), u.MaterialProperty.MP_ROUGHNESS)
    bind(scalar(m, .12), u.MaterialProperty.MP_SPECULAR)
    M.recompile_material(m); save(m)
    return m

def spawn(cls, label, location, rotation=None):
    a = ACT.spawn_actor_from_class(cls, u.Vector(*location), rotation or u.Rotator(), transient=False)
    assert a
    a.set_actor_label('TE_Parity20261007_' + label)
    a.set_editor_property('tags', ['TeddyEncounterOwned', 'ChamberParity20261007'])
    a.set_folder_path('TeddyEncounter/ChamberParity20261007')
    return a

def main():
    if not A.does_asset_exist(MAP):
        assert LEV.new_level_from_template(MAP, '/Game/Maps/TeddyEncounter')
        assert LEV.load_level(MAP)
        world = A.load_asset(MAP)
        A.set_metadata_tag(world, 'ChamberParity.Owner', OWNER)
        assert LEV.save_current_level()
    else:
        assert A.get_metadata_tag(A.load_asset(MAP), 'ChamberParity.Owner') == OWNER
        assert LEV.load_level(MAP)
    actors = {a.get_actor_label(): a for a in ACT.get_all_level_actors()}
    # Absolute baselines make revisions idempotent without resetting any source asset.
    tall_meshes = ('SM_ShellWallBay.', 'SM_ShellWallBayNarrow.', 'SM_RoomPilaster.')
    for label, a in actors.items():
        b = BASE.get(label)
        if b and not b['hidden'] and b['meshes'] and any(k in b['meshes'][0]['mesh'] for k in tall_meshes):
            s, loc = list(b['scale']), list(b['location'])
            s[2] *= P['wall_height_multiplier']
            loc[2] = (loc[2] + 5) * P['wall_height_multiplier'] - 5
            a.set_actor_scale3d(u.Vector(*s)); a.set_actor_location(u.Vector(*loc), False, False)
    cutaway = actors['TE_Chamber_FrontCutaway']
    cutaway.set_actor_scale3d(u.Vector(1, 1, P['wall_height_multiplier']))
    cutaway.set_actor_location(u.Vector(0, 0, 5 * (P['wall_height_multiplier'] - 1)), False, False)
    door = actors['TE_Chamber_RearBulkhead']
    b = BASE[door.get_actor_label()]
    door.set_actor_scale3d(u.Vector(b['scale'][0], b['scale'][1], b['scale'][2] * P['door_height_multiplier']))
    for label in ['TE_Chamber_RearBulkheadWheel', 'TE_Chamber_HeaderPractical'] + [n for n in actors if n.startswith('TE_Chamber_BulkheadBeacon')]:
        b = BASE[label]; loc = list(b['location']); loc[2] = (loc[2] - 7) * P['door_height_multiplier'] + 7
        actors[label].set_actor_location(u.Vector(*loc), False, False)
    for label in ['TE_Room_RearFan']:
        b = BASE[label]; loc = list(b['location']); loc[2] *= P['wall_height_multiplier']
        actors[label].set_actor_location(u.Vector(*loc), False, False)
    for label, a in actors.items():
        if label in BASE and ('Cornice' in label or label.startswith('TE_Room_RearFixture')):
            b = BASE[label]; loc = list(b['location']); loc[2] = (loc[2] + 5) * P['wall_height_multiplier'] - 5
            a.set_actor_location(u.Vector(*loc), False, False)

    mats = {n: floor_material('Floor_' + n, f) for n, f in
            [('Concrete', .85), ('ConcreteLight', .94), ('ConcreteDark', .67), ('Aggregate', .77), ('Dark', .38), ('Crack', .49)]}
    floor = actors['TE_Chamber_Recover_Main'].static_mesh_component
    for i, slot in enumerate(floor.static_mesh.get_editor_property('static_materials')):
        floor.set_material(i, mats[str(slot.material_slot_name)])
    # Only the placed component is changed. The shared mesh and original graphs stay intact.
    debris_mats = {'Concrete': floor_material('Debris', 1.42, True, .87),
                   'ChippedEdge': floor_material('ChippedEdge', .85, True, .98),
                   'WetShard': floor_material('WetShard', .48, True, .38)}
    source = ROOT / P.get('debris_source', 'Assets/Adapted/ChamberParity/Parity20261007')
    manifest = json.loads((source / 'manifest.json').read_text())
    assert manifest['owner'] == OWNER and all(a['fbx_roundtrip_passed'] for a in manifest['assets'])
    wanted = {'TE_Parity20261007_' + item['name'] for item in manifest['assets']}
    for label, a in actors.items():
        if label.startswith('TE_Parity20261007_SM_Parity20261007_Debris'):
            assert 'ChamberParity20261007' in [str(t) for t in a.tags]
            a.set_actor_hidden_in_game(label not in wanted)
            a.static_mesh_component.set_editor_property('visible', label in wanted)
    u.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
    for item in manifest['assets']:
        path = NS + '/Meshes/' + item['name']
        if A.does_asset_exist(path):
            mesh = A.load_asset(path)
            assert A.get_metadata_tag(mesh, 'ChamberParity.Owner') == OWNER
            assert A.get_metadata_tag(mesh, 'ChamberParity.SourceSHA256') == item['sha256']
        else:
            assert hashlib.sha256((source / item['file']).read_bytes()).hexdigest() == item['sha256']
            options = u.FbxImportUI()
            for k, v in {'automated_import_should_detect_type': False, 'mesh_type_to_import': u.FBXImportType.FBXIT_STATIC_MESH,
                         'import_as_skeletal': False, 'import_materials': False, 'import_textures': False}.items(): options.set_editor_property(k, v)
            for k, v in {'combine_meshes': True, 'auto_generate_collision': False, 'convert_scene': True,
                         'convert_scene_unit': True, 'force_front_x_axis': False}.items(): options.static_mesh_import_data.set_editor_property(k, v)
            options.static_mesh_import_data.set_editor_property('normal_import_method', u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
            task = u.AssetImportTask()
            task.filename = str(source / item['file']); task.destination_path = NS + '/Meshes'; task.destination_name = item['name']
            task.automated = True; task.save = False; task.replace_existing = False; task.options = options
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            assert task.imported_object_paths
            mesh = A.load_asset(path)
            A.set_metadata_tag(mesh, 'ChamberParity.Owner', OWNER)
            A.set_metadata_tag(mesh, 'ChamberParity.SourceSHA256', item['sha256'])
            for i, slot in enumerate(mesh.get_editor_property('static_materials')):
                actual = str(slot.material_slot_name)
                canonical = actual.removesuffix('_001')
                assert canonical in debris_mats, actual
                mesh.set_material(i, debris_mats[canonical])
            ext = mesh.get_bounds().box_extent
            assert max(abs(a-b) for a,b in zip([ext.x*2,ext.y*2,ext.z*2],item['dimensions_cm'])) < .2
            save(mesh)
        label = 'TE_Parity20261007_' + item['name']
        a = actors.get(label) or spawn(u.StaticMeshActor, item['name'], [0, 0, 0])
        a.static_mesh_component.set_static_mesh(mesh)
        a.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        a.static_mesh_component.set_lighting_channels(True, False, False)
        a.set_actor_enable_collision(False)
    R['debris'] = {'pieces': manifest['pieces'], 'triangles': manifest['triangles'], 'collision': 'NoCollision'}
    grate = actors['TE_Room_DrainGrate_-1_0'].static_mesh_component.static_mesh
    for index, y in enumerate([-1250, -850, -450, -50, 350, 750, 1150]):
        label = 'TE_Parity20261007_FrontDrain_' + str(index)
        a = actors.get(label) or spawn(u.StaticMeshActor, 'FrontDrain_' + str(index), [-1595, y, -1.5], u.Rotator(yaw=90))
        a.set_actor_scale3d(u.Vector(1, .85, .7))
        c = a.static_mesh_component; c.set_static_mesh(grate)
        c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        a.set_actor_enable_collision(False)

    for label, a in actors.items():
        b = BASE.get(label)
        if not b or not b['lights']: continue
        c = a.get_component_by_class(u.LightComponent)
        if c is None: continue
        old = b['lights'][0]['intensity']
        if label.startswith('TE_Chamber_') and ('WallWash' in label or 'Accent' in label): c.set_editor_property('intensity', old * P['wall_light_scale'])
        if label.startswith('TE_Room_CornerBounce'): c.set_editor_property('intensity', old * P['corner_light_scale'])
    key = actors['TE_Parity_Key'].get_component_by_class(u.SpotLightComponent)
    for k, v in P['key'].items(): key.set_editor_property(k, float(v))
    front = actors['TE_Chamber_FrontFloorReturn'].get_component_by_class(u.SpotLightComponent)
    front.set_editor_property('intensity', float(P['front_floor_intensity']))
    front.set_editor_property('attenuation_radius', 1900.)
    front.set_editor_property('outer_cone_angle', 50.)
    front.set_editor_property('specular_scale', .08)
    mist = actors['TE_Parity_FarFog_Light'].get_component_by_class(u.RectLightComponent)
    for k, v in P['mist'].items(): mist.set_editor_property(k, float(v))
    shaft = actors.get('TE_Parity20261007_OverheadShaft') or spawn(u.SpotLight, 'OverheadShaft', P['shaft']['location'])
    shaft.set_actor_location(u.Vector(*P['shaft']['location']), False, False)
    shaft.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(*P['shaft']['location']), u.Vector(*P['shaft']['target'])), False)
    c = shaft.get_component_by_class(u.SpotLightComponent)
    c.set_editor_property('mobility', u.ComponentMobility.MOVABLE)
    c.set_editor_property('intensity_units', u.LightUnits.CANDELAS)
    for k, v in P['shaft'].items():
        if k not in ('location', 'target'): c.set_editor_property(k, float(v))
    c.set_editor_property('indirect_lighting_intensity', 0.)
    c.set_editor_property('source_radius', 28.)
    c.set_light_color(u.LinearColor(.32, .70, .66, 1))
    c.set_cast_shadows(True)
    c.set_lighting_channels(True, False, True)
    h = P['upper_haze']
    haze = actors.get('TE_Parity20261007_UpperHaze') or spawn(u.LocalFogVolume, 'UpperHaze', h['location'])
    haze.set_actor_location(u.Vector(*h['location']), False, False)
    haze.set_actor_scale3d(u.Vector(h['scale'], h['scale'], h['scale']))
    fog = haze.get_component_by_class(u.LocalFogVolumeComponent)
    assert fog
    for k in ('radial_fog_extinction', 'height_fog_extinction', 'fog_phase_g'): fog.set_editor_property(k, float(h[k]))
    fog.set_editor_property('fog_albedo', u.LinearColor(.66, .83, .78, 1))
    fog.set_editor_property('fog_emissive', u.LinearColor(*h['fog_emissive'], 1))
    R['fog_console_values'] = {k: u.SystemLibrary.get_console_variable_int_value(k) for k in
        ['r.VolumetricFog', 'r.LocalFogVolume', 'r.SupportLocalFogVolumes', 'r.LocalFogVolume.RenderIntoVolumetricFog']}
    assert LEV.save_current_level()
    assert LEV.load_level(MAP), 'Explicit saved-map reload required'
    (OUT / 'saved-scene.json').write_text(json.dumps(snapshot_level(), indent=2), encoding='utf-8')
    R['reloaded'] = True
    R['passed'] = True

try:
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    main()
except Exception:
    R['error'] = traceback.format_exc()
finally:
    (OUT / 'receipt.json').write_text(json.dumps(R, indent=2), encoding='utf-8')
    finish_editor(None)
