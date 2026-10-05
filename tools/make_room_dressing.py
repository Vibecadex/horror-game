"""Modular chamber dressing. Run with installed Blender.

Writes Assets/Adapted/RoomDressing only. The scene importer globs
Assets/Adapted/Room/SM_*.fbx and does not see this folder. No ceiling, wheel,
tank, crate, or emissive sign. Five material slots match the room kit.
"""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Assets" / "Adapted" / "RoomDressing"
OWNER = "teddy-room-dressing-20261005"
if OUT.exists():
    marker = OUT / "manifest.json"
    if marker.exists() and json.loads(marker.read_text(encoding="utf-8"))["owner"] != OWNER:
        raise RuntimeError("Refusing to overwrite an unowned RoomDressing folder")
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0

COLORS = {
    "Metal": (0.11, 0.13, 0.125, 1),
    "Concrete": (0.16, 0.155, 0.145, 1),
    "Rust": (0.22, 0.09, 0.045, 1),
    "Dark": (0.012, 0.016, 0.018, 1),
    "Emissive": (0.02, 0.025, 0.026, 1),
}
MATS = {}
for name, color in COLORS.items():
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.62 if name == "Metal" else 0.88
    bsdf.inputs["Metallic"].default_value = 0.55 if name == "Metal" else 0.04
    MATS[name] = mat

PARTS = []
ASSETS = []
OBJECTS = []


def finish_piece(obj, mat="Metal", bevel=0):
    obj.data.materials.append(MATS[mat])
    bpy.context.view_layer.objects.active = obj
    if bevel:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    PARTS.append(obj)
    return obj


def box(name, loc, size, mat="Metal", bevel=0.008):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cap = min(bevel, min(size) * 0.18) if bevel else 0
    return finish_piece(obj, mat, cap)


def cylinder(name, loc, radius, depth, mat="Metal", axis="Z", vertices=10, bevel=0):
    rotation = {"X": (0, math.pi / 2, 0), "Y": (math.pi / 2, 0, 0), "Z": (0, 0, 0)}[axis]
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    for polygon in obj.data.polygons:
        polygon.use_smooth = len(polygon.vertices) > 4
    return finish_piece(obj, mat, bevel)


def ring(name, loc, radius, tube, mat="Metal", axis="Z", major=16, minor=5):
    rotation = {"X": (0, math.pi / 2, 0), "Y": (math.pi / 2, 0, 0), "Z": (0, 0, 0)}[axis]
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_torus_add(
        major_segments=major, minor_segments=minor, major_radius=radius, minor_radius=tube,
        location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return finish_piece(obj, mat)


def pipe(name, points, radius, mat="Metal"):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 3
    curve.bevel_depth = radius
    curve.bevel_resolution = 1
    curve.use_fill_caps = True
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, xyz in zip(spline.points, points):
        point.co = (*xyz, 1)
    obj = bpy.data.objects.new(name, curve)
    scene.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return finish_piece(obj, mat)


def bolts(xs, zs, y, radius=0.016):
    for x in xs:
        for z in zs:
            cylinder("Bolt", (x, y, z), radius, 0.018, "Metal", "Y", 6, 0)


def join_asset(name, origin_note, placement_note):
    assert PARTS, name
    bpy.ops.object.select_all(action="DESELECT")
    for obj in PARTS:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + "_Geometry"
    scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    old_slots = [slot.material.name for slot in obj.material_slots]
    indices = [list(MATS).index(old_slots[p.material_index]) for p in obj.data.polygons]
    obj.data.materials.clear()
    for mat in MATS.values():
        obj.data.materials.append(mat)
    for polygon, index in zip(obj.data.polygons, indices):
        polygon.material_index = index
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.update()
    obj.data.calc_loop_triangles()
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = [min(p[i] for p in points) for i in range(3)]
    maximum = [max(p[i] for p in points) for i in range(3)]
    triangles = len(obj.data.loop_triangles)
    entry = {
        "name": name, "file": name + ".fbx", "triangles": triangles,
        "vertices": len(obj.data.vertices),
        "bounds_m": {"min": minimum, "max": maximum},
        "dimensions_m": [maximum[i] - minimum[i] for i in range(3)],
        "expected_dimensions_cm": [round(100 * (maximum[i] - minimum[i]), 2) for i in range(3)],
        "origin": origin_note, "front": "Blender local -Y", "placement": placement_note,
        "material_slots": list(MATS),
        "collision": "None. Decorative. Keep it outside the combat footprint.",
    }
    bpy.ops.export_scene.fbx(
        filepath=str(OUT / entry["file"]), use_selection=True, object_types={"MESH"},
        axis_forward="-Y", axis_up="Z", global_scale=1, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_NONE", use_mesh_modifiers=True,
        mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False, path_mode="AUTO")
    entry["sha256"] = hashlib.sha256((OUT / entry["file"]).read_bytes()).hexdigest()
    ASSETS.append(entry)
    OBJECTS.append(obj)
    PARTS.clear()
    print("DRESS_ASSET", name, triangles, [round(v, 3) for v in entry["dimensions_m"]], flush=True)
    return obj


def wall_panel(width, height, rib_z, seam_x):
    box("Back", (0, 0.035, height * 0.5), (width, 0.05, height), "Concrete", 0.008)
    lip = 0.08
    box("Stile L", (-width * 0.5 + lip * 0.5, -0.02, height * 0.5), (lip, 0.09, height), "Metal", 0.005)
    box("Stile R", (width * 0.5 - lip * 0.5, -0.02, height * 0.5), (lip, 0.09, height), "Metal", 0.005)
    box("Rail T", (0, -0.02, height - lip * 0.5), (width, 0.09, lip), "Metal", 0.005)
    box("Rail B", (0, -0.02, lip * 0.5), (width, 0.09, lip), "Metal", 0.005)
    box("Recess", (0, 0.02, height * 0.5), (width - 0.20, 0.025, height - 0.20), "Dark", 0.003)
    box("Rib", (0, -0.035, rib_z), (width - 0.18, 0.035, 0.055), "Metal", 0.003)
    box("Seam", (seam_x, -0.03, height * 0.55), (0.028, 0.02, height * 0.62), "Dark", 0.002)
    bolts((-width * 0.5 + 0.06, width * 0.5 - 0.06), (0.08, height - 0.08), -0.07, 0.014)


wall_panel(2.40, 3.20, 1.70, 0.38)
join_asset("SM_DressPanel", "Floor Z=0. Back sits on +Y. Recess faces -Y.",
           "Tile on the interior face of the shell bays. Vary yaw only to face the room. Alternate with SM_DressPanelAlt.")

wall_panel(2.40, 3.20, 0.95, -0.42)
join_asset("SM_DressPanelAlt", "Same module as the first panel, rib and seam shifted.",
           "Pair with SM_DressPanel so a wall is not one repeated stamp.")

wall_panel(1.20, 3.20, 1.85, 0.12)
join_asset("SM_DressPanelNarrow", "1.20 m wide, same depth and height.",
           "Close a bay that the 2.40 m panel does not fill.")

box("Back", (0, 0.04, 2.40), (2.40, 0.05, 4.80), "Concrete", 0.008)
for z, mat in ((0.70, "Metal"), (2.40, "Rust"), (4.10, "Metal")):
    box("Rail", (0, -0.02, z), (2.40, 0.09, 0.08), mat, 0.004)
box("Stile L", (-1.16, -0.02, 2.40), (0.08, 0.09, 4.80), "Metal", 0.004)
box("Stile R", (1.16, -0.02, 2.40), (0.08, 0.09, 4.80), "Metal", 0.004)
box("Recess low", (0, 0.02, 1.45), (2.05, 0.02, 1.30), "Dark", 0.002)
box("Recess high", (0, 0.02, 3.35), (2.05, 0.02, 1.35), "Dark", 0.002)
bolts((-1.08, 1.08), (0.2, 2.2, 4.5), -0.07, 0.014)
join_asset("SM_DressPanelTall", "Floor Z=0. Two stacked recesses. Faces -Y.",
           "Far wall and the taller side bays. One or two per cluster, not a full grid of identical tall panels.")

box("Rib", (0, 0, 1.60), (0.14, 0.11, 3.20), "Metal", 0.006)
box("Shoe", (0, 0.02, 0.07), (0.26, 0.16, 0.14), "Rust", 0.005)
for z in (0.45, 1.25, 2.15, 2.90):
    cylinder("Rib bolt", (0, -0.07, z), 0.016, 0.016, "Metal", "Y", 6, 0)
join_asset("SM_DressRib", "Floor Z=0. Projects toward -Y.",
           "Vertical cover between panels. Thinner than SM_RoomPilaster. Do not replace the pilaster.")

box("Plate", (0, -0.01, 0.32), (0.82, 0.028, 0.52), "Metal", 0.004)
box("Older plate", (0.06, -0.02, 0.38), (0.40, 0.016, 0.24), "Rust", 0.003)
bolts((-0.32, 0.32), (0.12, 0.52), -0.035, 0.014)
join_asset("SM_DressRepairPlate", "Bottom at Z=0. Face -Y.",
           "One bolted patch per service cluster. Not a row.")

box("Host", (0, 0.03, 0.30), (0.92, 0.07, 0.60), "Concrete", 0.006)
box("Void", (0.06, -0.005, 0.24), (0.40, 0.05, 0.26), "Dark", 0.003)
box("Lip", (0.24, -0.02, 0.38), (0.18, 0.04, 0.07), "Concrete", 0.004)
box("Chip", (-0.22, -0.015, 0.12), (0.14, 0.04, 0.05), "Concrete", 0.003)
join_asset("SM_DressWallSpall", "Bottom at Z=0. Broken face -Y.",
           "A few bites on the lower wall. This is wall damage, not a floor debris card.")

for offset in (-0.07, 0.07):
    pipe(f"Conduit {offset}", [(-1.0, offset, 0.09), (1.0, offset, 0.09)], 0.03, "Metal")
for x in (-0.66, 0.0, 0.66):
    box("Saddle", (x, 0, 0.045), (0.05, 0.24, 0.04), "Rust", 0.002)
    cylinder("Stud", (x, 0, 0.02), 0.012, 0.03, "Metal", "Z", 6, 0)
join_asset("SM_DressConduitStraight", "Mount at Z=0. Long axis X. 2 m.",
           "Right wall and short jumps on the left. Smaller than SM_RoomPipeRack. Do not replace that rack.")

pipe("Elbow", [(0.0, 0.0, 0.08), (0.22, 0.0, 0.08), (0.40, -0.20, 0.08)], 0.03, "Metal")
box("Ear", (0.0, 0.03, 0.04), (0.14, 0.04, 0.12), "Metal", 0.003)
cylinder("Ear bolt", (0.0, -0.005, 0.04), 0.012, 0.012, "Metal", "Y", 6, 0)
join_asset("SM_DressConduitElbow", "Corner near the origin. Turn goes toward -Y.",
           "Ends of a conduit run. Keep the turn outside the walk ring.")

pipe("Tee main", [(-0.38, 0, 0.08), (0.38, 0, 0.08)], 0.032, "Rust")
pipe("Tee branch", [(0, 0, 0.08), (0, -0.34, 0.08)], 0.03, "Rust")
ring("Tee collar", (0, 0, 0.08), 0.055, 0.012, "Metal", "Y", 12, 5)
join_asset("SM_DressConduitTee", "Branch leaves toward -Y.",
           "One or two where a run splits. No valve.")

box("Box body", (0, 0.04, 0.18), (0.36, 0.16, 0.32), "Metal", 0.006)
box("Box seam", (0, -0.05, 0.18), (0.30, 0.012, 0.26), "Dark", 0.002)
pipe("Stub L", [(-0.18, 0.02, 0.18), (-0.36, 0.02, 0.18)], 0.025, "Rust")
pipe("Stub R", [(0.18, 0.02, 0.18), (0.36, 0.02, 0.18)], 0.025, "Rust")
pipe("Stub down", [(0, 0.02, 0.04), (0, 0.02, -0.08)], 0.025, "Rust")
bolts((-0.12, 0.12), (0.08, 0.28), -0.06, 0.01)
join_asset("SM_DressJunctionBox", "Back on +Y. Cover faces -Y.",
           "Where conduits meet. Right wall mostly. The down stub may hang below the origin.")

pipe("Loop", [(-0.42, 0.0, 0.55), (-0.28, -0.04, 0.22), (0.0, -0.08, 0.04), (0.28, -0.04, 0.22), (0.42, 0.0, 0.55)], 0.022, "Dark")
box("Clamp L", (-0.42, 0.02, 0.52), (0.06, 0.05, 0.10), "Metal", 0.003)
box("Clamp R", (0.42, 0.02, 0.52), (0.06, 0.05, 0.10), "Metal", 0.003)
join_asset("SM_DressCableLoop", "Clamps near Z=0.55. The loop sags toward -Y.",
           "One short loop in a cluster, as the art direction describes. Not a hanging mass over the fight.")

for shift in (-0.015, 0.0, 0.015):
    pipe(f"Drop {shift}", [(shift, 0, 1.45), (shift, -0.02, 0.35), (shift * 2, -0.05, 0.08)], 0.012, "Dark")
box("Clip", (0, 0.02, 1.40), (0.08, 0.04, 0.08), "Metal", 0.002)
box("Coil", (0, -0.04, 0.06), (0.10, 0.08, 0.08), "Dark", 0.002)
join_asset("SM_DressCableDrop", "Top clip at Z=1.45. Bundle hangs to the floor.",
           "From the cable tray down to a junction box. Right wall.")

pipe("Bend", [(0, 0, 0.10), (0, 0, 0.32), (0.14, 0, 0.48), (0.42, 0, 0.48)], 0.05, "Rust")
ring("Flange up", (0, 0, 0.10), 0.085, 0.014, "Metal", "Z", 14, 5)
ring("Flange out", (0.42, 0, 0.48), 0.085, 0.014, "Metal", "X", 14, 5)
join_asset("SM_DressPipeElbow", "Vertical leg on Z, horizontal leg toward +X. No wheel.",
           "Turn at the end of a left-wall pipe run. The rack already has its valve. Do not add one.")

cylinder("Spool", (0, 0, 0.10), 0.048, 0.40, "Rust", "X", 12, 0)
ring("Flange A", (-0.12, 0, 0.10), 0.086, 0.014, "Metal", "X", 14, 5)
ring("Flange B", (0.12, 0, 0.10), 0.086, 0.014, "Metal", "X", 14, 5)
box("Gasket", (0, 0, 0.10), (0.018, 0.15, 0.15), "Dark", 0)
join_asset("SM_DressFlangeJoint", "Pipe along X at Z=0.10.",
           "Visible joint in a pipe run. Bolted flanges, muted rust.")

box("Hanger plate", (0, 0.02, 0.22), (0.24, 0.03, 0.18), "Metal", 0.004)
cylinder("Rod", (0, -0.04, 0.08), 0.012, 0.22, "Metal", "Z", 6, 0)
cylinder("Clevis", (0, -0.04, -0.02), 0.055, 0.16, "Rust", "X", 10, 0)
join_asset("SM_DressPipeHanger", "Plate at the top. Clevis hangs below Z=0.",
           "Under a left-wall run, between the larger saddles.")

box("Breaker body", (0, 0.05, 0.42), (0.50, 0.16, 0.82), "Metal", 0.006)
door = box("Breaker door", (0.05, -0.045, 0.44), (0.44, 0.018, 0.72), "Metal", 0.003)
door.rotation_euler = (0, math.radians(14), 0)
box("Hinge", (-0.22, -0.02, 0.44), (0.03, 0.04, 0.66), "Rust", 0.002)
box("Latch", (0.18, -0.07, 0.40), (0.04, 0.02, 0.08), "Dark", 0.001)
join_asset("SM_DressBreaker", "Floor Z=0. Door ajar toward -Y.",
           "Right wall only. Smaller than SM_RoomServiceCabinet. Door stays dark. No glowing panel.")

box("Gang back", (0, 0.025, 0.08), (0.34, 0.05, 0.14), "Metal", 0.003)
for x in (-0.10, 0.0, 0.10):
    box("Gang cover", (x, -0.015, 0.08), (0.08, 0.012, 0.10), "Dark", 0.001)
    cylinder("Gang screw", (x, -0.025, 0.12), 0.008, 0.008, "Metal", "Y", 6, 0)
join_asset("SM_DressGangBox", "Back on +Y.",
           "Small blank covers beside the breaker. Right wall.")

for shift in (-0.02, 0.0, 0.02):
    pipe(f"Bundle {shift}", [(-0.9, shift, 0.06), (0.9, shift * 0.4, 0.055)], 0.014, "Dark")
for x in (-0.55, 0.05, 0.60):
    box("Tie", (x, 0, 0.06), (0.035, 0.09, 0.07), "Rust", 0.002)
join_asset("SM_DressBundle", "Long axis X, on the floor line.",
           "Along the right-wall foot. Not a second cable spool.")

box("Threshold", (0, 0, 0.012), (1.80, 0.34, 0.018), "Metal", 0)
box("Nose", (0, -0.16, 0.02), (1.80, 0.028, 0.02), "Metal", 0)
for x in (-0.60, -0.20, 0.20, 0.60):
    cylinder("Screw", (x, 0.06, 0.025), 0.012, 0.012, "Dark", "Z", 6, 0)
join_asset("SM_DressThreshold", "Floor Z=0. Long axis X. Nose toward -Y.",
           "At the bulkhead sill. One plate. Not a ramp into a hall.")

box("Anchor plate", (0, 0, 0.016), (0.38, 0.38, 0.024), "Metal", 0.003)
for x in (-0.11, 0.11):
    for y in (-0.11, 0.11):
        cylinder("Anchor bolt", (x, y, 0.04), 0.016, 0.035, "Rust", "Z", 6, 0)
join_asset("SM_DressAnchor", "Floor Z=0.",
           "A few floor anchors along the far utility strip and wall foot.")

box("Drain floor", (0, 0, 0.02), (0.52, 0.52, 0.03), "Dark", 0.002)
box("Drain wall L", (-0.24, 0, 0.05), (0.04, 0.52, 0.08), "Concrete", 0.003)
box("Drain wall R", (0.24, 0, 0.05), (0.04, 0.52, 0.08), "Concrete", 0.003)
box("Drain wall N", (0, -0.24, 0.05), (0.46, 0.04, 0.08), "Concrete", 0.003)
box("Drain wall F", (0, 0.24, 0.05), (0.46, 0.04, 0.08), "Concrete", 0.003)
for x in (-0.12, 0.0, 0.12):
    box("Drain bar", (x, 0, 0.07), (0.02, 0.42, 0.015), "Metal", 0.001)
join_asset("SM_DressDrainBox", "Floor Z=0. Square local drain.",
           "Perimeter only, beside the gutter. Not a substitute for SM_RoomFloorGrate and not a stripe.")

box("Kicker", (0, 0, 0.07), (1.20, 0.18, 0.14), "Concrete", 0.006)
box("Scuff", (0, -0.07, 0.045), (0.84, 0.03, 0.04), "Dark", 0.002)
join_asset("SM_DressKicker", "Floor Z=0. Long axis X.",
           "Short footing blocks along the cutaway and the far strip. Low. Not a wall.")

box("Louver frame", (0, 0.02, 0.36), (0.92, 0.10, 0.70), "Metal", 0.005)
box("Louver void", (0, -0.01, 0.36), (0.74, 0.04, 0.52), "Dark", 0.002)
for index, z in enumerate((0.18, 0.30, 0.42, 0.54)):
    slat = box("Slat", (0, -0.04, z), (0.70, 0.012, 0.06), "Metal", 0.001)
    slat.rotation_euler = (math.radians(28), 0, 0)
join_asset("SM_DressLouver", "Bottom at Z=0. Slats face -Y.",
           "Small wall vent. The big fan remains SM_RoomVentFan. One or two louvers, not a row.")

box("Hatch frame", (0, 0.025, 0.40), (0.78, 0.08, 0.78), "Metal", 0.005)
box("Hatch door", (0, -0.02, 0.40), (0.62, 0.025, 0.62), "Metal", 0.004)
box("Hatch seal", (0, -0.005, 0.40), (0.66, 0.012, 0.66), "Dark", 0.001)
cylinder("Dog", (-0.16, -0.045, 0.40), 0.02, 0.04, "Rust", "Y", 6, 0)
cylinder("Dog B", (0.16, -0.045, 0.40), 0.02, 0.04, "Rust", "Y", 6, 0)
cylinder("Hinge", (0, -0.01, 0.74), 0.02, 0.50, "Metal", "X", 6, 0)
join_asset("SM_DressHatch", "Bottom at Z=0. Closed cover faces -Y.",
           "Closed maintenance hatch. The dogs are handles, not a locking wheel. No path behind it.")

ring("Hose", (0, -0.02, 0.28), 0.20, 0.028, "Dark", "Y", 24, 6)
ring("Hose inner", (0, -0.01, 0.28), 0.13, 0.024, "Dark", "Y", 20, 5)
box("Hook", (0, 0.04, 0.52), (0.08, 0.06, 0.22), "Metal", 0.003)
pipe("Hose end", [(0.16, -0.08, 0.28), (0.22, -0.16, 0.10), (0.10, -0.18, 0.02)], 0.02, "Rust")
join_asset("SM_DressHoseCoil", "Hook above the coil. Coil faces -Y.",
           "One coil on a side wall. Not a second spool family and not a tank.")

box("Shaft", (0, 0, 2.10), (0.50, 0.50, 4.20), "Concrete", 0.016)
box("Column base", (0, 0, 0.08), (0.72, 0.72, 0.16), "Dark", 0.008)
box("Column cap", (0, 0, 4.16), (0.62, 0.62, 0.10), "Metal", 0.006)
for z in (0.95, 2.30, 3.45):
    box("Collar", (0, 0, z), (0.58, 0.58, 0.07), "Rust", 0.004)
for x in (-0.26, 0.26):
    for y in (-0.26, 0.26):
        cylinder("Base bolt", (x, y, 0.18), 0.016, 0.03, "Metal", "Z", 6, 0)
join_asset("SM_DressColumn", "Floor Z=0. 0.50 m shaft, 4.20 m tall.",
           "Far corners only, outside X=1480 and |Y|=1500. Not a pilaster and not a tank.")

box("Lintel", (0, 0, 0.20), (3.40, 0.46, 0.36), "Metal", 0.01)
box("Soffit", (0, -0.12, 0.05), (3.10, 0.16, 0.08), "Dark", 0.004)
for x in (-1.2, 0.0, 1.2):
    box("Stiffener", (x, -0.02, 0.22), (0.06, 0.40, 0.28), "Rust", 0.004)
join_asset("SM_DressHeader", "Soffit toward -Y. Seat the top against the wall.",
           "Above the bulkhead opening if the door head needs a separate lintel. Not a roof beam across the room.")

box("Guard A", (0.045, 0, 0.60), (0.09, 0.016, 1.20), "Metal", 0.003)
box("Guard B", (0, 0.045, 0.60), (0.016, 0.09, 1.20), "Metal", 0.003)
for z in (0.2, 0.6, 1.0):
    cylinder("Guard bolt", (0.07, -0.01, z), 0.012, 0.012, "Rust", "Y", 6, 0)
join_asset("SM_DressCornerGuard", "The angle wraps +X and +Y. Height 1.20 m.",
           "Outside corners of pilasters and the cutaway returns.")

box("Strut", (0, 0, 0.02), (2.00, 0.041, 0.041), "Metal", 0.002)
for x in (-0.75, -0.35, 0.05, 0.45, 0.85):
    box("Slot", (x, -0.012, 0.02), (0.10, 0.008, 0.016), "Dark", 0)
join_asset("SM_DressUnistrut", "Long axis X. Open side -Y.",
           "Short perimeter support. Do not link copies into a truss across the arena.")

box("Tray floor", (0, 0, 0.012), (1.10, 0.40, 0.016), "Rust", 0)
box("Tray lip L", (-0.54, 0, 0.04), (0.02, 0.40, 0.06), "Rust", 0.001)
box("Tray lip R", (0.54, 0, 0.04), (0.02, 0.40, 0.06), "Rust", 0.001)
box("Tray lip N", (0, -0.19, 0.04), (1.06, 0.02, 0.06), "Rust", 0.001)
box("Tray lip F", (0, 0.19, 0.04), (1.06, 0.02, 0.06), "Rust", 0.001)
join_asset("SM_DressDripTray", "Floor Z=0.",
           "Under a pipe joint on the left wall. One or two.")

pipe("Spout", [(0, 0, 1.70), (0, 0, 0.28), (0.06, -0.10, 0.08)], 0.038, "Rust")
box("Strap", (0, 0.03, 1.25), (0.12, 0.04, 0.05), "Metal", 0.002)
box("Strap B", (0, 0.03, 0.55), (0.12, 0.04, 0.05), "Metal", 0.002)
join_asset("SM_DressDownspout", "Wall straps on +Y. Outlet turns toward -Y.",
           "Vertical drop at a wall, outlet above the gutter. Not a second pipe rack.")

box("Meter body", (0, 0.04, 0.18), (0.28, 0.12, 0.34), "Dark", 0.005)
box("Bezel", (0, -0.035, 0.20), (0.18, 0.02, 0.18), "Metal", 0.002)
cylinder("Glass", (0, -0.05, 0.20), 0.055, 0.012, "Dark", "Y", 12, 0)
pipe("Meter lead", [(0.10, 0.02, 0.08), (0.28, 0.02, 0.08)], 0.016, "Rust")
join_asset("SM_DressMeter", "Face -Y. Glass is dark.",
           "One gauge on the pipe side. The face stays unlit.")

box("Clamp plate", (0, 0.02, 0.06), (0.14, 0.03, 0.10), "Metal", 0.002)
cylinder("U bolt", (0, -0.02, 0.05), 0.028, 0.10, "Rust", "Y", 8, 0)
cylinder("Nut L", (-0.04, 0.035, 0.09), 0.012, 0.012, "Metal", "Y", 6, 0)
cylinder("Nut R", (0.04, 0.035, 0.09), 0.012, 0.012, "Metal", "Y", 6, 0)
join_asset("SM_DressClamp", "Plate on +Y.",
           "Single pipe clamp. Use to break the rhythm of a run.")

box("Escutcheon", (0, 0, 0.16), (0.32, 0.02, 0.32), "Metal", 0.003)
cylinder("Penetration", (0, -0.012, 0.16), 0.055, 0.03, "Dark", "Y", 10, 0)
bolts((-0.11, 0.11), (0.06, 0.26), -0.02, 0.01)
join_asset("SM_DressEscutcheon", "Plate in the Y=0 plane. Pipe read faces -Y.",
           "Where a pipe passes through a panel. The dark cylinder is the penetration, not a hole you can enter.")

box("Plenum", (0, 0.08, 0.24), (0.62, 0.28, 0.40), "Metal", 0.006)
cylinder("Boot round", (0, -0.18, 0.24), 0.13, 0.16, "Metal", "Y", 12, 0.004)
box("Boot flange", (0, 0.22, 0.24), (0.74, 0.03, 0.52), "Rust", 0.004)
join_asset("SM_DressDuctBoot", "Flange on +Y, round outlet toward -Y.",
           "A short duct transition. Not another fan and not a ceiling run.")

total = sum(entry["triangles"] for entry in ASSETS)
assert len(ASSETS) >= 30, len(ASSETS)
assert total < 120000, total
for entry in ASSETS:
    assert entry["triangles"] < 14000, (entry["name"], entry["triangles"])
    lowered = entry["name"].lower()
    for banned in ("wheel", "tank", "crate", "ceiling", "barrel"):
        assert banned not in lowered, entry["name"]

roundtrips = []
for entry in ASSETS:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(OUT / entry["file"]), use_anim=False)
    loaded = [obj for obj in set(bpy.data.objects) - before]
    meshes = [obj for obj in loaded if obj.type == "MESH"]
    assert len(meshes) == 1, (entry["name"], [obj.type for obj in loaded])
    obj = meshes[0]
    bpy.context.view_layer.update()
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    dims = [max(p[i] for p in points) - min(p[i] for p in points) for i in range(3)]
    error = max(abs(a - b) for a, b in zip(dims, entry["dimensions_m"]))
    assert error < 0.00002, (entry["name"], dims, entry["dimensions_m"], error)
    obj.data.calc_loop_triangles()
    assert len(obj.data.loop_triangles) == entry["triangles"]
    assert len(obj.material_slots) == 5
    roundtrips.append({
        "name": entry["name"], "dimensions_m": dims, "max_dimension_error_m": error,
        "triangles": len(obj.data.loop_triangles), "material_slots": 5, "passed": True,
    })
    for extra in loaded:
        bpy.data.objects.remove(extra, do_unlink=True)

manifest = {
    "owner": OWNER,
    "source": "Original dressing modules for the chamber. Room kit and room shell were not modified.",
    "generator": "tools/make_room_dressing.py",
    "blender_version": bpy.app.version_string,
    "coordinate_system": "Metres, Z up, detailed face -Y. Same FBX axis setup as the room kit.",
    "fbx_settings": {
        "axis_forward": "-Y", "axis_up": "Z", "global_scale": 1,
        "apply_unit_scale": True, "apply_scale_options": "FBX_SCALE_NONE",
    },
    "material_slots": list(MATS),
    "total_triangles": total,
    "assets": ASSETS,
    "fbx_roundtrip_checks": roundtrips,
    "not_included": [
        "ceiling slab", "valve wheel", "locking wheel", "second tank", "second crate",
        "barrel", "luminous sign", "baked teal", "baked player pool",
    ],
    "limits": "On disk only. Place outside the combat footprint. No collision. Repeat panels and fittings in clusters, with gaps, rather than one continuous stripe.",
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

lines = ["# Room dressing", "",
         "Off the level. This folder is not on the room-kit import path.",
         "Use it with `Assets/Adapted/Room/` and `Assets/Adapted/RoomShell/`.",
         "The detailed face is local −Y. Confirm the imported facing the same way as the bulkhead.",
         "Keep every copy outside X −1400..1480 and Y −1500..1500. No collision.",
         "",
         "There is no ceiling, wheel, tank, crate, or lit sign in this set.",
         "",
         "| Mesh | Triangles | Centimetres |",
         "| --- | ---: | --- |"]
for entry in ASSETS:
    dims = " × ".join(str(int(round(v))) for v in entry["expected_dimensions_cm"])
    lines.append(f"| `{entry['name']}` | {entry['triangles']} | {dims} |")
lines.append("")
lines.append("Panels tile on the shell. Conduits, the breaker, the gang box, and the cable drop belong on the right wall. Pipe elbows, hangers, the meter, and the drip tray belong on the left. The column is a far-corner piece only.")
lines.append("")
(OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

for index, obj in enumerate(OBJECTS):
    column = index % 6
    row = index // 6
    obj.location = (column * 3.6, -row * 5.8, 0)
    obj.rotation_euler = (0, 0, 0)

bpy.ops.mesh.primitive_plane_add(size=80, location=(9, -14, -0.02))
ground = bpy.context.object
ground.name = "Preview ground (not exported)"
ground_mat = bpy.data.materials.new("Preview ground")
ground_mat.diffuse_color = (0.03, 0.035, 0.036, 1)
ground.data.materials.append(ground_mat)
world = bpy.data.worlds.new("Preview")
world.use_nodes = True
background = world.node_tree.nodes["Background"]
background.inputs["Color"].default_value = (0.015, 0.02, 0.024, 1)
background.inputs["Strength"].default_value = 0.35
scene.world = world
for name, loc, energy in (("Key", (6, -28, 16), 4000), ("Fill", (24, -8, 8), 900)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.size = 6
    data.color = (0.75, 0.88, 1.0) if name == "Key" else (0.55, 0.62, 0.66)
    lamp = bpy.data.objects.new(name, data)
    scene.collection.objects.link(lamp)
    lamp.location = loc
    lamp.rotation_euler = (Vector((9, -12, 2)) - lamp.location).to_track_quat("-Z", "Y").to_euler()
camera_data = bpy.data.cameras.new("Dressing overview")
camera = bpy.data.objects.new("Dressing overview", camera_data)
scene.collection.objects.link(camera)
target = Vector((9, -14, 1.6))
camera.location = target + Vector((22, -20, 16))
camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
camera_data.type = "ORTHO"
camera_data.ortho_scale = 42
scene.camera = camera
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 12
scene.cycles.use_denoising = True
scene.render.resolution_x = 1800
scene.render.resolution_y = 1200
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.render.filepath = str(OUT / "dressing-overview.png")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "RoomDressing_Kit.blend"))
bpy.ops.render.render(write_still=True)
print("DRESS_KIT_COMPLETE", json.dumps({"assets": len(ASSETS), "triangles": total}), flush=True)
