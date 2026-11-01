extends Node2D

const BG = Color("172e30")
const CREAM = Color("f5f0e5")
const INK = Color("243f3e")
const MUTED = Color("74827a")
const GOLD = Color("efbd69")
const CORAL = Color("db865f")
const MINT = Color("acd1b2")
const MAP_BG = Color("dce5d4")
const FOOD = Color("cf8050")
const CARE = Color("6e9f9e")
const SOCIAL = Color("9c8aae")
const ORIGIN = Vector2(447, 352)
const HALF = Vector2(78, 38)
const BOARD = Rect2(32, 164, 956, 614)
const SIDE = Rect2(1012, 164, 396, 614)
const NEED_NAMES = ["Food", "Care", "Connection"]
const NEED_COLORS = [FOOD, CARE, SOCIAL]
const TARGET = 70
const SERVICES = [
	{"name": "Community kitchen", "short": "Kitchen", "kind": "kitchen", "cost": 3, "range": 2, "power": [2, 0, 0], "color": FOOD, "desc": "A warm meal, without a barrier.", "effect": "+2 food"},
	{"name": "Neighborhood clinic", "short": "Clinic", "kind": "clinic", "cost": 4, "range": 2, "power": [0, 2, 0], "color": CARE, "desc": "Care within walking distance.", "effect": "+2 care"},
	{"name": "The common room", "short": "Commons", "kind": "commons", "cost": 3, "range": 2, "power": [0, 0, 2], "color": SOCIAL, "desc": "Somewhere everyone belongs.", "effect": "+2 connection"},
	{"name": "Pocket garden", "short": "Garden", "kind": "garden", "cost": 2, "range": 1, "power": [1, 0, 1], "color": Color("799767"), "desc": "Grow food. Grow friendships.", "effect": "+1 food, +1 connection"},
	{"name": "Library of things", "short": "Library", "kind": "library", "cost": 3, "range": 2, "power": [0, 1, 1], "color": Color("c0a16a"), "desc": "Share tools, skills, and support.", "effect": "+1 care, +1 connection"}
]
const WEEKS = [
	{"title": "A place to begin", "text": "Six households. Six weeks. Start by listening.", "need": -1},
	{"title": "A warmer week", "text": "The heat is here. Every home needs +1 care this week.", "need": 1},
	{"title": "The cost of a meal", "text": "Food prices rise. Every home needs +1 food this week.", "need": 0},
	{"title": "Someone to turn to", "text": "A lonely week. Every home needs +1 connection.", "need": 2},
	{"title": "Stronger together", "text": "A quieter week. Give the least-supported home a hand.", "need": -1},
	{"title": "A neighborhood for everyone", "text": "Your last week. Can every home reach 70% support?", "need": -1}
]

var font: Font
var homes: Array = []
var buildings: Dictionary = {}
var selected = Vector2i(-1, -1)
var hover_cell = Vector2i(-1, -1)
var hover_service = -1
var buttons: Array = []
var week = 1
var funds = 7
var actions = 3
var begun = false
var modal = ""
var sound_on = true
var time = 0.0
var notice = "Start with a home. A good neighborhood begins with listening."
var notice_time = 0.0
var history: Array = []
var particles: Array = []
var player: AudioStreamPlayer
var sound_bank: Dictionary = {}

func _ready() -> void:
	font = ThemeDB.fallback_font
	player = AudioStreamPlayer.new()
	player.volume_db = -16.0
	add_child(player)
	make_sounds()
	reset_game()

func reset_game() -> void:
	homes = [
		{"pos": Vector2i(0, 0), "name": "Maya & Leo", "tag": "A parent and a little explorer", "needs": [3, 1, 2], "priority": 0, "quote": "Between work and school, a reliable meal would give us a little breathing room.", "listened": false, "color": Color("cf8268")},
		{"pos": Vector2i(4, 0), "name": "The night shift", "tag": "People who keep the city going", "needs": [2, 3, 1], "priority": 1, "quote": "We look after this city at night. A clinic close to home would help us look after ourselves.", "listened": false, "color": Color("709b9a")},
		{"pos": Vector2i(0, 3), "name": "June", "tag": "A lifelong neighbor", "needs": [1, 3, 2], "priority": 1, "quote": "I still like doing things for myself. Having care within a short walk would make that easier.", "listened": false, "color": Color("b69c68")},
		{"pos": Vector2i(4, 3), "name": "New neighbors", "tag": "Finding their feet, together", "needs": [2, 1, 3], "priority": 2, "quote": "We have so much to share. We just need a place to meet the people around us.", "listened": false, "color": Color("a28eaf")},
		{"pos": Vector2i(2, 1), "name": "River House", "tag": "Three generations under one roof", "needs": [3, 2, 2], "priority": 0, "quote": "A shared kitchen would mean more than dinner. Grandma has a few recipes to teach, too.", "listened": false, "color": Color("c39070")},
		{"pos": Vector2i(2, 3), "name": "The students", "tag": "New beginnings, small budgets", "needs": [2, 2, 3], "priority": 2, "quote": "A place to share tools and get to know people would make this feel like home.", "listened": false, "color": Color("8b9e79")}
	]
	buildings.clear()
	week = 1
	funds = 7
	actions = 3
	selected = Vector2i(-1, -1)
	hover_cell = Vector2i(-1, -1)
	history.clear()
	particles.clear()
	modal = ""
	notice = "Start with a home. A good neighborhood begins with listening."
	notice_time = 8
	queue_redraw()

func _process(delta: float) -> void:
	time += delta
	notice_time = maxf(0, notice_time - delta)
	var mouse = get_global_mouse_position()
	hover_cell = cell_at(mouse) if modal == "" else Vector2i(-1, -1)
	hover_service = -1
	var over_button = false
	for b in buttons:
		if b.rect.has_point(mouse):
			over_button = true
			if str(b.id).begins_with("build_"):
				hover_service = int(str(b.id).trim_prefix("build_"))
	Input.set_default_cursor_shape(Input.CURSOR_POINTING_HAND if over_button or hover_cell.x >= 0 else Input.CURSOR_ARROW)
	for i in range(particles.size() - 1, -1, -1):
		particles[i].life -= delta
		particles[i].pos += particles[i].vel * delta
		particles[i].vel.y += 50 * delta
		if particles[i].life <= 0:
			particles.remove_at(i)
	queue_redraw()

func center(c: Vector2i) -> Vector2:
	return ORIGIN + Vector2((c.x - c.y) * HALF.x, (c.x + c.y) * HALF.y)

func cell_at(p: Vector2) -> Vector2i:
	# Roofs are clickable as well as the ground beneath them, front to back.
	for depth in range(7, -1, -1):
		for x in range(5):
			var y = depth - x
			if y < 0 or y > 3:
				continue
			var c = Vector2i(x, y)
			var q = p - center(c)
			if (home_index(c) >= 0 or buildings.has(c)) and absf(q.x) < 39 and q.y > -99 and q.y < 7:
				return c
	var d = p - ORIGIN
	var c = Vector2i(roundi((d.x / HALF.x + d.y / HALF.y) * 0.5), roundi((d.y / HALF.y - d.x / HALF.x) * 0.5))
	if c.x >= 0 and c.x < 5 and c.y >= 0 and c.y < 4:
		return c
	return Vector2i(-1, -1)

func home_index(c: Vector2i) -> int:
	for i in homes.size():
		if homes[i].pos == c:
			return i
	return -1

func distance(a: Vector2i, b: Vector2i) -> int:
	return absi(a.x - b.x) + absi(a.y - b.y)

func support(index: int, preview: int = -1) -> Array:
	var result = [0, 0, 0]
	var home = homes[index]
	if home.listened:
		result[home.priority] += 1
	for c in buildings:
		var b = buildings[c]
		var s = SERVICES[b.type]
		if distance(c, home.pos) <= s.range:
			for n in 3:
				if s.power[n] > 0:
					result[n] += s.power[n] + b.level - 1
	if preview >= 0 and selected.x >= 0 and not buildings.has(selected) and home_index(selected) < 0:
		var s = SERVICES[preview]
		if distance(selected, home.pos) <= s.range:
			for n in 3:
				result[n] += s.power[n]
	return result

func needs_for(index: int) -> Array:
	var needs = homes[index].needs.duplicate()
	var extra = WEEKS[week - 1].need
	if extra >= 0:
		needs[extra] += 1
	return needs

func score(index: int, preview: int = -1) -> int:
	var supplied = support(index, preview)
	var needed = needs_for(index)
	var total = 0.0
	for n in 3:
		total += minf(1.0, float(supplied[n]) / needed[n])
	return roundi(total / 3.0 * 100)

func average(preview: int = -1) -> int:
	var total = 0
	for i in homes.size():
		total += score(i, preview)
	return roundi(float(total) / homes.size())

func included() -> int:
	var total = 0
	for i in homes.size():
		if score(i) >= TARGET:
			total += 1
	return total

func save_undo() -> void:
	history.append({"homes": homes.duplicate(true), "buildings": buildings.duplicate(true), "funds": funds, "actions": actions, "notice": notice})

func toast(message: String) -> void:
	notice = message
	notice_time = 6

func build(type: int) -> void:
	if not begun or modal != "" or selected.x < 0 or home_index(selected) >= 0 or buildings.has(selected):
		return
	var service = SERVICES[type]
	if actions == 0:
		toast("You've given this week your all. Move to the next week.")
		play_sound("low")
		return
	if funds < service.cost:
		toast("Need more funds? Listen to a home, or advance the week.")
		play_sound("low")
		return
	save_undo()
	buildings[selected] = {"type": type, "level": 1}
	funds -= service.cost
	actions -= 1
	toast(service.short + " opened. Small places can make a big difference.")
	burst(center(selected) - Vector2(0, 40), service.color)
	play_sound("build")

func listen() -> void:
	var index = home_index(selected)
	if index < 0 or actions <= 0 or homes[index].listened or not begun or modal != "":
		return
	save_undo()
	homes[index].listened = true
	actions -= 1
	funds += 1
	toast("A local solution: +1 " + NEED_NAMES[homes[index].priority].to_lower() + " for " + homes[index].name + ". +1 fund from a neighbor.")
	burst(center(selected) - Vector2(0, 60), GOLD)
	play_sound("listen")

func upgrade() -> void:
	if not buildings.has(selected) or actions <= 0 or funds < 2 or buildings[selected].level >= 2 or modal != "":
		return
	save_undo()
	buildings[selected].level = 2
	actions -= 1
	funds -= 2
	toast("More support, in the same familiar place. Each benefit increased by 1.")
	burst(center(selected) - Vector2(0, 50), GOLD)
	play_sound("build")

func undo() -> void:
	if history.is_empty() or modal != "":
		return
	var last = history.pop_back()
	homes = last.homes
	buildings = last.buildings
	funds = last.funds
	actions = last.actions
	toast("Last action undone. There is room to try another approach.")
	play_sound("tap")

func next_week() -> void:
	if not begun or modal != "":
		return
	modal = "confirm" if actions > 0 else ""
	if actions == 0:
		advance_week()

func advance_week() -> void:
	modal = ""
	history.clear()
	if week == 6:
		modal = "result"
		if included() == 6:
			for i in 6:
				burst(Vector2(370 + i * 140, 340), [MINT, GOLD, CORAL][i % 3])
			play_sound("win")
		else:
			play_sound("listen")
		return
	week += 1
	funds += 4
	actions = 3
	toast("Week " + str(week) + ": " + WEEKS[week - 1].text + "  +4 funds.")
	play_sound("week")

func activate(id: String) -> void:
	if id.begins_with("build_"):
		build(int(id.trim_prefix("build_")))
	elif id.begins_with("home_"):
		selected = homes[int(id.trim_prefix("home_"))].pos
		play_sound("tap")
	else:
		match id:
			"begin":
				begun = true
				selected = homes[0].pos
				play_sound("week")
			"listen": listen()
			"upgrade": upgrade()
			"undo": undo()
			"next": next_week()
			"help": modal = "help"
			"close", "cancel": modal = ""
			"confirm": advance_week()
			"sound": sound_on = not sound_on
			"restart":
				begun = true
				reset_game()
				selected = homes[0].pos
	queue_redraw()

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var point = get_global_mouse_position()
		for i in range(buttons.size() - 1, -1, -1):
			if buttons[i].rect.has_point(point):
				activate(buttons[i].id)
				return
		if modal != "" or not begun:
			return
		var c = cell_at(point)
		if c.x >= 0:
			selected = c
			play_sound("tap")
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_M:
			sound_on = not sound_on
			return
		if event.keycode == KEY_ESCAPE:
			if modal in ["help", "confirm"]:
				modal = ""
			return
		if event.keycode in [KEY_H, KEY_QUESTION]:
			if modal == "": modal = "help"
			elif modal == "help": modal = ""
			return
		if modal != "":
			return
		if not begun:
			if event.keycode in [KEY_ENTER, KEY_SPACE]: activate("begin")
			return
		match event.keycode:
			KEY_1, KEY_2, KEY_3, KEY_4, KEY_5: build(event.keycode - KEY_1)
			KEY_L: listen()
			KEY_U: upgrade()
			KEY_Z: undo()
			KEY_SPACE: next_week()
			KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN:
				if selected.x < 0: selected = Vector2i(1, 1)
				elif event.keycode == KEY_LEFT: selected.x = maxi(0, selected.x - 1)
				elif event.keycode == KEY_RIGHT: selected.x = mini(4, selected.x + 1)
				elif event.keycode == KEY_UP: selected.y = maxi(0, selected.y - 1)
				elif event.keycode == KEY_DOWN: selected.y = mini(3, selected.y + 1)

func make_sounds() -> void:
	var melodies = {"tap": [440.0], "low": [196.0, 164.81], "listen": [329.63, 440.0, 523.25], "build": [261.63, 329.63, 392.0, 523.25], "week": [392.0, 523.25, 659.25], "win": [261.63, 329.63, 392.0, 523.25, 659.25, 783.99]}
	for key in melodies:
		var notes: Array = melodies[key]
		var length = 0.075 if key == "tap" else 0.14
		var count = int(22050 * (notes.size() * length + 0.15))
		var data = PackedByteArray()
		data.resize(count * 2)
		for i in count:
			var t = float(i) / 22050.0
			var sample = 0.0
			for n in notes.size():
				var age = t - n * length
				if age >= 0 and age < 0.3:
					var envelope = minf(age / 0.008, 1.0) * exp(-age * 18)
					sample += sin(age * TAU * notes[n]) * envelope * 0.28
			data.encode_s16(i * 2, int(clampf(sample, -1.0, 1.0) * 32767))
		var stream = AudioStreamWAV.new()
		stream.format = AudioStreamWAV.FORMAT_16_BITS
		stream.mix_rate = 22050
		stream.data = data
		sound_bank[key] = stream

func play_sound(key: String) -> void:
	if sound_on and player != null:
		player.stream = sound_bank[key]
		player.play()

func burst(pos: Vector2, color: Color) -> void:
	for i in 18:
		var angle = TAU * float(i) / 18
		particles.append({"pos": pos, "vel": Vector2(cos(angle) * (40 + i % 4 * 18), sin(angle) * 60 - 30), "life": 0.8 + (i % 4) * 0.1, "color": color})

# All the artwork below is native vector drawing: no imported art or fonts.
func box(rect: Rect2, color: Color, radius: float = 12.0, border: Color = Color.TRANSPARENT, width: float = 1.0) -> void:
	var style = StyleBoxFlat.new()
	style.bg_color = color
	style.set_corner_radius_all(int(radius))
	if border.a > 0:
		style.border_color = border
		style.set_border_width_all(int(width))
	draw_style_box(style, rect)

func txt(value: String, pos: Vector2, size: int = 18, color: Color = INK) -> void:
	draw_string(font, pos, value, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)

func centered(value: String, rect: Rect2, size: int, color: Color) -> void:
	var extent = font.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1, size)
	txt(value, Vector2(rect.position.x + (rect.size.x - extent.x) * 0.5, rect.position.y + (rect.size.y + font.get_ascent(size) - font.get_descent(size)) * 0.5), size, color)

func paragraph(value: String, pos: Vector2, width: float, size: int = 18, color: Color = INK, spacing: float = 1.45) -> float:
	var y = pos.y
	var line = ""
	for word in value.split(" "):
		var test = line + (" " if line != "" else "") + word
		if font.get_string_size(test, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x > width and line != "":
			txt(line, Vector2(pos.x, y), size, color)
			y += size * spacing
			line = word
		else:
			line = test
	if line != "":
		txt(line, Vector2(pos.x, y), size, color)
	return y + size * spacing

func button(id: String, rect: Rect2, label: String, color: Color = INK, text_color: Color = CREAM, enabled: bool = true, size: int = 17) -> void:
	var hovered = rect.has_point(get_global_mouse_position()) and modal == ""
	var fill = color.lightened(0.08) if hovered and enabled else color
	if not enabled:
		fill = Color("dce0d5")
		text_color = Color("859087")
	box(rect, fill, 9)
	centered(label, rect, size, text_color)
	if enabled:
		buttons.append({"id": id, "rect": rect})

func poly(points: Array, color: Color) -> void:
	draw_colored_polygon(PackedVector2Array(points), color)

func diamond(p: Vector2, width: float, height: float, color: Color) -> void:
	poly([p + Vector2(0, -height), p + Vector2(width, 0), p + Vector2(0, height), p + Vector2(-width, 0)], color)

func diamond_outline(p: Vector2, width: float, height: float, color: Color, thickness: float = 2.0) -> void:
	draw_polyline(PackedVector2Array([p + Vector2(0, -height), p + Vector2(width, 0), p + Vector2(0, height), p + Vector2(-width, 0), p + Vector2(0, -height)]), color, thickness, true)

func icon(kind: String, p: Vector2, color: Color, scale_factor: float = 1.0) -> void:
	var s = scale_factor
	match kind:
		"food", "kitchen":
			draw_arc(p + Vector2(0, -3) * s, 10 * s, 0, PI, 18, color, 2.5 * s, true)
			draw_line(p + Vector2(-11, -3) * s, p + Vector2(11, -3) * s, color, 2 * s, true)
			draw_line(p + Vector2(-5, 9) * s, p + Vector2(5, 9) * s, color, 2 * s, true)
			for x in [-4, 3]:
				draw_polyline(PackedVector2Array([p + Vector2(x, -8) * s, p + Vector2(x - 2, -12) * s, p + Vector2(x, -16) * s]), color, 1.5 * s, true)
		"care", "clinic":
			box(Rect2(p + Vector2(-3, -11) * s, Vector2(6, 22) * s), color, 1)
			box(Rect2(p + Vector2(-11, -3) * s, Vector2(22, 6) * s), color, 1)
		"social", "commons":
			draw_circle(p + Vector2(-6, -6) * s, 4 * s, color)
			draw_circle(p + Vector2(6, -6) * s, 4 * s, color)
			draw_arc(p + Vector2(-6, 8) * s, 6 * s, PI, TAU, 16, color, 3 * s, true)
			draw_arc(p + Vector2(6, 8) * s, 6 * s, PI, TAU, 16, color, 3 * s, true)
		"garden":
			draw_line(p + Vector2(0, 11) * s, p + Vector2(0, -6) * s, color, 2 * s, true)
			poly([p, p + Vector2(-10, -2) * s, p + Vector2(-10, -11) * s, p + Vector2(-2, -7) * s], color)
			poly([p + Vector2(0, -3) * s, p + Vector2(3, -12) * s, p + Vector2(11, -16) * s, p + Vector2(10, -6) * s], color)
		"library":
			poly([p + Vector2(-12, -9) * s, p + Vector2(-2, -7) * s, p + Vector2(-2, 11) * s, p + Vector2(-12, 8) * s], color)
			poly([p + Vector2(1, -7) * s, p + Vector2(12, -9) * s, p + Vector2(12, 8) * s, p + Vector2(1, 11) * s], color)
		"coin":
			draw_circle(p, 10 * s, color, false, 2 * s, true)
			draw_line(p + Vector2(0, -4) * s, p + Vector2(0, 4) * s, color, 2 * s, true)
		"heart":
			draw_circle(p + Vector2(-4, -3) * s, 5 * s, color)
			draw_circle(p + Vector2(4, -3) * s, 5 * s, color)
			poly([p + Vector2(-9, -1) * s, p + Vector2(9, -1) * s, p + Vector2(0, 10) * s], color)

func _draw() -> void:
	if font == null:
		return
	buttons.clear()
	draw_rect(Rect2(0, 0, 1440, 900), BG)
	draw_header()
	box(BOARD, MAP_BG, 18)
	draw_board()
	box(SIDE, CREAM, 18)
	draw_side()
	draw_footer()
	for p in particles:
		var col: Color = p.color
		col.a = minf(p.life * 2.0, 1.0)
		draw_circle(p.pos, 3.5, col, true, -1, true)
	if modal != "":
		draw_modal()

func draw_header() -> void:
	# A tiny neighborhood mark beside the wordmark.
	diamond(Vector2(57, 60), 23, 13, MINT)
	poly([Vector2(43, 59), Vector2(43, 42), Vector2(57, 34), Vector2(71, 42), Vector2(71, 59), Vector2(57, 67)], CREAM)
	poly([Vector2(39, 43), Vector2(57, 30), Vector2(75, 43), Vector2(68, 47), Vector2(57, 39), Vector2(46, 47)], CORAL)
	txt("COMMON GROUND", Vector2(94, 67), 36, CREAM)
	txt("A little care changes the whole neighborhood.", Vector2(95, 96), 16, MINT)
	box(Rect2(600, 30, 210, 78), Color("233d3e"), 12)
	txt("WEEK 0" + str(week) + " / 06", Vector2(619, 56), 14, MINT)
	for i in 6:
		box(Rect2(620 + i * 28, 75, 20, 5), GOLD if i < week else Color("45605a"), 2)
	box(Rect2(826, 30, 150, 78), Color("233d3e"), 12)
	icon("coin", Vector2(848, 53), GOLD, 0.7)
	txt("FUNDS", Vector2(867, 58), 13, MINT)
	txt(str(funds), Vector2(845, 94), 29, CREAM)
	txt("+4 / week", Vector2(878, 92), 12, MINT)
	box(Rect2(992, 30, 158, 78), Color("233d3e"), 12)
	txt("ACTIONS LEFT", Vector2(1010, 57), 13, MINT)
	for i in 3:
		draw_circle(Vector2(1020 + i * 29, 85), 8, GOLD if i < actions else Color("49615b"), true, -1, true)
	button("sound", Rect2(1170, 39, 120, 52), "Sound " + ("on" if sound_on else "off"), Color("2b4645"), CREAM, true, 15)
	button("help", Rect2(1304, 39, 104, 52), "How to play", Color("2b4645"), CREAM, true, 14)
	draw_line(Vector2(32, 129), Vector2(1408, 129), Color("39514c"), 1)
	txt("BUILD A PLACE WHERE NOBODY IS LEFT OUT", Vector2(34, 151), 12, MINT)
	txt("A SMALL GAME ABOUT THE BIG THINGS", Vector2(1110, 151), 12, MINT)

func draw_board() -> void:
	txt("THE NEIGHBORHOOD", Vector2(57, 198), 13, MUTED)
	txt(WEEKS[week - 1].title, Vector2(57, 232), 26, INK)
	box(Rect2(776, 184, 187, 47), Color("f3f0df"), 10)
	icon("heart", Vector2(797, 207), CORAL, 0.7)
	txt(str(included()) + " / 6 homes at 70%", Vector2(815, 213), 14, INK)
	# Understated contour lines, like a neighborhood plan on paper.
	for i in 5:
		draw_arc(Vector2(900, 445), 84 + i * 16, -1.0, 1.3, 40, Color("cddbc5"), 1.0, true)
	for i in 4:
		draw_arc(Vector2(100, 466), 60 + i * 18, 1.8, 4.3, 40, Color("cddbc5"), 1.0, true)
	# Floating island, with depth and a warm walking surface.
	var top = ORIGIN + Vector2(0, -51)
	var right = ORIGIN + Vector2(4 * 78 + 94, 4 * 38)
	var bottom = ORIGIN + Vector2(78, 7 * 38 + 52)
	var left = ORIGIN + Vector2(-3 * 78 - 94, 3 * 38)
	poly([left + Vector2(-2, 17), top + Vector2(0, 17), right + Vector2(5, 17), bottom + Vector2(0, 26)], Color("bdcbb4"))
	poly([left, bottom, bottom + Vector2(0, 17), left + Vector2(0, 17)], Color("9dad94"))
	poly([bottom, right, right + Vector2(0, 17), bottom + Vector2(0, 17)], Color("acb99b"))
	poly([top, right, bottom, left], Color("efe9d8"))
	# Pavement between the plots. Dashes quietly explain walkable distance.
	for x in range(4):
		var a = center(Vector2i(x, 0)) + Vector2(39, -19)
		var b = center(Vector2i(x, 3)) + Vector2(39, 19)
		dashed_line(a, b, Color("d4cfba"), 2, 8)
	for y in range(3):
		var a = center(Vector2i(0, y)) + Vector2(-39, 19)
		var b = center(Vector2i(4, y)) + Vector2(39, 19)
		dashed_line(a, b, Color("d4cfba"), 2, 8)
	var preview_type = hover_service
	var radius = -1
	if selected.x >= 0:
		if preview_type >= 0: radius = SERVICES[preview_type].range
		elif buildings.has(selected): radius = SERVICES[buildings[selected].type].range
	# Tile floors are drawn first; buildings are then drawn in depth order.
	for y in 4:
		for x in 5:
			var c = Vector2i(x, y)
			var p = center(c)
			var col = Color("c4d2b6") if (x + y) % 2 == 0 else Color("cbd7bc")
			if home_index(c) >= 0: col = Color("d7dcc2")
			if buildings.has(c): col = SERVICES[buildings[c].type].color.lerp(CREAM, 0.7)
			if radius >= 0 and distance(c, selected) <= radius:
				col = col.lerp(GOLD, 0.33)
			diamond(p + Vector2(0, 4), 68, 32, Color("b4c3a7"))
			diamond(p, 68, 32, col)
			if c == selected:
				diamond_outline(p, 70, 34, INK, 2.8)
			elif c == hover_cell and begun:
				diamond_outline(p, 69, 33, Color("78927c"), 2)
			if home_index(c) < 0 and not buildings.has(c):
				diamond_outline(p, 47, 23, Color("acbba0"), 1)
				draw_line(p + Vector2(-7, 0), p + Vector2(7, 0), Color("8b9f82"), 1.5, true)
				draw_line(p + Vector2(0, -5), p + Vector2(0, 5), Color("8b9f82"), 1.5, true)
				# A few tiny flowering weeds on the edge of each open lot.
				for j in 3:
					var g = p + Vector2(28 + j * 6, 7 - j * 3)
					draw_line(g, g + Vector2(0, -4), Color("8aa17d"), 1)
	if radius >= 0:
		for h in homes:
			if distance(h.pos, selected) <= radius:
				dashed_line(center(selected), center(h.pos), Color("b69959"), 2, 7)
	# Trees at the outside edges keep the plan feeling like a real little place.
	tree(Vector2(351, 306), 0.9, 0)
	tree(Vector2(246, 358), 0.75, 1)
	tree(Vector2(140, 431), 1.0, 2)
	tree(Vector2(824, 472), 1.05, 3)
	for depth in 8:
		for x in 5:
			var y = depth - x
			if y < 0 or y > 3: continue
			var c = Vector2i(x, y)
			var p = center(c)
			var hi = home_index(c)
			if hi >= 0:
				draw_house(p, homes[hi].color, hi)
				var value = score(hi)
				var color = INK if value < TARGET else Color("4f7959")
				box(Rect2(p.x - 24, p.y + 10, 48, 22), color, 7)
				centered(str(value) + "%", Rect2(p.x - 24, p.y + 10, 48, 22), 12, CREAM)
				if homes[hi].listened:
					draw_circle(p + Vector2(37, -46), 9, CREAM)
					draw_polyline(PackedVector2Array([p + Vector2(33, -46), p + Vector2(36, -43), p + Vector2(41, -49)]), Color("63916b"), 2, true)
				if preview_type >= 0 and score(hi, preview_type) > value:
					box(Rect2(p.x - 28, p.y - 108, 56, 24), GOLD, 7)
					centered("+" + str(score(hi, preview_type) - value) + "%", Rect2(p.x - 28, p.y - 108, 56, 24), 13, INK)
			elif buildings.has(c):
				draw_service(p, buildings[c].type, buildings[c].level)
	# Neighbors walk slowly along the paths, and pause to wave.
	for i in 7:
		var t = fmod(time * 0.025 + float(i) / 7, 1.0)
		var a = center(Vector2i(0, i % 3)) + Vector2(0, 38)
		var b = center(Vector2i(4, i % 3)) + Vector2(0, 38)
		var p = a.lerp(b, t if i % 2 == 0 else 1 - t)
		person(p, [CORAL, INK, SOCIAL, CARE][i % 4], i)
	tree(Vector2(298, 611), 0.95, 5)
	tree(Vector2(755, 601), 0.8, 7)
	# Legend and compass inhabit the unused corners of the board.
	txt("N", Vector2(913, 568), 12, MUTED)
	draw_line(Vector2(918, 602), Vector2(918, 578), MUTED, 1.3, true)
	poly([Vector2(918, 574), Vector2(914, 583), Vector2(922, 583)], MUTED)
	txt("ONE BLOCK", Vector2(838, 637), 10, MUTED)
	draw_line(Vector2(837, 647), Vector2(913, 647), MUTED, 1)
	for xx in [837, 913]: draw_line(Vector2(xx, 643), Vector2(xx, 651), MUTED, 1)
	# Six homes stay visible in the bottom strip, so nobody disappears into an average.
	draw_line(Vector2(56, 685), Vector2(964, 685), Color("b9c8b0"), 1)
	txt("EVERY HOME COUNTS", Vector2(57, 708), 11, MUTED)
	txt("Goal: each home at 70%+", Vector2(797, 708), 11, MUTED)
	for i in homes.size():
		var r = Rect2(56 + i * 153, 718, 143, 44)
		var active = selected == homes[i].pos
		if active: box(r, Color("f3f1e3"), 6)
		buttons.append({"id": "home_" + str(i), "rect": r})
		var name_short: String = ["Maya & Leo", "Night shift", "June", "New neighbors", "River House", "Students"][i]
		txt(name_short, r.position + Vector2(5, 16), 12, INK)
		var val = score(i)
		txt(str(val) + "%", r.position + Vector2(108, 16), 11, INK)
		box(Rect2(r.position + Vector2(5, 27), Vector2(132, 5)), Color("b9c8ad"), 2)
		if val > 0: box(Rect2(r.position + Vector2(5, 27), Vector2(132.0 * val / 100, 5)), Color("5b8263") if val >= TARGET else CORAL, 2)
		draw_line(r.position + Vector2(97.4, 24), r.position + Vector2(97.4, 34), INK, 1)
	if hover_cell.x >= 0 and modal == "" and hover_service < 0 and begun:
		var hi = home_index(hover_cell)
		if hi >= 0:
			var p = center(hover_cell) + Vector2(0, -117)
			var w = font.get_string_size(homes[hi].name, HORIZONTAL_ALIGNMENT_LEFT, -1, 14).x + 26
			box(Rect2(p.x - w / 2, p.y, w, 28), INK, 7)
			centered(homes[hi].name, Rect2(p.x - w / 2, p.y, w, 28), 14, CREAM)

func dashed_line(a: Vector2, b: Vector2, color: Color, width: float, dash: float) -> void:
	var length = a.distance_to(b)
	var direction = (b - a).normalized()
	var pos = 0.0
	while pos < length:
		draw_line(a + direction * pos, a + direction * minf(pos + dash, length), color, width, true)
		pos += dash * 2

func tree(p: Vector2, s: float, variant: int) -> void:
	draw_set_transform(p, 0, Vector2(s, s))
	ellipse_shape(Vector2(7, 4), Vector2(20, 8), Color(0.2, 0.35, 0.25, 0.12))
	draw_line(Vector2(0, 1), Vector2(0, -35), Color("6f7c59"), 5, true)
	var sway = sin(time * 0.8 + variant) * 1.3
	draw_circle(Vector2(sway - 8, -30), 16, Color("88a97e"), true, -1, true)
	draw_circle(Vector2(sway + 7, -34), 18, Color("749970"), true, -1, true)
	draw_circle(Vector2(sway, -46), 17, Color("98b785"), true, -1, true)
	draw_circle(Vector2(sway - 5, -50), 9, Color("abc494"), true, -1, true)
	draw_set_transform(Vector2.ZERO)

func ellipse_shape(p: Vector2, size: Vector2, color: Color) -> void:
	var vertices: Array = []
	for i in 28:
		var angle = TAU * float(i) / 28
		vertices.append(p + Vector2(cos(angle), sin(angle)) * size)
	poly(vertices, color)

func person(p: Vector2, shirt: Color, variant: int) -> void:
	ellipse_shape(p + Vector2(2, 1), Vector2(5, 2.5), Color(0.2, 0.3, 0.2, 0.15))
	var walk = sin(time * 6 + variant * 2) * 1.5
	draw_line(p + Vector2(-1.5, -4), p + Vector2(-2 - walk, 1), INK, 1.5, true)
	draw_line(p + Vector2(1.5, -4), p + Vector2(2 + walk, 1), INK, 1.5, true)
	box(Rect2(p + Vector2(-3, -11), Vector2(6, 8)), shirt, 2)
	draw_circle(p + Vector2(0, -14), 3, Color("bc9272") if variant % 2 == 0 else Color("7e604c"), true, -1, true)

func draw_house(p: Vector2, roof: Color, variant: int) -> void:
	var h = 49.0 + (variant % 3) * 6
	var w = 34.0
	var d = 17.0
	ellipse_shape(p + Vector2(8, 3), Vector2(43, 18), Color(0.2, 0.3, 0.2, 0.13))
	# Warm front facade and shaded side, with proper isometric roof planes.
	poly([p + Vector2(-w, -d), p + Vector2(0, 0), p + Vector2(0, -h), p + Vector2(-w, -h - d)], Color("e8ddbf"))
	poly([p, p + Vector2(w, -d), p + Vector2(w, -h - d), p + Vector2(0, -h)], Color("cec8ac"))
	poly([p + Vector2(-w - 5, -h - d), p + Vector2(-5, -h - d - 27), p + Vector2(w + 5, -h - d), p + Vector2(0, -h + 5)], roof)
	poly([p + Vector2(-5, -h - d - 27), p + Vector2(w + 5, -h - d), p + Vector2(35, -h - d - 8), p + Vector2(-9, -h - d - 34)], roof.lightened(0.15))
	draw_line(p + Vector2(-w - 5, -h - d), p + Vector2(0, -h + 5), roof.darkened(0.15), 2, true)
	# Windows, door, planter, chimney.
	for wx in [-26, -12]:
		var wy = float(wx) * 0.5 - 29
		poly([p + Vector2(wx, wy), p + Vector2(wx + 8, wy + 4), p + Vector2(wx + 8, wy + 15), p + Vector2(wx, wy + 11)], Color("6d8b86"))
		draw_line(p + Vector2(wx + 4, wy + 2), p + Vector2(wx + 4, wy + 13), Color("f5eacc"), 1, true)
	poly([p + Vector2(11, -5), p + Vector2(22, -11), p + Vector2(22, -32), p + Vector2(11, -26)], Color("647f73"))
	draw_circle(p + Vector2(14, -17), 1.1, GOLD)
	poly([p + Vector2(25, -39), p + Vector2(31, -42), p + Vector2(31, -53), p + Vector2(25, -50)], Color("7c9690"))
	poly([p + Vector2(-23, -h - 18), p + Vector2(-23, -h - 34), p + Vector2(-16, -h - 37), p + Vector2(-16, -h - 19)], roof.darkened(0.22))
	diamond(p + Vector2(-39, 1), 9, 4, Color("a88e68"))
	for j in 3:
		draw_circle(p + Vector2(-44 + j * 5, -3), 4, Color("7b9b6d"), true, -1, true)
		draw_circle(p + Vector2(-44 + j * 5, -6), 1.5, CORAL if variant % 2 == 0 else GOLD, true, -1, true)
	if variant % 2 == 0:
		draw_line(p + Vector2(36, -2), p + Vector2(48, 4), Color("a99c7e"), 2)
		for j in 3: draw_line(p + Vector2(36 + j * 6, -4 + j * 3), p + Vector2(36 + j * 6, 3 + j * 3), Color("a99c7e"), 1.5)

func draw_service(p: Vector2, type: int, level: int) -> void:
	var s = SERVICES[type]
	var col: Color = s.color
	if s.kind == "garden":
		for j in 3:
			var q = p + Vector2((j - 1) * 22, (j - 1) * 11)
			diamond(q, 19, 9, Color("a88e6a"))
			diamond(q + Vector2(0, -3), 17, 8, Color("7f7254"))
			for k in 3:
				var r = q + Vector2((k - 1) * 9, -(k - 1) * 4 - 5)
				draw_line(r, r + Vector2(0, -8), Color("527854"), 2)
				draw_circle(r + Vector2(-3, -8), 4, Color("81a25d"), true, -1, true)
				draw_circle(r + Vector2(3, -10), 4, Color("9cba70"), true, -1, true)
				if level == 2: draw_circle(r + Vector2(0, -12), 2, CORAL)
		tree(p + Vector2(-34, -10), 0.7, 4)
		draw_line(p + Vector2(27, -10), p + Vector2(27, -30), Color("8f805f"), 2)
		box(Rect2(p + Vector2(17, -35), Vector2(20, 13)), CREAM, 2)
		icon("garden", p + Vector2(27, -28), col, 0.35)
	else:
		var h = 46.0 if type != 4 else 57.0
		ellipse_shape(p + Vector2(10, 3), Vector2(47, 18), Color(0.2, 0.3, 0.2, 0.13))
		poly([p + Vector2(-39, -18), p, p + Vector2(0, -h), p + Vector2(-39, -h - 18)], Color("f2e8d0"))
		poly([p, p + Vector2(39, -18), p + Vector2(39, -h - 18), p + Vector2(0, -h)], Color("d7d1b8"))
		diamond(p + Vector2(0, -h - 19), 44, 21, col)
		diamond_outline(p + Vector2(0, -h - 20), 38, 18, col.lightened(0.2), 2)
		for wx in [-30, -15]:
			poly([p + Vector2(wx, wx * 0.46 - 12), p + Vector2(wx + 9, (wx + 9) * 0.46 - 12), p + Vector2(wx + 9, (wx + 9) * 0.46 - 30), p + Vector2(wx, wx * 0.46 - 30)], Color("769c94"))
		poly([p + Vector2(10, -5), p + Vector2(22, -11), p + Vector2(22, -35), p + Vector2(10, -29)], Color("668981"))
		poly([p + Vector2(26, -25), p + Vector2(34, -29), p + Vector2(34, -42), p + Vector2(26, -38)], Color("89aba0"))
		# Roof sign: immediately recognizable at a glance.
		box(Rect2(p + Vector2(-16, -h - 50), Vector2(32, 30)), CREAM, 7)
		icon(s.kind, p + Vector2(0, -h - 34), col, 0.8)
		if type == 0:
			for j in 5:
				var a = p + Vector2(-39 + j * 8, -33 + j * 3.7)
				poly([a, a + Vector2(8, 3.7), a + Vector2(3, 11), a + Vector2(-5, 7.3)], CORAL if j % 2 == 0 else CREAM)
		elif type == 2:
			for j in 5:
				var a = p + Vector2(-45 + j * 20, -10 + sin(j) * 4)
				poly([a, a + Vector2(8, 2), a + Vector2(3, 9)], [CORAL, GOLD, CARE][j % 3])
		elif type == 4:
			for j in 5:
				var a = p + Vector2(-33 + j * 5, -28 + j * 2.4)
				draw_line(a, a + Vector2(0, -10), [GOLD, CORAL, SOCIAL][j % 3], 3)
	var label_rect = Rect2(p + Vector2(-35, 10), Vector2(70, 21))
	box(label_rect, INK, 6)
	centered(s.short + (" +" if level > 1 else ""), label_rect, 11, CREAM)
	if level == 2:
		draw_circle(p + Vector2(38, -49), 8, GOLD)
		centered("+", Rect2(p + Vector2(30, -57), Vector2(16, 16)), 14, INK)

func draw_side() -> void:
	if not begun:
		draw_intro()
		return
	if selected.x < 0:
		txt("A little care goes a long way.", Vector2(1036, 210), 23, INK)
		paragraph("Choose a home to listen, or an empty lot to create something good.", Vector2(1036, 253), 340, 18, MUTED)
		draw_overview(353)
		return
	var hi = home_index(selected)
	if hi >= 0:
		draw_home_panel(hi)
	elif buildings.has(selected):
		draw_building_panel()
	else:
		draw_build_menu()

func draw_intro() -> void:
	txt("WELCOME TO", Vector2(1038, 201), 12, MUTED)
	txt("Common Ground", Vector2(1036, 242), 32, INK)
	paragraph("A better world starts on the block.", Vector2(1038, 278), 334, 20, INK)
	draw_line(Vector2(1038, 323), Vector2(1382, 323), Color("d7ddce"), 1)
	var steps = [
		["01", "Listen first", "Every home has a different story. Find out what would help."],
		["02", "Build close to people", "Create shared places. Benefits reach homes a short walk away."],
		["03", "Leave nobody out", "In six weeks, bring all six homes to at least 70% support."]
	]
	for i in 3:
		var y = 356 + i * 101
		draw_circle(Vector2(1053, y + 2), 17, [MINT, GOLD, Color("dccfe1")][i], true, -1, true)
		centered(steps[i][0], Rect2(1036, y - 15, 34, 34), 12, INK)
		txt(steps[i][1], Vector2(1087, y + 7), 20, INK)
		paragraph(steps[i][2], Vector2(1087, y + 34), 278, 15, MUTED, 1.4)
	button("begin", Rect2(1036, 680, 348, 52), "Let's make a little room   →", INK, CREAM, true, 18)
	centered("6 weeks  ·  10 minutes  ·  everyone counts", Rect2(1036, 741, 348, 20), 12, MUTED)

func draw_home_panel(index: int) -> void:
	var home = homes[index]
	txt("MEET YOUR NEIGHBORS", Vector2(1036, 201), 12, MUTED)
	txt(home.name, Vector2(1036, 237), 29, INK)
	txt(home.tag, Vector2(1036, 265), 14, MUTED)
	box(Rect2(1036, 285, 348, 119), Color("e8e7d9"), 10)
	txt("“", Vector2(1052, 323), 36, home.color)
	paragraph(home.quote, Vector2(1076, 313), 285, 16, INK, 1.5)
	txt("WHAT HELPS THIS HOME", Vector2(1036, 436), 12, MUTED)
	var supplied = support(index)
	var needed = needs_for(index)
	for n in 3:
		var y = 465 + n * 47
		icon(["food", "care", "social"][n], Vector2(1048, y + 2), NEED_COLORS[n], 0.7)
		txt(NEED_NAMES[n], Vector2(1068, y + 6), 16, INK)
		txt(str(supplied[n]) + " / " + str(needed[n]), Vector2(1338, y + 6), 14, INK)
		for j in needed[n]:
			box(Rect2(1171 + j * 32, y - 7, 25, 15), NEED_COLORS[n] if j < supplied[n] else Color("dce0d3"), 4)
	box(Rect2(1036, 603, 348, 47), INK, 9)
	txt("Overall support", Vector2(1052, 632), 16, CREAM)
	txt(str(score(index)) + "%", Vector2(1315, 634), 25, GOLD if score(index) < TARGET else MINT)
	if home.listened:
		button("listen", Rect2(1036, 672, 348, 48), "Heard & helped  ✓", INK, CREAM, false)
		centered("A local solution adds +1 " + NEED_NAMES[home.priority].to_lower() + ".", Rect2(1036, 731, 348, 21), 13, MUTED)
	else:
		button("listen", Rect2(1036, 672, 348, 48), "Listen & find a solution   [L]", INK, CREAM, actions > 0)
		centered("1 action  ·  +1 " + NEED_NAMES[home.priority].to_lower() + " here  ·  +1 fund", Rect2(1036, 731, 348, 21), 13, MUTED)

func draw_build_menu() -> void:
	txt("OPEN LOT  /  " + str(selected.x + 1) + " · " + str(selected.y + 1), Vector2(1036, 201), 12, MUTED)
	txt("Make room for good.", Vector2(1036, 239), 27, INK)
	paragraph("Hover to see who benefits. Each place takes one action to build.", Vector2(1036, 268), 343, 15, MUTED, 1.4)
	for i in SERVICES.size():
		var s = SERVICES[i]
		var r = Rect2(1036, 316 + i * 73, 348, 64)
		var over = r.has_point(get_global_mouse_position()) and modal == ""
		var affordable = funds >= s.cost and actions > 0
		box(r, Color("e9e7da") if not over else Color("e4dfc9"), 9, GOLD if over else Color.TRANSPARENT, 2)
		box(Rect2(r.position + Vector2(9, 10), Vector2(43, 43)), s.color.lerp(CREAM, 0.72), 9)
		icon(s.kind, r.position + Vector2(30, 33), s.color, 0.8)
		txt(s.name, r.position + Vector2(64, 24), 16, INK if affordable else MUTED)
		txt(s.effect + "  ·  " + str(s.range) + " blocks", r.position + Vector2(64, 46), 12, MUTED)
		icon("coin", r.position + Vector2(307, 24), INK if affordable else MUTED, 0.6)
		txt(str(s.cost), r.position + Vector2(319, 29), 16, INK if affordable else MUTED)
		txt("[" + str(i + 1) + "]", r.position + Vector2(310, 49), 11, MUTED)
		buttons.append({"id": "build_" + str(i), "rect": r})
	var gain = average(hover_service) - average() if hover_service >= 0 else 0
	if hover_service >= 0:
		box(Rect2(1036, 694, 348, 63), Color("e5e8d7"), 9)
		txt("THE REACH OF A SMALL THING", Vector2(1050, 716), 10, MUTED)
		txt("+" + str(gain) + "% neighborhood support", Vector2(1050, 741), 18, INK)
	else:
		paragraph("The gold preview shows walking distance. Benefits add up across nearby places.", Vector2(1038, 714), 340, 14, MUTED, 1.5)

func draw_building_panel() -> void:
	var b = buildings[selected]
	var s = SERVICES[b.type]
	txt("A SHARED PLACE  /  LEVEL " + str(b.level), Vector2(1036, 201), 12, MUTED)
	txt(s.name, Vector2(1036, 239), 25, INK)
	txt(s.desc, Vector2(1036, 267), 16, MUTED)
	box(Rect2(1036, 289, 348, 108), s.color.lerp(CREAM, 0.80), 10)
	icon(s.kind, Vector2(1075, 344), s.color, 1.5)
	var power_parts: Array[String] = []
	for n in 3:
		if s.power[n] > 0: power_parts.append("+" + str(s.power[n] + b.level - 1) + " " + NEED_NAMES[n].to_lower())
	paragraph(", ".join(power_parts), Vector2(1114, 328), 245, 18, INK, 1.3)
	txt("Within " + str(s.range) + " walking blocks", Vector2(1114, 374), 14, MUTED)
	txt("NEIGHBORS IN REACH", Vector2(1036, 430), 12, MUTED)
	var y = 459
	var count = 0
	for i in homes.size():
		if distance(homes[i].pos, selected) <= s.range:
			draw_circle(Vector2(1042, y - 5), 4, homes[i].color)
			txt(homes[i].name, Vector2(1056, y), 16, INK)
			txt(str(score(i)) + "%", Vector2(1337, y), 15, MUTED)
			buttons.append({"id": "home_" + str(i), "rect": Rect2(1036, y - 22, 348, 30)})
			y += 34
			count += 1
	if count == 0: paragraph("No homes in reach. Undo and try a place closer to people.", Vector2(1036, y), 340, 17, MUTED)
	if b.level == 1:
		button("upgrade", Rect2(1036, 672, 348, 48), "Grow this place   ·   2 funds   [U]", INK, CREAM, actions > 0 and funds >= 2, 16)
		centered("1 action  ·  +1 to each benefit  ·  same reach", Rect2(1036, 731, 348, 21), 12, MUTED)
	else:
		button("upgrade", Rect2(1036, 672, 348, 48), "Rooted & thriving  ✓", INK, CREAM, false)
		centered("This place is giving all it can.", Rect2(1036, 731, 348, 21), 14, MUTED)

func draw_overview(y_start: int) -> void:
	for i in homes.size():
		var y = y_start + i * 48
		button("home_" + str(i), Rect2(1036, y, 348, 40), homes[i].name + "    " + str(score(i)) + "%", Color("e5e6d8"), INK, true, 16)

func draw_footer() -> void:
	box(Rect2(32, 798, 956, 70), Color("233d3e"), 12)
	var event = WEEKS[week - 1]
	draw_circle(Vector2(61, 833), 12, GOLD)
	centered("i", Rect2(49, 821, 24, 24), 17, INK)
	var message: String = notice if notice_time > 0 else event.text
	paragraph(message, Vector2(84, 826 if font.get_string_size(message, HORIZONTAL_ALIGNMENT_LEFT, -1, 16).x > 875 else 839), 875, 16, CREAM, 1.4)
	button("undo", Rect2(1012, 798, 104, 70), "Undo [Z]", Color("2c4846"), CREAM, not history.is_empty(), 15)
	button("next", Rect2(1128, 798, 280, 70), ("See what we built" if week == 6 else "Next week") + "   →", GOLD, INK, begun, 19)
	txt("Click a home to listen. Click a lot to build. Every small choice reaches someone.", Vector2(34, 890), 12, MINT)
	txt("H  help     M  sound     SPACE  next week", Vector2(1157, 890), 11, MINT)

func draw_modal() -> void:
	buttons.clear()
	draw_rect(Rect2(0, 0, 1440, 900), Color(0.04, 0.12, 0.13, 0.73))
	if modal == "help":
		box(Rect2(352, 110, 736, 676), CREAM, 20)
		txt("A small guide to a better block.", Vector2(393, 166), 30, INK)
		txt("THE GOAL IS EVERYONE, NOT JUST THE AVERAGE.", Vector2(395, 199), 13, MUTED)
		var instructions = [
			["01   Listen before you build", "Select a home and listen: one action gives that home +1 to its priority need, and adds 1 fund. Each home can be heard once."],
			["02   Keep good things within reach", "Select an open lot, then hover over a service. Gold paths show the homes it reaches. Distance counts grid steps, without diagonals."],
			["03   Share the benefits", "Services help every home in reach, every week. Benefits stack. Food, care, and connection are equally important; extra food cannot replace missing care."],
			["04   Make space for everyone", "You have 3 actions per week. New weeks add 4 funds; unused money carries over, unused actions do not. Meet temporary needs, then get every home to 70% by week 6."]
		]
		var y = 244.0
		for step in instructions:
			txt(step[0], Vector2(395, y), 20, INK)
			y = paragraph(step[1], Vector2(395, y + 29), 646, 16, MUTED, 1.4) + 24
		box(Rect2(393, 662, 654, 46), Color("e4e6d7"), 8)
		centered("Arrows select  ·  1–5 build  ·  L listen  ·  U upgrade  ·  Z undo", Rect2(393, 662, 654, 46), 15, INK)
		button("close", Rect2(393, 725, 654, 40), "Back to the neighborhood   [Esc]", INK, CREAM)
	elif modal == "confirm":
		box(Rect2(446, 290, 548, 302), CREAM, 20)
		txt("A little time still left.", Vector2(483, 344), 29, INK)
		paragraph("You have " + str(actions) + " action" + ("s" if actions != 1 else "") + " left this week. Unused actions won't carry over. Your funds will.", Vector2(484, 389), 468, 18, MUTED)
		button("cancel", Rect2(483, 500, 225, 52), "Stay a little longer", Color("dfe4d4"), INK, true, 16)
		button("confirm", Rect2(723, 500, 233, 52), "Finish" if week == 6 else "Next week   →", INK, CREAM)
	elif modal == "result":
		draw_result()

func draw_result() -> void:
	var success = included() == 6
	box(Rect2(378, 94, 684, 713), CREAM, 20)
	txt("SIX WEEKS. MANY SMALL ACTS OF CARE.", Vector2(420, 137), 12, MUTED)
	txt("A place for everyone." if success else "Good roots. Room to grow.", Vector2(419, 186), 34, INK)
	paragraph("Every home has the support it needs to begin thriving. You made sure the quietest corners counted." if success else "You made a difference. A few neighbors still need more support. Try another plan, and start with those hardest to reach.", Vector2(421, 224), 598, 17, MUTED, 1.5)
	box(Rect2(420, 302, 600, 75), INK, 10)
	txt(str(included()) + " / 6", Vector2(443, 345), 29, MINT)
	txt("homes at 70%+", Vector2(541, 342), 16, CREAM)
	txt(str(average()) + "%", Vector2(808, 345), 29, GOLD)
	txt("average", Vector2(909, 342), 15, CREAM)
	for i in homes.size():
		var y = 407 + i * 36
		draw_circle(Vector2(428, y - 5), 5, homes[i].color)
		txt(homes[i].name, Vector2(445, y), 16, INK)
		var s = score(i)
		box(Rect2(651, y - 12, 250, 8), Color("dce1d2"), 4)
		if s > 0: box(Rect2(651, y - 12, 250.0 * s / 100, 8), Color("749971") if s >= TARGET else CORAL, 4)
		draw_line(Vector2(826, y - 16), Vector2(826, y), INK, 1)
		txt(str(s) + "%", Vector2(931, y), 17, INK)
	draw_line(Vector2(420, 630), Vector2(1020, 630), Color("d4dccb"), 1)
	paragraph("Take one small thing with you: ask a neighbor what would help, share something useful, or make a place where someone feels welcome.", Vector2(421, 659), 596, 17, INK, 1.5)
	button("restart", Rect2(420, 738, 600, 46), "Plant another beginning   →", INK, CREAM, true, 18)
