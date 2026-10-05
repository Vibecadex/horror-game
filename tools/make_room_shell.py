"""Author the chamber shell that is still engine boxes. Run with installed Blender.

Outputs stay in Assets/Adapted/RoomShell. tools/build_full_room.py globs only
Assets/Adapted/Room/SM_*.fbx, so this folder is not imported by the scene pass.
Meshes use the room kit's metres, Z-up, -Y front, and five material slots.
No ceiling, wheel, tank, crate family, or baked light.
"""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Assets" / "Adapted" / "RoomShell"
OWNER = "teddy-room-shell-20261005"
WALL_H = 7.60
if OUT.exists():
    marker = OUT / "manifest.json"
    if marker.exists() and json.loads(marker.read_text(encoding="utf-8"))["owner"] != OWNER:
        raise RuntimeError("Refusing to overwrite an unowned RoomShell folder")
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
    "Emissive": (0.05, 0.22, 0.24, 1),
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
    if name == "Emissive":
        bsdf.inputs["Emission Color"].default_value = color
        bsdf.inputs["Emission Strength"].default_value = 1.2
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


def box(name, loc, size, mat="Metal", bevel=0.012):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cap = min(bevel, min(size) * 0.18) if bevel else 0
    return finish_piece(obj, mat, cap)


def cylinder(name, loc, radius, depth, mat="Metal", axis="Z", vertices=12, bevel=0):
    rotation = {"X": (0, math.pi / 2, 0), "Y": (math.pi / 2, 0, 0), "Z": (0, 0, 0)}[axis]
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    for polygon in obj.data.polygons:
        polygon.use_smooth = len(polygon.vertices) > 4
    return finish_piece(obj, mat, bevel)


def ring(name, loc, radius, tube, mat="Metal", axis="Z", major=20, minor=6):
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


def beam(name, start, end, width, depth, mat="Metal", bevel=0.006):
    start, end = Vector(start), Vector(end)
    obj = box(name, tuple((start + end) / 2), (width, depth, (end - start).length), mat, bevel)
    obj.rotation_euler = (end - start).to_track_quat("Z", "Y").to_euler()
    return obj


def pipe(name, points, radius, mat="Metal"):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 3
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
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


def join_asset(name, origin_note, placement_note):
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
        "name": name,
        "file": name + ".fbx",
        "triangles": triangles,
        "vertices": len(obj.data.vertices),
        "bounds_m": {"min": minimum, "max": maximum},
        "dimensions_m": [maximum[i] - minimum[i] for i in range(3)],
        "expected_dimensions_cm": [round(100 * (maximum[i] - minimum[i]), 2) for i in range(3)],
        "origin": origin_note,
        "front": "Blender local -Y",
        "placement": placement_note,
        "material_slots": list(MATS),
        "collision": "None. Decorative shell. Do not add a second collision volume.",
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
    print("SHELL_ASSET", name, triangles, [round(v, 3) for v in entry["dimensions_m"]], flush=True)
    return obj


def wall_bay(width, leak_x, tie_x):
    half = width * 0.5
    box("Wall mass", (0, 0.06, WALL_H * 0.5), (width, 1.08, WALL_H), "Concrete", 0.018)
    box("Lower plinth", (0, -0.52, 0.40), (width - 0.08, 0.16, 0.80), "Dark", 0.01)
    box("Mid joint", (0, -0.505, 2.40), (width - 0.22, 0.03, 0.028), "Dark", 0.004)
    box("High joint", (0, -0.50, 5.55), (width - 0.30, 0.025, 0.022), "Dark", 0.004)
    box("Vertical joint", (leak_x * 0.15, -0.505, WALL_H * 0.5), (0.028, 0.025, WALL_H - 0.24), "Dark", 0.004)
    for z in (1.05, 1.52, 1.99, 2.82, 3.29, 3.76, 4.23, 4.70, 5.95, 6.42, 6.89):
        box("Form board", (0, -0.505, z), (width - 0.20, 0.03, 0.018), "Concrete", 0)
    box("Spall", (leak_x * 0.4, -0.53, 0.98), (0.26, 0.045, 0.07), "Concrete", 0.006)
    box("Leak", (leak_x, -0.545, 1.35), (0.055, 0.02, 1.70), "Dark", 0.003)
    box("Embed", (half * 0.55, -0.545, 6.35), (0.42, 0.028, 0.26), "Metal", 0.006)
    for x in (-0.12, 0.12):
        cylinder("Embed bolt", (half * 0.55 + x, -0.57, 6.35), 0.02, 0.02, "Metal", "Y", 6, 0)
    for x in tie_x:
        for z in (1.35, 3.15, 5.05, 6.55):
            cylinder("Form tie", (x, -0.555, z), 0.032, 0.025, "Rust", "Y", 8, 0)


# 1-2. Retaining bays. Interior face is local Y=-0.60. Thickness center is the origin.
wall_bay(4.00, -0.85, (-1.35, -0.35, 0.70))
join_asset(
    "SM_ShellWallBay",
    "Floor Z=0. Thickness center X/Y. Interior face local Y=-0.60. Top Z=7.60.",
    "Replace FarWall and SideWall boxes. Far wall: yaw like the bulkhead so the interior face sits on X=1660, step 400 cm along Y. Sides: yaw 0 at Y=-1740 and yaw 180 at Y=+1740, step 400 cm along X. Do not also leave the wall boxes up.")

wall_bay(2.00, 0.35, (-0.45, 0.50))
join_asset(
    "SM_ShellWallBayNarrow",
    "Same section as the 4 m bay, 2.00 m wide.",
    "Close a span that is not a multiple of 400 cm. One narrow bay plus eight wide bays covers the far 34 m span. Do not scale.")

# 3. Steel ledge. Z=0 is the seat on top of the wall. Brackets hang below.
box("Cornice shelf", (0, -0.24, 0.07), (4.00, 0.52, 0.10), "Metal", 0.008)
box("Cornice fascia", (0, -0.02, 0.14), (4.00, 0.08, 0.20), "Metal", 0.006)
for x in (-1.20, 1.20):
    box("Cornice bracket", (x, -0.20, -0.14), (0.07, 0.30, 0.32), "Metal", 0.005)
    box("Cornice brace", (x, -0.32, -0.02), (0.045, 0.18, 0.06), "Rust", 0.004)
join_asset(
    "SM_ShellCornice",
    "Z=0 seats on the wall top. Shelf projects toward -Y. Brackets extend below 0.",
    "Place at Z=760 on each wall bay, same yaw as that wall. This is the upper ledge, not a roof.")

# 4. Footing that projects into the room.
box("Footing mass", (0, -0.22, 0.18), (4.00, 0.70, 0.36), "Concrete", 0.014)
box("Footing nose", (0, -0.52, 0.30), (3.88, 0.14, 0.08), "Concrete", 0.006)
box("Footing damp", (0, -0.42, 0.045), (3.60, 0.12, 0.06), "Dark", 0.003)
for x in (-1.35, -0.40, 0.55, 1.45):
    cylinder("Footing bolt", (x, -0.50, 0.36), 0.028, 0.035, "Metal", "Z", 6, 0)
join_asset(
    "SM_ShellFoundation",
    "Floor Z=0. Most of the mass projects toward -Y, 13 cm tucks toward +Y.",
    "Along the interior foot of each wall, 400 cm centers. Replaces SideFoundation and FarFoundation boxes.")

# 5. Discontinuous drain channel, 48 cm wide.
box("Gutter shoulder L", (-1.53, 0, 0.09), (0.98, 0.48, 0.18), "Concrete", 0.008)
box("Gutter shoulder R", (1.53, 0, 0.09), (0.98, 0.48, 0.18), "Concrete", 0.008)
box("Gutter lip N", (0, -0.20, 0.09), (2.16, 0.08, 0.18), "Concrete", 0.004)
box("Gutter lip F", (0, 0.20, 0.09), (2.16, 0.08, 0.18), "Concrete", 0.004)
box("Gutter floor", (0, 0, 0.03), (2.20, 0.36, 0.06), "Dark", 0.003)
join_asset(
    "SM_ShellGutter",
    "Floor Z=0. Open recess is the middle 2.2 m. Long axis X.",
    "Near Y=±1560, outside the walk ring, 400 cm centers. The recess is the dark strip. Set the existing grate beside it. Do not scale the grate down into the slot, and do not run one channel across the arena.")

# 6. Broken foreground sill, 42–68 cm, not a wall.
box("Sill toe", (0, 0, 0.21), (3.40, 1.22, 0.42), "Concrete", 0.016)
box("Sill middle", (-0.15, 0.02, 0.49), (1.70, 1.02, 0.16), "Concrete", 0.008)
box("Sill high", (0.85, 0.02, 0.59), (0.90, 0.96, 0.18), "Concrete", 0.008)
box("Sill cap", (0.85, 0.0, 0.70), (1.05, 1.10, 0.04), "Metal", 0.004)
box("Drain mouth", (-1.20, -0.28, 0.07), (0.40, 0.34, 0.10), "Dark", 0.004)
box("Sill chip", (-1.40, 0.22, 0.46), (0.28, 0.18, 0.08), "Concrete", 0.006)
join_asset(
    "SM_ShellCutawaySill",
    "Floor Z=0. Broken end is the -X side at 42 cm. High stub is about 68 cm plus a short metal cap. Long axis X.",
    "Around X=-1540, spanning ±Y, with gaps between copies. Present the chipped face toward world -X. Replaces CutawaySill and CutawayCap boxes. Do not raise it into a wall.")

# 7. Short pier where a side wall meets the cutaway.
box("Return mass", (0, 0, 0.46), (1.15, 1.15, 0.92), "Concrete", 0.02)
box("Return step", (0.08, -0.08, 0.98), (0.72, 0.72, 0.16), "Concrete", 0.01)
box("Return plinth", (0, -0.04, 0.16), (1.22, 1.22, 0.32), "Dark", 0.01)
join_asset(
    "SM_ShellCutawayReturn",
    "Floor Z=0. Top about 1.06 m. Footprint about 1.2 m.",
    "Two copies only, at the near corners where the side walls meet the sill, outside X=-1480 and |Y|=1500. Not a fourth wall.")

# 8. Framed recess for the far wall, between pilasters.
box("Inset back", (0, 0.14, 1.85), (3.70, 0.08, 3.15), "Dark", 0.006)
box("Inset jamb L", (-1.95, -0.02, 1.85), (0.22, 0.36, 3.55), "Concrete", 0.012)
box("Inset jamb R", (1.95, -0.02, 1.85), (0.22, 0.36, 3.55), "Concrete", 0.012)
box("Inset sill", (0, -0.04, 0.14), (4.05, 0.34, 0.22), "Concrete", 0.01)
box("Inset header", (0, -0.08, 3.58), (4.28, 0.30, 0.18), "Metal", 0.01)
box("Inset leak", (-0.70, 0.09, 1.40), (0.05, 0.02, 1.55), "Dark", 0)
box("Inset leak B", (0.95, 0.09, 1.15), (0.04, 0.018, 1.10), "Dark", 0)
join_asset(
    "SM_ShellRearInset",
    "Floor of the opening at Z=0. Opening faces -Y. About 4.2 m wide and 3.6 m tall.",
    "Far wall between pilasters, yaw matched to that wall. Replaces RearInset and RearHeader boxes. The bulkhead door stays the landmark. No sign.")

# 9. Right-wall shuttered niche. Not a cabinet.
box("Niche back", (0, 0.12, 1.15), (1.50, 0.06, 1.65), "Dark", 0.005)
box("Niche jamb L", (-0.84, -0.02, 1.20), (0.14, 0.32, 2.20), "Metal", 0.008)
box("Niche jamb R", (0.84, -0.02, 1.20), (0.14, 0.32, 2.20), "Metal", 0.008)
box("Niche head", (0, -0.02, 2.24), (1.86, 0.34, 0.16), "Metal", 0.008)
box("Niche sill", (0, -0.02, 0.12), (1.68, 0.32, 0.18), "Concrete", 0.008)
box("Shutter housing", (0, -0.06, 2.40), (1.74, 0.22, 0.20), "Rust", 0.008)
for z in (1.78, 1.92, 2.06):
    box("Shutter slat", (0, -0.14, z), (1.58, 0.02, 0.07), "Metal", 0.002)
join_asset(
    "SM_ShellShutterNiche",
    "Floor Z=0. Opening faces -Y. Shutter covers only the upper part of the bay.",
    "Right wall only, one copy, outside Y=1500. The service cabinets stay. This is the shuttered niche, not a second cabinet.")

# 10. Pipe saddle. Wall plate is +Y, saddle is -Y.
box("Standoff plate", (0, 0.18, 0.30), (0.36, 0.05, 0.56), "Metal", 0.006)
box("Standoff arm L", (-0.10, -0.08, 0.36), (0.04, 0.46, 0.055), "Metal", 0.004)
box("Standoff arm R", (0.10, -0.08, 0.36), (0.04, 0.46, 0.055), "Metal", 0.004)
cylinder("Standoff saddle", (0, -0.32, 0.36), 0.09, 0.30, "Rust", "X", 12, 0.004)
for x in (-0.10, 0.10):
    for z in (0.14, 0.46):
        cylinder("Standoff bolt", (x, 0.215, z), 0.016, 0.018, "Metal", "Y", 6, 0)
join_asset(
    "SM_ShellPipeStandoff",
    "Plate center near the origin. Saddle faces -Y.",
    "Under the left-wall pipe runs, replacing PipeStandoff boxes. Keep the rack's own valve wheel. Do not add another.")

# 11. Small caged practical. The slit uses the emissive slot. Red stays a light.
box("Beacon body", (0, 0.04, 0.36), (0.34, 0.18, 0.68), "Dark", 0.01)
box("Beacon visor", (0, -0.08, 0.64), (0.40, 0.12, 0.05), "Metal", 0.004)
box("Beacon slit", (0, -0.09, 0.34), (0.04, 0.016, 0.18), "Emissive", 0.001)
box("Beacon mount", (0, 0.14, 0.36), (0.14, 0.08, 0.30), "Metal", 0.005)
for z in (0.22, 0.48):
    box("Beacon bar", (0, -0.12, z), (0.38, 0.014, 0.018), "Metal", 0.002)
join_asset(
    "SM_ShellBeaconHousing",
    "Floor of the housing at Z=0. Slit faces -Y. Slit is 4 cm by 18 cm.",
    "Replaces BeaconHousing and BeaconLens boxes at the two existing practicals. Assign the warning lens on the emissive slot if a red slit is required. The red point stays the light actor. No new fixture row.")

# 12. Far-corner pier and elbow. Exterior is +X/+Y. No wheel.
box("Riser pier", (0, 0, WALL_H * 0.5), (0.96, 0.96, WALL_H), "Concrete", 0.025)
box("Riser plinth", (0, 0, 0.24), (1.12, 1.12, 0.48), "Dark", 0.015)
box("Riser niche", (-0.10, -0.40, 1.60), (0.42, 0.14, 0.78), "Dark", 0.006)
pipe("Riser pipe", [(0.30, 0.30, 0.55), (0.30, 0.30, 5.15), (0.52, 0.30, 5.42), (1.05, 0.30, 5.42)], 0.075, "Rust")
cylinder("Riser cap", (1.05, 0.30, 5.42), 0.09, 0.06, "Metal", "X", 10, 0.004)
for z in (1.20, 3.40, 4.85):
    ring("Riser collar", (0.30, 0.30, z), 0.105, 0.018, "Metal", "Z", 16, 6)
join_asset(
    "SM_ShellCornerRiser",
    "Floor Z=0. Pier is 0.96 m square. Elbow leaves toward +X and stays on that side.",
    "Far corners around (1500, ±1550), entirely outside X=1480 and |Y|=1500. Turn the +X elbow along the outside of the far wall. Not a second tank. No valve wheel.")

# 13. Low conduit curb with a few footing lumps at one end.
box("Curb body", (0, 0, 0.11), (4.00, 0.36, 0.22), "Concrete", 0.01)
pipe("Curb conduit", [(-1.65, 0.0, 0.26), (1.50, 0.02, 0.26)], 0.05, "Rust")
for x in (-1.15, 0.15, 1.25):
    cylinder("Curb bolt", (x, -0.10, 0.24), 0.026, 0.03, "Metal", "Z", 6, 0)
box("Sediment a", (-1.62, 0.22, 0.09), (0.34, 0.20, 0.14), "Concrete", 0.01)
box("Sediment b", (-1.40, 0.06, 0.05), (0.16, 0.12, 0.07), "Dark", 0.004)
box("Sediment c", (-1.78, -0.08, 0.045), (0.18, 0.14, 0.06), "Concrete", 0.006)
join_asset(
    "SM_ShellUtilityCurb",
    "Floor Z=0. Long axis X. Sediment is part of this mesh, clustered at -X.",
    "Far utility strip X=1530 to 1620, behind the playable limit. Replaces the empty join at the wall foot. The parity floor chips remain the scatter. Do not spawn the old foot-debris boxes, and do not treat these lumps as a crate or a debris card.")

# 14. Short inward bracket. It does not reach another wall.
box("Bracket plate", (0, 0.02, 0.40), (0.70, 0.06, 0.78), "Metal", 0.008)
beam("Bracket arm A", (-0.16, 0.0, 0.62), (-0.16, -0.78, 0.98), 0.055, 0.07, "Metal", 0.004)
beam("Bracket arm B", (0.16, 0.0, 0.58), (0.16, -0.74, 0.92), 0.055, 0.07, "Metal", 0.004)
box("Bracket tip", (0, -0.76, 0.96), (0.46, 0.05, 0.06), "Rust", 0.004)
join_asset(
    "SM_ShellUpperBracket",
    "Plate bottom at Z=0. Arms reach about 0.78 m toward -Y and stop.",
    "A few copies on the upper interior face, plate bottom near Z=690. They suggest structure past the open centre. No truss, no lamp, no span across the arena.")

# 15. Ladder tray for the right wall only.
box("Tray rail L", (0, -0.15, 0.08), (2.20, 0.028, 0.07), "Metal", 0.003)
box("Tray rail R", (0, 0.15, 0.08), (2.20, 0.028, 0.07), "Metal", 0.003)
for x in (-0.85, -0.40, 0.05, 0.50, 0.90):
    box("Tray rung", (x, 0, 0.025), (0.028, 0.30, 0.022), "Metal", 0.002)
pipe("Tray cable", [(-0.95, 0.0, 0.06), (-0.1, -0.02, 0.035), (0.85, 0.03, 0.055)], 0.016, "Dark")
box("Tray hanger", (0.4, 0.24, 0.18), (0.22, 0.16, 0.28), "Metal", 0.006)
box("Tray hanger B", (-0.7, 0.24, 0.16), (0.16, 0.14, 0.22), "Rust", 0.005)
join_asset(
    "SM_ShellCableTray",
    "Long axis X. Hangers are +Y, toward the wall. Open upward.",
    "Right wall only, one or two copies around Z=420, outside Y=1500. Not a pipe rack and not a second valve.")

# 16. Outer leaf so a wide camera does not see an empty cut.
box("Backing mass", (0, 0.08, 3.90), (6.00, 0.42, 7.80), "Concrete", 0.016)
box("Backing shade", (0, -0.16, 1.40), (5.60, 0.06, 2.40), "Dark", 0.006)
join_asset(
    "SM_ShellDarkBacking",
    "Floor Z=0. Shaded face is -Y. 6.0 m wide, about 7.8 m tall.",
    "Outside the outer face of the three tall walls. Not a ceiling and not a hall behind the door.")

# 17. Low ground continuing past the shell.
box("Apron slab", (0, 0, 0.05), (6.00, 6.00, 0.10), "Dark", 0)
box("Apron joint", (0, 0, 0.105), (5.4, 0.02, 0.012), "Concrete", 0)
join_asset(
    "SM_ShellOuterApron",
    "Top near Z=0.10. Centered.",
    "Tile outside the walls only, top flush with the exterior ground. No collision. Does not enter X=-1400..1480 or Y=-1500..1500.")

total = sum(entry["triangles"] for entry in ASSETS)
below_ok = {"SM_ShellCornice", "SM_ShellUpperBracket"}
for entry in ASSETS:
    if entry["name"] not in below_ok:
        assert entry["bounds_m"]["min"][2] >= -0.002, (entry["name"], entry["bounds_m"]["min"])
assert 12 <= len(ASSETS) <= 20, len(ASSETS)
assert total < 80000, total
for entry in ASSETS:
    assert entry["triangles"] < 14000, (entry["name"], entry["triangles"])
    assert "wheel" not in entry["name"].lower()

roundtrips = []
for entry in ASSETS:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(OUT / entry["file"]), use_anim=False)
    loaded = [obj for obj in set(bpy.data.objects) - before]
    meshes = [obj for obj in loaded if obj.type == "MESH"]
    assert len(meshes) == 1, (entry["name"], len(meshes), [obj.type for obj in loaded])
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
    "source": "Original deterministic shell meshes for the chamber boxes. The ten-piece room kit was not modified.",
    "generator": "tools/make_room_shell.py",
    "blender_version": bpy.app.version_string,
    "coordinate_system": "Source metres, Z up, architectural fronts -Y. Same FBX axis setup as Assets/Adapted/Room. Unreal may present that front toward +Y. Confirm before placement, the way the bulkhead was confirmed.",
    "fbx_settings": {
        "axis_forward": "-Y", "axis_up": "Z", "global_scale": 1,
        "apply_unit_scale": True, "apply_scale_options": "FBX_SCALE_NONE",
    },
    "material_slots": list(MATS),
    "maps": "Assets/Adapted/RoomShell/Surfaces. Four families, no teal and no player pool. Not imported.",
    "replaces_boxes": [
        "FarWall", "SideWall", "SideLowerDamp", "SideCornice", "SideFoundation", "SideGutter",
        "FarLowerDamp", "FarCornice", "FarFoundation", "CutawaySill", "CutawayCap",
        "RearInset", "RearHeader", "PipeStandoff", "BeaconHousing", "BeaconLens",
    ],
    "leave_alone": [
        "Assets/Adapted/Room kit", "bulkhead locking wheel", "pipe-rack valve wheel",
        "parity floor chips", "TeddyV2", "level actors",
    ],
    "not_included": [
        "ceiling slab", "second wheel", "second tank", "second crate", "barrels",
        "spotlight row", "stage truss", "luminous sign", "baked player pool", "baked teal",
        "flat debris card", "fourth creature",
    ],
    "total_triangles": total,
    "assets": ASSETS,
    "fbx_roundtrip_checks": roundtrips,
    "limits": "Files on disk only. Placement, collision, and materials belong to the scene pass. Decorative meshes stay non-colliding. Existing blockers stay.",
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

readme = """# Room shell kit

Off the level. `tools/build_full_room.py` imports `Assets/Adapted/Room/SM_*.fbx` only. This folder is a later opt-in.

These meshes replace the chamber boxes: far wall, side walls, plinth, cornice, foundation, gutter, cutaway sill, rear insets, pipe standoffs, and beacon housings. The ten-piece room kit stays where it is. The bulkhead already has a locking wheel. The pipe rack already has a valve. Neither is repeated here.

Units are metres in Blender and centimetres after the room kit's FBX settings. The detailed face is local −Y. The existing import presented that face toward Unreal +Y. Confirm before placing. Wall origins match the old box centers: far wall X=1720, side walls Y=±1740, interior face 60 cm toward the arena.

When a mesh goes in, hide the box it replaces. Do not stack both, and do not give these a second collision shell.

| Mesh | Job |
| --- | --- |
| `SM_ShellWallBay` | 4.00 m retaining bay, 1.20 m thick, 7.60 m tall, dark 80 cm plinth |
| `SM_ShellWallBayNarrow` | Same section, 2.00 m, to finish a span |
| `SM_ShellCornice` | Steel ledge. Seat it at Z=760. Brackets hang below the seat |
| `SM_ShellFoundation` | Chamfered footing, projects into the room |
| `SM_ShellGutter` | 48 cm drain with a recess only in the middle |
| `SM_ShellCutawaySill` | Broken foreground curb, 42–68 cm, not a wall |
| `SM_ShellCutawayReturn` | 1.1 m pier at the two near corners |
| `SM_ShellRearInset` | Framed far-wall recess and header |
| `SM_ShellShutterNiche` | Right wall only, shutter partway down |
| `SM_ShellPipeStandoff` | Saddle under the left pipe run |
| `SM_ShellBeaconHousing` | Small cage and a 4×18 cm slit. Red stays a light |
| `SM_ShellCornerRiser` | Far-corner pier and elbow, outside the footprint |
| `SM_ShellUtilityCurb` | Far conduit curb. A few lumps are built in |
| `SM_ShellUpperBracket` | 0.8 m inward arm. No lamp and no span |
| `SM_ShellCableTray` | Right-wall ladder tray |
| `SM_ShellDarkBacking` | Outer leaf behind the three tall walls |
| `SM_ShellOuterApron` | Dark ground outside the shell |

Surface maps are in `Surfaces/`: charcoal concrete, worn green-grey steel, muted oxide, and a near-black recess. Roughness stays in the art-direction bands. They do not contain a teal wash or a player pool.

Generator: `tools/make_room_shell.py`. Surfaces: `tools/make_room_shell_surfaces.py`.
"""
(OUT / "README.md").write_text(readme, encoding="utf-8")

# Preview only. Exports already finished. Spread every mesh so none hides another.
def show(obj, loc, yaw=0):
    obj.location = loc
    obj.rotation_euler = (0, 0, yaw)

by_name = {obj.name: obj for obj in OBJECTS}
show(by_name["SM_ShellWallBay"], (0, 0, 0))
show(by_name["SM_ShellWallBayNarrow"], (4.2, 0, 0))
show(by_name["SM_ShellCornerRiser"], (7.4, 0, 0))
show(by_name["SM_ShellDarkBacking"], (12.2, 0, 0))
show(by_name["SM_ShellCornice"], (0, -5.2, 0.25))
show(by_name["SM_ShellFoundation"], (5.2, -5.2, 0))
show(by_name["SM_ShellGutter"], (10.4, -5.2, 0))
show(by_name["SM_ShellCutawaySill"], (15.6, -5.2, 0))
show(by_name["SM_ShellCutawayReturn"], (0, -8.2, 0))
show(by_name["SM_ShellRearInset"], (3.6, -8.2, 0))
show(by_name["SM_ShellShutterNiche"], (8.6, -8.2, 0))
show(by_name["SM_ShellUtilityCurb"], (12.2, -8.2, 0))
show(by_name["SM_ShellPipeStandoff"], (0, -10.6, 0))
show(by_name["SM_ShellBeaconHousing"], (2.2, -10.6, 0))
show(by_name["SM_ShellUpperBracket"], (4.4, -10.6, 0))
show(by_name["SM_ShellCableTray"], (7.2, -10.6, 0))
show(by_name["SM_ShellOuterApron"], (18.5, -1.5, 0))

bpy.ops.mesh.primitive_plane_add(size=60, location=(8, -4, -0.02))
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
for name, loc, energy in (("Key", (-4, -10, 9), 2500), ("Fill", (8, -6, 6), 600)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.size = 4
    data.color = (0.75, 0.88, 1.0) if name == "Key" else (0.55, 0.62, 0.66)
    lamp = bpy.data.objects.new(name, data)
    scene.collection.objects.link(lamp)
    lamp.location = loc
    lamp.rotation_euler = (Vector((1.2, 0.2, 2.5)) - lamp.location).to_track_quat("-Z", "Y").to_euler()
camera_data = bpy.data.cameras.new("Shell overview")
camera = bpy.data.objects.new("Shell overview", camera_data)
scene.collection.objects.link(camera)
target = Vector((9.0, -4.5, 2.4))
camera.location = target + Vector((18, -16, 14))
camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
camera_data.type = "ORTHO"
camera_data.ortho_scale = 36
scene.camera = camera
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.render.filepath = str(OUT / "shell-overview.png")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "RoomShell_Kit.blend"))
bpy.ops.render.render(write_still=True)
print("SHELL_KIT_COMPLETE", json.dumps({
    "assets": len(ASSETS), "triangles": total, "engine": scene.render.engine,
    "manifest": str(OUT / "manifest.json"),
}), flush=True)
