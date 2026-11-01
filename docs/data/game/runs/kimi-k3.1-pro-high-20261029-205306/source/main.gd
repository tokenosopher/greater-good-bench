extends Control

# Common Ground — all art, interface, and game logic are procedural and self-contained.
const DESIGN = Vector2(1280, 800)
const INK = Color("#173f3a")
const INK_SOFT = Color("#48645e")
const CREAM = Color("#f4f5ed")
const PAPER = Color("#fffdf7")
const GREEN = Color("#3f826b")
const GREEN_LIGHT = Color("#dcebe0")
const GOLD = Color("#edbd58")
const GOLD_LIGHT = Color("#fbefcf")
const BLUE = Color("#5d8ea0")
const BLUE_LIGHT = Color("#e0edf0")
const CORAL = Color("#d77962")
const CORAL_LIGHT = Color("#f6e3dc")
const RED = Color("#b9564f")
const LINE = Color("#d9e1d8")

var screen = "title"
var districts: Array[Dictionary] = []
var actions: Array[Dictionary] = []
var current_event: Dictionary = {}
var week = 1
var energy = 3
var supplies = 7
var selected_district = 0
var selected_action = -1
var buttons: Array[Dictionary] = []
var district_rects: Array[Rect2] = []
var mouse_design = Vector2.ZERO
var view_scale = 1.0
var view_offset = Vector2.ZERO
var font: Font
var help_open = false
var tutorial_open = false
var report_lines: Array[String] = []
var report_title = ""
var toast = ""
var toast_time = 0.0
var particles: Array[Dictionary] = []
var elapsed = 0.0
var rng = RandomNumberGenerator.new()

func _ready():
	font = ThemeDB.fallback_font
	mouse_filter = Control.MOUSE_FILTER_STOP
	rng.randomize()
	_make_actions()
	_reset_data()
	queue_redraw()

func _make_actions():
	actions = [
		{"id": "aid", "name": "Mutual aid", "desc": "-18 need   +4 trust", "cost": 2, "color": CORAL, "pale": CORAL_LIGHT},
		{"id": "listen", "name": "Listening circle", "desc": "+16 trust   -4 need", "cost": 0, "color": BLUE, "pale": BLUE_LIGHT},
		{"id": "garden", "name": "Community garden", "desc": "+22 green   -6 need", "cost": 3, "color": GREEN, "pale": GREEN_LIGHT},
		{"id": "prepare", "name": "Prepare together", "desc": "+24 ready   +3 trust", "cost": 2, "color": GOLD, "pale": GOLD_LIGHT},
		{"id": "skills", "name": "Skill share", "desc": "-10 need   +7 trust   +7 ready", "cost": 1, "color": Color("#8b75a5"), "pale": Color("#ece6f1")}
	]

func _reset_data():
	districts = [
		{"name": "North Market", "short": "NORTH", "need": 42.0, "trust": 48.0, "green": 45.0, "prep": 32.0},
		{"name": "Riverside", "short": "RIVER", "need": 56.0, "trust": 38.0, "green": 32.0, "prep": 24.0},
		{"name": "Old Town", "short": "OLD TOWN", "need": 35.0, "trust": 55.0, "green": 60.0, "prep": 40.0},
		{"name": "Southbank", "short": "SOUTH", "need": 63.0, "trust": 32.0, "green": 25.0, "prep": 20.0}
	]
	week = 1
	energy = 3
	supplies = 7
	selected_district = 0
	selected_action = -1
	current_event = _make_event(week)
	particles.clear()
	toast_time = 0.0

func _start_game():
	_reset_data()
	screen = "play"
	help_open = false
	tutorial_open = true
	queue_redraw()

func _process(delta):
	elapsed += delta
	if toast_time > 0.0:
		toast_time -= delta
	for i in range(particles.size() - 1, -1, -1):
		particles[i]["life"] -= delta
		particles[i]["pos"] += particles[i]["vel"] * delta
		particles[i]["vel"].y += 25.0 * delta
		if particles[i]["life"] <= 0.0:
			particles.remove_at(i)
	queue_redraw()

func _make_event(for_week: int) -> Dictionary:
	var target = rng.randi_range(0, 3)
	var kind = "heat"
	match for_week:
		1:
			kind = "heat"
		2:
			kind = "storm"
		3:
			kind = "grant"
		4:
			kind = "flu"
		5:
			kind = "festival"
		6:
			kind = "heat"
			target = -1
		7:
			kind = "layoffs"
		8:
			kind = "storm"
			target = -1
		9:
			kind = "neighbors"
		10:
			kind = "festival"
			target = -1
	var data = {"kind": kind, "target": target}
	match kind:
		"heat":
			data["title"] = "Heat wave"
			data["desc"] = "Green space and readiness reduce the rise in need."
			data["color"] = CORAL
		"storm":
			data["title"] = "Heavy storm"
			data["desc"] = "Readiness is the best protection; green space also helps."
			data["color"] = BLUE
		"grant":
			data["title"] = "Community grant"
			data["desc"] = "A shared grant adds 5 supplies. No neighborhood is harmed."
			data["color"] = GREEN
			data["target"] = -1
		"flu":
			data["title"] = "Flu season"
			data["desc"] = "Trust and readiness reduce its impact across the whole city."
			data["color"] = Color("#8b75a5")
			data["target"] = -1
		"festival":
			data["title"] = "Street festival"
			data["desc"] = "Everyone gains 7 trust and loses 3 need. A week to celebrate!"
			data["color"] = GOLD
			data["target"] = -1
		"layoffs":
			data["title"] = "Local layoffs"
			data["desc"] = "Trust and readiness cushion the shock for neighbors."
			data["color"] = CORAL
		"neighbors":
			data["title"] = "New neighbors"
			data["desc"] = "A warm welcome adds trust; strong trust reduces new need."
			data["color"] = GREEN
	return data

func _event_scope() -> String:
	if current_event.is_empty():
		return ""
	if int(current_event["target"]) < 0:
		return "ALL NEIGHBORHOODS"
	return districts[int(current_event["target"])]["name"].to_upper()

func _wellbeing() -> float:
	if districts.is_empty():
		return 0.0
	var total = 0.0
	for d in districts:
		total += 100.0 - float(d["need"])
	return total / districts.size()

func _average(key: String) -> float:
	var total = 0.0
	for d in districts:
		total += float(d[key])
	return total / max(1, districts.size())

func _fairness() -> float:
	var lowest = 100.0
	var highest = 0.0
	for d in districts:
		lowest = min(lowest, float(d["need"]))
		highest = max(highest, float(d["need"]))
	return 100.0 - (highest - lowest)

func _local_wellbeing(d: Dictionary) -> float:
	return 100.0 - float(d["need"])

func _won() -> bool:
	if _wellbeing() < 65.0 or _average("trust") < 45.0 or _average("green") < 40.0:
		return false
	for d in districts:
		if _local_wellbeing(d) < 50.0:
			return false
	return true

func _score() -> int:
	return int(round((_wellbeing() + _average("trust") + _average("green") + _fairness()) / 4.0))

func _status(d: Dictionary) -> String:
	var value = float(d["need"])
	if value <= 35.0:
		return "THRIVING"
	if value <= 55.0:
		return "STEADY"
	if value <= 70.0:
		return "STRAINED"
	return "IN CRISIS"

func _status_color(d: Dictionary) -> Color:
	var value = float(d["need"])
	if value <= 35.0:
		return GREEN
	if value <= 55.0:
		return BLUE
	if value <= 70.0:
		return Color("#c88a36")
	return RED

func _apply_action(district_index: int):
	if selected_action < 0 or selected_action >= actions.size():
		_show_toast("Choose a project first.")
		return
	if energy <= 0:
		_show_toast("No time left — end the week when you're ready.")
		return
	var action = actions[selected_action]
	if supplies < int(action["cost"]):
		_show_toast("Not enough supplies. Listening circles are always free.")
		return
	selected_district = district_index
	var d = districts[district_index]
	energy -= 1
	supplies -= int(action["cost"])
	match String(action["id"]):
		"aid":
			d["need"] = float(d["need"]) - 18.0
			d["trust"] = float(d["trust"]) + 4.0
			d["prep"] = float(d["prep"]) + 3.0
		"listen":
			d["trust"] = float(d["trust"]) + 16.0
			d["need"] = float(d["need"]) - 4.0
		"garden":
			d["green"] = float(d["green"]) + 22.0
			d["need"] = float(d["need"]) - 6.0
			d["prep"] = float(d["prep"]) + 4.0
		"prepare":
			d["prep"] = float(d["prep"]) + 24.0
			d["trust"] = float(d["trust"]) + 3.0
		"skills":
			d["need"] = float(d["need"]) - 10.0
			d["trust"] = float(d["trust"]) + 7.0
			d["prep"] = float(d["prep"]) + 7.0
	_clamp_district(d)
	_spawn_particles(district_index, action["color"])
	_show_toast(String(action["name"]) + " → " + String(d["name"]))
	if energy <= 0:
		selected_action = -1

func _clamp_district(d: Dictionary):
	for key in ["need", "trust", "green", "prep"]:
		d[key] = clampf(float(d[key]), 0.0, 100.0)

func _end_week():
	if screen != "play" or help_open or tutorial_open:
		return
	report_lines.clear()
	report_title = String(current_event["title"])
	# Ordinary life creates pressure; past investments create recurring support.
	for d in districts:
		d["need"] = float(d["need"]) + 3.0
		if float(d["green"]) >= 60.0:
			d["need"] = float(d["need"]) - 2.0
		if float(d["trust"]) >= 65.0:
			d["need"] = float(d["need"]) - 2.0
		d["green"] = float(d["green"]) - 1.0
		d["prep"] = float(d["prep"]) - 3.0
		_clamp_district(d)
	report_lines.append("Weekly pressure added 3 need. Green neighborhoods (60+) and trusted neighborhoods (65+) each softened it by 2.")
	var kind = String(current_event["kind"])
	var target = int(current_event["target"])
	match kind:
		"grant":
			supplies = mini(12, supplies + 5)
			report_lines.append("The community grant added 5 supplies, ready for the weeks ahead.")
		"festival":
			for d in districts:
				d["trust"] = float(d["trust"]) + 7.0
				d["need"] = float(d["need"]) - 3.0
				_clamp_district(d)
			report_lines.append("Shared joy crossed every boundary: +7 trust and -3 need everywhere.")
		_:
			var affected: Array[int] = []
			if target < 0:
				affected = [0, 1, 2, 3]
			else:
				affected = [target]
			var total_impact = 0
			for index in affected:
				var d = districts[index]
				var impact = 0
				match kind:
					"heat":
						impact = int(max(2, round(15.0 - float(d["green"]) * 0.10 - float(d["prep"]) * 0.16)))
						d["green"] = float(d["green"]) - 2.0
					"storm":
						impact = int(max(1, round(13.0 - float(d["prep"]) * 0.20 - float(d["green"]) * 0.04)))
						d["prep"] = float(d["prep"]) - 8.0
					"flu":
						impact = int(max(2, round(12.0 - float(d["trust"]) * 0.10 - float(d["prep"]) * 0.08)))
					"layoffs":
						impact = int(max(3, round(14.0 - float(d["trust"]) * 0.08 - float(d["prep"]) * 0.10)))
					"neighbors":
						impact = int(max(3, round(10.0 - float(d["trust"]) * 0.08)))
						d["trust"] = float(d["trust"]) + 4.0
				d["need"] = float(d["need"]) + impact
				total_impact += impact
				_clamp_district(d)
			if kind == "neighbors":
				report_lines.append(_event_scope().capitalize() + " welcomed new neighbors: +" + str(total_impact) + " need there, and +4 trust from showing up together.")
			elif target < 0:
				report_lines.append("The citywide impact added " + str(total_impact) + " total need across four neighborhoods. Preparation turned a harder hit into a manageable one.")
			else:
				report_lines.append(String(districts[target]["name"]) + " absorbed the challenge with +" + str(total_impact) + " need. Investments before the crisis reduced its impact.")
	selected_action = -1
	screen = "report"

func _continue_report():
	if week >= 10:
		screen = "end"
	else:
		week += 1
		energy = 3
		supplies = mini(12, supplies + 2)
		current_event = _make_event(week)
		screen = "play"
		_show_toast("Week " + str(week) + ": 3 time and 2 new supplies.")

func _show_toast(message: String):
	toast = message
	toast_time = 2.8

func _spawn_particles(index: int, color: Color):
	if district_rects.size() != 4:
		return
	var center = district_rects[index].get_center()
	for i in range(14):
		var angle = rng.randf_range(-PI, 0.0)
		var speed = rng.randf_range(35.0, 95.0)
		particles.append({"pos": center, "vel": Vector2(cos(angle), sin(angle)) * speed, "life": rng.randf_range(0.55, 1.0), "color": color})

# ---------- Input ----------

func _to_design(point: Vector2) -> Vector2:
	return (point - view_offset) / max(0.001, view_scale)

func _input(event):
	if event is InputEventMouseMotion:
		mouse_design = _to_design(event.position)
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		mouse_design = _to_design(event.position)
		for i in range(buttons.size() - 1, -1, -1):
			var b = buttons[i]
			if b["enabled"] and b["rect"].has_point(mouse_design):
				_activate(String(b["id"]))
				get_viewport().set_input_as_handled()
				return
	if event is InputEventKey and event.pressed and not event.echo:
		_handle_key(event.keycode)

func _handle_key(key: int):
	if key == KEY_H:
		if screen == "play":
			help_open = not help_open
			tutorial_open = false
		return
	if key == KEY_ESCAPE:
		if help_open or tutorial_open:
			help_open = false
			tutorial_open = false
		elif screen == "play":
			selected_action = -1
		return
	if screen == "title" and key == KEY_ENTER:
		_start_game()
		return
	if screen == "report" and key == KEY_ENTER:
		_continue_report()
		return
	if screen == "end" and (key == KEY_R or key == KEY_ENTER):
		_start_game()
		return
	if screen != "play" or help_open or tutorial_open:
		return
	if key >= KEY_1 and key <= KEY_5:
		selected_action = key - KEY_1
	elif key == KEY_LEFT:
		selected_district = posmod(selected_district - 1, 4)
	elif key == KEY_RIGHT:
		selected_district = posmod(selected_district + 1, 4)
	elif key == KEY_SPACE:
		_apply_action(selected_district)
	elif key == KEY_E:
		_end_week()

func _activate(id: String):
	if id == "start" or id == "restart":
		_start_game()
	elif id == "how":
		help_open = true
	elif id == "close_help":
		help_open = false
		tutorial_open = false
	elif id == "help":
		help_open = true
	elif id == "end_week":
		_end_week()
	elif id == "continue":
		_continue_report()
	elif id == "title":
		screen = "title"
		help_open = false
	elif id.begins_with("action_"):
		selected_action = int(id.trim_prefix("action_"))
	elif id.begins_with("district_"):
		var index = int(id.trim_prefix("district_"))
		selected_district = index
		if selected_action >= 0:
			_apply_action(index)

# ---------- Drawing helpers ----------

func _panel(rect: Rect2, color: Color, radius: int = 14, border: Color = Color.TRANSPARENT, border_width: int = 0):
	var style = StyleBoxFlat.new()
	style.bg_color = color
	style.set_corner_radius_all(radius)
	if border_width > 0:
		style.border_color = border
		style.set_border_width_all(border_width)
	draw_style_box(style, rect)

func _text(value: String, pos: Vector2, font_size: int = 18, color: Color = INK):
	draw_string(font, pos, value, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)

func _center(value: String, rect: Rect2, font_size: int = 18, color: Color = INK):
	var text_size = font.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size)
	var pos = rect.position + Vector2((rect.size.x - text_size.x) * 0.5, (rect.size.y + text_size.y * 0.72) * 0.5)
	draw_string(font, pos, value, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)

func _right(value: String, pos: Vector2, font_size: int = 18, color: Color = INK):
	var width = font.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
	_text(value, pos - Vector2(width, 0), font_size, color)

func _wrapped(value: String, rect: Rect2, font_size: int = 16, color: Color = INK_SOFT, line_gap: float = 5.0):
	var words = value.split(" ")
	var line = ""
	var y = rect.position.y + font_size
	for word in words:
		var attempt = line + ("" if line.is_empty() else " ") + word
		if font.get_string_size(attempt, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x > rect.size.x and not line.is_empty():
			_text(line, Vector2(rect.position.x, y), font_size, color)
			y += font_size + line_gap
			line = word
		else:
			line = attempt
	if not line.is_empty():
		_text(line, Vector2(rect.position.x, y), font_size, color)

func _button(id: String, rect: Rect2, label: String, style: String = "primary", enabled: bool = true):
	var hovered = rect.has_point(mouse_design) and enabled
	var fill = INK
	var text_color = PAPER
	if style == "secondary":
		fill = PAPER
		text_color = INK
	elif style == "soft":
		fill = GREEN_LIGHT
		text_color = INK
	elif style == "gold":
		fill = GOLD
		text_color = INK
	if not enabled:
		fill = Color("#e4e8e1")
		text_color = Color("#93a09a")
	elif hovered:
		fill = fill.lightened(0.08)
	_panel(rect, fill, 10, INK if style == "secondary" else Color.TRANSPARENT, 1 if style == "secondary" else 0)
	_center(label, rect, 17, text_color)
	buttons.append({"id": id, "rect": rect, "enabled": enabled})

func _pill(value: String, rect: Rect2, fill: Color, color: Color = INK, font_size: int = 12):
	_panel(rect, fill, int(rect.size.y * 0.5))
	_center(value, rect, font_size, color)

func _bar(rect: Rect2, value: float, color: Color, back: Color = Color("#e7ece5")):
	_panel(rect, back, int(rect.size.y * 0.5))
	var filled = Rect2(rect.position, Vector2(rect.size.x * clampf(value / 100.0, 0.0, 1.0), rect.size.y))
	if filled.size.x > 1.0:
		_panel(filled, back.blend(color), int(rect.size.y * 0.5))
		filled.size.x = max(0.0, filled.size.x - rect.size.y * 0.5)
		draw_rect(filled, color)

func _draw_icon(kind: String, center: Vector2, color: Color, scale_value: float = 1.0):
	var c = center
	var s = scale_value
	match kind:
		"aid":
			draw_circle(c + Vector2(-6, -3) * s, 7 * s, color)
			draw_circle(c + Vector2(6, -3) * s, 7 * s, color)
			draw_colored_polygon(PackedVector2Array([c + Vector2(-13, 0) * s, c + Vector2(13, 0) * s, c + Vector2(0, 14) * s]), color)
		"listen":
			draw_arc(c, 12 * s, -PI * 0.65, PI * 0.65, 24, color, 3 * s, true)
			draw_arc(c, 6 * s, -PI * 0.65, PI * 0.65, 20, color, 3 * s, true)
			draw_circle(c + Vector2(2, 9) * s, 3 * s, color)
		"garden":
			draw_line(c + Vector2(0, 12) * s, c + Vector2(0, -8) * s, color, 3 * s, true)
			draw_circle(c + Vector2(-6, -6) * s, 7 * s, color)
			draw_circle(c + Vector2(6, -11) * s, 7 * s, color)
			draw_line(c + Vector2(-10, 13) * s, c + Vector2(10, 13) * s, color, 3 * s, true)
		"prepare":
			var points = PackedVector2Array([c + Vector2(0, -14) * s, c + Vector2(12, -9) * s, c + Vector2(10, 5) * s, c + Vector2(0, 14) * s, c + Vector2(-10, 5) * s, c + Vector2(-12, -9) * s])
			draw_colored_polygon(points, color)
			draw_polyline(PackedVector2Array([c + Vector2(-5, 0) * s, c + Vector2(-1, 5) * s, c + Vector2(7, -5) * s]), PAPER, 2.5 * s, true)
		"skills":
			draw_line(c + Vector2(-8, -7) * s, c + Vector2(8, 7) * s, color, 3 * s, true)
			draw_line(c + Vector2(8, -7) * s, c + Vector2(-8, 7) * s, color, 3 * s, true)
			for p in [Vector2(-8, -7), Vector2(8, -7), Vector2(-8, 7), Vector2(8, 7)]:
				draw_circle(c + p * s, 5 * s, color)
		_:
			draw_circle(c, 11 * s, color)

func _logo(pos: Vector2, size_value: float = 1.0):
	_panel(Rect2(pos, Vector2(42, 42) * size_value), GOLD, 12)
	draw_line(pos + Vector2(21, 31) * size_value, pos + Vector2(21, 13) * size_value, INK, 3 * size_value, true)
	draw_line(pos + Vector2(21, 20) * size_value, pos + Vector2(13, 14) * size_value, INK, 3 * size_value, true)
	draw_line(pos + Vector2(21, 23) * size_value, pos + Vector2(29, 17) * size_value, INK, 3 * size_value, true)
	draw_circle(pos + Vector2(12, 12) * size_value, 6 * size_value, GREEN)
	draw_circle(pos + Vector2(30, 15) * size_value, 6 * size_value, GREEN)

# ---------- Screens ----------

func _draw():
	buttons.clear()
	district_rects.clear()
	view_scale = min(size.x / DESIGN.x, size.y / DESIGN.y)
	view_offset = (size - DESIGN * view_scale) * 0.5
	draw_rect(Rect2(Vector2.ZERO, size), INK)
	draw_set_transform(view_offset, 0.0, Vector2.ONE * view_scale)
	draw_rect(Rect2(Vector2.ZERO, DESIGN), CREAM)
	match screen:
		"title":
			_draw_title()
		"play", "report":
			_draw_play()
			if screen == "report":
				_draw_report()
		"end":
			_draw_end()
	if help_open:
		_draw_help(false)
	elif tutorial_open:
		_draw_help(true)
	if toast_time > 0.0 and screen == "play" and not help_open and not tutorial_open:
		_draw_toast()
	draw_set_transform(Vector2.ZERO)

func _draw_title():
	# Quiet background grid and sun give the title a warm, civic-poster feel.
	for x in range(0, 1281, 64):
		draw_line(Vector2(x, 0), Vector2(x, 800), Color(INK, 0.025), 1.0)
	for y in range(0, 801, 64):
		draw_line(Vector2(0, y), Vector2(1280, y), Color(INK, 0.025), 1.0)
	_logo(Vector2(66, 42), 1.0)
	_text("COMMON GROUND", Vector2(122, 70), 20, INK)
	_pill("A GAME ABOUT ALL OF US", Rect2(1005, 42, 210, 34), GREEN_LIGHT, GREEN, 12)
	_text("A small city.", Vector2(70, 238), 58, INK)
	_text("A shared future.", Vector2(70, 306), 58, GREEN)
	_wrapped("Ten weeks. Four neighborhoods. Limited time. Discover how much changes when we care for needs today and build capacity for tomorrow.", Rect2(74, 340, 460, 100), 20, INK_SOFT, 8)
	_button("start", Rect2(72, 478, 282, 60), "Start the first week", "primary")
	_button("how", Rect2(72, 552, 282, 48), "How to play", "secondary")
	_panel(Rect2(70, 646, 488, 92), PAPER, 14, LINE, 1)
	_text("THE SHARED GOAL", Vector2(92, 674), 12, GREEN)
	_text("65 wellbeing  ·  45 trust  ·  40 green", Vector2(92, 706), 19, INK)
	_text("And no neighborhood below 50.", Vector2(92, 730), 14, INK_SOFT)
	_draw_title_city()

func _draw_title_city():
	var area = Rect2(610, 132, 600, 570)
	_panel(area, Color("#e4ecdf"), 28)
	draw_circle(Vector2(1080, 228), 65 + sin(elapsed * 0.8) * 3.0, GOLD_LIGHT)
	draw_circle(Vector2(1080, 228), 40, GOLD)
	# Distant skyline.
	for i in range(9):
		var bx = 642.0 + i * 61.0
		var bh = 90.0 + float((i * 37) % 100)
		var color = Color("#b9d1c1") if i % 2 == 0 else Color("#cad9c8")
		_panel(Rect2(bx, 448 - bh, 48, bh), color, 5)
		for wy in range(0, 3):
			draw_rect(Rect2(bx + 11, 372 - wy * 22, 8, 10), Color("#f6edc9"))
			draw_rect(Rect2(bx + 29, 372 - wy * 22, 8, 10), Color("#f6edc9"))
	# River and paths.
	draw_colored_polygon(PackedVector2Array([Vector2(610, 555), Vector2(770, 484), Vector2(930, 510), Vector2(1210, 450), Vector2(1210, 536), Vector2(934, 588), Vector2(760, 559), Vector2(610, 635)]), BLUE_LIGHT)
	draw_arc(Vector2(885, 528), 215, 0.18, 2.82, 60, Color("#f9f5e7"), 19, true)
	# Neighborhood nodes, joined by visible relationships.
	var nodes = [Vector2(720, 318), Vector2(913, 290), Vector2(1080, 400), Vector2(792, 559)]
	for a in range(nodes.size()):
		for b in range(a + 1, nodes.size()):
			draw_line(nodes[a], nodes[b], Color(GREEN, 0.18), 2, true)
	for i in range(nodes.size()):
		var pulse = 2.0 + sin(elapsed * 1.5 + i) * 2.0
		draw_circle(nodes[i], 42 + pulse, Color(PAPER, 0.65))
		draw_circle(nodes[i], 34, PAPER)
		_draw_icon(["listen", "garden", "aid", "prepare"][i], nodes[i], [BLUE, GREEN, CORAL, GOLD][i], 1.15)
	# Tiny residents in the foreground.
	for i in range(8):
		var p = Vector2(688 + i * 58, 636 + sin(i * 2.1) * 13)
		var c = [CORAL, BLUE, GREEN, Color("#8b75a5")][i % 4]
		draw_circle(p - Vector2(0, 17), 7, c)
		draw_line(p - Vector2(0, 9), p + Vector2(0, 11), c, 6, true)
		draw_line(p + Vector2(0, 10), p + Vector2(-7, 22), c, 3, true)
		draw_line(p + Vector2(0, 10), p + Vector2(7, 22), c, 3, true)
	_pill("CARE  ·  CONNECT  ·  PREPARE", Rect2(754, 662, 314, 27), PAPER, INK_SOFT, 11)

func _draw_play():
	# Header.
	draw_rect(Rect2(0, 0, 1280, 70), INK)
	_logo(Vector2(26, 14), 1.0)
	_text("COMMON GROUND", Vector2(82, 45), 20, PAPER)
	_pill("WEEK " + str(week) + " / 10", Rect2(528, 18, 128, 34), Color(PAPER, 0.12), PAPER, 13)
	_text("Build a city where no one is left behind.", Vector2(682, 43), 15, Color("#d7e5dc"))
	_button("help", Rect2(1130, 16, 116, 38), "?  Help", "secondary")
	_draw_stats()
	_draw_map()
	_draw_actions()
	# Bottom goal ribbon.
	_panel(Rect2(32, 732, 1216, 44), Color("#e8ede4"), 10)
	_text("SHARED GOAL", Vector2(50, 759), 12, GREEN)
	_text("Wellbeing 65+", Vector2(180, 759), 14, INK)
	_text("Trust 45+", Vector2(320, 759), 14, INK)
	_text("Green 40+", Vector2(425, 759), 14, INK)
	_text("Every neighborhood 50+", Vector2(530, 759), 14, INK)
	_right("1–5 · arrows · Space · E", Vector2(1228, 759), 13, INK_SOFT)

func _draw_stats():
	var names = ["WELLBEING", "TRUST", "GREEN SPACE", "FAIRNESS"]
	var values = [_wellbeing(), _average("trust"), _average("green"), _fairness()]
	var colors = [GREEN, BLUE, Color("#729b55"), GOLD]
	var notes = ["goal 65+", "goal 45+", "goal 40+ · resilient at 60+", "100 = equal wellbeing"]
	for i in range(4):
		var r = Rect2(32 + i * 307, 88, 295, 84)
		_panel(r, PAPER, 13, LINE, 1)
		_text(names[i], r.position + Vector2(18, 23), 11, INK_SOFT)
		_text(str(int(round(values[i]))), r.position + Vector2(18, 57), 29, INK)
		_text(notes[i], r.position + Vector2(76, 52), 12, INK_SOFT)
		_bar(Rect2(r.position + Vector2(18, 68), Vector2(259, 6)), values[i], colors[i])

func _draw_map():
	_panel(Rect2(32, 190, 770, 526), PAPER, 16, LINE, 1)
	var event_color: Color = current_event["color"]
	_panel(Rect2(50, 208, 734, 78), event_color.lightened(0.72), 12)
	_draw_icon("prepare" if String(current_event["kind"]) in ["storm", "heat"] else "skills", Vector2(83, 246), event_color, 0.85)
	_text("FORECAST · " + _event_scope(), Vector2(112, 232), 11, event_color.darkened(0.2))
	_text(String(current_event["title"]), Vector2(112, 256), 20, INK)
	_text(String(current_event["desc"]), Vector2(278, 253), 13, INK_SOFT)
	_text("Arrives when you end this week", Vector2(278, 271), 11, event_color.darkened(0.15))
	district_rects = [Rect2(50, 304, 357, 187), Rect2(427, 304, 357, 187), Rect2(50, 509, 357, 187), Rect2(427, 509, 357, 187)]
	for i in range(4):
		_draw_district(i, district_rects[i])
	for p in particles:
		var c: Color = p["color"]
		c.a = clampf(p["life"], 0.0, 1.0)
		draw_circle(p["pos"], 4.0, c)

func _draw_district(index: int, r: Rect2):
	var d = districts[index]
	var selected = selected_district == index
	var hovered = r.has_point(mouse_design)
	var fill = Color("#f6f7f0") if not hovered else Color("#eef3e9")
	_panel(r, fill, 12, GREEN if selected else LINE, 3 if selected else 1)
	buttons.append({"id": "district_" + str(index), "rect": r, "enabled": true})
	_text(d["name"], r.position + Vector2(16, 27), 19, INK)
	var status_color = _status_color(d)
	_pill(_status(d), Rect2(r.position + Vector2(241, 11), Vector2(100, 24)), status_color.lightened(0.72), status_color.darkened(0.15), 10)
	_text("LOCAL WELLBEING", r.position + Vector2(16, 50), 10, INK_SOFT)
	_text(str(int(round(_local_wellbeing(d)))), r.position + Vector2(16, 79), 26, status_color)
	var labels = ["Need", "Trust", "Green"]
	var keys = ["need", "trust", "green"]
	var colors = [CORAL, BLUE, GREEN]
	for j in range(3):
		var y = 91 + j * 25
		_text(labels[j], r.position + Vector2(82, y + 9), 12, INK_SOFT)
		_bar(Rect2(r.position + Vector2(126, y + 2), Vector2(155, 8)), float(d[keys[j]]), colors[j])
		_right(str(int(round(float(d[keys[j]])))), r.position + Vector2(326, y + 11), 12, INK)
	_text("READY", r.position + Vector2(16, 169), 10, INK_SOFT)
	_bar(Rect2(r.position + Vector2(66, 161), Vector2(215, 7)), float(d["prep"]), GOLD)
	_right(str(int(round(float(d["prep"])))), r.position + Vector2(326, 171), 12, INK)

func _draw_actions():
	_panel(Rect2(818, 190, 430, 526), PAPER, 16, LINE, 1)
	_text("Invest together", Vector2(838, 222), 21, INK)
	_text("Pick a project, then a neighborhood.", Vector2(838, 244), 13, INK_SOFT)
	_pill(str(energy) + " TIME", Rect2(1031, 208, 88, 30), GREEN_LIGHT, GREEN, 12)
	_pill(str(supplies) + " SUPPLIES", Rect2(1126, 208, 104, 30), GOLD_LIGHT, Color("#916b23"), 11)
	for i in range(actions.size()):
		var action = actions[i]
		var r = Rect2(836, 262 + i * 70, 394, 62)
		var chosen = selected_action == i
		var hovered = r.has_point(mouse_design)
		var fill: Color = action["pale"] if chosen or hovered else Color("#f7f7f1")
		_panel(r, fill, 10, action["color"] if chosen else LINE, 2 if chosen else 1)
		buttons.append({"id": "action_" + str(i), "rect": r, "enabled": true})
		_draw_icon(String(action["id"]), r.position + Vector2(31, 31), action["color"], 0.72)
		_text(String(action["name"]), r.position + Vector2(59, 25), 17, INK)
		_text(String(action["desc"]), r.position + Vector2(59, 46), 12, INK_SOFT)
		var cost = "FREE" if int(action["cost"]) == 0 else str(action["cost"]) + " SUPPLY"
		_pill(cost, Rect2(r.position + Vector2(308, 9), Vector2(74, 22)), PAPER, INK_SOFT, 9)
		_pill(str(i + 1), Rect2(r.position + Vector2(357, 37), Vector2(23, 18)), Color(INK, 0.07), INK_SOFT, 10)
	var hint = "You can end early; unused time is not saved."
	if selected_action >= 0:
		hint = "Now choose a neighborhood on the map."
	_text(hint, Vector2(840, 626), 12, INK_SOFT)
	_button("end_week", Rect2(836, 646, 394, 48), "End week " + str(week) + "  →", "gold")

func _draw_report():
	buttons.clear()
	draw_rect(Rect2(Vector2.ZERO, DESIGN), Color(INK, 0.64))
	_panel(Rect2(302, 145, 676, 520), PAPER, 22)
	_pill("WEEK " + str(week) + " COMPLETE", Rect2(510, 171, 260, 30), GREEN_LIGHT, GREEN, 12)
	_center(report_title, Rect2(342, 218, 596, 46), 32, INK)
	_center("Small choices become shared resilience.", Rect2(342, 263, 596, 28), 16, INK_SOFT)
	var y = 320.0
	for line in report_lines:
		draw_circle(Vector2(354, y - 5), 4, GOLD)
		_wrapped(line, Rect2(372, y - 20, 552, 74), 16, INK, 6)
		y += 100.0
	var next_text = "See how the city grew" if week >= 10 else "Begin week " + str(week + 1) + "  ·  +2 supplies"
	_button("continue", Rect2(382, 587, 516, 52), next_text, "primary")

func _draw_end():
	_logo(Vector2(30, 24), 1.0)
	_text("COMMON GROUND", Vector2(86, 52), 19, INK)
	var won = _won()
	var title = "THRIVING TOGETHER" if won else "ROOTS FOR NEXT TIME"
	var subtitle = "You met the shared goal — and every neighborhood has a foundation." if won else "The city is still becoming. Every skill you practiced can grow the next attempt."
	_center(title, Rect2(180, 92, 920, 58), 40, GREEN if won else INK)
	_center(subtitle, Rect2(180, 151, 920, 30), 16, INK_SOFT)
	# Score medallion.
	draw_circle(Vector2(270, 354), 112, GOLD_LIGHT)
	draw_circle(Vector2(270, 354), 91, PAPER)
	_center(str(_score()), Rect2(180, 270, 180, 90), 64, INK)
	_center("COMMUNITY SCORE", Rect2(160, 369, 220, 28), 12, INK_SOFT)
	_center("out of 100", Rect2(190, 400, 160, 24), 13, GREEN)
	var names = ["Wellbeing", "Trust", "Green space", "Fairness"]
	var values = [_wellbeing(), _average("trust"), _average("green"), _fairness()]
	var colors = [GREEN, BLUE, Color("#729b55"), GOLD]
	for i in range(4):
		var y = 246 + i * 67
		_text(names[i], Vector2(466, y + 16), 16, INK)
		_bar(Rect2(590, y + 7, 400, 13), values[i], colors[i])
		_text(str(int(round(values[i]))), Vector2(1010, y + 20), 20, INK)
	_panel(Rect2(150, 513, 980, 118), PAPER, 16, LINE, 1)
	_center("THE PRACTICE TO CARRY WITH YOU", Rect2(190, 531, 900, 28), 12, GREEN)
	_center("Meet urgent needs. Listen before deciding. Prepare together. Measure success by those most at risk.", Rect2(185, 566, 910, 34), 18, INK)
	_button("restart", Rect2(330, 666, 296, 54), "Play another city", "primary")
	_button("title", Rect2(650, 666, 296, 54), "Back to title", "secondary")

func _draw_help(is_tutorial: bool):
	buttons.clear()
	draw_rect(Rect2(Vector2.ZERO, DESIGN), Color(INK, 0.70))
	_panel(Rect2(236, 100, 808, 600), PAPER, 22)
	_pill("WELCOME, NEIGHBOR" if is_tutorial else "FIELD GUIDE", Rect2(528, 126, 224, 30), GREEN_LIGHT, GREEN, 12)
	_center("How we grow common ground", Rect2(276, 174, 728, 48), 31, INK)
	var items = [
		["aid", "1. Meet needs today", "Choose a project, then a neighborhood. You have 3 time each week; supplies carry over. Mutual aid meets urgent needs, and listening is always free."],
		["prepare", "2. Read the forecast", "The event arrives when you end the week. Readiness softens storms and heat; green space cools heat; trust helps through illness and economic shocks."],
		["garden", "3. Build for tomorrow", "At 60+ green, a neighborhood prevents 2 need every week. At 65+ trust, neighbors prevent another 2. These investments keep giving."],
		["skills", "4. Leave no one behind", "After Week 10, aim for 65 wellbeing, 45 trust, 40 green space, and at least 50 local wellbeing everywhere. Fairness rewards closing gaps, not just averages."]
	]
	for i in range(items.size()):
		var y = 239 + i * 91
		var color = [CORAL, GOLD, GREEN, Color("#8b75a5")][i]
		_draw_icon(items[i][0], Vector2(292, y + 24), color, 0.9)
		_text(items[i][1], Vector2(328, y + 13), 18, INK)
		_wrapped(items[i][2], Rect2(328, y + 23, 654, 62), 14, INK_SOFT, 4)
	_button("close_help", Rect2(410, 624, 460, 48), "Let's begin" if is_tutorial else "Back to the city", "primary")
	_text("Keyboard: 1–5 choose · arrows select · Space applies · E ends week · H opens help", Vector2(309, 687), 12, INK_SOFT)

func _draw_toast():
	var width = min(760.0, max(390.0, font.get_string_size(toast, HORIZONTAL_ALIGNMENT_LEFT, -1, 15).x + 60.0))
	var r = Rect2((1280 - width) * 0.5, 680, width, 42)
	_panel(r, INK, 21)
	_center(toast, r, 15, PAPER)
