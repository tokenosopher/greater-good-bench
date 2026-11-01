import bpy, math, os
from mathutils import Vector
scene=bpy.context.scene
R=1.35
C=Vector((0,0,3.65))
mats={k:bpy.data.materials[n] for k,n in {'base':'Midnight | glazed stone','gold':'Brushed champagne brass','ocean':'Ocean | deep petrol enamel','land':'Land | celadon porcelain','grid':'Quiet cartographic lines','leaf':'New growth | malachite','vein':'Leaf midrib | spring green','floor':'Warm gallery plaster',**{'hand'+str(i):'Fired earth | hand '+str(i+1) for i in range(5)}}.items()}
def assign(o,m):
    o.data.materials.append(m)
    return o
def smooth(o):
    if o.type=='MESH':
        for p in o.data.polygons: p.use_smooth=True
    return o
def sphere(name,loc,scale,ma,seg=32,rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    assign(o,ma); smooth(o)
    return o
def path(name,pts,radius,ma,cyclic=False):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.resolution_u=16; cu.bevel_depth=radius; cu.bevel_resolution=3
    sp=cu.splines.new('POLY'); sp.points.add(len(pts)-1)
    for p,co in zip(sp.points,pts): p.co=(*co,1)
    sp.use_cyclic_u=cyclic
    ob=bpy.data.objects.new(name,cu); scene.collection.objects.link(ob); assign(ob,ma)
    return ob
def globe(lon,lat,r=R+.006):
    lo=math.radians(lon); la=math.radians(lat)
    return (r*math.cos(la)*math.sin(lo),-r*math.cos(la)*math.cos(lo),3.65+r*math.sin(la))
