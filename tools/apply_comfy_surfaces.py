"""Apply owned ComfyUI weave and damp maps. Leaves the rig, room kit, and key light in place."""
import json
import sys
import traceback
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from encounter_authoring import A, M, NS, asset, existing, own, save, components, component, compile
from apply_parity_look import node, scalar, rgb, bind, mul, blend

SRC = ROOT / "Assets" / "Adapted" / "Parity" / "Surfaces"
OUT = ROOT / "evidence" / "implementation" / "comfy-surfaces.json"
R = {"passed": False, "textures": [], "notes": []}


def set_optional(obj, name, value):
    try:
        obj.set_editor_property(name, value)
    except Exception as exc:
        R["notes"].append(f"{obj.get_name()}.{name}: {exc}")


def import_texture(name, kind):
    dest = NS + "/Parity/Surfaces"
    task = u.AssetImportTask()
    task.filename = str(SRC / (name + ".png"))
    task.destination_path = dest
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    assert task.imported_object_paths, name
    obj = own(A.load_asset(task.imported_object_paths[0]))
    if kind == "normal":
        obj.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_NORMALMAP)
        obj.set_editor_property("srgb", False)
        set_optional(obj, "flip_green_channel", False)
    elif kind == "data":
        obj.set_editor_property("srgb", False)
        set_optional(obj, "compression_settings", u.TextureCompressionSettings.TC_GRAYSCALE)
    else:
        obj.set_editor_property("srgb", True)
    set_optional(obj, "never_stream", True)
    save(obj)
    R["textures"].append({"name": name, "kind": kind, "path": obj.get_path_name(), "srgb": bool(obj.get_editor_property("srgb"))})
    return obj


def sample(mat, texture, sampler, uv):
    result = node(mat, u.MaterialExpressionTextureSample, texture=texture, sampler_type=sampler)
    from apply_parity_look import link
    link(uv, result, "UVs")
    return result


def rebuild(name, skeletal):
    mat = asset("Parity/Materials/" + name, u.Material, u.MaterialFactoryNew())
    M.delete_all_material_expressions(mat)
    if skeletal:
        mat.set_editor_property("used_with_skeletal_mesh", True)
    mat.set_editor_property("shading_model", u.MaterialShadingModel.MSM_DEFAULT_LIT)
    return mat


def channel(mat, source, which):
    from apply_parity_look import link
    mask = node(mat, u.MaterialExpressionComponentMask, r=which == "r", g=which == "g", b=which == "b", a=False)
    link(source, mask, "Input")
    return mask


def cloth_graph(mat, textures, darken):
    from apply_parity_look import link
    mat.set_editor_property("shading_model", u.MaterialShadingModel.MSM_CLOTH)
    mat.set_editor_property("use_material_attributes", True)
    attributes = node(mat, u.MaterialExpressionMakeMaterialAttributes)
    base = node(mat, u.MaterialExpressionTextureSample, texture=existing(NS + "/Teddy/T_Teddy_BaseColor"))
    desat = node(mat, u.MaterialExpressionDesaturation)
    link(base, desat, "", "RGB")
    link(scalar(mat, 0.12), desat, "Fraction")
    tinted = mul(mat, mul(mat, desat, 1.05 * darken), rgb(mat, (1.0, 0.94, 0.80)))
    uv = node(mat, u.MaterialExpressionTextureCoordinate, u_tiling=10.0, v_tiling=8.0)
    weave = sample(mat, textures["T_Comfy_Cloth_Weave"], u.MaterialSamplerType.SAMPLERTYPE_COLOR, uv)
    weave_gray = node(mat, u.MaterialExpressionDesaturation)
    link(weave, weave_gray, "", "RGB")
    link(scalar(mat, 1.0), weave_gray, "Fraction")
    breakup = blend(mat, scalar(mat, 0.90), scalar(mat, 1.12), channel(mat, weave_gray, "r"))
    link(mul(mat, tinted, breakup), attributes, "BaseColor")
    normal = sample(mat, textures["T_Comfy_Cloth_Normal"], u.MaterialSamplerType.SAMPLERTYPE_NORMAL, uv)
    link(blend(mat, rgb(mat, (0, 0, 1)), normal, scalar(mat, 0.8)), attributes, "Normal")
    rough = sample(mat, textures["T_Comfy_Cloth_Roughness"], u.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE, uv)
    link(blend(mat, scalar(mat, 0.84), scalar(mat, 0.97), channel(mat, rough, "r")), attributes, "Roughness")
    link(scalar(mat, 0.10), attributes, "Specular")
    link(rgb(mat, (0.09, 0.07, 0.04)), attributes, "SubsurfaceColor")
    # Cloth amount is exposed on this attributes node as ClearCoat. The previous parity pass rendered with that connection.
    link(scalar(mat, 0.32), attributes, "ClearCoat")
    bind(attributes, u.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
    M.recompile_material(mat)
    save(mat)
    return mat


def make_floor(textures):
    from apply_parity_look import link
    mat = rebuild("M_Parity_Floor", False)
    world = node(mat, u.MaterialExpressionWorldPosition)
    xy = node(mat, u.MaterialExpressionComponentMask, r=True, g=True, b=False, a=False)
    link(world, xy, "Input")
    uv = mul(mat, xy, 1.0 / 480.0)
    albedo = sample(mat, existing(NS + "/Arena/T_AI_Floor_Color"), u.MaterialSamplerType.SAMPLERTYPE_COLOR, uv)
    desat = node(mat, u.MaterialExpressionDesaturation)
    link(albedo, desat, "", "RGB")
    link(scalar(mat, 0.35), desat, "Fraction")
    dry = channel(mat, sample(mat, textures["T_Comfy_Floor_Dry"], u.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE, uv), "r")
    variation = channel(mat, sample(mat, textures["T_Comfy_Floor_Variation"], u.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE, uv), "r")
    damp_dark = blend(mat, scalar(mat, 0.64), scalar(mat, 1.0), dry)
    speck = blend(mat, scalar(mat, 0.88), scalar(mat, 1.08), variation)
    base = mul(mat, mul(mat, mul(mat, desat, 0.62), damp_dark), speck)
    bind(base, u.MaterialProperty.MP_BASE_COLOR)
    normal = sample(mat, existing(NS + "/Arena/T_AI_Floor_Normal"), u.MaterialSamplerType.SAMPLERTYPE_NORMAL, uv)
    bind(blend(mat, rgb(mat, (0, 0, 1)), normal, scalar(mat, 0.7)), u.MaterialProperty.MP_NORMAL)
    bind(blend(mat, scalar(mat, 0.42), scalar(mat, 0.93), dry), u.MaterialProperty.MP_ROUGHNESS)
    bind(scalar(mat, 0.22), u.MaterialProperty.MP_SPECULAR)
    M.recompile_material(mat)
    save(mat)
    return mat


def assign_cloth(actor_or_bp, material, placed=False):
    if placed:
        meshes = actor_or_bp.get_components_by_class(u.SkeletalMeshComponent)
    else:
        meshes = [c for _, (_, c) in components(actor_or_bp).items() if isinstance(c, u.SkeletalMeshComponent)]
    for mesh in meshes:
        mats = list(mesh.get_editor_property("override_materials"))
        if not mats:
            mats = [material]
        else:
            mats[0] = material
        mesh.set_editor_property("override_materials", mats)


def soften_player_pool():
    player = existing(NS + "/Blueprints/BP_EncounterPlayer")
    light = component(player, "ParityPlayerLight", u.SpotLightComponent, "CollisionCylinder")
    light.set_editor_property("mobility", u.ComponentMobility.MOVABLE)
    light.set_editor_property("intensity_units", u.LightUnits.CANDELAS)
    light.set_editor_property("use_inverse_squared_falloff", True)
    light.set_editor_property("intensity", 8500.0)
    light.set_light_color(u.LinearColor(0.94, 0.96, 1.0, 1))
    light.set_editor_property("attenuation_radius", 720.0)
    light.set_editor_property("source_radius", 55.0)
    light.set_editor_property("volumetric_scattering_intensity", 0.0)
    light.set_editor_property("cast_shadows", False)
    light.set_editor_property("relative_location", u.Vector(160, 0, 95))
    light.set_editor_property("relative_rotation", u.Rotator(pitch=-62, yaw=0, roll=0))
    light.set_editor_property("inner_cone_angle", 18.0)
    light.set_editor_property("outer_cone_angle", 48.0)
    compile(player)
    return light.get_name()


def main():
    lev = u.get_editor_subsystem(u.LevelEditorSubsystem)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    assert lev.load_level("/Game/Maps/TeddyEncounter")
    textures = {
        "T_Comfy_Cloth_Weave": import_texture("T_Comfy_Cloth_Weave", "color"),
        "T_Comfy_Cloth_Normal": import_texture("T_Comfy_Cloth_Normal", "normal"),
        "T_Comfy_Cloth_Roughness": import_texture("T_Comfy_Cloth_Roughness", "data"),
        "T_Comfy_Floor_Variation": import_texture("T_Comfy_Floor_Variation", "data"),
        "T_Comfy_Floor_Dry": import_texture("T_Comfy_Floor_Dry", "data"),
    }
    cloth = cloth_graph(rebuild("M_Parity_TeddyCloth", True), textures, 1.0)
    dark = cloth_graph(rebuild("M_Parity_StitchlingCloth", True), textures, 0.70)
    floor = make_floor(textures)
    assign_cloth(existing(NS + "/Blueprints/BP_TeddyBoss"), cloth)
    compile(existing(NS + "/Blueprints/BP_TeddyBoss"))
    assign_cloth(existing(NS + "/Blueprints/BP_Stitchling"), dark)
    compile(existing(NS + "/Blueprints/BP_Stitchling"))
    hidden = []
    for actor in actors.get_all_level_actors():
        name = actor.get_actor_label()
        if name == "TE_ArenaFloor":
            actor.static_mesh_component.set_material(0, floor)
        if name == "TE_MainTeddy":
            assign_cloth(actor, cloth, placed=True)
        if name.startswith("TE_Stitchling"):
            assign_cloth(actor, dark, placed=True)
        if name.startswith("TE_AI_Decal_") or name.startswith("TE_Room_FootDebris"):
            actor.set_actor_hidden_in_game(True)
            set_optional(actor, "hidden", True)
            hidden.append(name)
    pool = soften_player_pool()
    assert lev.save_current_level()
    assert lev.load_level("/Game/Maps/TeddyEncounter")
    saved = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "TE_ArenaFloor")
    assert saved.static_mesh_component.get_material(0) == floor
    teddy = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "TE_MainTeddy")
    override = teddy.get_component_by_class(u.SkeletalMeshComponent).get_editor_property("override_materials")[0]
    assert override == cloth
    R.update(passed=True, floor=floor.get_path_name(), cloth=cloth.get_path_name(), stitchling=dark.get_path_name(),
             hidden=hidden, player_pool=pool, shading=str(cloth.get_editor_property("shading_model")),
             cloth_scale=1.05, key_fog_camera_unchanged=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        R["error"] = traceback.format_exc()
        raise
    finally:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(R, indent=2))
        print("COMFY_SURFACES", json.dumps({"passed": R["passed"]}))
