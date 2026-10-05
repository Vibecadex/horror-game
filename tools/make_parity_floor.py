"""Create six original, shallow concrete-damage meshes in installed Blender.

Run: blender --background --disable-autoexec --python-exit-code 1 --python tools/make_parity_floor.py
Only Assets/Adapted/Parity/Floor is written. This does not launch Unreal.
Source coordinates are metres, +Z up; local Z=0 is the existing floor surface.
"""
import bpy
import hashlib
import json
import math
import random
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Assets" / "Adapted" / "Parity" / "Floor"
OWNER = "teddy-parity-floor-20261005"
if OUT.exists() and any(OUT.iterdir()):
    marker = OUT / "manifest.json"
    if not marker.exists() or json.loads(marker.read_text(encoding="utf-8")).get("owner") != OWNER:
        raise RuntimeError("Refusing to overwrite an unowned parity floor directory")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "manifest.json").write_text(json.dumps({"owner": OWNER, "status": "authoring"}), encoding="utf-8")
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
MATERIAL_NAMES = ["Concrete", "Aggregate", "Dark"]
MATERIALS = {}
for name, lo, hi in [
    ("Concrete", (.115, .139, .137, 1), (.23, .25, .236, 1)),
    ("Aggregate", (.14, .153, .142, 1), (.26, .275, .248, 1)),
    ("Dark", (.009, .014, .013, 1), (.021, .026, .023, 1)),
]:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = hi
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = .93
    shader.inputs["Specular IOR Level"].default_value = .2
    tex = nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 45
    tex.inputs["Detail"].default_value = 3
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = lo
    ramp.color_ramp.elements[1].color = hi
    links.new(tex.outputs["Fac"], ramp.inputs[0])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .22
    bump.inputs["Distance"].default_value = .009 if name != "Dark" else .002
    links.new(tex.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    MATERIALS[name] = mat


class Geometry:
    def __init__(self):
        self.vertices, self.faces, self.mats = [], [], []
        self.pieces = 0

    def face(self, verts, mat):
        start = len(self.vertices)
        self.vertices.extend(verts)
        for i in range(1, len(verts) - 1):
            self.faces.append((start, start + i, start + i + 1))
            self.mats.append(MATERIAL_NAMES.index(mat))

    def plate(self, points, height, edge, rng, tilt=(0, 0), bottom=.0008):
        """Closed irregular chipped prism, top bevel, and non-flat top facets."""
        if len(points) < 3:
            return
        cx = sum(x for x, y in points) / len(points)
        cy = sum(y for x, y in points) / len(points)
        n = len(points)
        outer, inner, base = [], [], []
        for x, y in points:
            r = math.hypot(x - cx, y - cy)
            shrink = min(.12, edge / max(r, .005))
            ix, iy = cx + (x - cx) * (1 - shrink), cy + (y - cy) * (1 - shrink)
            z = max(bottom + .0003, height + (x - cx) * tilt[0] + (y - cy) * tilt[1])
            outer.append((x, y, max(bottom + .0002, z - edge * .7)))
            inner.append((ix, iy, z))
            base.append((x, y, bottom))
        center = (cx, cy, max(bottom + .0005, height + rng.uniform(-.07, .06) * height))
        for i in range(n):
            j = (i + 1) % n
            self.face([center, inner[i], inner[j]], "Concrete")
            self.face([inner[i], outer[i], outer[j], inner[j]], "Aggregate")
            self.face([outer[i], base[i], base[j], outer[j]], "Aggregate")
        self.face(list(reversed(base)), "Dark")
        self.pieces += 1

    def ribbon(self, points, widths, height=.0016):
        for i in range(len(points) - 1):
            a, b = Vector(points[i]), Vector(points[i + 1])
            tangent = b - a
            if tangent.length < .0001:
                continue
            norm = Vector((-tangent.y, tangent.x)).normalized()
            wa, wb = widths[i] / 2, widths[i + 1] / 2
            corners = [a - norm * wa, b - norm * wb, b + norm * wb, a + norm * wa]
            self.face([(p.x, p.y, height) for p in corners], "Dark")


ASSETS, OBJECTS = [], []


def emit(name, geo, purpose, max_height, placement):
    mesh = bpy.data.meshes.new(name + "_Geometry")
    mesh.from_pydata(geo.vertices, [], geo.faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    for material in MATERIALS.values():
        mesh.materials.append(material)
    for polygon, mat in zip(mesh.polygons, geo.mats):
        polygon.material_index = mat
    uv = mesh.uv_layers.new(name="FloorMetres_4m")
    for loop in mesh.loops:
        p = mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (p.x / 4, p.y / 4)
    mesh.calc_loop_triangles()
    xyz = [obj.matrix_world @ v.co for v in mesh.vertices]
    minimum = [min(p[i] for p in xyz) for i in range(3)]
    maximum = [max(p[i] for p in xyz) for i in range(3)]
    assert minimum[2] >= 0 and maximum[2] <= max_height, (name, minimum, maximum)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=str(OUT / (name + ".fbx")), use_selection=True, object_types={"MESH"},
        axis_forward="-Y", axis_up="Z", global_scale=1, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_NONE", use_mesh_modifiers=True,
        mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False, path_mode="AUTO")
    entry = {
        "name": name, "file": name + ".fbx", "purpose": purpose,
        "triangles": len(mesh.loop_triangles), "vertices": len(mesh.vertices),
        "separate_pieces": geo.pieces, "bounds_m": {"min": minimum, "max": maximum},
        "dimensions_m": [maximum[i] - minimum[i] for i in range(3)],
        "expected_dimensions_cm": [(maximum[i] - minimum[i]) * 100 for i in range(3)],
        "highest_point_cm": maximum[2] * 100, "material_slots": MATERIAL_NAMES,
        "origin": "Underlying floor plane Z=0; centre of the authored field in X/Y.",
        "placement": placement, "collision": "Decoration only. NoCollision; actor collision false.",
        "sha256": hashlib.sha256((OUT / (name + ".fbx")).read_bytes()).hexdigest(),
    }
    ASSETS.append(entry)
    OBJECTS.append(obj)
    print("PARITY_FLOOR_ASSET", name, entry["triangles"], entry["highest_point_cm"], flush=True)


def clip_poly(poly, nx, ny, distance):
    if not poly:
        return []
    result = []
    prev = poly[-1]
    prev_d = nx * prev[0] + ny * prev[1] - distance
    for curr in poly:
        curr_d = nx * curr[0] + ny * curr[1] - distance
        if (curr_d <= 0) != (prev_d <= 0):
            t = prev_d / (prev_d - curr_d)
            result.append((prev[0] + t * (curr[0] - prev[0]), prev[1] + t * (curr[1] - prev[1])))
        if curr_d <= 0:
            result.append(curr)
        prev, prev_d = curr, curr_d
    return result


def shard(geo, rng, x, y, radius, thickness, aspect=1, tilt=.03):
    n = rng.randint(4, 7)
    angle = rng.uniform(0, math.tau)
    radii = [radius * rng.uniform(.68, 1.15) for _ in range(n)]
    points = []
    for i in range(n):
        a = angle + i * math.tau / n + rng.uniform(-.13, .13)
        points.append((x + math.cos(a) * radii[i], y + math.sin(a) * radii[i] * aspect))
    geo.plate(points, thickness, min(.009, thickness * .32), rng,
              tilt=(rng.uniform(-tilt, tilt), rng.uniform(-tilt, tilt)))


# Fracture field A: thin irregular plates with millimetre gaps and low edge lift.
# Voronoi sites are random Poisson-like samples, never a rectilinear tile grid.
rng = random.Random(712031)
geo = Geometry()
rx, ry = 3.12, 2.38
boundary = [(math.cos(a) * rx, math.sin(a) * ry) for a in [i * math.tau / 29 for i in range(29)]]
sites = []
for _ in range(6000):
    x, y = rng.uniform(-rx, rx), rng.uniform(-ry, ry)
    if (x / rx) ** 2 + (y / ry) ** 2 > .94:
        continue
    if any((x - p[0]) ** 2 + (y - p[1]) ** 2 < .12 ** 2 for p in sites):
        continue
    sites.append((x, y))
    if len(sites) == 108:
        break
seamed_edges = set()
for sx, sy in sites:
    cell = boundary[:]
    for ox, oy in sites:
        if (ox, oy) == (sx, sy):
            continue
        nx, ny = ox - sx, oy - sy
        cell = clip_poly(cell, nx, ny, (ox * ox + oy * oy - sx * sx - sy * sy) / 2)
        if not cell:
            break
    if len(cell) < 3:
        continue
    cx = sum(x for x, y in cell) / len(cell)
    cy = sum(y for x, y in cell) / len(cell)
    edge_factor = max(0, 1 - (cx / rx) ** 2 - (cy / ry) ** 2)
    # Missing edge cells dissolve the field into individual fragments, avoiding
    # a circular backing disc or a regular paving-stone silhouette.
    if edge_factor < .29 and rng.random() < .78:
        continue
    if edge_factor < .55 and rng.random() < .24:
        continue
    height = .0025 + edge_factor * rng.uniform(.004, .020)
    gap = rng.uniform(.0028, .0062)
    inset = []
    for x, y in cell:
        distance = max(.05, math.hypot(x - cx, y - cy))
        inset.append((cx + (x - cx) * (1 - gap / distance), cy + (y - cy) * (1 - gap / distance)))
    # Recessed narrow seams are floor-coloured dark bands, not a filled sticker.
    for i, point in enumerate(cell):
        other = cell[(i + 1) % len(cell)]
        key = tuple(sorted((tuple(round(v, 5) for v in point), tuple(round(v, 5) for v in other))))
        if key not in seamed_edges:
            geo.ribbon([point, other], [gap * 2.4, gap * 2.4], height=.001)
            seamed_edges.add(key)
    geo.plate(inset, height, min(.007, height * .35), rng, bottom=.0011)
for _ in range(42):
    a = rng.uniform(0, math.tau)
    radius = rng.uniform(.75, 1.05)
    shard(geo, rng, math.cos(a) * rx * radius, math.sin(a) * ry * radius,
          rng.uniform(.02, .095), rng.uniform(.008, .022), rng.uniform(.55, 1), tilt=.015)
emit("SM_ParityFractureField_A", geo, "Low broken-concrete plates with real bevels and thin recessed irregular seams.", .06,
     "Use 2-3 instances, varied yaw, XY scale .65-.95. Keep Z scale 1. Best in foreground/side floor; actual maximum below 3 cm.")


# Fracture field B: long, branching hairline fractures with discontinuous lips.
rng = random.Random(712032)
geo = Geometry()
def crack_branch(start, direction, length, depth, width=.012):
    points = [Vector(start)]
    angle = direction
    steps = max(4, int(length / .24))
    for i in range(steps):
        angle += rng.uniform(-.5, .5)
        step = length / steps * rng.uniform(.6, 1.4)
        points.append(points[-1] + Vector((math.cos(angle), math.sin(angle))) * step)
    widths = [width * rng.uniform(.45, 1.15) * (1 - i / len(points) * .77) for i in range(len(points))]
    geo.ribbon(points, widths)
    for i in range(len(points) - 1):
        if rng.random() > .67:
            continue
        a, b = points[i], points[i + 1]
        d = b - a
        norm = Vector((-d.y, d.x)).normalized() * rng.choice([-1, 1])
        lip_width = rng.uniform(.012, .047)
        offset = widths[i] * .55
        poly = [a + norm * offset, b + norm * offset, b + norm * (offset + lip_width * .45), a + norm * (offset + lip_width)]
        # Flip source points when the lip lies on the other side, preserving +Z normals.
        signed_area = sum(poly[j].x * poly[(j + 1) % 4].y - poly[(j + 1) % 4].x * poly[j].y for j in range(4))
        if signed_area < 0:
            poly.reverse()
        geo.plate([(p.x, p.y) for p in poly], rng.uniform(.004, .022), .003, rng)
    if depth:
        for fraction, sign in [(.34, 1), (.68, -1)]:
            i = int(fraction * steps)
            d = points[i + 1] - points[i]
            crack_branch(points[i], math.atan2(d.y, d.x) + sign * rng.uniform(.65, 1.1), length * rng.uniform(.30, .48), depth - 1, width * .64)
crack_branch((-3.0, -.35), .16, 6.8, 2)
crack_branch((-.8, -.7), 1.25, 3.5, 1, .009)
emit("SM_ParityFractureField_B", geo, "Branching sub-centimetre cracks with scattered lifted concrete lips, no broad backing sheet.", .04,
     "Use 5-8 instances rotated and XY-scaled .6-1.1, Z=1. Safe interior dressing; no collision.")


def scatter(seed, count, radius_x, radius_y, sizes, heights, edge=False):
    rng = random.Random(seed)
    geo = Geometry()
    for i in range(count):
        x = rng.uniform(-radius_x, radius_x)
        y = rng.gauss(0, radius_y * .4) if edge else rng.uniform(-radius_y, radius_y)
        if not edge and (x / radius_x) ** 2 + (y / radius_y) ** 2 > 1:
            continue
        radius = rng.uniform(*sizes)
        if i % 5:
            radius *= .42
        height = rng.uniform(*heights)
        aspect = rng.uniform(.4, .98)
        shard(geo, rng, x, y, radius, height, aspect, tilt=.10 if edge else .045)
    return geo


emit("SM_ParityEdgeSpall", scatter(712033, 150, 2.85, .75, (.08, .35), (.01, .085), edge=True),
     "Dense broken perimeter strip with angular chunks and small fragments, varied tilts and chipped bevels.", .13,
     "Perimeter only; align its long X axis with the wall. Centres should be outside the central walk ring, near Y +/-1330 or X +/-1250 cm.")
emit("SM_ParityRubbleScatter_A", scatter(712034, 112, 2.05, 1.58, (.055, .24), (.008, .037)),
     "Broad sparse distribution of tilted triangular and polygonal concrete flakes.", .06,
     "Interior safe. Use 8-12 instances, XY scale .75-1.15, varied yaw, Z=1. Do not place all instances at one repeated scale.")
emit("SM_ParityRubbleScatter_B", scatter(712035, 105, 1.72, 1.24, (.045, .205), (.006, .032)),
     "Second deterministic rubble pattern with smaller, denser chips and independent silhouettes.", .06,
     "Interior safe. Alternate with scatter A, XY scale .7-1.2, random yaw, Z=1.")
emit("SM_ParityMicroChips", scatter(712036, 350, 2.85, 2.45, (.017, .082), (.003, .012)),
     "Fine concrete aggregate particles that catch close light without hiding feet or movement.", .025,
     "Use 8-12 instances in foreground and peripheral ring; central combat area can take a few lightly scaled instances.")


total = sum(item["triangles"] for item in ASSETS)
assert total < 100000, total
roundtrips = []
for entry in ASSETS:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(OUT / entry["file"]), use_anim=False)
    loaded = [o for o in set(bpy.data.objects) - before if o.type == "MESH"]
    assert len(loaded) == 1, entry["name"]
    obj = loaded[0]
    xyz = [obj.matrix_world @ v.co for v in obj.data.vertices]
    dims = [max(p[i] for p in xyz) - min(p[i] for p in xyz) for i in range(3)]
    err = max(abs(a - b) for a, b in zip(dims, entry["dimensions_m"]))
    obj.data.calc_loop_triangles()
    slots = [m.material.name.split(".")[0] for m in obj.material_slots]
    assert err < .00002, (entry["name"], err)
    assert len(obj.data.loop_triangles) == entry["triangles"]
    assert slots == MATERIAL_NAMES, (entry["name"], slots)
    assert len(obj.data.uv_layers) == 1
    roundtrips.append({"name": entry["name"], "dimensions_m": dims, "max_dimension_error_m": err,
                       "triangles": len(obj.data.loop_triangles), "material_slots": slots, "uv_layers": 1, "passed": True})
    bpy.data.objects.remove(obj, do_unlink=True)


# Deterministic suggested actor positions in the existing 27 x 28 m play area.
# Higher edge spall stays near the boundary; all other assets are very shallow.
placements = []
def suggest(mesh, x, y, yaw, sx=1, sy=None):
    placements.append({"mesh": mesh, "location_cm": [x, y, -5], "rotation_deg": [0, yaw, 0],
                       "rotation_convention": "Unreal Rotator(pitch,yaw,roll)", "scale": [sx, sx if sy is None else sy, 1],
                       "collision_profile": "NoCollision", "cast_shadow": True})
for x, y, yaw, size in [(-750,-650,23,.85),(120,920,-31,.78),(900,-380,71,.72)]:
    suggest("SM_ParityFractureField_A",x,y,yaw,size)
for x,y,yaw,size in [(-440,80,24,1),(-530,920,-23,.72),(620,200,101,.85),(180,-970,10,.85),(1060,840,118,.75),(-1080,-140,85,.68)]:
    suggest("SM_ParityFractureField_B",x,y,yaw,size)
for x,y,yaw,size in [(-920,-1260,0,.86),(-120,-1330,0,.90),(770,-1300,-8,.91),(-1050,1250,0,.72),(-280,1320,8,.88),(690,1300,-4,.93),(1240,580,90,.92),(1280,-500,90,.85),(-1270,220,90,.8)]:
    suggest("SM_ParityEdgeSpall",x,y,yaw,size)
rng = random.Random(19377)
for i,(x,y) in enumerate([(-980,-850),(-500,-1090),(90,-1090),(660,-930),(1010,-660),(1010,-50),(980,640),(590,980),(10,1050),(-630,930),(-1020,550),(-1110,0),(-750,-400),(300,530),(450,-500),(-240,210)]):
    suggest("SM_ParityRubbleScatter_A" if i%2==0 else "SM_ParityRubbleScatter_B",x,y,rng.uniform(-180,180),rng.uniform(.68,.99))
for x,y in [(-900,-700),(-300,-950),(350,-880),(900,-510),(920,350),(540,920),(-170,970),(-850,600),(-950,30),(-280,190),(370,-170)]:
    suggest("SM_ParityMicroChips",x,y,rng.uniform(-180,180),rng.uniform(.75,1.0))

manifest = {
    "owner": OWNER, "status": "verified_fbx_ready_for_unreal",
    "source": "Original deterministic local mesh authoring. No external models, no AI-image sampling, no source-reference edits.",
    "visual_target": "study/visuals/direction-close-best.jpg",
    "target_sha256": hashlib.sha256((ROOT/"study/visuals/direction-close-best.jpg").read_bytes()).hexdigest(),
    "generator": "tools/make_parity_floor.py", "blender_version": bpy.app.version_string,
    "coordinate_system": "Metres, +Z up. Origin Z=0 on floor. FBX converts metres to Unreal centimetres. Place at measured floor top, currently Z=-5 cm.",
    "fbx_settings": {"axis_forward":"-Y","axis_up":"Z","global_scale":1,"apply_unit_scale":True,"apply_scale_options":"FBX_SCALE_NONE"},
    "material_slots": MATERIAL_NAMES,
    "material_guidance": {"Concrete":"Use the same world-aligned floor albedo/normal/roughness as the base floor; modest colour variance only.",
                          "Aggregate":"Slightly lighter neutral fractured concrete; roughness .90-.98, low specular. No emissive.",
                          "Dark":"Very dark desaturated concrete for narrow crack bottoms; roughness .95, low specular. No emissive."},
    "uv0": "Planar local XY metre coordinates /4. Use world-aligned sampling on instances for a continuous floor.",
    "total_triangles": total, "assets": ASSETS, "fbx_roundtrip_checks": roundtrips,
    "recommended_placements": placements,
    "placement_limits": "NoCollision and actor collision disabled. Do not scale Z upward. Hide older oversized crack/stain/debris decals when comparing. EdgeSpall is perimeter-only. Check actual game-camera views after import.",
    "limits": "Blender source/export geometry verified. Unreal import, materials, placement, lighting, runtime occlusion and visual parity require the integration owner's game captures.",
}
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")


# Editable kit studio: real geometry plus labelled, non-exported comparison pads.
preview_layout = [(-7,3.5,0),(1,3.5,0),(8,3.5,0),(-6,-3.4,0),(0,-3.4,0),(6.2,-3.4,0)]
for obj, loc in zip(OBJECTS,preview_layout):
    obj.location = loc
    obj["owner"] = OWNER
    obj["source_origin"] = "Floor Z=0. Exported FBX remains centred before this preview layout."

ground_mat = bpy.data.materials.new("Preview floor only")
ground_mat.use_nodes = True
shader = ground_mat.node_tree.nodes.get("Principled BSDF")
shader.inputs["Base Color"].default_value = (.08,.106,.109,1)
shader.inputs["Roughness"].default_value = .92
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.0015))
ground = bpy.context.object
ground.name = "Preview floor - not exported"
ground.data.materials.append(ground_mat)
label_mat = bpy.data.materials.new("Preview label only")
label_mat.diffuse_color = (.5,.7,.72,1)
for obj, entry in zip(OBJECTS, ASSETS):
    font = bpy.data.curves.new("Preview label", "FONT")
    font.body = entry["name"].replace("SM_Parity", "") + " | " + str(entry["triangles"]) + " tris"
    font.size = .25
    text_obj = bpy.data.objects.new("Label - " + entry["name"],font)
    scene.collection.objects.link(text_obj)
    text_obj.location = (obj.location.x-2.65,obj.location.y-2.8,.002)
    font.materials.append(label_mat)

world = bpy.data.worlds.new("Floor kit studio")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (.16,.21,.23,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = .55
scene.world = world
for name,loc,energy,size in [("Raking key",(-8,-7,5),3100,5),("Soft fill",(6,5,11),2500,8),("Edge fill",(11,-3,4),850,4)]:
    data = bpy.data.lights.new(name,"AREA")
    data.energy, data.shape, data.size = energy, "DISK", size
    light = bpy.data.objects.new(name,data)
    scene.collection.objects.link(light)
    light.location=loc
    light.rotation_euler=(Vector((0,0,0))-light.location).to_track_quat("-Z","Y").to_euler()
data = bpy.data.cameras.new("Floor kit overview")
camera = bpy.data.objects.new("Floor kit overview",data)
scene.collection.objects.link(camera)
camera.location=(8,-18,24)
camera.rotation_euler=(Vector((.4,.2,0))-camera.location).to_track_quat("-Z","Y").to_euler()
data.type="ORTHO"
data.ortho_scale=25
scene.camera=camera
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=24
scene.cycles.use_denoising=True
scene.render.resolution_x=1700
scene.render.resolution_y=1100
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="AgX"
scene.render.filepath=str(OUT/"kit-overview.png")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"ParityFloor_Kit.blend"))
bpy.ops.render.render(write_still=True)
camera.location=(-9,-2,3.3)
camera.rotation_euler=(Vector((-7,3.5,0))-camera.location).to_track_quat("-Z","Y").to_euler()
data.ortho_scale=7.5
scene.render.resolution_x=1400
scene.render.resolution_y=900
scene.render.filepath=str(OUT/"fracture-depth-detail.png")
bpy.ops.render.render(write_still=True)
print("PARITY_FLOOR_COMPLETE",json.dumps({"assets":len(ASSETS),"triangles":total,"placements":len(placements),"manifest":str(OUT/"manifest.json")}),flush=True)
