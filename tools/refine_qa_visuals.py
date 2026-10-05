"""Incremental QA art pass; run through astra_setup editor-script after backup.

Only encounter materials, light/fog properties and camera constants are changed.
No gameplay graph is replaced, no collision/attack range/timing is changed.
An authoring pass is NOT visual acceptance: rerun camera edge tests and captures.
"""
import json
import math
import os
from pathlib import Path
import sys
import traceback
from datetime import datetime, timezone

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from encounter_authoring import A, L, M, NS, asset, existing, components, compile, save

MAP = '/Game/Maps/TeddyEncounter'
OUT = Path(os.environ.get('TEDDY_QA_VISUAL_REPORT', str(
    ROOT / 'evidence/qa-repairs' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-visual-authoring.json'))))
report = {'passed': False, 'visual_acceptance': False, 'map': MAP,
          'changes': [], 'before': {}, 'requires': ['saved reopen', 'camera edge verification',
          'three reference comparisons', 'attack-warning readability', 'gameplay regression']}


def node(mat, cls, **props):
    result = M.create_material_expression(mat, cls)
    assert result
    for key, value in props.items():
        result.set_editor_property(key, value)
    return result


def link(source, target, pin, output=''):
    input_names = list(M.get_material_expression_input_names(target))
    if len(input_names) == 1 and input_names[0] in ('None', ''):
        pin = ''  # Single unnamed sockets use the empty API name in UE 5.8.
    assert M.connect_material_expressions(source, output, target, pin), (source, target, pin, list(M.get_material_expression_input_names(target)), list(M.get_material_expression_output_names(source)))


def prop(source, material, output):
    assert M.connect_material_property(source, '', output)


def scalar(mat, value):
    return node(mat, u.MaterialExpressionConstant, r=value)


def color(mat, rgb):
    return node(mat, u.MaterialExpressionConstant3Vector, constant=u.LinearColor(*rgb, 1))


def mul(mat, source, value):
    result = node(mat, u.MaterialExpressionMultiply, const_b=value)
    link(source, result, 'A')
    return result


def lerp(mat, a, b, alpha):
    result = node(mat, u.MaterialExpressionLinearInterpolate)
    for source, pin in [(a, 'A'), (b, 'B'), (alpha, 'Alpha')]:
        link(source, result, pin)
    return result


def noise(mat, position, scale):
    result = node(mat, u.MaterialExpressionNoise, scale=scale, quality=1,
                  levels=2, output_min=0., output_max=1., turbulence=False)
    # UE 5.8 exposes this as a world-position display name, not the C++ field name.
    input_names = list(M.get_material_expression_input_names(result))
    assert input_names and 'Position' in input_names[0], input_names
    link(position, result, input_names[0])
    return result


def material(name):
    # asset() refuses pre-existing destinations without the encounter ownership tag.
    result = asset('Materials/' + name, u.Material, u.MaterialFactoryNew())
    M.delete_all_material_expressions(result)
    return result


def make_floor():
    mat = material('M_QA_Concrete')
    position = node(mat, u.MaterialExpressionWorldPosition)
    broad = noise(mat, position, .0032)
    fine = noise(mat, position, .12)
    base = lerp(mat, color(mat, (.030, .039, .041)),
                color(mat, (.047, .056, .055)), broad)
    detail = lerp(mat, scalar(mat, .94), scalar(mat, 1.04), fine)
    albedo = node(mat, u.MaterialExpressionMultiply)
    link(base, albedo, 'A'); link(detail, albedo, 'B')
    # Preserve physical wear without the former 7x7 repeating slab grid. Existing
    # source textures stay untouched; broad, unequal UV repeats keep seams sparse.
    uv = node(mat, u.MaterialExpressionTextureCoordinate, u_tiling=3.1, v_tiling=2.7)
    worn = node(mat, u.MaterialExpressionTextureSample,
                texture=existing(NS + '/Arena/T_Concrete_Color'))
    link(uv, worn, 'UVs')
    worn_color = node(mat, u.MaterialExpressionMultiply, const_b=.82)
    link(worn, worn_color, 'A', 'RGB')
    prop(lerp(mat, albedo, worn_color, scalar(mat, .6)), mat, u.MaterialProperty.MP_BASE_COLOR)
    rough = lerp(mat, scalar(mat, .77), scalar(mat, .96), fine)
    prop(rough, mat, u.MaterialProperty.MP_ROUGHNESS)
    prop(scalar(mat, .2), mat, u.MaterialProperty.MP_SPECULAR)
    normal = node(mat, u.MaterialExpressionTextureSample,
                  texture=existing(NS + '/Arena/T_Concrete_Normal'),
                  sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    link(uv, normal, 'UVs')
    softened = node(mat, u.MaterialExpressionLinearInterpolate)
    link(color(mat, (0., 0., 1.)), softened, 'A')
    link(normal, softened, 'B', 'RGB')
    link(scalar(mat, .25), softened, 'Alpha')
    prop(softened, mat, u.MaterialProperty.MP_NORMAL)
    M.recompile_material(mat); save(mat)
    return mat


def make_cloth():
    mat = material('M_QA_TeddyCloth')
    mat.set_editor_property('used_with_skeletal_mesh', True)
    texture = existing(NS + '/Teddy/T_Teddy_BaseColor')
    assert texture
    sample = node(mat, u.MaterialExpressionTextureSample, texture=texture)
    desat = node(mat, u.MaterialExpressionDesaturation)
    link(sample, desat, '', 'RGB'); link(scalar(mat, .5), desat, 'Fraction')
    uv = node(mat, u.MaterialExpressionTextureCoordinate)
    uv3 = node(mat, u.MaterialExpressionAppendVector)
    link(uv, uv3, 'A'); link(scalar(mat, 0.), uv3, 'B')
    wear = noise(mat, uv3, 20.)
    modulation = lerp(mat, scalar(mat, 1.30), scalar(mat, 1.65), wear)
    base = node(mat, u.MaterialExpressionMultiply)
    link(desat, base, 'A'); link(modulation, base, 'B')
    prop(base, mat, u.MaterialProperty.MP_BASE_COLOR)
    prop(lerp(mat, scalar(mat, .84), scalar(mat, .97), wear), mat, u.MaterialProperty.MP_ROUGHNESS)
    prop(scalar(mat, .18), mat, u.MaterialProperty.MP_SPECULAR)
    # UV-anchored weave moves with the skin; subtle tangent normals, no geometry edits.
    waves = []
    for axis in ('r', 'g'):
        mask = node(mat, u.MaterialExpressionComponentMask, r=axis == 'r', g=axis == 'g', b=False, a=False)
        link(uv, mask, 'Input')
        wave = node(mat, u.MaterialExpressionSine, period=1.)
        link(mul(mat, mask, 72.), wave, 'Input')
        waves.append(mul(mat, wave, .025))
    xy = node(mat, u.MaterialExpressionAppendVector)
    link(waves[0], xy, 'A'); link(waves[1], xy, 'B')
    xyz = node(mat, u.MaterialExpressionAppendVector)
    link(xy, xyz, 'A'); link(scalar(mat, 1.), xyz, 'B')
    normal = node(mat, u.MaterialExpressionNormalize)
    link(xyz, normal, 'VectorInput'); prop(normal, mat, u.MaterialProperty.MP_NORMAL)
    M.recompile_material(mat); save(mat)
    return mat


def make_warning():
    mat = material('M_QA_AttackWarning')
    mat.set_editor_property('two_sided', True)
    c = color(mat, (.16, .051, .031))
    prop(c, mat, u.MaterialProperty.MP_BASE_COLOR)
    prop(mul(mat, c, .35), mat, u.MaterialProperty.MP_EMISSIVE_COLOR)
    prop(scalar(mat, .95), mat, u.MaterialProperty.MP_ROUGHNESS)
    M.recompile_material(mat); save(mat)
    return mat


def camera_patches(bp):
    """Return exact existing pins to update; refuse unfamiliar camera topology."""
    assert A.get_metadata_tag(bp, 'TrackingAuthored') == 'pair-framing-v2', 'Review changed camera before applying'
    nodes = u.BlueprintGraphEditor.get_graph_editor(L.find_event_graph(bp)).list_all_nodes()
    edits = []
    for pin_name, accepted, new in [
        ('B', [-.809784, -1 / math.tan(math.radians(47)), -1 / math.tan(math.radians(46))], -1 / math.tan(math.radians(46))),
        ('Min', [2100., 1850., 1700.], 1700.),
        ('B', [1.42, 1.52, 1.8], 1.8),
        ('B', [.8, 1.0], 1.0),
        ('B', [1200., 850.], 850.),
    ]:
        found = []
        for n in nodes:
            p = n.find_input_pin(pin_name)
            if not p.is_valid() or p.list_connected_pins():
                continue
            try:
                value = float(p.get_pin_value())
            except (ValueError, TypeError):
                continue
            if any(abs(value - previous) < .00001 for previous in accepted):
                found.append((p, value))
        assert len(found) == 1, (pin_name, accepted, new, len(found))
        edits.append((found[0][0], found[0][1], new))
    return edits


def change(obj, name, value):
    key = obj.get_path_name() + ':' + name
    report['before'][key] = str(obj.get_editor_property(name))
    obj.set_editor_property(name, value)


def main():
    lev = u.get_editor_subsystem(u.LevelEditorSubsystem)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    assert existing(MAP), 'Expected owned encounter map'
    assert lev.load_level(MAP)
    scene = list(actors.get_all_level_actors())
    required = ['TE_ArenaFloor', 'TE_CombatView', 'TE_AmbientFill', 'TE_Key',
                'TE_Rim', 'TE_PlayerFill', 'TE_FaceFill', 'TE_LowMist', 'TE_MainTeddy']
    for label in required:
        selected = [a for a in scene if a.get_actor_label() == label]
        assert len(selected) == 1, (label, len(selected))
        assert 'TeddyEncounterOwned' in [str(t) for t in selected[0].tags], label
    camera = existing(NS + '/Blueprints/BP_CombatCamera')
    edits = camera_patches(camera)  # Validate all graph selectors before changing assets.
    floor, cloth, warning = make_floor(), make_cloth(), make_warning()
    for name in ['BP_TeddyBoss', 'BP_Stitchling']:
        bp = existing(NS + '/Blueprints/' + name)
        for label, (_, c) in components(bp).items():
            if isinstance(c, u.SkeletalMeshComponent):
                change(c, 'override_materials', [cloth])
            elif isinstance(c, u.StaticMeshComponent) and 'AttackWarning' in label:
                change(c, 'override_materials', [warning])
        compile(bp)
    for pin, old, new in edits:
        assert pin.set_pin_value(str(new))
        report['changes'].append({'camera_pin': str(pin.get_pin_name()), 'old': old, 'new': new})
    for _, (_, c) in components(camera).items():
        if isinstance(c, u.CameraComponent):
            change(c, 'field_of_view', 48.)
    compile(camera)
    # Component overrides on placed characters can outlive Blueprint default changes.
    for a in list(actors.get_all_level_actors()):
        label = a.get_actor_label()
        if 'TeddyEncounterOwned' not in [str(t) for t in a.tags]:
            continue
        if label == 'TE_ArenaFloor':
            change(a.static_mesh_component, 'override_materials', [floor])
        if label == 'TE_MainTeddy' or label.startswith('TE_Stitchling'):
            for c in a.get_components_by_class(u.SkeletalMeshComponent):
                change(c, 'override_materials', [cloth])
            for c in a.get_components_by_class(u.StaticMeshComponent):
                if 'AttackWarning' in c.get_name():
                    change(c, 'override_materials', [warning])
        if label == 'TE_CombatView':
            rotation = a.get_actor_rotation()
            report['before']['camera_rotation'] = str(rotation)
            a.set_actor_rotation(u.Rotator(pitch=-46., yaw=rotation.yaw, roll=rotation.roll), False)
            change(a.get_component_by_class(u.CameraComponent), 'field_of_view', 48.)
        if label == 'TE_AmbientFill':
            c = a.get_component_by_class(u.DirectionalLightComponent)
            change(c, 'intensity', 2.)
        settings = {
            'TE_Key': ((0, -300, 1350), 65000., 2300., 150.),
            'TE_Rim': ((780, 720, 1250), 14000., 2050., 160.),
            'TE_PlayerFill': ((-750, 300, 1100), 9000., 2150., 200.),
            'TE_FaceFill': ((-1450, -350, 1000), 4500., 2200., 200.),
        }
        if label in settings:
            location, intensity, radius, source = settings[label]
            report['before'][label + ':location'] = str(a.get_actor_location())
            a.set_actor_location(u.Vector(*location), False, False)
            c = a.get_component_by_class(u.PointLightComponent)
            for key, value in [('intensity', intensity), ('attenuation_radius', radius), ('source_radius', source)]:
                change(c, key, value)
            change(c, 'volumetric_scattering_intensity', .65 if label == 'TE_Key' else .25)
        if label == 'TE_LowMist':
            c = a.get_component_by_class(u.ExponentialHeightFogComponent)
            for key, value in [('fog_density', .035), ('fog_height_falloff', .15),
                               ('enable_volumetric_fog', True), ('fog_max_opacity', .7)]:
                change(c, key, value)
            change(c, 'fog_inscattering_luminance', u.LinearColor(.012, .027, .033, 1))
        if label == 'TE_EdgeGlow':
            change(a.get_component_by_class(u.PointLightComponent), 'intensity', 140.)
    assert lev.save_current_level()
    assert u.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    assert lev.load_level(MAP)
    reopened = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == 'TE_ArenaFloor')
    assert reopened.static_mesh_component.get_material(0).get_path_name() == floor.get_path_name()
    report.update(passed=True, material_paths=[x.get_path_name() for x in [floor, cloth, warning]],
                  camera_pitch=-46, field_of_view=48,
                  height='clamp(max(1.8*abs(dx),1.0*abs(dy))+850,1700,5600)',
                  behavior='Attack timing, radius, collision, input and animation preserved; warning material only',
                  note='Authoring saved/reopened; rendered fidelity and edge coverage still require review')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        report['error'] = traceback.format_exc()
        raise
    finally:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
