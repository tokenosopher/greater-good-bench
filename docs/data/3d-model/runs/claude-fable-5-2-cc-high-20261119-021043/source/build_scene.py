import bpy, bmesh, math
from math import sin, cos, pi, radians, sqrt, exp
from mathutils import Vector, Matrix

V = Vector
X_AXIS, Y_AXIS, Z_AXIS = V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1))

# ----------------------------------------------------------------- utilities

def clean_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.cameras,
                 bpy.data.lights, bpy.data.actions, bpy.data.images):
        for d in list(coll):
            try:
                coll.remove(d)
            except Exception:
                pass
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


def get_col(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def srgb(hexs, a=1.0):
    hexs = hexs.lstrip('#')
    c = [int(hexs[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c]
    return (lin[0], lin[1], lin[2], a)


def make_mat(name, hexc, rough=0.5, metal=0.0, emit=None, emit_strength=1.0):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    b = None
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            b = n
    if b is None:
        nt.nodes.clear()
        b = nt.nodes.new('ShaderNodeBsdfPrincipled')
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(b.outputs[0], out.inputs[0])
    b.inputs['Base Color'].default_value = srgb(hexc)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = srgb(emit)
        b.inputs['Emission Strength'].default_value = emit_strength
    m.diffuse_color = srgb(hexc)
    return m


def add_obj(name, me, col, mats=()):
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    for m in mats:
        me.materials.append(m)
    return ob


def frame_from(T, hint):
    T = T.normalized()
    Xv = hint - T * hint.dot(T)
    if Xv.length < 1e-5:
        hint = X_AXIS if abs(T.x) < 0.9 else Y_AXIS
        Xv = hint - T * hint.dot(T)
    Xv.normalize()
    Yv = T.cross(Xv)
    return Xv, Yv


def loft(bm, secs, n=24):
    """secs: list of (center, ax_vec, ay_vec, exponent)."""
    rings = []
    for c, ax, ay, e in secs:
        ring = []
        for i in range(n):
            t = 2 * pi * i / n
            ct, st = cos(t), sin(t)
            x = math.copysign(abs(ct) ** (2 / e), ct)
            y = math.copysign(abs(st) ** (2 / e), st)
            ring.append(bm.verts.new(c + ax * x + ay * y))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])


def tube(bm, pts, radii, n=20, capk=5):
    T0 = (pts[1] - pts[0]).normalized()
    Xv, Yv = frame_from(T0, Z_AXIS)
    secs = []
    r = radii[0]
    for k in range(capk, 0, -1):
        a = (pi / 2) * k / (capk + 0.4)
        secs.append((pts[0] - T0 * r * sin(a), Xv * r * cos(a), Yv * r * cos(a), 2))
    for p, r in zip(pts, radii):
        secs.append((p, Xv * r, Yv * r, 2))
    T1 = (pts[-1] - pts[-2]).normalized()
    r = radii[-1]
    for k in range(1, capk + 1):
        a = (pi / 2) * k / (capk + 0.4)
        secs.append((pts[-1] + T1 * r * sin(a), Xv * r * cos(a), Yv * r * cos(a), 2))
    loft(bm, secs, n)


RAD = 1.07


def limb(bm, a, b, ra, rb, bulge=None):
    ra, rb = ra * RAD, rb * RAD
    if bulge:
        bulge = (bulge[0], bulge[1] * RAD)
        t, rm = bulge
        tube(bm, [a, a.lerp(b, t), b], [ra, rm, rb])
    else:
        tube(bm, [a, b], [ra, rb])


def ellipsoid(bm, c, ax, ay, az, u=24, v=14):
    M = Matrix(((ax.x, ay.x, az.x, c.x),
                (ax.y, ay.y, az.y, c.y),
                (ax.z, ay.z, az.z, c.z),
                (0, 0, 0, 1)))
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0, matrix=M)


def ik(root, target, l1, l2, pole):
    d = target - root
    L = d.length
    Lc = min(L, (l1 + l2) * 0.9995)
    dn = d / L
    a = (l1 * l1 - l2 * l2 + Lc * Lc) / (2 * Lc)
    h = sqrt(max(l1 * l1 - a * a, 0.0))
    pp = pole - dn * pole.dot(dn)
    if pp.length < 1e-6:
        pp = frame_from(dn, Z_AXIS)[0]
    pp.normalize()
    return root + dn * a + pp * h


def catmull(vals, i, u):
    p0 = vals[max(i - 1, 0)]
    p1 = vals[i]
    p2 = vals[i + 1]
    p3 = vals[min(i + 2, len(vals) - 1)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


# ----------------------------------------------------------------- figure parts
# (t along pelvis->neck, half width, half depth)
TORSO = [(-0.17, 0.08, 0.066), (-0.07, 0.15, 0.098), (0.08, 0.170, 0.108), (0.35, 0.142, 0.094),
         (0.62, 0.168, 0.114), (0.84, 0.186, 0.104), (0.95, 0.152, 0.084), (1.01, 0.08, 0.062)]

UPPER_ARM, FOREARM = 0.30, 0.265
THIGH, SHIN = 0.44, 0.43


class Spine:
    def __init__(self, P, N, R, bend=0.0):
        self.P, self.N = P.copy(), N.copy()
        self.L = (N - P).length
        self.T = (N - P).normalized()
        self.R = (R - self.T * R.dot(self.T)).normalized()
        self.F = self.T.cross(self.R).normalized()
        self.bend = bend

    def at(self, t):
        tc = min(max(t, 0.0), 1.0)
        return self.P + self.T * (t * self.L) + self.F * (self.bend * sin(pi * tc))

    def shoulder(self, side):
        return self.at(0.852) + self.R * (0.18 * side)

    def hip(self, side):
        return self.at(0.03) + self.R * (0.092 * side)


def torso(bm, sp, expo=2.5, sub=5):
    ts = [s[0] for s in TORSO]
    as_ = [s[1] for s in TORSO]
    bs = [s[2] for s in TORSO]
    secs = []
    for i in range(len(TORSO) - 1):
        for k in range(sub):
            u = k / sub
            secs.append((sp.at(catmull(ts, i, u)), sp.R * catmull(as_, i, u), sp.F * catmull(bs, i, u), expo))
    secs.append((sp.at(ts[-1]), sp.R * as_[-1], sp.F * bs[-1], expo))
    loft(bm, secs, 32)


def head(bm, center, up, right, s=1.08, neck_from=None):
    up = up.normalized()
    right = (right - up * right.dot(up)).normalized()
    fwd = up.cross(right)
    # cranium + jaw fuse into an egg with a chin, so the figure has a facing direction
    ellipsoid(bm, center + up * 0.022 * s - fwd * 0.008 * s, right * 0.093 * s, fwd * 0.108 * s, up * 0.104 * s)
    ellipsoid(bm, center - up * 0.048 * s + fwd * 0.026 * s, right * 0.068 * s, fwd * 0.074 * s, up * 0.08 * s)
    if neck_from is not None:
        limb(bm, neck_from, center - up * 0.05 * s - fwd * 0.012 * s, 0.056, 0.05)


def arm(bm, S, W, pole, hand_dir, palm_n, thumb_side=1.0, hand=True):
    E = ik(S, W, UPPER_ARM, FOREARM, pole)
    limb(bm, S, E, 0.058, 0.047)
    limb(bm, E, W, 0.047, 0.036, bulge=(0.3, 0.05))
    if hand:
        hd = hand_dir.normalized()
        pn = (palm_n - hd * palm_n.dot(hd)).normalized()
        side = pn.cross(hd)
        c = W + hd * 0.085
        ellipsoid(bm, c, side * 0.047, hd * 0.10, pn * 0.024)
        tc = W + hd * 0.055 + side * (0.042 * thumb_side)
        td = (hd + side * (0.7 * thumb_side)).normalized()
        ellipsoid(bm, tc, pn.cross(td) * 0.018, td * 0.045, pn * 0.017, u=12, v=8)
    return E


def leg(bm, H, A, pole, toe_dir, foot_up, foot_off=0.025, parts=('thigh', 'shin', 'foot')):
    K = ik(H, A, THIGH, SHIN, pole)
    if 'thigh' in parts:
        limb(bm, H, K, 0.092, 0.064, bulge=(0.3, 0.09))
    if 'shin' in parts:
        limb(bm, K, A, 0.064, 0.044, bulge=(0.3, 0.066))
    if 'foot' in parts:
        td = toe_dir.normalized()
        fu = (foot_up - td * foot_up.dot(td)).normalized()
        side = fu.cross(td)
        c = A + td * 0.075 - fu * foot_off
        ellipsoid(bm, c, side * 0.05, td * 0.13, fu * 0.043)
    return K


def finalize(bm, name, voxel=0.011, smooth_iter=13, smooth_fac=0.55):
    """Fuse all overlapping parts into one skin (voxel remesh + smooth)."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name + '_raw')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name + '_raw', me)
    bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new('rm', 'REMESH')
    m.mode = 'VOXEL'
    m.voxel_size = voxel
    m.adaptivity = 0.0
    s = ob.modifiers.new('sm', 'SMOOTH')
    s.factor = smooth_fac
    s.iterations = smooth_iter
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    me2.name = name
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    for p in me2.polygons:
        p.use_smooth = True
    return me2


def simple_mesh(bm, name, smooth_angle=None):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth_angle is not None:
        for p in me.polygons:
            p.use_smooth = True
        me.set_sharp_from_angle(angle=radians(smooth_angle))
    return me


def sweep(bm, pts, radius, n=12):
    """Round tube along a planar polyline (open ends capped)."""
    nrm = None
    for i in range(1, len(pts) - 1):
        c = (pts[i] - pts[i - 1]).cross(pts[i + 1] - pts[i])
        if c.length > 1e-9:
            nrm = c.normalized()
            break
    if nrm is None:
        nrm = frame_from(pts[1] - pts[0], Z_AXIS)[0]
    secs = []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        T = (b - a).normalized()
        Yv = T.cross(nrm).normalized()
        secs.append((p, nrm * radius, Yv * radius, 2))
    loft(bm, secs, n)


def rounded_slab(bm, hx, hy, hz, expo=6.0, edge=0.012, n=56):
    """Rounded box: superellipse outline in XZ, thickness along Y, softened rims."""
    secs = []
    for y, k in ((-hy, edge * 0.9), (-hy + edge * 0.35, edge * 0.35), (-hy + edge, 0.0),
                 (hy - edge, 0.0), (hy - edge * 0.35, edge * 0.35), (hy, edge * 0.9)):
        secs.append((V((0, y, 0)), X_AXIS * (hx - k), Z_AXIS * (hz - k), expo))
    loft(bm, secs, n)
