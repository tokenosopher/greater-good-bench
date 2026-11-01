extends SceneTree

var game
var failures = 0

func _initialize() -> void:
	call_deferred("run")

func check(condition: bool, description: String) -> void:
	if not condition:
		failures += 1
		push_error(description)

func run() -> void:
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	await process_frame
	game.sound_on = false
	await process_frame
	# Route real mouse and keyboard events through the viewport.
	var motion = InputEventMouseMotion.new()
	motion.position = Vector2(500, 512)
	motion.global_position = motion.position
	root.push_input(motion, true)
	var press = InputEventMouseButton.new()
	press.position = motion.position
	press.global_position = motion.position
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	root.push_input(press, true)
	check(game.selected == -1, "Mouse selects the commons")
	var key = InputEventKey.new()
	key.keycode = KEY_1
	key.pressed = true
	root.push_input(key)
	check(game.selected == 0, "Keyboard selects a neighbor")
	# Listening is persistent, costs one hour, and cannot be repeated.
	game.activate("listen")
	check(game.hours == 3 and game.wellbeing[0] == 56, "Listening cost and benefit")
	game.activate("listen")
	check(game.hours == 3, "Listening cannot be repeated")
	game.activate("tailored")
	check(game.hours == 2 and game.supplies == 4 and game.wellbeing[5] == 55, "Tailored help and neighbor benefit")
	game.activate("direct")
	check(game.hours == 2, "Only one support action per person each day")
	game.selected = -1
	game.activate("build_0")
	check(game.hours == 0 and game.projects[0], "Shared project cost")
	game.selected = 1
	game.activate("listen")
	check(not game.listened[1] and game.hours == 0, "Actions cannot overspend hours")
	game.activate("end_day")
	check(game.mode == "night" and game.day == 1, "Night review does not spend a day")
	game.activate("back")
	check(game.mode == "play" and game.hours == 0, "Can cancel night review")
	game.activate("end_day")
	game.activate("next_day")
	check(game.day == 2 and game.hours == 4 and game.supplies == 5, "Morning replenishment")
	check(game.listened[0] and not game.helped[0], "Understanding persists; support resets")
	check(game.wellbeing[0] == 69, "Canopy reduces overnight loss")
	# Verify the commons label can be clicked without selecting the garden.
	await process_frame
	var chosen = ""
	for i in range(game.buttons.size() - 1, -1, -1):
		if game.buttons[i].rect.has_point(Vector2(500, 512)):
			chosen = game.buttons[i].id
			break
	check(chosen == "commons", "Commons label hit target")
	# A resource-aware greedy strategy should be able to win.
	game.restart()
	game.sound_on = false
	for d in 7:
		# Build shade first, then the buddy network on the second day.
		if d == 0 or d == 1:
			game.activate("build_" + str(0 if d == 0 else 2))
		while game.hours > 0:
			var best = -1
			var low = 101
			for i in 6:
				if not game.helped[i] and game.wellbeing[i] < low:
					best = i
					low = game.wellbeing[i]
			if best < 0:
				break
			game.selected = best
			if not game.listened[best]:
				game.activate("listen")
			else:
				game.activate("tailored")
		game.activate("end_day")
		game.activate("next_day")
	print("Careful playthrough: ", game.wellbeing, "; projects: ", game.project_count())
	check(game.mode == "result" and game.day == 7, "Full week reaches results")
	check(game.steady_count() == 6 and game.project_count() >= 2, "Careful play is winnable")
	# Neglect is survivable until the final report and produces a different outcome.
	game.restart()
	game.sound_on = false
	for d in 7:
		game.activate("end_day")
		game.activate("next_day")
	check(game.mode == "result" and game.steady_count() < 6, "Neglect ending")
	game.activate("restart")
	check(game.day == 1 and game.wellbeing == [53, 45, 57, 48, 42, 51] and game.hours == 4, "Clean replay")
	print("Gameplay checks: ", "PASS" if failures == 0 else "FAIL (" + str(failures) + ")")
	quit(0 if failures == 0 else 1)
