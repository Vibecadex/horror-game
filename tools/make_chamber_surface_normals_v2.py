"""Repair the frozen slab/connected-field winding without designing new shapes.

Run in Blender background, optionally with -- Slabs or -- Floor. Writes only
the two owned NormalsV2 directories. Original files and Unreal remain untouched.
Cap roles come from original polygon islands inside each welded solid, rather
than material names: the connected fields use Concrete on both top and bottom.
"""
import bpy
import bmesh
import collections
import copy
import hashlib
import json
import sys
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'Assets/Adapted/ChamberParity'
WELD_M = 1e-6
ROLE_NAMES = {0: 'edge', 1: 'top_cap', 2: 'underside', 3: 'open_crack'}
CONFIG = {
    'Slabs': {'owner': 'teddy-chamber-slabs-normals-v2-20261005',
              'manifest_sha': '054151f1c5c1ae61c2b342a1c1b2758862ec7274134f1152f5bad6f424bf4287',
              'closed': [16], 'placements': 4, 'blend': 'ChamberSparseSlabsNormalsV2.blend'},
    'Floor': {'owner': 'teddy-chamber-floor-normals-v2-20261005',
              'manifest_sha': '193563fd5ebbf91c83327d29be24539e914525c1237679143032e0c217288133',
              'closed': [187, 220, 147], 'placements': 5, 'blend': 'ChamberFloorNormalsV2_Kit.blend'},
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def groups(bm):
    seen, result = set(), []
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


def closed(group):
    return all(edge.is_manifold for face in group for edge in face.edges)


def volume(group):
    # Centre the calculation on the component to avoid cancellation in thin
    # metre-scale fields. A positive result denotes outward-oriented volume.
    origin = group[0].verts[0].co
    return sum((face.verts[0].co-origin).dot((face.verts[1].co-origin).cross(face.verts[2].co-origin))/6
               for face in group)


def weld(raw, orient=True):
    bm = raw.copy()
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=WELD_M)
    corrections = 0
    if orient:
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        for group in groups(bm):
            if closed(group) and volume(group) < 0:
                for face in group:
                    face.normal_flip()
                corrections += 1
    bm.normal_update()
    return bm, corrections


def identify_roles(raw, slots, family, expected_closed):
    polygon_layer = raw.faces.layers.int.new('OriginalPolygonId')
    role_layer = raw.faces.layers.int.new('OriginalSurfaceRole')
    for index, island in enumerate(groups(raw)):
        for face in island:
            face[polygon_layer] = index
    joined, _ = weld(raw)
    ids = joined.faces.layers.int['OriginalPolygonId']
    roles, piece_rows, solid_count = {}, [], 0
    for piece in groups(joined):
        if not closed(piece):
            assert all(slots[face.material_index] == 'Crack' for face in piece), 'Unexpected open solid surface'
            for face in piece:
                roles[face[ids]] = 3
            continue
        solid_count += 1
        minimum_z = min(vertex.co.z for face in piece for vertex in face.verts)
        polygons = collections.defaultdict(list)
        for face in piece:
            polygons[face[ids]].append(face)
        if family == 'Slabs':
            bottoms = [index for index, faces in polygons.items()
                       if all(slots[face.material_index] == 'Dark' for face in faces)]
        else:
            bottoms = [index for index, faces in polygons.items()
                       if all(abs(vertex.co.z-minimum_z) < 1e-8 for face in faces for vertex in face.verts)]
        assert len(bottoms) == 1, 'Each closed piece must have one original underside polygon'
        top = max((index for index in polygons if index not in bottoms),
                  key=lambda index: sum(abs(face.normal.z)*face.calc_area() for face in polygons[index]))
        assert len(polygons[top]) == len(polygons[bottoms[0]]), 'Top/bottom polygon topology mismatch'
        for index in polygons:
            roles[index] = 2 if index in bottoms else 1 if index == top else 0
        piece_rows.append({'top_polygon': top, 'underside_polygon': bottoms[0],
                           'cap_triangles': len(polygons[top]), 'minimum_z_m': minimum_z})
    assert solid_count == expected_closed
    joined.free()
    for face in raw.faces:
        face[role_layer] = roles[face[polygon_layer]]
    return piece_rows


def audit(bm, slots, expected_closed, expected_open):
    bm.normal_update()
    roles = bm.faces.layers.int['OriginalSurfaceRole']
    ids = bm.faces.layers.int['OriginalPolygonId']
    rows = {name: {'triangles': 0, 'positive_z': 0, 'negative_z': 0, 'zero_z': 0,
                   'incorrect_triangles': 0, 'incorrect_area_m2': 0.} for name in ROLE_NAMES.values()}
    bad_polygons = set()
    by_material = {slot: {'positive_z': 0, 'negative_z': 0, 'zero_z': 0} for slot in slots}
    for face in bm.faces:
        role = face[roles]
        row = rows[ROLE_NAMES[role]]
        row['triangles'] += 1
        sign = 'positive_z' if face.normal.z > 1e-8 else 'negative_z' if face.normal.z < -1e-8 else 'zero_z'
        row[sign] += 1
        by_material[slots[face.material_index]][sign] += 1
        if (role in (1, 3) and face.normal.z <= 0) or (role == 2 and face.normal.z >= 0):
            row['incorrect_triangles'] += 1
            row['incorrect_area_m2'] += face.calc_area()
            bad_polygons.add(face[ids])
    pieces = groups(bm)
    solid_pieces = [piece for piece in pieces if closed(piece)]
    open_pieces = [piece for piece in pieces if not closed(piece)]
    volumes = [volume(piece) for piece in solid_pieces]
    inconsistent_edges = sum(edge.is_manifold and not edge.is_contiguous for edge in bm.edges)
    degenerate = sum(face.calc_area() < 1e-12 for face in bm.faces)
    errors = sum(row['incorrect_triangles'] for row in rows.values())
    open_materials = collections.Counter(','.join(sorted({slots[face.material_index] for face in piece})) for piece in open_pieces)
    passed = (errors == 0 and len(solid_pieces) == expected_closed and len(open_pieces) == expected_open
              and all(value > 0 for value in volumes) and not degenerate and not inconsistent_edges
              and (not open_materials or set(open_materials) == {'Crack'}))
    return {'surface_roles': rows, 'by_material': by_material,
            'wrong_cap_or_underside_triangles': errors,
            'closed_solid_components': len(solid_pieces), 'expected_closed_solid_components': expected_closed,
            'negative_volume_components': sum(value <= 0 for value in volumes),
            'minimum_signed_volume_m3': min(volumes) if volumes else None,
            'open_components': len(open_pieces), 'open_component_materials': dict(open_materials),
            'inconsistent_manifold_edges': inconsistent_edges, 'degenerate_triangles': degenerate,
            'passed': passed}, bad_polygons


def boundary(group):
    members = set(group)
    edges = set(edge for face in group for edge in face.edges
                if sum(adjacent in members for adjacent in edge.link_faces) == 1)
    neighbours = collections.defaultdict(list)
    for edge in edges:
        a, b = edge.verts
        neighbours[a].append(b)
        neighbours[b].append(a)
    assert edges and all(len(adjacent) == 2 for adjacent in neighbours.values())
    first = min(neighbours, key=lambda vertex: vertex.index)
    ring, previous, current = [first], None, first
    while True:
        following = next(vertex for vertex in neighbours[current] if vertex != previous)
        if following == first:
            break
        assert following not in ring
        ring.append(following)
        previous, current = current, following
    assert len(ring) == len(neighbours)
    return ring


def crossings(points):
    result = []
    count = len(points)
    for i in range(count):
        a, b = points[i], points[(i+1) % count]
        rx, ry = b[0]-a[0], b[1]-a[1]
        for j in range(i+2, count):
            if (j+1) % count == i:
                continue
            c, d = points[j], points[(j+1) % count]
            sx, sy = d[0]-c[0], d[1]-c[1]
            denominator = rx*sy-ry*sx
            if abs(denominator) < 1e-14:
                continue
            t = ((c[0]-a[0])*sy-(c[1]-a[1])*sx)/denominator
            u = ((c[0]-a[0])*ry-(c[1]-a[1])*rx)/denominator
            if 1e-8 < t < 1-1e-8 and 1e-8 < u < 1-1e-8:
                result.append((i, j))
    return result


def uncross_proven_boundaries(raw, bad_polygons, piece_roles, slots):
    """Repair only demonstrated intersecting perimeter profiles, without motion.

    A two-edge uncross reverses the intervening boundary order. The three original
    height rings follow the same corrected order; all original points and cap
    counts remain, and the matching sides are rebuilt as a closed boundary.
    """
    if not bad_polygons:
        return []
    raw.verts.index_update()
    ids = raw.faces.layers.int['OriginalPolygonId']
    roles = raw.faces.layers.int['OriginalSurfaceRole']
    uv_layer = raw.loops.layers.uv.active
    joined, _ = weld(raw)
    joined_ids = joined.faces.layers.int['OriginalPolygonId']
    pieces = {face[joined_ids]: piece for piece in groups(joined) if closed(piece) for face in piece}
    records = []
    raw_by_coordinate = {}
    for vertex in raw.verts:
        raw_by_coordinate.setdefault(tuple(vertex.co), vertex)
    all_uvs = {tuple(loop.vert.co): tuple(loop[uv_layer].uv) for face in raw.faces for loop in face.loops}
    for record in piece_roles:
        top_id, bottom_id = record['top_polygon'], record['underside_polygon']
        if not ({top_id, bottom_id} & bad_polygons):
            continue
        top_faces = [face for face in raw.faces if face[ids] == top_id]
        bottom_faces = [face for face in raw.faces if face[ids] == bottom_id]
        top_ring, bottom_ring = boundary(top_faces), boundary(bottom_faces)
        before_top = crossings([vertex.co for vertex in top_ring])
        before_bottom = crossings([vertex.co for vertex in bottom_ring])
        if not before_top and not before_bottom:
            continue
        piece = pieces[top_id]
        piece_ids = {face[joined_ids] for face in piece}
        edges_ids = sorted(piece_ids-{top_id, bottom_id})
        count = len(bottom_ring)
        assert len(top_ring) == count and len(edges_ids) == count*2
        assert record['minimum_z_m'] < .00011, 'Boundary repair must remain on demonstrated perimeter plates'
        edge_materials = {face.material_index for face in raw.faces if face[ids] in set(edges_ids)}
        assert len(edge_materials) == 1 and slots[next(iter(edge_materials))] == 'Concrete'
        # Source bevel inset is radial and <4.5mm; the nearest cap vertex is
        # its corresponding profile point. Verify bijection before any change.
        matched_top = [min(top_ring, key=lambda vertex: (vertex.co.x-low.co.x)**2+(vertex.co.y-low.co.y)**2)
                       for low in bottom_ring]
        assert len(set(matched_top)) == count
        piece_coordinates = {tuple(vertex.co) for face in piece for vertex in face.verts}
        outer_ring = []
        for low in bottom_ring:
            candidates = [point for point in piece_coordinates if point[0] == low.co.x and point[1] == low.co.y
                          and point[2] > low.co.z+1e-8]
            assert len(candidates) == 1
            outer_ring.append(raw_by_coordinate[candidates[0]])
        rings = [matched_top, outer_ring, bottom_ring]
        order = list(range(count))
        uncrosses = []
        for _ in range(count*4):
            found = next(((ring_index, cross[0]) for ring_index, ring in enumerate(rings)
                          if (cross := crossings([ring[index].co for index in order]))), None)
            if found is None:
                break
            ring_index, (i, j) = found
            old_order = order[:]
            order[i+1:j+1] = reversed(order[i+1:j+1])
            uncrosses.append({'ring': ring_index, 'crossed_edges': [i, j],
                              'reversed_original_indices': old_order[i+1:j+1]})
        assert all(not crossings([ring[index].co for index in order]) for ring in rings), 'Uncrossing did not converge'
        rings = [[ring[index] for index in order] for ring in rings]
        top_material, bottom_material = top_faces[0].material_index, bottom_faces[0].material_index
        edge_material = next(iter(edge_materials))
        old_triangles = sum(face[ids] in piece_ids for face in raw.faces)
        for face in list(raw.faces):
            if face[ids] in piece_ids:
                raw.faces.remove(face)

        def add_polygon(vertices, material, polygon_id, role, project_xy=False):
            vectors = [Vector((vertex.co.x, vertex.co.y, 0)) if project_xy else vertex.co.copy() for vertex in vertices]
            lookup = {tuple(point): index for index, point in enumerate(vectors)}
            for triangle in tessellate_polygon([vectors]):
                indices = [index if isinstance(index, int) else lookup[tuple(index)] for index in triangle]
                face = raw.faces.new(tuple(vertices[index] for index in indices))
                face.material_index, face[ids], face[roles] = material, polygon_id, role
                for loop in face.loops:
                    loop[uv_layer].uv = all_uvs[tuple(loop.vert.co)]

        top, outside, low = rings
        add_polygon(top, top_material, top_id, 1, True)
        add_polygon(list(reversed(low)), bottom_material, bottom_id, 2, True)
        for i in range(count):
            j = (i+1) % count
            add_polygon([top[i], outside[i], outside[j], top[j]], edge_material, edges_ids[i*2], 0)
            add_polygon([outside[i], low[i], low[j], outside[j]], edge_material, edges_ids[i*2+1], 0)
        new_triangles = sum(face[ids] in piece_ids for face in raw.faces)
        assert new_triangles == old_triangles
        records.append({'top_polygon': top_id, 'underside_polygon': bottom_id,
            'top_boundary_crossings_before': len(before_top), 'underside_boundary_crossings_before': len(before_bottom),
            'boundary_crossings_after': 0, 'uncross_operations': uncrosses, 'profile_vertex_count': count,
            'triangle_delta': new_triangles-old_triangles, 'unique_vertex_delta': 0, 'maximum_vertex_motion_cm': 0.,
            'topology_only_repair': True})
    joined.free()
    return records


def retessellate(raw, polygon_ids):
    if not polygon_ids:
        return []
    raw.verts.index_update()
    ids = raw.faces.layers.int['OriginalPolygonId']
    roles = raw.faces.layers.int['OriginalSurfaceRole']
    records = []
    original_groups = groups(raw)
    for group in original_groups:
        polygon_id = group[0][ids]
        if polygon_id not in polygon_ids:
            continue
        role = group[0][roles]
        assert role in (1, 2), 'Only actual cap surfaces may need XY retriangulation'
        material = group[0].material_index
        ring = boundary(group)
        projected = [Vector((vertex.co.x, vertex.co.y, 0)) for vertex in ring]
        lookup = {tuple(point): index for index, point in enumerate(projected)}
        triangles = tessellate_polygon([projected])
        assert len(triangles) == len(group), 'Triangle count changed'
        # Capture original face-corner UVs before replacing only face diagonals.
        uv_layer = raw.loops.layers.uv.active
        uv_by_vertex = {loop.vert: tuple(loop[uv_layer].uv) for face in group for loop in face.loops}
        for face in group:
            raw.faces.remove(face)
        for triangle in triangles:
            indices = [index if isinstance(index, int) else lookup[tuple(index)] for index in triangle]
            face = raw.faces.new(tuple(ring[index] for index in indices))
            face.material_index = material
            face[ids] = polygon_id
            face[roles] = role
            for loop in face.loops:
                loop[uv_layer].uv = uv_by_vertex[loop.vert]
        records.append({'polygon_id': polygon_id, 'surface_role': ROLE_NAMES[role],
                        'triangles': len(triangles), 'boundary_vertices': len(ring)})
    raw.normal_update()
    return records


def uv_by_position(mesh):
    result = collections.defaultdict(set)
    uv = mesh.uv_layers.active
    for loop in mesh.loops:
        result[tuple(mesh.vertices[loop.vertex_index].co)].add(tuple(uv.data[loop.index].uv))
    return dict(result)


def roundtrip_roles(imported, source):
    """Map imported triangle coordinates to audited source roles; no normal fixes."""
    source.verts.index_update()
    tree = KDTree(len(source.verts))
    for vertex in source.verts:
        tree.insert(vertex.co, vertex.index)
    tree.balance()
    ids = source.faces.layers.int['OriginalPolygonId']
    roles = source.faces.layers.int['OriginalSurfaceRole']
    face_lookup = {(face.material_index, tuple(sorted(vertex.index for vertex in face.verts))): (face[ids], face[roles])
                   for face in source.faces}
    bm = bmesh.new()
    bm.from_mesh(imported.data)
    bmesh.ops.transform(bm, matrix=imported.matrix_world, verts=list(bm.verts))
    mapping, maximum_error = {}, 0.
    for vertex in bm.verts:
        _, index, error = tree.find(vertex.co)
        assert error < .000004, 'FBX vertex coordinate drift'
        mapping[vertex] = index
        maximum_error = max(maximum_error, error)
    new_ids = bm.faces.layers.int.new('OriginalPolygonId')
    new_roles = bm.faces.layers.int.new('OriginalSurfaceRole')
    for face in bm.faces:
        key = (face.material_index, tuple(sorted(mapping[vertex] for vertex in face.verts)))
        polygon_id, role = face_lookup[key]
        face[new_ids], face[new_roles] = polygon_id, role
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=WELD_M)
    bm.normal_update()
    return bm, maximum_error


def run_family(family):
    config = CONFIG[family]
    source_folder, out = BASE/family, BASE/(family+'NormalsV2')
    assert sha(source_folder/'manifest.json') == config['manifest_sha']
    document = json.loads((source_folder/'manifest.json').read_text(encoding='utf-8'))
    source_hashes = {str(path.relative_to(ROOT)).replace('\\', '/'): sha(path)
                     for path in source_folder.iterdir() if path.is_file()}
    assert sha(ROOT/document['editable_blend']) == document['blend_sha256']
    for entry in document['assets']:
        assert sha(source_folder/entry['file']) == entry['sha256']
    if out.exists() and any(out.iterdir()):
        marker = out/'manifest.json'
        assert marker.exists() and json.loads(marker.read_text(encoding='utf-8')).get('owner') == config['owner']
    out.mkdir(parents=True, exist_ok=True)
    (out/'manifest.json').write_text(json.dumps({'owner': config['owner'], 'status': 'authoring'}), encoding='utf-8')
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/document['editable_blend']))
    slots = document['material_slots']
    assets, audits, checks = [], [], []
    for original, expected_closed in zip(document['assets'], config['closed']):
        obj = bpy.data.objects[original['name']]
        mesh = obj.data
        positions_before = {tuple(vertex.co) for vertex in mesh.vertices}
        uv_before = uv_by_position(mesh)
        raw = bmesh.new()
        raw.from_mesh(mesh)
        piece_roles = identify_roles(raw, slots, family, expected_closed)
        joined, initially_reversed = weld(raw)
        expected_open = sum(not closed(piece) for piece in groups(joined))
        before, _ = audit(raw, slots, expected_closed, expected_open)
        weld_audit, bad_polygons = audit(joined, slots, expected_closed, expected_open)
        joined.free()
        boundary_repairs = uncross_proven_boundaries(raw, bad_polygons, piece_roles, slots) if family == 'Floor' else []
        if boundary_repairs:
            rechecked, _ = weld(raw)
            _, bad_polygons = audit(rechecked, slots, expected_closed, expected_open)
            rechecked.free()
        changed_polygons = retessellate(raw, bad_polygons)
        repaired, reversed_volumes = weld(raw)
        raw.free()
        role_layer = repaired.faces.layers.int['OriginalSurfaceRole']
        for face in repaired.faces:
            if face[role_layer] == 3 and face.normal.z < 0:
                face.normal_flip()
        after, _ = audit(repaired, slots, expected_closed, expected_open)
        assert after['passed'], json.dumps({'mesh': original['name'], 'audit': after})
        repaired.to_mesh(mesh)
        mesh.update()
        mesh.calc_loop_triangles()
        assert {tuple(vertex.co) for vertex in mesh.vertices} == positions_before
        assert uv_by_position(mesh) == uv_before
        assert len(mesh.loop_triangles) == original['triangles']
        assert len(mesh.uv_layers) == 1 and [material.name for material in mesh.materials] == slots
        obj.name = original['name']+'_V2'
        mesh.name = obj.name+'_Geometry'
        obj['owner'] = config['owner']
        studio_location = obj.location.copy()
        obj.location = (0, 0, 0)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        fbx = out/(obj.name+'.fbx')
        bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'MESH'}, axis_forward='-Y', axis_up='Z',
            global_scale=1, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_mesh_modifiers=True,
            mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False, path_mode='AUTO')
        obj.location = studio_location
        entry = copy.deepcopy(original)
        entry.update({'name': obj.name, 'file': fbx.name, 'sha256': sha(fbx), 'vertices': len(mesh.vertices),
                      'original_mesh': original['name'], 'original_vertex_count': original['vertices'],
                      'closed_solid_components': expected_closed})
        assets.append(entry)
        previous = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=str(fbx), use_anim=False)
        loaded = [item for item in set(bpy.data.objects)-previous if item.type == 'MESH']
        assert len(loaded) == 1
        imported = loaded[0]
        imported.data.calc_loop_triangles()
        points = [imported.matrix_world@vertex.co for vertex in imported.data.vertices]
        dimensions = [max(point[i] for point in points)-min(point[i] for point in points) for i in range(3)]
        dimension_error = max(abs(a-b) for a, b in zip(dimensions, original['dimensions_m']))
        imported_slots = [slot.material.name.split('.')[0] for slot in imported.material_slots]
        assert dimension_error < .000025 and imported_slots == slots
        assert len(imported.data.loop_triangles) == original['triangles'] and len(imported.data.uv_layers) == 1
        imported_bm, vertex_error = roundtrip_roles(imported, repaired)
        imported_audit, _ = audit(imported_bm, slots, expected_closed, expected_open)
        assert imported_audit['passed'], json.dumps(imported_audit)
        imported_bm.free()
        repaired.free()
        bpy.data.objects.remove(imported, do_unlink=True)
        check = {'name': obj.name, 'actual_dimensions_cm': [value*100 for value in dimensions],
                 'max_dimension_error_m': dimension_error, 'max_vertex_position_error_m': vertex_error,
                 'triangles': original['triangles'], 'material_slots': slots,
                 'normal_signs_passed': True, 'closed_solid_components': expected_closed, 'passed': True,
                 'fbx_sha256': entry['sha256']}
        checks.append(check)
        audits.append({'name': obj.name, 'role_identification': piece_roles, 'before': before,
            'after_weld_before_retessellation': weld_audit, 'source_after': after, 'fbx_roundtrip': imported_audit,
            'retessellated_original_polygons': changed_polygons,
            'local_boundary_topology_repairs': boundary_repairs,
            'negative_volume_components_corrected_initially': initially_reversed,
            'negative_volume_components_corrected_finally': reversed_volumes,
            'all_vertex_positions_preserved': True, 'all_uv_coordinates_preserved': True,
            'triangle_count_preserved': True, 'material_assignments_preserved': True})
        print('SURFACE_NORMALS_REPAIRED', obj.name, json.dumps({'before_roles': before['surface_roles'],
            'after_wrong': after['wrong_cap_or_underside_triangles'], 'closed': expected_closed,
            'retessellated_polygons': len(changed_polygons), 'fbx': check}), flush=True)
    placements = copy.deepcopy(document['recommended_placements'])
    assert len(placements) == config['placements']
    for placement in placements:
        placement['mesh'] += '_V2'
    scene = bpy.context.scene
    for material in bpy.data.materials:
        material.use_backface_culling = True
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y = 1500, 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    preview = family.lower()+'-normals-v2-overview.png'
    scene.render.filepath = str(out/preview)
    blend = out/config['blend']
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.render.render(write_still=True)
    for relative, expected in source_hashes.items():
        assert sha(ROOT/relative) == expected, 'Frozen input changed: '+relative
    result = copy.deepcopy(document)
    result.update({'owner': config['owner'], 'status': 'source-ready-for-engine-review',
        'generator': 'tools/make_chamber_surface_normals_v2.py', 'generator_sha256': sha(Path(__file__)),
        'editable_blend': str(blend.relative_to(ROOT)).replace('\\', '/'), 'blend_sha256': sha(blend),
        'source': 'Bounded winding repair of the frozen '+family+' kit; no new shape or placement design.',
        'correction': 'Weld coincident surface vertices at 1e-6m and orient closed volumes outward. Identify actual top and '
                      'underside polygons from each original surface island inside the closed piece; material names alone '
                      'are not used for Floor caps. Uncross only proven self-intersecting perimeter-piece boundaries '
                      'by reconnecting their existing vertices, then rebuild matching sides. No vertex motion, bounds '
                      'or triangle-count change. Retriangulate only invalid cap boundaries. '
                      'Explicit upward open Crack ribbons. FBX face winding is audited without recalculation.',
        'assets': assets, 'recommended_placements': placements, 'fbx_roundtrip_checks': checks,
        'normal_audits': audits, 'normal_audits_passed': True,
        'source_preservation': {'original_manifest_sha256': config['manifest_sha'], 'files_unchanged': source_hashes, 'passed': True},
        'renders': [preview], 'render_note': 'Neutral source construction proof with backface culling enabled. Native Unreal review is separate.'})
    (out/'manifest.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print('SURFACE_NORMALS_READY', family, sha(out/'manifest.json'), flush=True)


requested = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['Slabs', 'Floor']
assert requested and all(family in CONFIG for family in requested)
for family in requested:
    run_family(family)
