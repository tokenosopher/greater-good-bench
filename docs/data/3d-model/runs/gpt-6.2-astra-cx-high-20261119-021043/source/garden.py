import bpy, math, os, random, bmesh
from mathutils import Vector
from math import sin, cos, pi, sqrt, exp
from collections import defaultdict
random.seed(518)
R=random.uniform
V=Vector
for o in list(bpy.data.objects): bpy.data.objects.remove(o,do_unlink=True)
sc=bpy.context.scene
mats={}
def mat(name,h,rough=.78,metal=0):
    rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    col=[(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4) for x in rgb]+[1]
    m=bpy.data.materials.new(name);m.diffuse_color=col;m.use_nodes=True
    p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=col;p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    mats[name]=m;return name
for name,h in {'enamel':'154749','rim':'376463','ivory':'F7EDD1','gold':'E3AF5A','road':'52636A','road2':'657577','pavement':'BCB8A7','curblight':'D6CCB8','curbdark':'948D81','native':'B47551','native dark':'945C47','sand':'DDA66C','pebbles':'A08B79','loam':'774C3B','mulch':'503E31','loam2':'8A604B','soil marks':'9F7359','chalk':'D9C1A0','gravel0':'887F71','gravel1':'BAA58C','gravel2':'776F63','gravel3':'D2B99A','root':'D3A475','root pale':'E1B78A','green0':'275A45','green1':'457650','green2':'64914E','green3':'92B157','green4':'AAC660','sedge':'748846','sedge lite':'ADC276','sedge dark':'526D41','bark':'735441','birch':'D9BB8F','barklight':'ECD6AF','lent':'7F6853','coral':'EE5938','coralLight':'FF8150','coralDark':'C73C2E','coat':'E6AB43','coat2':'BB7E31','hair':'352D2A','skin':'9D6548','boots':'433C33','trousers':'204E59','purple':'805CB6','purple lite':'B3A0D9','flower':'ED9261','flower lite':'F8BB82','cone':'89482D','pollen':'EDBF54','foam':'C0EBDA','metal':'334E4D','bgr':'C4CFC6'}.items(): mat(name,h)
mat('water','42A8AE',.22,.18);mat('water shade','338C98',.25,.16);mat('water glint','85D2C7',.28,.12)
group='Ground'
buf={}
def add(v,f,m):
    key=(group,m)
    if key not in buf: buf[key]=([],[])
    vs,fs=buf[key];n=len(vs);vs.extend([tuple(p) for p in v]);fs.extend([tuple(n+i for i in a) for a in f])
def flush():
    for (g,m),(v,f) in buf.items():
        me=bpy.data.meshes.new(g+' • '+m);me.from_pydata(v,[],f);me.materials.append(mats[m]);me.update()
        ob=bpy.data.objects.new(me.name,me);sc.collection.objects.link(ob)
    buf.clear()
def box(name,xyz,dims,m,r=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=xyz);o=bpy.context.object;o.name=name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mats[m])
    if r:
        b=o.modifiers.new('Rounded edges','BEVEL');b.width=r;b.segments=3
        n=o.modifiers.new('Face normals','WEIGHTED_NORMAL')
    return o
def tube(points,rads,m,n=7):
    ps=list(map(V,points));vs=[];fs=[]
    prev=None
    for i,p in enumerate(ps):
        d=(ps[min(i+1,len(ps)-1)]-ps[max(i-1,0)]).normalized()
        if prev is None: a=d.cross(V((0,1,0) if abs(d.y)<.9 else (1,0,0))).normalized()
        else: a=(prev-d*d.dot(prev)).normalized()
        b=d.cross(a);prev=a
        for j in range(n):vs.append(p+rads[i]*(a*cos(2*pi*j/n)+b*sin(2*pi*j/n)))
        if i:
            for j in range(n):fs.append(((i-1)*n+j,(i-1)*n+(j+1)%n,i*n+(j+1)%n,i*n+j))
    fs.append(tuple(reversed(range(n))));fs.append(tuple(range(len(vs)-n,len(vs))));add(vs,fs,m)
def rod(a,b,r,m,n=8):tube([a,b],[r,r],m,n)
def ball(p,s,m,n=10,k=6,tilt=0):
    x,y,z=p;vs=[(x,y,z-s[2])];fs=[]
    for i in range(1,k):
        t=-pi/2+pi*i/k
        for j in range(n):
            a=j*2*pi/n;u=s[0]*cos(t)*cos(a);v=s[1]*cos(t)*sin(a)
            vs.append((x+u*cos(tilt)-v*sin(tilt),y+u*sin(tilt)+v*cos(tilt),z+s[2]*sin(t)))
    top=len(vs);vs.append((x,y,z+s[2]))
    for j in range(n):fs.append((0,1+(j+1)%n,1+j));fs.append((top,top-n+j,top-n+(j+1)%n))
    for i in range(k-2):
        for j in range(n):
            a=1+i*n;fs.append((a+j,a+(j+1)%n,a+n+(j+1)%n,a+n+j))
    add(vs,fs,m)
def stripline(pts,width,m):tube(pts,[width]*len(pts),m,5)
def leaf(p,delta,width,m,bow=.04):
    p=V(p);d=V(delta);s=V((-d.y,d.x,0)).normalized()*width
    mid=p+d*.43;crest=mid+V((0,0,bow))
    lo=p+d*.20;hi=p+d*.68
    add([p,lo+s*.69,mid+s,hi+s*.72,p+d,hi-s*.63,mid-s,lo-s*.70,crest],[((i+1)%8,i,8) for i in range(8)],m)
def txt(body,loc,size,m,font=None,spacing=1,align='LEFT'):
    c=bpy.data.curves.new(body,'FONT');c.body=body;c.size=size;c.align_x=align;c.space_character=spacing;c.extrude=.0015;c.resolution_u=4
    if font: c.font=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/'+font,check_existing=True)
    o=bpy.data.objects.new(body,c);sc.collection.objects.link(o);o.location=loc;o.rotation_euler.x=pi/2;c.materials.append(mats[m]);return o
# Lacquered plinth and brass hairline
box('Foot',(0,0,.11),(10.1,5.31,.22),'rim',.10)
box('Deep teal exhibition plinth',(0,0,.485),(10.22,5.42,.79),'enamel',.10)
box('Fine brass reveal',(0,0,.88),(10.08,5.28,.042),'gold',.018)
txt('A softer street',(-4.35,-2.715,.29),.65,'ivory','Georgia.ttf')
txt('THE RAIN GARDEN',(.85,-2.715,.50),.29,'ivory','DIN Alternate Bold.ttf',1.14)
txt('STORMWATER  /  STREET SECTION',(.86,-2.715,.27),.145,'gold','DIN Alternate Bold.ttf',1.13)
# Badge, concentric ripple
for i,r in enumerate([.13,.084,.037]):
    pts=[(-4.70+r*cos(a*2*pi/40),-2.718,.50+.67*r*sin(a*2*pi/40)) for a in range(41)];stripline(pts,.009,'gold')
rod((.64,-2.715,.26),(.64,-2.715,.67),.009,'gold')
# modeled earth with undulating horizons and dished planting surface
X=5;Y=2.59;nx=66;ny=39
def center(x):return -.42+.21*sin(x*1.17)+.12*cos(x*.83)
def surface(x,y):
    d=y-center(x)
    if y>=1.38: return 2.61
    return 2.16+.40*(1-exp(-(d/(.91+.1*cos(x)))**2))+.046*sin(2.9*x+1.1*y)+.021*cos(3.4*y-1.3*x)+.31*(max(0,abs(x)-3.65)/1.35)**2
def H(i,x,y):
    w=.046*sin(x*1.46+y*.7)+.025*cos(x*2.23-y*1.8)
    return [.90,1.19+w,1.43+.82*w+.024*cos(x+y),1.48+.8*w,1.65+.65*w,surface(x,y)-.078,surface(x,y)][i]
xs=[-X+2*X*j/nx for j in range(nx+1)];ys=[-Y+2*Y*j/ny for j in range(ny+1)]
per=[(x,-Y) for x in xs]+[(X,y) for y in ys[1:]]+[(x,Y) for x in xs[-2::-1]]+[(-X,y) for y in ys[-2:0:-1]]
for i,m in enumerate(['native dark','native','sand','pebbles','loam','mulch']):
    vs=[(x,y,H(j,x,y)) for j in (i,i+1) for x,y in per];n=len(per);add(vs,[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)],m)
vs=[(x,y,surface(x,y)) for x in xs for y in ys];f=[]
for i in range(nx):
    for j in range(ny):
        a=i*(ny+1)+j;b=a+ny+1;f.extend([(a,b,b+1),(a,b+1,a+1)])
add(vs,f,'mulch')
# Natural aggregate revealed in the cut 
group='Mineral inclusions'
for i in range(1250):
    side=random.choices(['f','b','l','r'],[10,10,5,5])[0];x=R(-4.95,4.95);y=R(-2.54,2.54)
    if side in 'fb':y= -Y if side=='f' else Y
    else:x= -X if side=='l' else X
    u=random.random()
    z=R(H(2,x,y)+.026,H(4,x,y)-.025) if u<.73 else R(.96,surface(x,y)-.10)
    r=R(.018,.072) if u<.73 else R(.01,.046);s=(r,R(.7,1.2)*r,r*R(.34,.68))
    ball((x,y,z),s,random.choice(['gravel0','gravel1','gravel2','gravel3'] if u<.73 else ['loam2','soil marks','chalk']),7,4,R(0,6))
# Small chips and mineral flecks sit flush with the cut faces.
for side,nmarks in [('front',950),('back',800),('left',440),('right',440)]:
    for j in range(nmarks):
        if side in ['front','back']:
            x=R(-4.97,4.97);y=(-1 if side=='front' else 1)*(Y+.002);along=V((1,0,0))
        else:
            x=(-1 if side=='left' else 1)*(X+.002);y=R(-2.55,2.55);along=V((0,1,0))
        z=R(.924,surface(x,y)-.022);p=V((x,y,z));up=V((0,0,1));lo=z<H(2,x,y)
        l=R(.009,.048)*(1.75 if lo else 1);h=R(.003,.012);incl=R(-.35,.35)*l
        ps=[p-along*l,p-along*l*.27+up*h,p+along*l+up*incl,p+along*l*.35-up*h*.7]
        add(ps,[(0,1,2,3)],random.choice(['native dark','soil marks','native'] if lo else ['loam','loam2','soil marks']))
# Root fans engraved on section, shaped tapers and forklets
group='Exposed roots'
def root(x,z,dx,dz,w,level):
    pts=[V((x,-Y-.008,z))]
    for i in range(1,6):pts.append(V((x+dx*i/5+.032*sin(i*.95+dx*4),-Y-.012,z+dz*i/5)))
    tube(pts,[w*(1-.87*j/5) for j in range(6)],'root' if level>0 else 'root pale',5)
    if level:
        for j in [2,4]:
            p=pts[j];root(p.x,p.z,dx*R(.2,.65)+R(-.21,.21),dz*R(.32,.56),w*.46,level-1)
for x in [-4.56,-3.64,-3.5,-1.5,-.85,.13,1.72,2.97,3.40,4.4]:
    for j in range(4):root(x+R(-.04,.04),surface(x,-Y)-.02,R(-.40,.40),R(-.86,-.35),R(.012,.024),2)
# Back street, masonry and generous curb opening
group='Street'
box('Street foundation',(0,1.966,2.635),(10,1.248,.105),'curbdark',.018)
box('Bluestone asphalt',(0,1.966,2.71),(10,1.248,.098),'road',.022)
for a,b in [(-5,-3.11),(-1.63,5)]:
    ct=math.ceil((b-a)/.92);step=(b-a)/ct
    for j in range(ct):box('Chamfered kerbstone',(a+step*(j+.5),1.35,2.78),(step-.017,.24,.29),'curblight',.033)
# A paved corner meets the carriageway beside the inlet.
box('Corner • pavement bed',(-4.055,1.975,2.826),(1.89,1.225,.138),'curbdark',.024)
for i in range(3):
    for j in range(2):
        box('Corner • dressed paving',(-5+(i+.5)*.63,1.405+(j+.5)*.591,2.908),(.619,.578,.042),'pavement' if (i+j)%3 else 'curblight',.012)
for i in [0,1,2]:
    box('Lane stripe',(i*1.90+.34,2.39,2.765),(.86,.068,.012),'pavement',.008)
# Pool as contours from actual surface at one elevation
group='Captured rain'
waterZ=2.303
def shore(x,sgn):
    cy=center(x)
    if surface(x,cy)>waterZ:return cy
    a=0;b=1.5
    for _ in range(18):
        d=(a+b)/2
        if surface(x,cy+sgn*d)>waterZ:b=d
        else:a=d
    return cy+sgn*(a+b)/2
cols=105;vs=[];fs=[]
for i in range(cols+1):
    x=-4.91+9.82*i/cols;vs.extend([(x,shore(x,-1),waterZ),(x,shore(x,1),waterZ)])
    if i:fs.append((2*i-2,2*i,2*i+1,2*i-1))
add(vs,fs,'water')
# Falling ribbon of runoff across lip into water
pts=[(-2.29,2.55,2.767,.07),(-2.38,2.22,2.768,.10),(-2.33,1.84,2.768,.14),(-2.42,1.42,2.768,.23),(-2.40,1.34,2.762,.23),(-2.39,1.29,2.731,.24),(-2.38,1.26,2.615,.235)]
for j in range(18):
    y=1.22-j*.088;x=-2.38+.20*sin((1.2-y)*2.6);pts.append((x,y,max(waterZ+.006,surface(x,y)+.028),.23+.11*j/17))
# The sheet follows the soil across its width, wetting both banks.
v=[];f=[];lines=[[],[],[]]
for i,(x,y,z,w) in enumerate(pts):
    for j in range(9):
        s=-1+j/4;xx=x+s*w*(1+.06*sin(3*y+1.7*s));zz=z
        if y<=1.22:
            zz=max(waterZ+.003,surface(xx,y)+.010+.006*(1-s*s))
        v.append((xx,y,zz))
        if j in (1,4,7):lines[(1,4,7).index(j)].append((xx,y,zz+.004))
        if i and j:
            a=9*i+j;f.append((a-10,a-1,a,a-9))
add(v,f,'water')
for j,ln in enumerate(lines):stripline(ln[3:15+j*2],.0055,'water glint')
# Gutter water gathers against the stone and spreads into the opening.
v=[];f=[]
for k in range(56):
    t=k/55;x=-2.47+3.59*t;y0=1.465
    y1=y0+.30*(1-t)**.65*(.78+.20*cos(t*19)+.08*sin(t*32))
    v.extend([(x,y0,2.7685),(x,y1,2.7685)])
    if k:f.append((2*k-2,2*k,2*k+1,2*k-1))
add(v,f,'water')
for j in range(5):
    cx=-2.16+j*.47
    stripline([(cx+k*.035,1.525+.006*cos(k*.6+j),2.773) for k in range(5+j%3)],.0048,'water glint')
# Specular ripple arcs
for i in range(34):
    x=R(-4.54,4.55);y=center(x)+R(-.23,.23);r=R(.09,.35)
    if shore(x,1)-shore(x,-1)<.39: continue
    a=R(0,6);pts=[(x+r*cos(a+k*.15),y+r*.53*sin(a+k*.15),waterZ+.007) for k in range(random.randint(7,22))]
    stripline(pts,R(.005,.011),random.choice(['water glint','water shade','foam']))
# River cobbles, mulch chips across planted banks
group='River-washed stones'
for i in range(210):
    x=R(-4.87,4.87);y=shore(x,random.choice([-1,1]))+R(-.25,.25)
    if random.random()<.25:x=R(-2.84,-1.84);y=R(.1,1.18)
    if abs(x+2.38)<.28 and y>.17:continue
    r=R(.045,.145)*(1.45 if i%8==0 else 1)
    ball((x,y,surface(x,y)+r*.14),(r*R(.8,1.35),r*.77,r*R(.44,.72)),random.choice(['gravel0','gravel1','gravel2','gravel3','curbdark']),random.choice([7,8,9]),5,R(0,6))
for i in range(400):
    x=R(-4.97,4.97);y=R(-2.54,1.22);z=surface(x,y)
    if z<waterZ+.012:continue
    ball((x,y,z+.012),(R(.026,.09),R(.009,.029),.012),random.choice(['loam2','loam','soil marks']),6,3,R(0,6))
# Sculpted clumps of wet meadow grasses, each blade has a folded midrib
group='Sedges and rushes'
def grass(x,y,scale,seedheads=False):
    z=surface(x,y)-.012
    greens=random.choice([['sedge','sedge lite','sedge dark'],['green1','green2','green3'],['green0','green1','green2']])
    for k in range(random.randint(12,22)):
        ang=R(0,2*pi);lx=cos(ang);ly=sin(ang);h=R(.21,.67)*scale;w=R(.017,.037)*scale;l=R(.16,.49)*scale;rx=x+R(-.043,.043);ry=y+R(-.043,.043)
        v=[];f=[]
        for j in range(6):
            t=j/5;ww=w*(1-t*.98);cx=rx+lx*l*t**1.52;cy=ry+ly*l*t**1.52;cz=z+h*(1.8*t-.81*t*t)-l*.52*t**2.7
            v.extend([(cx-ly*ww,cy+lx*ww,cz),(cx+.3*ww*lx,cy+.3*ww*ly,cz+.38*ww),(cx+ly*ww,cy-lx*ww,cz)])
            if j:
                a=3*j;f.extend([(a-3,a,a+1,a-2),(a-2,a+1,a+2,a-1)])
        add(v,f,random.choice(greens))
    if seedheads:
        for j in range(random.randint(3,5)):
            a=R(0,6.28);d=V((.15*cos(a),.15*sin(a),R(.50,.84)))*scale;p=V((x,y,z))
            tube([p,p+d*.62,p+d],[.012,.009,.005],'sedge',5)
            for n in range(6):
                c=p+d*(.78+n*.040);ang=n*2.4;tip=c+V((.052*cos(ang),.052*sin(ang),.076))*scale
                tube([c,(c+tip)*.5,tip],[.006,.018,.001],'gold' if n%3==0 else 'sedge lite',5)
for i in range(120):
    x=R(-4.80,4.80);y=R(-2.43,1.16);z=surface(x,y)
    if z<waterZ+.012 or (abs(x+2.4)<.51 and y>-.40):continue
    grass(x,y,R(.64,1.63),i%4==0)
for x in [-4.55,-3.6,-1.5,-.85,.14,1.72,3.39,4.39]:grass(x,-2.546,R(.8,1.25),True)
# Blooming drifts: cone flowers, purple spires and cream umbels
def daisy(x,y,z,s,a):
    p=V((x,y,z));d=V((.09*cos(a),.09*sin(a),s))
    tube([p,p+d*.55,p+d],[.014,.012,.009],'green1',6)
    for j in (1,2,3):
        t=j*.205;b=a+j*2.5;leaf(p+d*t,(.16*cos(b),.16*sin(b),.075),.043,'green2')
    head=p+d;m=random.choice(['flower','flower lite','pollen'])
    for j in range(11):
        b=2*pi*j/11+a;l=R(.097,.135);s1=V((cos(b),sin(b),0));w=V((-sin(b),cos(b),0))*.027;c=head+s1*l*.74+V((0,0,-.012));end=head+s1*l+V((0,0,-.043))
        add([head,c+w,c+V((0,0,.011)),c-w,end],[(0,2,1),(0,3,2),(1,2,4),(2,3,4)],m)
    ball(head+V((0,0,.019)),(.049,.049,.046),'cone',10,5)
    for j in range(6):
        b=j*2.4;ball(head+V((.032*cos(b),.032*sin(b),.049)),(.009,.009,.008),'pollen',5,3)
def spire(x,y,z,s,a):
    p=V((x,y,z));d=V((.105*cos(a),.105*sin(a),s));tube([p,p+d],[.014,.008],'green1',5)
    for j in range(4):
        b=a+j*2.40;leaf(p+d*(.07+.11*j),(.18*cos(b),.18*sin(b),.16),.034,'sedge')
    for j in range(8):
        w=(1-.075*j);c=p+d*(.56+.06*j);b=j*2.4+a
        for k in range(3):
            aa=b+k*2*pi/3;end=c+V((.064*w*cos(aa),.064*w*sin(aa),.043*w));tube([c,end,end+V((.010*cos(aa),.010*sin(aa),.026*w))],[.017*w,.034*w,.018*w],'purple lite' if j>4 else 'purple',6)
def umbel(x,y,z,s,a):
    p=V((x,y,z));d=V((.11*cos(a),.11*sin(a),s));rod(p,p+d,.009,'sedge',5)
    for j in range(8):
        b=j*2.40;l=.14*sqrt((j+1)/8);h=p+d+V((l*cos(b),l*sin(b),.10-.25*l));rod(p+d,h,.005,'sedge lite',5)
        for k in range(4):
            t=k*2.4;ball(h+V((.025*cos(t),.025*sin(t),.007)),(.021,.021,.017),'ivory',6,3)
for fn,group,patches in [(daisy,'Apricot coneflowers',[(-3.75,-1.53),(-3.07,-1.70),(.97,-1.90),(3.99,.67)]),(spire,'Violet flower spikes',[(-4.24,.35),(-.36,-1.80),(.39,-1.87),(3.50,-1.54),(2.1,.78)]),(umbel,'Meadow umbels',[(-1.47,-2.08),(2.37,-1.70),(.07,.85)])]:
    for x,y in patches:
        for j in range(random.randint(5,9)):
            u=x+R(-.43,.43);v=y+R(-.32,.32)
            if surface(u,v)>waterZ:fn(u,v,surface(u,v),R(.48,.93),R(0,6.28))
# A riverside birch, with tapering bent stems, lenticels and folded leaves.
group='River birch • stems'
treebase=V((2.18,.70,surface(2.18,.70)-.03))
def twigpath(start,end,bend):
    d=end-start
    return [start+d*(i/5)+bend*sin(pi*i/5) for i in range(6)]
def woody(start,end,r,bend,mark=True):
    pts=twigpath(start,end,bend)
    tube(pts,[r*(1-.47*i/5) for i in range(6)],'birch' if r>.048 else 'bark',9 if r>.071 else 6)
    if r>.060 and mark:
        for j in range(int((end-start).length*9)):
            t=R(.02,.96);p=start+(end-start)*t+bend*sin(pi*t);d=((end-start)+bend*pi*cos(pi*t)).normalized();u=d.cross(V((0,1,0))).normalized();v=d.cross(u);theta=R(0,6.28);rr=r*(1-.47*t)*.987
            da=R(.35,1.25);vs=[]
            for k in range(6):
                s=k/5;ang=theta+s*da;pos=p+(u*cos(ang)+v*sin(ang))*rr
                vs.extend([pos,pos+d*(.003+.021*sin(s*pi))])
            add(vs,[(2*i,2*i+2,2*i+3,2*i+1) for i in range(5)],random.choice(['lent','barklight','barklight']))
    return pts
def crown_spray(p,d,tone):
    global group
    group='River birch • leafy twigs'
    p=V(p);d=V(d);v=V((-d.y,d.x,0)).normalized()
    if v.length<.1:v=V((1,0,0))
    path=twigpath(p,p+d,V((0,0,.16))*d.length);tube(path,[.015,.014,.012,.009,.006,.003],'bark',5)
    for k in range(1,6):
        t=k/6;sg=(-1)**k;pt=p+d*t+V((0,0,.16*sin(pi*t)*d.length))
        off=(v*sg*R(.18,.40)+d*R(.20,.34)+V((R(-.08,.08),R(-.08,.08),R(-.03,.19))))
        end=pt+off;rod(pt,end,.006,'bark',4)
        for j in range(1,6):
            q=pt+off*(j/5);ang=math.atan2(off.y,off.x)+(-1)**j*R(.55,1.12);l=R(.14,.26);delta=V((l*cos(ang),l*sin(ang),R(-.10,.12)))
            leaf(q,delta,l*R(.31,.47),random.choice(tone),R(.016,.05))
    group='River birch • stems'
for t,(dx,dy,dz) in enumerate([(-1.37,-.12,3.08),(-.28,.12,3.73),(.98,.19,3.41),(1.47,-.25,2.42),(-.18,-.56,2.74)]):
    base=treebase+V((.085*(t-2),R(-.1,.1),0));apex=base+V((dx,dy,dz));bend=V((-.19 if dx>0 else .17,.11,.07))
    woody(base,apex,R(.098,.143),bend)
    for j in range(7):
        t2=.40+.090*j;st=base+(apex-base)*t2+bend*sin(pi*t2);ang=j*2.40+t*1.32
        length=(1.45-.67*t2)*R(.84,1.29);br=V((cos(ang)*length+.16*dx,sin(ang)*length*.86,R(.38,.80)));end=st+br
        woody(st,end,.056*(1.23-.64*t2),V((0,0,-.13)))
        for k in range(4):
            tt=.48+.17*k;q=st+br*tt+V((0,0,-.13*sin(pi*tt)));a=ang+(-1)**k*R(.31,1.09)
            shade=['green1','green2','green2','green3'] if j<4 else ['green2','green3','green3','green4']
            crown_spray(q,V((R(.42,.78)*cos(a),R(.38,.72)*sin(a),R(.18,.58))),shade)
# Foot traveller in belted ochre raincoat with segmented vermilion umbrella
group='The walker'
x=-3.61;y=1.84;ground=2.932
def P(dx,dy,dz):return V((x+dx,y+dy,ground+dz))
def dress(rings,m,n=16):
    vs=[];fs=[]
    for dx,dy,z,rx,ry in rings:
        for j in range(n):
            a=j*2*pi/n;vs.append(P(dx+rx*cos(a),dy+ry*sin(a),z))
    for i in range(len(rings)-1):
        for j in range(n):fs.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
    fs.append(tuple(range(n-1,-1,-1)));fs.append(tuple(range(len(vs)-n,len(vs))));add(vs,fs,m)
for dx,dy in [(-.105,.06),(.115,-.07)]:
    ball(P(dx+.015,dy-.050,.072),(.10,.149,.072),'boots');tube([P(dx,dy,.085),P(dx,dy,.32),P(dx*.63,dy*.38,.73)],[.077,.074,.073],'trousers',10)
    tube([P(dx,dy,.10),P(dx,dy,.23)],[.083,.082],'boots',10)
dress([(0,0,.62,.259,.164),(0,0,.74,.247,.164),(0,0,.99,.169,.128),(0,0,1.28,.216,.141),(0,0,1.36,.183,.115),(0,0,1.39,.083,.085)],'coat')
dress([(0,0,.97,.18,.135),(0,0,1.015,.176,.136)],'coat2')
for j in range(4):ball(P(.032,-.142,1.28-j*.145),(.018,.011,.018),'coat2',7,4)
tube([P(-.18,0,1.30),P(-.24,-.04,1.05),P(-.24,-.09,.89)],[.088,.076,.062],'coat',10)
tube([P(.17,0,1.30),P(.27,-.028,1.12),P(.33,-.18,1.28)],[.084,.075,.058],'coat',10)
ball(P(-.24,-.093,.869),(.054,.05,.072),'skin');ball(P(.33,-.18,1.30),(.058,.053,.072),'skin')
ball(P(.008,0,1.52),(.132,.127,.18),'skin',14,10)
ball(P(.001,.035,1.61),(.143,.137,.126),'hair',14,8)
ball(P(-.068,.139,1.54),(.082,.075,.089),'hair')
ball(P(.066,-.107,1.52),(.032,.042,.031),'skin')
for hx,hy in [(-.047,-.114),(.047,-.118)]:
    ball(P(hx,hy,1.555),(.012,.008,.010),'hair',7,4)
for j in range(13):
    ang=j*2*pi/13;ball(P(.118*cos(ang),.037+.114*sin(ang),1.622+R(-.012,.006)),(.043,.041,.041),'hair',8,5)
dress([(0,0,1.34,.122,.115),(0,0,1.405,.109,.109)],'coat2')
# Curved umbrella handle and radial fabric gores with sewn ridges, scalloped edge
ux=x+.295;uy=y-.15;uz=ground+2.205
tube([(ux+.10,uy,ground+1.246),(ux+.092,uy,ground+1.20),(ux+.054,uy,ground+1.17),(ux+.015,uy,ground+1.18),(ux,uy,ground+1.222),(ux,uy,uz)],[.020,.020,.020,.020,.017,.013],'metal',8)
def canopy(a,t,between):
    rr=.99*t*(1-.07*sin(pi*between)**1.2*t**2)
    return V((ux+rr*cos(a),uy+rr*sin(a),uz+.22-.41*t**1.74-.042*t**2*sin(pi*between)+.10*rr*cos(a)-.20*rr*sin(a)))
for j in range(10):
    vs=[];fs=[]
    for k in range(7):
        t=.006+.994*k/6
        for q in range(7):vs.append(canopy(2*pi*(j+q/6)/10,t,q/6))
        if k:
            for q in range(6):a=k*7+q;fs.append((a-7,a,a+1,a-6))
    add(vs,fs,['coral','coralLight','coral','coralDark','coral','coralLight','coral','coral','coralLight','coral'][j])
    rib=[canopy(2*pi*j/10,k/10,0) for k in range(11)]
    stripline(rib,.009,'coralLight');ball(rib[-1],(.018,.018,.021),'coralDark',6,4)
    rod((ux,uy,uz-.18),rib[7]-V((0,0,.015)),.008,'metal',5)
ball((ux,uy,uz+.232),(.034,.034,.042),'metal',8,5)
# Tiny wagtails, waterline foragers with white cheek patches and long tails
group='Two wagtails'
def bird(x,y,z,angle):
    ux=V((cos(angle),sin(angle),0));uy=V((-sin(angle),cos(angle),0));up=V((0,0,1));p=V((x,y,z))
    def b(a,b,c):return p+a*ux+b*uy+c*up
    for t in [-.047,.047]:
        rod(b(.005,t,0),b(0,t,.114),.009,'bark',5);rod(b(-.02,t,.005),b(.061,t,.005),.008,'bark',5)
    ball(b(0,0,.174),(.153,.080,.093),'ivory',12,6,angle)
    ball(b(-.022,0,.207),(.142,.086,.067),'road',12,6,angle)
    ball(b(.10,0,.264),(.083,.075,.080),'metal',10,7)
    for s in [-1,1]:
        ball(b(.115,s*.052,.257),(.049,.026,.037),'ivory',8,6,angle)
        ball(b(.13,s*.071,.276),(.014,.008,.013),'hair',7,4,angle)
    tube([b(.155,0,.264),b(.24,0,.26)],[.028,.002],'metal',6)
    for s in [-1,1]:leaf(b(-.068,s*.026,.216),-.235*ux+s*.029*uy+.035*up,.027,'metal',.009)
ball((.98,-.13,waterZ-.043),(.21,.126,.092),'gravel2',9,5,-.19)
bird(-1.19,1.29,2.928,-1.93);bird(.98,-.13,max(surface(.98,-.13),waterZ)+.044,2.8)
flush()
# The reverse carries the explanation as part of the physical exhibit.
for body,loc,siz,font,m,spacing in [
    ('Rain from the street enters through the opening in the curb.',(4.65,2.715,.52),.246,'Georgia.ttf','ivory',1),
    ('THE PLANTED HOLLOW HOLDS THE WATER WHILE IT SOAKS INTO THE SOIL.',(4.64,2.715,.27),.169,'DIN Alternate Bold.ttf','gold',1.13)]:
    o=txt(body,loc,siz,m,font,spacing);o.rotation_euler.z=pi
# Soft daylight on a seamless studio sweep
floor=box('Studio sweep',(0,0,-.16),(200,200,.32),'bgr')
def aim(o,at):o.rotation_euler=(V(at)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,p,energy,size,col,at):
    d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=col
    o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=p;aim(o,at)
area('Sun through cloud',(-7,-8,13),2000,7,(1,.89,.73),(0,0,2.1))
area('Skylight',(5,-4,9),775,8,(.79,.90,1),(0,0,2.1))
area('Leaf rim',(1,6,11),1500,6,(1,.96,.79),(1,0,3.0))
sc.world.color=(.28,.28,.28)
sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs[0].default_value=(.71,.79,.84,1);sc.world.node_tree.nodes.get('Background').inputs[1].default_value=.38
cd=bpy.data.cameras.new('Exhibit camera');cam=bpy.data.objects.new('Exhibit camera',cd);sc.collection.objects.link(cam);sc.camera=cam
def camera(p,at,scale):
    cam.location=p;aim(cam,at);cd.type='ORTHO';cd.ortho_scale=scale
camera((7.1,-18.5,10.1),(0,0,2.83),13.9)
sc.render.engine='CYCLES';sc.cycles.samples=20;sc.cycles.use_denoising=True
sc.render.image_settings.file_format='JPEG';sc.render.image_settings.quality=91
sc.render.resolution_x=1560;sc.render.resolution_y=1200;sc.render.resolution_percentage=54
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'

