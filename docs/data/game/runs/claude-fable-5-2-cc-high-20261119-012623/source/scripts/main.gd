extends Node2D
## Steady Hands - flow between title, the five moments, debriefs and the pocket card.

const Art = preload("res://scripts/art.gd")
const HudScript = preload("res://scripts/hud.gd")
const SAVE_PATH := "user://steady_hands.cfg"
const NUMBERS := ["112", "911", "999", "000", "111", "119", "120", "108", "192"]

const MOMENTS := [
	{
		"id": "park", "time": "07:40", "name": "The Park", "sub": "A stranger collapses on the path.",
		"topic": "Cardiac arrest", "icon": "heart",
		"script": preload("res://scripts/s_collapse.gd"),
		"remember": [
			"Not responding and not breathing normally? Call {n} and start pushing.",
			"Centre of the chest. Hard and fast — two pushes a second — and let it rise each time.",
			"Point at ONE person: “You — call {n}.” A crowd waits. A named person acts.",
			"Switch on a defibrillator and do what it says. It will not shock a heart that doesn't need it.",
		],
		"fact": "Each minute without CPR cuts the chance of survival by 7–10%. CPR from a bystander can double or triple it. Never learned rescue breaths? Pushing alone is what counts.",
		"pocket": "No response, no normal breathing: call, push hard and fast on the centre of the chest, send for a defibrillator.",
	},
	{
		"id": "cafe", "time": "12:30", "name": "The Café", "sub": "A diner goes silent.",
		"topic": "Choking", "icon": "airway",
		"script": preload("res://scripts/s_choking.gd"),
		"remember": [
			"Can't speak, cough or breathe? That's choking. (If they CAN cough, tell them to keep coughing.)",
			"Lean them forward. Five hard blows between the shoulder blades.",
			"Then five abdominal thrusts: fist just above the navel, pull in and up. Keep alternating.",
			"If they go limp: call {n} and start chest compressions.",
		],
		"fact": "Brain injury begins after about four minutes without air — sooner than most ambulances can arrive. Babies under one need a gentler technique; a first-aid class teaches it in minutes.",
		"pocket": "Can't cough or speak: five back blows, five abdominal thrusts, repeat.",
	},
	{
		"id": "tea", "time": "15:10", "name": "Tea at Rosa's", "sub": "Something is off with Aunt Rosa.",
		"topic": "Stroke", "icon": "clock",
		"script": preload("res://scripts/s_stroke.gd"),
		"remember": [
			"F — Face. Ask for a smile. Does one side droop?",
			"A — Arms. Both arms up. Does one drift down?",
			"S — Speech. Slurred, strange, or missing words?",
			"T — Time. One sign is enough: call {n} at once, and note when it started.",
		],
		"fact": "During a stroke the brain loses around 1.9 million cells a minute. Treatment works — but only in the first hours. Even if the signs pass, it is still an emergency.",
		"pocket": "Face, Arms, Speech: one sign means Time to call. Note when it started.",
	},
	{
		"id": "ride", "time": "17:15", "name": "The Ride Home", "sub": "A cyclist is bleeding badly.",
		"topic": "Severe bleeding", "icon": "drop",
		"script": preload("res://scripts/s_bleeding.gd"),
		"remember": [
			"Heavy bleeding kills in minutes. Press first — any clean cloth, or your bare hands.",
			"Push hard, directly on the wound, and don't let go until help takes over.",
			"Soaked through? Add more on top. Never lift it to look.",
			"Lay them down, keep them warm, nothing to eat or drink.",
		],
		"fact": "A person can bleed to death in as little as five minutes. Most ambulances take longer than that. The person standing next to them doesn't.",
		"pocket": "Press hard on the wound and keep pressing. Add cloth, never lift.",
	},
	{
		"id": "kitchen", "time": "19:50", "name": "The Kitchen", "sub": "Boiling water, bare skin.",
		"topic": "Burns", "icon": "flame",
		"script": preload("res://scripts/s_burn.gd"),
		"remember": [
			"Cool running water for a full 20 minutes — as soon as you can.",
			"No ice. No butter, oil, toothpaste or creams.",
			"Rings, watches and loose clothing off before the swelling starts. Never pull off anything stuck to the skin.",
			"Cover loosely with cling film or a clean plastic bag. Don't pop blisters.",
		],
		"fact": "Get medical help for burns bigger than the person's hand, on the face, hands, feet or groin, with white or charred skin — and for young children.",
		"pocket": "Twenty minutes of cool running water. Nothing else on it.",
	},
]

var screen := ""
var screen_t := 0.0
var t := 0.0
var busy := false
var auto := false
var shots_dir := ""
var shot_n := 0
var shot_acc := 0.0
var quit_after := 0.0
var debug_screen := ""

var number := "112"
var best: Dictionary = {}
var today: Dictionary = {}
var idx := 0
var day_mode := true
var result: Dictionary = {}
var stars_shown := 0

var ui: Control
var fade: ColorRect
var scenario: Node
var hud: CanvasLayer
var num_label: Label
var sound_btn: Button


func _ready() -> void:
	randomize()
	for a in OS.get_cmdline_user_args():
		if a == "--auto":
			auto = true
		elif a.begins_with("--shots="):
			shots_dir = a.trim_prefix("--shots=")
		elif a.begins_with("--speed="):
			Engine.time_scale = float(a.trim_prefix("--speed="))
		elif a.begins_with("--screen="):
			debug_screen = a.trim_prefix("--screen=")
		elif a.begins_with("--quit-after="):
			quit_after = float(a.trim_prefix("--quit-after="))
		elif a.begins_with("--only="):
			idx = int(a.trim_prefix("--only="))
			day_mode = false
	_load()
	var layer := CanvasLayer.new()
	layer.layer = 8
	add_child(layer)
	ui = Control.new()
	ui.set_anchors_preset(Control.PRESET_FULL_RECT)
	ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(ui)
	var top := CanvasLayer.new()
	top.layer = 20
	add_child(top)
	fade = ColorRect.new()
	fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	fade.color = Color(Art.INK, 0.0)
	fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top.add_child(fade)
	_show_title()
	if debug_screen == "finale":
		for m: Dictionary in MOMENTS:
			today[m["id"]] = 1 + randi() % 3
		_show_finale()
	elif debug_screen == "card":
		_show_card()
	elif auto:
		if day_mode:
			_start_day()
		else:
			_go(_show_card)


func _exit_tree() -> void:
	Art.cleanup()


func _process(delta: float) -> void:
	t += delta
	screen_t += delta
	if screen == "card" and debug_screen == "" and (screen_t > 6.0 or (auto and screen_t > 0.3)):
		_go(_play)
	if screen == "debrief":
		var want := mini(int((screen_t - 0.5) / 0.38) + 1, int(result.get("stars", 1))) if screen_t > 0.5 else 0
		if want > stars_shown:
			stars_shown = want
			Sfx.play("star", -4.0, 0.9 + stars_shown * 0.12)
		if auto and screen_t > 2.2:
			_next()
	if quit_after > 0.0 and t > quit_after:
		get_tree().quit()
	if screen == "finale" and auto and screen_t > 2.0:
		print("AUTO OK")
		get_tree().quit()
	if screen != "play":
		queue_redraw()
	if shots_dir != "":
		shot_acc += delta / maxf(Engine.time_scale, 0.01)
		if shot_acc > 0.7:
			shot_acc = 0.0
			shot_n += 1
			get_viewport().get_texture().get_image().save_png("%s/shot_%03d.png" % [shots_dir, shot_n])


func _unhandled_input(event: InputEvent) -> void:
	var click: bool = event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT
	var k := event as InputEventKey
	var go: bool = k != null and k.pressed and not k.echo and (k.keycode == KEY_SPACE or k.keycode == KEY_ENTER)
	if k != null and k.pressed and not k.echo:
		if k.keycode == KEY_M:
			_toggle_sound()
		elif k.keycode == KEY_ESCAPE and screen == "play":
			_to_title()
	if screen == "card" and screen_t > 0.5 and (click or go):
		_go(_play)


# ---------------------------------------------------------------- persistence

func _load() -> void:
	var cf := ConfigFile.new()
	if cf.load(SAVE_PATH) == OK:
		number = str(cf.get_value("player", "number", "112"))
		for m: Dictionary in MOMENTS:
			best[m["id"]] = int(cf.get_value("best", m["id"], 0))


func _save() -> void:
	var cf := ConfigFile.new()
	cf.set_value("player", "number", number)
	for m: Dictionary in MOMENTS:
		cf.set_value("best", m["id"], int(best.get(m["id"], 0)))
	cf.save(SAVE_PATH)


# ---------------------------------------------------------------- navigation

func _go(fn: Callable) -> void:
	if busy:
		return
	busy = true
	fade.mouse_filter = Control.MOUSE_FILTER_STOP
	var tw := create_tween()
	tw.tween_property(fade, "color:a", 1.0, 0.22)
	tw.tween_callback(fn)
	tw.tween_property(fade, "color:a", 0.0, 0.3)
	tw.tween_callback(_unbusy)


func _unbusy() -> void:
	busy = false
	fade.mouse_filter = Control.MOUSE_FILTER_IGNORE


func _set_screen(s: String) -> void:
	screen = s
	screen_t = 0.0
	for c in ui.get_children():
		ui.remove_child(c)
		c.queue_free()
	if scenario != null:
		scenario.queue_free()
		scenario = null
	if hud != null:
		hud.queue_free()
		hud = null
	Sfx.stop_loop()
	queue_redraw()


func _button(text: String, kind: String, rect: Rect2, fn: Callable, size: int = 20) -> Button:
	var b := Button.new()
	b.text = text
	Art.style_button(b, kind, size)
	b.position = rect.position
	b.size = rect.size
	b.pressed.connect(fn)
	b.pressed.connect(_click)
	ui.add_child(b)
	return b


func _click() -> void:
	Sfx.play("click")


func _start_day() -> void:
	if busy:
		return
	day_mode = true
	idx = 0
	today.clear()
	_go(_show_card)


func _practice(i: int) -> void:
	if busy:
		return
	day_mode = false
	idx = i
	_go(_show_card)


func _to_title() -> void:
	_go(_show_title)


func _retry() -> void:
	_go(_play)


func _next() -> void:
	if busy:
		return
	if day_mode and idx < MOMENTS.size() - 1:
		idx += 1
		_go(_show_card)
	elif day_mode:
		_go(_show_finale)
	else:
		_go(_show_title)


func _cycle_number(d: int) -> void:
	var i := NUMBERS.find(number)
	number = NUMBERS[posmod(i + d, NUMBERS.size())]
	num_label.text = number
	_save()


func _toggle_sound() -> void:
	Sfx.set_muted(not Sfx.muted)
	if is_instance_valid(sound_btn):
		sound_btn.text = "Sound: off" if Sfx.muted else "Sound: on"
	if hud != null:
		hud.refresh_sound()


func n(s: String) -> String:
	return s.replace("{n}", number)


# ---------------------------------------------------------------- screens

func _show_title() -> void:
	_set_screen("title")
	_button("Begin the day", "primary", Rect2(80, 318, 280, 66), _start_day, 24)
	sound_btn = _button("Sound: off" if Sfx.muted else "Sound: on", "ghost", Rect2(1090, 24, 130, 38), _toggle_sound, 15)
	_button("<", "ghost", Rect2(80, 432, 44, 44), _cycle_number.bind(-1), 20)
	_button(">", "ghost", Rect2(232, 432, 44, 44), _cycle_number.bind(1), 20)
	num_label = Label.new()
	num_label.text = number
	num_label.position = Vector2(124, 432)
	num_label.size = Vector2(108, 44)
	num_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	num_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	num_label.add_theme_font_override("font", Art.bold())
	num_label.add_theme_font_size_override("font_size", 28)
	num_label.add_theme_color_override("font_color", Art.INK)
	ui.add_child(num_label)
	for i in MOMENTS.size():
		var b := Button.new()
		b.focus_mode = Control.FOCUS_NONE
		b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		b.position = Vector2(80 + i * 227, 536)
		b.size = Vector2(212, 132)
		b.add_theme_stylebox_override("normal", Art.flat(Art.PAPER, 18, Color(Art.INK, 0.12), 2))
		b.add_theme_stylebox_override("hover", Art.flat(Color.WHITE, 18, Art.CORAL, 2))
		b.add_theme_stylebox_override("pressed", Art.flat(Color("fde6dc"), 18, Art.CORAL, 2))
		b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
		b.draw.connect(_draw_moment_card.bind(b, i))
		b.pressed.connect(_practice.bind(i))
		b.pressed.connect(_click)
		ui.add_child(b)


func _show_card() -> void:
	_set_screen("card")


func _play() -> void:
	_set_screen("play")
	var m: Dictionary = MOMENTS[idx]
	hud = HudScript.new()
	hud.auto = auto
	add_child(hud)
	hud.menu_pressed.connect(_to_title)
	var scr: GDScript = m["script"]
	scenario = scr.new()
	scenario.hud = hud
	scenario.number = number
	scenario.auto = auto
	add_child(scenario)
	scenario.finished.connect(_on_finished)
	scenario.run()


func _on_finished(res: Dictionary) -> void:
	result = res
	var id: String = MOMENTS[idx]["id"]
	var s: int = res.get("stars", 1)
	today[id] = s
	best[id] = maxi(int(best.get(id, 0)), s)
	_save()
	_go(_show_debrief)


func _show_debrief() -> void:
	_set_screen("debrief")
	stars_shown = 0
	var last := day_mode and idx == MOMENTS.size() - 1
	var label := "Back to the title"
	if day_mode:
		label = "See your pocket card" if last else "On with the day"
	_button(label, "primary", Rect2(916, 624, 284, 60), _next, 21)
	_button("Try this moment again", "ghost", Rect2(660, 630, 236, 48), _retry, 17)


func _show_finale() -> void:
	_set_screen("finale")
	Sfx.play("win")
	_button("Back to the title", "primary", Rect2(948, 636, 252, 56), _to_title, 20)
	_button("Live the day again", "ghost", Rect2(716, 640, 212, 48), _start_day, 17)


# ---------------------------------------------------------------- drawing

func _draw() -> void:
	match screen:
		"title":
			_draw_title()
		"card":
			_draw_card()
		"debrief":
			_draw_debrief()
		"finale":
			_draw_finale()


func _draw_title() -> void:
	draw_rect(Rect2(0, 0, 1280, 720), Art.CREAM)
	var hc := Vector2(960, 262)
	var beat := fmod(t * 110.0 / 60.0, 1.0)
	var pulse := pow(1.0 - beat, 3.0)
	Art.disc(self, hc, 236.0 + pulse * 6.0, Color("fbe3da"))
	Art.disc(self, hc, 178.0 + pulse * 10.0, Color("f8d0c3"))
	# heartbeat trace
	var pts := PackedVector2Array()
	for i in 200:
		var x := 640.0 + i * 3.2
		var u := fposmod(x - t * 150.0, 220.0) / 220.0
		var y := 0.0
		if u > 0.30 and u < 0.36:
			y = -sin((u - 0.30) / 0.06 * PI) * 10.0
		elif u > 0.42 and u < 0.45:
			y = (u - 0.42) / 0.03 * 14.0
		elif u >= 0.45 and u < 0.49:
			y = 14.0 - (u - 0.45) / 0.04 * 88.0
		elif u >= 0.49 and u < 0.53:
			y = -74.0 + (u - 0.49) / 0.04 * 96.0
		elif u >= 0.53 and u < 0.56:
			y = 22.0 - (u - 0.53) / 0.03 * 22.0
		elif u > 0.66 and u < 0.78:
			y = -sin((u - 0.66) / 0.12 * PI) * 15.0
		pts.append(Vector2(x, hc.y + 10.0 + y))
	draw_polyline(pts, Color(Art.INK, 0.2), 3.0, true)
	Art.heart(self, hc + Vector2(0, 8), 118.0 + pulse * 12.0, Art.CORAL_DARK)
	Art.heart(self, hc, 118.0 + pulse * 12.0, Art.CORAL)
	Art.oval(self, hc + Vector2(-52, -52), Vector2(26, 15), Color(1, 1, 1, 0.28), -0.6)
	Art.text_c(self, Vector2(hc.x, 452), "This heart is beating 110 times a minute.", 17, Art.INK_SOFT)
	Art.text_c(self, Vector2(hc.x, 476), "By tonight your hands will know that rhythm.", 17, Art.INK_SOFT)

	Art.text(self, Vector2(76, 150), "Steady Hands", 86, Art.INK, true)
	Art.text(self, Vector2(80, 204), "One ordinary day. Five moments where", 26, Art.INK)
	Art.text(self, Vector2(80, 238), "the nearest person is you.", 26, Art.INK)
	Art.text(self, Vector2(80, 282), "Learn what to do in the minutes before help arrives.", 18, Art.INK_SOFT)
	Art.text(self, Vector2(80, 420), "EMERGENCY NUMBER WHERE YOU LIVE", 13, Art.INK_SOFT, true)
	Art.rrect(self, Rect2(124, 432, 108, 44), Color.WHITE, 12)
	Art.text(self, Vector2(296, 452), "Not sure? 112 works from mobile phones", 14, Art.INK_SOFT)
	Art.text(self, Vector2(296, 472), "in most countries.", 14, Art.INK_SOFT)
	Art.text(self, Vector2(80, 524), "OR PRACTISE A SINGLE MOMENT", 13, Art.INK_SOFT, true)
	Art.text(self, Vector2(80, 700), "General first-aid guidance drawn from international resuscitation and Red Cross guidelines. A game can't replace a hands-on course — but it's a start.", 13, Art.INK_SOFT)


func _draw_moment_card(b: Button, i: int) -> void:
	var m: Dictionary = MOMENTS[i]
	Art.icon(b, m["icon"], Vector2(176, 34), 15.0, Color(Art.CORAL, 0.9))
	Art.text(b, Vector2(18, 34), m["time"], 15, Art.INK_SOFT, true)
	Art.text(b, Vector2(18, 66), m["name"], 22, Art.INK, true)
	Art.text(b, Vector2(18, 90), m["topic"], 15, Art.INK_SOFT)
	var s: int = best.get(m["id"], 0)
	for k in 3:
		Art.star(b, Vector2(28 + k * 24, 112), 10.0, Art.AMBER if k < s else Color(Art.INK, 0.12))


func _draw_card() -> void:
	var m: Dictionary = MOMENTS[idx]
	draw_rect(Rect2(0, 0, 1280, 720), Art.INK)
	var a := clampf(screen_t * 2.5, 0.0, 1.0)
	Art.disc(self, Vector2(1010, 340), 190.0, Color(1, 1, 1, 0.04))
	Art.icon(self, m["icon"], Vector2(1010, 340), 86.0, Color(Art.CORAL, a))
	var tag := ("MOMENT %d OF %d" % [idx + 1, MOMENTS.size()]) if day_mode else "PRACTICE"
	Art.text(self, Vector2(120, 220), tag, 16, Color(Art.CORAL, a), true)
	Art.text(self, Vector2(114, 350), m["time"], 128, Color(1, 1, 1, a), true)
	Art.text(self, Vector2(120, 420), m["name"], 44, Color(1, 1, 1, a), true)
	Art.text(self, Vector2(120, 466), m["sub"], 24, Color(Art.CREAM, 0.75 * a))
	if screen_t > 1.0:
		Art.text(self, Vector2(120, 600), "Click to step in", 17, Color(1, 1, 1, 0.35 + 0.25 * sin(t * 4.0)))


func _draw_debrief() -> void:
	var m: Dictionary = MOMENTS[idx]
	draw_rect(Rect2(0, 0, 1280, 720), Art.CREAM)
	Art.disc(self, Vector2(120, 110), 300.0, Color("fbe3da"))
	Art.text(self, Vector2(80, 92), "%s  ·  %s" % [m["time"], String(m["name"]).to_upper()], 15, Art.INK_SOFT, true)
	var s: int = result.get("stars", 1)
	for k in 3:
		var c := Vector2(116 + k * 82, 160)
		Art.star(self, c, 36.0, Color(Art.INK, 0.1))
		if k < stars_shown and k < s:
			var age := screen_t - 0.5 - k * 0.38
			var sc := 1.0 + maxf(0.0, 0.5 - age * 2.5)
			Art.star(self, c, 36.0 * sc, Art.AMBER)
	var y := 222.0
	y += Art.para(self, Vector2(80, y), result.get("headline", ""), 500.0, 38, Art.INK, true) + 14.0
	y += Art.para(self, Vector2(80, y), result.get("outcome", ""), 500.0, 19, Art.INK) + 26.0
	var fact: String = n(m["fact"])
	var fh := Art.para_h(fact, 444.0, 17)
	Art.rrect(self, Rect2(80, y, 500, fh + 62), Color("fbe3da"), 18)
	Art.text(self, Vector2(104, y + 30), "WHY IT MATTERS", 13, Art.CORAL_DARK, true)
	Art.para(self, Vector2(104, y + 40), fact, 444.0, 17, Art.INK)

	var cardr := Rect2(650, 70, 550, 530)
	Art.card(self, cardr)
	Art.text(self, Vector2(686, 116), "REMEMBER", 15, Art.TEAL, true)
	Art.text(self, Vector2(686, 150), m["topic"], 30, Art.INK, true)
	var ry := 180.0
	var rem: Array = m["remember"]
	for k in rem.size():
		var line: String = n(rem[k])
		Art.disc(self, Vector2(702, ry + 16), 15.0, Art.TEAL)
		Art.text_c(self, Vector2(702, ry + 16), str(k + 1), 16, Color.WHITE, true)
		ry += Art.para(self, Vector2(734, ry), line, 430.0, 20, Art.INK) + 22.0


func _draw_finale() -> void:
	draw_rect(Rect2(0, 0, 1280, 720), Art.CREAM)
	Art.disc(self, Vector2(1180, 60), 280.0, Color("fbe3da"))
	var total := 0
	for m: Dictionary in MOMENTS:
		total += int(today.get(m["id"], 0))
	Art.text(self, Vector2(80, 82), "23:00  ·  THE DAY IS OVER", 15, Art.INK_SOFT, true)
	Art.text(self, Vector2(78, 136), "Five people got through today.", 44, Art.INK, true)
	Art.text(self, Vector2(80, 170), "None of them needed a hero. They needed whoever was closest to know what to do.", 19, Art.INK)
	Art.star(self, Vector2(1090, 110), 22.0, Art.AMBER)
	Art.text(self, Vector2(1120, 121), "%d / %d" % [total, MOMENTS.size() * 3], 30, Art.INK, true)

	var cardr := Rect2(80, 196, 1120, 420)
	Art.card(self, cardr)
	Art.text(self, Vector2(112, 238), "YOUR POCKET CARD", 15, Art.TEAL, true)
	var y := 258.0
	for m: Dictionary in MOMENTS:
		Art.disc(self, Vector2(132, y + 24), 21.0, Color("fbe3da"))
		Art.icon(self, m["icon"], Vector2(132, y + 24), 11.0, Art.CORAL)
		Art.text(self, Vector2(168, y + 31), m["topic"], 19, Art.INK, true)
		Art.para(self, Vector2(350, y + 2), n(m["pocket"]), 690.0, 18, Art.INK)
		var s: int = today.get(m["id"], 0)
		for k in 3:
			Art.star(self, Vector2(1092 + k * 26, y + 24), 10.0, Art.AMBER if k < s else Color(Art.INK, 0.12))
		y += 58.0
	draw_line(Vector2(112, y + 4), Vector2(1168, y + 4), Color(Art.INK, 0.1), 2.0)
	Art.text(self, Vector2(112, y + 40), "Always", 19, Art.CORAL_DARK, true)
	Art.para(self, Vector2(350, y + 20), n("Point at one person: “You — call {n}.” On speaker, the call handler will coach you."), 800.0, 18, Art.INK)
	Art.para(self, Vector2(80, 634), "Next step: a real first-aid course. A few hours with a manikin does what no game can. And pass this on — every player is one more pair of steady hands.", 600.0, 16, Art.INK_SOFT)
