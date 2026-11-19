# Render-only stage: backdrop, lights, cameras. Not exported.

def look_at(ob, target):
    d = V(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def build_stage():
    sc = bpy.context.scene
    col = get_col('Stage')
    for ob in list(col.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    # backdrop floor
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=400)
    bmesh.ops.translate(bm, vec=(0, 0, Z_BOT - 0.11), verts=bm.verts)
    me = simple_mesh(bm, 'Backdrop')
    floor_mat = bpy.data.materials.get('Backdrop') or make_mat('Backdrop', '#D2CCC3', rough=0.95)
    add_obj('Backdrop', me, col, [floor_mat])

    def area(name, loc, target, energy, size, color=(1, 1, 1)):
        L = bpy.data.lights.new(name, 'AREA')
        L.energy = energy
        L.size = size
        L.color = color
        ob = bpy.data.objects.new(name, L)
        col.objects.link(ob)
        ob.location = loc
        look_at(ob, target)
        return ob
    area('Key', (-3.8, -4.6, 6.2), (0, 0, 0.3), 1900, 3.2, (1.0, 0.95, 0.88))
    area('Fill', (5.5, -3.5, 2.6), (0, 0, 0.4), 350, 6.0, (0.85, 0.92, 1.0))
    area('Rim', (1.5, 6.0, 4.5), (0, 0, 0.5), 1100, 3.0, (1.0, 0.95, 0.9))

    w = sc.world or bpy.data.worlds.new('World')
    sc.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    bg = None
    for n in w.node_tree.nodes:
        if n.type == 'BACKGROUND':
            bg = n
    if bg:
        bg.inputs[0].default_value = srgb('#DDD8D0')
        bg.inputs[1].default_value = 0.75

    cams = {}

    def cam(name, loc, target, lens=50):
        c = bpy.data.cameras.new(name)
        c.lens = lens
        c.sensor_width = 36
        ob = bpy.data.objects.new(name, c)
        col.objects.link(ob)
        ob.location = loc
        look_at(ob, target)
        cams[name] = ob
        return ob
    cam('Cam hero', (-1.25, -8.75, 3.3), (0.03, -0.28, 0.2), 50)
    cam('Cam close', (-1.35, -2.55, 1.25), (0.12, 0.12, 0.45), 50)
    cam('Cam legend', (0.0, -5.2, 1.6), (0.0, -1.8, -0.15), 50)
    cam('Cam caller', (-1.0, -1.6, 1.7), (0.72, 0.75, 1.25), 60)
    cam('Cam side', (-5.3, -1.9, 1.35), (0.32, 0.42, 0.80), 62)
    cam('Cam top', (0.0, -0.01, 7.6), (0, 0, 0), 40)
    cam('Cam back', (2.3, 8.0, 3.0), (0.0, 0.2, 0.3), 50)
    sc.camera = cams['Cam hero']
    return cams


def setup_render(engine='CYCLES', samples=64, res=(1600, 1000)):
    sc = bpy.context.scene
    sc.render.engine = engine
    if engine == 'CYCLES':
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        try:
            sc.cycles.device = 'GPU'
            cp = bpy.context.preferences.addons['cycles'].preferences
            cp.compute_device_type = 'METAL'
        except Exception:
            pass
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = 90
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass


def render(cam_name, path, frame=None):
    sc = bpy.context.scene
    if frame is not None:
        sc.frame_set(frame)
    sc.camera = bpy.data.objects[cam_name]
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
