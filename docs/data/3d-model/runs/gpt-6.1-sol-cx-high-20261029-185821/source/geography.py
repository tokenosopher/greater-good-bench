from mathutils.geometry import tessellate_polygon
continents={
'Africa':[(-17,36),(-5,36),(10,37),(20,33),(32,31),(34,23),(43,12),(51,11),(48,3),(42,-5),(39,-16),(33,-26),(26,-35),(18,-34),(12,-23),(10,-6),(5,4),(-4,5),(-15,11),(-17,22)],
'Eurasia':[(-10,36),(-9,43),(-1,44),(-5,49),(-1,51),(6,54),(8,58),(5,62),(15,70),(28,71),(32,65),(44,68),(57,70),(75,73),(100,77),(118,73),(139,72),(160,66),(177,65),(179,57),(165,60),(155,55),(163,51),(155,47),(145,48),(142,41),(133,43),(130,38),(128,34),(121,39),(119,31),(122,25),(114,22),(109,18),(108,10),(103,2),(99,7),(98,17),(93,22),(88,21),(80,7),(75,13),(70,23),(61,25),(56,17),(49,12),(43,13),(36,30),(29,36),(25,40),(23,36),(20,40),(16,40),(15,45),(12,45),(8,43),(3,43),(-1,36)],
'North America':[(-168,66),(-155,71),(-140,69),(-130,71),(-118,75),(-100,78),(-84,74),(-70,62),(-61,54),(-54,52),(-60,46),(-68,44),(-75,35),(-81,26),(-81,30),(-89,29),(-87,22),(-90,18),(-86,16),(-83,10),(-78,8),(-77,9),(-85,19),(-96,20),(-106,24),(-114,31),(-122,39),(-129,51),(-137,58),(-150,61),(-162,58),(-168,61)],
'South America':[(-81,12),(-72,11),(-65,10),(-59,7),(-51,4),(-48,-1),(-35,-6),(-39,-17),(-42,-23),(-49,-28),(-53,-34),(-61,-40),(-66,-55),(-73,-51),(-75,-39),(-72,-27),(-75,-15),(-81,-5)],
'Australia':[(113,-22),(114,-33),(123,-35),(131,-32),(138,-35),(145,-39),(151,-33),(153,-25),(146,-17),(142,-11),(137,-15),(130,-12),(123,-15),(122,-18)],
'Greenland':[(-53,60),(-42,61),(-33,68),(-20,76),(-26,82),(-43,83),(-59,77),(-64,68)],
'Madagascar':[(49,-12),(50,-17),(46,-26),(44,-24),(45,-17)],
'Britain':[(-5,50),(1,51),(-1,55),(-3,59),(-6,58),(-5,54)],
'Ireland':[(-10,51),(-6,51),(-6,55),(-9,55)],
'Japan':[(130,31),(132,34),(136,35),(140,40),(142,44),(145,44),(142,39),(138,34),(133,32)],
'New Zealand north':[(173,-35),(178,-38),(176,-41),(174,-40)],
'New Zealand south':[(173,-41),(171,-45),(167,-47),(166,-45),(170,-42)],
'Sumatra':[(95,5),(101,-1),(105,-6),(102,-6),(97,0)],
'Borneo':[(109,7),(117,6),(119,1),(115,-4),(110,-3)],
'Java':[(105,-6),(114,-7),(115,-9),(107,-8)],
'New Guinea':[(131,-2),(140,-3),(150,-6),(149,-10),(141,-8),(134,-4)]}
def splittri(a,b,c,level,verts,faces):
    if level:
        ab=(a+b)*.5; bc=(b+c)*.5; ca=(c+a)*.5
        for tri in [(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)]: splittri(*tri,level-1,verts,faces)
    else:
        i=len(verts); verts.extend([globe(p.x,p.y,R+.022) for p in (a,b,c)]); faces.append((i,i+1,i+2))
for name,coords in continents.items():
    v2=[Vector((x,y,0)) for x,y in coords]; vs=[]; fs=[]
    for tri in tessellate_polygon([v2]): splittri(*(v2[i] for i in tri),3 if len(coords)>15 else 2,vs,fs)
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(vs,[],fs); mesh.update()
    ob=bpy.data.objects.new('Porcelain relief | '+name,mesh); scene.collection.objects.link(ob); assign(ob,mats['land']); smooth(ob)
    outline=[]
    for a,b in zip(coords,coords[1:]+coords[:1]):
        n=max(2,int(math.hypot(a[0]-b[0],a[1]-b[1])/2)+1)
        outline.extend([globe(a[0]+(b[0]-a[0])*j/n,a[1]+(b[1]-a[1])*j/n,R+.023) for j in range(n)])
    path('Brass coastline | '+name,outline,.007,mats['gold'],True)
path('A future worth tending | stem',[(0,0,4.98),(.02,0,5.15),(.08,.02,5.36),(.12,.02,5.57)],.035,mats['gold'])
def leaf(name,base,tip,width,bend):
    base=Vector(base); tip=Vector(tip); d=tip-base; side=d.cross(Vector((0,0,1))).normalized(); vs=[]; fs=[]
    N=20; W=10
    for i in range(N+1):
        t=i/N; mid=base+d*t+Vector((0,0,bend*math.sin(math.pi*t)))
        for j in range(W+1):
            q=(j/W)*2-1; p=mid+side*(q*width*math.sin(math.pi*t)**.8)
            p.z+=.07*(1-q*q)*math.sin(math.pi*t); vs.append(tuple(p))
    for i in range(N):
        for j in range(W):
            k=i*(W+1)+j; fs.append((k,k+1,k+W+2,k+W+1))
    me=bpy.data.meshes.new(name); me.from_pydata(vs,[],fs); me.update(); ob=bpy.data.objects.new(name,me); scene.collection.objects.link(ob); assign(ob,mats['leaf']); smooth(ob)
    sol=ob.modifiers.new('Porcelain leaf thickness','SOLIDIFY'); sol.thickness=.018
    pts=[tuple(base+d*(i/30)+Vector((0,0,(bend+.07)*math.sin(math.pi*i/30)+.012))) for i in range(31)]
    path(name+' | midrib',pts,.009,mats['vein'])
leaf('04 | first leaf',(.04,0,5.2),(-.66,-.06,5.72),.25,.10)
leaf('05 | next leaf',(.1,.02,5.45),(.75,.09,5.98),.28,.12)
