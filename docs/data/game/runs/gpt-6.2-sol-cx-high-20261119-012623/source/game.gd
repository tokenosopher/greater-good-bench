extends Node2D

const TownArt := preload("res://town_art.gd")
const MAP := Rect2(43, 239, 960, 560)
const TILE := Vector2(80, 70)
const SIDE := 1028
const RIGHT := 1397
const CAPACITY := 3
const DIRECTIONS := [Vector2i.RIGHT, Vector2i.DOWN, Vector2i.LEFT, Vector2i.UP]
const OUTSIDE := Vector2i(-1, -1)
const PAPER := Color("#f4ead4")
const PANEL := Color("#fbf3e0")
const INK := Color("#253b31")
const MUTED := Color("#646b54")
const LINE := Color("#c8b99a")
const FOREST := Color("#294c3e")
const RUST := Color("#a84832")
const SKY := Color("#287268")
const CREAM := Color("#fff2d6")
const GOLD := Color("#d99d50")
const ROW_Y := 386
const ROW_HEIGHT := 46
const UNDO := Rect2(1028, 798, 174, 48)
const RESET := Rect2(1213, 798, 184, 48)
const GUIDE := Rect2(1254, 857, 143, 30)
const SOUND := Rect2(1208, 857, 34, 30)
const NEXT := Rect2(311, 599, 424, 48)
const CLOSE_GUIDE := Rect2(538, 621, 364, 48)

const DAYS := [
	{
		"tab": "First round",
		"time": "12:00 PM",
		"limit": 49,
		"map": [
			"###=p##=pp##",
			"#S=W..A===B#",
			"#.#.##.#.#.#",
			"#==.C..===.#",
			"pp=#.##=.p##",
			"#..=..#=..D#",
			"#.#.##p#.=~~",
			"p=====...p~~",
		],
		"needs": [1, 1, 2, 1],
		"brief": ["Start at the blue fountain to fill", "your carrier with three bottles."],
	},
	{
		"tab": "Peak heat",
		"time": "2:00 PM",
		"limit": 38,
		"map": [
			"###=p##=pp##",
			"#S=W..A===B#",
			"#.#.##.#.#.#",
			"#==EC..===.#",
			"pp=#.##=.p##",
			"#..=..#=W.D#",
			"#.#.##p#.=~~",
			"p=====...p~~",
		],
		"needs": [1, 2, 1, 2, 1],
		"brief": ["Yesterday’s shade stays open.", "A second fountain opens in the east."],
	},
	{
		"tab": "Last light",
		"time": "5:00 PM",
		"limit": 58,
		"map": [
			"###=p##=pp##",
			"#S=W..A===B#",
			"#.#.##.#.#.#",
			"#==EC..===.#",
			"pp=#.##=.p##",
			"#F.=..#=w.D#",
			"#.#.##p#.=~~",
			"p=====...p~~",
		],
		"needs": [1, 2, 2, 1, 1, 1],
		"brief": ["The east fountain is closed. Group", "nearby visits around each refill."],
	},
]
const PEOPLE := [
	["Mira Patel", "#aa4c35"],
	["Ren & Jo", "#455f79"],
	["Luis Alvarez", "#855459"],
	["The Cho family", "#62633c"],
	["Amina Diallo", "#784e38"],
	["Eva & Max", "#376d5c"],
]
const GLYPHS := {
	"T": [31, 4, 4, 4, 4, 4, 4],
	"H": [17, 17, 17, 31, 17, 17, 17],
	"E": [31, 16, 16, 30, 16, 16, 31],
	"C": [15, 16, 16, 16, 16, 16, 15],
	"O": [14, 17, 17, 17, 17, 17, 14],
	"L": [16, 16, 16, 16, 16, 16, 31],
	"R": [30, 17, 17, 30, 20, 18, 17],
	"U": [17, 17, 17, 17, 17, 17, 14],
}

var town: Node2D
var foreground: Node2D
var font: Font
var grain: ImageTexture
var audio: AudioStreamPlayer
var sounds := {}
var muted := false
var day := 0
var board: Array = []
var needs: Array = []
var houses: Array[Vector2i] = []
var fountains: Array[Vector2i] = []
var delivered := {}
var shade_from_neighbors := {}
var history: Array[Dictionary] = []
var position_on_map := Vector2i.ZERO
var water := 0
var daylight := 0
var time_limit := 0
var elapsed := 0.0
var walking: Array[Vector2i] = []
var walk_progress := 0.0
var pointer := Vector2(-1, -1)
var hovered := OUTSIDE
var preview_route: Array[Vector2i] = []
var preview_cost := 0
var notice := ""
var notice_time := 0.0
var flash := {}
var guide_open := false
var result := ""
var finished_days: Array[int] = []


func _ready() -> void:
	font = ThemeDB.fallback_font
	grain = paper_grain()
	town = TownArt.new()
	town.position = MAP.position
	town.scale = Vector2(2, 2)
	town.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(town)
	foreground = Node2D.new()
	foreground.draw.connect(draw_foreground)
	add_child(foreground)
	audio = AudioStreamPlayer.new()
	add_child(audio)
	sounds["refill"] = chime([440.0, 587.33, 659.25], 0.30)
	sounds["serve"] = chime([392.0, 523.25, 659.25], 0.36)
	sounds["win"] = chime([392.0, 493.88, 587.33, 783.99], 0.62)
	sounds["end"] = chime([329.63, 261.63], 0.30)
	load_day(0)


func load_day(index: int) -> void:
	day = index
	var setup: Dictionary = DAYS[day]
	board = setup.map
	needs = setup.needs
	time_limit = setup.limit
	daylight = time_limit
	water = 0
	history.clear()
	delivered.clear()
	walking.clear()
	flash.clear()
	fountains.clear()
	houses.clear()
	houses.resize(needs.size())
	for y in TownArt.HEIGHT:
		for x in TownArt.WIDTH:
			var cell := Vector2i(x, y)
			var t := tile_at(cell)
			if t == "S":
				position_on_map = cell
			elif t == "W":
				fountains.append(cell)
			elif t >= "A" and t <= "F":
				houses[t.unicode_at(0) - 65] = cell
	result = ""
	notice = ""
	notice_time = 0
	walk_progress = 0
	town.modulate = [Color.WHITE, Color("#fff1dc"), Color("#f1e0d3")][day]
	update_town()
	refresh_preview(true)


func update_town() -> void:
	var shade := shade_from_neighbors.duplicate()
	shade.merge(delivered)
	town.update_map(board, shade)


func tile_at(cell: Vector2i) -> String:
	if cell.x < 0 or cell.y < 0 or cell.x >= TownArt.WIDTH or cell.y >= TownArt.HEIGHT:
		return "#"
	return board[cell.y][cell.x]


func walkable(cell: Vector2i) -> bool:
	return tile_at(cell) not in ["#", "p", "~"]


func cell_center(cell: Vector2i) -> Vector2:
	return MAP.position + (Vector2(cell) + Vector2(0.5, 0.5)) * TILE


func step_cost(cell: Vector2i) -> int:
	if tile_at(cell) in ["=", "W", "S"] or delivered.has(cell) or shade_from_neighbors.has(cell):
		return 1
	return 2


func plan_route(target: Vector2i) -> Array[Vector2i]:
	var path: Array[Vector2i] = []
	if not walkable(target) or target == position_on_map:
		return path
	var open: Array[Vector2i] = [position_on_map]
	var distances := {position_on_map: 0}
	var previous := {}
	while not open.is_empty():
		var best := 0
		for i in range(1, open.size()):
			if distances[open[i]] < distances[open[best]]:
				best = i
		var cell := open[best]
		open.remove_at(best)
		if cell == target:
			while cell != position_on_map:
				path.push_front(cell)
				cell = previous[cell]
			return path
		for direction: Vector2i in DIRECTIONS:
			var next := cell + direction
			if not walkable(next):
				continue
			var cost: int = distances[cell] + step_cost(next)
			if cost < distances.get(next, 10000):
				distances[next] = cost
				previous[next] = cell
				if not open.has(next):
					open.append(next)
	return path


func total_cost(path: Array[Vector2i]) -> int:
	var cost := 0
	for cell in path:
		cost += step_cost(cell)
	return cost


func point_target(point: Vector2) -> Vector2i:
	if MAP.has_point(point):
		return Vector2i(((point - MAP.position) / TILE).floor())
	var i := side_row_at(point)
	return houses[i] if i >= 0 else OUTSIDE


func side_row_at(point: Vector2) -> int:
	if point.x < SIDE or point.x > RIGHT or point.y < ROW_Y:
		return -1
	var i := int((point.y - ROW_Y) / ROW_HEIGHT)
	return i if i < houses.size() else -1


func refresh_preview(force := false) -> void:
	var cell := point_target(pointer)
	if not force and cell == hovered:
		return
	hovered = cell
	preview_route.clear()
	preview_cost = 0
	if result.is_empty() and walking.is_empty() and not guide_open:
		preview_route = plan_route(cell)
		preview_cost = total_cost(preview_route)
	queue_redraw()


func go(target: Vector2i, single_step := false) -> void:
	if guide_open or not result.is_empty() or not walking.is_empty() or not walkable(target):
		return
	if target == position_on_map:
		return
	var route := plan_route(target)
	if single_step:
		route = [target]
	if route.is_empty():
		return
	if total_cost(route) > daylight:
		show_notice("That route would run past the daylight you have left.")
		return
	history.append({"cell": position_on_map, "water": water, "light": daylight, "delivered": delivered.duplicate()})
	walking = route
	walk_progress = 0
	notice_time = 0
	refresh_preview(true)


func arrive() -> void:
	var cell: Vector2i = walking.pop_front()
	daylight -= step_cost(cell)
	position_on_map = cell
	var i := houses.find(cell)
	if tile_at(cell) == "W" and water < CAPACITY:
		water = CAPACITY
		flash[cell] = elapsed
		show_notice("Carrier filled. Pick a household to visit.")
		play_sound("refill")
	elif tile_at(cell) == "w" and walking.is_empty():
		show_notice("The east fountain is closed. Refill at the west fountain.")
	elif i >= 0 and not delivered.has(cell):
		if water >= needs[i]:
			water -= needs[i]
			delivered[cell] = true
			flash[cell] = elapsed
			update_town()
			if shade_from_neighbors.has(cell):
				show_notice("Checked in with %s." % PEOPLE[i][0])
			else:
				show_notice("%s opened a shaded stop." % PEOPLE[i][0])
			play_sound("serve")
		elif walking.is_empty():
			show_notice("%s needs %d %s. Refill at a fountain." % [
				PEOPLE[i][0], needs[i], "bottle" if needs[i] == 1 else "bottles"
			])
	if delivered.size() == needs.size():
		walking.clear()
		result = "complete"
		play_sound("win")
	elif walking.is_empty() and not can_move():
		result = "time"
		play_sound("end")
	if walking.is_empty():
		refresh_preview(true)
	queue_redraw()


func can_move() -> bool:
	for direction: Vector2i in DIRECTIONS:
		var cell := position_on_map + direction
		if walkable(cell) and step_cost(cell) <= daylight:
			return true
	return false


func undo_route() -> void:
	if history.is_empty() or result == "campaign":
		return
	var previous: Dictionary = history.pop_back()
	position_on_map = previous.cell
	water = previous.water
	daylight = previous.light
	delivered = previous.delivered
	walking.clear()
	walk_progress = 0
	result = ""
	flash.clear()
	update_town()
	show_notice("Route undone.")
	refresh_preview(true)


func advance() -> void:
	if result == "time":
		load_day(day)
	elif result == "complete":
		finished_days.append(daylight)
		shade_from_neighbors.merge(delivered)
		if day + 1 < DAYS.size():
			load_day(day + 1)
		else:
			result = "campaign"
			notice_time = 0
			refresh_preview(true)
	elif result == "campaign":
		finished_days.clear()
		shade_from_neighbors.clear()
		load_day(0)


func toggle_guide() -> void:
	guide_open = not guide_open
	refresh_preview(true)


func show_notice(message: String) -> void:
	notice = message
	notice_time = 3.0
	queue_redraw()


func _process(delta: float) -> void:
	elapsed += delta
	if notice_time > 0:
		notice_time -= delta
		if notice_time <= 0:
			queue_redraw()
	if not walking.is_empty() and not guide_open:
		walk_progress += delta * 12.0
		while walk_progress >= 1.0 and not walking.is_empty():
			walk_progress -= 1.0
			arrive()
	foreground.queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		pointer = get_global_mouse_position()
		refresh_preview()
		queue_redraw()
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		pointer = get_global_mouse_position()
		click(pointer)
	elif event is InputEventKey and event.pressed:
		var key: Key = event.physical_keycode
		if key == KEY_H or key == KEY_F1:
			if not event.echo:
				toggle_guide()
			return
		if guide_open:
			if key in [KEY_ESCAPE, KEY_ENTER, KEY_SPACE] and not event.echo:
				toggle_guide()
			return
		match key:
			KEY_ENTER, KEY_SPACE:
				if not event.echo:
					advance()
			KEY_Z:
				if not event.echo:
					undo_route()
			KEY_R:
				if not event.echo:
					restart()
			KEY_UP, KEY_W: go(position_on_map + Vector2i.UP, true)
			KEY_DOWN, KEY_S: go(position_on_map + Vector2i.DOWN, true)
			KEY_LEFT, KEY_A: go(position_on_map + Vector2i.LEFT, true)
			KEY_RIGHT, KEY_D: go(position_on_map + Vector2i.RIGHT, true)


func click(point: Vector2) -> void:
	if guide_open:
		if CLOSE_GUIDE.has_point(point) or not Rect2(451, 176, 538, 522).has_point(point):
			toggle_guide()
		return
	if GUIDE.has_point(point):
		toggle_guide()
	elif SOUND.has_point(point):
		muted = not muted
		queue_redraw()
	elif UNDO.has_point(point):
		undo_route()
	elif RESET.has_point(point):
		restart()
	elif not result.is_empty():
		if NEXT.has_point(point) and result != "campaign":
			advance()
	else:
		go(point_target(point))


func restart() -> void:
	if result == "campaign":
		advance()
	else:
		load_day(day)


func paper_grain() -> ImageTexture:
	var rng := RandomNumberGenerator.new()
	rng.seed = 92415
	var paper := Image.create_empty(720, 450, false, Image.FORMAT_RGBA8)
	for i in 28500:
		var x := rng.randi_range(0, 719)
		var y := rng.randi_range(0, 449)
		var color := Color("#69523c0f") if i % 3 == 0 else Color("#fff9eb35")
		paper.set_pixel(x, y, color)
	return ImageTexture.create_from_image(paper)


func chime(notes: Array, duration: float) -> AudioStreamWAV:
	const RATE := 22050
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = RATE
	var samples := PackedByteArray()
	samples.resize(int(duration * RATE) * 2)
	for i in range(samples.size() / 2):
		var t := float(i) / RATE
		var sample := 0.0
		for n in notes.size():
			var at := t - n * duration / (notes.size() + 2)
			if at >= 0:
				var phase: float = TAU * notes[n] * at
				var envelope: float = minf(at * 175.0, 1.0) * exp(-at * 21.0)
				sample += (sin(phase) + sin(phase * 2.0) * 0.14) * envelope
		samples.encode_s16(i * 2, int(sample * 2900.0 * minf(1.0, (duration - t) * 47.0)))
	stream.data = samples
	return stream


func play_sound(which: String) -> void:
	if not muted:
		audio.stream = sounds[which]
		audio.play()


func fill(r: Rect2, color: Color) -> void:
	draw_rect(r, color)


func outline(r: Rect2, color: Color, width := 1.0) -> void:
	draw_rect(r, color, false, width)


func text_at(value: String, x: float, baseline: float, size: int, color := INK) -> void:
	draw_string(font, Vector2(x, baseline), value, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)


func strong(value: String, x: float, baseline: float, size: int, color := INK) -> void:
	draw_string_outline(font, Vector2(x, baseline), value, HORIZONTAL_ALIGNMENT_LEFT, -1, size, 2, color)
	text_at(value, x, baseline, size, color)


func centered(value: String, x: float, baseline: float, size: int, color := INK, bold := false) -> void:
	var left := x - font.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x * 0.5
	if bold:
		strong(value, left, baseline, size, color)
	else:
		text_at(value, left, baseline, size, color)


func caps(value: String, x: float, baseline: float, size: int, color := INK, tracking := 2.0) -> void:
	for character in value:
		text_at(character, x, baseline, size, color)
		x += font.get_string_size(character, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x + tracking


func pixel_title(p: Vector2, phrase: String, unit: int, color: Color) -> void:
	var x := p.x
	for character in phrase:
		if character == " ":
			x += unit * 3
			continue
		var glyph: Array = GLYPHS[character]
		for y in 7:
			for col in 5:
				if glyph[y] & (1 << (4 - col)):
					fill(Rect2(x + col * unit, p.y + y * unit, unit, unit), color)
		x += unit * 6


func sun(c: CanvasItem, p: Vector2, radius: float, color: Color) -> void:
	c.draw_circle(p, radius * 0.47, color, true, -1, true)
	for i in 8:
		var direction := Vector2.from_angle(i * TAU / 8.0)
		c.draw_line(p + direction * radius * 0.69, p + direction * radius, color, 2, true)


func drop(c: CanvasItem, p: Vector2, s: float, color: Color) -> void:
	var silhouette := PackedVector2Array([
		p + Vector2(0, -1) * s, p + Vector2(0.55, -0.30) * s,
		p + Vector2(0.72, 0.13) * s, p + Vector2(0.52, 0.56) * s,
		p + Vector2(0.23, 0.73) * s, p + Vector2(-0.23, 0.73) * s,
		p + Vector2(-0.52, 0.56) * s, p + Vector2(-0.72, 0.13) * s,
		p + Vector2(-0.55, -0.30) * s,
	])
	c.draw_colored_polygon(silhouette, color)


func check(c: CanvasItem, p: Vector2, color: Color, size := 7.0) -> void:
	c.draw_polyline(PackedVector2Array([p + Vector2(-0.58, 0) * size, p + Vector2(-0.13, 0.43) * size,
		p + Vector2(0.68, -0.47) * size]), color, 2, true)


func button(r: Rect2, title: String, color: Color, ink: Color, enabled := true) -> void:
	fill(r, color.lightened(0.07) if enabled and r.has_point(pointer) else color)
	outline(r, LINE if color == PANEL or not enabled else color)
	centered(title, r.get_center().x, r.get_center().y + 6, 16, ink, enabled)


func _draw() -> void:
	if font == null:
		return
	fill(Rect2(0, 0, 1440, 900), PAPER)
	draw_texture_rect(grain, Rect2(0, 0, 1440, 900), false)
	draw_header()
	draw_map_frame()
	draw_sidebar()
	draw_footer()


func draw_header() -> void:
	fill(Rect2(44, 31, 22, 22), FOREST)
	fill(Rect2(53, 36, 4, 12), CREAM)
	fill(Rect2(49, 40, 12, 4), CREAM)
	caps("NEIGHBORHOOD FIELD GAME", 78, 47, 13, FOREST, 2.7)
	pixel_title(Vector2(46, 76), "THE COOL ROUTE", 8, Color("#ddceb0"))
	pixel_title(Vector2(43, 73), "THE COOL ROUTE", 8, INK)
	text_at("A neighborhood runs cooler when no one is left out.", 43, 167, 21, MUTED)

	sun(self, Vector2(1040, 53), 12, RUST)
	caps("HEAT WAVE", 1063, 58, 14, RUST, 2.5)
	draw_line(Vector2(1185, 53), Vector2(1397, 53), LINE, 1)
	for i in DAYS.size():
		var r := Rect2(SIDE + i * 125, 76, 119, 78)
		var is_current := i == day
		var is_done := i < finished_days.size()
		fill(r, FOREST if is_current else PANEL)
		outline(r, FOREST if is_current else LINE)
		var ink := CREAM if is_current else MUTED
		caps("DAY %02d" % (i + 1), r.position.x + 12, 101, 12, ink, 1.6)
		if is_done:
			check(self, r.position + Vector2(104, 20), ink, 6)
		text_at(DAYS[i].tab, r.position.x + 12, 132, 15, ink)
	draw_line(Vector2(43, 187), Vector2(1397, 187), INK, 1.0)


func draw_map_frame() -> void:
	fill(Rect2(43, 203, 960, 36), INK)
	for i in 3:
		fill(Rect2(56 + i * 4, 223 - i * 3, 2, 5 + i * 3), Color("#b5c19a"))
	caps("MAPLE WARD", 78, 226, 14, CREAM, 2.8)
	var phase := "DAY %02d  /  %s" % [day + 1, DAYS[day].time]
	var phase_x := 986 - font.get_string_size(phase, HORIZONTAL_ALIGNMENT_LEFT, -1, 14).x
	text_at(phase, phase_x, 226, 14, CREAM)
	fill(Rect2(43, 799, 960, 47), PANEL)
	outline(Rect2(43, 799, 960, 47), LINE)
	fill(Rect2(58, 814, 16, 16), TownArt.SHADE)
	fill(Rect2(61, 818, 10, 2), Color("#b0b18a"))
	text_at("Shade · 1 daylight", 83, 827, 15, INK)
	fill(Rect2(230, 814, 16, 16), TownArt.ROAD)
	fill(Rect2(233, 818, 10, 2), Color("#e0b688"))
	text_at("Sun · 2 daylight", 255, 827, 15, INK)
	draw_line(Vector2(398, 809), Vector2(398, 836), LINE, 1)
	drop(self, Vector2(421, 823), 9, SKY)
	text_at("Fountain · refill", 438, 827, 15, INK)
	var label := "Click a tile to route"
	var color := MUTED
	if result == "campaign":
		label = "All rounds complete"
		color = FOREST
	elif not walking.is_empty():
		label = "On the way…"
	elif not preview_route.is_empty():
		label = "Route uses %d daylight" % preview_cost
		if preview_cost > daylight:
			color = RUST
			label = "Needs %d more daylight" % (preview_cost - daylight)
	elif not result.is_empty():
		label = "Round complete" if result == "complete" else "Round ended"
	text_at(label, 983 - font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, 15).x, 827, 15, color)


func draw_sidebar() -> void:
	if result == "campaign":
		draw_campaign_summary()
		return
	draw_stats()
	strong("Check-ins", SIDE, 337, 29)
	var count := "%d / %d" % [delivered.size(), needs.size()]
	centered(count, 1363, 334, 17, FOREST, true)
	outline(Rect2(1330, 311, 67, 32), LINE)
	text_at("Bring water to every doorstep.", SIDE, 365, 16, MUTED)
	for i in needs.size():
		draw_row(i)

	draw_line(Vector2(SIDE, 681), Vector2(RIGHT, 681), LINE, 1)
	var tutorial: Array = DAYS[day].brief
	caps("FIELD NOTE", SIDE, 705, 12, SKY, 2.1)
	if result == "complete":
		tutorial = ["Every household has a shaded", "stop for the people coming after you."]
	elif result == "time":
		tutorial = ["Try visiting nearby stops together", "or use the shaded streets to save time."]
	elif day == 0 and water > 0:
		tutorial = ["Pick a household in the list or on the", "map. Check how much water it needs."]
		if not delivered.is_empty():
			tutorial = ["Each delivery opens a shaded stop.", "Coming back through it costs less."]
	text_at(tutorial[0], SIDE, 731, 17, INK)
	text_at(tutorial[1], SIDE, 754, 17, INK)

	button(UNDO, "Undo route  [Z]", PANEL if not history.is_empty() else PAPER,
		INK if not history.is_empty() else MUTED, not history.is_empty())
	button(RESET, "Restart day  [R]", PANEL, INK)


func draw_campaign_summary() -> void:
	fill(Rect2(SIDE, 203, RIGHT - SIDE, 470), PANEL)
	outline(Rect2(SIDE, 203, RIGHT - SIDE, 470), LINE)
	fill(Rect2(1048, 225, 42, 42), FOREST)
	check(self, Vector2(1069, 246), CREAM, 19)
	caps("ALL ROUNDS COMPLETE", 1104, 251, 13, SKY, 1.75)
	strong("A cooler", 1048, 323, 38)
	strong("neighborhood", 1048, 368, 38)
	text_at("Every household had someone", 1048, 403, 17, MUTED)
	text_at("to count on.", 1048, 427, 17, MUTED)
	for i in finished_days.size():
		var y := 466 + i * 52
		draw_line(Vector2(1048, y), Vector2(1377, y), LINE, 1.0)
		text_at("%s · %d check-ins" % [DAYS[i].tab, DAYS[i].needs.size()], 1048, y + 31, 17, INK)
		text_at("%d daylight left" % finished_days[i], 1259, y + 31, 16, SKY)
	caps("FIELD NOTE", SIDE, 705, 12, SKY, 2.1)
	text_at("Ask someone what they need on a hot", SIDE, 731, 17, INK)
	text_at("day. Agree on a time to check back.", SIDE, 754, 17, INK)
	button(RESET, "Play again  [R]", FOREST, CREAM)


func draw_stats() -> void:
	var water_card := Rect2(SIDE, 203, 174, 87)
	var time_card := Rect2(1213, 203, 184, 87)
	fill(water_card, Color("#e2e8d3"))
	outline(water_card, Color("#aebda0"))
	fill(time_card, Color("#f0ddba"))
	outline(time_card, Color("#d3b67f"))
	caps("WATER", SIDE + 14, 225, 12, FOREST, 1.8)
	caps("DAYLIGHT", 1227, 225, 12, RUST, 1.8)
	strong(str(water), SIDE + 14, 262, 31, FOREST)
	text_at("/ 3", SIDE + 39, 261, 16, MUTED)
	for i in CAPACITY:
		var p := Vector2(SIDE + 93 + i * 29, 250)
		drop(self, p, 12, SKY if i < water else Color("#b3c1aa"))
		if i < water:
			fill(Rect2(p + Vector2(-3, -1), Vector2(2, 4)), Color("#cae1c5"))
	var time_ink := RUST if daylight < 9 else INK
	strong(str(daylight), 1227, 262, 31, time_ink)
	var daylight_width := font.get_string_size(str(daylight), HORIZONTAL_ALIGNMENT_LEFT, -1, 31).x
	text_at("/ %d" % time_limit, 1239 + daylight_width, 261, 16, MUTED)
	sun(self, Vector2(1371, 250), 13, RUST)
	fill(Rect2(1228, 276, 154, 3), Color("#d3b88f"))
	var ratio := float(daylight) / time_limit
	fill(Rect2(1228, 276, floorf(154 * ratio), 3), RUST if daylight < 9 else Color("#b77b3e"))


func draw_row(i: int) -> void:
	var cell := houses[i]
	var done := delivered.has(cell)
	var y := ROW_Y + i * ROW_HEIGHT
	var active := hovered == cell
	var row := Rect2(SIDE, y, RIGHT - SIDE, ROW_HEIGHT - 5)
	fill(row, Color("#e2e8d3") if done else (Color("#fff8e8") if active else PANEL))
	outline(row, SKY if active else LINE)
	var p := Vector2(SIDE + 24, y + 20)
	var badge := Rect2(p - Vector2(13, 13), Vector2(26, 26))
	fill(badge, FOREST if done else Color(PEOPLE[i][1]))
	var letter := String.chr(65 + i)
	if done:
		check(self, p, CREAM, 9)
	else:
		centered(letter, p.x, y + 26, 15, CREAM, true)
	text_at(PEOPLE[i][0], SIDE + 49, y + 26, 17, INK)
	if done:
		text_at("Checked in", 1303, y + 25, 13, FOREST)
	else:
		for n in needs[i]:
			drop(self, Vector2(1373 - n * 18, y + 21), 8, SKY)
		text_at("needs", 1277, y + 25, 13, MUTED)


func draw_footer() -> void:
	var status := "Arrow keys / WASD to walk • Click or tap to route"
	if result == "campaign":
		status = "Maple Ward · All households reached"
	elif notice_time > 0:
		status = notice
	text_at(status, 43, 878, 15, MUTED)
	button(GUIDE, "Field guide  [H]", PANEL, INK)
	fill(SOUND, PANEL.lightened(0.1) if SOUND.has_point(pointer) else PANEL)
	outline(SOUND, LINE)
	var p := SOUND.get_center()
	draw_colored_polygon(PackedVector2Array([
		p + Vector2(-9, -3), p + Vector2(-5, -3), p + Vector2(0, -7),
		p + Vector2(0, 7), p + Vector2(-5, 3), p + Vector2(-9, 3),
	]), FOREST)
	if muted:
		draw_line(p + Vector2(3, -3), p + Vector2(9, 3), RUST, 2, true)
		draw_line(p + Vector2(3, 3), p + Vector2(9, -3), RUST, 2, true)
	else:
		draw_arc(p, 6, -0.9, 0.9, 6, FOREST, 1.5, true)
		draw_arc(p, 10, -0.8, 0.8, 6, FOREST, 1.5, true)


func front_text(value: String, x: float, baseline: float, size: int, color := INK, alignment := 0.0) -> void:
	var width := font.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	foreground.draw_string(font, Vector2(x - width * alignment, baseline), value,
		HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)


func front_box(r: Rect2, color: Color) -> void:
	foreground.draw_rect(r, color)


func draw_foreground() -> void:
	draw_route_on_map()
	for fountain in fountains:
		draw_fountain_badge(fountain)
	for i in houses.size():
		draw_house_badge(i)
	draw_courier()
	for cell in flash:
		draw_ripple(cell, elapsed - flash[cell])
	foreground.draw_rect(MAP, Color("#554a39"), false, 1.0)
	if not result.is_empty() and result != "campaign":
		draw_result()
	if guide_open:
		draw_guide()


func draw_route_on_map() -> void:
	if not walking.is_empty():
		var previous := cell_center(position_on_map)
		for cell in walking:
			var p := cell_center(cell)
			draw_route_segment(previous, p, Color("#f8ecd3af"))
			previous = p
		draw_target(walking.back(), CREAM)
	elif not preview_route.is_empty():
		var color := CREAM if preview_cost <= daylight else Color("#ffd0ad")
		var previous := cell_center(position_on_map)
		for cell in preview_route:
			var p := cell_center(cell)
			draw_route_segment(previous, p, color)
			previous = p
		draw_target(hovered, color)


func draw_route_segment(a: Vector2, b: Vector2, color: Color) -> void:
	var direction := a.direction_to(b)
	var distance := a.distance_to(b)
	for offset in range(4, int(distance), 10):
		var begin := a + direction * offset
		var end := a + direction * minf(offset + 5, distance)
		foreground.draw_line(begin + Vector2(0, 1), end + Vector2(0, 1), Color("#4b4a3d80"), 4)
		foreground.draw_line(begin, end, color, 2)


func draw_target(cell: Vector2i, color: Color) -> void:
	var r := Rect2(cell_center(cell) - TILE * 0.5 + Vector2(3, 3), TILE - Vector2(6, 6))
	for y in [r.position.y, r.end.y]:
		for x in [r.position.x, r.end.x]:
			var p := Vector2(x, y)
			var dx := 11.0 if x == r.position.x else -11.0
			var dy := 11.0 if y == r.position.y else -11.0
			foreground.draw_polyline(PackedVector2Array([p + Vector2(dx, 0), p, p + Vector2(0, dy)]), color, 2)


func draw_house_badge(i: int) -> void:
	var cell := houses[i]
	var p := cell_center(cell) + Vector2(19, -14)
	var done := delivered.has(cell)
	var active := hovered == cell and result.is_empty() and not guide_open
	var badge_color := Color(PEOPLE[i][1]) if not done else FOREST
	var r := Rect2(p - Vector2(14, 13), Vector2(28, 26))
	front_box(Rect2(r.position + Vector2(2, 3), r.size), Color("#342e2669"))
	front_box(r, CREAM)
	front_box(r.grow(-2), badge_color.lightened(0.14) if active else badge_color)
	front_box(Rect2(p + Vector2(-2, 13), Vector2(4, 4)), CREAM)
	if done:
		check(foreground, p, CREAM, 9)
	else:
		front_text(String.chr(65 + i), p.x, p.y + 5, 16, CREAM, 0.5)


func draw_fountain_badge(cell: Vector2i) -> void:
	var p := cell_center(cell) + Vector2(22, -14)
	var r := Rect2(p - Vector2(12, 12), Vector2(24, 24))
	front_box(Rect2(r.position + Vector2(2, 3), r.size), Color("#342e2650"))
	front_box(r, CREAM)
	front_box(r.grow(-2), SKY)
	drop(foreground, p + Vector2(0, 1), 9, CREAM)
	var gleam := 0.25 + 0.45 * maxf(sin(elapsed * 3.5), 0.0)
	front_box(Rect2(p + Vector2(-29, -11), Vector2(2, 3)), Color(1, 0.96, 0.78, gleam))
	if water == 0 and result.is_empty():
		var center := cell_center(cell) + Vector2(0, 24)
		front_box(Rect2(center - Vector2(25, 8), Vector2(50, 16)), FOREST)
		front_text("REFILL", center.x, center.y + 4, 10, CREAM, 0.5)


func draw_courier() -> void:
	var p := cell_center(position_on_map)
	var step := 0
	if not walking.is_empty():
		p = p.lerp(cell_center(walking.front()), walk_progress)
		step = int(walk_progress * 4.0) % 2
	p = p.round()
	var shadow := Color("#36362e80")
	var detail := Color("#302d2b")
	var jacket := Color("#eef2ca")
	front_box(Rect2(p + Vector2(-13, 8), Vector2(26, 6)), shadow)
	front_box(Rect2(p + Vector2(-9, 6), Vector2(18, 10)), shadow)
	# The courier sprite uses a two-pixel grid and a bright cap over the muted town.
	front_box(Rect2(p + Vector2(-8, 6), Vector2(6, 7 - step * 2)), detail)
	front_box(Rect2(p + Vector2(2, 6), Vector2(6, 5 + step * 2)), detail)
	front_box(Rect2(p + Vector2(-10, -4), Vector2(20, 12)), detail)
	front_box(Rect2(p + Vector2(-8, -4), Vector2(16, 10)), jacket)
	front_box(Rect2(p + Vector2(-7, -12), Vector2(14, 10)), detail)
	front_box(Rect2(p + Vector2(-5, -11), Vector2(10, 8)), Color("#d89b68"))
	front_box(Rect2(p + Vector2(-3, -7), Vector2(2, 2)), detail)
	front_box(Rect2(p + Vector2(2, -7), Vector2(2, 2)), detail)
	front_box(Rect2(p + Vector2(-7, -15), Vector2(12, 6)), Color("#dd773e"))
	front_box(Rect2(p + Vector2(-5, -16), Vector2(8, 2)), Color("#ffd080"))
	front_box(Rect2(p + Vector2(-9, -11), Vector2(17, 2)), Color("#ac5235"))
	front_box(Rect2(p + Vector2(-7, -2), Vector2(3, 8)), Color("#d79548"))
	front_box(Rect2(p + Vector2(7, 1), Vector2(9, 9)), detail)
	front_box(Rect2(p + Vector2(9, 1), Vector2(6, 7)), Color("#589993"))
	front_box(Rect2(p + Vector2(9, 2), Vector2(5, 2)), Color("#a5d1b9"))
	if history.is_empty():
		var bob := roundf(sin(elapsed * 3.0) * 1.5)
		var marker := Rect2(p + Vector2(-18, 20 + bob), Vector2(36, 17))
		front_box(marker, INK)
		front_text("YOU", p.x, marker.position.y + 12, 10, CREAM, 0.5)


func draw_ripple(cell: Vector2i, t: float) -> void:
	if t > 0.6:
		return
	var p := cell_center(cell)
	var r := 10.0 + t * 45.0
	var alpha := 1.0 - t / 0.6
	foreground.draw_arc(p, r, 0, TAU, 20, Color(0.94, 1.0, 0.79, alpha), 2, true)
	for i in 4:
		var v := Vector2.from_angle(i * TAU / 4.0 + 0.75)
		front_box(Rect2((p + v * (r + 5)).round(), Vector2(3, 3)), Color(1.0, 1.0, 0.8, alpha))


func front_panel(r: Rect2) -> void:
	front_box(Rect2(r.position + Vector2(5, 7), r.size), Color("#292c236b"))
	front_box(r, PANEL)
	foreground.draw_rect(r, INK, false, 2)
	foreground.draw_rect(r.grow(-7), LINE, false, 1)


func front_button(r: Rect2, caption: String) -> void:
	front_box(r, FOREST.lightened(0.09) if r.has_point(pointer) else FOREST)
	front_text(caption, r.get_center().x, r.get_center().y + 6, 17, CREAM, 0.5)


func draw_result() -> void:
	front_box(MAP, Color("#24342e91"))
	front_panel(Rect2(234, 344, 578, 327))
	var message := ""
	var caption := ""
	var title := ""
	var action := ""
	match result:
		"complete":
			title = "Everyone checked in"
			caption = "%d of %d households reached" % [delivered.size(), needs.size()]
			message = "%d daylight left. Every doorstep has shade now." % daylight
			action = "Next day   →" if day + 1 < DAYS.size() else "See the neighborhood   →"
		"time":
			title = "Daylight ran out"
			caption = "%d of %d households reached" % [delivered.size(), needs.size()]
			message = "Undo a route or try the day again."
			action = "Try again   [Enter]"
	var center := Vector2(523, 403)
	if result == "time":
		sun(foreground, center, 22, RUST)
	else:
		front_box(Rect2(center - Vector2(20, 20), Vector2(40, 40)), FOREST)
		check(foreground, center, CREAM, 21)
	front_text(title, 523, 474, 34, INK, 0.5)
	front_text(caption, 523, 513, 20, SKY, 0.5)
	front_text(message, 523, 550, 17, MUTED, 0.5)
	front_button(NEXT, action)


func draw_guide() -> void:
	front_box(Rect2(0, 0, 1440, 900), Color("#26352f9a"))
	front_panel(Rect2(451, 176, 538, 522))
	front_text("FIELD GUIDE", 720, 230, 14, SKY, 0.5)
	front_text("Make the rounds", 720, 280, 34, INK, 0.5)
	var directions := [
		["Fill your carrier", "Visit a fountain for three bottles of water."],
		["Check in at each home", "Click a home or move with arrows / WASD."],
		["Follow the shade", "Shade costs one daylight per tile. Sun costs two."],
		["Leave a shaded stop", "A household’s shade stays open on later days."],
	]
	for i in directions.size():
		var y := 317 + i * 69
		var p := Vector2(501, y + 13)
		front_box(Rect2(p - Vector2(11, 11), Vector2(22, 22)), Color("#e0e7cd"))
		if i == 0:
			drop(foreground, p, 8, SKY)
		elif i == 2:
			sun(foreground, p, 7, RUST)
		else:
			check(foreground, p, SKY)
		front_text(directions[i][0], 525, y + 16, 17, INK)
		front_text(directions[i][1], 525, y + 39, 16, MUTED)
	front_button(CLOSE_GUIDE, "Back to the map   [Esc]")
