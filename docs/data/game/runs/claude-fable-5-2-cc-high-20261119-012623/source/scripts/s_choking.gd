extends "res://scripts/scenario.gd"
## 12:30 - The Cafe. Choking: ask, back blows, abdominal thrusts, repeat.

const GROUND := 528.0
const H := Vector2(650, 376)            # the diner's hips
const ZONE_LO := 0.66
const ZONE_HI := 0.96

var chance := 0.92
var blocked := true
var lean := 0.06
var lean_to := 0.06
var you_x := -260.0
var you_to := -260.0
var blue := 0.0
var jolt := 0.0

var mode := ""              # "blows" / "thrusts"
var action_on := false
var hits := 0
var need := 5
var pop_at := -1
var strong_n := 0
var weak_n := 0
var marker_t := 0.0
var period := 1.25
var swing := -1.0
var swing_strong := false
var hit_pending := false
var round_done := false
var msg := ""
var msg_col := Art.TEAL
var msg_t := -10.0
var food_t := -10.0
var fist_set := false

var vic := {"skin": Art.SKINS[2], "hair": Art.HAIRS[0], "top": Color("3f7fb0"), "legs": Color("2b3340")}
var friend := {"skin": Art.SKINS[0], "hair": Art.HAIRS[5], "style": 6, "top": Color("d98fa8"), "legs": Art.INK}
var waiter := {"skin": Art.SKINS[3], "hair": Art.HAIRS[4], "style": 0, "top": Color("f2f0ea"), "legs": Color("1f2731")}


func run() -> void:
	hud.set_title("12:30  ·  The Café")
	set_phase("intro")
	hud.hide_panel()
	await pause(1.6)
	await say("Lunchtime. At the next table a woman is laughing with her mouth full — and then she isn't. She stands up, both hands at her throat. Her friend asks if she's all right. She doesn't answer.")
	hud.show_meter("HER CHANCES")
	await quiz("She isn't making a sound. Your first move?", [
		{"t": "Ask her: “Are you choking?”", "ok": true, "fb": "She nods, wild-eyed. She can't speak, can't cough, can't breathe: her airway is completely blocked, and she needs you now. (If she could cough hard, you'd just tell her to keep coughing.)"},
		{"t": "Hand her a glass of water", "ok": false, "fb": "Her airway is plugged — water can't get past, and may make it worse. Never give a drink to someone who is choking."},
		{"t": "Reach into her mouth and try to pull it out", "ok": false, "fb": "Fishing blind can push the food deeper. Only take something out if you can clearly see it."},
		{"t": "Give it a moment — she'll cough it up", "ok": false, "fb": "She can't cough. Silence means no air is moving at all. She has a few minutes before she blacks out."},
	])
	set_phase("step_in")
	you_to = H.x - 96.0
	await say("You point at the waiter: “You — call %s!” Then you step in behind her." % number)
	await quiz("How do you begin?", [
		{"t": "Lean her well forward and hit hard between the shoulder blades", "ok": true},
		{"t": "Pat her on the back while she stands upright", "ok": false, "fb": "Polite pats do nothing — and with her upright, the food can slip deeper. Lean her forward so gravity is on your side, and hit hard."},
		{"t": "Lay her down on the floor", "ok": false, "fb": "While she's conscious, keep her on her feet and leaning forward, so whatever comes loose falls out rather than back in."},
	])
	lean_to = 0.62
	await say("One hand supports her chest; she's bent well forward.\n\nNow give firm blows between her shoulder blades with the heel of your hand. Click (or press SPACE) when the marker is in the green — that's a blow with real force behind it.", "BACK BLOWS")
	await _round("blows", 5, -1)

	await quiz("Five firm back blows, and it's still stuck. Now?", [
		{"t": "Switch to abdominal thrusts", "ok": true},
		{"t": "Keep going with back blows until it comes out", "ok": false, "fb": "Back blows jolt; abdominal thrusts squeeze air up from below. They work differently — so if five of one fail, switch to five of the other."},
		{"t": "Stop and wait for the ambulance", "ok": false, "fb": "She'll be unconscious before it arrives. Don't stop."},
	])
	lean_to = 0.3
	you_to = H.x - 62.0
	mode = "thrusts"
	var asked := false
	while true:
		set_phase("fist")
		hud.instruct("Arms around her waist. Make a fist. Where does it go? Click the spot on her body." if not asked else "Try again — click where your fist should sit.", "ABDOMINAL THRUSTS")
		asked = true
		var p: Vector2 = await picked
		var dir := Vector2(sin(lean), -cos(lean))
		var u := (p - H).dot(dir)
		if u >= 14.0 and u <= 60.0:
			break
		elif u > 60.0:
			await bad("Too high — that's her ribs and breastbone. Your fist goes in the soft spot just above the navel, well below the ribs.")
		else:
			await bad("Too low. Just above the navel — between her belly button and the bottom of her ribs.")
	fist_set = true
	set_phase("fist_ok")
	await good("Just above the navel, below the ribs. Grab your fist with your other hand — then pull sharply inwards and upwards, as if trying to lift her off her feet.")
	await _round("thrusts", 5, -1)

	await say("Still stuck — and her lips are turning blue. Don't stop. Back to five back blows. Keep alternating, five and five, until it clears or help takes over.", "KEEP GOING")
	lean_to = 0.62
	you_to = H.x - 96.0
	period = 1.05
	await _round("blows", 5, 3)

	skill = clampf(float(strong_n) / maxf(float(strong_n + weak_n), 1.0) / 0.75, 0.0, 1.0)
	await pause(1.5)
	Sfx.play("good")
	await say("A lump of bread shoots out onto the floor. She drags in one huge, ragged breath — then another — and bursts into tears.")
	await quiz("She's breathing, talking, shaken. Are you done?", [
		{"t": "Not quite — she should see a doctor today", "ok": true, "fb": "Abdominal thrusts are forceful enough to bruise or injure organs, and bits of food can stay behind in the airway. Anyone who's had them should get checked."},
		{"t": "Yes. Sit her down and let her finish lunch", "ok": false, "fb": "She seems fine, but abdominal thrusts can cause internal injuries, and fragments can remain in the airway. She should be checked by a doctor today."},
	])
	await say("One more thing. If she had gone limp and unresponsive: lower her to the floor, make sure %s has been called, and start chest compressions — exactly as you did in the park." % number, "IF IT HADN'T WORKED")
	if chance > 0.45:
		finish("She's breathing again.", "You acted while everyone else was still wondering what was wrong. Firm blows, firm thrusts, no stopping.")
	else:
		finish("She's breathing again — just.", "It worked, but it took a long time and a lot of soft blows. These have to be hard: you are trying to knock something loose.")


func on_mistake() -> void:
	chance -= 0.06


func _round(kind: String, n: int, pop: int) -> void:
	mode = kind
	hits = 0
	need = n
	pop_at = pop
	round_done = false
	swing = -1.0
	marker_t = 0.0
	if kind == "blows":
		hud.instruct("Heel of your hand, between the shoulder blades. Click or press SPACE when the marker is in the green.", "BACK BLOWS — UP TO FIVE")
	else:
		hud.instruct("Sharp pull, inwards and upwards. Click or press SPACE when the marker is in the green.", "ABDOMINAL THRUSTS — UP TO FIVE")
	action_on = true
	set_phase("action")
	await step_done
	action_on = false


func _marker() -> float:
	var x := fposmod(marker_t / period, 1.0)
	return 1.0 - absf(2.0 * x - 1.0)


func _hit() -> void:
	if not action_on or round_done or swing >= 0.0:
		return
	var m := _marker()
	swing_strong = m >= ZONE_LO and m <= ZONE_HI
	swing = 0.0
	hit_pending = true


func tick(delta: float) -> void:
	lean = lerpf(lean, lean_to, 1.0 - exp(-6.0 * delta))
	you_x = lerpf(you_x, you_to, 1.0 - exp(-5.0 * delta))
	jolt = maxf(jolt - delta * 4.0, 0.0)
	if blocked:
		if action_on:
			chance -= 0.009 * delta
			blue = minf(blue + delta * 0.014, 0.5)
		elif hud.waiting():
			chance -= 0.004 * delta
			blue = minf(blue + delta * 0.008, 0.5)
	else:
		blue = maxf(blue - delta * 0.25, 0.0)
		chance = minf(chance + delta * 0.2, 0.95)
	chance = clampf(chance, 0.05, 0.97)
	hud.set_meter(chance)
	if action_on:
		marker_t += delta
		if auto and swing < 0.0 and not round_done:
			var m := _marker()
			if (m > 0.72 and m < 0.9) or randf() < 0.004:
				_hit()
	if swing >= 0.0:
		swing += delta / 0.46
		if hit_pending and swing >= 0.36:
			hit_pending = false
			_land()
		if swing >= 1.0:
			swing = -1.0
			if round_done:
				round_done = false
				step_done.emit()
	if auto and not fired and phase == "fist" and since() > 0.25:
		fired = true
		var dir := Vector2(sin(lean), -cos(lean))
		picked.emit(H + dir * (36.0 if randf() < 0.6 else randf_range(-10.0, 110.0)))


func _land() -> void:
	if swing_strong:
		hits += 1
		strong_n += 1
		jolt = 1.0
		Sfx.play("slap" if mode == "blows" else "thump")
		msg = "Firm!"
		msg_col = Art.TEAL
		if hits == pop_at:
			blocked = false
			food_t = t
			lean_to = 0.2
			Sfx.play("pop")
			round_done = true
		elif hits >= need:
			round_done = true
	else:
		weak_n += 1
		jolt = 0.3
		Sfx.play("soft")
		msg = "Too soft — put force behind it"
		msg_col = Art.AMBER
	msg_t = t


func press(p: Vector2) -> void:
	if action_on:
		_hit()
	elif phase == "fist":
		var dir := Vector2(sin(lean), -cos(lean))
		var fwd := Vector2(cos(lean), sin(lean))
		var d := p - H
		if absf(d.dot(fwd)) < 62.0 and d.dot(dir) > -40.0 and d.dot(dir) < 150.0:
			fired = true
			picked.emit(p)


func key(code: int, down: bool) -> void:
	if down and (code == KEY_SPACE or code == KEY_ENTER) and action_on:
		_hit()


# ---------------------------------------------------------------- drawing

func _draw() -> void:
	_draw_room()
	var dir := Vector2(sin(lean), -cos(lean))
	var fwd := Vector2(cos(lean), sin(lean))
	var jb := jolt * (1.0 if mode == "blows" else -0.7)
	var hip := H + fwd * jb * 3.0
	var sh := hip + dir * 118.0 + fwd * jb * 9.0
	var hd := sh + dir * 46.0 + fwd * 8.0

	# rescuer key points
	var yl := 0.14
	var ydir := Vector2(sin(yl), -cos(yl))
	var yhip := Vector2(you_x, H.y - 2.0)
	var ysh := yhip + ydir * 120.0
	var yhd := ysh + ydir * 46.0 + Vector2(6, 0)
	var back := hip + dir * 92.0 - fwd * 34.0
	var belly := hip + dir * 40.0 + fwd * 30.0
	var chest_front := hip + dir * 86.0 + fwd * 32.0
	var present := you_x > 300.0

	# waiter in the background
	var wp := Vector2(1020, 470)
	var wpose := {"face": {"gaze": Vector2(-2.5, 0.5), "brow": 0.7, "smile": -0.2}}
	if phase != "intro":
		wpose["rh"] = Vector2(26, -214)
	Art.person(self, wp, 0.78, waiter, wpose)
	if phase == "step_in":
		Art.bubble(self, wp + Vector2(0, -205), "Calling %s!" % number, 16, false, 180.0)

	# rescuer body
	if present or you_x > -200.0:
		Art.oval(self, Vector2(you_x, GROUND), Vector2(50, 9), Color(0, 0, 0, 0.12))
		Art.limb(self, yhip + Vector2(-6, 0), Vector2(you_x - 22, GROUND - 12), 27, Color("2f3b4c"))
		Art.limb(self, yhip + Vector2(6, 0), Vector2(you_x + 18, GROUND - 12), 27, Color("2f3b4c"))
		Art.oval(self, Vector2(you_x - 14, GROUND - 6), Vector2(20, 9), Color("1a2330"))
		Art.oval(self, Vector2(you_x + 26, GROUND - 6), Vector2(20, 9), Color("1a2330"))
		# far arm (drawn behind her)
		if mode == "thrusts" and (fist_set or phase == "fist"):
			_arm(ysh, belly + _thrust_off(dir, fwd), Art.CORAL.darkened(0.15), Art.SKINS[2], Vector2(0, 1))
		elif lean_to > 0.5:
			_arm(ysh, chest_front, Art.CORAL.darkened(0.15), Art.SKINS[2], Vector2(0, 1))
		Art.limb(self, yhip, ysh, 62, Art.CORAL)
		Art.disc(self, yhd + Vector2(-6, -5), 32, Art.HAIRS[0])
		Art.disc(self, yhd, 29, Art.SKINS[2])
		Art.disc(self, yhd + Vector2(29, 2), 5, Art.SKINS[2])
		Art.disc(self, yhd + Vector2(14, -3), 3.2, Art.INK)
		draw_line(yhd + Vector2(8, -12), yhd + Vector2(20, -10), Color(Art.INK, 0.7), 2.0, true)
		draw_line(yhd + Vector2(14, 14), yhd + Vector2(24, 13), Art.INK, 2.4, true)

	# the diner
	var skin: Color = vic["skin"]
	skin = skin.lerp(Color("7f93c9"), blue)
	var top: Color = vic["top"]
	Art.oval(self, Vector2(H.x + 6, GROUND), Vector2(54, 9), Color(0, 0, 0, 0.12))
	Art.limb(self, hip + Vector2(-6, 0), Vector2(H.x - 14, GROUND - 12), 27, vic["legs"])
	Art.limb(self, hip + Vector2(6, 0), Vector2(H.x + 22, GROUND - 12), 27, vic["legs"])
	Art.oval(self, Vector2(H.x - 6, GROUND - 6), Vector2(20, 9), Color("5a2f2a"))
	Art.oval(self, Vector2(H.x + 30, GROUND - 6), Vector2(20, 9), Color("5a2f2a"))
	Art.limb(self, hip, sh, 64, top)
	Art.limb(self, hd - fwd * 22.0, sh - fwd * 30.0 - dir * 16.0, 22, vic["hair"])
	Art.disc(self, hd - fwd * 6.0 + dir * 4.0, 33, vic["hair"])
	Art.disc(self, hd, 30, skin)
	Art.disc(self, hd + fwd * 30.0 - dir * 2.0, 5, skin)
	var eye := hd + fwd * 14.0 + dir * 5.0
	if blocked:
		Art.disc(self, eye, 6.5, Color.WHITE)
		Art.disc(self, eye + fwd * 1.5, 3.4, Art.INK)
		draw_line(eye + dir * 12.0 - fwd * 7.0, eye + dir * 9.0 + fwd * 7.0, Color(Art.INK, 0.7), 2.2, true)
		Art.oval(self, hd + fwd * 20.0 - dir * 12.0, Vector2(5, 6.5), Color("5a1f1f"), lean)
	else:
		draw_arc(eye, 4.5, 0.1 * PI, 0.9 * PI, 8, Art.INK, 2.2, true)
		Art.oval(self, hd + fwd * 21.0 - dir * 12.0, Vector2(4, 5), Color("5a1f1f"), lean)
	# navel / rib guides when placing the fist
	if phase == "fist":
		var a := 0.5 + 0.3 * sin(t * 4.0)
		Art.disc(self, hip + dir * 6.0 + fwd * 30.0, 4.0, Color(top.darkened(0.35), 1.0))
		Art.text(self, hip + dir * 6.0 + fwd * 44.0 + Vector2(0, 5), "navel", 14, Art.INK_SOFT)
		for i in 3:
			var rb := hip + dir * (72.0 + i * 13.0)
			draw_line(rb + fwd * 10.0, rb + fwd * 31.0, Color(top.darkened(0.25), 0.9), 3.0, true)
		Art.text(self, hip + dir * 86.0 + fwd * 44.0 + Vector2(0, 5), "ribs", 14, Art.INK_SOFT)
		if (mouse - H).length() < 170.0:
			Art.ring(self, mouse, 24.0, Color(Art.CORAL, a + 0.2), 4.0)
	# her near arm
	if blocked:
		_arm(sh, sh + dir * 16.0 + fwd * 26.0, top.darkened(0.1), skin, Vector2(0.3, 1))
	else:
		_arm(sh, hip + dir * 74.0 + fwd * 34.0, top.darkened(0.1), skin, Vector2(0.3, 1))

	# rescuer near arm, in front of her
	if present:
		if mode == "thrusts" and fist_set:
			var fist := belly + _thrust_off(dir, fwd)
			_arm(ysh, fist, Art.CORAL.darkened(0.06), Art.SKINS[2], Vector2(0.2, 1))
			Art.disc(self, fist, 15, Art.SKINS[2].darkened(0.05))
		elif mode == "thrusts":
			_arm(ysh, yhip + Vector2(34, -40), Art.CORAL.darkened(0.06), Art.SKINS[2], Vector2(-0.3, 1))
		elif lean_to > 0.5:
			var wind := ysh + Vector2(-56, -40).lerp(Vector2(-76, -78), _marker() if action_on else 0.3)
			var hand := wind
			if swing >= 0.0:
				if swing < 0.36:
					var k := swing / 0.36
					hand = wind.lerp(back, k * k)
				else:
					hand = back.lerp(wind, (swing - 0.36) / 0.64)
			_arm(ysh, hand, Art.CORAL.darkened(0.06), Art.SKINS[2], Vector2(-1, 0.4))
			Art.disc(self, chest_front, 12, Art.SKINS[2])
		else:
			_arm(ysh, yhip + Vector2(30, -30), Art.CORAL.darkened(0.06), Art.SKINS[2], Vector2(-0.3, 1))
	# impact burst
	if jolt > 0.55:
		var at := back if mode == "blows" else belly
		for i in 6:
			var a2 := i * TAU / 6.0 + 0.3
			var v := Vector2(cos(a2), sin(a2))
			draw_line(at + v * 22.0, at + v * (34.0 + jolt * 10.0), Color(Art.AMBER, jolt), 4.0, true)
	# the food
	var ft := t - food_t
	if ft < 1.6:
		var fp := hd + fwd * 26.0 + Vector2(ft * 260.0, -70.0 * ft + 420.0 * ft * ft)
		fp.y = minf(fp.y, GROUND - 4.0)
		Art.disc(self, fp, 8.0, Color("d9a45c"))
	elif not blocked:
		Art.disc(self, Vector2(H.x + 300, GROUND - 4), 8.0, Color("d9a45c"))
	if not blocked and ft > 0.4 and ft < 4.0:
		Art.bubble(self, hd + Vector2(30, -40), "*cough* … *gasp*", 18, false, 200.0, clampf((ft - 0.4) * 4.0, 0.0, 1.0))
	if phase == "intro" and since() > 0.5:
		Art.bubble(self, Vector2(300, 300), "Mara? Are you okay?", 17, false, 200.0, clampf((since() - 0.5) * 3.0, 0.0, 1.0))

	if action_on or (mode != "" and phase == "action"):
		_draw_meter_card()


func _thrust_off(dir: Vector2, fwd: Vector2) -> Vector2:
	if mode != "thrusts" or swing < 0.0:
		return Vector2.ZERO
	var k := sin(clampf(swing / 0.6, 0.0, 1.0) * PI)
	return (-fwd * 15.0 + dir * 12.0) * k


func _arm(a: Vector2, b: Vector2, sleeve: Color, skin: Color, prefer: Vector2) -> void:
	var hand := Art.reach(a, b, 139.0)
	var el := Art.joint(a, hand, 70.0, 70.0, prefer)
	Art.limb(self, a, el, 22, sleeve)
	Art.limb(self, el, hand, 19, sleeve)
	Art.disc(self, hand, 12, skin)


func _draw_meter_card() -> void:
	var r := Rect2(870, 96, 370, 400)
	Art.card(self, r)
	var blows := mode == "blows"
	Art.text(self, Vector2(900, 142), "BACK BLOWS" if blows else "ABDOMINAL THRUSTS", 22, Art.INK, true)
	Art.text(self, Vector2(900, 168), "between the shoulder blades" if blows else "just above the navel — in and up", 16, Art.INK_SOFT)
	for i in need:
		var c := Vector2(918 + i * 50, 216)
		Art.disc(self, c, 17, Color(Art.INK, 0.1))
		if i < hits:
			Art.disc(self, c, 17, Art.TEAL)
			Art.check(self, c, 15, Color.WHITE, 3.5)
	# power bar
	var bar := Rect2(900, 276, 310, 40)
	Art.text(self, Vector2(900, 266), "FORCE", 13, Art.INK_SOFT, true)
	Art.rrect(self, bar, Color(Art.INK, 0.1), 12)
	Art.rrect(self, Rect2(bar.position.x + bar.size.x * ZONE_LO, bar.position.y, bar.size.x * (ZONE_HI - ZONE_LO), bar.size.y), Art.TEAL, 10)
	var mx := bar.position.x + bar.size.x * _marker()
	Art.rrect(self, Rect2(mx - 6, bar.position.y - 8, 12, bar.size.y + 16), Art.INK, 6)
	Art.text(self, Vector2(900, 344), "soft", 13, Art.INK_SOFT)
	Art.text(self, Vector2(1172, 344), "firm", 13, Art.TEAL, true)
	if t - msg_t < 1.1:
		Art.text_c(self, Vector2(1055, 392), msg, 22, msg_col, true)
	else:
		Art.text_c(self, Vector2(1055, 392), "Click or SPACE in the green", 16, Art.INK_SOFT)
	draw_line(Vector2(900, 428), Vector2(1210, 428), Color(Art.INK, 0.1), 2.0)
	Art.text(self, Vector2(900, 462), "5 back blows  →  5 thrusts  →  repeat", 16, Art.INK, true)


func _lamp(x: float) -> void:
	draw_line(Vector2(x, 0), Vector2(x, 104), Art.INK, 3.0)
	Art.poly(self, PackedVector2Array([Vector2(x - 16, 100), Vector2(x + 16, 100), Vector2(x + 44, 144), Vector2(x - 44, 144)]), Color("d9623f"))
	Art.oval(self, Vector2(x, 150), Vector2(70, 26), Color(1.0, 0.9, 0.6, 0.22))


func _draw_room() -> void:
	draw_rect(Rect2(0, 0, 1280, 720), Color("f3e0c2"))
	draw_rect(Rect2(0, 396, 1280, 110), Color("e9cfa8"))
	draw_rect(Rect2(0, 392, 1280, 8), Color("c9a57a"))
	# window
	Art.rrect(self, Rect2(404, 106, 330, 232), Color("8c6a4a"), 10)
	Art.rrect(self, Rect2(416, 118, 306, 208), Color("cfe9f1"), 6)
	Art.rrect(self, Rect2(436, 222, 70, 104), Color("b7d7c0"), 6)
	Art.rrect(self, Rect2(520, 190, 90, 136), Color("e7c9b4"), 6)
	Art.rrect(self, Rect2(624, 236, 80, 90), Color("c5cfe0"), 6)
	draw_rect(Rect2(564, 118, 10, 208), Color("8c6a4a"))
	# chalk board
	Art.rrect(self, Rect2(60, 120, 124, 150), Color("8c6a4a"), 8)
	Art.rrect(self, Rect2(68, 128, 108, 134), Color("2c3a36"), 4)
	Art.text(self, Vector2(82, 156), "TODAY", 16, Color("f4efe6"), true)
	for i in 4:
		draw_line(Vector2(82, 178 + i * 22), Vector2(82 + 76 - i * 12, 178 + i * 22), Color(0.96, 0.94, 0.9, 0.7), 3.0)
	Art.rrect(self, Rect2(772, 170, 76, 96), Color("8c6a4a"), 6)
	Art.rrect(self, Rect2(779, 177, 62, 82), Color("f4efe6"), 3)
	Art.disc(self, Vector2(810, 230), 20, Color("d9623f"))
	draw_line(Vector2(810, 210), Vector2(816, 196), Color("5b8c5a"), 4.0, true)
	_lamp(250)
	_lamp(640)
	_lamp(1090)
	# floor
	draw_rect(Rect2(0, GROUND - 26, 1280, 300), Color("c79a6c"))
	for i in 9:
		draw_line(Vector2(i * 170 - 40, GROUND - 26), Vector2(i * 190 - 140, 720), Color("b78a5c"), 2.0)
	# friend at the table
	var fpose := {"face": {"gaze": Vector2(3, -1), "brow": 0.9 if blocked else 0.0, "smile": -0.5 if blocked else 0.8, "eyes": "wide" if blocked else "open"}}
	if blocked:
		fpose["rh"] = Vector2(70, -150)
	Art.person(self, Vector2(236, 568), 1.15, friend, fpose)
	Art.rrect(self, Rect2(96, 446, 300, 20), Color("8c6a4a"), 8)
	draw_rect(Rect2(236, 466, 20, 90), Color("75573b"))
	Art.rrect(self, Rect2(196, 552, 100, 12), Color("75573b"), 6)
	Art.oval(self, Vector2(170, 442), Vector2(40, 8), Color.WHITE)
	Art.oval(self, Vector2(320, 442), Vector2(40, 8), Color.WHITE)
	Art.oval(self, Vector2(322, 438), Vector2(22, 6), Color("d9a45c"))
	Art.rrect(self, Rect2(238, 410, 16, 34), Color(0.75, 0.9, 0.95, 0.8), 4)
	# pushed-back chair
	Art.rrect(self, Rect2(430, 470, 70, 12), Color("75573b"), 5)
	draw_rect(Rect2(434, 380, 9, 150), Color("75573b"))
	draw_rect(Rect2(488, 482, 9, 48), Color("75573b"))
	Art.rrect(self, Rect2(430, 380, 16, 70), Color("8c6a4a"), 6)
