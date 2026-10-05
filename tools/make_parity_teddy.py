"""Add a separately exported, skin-weighted crown seam to the adapted teddy.

Original mesh vertices, UVs, skin weights, 16 bind bones and six clips are retained.
Only tools/make_parity_teddy.py and Assets/Adapted/Parity/Teddy are owned here.
No Unreal process is launched. Run with installed Blender in background mode.
"""
import bpy
import hashlib
import json
import math
import random
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Assets/Adapted/Teddy/Teddy_Encounter.blend"
OUT = ROOT / "Assets/Adapted/Parity/Teddy"
OWNER = "teddy-parity-stitches-20261005"
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
if OUT.exists() and any(OUT.iterdir()):
    marker = OUT / "manifest.json"
    if not marker.exists() or json.loads(marker.read_text(encoding="utf-8")).get("owner") != OWNER:
        raise RuntimeError("Refusing to overwrite unowned parity teddy output")
OUT.mkdir(parents=True, exist_ok=True)
(OUT/"manifest.json").write_text(json.dumps({"owner":OWNER,"status":"authoring"}),encoding="utf-8")
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
rig = bpy.data.objects["TeddyRig"]
mesh = bpy.data.objects["Teddy_Stitched"]
assert mesh.type == "MESH" and rig.type == "ARMATURE"
CLIPS = {"Idle":90,"Walk":37,"Crawl":37,"Attack":54,"Hit":16,"Defeat":72}
original_vertices = [v.co.copy() for v in mesh.data.vertices]
original_weights = [[(g.group,g.weight) for g in v.groups] for v in mesh.data.vertices]
original_uvs = {layer.name:[tuple(item.uv) for item in layer.data] for layer in mesh.data.uv_layers}
original_polygons = [tuple(p.vertices) for p in mesh.data.polygons]
original_count = len(original_vertices)
mesh.data.calc_loop_triangles()
triangles = [tuple(t.vertices) for t in mesh.data.loop_triangles]
bvh = BVHTree.FromPolygons(original_vertices,triangles,all_triangles=True)
groups = {g.index:g.name for g in mesh.vertex_groups}
bone_snapshot = [{"name":b.name,"parent":b.parent.name if b.parent else None,
                  "head_local_m":list(b.head_local),"tail_local_m":list(b.tail_local),
                  "matrix_local":[list(row) for row in b.matrix_local]} for b in rig.data.bones]
assert len(bone_snapshot)==16


def evaluate_body(count):
    bpy.context.view_layer.update()
    evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    geometry=evaluated.to_mesh()
    result=[geometry.vertices[i].co.copy() for i in range(count)]
    evaluated.to_mesh_clear()
    return result


samples={}
for name,count in CLIPS.items():
    rig.animation_data.action=bpy.data.actions[name]
    for frame in (1,(count+1)//2,count):
        scene.frame_set(frame)
        samples[(name,frame)]=evaluate_body(original_count)
rig.animation_data.action=bpy.data.actions["Idle"]
scene.frame_set(1)
rig.data.pose_position="REST"
bpy.context.view_layer.update()


def surface(x,y,offset=.003):
    hit,normal,_,_=bvh.ray_cast(Vector((x,y,7)),Vector((0,0,-1)))
    if hit is None:
        raise RuntimeError("Crown/back seam ray missed source mesh: "+str((x,y)))
    if normal.z<0:
        normal=-normal
    return hit+normal*offset,normal


vertices,faces,materials=[],[],[]
def face(points,material):
    start=len(vertices)
    vertices.extend(Vector(p) for p in points)
    for i in range(1,len(points)-1):
        faces.append((start,start+i,start+i+1))
        materials.append(material)


def tube(points,radius,material,sides=7):
    rings=[]
    for i,p in enumerate(points):
        tangent=points[min(i+1,len(points)-1)]-points[max(i-1,0)]
        tangent.normalize()
        reference=Vector((0,0,1))
        if abs(tangent.dot(reference))>.94:
            reference=Vector((0,1,0))
        u=tangent.cross(reference).normalized()
        v=tangent.cross(u).normalized()
        rings.append([p+radius*(math.cos(j*math.tau/sides)*u+math.sin(j*math.tau/sides)*v) for j in range(sides)])
    for i in range(len(rings)-1):
        for j in range(sides):
            k=(j+1)%sides
            face([rings[i][j],rings[i][k],rings[i+1][k],rings[i+1][j]],material)
    face(list(reversed(rings[0])),material)
    face(rings[-1],material)


rng=random.Random(61917)
seam_samples=[]
# The large upper mass is the source teddy's head. A diagonal crown seam is
# clearly visible from the elevated combat camera without changing its outline.
def crown_xy(t):
    return (-.94+1.88*t,-.69+.14*math.sin(t*math.pi*1.6)+.05*math.sin(t*23))

for i in range(57):
    t=i/56
    x,y=crown_xy(t)
    p,n=surface(x,y,.0018)
    seam_samples.append(p)
tube(seam_samples,.016,"SeamDark",sides=6)

stitch_records=[]
for stitch_index in range(13):
    t=.035+stitch_index*.073+rng.uniform(-.012,.012)
    x,y=crown_xy(t)
    p,n=surface(x,y,.006)
    ta=Vector(crown_xy(max(0,t-.005)))
    tb=Vector(crown_xy(min(1,t+.005)))
    tangent=(tb-ta).normalized()
    cross=Vector((-tangent.y,tangent.x))
    span=rng.uniform(.12,.165)
    skew=rng.uniform(-.025,.025)
    points=[]
    for j in range(11):
        q=j/10
        xy=Vector((x,y))+cross*((q-.5)*span)+tangent*skew*(q-.5)
        pp,nn=surface(xy.x,xy.y,.006+.026*math.sin(q*math.pi))
        points.append(pp)
    radius=rng.uniform(.008,.0105)
    tube(points,radius,"StitchThread")
    stitch_records.append({"kind":"crown","span_cm":span*100,"diameter_cm":radius*200,"center_m":list(p)})
    # A short tail beside occasional knots avoids a factory-perfect stitch row.
    if stitch_index in (2,6,10):
        tail=[points[-2],points[-1],points[-1]+Vector((.026,-.018,.019)),points[-1]+Vector((.045,-.026,.012))]
        tube(tail,radius*.62,"StitchThread",sides=5)

# Short upper-back continuation, weighted from the existing skin across the
# head/spine junction. It stops before the torso bend and never reaches the feet.
back=[]
for i in range(35):
    t=i/34
    x=.105+.07*math.sin(t*8)
    y=-.50+1.32*t
    p,n=surface(x,y,.0018)
    back.append(p)
tube(back,.0115,"SeamDark",sides=6)
for t in (.31,.48,.65,.81,.94):
    x=.105+.07*math.sin(t*8)
    y=-.50+1.32*t
    points=[]
    span=rng.uniform(.102,.145)
    for j in range(9):
        q=j/8
        p,n=surface(x+(q-.5)*span,y+.018*math.sin(q*math.pi),.006+.022*math.sin(q*math.pi))
        points.append(p)
    radius=.0075
    tube(points,radius,"StitchThread")
    stitch_records.append({"kind":"upper_back","span_cm":span*100,"diameter_cm":radius*200,"center_m":list(points[4])})

new_mesh=bpy.data.meshes.new("Teddy_Parity_Stitches_Geometry")
new_mesh.from_pydata(vertices,[],faces)
new_mesh.update()
stitches=bpy.data.objects.new("Teddy_Parity_Stitches",new_mesh)
scene.collection.objects.link(stitches)
for name,color,roughness in [("SeamDark",(.010,.009,.007,1),.98),("StitchThread",(.24,.215,.15,1),.87)]:
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    mat.diffuse_color=color
    bsdf=mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=color
    bsdf.inputs["Roughness"].default_value=roughness
    bsdf.inputs["Specular IOR Level"].default_value=.18
    new_mesh.materials.append(mat)
for polygon,material in zip(new_mesh.polygons,materials):
    polygon.material_index=0 if material=="SeamDark" else 1
    polygon.use_smooth=True
new_mesh.uv_layers.new(name=mesh.data.uv_layers.active.name)
for g in mesh.vertex_groups:
    stitches.vertex_groups.new(name=g.name)
weight_errors=[]
used_bones=set()
for vertex in new_mesh.vertices:
    hit,normal,index,distance=bvh.find_nearest(vertex.co)
    tri=triangles[index]
    a,b,c=[original_vertices[i] for i in tri]
    bary=barycentric_transform(hit,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
    weights={}
    for vertex_index,factor in zip(tri,bary):
        for group,weight in original_weights[vertex_index]:
            weights[group]=weights.get(group,0)+max(0,factor)*weight
    total=sum(weights.values())
    assert total>.999, (vertex.index,total)
    for group,weight in weights.items():
        if weight>1e-7:
            stitches.vertex_groups[groups[group]].add([vertex.index],weight/total,"REPLACE")
            used_bones.add(groups[group])
    weight_errors.append(abs(total-1))
stitches.parent=rig
modifier=stitches.modifiers.new("Same existing teddy skin","ARMATURE")
modifier.object=rig
new_mesh.calc_loop_triangles()
added_triangles=len(new_mesh.loop_triangles)
bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True)
stitches.select_set(True)
bpy.context.view_layer.objects.active=mesh
bpy.ops.object.join()
assert len(mesh.data.vertices)==original_count+len(vertices)
assert all((v.co-original_vertices[i]).length<1e-7 for i,v in enumerate(mesh.data.vertices[:original_count]))
assert all([(g.group,g.weight) for g in v.groups]==original_weights[i] for i,v in enumerate(mesh.data.vertices[:original_count]))
assert [tuple(p.vertices) for p in mesh.data.polygons[:len(original_polygons)]]==original_polygons
for name,uvs in original_uvs.items():
    assert [tuple(item.uv) for item in mesh.data.uv_layers[name].data[:len(uvs)]]==uvs
assert [b.name for b in rig.data.bones]==[b["name"] for b in bone_snapshot]
rig.data.pose_position="POSE"
body_checks=[]
for (name,frame),expected in samples.items():
    rig.animation_data.action=bpy.data.actions[name]
    scene.frame_set(frame)
    actual=evaluate_body(original_count)
    error=max((a-b).length for a,b in zip(actual,expected))
    assert error<.000002, (name,frame,error)
    body_checks.append({"clip":name,"frame":frame,"max_original_body_deformation_error_m":error,"passed":True})


def export(path,bake):
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={"ARMATURE","MESH"},
        add_leaf_bones=False,bake_anim=bake,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0,axis_forward="-Y",axis_up="Z",apply_unit_scale=True,mesh_smooth_type="FACE")


rig.animation_data.action=bpy.data.actions["Idle"]
scene.frame_set(1)
rig.data.pose_position="REST"
export(OUT/"Teddy_Parity.fbx",False)
rig.data.pose_position="POSE"
clips=[]
for name,count in CLIPS.items():
    rig.animation_data.action=bpy.data.actions[name]
    scene.frame_start=1
    scene.frame_end=count
    scene.frame_set(1)
    path=OUT/("Teddy_Parity_"+name+".fbx")
    export(path,True)
    clips.append({"name":name,"frames":count,"fps":30,"file":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
rig.animation_data.action=bpy.data.actions["Idle"]
scene.frame_end=90
scene.frame_set(1)

# Read the static-skin FBX back: same 16 bones and hierarchy, mesh + three slots.
before=set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(OUT/"Teddy_Parity.fbx"),use_anim=False)
loaded=list(set(bpy.data.objects)-before)
new_rig=next(o for o in loaded if o.type=="ARMATURE")
new_body=next(o for o in loaded if o.type=="MESH")
loaded_bones=[{"name":b.name,"parent":b.parent.name if b.parent else None} for b in new_rig.data.bones]
assert loaded_bones==[{"name":b["name"],"parent":b["parent"]} for b in bone_snapshot]
assert len(new_body.material_slots)==3
new_body.data.calc_loop_triangles()
mesh.data.calc_loop_triangles()
assert len(new_body.data.loop_triangles)==len(mesh.data.loop_triangles)
head_error=max((new_rig.data.bones[b["name"]].head_local-Vector(b["head_local_m"])).length for b in bone_snapshot)
assert head_error<.00001,head_error
roundtrip={"passed":True,"bone_count":len(new_rig.data.bones),"same_bone_names_and_hierarchy":True,
           "max_bind_bone_head_error_m":head_error,"triangles":len(new_body.data.loop_triangles),
           "material_slots":[s.material.name.split(".")[0] for s in new_body.material_slots]}
for obj in loaded:
    bpy.data.objects.remove(obj,do_unlink=True)

assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
manifest={
    "owner":OWNER,"status":"verified_skin_and_clips_ready_for_unreal",
    "source":str(SOURCE.relative_to(ROOT)),"source_sha256_before":source_hash,"source_sha256_after":source_hash,
    "provenance":"Original local seam/thread geometry added to the preserved CC0-derived adapted teddy. Existing source mesh, rig, UVs, weights and clips retained.",
    "generator":"tools/make_parity_teddy.py","blender_version":bpy.app.version_string,
    "mesh_file":"Teddy_Parity.fbx","mesh_sha256":hashlib.sha256((OUT/"Teddy_Parity.fbx").read_bytes()).hexdigest(),
    "source_body_vertices":original_count,"added_vertices":len(vertices),"added_triangles":added_triangles,
    "total_triangles":len(mesh.data.loop_triangles),"total_vertices":len(mesh.data.vertices),
    "source_body_vertices_uvs_weights_unchanged":True,"bind_bones":bone_snapshot,
    "added_geometry_weighting":"Nearest source triangle barycentric interpolation of existing skin weights; no new bones.",
    "added_geometry_influencing_bones":sorted(used_bones),"maximum_weight_normalization_error":max(weight_errors),
    "material_slots":[s.material.name for s in mesh.material_slots],
    "material_guidance":{"Material_0":"Assign current tuned teddy cloth material.","SeamDark":"Near-black warm neutral, roughness .98; not emissive.","StitchThread":"Desaturated worn tan thread, roughness .87, low specular. About 1.5-2.1 cm diameter at full-size boss."},
    "stitches":stitch_records,"clips":clips,"original_body_pose_checks":body_checks,"fbx_roundtrip":roundtrip,
    "unreal_import_guidance":"Import Teddy_Parity.fbx as a NEW SkeletalMesh using the existing encounter teddy Skeleton. Import materials/textures/animations false. Preserve original physics asset and six runtime clips. Map material slots by name. Reopen and render all active poses.",
    "limits":"Local Blender source and FBX skeleton verified. Compatibility with the saved Unreal Skeleton, slot overrides, runtime animation and silhouette/visual parity still requires integration verification.",
}
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")

# Save the editable adaptation before adding the non-exported preview studio.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"Teddy_Parity.blend"))
world=bpy.data.worlds.new("Seam preview studio")
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.07,.11,.12,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.45
scene.world=world
for name,loc,energy,size,color in [("Crown key",(-4,-4,9),1500,4,(.7,.93,1)),("Back rim",(4,3,7),1300,3,(.53,.82,.81)),("Face fill",(0,-6,4),350,3,(.66,.74,.8))]:
    data=bpy.data.lights.new(name,"AREA")
    data.energy=energy
    data.size=size
    data.color=color
    light=bpy.data.objects.new(name,data)
    scene.collection.objects.link(light)
    light.location=loc
    light.rotation_euler=(Vector((0,0,3))-light.location).to_track_quat("-Z","Y").to_euler()
ground_material=bpy.data.materials.new("Preview floor")
ground_material.diffuse_color=(.035,.06,.064,1)
bpy.ops.mesh.primitive_plane_add(size=30,location=(0,0,0))
ground=bpy.context.object
ground.name="Preview floor - not exported"
ground.data.materials.append(ground_material)
camera_data=bpy.data.cameras.new("Crown seam preview")
camera=bpy.data.objects.new("Crown seam preview",camera_data)
scene.collection.objects.link(camera)
scene.camera=camera
camera.location=(5,-7,9)
camera.rotation_euler=(Vector((0,-.35,3.5))-camera.location).to_track_quat("-Z","Y").to_euler()
camera_data.type="ORTHO"
camera_data.ortho_scale=4.8
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=24
scene.cycles.use_denoising=True
scene.render.resolution_x=1300
scene.render.resolution_y=1100
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="AgX"
scene.render.filepath=str(OUT/"stitch-crown-detail.png")
bpy.ops.render.render(write_still=True)
camera.location=(-6,-9,10)
camera.rotation_euler=(Vector((0,-.2,2.2))-camera.location).to_track_quat("-Z","Y").to_euler()
camera_data.ortho_scale=7
scene.render.resolution_x=1400
scene.render.resolution_y=1100
scene.render.filepath=str(OUT/"teddy-parity-overview.png")
bpy.ops.render.render(write_still=True)
print("PARITY_TEDDY_COMPLETE",json.dumps({"manifest":str(OUT/"manifest.json"),"triangles":manifest["total_triangles"],"added_triangles":added_triangles,"pose_checks":len(body_checks),"roundtrip":roundtrip}),flush=True)
