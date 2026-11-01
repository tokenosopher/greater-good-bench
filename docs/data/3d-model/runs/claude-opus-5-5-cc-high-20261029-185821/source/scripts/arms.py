from mathutils import Quaternion
def capsule(name, a, b, r, mat):
    a = Vector(a); b = Vector(b); d = b - a
    c = prim('cyl', name, mat, loc=(a+b)/2, vertices=20, smooth=True)
    c.scale = (r, r, d.length/2)
    c.rotation_euler = d.to_track_quat('Z','Y').to_euler()
    for i,p in enumerate((a,b)):
        prim('sphere', f"{name} Joint{i}", mat, loc=p, scale=(r,r,r), segments=20, ring_count=10)
    return c
for o in list(bpy.data.objects):
    if o.name.startswith(("Caregiver Arm","Caregiver Hand","Child Arm","Child Hand")):
        bpy.data.objects.remove(o)
child = bpy.data.objects["Child"]; adult = bpy.data.objects["Caregiver"]; cup = bpy.data.objects["Cup of ORS"]
bpy.context.view_layer.update()
cfa = child.rotation_euler.z
fwd = Vector((math.cos(cfa), math.sin(cfa), 0)); side = Vector((-fwd.y, fwd.x, 0))
cup_pos = cup.location.copy()
CW = child.matrix_world; AW = adult.matrix_world
for k,sgn in enumerate((1,-1)):
    sh = CW @ Vector((0.0, sgn*0.030, 0.165))
    hand = cup_pos + side*sgn*0.019 + Vector((0,0,-0.004)) - fwd*0.004
    elbow = (sh+hand)/2 + Vector((0,0,-0.022)) + side*sgn*0.006
    capsule(f"Child Arm{k} Upper", sh, elbow, 0.0062, M['Cloth Yellow'])
    capsule(f"Child Arm{k} Fore", elbow, hand, 0.0055, M['Skin Child'])
    prim('sphere', f"Child Hand{k}", M['Skin Child'], loc=hand, scale=(0.0075,)*3, segments=16, ring_count=8)
sh = AW @ Vector((0.0, 0.032, 0.168))
hand = cup_pos + Vector((0,0,-0.022)) - fwd*0.004 + side*0.004
elbow = sh + (hand-sh)*0.45 + Vector((0,0,-0.05))
capsule("Caregiver Arm Upper", sh, elbow, 0.0095, M['Cloth Teal'])
capsule("Caregiver Arm Fore", elbow, hand, 0.0085, M['Skin Warm'])
prim('sphere', "Caregiver Hand", M['Skin Warm'], loc=hand, scale=(0.011,0.011,0.009), segments=16, ring_count=8)
sh2 = AW @ Vector((0.0, -0.032, 0.168))
back = CW @ Vector((-0.030, -0.012, 0.115))
el2 = sh2 + (back-sh2)*0.45 + Vector((0,0,-0.05))
capsule("Caregiver Arm2 Upper", sh2, el2, 0.0095, M['Cloth Teal'])
capsule("Caregiver Arm2 Fore", el2, back, 0.0085, M['Skin Warm'])
prim('sphere', "Caregiver Hand2", M['Skin Warm'], loc=back, scale=(0.011,)*3, segments=16, ring_count=8)
