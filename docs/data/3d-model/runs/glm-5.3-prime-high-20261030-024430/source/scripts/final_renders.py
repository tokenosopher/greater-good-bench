# Final renders: hero, close-up, pale-blue-dot
import bpy, numpy as np, os, math
from mathutils import Vector

BASE = '~/dev/art-crit-runs/2026-10-30-024430-3d-model/glm-5.3-prime-high-20261030-024430/work'
OUT = os.path.join(BASE, 'output')
REN = os.path.join(BASE, 'renders')
os.makedirs(OUT, exist_ok=True)

sc = bpy.context.scene
cam = bpy.data.objects['ShotCam']
target = bpy.data.objects['CamTarget']
world = sc.world

HERO = dict(cam_loc=(-3.0, -7.0, 1.6), target=(0.15, 0.4, 0.3), lens=35.0)

def set_shot(cam_loc, tgt, lens):
    cam.location = cam_loc
    target.location = tgt
    cam.data.lens = lens
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    deps.update()

def do_render(path, samples=128, res=(1920, 1080)):
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.cycles.samples = samples
    sc.render.filepath = path
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = 93
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path)
    img.reload()
    w, h = img.size
    px = np.array(img.pixels[:]).reshape(h, w, 4)[..., :3]
    lum = px.mean(axis=2)
    stats = {'mean': round(float(lum.mean()), 4), 'max': round(float(lum.max()), 3)}
    ys, xs = np.where(lum > 0.25)
    if len(ys):
        stats['bright_bbox'] = [int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())]
        stats['bright_count'] = int(len(ys))
    bpy.data.images.remove(img)
    return stats

# ---------------- A: hero
set_shot(HERO['cam_loc'], HERO['target'], HERO['lens'])
print('A hero:', do_render(os.path.join(OUT, 'render_hero.jpg')))

# ---------------- B: Earth close-up
set_shot((-1.23, -2.88, 0.66), (0.35, 0.30, 0.25), 55.0)
print('B closeup:', do_render(os.path.join(OUT, 'render_closeup.jpg')))

# ---------------- C: pale blue dot from afar (world env stars)
set_shot((-23.1, -53.9, 12.3), (0, 0, 0), 85.0)
stars = bpy.data.objects['Starfield']
stars.hide_render = True
# world -> environment texture with starfield
nt = world.node_tree
nodes, links = nt.nodes, nt.links
for n in list(nodes):
    if n.type in ('TEX_ENVIRONMENT',):
        nodes.remove(n)
env = nodes.new('ShaderNodeTexEnvironment')
env.image = bpy.data.images['starfield']
bg = [n for n in nodes if n.type == 'BACKGROUND'][0]
links.new(env.outputs['Color'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = 1.0
print('C dot:', do_render(os.path.join(OUT, 'render_dot.jpg')))
# restore world
links.remove(bg.inputs['Color'].links[0])
bg.inputs['Color'].default_value = (0.001, 0.001, 0.003, 1.0)
nodes.remove(env)
stars.hide_render = False
set_shot(HERO['cam_loc'], HERO['target'], HERO['lens'])

result = {'done': True}
