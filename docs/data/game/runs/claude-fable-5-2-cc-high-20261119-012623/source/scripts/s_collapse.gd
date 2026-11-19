extends "res://scripts/scenario.gd"
## 07:40 - The Park. Cardiac arrest: check, call, compress, defibrillate.

const C := Vector2(430, 322)          # centre of the chest in the close view
const TEMPO := 110.0
const SHOCK_BTN := Vector2(1122, 318)
const PAD_SIZE := Vector2(96, 76)

var view := "wide"
var chance := 0.95
var man := {"skin": Art.SKINS[1], "hair": Art.HAIRS[3], "style": 0, "top": Color("f3c64f"), "legs": Color("3d4b5e"), "sleeves": false}
var you := {"skin": Art.SKINS[2], "hair": Art.HAIRS[0], "style": 0, "top": Art.CORAL, "legs": Color("2f3b4c")}
var medic := {"skin": Art.SKINS[3], "hair": Art.HAIRS[4], "style": 0, "top": Color("2d6e5e"), "legs": Color("2d6e5e"), "stripe": Color("e9f26a")}
var people: Array = []
var caller := -1
var runner := -1
var run_t := 0.0
var shout_t := -10.0
var kneel := false

# compressions
var cpr_on := false
var cpr_time := 0.0
var cpr_len := 32.0
var guided := true
var guide_off := 0.0
var last_beat := -1
var pressing := false
var depth := 0.0
var peak := 0.0
var leaned := false
var last_press := -10.0
var gaps: Array[float] = []
var bpm := 0.0
var bpm_shown := 60.0
var count := 0
var total_good := 0
var total_expected := 0.0
var word := ""
var word_col := Art.TEAL
var word_t := -10.0
var cracked := false
var hands_on := false
var bare := false
var tapped := -10.0
var up_pending := false

# defibrillator
var pads: Array = []
var drag := -1
var targets: Array[Vector2] = [C + Vector2(-56, -72), C + Vector2(80, 66)]
var pad_hint := false
var touched := false
var shock_t := -10.0
var revived := false


func run() -> void:
	hud.set_title("07:40  ·  The Park")
	hud.chosen.connect(_on_choice)
	people = [
		{"p": Vector2(215, 520), "look": {"skin": Art.SKINS[0], "hair": Art.HAIRS[2], "style": 1, "top": Color("4f9d69"), "legs": Color("39424e")}, "tag": "in the green jacket", "think": "Is he… okay?"},
		{"p": Vector2(370, 462), "look": {"skin": Art.SKINS[3], "hair": Art.HAIRS[4], "style": 4, "hat": Color("c8402f"), "top": Color("e9e4da"), "legs": Color("4a5a70")}, "tag": "with the red cap", "think": "Someone should do something."},
		{"p": Vector2(960, 458), "look": {"skin": Art.SKINS[4], "hair": Art.HAIRS[4], "style": 5, "top": Color("3f6fb5"), "legs": Color("2b3340")}, "tag": "in the blue coat", "think": "Somebody's surely called already."},
		{"p": Vector2(1100, 518), "look": {"skin": Art.SKINS[1], "hair": Art.HAIRS[3], "style": 2, "top": Color("e58a3a"), "legs": Color("5b4a3f")}, "tag": "in the orange top", "think": "I'd only make it worse."},
	]
	pads = [
		{"pos": Vector2(862, 318), "home": Vector2(862, 318), "placed": -1},
		{"pos": Vector2(978, 318), "home": Vector2(978, 318), "placed": -1},
	]
	hud.hide_panel()
	set_phase("jog")
	await pause(2.3)
	set_phase("fall")
	await pause(0.5)
	Sfx.play("thud")
	set_phase("down")
	await pause(1.5)
	hud.show_meter("HIS CHANCES")
	await say("A jogger staggers, grabs at the air, and drops onto the path. He isn't moving.\nPeople stop. People stare. Nobody steps forward.")
	await quiz("What do you do?", [
		{"t": "Go to him", "ok": true},
		{"t": "Hold back — someone trained will surely step in", "ok": false, "fb": "Everyone here is thinking exactly that. It has a name: the bystander effect. The bigger the crowd, the longer everybody waits — while his brain runs out of oxygen."},
		{"t": "Keep walking. He probably just fainted", "ok": false, "fb": "Maybe. But if his heart has stopped he has minutes, and you'd be walking away with them. Checking costs you ten seconds."},
	])

	view = "close"
	set_phase("resp")
	hud.instruct("Kneel beside him. Tap his shoulders firmly and shout.  (Click his shoulders.)", "IS HE RESPONSIVE?")
	await picked
	tapped = t
	Sfx.play("slap")
	set_phase("resp2")
	await pause(1.5)
	set_phase("breath")
	hud.instruct("No response. Tilt his head back and watch his chest. Is he breathing normally?", "CHECK HIS BREATHING")
	await pause(5.2)
	await quiz("What did you see?", [
		{"t": "He's not breathing normally", "ok": true, "fb": "Right. Those odd gasps are not breathing — they're a sign his heart has stopped. Unresponsive and not breathing normally means: call, and start CPR."},
		{"t": "He gasped — so he's breathing", "ok": false, "fb": "That snoring gasp fools a lot of people. It's a reflex of a brain starved of oxygen, not a real breath. Treat it as NOT breathing."},
		{"t": "Hard to tell. Better to wait and watch", "ok": false, "fb": "If you're not sure, assume he isn't. Starting CPR on someone who turns out not to need it is very unlikely to do serious harm. Not starting on someone who does is fatal."},
	], "CHECK HIS BREATHING")

	view = "wide"
	kneel = true
	while caller < 0:
		set_phase("delegate")
		hud.instruct("You need an ambulance and a defibrillator. Give someone the job — click a person.", "GET HELP", ["Shout: “Somebody call an ambulance!”"])
		var r: int = await picked
		if r < 0:
			shout_t = t
			hud.hide_panel()
			set_phase("shout")
			await pause(1.8)
			await bad("Four people glance at each other. Nobody reaches for a phone. When a job belongs to “somebody”, nobody takes it. Pick ONE person, look at them, give them ONE job.")
		else:
			caller = r
	Sfx.play("good")
	set_phase("delegate2")
	hud.instruct("“You, %s — call %s and put it on speaker!” The phone is already out. Now send someone else to fetch a defibrillator (an AED)." % [people[caller]["tag"], number], "GET HELP")
	var r2: int = await picked
	runner = r2
	run_t = t
	Sfx.play("good")
	set_phase("sent")
	await pause(1.3)
	await say("“And you, %s — find a defibrillator and bring it here!” Stations, gyms, shops and offices often have one on the wall.\n\nOn speaker, the call handler says: “Stay on the line. I'll talk you through it.”" % people[runner]["tag"])

	view = "close"
	var asked := false
	while true:
		set_phase("hands")
		hud.instruct("Where do your hands go? Click the spot on his body." if not asked else "Try again — click where you'd push.", "CHEST COMPRESSIONS")
		asked = true
		var p: Vector2 = await picked
		var d := p - C
		if d.length() < 48.0:
			break
		elif d.y > 66.0:
			await bad("Too low — that's his stomach. You're trying to squeeze the heart: centre of the chest.")
		elif d.y < -58.0:
			await bad("Too high. Aim for the centre of the chest, on the lower half of the breastbone.")
		else:
			await bad("Close — but the heart sits nearer the middle than most people think. Dead centre, on the breastbone.")
	hands_on = true
	set_phase("ready")
	await good("Centre of the chest, on the breastbone. Heel of one hand, the other hand on top, arms straight, shoulders over your hands.")
	await say("Now push hard and fast: about two pushes every second, 5–6 cm deep (roughly 2 inches).\n\nClick, tap or press SPACE in time with the pulse. Push down — then let the chest come all the way back up.", "CHEST COMPRESSIONS")
	hud.instruct("Push in time with the pulse. Down, and fully back up.", "PUSH HARD · PUSH FAST")
	_start_cpr(32.0, true)
	await step_done

	Sfx.play("good")
	set_phase("aed_here")
	await say("The runner is back, out of breath, holding a green box. “What do I do with it?!”\n“Open it. Switch it on.” A calm recorded voice starts speaking. That is all an AED needs from you — it tells you every step.", "THE DEFIBRILLATOR")
	bare = true
	set_phase("pads")
	hud.instruct("“Attach pads to the patient's bare chest.”  Drag both pads onto him. The picture on each pad shows where it goes.", "THE AED SAYS")
	await picked
	Sfx.play("beep")
	set_phase("analyse")
	hud.instruct("“Analysing heart rhythm. Do not touch the patient.”  Hands off. Just wait.", "THE AED SAYS")
	await pause(4.0)
	if touched:
		await bad("Touching him while it analyses can blur the reading — and during a shock it's dangerous for you. When the AED says stand clear, everybody lets go.")
	Sfx.play("beep")
	set_phase("shock")
	hud.instruct("“Shock advised. Stand clear.”  Check nobody is touching him — then press the flashing button.", "THE AED SAYS")
	await picked
	Sfx.play("shock")
	shock_t = t
	chance += 0.12
	set_phase("shocked")
	hud.hide_panel()
	await pause(1.1)
	hud.instruct("“Shock delivered. Continue CPR.”  Straight back on the chest — don't wait to see what happens. No guide this time.", "THE AED SAYS")
	_start_cpr(15.0, false)
	await step_done

	Sfx.play("siren")
	skill = clampf(float(total_good) / maxf(total_expected, 1.0) / 0.8, 0.0, 1.0)
	var on_tempo := int(round(100.0 * float(total_good) / maxf(float(count), 1.0)))
	var stats := " You gave %d compressions; %d%% of them were on tempo." % [count, on_tempo]
	revived = chance > 0.5
	view = "wide"
	set_phase("end")
	hud.hide_panel()
	await pause(1.6)
	if revived:
		await say("As the ambulance pulls up, he coughs — and takes a breath of his own.\nThe paramedic looks at you. “You kept his brain alive until we got here. That was the hard part.”")
		finish("He's breathing. Because you moved.", "Your compressions kept blood flowing to his brain, and the AED restarted his heart before the ambulance even arrived." + stats)
	else:
		await say("The paramedics take over mid-rhythm. “We've got a pulse,” one calls. They load him up fast.\n“Whatever happens now — you gave him a chance he didn't have.”")
		finish("He has a chance. Because you moved.", "It took a while to get going — but imperfect CPR beats no CPR every single time." + stats)


func on_mistake() -> void:
	chance -= 0.05


func _on_choice(_i: int) -> void:
	if phase == "delegate" and hud.mode == "instruct":
		fired = true
		picked.emit(-1)


func _start_cpr(length: float, with_guide: bool) -> void:
	cpr_len = length
	cpr_time = 0.0
	guided = with_guide
	guide_off = 0.0 if with_guide else -10.0
	last_beat = -1
	gaps.clear()
	bpm = 0.0
	last_press = t
	total_expected += length * TEMPO / 60.0 * 0.92
	cpr_on = true
	set_phase("cpr")


# ---------------------------------------------------------------- simulation

func tick(delta: float) -> void:
	if hud.waiting() and not cpr_on and phase != "pads":
		chance -= 0.004 * delta
	if cpr_on:
		_tick_cpr(delta)
	else:
		depth = maxf(depth - 10.0 * delta, 0.0)
	chance = clampf(chance, 0.04, 0.97)
	hud.set_meter(chance)
	bpm_shown = lerpf(bpm_shown, bpm if bpm > 0.0 else 60.0, 1.0 - exp(-9.0 * delta))
	if drag >= 0:
		pads[drag]["pos"] = mouse
	if phase == "pads" and since() > 9.0:
		pad_hint = true
	if auto and not fired and since() > 0.25:
		_auto()


func _auto() -> void:
	match phase:
		"resp":
			fired = true
			picked.emit(0)
		"delegate":
			fired = true
			picked.emit(-1 if randf() < 0.4 else 0)
		"delegate2":
			fired = true
			picked.emit(2)
		"hands":
			fired = true
			picked.emit(C + Vector2(randf_range(-90, 90), randf_range(-120, 120)) if randf() < 0.5 else C)
		"pads":
			fired = true
			for i in 2:
				pads[i]["placed"] = i
				pads[i]["pos"] = targets[i]
			picked.emit(1)
		"analyse":
			fired = true
			touched = randf() < 0.5
		"shock":
			fired = true
			picked.emit(1)


func _tick_cpr(delta: float) -> void:
	cpr_time += delta
	if auto:
		var ph := fmod(cpr_time * TEMPO / 60.0, 1.0)
		if ph < 0.45 and not pressing:
			_down()
		elif ph >= 0.45 and pressing:
			_up()
	if pressing:
		depth = minf(depth + 12.0 * delta, 1.0)
		peak = maxf(peak, depth)
		if up_pending and t - last_press >= 0.09:
			_up()
	else:
		depth = maxf(depth - 10.0 * delta, 0.0)
	var beat := int(cpr_time * TEMPO / 60.0)
	if beat != last_beat:
		last_beat = beat
		if guided:
			Sfx.play("tick", -6.0)
	var idle := t - last_press
	if idle > 1.4:
		chance -= 0.02 * delta
		bpm = 0.0
		gaps.clear()
		if cpr_time > 2.5:
			_word("Don't stop!", Art.CORAL)
	if guided and cpr_time > 13.0:
		guided = false
		guide_off = cpr_time
		hud.instruct("The pulse has gone quiet — keep the same rhythm going on your own.", "NOW WITHOUT THE GUIDE")
	if not cracked and cpr_len > 20.0 and cpr_time > 21.0:
		cracked = true
		Sfx.play("crack")
		hud.instruct("You feel a crack under your hands. Ribs can break during good CPR. They heal. Keep going.", "DON'T STOP")
	if cpr_time >= cpr_len:
		if pressing:
			_finish_push()
		cpr_on = false
		step_done.emit()


func _down() -> void:
	if up_pending:
		up_pending = false
		_finish_push()
	if not cpr_on or pressing:
		return
	var gap := t - last_press
	leaned = depth > 0.3
	if gap < 1.4 and count > 0:
		gaps.append(gap)
		if gaps.size() > 3:
			gaps.pop_front()
		var sum := 0.0
		for g in gaps:
			sum += g
		bpm = 60.0 / (sum / gaps.size())
	last_press = t
	pressing = true
	peak = depth
	Sfx.play("thump", -3.0)


## A very quick tap (trackpads, touch) still counts as a full push.
func _up() -> void:
	if not pressing:
		return
	if t - last_press < 0.09 and cpr_on:
		up_pending = true
		return
	_finish_push()


func _finish_push() -> void:
	up_pending = false
	if not pressing:
		return
	pressing = false
	count += 1
	var ok := false
	if peak < 0.7:
		_word("Push harder", Art.AMBER)
	elif leaned:
		_word("Let the chest rise", Art.AMBER)
	elif gaps.is_empty():
		ok = true
	elif bpm < 97.0:
		_word("Faster", Art.AMBER)
	elif bpm > 125.0:
		_word("Slower", Art.AMBER)
	else:
		ok = true
		_word("Good", Art.TEAL)
	if ok:
		total_good += 1
		chance += 0.0012


func _word(s: String, col: Color) -> void:
	word = s
	word_col = col
	word_t = t


func _torso() -> Rect2:
	return Rect2(C.x - 112, C.y - 142, 224, 340)


func press(p: Vector2) -> void:
	if cpr_on:
		_down()
		return
	match phase:
		"resp":
			if p.distance_to(C + Vector2(-98, -112)) < 75.0 or p.distance_to(C + Vector2(98, -112)) < 75.0:
				fired = true
				picked.emit(1)
		"hands":
			if _torso().grow(30).has_point(p):
				fired = true
				picked.emit(p)
		"delegate", "delegate2":
			for i in people.size():
				var pp: Vector2 = people[i]["p"]
				if i != caller and Rect2(pp.x - 52, pp.y - 235, 104, 250).has_point(p):
					fired = true
					picked.emit(i)
					return
		"pads":
			for i in 2:
				var pos: Vector2 = pads[i]["pos"]
				if int(pads[i]["placed"]) < 0 and Rect2(pos - PAD_SIZE * 0.6, PAD_SIZE * 1.2).has_point(p):
					drag = i
		"analyse":
			if _torso().has_point(p) and not touched:
				touched = true
				_word("Hands off!", Art.CORAL)
		"shock":
			if p.distance_to(SHOCK_BTN) < 58.0:
				fired = true
				picked.emit(1)


func release(p: Vector2) -> void:
	if pressing:
		_up()
	if drag >= 0:
		var i := drag
		drag = -1
		var best := -1
		var bd := 85.0
		for k in 2:
			var taken := false
			for q in 2:
				if int(pads[q]["placed"]) == k:
					taken = true
			var d := p.distance_to(targets[k])
			if not taken and d < bd:
				bd = d
				best = k
		if best >= 0:
			pads[i]["placed"] = best
			pads[i]["pos"] = targets[best]
			Sfx.play("click")
			if int(pads[0]["placed"]) >= 0 and int(pads[1]["placed"]) >= 0:
				fired = true
				picked.emit(1)
		else:
			pads[i]["pos"] = pads[i]["home"]
			if _torso().grow(40).has_point(p):
				pad_hint = true
				Sfx.play("soft")


func key(code: int, down: bool) -> void:
	if code == KEY_SPACE or code == KEY_ENTER:
		if down:
			if cpr_on:
				_down()
			elif phase == "analyse" and not touched:
				touched = true
				_word("Hands off!", Art.CORAL)
		elif pressing:
			_up()


# ---------------------------------------------------------------- drawing

func _draw() -> void:
	if view == "wide":
		_draw_wide()
	else:
		_draw_close()
	var f := t - shock_t
	if f < 0.3:
		draw_rect(Rect2(0, 0, 1280, 720), Color(1, 1, 1, 0.85 * (1.0 - f / 0.3)))


func _tree(p: Vector2, s: float) -> void:
	draw_rect(Rect2(p.x - 10 * s, p.y - 80 * s, 20 * s, 90 * s), Color("8a6a4a"))
	Art.disc(self, p + Vector2(0, -130) * s, 66 * s, Color("6fae6a"))
	Art.disc(self, p + Vector2(-46, -92) * s, 46 * s, Color("7dba74"))
	Art.disc(self, p + Vector2(44, -96) * s, 48 * s, Color("64a562"))


func _draw_wide() -> void:
	draw_rect(Rect2(0, 0, 1280, 720), Color("cfe9f1"))
	Art.disc(self, Vector2(1090, 120), 90, Color(1.0, 0.95, 0.75, 0.35))
	Art.disc(self, Vector2(1090, 120), 48, Color("ffe9a8"))
	for i in 3:
		var cx := fposmod(160.0 + i * 470.0 + t * 7.0, 1500.0) - 110.0
		Art.oval(self, Vector2(cx, 96 + i * 38), Vector2(86, 20), Color(1, 1, 1, 0.85))
		Art.oval(self, Vector2(cx + 40, 84 + i * 38), Vector2(52, 20), Color(1, 1, 1, 0.85))
	Art.oval(self, Vector2(280, 420), Vector2(560, 150), Color("b9deaa"))
	Art.oval(self, Vector2(1010, 430), Vector2(600, 170), Color("add79e"))
	draw_rect(Rect2(0, 380, 1280, 340), Color("97cb8a"))
	Art.poly(self, PackedVector2Array([Vector2(0, 440), Vector2(1280, 418), Vector2(1280, 548), Vector2(0, 580)]), Color("e9e3d3"))
	for i in 16:
		var fx := fposmod(i * 173.0 + 60.0, 1280.0)
		var fy := 610.0 + fposmod(i * 67.0, 90.0)
		draw_line(Vector2(fx, fy), Vector2(fx, fy - 12), Color("7ab46f"), 2.5, true)
		Art.disc(self, Vector2(fx, fy - 14), 5.0, Color("fff6c9") if i % 3 != 0 else Color("f6c1d0"))
		Art.disc(self, Vector2(fx, fy - 14), 2.0, Color("f0b53a"))
	_tree(Vector2(96, 404), 1.15)
	_tree(Vector2(1196, 398), 1.05)
	_tree(Vector2(690, 372), 0.72)
	_tree(Vector2(520, 380), 0.5)
	# bench
	Art.rrect(self, Rect2(772, 352, 150, 12), Color("9a7653"), 4)
	Art.rrect(self, Rect2(772, 376, 150, 10), Color("9a7653"), 4)
	draw_rect(Rect2(784, 364, 8, 40), Color("6d5238"))
	draw_rect(Rect2(902, 364, 8, 40), Color("6d5238"))

	var down := phase != "jog" and phase != "fall"
	var worried := down
	var happy := phase == "end"
	# bystanders at the back
	for i in [1, 2]:
		_draw_bystander(i, worried, happy)
	# you, kneeling behind him
	if kneel:
		var yp := Vector2(690, 506)
		Art.oval(self, yp + Vector2(0, 4), Vector2(46, 9), Color(0, 0, 0, 0.12))
		Art.person(self, yp + Vector2(0, 56), 0.9, you, {"lf": Vector2(-20, -66), "rf": Vector2(20, -66), "lh": Vector2(-16, -92), "rh": Vector2(18, -92), "face": {"gaze": Vector2(0, 2.5), "brow": 0.5}})
	if phase == "end":
		Art.ambulance(self, Vector2(1080.0 + maxf(1.0 - since(), 0.0) * 460.0, 470), 1.05, t)
		Art.person(self, Vector2(800, 562), 0.9, medic, {"lf": Vector2(-20, -66), "rf": Vector2(20, -66), "lh": Vector2(-30, -100), "rh": Vector2(10, -96), "face": {"gaze": Vector2(-2, 2), "smile": 0.5}})
	# the jogger
	var jp := Vector2(545, 500)
	var pose := {}
	if phase == "jog":
		var k := clampf(since() / 2.3, 0.0, 1.0)
		jp.x = lerpf(-80.0, 545.0, k)
		var sw := sin(t * 15.0) * (1.0 - smoothstep(0.8, 1.0, k))
		pose = {"lf": Vector2(-12 + sw * 28, -9 - maxf(0.0, -sw) * 12), "rf": Vector2(12 - sw * 28, -9 - maxf(0.0, sw) * 12), "lh": Vector2(-36 - sw * 20, -122), "rh": Vector2(36 + sw * 20, -122), "face": {"gaze": Vector2(2, 0)}}
		if k > 0.8:
			pose["rot"] = (k - 0.8) / 0.2 * 0.25
			pose["rh"] = Vector2(8, -150)
			pose["face"] = {"brow": 1.0, "smile": -0.6, "eyes": "wide"}
	elif phase == "fall":
		var k2 := clampf(since() / 0.45, 0.0, 1.0)
		pose = {"rot": lerpf(0.25, PI / 2.0, k2 * k2), "face": {"eyes": "closed", "smile": -0.3}}
	else:
		var eyes := "open" if (phase == "end" and revived and since() > 1.2) else "closed"
		pose = {"rot": PI / 2.0, "face": {"eyes": eyes, "smile": 0.0}, "lh": Vector2(-60, -110), "rh": Vector2(58, -112)}
		Art.oval(self, jp + Vector2(118, 14), Vector2(140, 12), Color(0, 0, 0, 0.1))
	if not down:
		Art.oval(self, jp + Vector2(0, 2), Vector2(40, 8), Color(0, 0, 0, 0.12))
	Art.person(self, jp, 0.9, man, pose)
	for i in [0, 3]:
		_draw_bystander(i, worried, happy)

	# thought bubbles while nobody acts
	if down and caller < 0 and phase != "shout":
		var which := int(t / 2.4) % people.size()
		var a := clampf(sin(fmod(t, 2.4) / 2.4 * PI) * 2.2, 0.0, 1.0)
		var bp: Vector2 = people[which]["p"]
		Art.bubble(self, bp + Vector2(0, -238), people[which]["think"], 17, true, 200.0, a)
	if phase == "shout":
		Art.bubble(self, Vector2(690, 340), "Somebody call an ambulance!", 18, false, 260.0, clampf(since() * 5.0, 0.0, 1.0))
	if caller >= 0 and (phase == "delegate2" or phase == "sent"):
		var cp: Vector2 = people[caller]["p"]
		Art.bubble(self, cp + Vector2(0, -238), "Calling %s!" % number, 18, false, 200.0)
	if phase == "sent" and runner >= 0:
		var rp: Vector2 = people[runner]["p"]
		Art.bubble(self, rp + Vector2(_run_dx(runner), -238), "On it!", 18, false, 120.0)


func _run_dx(i: int) -> float:
	if i != runner:
		return 0.0
	var pp: Vector2 = people[i]["p"]
	var dir := 1.0 if pp.x > 640.0 else -1.0
	return dir * maxf(t - run_t - 0.5, 0.0) * 330.0


func _draw_bystander(i: int, worried: bool, happy: bool) -> void:
	var b: Dictionary = people[i]
	var bp: Vector2 = b["p"]
	var dx := _run_dx(i)
	if absf(dx) > 700.0 and phase != "end":
		return
	if phase == "end" and i == runner:
		dx = 0.0
	var gz := Vector2(clampf((640.0 - bp.x) / 160.0, -3.0, 3.0), 1.5)
	var pose := {"face": {"gaze": gz, "brow": 0.8 if worried else 0.0, "smile": -0.35 if worried else 0.3}}
	if happy:
		pose["face"] = {"gaze": gz, "smile": 0.9}
	if i == caller and not happy:
		pose["rh"] = Vector2(26, -214)
	if i == runner and absf(dx) > 0.0:
		var sw := sin(t * 16.0)
		pose["lf"] = Vector2(-12 + sw * 28, -9 - maxf(0.0, -sw) * 12)
		pose["rf"] = Vector2(12 - sw * 28, -9 - maxf(0.0, sw) * 12)
	var pickable := (phase == "delegate" or phase == "delegate2") and i != caller
	if pickable:
		var hov := Rect2(bp.x - 52, bp.y - 235, 104, 250).has_point(mouse)
		var pul := 0.5 + 0.5 * sin(t * 5.0 + i)
		Art.oval(self, bp + Vector2(0, 4), Vector2(58 + pul * 6, 15 + pul * 2), Color(Art.CORAL, 0.75 if hov else 0.35))
		Art.oval(self, bp + Vector2(0, 4), Vector2(46, 11), Color("e9e3d3"))
		if hov:
			Art.rrect(self, Rect2(bp.x - 100, bp.y + 22, 200, 30), Art.INK, 15)
			Art.text_c(self, Vector2(bp.x, bp.y + 37), "“You, %s”" % b["tag"], 15, Color.WHITE)
	else:
		Art.oval(self, bp + Vector2(dx, 3), Vector2(40, 8), Color(0, 0, 0, 0.12))
	Art.person(self, bp + Vector2(dx, 0), 0.9, b["look"], pose)


func _draw_close() -> void:
	draw_rect(Rect2(0, 0, 1280, 720), Color("e9e3d3"))
	for i in 14:
		var px := fposmod(i * 197.3, 1280.0)
		var py := fposmod(i * 131.7 + 40.0, 720.0)
		Art.oval(self, Vector2(px, py), Vector2(16 + i % 3 * 6, 6 + i % 2 * 3), Color("ded7c4"))
	draw_rect(Rect2(0, 0, 70, 720), Color("97cb8a"))
	for i in 9:
		Art.disc(self, Vector2(70, i * 90.0 + 20.0), 26.0, Color("97cb8a"))

	var skin: Color = man["skin"]
	var shirt: Color = man["top"]
	var gasp := phase == "breath" and (fmod(since(), 2.3) > 1.55 and fmod(since(), 2.3) < 2.0)
	var jolt := 0.0
	if t - shock_t < 0.25:
		jolt = sin((t - shock_t) * 50.0) * 6.0
	var o := Vector2(0, jolt)
	# shadow
	Art.rrect(self, Rect2(C.x - 124, C.y - 136, 260, 350).grow(2), Color(0, 0, 0, 0.08), 70)
	# legs / shorts running off the bottom
	Art.limb(self, C + Vector2(-52, 230) + o, C + Vector2(-60, 480), 84, skin.darkened(0.04))
	Art.limb(self, C + Vector2(52, 230) + o, C + Vector2(60, 480), 84, skin.darkened(0.04))
	Art.rrect(self, Rect2(C.x - 108, C.y + 150, 216, 150), Color("3d4b5e"), 40)
	# arms
	for sx: float in [-1.0, 1.0]:
		Art.limb(self, C + Vector2(sx * 104, -104) + o, C + Vector2(sx * 150, 20) + o, 50, shirt.darkened(0.08))
		Art.limb(self, C + Vector2(sx * 150, 20) + o, C + Vector2(sx * 158, 150) + o, 42, skin)
		Art.disc(self, C + Vector2(sx * 158, 168) + o, 24, skin)
	# neck + torso
	draw_rect(Rect2(C.x - 26, C.y - 176, 52, 50), skin.darkened(0.1))
	var tr := _torso()
	tr.position += o
	if gasp:
		tr = tr.grow(2.0)
	if bare:
		Art.rrect(self, tr, skin, 64)
		draw_arc(C + Vector2(-48, -84) + o, 40, PI * 1.15, PI * 1.85, 12, skin.darkened(0.16), 4.0, true)
		draw_arc(C + Vector2(48, -84) + o, 40, PI * 1.15, PI * 1.85, 12, skin.darkened(0.16), 4.0, true)
		draw_line(C + Vector2(0, -80) + o, C + Vector2(0, 40) + o, skin.darkened(0.08), 3.0, true)
		Art.poly(self, PackedVector2Array([tr.position + Vector2(0, 60), tr.position + Vector2(44, 6), tr.position + Vector2(30, 120), tr.position + Vector2(40, 338), tr.position + Vector2(6, 300)]), shirt)
		Art.poly(self, PackedVector2Array([tr.position + Vector2(224, 60), tr.position + Vector2(180, 6), tr.position + Vector2(194, 120), tr.position + Vector2(184, 338), tr.position + Vector2(218, 300)]), shirt)
	else:
		Art.rrect(self, tr, shirt, 64)
		draw_arc(C + Vector2(0, -150) + o, 34, 0.15 * PI, 0.85 * PI, 12, shirt.darkened(0.15), 5.0, true)
	# head
	var face := {"eyes": "closed", "smile": -0.1}
	if gasp:
		face["mouth"] = "gasp"
	Art.head(self, Transform2D(0.0, Vector2(2.0, 2.0), 0.0, C + Vector2(0, -222) + o), man, face)
	if gasp:
		Art.text(self, C + Vector2(70, -205), "…hhk…", 22, Art.INK_SOFT)

	# placed pads + wires
	if bare:
		for i in 2:
			if int(pads[i]["placed"]) >= 0:
				_draw_pad(i, o)
		if (pad_hint or drag >= 0) and phase == "pads":
			for k in 2:
				var taken := false
				for q in 2:
					if int(pads[q]["placed"]) == k:
						taken = true
				if not taken:
					var a := 0.35 + 0.25 * sin(t * 5.0)
					var rr := Rect2(targets[k] - PAD_SIZE * 0.5, PAD_SIZE)
					draw_rect(rr, Color(Art.CORAL, a), false, 3.0)

	# phase-specific overlays
	if phase == "resp":
		for sx: float in [-1.0, 1.0]:
			var sp := C + Vector2(sx * 98, -112)
			var pul := fmod(t * 1.3 + (0.3 if sx > 0 else 0.0), 1.0)
			Art.ring(self, sp, 28.0 + pul * 26.0, Color(Art.CORAL, 1.0 - pul), 4.0)
	if phase == "resp2" or (phase == "resp" and t - tapped < 0.4):
		var sh := sin(t * 40.0) * 5.0 * maxf(0.0, 1.0 - since() * 2.0)
		_draw_hand(C + Vector2(-98 + sh, -112), 0.8)
		_draw_hand(C + Vector2(98 + sh, -112), 0.8)
		Art.bubble(self, Vector2(690, 250), "Hey! Can you hear me?!", 20, false, 300.0, clampf(since() * 6.0, 0.0, 1.0))
		if since() > 0.8:
			Art.text(self, Vector2(590, 300), "…nothing.", 22, Art.INK_SOFT)
	if phase == "breath":
		var sec := mini(int(since()) + 1, 5)
		Art.card(self, Rect2(730, 190, 400, 150))
		Art.text(self, Vector2(760, 232), "WATCHING HIS CHEST", 14, Art.INK_SOFT, true)
		for i in 5:
			Art.disc(self, Vector2(772 + i * 34, 268), 10, Art.TEAL if i < sec else Color(Art.INK, 0.12))
		Art.text(self, Vector2(760, 314), "Look, listen, feel — no more than 10 seconds.", 16, Art.INK)
	if phase == "hands":
		var d := mouse - C
		if _torso().grow(30).has_point(mouse):
			Art.ring(self, mouse, 30.0, Color(Art.CORAL, 0.8), 4.0)
			Art.disc(self, mouse, 5.0, Art.CORAL)
		Art.card(self, Rect2(730, 200, 420, 110))
		Art.para(self, Vector2(758, 222), "Your hands need to squeeze his heart between the breastbone and the spine.", 370.0, 18, Art.INK)
		if d.length() < 0.0:
			pass

	if hands_on and (cpr_on or phase == "ready" or phase == "aed_here"):
		Art.disc(self, C, 62.0 + depth * 8.0, Color(0, 0, 0, 0.05 + 0.1 * depth))
		_draw_cpr_hands(1.0 - depth * 0.08)
	if cpr_on:
		_draw_gauges()
	if phase == "aed_here" or phase == "pads" or phase == "analyse" or phase == "shock" or phase == "shocked":
		_draw_aed()
	if phase == "analyse" and t - word_t < 1.2:
		Art.text_c(self, C + Vector2(0, -30), word, 34, word_col, true)


func _draw_hand(p: Vector2, s: float) -> void:
	var skin: Color = you["skin"]
	Art.oval(self, p, Vector2(36, 30) * s, skin)
	for i in 4:
		Art.limb(self, p + Vector2(-20 + i * 13, -14) * s, p + Vector2(-24 + i * 15, -40) * s, 12 * s, skin)
	Art.limb(self, p + Vector2(-28, 4) * s, p + Vector2(-46, -8) * s, 12 * s, skin)


func _draw_cpr_hands(k: float) -> void:
	var skin: Color = you["skin"]
	var sleeve: Color = you["top"]
	Art.limb(self, C + Vector2(-330, 96), C + Vector2(-58, 4), 46, sleeve)
	Art.limb(self, C + Vector2(-330, 30), C + Vector2(-58, -6), 46, sleeve.darkened(0.08))
	Art.limb(self, C + Vector2(-70, -2), C + Vector2(-34, 0), 38, skin.darkened(0.05))
	Art.oval(self, C + Vector2(2, 6), Vector2(50, 38) * k, skin.darkened(0.1))
	Art.oval(self, C + Vector2(-2, -2), Vector2(46, 34) * k, skin)
	for i in 4:
		var a := -0.5 + i * 0.33
		draw_line(C + Vector2(20, a * 30.0) * k, C + Vector2(42, a * 40.0) * k, skin.darkened(0.16), 2.5, true)


func _draw_pad(i: int, o: Vector2 = Vector2.ZERO) -> void:
	var pos: Vector2 = pads[i]["pos"]
	pos += o
	var home: Vector2 = pads[i]["home"]
	# wire back to the device
	var pts := PackedVector2Array()
	var a := pos + Vector2(PAD_SIZE.x * 0.5 - 6, 0)
	var b := home + Vector2(0, 60)
	for k in 17:
		var u := k / 16.0
		var m := a.lerp(b, u) + Vector2(0, sin(u * PI) * 46.0)
		pts.append(m)
	if pos.distance_to(home) > 4.0:
		draw_polyline(pts, Color("394656"), 3.0, true)
	var r := Rect2(pos - PAD_SIZE * 0.5, PAD_SIZE)
	Art.rrect(self, r.grow(2), Color("394656"), 12)
	Art.rrect(self, r, Color.WHITE, 10)
	# the little picture printed on the pad
	var ic := pos + Vector2(-8, 2)
	Art.rrect(self, Rect2(ic.x - 17, ic.y - 22, 34, 48), Color("d9dee4"), 10)
	Art.disc(self, ic + Vector2(0, -31), 8.0, Color("d9dee4"))
	var spot := ic + (Vector2(-8, -11) if i == 0 else Vector2(11, 10))
	draw_rect(Rect2(spot.x - 7, spot.y - 6, 14, 12), Art.CORAL)
	Art.text(self, pos + Vector2(22, 8), str(i + 1), 20, Art.INK, true)


func _draw_gauges() -> void:
	var cardr := Rect2(734, 80, 506, 492)
	Art.card(self, cardr)
	var beat := fmod(cpr_time * TEMPO / 60.0, 1.0)
	var pulse := pow(1.0 - beat, 3.0)
	var ga := 1.0 if guided else clampf(1.0 - (cpr_time - guide_off) * 1.2, 0.0, 1.0)
	var hc := Vector2(800, 146)
	if ga > 0.0:
		Art.ring(self, hc, 36.0 + (1.0 - pulse) * 22.0, Color(Art.CORAL, pulse * ga * 0.8), 3.0)
	Art.heart(self, hc, 30.0 + pulse * 9.0 * ga, Color(Art.CORAL, 0.22 + 0.78 * ga))
	Art.text(self, Vector2(858, 136), "FOLLOW THE PULSE" if guided else "KEEP THE RHYTHM GOING", 14, Art.INK_SOFT, true)
	Art.text(self, Vector2(858, 168), "%d compressions" % count, 24, Art.INK, true)

	# rate dial: 60..160 per minute across the top half
	var dc := Vector2(1018, 396)
	var R := 140.0
	draw_arc(dc, R, PI, TAU, 48, Color(Art.INK, 0.12), 26.0, true)
	draw_arc(dc, R, _ang(100.0), _ang(120.0), 16, Art.TEAL, 26.0, true)
	var na := _ang(bpm_shown)
	draw_line(dc, dc + Vector2(cos(na), sin(na)) * (R - 4.0), Art.INK, 6.0, true)
	Art.disc(self, dc, 12.0, Art.INK)
	Art.text_c(self, dc + Vector2(-R, 26), "slow", 15, Art.INK_SOFT)
	Art.text_c(self, dc + Vector2(R, 26), "fast", 15, Art.INK_SOFT)
	Art.text_c(self, dc + Vector2(0, -R - 34), "100–120 a minute", 15, Art.TEAL, true)
	if bpm > 0.0:
		Art.text_c(self, dc + Vector2(0, 42), "%d a minute" % int(round(bpm)), 20, Art.INK, true)
	else:
		Art.text_c(self, dc + Vector2(0, 42), "—", 20, Art.INK_SOFT, true)
	if t - word_t < 0.9:
		var ww := Art.text_w(word, 26, true) + 44.0
		Art.rrect(self, Rect2(dc.x - ww * 0.5, dc.y + 66, ww, 44), word_col, 22)
		Art.text_c(self, dc + Vector2(0, 88), word, 26, Color.WHITE, true)

	# depth
	var bar := Rect2(764, 236, 36, 200)
	Art.text(self, Vector2(758, 226), "DEPTH", 13, Art.INK_SOFT, true)
	Art.rrect(self, bar, Color(Art.INK, 0.1), 10)
	Art.rrect(self, Rect2(bar.position.x, bar.position.y + 140, 36, 60), Color(Art.TEAL, 0.3), 10)
	if depth > 0.03:
		Art.rrect(self, Rect2(bar.position.x, bar.position.y, 36, maxf(200.0 * depth, 14.0)), Art.CORAL, 10)
	Art.text_c(self, Vector2(782, 456), "5–6 cm", 13, Art.TEAL, true)

	# progress
	var pr := Rect2(764, 544, 446, 10)
	Art.text(self, Vector2(764, 534), "Ambulance on its way" if cpr_len > 20.0 else "Ambulance almost here", 14, Art.INK_SOFT)
	Art.rrect(self, pr, Color(Art.INK, 0.1), 5)
	Art.rrect(self, Rect2(pr.position, Vector2(maxf(pr.size.x * cpr_time / cpr_len, 10.0), 10)), Art.TEAL, 5)


func _ang(b: float) -> float:
	return PI + PI * clampf((b - 60.0) / 100.0, 0.0, 1.0)


func _draw_aed() -> void:
	var body := Rect2(770, 104, 440, 330)
	Art.rrect(self, Rect2(body.position + Vector2(0, 8), body.size), Color(0, 0, 0, 0.14), 30)
	Art.rrect(self, body, Color("2f9b6b"), 30)
	Art.rrect(self, Rect2(930, 84, 120, 34), Color("237a54"), 14)
	Art.rrect(self, Rect2(950, 96, 80, 12), Color("ecdcb9"), 6)
	var screen := Rect2(798, 136, 384, 96)
	Art.rrect(self, screen, Color("16222e"), 12)
	var msg := "SWITCHED ON"
	var sub := "Follow the voice prompts"
	match phase:
		"pads":
			msg = "ATTACH PADS"
			sub = "to the patient's bare chest"
		"analyse":
			msg = "ANALYSING RHYTHM"
			sub = "DO NOT TOUCH THE PATIENT"
		"shock":
			msg = "SHOCK ADVISED"
			sub = "STAND CLEAR — press the button"
		"shocked":
			msg = "SHOCK DELIVERED"
			sub = "Continue CPR"
	Art.text(self, screen.position + Vector2(18, 38), msg, 24, Color("9ff0c0"), true)
	Art.text(self, screen.position + Vector2(18, 70), sub, 16, Color("9ff0c0"))
	if phase == "analyse":
		var pts := PackedVector2Array()
		for i in 60:
			var x := screen.position.x + 250 + i * 2.0
			var y := screen.position.y + 64 + sin(i * 0.9 + t * 14.0) * 7.0 + sin(i * 2.3 + t * 23.0) * 5.0
			pts.append(Vector2(x, y))
		draw_polyline(pts, Color("9ff0c0"), 2.0, true)
	# pad tray
	Art.rrect(self, Rect2(800, 262, 240, 118), Color("237a54"), 16)
	for i in 2:
		if int(pads[i]["placed"]) < 0 and i != drag:
			_draw_pad(i)
	# shock button
	var flash := phase == "shock" and fmod(t * 2.6, 1.0) < 0.55
	if flash:
		Art.disc(self, SHOCK_BTN, 62.0, Color(1.0, 0.7, 0.2, 0.35))
	Art.disc(self, SHOCK_BTN, 50.0, Color("f08a24") if (flash or phase == "shocked") else Color("9c6a35"))
	Art.poly(self, PackedVector2Array([SHOCK_BTN + Vector2(6, -30), SHOCK_BTN + Vector2(-16, 4), SHOCK_BTN + Vector2(-2, 4), SHOCK_BTN + Vector2(-8, 30), SHOCK_BTN + Vector2(16, -6), SHOCK_BTN + Vector2(2, -6)]), Color.WHITE)
	Art.text_c(self, SHOCK_BTN + Vector2(0, 68), "SHOCK", 14, Color.WHITE, true)
	Art.text(self, Vector2(804, 412), "Pads on bare, dry skin", 14, Color("d5f3e3"))
	if drag >= 0:
		_draw_pad(drag)
