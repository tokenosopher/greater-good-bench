# Lettering and icons wrapped onto the sloped rim of the plinth.

def band_xf(phi_c, v0):
    r_base = R_BOT - v0 * cos(BAND_S)

    def xf(x, y, z):
        v = v0 + y
        phi = phi_c + x / r_base
        r = R_BOT - v * cos(BAND_S) + z * sin(BAND_S)
        zz = Z_BOT + v * sin(BAND_S) + z * cos(BAND_S)
        return V((r * sin(phi), -r * cos(phi), zz))
    return xf


def text_mesh(body, size, bold=0.0, extrude=0.004):
    cu = bpy.data.curves.new('txt', 'FONT')
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.offset = bold
    cu.align_x = 'LEFT'
    cu.resolution_u = 3
    ob = bpy.data.objects.new('txt', cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.curves.remove(cu)
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    me['ybounds'] = (min(ys), max(ys))
    return me, min(xs), max(xs)


class Legend:
    def __init__(self):
        self.bm = bmesh.new()
        self.EX = 0.004

    def add_text(self, me, x_off, phi_c, v0, mat_index, lift=0.0):
        xf = band_xf(phi_c, v0)
        tmp = bmesh.new()
        tmp.from_mesh(me)
        for v in tmp.verts:
            v.co = xf(v.co.x + x_off, v.co.y, v.co.z + self.EX - 0.0015 + lift)
        for f in tmp.faces:
            f.material_index = mat_index
        tmp_me = bpy.data.meshes.new('tmp')
        tmp.to_mesh(tmp_me)
        tmp.free()
        self.bm.from_mesh(tmp_me)
        bpy.data.meshes.remove(tmp_me)
        bpy.data.meshes.remove(me)

    def line(self, body, size, phi_c, v0, mat_index, bold=0.0):
        me, x0, x1 = text_mesh(body, size, bold, self.EX)
        self.add_text(me, -(x0 + x1) / 2, phi_c, v0, mat_index)

    def poly(self, pts, phi_c, v0, mat_index, z0=-0.0015, z1=0.0065):
        xf = band_xf(phi_c, v0)
        n0 = len(self.bm.faces)
        extruded_poly(self.bm, pts, z0, z1, xf, mat_index)


def handset_pts(s=1.0):
    """Classic telephone receiver, tilted, ear and mouth pieces facing lower-left."""
    pts = []
    n = 14
    for i in range(n + 1):                      # outer edge of the handle
        u = i / n
        x = -0.50 + u
        pts.append((x, 0.13 + 0.11 * sin(pi * u)))
    def piece(x_out, x_in):                     # rounded ear / mouth piece, hanging down
        out = []
        for a in range(0, 91, 18):
            r = radians(a)
            out.append((x_out - math.copysign(0.07, x_out) * (1 - cos(r)), -0.21 - 0.07 * sin(r)))
        for a in range(90, -1, -18):
            r = radians(a)
            out.append((x_in + math.copysign(0.07, x_out) * (1 - cos(r)), -0.21 - 0.07 * sin(r)))
        return out
    pts += [(0.57, 0.06)] + piece(0.57, 0.23) + [(0.23, -0.03)]
    for i in range(1, n):                       # inner edge of the handle
        u = i / n
        x = 0.23 - 0.46 * u
        pts.append((x, -0.03 + 0.07 * sin(pi * u)))
    left = piece(-0.57, -0.23)
    pts += [(-0.23, -0.03)] + left[::-1] + [(-0.57, 0.06)]
    rot = radians(-45)
    return [((x * cos(rot) - y * sin(rot)) * s, (x * sin(rot) + y * cos(rot)) * s) for x, y in pts]


def disc_pts(r, n=40):
    return [(r * cos(2 * pi * i / n), r * sin(2 * pi * i / n)) for i in range(n)]


ARROW = [(-0.10, 0.62), (0.10, 0.62), (0.10, 0.20), (0.26, 0.20), (0.0, -0.16), (-0.26, 0.20), (-0.10, 0.20)]


def build_legend(col, M):
    L = Legend()
    WHITE, BLUE, CORAL, GREEN = 0, 1, 2, 3
    H_SIZE, S_SIZE = 0.21, 0.066
    V_HEAD, V_S1, V_S2 = 0.40, 0.25, 0.145
    GAP = 0.075
    ICON = 0.23

    def step(phi_deg, num, word, colour, icon, sub1, sub2):
        phi = radians(phi_deg)
        BADGE = 0.215
        me_n, n0, n1 = text_mesh(num, 0.165, 0.007, L.EX)
        ny0, ny1 = me_n['ybounds']
        me_w, w0, w1 = text_mesh(word, H_SIZE, 0.005, L.EX)
        ww = w1 - w0
        total = BADGE + GAP + ww + GAP * 1.3 + ICON
        r_base = R_BOT - V_HEAD * cos(BAND_S)
        x = -total / 2
        vc = V_HEAD + 0.075
        L.poly(disc_pts(BADGE / 2), phi + (x + BADGE / 2) / r_base, vc, colour)
        r_b2 = R_BOT - vc * cos(BAND_S)
        L.add_text(me_n, -(n0 + n1) / 2, phi + (x + BADGE / 2) / r_base, vc - (ny0 + ny1) / 2, WHITE, lift=0.004)
        x += BADGE + GAP
        L.add_text(me_w, x - w0, phi, V_HEAD, WHITE)
        x += ww + GAP * 1.3 + ICON / 2
        icon(phi + x / r_base, vc)
        L.line(sub1, S_SIZE, phi, V_S1, WHITE)
        L.line(sub2, S_SIZE, phi, V_S2, WHITE)

    def icon_phone(phi, v):
        L.poly(handset_pts(0.21), phi, v, BLUE)

    def icon_push(phi, v):
        L.poly([(x, y - 0.035) for x, y in heart_pts(0.105)], phi, v, CORAL)
        L.poly([(x * 0.17, y * 0.17 + 0.03) for x, y in ARROW], phi, v, WHITE, z1=0.0095)

    def icon_aed(phi, v):
        L.poly(heart_pts(0.115), phi, v, GREEN)
        L.poly([(x * 0.115, y * 0.115 + 0.008) for x, y in BOLT], phi, v, WHITE, z1=0.0095)

    step(-45, '1', 'CALL', BLUE, icon_phone, 'your emergency number.', 'Put the phone on speaker.')
    step(0, '2', 'PUSH', CORAL, icon_push, 'centre of the chest, 5 cm deep,', 'two pushes a second. Don’t stop.')
    step(45, '3', 'SHOCK', GREEN, icon_aed, 'Send for a defibrillator (AED).', 'Open it. It tells you what to do.')

    # the "if" and the "until", either side of the three steps
    L.line('SOMEONE COLLAPSES', 0.115, radians(-93), 0.39, WHITE, 0.003)
    L.line('AND ISN’T BREATHING NORMALLY?', 0.07, radians(-86), 0.165, WHITE, 0.001)
    L.line('KEEP GOING', 0.115, radians(93), 0.39, WHITE, 0.003)
    L.line('UNTIL HELP TAKES OVER', 0.078, radians(93), 0.22, WHITE, 0.001)
    # the back of the plinth
    L.line('ANYONE CAN DO THIS', 0.17, radians(180), 0.37, WHITE, 0.004)
    L.line('Any attempt is better than none.', 0.085, radians(180), 0.19, CORAL, 0.001)
    for a in (-133, 133):
        L.poly([(x, y - 0.0) for x, y in heart_pts(0.10)], radians(a), 0.33, CORAL)

    bmesh.ops.recalc_face_normals(L.bm, faces=L.bm.faces[:])
    me = bpy.data.meshes.new('Legend')
    L.bm.to_mesh(me)
    L.bm.free()
    ob = add_obj('Legend', me, col, [M['white'], M['caller'], M['pulse'], M['aed']])
    return ob
