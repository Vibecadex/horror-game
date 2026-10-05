"""Separate, eroded fracture field; never writes the preserved Floor kit.

Run in installed Blender with --background --disable-autoexec
--python-exit-code 1 --python tools/make_parity_fracture_v3.py.
Coordinates/export follow make_parity_floor.py: metres, +Z, floor plane Z=0.
"""
import ast
import bpy
import hashlib
import json
import math
import random
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Assets/Adapted/Parity/FloorV3'
OWNER = 'teddy-parity-fracture-v3-20261005'
SOURCE = ROOT / 'tools/make_parity_floor.py'
if OUT.exists() and any(OUT.iterdir()):
    marker = OUT / 'manifest.json'
    if not marker.exists() or json.loads(marker.read_text()).get('owner') != OWNER:
        raise RuntimeError('Refusing an unowned FloorV3 output')
OUT.mkdir(parents=True, exist_ok=True)
(OUT/'manifest.json').write_text(json.dumps({'owner': OWNER, 'status': 'authoring'}))
original_hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in (ROOT/'Assets/Adapted/Parity/Floor').glob('*') if p.is_file()}
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
MATERIAL_NAMES = ['Concrete', 'Aggregate', 'Dark', 'ConcreteLight', 'ConcreteDark']

# Reuse only these reviewed, pure geometry definitions; executing the original
# module would rebuild its owned kit and is deliberately avoided.
parsed = ast.parse(SOURCE.read_text())
helpers = [n for n in parsed.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
           and n.name in ('Geometry', 'clip_poly')]
assert len(helpers) == 2
exec(compile(ast.Module(body=helpers, type_ignores=[]), str(SOURCE), 'exec'), globals())
geo = Geometry()
rng = random.Random(5120317)
RX, RY = 3.12, 2.38

def make_material(name, multiplier):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    shader = m.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value = .92
    shader.inputs['Specular IOR Level'].default_value = .18
    nodes, links = m.node_tree.nodes, m.node_tree.links
    texture = nodes.new('ShaderNodeTexNoise')
    texture.inputs['Scale'].default_value = 35
    texture.inputs['Detail'].default_value = 3
    texture.inputs['Roughness'].default_value = .65
    coords = nodes.new('ShaderNodeTexCoord')
    links.new(coords.outputs['Object'], texture.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    if name == 'Dark':
        lo, hi = (.017, .022, .021, 1), (.030, .037, .034, 1)
    else:
        lo = tuple(v*multiplier for v in (.12, .14, .132))+(1,)
        hi = tuple(v*multiplier for v in (.205, .22, .198))+(1,)
    ramp.color_ramp.elements[0].color = lo
    ramp.color_ramp.elements[1].color = hi
    links.new(texture.outputs['Fac'], ramp.inputs[0])
    links.new(ramp.outputs['Color'], shader.inputs['Base Color'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .15
    bump.inputs['Distance'].default_value = .004
    links.new(texture.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    m.diffuse_color = hi
    return m

materials = [make_material(n, s) for n, s in zip(MATERIAL_NAMES, (1, 1.07, 1, 1.18, .82))]

def plate(points, height, top='Concrete', bevel=.003, tilt=(0, 0)):
    """Mostly flush plates: selected chipped rims have relief, not every edge."""
    cx = sum(p[0] for p in points)/len(points)
    cy = sum(p[1] for p in points)/len(points)
    inner, outer, base = [], [], []
    for x, y in points:
        dist = max(.04, math.hypot(x-cx, y-cy))
        shrink = min(.075, bevel/dist)
        z = max(.0018, height+(x-cx)*tilt[0]+(y-cy)*tilt[1])
        inner.append((cx+(x-cx)*(1-shrink), cy+(y-cy)*(1-shrink), z))
        outer.append((x, y, max(.0013, z-bevel*.5)))
        base.append((x, y, .001))
    centre = (cx, cy, max(.0018, height))
    for i in range(len(points)):
        j = (i+1) % len(points)
        geo.face([centre, inner[i], inner[j]], top)
        # Flush weathered rim retains the plate value. Detached/chipped pieces
        # receive a subtly brighter aggregate edge rather than a white outline.
        edge_mat = 'Aggregate' if height > .012 and rng.random() < .30 else top
        geo.face([inner[i], outer[i], outer[j], inner[j]], edge_mat)
        geo.face([outer[i], base[i], base[j], outer[j]], 'ConcreteDark')
    geo.face(list(reversed(base)), 'ConcreteDark')
    geo.pieces += 1

boundary = []
for i in range(39):
    a = math.tau*i/39
    irregular = 1 + .045*math.sin(a*5+.4) + .035*math.sin(a*9)
    boundary.append((math.cos(a)*RX*irregular, math.sin(a)*RY*irregular))
sites = []
for _ in range(8000):
    x, y = rng.uniform(-RX, RX), rng.uniform(-RY, RY)
    if (x/RX)**2+(y/RY)**2 > .93: continue
    if any((x-p[0])**2+(y-p[1])**2 < .17**2 for p in sites): continue
    sites.append((x, y))
    if len(sites) == 94: break

cells = []
for sx, sy in sites:
    cell = boundary[:]
    for ox, oy in sites:
        if (ox, oy) == (sx, sy): continue
        cell = clip_poly(cell, ox-sx, oy-sy, (ox*ox+oy*oy-sx*sx-sy*sy)/2)
        if not cell: break
    if len(cell) < 3: continue
    cx = sum(x for x, y in cell)/len(cell)
    cy = sum(y for x, y in cell)/len(cell)
    edge = (cx/RX)**2+(cy/RY)**2
    if edge > .73 and rng.random() < .73: continue
    if edge > .52 and rng.random() < .20: continue
    cells.append(cell)

edges = {}
def edge_data(a, b):
    key = tuple(sorted((tuple(round(v, 5) for v in a), tuple(round(v, 5) for v in b))))
    if key not in edges:
        seed = int(hashlib.sha256(repr(key).encode()).hexdigest()[:12], 16)
        er = random.Random(seed)
        start, end = Vector(key[0]), Vector(key[1])
        direction = end-start
        length = direction.length
        normal = Vector((-direction.y, direction.x)).normalized()
        count = max(3, int(length/.085))
        path = []
        for i in range(count+1):
            t = i/count
            amp = min(.027, length*.055)*math.sin(t*math.pi)
            p = start+direction*t+normal*er.uniform(-amp, amp)
            path.append(p)
        hidden = er.random() < .32
        width = er.uniform(.004, .018)
        # Some fracture sections are swallowed by wear. No full dark polygon loop.
        widths = [width*er.uniform(.30, 1.60) for _ in path]
        active = [not hidden and er.random() > .18 for _ in range(count)]
        edges[key] = {'path': path, 'widths': widths, 'active': active,
                      'hidden': hidden, 'length': length}
    row = edges[key]
    forward = (Vector(a)-row['path'][0]).length < (Vector(a)-row['path'][-1]).length
    return row, forward

material_counts = {n: 0 for n in MATERIAL_NAMES}
for index, cell in enumerate(cells):
    cx = sum(x for x, y in cell)/len(cell)
    cy = sum(y for x, y in cell)/len(cell)
    shape = []
    for i, a in enumerate(cell):
        b = cell[(i+1)%len(cell)]
        row, forward = edge_data(a, b)
        path = row['path'] if forward else list(reversed(row['path']))
        for j, p in enumerate(path[:-1]):
            distance = max(.05, math.hypot(p.x-cx, p.y-cy))
            inset = .0003 if row['hidden'] else rng.uniform(.001, .006)
            # Local missing chips alter geometry rather than drawing another line.
            if j not in (0, len(path)-2) and rng.random() < .045:
                inset += rng.uniform(.018, .045)
            shape.append((cx+(p.x-cx)*(1-inset/distance), cy+(p.y-cy)*(1-inset/distance)))
    if len(shape) < 3: continue
    # Correlated wear groups cross neighbouring cells; avoids checkerboard mosaic.
    wear = .60*math.sin(cx*1.75+.5)*math.cos(cy*1.25-.2)+.34*math.sin(cy*3.2+cx*.7)
    top = 'ConcreteLight' if wear > .28 else 'ConcreteDark' if wear < -.34 else 'Concrete'
    material_counts[top] += 1
    raised = rng.random() < .18
    height = rng.uniform(.010, .026) if raised else rng.uniform(.0018, .0040)
    plate(shape, height, top, bevel=.002 if not raised else .004,
          tilt=(rng.uniform(-.012, .012), rng.uniform(-.012, .012)) if raised else (0, 0))

active_segments = skipped_segments = 0
for row in edges.values():
    for i, active in enumerate(row['active']):
        if not active:
            skipped_segments += 1
            continue
        # Dark recess sits below shallow top surfaces and has variable width.
        geo.ribbon(row['path'][i:i+2], row['widths'][i:i+2], height=.0012)
        active_segments += 1

fragment_records = []
for i in range(17):
    a = rng.uniform(0, math.tau)
    r = rng.uniform(.70, 1.03)
    cx, cy = math.cos(a)*RX*r, math.sin(a)*RY*r
    diameter = rng.uniform(.20, .40)
    n = rng.randint(5, 8)
    phase = rng.uniform(0, math.tau)
    points = []
    for j in range(n):
        angle = phase+j*math.tau/n+rng.uniform(-.10, .10)
        radius = diameter*.5*rng.uniform(.75, 1.0)
        points.append((cx+math.cos(angle)*radius, cy+math.sin(angle)*radius*rng.uniform(.62, .95)))
    span = max(math.dist(a, b) for a in points for b in points)
    points = [(cx+(x-cx)*diameter/span, cy+(y-cy)*diameter/span) for x, y in points]
    actual_span = max(math.dist(a, b) for a in points for b in points)
    assert .20 <= actual_span <= .40
    h = rng.uniform(.012, .037)
    plate(points, h, rng.choice(['Concrete', 'ConcreteLight', 'Aggregate']), .005,
          (rng.uniform(-.025, .025), rng.uniform(-.025, .025)))
    fragment_records.append({'centre_m': [cx, cy], 'actual_max_span_cm': actual_span*100, 'height_cm': h*100})

name = 'SM_ParityFractureField_A_V3'
mesh = bpy.data.meshes.new(name+'_Geometry')
mesh.from_pydata(geo.vertices, [], geo.faces)
mesh.update()
obj = bpy.data.objects.new(name, mesh)
scene.collection.objects.link(obj)
for m in materials: mesh.materials.append(m)
for face, mat in zip(mesh.polygons, geo.mats): face.material_index = mat
uv = mesh.uv_layers.new(name='FloorMetres_4m')
for loop in mesh.loops:
    p = mesh.vertices[loop.vertex_index].co
    uv.data[loop.index].uv = (p.x/4, p.y/4)
mesh.calc_loop_triangles()
xyz = [v.co for v in mesh.vertices]
minimum = [min(p[i] for p in xyz) for i in range(3)]
maximum = [max(p[i] for p in xyz) for i in range(3)]
dims = [maximum[i]-minimum[i] for i in range(3)]
assert minimum[2] >= 0 and maximum[2] < .06, (minimum, maximum)
assert all(math.isfinite(v) for p in xyz for v in p)
assert len(mesh.loop_triangles) < 40000
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
fbx = OUT/(name+'.fbx')
bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'MESH'},
    axis_forward='-Y', axis_up='Z', global_scale=1, apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_NONE', mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False)

before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(fbx), use_anim=False)
loaded = [o for o in set(bpy.data.objects)-before if o.type == 'MESH']
assert len(loaded) == 1
test = loaded[0]
points = [test.matrix_world@v.co for v in test.data.vertices]
round_dims = [max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
error = max(abs(a-b) for a, b in zip(dims, round_dims))
test.data.calc_loop_triangles()
slots = [s.material.name.split('.')[0] for s in test.material_slots]
assert error < .00002, error
assert len(test.data.loop_triangles) == len(mesh.loop_triangles)
assert slots == MATERIAL_NAMES, slots
assert len(test.data.uv_layers) == 1
bpy.data.objects.remove(test, do_unlink=True)

manifest = {
    'owner': OWNER, 'status': 'verified_fbx_ready_for_unreal', 'generator': str(Path(__file__).relative_to(ROOT)),
    'source': 'Original deterministic local fracture repair; reuses reviewed geometry definitions from make_parity_floor.py without executing its authoring body.',
    'blender_version': bpy.app.version_string,
    'coordinate_system': 'Metres, +Z up, local XY centre near original field; Z=0 underlying floor. FBX axis -Y/+Z, apply_unit_scale true, FBX_SCALE_NONE.',
    'assets': [{'name': name, 'file': fbx.name, 'triangles': len(mesh.loop_triangles), 'vertices': len(mesh.vertices),
                'bounds_m': {'min': minimum, 'max': maximum}, 'dimensions_m': dims,
                'expected_dimensions_cm': [d*100 for d in dims], 'highest_point_cm': maximum[2]*100,
                'material_slots': MATERIAL_NAMES, 'sha256': hashlib.sha256(fbx.read_bytes()).hexdigest()}],
    'material_guidance': {'Concrete': 'Same world-aligned floor material.', 'ConcreteLight': 'Same floor material, base colour multiplied by1.18; preserve aligned maps.',
        'ConcreteDark': 'Same floor material, base colour multiplied by0.82; preserve aligned maps.',
        'Aggregate': 'Subdued slightly lighter fracture edge material, no emission.', 'Dark': 'Dark low-reflectance narrow recesses, no emission.'},
    'uv0': 'Local XY metres /4; world-aligned material recommended for seamless base-floor blending.',
    'construction': {'plate_count': len(cells), 'plate_material_counts': material_counts, 'distinct_edges': len(edges),
        'fully_interrupted_edges': sum(r['hidden'] for r in edges.values()), 'drawn_segments': active_segments,
        'interrupted_segments': skipped_segments, 'detached_fragments': fragment_records,
        'notes': 'Shared jittered paths, variable fracture width, selective missing chips, mostly flush faces with sparse tilted lifted plates. Correlated wear crosses cell groups.'},
    'fbx_roundtrip_checks': [{'passed': True, 'dimensions_m': round_dims, 'max_dimension_error_m': error,
        'triangles': len(mesh.loop_triangles), 'material_slots': slots, 'uv_layers': 1}],
    'placement': 'Replacement Field_A at existing local origin/rotation/XY scale. Put actor at measured floor top; keep Z scale1. NoCollision and actor collision false. Never overwrite previous mesh.',
    'preserved_source_hashes': original_hashes,
    'limits': 'Blender source, FBX roundtrip and previews only. Root integrator must import separately, bind slots, disable collision and inspect actual gameplay rendering.'
}
(OUT/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print('FRACTURE_V3_FBX_READY', json.dumps({'file': str(fbx), 'triangles': len(mesh.loop_triangles), 'dimensions_m': dims}), flush=True)

# Separate preview stage; nothing except the field was exported.
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
ground = bpy.context.object
ground.name = 'Preview only - base concrete'
ground.data.materials.append(materials[0])
world = bpy.data.worlds.new('Fracture V3 inspection')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.22, .27, .28, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .30
scene.world = world
for label, loc, energy, size in [('Raking key', (-3, -4, 4), 1000, 3), ('Soft fill', (4, 3, 6), 550, 5)]:
    data = bpy.data.lights.new(label, 'AREA')
    data.energy, data.size = energy, size
    light = bpy.data.objects.new(label, data)
    scene.collection.objects.link(light)
    light.location = loc
    light.rotation_euler = (Vector((0, 0, 0))-light.location).to_track_quat('-Z', 'Y').to_euler()
camdata = bpy.data.cameras.new('Fracture V3 overview')
camera = bpy.data.objects.new('Fracture V3 overview', camdata)
scene.collection.objects.link(camera)
camera.location = (1, -6.5, 7.4)
camera.rotation_euler = (Vector((0, 0, 0))-camera.location).to_track_quat('-Z', 'Y').to_euler()
camdata.type = 'ORTHO'
camdata.ortho_scale = 8.2
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 20
scene.cycles.use_denoising = True
scene.render.threads_mode = 'FIXED'
scene.render.threads = 4
scene.render.resolution_x, scene.render.resolution_y = 1200, 850
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.render.filepath = str(OUT/'fracture-v3-overview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ParityFracture_V3.blend'))
bpy.ops.render.render(write_still=True)
camera.location = (1.4, -4.6, 2.4)
camera.rotation_euler = (Vector((0, 0, 0))-camera.location).to_track_quat('-Z', 'Y').to_euler()
camdata.ortho_scale = 5.8
scene.render.filepath = str(OUT/'fracture-v3-depth.png')
bpy.ops.render.render(write_still=True)
after_hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (ROOT/'Assets/Adapted/Parity/Floor').glob('*') if p.is_file()}
assert original_hashes == after_hashes, 'Preserved Floor kit changed during build'
manifest['previews'] = ['fracture-v3-overview.png', 'fracture-v3-depth.png']
manifest['preserved_original_kit_verified'] = True
(OUT/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print('FRACTURE_V3_COMPLETE', json.dumps({'manifest': str(OUT/'manifest.json'), 'source_preserved': True}), flush=True)
