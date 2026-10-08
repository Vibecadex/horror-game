"""Open the reverse service bays into the depth the frame already has.

Writes only Assets/Adapted/ChamberParity/BayDepth. The original kit FBX stays.
The shell face is at world X about -1610, so the cavity stays in front of it.
"""
import bpy
import bmesh
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Assets' / 'Adapted' / 'ChamberParity' / 'BayDepth'
OWNER = 'teddy-chamber-bay-depth-20261005'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0

SLOTS = ['Metal', 'Concrete', 'Rust', 'Dark', 'Emissive']
MATS = {}
for name, color in {
    'Metal': (.07, .08, .075, 1),
    'Concrete': (.16, .16, .15, 1),
    'Rust': (.12, .06, .03, 1),
    'Dark': (.02, .025, .024, 1),
    'Emissive': (.45, .03, .015, 1),
}.items():
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    MATS[name] = material

PARTS = []


def finish(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(MATS[material])
    PARTS.append(obj)
    return obj


def box(name, location, size, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, material)


def cylinder(name, location, radius, depth, material, axis='Z', vertices=24):
    rotation = {'Y': (math.pi / 2, 0, 0), 'Z': (0, 0, 0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return finish(obj, material)


# Front frame matches the reviewed bay. The solid leaf is omitted so the
# jamb depth is a recess instead of a flat dark card. Back stays at local
# Y 0.24, which lands just in front of the shell face after the -90 yaw.
for x in (-1.045, 1.045):
    box('Worn concrete door jamb', (x, -.055, 1.705), (.23, .48, 3.41), 'Concrete')
    box('Metal reveal jamb', (x * .852, -.02, 1.61), (.10, .62, 3.20), 'Metal')
    box('Outer steel jamb lip', (x * .916, -.321, 1.66), (.134, .115, 3.31), 'Metal')
box('Concrete lintel', (0, -.055, 3.475), (2.32, .48, .25), 'Concrete')
box('Recessed head reveal', (0, -.02, 3.177), (1.90, .55, .12), 'Metal')
box('Black threshold tray', (0, -.02, .06), (1.89, .70, .08), 'Dark')
for y in (-.28, -.12, .04):
    box('Threshold anti-slip lip', (0, y, .09), (1.75, .038, .018), 'Metal')
box('Dark rear chamber', (0, .24, 1.62), (1.62, .06, 3.05), 'Dark')
box('Interior left return', (-.78, .08, 1.58), (.06, .36, 2.95), 'Dark')
box('Interior right return', (.78, .08, 1.58), (.06, .36, 2.95), 'Dark')
box('Interior head', (0, .08, 3.02), (1.50, .36, .06), 'Dark')
cylinder('Service drum', (.34, .02, .42), .18, .78, 'Metal')
cylinder('Service drum rust band', (.34, .02, .22), .185, .08, 'Rust')
box('Beacon mounting plate', (0, -.27, 3.443), (.34, .072, .16), 'Metal')
cylinder('Beacon red lens', (0, -.329, 3.443), .045, .04, 'Emissive', 'Y', 20)
box('Beacon rain hood', (0, -.36, 3.50), (.28, .16, .04), 'Dark')

bpy.ops.object.select_all(action='DESELECT')
for obj in PARTS:
    obj.select_set(True)
bpy.context.view_layer.objects.active = PARTS[0]
bpy.ops.object.join()
obj = bpy.context.object
obj.name = 'SM_ChamberServiceDoorBay'
scene.cursor.location = (0, 0, 0)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
old = [slot.material.name for slot in obj.material_slots]
indices = [SLOTS.index(old[poly.material_index]) for poly in obj.data.polygons]
obj.data.materials.clear()
for material in MATS.values():
    obj.data.materials.append(material)
for poly, index in zip(obj.data.polygons, indices):
    poly.material_index = index
mesh = bmesh.new()
mesh.from_mesh(obj.data)
bmesh.ops.recalc_face_normals(mesh, faces=list(mesh.faces))
mesh.to_mesh(obj.data)
mesh.free()
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.012)
bpy.ops.object.mode_set(mode='OBJECT')
obj.data.calc_loop_triangles()
points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
bounds = {'min': [min(point[i] for point in points) for i in range(3)],
          'max': [max(point[i] for point in points) for i in range(3)]}
dims = [bounds['max'][i] - bounds['min'][i] for i in range(3)]
fbx = OUT / 'SM_ChamberServiceDoorBay.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'MESH'},
    axis_forward='-Y', axis_up='Z', global_scale=1, apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_NONE', use_mesh_modifiers=True,
    mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False, path_mode='AUTO')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'ChamberBayDepth.blend'))
entry = {
    'name': 'SM_ChamberServiceDoorBay',
    'file': fbx.name,
    'purpose': 'Open reverse service recess. Same frame, no solid leaf, drum inside the existing reveal.',
    'triangles': len(obj.data.loop_triangles),
    'expected_dimensions_cm': [100 * value for value in dims],
    'material_slots': SLOTS,
    'sha256': hashlib.sha256(fbx.read_bytes()).hexdigest(),
    'preserves_original_kit_fbx': True,
}
manifest = {
    'owner': OWNER,
    'status': 'source-ready-for-engine-review',
    'replaces_visible_mesh_path': '/Game/TeddyEncounter/Chamber/Meshes/SM_ChamberServiceDoorBay',
    'original_kit_fbx_untouched': 'Assets/Adapted/ChamberParity/SM_ChamberServiceDoorBay.fbx',
    'assets': [entry],
}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('BAY_DEPTH', entry['triangles'], [round(value, 3) for value in dims], flush=True)
