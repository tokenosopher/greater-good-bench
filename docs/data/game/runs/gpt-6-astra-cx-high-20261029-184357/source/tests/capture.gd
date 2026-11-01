extends SceneTree

func _initialize() -> void:
	call_deferred("capture")

func capture() -> void:
	DirAccess.make_dir_recursive_absolute("res://.validation")
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	scene.sound_on = false
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://.validation/01-welcome.png")
	scene.activate("begin")
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://.validation/02-resident.png")
	scene.listen()
	scene.selected = Vector2i(1, 1)
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://.validation/03-build.png")
	scene.modal = "help"
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://.validation/04-help.png")
	scene.modal = ""
	scene.week = 6
	scene.funds = 100
	scene.actions = 100
	for i in scene.homes.size():
		scene.selected = scene.homes[i].pos
		scene.listen()
	for move in [[2, 0, 4], [3, 2, 4], [1, 3, 3], [4, 1, 0], [1, 2, 4], [1, 0, 0], [3, 3, 3], [0, 1, 1], [0, 2, 2]]:
		scene.selected = Vector2i(move[0], move[1])
		scene.build(move[2])
		scene.upgrade()
	scene.funds = 2
	scene.actions = 0
	scene.selected = Vector2i(1, 2)
	scene.particles.clear()
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://.validation/05-neighborhood.png")
	scene.advance_week()
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://.validation/06-ending.png")
	scene.queue_free()
	await process_frame
	quit()
