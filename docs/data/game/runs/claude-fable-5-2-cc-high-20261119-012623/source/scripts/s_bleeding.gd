extends "res://scripts/scenario.gd"
## 17:15 - The Ride Home. Severe bleeding: press hard, add don't lift, don't let go.

const W := Vector2(450, 330)            # the wound in the close view
const NEED := 25.0

var view := "street"
var bleeding := false
var loss := 0.0
var pressure := 0.0
var hold_mouse := false
var hold_key := false
var held := 0.0
var hold_total := 0.0
var goal := 999.0
var sim := false
var cloths := 0
var soak := 0.0
var soak2 := 0.0
var hurt_t := -10.0
var no_peek_t := -10.0

var rider := {"skin": Art.SKINS[3], "hair": Art.HAIRS[4], "style": 0, "top": Color("2f8fb0"), "legs": Color("242c38"), "sleeves": false}
var helper := {"skin": Art.SKINS[0], "hair": Art.HAIRS[1], "style": 1, "top": Color("c9a7d8"), "legs": Color("4a5a70")}
var medic := {"skin": Art.SKINS[1], "hair": Art.HAIRS[2], "style": 2, "top": Color("2d6e5e"), "legs": Color("2d6e5e"), "stripe": Color("e9f26a")}


func run() -> void:
	hud.set_title("17:15  ·  The Ride Home")
	hud.chosen.connect(_on_choice)
	hud.hide_panel()
	set_phase("ride")
	await pause(1.5)
	Sfx.play("thud")
	Sfx.play("crack")
	set_phase("crash")
	await pause(1.3)
	await say("A cyclist clips the kerb and comes down hard on a broken bottle. He sits up, staring at his forearm. It's laid open — and bright blood is pumping out in spurts.")
	hud.show_meter("HIS CHANCES")
	bleeding = true
	await quiz("Seconds count. What first?", [
		{"t": "Press hard on the wound with your scarf — right now", "ok": true},
		{"t": "Rinse the wound clean first", "ok": false, "fb": "Cleaning is for small cuts. This is bleeding that can kill: the only thing that matters right now is stopping it. Press."},
		{"t": "Run to the pharmacy for a first-aid kit", "ok": false, "fb": "By the time you're back he may have lost litres. Use what you have — a scarf, a T-shirt, your bare hands. Press."},
		{"t": "Call %s and wait with him" % number, "ok": false, "fb": "Calling is right — waiting isn't. He can bleed out before they arrive. Get someone else to call, or put your phone on speaker, and press."},
	])
	set_phase("point")
	await say("You point at a woman on the pavement: “You — call %s!” Then you fold your scarf into a pad and go straight for the wound.\n(If you had gloves or a plastic bag, you'd put them between you and the blood.)" % number)

	view = "close"
	cloths = 1
	sim = true
	set_phase("hold")
	goal = 6.5
	hud.instruct("Press and HOLD on the wound — click and keep holding, or hold SPACE. Hard, steady pressure.", "DIRECT PRESSURE")
	await step_done
	hurt_t = t
	set_phase("hold")
	goal = 12.0
	hud.instruct("“Aah — stop, that hurts!”  It will hurt. Pressure is what's keeping him alive. Keep pressing; keep talking to him.", "DON'T LET GO")
	await step_done
	sim = false
	await quiz("Blood has soaked right through the scarf. A passer-by holds out a clean T-shirt.", [
		{"t": "Put it on top of the scarf and press harder", "ok": true, "fb": "Add, never remove. More padding, more pressure — and the clot forming underneath stays where it is."},
		{"t": "Take the soaked scarf off and swap it for the clean shirt", "ok": false, "fb": "Lifting the scarf tears away the clot that has started to form, and the bleeding begins again. Leave it. Add on top, press harder."},
	])
	cloths = 2
	sim = true
	set_phase("hold_peek")
	goal = 19.0
	hud.instruct("Back on it. Firm and steady. The bleeding seems to be slowing…", "DIRECT PRESSURE", ["Lift the cloth for a quick look — has it stopped?"])
	var r: String = await picked
	if r == "peek":
		sim = false
		loss += 0.1
		await bad("Don't peek. Every time you lift, you break the seal and the clot, and it starts again. Keep the pressure on until someone with proper kit takes over.")
		sim = true
	else:
		no_peek_t = t
		Sfx.play("good")
	set_phase("hold")
	goal = NEED
	hud.instruct("You didn't lift it. Good. Hold on — help is nearly here." if r != "peek" else "Back on it. Hold on — help is nearly here.", "DON'T LET GO")
	await step_done
	sim = false
	await quiz("He's gone pale and clammy. “I feel dizzy…” You keep pressing — and?", [
		{"t": "Lay him down, keep him warm, keep talking to him", "ok": true, "fb": "He's going into shock from blood loss. Lying flat keeps blood going to his brain; a coat over him keeps him warm; your voice keeps him calm."},
		{"t": "Give him some water or something sweet", "ok": false, "fb": "Nothing to eat or drink: he may need surgery, and he could choke if he passes out. Lay him down and keep him warm."},
		{"t": "Get him on his feet to walk it off", "ok": false, "fb": "Standing sends what blood he has left to his legs — he'll faint. Lay him down and keep him warm."},
	])
	Sfx.play("siren")
	skill = clampf((held / maxf(hold_total, 1.0) - 0.5) / 0.35, 0.0, 1.0)
	view = "street"
	set_phase("end")
	hud.hide_panel()
	await pause(1.8)
	await say("The paramedics kneel down. “Don't let go until I say… and — now.” A proper pressure dressing goes on in seconds.\n“Good hands. A cut like that, most people just stand there.”\n\n(If an arm or leg won't stop bleeding under pressure, a tourniquet above the wound saves lives. A course will show you how.)")
	if loss < 0.45:
		finish("The bleeding stopped under your hands.", "You went straight to pressure, added instead of lifting, and didn't let go when it got uncomfortable.")
	else:
		finish("He's alive — and a lot paler.", "He lost more blood than he needed to. With bleeding like this, every second off the wound counts. Press at once, and don't let up.")


func on_mistake() -> void:
	loss += 0.07


func _on_choice(_i: int) -> void:
	if phase == "hold_peek" and hud.mode == "instruct":
		fired = true
		picked.emit("peek")


func tick(delta: float) -> void:
	if bleeding and not sim and hud.waiting():
		loss += 0.006 * delta
	if sim:
		var on := hold_mouse or hold_key or (auto and fmod(t, 5.0) > 0.4)
		pressure = move_toward(pressure, 1.0 if on else 0.0, delta * (3.2 if on else 1.7))
		hold_total += delta
		if pressure > 0.75:
			held += delta
			soak = minf(soak + delta * 0.09, 1.0)
			if cloths > 1:
				soak2 = minf(soak2 + delta * 0.035, 0.5)
		else:
			loss += delta * 0.035 * (1.0 - pressure)
			soak = minf(soak + delta * 0.2, 1.0)
		if held >= goal:
			goal = 999.0
			fired = true
			if phase == "hold_peek":
				picked.emit("ok")
			else:
				step_done.emit()
	else:
		pressure = move_toward(pressure, 0.6, delta)
	loss = clampf(loss, 0.0, 0.92)
	hud.set_meter(0.95 - loss)
	if auto and not fired and phase == "hold_peek" and since() > 0.3 and randf() < 0.01:
		fired = true
		picked.emit("peek")


func press(p: Vector2) -> void:
	if sim and p.distance_to(W) < 150.0:
		hold_mouse = true


func release(_p: Vector2) -> void:
	hold_mouse = false


func key(code: int, down: bool) -> void:
	if code == KEY_SPACE or code == KEY_ENTER:
		hold_key = down and sim


# ---------------------------------------------------------------- drawing

func _draw() -> void:
	if view == "street":
		_draw_street()
	else:
		_draw_close()


func _building(x: float, w: float, h: float, col: Color) -> void:
	draw_rect(Rect2(x, 400 - h, w, h), col)
	var cols := int(w / 56.0)
	var rows := int(h / 70.0)
	for i in cols:
		for j in rows:
			var lit := (i * 7 + j * 3 + int(x)) % 4 == 0
			Art.rrect(self, Rect2(x + 18 + i * 56, 400 - h + 22 + j * 66, 28, 38), Color("ffe6a3") if lit else col.darkened(0.14), 4)


func _draw_bike(p: Vector2, rot: float) -> void:
	draw_set_transform(p, rot, Vector2.ONE)
	Art.ring(self, Vector2(-62, 0), 40.0, Art.INK, 6.0)
	Art.ring(self, Vector2(62, 0), 40.0, Art.INK, 6.0)
	draw_polyline(PackedVector2Array([Vector2(-62, 0), Vector2(-18, -58), Vector2(44, -58), Vector2(0, 0), Vector2(-62, 0)]), Art.CORAL, 6.0, true)
	draw_line(Vector2(0, 0), Vector2(-18, -58), Art.CORAL, 6.0, true)
	draw_line(Vector2(44, -58), Vector2(62, 0), Art.CORAL, 6.0, true)
	draw_line(Vector2(44, -58), Vector2(38, -80), Art.INK, 5.0, true)
	draw_line(Vector2(26, -84), Vector2(54, -76), Art.INK, 6.0, true)
	Art.rrect(self, Rect2(-34, -70, 34, 9), Art.INK, 4)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _draw_street() -> void:
	draw_rect(Rect2(0, 0, 1280, 720), Color("f6d9b8"))
	Art.disc(self, Vector2(240, 250), 70, Color("f9c98d"))
	_building(0, 250, 300, Color("d9a58a"))
	_building(250, 200, 220, Color("b8a2c2"))
	_building(450, 300, 330, Color("e0b77f"))
	_building(750, 220, 250, Color("9fb7c4"))
	_building(970, 310, 310, Color("c9907a"))
	Art.rrect(self, Rect2(790, 330, 120, 70), Color("f4efe6"), 6)
	Art.rrect(self, Rect2(780, 318, 140, 18), Art.TEAL, 6)
	draw_rect(Rect2(843, 346, 14, 38), Art.TEAL)
	draw_rect(Rect2(831, 358, 38, 14), Art.TEAL)
	draw_rect(Rect2(0, 400, 1280, 70), Color("d5cfc6"))
	draw_rect(Rect2(0, 466, 1280, 10), Color("b5aea4"))
	draw_rect(Rect2(0, 476, 1280, 244), Color("6c7480"))
	for i in 8:
		draw_rect(Rect2(i * 180 - 20, 640, 90, 8), Color(1, 1, 1, 0.5))

	# the helper on the pavement
	var hp := Vector2(960, 462)
	var hpose := {"face": {"gaze": Vector2(-3, 1.5), "brow": 0.8, "smile": -0.3}}
	if phase == "point" or phase == "end":
		hpose["rh"] = Vector2(26, -214)
	Art.person(self, hp, 0.85, helper, hpose)
	if phase == "point":
		Art.bubble(self, hp + Vector2(0, -222), "Calling %s!" % number, 17, false, 180.0)

	if phase == "ride":
		var k := clampf(since() / 1.5, 0.0, 1.0)
		var bx := lerpf(-140.0, 470.0, k)
		_draw_bike(Vector2(bx, 520), 0.0)
		Art.person(self, Vector2(bx - 8, 500), 0.8, rider, {"lf": Vector2(-8, -30), "rf": Vector2(14, -50), "lh": Vector2(20, -130), "rh": Vector2(42, -126), "rot": 0.2, "face": {"gaze": Vector2(3, 0)}})
		return
	# broken bottle
	for i in 5:
		var gp := Vector2(590 + i * 17, 500 + (i % 2) * 9)
		Art.poly(self, PackedVector2Array([gp, gp + Vector2(11, -5), gp + Vector2(7, 7)]), Color("5fae7a"))
	_draw_bike(Vector2(380, 560), -1.25)
	# blood on the road
	var pool := 20.0 + loss * 160.0
	if phase != "end":
		Art.oval(self, Vector2(650, 566), Vector2(pool, pool * 0.22), Art.BLOOD)
	else:
		Art.oval(self, Vector2(650, 566), Vector2(pool, pool * 0.22), Art.BLOOD.darkened(0.25))
	# the rider, sitting
	var rp := Vector2(620, 600)
	var fresh := phase == "crash" or phase == "point"
	var rpose := {"lf": Vector2(-34, -72), "rf": Vector2(34, -72), "rh": Vector2(26, -120), "lh": Vector2(18, -112),
		"face": {"brow": 1.0, "smile": -0.7, "eyes": "wide" if fresh else "open", "gaze": Vector2(2, 3)}}
	Art.person(self, rp, 1.0, rider, rpose)
	if fresh:
		var spurt := fmod(t * 1.8, 1.0)
		Art.disc(self, rp + Vector2(30, -120), 12.0, Art.BLOOD)
		Art.disc(self, rp + Vector2(34 + spurt * 22.0, -116 + spurt * spurt * 60.0), 5.0 * (1.0 - spurt) + 2.0, Art.BLOOD)
		draw_line(rp + Vector2(30, -112), rp + Vector2(32, -80), Art.BLOOD, 5.0, true)
	else:
		Art.rrect(self, Rect2(rp.x + 6, rp.y - 136, 46, 32), Color("f2efe9"), 8)
		draw_rect(Rect2(rp.x + 6, rp.y - 124, 46, 6), Art.CORAL)
	if phase == "end":
		Art.ambulance(self, Vector2(1060.0 + maxf(1.0 - since(), 0.0) * 460.0, 640), 1.1, t)
		Art.person(self, Vector2(740, 640), 0.95, medic, {"lf": Vector2(-22, -66), "rf": Vector2(22, -66), "lh": Vector2(-60, -130), "rh": Vector2(-20, -100), "face": {"gaze": Vector2(-3, 1), "smile": 0.5}})


func _draw_close() -> void:
	draw_rect(Rect2(0, 0, 1280, 720), Color("d7d2ca"))
	draw_rect(Rect2(0, 0, 1280, 96), Color("b9b2a8"))
	for i in 5:
		draw_line(Vector2(i * 300 + 60, 96), Vector2(i * 300 - 20, 720), Color("cbc5bb"), 3.0)
	# blood pooling under the arm
	var pool := 26.0 + loss * 300.0
	Art.oval(self, W + Vector2(10, 150), Vector2(pool * 1.5, pool * 0.42), Art.BLOOD)
	# forearm
	var skin: Color = rider["skin"]
	Art.oval(self, W + Vector2(0, 104), Vector2(400, 20), Color(0, 0, 0, 0.1))
	Art.limb(self, Vector2(40, 372), Vector2(250, 352), 196, rider["top"])
	Art.limb(self, Vector2(250, 350), Vector2(730, 318), 168, skin)
	Art.oval(self, Vector2(812, 312), Vector2(86, 74), skin)
	for i in 4:
		Art.limb(self, Vector2(860, 270 + i * 30), Vector2(942 - absf(i - 1.5) * 12.0, 262 + i * 34), 28, skin)
	Art.limb(self, Vector2(800, 262), Vector2(846, 214), 28, skin)
	# the wound
	Art.oval(self, W, Vector2(74, 20), Art.BLOOD.darkened(0.15), -0.08)
	Art.oval(self, W, Vector2(60, 9), Color("5d0f15"), -0.08)
	if cloths == 0 or pressure < 0.4:
		for i in 3:
			var ph := fmod(t * 1.5 + i * 0.33, 1.0)
			var dp := W + Vector2(-40 + i * 40, 30 + ph * 110.0)
			Art.drop(self, dp, 9.0 * (1.0 - pressure * 0.8), Art.BLOOD)
	# cloths
	if cloths >= 1:
		var c1 := Color("e2b23a").lerp(Art.BLOOD, soak * 0.85)
		Art.rrect(self, Rect2(W.x - 108, W.y - 76, 216, 152), c1.darkened(0.1), 20)
		Art.rrect(self, Rect2(W.x - 104, W.y - 72, 208, 140), c1, 18)
		for i in 4:
			draw_line(Vector2(W.x - 104, W.y - 46 + i * 30), Vector2(W.x + 104, W.y - 46 + i * 30), c1.darkened(0.12), 3.0)
	if cloths >= 2:
		var c2 := Color("f4f2ee").lerp(Art.BLOOD, soak2)
		draw_set_transform(W, 0.12, Vector2.ONE)
		Art.rrect(self, Rect2(-92, -66, 184, 132), c2.darkened(0.08), 18)
		Art.rrect(self, Rect2(-88, -62, 176, 122), c2, 16)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	# your hand
	if phase.begins_with("hold") or not sim:
		if pressure > 0.04 or hold_mouse or hold_key:
			var k := 1.0 - pressure * 0.07
			var hp := W + Vector2(4, 8)
			Art.disc(self, hp, 96.0, Color(0, 0, 0, 0.06 + 0.1 * pressure))
			Art.limb(self, hp + Vector2(60, 400), hp + Vector2(20, 70), 84, Art.CORAL)
			var ys := Art.SKINS[2]
			Art.oval(self, hp, Vector2(74, 66) * k, ys)
			for i in 4:
				Art.limb(self, hp + Vector2(-48 + i * 30, -40) * k, hp + Vector2(-66 + i * 40, -106 + absf(i - 1.5) * 12.0) * k, 26 * k, ys)
			Art.limb(self, hp + Vector2(-62, 10) * k, hp + Vector2(-106, -22) * k, 28 * k, ys)
		elif sim:
			var pul := fmod(t * 1.3, 1.0)
			Art.ring(self, W, 60.0 + pul * 50.0, Color(Art.CORAL, 1.0 - pul), 5.0)
			Art.rrect(self, Rect2(W.x - 84, W.y - 18, 168, 36), Art.INK, 18)
			Art.text_c(self, W, "PRESS AND HOLD", 16, Color.WHITE, true)

	# his face, top-left
	var fc := Vector2(128, 190)
	Art.disc(self, fc, 70, Color("f4efe6"))
	var grim := clampf(1.0 - held / NEED, 0.0, 1.0)
	Art.head(self, Transform2D(0.0, Vector2(1.9, 1.9), 0.0, fc + Vector2(0, 6)), rider, {"brow": 1.0, "smile": -0.4 - 0.4 * grim, "gaze": Vector2(2, 2), "tint": Color(0.92, 0.92, 0.88, clampf(loss * 0.9, 0.0, 0.5))})
	if t - hurt_t < 4.0:
		Art.bubble(self, fc + Vector2(40, -64), "Aah — stop, that hurts!", 19, false, 260.0, clampf((t - hurt_t) * 5.0, 0.0, 1.0), 100.0)
	if t - no_peek_t < 2.5:
		Art.card(self, Rect2(W.x - 150, W.y - 190, 300, 54), Art.TEAL, 27)
		Art.check(self, Vector2(W.x - 116, W.y - 163), 22, Color.WHITE, 4.0)
		Art.text(self, Vector2(W.x - 90, W.y - 156), "You didn't lift it. Good.", 19, Color.WHITE, true)

	# gauge card
	var r := Rect2(980, 96, 260, 420)
	Art.card(self, r)
	Art.text(self, Vector2(1008, 140), "PRESSURE", 14, Art.INK_SOFT, true)
	var bar := Rect2(1008, 158, 56, 250)
	Art.rrect(self, bar, Color(Art.INK, 0.1), 14)
	Art.rrect(self, Rect2(bar.position, Vector2(56, 250 * 0.25)), Color(Art.TEAL, 0.28), 14)
	var fill := 250.0 * pressure
	if fill > 4.0:
		Art.rrect(self, Rect2(bar.position.x, bar.end.y - maxf(fill, 20.0), 56, maxf(fill, 20.0)), Art.TEAL if pressure > 0.75 else Art.AMBER, 14)
	Art.text(self, Vector2(1078, 192), "FIRM", 15, Art.TEAL, true)
	Art.text(self, Vector2(1078, 214), "keep it here", 14, Art.INK_SOFT)
	Art.text(self, Vector2(1078, 400), "none", 14, Art.INK_SOFT)
	if sim and pressure < 0.75:
		Art.text(self, Vector2(1078, 300), "He's", 17, Art.CORAL, true)
		Art.text(self, Vector2(1078, 322), "bleeding!", 17, Art.CORAL, true)
	Art.text(self, Vector2(1008, 450), "Ambulance on its way", 14, Art.INK_SOFT)
	Art.rrect(self, Rect2(1008, 462, 204, 10), Color(Art.INK, 0.1), 5)
	Art.rrect(self, Rect2(1008, 462, maxf(204.0 * clampf(held / NEED, 0.0, 1.0), 10.0), 10), Art.TEAL, 5)
