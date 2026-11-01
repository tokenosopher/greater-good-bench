# Open one place in the circle, facing the viewer.
oldangles=[-90,-18,54,126,198]
newangles=[-120,0,60,120,180]
for i,(a,b) in enumerate(zip(oldangles,newangles)):
    for name in ['Hand '+str(i+1)+' | shared responsibility','Brass foot | hand '+str(i+1)]:
        o=bpy.data.objects[name]; o.rotation_euler.z=math.radians(b-a)
for o in scene.objects:
    if o.name.startswith('Open circle'): o.rotation_euler.z=math.radians(30)
def textob(name,body,loc,size,rot=(0,0,0),ma=None):
    cu=bpy.data.curves.new(name,'FONT'); cu.body=body; cu.align_x='CENTER'; cu.align_y='CENTER'; cu.size=size; cu.extrude=.0015; cu.bevel_depth=.0007; cu.bevel_resolution=1
    ob=bpy.data.objects.new(name,cu); scene.collection.objects.link(ob); ob.location=loc; ob.rotation_euler=rot; assign(ob,ma or mats['gold']); return ob
# The inscription is inlaid into the empty place at the table.
angle=math.radians(30)
def onbase(x,y,z):
    return (x*math.cos(angle)-y*math.sin(angle),x*math.sin(angle)+y*math.cos(angle),z)
textob('Inscription | NO ONE','NO ONE',onbase(0,-1.58,.517),.20,(0,0,angle))
textob('Inscription | THRIVES ALONE','THRIVES ALONE',onbase(0,-1.85,.517),.17,(0,0,angle))
textob('Edition mark','C O M M O N   G R O U N D',onbase(0,-2.12,.517),.07,(0,0,angle))
# A small circular brass marker gives the opening a human scale.
for xx in [-.94,.94]:
    path('Inlaid invitation detail',[onbase(xx,-1.68,.521),onbase(xx,-1.95,.521)],.008,mats['gold'])
# Gallery floor stays outside the exported object.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.025)); floor=bpy.context.object; floor.name='STUDIO | ground'; assign(floor,mats['floor'])
def aim(o,target): o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,color,size,target):
    da=bpy.data.lights.new(name,'AREA'); da.energy=power; da.color=color; da.shape='DISK'; da.size=size; ob=bpy.data.objects.new(name,da); scene.collection.objects.link(ob); ob.location=loc; aim(ob,target)
area('STUDIO | softbox key',(-5,-6,10),1300,(1,.85,.68),5,(0,0,3))
area('STUDIO | cool fill',(5,-2,7),950,(.65,.83,1),4,(0,0,3))
area('STUDIO | rim',(2,5,9),1650,(1,.9,.70),3,(0,0,3.5))
area('STUDIO | frontal card',(1,-7,4),200,(1,.95,.85),3,(0,0,2.5))
da=bpy.data.cameras.new('Camera | invitation'); cam=bpy.data.objects.new('Camera | invitation',da); scene.collection.objects.link(cam); cam.location=(7,-12.124,8.3); aim(cam,(0,0,2.9)); da.type='ORTHO'; da.ortho_scale=7.6; da.lens=50; scene.camera=cam
scene.render.resolution_x=1200; scene.render.resolution_y=1400; scene.render.resolution_percentage=75
scene.render.filepath=os.path.join(os.getcwd(),'preview.jpg')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.getcwd(),'working.blend'))
bpy.ops.render.render(write_still=True)
