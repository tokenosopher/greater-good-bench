"""Held in Common — a small monument: many open hands, one living Earth, a young olive."""

import bpy
import math
import random
from mathutils import Vector, Matrix, Euler

random.seed(7)

# ---------------------------------------------------------------------------
# cleanup
# ---------------------------------------------------------------------------

def wipe():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                 bpy.data.images, bpy.data.cameras, bpy.data.lights):
        for d in list(coll):
            coll.remove(d)


def srgb_to_linear(c):
    def f(u):
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    return tuple(f(x) for x in c)


def new_mat(name, color_srgb, rough=0.45, metallic=0.0, emit=None, emit_str=0.0, alpha=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color_srgb, alpha)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    col = srgb_to_linear(color_srgb)
    bsdf.inputs["Base Color"].default_value = (*col, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = metallic
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.45
    if alpha < 1.0:
        mat.blend_method = 'BLEND' if hasattr(mat, "blend_method") else mat.blend_method
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
        mat.use_transparency_overlap = False if hasattr(mat, "use_transparency_overlap") else None
    if emit and emit_str > 0 and "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*srgb_to_linear(emit), 1)
        bsdf.inputs["Emission Strength"].default_value = emit_str
    return mat, bsdf


def skin_mat(name, color_srgb):
    mat, bsdf = new_mat(name, color_srgb, rough=0.46, metallic=0.0)
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.18
    if "Subsurface Radius" in bsdf.inputs:
        bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.38, 0.22)
    if "Subsurface Scale" in bsdf.inputs:
        bsdf.inputs["Subsurface Scale"].default_value = 0.012
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.38
    return mat


# ---------------------------------------------------------------------------
# hand
# ---------------------------------------------------------------------------

def make_curve(name, pts, bevel_res=3):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 1.0
    cu.bevel_resolution = bevel_res
    cu.resolution_u = 6
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1.0)
        sp.points[i].radius = p[3]
    obj = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(obj)
    return obj


def finger_pts(x0, length, lift, spread, r0, r1, n=8, y0=0.090, z0=0.011):
    pts = []
    for i in range(n):
        t = i / (n - 1)
        y = y0 + length * (t - 0.16 * t * t)
        z = z0 + lift * (t ** 1.28)
        x = x0 + spread * (t ** 1.05)
        r = r0 + (r1 - r0) * t
        if 0.16 < t < 0.40:
            r *= 1.06
            z += 0.002
        pts.append((x, y, z, max(r, 0.0045)))
    return pts


def add_sphere(name, loc, scale, segs=24):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=1.0, segments=segs, ring_count=max(8, segs // 2), location=loc
    )
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return o


def build_hand(name, mat, chubby=1.0, curl=1.0, spread=1.0, mirror=False):
    c = chubby
    parts = []
    parts.append(make_curve(name + "_i", finger_pts(
        0.021 * spread, 0.096, 0.058 * curl, 0.010 * spread, 0.0100 * c, 0.0068 * c)))
    parts.append(make_curve(name + "_m", finger_pts(
        0.000, 0.108, 0.066 * curl, 0.001 * spread, 0.0105 * c, 0.0070 * c)))
    parts.append(make_curve(name + "_r", finger_pts(
        -0.020 * spread, 0.100, 0.060 * curl, -0.006 * spread, 0.0098 * c, 0.0066 * c)))
    parts.append(make_curve(name + "_p", finger_pts(
        -0.039 * spread, 0.078, 0.046 * curl, -0.010 * spread, 0.0084 * c, 0.0056 * c)))
    # abducted thumb — silhouette must read at a distance
    parts.append(make_curve(name + "_t", [
        (0.040, 0.022, 0.004, 0.0155 * c),
        (0.062, 0.032, 0.014, 0.0136 * c),
        (0.080, 0.050, 0.030, 0.0122 * c),
        (0.078, 0.074, 0.048, 0.0110 * c),
        (0.062, 0.096, 0.062, 0.0096 * c),
        (0.048, 0.110, 0.070, 0.0084 * c),
    ]))
    parts.append(make_curve(name + "_w", [
        (0.000, 0.010, -0.002, 0.026 * c),
        (0.000, -0.030, -0.008, 0.023 * c),
        (0.000, -0.080, -0.014, 0.021 * c),
        (0.000, -0.150, -0.020, 0.019 * c),
    ]))

    palm_parts = [
        add_sphere(name + "_palm", (0.000, 0.056, 0.000), (0.048, 0.050, 0.019)),
        add_sphere(name + "_thenar", (0.030, 0.038, 0.004), (0.024, 0.028, 0.015)),
        add_sphere(name + "_hypo", (-0.026, 0.046, -0.002), (0.018, 0.034, 0.013)),
        add_sphere(name + "_knuck", (0.000, 0.098, 0.009), (0.046, 0.015, 0.012)),
        add_sphere(name + "_heel", (0.000, 0.020, -0.004), (0.036, 0.020, 0.015)),
        add_sphere(name + "_k1", (0.022, 0.100, 0.015), (0.012, 0.010, 0.008), 12),
        add_sphere(name + "_k2", (0.000, 0.105, 0.016), (0.012, 0.010, 0.008), 12),
        add_sphere(name + "_k3", (-0.020, 0.100, 0.014), (0.011, 0.009, 0.007), 12),
        add_sphere(name + "_k4", (-0.038, 0.094, 0.012), (0.009, 0.008, 0.007), 12),
    ]

    bpy.ops.object.select_all(action="DESELECT")
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.convert(target="MESH")

    bpy.ops.object.select_all(action="DESELECT")
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and o.name.startswith(name)]
    # parts were renamed? convert keeps names. palm_parts too.
    all_parts = []
    for o in list(bpy.context.scene.objects):
        if o.type == "MESH" and (o.name.startswith(name)):
            all_parts.append(o)
    if not all_parts:
        raise RuntimeError("no hand parts for " + name)
    for o in all_parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = all_parts[0]
    bpy.ops.object.join()
    hand = bpy.context.active_object
    hand.name = name

    rem = hand.modifiers.new("Remesh", "REMESH")
    rem.mode = "VOXEL"
    rem.voxel_size = 0.0034
    rem.use_smooth_shade = True
    sm = hand.modifiers.new("Smooth", "SMOOTH")
    sm.factor = 0.55
    sm.iterations = 10
    bpy.context.view_layer.objects.active = hand
    bpy.ops.object.modifier_apply(modifier="Remesh")
    bpy.ops.object.modifier_apply(modifier="Smooth")

    if mirror:
        hand.scale.x = -1
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode="OBJECT")

    for p in hand.data.polygons:
        p.use_smooth = True
    hand.data.materials.append(mat)
    # origin stays near the wrist (geometry was built around world origin)
    return hand


def orient_hand(obj, angle_deg, wrist_r, wrist_z, pitch_deg, roll_deg, globe_center):
    """Place a hand so fingers reach inward/up and the palm faces the globe."""
    a = math.radians(angle_deg)
    loc = Vector((math.sin(a) * wrist_r, -math.cos(a) * wrist_r, wrist_z))
    inward = Vector((-loc.x, -loc.y, 0.0))
    if inward.length < 1e-6:
        inward = Vector((0, 1, 0))
    inward.normalize()
    pitch = math.radians(pitch_deg)
    forward = (inward * math.cos(pitch) + Vector((0, 0, 1)) * math.sin(pitch)).normalized()
    # palm faces toward globe center, blended with world up so it stays an open palm
    to_globe = (globe_center - loc)
    if to_globe.length < 1e-6:
        to_globe = Vector((0, 0, 1))
    to_globe.normalize()
    palm = (to_globe * 0.72 + Vector((0, 0, 1)) * 0.55).normalized()
    # roll around forward
    x_axis = forward.cross(palm)
    if x_axis.length < 1e-6:
        x_axis = forward.cross(Vector((0, 0, 1)))
    x_axis.normalize()
    palm = x_axis.cross(forward).normalized()
    roll = math.radians(roll_deg)
    x_axis = (x_axis * math.cos(roll) + palm * math.sin(roll)).normalized()
    palm = x_axis.cross(forward).normalized()
    # columns are local axes
    mat = Matrix((
        (x_axis.x, forward.x, palm.x, loc.x),
        (x_axis.y, forward.y, palm.y, loc.y),
        (x_axis.z, forward.z, palm.z, loc.z),
        (0.0, 0.0, 0.0, 1.0),
    ))
    obj.matrix_world = mat
    return loc


# ---------------------------------------------------------------------------
# earth texture
# ---------------------------------------------------------------------------

def hash_noise(x, y):
    n = math.sin(x * 127.1 + y * 311.7) * 43758.5453
    return n - math.floor(n)


def vnoise(lon, lat):
    # smooth value noise in degrees
    x = lon * 0.15
    y = lat * 0.15
    x0 = math.floor(x)
    y0 = math.floor(y)
    fx = x - x0
    fy = y - y0
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)

    def h(ix, iy):
        return hash_noise(ix * 1.13, iy * 2.71)

    n00 = h(x0, y0)
    n10 = h(x0 + 1, y0)
    n01 = h(x0, y0 + 1)
    n11 = h(x0 + 1, y0 + 1)
    return (n00 * (1 - fx) + n10 * fx) * (1 - fy) + (n01 * (1 - fx) + n11 * fx) * fy


def fbm(lon, lat):
    v = 0.0
    a = 0.55
    f = 1.0
    for _ in range(4):
        v += a * vnoise(lon * f, lat * f)
        f *= 2.05
        a *= 0.5
    return v


def ellipse(lon, lat, clon, clat, rlon, rlat):
    return ((lon - clon) / rlon) ** 2 + ((lat - clat) / rlat) ** 2 <= 1.0


def point_in_poly(x, y, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi):
            inside = not inside
        j = i
    return inside


AFRICA = [
    (-17, 15), (-16, 21), (-16, 27), (-10, 32), (-6, 35), (3, 37), (11, 33),
    (25, 32), (33, 31), (35, 26), (43, 12), (51, 12), (45, 2), (41, -2),
    (42, -12), (40, -16), (35, -22), (33, -26), (28, -33), (20, -35),
    (18, -32), (12, -17), (13, -6), (10, 2), (9, 4), (-4, 5), (-8, 4),
    (-14, 10), (-17, 14),
]
SOUTH_AMERICA = [
    (-78, 10), (-70, 12), (-60, 10), (-52, 6), (-36, -5), (-35, -8),
    (-39, -16), (-40, -22), (-48, -28), (-53, -34), (-62, -40), (-68, -48),
    (-75, -52), (-74, -46), (-73, -40), (-72, -18), (-70, -18), (-76, -14),
    (-81, -5), (-79, 1), (-78, 7),
]
NORTH_AMERICA = [
    (-166, 66), (-158, 71), (-140, 70), (-128, 71), (-105, 73), (-88, 74),
    (-82, 72), (-78, 63), (-70, 60), (-64, 58), (-56, 53), (-64, 47),
    (-70, 45), (-74, 40), (-76, 35), (-81, 31), (-82, 28), (-90, 29),
    (-97, 26), (-97, 20), (-106, 22), (-110, 24), (-114, 31), (-117, 33),
    (-122, 37), (-124, 40), (-124, 48), (-128, 55), (-136, 58), (-152, 60),
    (-165, 64),
]
GREENLAND = [
    (-68, 76), (-62, 66), (-52, 61), (-43, 60), (-42, 66), (-22, 70),
    (-20, 78), (-30, 82), (-48, 83), (-62, 80), (-68, 76),
]
INDIA = [
    (68, 24), (70, 21), (72, 19), (73, 16), (75, 10), (77, 8), (80, 10),
    (80, 15), (77, 16), (84, 18), (87, 21), (88, 22), (85, 22), (80, 22),
    (76, 24), (72, 23), (68, 23),
]
AUSTRALIA = [
    (113, -22), (122, -16), (128, -14), (136, -12), (142, -11), (146, -15),
    (146, -19), (150, -24), (153, -26), (153, -28), (150, -34), (146, -39),
    (140, -38), (136, -35), (128, -32), (124, -33), (116, -35), (114, -30),
    (113, -26),
]
BRITAIN = [(-8, 54), (-6, 58), (-3, 59), (1, 58), (2, 53), (1, 51), (-5, 50), (-5, 52)]
JAPAN = [(140, 35), (141, 41), (145, 43), (145, 41), (142, 38), (141, 35), (138, 35), (132, 34), (131, 33), (131, 34)]


def is_land(lon, lat):
    # wrap
    if lon > 180:
        lon -= 360
    if lon < -180:
        lon += 360
    n = fbm(lon, lat)
    # coastline wobble applied to test coordinates
    wob = (n - 0.45) * 7.5
    lon_w = lon + wob * 0.65
    lat_w = lat + (fbm(lon + 40, lat - 20) - 0.45) * 5.5

    if lat_w < -63 + (n - 0.5) * 6:
        return True  # Antarctica
    if point_in_poly(lon_w, lat_w, AFRICA):
        return True
    if point_in_poly(lon_w, lat_w, SOUTH_AMERICA):
        return True
    if point_in_poly(lon_w, lat_w, NORTH_AMERICA):
        return True
    if point_in_poly(lon_w, lat_w, GREENLAND):
        return True
    if point_in_poly(lon_w, lat_w, AUSTRALIA):
        return True
    if point_in_poly(lon_w, lat_w, INDIA):
        return True
    if point_in_poly(lon_w, lat_w, BRITAIN):
        return True

    # Eurasia as blended ellipses, then cut seas
    eurasia = (
        ellipse(lon_w, lat_w, 15, 50, 30, 11)
        or ellipse(lon_w, lat_w, 18, 63, 16, 7)
        or ellipse(lon_w, lat_w, 55, 60, 32, 10)
        or ellipse(lon_w, lat_w, 100, 60, 40, 11)
        or ellipse(lon_w, lat_w, 145, 62, 28, 9)
        or ellipse(lon_w, lat_w, 105, 38, 28, 12)
        or ellipse(lon_w, lat_w, 108, 22, 14, 9)
        or ellipse(lon_w, lat_w, 45, 28, 14, 9)
        or ellipse(lon_w, lat_w, 48, 38, 12, 7)
        or ellipse(lon_w, lat_w, 32, 42, 10, 6)
        or ellipse(lon_w, lat_w, 65, 38, 14, 8)
    )
    if eurasia:
        # cut inland seas so the Mediterranean reads
        if ellipse(lon, lat, 18, 36, 22, 5.2):
            return False
        if ellipse(lon, lat, 34, 43.5, 8, 3.2):
            return False
        if ellipse(lon, lat, 39, 22, 3.2, 9):
            return False
        if ellipse(lon, lat, 50, 28, 4, 6):  # Persian gulf-ish bite
            return False
        return True

    # central america bridge
    if ellipse(lon_w, lat_w, -85, 14, 10, 5) or ellipse(lon_w, lat_w, -78, 8, 6, 3.5):
        return True
    # japan-ish if polygon missed
    if point_in_poly(lon_w, lat_w, JAPAN) or ellipse(lon_w, lat_w, 138, 36, 3.5, 8):
        return True
    # madagascar, nz, indonesia, philippines, caribbean
    islands = [
        (46, -19, 2.4, 6.5),
        (172, -41, 3.2, 5),
        (174, -38, 2, 3),
        (115, -2, 8, 3.2),
        (122, -2, 6, 2.6),
        (108, 0, 4, 2.5),
        (122, 12, 3, 6),
        (-78, 22, 3.5, 2.2),
        (-76, 20, 2, 1.5),
        (-68, 19, 2, 1.2),
        (35, 31, 2.2, 1.4),  # cyprus-ish / levant already in eurasia
        (-16, 28, 2, 1.2),  # canaries hint
        (44, -16, 1.2, 2),
    ]
    for clon, clat, rlo, rla in islands:
        if ellipse(lon_w, lat_w, clon, clat, rlo, rla):
            return True
    return False


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def build_earth_images(w=1400, h=700):
    mask = bytearray(w * h)
    for y in range(h):
        lat = 90.0 - (y + 0.5) / h * 180.0
        for x in range(w):
            lon = -180.0 + (x + 0.5) / w * 360.0
            if is_land(lon, lat):
                mask[y * w + x] = 1

    color = [0] * (w * h * 4)
    rough = [0] * (w * h * 4)

    def near(x, y, dist):
        for dx, dy in ((dist, 0), (-dist, 0), (0, dist), (0, -dist),
                       (dist, dist), (dist, -dist), (-dist, dist), (-dist, -dist)):
            xx = (x + dx) % w
            yy = y + dy
            if 0 <= yy < h and mask[yy * w + xx]:
                return True
        return False

    for y in range(h):
        lat = 90.0 - (y + 0.5) / h * 180.0
        for x in range(w):
            lon = -180.0 + (x + 0.5) / w * 360.0
            land = mask[y * w + x]
            n = fbm(lon * 1.3, lat * 1.3)
            n2 = fbm(lon * 0.4 + 20, lat * 0.4 - 10)
            i = (y * w + x) * 4
            if land:
                ice = abs(lat) > 68 or (abs(lat) > 60 and n > 0.62) or lat < -62
                desert = (
                    (-16 < lon < 38 and 14 < lat < 32)
                    or (35 < lon < 58 and 14 < lat < 31)
                    or (121 < lon < 146 and -32 < lat < -18 and n > 0.4)
                    or (-118 < lon < -102 and 26 < lat < 40 and n > 0.48)
                )
                if ice:
                    col = lerp((214, 224, 230), (245, 248, 250), n)
                elif desert:
                    col = lerp((176, 146, 86), (214, 186, 120), n)
                else:
                    # latitude greens: lusher in tropics, paler toward poles
                    trop = max(0.0, 1.0 - abs(lat) / 55.0)
                    deep = lerp((38, 92, 46), (72, 130, 58), trop)
                    dry = lerp((96, 118, 58), (150, 146, 78), n2)
                    col = lerp(deep, dry, n * 0.85)
                    # mountain dust
                    if n2 > 0.72 and abs(lat) < 50:
                        col = lerp(col, (130, 124, 112), 0.45)
                # coastal sand
                ocean_neighbor = False
                for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                    xx = (x + dx) % w
                    yy = min(h - 1, max(0, y + dy))
                    if not mask[yy * w + xx]:
                        ocean_neighbor = True
                        break
                if ocean_neighbor and not ice:
                    col = lerp(col, (206, 186, 130), 0.55)
                rgh = 0.78 if not ice else 0.42
            else:
                # ocean
                depth = n2
                deep = (8, 42, 92)
                mid = (16, 86, 140)
                col = lerp(deep, mid, depth)
                if near(x, y, 2) or near(x, y, 3):
                    col = lerp(col, (64, 168, 176), 0.72)
                elif near(x, y, 5):
                    col = lerp(col, (28, 120, 156), 0.45)
                # polar sea ice
                if abs(lat) > 74:
                    col = lerp(col, (210, 222, 228), min(1.0, (abs(lat) - 74) / 10))
                rgh = 0.16
            # soft cloud veil, kept lighter over the African face (lon -10..50)
            cloud = fbm(lon * 0.85 + 100, lat * 0.85)
            cloud2 = fbm(lon * 2.2 - 30, lat * 2.2)
            cval = cloud * 0.65 + cloud2 * 0.35
            face = -20 < lon < 55 and -35 < lat < 40
            thresh = 0.60 if face else 0.52
            if cval > thresh:
                strength = min(1.0, (cval - thresh) / 0.18) * (0.42 if face else 0.62)
                col = lerp(col, (244, 246, 248), strength * 0.85)
                rgh = rgh * (1 - strength) + 0.55 * strength
            color[i] = int(max(0, min(255, col[0])))
            color[i + 1] = int(max(0, min(255, col[1])))
            color[i + 2] = int(max(0, min(255, col[2])))
            color[i + 3] = 255
            rv = int(max(0, min(255, rgh * 255)))
            rough[i] = rv
            rough[i + 1] = rv
            rough[i + 2] = rv
            rough[i + 3] = 255
    return w, h, bytes(color), bytes(rough), mask


def assign_image(name, w, h, raw):
    img = bpy.data.images.new(name, w, h, alpha=True)
    img.colorspace_settings.name = "sRGB" if "color" in name.lower() or name == "EarthColor" else "Non-Color"
    # Blender pixels are float RGBA, bottom-first? file from buffer handles orientation.
    img.pixels.foreach_set([c / 255.0 for c in raw])  # too slow and memory heavy
    return img


def image_from_bytes(name, w, h, raw, srgb=True):
    img = bpy.data.images.new(name, w, h, alpha=True)
    # faster path: write a temp PNG via Blender's packed buffer
    # pixels.foreach_set wants a flat float sequence. Build it in chunks to limit peak.
    # 1400*700*4 floats is ~15MB, fine.
    flat = [0.0] * (w * h * 4)
    # Blender image pixels are bottom-up
    for y in range(h):
        src = (h - 1 - y) * w * 4
        dst = y * w * 4
        row = raw[src:src + w * 4]
        for k, b in enumerate(row):
            flat[dst + k] = b / 255.0
    img.pixels.foreach_set(flat)
    img.pack()
    try:
        img.colorspace_settings.name = "sRGB" if srgb else "Non-Color"
    except Exception:
        pass
    return img


# ---------------------------------------------------------------------------
# scene
# ---------------------------------------------------------------------------

def look_at(obj, target, roll=0.0):
    direction = Vector(target) - obj.location
    quat = direction.to_track_quat("-Z", "Y")
    obj.rotation_euler = quat.to_euler()


def build():
    wipe()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 900
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 88
    if hasattr(scene, "eevee"):
        ee = scene.eevee
        if hasattr(ee, "taa_render_samples"):
            ee.taa_render_samples = 48
        if hasattr(ee, "use_raytracing"):
            ee.use_raytracing = True
        if hasattr(ee, "use_shadows"):
            ee.use_shadows = True
        if hasattr(ee, "use_gtao"):
            ee.use_gtao = True
    try:
        scene.view_settings.view_transform = "AgX"
    except Exception:
        pass
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass

    # camera + lights created after geometry so we can frame
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = 58
    cam_data.clip_start = 0.02
    cam_data.clip_end = 80
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam

    globe_r = 0.32
    globe_c = Vector((0.0, 0.0, 0.86))
    water_z = 0.28

    # ---- hands ----
    tones = {
        "deep": (0.45, 0.28, 0.18),
        "golden": (0.80, 0.58, 0.40),
        "light": (0.89, 0.73, 0.60),
        "medium": (0.62, 0.40, 0.27),
        "terra": (0.72, 0.46, 0.32),
        "child": (0.84, 0.62, 0.46),
    }
    # angle, tone, scale, mirror, pitch, roll, wrist_r, wrist_z, chubby, curl, spread
    roster = [
        (42, "deep", 1.06, False, 48, 8, 0.50, 0.40, 1.0, 1.0, 1.02),
        (108, "light", 0.98, True, 50, -6, 0.52, 0.39, 0.98, 1.05, 0.96),
        (168, "golden", 1.08, False, 46, 10, 0.54, 0.38, 1.02, 0.95, 1.05),
        (222, "medium", 1.0, True, 49, -8, 0.51, 0.40, 1.0, 1.08, 1.0),
        (286, "terra", 1.04, False, 47, 5, 0.53, 0.39, 0.97, 1.0, 1.04),
        (338, "child", 0.64, True, 56, -4, 0.40, 0.36, 1.18, 1.1, 1.08),
    ]
    hands = []
    wrist_xy = []
    for i, (ang, tone, scale, mirror, pitch, roll, wr, wz, chubby, curl, spread) in enumerate(roster):
        mat = skin_mat(f"Skin_{tone}_{i}", tones[tone])
        hand = build_hand(f"Hand_{i}", mat, chubby=chubby, curl=curl, spread=spread, mirror=mirror)
        hand.scale = (scale, scale, scale)
        bpy.context.view_layer.objects.active = hand
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        loc = orient_hand(hand, ang, wr, wz, pitch, roll, globe_c)
        hands.append(hand)
        wrist_xy.append((loc.x, loc.y))

    # ---- earth ----
    print("raster earth...")
    w, h, color_bytes, rough_bytes, mask = build_earth_images(1280, 640)
    print("upload images...")
    color_img = image_from_bytes("EarthColor", w, h, color_bytes, srgb=True)
    rough_img = image_from_bytes("EarthRough", w, h, rough_bytes, srgb=False)

    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=globe_r, segments=96, ring_count=48, location=globe_c
    )
    earth = bpy.context.active_object
    earth.name = "Earth"
    for p in earth.data.polygons:
        p.use_smooth = True
    # tilt: north pole leans back-right so Africa's face and the tree both read
    earth.rotation_euler = (math.radians(18), math.radians(-8), math.radians(-18))

    earth_mat = bpy.data.materials.new("EarthMat")
    earth_mat.use_nodes = True
    nt = earth_mat.node_tree
    nodes = nt.nodes
    links = nt.links
    bsdf = nodes.get("Principled BSDF")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = color_img
    tex.interpolation = "Smart"
    tex.projection = "FLAT"
    rtex = nodes.new("ShaderNodeTexImage")
    rtex.image = rough_img
    rtex.interpolation = "Smart"
    try:
        rtex.image.colorspace_settings.name = "Non-Color"
    except Exception:
        pass
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(rtex.outputs["Color"], bsdf.inputs["Roughness"])
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.5
    earth.data.materials.append(earth_mat)

    # atmosphere shell — soft blue presence, exports as a faint translucent sphere
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=globe_r * 1.035, segments=48, ring_count=24, location=globe_c
    )
    atmo = bpy.context.active_object
    atmo.name = "Atmosphere"
    atmo.rotation_euler = earth.rotation_euler
    for p in atmo.data.polygons:
        p.use_smooth = True
    atmo_mat, atmo_bsdf = new_mat(
        "Atmo", (0.62, 0.80, 1.0), rough=0.2, emit=(0.55, 0.78, 1.0), emit_str=0.35, alpha=0.10
    )
    atmo_mat.blend_method = "BLEND"
    if hasattr(atmo_mat, "surface_render_method"):
        try:
            atmo_mat.surface_render_method = "BLENDED"
        except Exception:
            pass
    if "Alpha" in atmo_bsdf.inputs:
        atmo_bsdf.inputs["Alpha"].default_value = 0.12
    atmo.data.materials.append(atmo_mat)

    # ---- olive tree, rooted on the upper front of the globe ----
    # root in world space, slightly toward the camera (-Y) and the light (+X)
    root = Vector((0.05, -0.07, globe_c.z + globe_r * 0.93))
    # pull root onto the sphere
    root = globe_c + (root - globe_c).normalized() * globe_r * 1.002

    wood, _ = new_mat("Wood", (0.62, 0.50, 0.36), rough=0.62)
    leaf_a, _ = new_mat("LeafA", (0.48, 0.56, 0.34), rough=0.55)
    leaf_b, _ = new_mat("LeafB", (0.33, 0.46, 0.26), rough=0.5)
    leaf_c, _ = new_mat("LeafC", (0.62, 0.66, 0.42), rough=0.48)
    olive_mat, _ = new_mat("Olive", (0.28, 0.32, 0.16), rough=0.4)
    soil_mat, _ = new_mat("Soil", (0.40, 0.32, 0.20), rough=0.8)

    def curve_mesh(name, pts, mat):
        obj = make_curve(name, pts, bevel_res=4)
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.convert(target="MESH")
        obj = bpy.context.active_object
        obj.name = name
        for p in obj.data.polygons:
            p.use_smooth = True
        obj.data.materials.append(mat)
        return obj

    # trunk
    trunk_pts = []
    for i in range(8):
        t = i / 7
        # gentle lean toward light and camera
        x = root.x + 0.01 * math.sin(t * 2.2) + 0.03 * t
        y = root.y - 0.02 * t - 0.015 * math.sin(t * 3)
        z = root.z + 0.34 * t
        r = 0.016 * (1 - t) + 0.005
        trunk_pts.append((x, y, z, r))
    trunk = curve_mesh("Trunk", trunk_pts, wood)

    def branch_from(t_on_trunk, direction, length, radius, n=5):
        base = Vector(trunk_pts[min(len(trunk_pts) - 1, int(t_on_trunk * (len(trunk_pts) - 1)))][:3])
        # interpolate
        idx = t_on_trunk * (len(trunk_pts) - 1)
        i0 = int(math.floor(idx))
        i1 = min(len(trunk_pts) - 1, i0 + 1)
        f = idx - i0
        base = Vector(trunk_pts[i0][:3]).lerp(Vector(trunk_pts[i1][:3]), f)
        d = Vector(direction).normalized()
        pts = []
        tip = base
        for i in range(n):
            t = i / (n - 1)
            # sag slightly then rise
            bend = Vector((0, 0, 0.08 * math.sin(t * math.pi)))
            tip = base + d * length * t + bend * length
            r = radius * (1 - 0.62 * t)
            pts.append((tip.x, tip.y, tip.z, max(r, 0.0025)))
        return pts, tip

    branches = [
        branch_from(0.42, (-0.85, 0.15, 0.55), 0.15, 0.007),
        branch_from(0.52, (0.9, -0.2, 0.5), 0.17, 0.0075),
        branch_from(0.64, (-0.3, 0.7, 0.6), 0.13, 0.006),
        branch_from(0.72, (0.25, -0.85, 0.55), 0.15, 0.0065),
        branch_from(0.84, (-0.55, -0.35, 0.75), 0.11, 0.0055),
        branch_from(0.9, (0.6, 0.25, 0.78), 0.10, 0.005),
        branch_from(0.96, (0.05, -0.2, 1.0), 0.08, 0.0045),
    ]
    leaf_spots = []
    for bi, (pts, tip) in enumerate(branches):
        curve_mesh(f"Branch_{bi}", pts, wood)
        leaf_spots.append(tip)
        # a midpoint cluster on longer branches
        mid = Vector(pts[len(pts) // 2][:3])
        leaf_spots.append(mid.lerp(tip, 0.35))

    # crown tip
    leaf_spots.append(Vector(trunk_pts[-1][:3]))

    leaf_mats = [leaf_a, leaf_b, leaf_c]
    for i, spot in enumerate(leaf_spots):
        mat = leaf_mats[i % 3]
        # 2-3 soft masses per spot
        for k in range(2):
            jitter = Vector((
                random.uniform(-0.025, 0.025),
                random.uniform(-0.025, 0.025),
                random.uniform(-0.01, 0.03),
            ))
            loc = spot + jitter
            sc = random.uniform(0.028, 0.052)
            bpy.ops.mesh.primitive_ico_sphere_add(radius=1.0, subdivisions=1, location=loc)
            leaf = bpy.context.active_object
            leaf.name = f"Leaf_{i}_{k}"
            leaf.scale = (sc * random.uniform(0.8, 1.3), sc * random.uniform(0.7, 1.2), sc * random.uniform(0.55, 0.9))
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            sm = leaf.modifiers.new("S", "SMOOTH")
            sm.iterations = 4
            sm.factor = 0.7
            bpy.ops.object.modifier_apply(modifier="S")
            for p in leaf.data.polygons:
                p.use_smooth = True
            leaf.data.materials.append(mat)

    # a few olives
    rng_spots = leaf_spots[::2]
    for i, spot in enumerate(rng_spots[:7]):
        loc = spot + Vector((random.uniform(-0.01, 0.01), random.uniform(-0.01, 0.01), -0.012))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.007, segments=10, ring_count=6, location=loc)
        ol = bpy.context.active_object
        ol.name = f"Olive_{i}"
        ol.scale = (0.8, 0.8, 1.15)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        ol.data.materials.append(olive_mat)
        for p in ol.data.polygons:
            p.use_smooth = True

    # soil mound + roots
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, segments=16, ring_count=8, location=root + Vector((0, 0, 0.005)))
    soil = bpy.context.active_object
    soil.name = "Soil"
    soil.scale = (1.3, 1.1, 0.45)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    soil.data.materials.append(soil_mat)
    for p in soil.data.polygons:
        p.use_smooth = True

    for i in range(5):
        ang = i / 5 * math.pi * 2 + 0.4
        pts = []
        for k in range(5):
            t = k / 4
            direction = Vector((math.cos(ang), math.sin(ang), 0))
            p = root + direction * (0.01 + 0.07 * t) + Vector((0, 0, 0.01 - 0.045 * t * t))
            # snap toward sphere
            radial = p - globe_c
            p = globe_c + radial.normalized() * (globe_r + 0.004 + 0.01 * (1 - t))
            pts.append((p.x, p.y, p.z, 0.008 * (1 - t) + 0.0025))
        curve_mesh(f"Root_{i}", pts, wood)

    # ---- water + plinth ----
    rings = 48
    segs = 72
    water_r = 1.02
    mesh = bpy.data.meshes.new("WaterMesh")
    verts = []
    faces = []
    for ri in range(rings):
        r = water_r * (ri / (rings - 1)) ** 0.92
        for s in range(segs):
            ang = 2 * math.pi * s / segs
            x = math.cos(ang) * r
            y = math.sin(ang) * r
            # concentric ripples, a broad center swell, and a ring around each wrist
            z = water_z
            z += 0.010 * math.sin(r * 20.0 - 0.6) * math.exp(-r * 1.15)
            z += 0.016 * math.exp(-r * r * 3.2)
            z += 0.0035 * math.sin(x * 7.5 + y * 3.2)
            for wx, wy in wrist_xy:
                d = math.hypot(x - wx, y - wy)
                z += 0.018 * math.exp(-(d * d) / 0.010)
                z += 0.010 * math.exp(-((d - 0.055) ** 2) / 0.0016)
            verts.append((x, y, z))
    # faces
    for ri in range(rings - 1):
        for s in range(segs):
            s2 = (s + 1) % segs
            a = ri * segs + s
            b = ri * segs + s2
            c = (ri + 1) * segs + s2
            d = (ri + 1) * segs + s
            if ri == 0:
                # triangle fan degenerates at center — still ok as quads of tiny r
                pass
            faces.append((a, b, c, d))
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    for p in mesh.polygons:
        p.use_smooth = True
    water = bpy.data.objects.new("Water", mesh)
    bpy.context.collection.objects.link(water)
    water_mat, water_bsdf = new_mat("WaterMat", (0.05, 0.16, 0.22), rough=0.08)
    if "Coat Weight" in water_bsdf.inputs:
        water_bsdf.inputs["Coat Weight"].default_value = 0.55
    if "IOR" in water_bsdf.inputs:
        water_bsdf.inputs["IOR"].default_value = 1.333
    if "Specular IOR Level" in water_bsdf.inputs:
        water_bsdf.inputs["Specular IOR Level"].default_value = 0.6
    water.data.materials.append(water_mat)

    # stone plinth
    bpy.ops.mesh.primitive_cylinder_add(radius=1.12, depth=0.10, location=(0, 0, water_z - 0.07), vertices=64)
    plinth = bpy.context.active_object
    plinth.name = "Plinth"
    bev = plinth.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.015
    bev.segments = 2
    bpy.ops.object.modifier_apply(modifier="Bevel")
    for p in plinth.data.polygons:
        p.use_smooth = True
    stone, _ = new_mat("Stone", (0.70, 0.66, 0.58), rough=0.72)
    plinth.data.materials.append(stone)

    # bronze inlay ring
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.78, minor_radius=0.012, major_segments=72, minor_segments=12,
        location=(0, 0, water_z + 0.004),
    )
    ring = bpy.context.active_object
    ring.name = "Inlay"
    ring.scale.z = 0.35
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bronze, _ = new_mat("Bronze", (0.62, 0.42, 0.22), rough=0.38, metallic=0.85)
    ring.data.materials.append(bronze)

    # outer stone lip, just proud of the water
    bpy.ops.mesh.primitive_torus_add(
        major_radius=1.05, minor_radius=0.028, major_segments=80, minor_segments=12,
        location=(0, 0, water_z - 0.004),
    )
    lip = bpy.context.active_object
    lip.name = "Lip"
    lip.scale.z = 0.55
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    lip.data.materials.append(stone)

    # ---- lights ----
    def add_light(name, kind, loc, energy, size, color):
        ld = bpy.data.lights.new(name, kind)
        ld.energy = energy
        ld.color = color
        if kind == "AREA":
            ld.size = size
        if kind == "SUN":
            ld.energy = energy
        obj = bpy.data.objects.new(name, ld)
        bpy.context.collection.objects.link(obj)
        obj.location = loc
        return obj

    key = add_light("Key", "AREA", (1.6, -1.3, 2.4), 180, 2.4, (1.0, 0.90, 0.78))
    look_at(key, globe_c)
    fill = add_light("Fill", "AREA", (-1.8, -0.6, 1.4), 40, 3.0, (0.65, 0.78, 1.0))
    look_at(fill, globe_c)
    rim = add_light("Rim", "AREA", (-0.4, 1.8, 1.8), 90, 1.6, (1.0, 0.84, 0.70))
    look_at(rim, globe_c)
    # earthlight — the world illuminates the hands that hold it
    earthlight = add_light("Earthlight", "POINT", globe_c, 8, 0.2, (0.55, 0.75, 1.0))
    warm = add_light("WarmBounce", "AREA", (0.2, -0.4, 0.35), 15, 1.2, (1.0, 0.78, 0.55))
    look_at(warm, globe_c + Vector((0, 0, -0.2)))

    # world gradient
    world = bpy.data.worlds["World"]
    world.use_nodes = True
    wnt = world.node_tree
    wnt.nodes.clear()
    bg = wnt.nodes.new("ShaderNodeBackground")
    out = wnt.nodes.new("ShaderNodeOutputWorld")
    geo = wnt.nodes.new("ShaderNodeNewGeometry")
    sep = wnt.nodes.new("ShaderNodeSeparateXYZ")
    add = wnt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    add.inputs[1].default_value = 0.15
    mul = wnt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 0.55
    ramp = wnt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*srgb_to_linear((0.93, 0.72, 0.55)), 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (*srgb_to_linear((0.32, 0.50, 0.72)), 1)
    mid = ramp.color_ramp.elements.new(0.38)
    mid.color = (*srgb_to_linear((0.96, 0.86, 0.74)), 1)
    hi = ramp.color_ramp.elements.new(0.72)
    hi.color = (*srgb_to_linear((0.55, 0.72, 0.86)), 1)
    bg.inputs[1].default_value = 0.85
    wnt.links.new(geo.outputs["Normal"], sep.inputs["Vector"])
    wnt.links.new(sep.outputs["Z"], add.inputs[0])
    wnt.links.new(add.outputs["Value"], mul.inputs[0])
    wnt.links.new(mul.outputs["Value"], ramp.inputs["Fac"])
    wnt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    wnt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    # hero camera — slightly above the equator, front, so palms, Africa, and the tree all read
    cam.location = Vector((0.55, -2.05, 1.18))
    look_at(cam, Vector((0.0, 0.0, 0.92)))
    cam.data.dof.use_dof = False

    # shade smooth already set
    print("SCENE READY", "hands", len(hands), "verts", sum(len(o.data.vertices) for o in bpy.data.objects if o.type == "MESH"))
    return {
        "hands": len(hands),
        "mesh_verts": sum(len(o.data.vertices) for o in bpy.data.objects if o.type == "MESH"),
        "objects": [o.name for o in bpy.data.objects if o.type == "MESH"],
    }


if __name__ == "__main__":
    result = build()
    print(result)
