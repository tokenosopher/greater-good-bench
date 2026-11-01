extends SceneTree

var failures = 0

func _initialize() -> void:
	call_deferred("run_checks")

func check(condition: bool, message: String) -> void:
	if not condition:
		failures += 1
		push_error("CHECK FAILED: " + message)

func key(game: Node, code: int) -> void:
	var event = InputEventKey.new()
	event.keycode = code
	event.pressed = true
	game._unhandled_input(event)

func run_checks() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	await process_frame
	game.sound_on = false
	check(game.homes.size() == 6 and game.funds == 7 and game.actions == 3, "Initial state")
	check(game.average() == 0, "Initial unmet needs")
	key(game, KEY_ENTER)
	check(game.begun and game.selected == Vector2i(0, 0), "Keyboard start")
	key(game, KEY_L)
	check(game.homes[0].listened and game.funds == 8 and game.actions == 2, "Listening applies local solution and contribution")
	check(game.support(0) == [1, 0, 0], "Listening helps the priority need")
	key(game, KEY_L)
	check(game.funds == 8 and game.actions == 2, "Listening cannot be repeated")
	key(game, KEY_Z)
	check(not game.homes[0].listened and game.funds == 7 and game.actions == 3, "Undo restores resident, funds, and actions")
	key(game, KEY_1)
	check(game.buildings.is_empty(), "Cannot build over a home")
	key(game, KEY_RIGHT)
	check(game.selected == Vector2i(1, 0), "Arrow navigation")
	var preview_score = game.score(0, 0)
	check(game.funds == 7 and game.buildings.is_empty(), "Preview does not mutate the campaign")
	key(game, KEY_1)
	check(game.score(0) == preview_score, "Preview matches actual support")
	check(game.buildings.size() == 1 and game.funds == 4 and game.actions == 2, "Build through keyboard")
	check(game.support(0) == [2, 0, 0], "Nearby home receives service")
	check(game.support(1) == [0, 0, 0], "Distant home does not receive service")
	key(game, KEY_2)
	check(game.buildings.size() == 1 and game.funds == 4, "Cannot overwrite a service")
	key(game, KEY_U)
	check(game.buildings[Vector2i(1, 0)].level == 2 and game.support(0)[0] == 3, "Upgrade raises output")
	key(game, KEY_U)
	check(game.funds == 2 and game.actions == 1, "Cannot upgrade above level two")
	key(game, KEY_Z)
	check(game.buildings[Vector2i(1, 0)].level == 1 and game.funds == 4, "Undo restores previous upgrade level")
	game.selected = Vector2i(4, 2)
	key(game, KEY_2)
	check(game.funds == 0 and game.actions == 1, "A service spends its actual price")
	game.selected = Vector2i(3, 0)
	key(game, KEY_1)
	check(game.funds == 0 and game.actions == 1, "Insufficient funds do not spend an action")
	game.selected = game.homes[2].pos
	key(game, KEY_L)
	check(game.actions == 0, "Three actions end the work week")
	game.selected = game.homes[3].pos
	key(game, KEY_L)
	check(not game.homes[3].listened, "Cannot act with zero actions")
	key(game, KEY_Z)
	key(game, KEY_SPACE)
	check(game.modal == "confirm" and game.week == 1, "Warn before forfeiting remaining actions")
	key(game, KEY_ESCAPE)
	check(game.modal == "", "Escape closes the confirmation")
	key(game, KEY_H)
	check(game.modal == "help", "Help shortcut opens help")
	key(game, KEY_ESCAPE)
	game.advance_week()
	check(game.week == 2 and game.funds == 4 and game.actions == 3, "New week supplies resources")
	check(game.needs_for(0) == [3, 2, 2], "Heat week adds care need")
	check(game.history.is_empty(), "Cannot undo a previous week")
	game.advance_week()
	check(game.needs_for(0) == [4, 1, 2], "Food week replaces the temporary care need")
	game.advance_week()
	check(game.needs_for(0) == [3, 1, 3], "Connection week changes needs")
	game.advance_week()
	check(game.needs_for(0) == [3, 1, 2], "Temporary needs expire")

	# A legal full campaign, using the same action methods as the interface.
	game.reset_game()
	game.begun = true
	var plan = [
		[["b", 2, 0, 4], ["b", 3, 2, 4], ["l", 2]],
		[["b", 1, 3, 3], ["b", 4, 1, 0], ["l", 0]],
		[["b", 1, 2, 4], ["b", 1, 0, 0], ["l", 3]],
		[["l", 1], ["l", 5], ["l", 4]],
		[["u", 2, 0], ["b", 3, 3, 3], ["u", 1, 2]],
		[["b", 0, 1, 0], ["u", 0, 1], ["b", 0, 2, 0]]
	]
	for w in plan.size():
		for move in plan[w]:
			var before = game.actions
			if move[0] == "l":
				game.selected = game.homes[move[1]].pos
				game.listen()
			else:
				game.selected = Vector2i(move[1], move[2])
				if move[0] == "b": game.build(move[3])
				else: game.upgrade()
			check(game.actions == before - 1, "Campaign action succeeds in week " + str(w + 1))
			check(game.funds >= 0, "Campaign never overspends")
		game.next_week()
	check(game.modal == "result" and game.week == 6, "Sixth week concludes the game")
	check(game.included() == 6 and game.average() == 100, "A legal strategy supports all households")
	game.activate("restart")
	check(game.week == 1 and game.buildings.is_empty() and game.modal == "", "Replay resets the campaign")
	for i in 6: game.advance_week()
	check(game.modal == "result" and game.included() == 0, "Unsuccessful campaign also concludes")
	game.queue_free()
	await process_frame
	print("Common Ground: all gameplay checks passed." if failures == 0 else "Failed checks: " + str(failures))
	quit(0 if failures == 0 else 1)
