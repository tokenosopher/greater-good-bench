extends "res://scripts/scenario.gd"
## 15:10 - Tea at Rosa's. Stroke: Face, Arms, Speech, Time.

const TESTS := ["face", "arms", "speech"]
const TEST_LABEL := {"face": "Ask her to smile", "arms": "Ask her to raise both arms", "speech": "Ask her to repeat a sentence"}
const CARD_TIME := 9.0

var chance := 0.92
var rosa := {"skin": Art.SKINS[1], "hair": Art.HAIRS[3], "style": 2, "top": Color("7d5ba6"), "legs": Art.INK}
var test := ""
var test_t := 0.0
var done_tests := {"face": false, "arms": false, "speech": false}
var time_done := false
var zoom := 0.0
var shift := 0.0
var typed := ""
var shake_t := -10.0
var view := "room"

var cards: Array = []
var card_i := -1
var card: Dictionary = {}
var card_t := 0.0
var card_res := 0
var card_fb := ""
var card_side := 1.0
var drill_right := 0


func run() -> void:
	hud.set_title("15:10  ·  Tea at Rosa's")
	hud.chosen.connect(_on_choice)
	hud.hide_panel()
	set_phase("tea")
	await pause(1.8)
	set_phase("drop")
	Sfx.play("crack")
	await pause(1.1)
	await say("Tea at Aunt Rosa's. She's halfway through a story when the cup slips out of her hand. She looks down at it, puzzled.\n“Thass… funny,” she says.")
	hud.show_meter("HER CHANCES")
	while true:
		var left: Array = []
		var labels: Array = []
		for k: String in TESTS:
			if not done_tests[k]:
				left.append(k)
				labels.append(TEST_LABEL[k])
		if left.is_empty():
			break
		set_phase("fast")
		hud.instruct("Something is off. Check her — three quick tests, any order.", "F · A · S · T", labels)
		var i: int = await picked
		var kind: String = left[i]
		test = kind
		test_t = t
		set_phase("test")
		match kind:
			"face":
				hud.instruct("“Rosa — give me a big smile.”", "F IS FOR FACE")
				await pause(2.6)
				await quiz("Look at her smile. What do you see?", [
					{"t": "One side of her mouth isn't lifting", "ok": true, "fb": "F — Face. A smile that only works on one side is a classic sign of a stroke."},
					{"t": "A normal smile", "ok": false, "fb": "Look again: one corner of her mouth stays down, and the eyelid on that side is heavy. A lopsided face is a classic stroke sign."},
				], "F IS FOR FACE")
			"arms":
				hud.instruct("“Now close your eyes and hold both arms out.”", "A IS FOR ARMS")
				await pause(3.6)
				await quiz("Watch her arms. What happens?", [
					{"t": "One arm is sinking", "ok": true, "fb": "A — Arms. She can't keep one arm up, and she hasn't even noticed. Weakness on one side of the body is a stroke sign."},
					{"t": "Both arms stay level", "ok": false, "fb": "Look again: one arm keeps drifting down. Weakness down one side of the body is a stroke sign."},
				], "A IS FOR ARMS")
			"speech":
				hud.instruct("“Repeat after me: The sky is blue today.”", "S IS FOR SPEECH")
				await pause(3.4)
				await quiz("Listen to her. How does it sound?", [
					{"t": "Slurred — the words aren't coming out right", "ok": true, "fb": "S — Speech. Slurred, garbled or missing words — or not understanding you — are stroke signs."},
					{"t": "Clear enough", "ok": false, "fb": "Listen again: “Th' shky… iz bloo… t'day.” Slurred or jumbled speech is a stroke sign."},
				], "S IS FOR SPEECH")
		done_tests[kind] = true
		test = ""
	set_phase("time")
	await say("Face. Arms. Speech. Any ONE of those signs would be enough.\n\nRosa waves you off with her good hand. “Don't fussh, dear. I'm jusht tired. I'll lie down for a bit.”", "T IS FOR TIME")
	await quiz("What now?", [
		{"t": "Call %s right now" % number, "ok": true, "fb": "T — Time. Don't wait to see if it passes, and don't let her talk you out of it. Every minute, more of her brain is dying — and the treatment only works early."},
		{"t": "Let her lie down, and check on her in an hour", "ok": false, "fb": "An hour from now, millions more brain cells are gone and the window for treatment may have closed. With stroke signs, “wait and see” is the most dangerous choice there is."},
		{"t": "Give her an aspirin and some water", "ok": false, "fb": "Some strokes are bleeds, and aspirin makes those worse. She may also be unable to swallow safely. Nothing to eat, drink or take — just call."},
		{"t": "Drive her to the hospital yourself", "ok": false, "fb": "Better than waiting — but an ambulance crew starts care on the way, warns the hospital, and takes her straight to a stroke unit. Call."},
	], "T IS FOR TIME")
	time_done = true
	view = "dial"
	while true:
		set_phase("dial")
		hud.instruct("Dial your emergency number. (Click the keys, or type.)", "CALL NOW")
		var s: String = await picked
		if s == number:
			break
		shake_t = t
		typed = ""
		await bad("That's not it. The emergency number you chose for where you live is %s. Know it without thinking — you can dial it from a locked phone." % number)
	Sfx.play("good")
	set_phase("call")
	await quiz("“Ambulance. What's happened?” You describe her face, her arm, her speech. “And when did this start?”", [
		{"t": "“About ten past three — a few minutes ago.”", "ok": true, "fb": "Exactly what they need. Clot-busting treatment can only be given within a few hours of the FIRST symptom — so the clock on the wall just became the most important thing in the room."},
		{"t": "“Sometime this morning, I think.”", "ok": false, "fb": "The wall clock said ten past three when her cup fell. A wrong start time can rule her out of treatment. When you spot a sign, look at a clock."},
		{"t": "“I didn't notice.”", "ok": false, "fb": "The wall clock said ten past three when her cup fell. Doctors need that time to decide which treatments are still possible. When you spot a sign, look at a clock."},
	], "ON THE PHONE")
	view = "room"
	set_phase("wait")
	await say("“Stay with her. Nothing to eat or drink. We're on our way.”\n\nWhile you wait, a drill. Six strangers, one test each. For each one: fine — or call?", "RECOGNITION DRILL")

	view = "drill"
	var pool := [
		{"kind": "face", "bad": false, "ask": "“Give me a big smile.”", "fb": "An even smile on both sides. Fine."},
		{"kind": "face", "bad": true, "ask": "“Give me a big smile.”", "fb": "One corner of the mouth stays down. Stroke sign — call."},
		{"kind": "arms", "bad": false, "ask": "“Hold both arms out.”", "fb": "Both arms hold steady. Fine."},
		{"kind": "arms", "bad": true, "ask": "“Hold both arms out.”", "fb": "One arm sinks. Stroke sign — call."},
		{"kind": "speech", "bad": false, "ask": "“Say: It's a lovely day today.”", "fb": "Clear speech. Fine."},
		{"kind": "speech", "bad": true, "ask": "“Say: It's a lovely day today.”", "fb": "Slurred, garbled words. Stroke sign — call."},
	]
	pool.shuffle()
	cards = pool
	for i in cards.size():
		card_i = i
		card = cards[i]
		card["look"] = _random_look(i)
		card_side = 1.0 if randf() < 0.5 else -1.0
		card_res = 0
		card_t = t
		set_phase("card")
		hud.instruct(card["ask"], "STRANGER %d OF %d" % [i + 1, cards.size()], ["Looks fine", "Stroke sign — call %s" % number])
		var a: int = await picked
		var is_bad: bool = card["bad"]
		var right := a >= 0 and (a == 1) == is_bad
		if right:
			drill_right += 1
			Sfx.play("good")
		else:
			Sfx.play("bad")
		card_res = 1 if right else -1
		cards[i]["res"] = card_res
		card_fb = ("Too slow. " if a < 0 else "") + String(card["fb"])
		hud.hide_panel()
		set_phase("card_fb")
		await pause(2.0)
	card = {"kind": "tia", "bad": true, "look": _random_look(7)}
	card_res = 0
	set_phase("tia")
	await quiz("One more. A man at the bus stop tells you: “Funny thing — ten minutes ago my hand went numb and my words came out wrong. It's passed now. I feel fine.”", [
		{"t": "“That still needs an ambulance. I'm calling %s.”" % number, "ok": true, "fb": "Stroke signs that vanish are often a “mini-stroke” (a TIA): a warning that a major stroke may follow within hours or days. It's still an emergency."},
		{"t": "“Glad it passed. Take it easy today.”", "ok": false, "fb": "Stroke signs that vanish are often a “mini-stroke” (a TIA): a warning that a major stroke may follow within hours or days. Even when it passes, it is an emergency."},
	], "LAST ONE")
	skill = clampf(drill_right / 5.0, 0.0, 1.0)
	view = "room"
	set_phase("end")
	Sfx.play("siren")
	await say("Back at Rosa's, the paramedics run the same three checks you did, then radio ahead: “Suspected stroke, onset fifteen-ten.”\nBecause you noticed, called, and knew the time, the stroke team is waiting at the door when she arrives.")
	if chance > 0.5:
		finish("Rosa was treated in time.", "You spotted the signs, refused to wait, and gave the hospital the one number they needed: when it started. You got %d of 6 in the drill." % drill_right)
	else:
		finish("Rosa got to hospital.", "She's being treated — but minutes were lost along the way, and in a stroke minutes are brain. You got %d of 6 in the drill." % drill_right)


func on_mistake() -> void:
	chance -= 0.07


func _random_look(i: int) -> Dictionary:
	var tops := [Color("4f9d69"), Color("3f6fb5"), Color("e58a3a"), Color("c8402f"), Color("8a6bb8"), Color("3d8f96"), Color("d9a441"), Color("5d6a7a")]
	return {"skin": Art.SKINS[randi() % 5], "hair": Art.HAIRS[randi() % 6], "style": [0, 1, 2, 3, 5, 6][randi() % 6], "top": tops[i % tops.size()], "legs": Art.INK}


func _on_choice(i: int) -> void:
	if (phase == "fast" or phase == "card") and hud.mode == "instruct":
		fired = true
		picked.emit(i)


func tick(delta: float) -> void:
	if hud.waiting():
		chance -= 0.004 * delta
	chance = clampf(chance, 0.05, 0.97)
	hud.set_meter(chance)
	zoom = lerpf(zoom, 1.0 if test == "face" else 0.0, 1.0 - exp(-5.0 * delta))
	shift = lerpf(shift, 1.0 if view == "dial" else 0.0, 1.0 - exp(-6.0 * delta))
	if phase == "card" and t - card_t > CARD_TIME:
		fired = true
		picked.emit(-2)
	if auto and not fired and since() > 0.2:
		match phase:
			"fast":
				fired = true
				picked.emit(0)
			"card":
				fired = true
				var want := 1 if card["bad"] else 0
				picked.emit(want if randf() < 0.8 else 1 - want)
			"dial":
				fired = true
				picked.emit(number if randf() < 0.6 else "123")


func _key_rect(i: int) -> Rect2:
	return Rect2(864 + (i % 3) * 86, 232 + (i / 3) * 62, 78, 54)


func _key_label(i: int) -> String:
	if i < 9:
		return str(i + 1)
	return ["<", "0", "CALL"][i - 9]


func _tap_key(label: String) -> void:
	if label == "<":
		typed = typed.left(-1) if typed.length() > 0 else ""
		Sfx.play("click")
	elif label == "CALL":
		if typed != "":
			fired = true
			picked.emit(typed)
	elif typed.length() < 6:
		typed += label
		Sfx.play("dial")


func press(p: Vector2) -> void:
	if phase == "dial":
		for i in 12:
			if _key_rect(i).has_point(p):
				_tap_key(_key_label(i))
				return


func key(code: int, down: bool) -> void:
	if not down or phase != "dial":
		return
	if code >= KEY_0 and code <= KEY_9:
		_tap_key(str(code - KEY_0))
	elif code >= KEY_KP_0 and code <= KEY_KP_9:
		_tap_key(str(code - KEY_KP_0))
	elif code == KEY_BACKSPACE:
		_tap_key("<")
	elif code == KEY_ENTER or code == KEY_KP_ENTER:
		_tap_key("CALL")


# ---------------------------------------------------------------- drawing

func _draw() -> void:
	if view == "drill":
		_draw_drill()
		return
	_draw_room()
	# Rosa
	var s := lerpf(1.75, 3.1, zoom)
	var px := lerpf(640.0, 420.0, shift)
	var head_y := lerpf(208.0, 300.0, zoom)
	var p := Vector2(px, head_y + 224.0 * s)
	var pose := _test_pose(test, t - test_t, true, 1.0)
	if test == "":
		var f := {"droop": 0.75, "side": 1.0, "smile": 0.0, "brow": 0.3}
		if phase == "tea":
			f = {"smile": 0.8}
		elif phase == "end":
			f = {"droop": 0.75, "side": 1.0, "smile": 0.3}
		pose = {"face": f}
		if phase == "tea":
			pose["rh"] = Vector2(34, -140)
		else:
			pose["rh"] = Vector2(44, -92)
	Art.person(self, p, s, rosa, pose)
	if phase == "tea":
		_cup(p + Vector2(34, -150) * s, 0.0, 1.5)
	# table in front of her
	Art.rrect(self, Rect2(110, 440, 1060, 340), Color("f4efe6"), 26)
	Art.rrect(self, Rect2(110, 440, 1060, 16), Color("e2dacb"), 8)
	for i in 8:
		Art.disc(self, Vector2(180 + i * 132, 492), 5.0, Color("e7c2b4"))
	_teapot(Vector2(300, 436))
	_cup(Vector2(900, 450), 0.0, 1.6)
	if phase != "tea":
		Art.oval(self, Vector2(px + 110, 474), Vector2(64, 13), Color("b98b5e"))
		_cup(Vector2(px + 76, 464), 1.35, 1.6)
	if test == "speech":
		var n := int(clampf((t - test_t - 0.6) * 12.0, 0.0, 99.0))
		var line := "Th' shky… iz bloo… t'day."
		if n > 0:
			Art.bubble(self, Vector2(px + 60, head_y - 30), line, 24, false, 330.0, 1.0, 140.0, n)
	if phase == "time":
		Art.bubble(self, Vector2(px + 60, head_y - 30), "Don't fussh, dear.", 22, false, 300.0, 1.0, 120.0)
	_draw_fast()
	if shift > 0.02:
		_draw_phone()


func _test_pose(kind: String, e: float, stroke: bool, side: float) -> Dictionary:
	var d := 0.78 if stroke else 0.0
	match kind:
		"face":
			var sm := smoothstep(0.3, 1.3, e)
			return {"face": {"droop": d, "side": side, "smile": sm, "brow": -0.2}}
		"arms":
			var up := smoothstep(0.2, 1.0, e)
			var pose := {"face": {"eyes": "closed", "droop": d * 0.6, "side": side, "smile": 0.1}}
			for sx: float in [-1.0, 1.0]:
				var a := lerpf(1.35, -0.12, up)
				if stroke and sx == side:
					a += smoothstep(1.3, 3.2, e) * 0.95 + sin(e * 9.0) * 0.02
				else:
					a += sin(e * 3.0 + sx) * 0.015
				var hand := Vector2(sx * 30.0, -178.0) + Vector2(sx * cos(a), sin(a)) * 82.0
				pose["lh" if sx < 0.0 else "rh"] = hand
			return pose
		"speech":
			var talking := e > 0.6 and e < 2.6
			var f := {"droop": d, "side": side, "smile": 0.0}
			if talking and fmod(e, 0.3) < 0.15:
				f["mouth"] = "gasp"
			return {"face": f}
	return {}


func _cup(p: Vector2, rot: float, s: float) -> void:
	draw_set_transform(p, rot, Vector2(s, s))
	Art.ring(self, Vector2(15, -9), 7.0, Color.WHITE, 3.0)
	Art.rrect(self, Rect2(-13, -20, 26, 22), Color.WHITE, 7)
	draw_rect(Rect2(-13, -14, 26, 3), Color("d98fa8"))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _teapot(p: Vector2) -> void:
	Art.ring(self, p + Vector2(-52, -42), 22.0, Color("d98fa8"), 8.0)
	Art.poly(self, PackedVector2Array([p + Vector2(40, -40), p + Vector2(84, -78), p + Vector2(92, -70), p + Vector2(50, -18)]), Color("d98fa8"))
	Art.oval(self, p + Vector2(0, -44), Vector2(56, 46), Color("e8a7bb"))
	Art.rrect(self, Rect2(p.x - 30, p.y - 96, 60, 12), Color("d98fa8"), 6)
	Art.disc(self, p + Vector2(0, -102), 8.0, Color("d98fa8"))
	draw_rect(Rect2(p.x - 40, p.y - 6, 80, 8), Color("d98fa8"))


func _draw_room() -> void:
	draw_rect(Rect2(0, 0, 1280, 720), Color("ece0cf"))
	for i in 17:
		draw_rect(Rect2(i * 80.0 + 10, 0, 26, 420), Color("e7d9c5"))
	draw_rect(Rect2(0, 404, 1280, 316), Color("d9c4a6"))
	draw_rect(Rect2(0, 400, 1280, 8), Color("bfa27c"))
	# window
	Art.rrect(self, Rect2(846, 108, 196, 236), Color("9a7653"), 10)
	Art.rrect(self, Rect2(858, 120, 172, 212), Color("cfe9f1"), 6)
	Art.oval(self, Vector2(944, 330), Vector2(84, 50), Color("a8d498"))
	draw_rect(Rect2(858, 300, 172, 32), Color("a8d498"))
	draw_rect(Rect2(940, 120, 8, 212), Color("9a7653"))
	draw_rect(Rect2(858, 222, 172, 8), Color("9a7653"))
	# framed picture
	Art.rrect(self, Rect2(292, 150, 120, 150), Color("9a7653"), 6)
	Art.rrect(self, Rect2(302, 160, 100, 130), Color("f4efe6"), 3)
	Art.disc(self, Vector2(352, 208), 20, Color("e7b7a4"))
	Art.rrect(self, Rect2(326, 232, 52, 50), Color("8fb5a4"), 14)
	# wall clock, 3:10
	var cc := Vector2(1146, 176)
	if phase == "drop" or phase == "call":
		var pul := fmod(t * 1.2, 1.0)
		Art.ring(self, cc, 62.0 + pul * 22.0, Color(Art.CORAL, (1.0 - pul) * 0.6), 4.0)
	Art.disc(self, cc, 62, Art.INK)
	Art.disc(self, cc, 54, Color.WHITE)
	for i in 12:
		var a := i * TAU / 12.0
		var v := Vector2(sin(a), -cos(a))
		draw_line(cc + v * 44.0, cc + v * 50.0, Art.INK, 3.0 if i % 3 == 0 else 1.5, true)
	var ha := (3.0 + 10.0 / 60.0) / 12.0 * TAU
	var ma := 10.0 / 60.0 * TAU
	draw_line(cc, cc + Vector2(sin(ha), -cos(ha)) * 26.0, Art.INK, 5.0, true)
	draw_line(cc, cc + Vector2(sin(ma), -cos(ma)) * 40.0, Art.INK, 3.5, true)
	var sa := fmod(t, 60.0) / 60.0 * TAU
	draw_line(cc, cc + Vector2(sin(sa), -cos(sa)) * 42.0, Art.CORAL, 1.5, true)
	Art.disc(self, cc, 4, Art.INK)


func _draw_fast() -> void:
	if phase == "tea" or phase == "drop":
		return
	var r := Rect2(40, 92, 204, 300)
	Art.card(self, r)
	var names := ["Face", "Arms", "Speech", "Time"]
	var keys := ["face", "arms", "speech", "time"]
	for i in 4:
		var c := Vector2(84, 138 + i * 68)
		var is_done: bool = time_done if i == 3 else done_tests[keys[i]]
		var active: bool = test == keys[i] or (i == 3 and phase == "time")
		Art.disc(self, c, 25, Art.TEAL if is_done else (Art.AMBER if active else Color(Art.INK, 0.1)))
		Art.text_c(self, c, names[i].left(1), 26, Color.WHITE if (is_done or active) else Art.INK_SOFT, true)
		Art.text(self, c + Vector2(40, 7), names[i], 20, Art.INK if (is_done or active) else Art.INK_SOFT, is_done or active)


func _draw_phone() -> void:
	var ox := (1.0 - shift) * 460.0
	var sh := sin((t - shake_t) * 50.0) * 10.0 * maxf(0.0, 1.0 - (t - shake_t) * 2.5)
	draw_set_transform(Vector2(ox + sh, 0), 0.0, Vector2.ONE)
	Art.rrect(self, Rect2(840, 76, 300, 470).grow(3), Color(0, 0, 0, 0.2), 38)
	Art.rrect(self, Rect2(840, 70, 300, 470), Art.INK, 36)
	Art.rrect(self, Rect2(856, 100, 268, 110), Color("f4f6f8"), 14)
	Art.text(self, Vector2(874, 132), "EMERGENCY CALL", 13, Art.INK_SOFT, true)
	Art.text_c(self, Vector2(990, 172), typed if typed != "" else "_", 44, Art.INK, true)
	for i in 12:
		var kr := _key_rect(i)
		var lab := _key_label(i)
		var hov := kr.has_point(mouse - Vector2(ox, 0)) and phase == "dial"
		var col := Color("3a4a5c")
		if lab == "CALL":
			col = Art.TEAL
		elif lab == "<":
			col = Color("55606e")
		Art.rrect(self, kr, col.lightened(0.18) if hov else col, 14)
		Art.text_c(self, kr.get_center(), lab, 20 if lab == "CALL" else 26, Color.WHITE, true)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _draw_drill() -> void:
	draw_rect(Rect2(0, 0, 1280, 720), Color("dfeee9"))
	Art.oval(self, Vector2(640, 610), Vector2(700, 150), Color("cfe3dc"))
	# bus stop sign for flavour
	draw_rect(Rect2(1040, 150, 10, 420), Color("8fa3a0"))
	Art.rrect(self, Rect2(1000, 120, 90, 70), Color("3f6fb5"), 12)
	Art.rrect(self, Rect2(1018, 140, 54, 30), Color.WHITE, 8)
	if card.is_empty():
		return
	var kind: String = card["kind"]
	var is_bad: bool = card["bad"]
	var e := t - card_t
	var look: Dictionary = card["look"]
	if kind == "tia":
		Art.person(self, Vector2(640, 600), 1.6, look, {"face": {"smile": 0.5}, "rh": Vector2(60, -150)})
		Art.bubble(self, Vector2(700, 215), "It's passed now. I feel fine.", 20, false, 300.0, 1.0, 120.0)
		return
	var s := 3.0 if kind == "face" else 1.6
	var head_y := 300.0 if kind == "face" else 240.0
	var p := Vector2(640, head_y + 224.0 * s)
	Art.person(self, p, s, look, _test_pose(kind, e, is_bad, card_side))
	if kind == "speech":
		var line := "Ish a luvvy… dayy… t'dayy." if is_bad else "It's a lovely day today."
		var n := int(clampf((e - 0.6) * 14.0, 0.0, 99.0))
		if n > 0:
			Art.bubble(self, Vector2(700, 190), line, 22, false, 320.0, 1.0, 110.0, n)
	# timer
	if phase == "card":
		var left := clampf(1.0 - e / CARD_TIME, 0.0, 1.0)
		Art.rrect(self, Rect2(440, 84, 400, 10), Color(Art.INK, 0.1), 5)
		Art.rrect(self, Rect2(440, 84, maxf(400.0 * left, 10.0), 10), Art.AMBER if left < 0.35 else Art.TEAL, 5)
	for i in cards.size():
		var c := Vector2(60 + i * 30, 104)
		var col := Color(Art.INK, 0.12)
		if i < card_i or (i == card_i and card_res != 0):
			col = Art.TEAL if int(cards[i].get("res", 0)) > 0 else Art.CORAL
		Art.disc(self, c, 9, col)
	if phase == "card_fb":
		var ok := card_res > 0
		var w := Art.text_w(card_fb, 22, true) + 110.0
		var r := Rect2(640 - w * 0.5, 560, w, 64)
		Art.card(self, r, Art.TEAL if ok else Art.CORAL, 32)
		if ok:
			Art.check(self, r.position + Vector2(40, 32), 26, Color.WHITE, 5.0)
		else:
			Art.cross(self, r.position + Vector2(40, 32), 26, Color.WHITE, 5.0)
		Art.text(self, r.position + Vector2(72, 40), card_fb, 22, Color.WHITE, true)
