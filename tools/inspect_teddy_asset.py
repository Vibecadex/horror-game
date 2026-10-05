"""Render the downloaded GLB for review; never write back to the source asset."""
import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(r"C:\Projects\to-deploy\horror-game")
ASSET = ROOT / "Assets/ThirdParty/HorrorTeddyBear/horror-teddy-bear-monster.glb"
OUTPUT = ROOT / "evidence/asset-research"
OUTPUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ASSET))
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
report = {
    "source": str(ASSET),
    "bounds_min": list(low),
    "bounds_max": list(high),
    "dimensions": list(high-low),
    "mesh_objects": [obj.name for obj in meshes],
    "armatures": [obj.name for obj in bpy.context.scene.objects if obj.type == "ARMATURE"],
    "actions": [action.name for action in bpy.data.actions],
    "images": [{"name": item.name, "size": list(item.size)} for item in bpy.data.images],
    "uv_layers": {obj.name: len(obj.data.uv_layers) for obj in meshes},
    "review_only": True,
    "unreal_import_verified": False,
}
(OUTPUT / "teddy-blender-inspection.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

center = Vector(((low.x+high.x)/2, (low.y+high.y)/2, low.z))
scale = 2.0 / (high.z-low.z)
for obj in meshes:
    for vertex in obj.data.vertices:
        vertex.co = (obj.matrix_world @ vertex.co - center) * scale
    obj.matrix_world.identity()

bpy.ops.mesh.primitive_plane_add(size=200)
floor = bpy.context.object
material = bpy.data.materials.new("Review floor")
material.diffuse_color = (0.06, 0.07, 0.085, 1)
floor.data.materials.append(material)

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 24
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world = bpy.data.worlds.new("Review world")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.20, 0.24, 1)
scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.45

for index, (location, energy, size) in enumerate([
    ((-3, -4, 5), 500, 4), ((4, -1, 3), 300, 3), ((0, 4, 5), 600, 3)
]):
    data = bpy.data.lights.new(f"Review light {index}", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector((0, 0, 1))-obj.location).to_track_quat("-Z", "Y").to_euler()

camera_data = bpy.data.cameras.new("Review camera")
camera_data.type = "ORTHO"
camera_data.ortho_scale = 2.9
camera = bpy.data.objects.new("Review camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
for label, location in [("front", (3, -6, 2.8)), ("reverse", (-3, 6, 2.8))]:
    camera.location = location
    camera.rotation_euler = (Vector((0, 0, 1))-camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(OUTPUT / f"teddy-{label}.png")
    bpy.ops.render.render(write_still=True)
print("TEDDY_INSPECTION " + json.dumps(report))
