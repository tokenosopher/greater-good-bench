import bpy, bmesh, math
from mathutils import Vector, Matrix
M = {m.name: m for m in bpy.data.materials}
col = bpy.context.scene.collection
def link(o, parent=None):
    col.objects.link(o)
    if parent: o.parent = parent
    return o
def mesh_obj(name, bm, material, smooth=True):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); me.materials.append(material); link(o)
    return o
def lathe(name, profile, material, segs=64, close_bottom=True, close_top=False, smooth=True):
    bm = bmesh.new(); rings = []
    for (r, z) in profile:
        rings.append([bm.verts.new((r*math.cos(2*math.pi*i/segs), r*math.sin(2*math.pi*i/segs), z)) for i in range(segs)])
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(segs):
            j = (i+1) % segs
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if close_bottom and profile[0][0] > 0: bm.faces.new(list(reversed(rings[0])))
    if close_top and profile[-1][0] > 0: bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, material, smooth)
def prim(kind, name, material, loc=(0,0,0), scale=(1,1,1), rot=(0,0,0), smooth=None, **kw):
    fn = {'cube': bpy.ops.mesh.primitive_cube_add, 'cyl': bpy.ops.mesh.primitive_cylinder_add,
          'sphere': bpy.ops.mesh.primitive_uv_sphere_add, 'torus': bpy.ops.mesh.primitive_torus_add,
          'cone': bpy.ops.mesh.primitive_cone_add}[kind]
    fn(location=loc, rotation=rot, **kw)
    o = bpy.context.active_object; o.name = name; o.scale = scale
    o.data.materials.append(material)
    if smooth is None: smooth = kind in ('sphere','torus')
    if smooth: bpy.ops.object.shade_smooth()
    return o
def text(name, body, material, loc, size=0.05, rot=(math.radians(90),0,0), extrude=0.003, align='CENTER'):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body
    cu.size = size; cu.extrude = extrude; cu.align_x = align; cu.align_y = 'CENTER'
    o = bpy.data.objects.new(name, cu); link(o)
    o.location = loc; o.rotation_euler = rot
    cu.materials.append(material)
    return o

def empty(name, loc=(0,0,0), rot=(0,0,0)):
    e = bpy.data.objects.new(name, None); link(e); e.location = loc; e.rotation_euler = rot
    e.empty_display_size = 0.05
    return e

def jug(name, x, y, fill_mat, fill_level=0.155, handle_side=1):
    root = empty(name, (x, y, 0))
    prof = [(0.050,0.0),(0.055,0.008),(0.056,0.10),(0.056,0.19),(0.059,0.205)]
    g = lathe(name+" Glass", prof, M['Glass'], segs=72)
    s = g.modifiers.new("solid", 'SOLIDIFY'); s.thickness = 0.003; s.offset = -1
    g.parent = root
    # base thick bottom
    b = lathe(name+" Base", [(0.049,0.0),(0.049,0.006)], M['Glass'], segs=72, close_top=True); b.parent = root
    w = lathe(name+" Liquid", [(0.051,0.006),(0.0525,fill_level)], fill_mat, segs=72, close_top=True); w.parent = root
    # 1 L mark ring
    bpy.ops.mesh.primitive_torus_add(major_radius=0.0565, minor_radius=0.0012, location=(x, y, fill_level+0.0005),
        major_segments=72, minor_segments=8)
    r = bpy.context.active_object; r.name = name+" 1L Mark"; r.data.materials.append(M['Accent Red'])
    r.parent = root; r.location = (0,0,fill_level+0.0005)
    # handle: half torus
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, segments=1, radius=1)  # dummy
    bm.free()
    bpy.ops.mesh.primitive_torus_add(major_radius=0.045, minor_radius=0.008, major_segments=48, minor_segments=12)
    h = bpy.context.active_object; h.name = name+" Handle"
    bm = bmesh.new(); bm.from_mesh(h.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x < -0.0], context='VERTS')
    bm.to_mesh(h.data); bm.free()
    for p in h.data.polygons: p.use_smooth = True
    h.data.materials.append(M['Glass'])
    h.parent = root; h.rotation_euler = (math.radians(90), 0, 0 if handle_side > 0 else math.pi)
    h.location = (0.050*handle_side, 0, 0.115); h.scale = (0.75, 1.3, 1)
    return root

def spoon(name, loc, rot_z=0.0, fill=None, half=False, tilt=0.0):
    root = empty(name, loc, (tilt, 0, rot_z))
    sy = 1.45
    bowl_prof = [(0.0,0.0),(0.008,0.0010),(0.013,0.0030),(0.0165,0.0058),(0.0180,0.0085)]
    b = lathe(name+" Bowl", bowl_prof, M['Spoon Steel'], segs=48)
    bm = bmesh.new(); bm.from_mesh(b.data)
    # remove center-point degenerate ring (r=0)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7); bm.to_mesh(b.data); bm.free()
    for p in b.data.polygons: p.use_smooth = True
    s = b.modifiers.new("solid", 'SOLIDIFY'); s.thickness = 0.0012; s.offset = -1
    b.scale = (1, sy, 1); b.parent = root
    # handle: tapered flat bar from bowl rear (y=+0.026) to y=+0.13, rising slightly
    bm = bmesh.new()
    pts = [(0.0, 0.024, 0.0080, 0.0030), (0.0, 0.045, 0.0105, 0.0028), (0.0, 0.075, 0.0125, 0.0045),
           (0.0, 0.105, 0.0135, 0.0065), (0.0, 0.125, 0.0138, 0.0068), (0.0, 0.135, 0.0138, 0.0040)]
    rings = []
    for (px, py, pz, hw) in pts:
        t = 0.0011
        rings.append([bm.verts.new((px-hw, py, pz-t)), bm.verts.new((px+hw, py, pz-t)),
                      bm.verts.new((px+hw, py, pz+t)), bm.verts.new((px-hw, py, pz+t))])
    for a, c in zip(rings[:-1], rings[1:]):
        for i in range(4):
            j = (i+1) % 4
            bm.faces.new((a[i], a[j], c[j], c[i]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    hnd = mesh_obj(name+" Handle", bm, M['Spoon Steel'], smooth=False)
    sub = hnd.modifiers.new("sub", 'SUBSURF'); sub.levels = 2; sub.render_levels = 2
    hnd.parent = root
    if fill is not None:
        fprof = [(0.0,0.0012),(0.0075,0.0021),(0.0123,0.0040),(0.0157,0.0065),(0.0171,0.0080)]
        f = lathe(name+" Fill", fprof, fill, segs=48, close_top=True)
        bm = bmesh.new(); bm.from_mesh(f.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
        if half:
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
            r = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0,0,0), plane_no=(0,1,0), clear_outer=True)
            edges = [e for e in r['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
            bmesh.ops.holes_fill(bm, edges=edges)
        bm.to_mesh(f.data); bm.free()
        for p in f.data.polygons: p.use_smooth = False
        f.scale = (1, sy, 1); f.parent = root
        # sugar/salt texture: small displacement via noise
    return root
