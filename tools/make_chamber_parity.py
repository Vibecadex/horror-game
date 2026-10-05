"""Author the missing chamber-reference modules; never invokes Unreal.

Run with installed Blender in background mode with --disable-autoexec.
Only Assets/Adapted/ChamberParity is written. Existing room, shell, dressing,
character, animation and source-reference assets are not modified.

Coordinates: metres, Z up, architectural front -Y, floor pivots except wheel axle.
The tested project static-FBX convention presents source -Y as Unreal +Y;
placement recommendations explicitly account for that Y reflection.
"""
import bpy
import bmesh
import hashlib
import itertools
import json
import math
import random
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Assets' / 'Adapted' / 'ChamberParity'
OWNER = 'teddy-chamber-parity-20261005'
if OUT.exists() and any(OUT.iterdir()):
    marker = OUT / 'manifest.json'
    if not marker.exists() or json.loads(marker.read_text(encoding='utf-8')).get('owner') != OWNER:
        raise RuntimeError('Refusing to overwrite an unowned ChamberParity folder')
OUT.mkdir(parents=True, exist_ok=True)
(OUT/'manifest.json').write_text(json.dumps({'owner': OWNER, 'status': 'authoring'}), encoding='utf-8')
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'

SLOTS = ['Metal', 'Concrete', 'Rust', 'Dark', 'Emissive', 'Stencil']
MATS = {}
PALETTE = {
    'Metal': ((.060, .073, .071, 1), (.18, .195, .18, 1), .65, .70),
    'Concrete': ((.13, .134, .124, 1), (.275, .273, .247, 1), .01, .93),
    'Rust': ((.048, .035, .020, 1), (.18, .093, .040, 1), .12, .96),
    'Dark': ((.005, .008, .009, 1), (.026, .034, .033, 1), .24, .82),
    'Emissive': ((.40, .005, .002, 1), (.6, .007, .003, 1), .05, .42),
    'Stencil': ((.20, .205, .174, 1), (.42, .432, .379, 1), .02, .96),
}
for name in SLOTS:
    lo, hi, metal, rough = PALETTE[name]
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = hi
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.get('Principled BSDF')
    shader.inputs['Metallic'].default_value = metal
    shader.inputs['Roughness'].default_value = rough
    coords = nodes.new('ShaderNodeTexCoord')
    tex = nodes.new('ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value = 8 if name == 'Concrete' else 13
    tex.inputs['Detail'].default_value = 4
    tex.inputs['Roughness'].default_value = .76
    links.new(coords.outputs['Object'], tex.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .26
    ramp.color_ramp.elements[0].color = lo
    ramp.color_ramp.elements[1].position = .73
    ramp.color_ramp.elements[1].color = hi
    links.new(tex.outputs['Fac'], ramp.inputs[0])
    links.new(ramp.outputs['Color'], shader.inputs['Base Color'])
    fine = nodes.new('ShaderNodeTexNoise')
    fine.inputs['Scale'].default_value = 170 if name == 'Concrete' else 250
    fine.inputs['Detail'].default_value = 3
    links.new(coords.outputs['Object'], fine.inputs['Vector'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .32 if name == 'Concrete' else .20
    bump.inputs['Distance'].default_value = .005 if name == 'Concrete' else .0018
    links.new(fine.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    if name == 'Emissive':
        shader.inputs['Emission Color'].default_value = hi
        shader.inputs['Emission Strength'].default_value = 2.0
    MATS[name] = mat

PARTS, OBJECTS, ASSETS = [], [], []


def finish(obj, material='Metal', bevel=0, smooth=False):
    # Converted font booleans may leave an empty slot; own each new part's
    # initial material table explicitly before later per-face assignments.
    obj.data.materials.clear()
    obj.data.materials.append(MATS[material])
    bpy.context.view_layer.objects.active = obj
    if bevel:
        modifier = obj.modifiers.new('Machined and worn edge radius', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 2
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = len(p.vertices) == 4
    PARTS.append(obj)
    return obj


def box(name, location, size, material='Metal', bevel=.012):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, material, min(bevel, min(size)*.2) if bevel else 0)


def cylinder(name, location, radius, depth, material='Metal', axis='Z', vertices=32, bevel=.004):
    rotation = {'X': (0, math.pi/2, 0), 'Y': (math.pi/2, 0, 0), 'Z': (0, 0, 0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                      location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return finish(obj, material, bevel, True)


def torus(name, location, radius, tube, material='Metal', axis='Z', major=48, minor=8):
    rotation = {'X': (0, math.pi/2, 0), 'Y': (math.pi/2, 0, 0), 'Z': (0, 0, 0)}[axis]
    bpy.ops.mesh.primitive_torus_add(major_segments=major, minor_segments=minor,
                                   major_radius=radius, minor_radius=tube,
                                   location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    finish(obj, material)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def beam(name, start, end, width, depth, material='Metal', bevel=.006):
    a, b = Vector(start), Vector(end)
    obj = box(name, (a+b)/2, (width, depth, (b-a).length), material, bevel)
    obj.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    return obj


def raw_mesh(name, vertices, faces, material='Metal', bevel=0):
    data = bpy.data.meshes.new(name+'Geometry')
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    return finish(obj, material, bevel)


def profile(width, height, cut, bottom=0):
    return [(-width/2+cut, bottom), (width/2-cut, bottom),
            (width/2, bottom+cut), (width/2, bottom+height-cut),
            (width/2-cut, bottom+height), (-width/2+cut, bottom+height),
            (-width/2, bottom+height-cut), (-width/2, bottom+cut)]


def plate(name, polygon, front, back, material='Metal', bevel=.008):
    n = len(polygon)
    vertices = [(x, y, z) for y in (front, back) for x, z in polygon]
    faces = [tuple(range(n-1, -1, -1)), tuple(range(n, n*2))]
    faces += [(i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n)]
    return raw_mesh(name, vertices, faces, material, bevel)


def frame(name, outer, inner, front, back, material='Metal', bevel=.008):
    assert len(outer) == len(inner)
    n = len(outer)
    vertices = [(x, y, z) for y in (front, back) for loop in (outer, inner) for x,z in loop]
    faces = []
    for i in range(n):
        j = (i+1)%n
        faces.extend([(i, j, j+n, i+n),
                      (i+n*2, i+n*3, j+n*3, j+n*2),
                      (i, i+n*2, j+n*2, j),
                      (i+n, j+n, j+n*3, i+n*3)])
    return raw_mesh(name, vertices, faces, material, bevel)


def bolt(x, y, z, radius=.030):
    cylinder('Recessed washer', (x,y+.008,z), radius*1.6, .020, 'Dark', 'Y', 16, .002)
    cylinder('Worn hex head', (x,y-.012,z), radius, .035, 'Metal', 'Y', 6, .003)


def text_stencil(body, left, front, bottom, height):
    curve = bpy.data.curves.new('B-3 stencil outlines', 'FONT')
    curve.body = body
    curve.size = height
    curve.space_character = 1.1
    curve.extrude = .0014
    curve.resolution_u = 3
    obj = bpy.data.objects.new('B-3 worn physical stencil', curve)
    scene.collection.objects.link(obj)
    obj.location = (left, front, bottom)
    obj.rotation_euler = (math.pi/2,0,0)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    # Narrow missing paint bridges provide a recognisable industrial stencil.
    for offset, z, width, h in ((.055, .19, .028, .15),(.31,.40,.026,.17),(.87,.25,.025,.14)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(left+offset,front,bottom+z))
        cutter = bpy.context.object
        cutter.dimensions = (width,.04,h)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        modifier = obj.modifiers.new('Stencil paint interruption','BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = cutter
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
    finish(obj, 'Stencil')
    return obj


def bounds(obj):
    points = [obj.matrix_world @ Vector(v) for v in obj.bound_box]
    return {'min':[min(p[i] for p in points) for i in range(3)],
            'max':[max(p[i] for p in points) for i in range(3)]}


def export_asset(name, purpose, details, origin=None):
    bpy.ops.object.select_all(action='DESELECT')
    part_count = len(PARTS)
    for obj in PARTS:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name+'_Geometry'
    scene.cursor.location = (0,0,0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    old_slots = [s.material.name for s in obj.material_slots]
    indices = [SLOTS.index(old_slots[p.material_index]) for p in obj.data.polygons]
    obj.data.materials.clear()
    for material in MATS.values():
        obj.data.materials.append(material)
    for p,index in zip(obj.data.polygons,indices):
        p.material_index = index
    bm=bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.calc_loop_triangles()
    b = bounds(obj)
    dims = [b['max'][i]-b['min'][i] for i in range(3)]
    used = {SLOTS[p.material_index] for p in obj.data.polygons}
    entry = {'name':name,'file':name+'.fbx','purpose':purpose,'detail':details,
             'triangles':len(obj.data.loop_triangles),'vertices':len(obj.data.vertices),
             'component_count':part_count,'bounds_m':b,'dimensions_m':dims,
             'expected_dimensions_cm':[100*v for v in dims],
             'origin':origin or 'Floor Z=0, centre of module width X=0. Back of wall-mounted assembly toward +Y.',
             'front':'Blender -Y; project static FBX imports this toward Unreal +Y.',
             'material_slots':SLOTS,'used_materials':sorted(used),
             'collision':'NoCollision decoration; retain existing chamber collision.'}
    bpy.ops.export_scene.fbx(filepath=str(OUT/entry['file']),use_selection=True,
        object_types={'MESH'},axis_forward='-Y',axis_up='Z',global_scale=1,
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',
        use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,
        bake_anim=False,path_mode='AUTO')
    entry['sha256'] = hashlib.sha256((OUT/entry['file']).read_bytes()).hexdigest()
    obj['owner'] = OWNER
    obj['source_origin'] = entry['origin']
    obj['source_front'] = '-Y'
    obj['purpose'] = purpose
    ASSETS.append(entry)
    OBJECTS.append(obj)
    PARTS.clear()
    print('CHAMBER_ASSET',name,entry['triangles'],dims,flush=True)
    return obj


# 1. Reverse-side service bay. The shadow cavity is physical, not a flat card.
# It remains closed scenery; parent retains the room's original collision.
box('Dark rear chamber', (0,.20,1.64), (1.77,.055,3.16), 'Dark', .012)
box('Subdued service leaf', (0,.161,1.63), (1.60,.047,3.01), 'Dark', .025)
for x in (-1.045,1.045):
    box('Worn concrete door jamb',(x,-.055,1.705),(.23,.48,3.41),'Concrete',.034)
    box('Metal reveal jamb',(x*.852,-.042,1.61),(.103,.51,3.20),'Metal',.012)
    box('Outer steel jamb lip',(x*.916,-.321,1.66),(.134,.115,3.31),'Metal',.008)
    for z in (.25,1.32,2.54,3.21):
        bolt(x*.924,-.392,z,.021)
box('Concrete lintel',(0,-.055,3.475),(2.32,.48,.25),'Concrete',.032)
box('Recessed head reveal',(0,-.045,3.177),(1.90,.51,.12),'Metal',.014)
box('Black threshold tray',(0,-.047,.042),(1.89,.61,.084),'Dark',.008)
for y in (-.28,-.15,-.02,.11):
    box('Threshold anti-slip lip',(0,y,.082),(1.75,.038,.018),'Metal',.003)
for x in (-.58,.58):
    for z in (.37,2.73):
        bolt(x,.124,z,.019)
box('Subtle leaf waist reinforcement',(0,.118,1.26),(1.48,.035,.075),'Metal',.005)
box('Inset latch backing',(.60,.107,1.44),(.15,.042,.30),'Dark',.008)
box('Recessed latch handle',(.60,.066,1.46),(.038,.045,.17),'Metal',.009)
box('Beacon mounting plate',(0,-.27,3.443),(.34,.072,.24),'Metal',.011)
cylinder('Beacon red lens',(0,-.329,3.443),.058,.056,'Emissive','Y',24,.011)
box('Beacon rain hood',(0,-.373,3.533),(.39,.28,.048),'Dark',.009)
for x in (-.15,.15):
    bolt(x,-.325,3.44,.013)
service = export_asset('SM_ChamberServiceDoorBay',
    'Two shallow recessed service bays for the reverse/fourth wall.',
    '2.32m concrete frame, 1.6m dark leaf, ~0.55m real reveal depth, threshold grip lips, one small red beacon. No wheel.')


# 2/3. Real rolled-shell barrels. Lathed rings plus correlated local dents make
# their silhouette distinct from clean cylinders, without high-cost sculpting.
def drum(cx, cy, yaw=0, scale=1, seed=8):
    start = len(PARTS)
    rng = random.Random(seed)
    dents = [(rng.uniform(0,math.tau),rng.uniform(.20,.79),rng.uniform(.012,.026)) for _ in range(4)]
    profile_rows = [(0,.286),(.012,.300),(.031,.303),(.052,.290),
                    (.10,.287),(.19,.288),(.227,.291),(.242,.310),(.262,.312),(.279,.291),
                    (.365,.287),(.46,.285),(.55,.288),(.639,.291),(.659,.312),(.679,.310),
                    (.696,.291),(.79,.288),(.865,.287),(.903,.300),(.923,.300),(.930,.290)]
    segments = 48
    vertices,faces,face_rust = [],[],[]
    for z,radius in profile_rows:
        for j in range(segments):
            a = j*math.tau/segments
            dent = 0
            for da,dz,amplitude in dents:
                delta = math.atan2(math.sin(a-da),math.cos(a-da))
                dent -= amplitude*math.exp(-(delta/.27)**2-((z-dz)/.115)**2)
            r = radius+dent+.0017*math.sin(a*7+z*23)
            vertices.append((math.cos(a)*r,math.sin(a)*r,z+.0008*math.sin(a*5)))
    for row in range(len(profile_rows)-1):
        for j in range(segments):
            faces.append((row*segments+j,row*segments+(j+1)%segments,
                          (row+1)*segments+(j+1)%segments,(row+1)*segments+j))
            # Narrow oxide tracks in the lower roll and a few coherent dents.
            face_rust.append(row in (1,2,18) and ((j+seed)%17<6))
    faces.append(tuple(range(segments-1,-1,-1)))
    face_rust.append(False)
    body = raw_mesh('Dented rolled steel drum shell',vertices,faces,'Metal')
    body.data.materials.append(MATS['Rust'])
    for p,oxide in zip(body.data.polygons,face_rust):
        p.material_index = 1 if oxide else 0
        p.use_smooth = len(p.vertices)==4
    # Inset, dished lid with bead seam, two physically modelled bung plugs.
    cylinder('Inset drum lid',(0,0,.908),.287,.016,'Metal','Z',48,.002)
    torus('Rolled drum upper rim',(0,0,.922),.296,.007,'Metal','Z',48,6)
    torus('Pressed lid groove',(0,0,.917),.253,.004,'Dark','Z',48,6)
    torus('Rolled drum lower rim',(0,0,.019),.297,.006,'Rust','Z',48,6)
    for x,y,r in ((.153,.08,.037),(-.161,-.08,.021)):
        cylinder('Bung socket',(x,y,.923),r*1.33,.018,'Dark','Z',20,.002)
        cylinder('Bung six-sided plug',(x,y,.937),r,.018,'Metal','Z',6,.003)
        box('Bung driver groove',(x,y,.947),(r*1.35,.007,.003),'Dark',.0005)
    # A short worn paint scuff follows the side rather than becoming a label.
    for a in (.25,.44,.62):
        a += seed*.7
        pts = []
        for r,z,aa in ((.289,.437,a),(.289,.452,a),(.289,.445,a+.10),(.289,.428,a+.09)):
            pts.append((math.cos(aa)*r,math.sin(aa)*r,z))
        raw_mesh('Worn side paint chip',pts,[(0,1,2,3)],'Rust')
    c,s = math.cos(yaw),math.sin(yaw)
    for obj in PARTS[start:]:
        # Bake each object's complete world transform before cluster placement.
        for vertex in obj.data.vertices:
            p = obj.matrix_world @ vertex.co
            vertex.co = (cx+scale*(c*p.x-s*p.y),cy+scale*(s*p.x+c*p.y),scale*p.z)
        obj.location = (0,0,0)
        obj.rotation_euler = (0,0,0)
        obj.scale = (1,1,1)


drum(0,0,seed=11)
single = export_asset('SM_ChamberDrum',
    'Single worn low steel drum for door-side/perimeter dressing.',
    '48 radial segments, two rolled reinforcement beads, correlated dents, inset lid, two bung plugs; floor pivot.')
drum(-.331,.04,yaw=.18,seed=16)
drum(.331,-.037,yaw=-.35,scale=.953,seed=31)
pair = export_asset('SM_ChamberDrumPair',
    'Irregular two-drum group for the side service perimeter.',
    'Two different dent patterns, staggered positions, subtly different heights. Does not include a tank or fan.')


# 4. Reference-proportioned bulkhead; this REPLACES the old 5m assembly.
# Its sole wheel is a separate axle-pivot mesh; never stack it over the old door.
outer = profile(10.0,5.60,.73)
opening = profile(8.82,4.70,.60,.39)
frame('Chamfered concrete pressure surround',outer,opening,-.36,.36,'Concrete',.040)
frame('Dark isolation gasket',profile(9.00,4.88,.63,.30),
      profile(8.66,4.57,.58,.46),-.405,.12,'Dark',.015)
frame('Stepped heavy steel pressure frame',profile(8.98,4.88,.64,.30),
      profile(8.42,4.34,.52,.56),-.61,-.235,'Metal',.028)
frame('Inner rolled sealing lip',profile(8.51,4.42,.54,.52),
      profile(8.34,4.25,.51,.60),-.644,-.39,'Rust',.009)
plate('Continuous dark pressure backing',profile(8.47,4.40,.53,.52),.08,.15,'Dark',.008)
for sign in (-1,1):
    poly = [(sign*.035,.61),(sign*3.655,.61),(sign*4.15,1.10),
            (sign*4.15,4.32),(sign*3.645,4.83),(sign*.035,4.83)]
    if sign<0:
        poly.reverse()
    plate('Broad closed pressure door leaf',poly,-.12,.055,'Metal',.017)
    # Real shallow inset panels and horizontal ribs replace the old X-bracing.
    for z,h in ((1.39,1.13),(3.30,1.53)):
        box('Broad inset panel shadow',(sign*2.04,-.154,z),(3.47,.038,h),'Dark',.010)
        box('Raised inset panel skin',(sign*2.04,-.184,z),(3.30,.034,h-.145),'Metal',.011)
    for z in (.82,2.13,2.45,4.58):
        box('Horizontal pressure rib',(sign*2.04,-.235,z),(3.83,.15,.105),'Metal',.014)
        for xoffset in (-1.70,1.70):
            bolt(sign*2.04+xoffset,-.323,z,.023)
    box('Inner leaf closing rail',(sign*.132,-.214,2.74),(.142,.148,3.90),'Metal',.012)
    # Three heavy hinge knuckles sit inside the pressure frame at each side.
    for z in (1.36,2.66,3.94):
        box('Hinge cheek',(sign*4.02,-.255,z),(.36,.28,.22),'Metal',.021)
        cylinder('Hinge pin',(sign*4.135,-.391,z),.065,.33,'Rust','Z',20,.006)
    # Low corrosion edges are irregular plates, avoiding clean orange stripes.
    for k in range(4):
        x = sign*(.53+k*.80)
        poly = [(x-.22,.87),(x+.23,.865),(x+.13,.84),(x-.17,.845)]
        plate('Broken lower rib oxide',poly,-.315,-.311,'Rust',0)

# Fastened frame flange, kept out of the cropped/chamfered corners.
for x in (-4.36,4.36):
    for z in (1.22,2.08,3.03,3.94):
        bolt(x,-.655,z,.036)
for x in (-3.6,-2.4,-1.2,0,1.2,2.4,3.6):
    bolt(x,-.653,4.995,.032)
    bolt(x,-.653,.391,.031)

# Gearbox and shaft stay on the door; one separate pressure wheel follows.
box('Lock gearbox shadow',(0,-.30,2.54),(.69,.26,.61),'Dark',.048)
box('Cast gearbox front',(0,-.457,2.54),(.55,.115,.46),'Metal',.035)
cylinder('Wheel central shaft',(0,-.625,2.54),.128,.28,'Metal','Y',32,.012)
for sign in (-1,1):
    box('Locking rod guide',(sign*.16,-.382,1.32),(.19,.13,.21),'Dark',.012)
    box('Locking rod guide',(sign*.16,-.382,3.92),(.19,.13,.21),'Dark',.012)
    cylinder('Vertical locking rod',(sign*.16,-.339,2.62),.034,3.60,'Metal','Z',16,.003)

text_stencil('B-3',1.86,-.207,3.10,.56)
box('Overhead fixture recess',(0,-.42,5.35),(1.76,.16,.16),'Dark',.018)
box('Overhead worn reflector',(0,-.513,5.35),(1.42,.041,.045),'Stencil',.008)
for x in (-.84,-.42,0,.42,.84):
    box('Overhead fixture guard',(x,-.558,5.35),(.028,.055,.175),'Metal',.004)
bulkhead = export_asset('SM_ChamberBulkhead',
    'Replacement 10m-wide rear pressure bulkhead, centred between rear piers.',
    '10x5.6m clipped concrete surround; recessed wide horizontal-panel leaves; gearbox/axle accepts ONE separate wheel; subordinate physical B-3 stencil. Conceal old bulkhead, do not layer over its wheel.')

cylinder('Wheel spoke hub',(0,.011,0),.16,.105,'Metal','Y',32,.015)
torus('Sole main bulkhead wheel rim',(0,0,0),.75,.035,'Metal','Y',64,10)
for a in [i*math.tau/6+.10 for i in range(6)]:
    beam('Cast wheel spoke',(math.cos(a)*.12,.011,math.sin(a)*.12),
         (math.cos(a+.065)*.733,0,math.sin(a+.065)*.733),.042,.044,'Metal',.007)
cylinder('Wheel central cap',(0,-.057,0),.088,.042,'Rust','Y',12,.008)
wheel = export_asset('SM_ChamberBulkheadWheel',
    'The only locking wheel for SM_ChamberBulkhead; distinct axle pivot allows proportion tuning.',
    '1.57m six-spoke cast pressure wheel. Align to door local(0,-.811,2.54)m; no second wheel is present in the door mesh.',
    'Axle centre X=Y=Z=0; front -Y. This is the sole non-floor pivot in the kit.')


def world_bounds(row, entry):
    c,s = math.cos(math.radians(row['yaw'])),math.sin(math.radians(row['yaw']))
    pts = []
    for p in itertools.product(*zip(entry['bounds_m']['min'],entry['bounds_m']['max'])):
        x,y,z = [a*b*100 for a,b in zip(p,row['scale'])]
        y=-y
        pts.append((row['location_cm'][0]+c*x-s*y,row['location_cm'][1]+s*x+c*y,row['location_cm'][2]+z))
    return {'min':[min(p[i] for p in pts) for i in range(3)],
            'max':[max(p[i] for p in pts) for i in range(3)]}


def placement(label, mesh, loc, yaw, reason):
    row = {'label':label,'mesh':mesh,'location_cm':loc,'yaw':yaw,'scale':[1,1,1],
           'collision':'NoCollision','reason':reason}
    entry = next(a for a in ASSETS if a['name']==mesh)
    b=world_bounds(row,entry)
    row['world_bounds_cm']=b
    row['outside_combat_guard'] = (b['max'][0]<=-1400 or b['min'][0]>=1480 or b['max'][1]<=-1500 or b['min'][1]>=1500)
    assert row['outside_combat_guard'], (label,b)
    return row


placements = [
    placement('RearBulkhead','SM_ChamberBulkhead',[1630,180,62],90,
        'Replace/conceal TE_Room_Bulkhead only; rear door spans Y[-320,680]. Inspect overlapping old rear inset/header dressing.'),
    placement('RearBulkheadWheel','SM_ChamberBulkheadWheel',[1548.9,180,316],90,
        'Exactly one wheel, aligned to main door local(0,-.811,2.54)m. Axle pivot allows independent uniform scale.'),
    placement('ReverseDoorL','SM_ChamberServiceDoorBay',[-1580,-700,-5],-90,
        'Fourth wall visible face at X<=-1605, behind dark leaf; copy original closed collision.'),
    placement('ReverseDoorR','SM_ChamberServiceDoorBay',[-1580,700,-5],-90,
        'Second reverse service bay; same height and door design; beacon is small red lens only.'),
    placement('ReverseDrumL','SM_ChamberDrum',[-1565,-450,-5],-90,
        'Single drum beside reverse left door, supported by arena floor, outside guard.'),
    placement('ReverseDrumR','SM_ChamberDrum',[-1565,980,-5],-73,
        'Offset single drum beside reverse right door. Keep gaps between service groups.'),
    placement('RightServiceDrums','SM_ChamberDrumPair',[130,1590,62],180,
        'Two drums supported by retained right foundation top61cm; beside existing services, not a repeated row.'),
    placement('LeftServiceDrums','SM_ChamberDrumPair',[850,-1590,62],0,
        'Two drums supported by left foundation top61cm, between existing pilasters.'),
    placement('RearDrum','SM_ChamberDrum',[1570,-435,62],90,
        'One drum near left bulkhead jamb, clear of retained rear crate atY-585 and original door wheel.'),
]

# Independent FBX readback checks dimensions, topology count, material names,
# UV availability and geometry bounds. This is source verification, not UE QA.
roundtrips=[]
for entry in ASSETS:
    before=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(OUT/entry['file']),use_anim=False)
    loaded=[o for o in set(bpy.data.objects)-before if o.type=='MESH']
    assert len(loaded)==1,(entry['name'],len(loaded))
    obj=loaded[0]
    b=bounds(obj)
    dimensions=[b['max'][i]-b['min'][i] for i in range(3)]
    error=max(abs(a-b) for a,b in zip(dimensions,entry['dimensions_m']))
    obj.data.calc_loop_triangles()
    imported_names=[slot.material.name.split('.')[0] for slot in obj.material_slots]
    assert error<.000025,(entry['name'],error)
    assert len(obj.data.loop_triangles)==entry['triangles']
    assert imported_names==SLOTS,(entry['name'],imported_names)
    assert len(obj.data.uv_layers)>=1
    assert all(math.isfinite(v) for vertex in obj.data.vertices for v in vertex.co)
    roundtrips.append({'name':entry['name'],'max_dimension_error_m':error,
                      'triangles':len(obj.data.loop_triangles),'material_slots':imported_names,
                      'uv_layers':len(obj.data.uv_layers),'passed':True})
    bpy.data.objects.remove(obj,do_unlink=True)
assert sum(a['triangles'] for a in ASSETS)<60000

# Editable scene layout is separate from origin-zero exports.
layout=[(-7.1,0,0),(-5.45,-2.1,0),(-3.70,-2.0,0),(1.60,.6,0),(1.60,-.211,2.54)]
for obj,loc in zip(OBJECTS,layout):
    obj.location=loc

bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.024))
ground=bpy.context.object
ground.name='Studio floor - not exported'
mat=bpy.data.materials.new('StudioFloor')
mat.use_nodes=True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.12,.13,.125,1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.95
ground.data.materials.append(mat)
world=bpy.data.worlds.new('Neutral material-check studio')
world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.16,.17,.18,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.38
scene.world=world
for name,loc,energy,size in [('Broad key',(-5,-9,12),2800,7),('Soft fill',(9,-4,9),2200,5),('Rim',(0,6,11),3100,6)]:
    data=bpy.data.lights.new(name,'AREA')
    data.energy=energy;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector((0,0,2))-obj.location).to_track_quat('-Z','Y').to_euler()
camera_data=bpy.data.cameras.new('Chamber modules overview')
camera=bpy.data.objects.new('Chamber modules overview',camera_data)
scene.collection.objects.link(camera)
camera.location=(11,-22,14)
camera.rotation_euler=(Vector((-.9,0,2.3))-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.type='ORTHO';camera_data.ortho_scale=21
scene.camera=camera
scene.render.resolution_x=1800;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.filepath=str(OUT/'kit-overview.png')
blend_path=OUT/'ChamberParity_Kit.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
bpy.ops.render.render(write_still=True)

# Straight front proof lets reviewers judge pressure-frame/door proportions.
camera.location=(1.6,-16,3.0)
camera.rotation_euler=(Vector((1.6,.6,2.8))-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.ortho_scale=11.3
scene.render.resolution_x=1600;scene.render.resolution_y=950
scene.render.filepath=str(OUT/'bulkhead-front.png')
for obj in (service,single,pair):
    obj.hide_render=True
bpy.ops.render.render(write_still=True)
for obj in (service,single,pair):
    obj.hide_render=False

# Detail proof for the newly required bay/drums, in neutral light.
bulkhead.hide_render=True
wheel.hide_render=True
camera.location=(-3.2,-9,5.2)
camera.rotation_euler=(Vector((-6.0,-.30,1.5))-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.ortho_scale=6.7
scene.render.resolution_x=1300;scene.render.resolution_y=1050
scene.render.filepath=str(OUT/'service-and-drums.png')
bpy.ops.render.render(write_still=True)
bulkhead.hide_render=False
wheel.hide_render=False

references=[]
for relative in ('study/visuals/chamber-target-front.png','study/visuals/chamber-target-reverse.png'):
    p=ROOT/relative
    references.append({'path':relative,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
manifest={
    'owner':OWNER,'status':'source-kit-ready-for-engine-review',
    'generator':'tools/make_chamber_parity.py',
    'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'editable_blend':'Assets/Adapted/ChamberParity/ChamberParity_Kit.blend',
    'blend_sha256':hashlib.sha256(blend_path.read_bytes()).hexdigest(),
    'source':'Original deterministic local geometry authored for the two user-selected chamber references. No external models or texture downloads.',
    'references':references,
    'reused_design_contract':'Generic bevel/primitive/export helpers follow the existing tools/make_industrial_room.py conventions. Existing room assets and generators were read only; no mesh or texture was overwritten.',
    'preserved':'Assets/Adapted/Room, RoomShell, RoomDressing, all original references, characters, rigs and clips remain unchanged.',
    'blender_version':bpy.app.version_string,
    'coordinate_system':'Metres, Z up, architectural front -Y; tested project static import mirrors Y. Origin zero at floor except separate wheel at axle centre.',
    'fbx_settings':{'axis_forward':'-Y','axis_up':'Z','global_scale':1,'apply_unit_scale':True,'apply_scale_options':'FBX_SCALE_NONE'},
    'material_slots':SLOTS,
    'material_contract':{'Metal':'worn painted steel','Concrete':'aged neutral concrete','Rust':'subdued dark oxide','Dark':'deep neutral cavity/recess','Emissive':'small red service-door beacon only','Stencil':'nonemissive aged pale paint; also overhead reflector'},
    'material_note':'Blender procedural noise/bump is preview-only. FBX slots/UVs are supplied for root-owned Unreal world-space materials. No baked teal or gameplay light pool.',
    'assets':ASSETS,'total_unique_triangles':sum(a['triangles'] for a in ASSETS),
    'fbx_roundtrip_checks':roundtrips,
    'combat_guard_cm':{'x':[-1400,1480],'y':[-1500,1500]},
    'recommended_placements':placements,
    'integration_requirements':[
        'Import into a new owned namespace with NoCollision and metre-to-centimetre dimensions verified; retain original collision.',
        'Main bulkhead is a replacement: conceal old TE_Room_Bulkhead visually without moving/removing original actor or its collision. Door body has no wheel; place exactly one separate SM_ChamberBulkheadWheel at its axle. Never layer the old wheel.',
        'Review and conceal old rear inset/header modules that overlap the 10m door; keep piers whose actual AABBs remain clear.',
        'Fourth-wall face must be behind the service leaves (X<=-1605 for the proposed X=-1580 origins), or use actual modular door gaps. A face atX=-1550 would occlude the recess.',
        'Fourth wall and mounted bays need root-owned reversible camera cutaway behavior; source kit does not implement gameplay or camera changes.',
        'Conceal the old low cutaway sill meshes wherever they overlap floor-level reverse door/drum geometry; preserve their collision and transforms.',
        'Drums atZ62 are on existing peripheral foundations whose top is61cm. Reverse drums atZ-5 rest on the arena floor. Do not reuse Z62 on bare floor.',
        'Existing cabinets, tanks, fans and pipe-rack wheels are reused, not duplicated by this kit.',
        'Actual Unreal shading, silhouette, floor contact and both full-room views require parent integration and independent capture review.'
    ],
    'render_evidence':['kit-overview.png','bulkhead-front.png','service-and-drums.png'],
    'limits':'Source geometry and Blender exports verified. No Unreal assets were imported or written. No exact-parity or player-acceptance claim.'
}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('CHAMBER_COMPLETE',json.dumps({'assets':len(ASSETS),'triangles':manifest['total_unique_triangles'],
                                  'roundtrips_passed':len(roundtrips),'placements':len(placements)}),flush=True)
