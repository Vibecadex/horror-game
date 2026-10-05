"""Author an original, modular industrial room kit. Run with installed Blender.

All new outputs are restricted to Assets/Adapted/Room. No Unreal edits. The
exported meshes use metres, Z up, and -Y as the architectural front. FBX stores
the normal metre-to-centimetre conversion for Unreal. An import round trip
checks bounds, triangle counts and material slots before delivery.
"""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Assets' / 'Adapted' / 'Room'
OWNER = 'teddy-industrial-room-20261005'
if OUT.exists():
    marker = OUT / 'manifest.json'
    if not marker.exists() or json.loads(marker.read_text())['owner'] != OWNER:
        raise RuntimeError('Refusing to overwrite an unowned Room folder')
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0

COLORS = {
    'Metal': (0.14, 0.20, 0.20, 1),
    'Concrete': (0.22, 0.25, 0.25, 1),
    'Rust': (0.24, 0.10, 0.045, 1),
    'Dark': (0.018, 0.029, 0.032, 1),
    'Emissive': (0.11, 0.58, 0.62, 1),
}
MATS = {}
for name, color in COLORS.items():
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = 0.76 if name != 'Metal' else 0.57
    bsdf.inputs['Metallic'].default_value = 0.65 if name == 'Metal' else 0.1
    if name == 'Emissive':
        bsdf.inputs['Emission Color'].default_value = color
        bsdf.inputs['Emission Strength'].default_value = 2.0
    MATS[name] = mat

PARTS = []
ASSETS = []
OBJECTS = []


def finish_piece(obj, mat='Metal', bevel=0):
    obj.data.materials.append(MATS[mat])
    bpy.context.view_layer.objects.active = obj
    if bevel:
        mod = obj.modifiers.new('Edge catches', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    PARTS.append(obj)
    return obj


def box(name, loc, size, mat='Metal', bevel=0.018, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish_piece(obj, mat, min(bevel, min(size) * 0.2))


def cylinder(name, loc, radius, depth, mat='Metal', axis='Z', vertices=32, bevel=0.008):
    rotation = {'X': (0, math.pi / 2, 0), 'Y': (math.pi / 2, 0, 0), 'Z': (0, 0, 0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                      depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    for polygon in obj.data.polygons:
        polygon.use_smooth = len(polygon.vertices) == 4
    return finish_piece(obj, mat, bevel)


def ring(name, loc, radius, tube, mat='Metal', axis='Z', major=32, minor=8):
    rotation = {'X': (0, math.pi / 2, 0), 'Y': (math.pi / 2, 0, 0), 'Z': (0, 0, 0)}[axis]
    bpy.ops.mesh.primitive_torus_add(major_segments=major, minor_segments=minor,
                                   major_radius=radius, minor_radius=tube,
                                   location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return finish_piece(obj, mat)


def beam(name, start, end, width, depth, mat='Metal', bevel=0.01):
    start, end = Vector(start), Vector(end)
    obj = box(name, (start + end) / 2, (width, depth, (end - start).length), mat, bevel)
    obj.rotation_euler = (end - start).to_track_quat('Z', 'Y').to_euler()
    return obj


def pipe(name, points, radius, mat='Metal'):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 1
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    curve.resolution_u = 8
    curve.use_fill_caps = True
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for point, xyz in zip(spline.points, points):
        point.co = (*xyz, 1)
    obj = bpy.data.objects.new(name, curve)
    scene.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return finish_piece(obj, mat)


def bolts_face(xs, zs, y, radius=0.032):
    for x in xs:
        for z in zs:
            cylinder('Hex fastener', (x, y, z), radius, 0.034, 'Metal', 'Y', 6, 0.003)


def join_asset(name, origin_note, placement_note):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in PARTS:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + '_Geometry'
    scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    # Deterministic five-slot ordering for overrides, regardless of mesh content.
    old_slots = [slot.material.name for slot in obj.material_slots]
    indices = [list(MATS).index(old_slots[p.material_index]) for p in obj.data.polygons]
    obj.data.materials.clear()
    for mat in MATS.values():
        obj.data.materials.append(mat)
    for polygon, index in zip(obj.data.polygons, indices):
        polygon.material_index = index
    # UVs provide usable material coordinates; world-space Unreal materials may
    # override these. No textures or external files are required.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.015)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.calc_loop_triangles()
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = [min(p[i] for p in points) for i in range(3)]
    maximum = [max(p[i] for p in points) for i in range(3)]
    triangles = len(obj.data.loop_triangles)
    entry = {
        'name': name, 'file': name + '.fbx', 'triangles': triangles,
        'vertices': len(obj.data.vertices),
        'bounds_m': {'min': minimum, 'max': maximum},
        'dimensions_m': [maximum[i] - minimum[i] for i in range(3)],
        'expected_dimensions_cm': [100 * (maximum[i] - minimum[i]) for i in range(3)],
        'origin': origin_note, 'front': 'Blender local -Y',
        'placement': placement_note, 'material_slots': list(MATS),
        'collision': 'Environment prop; author simple collision only where required. Perimeter placements recommended.',
    }
    bpy.ops.export_scene.fbx(filepath=str(OUT / entry['file']), use_selection=True,
        object_types={'MESH'}, axis_forward='-Y', axis_up='Z', global_scale=1,
        apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
        use_mesh_modifiers=True, mesh_smooth_type='FACE', add_leaf_bones=False,
        bake_anim=False, path_mode='AUTO')
    entry['sha256'] = hashlib.sha256((OUT / entry['file']).read_bytes()).hexdigest()
    ASSETS.append(entry)
    OBJECTS.append(obj)
    PARTS.clear()
    print('ROOM_ASSET', name, triangles, entry['dimensions_m'], flush=True)
    return obj


# 1. Deep structural rib with stepped shoe, rusted steel spine, and collar seams.
box('Concrete spine', (0, 0.13, 2.5), (0.76, 0.44, 5.0), 'Concrete', 0.055)
box('Deep steel rib', (0, -0.18, 2.53), (0.31, 0.38, 4.77), 'Metal', 0.032)
box('Rib front flange', (0, -0.405, 2.58), (0.55, 0.13, 4.68), 'Metal', 0.02)
for z in (0.14, 0.38, 2.65, 4.73):
    box('Bolted collar', (0, -0.16, z), (0.98, 0.66, 0.15), 'Rust' if z == 0.38 else 'Metal', 0.025)
bolts_face((-0.37, 0.37), (0.38, 2.65, 4.73), -0.506)
join_asset('SM_RoomPilaster', 'Floor at Z=0, centered in X/Y.', 'Full-height perimeter support; front projects toward -Y.')

# 2. Framed split pressure door: three depth levels, exposed bracing, mechanism.
for x in (-2.3, 2.3):
    box('Door concrete jamb', (x, 0, 2.19), (0.42, 0.56, 4.38), 'Concrete', 0.05)
    box('Door steel jamb', (x * 0.9, -0.25, 2.24), (0.20, 0.28, 4.47), 'Metal', 0.025)
box('Deep top lintel', (0, 0, 4.59), (5.02, 0.56, 0.42), 'Concrete', 0.04)
box('Top track', (0, -0.32, 4.32), (4.41, 0.26, 0.28), 'Rust', 0.026)
box('Threshold', (0, -0.17, 0.07), (4.57, 0.63, 0.14), 'Metal', 0.018)
for sign in (-1, 1):
    x = sign * 1.03
    box('Split door leaf', (x, -0.015, 2.18), (2.02, 0.27, 4.2), 'Metal', 0.045)
    for z, h in ((1.18, 1.86), (3.26, 1.69)):
        box('Recessed service panel', (x, -0.159, z), (1.67, 0.048, h), 'Dark', 0.025)
        box('Plate inset', (x, -0.194, z), (1.48, 0.039, h - 0.19), 'Metal', 0.025)
    for z in (0.33, 2.18, 4.01):
        box('Door cross stiffener', (x, -0.24, z), (1.88, 0.13, 0.14), 'Metal', 0.016)
    beam('Diagonal bracing', (x - 0.75, -0.245, 0.44), (x + 0.75, -0.245, 1.96), 0.12, 0.11, 'Rust')
    beam('Upper diagonal', (x + 0.75, -0.245, 2.40), (x - 0.75, -0.245, 3.89), 0.12, 0.11)
    box('Center locking rod', (sign * 0.17, -0.3, 2.15), (0.12, 0.12, 3.85), 'Metal', 0.01)
    bolts_face((x - 0.84, x + 0.84), (0.34, 2.18, 4.01), -0.316)
box('Lock housing', (0, -0.34, 2.22), (0.77, 0.22, 0.59), 'Dark', 0.045)
cylinder('Lock central shaft', (0, -0.50, 2.22), 0.17, 0.13, 'Metal', 'Y', 24)
ring('Door locking wheel', (0, -0.59, 2.22), 0.32, 0.026, 'Rust', 'Y', 24, 6)
for angle in (0, math.pi / 2, math.pi, math.pi * 1.5):
    beam('Lock wheel spoke', (0, -0.59, 2.22), (math.cos(angle) * 0.31, -0.59, 2.22 + math.sin(angle) * 0.31), 0.025, 0.025)
box('Header light backing', (0, -0.30, 4.6), (1.5, 0.12, 0.17), 'Dark', 0.015)
box('Header narrow light', (0, -0.372, 4.6), (1.26, 0.027, 0.055), 'Emissive', 0.008)
join_asset('SM_RoomBulkhead', 'Floor at Z=0; centered door width X=0.', 'Closed dressing door, 5.02m wide; rear depth +Y, detailed face -Y.')

# 3. Wall ventilation unit with curved fan blades beneath a wire guard.
box('Vent square back plate', (0, 0.15, 0), (2.5, 0.17, 2.5), 'Rust', 0.07)
cylinder('Dark duct interior', (0, 0.016, 0), 1.08, 0.2, 'Dark', 'Y', 48, 0)
ring('Vent rolled outer lip', (0, -0.055, 0), 1.105, 0.105, 'Metal', 'Y', 48, 8)
cylinder('Fan motor', (0, -0.15, 0), 0.22, 0.31, 'Metal', 'Y', 24)
for i in range(6):
    a = i * math.tau / 6
    profile = [(0.18, -0.07), (0.76, -0.32), (1.00, -0.12), (0.78, 0.18), (0.32, 0.18)]
    verts = []
    for y in (-0.14, -0.09):
        verts.extend([(math.cos(a) * x - math.sin(a) * z, y, math.sin(a) * x + math.cos(a) * z) for x, z in profile])
    faces = [(4,3,2,1,0),(5,6,7,8,9)] + [(j, (j+1)%5, (j+1)%5+5, j+5) for j in range(5)]
    mesh = bpy.data.meshes.new('Fan blade')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new('Swept fan blade', mesh)
    scene.collection.objects.link(obj)
    finish_piece(obj, 'Metal', 0.018)
for radius in (0.37, 0.66, 0.91, 1.10):
    ring('Wire guard concentric', (0, -0.29, 0), radius, 0.017, 'Metal', 'Y', 40, 6)
for a in [i * math.tau / 12 for i in range(12)]:
    beam('Guard radial wire', (0, -0.292, 0), (math.cos(a)*1.11, -0.292, math.sin(a)*1.11), 0.02, 0.02, 'Metal', 0.002)
bolts_face((-1.095, 1.095), (-1.095, 1.095), -0.003, 0.046)
join_asset('SM_RoomVentFan', 'Wall mount, origin at fan center.', 'Mount center >=2.7m above floor. Face local -Y; fan is static environmental dressing.')

# 4. Pressure vessel: bands, end domes, access collar, front gauge, and piping.
cylinder('Tank body', (0, 0, 2.13), 0.67, 3.24, 'Metal', 'Z', 48, 0.045)
for z in (0.51, 3.75):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=12, radius=1, location=(0,0,z))
    obj = bpy.context.object
    obj.scale=(0.666,0.666,0.29)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in obj.data.polygons:p.use_smooth=True
    finish_piece(obj,'Metal')
for z in (0.64, 1.52, 3.18, 3.62):
    ring('Welded reinforcement band', (0,0,z),0.68,0.035,'Rust' if z==0.64 else 'Metal')
for x in (-0.45,0.45):
    for y in (-0.45,0.45):
        box('Vessel short foot',(x,y,0.24),(0.21,0.24,0.48),'Metal',0.028)
        box('Anchor sole',(x,y,0.05),(0.35,0.37,0.10),'Rust',0.018)
cylinder('Top access neck',(0,0,4.03),0.27,0.26,'Metal','Z',24)
cylinder('Top bolted flange',(0,0,4.16),0.36,0.10,'Rust','Z',32)
for a in [i*math.tau/8 for i in range(8)]:
    cylinder('Flange bolts',(math.cos(a)*.29,math.sin(a)*.29,4.225),.033,.047,'Metal','Z',6,.003)
pipe('Side riser',[(-.77,.05,.62),(-.77,.05,3.55),(-.72,.05,3.75),(-.44,.05,3.87)],.077,'Rust')
cylinder('Gauge base',(0,-.675,2.9),.17,.18,'Metal','Y',24)
cylinder('Gauge dark face',(0,-.774,2.9),.139,.028,'Dark','Y',24,0)
beam('Gauge needle',(0,-.795,2.9),(.075,-.795,2.97),.013,.012,'Concrete',.001)
box('Vessel label inset',(0,-.672,2.40),(.36,.035,.20),'Dark',.012)
box('Vessel identification stripe',(0,-.699,2.40),(.20,.016,.026),'Rust',.003)
join_asset('SM_RoomUtilityTank','Floor Z=0; cylindrical vessel center X/Y=0.','Put at rear/side corners outside the combat boundary. Front gauge faces -Y.')

# 5. Two-tier service cabinet with vents, switches, hinges and exposed conduit.
box('Cabinet plinth',(0,0,.12),(1.68,.72,.24),'Dark',.035)
box('Cabinet folded body',(0,.01,1.24),(1.6,.65,2.26),'Metal',.045)
for z,h in ((.78,1.05),(1.85,.78)):
    box('Door shadow gasket',(0,-.324,z),(1.43,.028,h),'Dark',.018)
    box('Cabinet door',(0,-.356,z),(1.34,.038,h-.09),'Metal',.022)
    box('Door pull',(.49,-.429,z),(.045,.085,.22),'Dark',.01)
    for zz in (z-h*.31,z+h*.31):
        cylinder('Cabinet hinge',(-.70,-.365,zz),.035,.16,'Rust','Z',12,.004)
for z in [.38+i*.065 for i in range(8)]:
    box('Vent dark slot',(-.08,-.383,z),(.93,.024,.033),'Dark',.003)
box('Control panel recess',(-.12,-.385,1.85),(.82,.045,.48),'Dark',.014)
for x in (-.39,-.12,.15):
    cylinder('Toggle socket',(x,-.425,1.80),.054,.042,'Metal','Y',16,.003)
    beam('Switch lever',(x,-.445,1.80),(x,-.50,1.86),.022,.022,'Rust',.004)
    box('Status bar',(x,-.423,2.01),(.08,.027,.028),'Emissive',.003)
pipe('External cable conduit',[(.54,.04,2.37),(.54,.04,2.54),(.75,.04,2.63),(.93,.04,2.63)],.025,'Dark')
join_asset('SM_RoomServiceCabinet','Floor Z=0, center X/Y=0.','Tall front detailed cabinet with raised switches, vents and three tiny indicator lamps.')

# 6. Repeated horizontal service pipes, flange pairs and a large shutoff wheel.
for z,radius in ((-.24,.135),(.25,.09)):
    cylinder('Long pipe',(0,0,z),radius,5.0,'Metal','X',24,.004)
    for x in (-2.36,-1.06,1.06,2.36):
        cylinder('Pipe coupling',(x,0,z),radius*1.38,.105,'Rust','X',24,.012)
for x in (-1.85,0,1.85):
    box('Pipe mounting saddle',(x,.15,0),(.15,.39,.88),'Dark',.02)
    for z,radius in ((-.24,.135),(.25,.09)):
        ring('Pipe retaining band',(x,0,z),radius+.017,.018,'Metal','X',24,6)
pipe('Valve branch',[(.65,0,-.24),(.65,-.12,-.24),(.65,-.32,-.24)],.065,'Metal')
ring('Valve wheel',(.65,-.39,-.24),.245,.021,'Rust','Y',32,6)
cylinder('Valve hub',(.65,-.39,-.24),.06,.08,'Metal','Y',16)
for a in (0,math.pi/2,math.pi,math.pi*1.5):
    beam('Valve spoke',(.65,-.39,-.24),(.65+math.cos(a)*.24,-.39,-.24+math.sin(a)*.24),.02,.02,'Metal',.002)
join_asset('SM_RoomPipeRack','Centered pipe run; local X spans -2.5 to +2.5m.','Mount horizontally on wall, center at desired height; front/valve is -Y.')

# 7. Floor service trench, inset dark basin, load-bearing grate bars and seams.
box('Grate catch basin',(0,0,-.041),(4.0,.9,.078),'Dark',.01)
for y in (-.428,.428):
    box('Grate long frame',(0,y,.012),(4,.065,.07),'Rust',.008)
for x in (-1.972,0,1.972):
    box('Grate transverse frame',(x,0,.012),(.065,.84,.07),'Metal',.008)
for i in range(31):
    box('Grate load bar',(-1.89+i*.126,0,.019),(.028,.82,.053),'Metal',.003)
for y in (-.25,.25):
    box('Grate underside tie',(0,y,-.008),(3.87,.029,.04),'Dark',.004)
join_asset('SM_RoomFloorGrate','Top surface near Z=0 (+0.047m); center X/Y.','Recess into floor or place at Z=-4.7cm to avoid a step. Local X length 4m.')

# 8. Large industrial cable spool with wound cable and brace plates.
cylinder('Spool core',(0,0,.48),.37,.74,'Dark','Z',32,.01)
for z in (.085,.875):
    cylinder('Spool end flange',(0,0,z),.67,.12,'Metal','Z',40,.018)
    ring('Spool raised rim',(0,0,z),.61,.018,'Rust','Z',40,6)
for z in [.18+i*.047 for i in range(14)]:
    ring('Heavy coiled cable',(0,0,z),.485,.027,'Dark','Z',40,6)
cylinder('Spool top hub',(0,0,.953),.10,.07,'Dark','Z',24,.006)
for a in [i*math.tau/6 for i in range(6)]:
    cylinder('Spool flange bolt',(math.cos(a)*.48,math.sin(a)*.48,.95),.035,.05,'Rust','Z',6,.003)
join_asset('SM_RoomCableSpool','Floor Z=0.025m, center X/Y=0.','Low peripheral clutter; metallic flanges with visibly wound black cable.')

# 9. Braced cargo crate, separated corner protectors, latch bars, inset lid.
box('Cargo box body',(0,0,.57),(1.34,1.14,1.02),'Metal',.04)
box('Cargo box shadow lid seam',(0,0,1.074),(1.40,1.20,.045),'Dark',.012)
box('Cargo lid',(0,0,1.112),(1.40,1.20,.06),'Metal',.02)
box('Cargo inset lid',(0,0,1.146),(1.10,.90,.025),'Dark',.01)
for x in (-.64,.64):
    for y in (-.54,.54):
        box('Cargo protected corner',(x,y,.60),(.14,.14,1.08),'Rust',.023)
for y in (-.584,.584):
    for x in (-.41,.41):
        box('Cargo vertical rib',(x,y,.60),(.08,.07,.95),'Metal',.01)
    box('Cargo handle backing',(0,y*1.065,.68),(.32,.05,.22),'Dark',.013)
    box('Cargo fold handle',(0,y*1.115,.68),(.26,.025,.036),'Metal',.006)
for x in (-.45,.45):
    box('Cargo top brace',(x,0,1.18),(.12,1.08,.055),'Rust',.01)
for x in (-.46,.46):
    box('Cargo runner',(x,0,.045),(.17,1.18,.09),'Dark',.015)
join_asset('SM_RoomCargoCrate','Floor Z=0; center X/Y=0.','Low perimeter cargo dressing; elevated camera reads inset lid and brace bands.')

# 10. Cage-protected industrial light, short narrow luminous strips.
box('Fixture rear shell',(0,0,0),(2.06,.24,.34),'Metal',.035)
box('Fixture dark reflector',(0,-.137,0),(1.83,.045,.24),'Dark',.02)
for z in (-.055,.055):
    box('Fixture tube',(0,-.176,z),(1.65,.035,.045),'Emissive',.012)
for x in (-.93,-.46,0,.46,.93):
    box('Fixture transverse cage',(x,-.20,0),(.035,.08,.32),'Metal',.01)
for z in (-.16,.16):
    box('Fixture cage rail',(0,-.217,z),(1.91,.03,.028),'Metal',.005)
join_asset('SM_RoomStripLight','Centered fixture; long axis X, light faces -Y.','Mount on high wall or rotate for overhead use. Emissive slot 4; add actual Unreal lighting separately.')

total = sum(entry['triangles'] for entry in ASSETS)
assert total < 80000, total

# Fresh FBX readback before laying out the editable kit scene. This proves FBX
# geometry and slot count, not the Unreal importer or runtime collision.
roundtrips = []
for entry in ASSETS:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(OUT/entry['file']), use_anim=False)
    loaded = [obj for obj in set(bpy.data.objects) - before if obj.type == 'MESH']
    assert len(loaded) == 1, (entry['name'], len(loaded))
    obj = loaded[0]
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    dims = [max(p[i] for p in points) - min(p[i] for p in points) for i in range(3)]
    error = max(abs(a-b) for a,b in zip(dims,entry['dimensions_m']))
    assert error < 0.00002, (entry['name'],dims,entry['dimensions_m'])
    obj.data.calc_loop_triangles()
    assert len(obj.data.loop_triangles) == entry['triangles']
    assert len(obj.material_slots) == 5
    roundtrips.append({'name':entry['name'],'dimensions_m':dims,'max_dimension_error_m':error,
                       'triangles':len(obj.data.loop_triangles),'material_slots':5,'passed':True})
    bpy.data.objects.remove(obj,do_unlink=True)

manifest = {
    'owner': OWNER,
    'source': 'Original deterministic local mesh authoring for this project; no external models or textures.',
    'generator': 'tools/make_industrial_room.py',
    'blender_version': bpy.app.version_string,
    'coordinate_system': 'Source metres, Z up, architectural fronts -Y. Unreal importer may rotate local axes; check imported bounds before placement.',
    'fbx_settings': {'axis_forward':'-Y','axis_up':'Z','global_scale':1,'apply_unit_scale':True,'apply_scale_options':'FBX_SCALE_NONE'},
    'material_slots':list(MATS),
    'total_triangles':total,
    'assets':ASSETS,
    'fbx_roundtrip_checks':roundtrips,
    'limits':'Static scenery kit only. Unreal material overrides, placement, lighting, collision and camera visibility must be verified in the game.',
}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')

# Source scene displays the same exported meshes in a clean kit layout.
locations = [(-6,1,0),(-1,2,0),(4,2,2.9),(7.4,1,0),(-5,-3,0),(0,-2,1.25),
             (2.5,-4,0),(6,-3.3,0),(4.1,-3,0),(-1.1,-5,1.0)]
for obj, loc in zip(OBJECTS,locations):
    obj.location=loc
    obj['source_origin_note']=next(x['origin'] for x in ASSETS if x['name']==obj.name)
    obj['source_front']='-Y'
    obj['owner']=OWNER

# Isolated render studio, excluded from exported assets.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.04))
ground=bpy.context.object
ground.name='Preview ground (not exported)'
ground_mat=bpy.data.materials.new('Preview ground')
ground_mat.diffuse_color=(.05,.07,.075,1)
ground.data.materials.append(ground_mat)
world=bpy.data.worlds.new('Preview studio')
world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.11,.16,.20,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
scene.world=world
for name,loc,energy,size in [('Studio key',(-6,-8,13),2300,8),('Studio fill',(9,-1,8),1800,6),('Studio rim',(0,8,11),2500,7)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector((0,0,1.8))-obj.location).to_track_quat('-Z','Y').to_euler()
camera_data=bpy.data.cameras.new('Kit overview')
camera=bpy.data.objects.new('Kit overview',camera_data);scene.collection.objects.link(camera)
camera.location=(15,-25,21);camera.rotation_euler=(Vector((.3,-.2,1.7))-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.type='ORTHO';camera_data.ortho_scale=23
scene.camera=camera
scene.render.engine='CYCLES'
scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.render.filepath=str(OUT/'kit-overview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'IndustrialRoom_Kit.blend'))
bpy.ops.render.render(write_still=True)
print('ROOM_KIT_COMPLETE',json.dumps({'assets':len(ASSETS),'triangles':total,'manifest':str(OUT/'manifest.json')}),flush=True)
