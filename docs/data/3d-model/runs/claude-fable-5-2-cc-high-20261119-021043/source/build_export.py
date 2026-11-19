def export_glb(path, current=True):
    sc = bpy.context.scene
    sc.frame_set(PERIOD // 2)
    for ob in bpy.data.objects:
        ob.select_set(False)
    model = bpy.data.collections['Model']
    for ob in model.objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['Plinth']
    bpy.ops.export_scene.gltf(
        filepath=path, export_format='GLB', use_selection=True,
        export_apply=False, export_yup=True,
        export_animations=True, export_animation_mode='SCENE', export_anim_scene_split_object=False,
        export_current_frame=current, export_nla_strips_merged_animation_name='Compressions at 110 a minute',
        export_morph=True, export_morph_normal=True,
        export_cameras=False, export_lights=False,
        export_draco_mesh_compression_enable=False,
    )
    for ob in bpy.data.objects:
        ob.select_set(False)
