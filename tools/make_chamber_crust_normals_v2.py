"""Repair frozen crust winding in separate, strictly owned source exports.

Preserve all vertex positions, UV coordinates, six slots, triangle counts and
five placements. Re-tessellate only cap polygons folded by the old XY warp,
then weld coincident surface vertices and orient the 39 closed pieces outward.
Never opens Unreal or modifies the original kit.
"""
import bpy
import bmesh
import collections
import copy
import hashlib
import json
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Assets/Adapted/ChamberParity/Crust'
OUT = ROOT / 'Assets/Adapted/ChamberParity/CrustNormalsV2'
OWNER = 'teddy-chamber-crust-normals-v2-20261005'
EXPECTED_MANIFEST = '89e2c3b844876594cbff18be22428d6c75df60ff49490404b2df5daa08d643f3'
SLOTS = ['Concrete', 'ConcreteLight', 'ConcreteDark', 'Aggregate', 'Dark', 'Crack']
TOPS = set(SLOTS[:3])
WELD_M = 0.000001


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point_key(point):
    return tuple(float(v) for v in point)


def face_key(face):
    return tuple(sorted(point_key(v.co) for v in face.verts))


def components(bm):
    seen = set()
    result = []
    for face in bm.faces:
        if face in seen:
            continue
        group, stack = [], [face]
        seen.add(face)
        while stack:
            current = stack.pop()
            group.append(current)
            for edge in current.edges:
                for adjacent in edge.link_faces:
                    if adjacent not in seen:
                        seen.add(adjacent)
                        stack.append(adjacent)
        result.append(group)
    return result


def audit(bm, transform=None):
    bm.normal_update()
    normal_matrix = transform.to_3x3().inverted().transposed() if transform else None
    rows = {name: {'positive_z': 0, 'negative_z': 0, 'zero_z': 0,
                   'positive_area_m2': 0., 'negative_area_m2': 0.} for name in SLOTS}
    bad = []
    for face in bm.faces:
        name = SLOTS[face.material_index]
        normal = (normal_matrix @ face.normal).normalized() if normal_matrix else face.normal
        key = 'positive_z' if normal.z > 1e-8 else 'negative_z' if normal.z < -1e-8 else 'zero_z'
        rows[name][key] += 1
        if normal.z > 0:
            rows[name]['positive_area_m2'] += face.calc_area()
        elif normal.z < 0:
            rows[name]['negative_area_m2'] += face.calc_area()
        if ((name in TOPS or name == 'Crack') and normal.z <= 0) or (name == 'Dark' and normal.z >= 0):
            bad.append(face_key(face))
    groups = components(bm)
    closed = [group for group in groups if all(edge.is_manifold for face in group for edge in face.edges)]
    opened = [group for group in groups if group not in closed]
    closed_rows = []
    for group in closed:
        volume = sum(face.verts[0].co.dot(face.verts[1].co.cross(face.verts[2].co)) / 6 for face in group)
        closed_rows.append({'triangles': len(group), 'signed_volume_m3': volume,
                            'materials': sorted({SLOTS[face.material_index] for face in group})})
    open_materials = collections.Counter(','.join(sorted({SLOTS[f.material_index] for f in group})) for group in opened)
    degenerate = sum(face.calc_area() < 1e-12 for face in bm.faces)
    return {
        'by_material': rows,
        'wrong_cap_or_underside_triangles': len(bad),
        'closed_solid_components': len(closed),
        'expected_closed_solid_components': 39,
        'closed_components': sorted(closed_rows, key=lambda row: (row['triangles'], row['signed_volume_m3'])),
        'open_components': len(opened),
        'open_component_materials': dict(open_materials),
        'degenerate_triangles': degenerate,
        'passed': len(bad) == 0 and len(closed) == 39 and all(row['signed_volume_m3'] > 0 for row in closed_rows)
                  and set(open_materials) == {'Crack'} and degenerate == 0,
    }, set(bad)


def welded_copy(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=WELD_M)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.normal_update()
    # Open joint ribbons do not define a volume; their visible face is explicit.
    for face in bm.faces:
        if SLOTS[face.material_index] == 'Crack' and face.normal.z < 0:
            face.normal_flip()
    bm.normal_update()
    return bm


def polygon_boundary(group):
    members = set(group)
    edges = [edge for face in group for edge in face.edges
             if sum(adjacent in members for adjacent in edge.link_faces) == 1]
    edges = list(set(edges))
    links = collections.defaultdict(list)
    for edge in edges:
        a, b = edge.verts
        links[a].append(b)
        links[b].append(a)
    assert edges and all(len(neighbours) == 2 for neighbours in links.values()), 'Non-simple original surface boundary'
    first = min(links, key=lambda vertex: vertex.index)
    ring, previous, current = [first], None, first
    while True:
        following = next(vertex for vertex in links[current] if vertex != previous)
        if following == first:
            break
        assert following not in ring, 'Self-connected boundary'
        ring.append(following)
        previous, current = current, following
    assert len(ring) == len(links)
    return ring


def repair_folded_caps(mesh, bad_keys):
    """Change diagonals inside original disconnected polygon islands only."""
    if not bad_keys:
        return {'retessellated_original_polygons': 0, 'retessellated_triangles': 0}
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    replacement_faces, material_indices, changed = [], [], []
    for group in components(bm):
        material = group[0].material_index
        assert all(face.material_index == material for face in group)
        if not any(face_key(face) in bad_keys for face in group):
            for face in group:
                replacement_faces.append(tuple(vertex.index for vertex in face.verts))
                material_indices.append(material)
            continue
        assert SLOTS[material] in TOPS | {'Dark'}, 'Unexpected folded non-cap surface'
        ring = polygon_boundary(group)
        # XY projection explicitly preserves the intended horizontal upper/lower
        # surface under the old nonlinear XY warp. Every original 3D vertex stays.
        projected = [Vector((vertex.co.x, vertex.co.y, 0.)) for vertex in ring]
        lookup = {tuple(vector): index for index, vector in enumerate(projected)}
        triangles = tessellate_polygon([projected])
        assert len(triangles) == len(group), 'Retessellation changed triangle budget'
        for triangle in triangles:
            indices = [index if isinstance(index, int) else lookup[tuple(index)] for index in triangle]
            replacement_faces.append(tuple(ring[index].index for index in indices))
            material_indices.append(material)
        changed.append({'material': SLOTS[material], 'triangles': len(triangles), 'boundary_vertices': len(ring)})
    vertices = [tuple(vertex.co) for vertex in bm.verts]
    bm.free()
    old_slots = list(mesh.materials)
    mesh.clear_geometry()
    mesh.from_pydata(vertices, [], replacement_faces)
    mesh.update()
    assert list(mesh.materials) == old_slots
    for face, material in zip(mesh.polygons, material_indices):
        face.material_index = material
    # The frozen UV contract is XY/4m; after the unchanged coordinates are restored
    # it is byte-equivalent float data at each face corner, irrespective of winding.
    uv = mesh.uv_layers.get('FloorMetres_4m') or mesh.uv_layers.new(name='FloorMetres_4m')
    for loop in mesh.loops:
        point = mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (point.x / 4, point.y / 4)
    return {'retessellated_original_polygons': len(changed),
            'retessellated_triangles': sum(row['triangles'] for row in changed), 'polygons': changed}


def uv_by_position(mesh):
    uv = mesh.uv_layers.active
    result = collections.defaultdict(set)
    for loop in mesh.loops:
        result[point_key(mesh.vertices[loop.vertex_index].co)].add(tuple(uv.data[loop.index].uv))
    return dict(result)


assert sha(SOURCE / 'manifest.json') == EXPECTED_MANIFEST, 'Frozen source manifest changed'
source_doc = json.loads((SOURCE / 'manifest.json').read_text(encoding='utf-8'))
assert source_doc['owner'] == 'teddy-chamber-crust-20261005'
source_hashes = {str(path.relative_to(ROOT)).replace('\\', '/'): sha(path) for path in SOURCE.iterdir() if path.is_file()}
assert sha(ROOT / source_doc['editable_blend']) == source_doc['blend_sha256']
for entry in source_doc['assets']:
    assert sha(SOURCE / entry['file']) == entry['sha256']
if OUT.exists() and any(OUT.iterdir()):
    marker = OUT / 'manifest.json'
    assert marker.exists() and json.loads(marker.read_text(encoding='utf-8')).get('owner') == OWNER, 'Unowned output directory'
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'manifest.json').write_text(json.dumps({'owner': OWNER, 'status': 'authoring'}), encoding='utf-8')
bpy.ops.wm.open_mainfile(filepath=str(ROOT / source_doc['editable_blend']))
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
assets, audits, objects = [], [], []

for original in source_doc['assets']:
    obj = bpy.data.objects[original['name']]
    mesh = obj.data
    positions_before = {point_key(vertex.co) for vertex in mesh.vertices}
    uv_before = uv_by_position(mesh)
    raw = bmesh.new()
    raw.from_mesh(mesh)
    before_audit, _ = audit(raw)
    raw.free()
    welded = welded_copy(mesh)
    welded_audit, bad_keys = audit(welded)
    welded.free()
    retessellation = repair_folded_caps(mesh, bad_keys)
    repaired = welded_copy(mesh)
    # The reflected/warped B boundary contains two minute upper-bevel returns.
    # Their outward faces truly point downward; retain the closed winding and
    # classify that exposed edge as Aggregate instead of pretending it is a cap.
    edge_returns = []
    for face in repaired.faces:
        if SLOTS[face.material_index] in TOPS and face.normal.z < 0:
            assert original['name'].endswith('_B') and face.calc_area() < .001
            edge_returns.append({'previous_material': SLOTS[face.material_index],
                                 'area_m2': face.calc_area(), 'normal_z': face.normal.z,
                                 'coordinates_m': [list(vertex.co) for vertex in face.verts]})
            face.material_index = SLOTS.index('Aggregate')
    assert len(edge_returns) in (0, 4)
    after_audit, _ = audit(repaired)
    assert after_audit['passed'], json.dumps(after_audit)
    repaired.to_mesh(mesh)
    repaired.free()
    mesh.update()
    mesh.calc_loop_triangles()
    assert {point_key(vertex.co) for vertex in mesh.vertices} == positions_before, 'Vertex coordinate drift'
    assert uv_by_position(mesh) == uv_before, 'UV coordinate drift'
    assert len(mesh.loop_triangles) == original['triangles']
    assert [material.name for material in mesh.materials] == SLOTS
    assert len(mesh.uv_layers) == 1
    obj.name = original['name'] + '_V2'
    mesh.name = obj.name + '_Geometry'
    obj['owner'] = OWNER
    studio_location = obj.location.copy()
    obj.location = (0, 0, 0)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    path = OUT / (obj.name + '.fbx')
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'MESH'}, axis_forward='-Y', axis_up='Z',
        global_scale=1, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_mesh_modifiers=True,
        mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False, path_mode='AUTO')
    obj.location = studio_location
    entry = copy.deepcopy(original)
    entry.update({'name': obj.name, 'file': path.name, 'sha256': sha(path), 'vertices': len(mesh.vertices),
                  'original_mesh': original['name'], 'original_vertex_count': original['vertices']})
    assets.append(entry)
    objects.append(obj)
    audits.append({'name': obj.name, 'before': before_audit, 'after_weld_before_retessellation': welded_audit,
                   'retessellation': retessellation, 'source_after': after_audit,
                   'exposed_bevel_returns_classified_aggregate': edge_returns,
                   'all_vertex_positions_preserved': True, 'all_uv_coordinates_preserved': True,
                   'triangle_count_preserved': True})
    print('CRUST_NORMALS_SOURCE', obj.name, json.dumps({'incorrect_before': before_audit['wrong_cap_or_underside_triangles'],
        'incorrect_after': after_audit['wrong_cap_or_underside_triangles'], 'closed_solids': after_audit['closed_solid_components'],
        'vertices': len(mesh.vertices), 'triangles': entry['triangles'], 'retessellation': retessellation}), flush=True)

checks = []
for entry, normal_receipt in zip(assets, audits):
    previous = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(OUT / entry['file']), use_anim=False)
    loaded = [obj for obj in set(bpy.data.objects) - previous if obj.type == 'MESH']
    assert len(loaded) == 1
    obj = loaded[0]
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    dimensions = [max(point[i] for point in points) - min(point[i] for point in points) for i in range(3)]
    error = max(abs(a - b) for a, b in zip(dimensions, entry['dimensions_m']))
    obj.data.calc_loop_triangles()
    names = [slot.material.name.split('.')[0] for slot in obj.material_slots]
    assert error < .000025 and names == SLOTS and len(obj.data.loop_triangles) == entry['triangles'] and len(obj.data.uv_layers) == 1
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    # FBX may split vertices at UV/normal boundaries. Rejoin exact positions only
    # for topology inspection; do NOT recalculate or flip the imported normals.
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=WELD_M)
    roundtrip_audit, _ = audit(bm, obj.matrix_world)
    assert roundtrip_audit['passed'], json.dumps(roundtrip_audit)
    bm.free()
    normal_receipt['fbx_roundtrip'] = roundtrip_audit
    checks.append({'name': entry['name'], 'max_dimension_error_m': error,
        'actual_dimensions_cm': [100 * value for value in dimensions], 'triangles': entry['triangles'],
        'material_slots': names, 'normal_signs_passed': True, 'closed_solid_components': 39, 'passed': True})
    bpy.data.objects.remove(obj, do_unlink=True)
    print('CRUST_NORMALS_FBX', entry['name'], json.dumps(checks[-1]), flush=True)

placements = copy.deepcopy(source_doc['recommended_placements'])
for placement in placements:
    placement['mesh'] += '_V2'

# Construction proof renders deliberately cull back-facing surfaces, matching
# the one-sided runtime requirement instead of concealing invalid winding.
for material in bpy.data.materials:
    material.use_backface_culling = True
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1500
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(OUT / 'crust-normals-v2-overview.png')
blend = OUT / 'ChamberCrustNormalsV2_Kit.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.render.render(write_still=True)

for relative, expected in source_hashes.items():
    assert sha(ROOT / relative) == expected, 'Original source changed during correction: ' + relative
manifest = copy.deepcopy(source_doc)
manifest.update({
    'owner': OWNER, 'status': 'source-ready-for-engine-review',
    'generator': 'tools/make_chamber_crust_normals_v2.py', 'generator_sha256': sha(Path(__file__)),
    'editable_blend': str(blend.relative_to(ROOT)).replace('\\', '/'), 'blend_sha256': sha(blend),
    'source': 'Separate winding repair of the frozen original Crust kit. No new shapes or placements.',
    'correction': 'Weld coincident polygon islands at 1e-6 metres, retessellate warped cap boundaries where required, '
                  'orient the 39 closed solid pieces outward, explicitly orient open Crack ribbons upward. '
                  'Four minute, truly downward-facing B bevel return triangles are classified as Aggregate. '
                  'Original coordinates, UVs, six material slots and triangle counts are preserved.',
    'source_preservation': {'original_manifest_sha256': EXPECTED_MANIFEST, 'files_unchanged': source_hashes, 'passed': True},
    'assets': assets, 'fbx_roundtrip_checks': checks, 'recommended_placements': placements,
    'normal_audits': audits, 'normal_audits_passed': all(row['source_after']['passed'] and row['fbx_roundtrip']['passed'] for row in audits),
    'renders': ['crust-normals-v2-overview.png'],
    'render_note': 'Neutral construction evidence with material backface culling enabled; final Unreal camera proof is separate.',
})
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print('CRUST_NORMALS_V2_COMPLETE', json.dumps({'meshes': 2, 'placements': 5, 'triangles': manifest['total_unique_triangles'],
    'normal_audits_passed': manifest['normal_audits_passed'], 'manifest_sha256': sha(OUT / 'manifest.json')}), flush=True)
