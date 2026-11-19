extends "res://scripts/scenario.gd"
## 19:50 - The Kitchen. Burns: cool running water for 20 minutes, nothing else.

const COOL_LEN := 19.0                  # seconds on screen for the 20 minutes
const ZONE_LO := 0.3
const ZONE_HI := 0.7
const BTN_COLD := Rect2(74, 236, 150, 56)
const BTN_WARM := Rect2(236, 236, 150, 56)
const WATCH := Vector2(806, 396)

const ITEMS := [
	{"id": "ice", "rect": Rect2(150, 150, 120, 110), "name": "Ice"},
	{"id": "butter", "rect": Rect2(300, 150, 130, 110), "name": "Butter"},
	{"id": "paste", "rect": Rect2(460, 150, 130, 110), "name": "Toothpaste"},
	{"id": "tap", "rect": Rect2(690, 240, 200, 200), "name": "Cold tap"},
]
const WRONG := {
	"ice": "Ice is too cold. It shuts down blood flow in skin that is already damaged and can deepen the injury. Cool — not freezing.",
	"butter": "Butter, oil and grease seal the heat in, so the burn keeps cooking — and they bring infection with them.",
	"paste": "Toothpaste traps heat, irritates the wound and has to be scrubbed off later. It's a myth in almost every country on earth.",
}

var view := "kitchen"
var saved := 0.9
var tried: Dictionary = {}
var temp := 0.5
var drift := 0.12
var drift_t := 1.5
var cold := false
var warm := false
var key_cold := false
var key_warm := false
var cooling := false
var cool_t := 0.0
var in_zone := 0.0
var watch_on := true
var watch_t := -10.0
var asked_stop := false
var covered := false

var sam := {"skin": Art.SKINS[0], "hair": Art.HAIRS[2], "style": 0, "top": Color("5b8c5a"), "legs": Color("39424e"), "sleeves": false}


func run() -> void:
	hud.set_title("19:50  ·  The Kitchen")
	hud.hide_panel()
	set_phase("cook")
	await pause(1.5)
	Sfx.play("slap")
	Sfx.play("thud")
	set_phase("spill")
	await pause(1.0)
	await say("Dinner at home. Your flatmate Sam lifts the pasta pot off the stove — and it slips. Boiling water pours over his forearm.")
	hud.show_meter("SKIN SAVED")
	var first := true
	while true:
		set_phase("pick")
		hud.instruct("He's hopping with pain. Every family has a cure for burns. What do you reach for? Click it." if first else "Not that. What else is there? Click it.", "FIRST: COOL THE BURN")
		first = false
		var id: String = await picked
		if id == "tap":
			break
		tried[id] = true
		await bad(WRONG[id])
	set_phase("chosen")
	await good("Cool running water. It's the one thing proven to limit a burn: it draws the heat out of the skin, eases the pain, and reduces scarring.")
	await quiz("Arm under the tap. For how long?", [
		{"t": "A full 20 minutes", "ok": true, "fb": "Twenty minutes. It feels endless — and it's what stops the burn going deeper. It still helps even three hours after the injury."},
		{"t": "Until it stops stinging — a minute or two", "ok": false, "fb": "The pain fades long before the heat is gone; underneath, the skin keeps cooking. Go the full 20 minutes."},
		{"t": "About five minutes", "ok": false, "fb": "Better than nothing — but burns keep deepening for a long while. The evidence says 20 minutes."},
	])
	view = "sink"
	set_phase("cool")
	Sfx.loop("water")
	hud.instruct("Keep the water COOL — not icy, not warm. Hold the buttons (or the ← → keys) to adjust. And slip his watch off before the arm swells.", "20 MINUTES UNDER THE TAP")
	cooling = true
	await step_done
	cooling = false
	Sfx.stop_loop()
	skill = clampf((in_zone / COOL_LEN - 0.4) / 0.4, 0.0, 1.0)
	set_phase("cooled")
	if watch_on:
		await bad("His wrist has puffed up around the watch strap. Burns swell fast: take off rings, watches and bracelets straight away, before they start cutting off the blood.")
		watch_on = false
		watch_t = t
	await quiz("Twenty minutes done. The skin is red and a blister is rising. Now?", [
		{"t": "Lay cling film or a clean plastic bag loosely over it", "ok": true, "fb": "Cling film keeps the burn clean, doesn't stick, and lets a doctor see through it. Lay it on in a strip — never wrap it tight around the arm."},
		{"t": "Pop the blister so it can drain", "ok": false, "fb": "A blister is a sterile dressing your body made itself. Pop it and you open the door to infection."},
		{"t": "Rub in a soothing cream and wrap it in cotton wool", "ok": false, "fb": "Creams hold heat in and must be scrubbed off at the hospital; fluffy fibres stick to the wound. Cover it loosely with something clean and smooth."},
	])
	covered = true
	set_phase("covered")
	await say("The burn is bigger than Sam's palm and it's blistering, so you take him to get it looked at.\n\nGet medical help for any burn larger than the person's hand, on the face, hands, feet or groin, or with white or charred skin — and for young children.")
	if saved > 0.5:
		finish("Sam will heal without a scar.", "Twenty minutes of cool water, nothing from the fridge or the bathroom cabinet, and a loose clean cover. Boring — and exactly right.")
	else:
		finish("Sam's burn will take a while to heal.", "Every detour — the ice, the butter, water too cold or too warm — let the heat sink deeper. Cool running water, straight away, for 20 minutes.")


func on_mistake() -> void:
	saved -= 0.09


func tick(delta: float) -> void:
	if hud.waiting() and not cooling:
		saved -= 0.006 * delta
	if cooling:
		cool_t += delta
		drift_t -= delta
		if drift_t <= 0.0:
			drift_t = randf_range(1.3, 2.4)
			var away := 1.0 if temp > 0.5 else -1.0
			drift = randf_range(0.1, 0.2) * (away if randf() < 0.65 else -away)
		var c := 0.0
		if cold or key_cold:
			c -= 1.0
		if warm or key_warm:
			c += 1.0
		if auto:
			c = clampf((0.5 - temp) * 6.0, -1.0, 1.0)
			if cool_t > 4.0 and randf() < 0.5:
				_take_watch()
		temp = clampf(temp + (drift + c * 0.42) * delta, 0.0, 1.0)
		if temp >= ZONE_LO and temp <= ZONE_HI:
			in_zone += delta
			saved += 0.004 * delta
		else:
			saved -= 0.02 * delta
		if not asked_stop and cool_t > COOL_LEN * 0.35:
			asked_stop = true
			hud.instruct("“It's stopped hurting — can we stop?”  Not yet. The heat is still in there. The full twenty.", "20 MINUTES UNDER THE TAP")
		if cool_t >= COOL_LEN:
			step_done.emit()
	saved = clampf(saved, 0.05, 0.97)
	hud.set_meter(saved)
	if auto and not fired and phase == "pick" and since() > 0.25:
		fired = true
		var left: Array = []
		for it: Dictionary in ITEMS:
			if not tried.has(it["id"]):
				left.append(it["id"])
		picked.emit(left[randi() % left.size()] if randf() < 0.5 else "tap")


func _take_watch() -> void:
	if watch_on:
		watch_on = false
		watch_t = t
		Sfx.play("good")


func press(p: Vector2) -> void:
	if phase == "pick":
		for it: Dictionary in ITEMS:
			var r: Rect2 = it["rect"]
			if r.has_point(p) and not tried.has(it["id"]):
				fired = true
				picked.emit(it["id"])
				return
	elif cooling:
		if BTN_COLD.has_point(p):
			cold = true
		elif BTN_WARM.has_point(p):
			warm = true
		elif p.distance_to(WATCH) < 60.0:
			_take_watch()


func release(_p: Vector2) -> void:
	cold = false
	warm = false


func key(code: int, down: bool) -> void:
	if code == KEY_LEFT or code == KEY_A:
		key_cold = down
	elif code == KEY_RIGHT or code == KEY_D:
		key_warm = down


# ---------------------------------------------------------------- drawing

func _draw() -> void:
	if view == "kitchen":
		_draw_kitchen()
	else:
		_draw_sink()


func _tiles(col: Color, line: Color) -> void:
	draw_rect(Rect2(0, 0, 1280, 720), col)
	for i in 22:
		draw_line(Vector2(i * 64, 0), Vector2(i * 64, 720), line, 2.0)
	for j in 12:
		draw_line(Vector2(0, j * 64), Vector2(1280, j * 64), line, 2.0)


func _draw_kitchen() -> void:
	_tiles(Color("e4efe9"), Color("d5e4dc"))
	# shelf with the "remedies"
	Art.rrect(self, Rect2(120, 262, 500, 16), Color("9a7653"), 6)
	draw_rect(Rect2(150, 278, 10, 26), Color("7a5c40"))
	draw_rect(Rect2(580, 278, 10, 26), Color("7a5c40"))
	# ice pack
	Art.rrect(self, Rect2(164, 196, 92, 66), Color("8ec5e6"), 14)
	Art.rrect(self, Rect2(172, 204, 76, 50), Color("b9def2"), 10)
	for i in 3:
		var a := i * PI / 3.0
		draw_line(Vector2(210, 229) - Vector2(cos(a), sin(a)) * 16.0, Vector2(210, 229) + Vector2(cos(a), sin(a)) * 16.0, Color.WHITE, 3.0, true)
	# butter
	Art.rrect(self, Rect2(312, 250, 106, 12), Color("f4f6f8"), 6)
	Art.rrect(self, Rect2(326, 214, 78, 38), Color("f6d76a"), 8)
	Art.rrect(self, Rect2(326, 214, 78, 12), Color("fbe58e"), 6)
	# toothpaste
	draw_set_transform(Vector2(525, 240), -0.12, Vector2.ONE)
	Art.rrect(self, Rect2(-52, -16, 84, 34), Color("f4f6f8"), 8)
	draw_rect(Rect2(-30, -16, 22, 34), Art.TEAL)
	Art.rrect(self, Rect2(30, -9, 16, 20), Color("d9dee4"), 4)
	Art.rrect(self, Rect2(44, -12, 12, 26), Art.CORAL, 4)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	# tap over the sink
	_draw_tap(Vector2(790, 300), 1.0, false)
	# counter
	draw_rect(Rect2(0, 440, 1280, 34), Color("c9a27c"))
	draw_rect(Rect2(0, 474, 1280, 246), Color("f4efe6"))
	Art.rrect(self, Rect2(696, 430, 190, 22), Color("aebbc2"), 8)
	for i in 4:
		Art.rrect(self, Rect2(60 + i * 310, 500, 270, 200), Color("ebe4d8"), 10)
		Art.rrect(self, Rect2(170 + i * 310, 520, 50, 10), Color("b9ad9b"), 5)
	# stove + pot
	Art.rrect(self, Rect2(960, 424, 250, 20), Color("39424e"), 6)
	Art.oval(self, Vector2(1020, 432), Vector2(40, 6), Color("e5533d"))
	var spilled := phase != "cook"
	if spilled:
		draw_set_transform(Vector2(1120, 420), 1.2, Vector2.ONE)
	else:
		draw_set_transform(Vector2(1020, 388 + sin(t * 9.0) * 1.5), 0.0, Vector2.ONE)
	Art.rrect(self, Rect2(-52, -40, 104, 80), Color("8f9aa3"), 12)
	Art.rrect(self, Rect2(-70, -30, 22, 10), Color("39424e"), 4)
	Art.rrect(self, Rect2(48, -30, 22, 10), Color("39424e"), 4)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	if spilled:
		Art.oval(self, Vector2(1130, 448), Vector2(120, 9), Color(0.75, 0.88, 0.95, 0.8))
	for i in 3:
		var ph := fmod(t * 0.5 + i * 0.33, 1.0)
		var sx := (1000.0 if not spilled else 1100.0) + i * 22.0
		draw_arc(Vector2(sx, 360 - ph * 70.0), 10.0, -0.5 * PI, 0.5 * PI, 8, Color(1, 1, 1, 0.7 * (1.0 - ph)), 4.0, true)

	# Sam
	var sp := Vector2(1010, 640) if phase == "cook" else Vector2(930, 640)
	var pose := {"rh": Vector2(46, -150), "lh": Vector2(-10, -150), "face": {"smile": 0.6, "gaze": Vector2(2, 2)}}
	if spilled:
		var hop := absf(sin(t * 9.0)) * 10.0 if phase != "covered" else 0.0
		sp.y -= hop
		pose = {"rh": Vector2(66, -170), "lh": Vector2(34, -150), "face": {"mouth": "open", "brow": 1.0, "eyes": "wide"}}
		if phase == "covered":
			pose["face"] = {"smile": 0.4, "brow": 0.3}
	Art.person(self, sp, 1.25, sam, pose)
	if spilled:
		var hand := sp + Vector2(66, -170) * 1.25
		var el := sp + Vector2(60, -132) * 1.25
		Art.limb(self, el + Vector2(2, 4), hand + Vector2(0, 8), 20, Color("d8452f") if not covered else Color(0.9, 0.95, 1.0, 0.9))
	draw_rect(Rect2(0, 440, 640, 34), Color("c9a27c"))

	# clickable remedies
	if phase == "pick":
		for it: Dictionary in ITEMS:
			var r: Rect2 = it["rect"]
			var id: String = it["id"]
			if tried.has(id):
				Art.cross(self, r.get_center(), 70.0, Art.CORAL, 9.0)
				continue
			var hov := r.has_point(mouse)
			var pul := 0.5 + 0.5 * sin(t * 4.0 + r.position.x * 0.01)
			draw_rect(r.grow(4.0 + pul * 3.0), Color(Art.CORAL, 0.9 if hov else 0.3 + 0.2 * pul), false, 3.0)
			var lw := Art.text_w(it["name"], 15, true) + 24.0
			Art.rrect(self, Rect2(r.get_center().x - lw * 0.5, r.end.y + 12, lw, 28), Art.INK if hov else Color(Art.INK, 0.75), 14)
			Art.text_c(self, Vector2(r.get_center().x, r.end.y + 26), it["name"], 15, Color.WHITE, true)
	else:
		for it: Dictionary in ITEMS:
			if tried.has(it["id"]):
				var r2: Rect2 = it["rect"]
				Art.cross(self, r2.get_center(), 70.0, Art.CORAL, 9.0)


func _draw_tap(p: Vector2, s: float, running: bool) -> void:
	var steel := Color("9aa7b0")
	draw_set_transform(p, 0.0, Vector2(s, s))
	Art.rrect(self, Rect2(-16, 40, 32, 100), steel, 8)
	Art.rrect(self, Rect2(-16, 20, 110, 30), steel, 14)
	Art.rrect(self, Rect2(70, 20, 26, 58), steel, 10)
	Art.rrect(self, Rect2(-50, 4, 60, 18), Color("5b8fd0"), 9)
	if running:
		pass
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _draw_sink() -> void:
	_tiles(Color("e4efe9"), Color("d5e4dc"))
	# basin
	Art.rrect(self, Rect2(300, 300, 760, 500), Color("b7c3ca"), 60)
	Art.rrect(self, Rect2(330, 330, 700, 480), Color("d3dce1"), 50)
	Art.disc(self, Vector2(640, 560), 26, Color("8f9aa3"))
	# tap + stream
	_draw_tap(Vector2(560, 20), 1.6, true)
	var cool_col := Color("9fd6f2")
	var stream := Color("d8f1fb").lerp(cool_col, clampf(temp * 2.0, 0.0, 1.0)).lerp(Color("f2c9b4"), clampf((temp - 0.6) * 2.5, 0.0, 1.0))
	var sx := 560.0 + 83.0 * 1.6
	Art.rrect(self, Rect2(sx - 22, 140, 44, 222), Color(stream, 0.85), 16)
	for i in 5:
		var ph := fmod(t * 2.4 + i * 0.2, 1.0)
		draw_line(Vector2(sx - 12 + i * 6, 150 + ph * 180.0), Vector2(sx - 12 + i * 6, 172 + ph * 180.0), Color(1, 1, 1, 0.7), 2.5, true)
	if temp > 0.72:
		for i in 3:
			var ph2 := fmod(t * 0.6 + i * 0.33, 1.0)
			draw_arc(Vector2(sx + 50 + i * 20, 300 - ph2 * 80.0), 12.0, -0.5 * PI, 0.5 * PI, 8, Color(1, 1, 1, 0.8 * (1.0 - ph2)), 4.0, true)
	if temp < 0.28:
		for i in 4:
			var a := t * 0.7 + i * 1.6
			Art.star(self, Vector2(sx + 60 + cos(a) * 26.0 + i * 8, 250 + sin(a * 1.3) * 60.0), 7.0, Color(1, 1, 1, 0.9))

	# forearm
	var skin: Color = sam["skin"]
	var prog := clampf(cool_t / COOL_LEN, 0.0, 1.0)
	Art.limb(self, Vector2(60, 420), Vector2(240, 410), 180, sam["top"])
	Art.limb(self, Vector2(240, 408), Vector2(790, 396), 150, skin)
	Art.oval(self, Vector2(880, 392), Vector2(80, 68), skin)
	for i in 4:
		Art.limb(self, Vector2(930, 352 + i * 28), Vector2(1006 - absf(i - 1.5) * 10.0, 346 + i * 31), 26, skin)
	Art.limb(self, Vector2(870, 344), Vector2(912, 300), 26, skin)
	# the burn
	var red := Color(0.86, 0.22, 0.16, lerpf(0.72, 0.36, prog))
	Art.oval(self, Vector2(560, 400), Vector2(190, 62), red, -0.02)
	Art.oval(self, Vector2(520, 392), Vector2(90, 34), Color(red, red.a * 0.8), 0.1)
	if covered or phase == "covered":
		Art.rrect(self, Rect2(360, 322, 400, 160), Color(0.9, 0.96, 1.0, 0.55), 20)
	# splash
	for i in 6:
		var ph3 := fmod(t * 1.8 + i * 0.17, 1.0)
		var dirx := (i - 2.5) * 26.0
		Art.disc(self, Vector2(sx + dirx * ph3 * 2.0, 352 - sin(ph3 * PI) * 30.0), 6.0 * (1.0 - ph3), Color(stream, 0.9))
	# watch
	if watch_on:
		var swell := smoothstep(0.5, 1.0, prog)
		Art.rrect(self, Rect2(WATCH.x - 20, WATCH.y - 80, 40, 160), Color("39424e"), 10)
		Art.disc(self, WATCH, 34, Color("22303f"))
		Art.disc(self, WATCH, 27, Color("f4f6f8"))
		draw_line(WATCH, WATCH + Vector2(0, -18), Art.INK, 3.0, true)
		draw_line(WATCH, WATCH + Vector2(12, 6), Art.INK, 3.0, true)
		if cooling:
			var pul := fmod(t * 1.2, 1.0)
			Art.ring(self, WATCH, 40.0 + pul * 22.0, Color(Art.CORAL, (1.0 - pul) * (0.5 + swell * 0.5)), 4.0)
	elif t - watch_t < 0.6:
		var k := (t - watch_t) / 0.6
		Art.disc(self, WATCH + Vector2(k * 160.0, -k * 220.0 + k * k * 120.0), 27 * (1.0 - k * 0.5), Color("f4f6f8"))
	if not watch_on and t - watch_t < 2.2 and cooling:
		Art.card(self, Rect2(WATCH.x - 96, WATCH.y - 150, 192, 46), Art.TEAL, 23)
		Art.text_c(self, Vector2(WATCH.x, WATCH.y - 127), "Watch off. Good.", 17, Color.WHITE, true)

	# temperature card
	var r := Rect2(44, 90, 372, 226)
	Art.card(self, r)
	Art.text(self, Vector2(74, 130), "WATER TEMPERATURE", 14, Art.INK_SOFT, true)
	var bar := Rect2(74, 150, 312, 30)
	Art.rrect(self, bar, Color("cfe6f5"), 12)
	Art.rrect(self, Rect2(bar.position.x + bar.size.x * ZONE_HI, bar.position.y, bar.size.x * (1.0 - ZONE_HI), 30), Color("f3c3b0"), 12)
	Art.rrect(self, Rect2(bar.position.x + bar.size.x * ZONE_LO, bar.position.y, bar.size.x * (ZONE_HI - ZONE_LO), 30), Art.TEAL, 4)
	var nx := bar.position.x + bar.size.x * temp
	Art.rrect(self, Rect2(nx - 6, bar.position.y - 8, 12, 46), Art.INK, 6)
	Art.text(self, Vector2(78, 210), "icy", 14, Art.INK_SOFT)
	Art.text_c(self, Vector2(230, 204), "COOL", 14, Art.TEAL, true)
	Art.text(self, Vector2(346, 210), "warm", 14, Art.INK_SOFT)
	for b in 2:
		var br: Rect2 = BTN_COLD if b == 0 else BTN_WARM
		var on := (cold or key_cold) if b == 0 else (warm or key_warm)
		var hov := br.has_point(mouse)
		var col := Color("5b8fd0") if b == 0 else Color("e0795a")
		Art.rrect(self, br, col.darkened(0.2) if on else (col.lightened(0.12) if hov else col), 16)
		Art.text_c(self, br.get_center(), "<  COLDER" if b == 0 else "WARMER  >", 17, Color.WHITE, true)

	# the 20-minute clock
	var cc := Vector2(1140, 200)
	Art.card(self, Rect2(1040, 90, 200, 240))
	Art.disc(self, cc, 70, Color(Art.INK, 0.08))
	if prog > 0.005:
		var pts := PackedVector2Array([cc])
		var steps := int(48 * prog) + 2
		for i in steps:
			var a2 := -PI / 2.0 + TAU * prog * i / float(steps - 1)
			pts.append(cc + Vector2(cos(a2), sin(a2)) * 70.0)
		if pts.size() >= 3:
			draw_colored_polygon(pts, Art.TEAL)
	Art.disc(self, cc, 46, Art.PAPER)
	Art.text_c(self, cc + Vector2(0, -6), "%d" % int(prog * 20.0), 34, Art.INK, true)
	Art.text_c(self, cc + Vector2(0, 22), "min", 14, Art.INK_SOFT)
	Art.text_c(self, Vector2(1140, 300), "of 20 minutes", 15, Art.INK_SOFT)
	if asked_stop and cool_t < COOL_LEN * 0.35 + 4.0:
		Art.bubble(self, Vector2(60, 590), "It's stopped hurting. Can we stop?", 19, false, 300.0, 1.0, 150.0)
