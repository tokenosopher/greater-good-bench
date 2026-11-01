import bpy
import bmesh
import math
import os
import numpy as np
from mathutils import noise, Vector as Vec

WORK = os.getcwd()

def aim(obj, target_xyz, up='Z'):
    d = (Vec(target_xyz) - obj.location).normalized()
    obj.rotation_euler = d.to_track_quat('-Z', up).to_euler()
OSEP = os.sep

PI = math.pi

# ---------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------
def reset_scene():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    for it in list(bpy.data.meshes):
        if it.users == 0:
            bpy.data.meshes.remove(it)
    for it in list(bpy.data.materials):
        if it.users == 0:
            bpy.data.materials.remove(it)
    for it in list(bpy.data.cameras):
        if it.users == 0:
            bpy.data.cameras.remove(it)
    for it in list(bpy.data.lights):
        if it.users == 0:
            bpy.data.lights.remove(it)
    for it in list(bpy.data.images):
        if it.users == 0:
            bpy.data.images.remove(it)

def link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj

def mesh_from_pydata(name, verts, faces):
    m = bpy.data.meshes.new(name)
    m.from_pydata(verts, [], faces)
    m.update()
    bm = bmesh.new()
    bm.from_mesh(m)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(m)
    bm.free()
    m.update()
    for p in m.polygons:
        p.use_smooth = True
    return m

def make_cylinder(name, r, h, segments=160):
    verts = []
    faces = []
    bot = []
    top = []
    for s in range(segments):
        a = 2 * PI * s / segments
        x = r * math.cos(a)
        y = r * math.sin(a)
        bot.append(len(verts)); verts.append((x, y, -h / 2))
    for s in range(segments):
        a = 2 * PI * s / segments
        x = r * math.cos(a)
        y = r * math.sin(a)
        top.append(len(verts)); verts.append((x, y, h / 2))
    bc = len(verts); verts.append((0, 0, -h / 2))
    tc = len(verts); verts.append((0, 0, h / 2))
    for s in range(segments):
        s2 = (s + 1) % segments
        faces.append((bot[s], bot[s2], top[s2], top[s]))
    for s in range(segments):
        s2 = (s + 1) % segments
        faces.append((bot[s], bc, bot[s2]))
        faces.append((top[s], top[s2], tc))
    return mesh_from_pydata(name, verts, faces)

def cos_interp(p0, p1, t):
    tt = (1.0 - math.cos(t * PI)) * 0.5
    return p0 + (p1 - p0) * tt

def droplet_silhouette():
    # (r, z) control points, bottom -> top (pointed top teardrop)
    pts = [
        (0.00, -0.52),
        (0.16, -0.47),
        (0.30, -0.40),
        (0.40, -0.30),
        (0.46, -0.18),
        (0.47, -0.05),
        (0.45, 0.08),
        (0.40, 0.22),
        (0.33, 0.38),
        (0.24, 0.54),
        (0.15, 0.68),
        (0.07, 0.82),
        (0.00, 1.02),
    ]
    samples = []
    div = 7
    for i in range(len(pts) - 1):
        r0, z0 = pts[i]
        r1, z1 = pts[i + 1]
        for k in range(div):
            t = k / div
            rr = cos_interp(r0, r1, t)
            zz = z0 + (z1 - z0) * t
            samples.append((rr, zz))
    samples.append((0.0, 1.02))
    return samples

def make_droplet(name, segments=192):
    sil = droplet_silhouette()
    verts = []
    faces = []
    inner = sil[1:-1]  # rings with r>0
    verts.append((0, 0, sil[0][1]))  # bottom pole
    rings = []
    for (r, z) in inner:
        start = len(verts)
        idx = []
        for s in range(segments):
            a = 2 * PI * s / segments
            verts.append((r * math.cos(a), r * math.sin(a), z))
            idx.append(start + s)
        rings.append(idx)
    top_idx = len(verts); verts.append((0, 0, sil[-1][1]))  # top pole
    # bottom fan
    r0 = rings[0]
    for s in range(segments):
        s2 = (s + 1) % segments
        faces.append((0, r0[s], r0[s2]))
    for ri in range(len(rings) - 1):
        a = rings[ri]; b = rings[ri + 1]
        for s in range(segments):
            s2 = (s + 1) % segments
            faces.append((a[s], a[s2], b[s2], b[s]))
    rtop = rings[-1]
    for s in range(segments):
        s2 = (s + 1) % segments
        faces.append((rtop[s], top_idx, rtop[s2]))
    return mesh_from_pydata(name, verts, faces)

# ---------------------------------------------------------------
# Materials / world helpers
# ---------------------------------------------------------------
def new_material(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m

def principled(m):
    nt = m.node_tree
    n = nt.nodes.get('Principled BSDF')
    if n is None:
        n = nt.nodes.new('ShaderNodeBsdfPrincipled')
    return n

def set_socket(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value

def image_node(m, img, data=False):
    nt = m.node_tree
    tn = nt.nodes.new('ShaderNodeTexImage')
    tn.image = img
    if data:
        img.colorspace_settings.name = 'Non-Color'
    return tn

# ---------------------------------------------------------------
# Texture generation (procedural Earth)
# ---------------------------------------------------------------
def ramp(v, stops, cols):
    v = np.clip(v, stops[0], stops[-1])
    out = np.zeros(v.shape + (3,), dtype=np.float32)
    for c in range(3):
        ys = [cols[i][c] for i in range(len(cols))]
        out[..., c] = np.interp(v, stops, ys)
    return out

def save_image(img, arr, path):
    H, W = arr.shape[0], arr.shape[1]
    if arr.ndim == 2:
        flat = np.zeros((H, W, 4), dtype=np.float32)
        flat[..., 0] = arr
        flat[..., 1] = arr
        flat[..., 2] = arr
        flat[..., 3] = 1.0
    else:
        flat = np.ones((H, W, 4), dtype=np.float32)
        flat[..., :3] = arr
    img.pixels.foreach_set(flat.ravel())
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    return img

def generate_earth_textures(W=1024, H=512, land_frac=0.31):
    noise.seed_set(1234)
    us = np.linspace(0, 1, W, endpoint=False)
    vs = np.linspace(0, 1, H, endpoint=False)
    lat = (0.5 - vs) * PI  # image top row = north pole
    ct = np.cos(lat)
    st = np.sin(lat)
    e = np.zeros((H, W), dtype=np.float32)
    d = np.zeros((H, W), dtype=np.float32)
    for j in range(H):
        cj = ct[j]; sj = st[j]
        for i in range(W):
            phi = us[i] * 2 * PI
            x = cj * math.cos(phi)
            y = cj * math.sin(phi)
            z = sj
            e[j, i] = noise.fractal((x, y, z), 0.55, 2.0, 6, noise_basis='PERLIN_ORIGINAL')
            d[j, i] = noise.turbulence((x * 3, y * 3, z * 3), 5, False,
                                       noise_basis='PERLIN_ORIGINAL', amplitude_scale=0.5, frequency_scale=2.0)
    field = e + 0.35 * d
    t = float(np.percentile(field, 100 * (1 - land_frac)))
    height = field - t  # >0 = land, <0 = ocean

    abslat = np.abs(lat)[:, None]
    ice = np.clip((abslat - 1.02) / 0.28, 0, 1)
    snow = np.clip((field - (t + 0.5)) / 0.25, 0, 1)

    land = height > 0
    ocean = ~land

    color = np.zeros((H, W, 3), dtype=np.float32)
    rough = np.zeros((H, W), dtype=np.float32)

    # ----- ocean -----
    depth = np.clip(-height[ocean] / 0.55, 0, 1)
    col_o = ramp(depth,
                 [0.0, 0.25, 0.6, 1.0],
                 [(0.16, 0.40, 0.52),   # coastal
                  (0.06, 0.23, 0.40),   # shelf
                  (0.02, 0.13, 0.27),   # deep
                  (0.008, 0.06, 0.16)])  # abyss
    color[ocean] = col_o
    rough[ocean] = 0.05 + 0.12 * (1.0 - depth) ** 2

    # ----- land -----
    elev = np.clip(height[land] / 0.6, 0, 1)
    col_l = ramp(elev,
                 [0.0, 0.12, 0.3, 0.5, 0.75, 1.0],
                 [(0.48, 0.55, 0.30),   # coastal lowland
                  (0.26, 0.43, 0.20),   # vegetation
                  (0.11, 0.30, 0.15),   # forest
                  (0.36, 0.38, 0.24),   # highland
                  (0.45, 0.36, 0.22),   # rock/tan
                  (0.52, 0.49, 0.45)])  # gray rock
    color[land] = col_l
    rough[land] = 0.5 + 0.3 * elev

    # ----- snow (land high altitude) -----
    snow_c = np.array([0.93, 0.94, 0.96], dtype=np.float32)
    color = color * (1 - snow[..., None]) + snow_c * snow[..., None]
    rough = rough * (1 - snow) + 0.15 * snow

    # ----- polar ice -----
    ice_c = np.array([0.86, 0.90, 0.95], dtype=np.float32)
    color = color * (1 - ice[..., None]) + ice_c * ice[..., None]
    rough = rough * (1 - ice) + 0.06 * ice

    print("land_fraction", float(land.mean()), "threshold t", t)
    return color, rough

def build_textures():
    color, rough = generate_earth_textures()
    cimg = bpy.data.images.new('earth_color', color.shape[1], color.shape[0])
    rimg = bpy.data.images.new('earth_rough', rough.shape[1], rough.shape[0])
    cpath = os.path.join(WORK, 'texture_earth_color.png')
    rpath = os.path.join(WORK, 'texture_earth_rough.png')
    save_image(cimg, color, cpath)
    save_image(rimg, rough, rpath)
    cimg.colorspace_settings.name = 'sRGB'
    rimg.colorspace_settings.name = 'Non-Color'
    return cimg, rimg

# ---------------------------------------------------------------
# Build the whole scene
# ---------------------------------------------------------------
def build():
    reset_scene()
    scene = bpy.context.scene

    cimg, rimg = build_textures()

    # ------------------- world / sky -------------------
    world = scene.world
    world.use_nodes = True
    wnt = world.node_tree
    wnt.nodes.clear()
    wout = wnt.nodes.new('ShaderNodeOutputWorld')
    wbg = wnt.nodes.new('ShaderNodeBackground')
    wsky = wnt.nodes.new('ShaderNodeTexSky')
    wsky.sky_type = 'PREETHAM'
    wsky.sun_elevation = 0.35
    wsky.sun_rotation = 2.2
    wsky.sun_intensity = 1.0
    wbg.inputs['Strength'].default_value = 1.0
    wnt.links.new(wsky.outputs['Color'], wbg.inputs['Color'])
    wnt.links.new(wbg.outputs['Background'], wout.inputs['Surface'])

    # ------------------- materials -------------------
    # stone (dark base + light basin)
    mat_stone_dark = new_material('StoneDark')
    b = principled(mat_stone_dark)
    set_socket(b, 'Base Color', (0.34, 0.30, 0.26, 1.0))
    set_socket(b, 'Roughness', 0.55)
    set_socket(b, 'Specular IOR Level', 0.2)

    mat_stone_light = new_material('StoneLight')
    b = principled(mat_stone_light)
    set_socket(b, 'Base Color', (0.60, 0.53, 0.44, 1.0))
    set_socket(b, 'Roughness', 0.5)
    set_socket(b, 'Specular IOR Level', 0.22)

    # water in the basin
    mat_water = new_material('Water')
    b = principled(mat_water)
    set_socket(b, 'Base Color', (0.002, 0.009, 0.02, 1.0))
    set_socket(b, 'Roughness', 0.03)
    set_socket(b, 'IOR', 1.33)
    set_socket(b, 'Specular IOR Level', 1.0)
    wnt2 = mat_water.node_tree
    wtexcoord = wnt2.nodes.new('ShaderNodeTexCoord')
    wwave = wnt2.nodes.new('ShaderNodeTexWave')
    wwave.wave_type = 'RINGS'
    wwave.inputs['Scale'].default_value = 4.0
    wwave.inputs['Detail'].default_value = 3.0
    wbump = wnt2.nodes.new('ShaderNodeBump')
    wbump.inputs['Strength'].default_value = 0.015
    wbump.inputs['Distance'].default_value = 1.0
    wnt2.links.new(wtexcoord.outputs['Object'], wwave.inputs['Vector'])
    wnt2.links.new(wwave.outputs['Color'], wbump.inputs['Height'])
    wnt2.links.new(wbump.outputs['Normal'], b.inputs['Normal'])

    # glass droplet
    mat_glass = new_material('GlassDrop')
    b = principled(mat_glass)
    set_socket(b, 'Base Color', (1.0, 1.0, 1.0, 1.0))
    set_socket(b, 'Roughness', 0.01)
    set_socket(b, 'IOR', 1.33)
    set_socket(b, 'Transmission Weight', 1.0)
    set_socket(b, 'Metallic', 0.0)
    set_socket(b, 'Specular IOR Level', 0.8)

    # earth
    mat_earth = new_material('Earth')
    b = principled(mat_earth)
    set_socket(b, 'Base Color', (1, 1, 1, 1))
    set_socket(b, 'Metallic', 0.0)
    set_socket(b, 'Roughness', 0.7)
    set_socket(b, 'Specular IOR Level', 0.3)
    ent = mat_earth.node_tree
    cnode = image_node(mat_earth, cimg, data=False)
    rnode = image_node(mat_earth, rimg, data=True)
    ent.links.new(cnode.outputs['Color'], b.inputs['Base Color'])
    ent.links.new(rnode.outputs['Color'], b.inputs['Roughness'])

    # ------------------- geometry -------------------
    # pedestal base
    cyl = make_cylinder('PlinthBase', 3.0, 0.4, 160)
    o = bpy.data.objects.new('PlinthBase', cyl)
    link(o); o.location = (0, 0, 0.2); o.data.materials.append(mat_stone_dark)

    # column
    cyl = make_cylinder('Column', 1.8, 1.6, 160)
    o = bpy.data.objects.new('Column', cyl)
    link(o); o.location = (0, 0, 1.2); o.data.materials.append(mat_stone_light)

    # basin
    cyl = make_cylinder('Basin', 5.6, 0.55, 200)
    o = bpy.data.objects.new('Basin', cyl)
    link(o); o.location = (0, 0, 2.15); o.data.materials.append(mat_stone_light)

    # water disc
    cyl = make_cylinder('WaterDisc', 5.45, 0.06, 200)
    o = bpy.data.objects.new('WaterDisc', cyl)
    link(o); o.location = (0, 0, 2.34); o.data.materials.append(mat_water)

    # droplet
    dm = make_droplet('Droplet', 192)
    drop = bpy.data.objects.new('Droplet', dm)
    link(drop); drop.location = (0, 0, 2.92); drop.data.materials.append(mat_glass)

    # earth inside droplet
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = None
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=0.32,
                                         location=(0, 0, 2.80))
    earth = bpy.context.active_object
    earth.name = 'Earth'
    earth.data.materials.append(mat_earth)
    earth.rotation_euler = (0.42, 0.0, -0.35)

    # ------------------- ground plane -------------------
    mat_ground = new_material('Ground')
    b = principled(mat_ground)
    set_socket(b, 'Base Color', (0.53, 0.48, 0.40, 1.0))
    set_socket(b, 'Roughness', 0.9)
    set_socket(b, 'Specular IOR Level', 0.2)
    gt = mat_ground.node_tree
    gtc = gt.nodes.new('ShaderNodeTexCoord')
    gnoise = gt.nodes.new('ShaderNodeTexNoise')
    gnoise.inputs['Scale'].default_value = 0.6
    gbump = gt.nodes.new('ShaderNodeBump')
    gbump.inputs['Strength'].default_value = 0.15
    gt.links.new(gtc.outputs['Object'], gnoise.inputs['Vector'])
    gt.links.new(gnoise.outputs['Color'], gbump.inputs['Height'])
    gt.links.new(gbump.outputs['Normal'], b.inputs['Normal'])
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = 'Ground'
    ground.data.materials.append(mat_ground)

    # ------------------- lights -------------------
    # key sun (warm) from front-left-upper
    sun = bpy.data.lights.new('Sun', 'SUN')
    sun.energy = 4.5
    sun.color = (1.0, 0.87, 0.68)
    sun_obj = bpy.data.objects.new('Sun', sun)
    link(sun_obj)
    sun_obj.location = (3.5, 9.5, 6.5)
    aim(sun_obj, (0, 0, 2.0), 'Y')

    # cool rim/fill sun from behind-right
    fill = bpy.data.lights.new('Fill', 'SUN')
    fill.energy = 0.6
    fill.color = (0.65, 0.75, 0.95)
    fill_obj = bpy.data.objects.new('Fill', fill)
    link(fill_obj)
    fill_obj.location = (-6.0, -3.0, 6.0)
    aim(fill_obj, (0, 0, 2.0), 'Y')

    # ------------------- camera -------------------
    cam = bpy.data.cameras.new('Cam')
    cam.lens = 48
    cam.dof.use_dof = True
    cam.dof.aperture_fstop = 4.0
    cam_obj = bpy.data.objects.new('Camera', cam)
    link(cam_obj)
    cam_obj.location = (5.2, 8.6, 2.8)
    scene.camera = cam_obj

    target = bpy.data.objects.new('Target', None)
    link(target)
    target.location = (0.3, 0, 2.8)
    cam.dof.focus_object = target
    aim(cam_obj, (0.3, 0, 2.8), 'Z')

    # ------------------- render settings -------------------
    scene.render.engine = 'CYCLES'
    cyc = scene.cycles
    cyc.device = 'GPU'
    cyc.samples = 64
    cyc.use_denoising = True
    cyc.denoiser = 'OPENIMAGEDENOISE'
    cyc.max_bounces = 12
    cyc.caustics_reflective = False
    cyc.caustics_refractive = False

    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.image_settings.file_format = 'JPEG'
    scene.render.image_settings.quality = 92

    outdir = os.path.join(WORK, 'output')
    os.makedirs(outdir, exist_ok=True)
    scene.render.filepath = os.path.join(WORK, 'preview.jpg')
    bpy.ops.render.render(write_still=True)

    print("BUILD DONE")

if __name__ == '__main__':
    build()