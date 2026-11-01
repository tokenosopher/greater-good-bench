extends Node2D
## Ripple: A Kindness Game
## A tiny cooperative village simulator. Kindness is contagious: helping one
## villager lifts everyone around them, and a happy community gives energy
## back to you. Greed (hoarding) gives you a quick boost but wounds everyone,
## including yourself in the long run. Build a "Beloved Community" to win.

const WIDTH := 1024.0
const HEIGHT := 640.0

const COLS := 9
const ROWS := 5
const CELL := 60.0
const GRID_W := COLS * CELL
const GRID_H := ROWS * CELL
const GRID_LEFT := (WIDTH - GRID_W) / 2.0
const GRID_TOP := 132.0

const SAD_COLOR := Color(0.30, 0.42, 0.84)
const MID_COLOR := Color(0.36, 0.74, 0.55)
const HAPPY_COLOR := Color(0.99, 0.81, 0.22)
const BG_COLOR := Color(0.065, 0.075, 0.125)
const CELL_A := Color(0.09, 0.10, 0.16)
const CELL_B := Color(0.105, 0.12, 0.185)
const TEXT_COLOR := Color(0.90, 0.92, 0.95)
const DIM_COLOR := Color(0.62, 0.66, 0.74)
const CARE_COLOR := Color(0.42, 0.85, 0.95)
const GOLD_COLOR := Color(0.99, 0.85, 0.30)

const KIND_COST := 0.18
const KIND_SELF := 0.04
const KIND_TARGET := 0.55
const KIND_NEIGHBOR := 0.20
const KIND_RADIUS := 1
const GREED_GAIN := 0.55
const GREED_HARM := 0.33
const GREED_DISTRUST := 3.0
const DECAY_SPEED := 0.040
const JOY_TARGET := 0.80
const JOY_SECONDS := 5.0

enum State { INTRO, PLAY, WON }

var state: int = State.INTRO
var font: Font

var moods: Array = []      # flattened COLS*ROWS
var troubles: Array = []   # bool flags
var ripple_rings: Array = []
var floaties: Array = []

var caret := Vector2i(4, 2)
var care := 0.72
var distrust := 0.0
var trouble_timer := 2.4
var joy_time := 0.0
var avg_mood := 0.5
var kindness_count := 0
var greed_count := 0
var current_stage := 0
var lesson_text := ""
var lesson_timer := 0.0
var hint_text := ""
var hint_timer := 0.0

const STAGE_NAMES := ["Struggling", "Getting By", "Thriving", "Beloved Community"]
const STAGE_LESSONS := {
	2: "Kindness ripples \u2014 helping one person lifts everyone around them.",
	3: "Trust and cooperation outlast greed. This is what sustains a community.",
}


func _ready() -> void:
	font = ThemeDB.fallback_font
	_init_board()


func _init_board() -> void:
	moods.clear()
	troubles.clear()
	for i in COLS * ROWS:
		moods.append(0.58)
		troubles.append(false)
	care = 0.72
	distrust = 0.0
	trouble_timer = 2.4
	joy_time = 0.0
	avg_mood = 0.58
	kindness_count = 0
	greed_count = 0
	current_stage = _stage_for(avg_mood)
	lesson_text = ""
	lesson_timer = 0.0
	hint_text = ""
	hint_timer = 0.0
	ripple_rings.clear()
	floaties.clear()
	caret = Vector2i(COLS / 2, ROWS / 2)


func _process(delta: float) -> void:
	match state:
		State.PLAY:
			_update_play(delta)
		State.INTRO:
			_passive_update(delta)
		State.WON:
			_update_fx(delta)
	queue_redraw()


func _passive_update(delta: float) -> void:
	# Gentle idle animation behind the intro screen.
	_update_fx(delta)
	_update_lessons_hints(delta)


func _update_play(delta: float) -> void:
	# Mood drifts back toward neutral: wellbeing must be tended to, it is not automatic.
	for i in moods.size():
		var m: float = moods[i]
		moods[i] = move_toward(m, 0.5, DECAY_SPEED * delta)

	# Care recharges faster when the community is happy (mutual aid returns to you)
	# and slower when distrust is high.
	avg_mood = _average_mood()
	var recharge := (0.03 + avg_mood * 0.08) / (1.0 + distrust)
	care = minf(1.0, care + recharge * delta)
	distrust = maxf(0.0, distrust - 0.6 * delta)

	# New troubles appear: someone in town has a bad day.
	trouble_timer -= delta
	if trouble_timer <= 0.0:
		trouble_timer = randf_range(2.3, 3.6)
		var i := randi() % (COLS * ROWS)
		moods[i] = maxf(0.0, moods[i] - 0.55)
		troubles[i] = true

	# Stage progression and its gentle lessons.
	var stage := _stage_for(avg_mood)
	if stage > current_stage:
		current_stage = stage
		if STAGE_LESSONS.has(stage):
			lesson_text = STAGE_LESSONS[stage]
			lesson_timer = 6.0

	# Joy accumulates when the whole community is well, and evaporates under neglect.
	if avg_mood >= JOY_TARGET:
		joy_time += delta
	else:
		joy_time = maxf(0.0, joy_time - delta * 2.0)
	if joy_time >= JOY_SECONDS:
		state = State.WON

	_update_fx(delta)
	_update_lessons_hints(delta)


func _update_fx(delta: float) -> void:
	var to_remove := []
	for ring in ripple_rings:
		ring.life += delta
		if ring.life >= ring.duration:
			to_remove.append(ring)
	for ring in to_remove:
		ripple_rings.erase(ring)

	to_remove.clear()
	for f in floaties:
		f.life += delta
		f.pos += f.vel * delta
		if f.life >= f.duration:
			to_remove.append(f)
	for f in to_remove:
		floaties.erase(f)


func _update_lessons_hints(delta: float) -> void:
	if lesson_timer > 0.0:
		lesson_timer -= delta
		if lesson_timer <= 0.0:
			lesson_text = ""
	if hint_timer > 0.0:
		hint_timer -= delta
		if hint_timer <= 0.0:
			hint_text = ""


func _average_mood() -> float:
	var sum := 0.0
	for m in moods:
		sum += m
	return sum / float(moods.size())


func _stage_for(avg: float) -> int:
	if avg < 0.32:
		return 0
	if avg < 0.56:
		return 1
	if avg < 0.78:
		return 2
	return 3


func _input(event: InputEvent) -> void:
	if not (event is InputEventKey):
		return
	var key := event as InputEventKey
	if not key.pressed:
		return
	var kc := key.keycode
	var echo := key.echo

	match state:
		State.INTRO:
			if kc == KEY_SPACE or kc == KEY_ENTER:
				_init_board()
				state = State.PLAY
			return
		State.WON:
			if kc == KEY_R:
				_init_board()
				state = State.PLAY
			return
		State.PLAY:
			pass

	# Movement (echo allowed so holding a key glides nicely).
	if kc == KEY_LEFT or kc == KEY_A:
		caret.x = clampi(caret.x - 1, 0, COLS - 1)
	elif kc == KEY_RIGHT or kc == KEY_D:
		caret.x = clampi(caret.x + 1, 0, COLS - 1)
	elif kc == KEY_UP or kc == KEY_W:
		caret.y = clampi(caret.y - 1, 0, ROWS - 1)
	elif kc == KEY_DOWN or kc == KEY_S:
		caret.y = clampi(caret.y + 1, 0, ROWS - 1)

	if echo:
		return

	if kc == KEY_SPACE:
		_do_kindness()
	elif kc == KEY_X or kc == KEY_G:
		_do_greed()
	elif kc == KEY_R:
		_init_board()
	elif kc == KEY_ESCAPE:
		state = State.INTRO


func _do_kindness() -> void:
	var i := _idx(caret)
	if care < KIND_COST:
		_show_hint("Care is low \u2014 wait a moment. A happy community recharges you.")
		return
	care -= KIND_COST
	care = minf(1.0, care + KIND_SELF)
	moods[i] = clampf(moods[i] + KIND_TARGET, 0.0, 1.0)
	troubles[i] = false
	var c := _cell_center(caret)
	_spawn_ripple(c, Color(0.5, 1.0, 0.9), 58.0, 0.45)
	_spawn_floaty(c + Vector2(0, -26), "+", Color(0.55, 1.0, 0.85))
	for n in _neighbors(caret, KIND_RADIUS):
		var ni := _idx(n)
		moods[ni] = clampf(moods[ni] + KIND_NEIGHBOR, 0.0, 1.0)
		troubles[ni] = false
		_spawn_ripple(_cell_center(n), Color(0.5, 1.0, 0.9), 34.0, 0.38)
	kindness_count += 1
	if greed_count > 0:
		greed_count = 0  # a fresh kindness washes away the memory of greed


func _do_greed() -> void:
	care = minf(1.0, care + GREED_GAIN)
	distrust += GREED_DISTRUST
	for i in moods.size():
		moods[i] = maxf(0.0, moods[i] - GREED_HARM)
		var c := _cell_center(_cell_at(i))
		_spawn_floaty(c, "\u2212", Color(0.9, 0.35, 0.35))
	greed_count += 1
	_spawn_ripple(_cell_center(caret), Color(0.9, 0.3, 0.3), 70.0, 0.5)
	_show_hint("Hoard and everyone pays \u2014 including you. Trust is a shared resource.")


func _show_hint(text: String) -> void:
	hint_text = text
	hint_timer = 4.0


# ---- Helpers -------------------------------------------------------------

func _idx(c: Vector2i) -> int:
	return c.y * COLS + c.x


func _cell_at(i: int) -> Vector2i:
	return Vector2i(i % COLS, i / COLS)


func _cell_center(c: Vector2i) -> Vector2:
	return Vector2(GRID_LEFT + c.x * CELL + CELL / 2.0, GRID_TOP + c.y * CELL + CELL / 2.0)


func _neighbors(c: Vector2i, radius: int) -> Array:
	var out := []
	for dy in range(-radius, radius + 1):
		for dx in range(-radius, radius + 1):
			if dx == 0 and dy == 0:
				continue
			if absi(dx) + absi(dy) > radius:
				continue
			var n := c + Vector2i(dx, dy)
			if n.x >= 0 and n.x < COLS and n.y >= 0 and n.y < ROWS:
				out.append(n)
	return out


func _mood_color(m: float) -> Color:
	if m < 0.5:
		return SAD_COLOR.lerp(MID_COLOR, m / 0.5)
	return MID_COLOR.lerp(HAPPY_COLOR, (m - 0.5) / 0.5)


func _spawn_ripple(center: Vector2, color: Color, max_radius: float, duration: float) -> void:
	ripple_rings.append({
		"center": center,
		"color": color,
		"max_radius": max_radius,
		"duration": duration,
		"life": 0.0,
	})


func _spawn_floaty(pos: Vector2, text: String, color: Color) -> void:
	floaties.append({
		"pos": pos,
		"vel": Vector2(0, -34),
		"text": text,
		"color": color,
		"duration": 0.8,
		"life": 0.0,
	})


# ---- Drawing -------------------------------------------------------------

func _draw() -> void:
	draw_rect(Rect2(0, 0, WIDTH, HEIGHT), BG_COLOR)
	_draw_grid()
	_draw_hud()

	match state:
		State.INTRO:
			_draw_intro()
		State.WON:
			_draw_won()


func _draw_grid() -> void:
	draw_rect(Rect2(GRID_LEFT - 8, GRID_TOP - 8, GRID_W + 16, GRID_H + 16),
			Color(0.13, 0.15, 0.22), true)
	for r in ROWS:
		for c in COLS:
			var rect := Rect2(GRID_LEFT + c * CELL, GRID_TOP + r * CELL, CELL, CELL)
			var shade := CELL_A if (r + c) % 2 == 0 else CELL_B
			draw_rect(rect, shade, true)
			draw_rect(rect, Color(0.16, 0.18, 0.26), false, 1.0)

	for ring in ripple_rings:
		var t: float = ring.life / ring.duration
		var radius: float = ring.max_radius * t
		var alpha := (1.0 - t) * 0.8
		var col: Color = ring.color
		col.a = alpha
		draw_arc(ring.center, radius, 0.0, TAU, 40, col, 3.0, true)

	for i in moods.size():
		var pos := _cell_center(_cell_at(i))
		_draw_villager(pos, moods[i], troubles[i])

	# Ripple + player marker (the helper you control).
	_draw_player(_cell_center(caret))

	for f in floaties:
		var t: float = f.life / f.duration
		var col: Color = f.color
		col.a = 1.0 - t
		draw_string(font, f.pos, f.text, HORIZONTAL_ALIGNMENT_CENTER, -1, 18, col)


func _draw_villager(center: Vector2, mood: float, in_trouble: bool) -> void:
	var body := _mood_color(mood)
	draw_circle(center, 19.0, body.darkened(0.25))
	draw_circle(center, 15.5, body)
	# Eyes
	var eye_off := Vector2(5.0, -4.0)
	draw_circle(center + Vector2(-eye_off.x, eye_off.y), 2.2, Color(0.08, 0.08, 0.12))
	draw_circle(center + Vector2(eye_off.x, eye_off.y), 2.2, Color(0.08, 0.08, 0.12))
	# Mouth: bends up when happy, down when sad.
	var baseline := center + Vector2(0, 5.5)
	var bend := (mood - 0.5) * 14.0
	var pts := PackedVector2Array([
		baseline + Vector2(-7, -bend),
		baseline + Vector2(0, bend),
		baseline + Vector2(7, -bend),
	])
	draw_polyline(pts, Color(0.08, 0.08, 0.12), 2.0, true)
	if in_trouble:
		draw_string(font, center + Vector2(0, -26), "!", HORIZONTAL_ALIGNMENT_CENTER, -1, 20,
				Color(1.0, 0.5, 0.4))


func _draw_player(center: Vector2) -> void:
	var pulse := 1.0 + sin(Time.get_ticks_msec() / 240.0) * 0.06
	var r := 21.0 * pulse
	draw_circle(center, r + 5.0, Color(1.0, 1.0, 1.0, 0.10))
	draw_circle(center, r, Color(0.95, 0.96, 1.0))
	draw_arc(center, r, 0.0, TAU, 40, Color(0.5, 0.85, 0.95), 3.0, true)
	_draw_heart(center, 10.0, Color(0.96, 0.35, 0.45))


func _draw_heart(center: Vector2, s: float, color: Color) -> void:
	draw_circle(center + Vector2(-s * 0.24, -s * 0.18), s * 0.30, color)
	draw_circle(center + Vector2(s * 0.24, -s * 0.18), s * 0.30, color)
	var tri := PackedVector2Array([
		center + Vector2(-s * 0.46, -s * 0.08),
		center + Vector2(s * 0.46, -s * 0.08),
		center + Vector2(0, s * 0.50),
	])
	draw_colored_polygon(tri, color)


func _draw_hud() -> void:
	# Title
	draw_string(font, Vector2(32, 44), "RIPPLE", HORIZONTAL_ALIGNMENT_LEFT, -1, 34, TEXT_COLOR)
	draw_string(font, Vector2(33, 70), "a kindness game", HORIZONTAL_ALIGNMENT_LEFT, -1, 15, DIM_COLOR)

	# Community meter
	var stage: String = STAGE_NAMES[_stage_for(avg_mood)]
	draw_string(font, Vector2(GRID_LEFT, 96), "Community wellbeing \u00b7 %s" % stage,
			HORIZONTAL_ALIGNMENT_LEFT, -1, 16, TEXT_COLOR)
	var bar := Rect2(GRID_LEFT, 102, GRID_W, 16)
	draw_rect(bar, Color(0.12, 0.14, 0.22), true)
	draw_rect(bar, Color(0.25, 0.28, 0.4), false, 1.0)
	draw_rect(Rect2(bar.position, Vector2(bar.size.x * clampf(avg_mood, 0.0, 1.0), bar.size.y)),
			GOLD_COLOR, true)
	# Joy goal marker
	var goal_x := bar.position.x + bar.size.x * JOY_TARGET
	draw_line(Vector2(goal_x, bar.position.y), Vector2(goal_x, bar.position.y + bar.size.y),
			Color(1, 1, 1, 0.7), 2.0)

	# Care meter (bottom-left of the play field)
	draw_string(font, Vector2(32, HEIGHT - 116), "Care", HORIZONTAL_ALIGNMENT_LEFT, -1, 15, DIM_COLOR)
	var care_bar := Rect2(32, HEIGHT - 102, 220, 14)
	draw_rect(care_bar, Color(0.12, 0.14, 0.22), true)
	draw_rect(care_bar, Color(0.25, 0.28, 0.4), false, 1.0)
	draw_rect(Rect2(care_bar.position, Vector2(care_bar.size.x * care, care_bar.size.y)),
			CARE_COLOR, true)

	# Ledger (right)
	var ledger := "Acts of kindness: %d" % kindness_count
	if greed_count > 0:
		ledger += "    Hoardings: %d" % greed_count
	draw_string(font, Vector2(GRID_LEFT + GRID_W, HEIGHT - 96), ledger,
			HORIZONTAL_ALIGNMENT_RIGHT, -1, 15, DIM_COLOR)

	# Joy progress while near the goal
	if state == State.PLAY and avg_mood >= JOY_TARGET:
		draw_string(font, Vector2(WIDTH / 2.0, HEIGHT - 40),
				"Joy is spreading\u2026 %.0f%%" % (joy_time / JOY_SECONDS * 100.0),
				HORIZONTAL_ALIGNMENT_CENTER, -1, 16, GOLD_COLOR)

	# Lesson / hint banners
	if lesson_text != "":
		draw_string(font, Vector2(WIDTH / 2.0, HEIGHT - 64), lesson_text,
				HORIZONTAL_ALIGNMENT_CENTER, -1, 16, GOLD_COLOR)
	if hint_text != "":
		draw_string(font, Vector2(WIDTH / 2.0, HEIGHT - 28), hint_text,
				HORIZONTAL_ALIGNMENT_CENTER, -1, 14, Color(1.0, 0.72, 0.6))

	# Controls hint
	if state == State.PLAY:
		draw_string(font, Vector2(WIDTH / 2.0, HEIGHT - 84),
				"Arrows / WASD to move  \u00b7  SPACE: help  \u00b7  X: hoard",
				HORIZONTAL_ALIGNMENT_CENTER, -1, 13, DIM_COLOR)


func _draw_intro() -> void:
	var dim := Color(0.02, 0.025, 0.05, 0.82)
	draw_rect(Rect2(0, 0, WIDTH, HEIGHT), dim)
	draw_string(font, Vector2(WIDTH / 2.0, 250), "RIPPLE", HORIZONTAL_ALIGNMENT_CENTER, -1, 64, TEXT_COLOR)
	draw_string(font, Vector2(WIDTH / 2.0, 292), "a kindness game", HORIZONTAL_ALIGNMENT_CENTER, -1, 22, GOLD_COLOR)
	var lines := [
		"In a little village, everyone has ups and downs.",
		"Move with the arrow keys and press SPACE to help someone in need.",
		"Kindness is contagious: it ripples to the neighbours, and a cheerful",
		"community gives you the energy to keep helping.",
		"",
		"Press X to hoard for yourself if you like \u2014 and watch what happens.",
		"Fill the community's wellbeing past the white line, and hold it there",
		"to become a Beloved Community.",
	]
	var y := 350.0
	for line in lines:
		draw_string(font, Vector2(WIDTH / 2.0, y), line, HORIZONTAL_ALIGNMENT_CENTER, -1, 18, TEXT_COLOR)
		y += 28.0
	var blink := 0.6 + 0.4 * sin(Time.get_ticks_msec() / 300.0)
	draw_string(font, Vector2(WIDTH / 2.0, 580), "Press SPACE to begin",
			HORIZONTAL_ALIGNMENT_CENTER, -1, 20, Color(1, 1, 1, blink))


func _draw_won() -> void:
	var dim := Color(0.02, 0.03, 0.05, 0.85)
	draw_rect(Rect2(0, 0, WIDTH, HEIGHT), dim)
	draw_string(font, Vector2(WIDTH / 2.0, 240), "A Beloved Community", HORIZONTAL_ALIGNMENT_CENTER, -1, 54, GOLD_COLOR)
	var lines := [
		"You helped %d times, and the whole village is well." % kindness_count,
		"",
		"Kindness is contagious. Every small act ripples outward in ways",
		"you cannot see. Real-world research shows the same: cooperation,",
		"trust and generosity build the commons that everyone depends on,",
		"while greed quietly depletes them.",
		"",
		"This is the only game worth everyone playing \u2014 in here, and out there.",
	]
	var y := 320.0
	for line in lines:
		draw_string(font, Vector2(WIDTH / 2.0, y), line, HORIZONTAL_ALIGNMENT_CENTER, -1, 18, TEXT_COLOR)
		y += 28.0
	draw_string(font, Vector2(WIDTH / 2.0, y + 20), "Press R to play again",
			HORIZONTAL_ALIGNMENT_CENTER, -1, 16, DIM_COLOR)