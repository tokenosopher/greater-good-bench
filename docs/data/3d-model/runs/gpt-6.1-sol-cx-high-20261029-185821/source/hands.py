from mathutils import Matrix
def catmull(points,n=7):
    out=[]
    for i in range(len(points)-1):
        a=Vector(points[max(0,i-1)]); b=Vector(points[i]); c=Vector(points[i+1]); d=Vector(points[min(len(points)-1,i+2)])
        for j in range(n):
            t=j/n
            out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    out.append(Vector(points[-1])); return out
def tube(name,coords,radii,ma):
    # Last component stores radius so the spline also smooths the taper.
    pp=catmull([(*co,ra) for co,ra in zip(coords,radii)])
    vs=[]; fs=[]; N=16
    for i,p in enumerate(pp):
        pos=Vector(p[:3]); tan=Vector(pp[min(i+1,len(pp)-1)][:3])-Vector(pp[max(0,i-1)][:3]); tan.normalize()
        side=tan.cross(Vector((0,1,0)))
        if side.length<.01: side=tan.cross(Vector((1,0,0)))
        side.normalize(); other=tan.cross(side).normalized()
        for j in range(N):
            a=2*math.pi*j/N; vs.append(tuple(pos+p[3]*(math.cos(a)*side+math.sin(a)*other)))
    for i in range(len(pp)-1):
        for j in range(N):
            a=i*N+j; b=i*N+(j+1)%N; fs.append((a,b,b+N,a+N))
    fs.append(tuple(range(N-1,-1,-1))); fs.append(tuple((len(pp)-1)*N+j for j in range(N)))
    me=bpy.data.meshes.new(name); me.from_pydata(vs,[],fs); me.update(); ob=bpy.data.objects.new(name,me); scene.collection.objects.link(ob); assign(ob,ma); smooth(ob); return ob
for h,deg in enumerate([-90,-18,54,126,198]):
    ma=mats['hand'+str(h)]; parts=[]; angle=math.radians(deg)
    # Local Y is the outward radial direction; local X spans the palm.
    rot=Matrix(((math.sin(angle),math.cos(angle),0),(-math.cos(angle),math.sin(angle),0),(0,0,1)))
    def piece(o):
        o.location=rot@o.location; o.rotation_euler=rot.to_euler(); parts.append(o); return o
    armcoords=[(0,1.88,.51),(.03,1.83,.80),(.03,1.62,1.14),(.01,1.29,1.65),(0,1.07,2.05)]
    piece(tube('Arm',armcoords,[.29,.28,.255,.195,.20],ma))
    piece(sphere('Palm',(0,.99,2.30),(.405,.205,.43),ma))
    xs=[-.29,-.10,.11,.30]; heights=[3.10,3.25,3.17,2.98]
    for f,(x,zt) in enumerate(zip(xs,heights)):
        def surf(xx,zz): return math.sqrt(max(.01,R*R-(zz-3.65)**2-xx*xx))+.075
        start=2.52 if f<3 else 2.48
        coords=[(x,.98,start),(x*1.09,surf(x*1.09,2.78),2.78),(x*1.17,surf(x*1.17,zt-.12),zt-.12),(x*1.13,surf(x*1.13,zt),zt)]
        piece(tube('Finger '+str(f),coords,[.105 if f<3 else .092,.097 if f<3 else .085,.088 if f<3 else .077,.065],ma))
        piece(sphere('Soft fingertip',coords[-1],(.067,.067,.075),ma,20,12))
    tc=[(-.28,.99,2.11),(-.48,1.02,2.32),(-.60,1.03,2.51),(-.57,1.10,2.69)]
    piece(tube('Opposable thumb',tc,[.15,.13,.11,.08],ma))
    piece(sphere('Thumb tip',tc[-1],(.082,.082,.09),ma,20,12))
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join(); hand=bpy.context.object; hand.name='Hand '+str(h+1)+' | shared responsibility'
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    rem=hand.modifiers.new('Sculpted continuous ceramic','REMESH'); rem.mode='VOXEL'; rem.voxel_size=.027; rem.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=rem.name)
    sm=hand.modifiers.new('Hand finished surface','SMOOTH'); sm.factor=.65; sm.iterations=5; bpy.ops.object.modifier_apply(modifier=sm.name)
    dec=hand.modifiers.new('Efficient sculpt topology','DECIMATE'); dec.ratio=.48; bpy.ops.object.modifier_apply(modifier=dec.name)
    smooth(hand)
    # A restrained brass cuff gives each ceramic arm a deliberate finished foot.
    pts=[tuple(rot@Vector((.292*math.cos(a),1.875+.292*math.sin(a),.58))) for a in [j*2*math.pi/80 for j in range(80)]]
    path('Brass foot | hand '+str(h+1),pts,.018,mats['gold'],True)
