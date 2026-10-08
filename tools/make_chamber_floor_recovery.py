"""Recover medium-scale broken concrete. New versioned export only.

Writes Assets/Adapted/ChamberParity/FloorRecoveryV4.
Does not import Unreal assets and does not overwrite Floor, V2, or FloorMorphologyV3.
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
OUT = ROOT / 'Assets/Adapted/ChamberParity/FloorRecoveryV4'
OWNER = 'teddy-chamber-floor-recovery-v4-20261005'
V3 = ROOT / 'Assets/Adapted/ChamberParity/FloorMorphologyV3/manifest.json'
if OUT.exists() and any(OUT.iterdir()):
    marker = OUT / 'manifest.json'
    if not marker.exists() or json.loads(marker.read_text(encoding='utf-8')).get('owner') != OWNER:
        raise RuntimeError('Refusing to overwrite unowned floor recovery')
before_v3 = V3.read_bytes()
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'manifest.json').write_text(json.dumps({'owner': OWNER, 'status': 'authoring'}), encoding='utf-8')
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
SLOTS = ['Concrete', 'ConcreteLight', 'ConcreteDark', 'Aggregate', 'Dark', 'Crack']
MATS = {}
for name, color in [
    ('Concrete', (.22, .23, .22, 1)),
    ('ConcreteLight', (.26, .27, .25, 1)),
    ('ConcreteDark', (.16, .17, .16, 1)),
    ('Aggregate', (.2, .2, .19, 1)),
    ('Dark', (.08, .09, .08, 1)),
    ('Crack', (.14, .15, .14, 1)),
]:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = color
    MATS[name] = mat

PATHS = [
    [(-15.4, -11.6), (-8.6, -7.2), (-2.4, -10.4), (3.6, -5.2), (9.4, -8.8), (14.8, -3.6)],
    [(-14.8, 2.4), (-7.2, -1.2), (-0.6, 3.4), (6.2, 0.4), (12.8, 4.2), (15.6, -1.8)],
    [(-13.2, 12.4), (-6.4, 8.2), (0.8, 11.6), (7.2, 7.4), (13.4, 12.2)],
    [(-16.2, -4.8), (-12.4, 1.6), (-15.2, 8.6), (-9.6, 13.2)],
]


def signed_area(poly):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1])) / 2


def area(poly):
    return abs(signed_area(poly))


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


def _cross(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    return (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)


def _unit_normal(a, b, c):
    """Normalized face normal. None only for a collapsed triangle.

    Cross-product length below 1e-8 is area below 5e-9 m2. This is numerical
    collapse, not an area allowance. A 50 cm2 bevel is a real face and is tested.
    """
    normal = _cross(a, b, c)
    magnitude = math.sqrt(normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2)
    if magnitude < 1e-8:
        return None
    return (normal[0] / magnitude, normal[1] / magnitude, normal[2] / magnitude)


def distort(p, amount):
    x, y = p
    return (x + amount * math.sin(y * 1.7 + 0.6), y + amount * math.cos(x * 1.4 - 0.3))


def split_once(poly, rng, min_area, min_ratio):
    cx, cy = centre(poly)
    spanx = max(x for x, y in poly) - min(x for x, y in poly)
    spany = max(y for x, y in poly) - min(y for x, y in poly)
    angle = rng.uniform(0, math.pi)
    if spanx > spany * 1.35:
        angle = rng.uniform(-.7, .7)
    elif spany > spanx * 1.35:
        angle = math.pi / 2 + rng.uniform(-.7, .7)
    nx, ny = math.cos(angle), math.sin(angle)
    d = nx * cx + ny * cy + rng.uniform(-.28, .28) * min(spanx, spany)
    left, right = clip(poly, nx, ny, d), clip(poly, -nx, -ny, -d)
    if min(len(left), len(right)) < 3:
        return None
    areas = (area(left), area(right))
    if min(areas) < min_area or min(areas) / max(areas) < min_ratio:
        return None
    return left, right


def split_toward(cells, target, rng, min_area, min_ratio, predicate=None):
    attempts = 0
    while len(cells) < target and attempts < target * 30:
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
        for _ in range(10):
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
        self.bevel_faults = []

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

    def slab(self, poly, height, bevel, material='Concrete', tilt=(0, 0), base=.004, edge_material='Concrete', height_fade=None):
        if signed_area(poly) < 0:
            poly = list(reversed(poly))
        cx, cy = centre(poly)
        radii = [math.hypot(x - cx, y - cy) for x, y in poly]
        bevel = min(bevel, max(.002, min(radii) * .35))
        inset = _miter_inset(poly, bevel)
        n = len(poly)
        lower, outer, inner = [], [], []
        for (x, y), (ix, iy) in zip(poly, inset):
            z = height + (x - cx) * tilt[0] + (y - cy) * tilt[1]
            z = max(base + .0022, min(.036, z))
            if height_fade is not None:
                fade = max(0.0, min(1.0, float(height_fade((x, y)))))
                z = base + (z - base) * fade
            # The cap stays above the outer ring. Clamping the ring up to base
            # while the cap sits on base inverts the bevel.
            z = max(base + .0018, min(.036, z))
            drop = min(max(bevel, .004) * .35, max(.0006, (z - base) * .62))
            outer_z = z - drop
            outer_z = max(base + .0002, min(outer_z, z - .00045))
            assert z > outer_z + .0002, (z, outer_z, height)
            lower.append((x, y, base))
            outer.append((x, y, outer_z))
            inner.append((ix, iy, z))
        self._authored_caps(inner)
        self.polygon(inner, material)
        for i in range(n):
            j = (i + 1) % n
            dx = outer[j][0] - outer[i][0]
            dy = outer[j][1] - outer[i][1]
            elen = math.hypot(dx, dy)
            if elen < 1e-8:
                continue
            # Inset this edge to its own left. A shared miter corner folds one
            # triangle on concave chips; the edge strip does not.
            left = (-dy / elen, dx / elen)
            bevel_i = (outer[i][0] + left[0] * bevel, outer[i][1] + left[1] * bevel, inner[i][2])
            bevel_j = (outer[j][0] + left[0] * bevel, outer[j][1] + left[1] * bevel, inner[j][2])
            outward = (dy, -dx)
            self._authored_pair((bevel_i, outer[i], outer[j]), (bevel_i, outer[j], bevel_j), outward, 'bevel')
            self._authored_pair((outer[i], lower[i], lower[j]), (outer[i], lower[j], outer[j]), outward, 'side')
            self.quad(bevel_i, outer[i], outer[j], bevel_j, edge_material)
            side = 'ConcreteDark' if edge_material == 'Aggregate' else 'Concrete'
            self.quad(outer[i], lower[i], lower[j], outer[j], side)
        self.polygon(list(reversed(lower)), material)

    def _authored_caps(self, ring):
        vectors = [Vector((p[0], p[1], p[2])) for p in ring]
        if len(vectors) < 3:
            return
        for tri in tessellate_polygon([vectors]):
            points = [vectors[index] for index in tri]
            unit = _unit_normal(*points)
            if unit is None:
                continue
            if unit[2] <= 0:
                self.bevel_faults.append(('cap', unit[2], 0.0))

    def _authored_pair(self, first, second, outward, kind):
        ox, oy = outward
        olen = math.hypot(ox, oy)
        if olen < 1e-8:
            return
        ox, oy = ox / olen, oy / olen
        for tri in (first, second):
            unit = _unit_normal(*tri)
            if unit is None:
                continue
            dot = unit[0] * ox + unit[1] * oy
            if kind == 'bevel':
                if unit[2] <= 0 or dot <= 0:
                    self.bevel_faults.append((kind, unit[2], dot))
            elif dot <= 0:
                self.bevel_faults.append((kind, unit[2], dot))


def _miter_inset(poly, distance):
    """Move each corner along the local inward bisector, not toward the centroid."""
    points = []
    count = len(poly)
    for index in range(count):
        previous = poly[(index - 1) % count]
        current = poly[index]
        nxt = poly[(index + 1) % count]
        ax, ay = current[0] - previous[0], current[1] - previous[1]
        bx, by = nxt[0] - current[0], nxt[1] - current[1]
        la = math.hypot(ax, ay) or 1e-9
        lb = math.hypot(bx, by) or 1e-9
        left0 = (-ay / la, ax / la)
        left1 = (-by / lb, bx / lb)
        sx, sy = left0[0] + left1[0], left0[1] + left1[1]
        length = math.hypot(sx, sy)
        if length < 1e-6:
            sx, sy = left0
            scale = distance
        else:
            sx, sy = sx / length, sy / length
            support = left0[0] * sx + left0[1] * sy
            if support <= 0:
                sx, sy = -sx, -sy
                scale = distance
            else:
                scale = min(distance / support, distance * 2.2)
        points.append((current[0] + sx * scale, current[1] + sy * scale))
    return points


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
        a = angle + j * math.tau / n + rng.uniform(-.28, .28)
        r = radius * rng.uniform(.5, 1.2)
        poly.append((x + math.cos(a) * r, y + math.sin(a) * r * rng.uniform(.58, 1.08)))
    return poly


def make_field(name, seed):
    rng = random.Random(seed)
    boundary = [
        (-17.2, -12.8), (-16.6, -15.05), (-9.4, -15.15), (-1.2, -14.85),
        (6.8, -15.2), (12.6, -14.7), (16.3, -12.2), (16.45, -4.6),
        (16.15, 3.8), (16.4, 11.4), (13.2, 15.05), (5.4, 15.2),
        (-2.8, 14.9), (-10.4, 15.15), (-15.8, 14.4), (-17.25, 7.2),
        (-17.35, -1.4), (-17.1, -8.2),
    ]
    cells = [boundary]
    split_toward(cells, 90, rng, min_area=6.0, min_ratio=.28)
    split_toward(cells, 180, rng, min_area=3.2, min_ratio=.24, predicate=lambda cell: area(cell) > 8)
    split_toward(cells, 460, rng, min_area=0.45, min_ratio=.2,
                 predicate=lambda cell: belt_distance(centre(cell)) < 2.15 and area(cell) > 1.5)
    split_toward(cells, 620, rng, min_area=0.22, min_ratio=.18,
                 predicate=lambda cell: belt_distance(centre(cell)) < 1.05 and area(cell) > 0.85)
    for _ in range(80):
        big = [i for i, cell in enumerate(cells) if area(cell) > 9.2]
        if not big:
            break
        index = max(big, key=lambda i: area(cells[i]))
        parts = None
        for _attempt in range(12):
            parts = split_once(cells[index], rng, 1.6, .2)
            if parts:
                break
        if not parts:
            break
        cells[index:index + 1] = list(parts)
    cells = subdivide_t_junctions(cells)
    ranked = sorted(cells, key=lambda cell: (belt_distance(centre(cell)), -area(cell)))
    bites = [cell for cell in ranked if belt_distance(centre(cell)) < 1.05 and 0.18 < area(cell) < 1.25]
    rng.shuffle(bites)
    dropped = bites[:22]
    print('RECOVERY_BITES', len(bites), 'used', len(dropped), flush=True)
    drop_ids = {id(cell) for cell in dropped}
    kept = [cell for cell in cells if id(cell) not in drop_ids]
    print('RECOVERY_CELLS', len(cells), 'kept', len(kept), flush=True)
    assert 180 <= len(kept) <= 900, len(kept)
    assert 14 <= len(dropped) <= 28, len(dropped)
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
        on_chamber_boundary = boundary_distance(mid, boundary) < .5
        internal_gap = len(edge['owners']) == 1 and not on_chamber_boundary
        eroded = (internal_gap or dist < 1.35) and not on_chamber_boundary
        n = max(3, min(12, int(length / (.42 if eroded else .8)) + 1))
        amount = .16 if eroded else .03
        jitter_cap = min(.32 if eroded else .04, length * (.24 if eroded else .05))
        points = []
        nx, ny = -dy / max(length, 1e-6), dx / max(length, 1e-6)
        for i in range(n + 1):
            t = i / n
            jitter = math.sin(t * math.pi) * local.uniform(-1, 1) * jitter_cap
            p = (a[0] + t * dx + nx * jitter, a[1] + t * dy + ny * jitter)
            points.append(distort(p, amount))
        if eroded and length > 1.15:
            for notch_t in ((.34, .66) if length > 1.7 else (.5,)):
                index = min(n - 1, max(1, int(round(notch_t * n))))
                push = local.uniform(.12, .30) * (1 if local.random() < .5 else -1)
                px, py = points[index]
                points[index] = (px + nx * push, py + ny * push)
        edge['points'] = points
    bite_segments = []
    for cell in dropped:
        bite_segments.extend(zip(cell, cell[1:] + cell[:1]))

    def perimeter_fade(p):
        return min(1.0, boundary_distance(p, boundary) / .55) ** 1.1

    def bite_lip(p):
        if not bite_segments:
            return 1.0
        near = min(distance_segment(p, a, b) for a, b in bite_segments)
        if near >= .62:
            return 1.0
        t = near / .62
        wave = abs(math.sin(p[0] * 13.0 + p[1] * 8.4))
        chip = .42 + .28 * wave
        return max(.42, min(1.0, chip + (1.0 - chip) * (t ** .75)))

    def edge_fade(p):
        # Perimeter only meets the drainage. Internal bites keep a chipped lip.
        return max(0.0, min(1.0, perimeter_fade(p) * bite_lip(p)))

    internal_lips = []
    for cell in dropped:
        for a, b in zip(cell, cell[1:] + cell[:1]):
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            if boundary_distance(mid, boundary) > .8:
                internal_lips.append(bite_lip(mid))
    perimeter_samples = [perimeter_fade(p) for p in boundary]
    assert internal_lips and min(internal_lips) >= .42, (min(internal_lips) if internal_lips else None)
    assert max(perimeter_samples) <= .02, max(perimeter_samples)
    print('FADE_BITE', round(min(internal_lips), 3), round(max(internal_lips), 3),
          'FADE_PERIMETER', round(max(perimeter_samples), 4), flush=True)

    geo = Geometry()
    surface_counts = Counter()
    plate_heights = []
    plate_areas = []
    geo.polygon([(x, y, .0032) for x, y in boundary], 'Concrete')
    geo.polygon([(x, y, .0014) for x, y in reversed(boundary)], 'Concrete')
    surface_counts['Concrete'] += 1
    # Missing bites stay the lower concrete sheet. A dark cap in the same
    # polygon was the flat triangular patch. Chips below sit in that recess.
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
        fade = min(1, boundary_distance((cx, cy), boundary) / .8)
        if dist < 1.15:
            top = rng.uniform(.022, .034) * (.8 + .2 * fade)
            gap = rng.uniform(.05, .12) * max(.6, fade)
            material = 'Concrete'
            edge_material = 'Aggregate'
        elif dist < 2.4:
            top = rng.uniform(.012, .02) * (.82 + .18 * fade)
            gap = rng.uniform(.02, .05)
            material = 'Concrete'
            edge_material = 'Aggregate' if rng.random() < .35 else 'Concrete'
        else:
            top = rng.uniform(.0035, .0065)
            gap = rng.uniform(.002, .005)
            material = 'ConcreteLight' if rng.random() < .08 else 'Concrete'
            edge_material = 'Concrete'
        pp = inset_poly(poly, gap)
        if area(pp) < .12:
            continue
        geo.slab(pp, top, .012 * max(fade, .3), material, tilt=(rng.uniform(-.004, .004), rng.uniform(-.004, .004)),
                 base=.005, edge_material=edge_material, height_fade=edge_fade)
        surface_counts[material] += 1
        plate_heights.append(top)
        plate_areas.append(area(pp))
    fragments = []

    def contains(poly, p):
        x, y = p
        hit = False
        a = poly[-1]
        for b in poly:
            if ((a[1] > y) != (b[1] > y)) and (x < (b[0] - a[0]) * (y - a[1]) / ((b[1] - a[1]) or 1e-9) + a[0]):
                hit = not hit
            a = b
        return hit

    def add_fragment(x, y, span, height):
        if boundary_distance((x, y), boundary) < .5:
            return False
        poly = angular(rng, x, y, span)
        geo.slab(poly, height, .01, 'ConcreteLight', tilt=(rng.uniform(-.01, .01), rng.uniform(-.01, .01)),
                 base=.004, edge_material='Aggregate')
        fragments.append({'centre_m': [round(x, 3), round(y, 3)], 'nominal_span_cm': round(span * 100, 1), 'top_cm': round(height * 100, 2)})
        return True

    for cell in dropped:
        cx, cy = centre(cell)
        span = min(1.15, max(.42, math.sqrt(area(cell)) * .9))
        placed = add_fragment(cx, cy, span, rng.uniform(.02, .032))
        if area(cell) > .45:
            for _ in range(4):
                ox, oy = rng.uniform(-span * .35, span * .35), rng.uniform(-span * .35, span * .35)
                if contains(cell, (cx + ox, cy + oy)):
                    placed = add_fragment(cx + ox, cy + oy, span * rng.uniform(.35, .6), rng.uniform(.016, .028)) or placed
                    break
        if not placed and contains(cell, (cx, cy)):
            add_fragment(cx, cy, min(span, .5), rng.uniform(.018, .028))
    assert 18 <= len(fragments) <= 55, len(fragments)
    print('BEVEL_FAULTS', len(geo.bevel_faults), 'sample', geo.bevel_faults[:4], flush=True)
    assert not geo.bevel_faults, geo.bevel_faults[:8]
    areas_sorted = sorted(plate_areas)
    median = areas_sorted[len(areas_sorted) // 2]
    medium = sum(1 for value in plate_areas if .2 <= value <= 2.2)
    quiet = sum(1 for value in plate_areas if value >= 3.2)
    print('RECOVERY_AREAS', 'plates', len(plate_areas), 'median', round(median, 3),
          'max', round(areas_sorted[-1], 3), 'medium', medium, 'quiet', quiet, flush=True)
    assert .45 <= median <= 3.2, median
    assert areas_sorted[-1] < 12, areas_sorted[-1]
    assert medium >= 80, medium
    assert quiet >= 18, quiet
    assert max(area(cell) for cell in dropped) < 1.6
    mesh = bpy.data.meshes.new(name + '_Geometry')
    mesh.from_pydata(geo.vertices, [], geo.faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    for mat in MATS.values():
        mesh.materials.append(mat)
    for poly, index in zip(mesh.polygons, geo.indices):
        poly.material_index = index
    # No weld, recalculation, or flip. Those passes rewrote loose faces and were
    # not proof. The export keeps the authored winding verified above.
    repairs = 0
    mesh.update()
    cap_down = 0
    for poly in mesh.polygons:
        zs = [mesh.vertices[index].co.z for index in poly.vertices]
        # Tops, including quiet caps below 1 cm. Undersides sit on the slab base.
        if min(zs) > .0055 and poly.normal.z <= 0:
            cap_down += 1
    print('NORMAL_CHECK', 'faces', len(mesh.polygons), 'authored_tops_down', cap_down,
          'repairs', repairs, flush=True)
    assert cap_down == 0, cap_down
    uv = mesh.uv_layers.new(name='FloorMetres_4m')
    for loop in mesh.loops:
        p = mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (p.x / 4, p.y / 4)
    mesh.calc_loop_triangles()
    minimum = [min(v.co[i] for v in mesh.vertices) for i in range(3)]
    maximum = [max(v.co[i] for v in mesh.vertices) for i in range(3)]
    assert minimum[2] >= 0 and maximum[2] <= .037, (name, minimum, maximum)
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
             'plate_count': len(plate_areas), 'recess_bites': len(dropped), 'detached_fragments': fragments,
             'surface_material_counts': dict(surface_counts),
             'medium_plate_count': medium, 'quiet_plate_count': quiet,
             'median_plate_area_m2': median,
             'plate_area_range_m2': [areas_sorted[0], areas_sorted[-1]],
             'plate_top_range_cm': [min(plate_heights) * 100, max(plate_heights) * 100],
             'origin': 'Local Z=0 is the arena top. Actor Z=-5 cm, Z scale exactly 1. NoCollision. Sheet reaches the drainage lip.',
             'normal_repairs': repairs,
             'sha256': hashlib.sha256((OUT / (name + '.fbx')).read_bytes()).hexdigest()}
    print('RECOVERY_ASSET', name, entry['triangles'], 'plates', entry['plate_count'],
          'median_m2', round(median, 2), 'bites', len(dropped), 'fragments', len(fragments),
          'max_cm', round(entry['highest_point_cm'], 2), flush=True)
    return entry, obj


entry, obj = make_field('SM_ChamberFractureRecover_Main', 202610054)
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
roundtrip.data.update()
# Exact coverage: polygons whose lowest vertex is above local Z = 1 cm and whose
# normal Z is negative. Quiet caps below 1 cm, and every side face, are outside
# this round-trip count. Those are covered by the authored triangle test.
imported_down = sum(1 for poly in roundtrip.data.polygons if min(roundtrip.data.vertices[index].co.z for index in poly.vertices) > .01 and poly.normal.z < 0)
assert imported_down == 0, imported_down
checks.append({'name': entry['name'], 'max_dimension_error_m': error, 'triangles': len(roundtrip.data.loop_triangles),
               'slots': names, 'passed': True,
               'fbx_downward_above_1cm': imported_down,
               'fbx_check_coverage': 'lowest vertex above 1 cm and normal Z < 0 only; quiet caps below 1 cm and side orientation are not in this count',
               'authored_normal_faults': 0, 'normal_repairs': entry['normal_repairs']})
bpy.data.objects.remove(roundtrip, do_unlink=True)


def placement(label, loc, yaw=0, xy=1):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    pts = []
    for p in itertools.product(*zip(entry['bounds_m']['min'], entry['bounds_m']['max'])):
        x, y, z = p[0] * 100 * xy, -p[1] * 100 * xy, p[2] * 100
        pts.append((loc[0] + c * x - s * y, loc[1] + s * x + c * y, loc[2] + z))
    bounds = {'min': [min(p[i] for p in pts) for i in range(3)], 'max': [max(p[i] for p in pts) for i in range(3)]}
    assert bounds['min'][2] >= -5.05 and bounds['max'][2] <= 1.05, bounds
    assert bounds['min'][0] <= -1650 and bounds['max'][0] >= 1640, bounds
    assert bounds['min'][1] <= -1490 and bounds['max'][1] >= 1490, bounds
    assert bounds['min'][1] >= -1540 and bounds['max'][1] <= 1540, bounds
    return {'label': label, 'mesh': entry['name'], 'location_cm': loc, 'yaw': yaw, 'scale': [xy, xy, 1],
            'collision': 'NoCollision', 'world_bounds_cm': bounds}


placements = [placement('Main', [40, 0, -5])]
assert V3.read_bytes() == before_v3
world = bpy.data.worlds.new('Neutral recovery study')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.16, .17, .16, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35
scene.world = world
for name, loc, power, size in [('Rake', (-8, -18, 12), 2500, 8), ('Overhead', (4, 6, 18), 1800, 12)]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = power
    data.size = size
    light = bpy.data.objects.new(name, data)
    scene.collection.objects.link(light)
    light.location = loc
    light.rotation_euler = (Vector((0, 0, 0)) - light.location).to_track_quat('-Z', 'Y').to_euler()
data = bpy.data.cameras.new('Recovery study')
camera = bpy.data.objects.new('Recovery study', data)
scene.collection.objects.link(camera)
data.type = 'ORTHO'
data.ortho_scale = 42
camera.location = (0, -22, 32)
camera.rotation_euler = (Vector((0, 0, 0)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = camera
scene.render.resolution_x = 1400
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(OUT / 'recovery-overview.png')
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
blend = OUT / 'ChamberFloorRecovery_V4.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
manifest = {'owner': OWNER, 'status': 'source-ready-for-engine-review', 'generator': 'tools/make_chamber_floor_recovery.py',
            'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'editable_blend': 'Assets/Adapted/ChamberParity/FloorRecoveryV4/ChamberFloorRecovery_V4.blend',
            'blend_sha256': hashlib.sha256(blend.read_bytes()).hexdigest(),
            'source': 'Corrected V4: chamber-boundary fade only, chipped lips around internal bites, outward-falling bevels, concrete caps, grounded chips in the missing concrete. The sheet meets the drainage lip. V3 remains a separate preserved export.',
            'correction': 'Perimeter fade stays on the chamber boundary. Bevel and side triangles are tested with normalized normals against the local CCW outward (dy, -dx), including both triangles of a non-planar quad. No area cutoff above numerical collapse.',
            'normal_orientation': {
                'authored': 'Non-degenerate cap, bevel, and side triangles. Bevel normals must have positive normalized Z and a positive dot with local edge outward (dy, -dx). Side normals must have a positive outward dot. Both triangles of each quad are tested. Degenerate means cross-product length below 1e-8.',
                'repair': 'None. Faces are not welded, recalculated, or flipped after the authored test. A later flip would not be proof of orientation.',
                'fbx_roundtrip': 'Downward normals are counted only for polygons whose lowest vertex is above 1 cm. That count does not cover quiet caps below 1 cm or side orientation.',
                'watertightness_required': False,
            },
            'preserved': 'Floor, FloorNormalsV2, Slabs, SlabsNormalsV2, Crust, CrustNormalsV2, FloorMorphologyV3, characters, and lighting are not modified by this generator.',
            'v3_manifest_sha256': hashlib.sha256(before_v3).hexdigest(),
            'references': ['study/visuals/chamber-target-front.png', 'study/visuals/chamber-target-reverse.png'],
            'coordinate_system': 'Metres, +Z up. Static FBX mirrors Y in the project importer.',
            'fbx_settings': {'axis_forward': '-Y', 'axis_up': 'Z', 'global_scale': 1, 'apply_unit_scale': True, 'apply_scale_options': 'FBX_SCALE_NONE'},
            'material_slots': SLOTS,
            'material_scale': {'tile_cm': 720, 'detail_weight': 0.28, 'normal_mix': 0.28, 'value_scale': 0.74,
                               'foreground_damp': 0.42, 'foreground_dry': 0.94,
                               'note': 'Importer builds M_Chamber_FloorRecover* only. Concrete normal and wet/dry roughness. No black cards. No flat normal.'},
            'assets': [entry], 'total_unique_triangles': entry['triangles'], 'fbx_roundtrip_checks': checks,
            'recommended_placements': placements,
            'construction_limits': 'Relief stays within 0-3.7 cm local and world Z -5.05 to 1.05 cm. No collision. Perimeter reaches the drainage lip without covering the grate centre.',
            'renders': ['recovery-overview.png'] if rendered else [],
            'render_engine_error': render_error}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print('RECOVERY_COMPLETE', json.dumps({'triangles': entry['triangles'], 'rendered': rendered, 'placement': placements[0]['world_bounds_cm']}), flush=True)
