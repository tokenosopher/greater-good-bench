import bpy
import os
from mathutils import Vector

WORK = os.getcwd()
OUT = os.path.join(WORK, 'output')
os.makedirs(OUT, exist_ok=True)

exec(open(os.path.join(WORK, 'build.py')).read())
build()

scene = bpy.context.scene
cam_obj = scene.camera
cam = cam_obj.data
target = bpy.data.objects['Target']

def aim(obj, t, up='Z'):
    d = (Vector(t) - obj.location).normalized()
    obj.rotation_euler = d.to_track_quat('-Z', up).to_euler()

# render settings
scene.render.engine = 'CYCLES'
cyc = scene.cycles
cyc.device = 'GPU'
cyc.samples = 256
cyc.use_denoising = True
cyc.denoiser = 'OPENIMAGEDENOISE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 95

shots = [
    ('hero', (5.2, 8.6, 2.8), (0.3, 0, 2.8), 48),
    ('closeup', (1.5, 3.0, 2.55), (0.0, 0, 2.8), 70),
    ('wide', (7.0, 9.0, 4.0), (0.3, 0, 2.0), 35),
]

cam.dof.use_dof = True
cam.dof.aperture_fstop = 4.0

for name, pos, t, lens in shots:
    cam_obj.location = pos
    cam.lens = lens
    target.location = t
    aim(cam_obj, t, 'Z')
    cam.dof.focus_object = target
    scene.render.filepath = os.path.join(OUT, name + '.jpg')
    bpy.ops.render.render(write_still=True)
    print("rendered", name)

# ------- export GLB (monument only, no ground/lights/camera) -------
bpy.ops.object.select_all(action='DESELECT')
for nm in ['PlinthBase', 'Column', 'Basin', 'WaterDisc', 'Droplet', 'Earth']:
    bpy.data.objects[nm].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['Droplet']

glb = os.path.join(OUT, 'the_world_in_a_drop.glb')
bpy.ops.export_scene.gltf(
    filepath=glb,
    export_format='GLB',
    use_selection=True,
    export_apply=False,
)
print("exported glb")

# ------- report sizes -------
report = []
for f in sorted(os.listdir(OUT)):
    p = os.path.join(OUT, f)
    report.append((f, os.path.getsize(p)))
print("FILES:", report)
with open(os.path.join(OUT, '_sizes.txt'), 'w') as fh:
    for f, s in report:
        fh.write(f"{f} {s}\n")
print("DONE")