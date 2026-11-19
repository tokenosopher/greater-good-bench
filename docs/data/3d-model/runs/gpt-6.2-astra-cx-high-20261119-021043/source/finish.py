import os,bpy
from mathutils import Vector as V
sc=bpy.context.scene
for o in list(sc.objects):
    if o.type=='FONT':
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
        bpy.ops.object.convert(target='MESH')
    if o.type=='MESH' and o.name.startswith(('River-washed stones','Mineral inclusions','The walker •','Apricot coneflowers','Meadow umbels','Two wagtails','Exposed roots','River birch • leafy twigs • bark','River birch • stems','Violet flower spikes')):
        for p in o.data.polygons:p.use_smooth=True
    if o.name.startswith('Rain from the street'):o.scale*=1.69
    if o.name.startswith('THE PLANTED HOLLOW'):o.scale*=1.38
bpy.ops.object.select_all(action='DESELECT')
for o in sc.objects:
    if o.type=='MESH' and o.name!='Studio sweep':o.select_set(True)
out=os.path.abspath('output/a-softer-street.glb')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_apply=True,export_draco_mesh_compression_enable=False,export_texcoords=False,export_animations=False)
