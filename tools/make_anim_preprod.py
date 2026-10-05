"""Key additional in-place clips on a copy of the existing teddy rig.

Opens Teddy_Encounter.blend, saves a new blend under Assets/Adapted/AnimPreprod,
and never writes the source blend back. The sixteen bones and the six shipped
actions stay in the copy. New actions are rotation offsets from Idle or from
the last Defeat frame.
"""
import bpy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Assets" / "Adapted" / "Teddy" / "Teddy_Encounter.blend"
OUT = ROOT / "Assets" / "Adapted" / "AnimPreprod"
OWNER = "teddy-anim-preprod-20261005"
if OUT.exists():
    marker = OUT / "manifest.json"
    if marker.exists() and json.loads(marker.read_text(encoding="utf-8"))["owner"] != OWNER:
        raise RuntimeError("Refusing to overwrite an unowned AnimPreprod folder")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "previews").mkdir(exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(SRC))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "Teddy_AnimPreprod.blend"))

rig = bpy.data.objects["TeddyRig"]
mesh = bpy.data.objects["Teddy_Stitched"]
scene = bpy.context.scene
scene.render.fps = 30
scene.frame_start = 1
D = math.radians

bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")


def bind(action):
    ad = rig.animation_data
    if ad is None:
        rig.animation_data_create()
        ad = rig.animation_data
    ad.action = action
    slots = getattr(action, "slots", None)
    if slots is not None and len(slots) == 0:
        slots.new(id_type="OBJECT", name="TeddyRig")
    if getattr(ad, "action_slot", None) is None and slots:
        ad.action_slot = slots[0]


def capture(action_name, frame):
    bind(bpy.data.actions[action_name])
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    pose = {}
    for bone in rig.pose.bones:
        bone.rotation_mode = "XYZ"
        pose[bone.name] = (tuple(bone.rotation_euler), tuple(bone.location))
    return pose


IDLE = capture("Idle", 1)
DEFEAT = capture("Defeat", 72)


def smooth(curves):
    for curve in curves:
        for key in curve.keyframe_points:
            key.interpolation = "BEZIER"
            key.handle_left_type = "AUTO_CLAMPED"
            key.handle_right_type = "AUTO_CLAMPED"


def action_curves(action):
    found = list(getattr(action, "fcurves", []) or [])
    layers = getattr(action, "layers", None)
    if layers:
        for layer in layers:
            for strip in getattr(layer, "strips", []) or []:
                bag = getattr(strip, "channelbag", None)
                if bag and getattr(bag, "fcurves", None):
                    found.extend(bag.fcurves)
    return found


def build(name, frames, base, keys):
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    bind(action)
    for frame, delta in keys:
        scene.frame_set(frame)
        for bone in rig.pose.bones:
            rotation, location = base[bone.name]
            add = delta.get(bone.name, (0.0, 0.0, 0.0))
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = tuple(rotation[i] + add[i] for i in range(3))
            bone.location = location
            bone.keyframe_insert("rotation_euler", frame=frame)
            bone.keyframe_insert("location", frame=frame)
    smooth(action_curves(action))
    action.frame_range = (1, frames)
    return action


# Pitch is local X. Negative upper-arm X raises the arm. Small Z is the shipped sway.
# Spine Z at 25 degrees folded the chest, so turns and the search yaw use local Y.
CLIPS = {
    "TurnLeft": (24, IDLE, [
        (1, {}),
        (12, {"spine": (0, D(22), 0), "head": (0, D(14), 0), "thigh_L": (D(8), 0, 0), "shin_L": (D(-6), 0, 0)}),
        (24, {}),
    ]),
    "TurnRight": (24, IDLE, [
        (1, {}),
        (12, {"spine": (0, D(-22), 0), "head": (0, D(-14), 0), "thigh_R": (D(8), 0, 0), "shin_R": (D(-6), 0, 0)}),
        (24, {}),
    ]),
    "StepLeft": (20, IDLE, [
        (1, {}),
        (8, {"pelvis": (0, 0, D(6)), "thigh_L": (D(14), 0, D(8)), "shin_L": (D(-10), 0, 0), "thigh_R": (D(-4), 0, 0)}),
        (20, {}),
    ]),
    "StepRight": (20, IDLE, [
        (1, {}),
        (8, {"pelvis": (0, 0, D(-6)), "thigh_R": (D(14), 0, D(-8)), "shin_R": (D(-10), 0, 0), "thigh_L": (D(-4), 0, 0)}),
        (20, {}),
    ]),
    "Telegraph": (18, IDLE, [
        (1, {}),
        (18, {"spine": (D(-10), 0, 0), "head": (D(8), 0, 0), "upperarm_R": (D(-55), 0, 0), "forearm_R": (D(-14), 0, 0)}),
    ]),
    "Recover": (16, IDLE, [
        (1, {"spine": (D(18), 0, 0), "head": (D(8), 0, 0), "upperarm_R": (D(20), 0, 0), "forearm_R": (D(8), 0, 0)}),
        (16, {}),
    ]),
    "AttackLeft": (36, IDLE, [
        (1, {}),
        (10, {"spine": (D(-8), 0, 0), "head": (D(6), 0, 0), "upperarm_L": (D(-50), 0, 0), "forearm_L": (D(-12), 0, 0)}),
        (20, {"spine": (D(16), 0, 0), "head": (D(8), 0, 0), "upperarm_L": (D(22), 0, 0), "forearm_L": (D(6), 0, 0)}),
        (36, {}),
    ]),
    "Stagger": (24, IDLE, [
        (1, {}),
        (8, {"spine": (D(18), 0, D(8)), "head": (D(10), 0, D(6)), "upperarm_L": (D(16), 0, 0), "upperarm_R": (D(16), 0, 0)}),
        (24, {}),
    ]),
    "IdleHeavy": (120, IDLE, [
        (1, {}),
        (60, {"spine": (D(3), 0, 0), "head": (D(2), D(2), 0), "upperarm_L": (D(2), 0, 0), "upperarm_R": (D(2), 0, 0)}),
        (120, {}),
    ]),
    "Threat": (45, IDLE, [
        (1, {}),
        (22, {"spine": (D(-8), 0, 0), "head": (D(6), 0, 0), "upperarm_L": (D(-28), 0, 0), "upperarm_R": (D(-28), 0, 0)}),
        (45, {}),
    ]),
    "WalkStop": (16, IDLE, [
        (1, {"thigh_L": (D(12), 0, 0), "shin_L": (D(-8), 0, 0), "thigh_R": (D(-6), 0, 0), "spine": (D(4), 0, 0)}),
        (16, {}),
    ]),
    "StitchlingIdle": (60, IDLE, [
        (1, {"spine": (D(8), 0, 0), "head": (D(6), 0, 0)}),
        (30, {"spine": (D(10), 0, D(3)), "head": (D(8), 0, D(4)), "upperarm_L": (D(4), 0, 0)}),
        (60, {"spine": (D(8), 0, 0), "head": (D(6), 0, 0)}),
    ]),
    "StitchlingFlinch": (12, IDLE, [
        (1, {"spine": (D(8), 0, 0)}),
        (4, {"spine": (D(18), 0, D(6)), "head": (D(12), 0, D(6)), "upperarm_L": (D(10), 0, 0), "upperarm_R": (D(10), 0, 0)}),
        (12, {"spine": (D(8), 0, 0)}),
    ]),
    "DefeatBreath": (48, DEFEAT, [
        (1, {}),
        (24, {"spine": (D(2.5), 0, 0), "head": (D(1.5), 0, 0)}),
        (48, {}),
    ]),
    "Brace": (20, IDLE, [
        (1, {}),
        (10, {"spine": (D(8), 0, 0), "head": (D(4), 0, 0), "upperarm_L": (D(-20), 0, 0), "upperarm_R": (D(-20), 0, 0), "forearm_L": (D(-30), 0, 0), "forearm_R": (D(-30), 0, 0)}),
        (20, {}),
    ]),
    "HitLeft": (18, IDLE, [
        (1, {}),
        (6, {"spine": (D(8), D(-12), 0), "head": (D(6), D(-10), 0), "upperarm_L": (D(18), 0, 0), "upperarm_R": (D(6), 0, 0)}),
        (18, {}),
    ]),
    "SwipeLow": (28, IDLE, [
        (1, {"spine": (D(12), 0, 0), "head": (D(8), 0, 0)}),
        (8, {"spine": (D(8), 0, D(8)), "upperarm_R": (D(-16), 0, 0), "forearm_R": (D(-8), 0, 0)}),
        (16, {"spine": (D(18), 0, D(-6)), "upperarm_R": (D(24), 0, 0), "forearm_R": (D(6), 0, 0)}),
        (28, {"spine": (D(12), 0, 0)}),
    ]),
    "Search": (72, IDLE, [
        (1, {}),
        (24, {"spine": (0, D(14), 0), "head": (D(-4), D(16), 0)}),
        (48, {"spine": (0, D(-14), 0), "head": (D(-4), D(-16), 0)}),
        (72, {}),
    ]),
    "Slump": (30, IDLE, [
        (1, {"spine": (D(14), 0, D(6)), "head": (D(12), 0, 0), "upperarm_L": (D(20), 0, D(-8)), "upperarm_R": (D(20), 0, D(8))}),
        (30, {}),
    ]),
    "WeightShift": (90, IDLE, [
        (1, {}),
        (45, {"pelvis": (0, 0, D(4)), "spine": (0, 0, D(-3)), "thigh_L": (D(4), 0, D(4)), "thigh_R": (D(-2), 0, 0), "head": (D(1), D(3), 0)}),
        (90, {}),
    ]),
}

built = []
for name, (frames, base, keys) in CLIPS.items():
    build(name, frames, base, keys)
    built.append((name, frames))
    print("ANIM_KEYED", name, frames, flush=True)


def export(path):
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, object_types={"ARMATURE", "MESH"},
        add_leaf_bones=False, bake_anim=True, bake_anim_use_all_actions=False,
        bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0,
        axis_forward="-Y", axis_up="Z", apply_unit_scale=True, mesh_smooth_type="FACE")
    bpy.ops.object.mode_set(mode="POSE")


clips = []
for name, frames in built:
    rig.animation_data.action = bpy.data.actions[name]
    scene.frame_start = 1
    scene.frame_end = frames
    scene.frame_set(1)
    path = OUT / f"Teddy_{name}.fbx"
    export(path)
    clips.append({
        "name": name, "frames": frames, "fps": 30, "in_place": True,
        "file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "base": "Defeat frame 72" if name == "DefeatBreath" else "Idle frame 1",
    })
    print("ANIM_EXPORTED", name, flush=True)

# One still per clip at its strongest pose, for the preprod sheet.
for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
eevee = getattr(scene, "eevee", None)
if eevee is not None and hasattr(eevee, "taa_render_samples"):
    eevee.taa_render_samples = 16
scene.render.resolution_x = 480
scene.render.resolution_y = 320
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
camera_data = bpy.data.cameras.new("Preprod")
camera = bpy.data.objects.new("Preprod", camera_data)
scene.collection.objects.link(camera)
camera.location = (3.4, -4.6, 2.2)
camera.rotation_euler = (math.radians(68), 0, math.radians(36))
scene.camera = camera
world = bpy.data.worlds.new("Preprod")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.03, 0.034, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.4
scene.world = world
peaks = {
    "TurnLeft": 12, "TurnRight": 12, "StepLeft": 8, "StepRight": 8, "Telegraph": 18,
    "Recover": 1, "AttackLeft": 20, "Stagger": 8, "IdleHeavy": 60, "Threat": 22,
    "WalkStop": 1, "StitchlingIdle": 30, "StitchlingFlinch": 4, "DefeatBreath": 24,
    "Brace": 10, "HitLeft": 6, "SwipeLow": 16, "Search": 24, "Slump": 1, "WeightShift": 45,
}
for name, _frames in built:
    rig.animation_data.action = bpy.data.actions[name]
    scene.frame_set(peaks[name])
    scene.render.filepath = str(OUT / "previews" / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("ANIM_PREVIEW", name, flush=True)

bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "Teddy_AnimPreprod.blend"))
shipped = ["Idle", "Walk", "Crawl", "Attack", "Hit", "Defeat"]
manifest = {
    "owner": OWNER,
    "source_blend": "Assets/Adapted/Teddy/Teddy_Encounter.blend",
    "source_written": False,
    "skeleton": "Teddy_Skeleton",
    "bones": [bone.name for bone in rig.data.bones],
    "shipped_clips_unchanged": shipped,
    "new_clips": clips,
    "notes": "In-place offsets for the existing rig. Import as animation only onto the encounter skeleton. Stitchling clips are the same bones; the actor stays at 0.35 scale. DefeatBreath holds the grounded defeat and does not stand up.",
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("ANIM_PREPROD_COMPLETE", len(clips), flush=True)
