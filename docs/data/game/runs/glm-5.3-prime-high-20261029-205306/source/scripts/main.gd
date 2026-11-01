extends Control
## THE COMMONS - shell script. Builds all UI in code so the project stays
## fully self-contained (no external assets, no .tscn authoring hazards).

const CooperateScript := preload("res://scripts/cooperate.gd")
const AidScript := preload("res://scripts/aid.gd")

const BG_COLOR := Color("141a20")
const PANEL_COLOR := Color("1d252e")
const CARD_COLOR := Color("26313d")
const ACCENT := Color("7fd4a8")
const WARM := Color("f0c674")
const MUTED := Color("9aa7b1")

var tab_buttons: Dictionary = {}
var panels: Dictionary = {}

func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = BG_COLOR
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)

	var outer := MarginContainer.new()
	outer.set_anchors_preset(Control.PRESET_FULL_RECT)
	outer.add_theme_constant_override("margin_left", 24)
	outer.add_theme_constant_override("margin_right", 24)
	outer.add_theme_constant_override("margin_top", 16)
	outer.add_theme_constant_override("margin_bottom", 16)
	add_child(outer)

	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 12)
	outer.add_child(root)

	root.add_child(_make_header())
	root.add_child(_make_navbar())

	var content := VBoxContainer.new()
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(content)

	panels["intro"] = _make_intro()
	panels["commons"] = CooperateScript.new()
	panels["aid"] = AidScript.new()
	for key in ["intro", "commons", "aid"]:
		var p: Control = panels[key]
		p.size_flags_vertical = Control.SIZE_EXPAND_FILL
		p.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		content.add_child(p)

	var footer := Label.new()
	footer.text = "Everything here is illustrative, but the pattern is real: cooperation compounds, and some help does 100x more than other help."
	footer.add_theme_font_size_override("font_size", 13)
	footer.add_theme_color_override("font_color", MUTED)
	footer.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	footer.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	root.add_child(footer)

	show_panel("intro")

func _make_header() -> Control:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 0)
	var title := Label.new()
	title.text = "THE COMMONS"
	title.add_theme_font_size_override("font_size", 42)
	title.add_theme_color_override("font_color", WARM)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(title)
	var sub := Label.new()
	sub.text = "a small game about doing the most good for the greatest number"
	sub.add_theme_font_size_override("font_size", 16)
	sub.add_theme_color_override("font_color", MUTED)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(sub)
	return box

func _make_navbar() -> Control:
	var bar := HBoxContainer.new()
	bar.add_theme_constant_override("separation", 10)
	bar.alignment = BoxContainer.ALIGNMENT_CENTER
	for pair in [["intro", "Welcome"], ["commons", "1 · The Commons"], ["aid", "2 · The Aid Office"]]:
		var key: String = pair[0]
		var txt: String = pair[1]
		var b := Button.new()
		b.text = txt
		b.custom_minimum_size = Vector2(180, 40)
		b.add_theme_font_size_override("font_size", 17)
		b.pressed.connect(func() -> void: show_panel(key))
		tab_buttons[key] = b
		bar.add_child(b)
	return bar

func show_panel(key: String) -> void:
	for k in panels:
		panels[k].visible = (k == key)
	for k in tab_buttons:
		var b: Button = tab_buttons[k]
		b.modulate = ACCENT if k == key else Color.WHITE

func _make_intro() -> Control:
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 14)
	scroll.add_child(box)

	var blocks: Array = [
		["The premise", ACCENT,
		 "The biggest problems humans face — pandemics, climate, poverty, misinformation — are shared problems. They get solved by two skills:\n\n1. COOPERATING when it's tempting to freeload.\n2. CHOOSING WISELY among ways to help, because they are not remotely equal.\n\nThis game trains both. Two doors, two lessons, one score each."],
		["Door 1 — The Commons", WARM,
		 "You and four neighbours share a well, a vaccine schedule, a climate. Every round you each get 10 coins. Whatever goes into the common pot is multiplied (x1.6) and split five ways — more for everyone if everyone gives.\n\nBut keeping your coins is always the selfish best move... for one round. Over 20 rounds you'll discover which strategy actually wins, and what it costs the group when trust breaks.\n\nThis is the real math behind taxes, climate treaties, open-source software and neighborhood watch schemes."],
		["Door 2 — The Aid Office", Color("8ab6f0"),
		 "You control a relief budget. Every option sounds wonderful. But some interventions are 10–100x more effective than others, and the shiny ones are often the least effective.\n\nRead the claims, weigh the evidence, spend at the margin, and buy information before you buy hope. Real-world cost-effectiveness gaps this size are documented by GiveWell and the DCP3 project — here they're compressed into a game."],
		["How to play", MUTED,
		 "Click a tab above. Each mode takes about 10 minutes and explains itself as you go. Your choices change the outcome; the strategies you learn are the ones worth carrying into the real world."],
	]
	for block in blocks:
		var heading: String = block[0]
		var color: Color = block[1]
		var body: String = block[2]
		var panel := PanelContainer.new()
		panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		panel.add_theme_stylebox_override("panel", _soft_panel(CARD_COLOR, 10))
		var inner := MarginContainer.new()
		inner.add_theme_constant_override("margin_left", 18)
		inner.add_theme_constant_override("margin_right", 18)
		inner.add_theme_constant_override("margin_top", 12)
		inner.add_theme_constant_override("margin_bottom", 12)
		panel.add_child(inner)
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 6)
		var h := Label.new()
		h.text = heading
		h.add_theme_font_size_override("font_size", 22)
		h.add_theme_color_override("font_color", color)
		v.add_child(h)
		var b := Label.new()
		b.text = body
		b.add_theme_font_size_override("font_size", 16)
		b.add_theme_color_override("font_color", Color("dce3e8"))
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(b)
		inner.add_child(v)
		box.add_child(panel)

	return scroll

func _soft_panel(color: Color, radius: int) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = color
	sb.set_corner_radius_all(radius)
	sb.content_margin_left = 4
	sb.content_margin_right = 4
	sb.content_margin_top = 4
	sb.content_margin_bottom = 4
	return sb
