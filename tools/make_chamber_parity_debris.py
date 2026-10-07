"""Original, grounded concrete shards for the isolated 20261007 chamber candidate.

Blender background script. Reads the preserved recovery FBX for contact height.
Writes only Assets/Adapted/ChamberParity/Parity20261007. No Unreal mutations.
"""
import bpy
import bmesh
import hashlib
import json
import math
import os
import random
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Assets/Adapted/ChamberParity/Parity20261007'
REVISION = int(os.environ.get('CHAMBER_DEBRIS_REVISION', '1'))
assert REVISION in (1, 2)
if REVISION == 2:
    OUT = OUT / 'DebrisV2'
OWNER = 'chamber-parity-20261007'
OUT.mkdir(parents=True, exist_ok=True)
assert not (OUT / 'manifest.json').exists(), 'Use a new revision rather than overwrite exported art.'
SOURCE = ROOT / 'Assets/Adapted/ChamberParity/FloorRecoveryV4/SM_ChamberFractureRecover_Main.fbx'
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1
bpy.ops.import_scene.fbx(filepath=str(SOURCE), use_anim=False)
floor = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
tree = BVHTree.FromPolygons([floor.matrix_world @ v.co for v in floor.data.vertices],
                          [list(p.vertices) for p in floor.data.polygons])

def height(x, y):
    point, normal, _, _ = tree.ray_cast(Vector((x - .4, y, 2)), Vector((0, 0, -1)))
    assert point is not None, (x, y)
    return point.z - .05

SLOTS = ['Concrete', 'ChippedEdge', 'WetShard']
mats = []
for name, color in zip(SLOTS, [(.23, .24, .22, 1), (.13, .14, .13, 1), (.065, .074, .070, 1)]):
    m = bpy.data.materials.new(name)
    m.diffuse_color = color
    mats.append(m)
rng = random.Random(7102026)
# Deliberately uneven banks with quiet central combat space, not a uniform grid.
clusters = [(-11, -12, 3.4, 1.5, 115), (-2, -12.4, 4.5, 1.5, 115),
            (9, -12, 3.7, 1.7, 100), (11.8, 2, 2.0, 6.0, 110),
            (0, 12.8, 5.6, 1.4, 115), (-11.7, 11, 2.7, 2.6, 85),
            (-11, -3, 1.7, 2.3, 45), (2, -4.5, 2.7, 1.6, 25)]
groups = {i: {'verts': [], 'faces': [], 'materials': [], 'pieces': []} for i in range(4)}
for cx, cy, sx, sy, count in clusters:
    for _ in range(count):
        x = max(-15.2, min(15.2, rng.gauss(cx, sx * .55)))
        y = max(-14.5, min(14.5, rng.gauss(cy, sy * .55)))
        span = (rng.uniform(.28, .86) if rng.random() < .46 else rng.uniform(.08, .29)) if REVISION == 2 else (rng.uniform(.18, .58) if rng.random() < .30 else rng.uniform(.045, .24))
        n = rng.choice([3, 4, 4, 5, 6])
        phi = rng.uniform(0, math.tau)
        radii = [rng.uniform(.65, 1.) * span / 2 for _ in range(n)]
        poly = [(x + r * math.cos(phi + j * math.tau / n),
                 y + r * math.sin(phi + j * math.tau / n) * .8) for j, r in enumerate(radii)]
        ground = [height(px, py) for px, py in poly]
        thickness = rng.uniform(.015, .045) if span > .18 else rng.uniform(.008, .025)
        top_z = max(ground) + thickness
        tilt = rng.uniform(-.023, .023)
        base = [(px, py, h - .002) for (px, py), h in zip(poly, ground)]
        outer = [(px, py, top_z + tilt * (px - x) / span - .005) for px, py in poly]
        inner = [(x + (px - x) * .89, y + (py - y) * .89,
                  top_z + tilt * (px - x) / span) for px, py in poly]
        g = groups[int(x > 0) * 2 + int(y > 0)]
        start = len(g['verts'])
        g['verts'].extend(base + outer + inner)
        def face(vs, mat):
            g['faces'].append(tuple(start + i for i in vs))
            g['materials'].append(mat)
        face(list(reversed(range(n))), 1)
        face(list(range(n * 2, n * 3)), 2 if rng.random() < .16 else 0)
        for j in range(n):
            k = (j + 1) % n
            face([j, k, n + k, n + j], 1)
            face([n + j, n + k, 2 * n + k, 2 * n + j], 0)
        g['pieces'].append({'centre_blender_m': [x, y], 'span_m': span,
                            'floor_range_m': [min(ground), max(ground)], 'thickness_m': thickness})

bpy.data.objects.remove(floor, do_unlink=True)
assets = []
for index, g in groups.items():
    name = 'SM_Parity20261007_Debris_' + str(index) + ('_V2' if REVISION == 2 else '')
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(g['verts'], [], g['faces'])
    assert not mesh.validate(), 'Invalid authored geometry'
    mesh.update()
    for m in mats:
        mesh.materials.append(m)
    for p, mi in zip(mesh.polygons, g['materials']):
        p.material_index = mi
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges), 'Open concrete fragment'
    bm.to_mesh(mesh)
    bm.free()
    uv = mesh.uv_layers.new(name='WorldMetres')
    for loop in mesh.loops:
        p = mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (p.x / 4, p.y / 4)
    mesh.calc_loop_triangles()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    path = OUT / (name + '.fbx')
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'MESH'},
        axis_forward='-Y', axis_up='Z', global_scale=1, apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_NONE', bake_anim=False, use_mesh_modifiers=True)
    mins = [min(v.co[j] for v in mesh.vertices) for j in range(3)]
    maxs = [max(v.co[j] for v in mesh.vertices) for j in range(3)]
    entry = {'name': name, 'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
             'triangles': len(mesh.loop_triangles), 'pieces': len(g['pieces']),
             'dimensions_cm': [(b - a) * 100 for a, b in zip(mins, maxs)],
             'bounds_blender_m': [mins, maxs], 'material_slots': SLOTS, 'manifold': True}
    # Reimport our own output, validating both scale and closed fragment geometry.
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(path), use_anim=False)
    imported = [o for o in set(bpy.data.objects) - before if o.type == 'MESH']
    assert len(imported) == 1
    back = imported[0]
    pts = [back.matrix_world @ v.co for v in back.data.vertices]
    dims = [(max(p[j] for p in pts) - min(p[j] for p in pts)) * 100 for j in range(3)]
    assert max(abs(a - b) for a, b in zip(dims, entry['dimensions_cm'])) < .02
    back.data.calc_loop_triangles()
    assert len(back.data.loop_triangles) == entry['triangles']
    entry['fbx_roundtrip_passed'] = True
    bpy.data.objects.remove(back, do_unlink=True)
    assets.append(entry)

blend_path = OUT / 'ChamberParityDebris_20261007.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
manifest = {'owner': OWNER, 'generator': 'tools/make_chamber_parity_debris.py',
    'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'floor_source_sha256': source_hash, 'assets': assets, 'pieces': sum(a['pieces'] for a in assets),
    'triangles': sum(a['triangles'] for a in assets), 'units': 'metres; FBX -Y/+Z; Unreal mirrors Y',
    'placement': [0, 0, 0], 'collision': 'NoCollision',
    'contact': 'Every underside vertex samples the preserved recovery surface by raycast, with 2 mm embed.',
    'provenance': 'Original deterministic geometry; existing authored floor used only for grounding.'}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('PARITY_DEBRIS_COMPLETE', json.dumps({'pieces': manifest['pieces'], 'triangles': manifest['triangles']}))
