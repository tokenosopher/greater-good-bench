"""Final renders + GLB export for PALE BLUE DOT."""
import bpy
import os
import math
from mathutils import Vector

ROOT = os.getcwd()
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

scene = bpy.context.scene
earth = bpy.data.objects["Earth"]
clouds = bpy.data.objects["Clouds"]
atmo = bpy.data.objects["Atmosphere"]
moon = bpy.data.objects["Moon"]

# hero camera (Earth portrait; moon is out of frame)
cam = bpy.data.objects["HeroCam"]
cam.location = (0.55, -5.00, 1.20)
cam.data.lens = 55
scene.camera = cam

scene.render.engine = "CYCLES"
scene.cycles.device = "GPU"
scene.cycles.samples = 96
scene.cycles.use_denoising = True
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.015
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 93
scene.render.filepath = os.path.join(OUT, "the_overview.jpg")

# ---------------- hero (moon just outside frame) ----------------
moon.hide_render = True
bpy.ops.render.render(write_still=True)
print("hero done", os.path.getsize(scene.render.filepath))

# ---------------- wide (Earth + Moon) ----------------
moon.hide_render = False
wide_data = bpy.data.cameras.new("WideCam")
wide_data.lens = 50
wide_data.sensor_width = 36
wide_data.clip_start = 0.05
wide_data.clip_end = 2000
wide = bpy.data.objects.new("WideCam", wide_data)
scene.collection.objects.link(wide)
wide.location = (0.4, -9.30, 2.50)
target = bpy.data.objects["Target"]
target.location = (0, 0, 0.10)
tc = wide.constraints.new("TRACK_TO")
tc.target = target
tc.track_axis = "TRACK_NEGATIVE_Z"
tc.up_axis = "UP_Y"
scene.camera = wide
scene.render.filepath = os.path.join(OUT, "the_blue_dot.jpg")
bpy.ops.render.render(write_still=True)
print("wide done", os.path.getsize(scene.render.filepath))

# ---------------- export ----------------
scene.camera = cam
for ob in bpy.data.objects:
    ob.select_set(False)
for ob in (earth, clouds, atmo, moon):
    ob.select_set(True)
bpy.context.view_layer.objects.active = earth
glb_path = os.path.join(OUT, "pale_blue_dot.glb")
bpy.ops.export_scene.gltf(
    filepath=glb_path,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
    export_draco_mesh_compression_enable=False,
    export_meshopt_compression_enable=False,
)
print("glb", os.path.getsize(glb_path))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "pale_blue_dot_final.blend"))
print("FINAL OK")
