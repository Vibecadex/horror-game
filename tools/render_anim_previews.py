"""Re-frame the AnimPreprod pose stills. Opens only the preprod blend."""
import bpy
import math
from mathutils import Vector
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLEND = ROOT / "Assets" / "Adapted" / "AnimPreprod" / "Teddy_AnimPreprod.blend"
OUT = BLEND.parent / "previews"
bpy.ops.wm.open_mainfile(filepath=str(BLEND))

rig = bpy.data.objects["TeddyRig"]
mesh = bpy.data.objects["Teddy_Stitched"]
rig.hide_render = True
rig.hide_set(True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "OBJECT"
scene.display.shading.show_cavity = True
mesh.color = (0.45, 0.38, 0.28, 1)
scene.render.resolution_x = 480
scene.render.resolution_y = 320
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"

camera = bpy.data.objects.get("Preprod")
if camera is None:
    camera = bpy.data.objects.new("Preprod", bpy.data.cameras.new("Preprod"))
    scene.collection.objects.link(camera)
camera.data.lens = 35
scene.camera = camera

peaks = {
    "TurnLeft": 12, "TurnRight": 12, "StepLeft": 8, "StepRight": 8, "Telegraph": 18,
    "Recover": 1, "AttackLeft": 20, "Stagger": 8, "IdleHeavy": 60, "Threat": 22,
    "WalkStop": 1, "StitchlingIdle": 30, "StitchlingFlinch": 4, "DefeatBreath": 24,
    "Brace": 10, "HitLeft": 6, "SwipeLow": 16, "Search": 24, "Slump": 1, "WeightShift": 45,
}

def frame_camera():
    deps = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(deps)
    corners = [ev.matrix_world @ Vector(corner) for corner in ev.bound_box]
    center = sum(corners, Vector()) / len(corners)
    high = max(corner.z for corner in corners)
    low = min(corner.z for corner in corners)
    span = max(high - low, 1.0)
    camera.location = center + Vector((span * 1.15, -span * 1.55, span * 0.42))
    direction = center + Vector((0, 0, span * 0.05)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    print("FRAME", tuple(round(v, 2) for v in center), "span", round(span, 2), flush=True)

for name, frame in peaks.items():
    action = bpy.data.actions.get(name)
    if action is None:
        print("MISSING", name, flush=True)
        continue
    rig.animation_data.action = action
    slots = getattr(action, "slots", None)
    if getattr(rig.animation_data, "action_slot", None) is None and slots:
        rig.animation_data.action_slot = slots[0]
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    frame_camera()
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("FRAMED", name, flush=True)

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
print("PREVIEWS_FRAMED", len(peaks), flush=True)
