"""Coarser connected floor erosion for the chamber. New versioned export only.

Writes Assets/Adapted/ChamberParity/FloorMorphologyV3.
Does not import Unreal assets and does not overwrite Floor, Slabs, Crust, or any V2 kit.
Metres, local floor Z=0, static FBX axis_forward -Y, axis_up Z.
"""
import bpy
import bmesh
import hashlib
import itertools
import json
import math
import random
from collections import Counter
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Assets/Adapted/ChamberParity/FloorMorphologyV3'
OWNER = 'teddy-chamber-floor-morphology-v3-20261005'
if OUT.exists() and any(OUT.iterdir()):
    marker = OUT / 'manifest.json'
    if not marker.exists() or json.loads(marker.read_text(encoding='utf-8')).get('owner') != OWNER:
        raise RuntimeError('Refusing to overwrite unowned floor morphology')
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'manifest.json').write_text(json.dumps({'owner': OWNER, 'status': 'authoring'}), encoding='utf-8')
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
SLOTS = ['Concrete', 'ConcreteLight', 'ConcreteDark', 'Aggregate', 'Dark', 'Crack']
MATS = {}
for name, lo, hi in [
    ('Concrete', (.16, .177, .169, 1), (.24, .25, .232, 1)),
    ('ConcreteLight', (.17, .184, .171, 1), (.255, .265, .242, 1)),
    ('ConcreteDark', (.11, .122, .118, 1), (.18, .19, .178, 1)),
    ('Aggregate', (.13, .136, .128, 1), (.2, .208, .192, 1)),
    ('Dark', (.02, .026, .024, 1), (.04, .046, .04, 1)),
    ('Crack', (.008, .011, .01, 1), (.016, .02, .018, 1)),
]:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = hi
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value = .98 if name in ('Dark', 'Crack') else .94
    shader.inputs['Specular IOR Level'].default_value = 0 if name in ('Dark', 'Crack') else .1
    MATS[name] = mat

PATHS = [
    [(-11.6, -10.8), (-7.4, -5.2), (-2.2, -8.4), (1.8, -2.6), (-1.4, 2.2), (4.2, 5.6), (9.2, 1.4), (12.2, -4.8), (6.6, -10.2)],
    [(-0.6, 1.6), (2.8, 8.2), (8.6, 11.4), (12.0, 6.8)],
    [(-8.8, 2.4), (-12.2, 7.2), (-5.6, 11.6), (-0.8, 8.6)],
]


def area(poly):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))) / 2


def centre(poly):
    return (sum(x for x, y in poly) / len(poly), sum(y for x, y in poly) / len(poly))


def clip(poly, nx, ny, d):
    result = []
    a = poly[-1]
    da = a[0] * nx + a[1] * ny - d
    for b in poly:
        db = b[0] * nx + b[1] * ny - d
        if (da <= 0) != (db <= 0):
            t = da / (da - db)
            result.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        if db <= 0:
            result.append(b)
        a, da = b, db
    return result


def canonical(p):
    return (round(p[0], 5), round(p[1], 5))


def distance_segment(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    denom = dx * dx + dy * dy
    t = 0 if denom < 1e-12 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / denom))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def belt_distance(p):
    best = 1e9
    for path in PATHS:
        for a, b in zip(path, path[1:]):
            best = min(best, distance_segment(p, a, b))
    return best


def boundary_distance(p, boundary):
    return min(distance_segment(p, a, b) for a, b in zip(boundary, boundary[1:] + boundary[:1]))


def distort(p, amount):
    x, y = p
    return (x + amount * math.sin(y * 1.15 + 0.4), y + amount * math.cos(x * 1.05 - 0.2))


def split_once(poly, rng, min_area, min_ratio):
    cx, cy = centre(poly)
    spanx = max(x for x, y in poly) - min(x for x, y in poly)
    spany = max(y for x, y in poly) - min(y for x, y in poly)
    angle = rng.uniform(0, math.pi)
    if spanx > spany * 1.45:
        angle = rng.uniform(-.4, .4)
    elif spany > spanx * 1.45:
        angle = math.pi / 2 + rng.uniform(-.4, .4)
    nx, ny = math.cos(angle), math.sin(angle)
    d = nx * cx + ny * cy + rng.uniform(-.1, .1) * min(spanx, spany)
    left, right = clip(poly, nx, ny, d), clip(poly, -nx, -ny, -d)
    if min(len(left), len(right)) < 3:
        return None
    areas = (area(left), area(right))
    if min(areas) < min_area or min(areas) / max(areas) < min_ratio:
        return None
    return left, right


def split_toward(cells, target, rng, min_area, min_ratio, predicate=None):
    attempts = 0
    while len(cells) < target and attempts < target * 25:
        attempts += 1
        ranked = []
        for index, cell in enumerate(cells):
            if predicate and not predicate(cell):
                continue
            ranked.append((area(cell) * rng.uniform(.85, 1.15), index))
        if not ranked:
            break
        index = max(ranked)[1]
        parts = None
        for _ in range(8):
            parts = split_once(cells[index], rng, min_area, min_ratio)
            if parts:
                break
        if not parts:
            continue
        cells[index:index + 1] = list(parts)
    return cells


def subdivide_t_junctions(cells):
    points = sorted(set(canonical(p) for cell in cells for p in cell))
    result = []
    for poly in cells:
        refined = []
        for a, b in zip(poly, poly[1:] + poly[:1]):
            ax, ay = a
            dx, dy = b[0] - ax, b[1] - ay
            length2 = dx * dx + dy * dy
            if length2 < 1e-10:
                continue
            on = []
            for p in points:
                t = ((p[0] - ax) * dx + (p[1] - ay) * dy) / length2
                cross = abs((p[0] - ax) * dy - (p[1] - ay) * dx)
                if -1e-5 <= t < 1 - 1e-5 and cross < 3e-4:
                    on.append((t, p))
            refined.append(canonical(a))
            refined.extend(p for _, p in sorted(on))
        cleaned = []
        for p in refined:
            if not cleaned or p != cleaned[-1]:
                cleaned.append(p)
        if len(cleaned) >= 2 and cleaned[0] == cleaned[-1]:
            cleaned.pop()
        if len(cleaned) >= 3:
            result.append(cleaned)
    return result


class Geometry:
    def __init__(self):
        self.vertices = []
        self.faces = []
        self.indices = []

    def polygon(self, points, material):
        if len(points) < 3:
            return
        vectors = [Vector(p) for p in points]
        start = len(self.vertices)
        self.vertices.extend(points)
        lookup = {tuple(v): start + i for i, v in enumerate(vectors)}
        for tri in tessellate_polygon([vectors]):
            self.faces.append(tuple(start + v if isinstance(v, int) else lookup[tuple(v)] for v in tri))
            self.indices.append(SLOTS.index(material))

    def quad(self, a, b, c, d, material):
        self.polygon([a, b, c, d], material)

    def ribbon(self, points, widths, z, material='Crack'):
        for i, (a, b) in enumerate(zip(points, points[1:])):
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            if length < 1e-5:
                continue
            nx, ny = -dy / length, dx / length
            wa, wb = widths[i] / 2, widths[i + 1] / 2
            self.quad((a[0] - nx * wa, a[1] - ny * wa, z), (b[0] - nx * wb, b[1] - ny * wb, z),
                      (b[0] + nx * wb, b[1] + ny * wb, z), (a[0] + nx * wa, a[1] + ny * wa, z), material)

    def slab(self, poly, height, bevel, material='Concrete', tilt=(0, 0), base=.001, edge_material='Concrete', height_fade=None):
        cx, cy = centre(poly)
        n = len(poly)
        lower, outer, inner = [], [], []
        for x, y in poly:
            vx, vy = cx - x, cy - y
            length = max(.02, math.hypot(vx, vy))
            ix, iy = x + vx / length * bevel, y + vy / length * bevel
            z = max(base + .0004, min(.0375, height + (x - cx) * tilt[0] + (y - cy) * tilt[1]))
            if height_fade is not None:
                z = base + (z - base) * height_fade((x, y))
            lower.append((x, y, base))
            outer.append((x, y, max(base + .0003, z - bevel * .35)))
            inner.append((ix, iy, z))
        self.polygon(inner, material)
        for i in range(n):
            j = (i + 1) % n
            self.quad(inner[i], outer[i], outer[j], inner[j], edge_material)
            side = 'Dark' if edge_material == 'Aggregate' else edge_material
            self.quad(outer[i], lower[i], lower[j], outer[j], side)
        self.polygon(list(reversed(lower)), material)


def inset_poly(poly, amount):
    cx, cy = centre(poly)
    result = []
    for x, y in poly:
        vx, vy = cx - x, cy - y
        length = max(.02, math.hypot(vx, vy))
        result.append((x + vx / length * amount, y + vy / length * amount))
    return result


def angular(rng, x, y, span):
    n = rng.choice((3, 4, 4, 5))
    angle = rng.uniform(0, math.tau)
    radius = span * .5
    poly = []
    for j in range(n):
        a = angle + j * math.tau / n + rng.uniform(-.22, .22)
        r = radius * rng.uniform(.55, 1.15)
        poly.append((x + math.cos(a) * r, y + math.sin(a) * r * rng.uniform(.62, 1.05)))
    return poly


def make_field(name, seed):
    rng = random.Random(seed)
    boundary = [(-13.15, -12.4), (-11.4, -13.85), (-3.6, -14.15), (3.4, -13.7), (9.2, -13.15),
                (13.15, -10.6), (13.45, -2.4), (12.7, 5.2), (13.2, 10.4), (9.6, 13.55),
                (2.2, 14.15), (-5.4, 13.7), (-11.2, 12.15), (-13.25, 6.1), (-13.5, -1.6)]
    cells = [boundary]
    split_toward(cells, 18, rng, min_area=10.0, min_ratio=.24)
    split_toward(cells, 58, rng, min_area=1.15, min_ratio=.18,
                 predicate=lambda cell: belt_distance(centre(cell)) < 2.6 and area(cell) > 3.2)
    for _ in range(10):
        order = sorted(range(len(cells)), key=lambda i: belt_distance(centre(cells[i])))
        progressed = False
        for index in order[:8]:
            if area(cells[index]) < 3.2:
                continue
            parts = None
            for _attempt in range(6):
                parts = split_once(cells[index], rng, 1.05, .16)
                if parts:
                    break
            if parts:
                cells[index:index + 1] = list(parts)
                progressed = True
                break
        if not progressed:
            break
    cells = subdivide_t_junctions(cells)
    ranked = sorted(cells, key=lambda cell: (belt_distance(centre(cell)), area(cell)))
    medium = [cell for cell in ranked if belt_distance(centre(cell)) < 1.7 and 3.2 < area(cell) < 12]
    small = [cell for cell in ranked if belt_distance(centre(cell)) < 1.15 and area(cell) <= 3.2]
    dropped = (medium[:6] + small[:4])[:10]
    print('MORPHOLOGY_HOLES', len(medium), len(small), len(dropped), flush=True)
    drop_ids = {id(cell) for cell in dropped}
    kept = [cell for cell in cells if id(cell) not in drop_ids]
    print('MORPHOLOGY_CELLS', len(cells), 'kept', len(kept), 'dropped', len(dropped), flush=True)
    assert 28 <= len(kept) <= 90, len(kept)
    assert len(dropped) == 10, len(dropped)
    edges = {}
    for cell_index, cell in enumerate(kept):
        for a, b in zip(cell, cell[1:] + cell[:1]):
            key = tuple(sorted((a, b)))
            if a != b:
                edges.setdefault(key, {'owners': []})['owners'].append(cell_index)
    for key, edge in edges.items():
        a, b = key
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        local = random.Random(int(hashlib.sha256(repr((seed, key)).encode()).hexdigest()[:12], 16))
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        dist = belt_distance(mid)
        n = max(2, min(14, int(length / .55) + 1))
        amount = .07 if dist < 1.7 else .02
        points = []
        for i in range(n + 1):
            t = i / n
            jitter = math.sin(t * math.pi) * local.uniform(-1, 1) * min(.16 if dist < 1.7 else .04, length * .08)
            p = (a[0] + t * dx - dy / max(length, 1e-6) * jitter, a[1] + t * dy + dx / max(length, 1e-6) * jitter)
            points.append(distort(p, amount))
        edge['points'] = points
        edge['length'] = length
        edge['distance'] = dist
        if dist < .85:
            edge['width'] = local.uniform(.16, .30)
            edge['draw'] = True
        elif dist < 1.35 and length > 1.4 and local.random() < .35:
            edge['width'] = local.uniform(.06, .12)
            edge['draw'] = True
        else:
            edge['width'] = 0
            edge['draw'] = False
    outer_segments = []
    for edge in edges.values():
        if len(edge['owners']) == 1:
            outer_segments.extend(zip(edge['points'], edge['points'][1:]))

    def edge_fade(p):
        if not outer_segments:
            return 1
        distance = min(distance_segment(p, a, b) for a, b in outer_segments)
        return min(1, distance / .85) ** 1.25

    geo = Geometry()
    surface_counts = Counter()
    plate_heights = []
    plate_areas = []
    # Continuous low sheet. It hides the old fine-grain floor. No dark rim.
    geo.polygon([(x, y, .0024) for x, y in boundary], 'Concrete')
    geo.polygon([(x, y, .0012) for x, y in reversed(boundary)], 'Concrete')
    surface_counts['Concrete'] += 1
    for cell in kept:
        poly = []
        for a, b in zip(cell, cell[1:] + cell[:1]):
            key = tuple(sorted((a, b)))
            path = edges[key]['points']
            if a != key[0]:
                path = list(reversed(path))
            poly.extend(path[:-1])
        if len(poly) < 3:
            continue
        cx, cy = centre(poly)
        dist = belt_distance((cx, cy))
        fade = min(1, boundary_distance((cx, cy), boundary) / .9)
        if dist < 1.5:
            top = rng.uniform(.01, .02) * (.4 + .6 * fade)
            gap = rng.uniform(.03, .07) * max(.35, fade)
            material = 'ConcreteDark' if rng.random() < .62 else 'Concrete'
        elif dist < 3.0:
            top = rng.uniform(.0045, .008) * (.55 + .45 * fade)
            gap = rng.uniform(.003, .008)
            material = 'Concrete'
        else:
            top = .0042
            gap = .0008
            material = 'ConcreteLight' if rng.random() < .08 else 'Concrete'
        pp = inset_poly(poly, gap)
        if area(pp) < .4:
            continue
        geo.slab(pp, top, .008 * max(fade, .25), material, tilt=(rng.uniform(-.003, .003), rng.uniform(-.003, .003)),
                 base=.005, edge_material='Concrete', height_fade=edge_fade)
        surface_counts[material] += 1
        plate_heights.append(top)
        plate_areas.append(area(pp))
    fragments = []
    spots = [centre(cell) for cell in dropped]
    for path in PATHS:
        for a, b in zip(path, path[1:]):
            for t in (.2, .55, .85):
                spots.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    rng.shuffle(spots)
    for index, (x, y) in enumerate(spots[:16]):
        x = max(-13.3, min(13.3, x + rng.gauss(0, .22)))
        y = max(-13.8, min(13.8, y + rng.gauss(0, .22)))
        if belt_distance((x, y)) > 1.8:
            continue
        span = rng.uniform(.85, 1.45) if index % 4 == 0 else rng.uniform(.4, .8)
        poly = angular(rng, x, y, span)
        height = rng.uniform(.022, .036)
        geo.slab(poly, height, .012, 'Concrete', tilt=(rng.uniform(-.015, .015), rng.uniform(-.015, .015)),
                 base=.009, edge_material='Aggregate')
        fragments.append({'centre_m': [round(x, 3), round(y, 3)], 'nominal_span_cm': round(span * 100, 1), 'top_cm': round(height * 100, 2)})
    assert 10 <= len(fragments) <= 16, len(fragments)
    print('MORPHOLOGY_BREAKS', 'missing', len(dropped), 'fragments', len(fragments), flush=True)
    areas_sorted = sorted(plate_areas)
    assert areas_sorted[len(areas_sorted) // 2] > 2.0, areas_sorted[len(areas_sorted) // 2]
    mesh = bpy.data.meshes.new(name + '_Geometry')
    mesh.from_pydata(geo.vertices, [], geo.faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    for mat in MATS.values():
        mesh.materials.append(mat)
    for poly, index in zip(mesh.polygons, geo.indices):
        poly.material_index = index
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    uv = mesh.uv_layers.new(name='FloorMetres_4m')
    for loop in mesh.loops:
        p = mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (p.x / 4, p.y / 4)
    mesh.calc_loop_triangles()
    minimum = [min(v.co[i] for v in mesh.vertices) for i in range(3)]
    maximum = [max(v.co[i] for v in mesh.vertices) for i in range(3)]
    assert minimum[2] >= 0 and maximum[2] <= .039, (name, minimum, maximum)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(filepath=str(OUT / (name + '.fbx')), use_selection=True, object_types={'MESH'},
        axis_forward='-Y', axis_up='Z', global_scale=1, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
        use_mesh_modifiers=True, mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False, path_mode='AUTO')
    entry = {'name': name, 'file': name + '.fbx', 'triangles': len(mesh.loop_triangles), 'vertices': len(mesh.vertices),
             'bounds_m': {'min': minimum, 'max': maximum},
             'dimensions_m': [maximum[i] - minimum[i] for i in range(3)],
             'expected_dimensions_cm': [(maximum[i] - minimum[i]) * 100 for i in range(3)],
             'highest_point_cm': maximum[2] * 100, 'material_slots': SLOTS,
             'plate_count': len(plate_areas), 'missing_chunks': len(dropped), 'detached_fragments': fragments,
             'surface_material_counts': dict(surface_counts),
             'visible_erosion_edges': len(dropped), 'median_plate_area_m2': areas_sorted[len(areas_sorted) // 2],
             'plate_area_range_m2': [areas_sorted[0], areas_sorted[-1]],
             'plate_top_range_cm': [min(plate_heights) * 100, max(plate_heights) * 100],
             'origin': 'Local Z=0 is the underlying floor. Actor Z=-5 cm, Z scale exactly 1. NoCollision.',
             'sha256': hashlib.sha256((OUT / (name + '.fbx')).read_bytes()).hexdigest()}
    print('MORPHOLOGY_ASSET', name, entry['triangles'], 'plates', entry['plate_count'],
          'median_m2', round(entry['median_plate_area_m2'], 2), 'missing', len(dropped),
          'fragments', len(fragments), 'max_cm', round(entry['highest_point_cm'], 2), flush=True)
    return entry, obj


entry, obj = make_field('SM_ChamberFractureMorph_Main', 20261005)
checks = []
before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(OUT / entry['file']), use_anim=False)
loaded = [o for o in set(bpy.data.objects) - before if o.type == 'MESH']
assert len(loaded) == 1
roundtrip = loaded[0]
pts = [roundtrip.matrix_world @ v.co for v in roundtrip.data.vertices]
dims = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
error = max(abs(a - b) for a, b in zip(dims, entry['dimensions_m']))
roundtrip.data.calc_loop_triangles()
names = [slot.material.name.split('.')[0] for slot in roundtrip.material_slots]
assert error < .00005 and len(roundtrip.data.loop_triangles) == entry['triangles'] and names == SLOTS
assert len(roundtrip.data.uv_layers) == 1
checks.append({'name': entry['name'], 'max_dimension_error_m': error, 'triangles': len(roundtrip.data.loop_triangles),
               'slots': names, 'passed': True})
bpy.data.objects.remove(roundtrip, do_unlink=True)


def placement(label, loc, yaw=0, xy=1):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    pts = []
    for p in itertools.product(*zip(entry['bounds_m']['min'], entry['bounds_m']['max'])):
        x, y, z = p[0] * 100 * xy, -p[1] * 100 * xy, p[2] * 100
        pts.append((loc[0] + c * x - s * y, loc[1] + s * x + c * y, loc[2] + z))
    bounds = {'min': [min(p[i] for p in pts) for i in range(3)], 'max': [max(p[i] for p in pts) for i in range(3)]}
    assert bounds['min'][0] >= -1400 and bounds['max'][0] <= 1480
    assert bounds['min'][1] >= -1500 and bounds['max'][1] <= 1500
    assert bounds['min'][2] >= -5.05 and bounds['max'][2] <= 1.05
    return {'label': label, 'mesh': entry['name'], 'location_cm': loc, 'yaw': yaw, 'scale': [xy, xy, 1],
            'collision': 'NoCollision', 'world_bounds_cm': bounds}


placements = [placement('Main', [40, 0, -5])]
world = bpy.data.worlds.new('Neutral morphology study')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.16, .17, .16, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35
scene.world = world
for name, loc, power, size in [('Rake', (-8, -16, 10), 2500, 8), ('Overhead', (4, 6, 18), 1800, 12)]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = power
    data.size = size
    light = bpy.data.objects.new(name, data)
    scene.collection.objects.link(light)
    light.location = loc
    light.rotation_euler = (Vector((0, 0, 0)) - light.location).to_track_quat('-Z', 'Y').to_euler()
data = bpy.data.cameras.new('Morphology study')
camera = bpy.data.objects.new('Morphology study', data)
scene.collection.objects.link(camera)
data.type = 'ORTHO'
data.ortho_scale = 34
camera.location = (0, -18, 28)
camera.rotation_euler = (Vector((0, 0, 0)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = camera
scene.render.resolution_x = 1400
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(OUT / 'morphology-overview.png')
rendered = False
render_error = None
for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES'):
    try:
        scene.render.engine = engine
        if engine == 'CYCLES':
            scene.cycles.device = 'CPU'
            scene.cycles.samples = 16
            scene.cycles.use_denoising = True
        bpy.ops.render.render(write_still=True)
        rendered = True
        break
    except Exception as error:
        render_error = str(error)
blend = OUT / 'ChamberFloorMorphology_V3.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
manifest = {'owner': OWNER, 'status': 'source-ready-for-engine-review', 'generator': 'tools/make_chamber_floor_morphology.py',
            'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'editable_blend': 'Assets/Adapted/ChamberParity/FloorMorphologyV3/ChamberFloorMorphology_V3.blend',
            'blend_sha256': hashlib.sha256(blend.read_bytes()).hexdigest(),
            'source': 'Deterministic coarse plates, connected erosion along three paths, omitted chunks, and sparse angular fragments. Not a rerun of the fine Floor kit.',
            'preserved': 'Floor, FloorNormalsV2, Slabs, SlabsNormalsV2, Crust, CrustNormalsV2, characters, and the saved level are not modified by this generator.',
            'references': ['study/visuals/chamber-target-front.png', 'study/visuals/chamber-target-reverse.png'],
            'coordinate_system': 'Metres, +Z up. Static FBX mirrors Y in the project importer.',
            'fbx_settings': {'axis_forward': '-Y', 'axis_up': 'Z', 'global_scale': 1, 'apply_unit_scale': True, 'apply_scale_options': 'FBX_SCALE_NONE'},
            'material_slots': SLOTS,
            'material_scale': {'tile_cm': 3200, 'texture_weight': 0.22, 'normal': 'flat', 'detail_weight': 0.0,
                               'note': 'Importer builds M_Chamber_FloorMorph* only. No black crack cards. Flat normal. Large-scale stain.'},
            'assets': [entry], 'total_unique_triangles': entry['triangles'], 'fbx_roundtrip_checks': checks,
            'recommended_placements': placements,
            'construction_limits': 'Relief stays within 0-3.9 cm local and world Z -5.05 to 1.05 cm at the recommended placement. No collision. Exterior height tapers. Quiet plates stay outside the erosion paths.',
            'renders': ['morphology-overview.png'] if rendered else [],
            'render_engine_error': render_error}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print('MORPHOLOGY_COMPLETE', json.dumps({'triangles': entry['triangles'], 'rendered': rendered, 'placement': placements[0]['world_bounds_cm']}), flush=True)
