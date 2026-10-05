"""Import original AI floor, plush, and decal maps onto the existing encounter.

Replaces sampling inside the owned floor and cloth materials. Does not replace
the teddy mesh, skeleton, clips, or GLB, and does not change lights, fog,
exposure, camera, combat, or room actors. Run through astra_setup editor-script.
"""
import json
import sys
import traceback
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from encounter_authoring import A, M, NS, asset, components, compile, existing, own, save

MAP = '/Game/Maps/TeddyEncounter'
OUT = ROOT / 'evidence' / 'implementation' / 'ai-surfaces.json'
SRC = ROOT / 'Assets' / 'Adapted' / 'Arena'
report = {
    'passed': False,
    'visual_acceptance': False,
    'map': MAP,
    'lights_fog_exposure_camera_combat_unchanged': True,
    'mesh_replaced': False,
    'textures': [],
    'materials': [],
    'decals': [],
    'notes': [],
}


def node(mat, cls, **props):
    result = M.create_material_expression(mat, cls)
    assert result
    for key, value in props.items():
        result.set_editor_property(key, value)
    return result


def link(source, target, pin, output=''):
    input_names = list(M.get_material_expression_input_names(target))
    if len(input_names) == 1 and input_names[0] in ('None', ''):
        pin = ''
    assert M.connect_material_expressions(source, output, target, pin), (
        source, target, pin, input_names, list(M.get_material_expression_output_names(source)))


def bind(source, prop, output=''):
    assert M.connect_material_property(source, output, prop), (source, output, prop)


def scalar(mat, value):
    return node(mat, u.MaterialExpressionConstant, r=value)


def color(mat, rgb):
    return node(mat, u.MaterialExpressionConstant3Vector, constant=u.LinearColor(*rgb, 1))


def lerp(mat, a, b, alpha, a_output='', b_output=''):
    result = node(mat, u.MaterialExpressionLinearInterpolate)
    link(a, result, 'A', a_output)
    link(b, result, 'B', b_output)
    link(alpha, result, 'Alpha')
    return result


def material(name):
    result = asset('Materials/' + name, u.Material, u.MaterialFactoryNew())
    M.delete_all_material_expressions(result)
    return result


def set_optional(obj, name, value):
    try:
        obj.set_editor_property(name, value)
    except Exception as exc:
        report['notes'].append(f'{obj.get_name()}.{name}: {exc}')


def import_texture(name, kind):
    path = NS + '/Arena/' + name
    task = u.AssetImportTask()
    task.filename = str(SRC / (name + '.png'))
    task.destination_path = NS + '/Arena'
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    assert task.imported_object_paths, name
    obj = own(A.load_asset(task.imported_object_paths[0]))
    assert obj.get_name() == name, (name, obj.get_path_name())
    if kind == 'normal':
        obj.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_NORMALMAP)
        obj.set_editor_property('srgb', False)
        set_optional(obj, 'flip_green_channel', False)
    elif kind == 'rough':
        obj.set_editor_property('srgb', False)
        set_optional(obj, 'compression_settings', u.TextureCompressionSettings.TC_GRAYSCALE)
    else:
        obj.set_editor_property('srgb', True)
        set_optional(obj, 'compression_no_alpha', False)
    set_optional(obj, 'never_stream', True)
    save(obj)
    report['textures'].append({
        'name': name,
        'kind': kind,
        'path': obj.get_path_name(),
        'srgb': bool(obj.get_editor_property('srgb')),
        'compression': str(obj.get_editor_property('compression_settings')),
    })
    return obj


def sample(mat, texture, sampler, uv=None):
    result = node(mat, u.MaterialExpressionTextureSample, texture=texture, sampler_type=sampler)
    if uv is not None:
        link(uv, result, 'UVs')
    return result


def make_floor_material(textures):
    mat = material('M_QA_Concrete')
    # Cube UV covers the full 60 m slab. About 9 by 7 repeats keeps cracks
    # near a few metres and avoids a square seam.
    uv = node(mat, u.MaterialExpressionTextureCoordinate, u_tiling=9.0, v_tiling=7.0)
    albedo = sample(mat, textures['T_AI_Floor_Color'], u.MaterialSamplerType.SAMPLERTYPE_COLOR, uv)
    darkened = node(mat, u.MaterialExpressionMultiply, const_b=0.20)
    link(albedo, darkened, 'A', 'RGB')
    bind(darkened, u.MaterialProperty.MP_BASE_COLOR)
    normal = sample(mat, textures['T_AI_Floor_Normal'], u.MaterialSamplerType.SAMPLERTYPE_NORMAL, uv)
    bind(normal, u.MaterialProperty.MP_NORMAL, 'RGB')
    rough = sample(mat, textures['T_AI_Floor_Roughness'], u.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE, uv)
    span = node(mat, u.MaterialExpressionLinearInterpolate)
    link(scalar(mat, 0.78), span, 'A')
    link(scalar(mat, 0.96), span, 'B')
    link(rough, span, 'Alpha', 'R')
    bind(span, u.MaterialProperty.MP_ROUGHNESS)
    bind(scalar(mat, 0.18), u.MaterialProperty.MP_SPECULAR)
    M.recompile_material(mat)
    save(mat)
    report['materials'].append({'name': 'M_QA_Concrete', 'path': mat.get_path_name(), 'uv': [9.0, 7.0], 'albedo_scale': 0.20})
    return mat


def make_cloth_material(name, textures):
    mat = material(name)
    mat.set_editor_property('used_with_skeletal_mesh', True)
    base_tex = existing(NS + '/Teddy/T_Teddy_BaseColor')
    assert base_tex, 'Owned teddy base color is missing'
    sample_base = node(mat, u.MaterialExpressionTextureSample, texture=base_tex)
    desat = node(mat, u.MaterialExpressionDesaturation)
    link(sample_base, desat, '', 'RGB')
    link(scalar(mat, 0.5), desat, 'Fraction')
    uv = node(mat, u.MaterialExpressionTextureCoordinate)
    uv3 = node(mat, u.MaterialExpressionAppendVector)
    link(uv, uv3, 'A')
    link(scalar(mat, 0.), uv3, 'B')
    wear = node(mat, u.MaterialExpressionNoise, scale=20., quality=1, levels=2,
                output_min=0., output_max=1., turbulence=False)
    wear_inputs = list(M.get_material_expression_input_names(wear))
    assert wear_inputs and 'Position' in wear_inputs[0], wear_inputs
    link(uv3, wear, wear_inputs[0])
    modulation = lerp(mat, scalar(mat, 1.30), scalar(mat, 1.65), wear)
    base = node(mat, u.MaterialExpressionMultiply)
    link(desat, base, 'A')
    link(modulation, base, 'B')
    bind(base, u.MaterialProperty.MP_BASE_COLOR)
    fiber_uv = node(mat, u.MaterialExpressionTextureCoordinate, u_tiling=7.5, v_tiling=6.2)
    rough = sample(mat, textures['T_AI_Plush_Roughness'], u.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE, fiber_uv)
    span = node(mat, u.MaterialExpressionLinearInterpolate)
    link(scalar(mat, 0.84), span, 'A')
    link(scalar(mat, 0.97), span, 'B')
    link(rough, span, 'Alpha', 'R')
    bind(span, u.MaterialProperty.MP_ROUGHNESS)
    bind(scalar(mat, 0.18), u.MaterialProperty.MP_SPECULAR)
    normal = sample(mat, textures['T_AI_Plush_Normal'], u.MaterialSamplerType.SAMPLERTYPE_NORMAL, fiber_uv)
    softened = node(mat, u.MaterialExpressionLinearInterpolate)
    link(color(mat, (0., 0., 1.)), softened, 'A')
    link(normal, softened, 'B', 'RGB')
    link(scalar(mat, 0.62), softened, 'Alpha')
    bind(softened, u.MaterialProperty.MP_NORMAL)
    shading = 'MSM_DEFAULT_LIT'
    cloth_pin = None
    try:
        mat.set_editor_property('shading_model', u.MaterialShadingModel.MSM_CLOTH)
        bind(color(mat, (0.45, 0.42, 0.40)), u.MaterialProperty.MP_SUBSURFACE_COLOR)
        cloth_prop, cloth_pin = cloth_amount_property()
        if cloth_prop is None:
            raise RuntimeError('Cloth amount pin is not in MaterialProperty')
        bind(scalar(mat, 0.15), cloth_prop)
        shading = 'MSM_CLOTH'
    except Exception as exc:
        report['notes'].append(f'{name} cloth shading fallback: {exc}')
        set_optional(mat, 'shading_model', u.MaterialShadingModel.MSM_DEFAULT_LIT)
        shading = 'MSM_DEFAULT_LIT'
    M.recompile_material(mat)
    save(mat)
    report['materials'].append({
        'name': name,
        'path': mat.get_path_name(),
        'shading_model': shading,
        'cloth_pin': cloth_pin,
        'base_color': base_tex.get_path_name(),
        'fiber_uv': [7.5, 6.2],
        'normal_strength': 0.62,
    })
    return mat


def cloth_amount_property():
    """Cloth amount is EMaterialProperty value 16. UE 5.8 Python omits the name."""
    names = [name for name in dir(u.MaterialProperty) if name.startswith('MP_')]
    folded = {name.replace('_', '').upper(): name for name in names}
    for key in ('MPCUSTOMDATA0', 'MPCLOTH'):
        if key in folded:
            return getattr(u.MaterialProperty, folded[key]), folded[key]
    sub = int(u.MaterialProperty.MP_SUBSURFACE_COLOR)
    ambient = int(u.MaterialProperty.MP_AMBIENT_OCCLUSION)
    report['notes'].append(f'subsurface={sub} ambient={ambient}')
    # These two values have stayed 15 and 18, with custom data 0 between them.
    if sub != 15 or ambient != 18:
        report['notes'].append('No cloth-amount pin; staying default lit. MP_ names: ' + ', '.join(names))
        return None, None
    member = None
    for factory in (lambda: u.MaterialProperty(16), lambda: u.MaterialProperty.cast(16)):
        try:
            member = factory()
            break
        except Exception as exc:
            report['notes'].append(f'MaterialProperty(16): {exc}')
    if member is not None and int(member) == 16 and 'UV' not in str(member).upper():
        report['notes'].append(f'cloth pin by value 16: {member}')
        return member, str(member)
    report['notes'].append('No cloth-amount pin; staying default lit. MP_ names: ' + ', '.join(names))
    return None, None


def make_decal_material(name, texture, color_scale, opacity_scale):
    mat = material(name)
    # UE 5.8 retires Material.DecalBlendMode. Deferred decals take the material
    # blend mode, and unconnected channels are left alone.
    mat.set_editor_property('material_domain', u.MaterialDomain.MD_DEFERRED_DECAL)
    mat.set_editor_property('blend_mode', u.BlendMode.BLEND_TRANSLUCENT)
    stamp = node(mat, u.MaterialExpressionTextureSample, texture=texture,
                 sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR)
    darkened = node(mat, u.MaterialExpressionMultiply, const_b=color_scale)
    link(stamp, darkened, 'A', 'RGB')
    bind(darkened, u.MaterialProperty.MP_BASE_COLOR)
    fade = node(mat, u.MaterialExpressionMultiply, const_b=opacity_scale)
    link(stamp, fade, 'A', 'A')
    bind(fade, u.MaterialProperty.MP_OPACITY)
    M.recompile_material(mat)
    save(mat)
    report['materials'].append({
        'name': name, 'path': mat.get_path_name(),
        'domain': 'MD_DEFERRED_DECAL', 'color_scale': color_scale, 'opacity_scale': opacity_scale,
    })
    return mat


def assign_cloth(cloth):
    for name in ['BP_TeddyBoss', 'BP_Stitchling']:
        bp = existing(NS + '/Blueprints/' + name)
        assert bp, name
        for label, (_, component) in components(bp).items():
            if isinstance(component, u.SkeletalMeshComponent):
                component.set_editor_property('override_materials', [cloth])
                report['notes'].append(f'{name}.{label} override -> {cloth.get_name()}')
        compile(bp)


def main():
    lev = u.get_editor_subsystem(u.LevelEditorSubsystem)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    assert existing(MAP), 'Expected owned encounter map'
    assert lev.load_level(MAP)
    textures = {}
    for name, kind in [
        ('T_AI_Floor_Color', 'color'),
        ('T_AI_Floor_Normal', 'normal'),
        ('T_AI_Floor_Roughness', 'rough'),
        ('T_AI_Plush_Normal', 'normal'),
        ('T_AI_Plush_Roughness', 'rough'),
        ('T_AI_Decal_Crack', 'decal'),
        ('T_AI_Decal_Stain', 'decal'),
        ('T_AI_Decal_Scuff', 'decal'),
        ('T_AI_Decal_Debris', 'decal'),
    ]:
        textures[name] = import_texture(name, kind)
    floor = make_floor_material(textures)
    cloth = make_cloth_material('M_QA_TeddyCloth', textures)
    make_cloth_material('M_TeddyCloth', textures)
    decal_mats = {
        'Crack': make_decal_material('M_AI_Decal_Crack', textures['T_AI_Decal_Crack'], 0.18, 0.50),
        'Stain': make_decal_material('M_AI_Decal_Stain', textures['T_AI_Decal_Stain'], 0.28, 0.46),
        'Scuff': make_decal_material('M_AI_Decal_Scuff', textures['T_AI_Decal_Scuff'], 0.24, 0.40),
        'Debris': make_decal_material('M_AI_Decal_Debris', textures['T_AI_Decal_Debris'], 0.22, 0.44),
    }
    assign_cloth(cloth)
    floor_actor = None
    for actor in list(actors.get_all_level_actors()):
        label = actor.get_actor_label()
        if label.startswith('TE_AI_Decal_'):
            assert 'TeddyEncounterOwned' in [str(tag) for tag in actor.tags], label
            assert actors.destroy_actor(actor)
            continue
        if label.startswith('TE_Room_') or 'FullRoomOwned' in [str(tag) for tag in actor.tags]:
            continue
        if 'TeddyEncounterOwned' not in [str(tag) for tag in actor.tags]:
            continue
        if label == 'TE_ArenaFloor':
            floor_actor = actor
            actor.static_mesh_component.set_editor_property('override_materials', [floor])
        if label == 'TE_MainTeddy' or label.startswith('TE_Stitchling'):
            for component in actor.get_components_by_class(u.SkeletalMeshComponent):
                component.set_editor_property('override_materials', [cloth])
    assert floor_actor, 'TE_ArenaFloor missing'
    origin, extent = floor_actor.get_actor_bounds(False)
    top = origin.z + extent.z
    assert -80.0 < top < 80.0, (top, str(origin), str(extent))
    placements = [
        ('01', 'Crack', 80, 360, 18, 220, 760, 240),
        ('02', 'Stain', -460, 40, -33, 200, 520, 460),
        ('03', 'Scuff', 700, -60, 72, 180, 340, 220),
        ('04', 'Debris', -40, -560, 148, 200, 400, 320),
    ]
    for index, (suffix, key, x, y, yaw, depth, width, height) in enumerate(placements):
        actor = actors.spawn_actor_from_class(
            u.DecalActor, u.Vector(x, y, top + 40), u.Rotator(pitch=-90, yaw=yaw, roll=0), transient=False)
        assert actor
        label = 'TE_AI_Decal_' + suffix
        actor.set_actor_label(label)
        actor.set_editor_property('tags', ['TeddyEncounterOwned'])
        component = actor.get_component_by_class(u.DecalComponent)
        assert component, label
        component.set_decal_material(decal_mats[key])
        component.set_editor_property('decal_size', u.Vector(depth, width, height))
        set_optional(component, 'sort_order', index)
        set_optional(component, 'fade_screen_size', 0.0)
        report['decals'].append({
            'label': label, 'material': key, 'location': [x, y, top + 40],
            'yaw': yaw, 'decal_size': [depth, width, height],
        })
    assert lev.save_current_level()
    assert u.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    assert lev.load_level(MAP)
    reopened = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == 'TE_ArenaFloor')
    applied = reopened.static_mesh_component.get_material(0)
    assert applied.get_path_name() == floor.get_path_name(), applied.get_path_name()
    saved = [a.get_actor_label() for a in actors.get_all_level_actors() if a.get_actor_label().startswith('TE_AI_Decal_')]
    assert sorted(saved) == [row['label'] for row in report['decals']], saved
    report.update(passed=True, floor_top_z=top, floor_material=applied.get_path_name(),
                  decal_labels=saved,
                  note='Surfaces saved and the map reopened. Lighting and rendered grade are a later plate.')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        report['error'] = traceback.format_exc()
        raise
    finally:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps({'passed': report['passed'], 'receipt': str(OUT)}))
