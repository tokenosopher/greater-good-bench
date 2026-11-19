# Builds the model. Expects build_scene.py helpers in globals.

PERIOD = 24          # frames per compression
FPS = 44             # 24 frames / 44 fps = 0.545 s  ->  110 compressions a minute
DEPTH = 0.05         # compression depth (5 cm)

# plinth geometry
R_TOP, Z_TOP = 1.58, -0.015
R_BOT, Z_BOT = 2.16, -0.42
BAND_L = sqrt((R_BOT - R_TOP) ** 2 + (Z_TOP - Z_BOT) ** 2)
BAND_S = math.atan2(Z_TOP - Z_BOT, R_BOT - R_TOP)   # slope angle from horizontal


def build_materials():
    M = {}
    M['slate'] = make_mat('Slate', '#141922', rough=0.78)
    M['victim'] = make_mat('Bone', '#F1ECE2', rough=0.55)
    M['rescuer'] = make_mat('Coral', '#F0502F', rough=0.5)
    M['caller'] = make_mat('Blue', '#2F86E6', rough=0.5)
    M['aed'] = make_mat('AED Green', '#12A557', rough=0.45)
    M['white'] = make_mat('Letter White', '#F4EFE6', rough=0.6)
    M['pulse'] = make_mat('Pulse', '#F0502F', rough=0.5, emit='#FF5A36', emit_strength=1.6)
    M['phone'] = make_mat('Phone', '#0E1116', rough=0.3)
    M['screen'] = make_mat('Phone Screen', '#BFE3FF', rough=0.3, emit='#BFE3FF', emit_strength=1.2)
    return M


# ----------------------------------------------------------------- victim

def build_victim(col, M):
    bm = bmesh.new()
    sp = Spine(V((0.34, 0, 0.108)), V((-0.21, 0, 0.116)), V((0, -1, 0)))
    torso(bm, sp)
    hc = sp.N + sp.T * 0.15 + V((0, 0, -0.004))
    head(bm, hc, sp.T + V((0, 0.12, 0.0)), sp.R, neck_from=sp.at(0.97))
    # camera-side (right) arm: relaxed, a little away from the body, palm up
    S = sp.shoulder(+1) + V((0, 0, -0.01))
    arm(bm, S, V((0.345, -0.345, 0.04)), V((0, -1, -0.2)), V((1, -0.12, 0)), V((0, 0, 1)), thumb_side=-1)
    # far arm: flung up and out, leaving room for the rescuer's knees
    S = sp.shoulder(-1) + V((0, 0, -0.01))
    arm(bm, S, V((-0.55, 0.60, 0.04)), V((-0.2, 1, -0.3)), V((-0.8, 0.5, 0)), V((0, 0, 1)), thumb_side=-1)
    for side in (+1, -1):
        H = sp.hip(side)
        A = V((1.215, -0.17 * side, 0.052))
        leg(bm, H, A, V((0, 0, 1)), V((0.12, -0.55 * side, 0.83)), V((-1, 0, 0.1)))
    me = finalize(bm, 'Person')
    ob = add_obj('Person', me, col, [M['victim']])
    # chest height at the compression point
    top = max(v.co.z for v in me.vertices if abs(v.co.x) < 0.03 and abs(v.co.y) < 0.03)
    # shape key: the chest gives 5 cm under the hands
    ob.shape_key_add(name='Basis')
    sk = ob.shape_key_add(name='Compress')
    for v in me.vertices:
        c = v.co
        d = sqrt((c.x / 0.15) ** 2 + (c.y / 0.15) ** 2)
        w = exp(-d ** 4)
        zf = min(max((c.z - 0.07) / 0.09, 0.0), 1.0)
        zf = zf * zf * (3 - 2 * zf)
        dz = -(DEPTH + 0.002) * w * zf
        if dz < -1e-5:
            sk.data[v.index].co = V((c.x, c.y, c.z + dz))
    return ob, top


# ----------------------------------------------------------------- rescuer

def build_rescuer(col, M, chest_top):
    KNEE_Y, KNEE_Z = 0.27, 0.066
    sp = Spine(V((0, 0.42, 0.50)), V((0, -0.005, 0.868)), V((-1, 0, 0)), bend=-0.012)
    knee_piv = V((0, KNEE_Y, KNEE_Z))
    hip_piv = V((0, sp.hip(1).y, sp.hip(1).z))

    lower, thighs, upper = bmesh.new(), bmesh.new(), bmesh.new()
    for side in (+1, -1):
        H = sp.hip(side)
        K = V((-0.115 * side, KNEE_Y, KNEE_Z))
        A = V((-0.115 * side, KNEE_Y + SHIN, 0.047))
        limb(thighs, H, K, 0.092, 0.066, bulge=(0.3, 0.09))
        limb(lower, K, A, 0.066, 0.044, bulge=(0.3, 0.066))
        td = V((0.10 * -side * -1, 1, -0.02)).normalized()
        ellipsoid(lower, A + td * 0.075 + V((0, 0, 0.0)), X_AXIS * 0.05, td * 0.13, Z_AXIS * 0.043)
    torso(upper, sp)
    up = V((0, -0.80, 0.60)).normalized()
    head(upper, sp.N + up * 0.14, up, sp.R, neck_from=sp.at(0.97))
    # straight, locked arms; shoulders stacked directly over the hands
    hz = chest_top
    for side in (+1, -1):
        S = sp.shoulder(side)
        W = V((-0.026 * side, 0.03, hz + 0.088))
        limb(upper, S, S.lerp(W, 0.53), 0.058, 0.048)
        limb(upper, S.lerp(W, 0.53), W, 0.048, 0.037, bulge=(0.3, 0.05))
    # stacked hands, heel on the breastbone, fingers across the chest
    for k, (yaw, z) in enumerate(((-0.30, hz + 0.019), (0.30, hz + 0.048))):
        hd = V((sin(yaw), -cos(yaw), 0.0))
        sd = V((cos(yaw), sin(yaw), 0.0))
        c = V((0, 0.03, z)) + hd * 0.072
        ellipsoid(upper, c, sd * 0.048, hd * 0.098, Z_AXIS * 0.021)
    hand_pt = V((0, 0.0, hz))

    obs = {}
    for name, bm, piv in (('Rescuer legs', lower, None), ('Rescuer thighs', thighs, knee_piv), ('Rescuer body', upper, hip_piv)):
        me = finalize(bm, name)
        if piv is not None:
            me.transform(Matrix.Translation(-piv))
        obs[name] = add_obj(name, me, col, [M['rescuer']])

    e_knee = bpy.data.objects.new('Rescuer knee pivot', None)
    e_hip = bpy.data.objects.new('Rescuer hip pivot', None)
    for e in (e_knee, e_hip):
        e.empty_display_size = 0.05
        col.objects.link(e)
    e_knee.location = knee_piv
    e_hip.parent = e_knee
    e_hip.location = hip_piv - knee_piv
    obs['Rescuer thighs'].parent = e_knee
    obs['Rescuer body'].parent = e_hip

    # solve the two hinge angles so the hands travel straight down by DEPTH
    def hand_at(phi, psi):
        Mk = Matrix.Translation(knee_piv) @ Matrix.Rotation(phi, 4, 'X')
        Mh = Mk @ Matrix.Translation(hip_piv - knee_piv) @ Matrix.Rotation(psi, 4, 'X')
        return Mh @ (hand_pt - hip_piv)
    target = hand_pt + V((0, 0, -DEPTH))
    phi = psi = 0.0
    for _ in range(30):
        f = hand_at(phi, psi) - target
        e = 1e-5
        d1 = (hand_at(phi + e, psi) - hand_at(phi, psi)) / e
        d2 = (hand_at(phi, psi + e) - hand_at(phi, psi)) / e
        a, b, c, d = d1.y, d2.y, d1.z, d2.z
        det = a * d - b * c
        dphi = (-f.y * d + b * f.z) / det
        dpsi = (-a * f.z + c * f.y) / det
        phi += dphi
        psi += dpsi
    err = (hand_at(phi, psi) - target).length
    return obs, e_knee, e_hip, phi, psi, err


# ----------------------------------------------------------------- caller with defibrillator

def build_caller(col, M):
    pos = V((0.80, 0.82, 0.0))
    yaw = radians(150)
    MW = Matrix.Translation(pos) @ Matrix.Rotation(yaw, 4, 'Z')

    def W(x, y, z):
        return MW @ V((x, y, z))

    def D(x, y, z):
        return (MW.to_3x3() @ V((x, y, z)))

    bm = bmesh.new()
    sp = Spine(W(0, 0.0, 0.93), W(0, 0.045, 1.475), D(1, 0, 0), bend=0.0)
    torso(bm, sp)
    hc = sp.N + D(0, 0.015, 0.145)
    head(bm, hc, D(-0.06, 0.04, 1), D(1, 0, 0), neck_from=sp.at(0.97))
    # left arm: phone to the ear
    Sl = sp.shoulder(-1)
    Wl = W(-0.155, 0.135, 1.50)
    arm(bm, Sl, Wl, D(-0.6, 0.5, -1), D(0.25, -0.35, 1), D(1, 0.1, 0), thumb_side=1)
    # right arm: carrying the defibrillator
    Sr = sp.shoulder(+1)
    Wr = W(0.265, 0.10, 0.905)
    arm(bm, Sr, Wr, D(0.2, -1, 0), D(0, 0.15, -1), D(-1, 0, 0), thumb_side=1)
    # legs mid-stride
    leg(bm, sp.hip(-1), W(-0.10, 0.27, 0.075), D(0, 1, 0), D(0, 1, -0.05), D(0, 0, 1))
    leg(bm, sp.hip(+1), W(0.10, -0.33, 0.135), D(0, 1, 0.2), D(0, 0.75, -0.62), D(0, 0.62, 0.75))
    me = finalize(bm, 'Caller')
    ob = add_obj('Caller', me, col, [M['caller']])

    # phone
    bmp = bmesh.new()
    rounded_slab(bmp, 0.038, 0.0055, 0.079, expo=5.0, edge=0.003, n=40)
    mep = simple_mesh(bmp, 'Phone', smooth_angle=40)
    ph = add_obj('Phone', mep, col, [M['phone']])
    # local frame for the phone: flat against the side of the head
    c = hc + D(-0.121, 0.022, -0.045)
    ph.matrix_world = Matrix.Translation(c) @ MW.to_3x3().to_4x4() @ Matrix.Rotation(radians(90), 4, 'Z') @ Matrix.Rotation(radians(-18), 4, 'Y')

    # defibrillator case
    aed = build_aed(col, M)
    aed.matrix_world = Matrix.Translation(Wr + D(0.0, 0.02, -0.262)) @ MW.to_3x3().to_4x4() @ Matrix.Rotation(radians(-55), 4, 'Z')
    return ob, ph, aed


def heart_pts(scale=1.0, n=48):
    pts = []
    for i in range(n):
        t = 2 * pi * i / n
        x = 16 * sin(t) ** 3
        y = 13 * cos(t) - 5 * cos(2 * t) - 2 * cos(3 * t) - cos(4 * t)
        pts.append((x / 17.0 * scale, (y + 2.5) / 17.0 * scale))
    return pts


BOLT = [(0.16, 0.62), (-0.30, -0.08), (-0.02, -0.08), (-0.18, -0.66), (0.32, 0.10), (0.03, 0.10)]


def extruded_poly(bm, pts, z0, z1, xf=None, mat_index=0):
    """Add a prism from 2D points (x, y) between z0 and z1; xf maps (x,y,z)->Vector."""
    xf = xf or (lambda x, y, z: V((x, y, z)))
    bot = [bm.verts.new(xf(x, y, z0)) for x, y in pts]
    top = [bm.verts.new(xf(x, y, z1)) for x, y in pts]
    n = len(pts)
    faces = [bm.faces.new(top), bm.faces.new(bot[::-1])]
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new((bot[i], bot[j], top[j], top[i])))
    for f in faces:
        f.material_index = mat_index
    return faces


def build_aed(col, M):
    """Case stands in its local XZ plane, face towards -Y. Origin at centre."""
    bm = bmesh.new()
    rounded_slab(bm, 0.15, 0.055, 0.125, expo=6.0, edge=0.014)
    for f in bm.faces:
        f.material_index = 0
    # handle
    hp = []
    for i in range(17):
        u = i / 16
        ang = pi * u
        hp.append(V((-0.075 * cos(ang), 0, 0.115 + 0.075 * sin(ang) ** 0.6)))
    sweep(bm, hp, 0.013)
    # emblem on both faces: white heart, green bolt
    for sgn in (-1, 1):
        y0 = sgn * 0.054
        xf = lambda x, y, z, sgn=sgn: V((x * -sgn, sgn * z, y - 0.005))
        extruded_poly(bm, heart_pts(0.088), 0.050, 0.060, xf, 1)
        extruded_poly(bm, [(x * 0.085, y * 0.085 + 0.006) for x, y in BOLT], 0.055, 0.064, xf, 0)
    me = simple_mesh(bm, 'Defibrillator', smooth_angle=35)
    ob = add_obj('Defibrillator', me, col, [M['aed'], M['white']])
    return ob


# ----------------------------------------------------------------- plinth and pulse rings

def build_plinth(col, M):
    prof = [(R_TOP - 0.015, 0.0), (R_TOP, Z_TOP), (R_BOT, Z_BOT), (R_BOT + 0.012, Z_BOT - 0.014), (R_BOT + 0.012, Z_BOT - 0.11)]
    n = 192
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        rings.append([bm.verts.new((r * cos(2 * pi * i / n), r * sin(2 * pi * i / n), z)) for i in range(n)])
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    ct = bm.verts.new((0, 0, 0))
    cb = bm.verts.new((0, 0, Z_BOT - 0.11))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((ct, rings[0][i], rings[0][j]))
        bm.faces.new((cb, rings[-1][j], rings[-1][i]))
    me = simple_mesh(bm, 'Plinth', smooth_angle=20)
    return add_obj('Plinth', me, col, [M['slate']])


def ring_height(r, r_in, r_out):
    a = min(max((r - r_in) / 0.25, 0.0), 1.0)
    b = min(max((r_out - r) / 0.55, 0.0), 1.0)
    a = a * a * (3 - 2 * a)
    b = b * b * (3 - 2 * b)
    return 0.016 * a * b


def build_rings(col, M):
    K = 7
    r0, dr = 0.14, 0.20
    radii = [r0 + k * dr for k in range(K + 1)]
    r_in, r_out = radii[0], radii[-1]
    n = 160
    wdt = 0.028
    cross = [(-0.5, 0.0), (-0.3, 0.72), (0.0, 1.0), (0.3, 0.72), (0.5, 0.0)]
    bm = bmesh.new()
    targets = []

    def ring_pts(r):
        h = ring_height(r, r_in, r_out)
        return [(r + cx * wdt, -0.004 + cz * h) for cx, cz in cross]
    for k in range(K):
        p0 = ring_pts(radii[k])
        p1 = ring_pts(radii[k + 1])
        loops = []
        for (rr, zz), (rr1, zz1) in zip(p0, p1):
            loop = []
            for i in range(n):
                a = 2 * pi * i / n
                v = bm.verts.new((rr * cos(a), rr * sin(a), zz))
                targets.append(V((rr1 * cos(a), rr1 * sin(a), zz1)))
                loop.append(v)
            loops.append(loop)
        for a, b in zip(loops, loops[1:]):
            for i in range(n):
                j = (i + 1) % n
                bm.faces.new((a[i], b[i], b[j], a[j]))
    bm.verts.index_update()
    order = {v.index: t for v, t in zip(bm.verts, targets)}
    me = bpy.data.meshes.new('Pulse')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = add_obj('Pulse', me, col, [M['pulse']])
    ob.shape_key_add(name='Basis')
    sk = ob.shape_key_add(name='Spread')
    for i, t in order.items():
        sk.data[i].co = t
    return ob


# ----------------------------------------------------------------- animation

def animate(victim, pulse, e_knee, e_hip, phi, psi):
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.render.fps_base = 1.0
    sc.frame_start = 0
    sc.frame_end = PERIOD
    half = PERIOD // 2
    ed = bpy.context.preferences.edit
    old = ed.keyframe_new_interpolation_type
    ed.keyframe_new_interpolation_type = 'BEZIER'
    kb = victim.data.shape_keys.key_blocks['Compress']
    for f, w in ((0, 0.0), (half, 1.0), (PERIOD, 0.0)):
        e_knee.rotation_euler = (phi * w, 0, 0)
        e_hip.rotation_euler = (psi * w, 0, 0)
        e_knee.keyframe_insert('rotation_euler', frame=f)
        e_hip.keyframe_insert('rotation_euler', frame=f)
        kb.value = w
        kb.keyframe_insert('value', frame=f)
    ed.keyframe_new_interpolation_type = 'LINEAR'
    kp = pulse.data.shape_keys.key_blocks['Spread']
    for f, w in ((0, 0.0), (PERIOD, 1.0)):
        kp.value = w
        kp.keyframe_insert('value', frame=f)
    ed.keyframe_new_interpolation_type = old
    sc.frame_set(half)


def build_all():
    clean_scene()
    bpy.context.scene.name = 'Two Hands'
    col = get_col('Model')
    M = build_materials()
    victim, chest_top = build_victim(col, M)
    obs, e_knee, e_hip, phi, psi, err = build_rescuer(col, M, chest_top)
    caller, phone, aed = build_caller(col, M)
    plinth = build_plinth(col, M)
    pulse = build_rings(col, M)
    legend = build_legend(col, M)
    animate(victim, pulse, e_knee, e_hip, phi, psi)
    return dict(M=M, col=col, victim=victim, chest_top=chest_top, phi=phi, psi=psi, err=err, pulse=pulse,
                e_knee=e_knee, e_hip=e_hip)
