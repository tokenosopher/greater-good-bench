extends Control

# All art, interaction, and sound are generated locally; no assets are loaded.
const INK = Color("263e38")
const MUTED = Color("6d7b70")
const PAPER = Color("f5f1e7")
const WHITE = Color("fffcf5")
const GREEN = Color("285c4d")
const LIGHT_GREEN = Color("e2eadb")
const LINE = Color("d9ddce")
const ORANGE = Color("c96b4d")
const GOLD = Color("dfac60")
const MAP_RECT = Rect2(44, 218, 912, 488)
const POSITIONS = [Vector2(217, 364), Vector2(494, 325), Vector2(778, 365), Vector2(788, 557), Vector2(493, 591), Vector2(213, 559)]
const NAMES = ["Mara", "Ivo", "June", "Noah", "Asha", "Eli"]
const PLACES = ["COMMUNITY KITCHEN", "THE REPAIR SHOP", "WILLOW LIBRARY", "ROOFTOP HOMES", "POCKET GARDEN", "CORNER CLINIC"]
const COLORS = [Color("ca795a"), Color("dfb665"), Color("6b9c9b"), Color("9294b0"), Color("7f9a66"), Color("d69b84")]
const SKIN = [Color("bb7959"), Color("dca97c"), Color("b77a55"), Color("e0b58e"), Color("9f684c"), Color("c89570")]
const HAIR = [Color("3c3d32"), Color("695c47"), Color("333f3a"), Color("8a5b3b"), Color("363a30"), Color("42483d")]
const NEEDS = [
	"The kitchen is running low, and the lunch queue keeps growing.",
	"The shop is full of broken fans. Ivo cannot repair them all alone.",
	"Heat advice has arrived, but it is not reaching everyone on the block.",
	"Noah has barely left the apartment this week. The days feel very long.",
	"The garden is thirsty. Carrying water in this heat is wearing Asha out.",
	"Eli is helping everyone else, with very little time left to recover."
]
const VOICES = [
	'“We have food nearby. What we need is a way to share it before it goes to waste.”',
	'“I could teach the repairs. A few extra hands would go further than new parts.”',
	'“Not everyone reads these notices. A call in a familiar language would help.”',
	'“I miss being useful. I would love to help someone, if they asked.”',
	'“The water is too heavy for one person. Could we take turns in the cool morning?”',
	'“I do not need more things. I need someone to cover the errands so I can rest.”'
]
const DIRECT_NAMES = ["Bring a food parcel", "Buy replacement parts", "Print more leaflets", "Drop off a care package", "Deliver extra water", "Bring clinic supplies"]
const TAILORED_NAMES = ["Organize a food swap", "Host a repair circle", "Start a language phone tree", "Invite Noah to lend a hand", "Make a watering rota", "Cover Eli’s errands"]
const TAILORED_DESCS = ["Mara +16 · Eli +4 · 1 supply", "Ivo +16 · Noah +4 · 1 supply", "June +16 · everyone else +2", "Noah +16 · Mara +4", "Asha +16 · Ivo +4", "Eli +16 · Asha +4"]
const PARTNERS = [5, 3, -1, 0, 1, 4]
const PROJECT_NAMES = ["A canopy for everyone", "A neighborhood sharing shelf", "A buddy network"]
const PROJECT_SHORT = ["Shade canopy", "Sharing shelf", "Buddy network"]
const PROJECT_DESCS = ["A cool place to gather. Every neighbor loses 1 less wellbeing each night.", "Useful things, freely shared. Receive 1 extra supply every morning.", "Nobody disappears from view. The least steady neighbor gains +5 each morning."]
const DAY_NAMES = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
const TEMPS = [26, 29, 34, 28, 30, 36, 29]
const NIGHT_LOSS = [7, 7, 10, 7, 8, 11, 0]

var font: Font
var day = 1
var hours = 4
var supplies = 5
var wellbeing = [53, 45, 57, 48, 42, 51]
var listened = [false, false, false, false, false, false]
var helped = [false, false, false, false, false, false]
var projects = [false, false, false]
var selected = 0
var mode = "play"
var previous_mode = "play"
var buttons: Array = []
var hover = ""
var focus_id = ""
var elapsed = 0.0
var toast = ""
var toast_time = 0.0
var floats: Array = []
var actions_taken = 0
var conversations = 0
var targeted_help = 0
var sound_on = true
var audio_player: AudioStreamPlayer
var chime: AudioStreamWAV
var click_sound: AudioStreamWAV

func _ready() -> void:
	font = ThemeDB.fallback_font
	mouse_filter = Control.MOUSE_FILTER_STOP
	audio_player = AudioStreamPlayer.new()
	add_child(audio_player)
	chime = make_tone([523.25, 659.25, 783.99], 0.34)
	click_sound = make_tone([392.0, 523.25], 0.14)
	queue_redraw()

func _process(delta: float) -> void:
	elapsed += delta
	if toast_time > 0:
		toast_time -= delta
	for f in floats:
		f["age"] += delta
	floats = floats.filter(func(f): return f["age"] < 1.7)
	queue_redraw()

func make_tone(notes: Array, duration: float) -> AudioStreamWAV:
	var wave = AudioStreamWAV.new()
	wave.format = AudioStreamWAV.FORMAT_16_BITS
	wave.mix_rate = 22050
	var count = int(duration * 22050)
	var data = PackedByteArray()
	data.resize(count * 2)
	for i in range(count):
		var t = float(i) / 22050.0
		var n = mini(int(t / duration * notes.size()), notes.size() - 1)
		var local_t = fmod(t, duration / notes.size())
		var env = minf(local_t * 150.0, 1.0) * exp(-local_t * 18.0)
		var v = sin(TAU * float(notes[n]) * t) * env * 0.11
		data.encode_s16(i * 2, int(v * 32767))
	wave.data = data
	return wave

func play_sound(success: bool = false) -> void:
	if sound_on:
		audio_player.stream = chime if success else click_sound
		audio_player.play()

func _input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		var p = event.position
		hover = ""
		for b in buttons:
			if b.rect.has_point(p) and b.enabled:
				hover = b.id
		mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND if hover != "" else Control.CURSOR_ARROW
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var p = event.position
		for i in range(buttons.size() - 1, -1, -1):
			var b = buttons[i]
			if b.rect.has_point(p):
				if b.enabled:
					activate(b.id)
				return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_TAB:
			var enabled = buttons.filter(func(b): return b.enabled)
			if enabled.size() > 0:
				var index = -1
				for i in enabled.size():
					if enabled[i].id == focus_id:
						index = i
				index = posmod(index + (-1 if event.shift_pressed else 1), enabled.size())
				focus_id = enabled[index].id
			get_viewport().set_input_as_handled()
		elif event.keycode == KEY_ENTER and focus_id != "":
			activate(focus_id)
		elif event.keycode == KEY_ESCAPE:
			if mode in ["help", "night"]:
				mode = previous_mode if mode == "help" else "play"
		elif event.keycode == KEY_SLASH or event.keycode == KEY_F1:
			activate("help")
		elif mode == "play":
			if event.keycode >= KEY_1 and event.keycode <= KEY_6:
				activate("person_" + str(event.keycode - KEY_1))
			elif event.keycode == KEY_L:
				activate("listen")
			elif event.keycode == KEY_H:
				activate("direct")
			elif event.keycode == KEY_P:
				activate("tailored")
			elif event.keycode == KEY_C:
				activate("commons")
			elif event.keycode == KEY_SPACE:
				activate("end_day")
		elif mode == "result" and event.keycode == KEY_R:
			activate("restart")

func activate(id: String) -> void:
	focus_id = ""
	if id == "sound":
		sound_on = not sound_on
		play_sound()
		return
	if id == "help":
		if mode == "help":
			mode = previous_mode
		else:
			previous_mode = mode
			mode = "help"
		play_sound()
		return
	if id == "close_help":
		mode = previous_mode
		return
	if mode == "help":
		return
	if id == "restart":
		restart()
		return
	if mode == "result":
		return
	if id == "back":
		mode = "play"
		return
	if id == "next_day" and mode == "night":
		if day == 7:
			mode = "result"
			play_sound(true)
		else:
			advance_day()
		return
	if mode != "play":
		return
	if id.begins_with("person_"):
		selected = int(id.trim_prefix("person_"))
		play_sound()
	elif id == "commons":
		selected = -1
		play_sound()
	elif id == "listen" and selected >= 0:
		if hours < 1 or listened[selected] or helped[selected]:
			return
		hours -= 1
		listened[selected] = true
		conversations += 1
		actions_taken += 1
		gain(selected, 3)
		message("A little understanding opens a better possibility.")
		play_sound(true)
	elif id in ["direct", "tailored"] and selected >= 0:
		if helped[selected] or hours < 1:
			return
		var tailored = id == "tailored"
		var cost = (1 if selected < 2 else 0) if tailored else 2
		if (tailored and not listened[selected]) or supplies < cost:
			return
		hours -= 1
		supplies -= cost
		helped[selected] = true
		actions_taken += 1
		gain(selected, 16 if tailored else 12)
		if tailored:
			targeted_help += 1
			if PARTNERS[selected] == -1:
				for i in 6:
					if i != selected:
						gain(i, 2)
			else:
				gain(PARTNERS[selected], 4)
			message("Care travels. " + NAMES[selected] + "’s plan helped a neighbor, too.")
		else:
			message(NAMES[selected] + " has what they need for today.")
		play_sound(true)
	elif id.begins_with("build_"):
		var index = int(id.trim_prefix("build_"))
		if projects[index] or hours < 2 or supplies < 2:
			return
		hours -= 2
		supplies -= 2
		projects[index] = true
		actions_taken += 1
		for i in 6:
			gain(i, 3)
		message(PROJECT_SHORT[index] + " is ready. Everyone gains +3 wellbeing.")
		play_sound(true)
	elif id == "end_day":
		mode = "night"
		play_sound()

func gain(index: int, amount: int) -> void:
	var before = wellbeing[index]
	wellbeing[index] = mini(100, wellbeing[index] + amount)
	var actual = wellbeing[index] - before
	if actual > 0:
		floats.append({"pos": POSITIONS[index] + Vector2(35, -70), "text": "+" + str(actual), "age": 0.0})

func message(value: String) -> void:
	toast = value
	toast_time = 4.8

func advance_day() -> void:
	var loss = maxi(0, NIGHT_LOSS[day - 1] - (1 if projects[0] else 0))
	for i in 6:
		wellbeing[i] = maxi(0, wellbeing[i] - loss)
	if projects[2]:
		var lowest = wellbeing.find(wellbeing.min())
		wellbeing[lowest] = mini(100, wellbeing[lowest] + 5)
	day += 1
	hours = 4
	supplies = mini(9, supplies + 3 + (1 if projects[1] else 0))
	helped = [false, false, false, false, false, false]
	mode = "play"
	selected = wellbeing.find(wellbeing.min())
	message("A new morning. +" + str(4 if projects[1] else 3) + " supplies. " + NAMES[selected] + " could use a hand.")
	play_sound()

func restart() -> void:
	day = 1
	hours = 4
	supplies = 5
	wellbeing = [53, 45, 57, 48, 42, 51]
	listened = [false, false, false, false, false, false]
	helped = [false, false, false, false, false, false]
	projects = [false, false, false]
	selected = 0
	mode = "play"
	conversations = 0
	actions_taken = 0
	targeted_help = 0
	toast_time = 0
	floats.clear()
	play_sound()

func _draw() -> void:
	buttons.clear()
	draw_rect(Rect2(0, 0, 1440, 900), PAPER)
	draw_header()
	draw_map()
	draw_resources()
	draw_detail()
	draw_footer()
	for f in floats:
		var alpha = clampf(1.7 - f.age, 0, 1)
		var point = f.pos + Vector2(0, -f.age * 30)
		round_rect(Rect2(point - Vector2(7, 24), Vector2(53, 34)), Color(1, 0.99, 0.95, alpha), 17)
		text_at(point, f.text, 23, Color(0.15, 0.36, 0.29, alpha))
	if toast_time > 0 and mode == "play":
		var w = minf(870, font.get_string_size(toast, HORIZONTAL_ALIGNMENT_LEFT, -1, 16).x + 52)
		round_rect(Rect2(500 - w / 2, 654, w, 39), GREEN, 19)
		center_text(Vector2(500, 680), toast, 16, WHITE)
	if mode == "help":
		draw_help()
	elif mode == "night":
		draw_night()
	elif mode == "result":
		draw_result()

func text_at(pos: Vector2, value: String, size: int = 18, color: Color = INK) -> void:
	draw_string(font, pos, value, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)

func center_text(pos: Vector2, value: String, size: int = 18, color: Color = INK) -> void:
	var w = font.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	text_at(pos - Vector2(w / 2, 0), value, size, color)

func right_text(pos: Vector2, value: String, size: int = 18, color: Color = INK) -> void:
	var w = font.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	text_at(pos - Vector2(w, 0), value, size, color)

func paragraph(pos: Vector2, value: String, width: float, size: int = 17, color: Color = MUTED, spacing: float = 1.45) -> float:
	var line = ""
	var y = pos.y
	for word in value.split(" "):
		var test = line + (" " if line != "" else "") + word
		if font.get_string_size(test, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x > width and line != "":
			text_at(Vector2(pos.x, y), line, size, color)
			y += size * spacing
			line = word
		else:
			line = test
	if line != "":
		text_at(Vector2(pos.x, y), line, size, color)
	return y + size * spacing

func round_rect(rect: Rect2, color: Color, radius: int = 12, border_color: Color = Color.TRANSPARENT, border: int = 0) -> void:
	var style = StyleBoxFlat.new()
	style.bg_color = color
	style.corner_radius_top_left = radius
	style.corner_radius_top_right = radius
	style.corner_radius_bottom_left = radius
	style.corner_radius_bottom_right = radius
	style.border_color = border_color
	style.set_border_width_all(border)
	draw_style_box(style, rect)

func line(a: Vector2, b: Vector2, color: Color = LINE, width: float = 1.0) -> void:
	draw_line(a, b, color, width, true)

func ellipse(pos: Vector2, radius: Vector2, color: Color) -> void:
	var pts = PackedVector2Array()
	for i in 40:
		var angle = TAU * i / 40.0
		pts.append(pos + Vector2(cos(angle) * radius.x, sin(angle) * radius.y))
	draw_colored_polygon(pts, color)

func polygon(points: Array, color: Color) -> void:
	draw_colored_polygon(PackedVector2Array(points), color)

func hit(id: String, rect: Rect2, enabled: bool = true) -> void:
	buttons.append({"id": id, "rect": rect, "enabled": enabled})
	if focus_id == id and enabled:
		round_rect(rect.grow(4), Color.TRANSPARENT, 13, GOLD, 3)

func is_over(id: String) -> bool:
	return hover == id or focus_id == id

func pill(rect: Rect2, value: String, bg: Color, fg: Color, size: int = 13) -> void:
	round_rect(rect, bg, int(rect.size.y / 2))
	center_text(Vector2(rect.get_center().x, rect.position.y + rect.size.y * 0.5 + size * 0.35), value, size, fg)

func button(id: String, rect: Rect2, title: String, subtitle: String = "", style: String = "plain", enabled: bool = true, suffix: String = "") -> void:
	var bg = WHITE
	var fg = INK
	var stroke = LINE
	if style == "primary":
		bg = GREEN
		fg = WHITE
		stroke = GREEN
	elif style == "soft":
		bg = LIGHT_GREEN
		stroke = LIGHT_GREEN
	if not enabled:
		bg = Color("eeeee5")
		fg = Color("92988b")
		stroke = Color("e4e5db")
	elif is_over(id):
		bg = bg.lightened(0.06) if style == "primary" else Color("e8eddf")
		stroke = GREEN
	round_rect(rect, bg, 12, stroke, 1)
	var y = rect.position.y + (rect.size.y / 2 + 6 if subtitle == "" else 27)
	text_at(Vector2(rect.position.x + 18, y), title, 17, fg)
	if suffix != "":
		right_text(Vector2(rect.end.x - 17, y), suffix, 14, fg)
	if subtitle != "":
		text_at(Vector2(rect.position.x + 18, rect.position.y + 49), subtitle, 13, fg if style == "primary" else MUTED)
	hit(id, rect, enabled)

func icon(kind: String, p: Vector2, color: Color = INK, s: float = 1.0) -> void:
	if kind == "clock":
		draw_arc(p, 8 * s, 0, TAU, 32, color, 1.8 * s, true)
		line(p, p + Vector2(0, -4) * s, color, 1.8 * s)
		line(p, p + Vector2(4, 2) * s, color, 1.8 * s)
	elif kind == "box":
		var a = p + Vector2(-8, -5) * s
		var b = p + Vector2(8, 5) * s
		draw_rect(Rect2(a, b - a), color, false, 1.7 * s)
		line(a, p + Vector2(0, -10) * s, color, 1.7 * s)
		line(p + Vector2(0, -10) * s, Vector2(b.x, a.y), color, 1.7 * s)
		line(p + Vector2(0, -5) * s, p + Vector2(0, 5) * s, color, 1.7 * s)
	elif kind == "check":
		line(p + Vector2(-5, 0) * s, p + Vector2(-1, 4) * s, color, 2 * s)
		line(p + Vector2(-1, 4) * s, p + Vector2(7, -5) * s, color, 2 * s)
	elif kind == "leaf":
		ellipse(p + Vector2(3, -3) * s, Vector2(7, 4) * s, color)
		line(p + Vector2(-6, 7) * s, p + Vector2(7, -6) * s, color, 1.8 * s)
	elif kind == "sun":
		draw_circle(p, 5 * s, color)
		for i in 8:
			var v = Vector2.from_angle(TAU * i / 8)
			line(p + v * 8 * s, p + v * 11 * s, color, 1.5 * s)
	elif kind == "heart":
		draw_circle(p + Vector2(-3, -2) * s, 4 * s, color)
		draw_circle(p + Vector2(3, -2) * s, 4 * s, color)
		polygon([p + Vector2(-7, -1) * s, p + Vector2(7, -1) * s, p + Vector2(0, 7) * s], color)

func draw_header() -> void:
	round_rect(Rect2(44, 30, 44, 44), GREEN, 12)
	polygon([Vector2(54, 53), Vector2(66, 42), Vector2(78, 53), Vector2(78, 65), Vector2(54, 65)], PAPER)
	draw_rect(Rect2(63, 55, 7, 10), GOLD)
	text_at(Vector2(101, 51), "COMMON GROUND", 23, GREEN)
	text_at(Vector2(102, 72), "Small acts. Shared futures.", 13, MUTED)
	text_at(Vector2(521, 45), "YOUR WEEK OF CARE", 11, MUTED)
	for d in 7:
		var x = 532 + d * 40
		var color = GREEN if d < day else Color("e1e3d6")
		draw_circle(Vector2(x, 66), 12 if d == day - 1 else 9, color)
		if d < day - 1:
			icon("check", Vector2(x, 66), WHITE, 0.7)
		elif d == day - 1:
			center_text(Vector2(x, 71), str(day), 13, WHITE)
		else:
			center_text(Vector2(x, 70), str(d + 1), 10, MUTED)
	button("help", Rect2(1120, 34, 155, 38), "How to play", "", "plain", true, "?")
	button("sound", Rect2(1285, 34, 111, 38), "Sound " + ("on" if sound_on else "off"), "", "plain")
	line(Vector2(44, 99), Vector2(1396, 99))
	text_at(Vector2(44, 137), "DAY %02d / 07   ·   %s" % [day, DAY_NAMES[day - 1]], 12, GREEN)
	var headlines = ["A little care changes the whole block.", "Good ideas grow when we listen.", "Nobody should face the heat alone.", "Shared work makes lighter days.", "Make time for the quietest neighbor.", "Keep the coolest places open to all.", "Look how far small acts can travel."]
	text_at(Vector2(44, 177), headlines[day - 1], 33, INK)
	var subtitle = "Listen to your neighbors. Meet real needs. Build things that last."
	if day == 3 or day == 6:
		subtitle = "Heatwave today: protect everyone before tonight’s −" + str(NIGHT_LOSS[day - 1]) + " wellbeing."
	elif day == 7:
		subtitle = "One last day to leave the block a little stronger than you found it."
	text_at(Vector2(45, 201), subtitle, 16, ORANGE if day == 3 or day == 6 else MUTED)
	var steady = steady_count()
	text_at(Vector2(997, 135), "OUR SHARED GOAL", 11, MUTED)
	icon("heart", Vector2(1006, 158), GREEN, 1.1)
	text_at(Vector2(1028, 165), str(steady) + "/6 neighbors steady", 19, INK)
	icon("leaf", Vector2(1006, 189), GREEN, 1.1)
	text_at(Vector2(1028, 196), str(mini(project_count(), 2)) + "/2 shared projects", 17, MUTED)

func steady_count() -> int:
	var result = 0
	for w in wellbeing:
		if w >= 45:
			result += 1
	return result

func project_count() -> int:
	return projects.count(true)

func draw_map() -> void:
	round_rect(Rect2(44, 223, 912, 488), Color("e0e3d5"), 22)
	round_rect(MAP_RECT, Color("e4eadc"), 22)
	# A restrained paper texture, generated from a fixed pattern.
	for i in 165:
		var x = 58 + fmod(i * 137.7, 881)
		var y = 231 + fmod(i * 71.3, 457)
		draw_circle(Vector2(x, y), 0.8, Color(0.44, 0.54, 0.40, 0.12))
	var center = Vector2(500, 453)
	for p in POSITIONS:
		line(p + Vector2(0, 11), center, Color("d8dfce"), 32)
		line(p + Vector2(0, 11), center, Color("f4f0e2"), 26)
	# A looping, walkable lane.
	var loop = PackedVector2Array([Vector2(215, 375), Vector2(494, 337), Vector2(778, 377), Vector2(788, 565), Vector2(493, 602), Vector2(213, 570), Vector2(215, 375)])
	draw_polyline(loop, Color("d7decd"), 28, true)
	draw_polyline(loop, Color("f4f0e2"), 23, true)
	for i in 9:
		line(Vector2(350 + i * 7, 349), Vector2(352 + i * 7, 364), Color("dfdece"), 2)
	for t in [[99, 338, 0.9], [324, 287, 0.8], [637, 276, 0.8], [889, 296, 0.9], [885, 484, 0.9], [891, 626, 0.65], [636, 646, 0.7], [354, 638, 0.62], [105, 619, 0.8], [95, 473, 0.8], [345, 465, 0.65], [654, 473, 0.7]]:
		tree(Vector2(t[0], t[1]), t[2])
	for p in [Vector2(322, 359), Vector2(642, 363), Vector2(359, 589), Vector2(657, 590)]:
		flower_patch(p)
	# Plaza changes as shared projects are built.
	ellipse(center + Vector2(0, 10), Vector2(78, 49), Color("cbd5c0"))
	ellipse(center, Vector2(77, 49), Color("f9f3e5"))
	ellipse(center, Vector2(65, 39), Color("e1dcc9"))
	ellipse(center, Vector2(61, 36), Color("ece9d8"))
	if selected == -1 or is_over("commons"):
		draw_arc(center, 78, 0, TAU, 70, Color("91a88a"), 2, true)
	if projects[0]:
		for dx in [-44, 44]:
			line(center + Vector2(dx, 9), center + Vector2(dx, -47), Color("9b7a52"), 4)
		polygon([center + Vector2(-56, -47), center + Vector2(0, -67), center + Vector2(56, -47), center + Vector2(0, -23)], Color("d9b06a"))
		line(center + Vector2(-56, -47), center + Vector2(56, -47), Color("efcd8f"), 2)
	else:
		tree(center + Vector2(0, -3), 0.86)
	bench(center + Vector2(-41, 12))
	bench(center + Vector2(37, 17))
	if projects[1]:
		round_rect(Rect2(center + Vector2(-58, -8), Vector2(21, 26)), Color("a77752"), 2)
		line(center + Vector2(-56, 4), center + Vector2(-39, 4), PAPER, 2)
		draw_rect(Rect2(center + Vector2(-54, -5), Vector2(5, 8)), GOLD)
		draw_rect(Rect2(center + Vector2(-46, 7), Vector2(5, 8)), Color("86aaa2"))
	if projects[2]:
		mini_person(center + Vector2(17, 4), Color("bd7757"), 0.8)
		mini_person(center + Vector2(28, 8), Color("69918c"), 0.8)
	var common_color = GREEN if selected == -1 else WHITE
	round_rect(Rect2(421, 489, 158, 43), common_color, 12, Color("d1d8c5"), 1)
	center_text(Vector2(500, 508), "THE COMMONS", 12, WHITE if selected == -1 else GREEN)
	center_text(Vector2(500, 523), str(project_count()) + "/3 projects built", 10, Color("d0e1d0") if selected == -1 else MUTED)
	hit("commons", Rect2(420, 394, 160, 139))
	for i in 6:
		draw_site(i)
	# People make the block feel inhabited.
	mini_person(Vector2(348 + sin(elapsed * 0.4) * 7, 382), Color("c77758"), 1.0)
	mini_person(Vector2(645, 409 + sin(elapsed * 0.35) * 6), Color("738caa"), 0.9)
	mini_person(Vector2(668, 573), Color("b39d5c"), 0.85)
	text_at(Vector2(68, 246), "WILLOW BLOCK", 12, GREEN)
	line(Vector2(69, 254), Vector2(174, 254), Color("bdcbb4"))
	icon("sun", Vector2(835, 244), ORANGE, 0.8)
	text_at(Vector2(851, 249), str(TEMPS[day - 1]) + "°C", 14, INK)
	text_at(Vector2(69, 683), "A SMALL PLACE. A SHARED FUTURE.", 10, MUTED)
	pill(Rect2(773, 666, 157, 24), "Click a place to connect", Color("f5f2e7"), MUTED, 11)

func tree(p: Vector2, scale_value: float = 1.0) -> void:
	var s = scale_value
	ellipse(p + Vector2(6, 6) * s, Vector2(20, 9) * s, Color(0.28, 0.40, 0.24, 0.12))
	line(p, p + Vector2(0, -25) * s, Color("8a7958"), 5 * s)
	line(p + Vector2(0, -9) * s, p + Vector2(9, -24) * s, Color("8a7958"), 3 * s)
	draw_circle(p + Vector2(0, -32) * s, 20 * s, Color("8ca47b"))
	draw_circle(p + Vector2(-12, -24) * s, 13 * s, Color("90aa7e"))
	draw_circle(p + Vector2(11, -27) * s, 15 * s, Color("78966c"))
	draw_circle(p + Vector2(-4, -40) * s, 12 * s, Color("a1b58b"))

func flower_patch(p: Vector2) -> void:
	for j in 5:
		var q = p + Vector2(j * 6 - 12, sin(j * 2.2) * 4)
		line(q, q + Vector2(0, -6), Color("7b9465"), 1.2)
		draw_circle(q + Vector2(0, -6), 2.7, GOLD if j % 2 == 0 else Color("d69479"))

func bench(p: Vector2) -> void:
	line(p + Vector2(-11, 1), p + Vector2(-11, 8), Color("76806a"), 2)
	line(p + Vector2(11, 1), p + Vector2(11, 8), Color("76806a"), 2)
	line(p + Vector2(-13, 0), p + Vector2(13, 0), Color("b29569"), 5)
	line(p + Vector2(-13, -6), p + Vector2(13, -6), Color("b29569"), 3)

func mini_person(p: Vector2, shirt: Color, s: float) -> void:
	ellipse(p + Vector2(1, 2), Vector2(5, 2) * s, Color(0.2, 0.3, 0.2, 0.13))
	line(p + Vector2(-2, 0) * s, p + Vector2(-2, -7) * s, INK, 2 * s)
	line(p + Vector2(2, 0) * s, p + Vector2(2, -7) * s, INK, 2 * s)
	line(p + Vector2(0, -7) * s, p + Vector2(0, -15) * s, shirt, 7 * s)
	draw_circle(p + Vector2(0, -20) * s, 4 * s, Color("c89671"))

func draw_site(index: int) -> void:
	var p = POSITIONS[index]
	var active = selected == index
	var over = is_over("person_" + str(index))
	if active or over:
		ellipse(p + Vector2(0, -8), Vector2(96, 63), Color("d2ddc9"))
		ellipse(p + Vector2(0, -8), Vector2(89, 57), Color("edf0df"))
	if index == 4:
		draw_garden(p)
	else:
		draw_building(p, index)
	var r = Rect2(p + Vector2(-82, 29), Vector2(164, 51))
	round_rect(Rect2(r.position + Vector2(0, 3), r.size), Color(0.33, 0.42, 0.29, 0.1), 12)
	round_rect(r, GREEN if active else WHITE, 12, GREEN if active or over else Color("d3dcc8"), 2 if active else 1)
	portrait(p + Vector2(-57, 54), 17, index)
	text_at(p + Vector2(-32, 50), NAMES[index], 16, WHITE if active else INK)
	var meter_color = Color("edb97d") if wellbeing[index] < 45 else Color("a6bd8a")
	round_rect(Rect2(p + Vector2(-32, 59), Vector2(76, 4)), Color("547866") if active else Color("e5e8dc"), 2)
	round_rect(Rect2(p + Vector2(-32, 59), Vector2(76 * wellbeing[index] / 100.0, 4)), meter_color, 2)
	right_text(p + Vector2(66, 58), str(wellbeing[index]), 13, WHITE if active else MUTED)
	if helped[index]:
		draw_circle(p + Vector2(57, -65), 11, GREEN)
		icon("check", p + Vector2(57, -65), WHITE, 0.8)
	elif wellbeing[index] < 45:
		var alert_pos = p + Vector2(62, -39) if index == 4 else p + Vector2(57, -65)
		draw_circle(alert_pos, 11, ORANGE)
		center_text(alert_pos + Vector2(0, 5), "!", 14, WHITE)
	hit("person_" + str(index), Rect2(p + Vector2(-95, -58 if index == 4 else -125 if index == 3 else -92), Vector2(190, 138 if index == 4 else 206 if index == 3 else 173)))

func draw_building(p: Vector2, index: int) -> void:
	var w = 56.0 if index != 3 else 51.0
	var d = 24.0
	var h = 65.0 if index != 3 else 99.0
	var roof = COLORS[index]
	ellipse(p + Vector2(9, 12), Vector2(72, 25), Color(0.29, 0.39, 0.26, 0.11))
	polygon([p + Vector2(-w - 9, 0), p + Vector2(0, -d - 12), p + Vector2(w + 9, 0), p + Vector2(0, d + 13)], Color("d2d7c3"))
	polygon([p + Vector2(-w, -h), p + Vector2(0, -h + d), p + Vector2(0, d), p + Vector2(-w, 0)], Color("e3d9b9"))
	polygon([p + Vector2(0, -h + d), p + Vector2(w, -h), p + Vector2(w, 0), p + Vector2(0, d)], Color("f4e8cb"))
	# Shallow hipped roofs and warm, angled facades.
	polygon([p + Vector2(-w - 5, -h), p + Vector2(0, -h - d - 3), p + Vector2(w + 5, -h), p + Vector2(0, -h + d + 3)], roof)
	polygon([p + Vector2(-w - 5, -h), p + Vector2(0, -h - d - 3), p + Vector2(0, -h - 5), p + Vector2(0, -h + d + 3)], roof.lightened(0.08))
	line(p + Vector2(-w - 5, -h), p + Vector2(0, -h + d + 3), roof.darkened(0.18), 3)
	line(p + Vector2(0, -h + d + 3), p + Vector2(w + 5, -h), roof.darkened(0.2), 3)
	var rows = 2 if index == 3 else 1
	for row in rows:
		for col in 2:
			var x = 12 + col * 25
			var y = -h + d + 15 + row * 31 - x * d / w
			polygon([p + Vector2(x, y), p + Vector2(x + 14, y - 6), p + Vector2(x + 14, y + 10), p + Vector2(x, y + 16)], Color("6c8b83"))
			line(p + Vector2(x + 7, y - 3), p + Vector2(x + 7, y + 13), Color("c6d3b9"), 1.5)
			line(p + Vector2(x, y + 8), p + Vector2(x + 14, y + 2), Color("c6d3b9"), 1.5)
	for col in 2:
		var x = -43 + col * 23
		var y = -h + 16 + (x + w) * d / w
		polygon([p + Vector2(x, y), p + Vector2(x + 13, y + 5), p + Vector2(x + 13, y + 19), p + Vector2(x, y + 14)], Color("8a9c88"))
	polygon([p + Vector2(-20, -12), p + Vector2(-6, -6), p + Vector2(-6, d - 3), p + Vector2(-20, d - 9)], Color("8d7759"))
	if index == 0:
		# Striped kitchen awning.
		for j in 6:
			var x = 3 + j * 8
			polygon([p + Vector2(x, -29 - x * 0.43), p + Vector2(x + 8, -32.5 - x * 0.43), p + Vector2(x + 14, -23 - x * 0.43), p + Vector2(x + 6, -19.5 - x * 0.43)], WHITE if j % 2 else roof)
		flower_patch(p + Vector2(-66, 6))
	elif index == 1:
		line(p + Vector2(-23, -86), p + Vector2(3, -75), Color("8f7651"), 4)
		draw_arc(p + Vector2(-23, -86), 6, 0.2, 4.1, 15, Color("8f7651"), 3, true)
		for j in 2:
			draw_arc(p + Vector2(61 + j * 9, 5 + j * 4), 9, 0, TAU, 24, Color("526858"), 3, true)
	elif index == 2:
		# Books in the library sign.
		for j in 4:
			line(p + Vector2(-16 + j * 7, -85 + j * 2), p + Vector2(-16 + j * 7, -72 + j * 2), PAPER if j % 2 else GOLD, 5)
		bench(p + Vector2(67, 10))
	elif index == 3:
		# Roof garden and a small laundry line.
		line(p + Vector2(-18, -106), p + Vector2(22, -101), Color("64705e"), 1.5)
		for j in 3:
			draw_rect(Rect2(p + Vector2(-12 + j * 11, -105 + j), Vector2(7, 10)), PAPER if j % 2 else Color("d5b57e"))
		draw_circle(p + Vector2(-27, -107), 8, Color("849c70"))
	elif index == 5:
		line(p + Vector2(4, -86), p + Vector2(4, -69), PAPER, 6)
		line(p + Vector2(-5, -78), p + Vector2(13, -78), PAPER, 6)
		flower_patch(p + Vector2(65, 8))

func draw_garden(p: Vector2) -> void:
	ellipse(p + Vector2(3, -8), Vector2(76, 37), Color(0.29, 0.39, 0.26, 0.10))
	polygon([p + Vector2(-65, -16), p + Vector2(-2, -48), p + Vector2(65, -16), p + Vector2(0, 16)], Color("bdc6a0"))
	for row in 3:
		var c = p + Vector2(-37 + row * 25, -13 - row * 5)
		polygon([c + Vector2(-13, -9), c + Vector2(10, -20), c + Vector2(35, -7), c + Vector2(12, 5)], Color("a9825c"))
		polygon([c + Vector2(-10, -10), c + Vector2(10, -18), c + Vector2(31, -7), c + Vector2(12, 2)], Color("716f4c"))
		for j in 3:
			var v = c + Vector2(1 + j * 9, -9 + j * 3)
			line(v, v + Vector2(0, -12), Color("6b8a53"), 2)
			ellipse(v + Vector2(-3, -9), Vector2(5, 3), Color("8baf6a"))
			ellipse(v + Vector2(3, -13), Vector2(5, 3), Color("749c59"))
			if row == 1:
				draw_circle(v + Vector2(0, -16), 3, ORANGE)
	line(p + Vector2(-62, -16), p + Vector2(-62, -48), Color("9f895f"), 3)
	line(p + Vector2(-62, -44), p + Vector2(-39, -50), Color("9f895f"), 2)
	line(p + Vector2(-39, -22), p + Vector2(-39, -50), Color("9f895f"), 3)
	flower_patch(p + Vector2(57, 2))

func portrait(p: Vector2, r: float, index: int) -> void:
	draw_circle(p, r, COLORS[index].lightened(0.25))
	# Faces are built from simple shapes and remain legible at badge size.
	var s = r / 25.0
	ellipse(p + Vector2(0, 18) * s, Vector2(18, 12) * s, COLORS[index].darkened(0.12))
	draw_circle(p + Vector2(0, -3) * s, 13 * s, HAIR[index])
	ellipse(p + Vector2(0, 1) * s, Vector2(10, 13) * s, SKIN[index])
	ellipse(p + Vector2(-4, -9) * s, Vector2(10, 5) * s, HAIR[index])
	if index == 0 or index == 4:
		draw_circle(p + Vector2(10, -9) * s, 6 * s, HAIR[index])
	elif index == 1:
		line(p + Vector2(-9, -9) * s, p + Vector2(10, -9) * s, Color("d9d1b3"), 4 * s)
	elif index == 2:
		draw_arc(p + Vector2(-4, 0) * s, 3 * s, 0, TAU, 16, INK, s, true)
		draw_arc(p + Vector2(5, 0) * s, 3 * s, 0, TAU, 16, INK, s, true)
		line(p + Vector2(-1, 0) * s, p + Vector2(2, 0) * s, INK, s)
	elif index == 5:
		polygon([p + Vector2(-14, -9) * s, p + Vector2(-9, -18) * s, p + Vector2(10, -18) * s, p + Vector2(13, -8) * s], Color("ebdfbc"))
	if index != 2:
		draw_circle(p + Vector2(-4, 0) * s, 1.1 * s, INK)
		draw_circle(p + Vector2(4, 0) * s, 1.1 * s, INK)
	draw_arc(p + Vector2(0, 4) * s, 3 * s, 0.25, 2.8, 12, HAIR[index], s, true)

func draw_resources() -> void:
	round_rect(Rect2(44, 726, 912, 91), WHITE, 16, LINE, 1)
	icon("clock", Vector2(78, 758), GREEN, 1.15)
	text_at(Vector2(99, 764), "TIME TO GIVE", 11, MUTED)
	for i in 4:
		pill(Rect2(67 + i * 42, 779, 32, 14), "", GREEN if i < hours else Color("e7e9df"), WHITE)
	text_at(Vector2(253, 790), str(hours) + " / 4 hours", 20, INK)
	line(Vector2(384, 747), Vector2(384, 798))
	icon("box", Vector2(415, 758), GREEN, 1.15)
	text_at(Vector2(437, 764), "SHARED SUPPLIES", 11, MUTED)
	text_at(Vector2(408, 794), str(supplies), 27, INK)
	text_at(Vector2(434, 792), "+" + str(4 if projects[1] else 3) + " each morning · capacity 9", 13, MUTED)
	line(Vector2(666, 747), Vector2(666, 798))
	icon("sun", Vector2(698, 758), ORANGE, 1.0)
	text_at(Vector2(720, 764), "TONIGHT’S FORECAST", 11, MUTED)
	var loss = maxi(0, NIGHT_LOSS[day - 1] - (1 if projects[0] and day < 7 else 0))
	text_at(Vector2(690, 793), "−" + str(loss) + " wellbeing", 20, INK)
	text_at(Vector2(839, 791), "each" if day < 7 else "week ends", 12, MUTED)

func draw_detail() -> void:
	var panel = Rect2(980, 218, 416, 488)
	round_rect(Rect2(980, 223, 416, 488), Color("e6e1d4"), 20)
	round_rect(panel, WHITE, 20, LINE, 1)
	if selected < 0:
		draw_commons()
	else:
		draw_person_panel(selected)
	var title = "Close the day" if day < 7 else "See what we changed"
	var subtitle = str(hours) + " hour" + ("s" if hours != 1 else "") + " left · rest, then start a new morning" if day < 7 else str(hours) + " hours left · review our week before finishing"
	button("end_day", Rect2(980, 726, 416, 91), title, subtitle, "primary", true, "→")

func draw_person_panel(index: int) -> void:
	text_at(Vector2(1005, 248), "YOUR NEIGHBOR  /  %02d" % (index + 1), 11, MUTED)
	portrait(Vector2(1039, 292), 28, index)
	text_at(Vector2(1083, 288), NAMES[index], 29, INK)
	text_at(Vector2(1084, 310), PLACES[index], 10, MUTED)
	var status = "Needs care" if wellbeing[index] < 45 else "Steady" if wellbeing[index] < 70 else "Thriving"
	var col = ORANGE if wellbeing[index] < 45 else GREEN
	pill(Rect2(1005, 333, 113, 25), status, col.lightened(0.85), col, 12)
	text_at(Vector2(1130, 351), str(wellbeing[index]) + "/100 wellbeing", 13, MUTED)
	line(Vector2(1005, 373), Vector2(1371, 373))
	if helped[index]:
		draw_circle(Vector2(1188, 431), 24, LIGHT_GREEN)
		icon("check", Vector2(1188, 431), GREEN, 1.7)
		center_text(Vector2(1188, 481), "A little steadier, together.", 21, INK)
		paragraph(Vector2(1010, 515), NAMES[index] + " has been supported today. There are other people to check on, and shared projects to build.", 350, 17)
		button("commons", Rect2(1005, 610, 366, 64), "Visit the commons", "Care that reaches the whole block", "soft", true, "→")
		return
	if listened[index]:
		paragraph(Vector2(1005, 403), VOICES[index], 361, 17, INK, 1.4)
		text_at(Vector2(1005, 494), "HEARD & UNDERSTOOD  ·  +3 WELLBEING", 10, GREEN)
		var cost = 1 if index < 2 else 0
		var enabled = hours >= 1 and supplies >= cost
		button("tailored", Rect2(1005, 515, 366, 70), TAILORED_NAMES[index], TAILORED_DESCS[index], "primary", enabled, "1h")
		button("direct", Rect2(1005, 597, 366, 67), DIRECT_NAMES[index], "+12 wellbeing · 2 supplies", "plain", hours >= 1 and supplies >= 2, "1h")
		if hours == 0:
			text_at(Vector2(1007, 689), "Time to rest. Your care continues tomorrow.", 12, MUTED)
		else:
			text_at(Vector2(1007, 689), "Their knowledge makes your help go further.", 12, MUTED)
	else:
		paragraph(Vector2(1005, 403), NEEDS[index], 357, 17, INK, 1.4)
		button("listen", Rect2(1005, 473, 366, 70), "First, listen", "+3 wellbeing · discover what would really help", "primary", hours >= 1, "1h")
		button("direct", Rect2(1005, 555, 366, 67), DIRECT_NAMES[index], "+12 wellbeing · 2 supplies", "plain", hours >= 1 and supplies >= 2, "1h")
		icon("leaf", Vector2(1014, 653), GREEN, 0.85)
		paragraph(Vector2(1033, 651), "Listening once unlocks their idea for the whole week.", 328, 13, MUTED, 1.45)

func draw_commons() -> void:
	text_at(Vector2(1005, 248), "CARE THAT KEEPS GOING", 11, GREEN)
	text_at(Vector2(1005, 285), "The commons", 29, INK)
	text_at(Vector2(1005, 311), "Build once. Help the whole block.", 15, MUTED)
	for i in 3:
		var y = 333 + i * 115
		var built = projects[i]
		var r = Rect2(1005, y, 366, 102)
		var enabled = not built and hours >= 2 and supplies >= 2
		round_rect(r, LIGHT_GREEN if built else (Color("edf0e4") if is_over("build_" + str(i)) and enabled else PAPER), 12, Color("bccbb3") if built else LINE, 1)
		text_at(Vector2(1020, y + 26), PROJECT_SHORT[i], 18, INK)
		if built:
			icon("check", Vector2(1348, y + 20), GREEN, 1.1)
		else:
			right_text(Vector2(1357, y + 25), "2h · 2 supplies", 12, MUTED)
		paragraph(Vector2(1020, y + 49), PROJECT_DESCS[i], 327, 13, MUTED, 1.4)
		text_at(Vector2(1020, y + 88), "BUILT · EVERYONE +3" if built else ("BUILD TOGETHER  →" if enabled else ("Need 2 hours" if hours < 2 else "Need 2 supplies")), 10, GREEN if built or enabled else MUTED)
		hit("build_" + str(i), r, enabled)

func draw_footer() -> void:
	text_at(Vector2(45, 849), "THE AIM", 10, GREEN)
	text_at(Vector2(107, 849), "Finish day 7 with everyone at 45+ wellbeing and at least 2 shared projects.", 14, MUTED)
	right_text(Vector2(1395, 849), "1–6  Neighbors    C  Commons    Space  Close day", 12, MUTED)
	text_at(Vector2(45, 877), "You cannot do everything. You can make sure nobody is forgotten.", 11, Color("92998a"))
	right_text(Vector2(1395, 877), "A GAME ABOUT MUTUAL CARE", 10, Color("92998a"))

func overlay_panel(rect: Rect2) -> void:
	buttons.clear()
	draw_rect(Rect2(0, 0, 1440, 900), Color(0.10, 0.19, 0.16, 0.58))
	round_rect(Rect2(rect.position + Vector2(0, 10), rect.size), Color(0.1, 0.17, 0.13, 0.15), 24)
	round_rect(rect, WHITE, 24)

func draw_help() -> void:
	overlay_panel(Rect2(344, 113, 752, 674))
	text_at(Vector2(390, 159), "WELCOME TO WILLOW BLOCK", 12, GREEN)
	text_at(Vector2(390, 204), "A good week starts with listening.", 31, INK)
	paragraph(Vector2(390, 241), "A heatwave is coming. You have seven days to help six neighbors stay steady and build a community that can look after itself.", 655, 18)
	var tips = [
		["01", "Look around", "Click a place on the map. Below 45 wellbeing, a neighbor needs care. Everyone matters; the average is not the goal."],
		["02", "Listen, then act", "Spend 1 hour to listen. You gain understanding for the whole week, unlocking more effective help and benefits for others."],
		["03", "Share the work", "The commons has three lasting projects. Each costs 2 hours and 2 supplies, gives everyone +3, and helps every new day."],
		["04", "Make room for rest", "You have 4 hours each day. Night reduces wellbeing as shown in the forecast. Each morning brings 3 supplies (up to 9)."]
	]
	for i in 4:
		var y = 321 + i * 82
		pill(Rect2(390, y - 19, 35, 29), tips[i][0], LIGHT_GREEN, GREEN, 12)
		text_at(Vector2(441, y), tips[i][1], 18, INK)
		paragraph(Vector2(441, y + 24), tips[i][2], 590, 14, MUTED, 1.35)
	line(Vector2(390, 657), Vector2(1050, 657))
	text_at(Vector2(390, 684), "Finish with all 6 neighbors at 45+ and 2 shared projects.", 16, GREEN)
	text_at(Vector2(390, 714), "Keys: 1–6 select · L listen · H help · P their plan · C commons", 12, MUTED)
	button("close_help", Rect2(838, 729, 212, 39), "Back to the block", "", "primary")

func draw_night() -> void:
	overlay_panel(Rect2(386, 155, 668, 591))
	text_at(Vector2(430, 201), "THE BLOCK AT NIGHT", 12, GREEN)
	text_at(Vector2(430, 244), "One week of showing up." if day == 7 else "Care includes calling it a day.", 29, INK)
	var loss = maxi(0, NIGHT_LOSS[day - 1] - (1 if projects[0] else 0))
	var extra = "Your canopy softens the heat." if projects[0] else "A shade canopy can soften the heat."
	paragraph(Vector2(430, 283), "Our week ends here. Take one last look at how everyone is doing before you finish." if day == 7 else "Tonight: −" + str(loss) + " wellbeing for everyone. " + extra, 573, 17)
	var predicted = wellbeing.duplicate()
	for i in 6:
		predicted[i] = maxi(0, predicted[i] - loss)
	if projects[2] and day < 7:
		var low = predicted.find(predicted.min())
		predicted[low] = mini(100, predicted[low] + 5)
	for i in 6:
		var x = 432 + (i % 3) * 192
		var y = 362 + (i / 3) * 69
		portrait(Vector2(x + 18, y + 5), 18, i)
		text_at(Vector2(x + 47, y + 1), NAMES[i], 15, INK)
		text_at(Vector2(x + 47, y + 23), str(wellbeing[i]) + " → " + str(predicted[i]), 16, ORANGE if predicted[i] < 45 else GREEN)
	line(Vector2(430, 494), Vector2(1010, 494))
	if hours > 0:
		paragraph(Vector2(430, 523), "You still have " + str(hours) + " hour" + ("s" if hours != 1 else "") + " to give today. You can return to the block, or rest now.", 572, 17, INK)
	else:
		paragraph(Vector2(430, 523), "You gave your time today. Take a moment to see what your care made possible." if day == 7 else "You gave your time today. Tomorrow brings four fresh hours and " + str(4 if projects[1] else 3) + " supplies.", 572, 17, INK)
	if day < 7:
		text_at(Vector2(430, 593), "TOMORROW  ·  " + DAY_NAMES[day] + "  ·  " + str(TEMPS[day]) + "°C" + ("  /  HEATWAVE" if TEMPS[day] >= 34 else ""), 12, MUTED)
	else:
		text_at(Vector2(430, 593), "OUR GOAL  ·  EVERYONE AT 45+  ·  TWO SHARED PROJECTS", 12, GREEN)
	button("back", Rect2(430, 638, 196, 58), "Back to the block", "", "plain")
	button("next_day", Rect2(641, 638, 369, 58), "Finish our week" if day == 7 else "Rest & begin day " + str(day + 1), "", "primary", true, "→")

func draw_result() -> void:
	var won = steady_count() == 6 and project_count() >= 2
	overlay_panel(Rect2(333, 91, 774, 718))
	text_at(Vector2(379, 137), "SEVEN DAYS. MANY SMALL ACTS.", 12, GREEN)
	text_at(Vector2(379, 183), "A stronger kind of neighborhood." if won else "Every act of care leaves a trace.", 32, INK)
	var summary = "Everyone is steady, and your shared projects will keep helping long after this week. You made care something the whole block can carry." if won else "Some needs remain. Your week still changed lives. Next time, listen early, protect the people struggling most, and invest in care that lasts."
	paragraph(Vector2(379, 225), summary, 674, 18, MUTED, 1.45)
	for i in 6:
		var x = 379 + (i % 3) * 231
		var y = 342 + (i / 3) * 83
		portrait(Vector2(x + 24, y), 24, i)
		text_at(Vector2(x + 60, y - 4), NAMES[i], 18, INK)
		text_at(Vector2(x + 60, y + 20), str(wellbeing[i]) + " / 100  ·  " + ("Steady" if wellbeing[i] >= 45 else "Needs care"), 13, GREEN if wellbeing[i] >= 45 else ORANGE)
	line(Vector2(379, 489), Vector2(1061, 489))
	var metrics = [[str(steady_count()) + "/6", "NEIGHBORS STEADY"], [str(project_count()), "SHARED PROJECTS"], [str(conversations), "PEOPLE HEARD"], [str(targeted_help), "PLANS MADE REAL"]]
	for i in 4:
		text_at(Vector2(379 + i * 175, 536), metrics[i][0], 32, GREEN)
		text_at(Vector2(379 + i * 175, 562), metrics[i][1], 10, MUTED)
	round_rect(Rect2(379, 594, 682, 100), LIGHT_GREEN, 14)
	text_at(Vector2(398, 622), "TAKE ONE SMALL THING INTO THE WORLD", 11, GREEN)
	paragraph(Vector2(398, 648), "Ask someone: “What would actually help?” Listen to their answer. Choose one small thing you can sustainably do together.", 639, 16, INK, 1.4)
	button("restart", Rect2(792, 724, 269, 48), "Try another week", "", "primary", true, "→")
	text_at(Vector2(379, 753), "A better world is a practice, not a perfect score.", 14, MUTED)
