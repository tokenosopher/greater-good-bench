extends Node2D
## RIPPLE — One Small Kindness at a Time
## A cozy five-day village game. Notice a need, respond well, and watch help spread.

enum State { INTRO, PLAYING, DIALOG, SUMMARY, ENDING }

const VIEW := Vector2(1152, 648)
const DAY_LENGTH := 80.0
const TOTAL_DAYS := 5

var state: int = State.INTRO
var day := 1
var time_left := DAY_LENGTH
var warmth := 45.0
var kindness := 0
var ripples := 0
var expired_count := 0

var day_kindness_start := 0
var day_ripples_start := 0
var day_expired_start := 0

var player_pos := Vector2(576, 405)
var player_face := Vector2.DOWN
var player_speed := 218.0
var speed_mult := 1.0
var need_time_bonus := 0.0
var inspire_next := false
var carrying := ""

var npcs: Array[Dictionary] = []
var needs: Array[Dictionary] = []
var particles: Array[Dictionary] = []
var flowers: Array[Dictionary] = []
var obstacles: Array[Rect2] = []

var spawn_timer := 1.0
var toast_timer := 0.0
var next_need_id := 1
var summary_is_ending := false

var current_dialog_need_id := -1
var dialog_resolved := false

# UI
var ui_layer: CanvasLayer
var day_label: Label
var stats_label: Label
var timer_label: Label
var carry_label: Label
var prompt_label: Label
var toast_label: Label

var intro_panel: Panel
var dialog_panel: Panel
var dialog_title: Label
var dialog_body: Label
var dialog_buttons: Array[Button] = []

var summary_panel: Panel
var summary_title: Label
var summary_body: Label
var summary_buttons: Array[Button] = []
var summary_main_button: Button

var audio_players: Array[AudioStreamPlayer] = []
var audio_index := 0

const NPC_DATA := [
	{"name": "Maya", "color": Color(0.92, 0.45, 0.38), "home": Vector2(180, 225)},
	{"name": "Jonah", "color": Color(0.35, 0.62, 0.92), "home": Vector2(390, 225)},
	{"name": "Priya", "color": Color(0.98, 0.72, 0.28), "home": Vector2(755, 225)},
	{"name": "Sam", "color": Color(0.55, 0.78, 0.45), "home": Vector2(990, 225)},
	{"name": "Noor", "color": Color(0.72, 0.52, 0.95), "home": Vector2(255, 430)},
	{"name": "Elena", "color": Color(0.96, 0.58, 0.72), "home": Vector2(475, 535)},
	{"name": "Theo", "color": Color(0.38, 0.82, 0.78), "home": Vector2(735, 430)},
	{"name": "Grace", "color": Color(0.88, 0.62, 0.42), "home": Vector2(835, 555)},
]

const LITTER_SPOTS := [
	Vector2(205, 255), Vector2(485, 250), Vector2(770, 255), Vector2(1010, 255),
	Vector2(575, 445), Vector2(205, 445), Vector2(825, 445), Vector2(385, 565),
	Vector2(650, 545), Vector2(105, 545)
]

const PLANT_SPOTS := [
	Vector2(105, 505), Vector2(165, 545), Vector2(225, 500), Vector2(285, 550),
	Vector2(130, 575), Vector2(255, 585), Vector2(320, 510)
]

const ITEM_DEFS := [
	{"item": "Watering can", "where": "by the well", "pos": Vector2(628, 352)},
	{"item": "Library book", "where": "outside the library", "pos": Vector2(248, 350)},
	{"item": "Warm bread", "where": "outside the bakery", "pos": Vector2(902, 352)},
	{"item": "Toy duck", "where": "by the pond", "pos": Vector2(842, 535)},
	{"item": "Posted letter", "where": "on the centre bench", "pos": Vector2(576, 205)},
	{"item": "Cosy blanket", "where": "outside the corner shop", "pos": Vector2(248, 425)},
]

const RIPPLE_LINES := [
	"%s paid it forward — carrying a neighbour's shopping without being asked.",
	"%s paid it forward — stopping to thank the person who cleans the square.",
	"%s paid it forward — inviting someone new to join lunch.",
	"%s paid it forward — watering a stranger's wilting flowers.",
	"%s paid it forward — checking in on a friend who had gone quiet.",
	"%s paid it forward — picking up litter and leaving the path better than they found it.",
]


func _ready() -> void:
	randomize()
	_build_obstacles()
	_build_audio()
	_build_ui()
	_reset_game()
	_show_intro()


func _build_obstacles() -> void:
	obstacles = [
		Rect2(64, 92, 150, 92), Rect2(292, 84, 160, 94),
		Rect2(674, 84, 160, 94), Rect2(918, 92, 160, 92),
		Rect2(64, 286, 156, 98), Rect2(932, 286, 144, 98),
		Rect2(872, 476, 216, 104), Rect2(538, 262, 76, 76),
	]


func _build_audio() -> void:
	for i in 6:
		var p := AudioStreamPlayer.new()
		p.bus = "Master"
		add_child(p)
		audio_players.append(p)


func _tone(freq: float, duration: float = 0.14, delay: float = 0.0) -> void:
	# Tiny synthesized chime: no audio files needed.
	if delay > 0.0:
		await get_tree().create_timer(delay).timeout
	var rate := 22050
	var count := int(rate * duration)
	var data := PackedByteArray()
	data.resize(count)
	for i in count:
		var t := float(i) / rate
		var env := 1.0 - float(i) / float(count)
		var sample := int(128.0 + sin(TAU * freq * t) * 52.0 * env * env)
		data[i] = clampi(sample, 1, 254)
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_8_BITS
	stream.mix_rate = rate
	stream.stereo = false
	stream.data = data
	var player := audio_players[audio_index]
	audio_index = (audio_index + 1) % audio_players.size()
	player.stream = stream
	player.play()


func _sound(kind: String) -> void:
	match kind:
		"good":
			_tone(659.25, 0.13)
			_tone(987.77, 0.2, 0.09)
		"pickup":
			_tone(523.25, 0.1)
		"ok":
			_tone(440.0, 0.12)
		"bad":
			_tone(196.0, 0.22)
		"day":
			_tone(392.0, 0.16)
			_tone(587.33, 0.24, 0.12)


# ---------------------------------------------------------------- UI building
func _make_label(text: String, pos: Vector2, size: Vector2, font_size: int, color := Color.WHITE, align := HORIZONTAL_ALIGNMENT_LEFT) -> Label:
	var l := Label.new()
	l.text = text
	l.position = pos
	l.size = size
	l.horizontal_alignment = align
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.45))
	l.add_theme_constant_override("shadow_offset_x", 1)
	l.add_theme_constant_override("shadow_offset_y", 1)
	return l


func _style_panel(p: Panel, bg: Color) -> void:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = Color(1, 1, 1, 0.75)
	s.set_border_width_all(2)
	s.set_corner_radius_all(18)
	s.shadow_color = Color(0, 0, 0, 0.35)
	s.shadow_size = 10
	s.shadow_offset = Vector2(0, 4)
	p.add_theme_stylebox_override("panel", s)


func _make_button(text: String, pos: Vector2, size: Vector2, font_size := 17) -> Button:
	var b := Button.new()
	b.text = text
	b.position = pos
	b.size = size
	b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	b.add_theme_font_size_override("font_size", font_size)
	var normal := StyleBoxFlat.new()
	normal.bg_color = Color(0.16, 0.48, 0.42, 1)
	normal.set_corner_radius_all(12)
	normal.set_border_width_all(2)
	normal.border_color = Color(1, 1, 1, 0.65)
	normal.content_margin_left = 12
	normal.content_margin_right = 12
	normal.content_margin_top = 8
	normal.content_margin_bottom = 8
	var hover := normal.duplicate() as StyleBoxFlat
	hover.bg_color = Color(0.22, 0.62, 0.53, 1)
	var pressed := normal.duplicate() as StyleBoxFlat
	pressed.bg_color = Color(0.10, 0.36, 0.32, 1)
	b.add_theme_stylebox_override("normal", normal)
	b.add_theme_stylebox_override("hover", hover)
	b.add_theme_stylebox_override("pressed", pressed)
	b.add_theme_color_override("font_color", Color.WHITE)
	return b


func _build_ui() -> void:
	ui_layer = CanvasLayer.new()
	add_child(ui_layer)

	var top := ColorRect.new()
	top.color = Color(0.07, 0.16, 0.15, 0.88)
	top.position = Vector2.ZERO
	top.size = Vector2(VIEW.x, 58)
	ui_layer.add_child(top)

	day_label = _make_label("Day 1 of 5", Vector2(18, 5), Vector2(170, 48), 22, Color(1, 0.9, 0.6))
	ui_layer.add_child(day_label)
	stats_label = _make_label("", Vector2(195, 5), Vector2(500, 48), 18)
	ui_layer.add_child(stats_label)
	timer_label = _make_label("", Vector2(735, 5), Vector2(190, 48), 18, Color.WHITE, HORIZONTAL_ALIGNMENT_RIGHT)
	ui_layer.add_child(timer_label)
	carry_label = _make_label("Hands free", Vector2(940, 5), Vector2(195, 48), 17, Color(0.75, 0.95, 1), HORIZONTAL_ALIGNMENT_RIGHT)
	ui_layer.add_child(carry_label)

	toast_label = _make_label("", Vector2(176, 522), Vector2(800, 42), 19, Color(1, 0.96, 0.75), HORIZONTAL_ALIGNMENT_CENTER)
	ui_layer.add_child(toast_label)
	prompt_label = _make_label("", Vector2(176, 566), Vector2(800, 58), 20, Color.WHITE, HORIZONTAL_ALIGNMENT_CENTER)
	ui_layer.add_child(prompt_label)

	_build_intro_panel()
	_build_dialog_panel()
	_build_summary_panel()


func _build_intro_panel() -> void:
	intro_panel = Panel.new()
	intro_panel.position = Vector2(246, 78)
	intro_panel.size = Vector2(660, 500)
	_style_panel(intro_panel, Color(0.08, 0.20, 0.19, 0.97))
	ui_layer.add_child(intro_panel)

	intro_panel.add_child(_make_label("R I P P L E", Vector2(30, 18), Vector2(600, 58), 44, Color(1, 0.88, 0.55), HORIZONTAL_ALIGNMENT_CENTER))
	intro_panel.add_child(_make_label("One small kindness at a time", Vector2(30, 76), Vector2(600, 34), 21, Color(0.8, 0.95, 0.9), HORIZONTAL_ALIGNMENT_CENTER))
	var body := "This village does not need a hero. It needs people who notice.\n\nFor five short days, walk around, spot who (or what) needs care, and choose how to respond. Listening can matter more than fixing. Fetch what is needed. Tend the shared garden. Every genuine kindness can inspire someone else to pass it on — watch for the ripples.\n\nMove: WASD / Arrow keys    •    Interact: E or Space\n\nIf everyone practised this for real — notice, pause, help well, pass it on — the world would quietly become a kinder place."
	intro_panel.add_child(_make_label(body, Vector2(42, 122), Vector2(576, 282), 18, Color.WHITE))
	var start := _make_button("▶   Start Day 1 in the village", Vector2(150, 420), Vector2(360, 56), 20)
	start.pressed.connect(_on_start_pressed)
	intro_panel.add_child(start)


func _build_dialog_panel() -> void:
	dialog_panel = Panel.new()
	dialog_panel.position = Vector2(256, 104)
	dialog_panel.size = Vector2(640, 448)
	_style_panel(dialog_panel, Color(0.10, 0.17, 0.24, 0.98))
	ui_layer.add_child(dialog_panel)
	dialog_title = _make_label("", Vector2(30, 16), Vector2(580, 52), 26, Color(1, 0.9, 0.6), HORIZONTAL_ALIGNMENT_CENTER)
	dialog_panel.add_child(dialog_title)
	dialog_body = _make_label("", Vector2(38, 74), Vector2(564, 142), 19)
	dialog_body.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	dialog_panel.add_child(dialog_body)
	for i in 3:
		var b := _make_button("", Vector2(38, 224 + i * 68), Vector2(564, 58), 17)
		b.pressed.connect(_on_dialog_option.bind(i))
		dialog_panel.add_child(b)
		dialog_buttons.append(b)
	dialog_panel.hide()


func _build_summary_panel() -> void:
	summary_panel = Panel.new()
	summary_panel.position = Vector2(256, 88)
	summary_panel.size = Vector2(640, 478)
	_style_panel(summary_panel, Color(0.09, 0.20, 0.18, 0.98))
	ui_layer.add_child(summary_panel)
	summary_title = _make_label("", Vector2(30, 16), Vector2(580, 54), 29, Color(1, 0.9, 0.6), HORIZONTAL_ALIGNMENT_CENTER)
	summary_panel.add_child(summary_title)
	summary_body = _make_label("", Vector2(40, 78), Vector2(560, 168), 19)
	summary_body.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	summary_panel.add_child(summary_body)
	summary_panel.add_child(_make_label("How will you carry today into tomorrow?", Vector2(40, 244), Vector2(560, 30), 17, Color(0.8, 0.95, 0.9), HORIZONTAL_ALIGNMENT_CENTER))
	for i in 3:
		var b := _make_button("", Vector2(40, 282 + i * 58), Vector2(560, 50), 16)
		b.pressed.connect(_on_reflection_option.bind(i))
		summary_panel.add_child(b)
		summary_buttons.append(b)
	summary_main_button = _make_button("Play again", Vector2(170, 282), Vector2(300, 58), 20)
	summary_main_button.pressed.connect(_on_summary_main_pressed)
	summary_panel.add_child(summary_main_button)
	summary_panel.hide()


# ---------------------------------------------------------------- game setup
func _reset_game() -> void:
	day = 1
	warmth = 45.0
	kindness = 0
	ripples = 0
	expired_count = 0
	carrying = ""
	speed_mult = 1.0
	need_time_bonus = 0.0
	player_pos = Vector2(576, 405)
	needs.clear()
	particles.clear()
	flowers.clear()
	npcs.clear()
	for data in NPC_DATA:
		npcs.append({
			"name": data["name"], "color": data["color"], "home": data["home"],
			"pos": data["home"], "target": data["home"], "wait": randf_range(0.0, 2.0),
			"inspired": false, "ripple_timer": randf_range(13.0, 22.0), "sad": 0.0,
		})
	for i in 9:
		_add_flower(Vector2(randf_range(80, 1080), randf_range(210, 610)))
	_update_stats()


func _add_flower(pos: Vector2) -> void:
	if flowers.size() > 110:
		return
	var palette := [Color(1, 0.55, 0.65), Color(1, 0.85, 0.35), Color(0.75, 0.65, 1), Color(1, 1, 1), Color(1, 0.65, 0.4)]
	flowers.append({"pos": pos, "color": palette[randi() % palette.size()], "phase": randf() * TAU})


func _start_day() -> void:
	time_left = DAY_LENGTH
	spawn_timer = 0.6
	needs.clear()
	carrying = ""
	day_kindness_start = kindness
	day_ripples_start = ripples
	day_expired_start = expired_count
	if inspire_next:
		inspire_next = false
		var candidates: Array[int] = []
		for i in npcs.size():
			if not bool(npcs[i]["inspired"]):
				candidates.append(i)
		if not candidates.is_empty():
			var idx: int = candidates[randi() % candidates.size()]
			npcs[idx]["inspired"] = true
			_show_toast("%s starts the day inspired to help." % str(npcs[idx]["name"]))
	state = State.PLAYING
	intro_panel.hide()
	summary_panel.hide()
	dialog_panel.hide()
	_sound("day")
	_update_stats()


func _show_intro() -> void:
	state = State.INTRO
	intro_panel.show()


func _on_start_pressed() -> void:
	_start_day()


# ---------------------------------------------------------------- main loop
func _process(delta: float) -> void:
	if toast_timer > 0.0:
		toast_timer -= delta
		if toast_timer <= 0.0:
			toast_label.text = ""
	_update_particles(delta)

	if state == State.PLAYING:
		time_left -= delta
		if time_left <= 0.0:
			time_left = 0.0
			_end_day()
		else:
			_update_player(delta)
			_update_npcs(delta)
			_update_needs(delta)
			spawn_timer -= delta
			if spawn_timer <= 0.0:
				spawn_timer = randf_range(5.5, 8.5)
				_spawn_need()
			_update_prompt()
	_update_stats()
	queue_redraw()


func _update_player(delta: float) -> void:
	var dir := Vector2.ZERO
	if Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP):
		dir.y -= 1.0
	if Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN):
		dir.y += 1.0
	if Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT):
		dir.x -= 1.0
	if Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT):
		dir.x += 1.0
	if dir == Vector2.ZERO:
		return
	dir = dir.normalized()
	player_face = dir
	var step := dir * player_speed * speed_mult * delta
	var next := player_pos + Vector2(step.x, 0)
	if not _collides(next):
		player_pos = next
	next = player_pos + Vector2(0, step.y)
	if not _collides(next):
		player_pos = next
	player_pos.x = clampf(player_pos.x, 24, VIEW.x - 24)
	player_pos.y = clampf(player_pos.y, 82, VIEW.y - 22)


func _collides(pos: Vector2) -> bool:
	for r in obstacles:
		if r.grow(13).has_point(pos):
			return true
	return false


func _npc_has_need(idx: int) -> bool:
	for n in needs:
		if int(n.get("npc", -1)) == idx:
			return true
	return false


func _update_npcs(delta: float) -> void:
	for i in npcs.size():
		var npc := npcs[i]
		if float(npc["sad"]) > 0.0:
			npc["sad"] = float(npc["sad"]) - delta
		if _npc_has_need(i):
			npcs[i] = npc
			continue
		if bool(npc["inspired"]):
			npc["ripple_timer"] = float(npc["ripple_timer"]) - delta
			if float(npc["ripple_timer"]) <= 0.0:
				npc["ripple_timer"] = randf_range(14.0, 23.0)
				_do_ripple(i)
		if float(npc["wait"]) > 0.0:
			npc["wait"] = float(npc["wait"]) - delta
		else:
			var pos: Vector2 = npc["pos"]
			var target: Vector2 = npc["target"]
			if pos.distance_to(target) < 8.0:
				npc["target"] = Vector2(npc["home"]) + Vector2(randf_range(-70, 70), randf_range(-38, 48))
				npc["wait"] = randf_range(0.6, 2.6)
			else:
				var new_pos := pos.move_toward(target, 42.0 * delta)
				if not _collides(new_pos):
					npc["pos"] = new_pos
				else:
					npc["wait"] = 0.5
		npcs[i] = npc
	# Keep any person-bound need marker glued to that person.
	for ni in needs.size():
		var need := needs[ni]
		if int(need.get("npc", -1)) >= 0:
			need["pos"] = npcs[int(need["npc"])]["pos"]
			needs[ni] = need


func _update_needs(delta: float) -> void:
	for i in range(needs.size() - 1, -1, -1):
		var need := needs[i]
		need["timer"] = float(need["timer"]) - delta
		# Pick up a needed item simply by walking to it.
		if str(need["type"]) == "fetch" and not bool(need["item_taken"]) and carrying == "":
			if player_pos.distance_to(need["item_pos"]) < 30.0:
				need["item_taken"] = true
				carrying = str(need["item"])
				_show_toast("Picked up: %s. Take it to %s. [E]" % [carrying, str(need["who"])])
				_sound("pickup")
				_add_hearts(need["item_pos"], 4)
		needs[i] = need
		if float(need["timer"]) <= 0.0:
			var who := str(need.get("who", "Something"))
			if int(need.get("npc", -1)) >= 0:
				var idx := int(need["npc"])
				npcs[idx]["sad"] = 8.0
			warmth = clampf(warmth - 4.0, 0, 100)
			expired_count += 1
			_show_toast("%s was left waiting. Unmet needs don't vanish — they weigh on a place." % who)
			_sound("bad")
			needs.remove_at(i)


func _do_ripple(idx: int) -> void:
	ripples += 1
	warmth = clampf(warmth + 2.0, 0, 100)
	var npc := npcs[idx]
	_add_hearts(npc["pos"], 6)
	_add_flower(Vector2(npc["pos"]) + Vector2(randf_range(-45, 45), randf_range(20, 55)))
	if not npcs.is_empty():
		var other := randi() % npcs.size()
		_add_hearts(npcs[other]["pos"], 3)
	_show_toast(RIPPLE_LINES[randi() % RIPPLE_LINES.size()] % str(npc["name"]))
	_sound("ok")


func _update_particles(delta: float) -> void:
	for i in range(particles.size() - 1, -1, -1):
		var p := particles[i]
		p["life"] = float(p["life"]) - delta
		p["pos"] = Vector2(p["pos"]) + Vector2(p["vel"]) * delta
		p["vel"] = Vector2(p["vel"]) + Vector2(0, -18) * delta
		if float(p["life"]) <= 0.0:
			particles.remove_at(i)
		else:
			particles[i] = p


func _add_hearts(pos: Vector2, count: int) -> void:
	for i in count:
		particles.append({
			"pos": pos + Vector2(randf_range(-14, 14), randf_range(-10, 4)),
			"vel": Vector2(randf_range(-12, 12), randf_range(-42, -22)),
			"life": randf_range(0.7, 1.3), "max_life": 1.3,
			"color": [Color(1, 0.45, 0.6), Color(1, 0.75, 0.4), Color(0.6, 0.95, 0.8)][randi() % 3],
		})


# ---------------------------------------------------------------- needs
func _spawn_need(force := false) -> void:
	if needs.size() >= 4 and not force:
		return
	var types: Array[String] = ["listen", "groceries", "anxious", "newcomer", "litter", "plant", "fetch"]
	var kind: String = types[randi() % types.size()]
	var need: Dictionary = {
		"id": next_need_id, "type": kind, "timer": 38.0 + need_time_bonus,
		"max_timer": 38.0 + need_time_bonus, "npc": -1, "pos": Vector2.ZERO,
		"who": "Something", "item": "", "item_pos": Vector2.ZERO, "item_taken": true, "where": "",
	}
	next_need_id += 1

	if kind in ["listen", "groceries", "anxious", "newcomer", "fetch"]:
		var free: Array[int] = []
		for i in npcs.size():
			if not _npc_has_need(i):
				free.append(i)
		if free.is_empty():
			return
		var idx: int = free[randi() % free.size()]
		need["npc"] = idx
		need["pos"] = npcs[idx]["pos"]
		need["who"] = str(npcs[idx]["name"])
		if kind == "fetch":
			var def: Dictionary = ITEM_DEFS[randi() % ITEM_DEFS.size()]
			need["item"] = str(def["item"])
			need["item_pos"] = def["pos"]
			need["where"] = str(def["where"])
			need["item_taken"] = false
			_show_toast("%s needs the %s — it's %s." % [str(npcs[idx]["name"]), str(def["item"]), str(def["where"])])
		else:
			_show_toast("%s could use a moment of your attention." % str(npcs[idx]["name"]))
	elif kind == "litter":
		need["pos"] = LITTER_SPOTS[randi() % LITTER_SPOTS.size()]
		need["who"] = "The shared path"
		_show_toast("Litter has gathered on a shared path.")
	elif kind == "plant":
		need["pos"] = PLANT_SPOTS[randi() % PLANT_SPOTS.size()]
		need["who"] = "A garden plant"
		_show_toast("A plant in the community garden is wilting.")
	needs.append(need)


func _nearest_need() -> Dictionary:
	var best: Dictionary = {}
	var best_d := 58.0
	for n in needs:
		var d := player_pos.distance_to(n["pos"])
		if d < best_d:
			best_d = d
			best = n
	return best


func _update_prompt() -> void:
	var need := _nearest_need()
	if need.is_empty():
		if carrying != "":
			prompt_label.text = "You are carrying: %s — find who needs it." % carrying
		else:
			prompt_label.text = "Wander, notice the ❗ bubbles, and press E when close.  •  Move: WASD / arrows"
		return
	match str(need["type"]):
		"litter":
			prompt_label.text = "Press E — clear the litter from the shared path"
		"plant":
			prompt_label.text = "Press E — water and tend this wilting plant"
		"fetch":
			if bool(need["item_taken"]):
				prompt_label.text = "Press E — give the %s to %s" % [str(need["item"]), str(need["who"])]
			else:
				prompt_label.text = "Find the %s (%s), walk over it, then bring it to %s" % [str(need["item"]), str(need["where"]), str(need["who"])]
		_:
			prompt_label.text = "Press E — talk with %s" % str(need["who"])


func _unhandled_input(event: InputEvent) -> void:
	if state != State.PLAYING:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		var k := (event as InputEventKey).physical_keycode
		if k == KEY_E or k == KEY_SPACE or k == KEY_ENTER:
			_try_interact()


func _try_interact() -> void:
	var need := _nearest_need()
	if need.is_empty():
		return
	match str(need["type"]):
		"litter", "plant":
			_complete_need(need, 2)
		"fetch":
			if carrying == str(need["item"]):
				carrying = ""
				_complete_need(need, 2)
			else:
				_show_toast("You need the %s — it's %s. Walk over it to pick it up." % [str(need["item"]), str(need["where"])])
				_sound("ok")
		_:
			_open_dialog(need)


func _remove_need(id: int) -> void:
	for i in range(needs.size() - 1, -1, -1):
		if int(needs[i]["id"]) == id:
			needs.remove_at(i)
			return


func _complete_need(need: Dictionary, quality: int) -> void:
	# quality: 2 = thoughtful, 1 = partial, 0 = brushed off
	_remove_need(int(need["id"]))
	if quality == 2:
		kindness += 1
		warmth = clampf(warmth + 6.0, 0, 100)
		_add_hearts(need["pos"], 9)
		_add_flower(Vector2(need["pos"]) + Vector2(randf_range(-35, 35), randf_range(18, 46)))
		_add_flower(Vector2(need["pos"]) + Vector2(randf_range(-45, 45), randf_range(18, 55)))
		if int(need.get("npc", -1)) >= 0:
			var idx := int(need["npc"])
			if not bool(npcs[idx]["inspired"]):
				npcs[idx]["inspired"] = true
				npcs[idx]["ripple_timer"] = randf_range(9.0, 16.0)
		else:
			# Tending the commons inspires a random passer-by now and then.
			var idx := randi() % npcs.size()
			if not bool(npcs[idx]["inspired"]):
				npcs[idx]["inspired"] = true
				npcs[idx]["ripple_timer"] = randf_range(10.0, 18.0)
		_sound("good")
	elif quality == 1:
		kindness += 1
		warmth = clampf(warmth + 2.0, 0, 100)
		_add_hearts(need["pos"], 4)
		_add_flower(Vector2(need["pos"]) + Vector2(randf_range(-30, 30), randf_range(18, 42)))
		_sound("ok")
	else:
		warmth = clampf(warmth - 1.0, 0, 100)
		_sound("bad")


# ---------------------------------------------------------------- dialogue
func _dialog_data(kind: String, who: String) -> Dictionary:
	match kind:
		"listen":
			return {
				"title": "%s feels lonely" % who,
				"body": "%s sits alone on the bench. \"Everyone's so busy lately. I had some news I wanted to share… but I don't want to be a burden.\"" % who,
				"options": [
					{"text": "Sit down, ask about the news, and really listen", "q": 2, "r": "You listen without checking the time. %s's shoulders relax. \"Thank you for actually hearing me.\" Being heard is not a small thing — it tells someone they still belong." % who},
					{"text": "\"Cheer up! Stay positive!\" and hurry on", "q": 1, "r": "%s smiles politely, but the news stays unshared. Good intentions land better when we slow down enough to listen first." % who},
					{"text": "Smile and keep walking — someone else will stop", "q": 0, "r": "%s watches you go. When everyone assumes someone else will help, usually no one does." % who},
				],
			}
		"groceries":
			return {
				"title": "%s is struggling" % who,
				"body": "%s is juggling heavy shopping bags, stopping every few steps to rest their arms. Your hands are free." % who,
				"options": [
					{"text": "Ask which way they're going and carry a bag alongside them", "q": 2, "r": "You walk together and chat on the way. The bags are lighter — and so is the walk. Asking first keeps help kind rather than presumptuous."},
					{"text": "Grab a bag without asking and stride ahead quickly", "q": 1, "r": "The load is shared, but %s has to hurry to keep up with their own shopping. Help works best at the other person's pace." % who},
					{"text": "They look like they're managing — walk past", "q": 0, "r": "\"Managing\" often just means struggling quietly. A ten-second offer costs little and can change a whole afternoon."},
				],
			}
		"anxious":
			return {
				"title": "%s looks overwhelmed" % who,
				"body": "%s is staring at a long to-do list, tapping their foot. \"I don't even know where to start. Everything feels like too much.\"" % who,
				"options": [
					{"text": "Ask what feels heaviest, and help them pick one first step", "q": 2, "r": "Together you find one small, doable step. %s breathes out. Naming a feeling — and shrinking the mountain to a step — is real help." % who},
					{"text": "\"Don't worry, it'll be fine!\" and change the subject", "q": 1, "r": "You meant well, but %s still feels alone with the list. Reassurance helps most after someone feels understood." % who},
					{"text": "Everyone's stressed — leave them to it", "q": 0, "r": "True, everyone is stressed. That's exactly why a two-minute pause for one person matters so much."},
				],
			}
		_:
			return {
				"title": "%s is new here" % who,
				"body": "%s stands at the edge of the square holding a map upside down, too shy to ask anyone for directions." % who,
				"options": [
					{"text": "Introduce yourself, point out the landmarks, and invite them to the garden later", "q": 2, "r": "%s turns the map the right way up, laughing. A welcome is more than directions — it's an invitation to belong." % who},
					{"text": "Point vaguely toward the centre and walk off", "q": 1, "r": "%s finds the centre, eventually. A little warmth would have turned directions into a first friend." % who},
					{"text": "Pretend not to notice — newcomers should explore", "q": 0, "r": "Exploring is fun. Feeling invisible in a new place is not. One hello can redraw someone's whole map of a town."},
				],
			}


func _open_dialog(need: Dictionary) -> void:
	state = State.DIALOG
	current_dialog_need_id = int(need["id"])
	dialog_resolved = false
	var data := _dialog_data(str(need["type"]), str(need["who"]))
	dialog_title.text = str(data["title"])
	dialog_body.text = str(data["body"])
	var options: Array = (data["options"] as Array).duplicate()
	options.shuffle()
	for i in 3:
		var opt: Dictionary = options[i]
		dialog_buttons[i].text = str(opt["text"])
		dialog_buttons[i].set_meta("quality", int(opt["q"]))
		dialog_buttons[i].set_meta("response", str(opt["r"]))
		dialog_buttons[i].show()
	dialog_panel.show()
	_sound("ok")


func _on_dialog_option(idx: int) -> void:
	if state != State.DIALOG:
		return
	if dialog_resolved:
		dialog_panel.hide()
		state = State.PLAYING
		return
	var b := dialog_buttons[idx]
	var quality := int(b.get_meta("quality"))
	var response := str(b.get_meta("response"))
	# Complete the stored need, then show what happened.
	var stored: Dictionary = {}
	for n in needs:
		if int(n["id"]) == current_dialog_need_id:
			stored = n
			break
	if not stored.is_empty():
		_complete_need(stored, quality)
	dialog_resolved = true
	dialog_body.text = response
	dialog_buttons[0].text = "Continue  ▶"
	dialog_buttons[0].show()
	dialog_buttons[1].hide()
	dialog_buttons[2].hide()
	# Always route Continue through button 0.
	if idx != 0:
		# Move focus so the next click lands naturally; any visible button continues.
		pass


# ---------------------------------------------------------------- day flow
func _end_day() -> void:
	state = State.SUMMARY
	summary_is_ending = day >= TOTAL_DAYS
	needs.clear()
	carrying = ""
	var did_kind := kindness - day_kindness_start
	var did_ripple := ripples - day_ripples_start
	var did_expired := expired_count - day_expired_start
	if summary_is_ending:
		_show_ending(did_kind, did_ripple, did_expired)
		return
	summary_panel.show()
	summary_title.text = "Evening of Day %d" % day
	summary_body.text = "Today you helped thoughtfully %d time(s).\nYour kindness rippled onward %d time(s) through other people.\n%d need(s) were left waiting.\n\nVillage warmth: %d / 100      Flowers blooming: %d\n\nKindness is a skill. Rest, reflection and company all make tomorrow's noticing easier — choose one:" % [did_kind, did_ripple, did_expired, int(warmth), flowers.size()]
	summary_buttons[0].text = "🌙  Rest well  —  walk a little faster tomorrow"
	summary_buttons[1].text = "🔎  Reflect & notice more  —  needs stay a little longer tomorrow"
	summary_buttons[2].text = "💛  Message a friend  —  someone starts tomorrow inspired"
	for b in summary_buttons:
		b.show()
	summary_main_button.hide()
	_sound("day")


func _on_reflection_option(idx: int) -> void:
	if state != State.SUMMARY or summary_is_ending:
		return
	speed_mult = 1.0
	match idx:
		0:
			speed_mult = 1.18
		1:
			need_time_bonus = 10.0
		2:
			inspire_next = true
	if idx != 1:
		need_time_bonus = 0.0
	day += 1
	summary_panel.hide()
	_start_day()
	_show_toast("Day %d — notice one more person than yesterday." % day)


func _show_ending(did_kind: int, did_ripple: int, did_expired: int) -> void:
	state = State.ENDING
	summary_panel.show()
	var title := "🌸  A Village in Bloom"
	var verdict := "Look at this place. People greet each other now. Helped neighbours help others before you even arrive. This is what happens when kindness becomes a habit a whole community shares."
	if warmth < 55.0:
		title = "🌱  Seeds Planted"
		verdict = "Some seeds sprouted; some needs waited too long. That's honest — real villages are like that too. The hopeful part: every single thoughtful act still counted, and several grew into ripples."
	elif warmth < 78.0:
		title = "🌼  A Warmer Village"
		verdict = "The village feels noticeably warmer. People have started looking out for each other between your visits. A few more noticed moments each day and it would truly bloom."
	summary_title.text = title
	summary_body.text = "%s\n\nOver %d days:  %d thoughtful acts  •  %d ripples  •  %d needs missed  •  warmth %d/100\n\n★ YOUR REAL-WORLD QUEST ★\nToday, in real life: notice one person, pause, and do one small helpful thing well — listen fully, carry the bag, send the message, tend a shared space. Then watch for the ripple." % [verdict, TOTAL_DAYS, kindness, ripples, expired_count, int(warmth)]
	for b in summary_buttons:
		b.hide()
	summary_main_button.text = "↻  Play again — five new days"
	summary_main_button.show()
	_sound("good")
	# did_* kept for signature clarity / future stats; silence unused warnings by referencing:
	if did_kind + did_ripple + did_expired == -999:
		print("never")


func _on_summary_main_pressed() -> void:
	if state != State.ENDING:
		return
	_reset_game()
	summary_panel.hide()
	_start_day()


func _show_toast(text: String) -> void:
	toast_label.text = text
	toast_timer = 4.2


func _update_stats() -> void:
	if day_label == null:
		return
	day_label.text = "Day %d of %d" % [mini(day, TOTAL_DAYS), TOTAL_DAYS]
	stats_label.text = "❤ Kindness %d    ✨ Ripples %d    🌡 Warmth %d/100    🌸 %d" % [kindness, ripples, int(warmth), flowers.size()]
	if state == State.PLAYING or state == State.DIALOG:
		timer_label.text = "☀ %d sec left" % int(ceil(time_left))
	else:
		timer_label.text = ""
	carry_label.text = ("🎒 " + carrying) if carrying != "" else "Hands free"


# ---------------------------------------------------------------- drawing
func _ellipse_points(center: Vector2, rx: float, ry: float, count := 28) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in count:
		var a := TAU * float(i) / float(count)
		pts.append(center + Vector2(cos(a) * rx, sin(a) * ry))
	return pts


func _draw_house(rect: Rect2, wall: Color, roof: Color, label_col: Color) -> void:
	draw_rect(rect, wall)
	draw_rect(rect, Color(0, 0, 0, 0.12), false, 3.0)
	var roof_pts := PackedVector2Array([
		rect.position + Vector2(-10, 4), rect.position + Vector2(rect.size.x * 0.5, -34),
		rect.position + Vector2(rect.size.x + 10, 4)])
	draw_colored_polygon(roof_pts, roof)
	draw_rect(Rect2(rect.get_center() + Vector2(-13, 12), Vector2(26, rect.size.y - 12)), Color(0.42, 0.28, 0.18))
	draw_circle(rect.get_center() + Vector2(7, rect.size.y * 0.62), 3, Color(1, 0.9, 0.5))
	draw_rect(Rect2(rect.position + Vector2(16, 28), Vector2(28, 24)), Color(0.85, 0.95, 1))
	draw_rect(Rect2(rect.position + Vector2(rect.size.x - 44, 28), Vector2(28, 24)), Color(0.85, 0.95, 1))
	draw_circle(rect.position + Vector2(rect.size.x * 0.5, 18), 7, label_col)


func _draw_person(pos: Vector2, body_col: Color, face_dir: Vector2, is_player: bool, inspired: bool, sad: bool, t: float) -> void:
	var bob := sin(t * 6.0 + pos.x * 0.05) * 1.2 if is_player else sin(t * 3.0 + pos.y * 0.07) * 0.8
	var p := pos + Vector2(0, bob)
	draw_colored_polygon(_ellipse_points(p + Vector2(0, 18), 16, 6), Color(0, 0, 0, 0.22))
	if inspired:
		draw_arc(p + Vector2(0, 2), 24 + sin(t * 3.0) * 2.0, 0, TAU, 32, Color(1, 0.85, 0.3, 0.85), 2.5)
	if is_player:
		draw_circle(p + Vector2(-face_dir.x * 3.0, 8), 13, Color(0.12, 0.45, 0.55))
	draw_circle(p + Vector2(0, 6), 15, body_col)
	draw_circle(p + Vector2(0, -12), 10.5, Color(0.98, 0.82, 0.66))
	# hair cap
	draw_arc(p + Vector2(0, -14), 10, PI, TAU, 16, body_col.darkened(0.25), 6.0)
	var eye_off := face_dir * 3.0
	draw_circle(p + Vector2(-4, -12) + eye_off, 1.7, Color(0.1, 0.1, 0.12))
	draw_circle(p + Vector2(4, -12) + eye_off, 1.7, Color(0.1, 0.1, 0.12))
	if sad:
		draw_arc(p + Vector2(0, -4) + eye_off, 4, PI * 1.15, PI * 1.85, 12, Color(0.1, 0.1, 0.12), 1.6)
	else:
		draw_arc(p + Vector2(0, -7) + eye_off, 4, PI * 0.15, PI * 0.85, 12, Color(0.1, 0.1, 0.12), 1.6)
	if is_player:
		draw_circle(p + Vector2(0, -30), 0.1, Color.TRANSPARENT)


func _draw_heart(pos: Vector2, s: float, col: Color) -> void:
	var pts := PackedVector2Array()
	for i in 24:
		var a := TAU * float(i) / 24.0
		var x := 16.0 * pow(sin(a), 3.0)
		var y := 13.0 * cos(a) - 5.0 * cos(2 * a) - 2.0 * cos(3 * a) - cos(4 * a)
		pts.append(pos + Vector2(x, -y) * s)
	draw_colored_polygon(pts, col)


func _draw() -> void:
	var t := float(Time.get_ticks_msec()) / 1000.0
	var warm_mix := clampf(warmth / 100.0, 0, 1)
	var grass := Color(0.48, 0.52, 0.43).lerp(Color(0.30, 0.62, 0.32), warm_mix)
	draw_rect(Rect2(Vector2.ZERO, VIEW), grass)
	# subtle grass patches
	for i in 14:
		var gx := float((i * 173) % 1080 + 30)
		var gy := float((i * 211) % 540 + 80)
		draw_colored_polygon(_ellipse_points(Vector2(gx, gy), 34, 13), grass.darkened(0.06 + 0.01 * float(i % 3)))

	# paths
	var path_col := Color(0.86, 0.78, 0.60)
	draw_rect(Rect2(0, 232, VIEW.x, 46), path_col)
	draw_rect(Rect2(548, 58, 56, 560), path_col)
	draw_rect(Rect2(0, 420, VIEW.x, 38), path_col)

	# community garden
	draw_rect(Rect2(58, 468, 310, 124), Color(0.48, 0.34, 0.22))
	for r in 3:
		draw_rect(Rect2(70, 482 + r * 36, 286, 22), Color(0.40, 0.27, 0.17))
	draw_rect(Rect2(58, 468, 310, 124), Color(1, 1, 1, 0.35), false, 2.0)

	# pond
	draw_colored_polygon(_ellipse_points(Vector2(980, 528), 108, 52), Color(0.35, 0.62, 0.85))
	draw_colored_polygon(_ellipse_points(Vector2(962, 514), 62, 24), Color(0.55, 0.78, 0.95, 0.7))

	# buildings
	_draw_house(Rect2(64, 92, 150, 92), Color(0.96, 0.82, 0.62), Color(0.78, 0.38, 0.30), Color(0.95, 0.5, 0.4))
	_draw_house(Rect2(292, 84, 160, 94), Color(0.78, 0.86, 0.98), Color(0.35, 0.48, 0.72), Color(0.4, 0.65, 1))
	_draw_house(Rect2(674, 84, 160, 94), Color(0.98, 0.88, 0.70), Color(0.62, 0.42, 0.78), Color(0.8, 0.6, 1))
	_draw_house(Rect2(918, 92, 160, 92), Color(0.86, 0.95, 0.78), Color(0.38, 0.62, 0.38), Color(0.55, 0.9, 0.55))
	_draw_house(Rect2(64, 286, 156, 98), Color(0.92, 0.78, 0.88), Color(0.55, 0.38, 0.55), Color(1, 0.75, 0.9))
	_draw_house(Rect2(932, 286, 144, 98), Color(1, 0.90, 0.66), Color(0.82, 0.55, 0.28), Color(1, 0.8, 0.4))

	# trees
	for tree_pos in [Vector2(255, 150), Vector2(625, 165), Vector2(875, 175), Vector2(255, 365), Vector2(880, 390), Vector2(430, 340), Vector2(700, 350)]:
		draw_rect(Rect2(tree_pos + Vector2(-5, 4), Vector2(10, 22)), Color(0.45, 0.32, 0.20))
		draw_circle(tree_pos + Vector2(0, -12), 24, Color(0.22, 0.52, 0.28).lerp(Color(0.3, 0.66, 0.3), warm_mix))
		draw_circle(tree_pos + Vector2(-14, 0), 16, Color(0.26, 0.58, 0.30))

	# well
	draw_circle(Vector2(576, 300), 30, Color(0.62, 0.62, 0.66))
	draw_circle(Vector2(576, 300), 20, Color(0.25, 0.45, 0.70))
	draw_rect(Rect2(548, 252, 56, 8), Color(0.45, 0.32, 0.20))

	# bench
	draw_rect(Rect2(548, 188, 56, 10), Color(0.55, 0.38, 0.22))
	draw_rect(Rect2(552, 198, 8, 12), Color(0.4, 0.28, 0.16))
	draw_rect(Rect2(592, 198, 8, 12), Color(0.4, 0.28, 0.16))

	# flowers (the village visibly blooms as warmth rises)
	for f in flowers:
		var fp: Vector2 = f["pos"]
		var sway := sin(t * 2.0 + float(f["phase"])) * 2.0
		draw_line(fp, fp + Vector2(sway, -9), Color(0.25, 0.55, 0.25), 2.0)
		for petal in 5:
			var a := TAU * float(petal) / 5.0
			draw_circle(fp + Vector2(sway, -11) + Vector2(cos(a), sin(a)) * 4.5, 3.4, f["color"])
		draw_circle(fp + Vector2(sway, -11), 2.6, Color(1, 0.9, 0.4))

	# unattended garden plants look thirsty until tended (drawn under need markers anyway)
	for spot in PLANT_SPOTS:
		draw_line(spot, spot + Vector2(0, -12), Color(0.3, 0.5, 0.25), 2.5)
		draw_circle(spot + Vector2(-5, -13), 5, Color(0.42, 0.62, 0.32))
		draw_circle(spot + Vector2(5, -15), 5, Color(0.48, 0.68, 0.36))

	# NPCs, then player
	for npc in npcs:
		_draw_person(npc["pos"], npc["color"], Vector2.DOWN, false, bool(npc["inspired"]), float(npc["sad"]) > 0.0, t)
	_draw_person(player_pos, Color(0.16, 0.62, 0.58), player_face, true, false, false, t)
	# player marker ring
	draw_arc(player_pos + Vector2(0, 16), 18, 0, TAU, 28, Color(1, 1, 1, 0.55), 2.0)

	# needs: item on the ground + floating bubble marker
	for need in needs:
		if str(need["type"]) == "fetch" and not bool(need["item_taken"]):
			var ip: Vector2 = need["item_pos"]
			var pulse := 15.0 + sin(t * 5.0) * 3.0
			draw_arc(ip, pulse, 0, TAU, 28, Color(1, 0.85, 0.3, 0.9), 3.0)
			draw_rect(Rect2(ip - Vector2(10, 8), Vector2(20, 16)), Color(0.95, 0.72, 0.30))
			draw_rect(Rect2(ip - Vector2(10, 2), Vector2(20, 4)), Color(0.65, 0.42, 0.18))
		var bp: Vector2 = Vector2(need["pos"]) + Vector2(0, -52 + sin(t * 4.0 + float(int(need["id"]))) * 4.0)
		var frac := clampf(float(need["timer"]) / maxf(1.0, float(need["max_timer"])), 0, 1)
		draw_circle(bp, 17, Color(1, 1, 1, 0.96))
		draw_arc(bp, 17, -PI / 2.0, -PI / 2.0 + TAU * frac, 28, Color(0.92, 0.35, 0.30) if frac < 0.3 else Color(0.25, 0.65, 0.55), 4.0)
		match str(need["type"]):
			"litter":
				draw_rect(Rect2(bp - Vector2(7, 5), Vector2(14, 10)), Color(0.55, 0.45, 0.35))
				draw_circle(bp + Vector2(-4, -7), 3, Color(0.8, 0.8, 0.82))
			"plant":
				draw_colored_polygon(PackedVector2Array([bp + Vector2(0, -9), bp + Vector2(6, 2), bp + Vector2(3, 7), bp + Vector2(-3, 7), bp + Vector2(-6, 2)]), Color(0.3, 0.62, 0.95))
			"fetch":
				draw_rect(Rect2(bp - Vector2(8, 7), Vector2(16, 14)), Color(0.95, 0.72, 0.30))
				draw_line(bp + Vector2(-8, 0), bp + Vector2(8, 0), Color(0.65, 0.42, 0.18), 3.0)
			_:
				# speech bubble: three dots
				draw_circle(bp + Vector2(-6, 0), 2.6, Color(0.25, 0.45, 0.65))
				draw_circle(bp, 2.6, Color(0.25, 0.45, 0.65))
				draw_circle(bp + Vector2(6, 0), 2.6, Color(0.25, 0.45, 0.65))
		# litter pile itself on the ground
		if str(need["type"]) == "litter":
			var lp: Vector2 = need["pos"]
			draw_rect(Rect2(lp - Vector2(11, 4), Vector2(12, 8)), Color(0.62, 0.55, 0.45))
			draw_rect(Rect2(lp + Vector2(1, -7), Vector2(11, 8)), Color(0.78, 0.76, 0.72))
			draw_circle(lp + Vector2(12, 2), 4, Color(0.85, 0.45, 0.4))

	# floating hearts / sparkles
	for p in particles:
		var alpha := clampf(float(p["life"]) / 1.3, 0, 1)
		var col: Color = p["color"]
		col.a = alpha
		_draw_heart(p["pos"], 0.55, col)
