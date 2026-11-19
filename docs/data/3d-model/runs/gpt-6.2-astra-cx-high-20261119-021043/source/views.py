import bpy,os
from mathutils import Vector as V
sc=bpy.context.scene;cam=sc.camera
def shot(name,pos,at,scale,w,h,samples=48,pct=100):
    cam.location=pos;cam.rotation_euler=(V(at)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;cam.data.type='ORTHO'
    sc.render.filepath=os.path.abspath(name);sc.render.resolution_x=w;sc.render.resolution_y=h;sc.render.resolution_percentage=pct;sc.cycles.samples=samples;sc.render.image_settings.quality=93;bpy.ops.render.render(write_still=True)
