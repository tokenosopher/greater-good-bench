# Build "One Home - Pale Blue Dot" scene
import bpy, os, math
from mathutils import Vector

BASE = '~/dev/art-crit-runs/2026-10-30-024430-3d-model/glm-5.3-prime-high-20261030-024430/work'
TEX = os.path.join(BASE, 'textures')

P = dict(
    earth_r=1.0,
    clouds_r=1.016,
    atmo_r=1.05,
    moon_r=0.30,
    moon_pos=(3.3, -0.5, 1.85),
    stars_r=10.0,
    cam_pos=(-3.0, -7.0, 1.6),
    cam_target=(0.15, 0.4, 0.3),
    cam_lens=35.0,
    plaque_ndc=(0.21, 0.34), plaque_dist=5.2,
    sun_dir=(0.60, -0.25, 0.60),
    sun_energy=5.0,
    fill_dir=(-0.5, 0.35, -0.25),
    fill_energy=0.22,
)

# ---------------------------------------------------------------- clean
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for m in list(bpy.data.materials):
    bpy.data.materials.remove(m, do_unlink=True)
for c in list(bpy.data.cameras):
    bpy.data.cameras.remove(c)
for l in list(bpy.data.lights):
    bpy.data.lights.remove(l, do_unlink=True)
for me in list(bpy.data.meshes):
    bpy.data.meshes.remove(me, do_unlink=True)
for c in list(bpy.data.curves):
    bpy.data.curves.remove(c, do_unlink=True)

def load_img(name):
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.load(os.path.join(TEX, name + '.png'))
    img.reload()
    return img

IMG = {n: load_img(n) for n in ['earth_diffuse', 'earth_rough', 'earth_clouds', 'moon_diffuse', 'starfield']}

# ---------------------------------------------------------------- helpers
def spherical_uvs(me, radius):
    """u = (lon+180)/360 with lon=atan2(y,x); v = (lat+90)/180, row0 = north."""
    uv = me.uv_layers[0] if me.uv_layers else me.uv_layers.new(name='Map')
    vpol = 0.9995 * radius
    lons, lats = [], []
    for v in me.vertices:
        lons.append(math.atan2(v.co.y, v.co.x))
        lats.append(math.asin(max(-1.0, min(1.0, v.co.z / radius))))
    pole = [abs(me.vertices[v.index].co.z) >= vpol for v in me.vertices]
    for f in me.polygons:
        ref_u = None
        for li in f.loop_indices:
            vi = me.loops[li].vertex_index
            if not pole[vi]:
                ref_u = (lons[vi] + math.pi) / (2.0 * math.pi)
        us = []
        for li in f.loop_indices:
            vi = me.loops[li].vertex_index
            u = (lons[vi] + math.pi) / (2.0 * math.pi)
            if pole[vi] and ref_u is not None:
                u = ref_u
            us.append(u)
        # fix longitude wrap inside a face
        if max(us) - min(us) > 0.5:
            us = [u + 1.0 if u < 0.5 else u for u in us]
        for li, u in zip(f.loop_indices, us):
            vi = me.loops[li].vertex_index
            vv = (math.pi / 2 - lats[vi]) / math.pi  # pixels row0 = image bottom = north
            uv.data[li].uv = (u, vv)

def add_sphere(name, radius, segs, rings, loc):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=radius, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.name = name
    spherical_uvs(ob.data, radius)
    bpy.ops.object.shade_smooth()
    return ob

def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m

def tex_node(nt, image, non_color=False):
    n = nt.nodes.new('ShaderNodeTexImage')
    n.image = image
    n.interpolation = 'Smart'
    if non_color:
        n.image.colorspace_settings.name = 'Non-Color'
    return n

def set_blended(m):
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        try:
            m.blend_method = 'BLEND'
        except Exception:
            pass

# ---------------------------------------------------------------- Earth
earth = add_sphere('Earth', P['earth_r'], 128, 64, (0, 0, 0))
matE = new_mat('Earth')
nt = matE.node_tree
bsdf = nt.nodes['Principled BSDF']
diff = tex_node(nt, IMG['earth_diffuse'])
rgh = tex_node(nt, IMG['earth_rough'], non_color=True)
nt.links.new(diff.outputs['Color'], bsdf.inputs['Base Color'])
nt.links.new(rgh.outputs['Color'], bsdf.inputs['Roughness'])
bsdf.inputs['Specular IOR Level'].default_value = 0.55
earth.data.materials.append(matE)

# ---------------------------------------------------------------- Clouds
clouds = add_sphere('Clouds', P['clouds_r'], 128, 64, (0, 0, 0))
matC = new_mat('Clouds')
nt = matC.node_tree
bsdf = nt.nodes['Principled BSDF']
ct = tex_node(nt, IMG['earth_clouds'])
nt.links.new(ct.outputs['Alpha'], bsdf.inputs['Alpha'])
bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)
bsdf.inputs['Roughness'].default_value = 0.9
set_blended(matC)
clouds.data.materials.append(matC)
clouds.visible_shadow = True

# ---------------------------------------------------------------- Atmosphere
atmo = add_sphere('Atmosphere', P['atmo_r'], 96, 48, (0, 0, 0))
matA = new_mat('Atmosphere')
nt = matA.node_tree
bsdf = nt.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.35, 0.60, 1.0, 1.0)
bsdf.inputs['Alpha'].default_value = 0.07
bsdf.inputs['Roughness'].default_value = 1.0
bsdf.inputs['Emission Color'].default_value = (0.10, 0.28, 0.65, 1.0)
bsdf.inputs['Emission Strength'].default_value = 0.8
set_blended(matA)
atmo.data.materials.append(matA)
atmo.visible_shadow = False

# ---------------------------------------------------------------- Moon
moon = add_sphere('Moon', P['moon_r'], 96, 48, P['moon_pos'])
matM = new_mat('Moon')
nt = matM.node_tree
bsdf = nt.nodes['Principled BSDF']
md = tex_node(nt, IMG['moon_diffuse'])
nt.links.new(md.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Roughness'].default_value = 0.95
moon.data.materials.append(matM)

# ---------------------------------------------------------------- Starfield
stars = add_sphere('Starfield', P['stars_r'], 64, 32, (0, 0, 0))
bpy.context.view_layer.objects.active = stars
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.flip_normals()
bpy.ops.object.mode_set(mode='OBJECT')
matS = new_mat('Starfield')
nt = matS.node_tree
nt.nodes.remove(nt.nodes['Principled BSDF'])
emis = nt.nodes.new('ShaderNodeEmission')
so = nt.nodes['Material Output']
st = tex_node(nt, IMG['starfield'])
nt.links.new(st.outputs['Color'], emis.inputs['Color'])
emis.inputs['Strength'].default_value = 3.0
nt.links.new(emis.outputs['Emission'], so.inputs['Surface'])
matS.use_backface_culling = False
if hasattr(matS, 'shadow_method'):
    matS.shadow_method = 'NONE'
stars.data.materials.append(matS)
stars.visible_shadow = False

# ---------------------------------------------------------------- Lights
sun_ob = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
sun_ob.data.energy = P['sun_energy']
sun_ob.data.color = (1.0, 0.97, 0.92)
sun_ob.data.angle = 0.0093  # ~0.53 deg
S = Vector(P['sun_dir']).normalized()
sun_ob.rotation_euler = S.to_track_quat('Z', 'Y').to_euler()
bpy.context.collection.objects.link(sun_ob)

fill_ob = bpy.data.objects.new('Earthshine', bpy.data.lights.new('Earthshine', 'SUN'))
fill_ob.data.energy = P['fill_energy']
fill_ob.data.color = (0.4, 0.55, 0.85)
F = Vector(P['fill_dir']).normalized()
fill_ob.rotation_euler = F.to_track_quat('Z', 'Y').to_euler()
bpy.context.collection.objects.link(fill_ob)

# ---------------------------------------------------------------- Camera
cam_data = bpy.data.cameras.new('ShotCam')
cam_data.lens = P['cam_lens']
cam = bpy.data.objects.new('ShotCam', cam_data)
cam.location = P['cam_pos']
bpy.context.collection.objects.link(cam)
target = bpy.data.objects.new('CamTarget', None)
target.location = P['cam_target']
bpy.context.collection.objects.link(target)
con = cam.constraints.new(type='TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
bpy.context.scene.camera = cam

# ---------------------------------------------------------------- Plaque
cam_pos = Vector(P['cam_pos'])
# camera rotation: look from cam_pos toward cam_target (camera -Z along view, Y up)
v_view = (Vector(P['cam_target']) - cam_pos).normalized()
cam_rot = v_view.to_track_quat('-Z', 'Y').to_matrix()
# plaque center: along camera ray through plaque_ndc at plaque_dist
tan_h = 18.0 / P['cam_lens']
tan_v = 12.0 / P['cam_lens']
xn, yn = P['plaque_ndc']
d_cam = Vector(((xn * 2 - 1) * tan_h, (yn * 2 - 1) * tan_v, -1.0)).normalized()
d_w = (cam_rot @ d_cam).normalized()
plaque_pos = cam_pos + d_w * P['plaque_dist']
root = bpy.data.objects.new('Plaque', None)
root.location = plaque_pos
q = (cam_pos - plaque_pos).normalized().to_track_quat('Z', 'Y')
root.rotation_euler = q.to_euler()
bpy.context.collection.objects.link(root)

# slab
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
slab = bpy.context.active_object
slab.name = 'PlaqueSlab'
slab.data.name = 'PlaqueSlab'
slab.scale = (0.85, 0.575, 0.026)
bpy.ops.object.transform_apply(scale=True)
matP = new_mat('PlaqueSlab')
nt = matP.node_tree
b = nt.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (0.030, 0.034, 0.045, 1.0)
b.inputs['Roughness'].default_value = 0.45
b.inputs['Metallic'].default_value = 0.2
b.inputs['Emission Color'].default_value = (0.02, 0.03, 0.06, 1.0)
b.inputs['Emission Strength'].default_value = 1.0
slab.data.materials.append(matP)
slab.parent = root

matG = new_mat('Gold')
nt = matG.node_tree
g = nt.nodes['Principled BSDF']
g.inputs['Base Color'].default_value = (1.0, 0.78, 0.35, 1.0)
g.inputs['Metallic'].default_value = 1.0
g.inputs['Roughness'].default_value = 0.32
g.inputs['Emission Color'].default_value = (1.0, 0.72, 0.30, 1.0)
g.inputs['Emission Strength'].default_value = 0.5

def add_text(name, body, size, loc):
    curve = bpy.data.curves.new(name, type='FONT')
    curve.body = body
    curve.size = size
    curve.align_x = 'CENTER'
    curve.align_y = 'CENTER'
    curve.extrude = 0.006
    curve.bevel_depth = 0.0006
    curve.bevel_resolution = 1
    curve.space_character = 1.05
    t = bpy.data.objects.new(name, curve)
    t.location = loc
    t.parent = root
    t.data.materials.append(matG)
    bpy.context.collection.objects.link(t)
    return t

add_text('PlaqueTitle', 'ONE HOME', 0.20, (0, 0.40, 0.035))
add_text('PlaqueQuote', "That's here. That's home. That's us.", 0.085, (0, 0.08, 0.035))
add_text('PlaqueAttribution', '— Carl Sagan, Pale Blue Dot, 1994', 0.062, (0, -0.10, 0.035))
add_text('PlaqueFooter', '8.2 billion lives. No borders visible from here.', 0.053, (0, -0.26, 0.035))

# convert text to mesh for glTF
txt_objs = [o for o in (bpy.data.objects['PlaqueTitle'], bpy.data.objects['PlaqueQuote'],
                        bpy.data.objects['PlaqueAttribution'], bpy.data.objects['PlaqueFooter'])]
for o in txt_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = txt_objs[0]
bpy.ops.object.convert(target='MESH')
for o in txt_objs:
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass
    o.select_set(False)

# ---------------------------------------------------------------- World & render settings
world = bpy.context.scene.world or bpy.data.worlds.new('World')
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.001, 0.001, 0.003, 1.0)
bg.inputs[1].default_value = 1.0

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 96
scene.cycles.use_denoising = True
scene.cycles.transparent_max_bounces = 12
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 92

result = {'objects': [o.name for o in bpy.data.objects],
          'sun_dir': tuple(round(c, 3) for c in S),
          'camera': cam.name}
