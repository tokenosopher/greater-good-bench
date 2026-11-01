extends Control
## Common Ground — a short game about listening for interests, not positions.

const Data = preload("res://scripts/data.gd")
const UIKit = preload("res://scripts/ui_kit.gd")
const Background = preload("res://scripts/background.gd")
const PartyPanel = preload("res://scripts/party_panel.gd")
const Audio = preload("res://scripts/audio.gd")

const MAX_TRUST := 6
const START_TRUST := 4
const MAX_TURNS := 14
const TOTAL_NEEDS := 6

var mode := "menu"
var scenarios: Array = []
var scenario_index := 0
var scenario: Dictionary = {}
var party_a: Dictionary = {}
var party_b: Dictionary = {}
var trust := {"a": START_TRUST, "b": START_TRUST}
var turn := 0
var revealed := {}
var resolved := {}
var selected: Array[String] = []
var failed_pairs := {}
var log_entries: Array[String] = []
var sound_on := true
var last_result := ""

var bg: Control
var fade: ColorRect
var screen: Control = null
var overlay: Control = null
var audio: Node

var panel_a
var panel_b
var log_text: RichTextLabel
var turn_label: Label
var turn_sub: Label
var progress_bar: ProgressBar
var cg_count: Label
var chip_a: Dictionary = {}
var chip_b: Dictionary = {}
var connect_button: Button
var status_label: Label
var sound_button: Button


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scenarios = Data.scenarios()

	bg = Background.new()
	bg.z_index = -10
	_full_rect(bg)
	add_child(bg)

	audio = Audio.new()
	add_child(audio)

	fade = ColorRect.new()
	fade.z_index = 100
	fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fade.color = Color(UIKit.CREAM.r, UIKit.CREAM.g, UIKit.CREAM.b, 0.0)
	_full_rect(fade)
	add_child(fade)

	_show_menu()


# ---------------------------------------------------------------------------
# Screen plumbing
# ---------------------------------------------------------------------------

func _full_rect(c: Control) -> void:
	c.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)


func _new_screen() -> Control:
	if screen != null:
		remove_child(screen)
		screen.queue_free()
	if overlay != null:
		overlay.queue_free()
		overlay = null
	screen = Control.new()
	screen.name = "Screen"
	screen.mouse_filter = Control.MOUSE_FILTER_PASS
	_full_rect(screen)
	add_child(screen)
	_paint_in()
	return screen


func _paint_in() -> void:
	fade.color = Color(UIKit.CREAM.r, UIKit.CREAM.g, UIKit.CREAM.b, 1.0)
	var tw := create_tween()
	tw.tween_property(fade, "color:a", 0.0, 0.3).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)


func _page(width: float, height: float = 0.0) -> Array:
	var cc := CenterContainer.new()
	_full_rect(cc)
	screen.add_child(cc)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(width, height)
	panel.add_theme_stylebox_override("panel", UIKit.box(UIKit.PAPER, 22, Color(UIKit.GREEN, 0.16), 1, true))
	cc.add_child(panel)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 30)
	margin.add_theme_constant_override("margin_right", 30)
	margin.add_theme_constant_override("margin_top", 24)
	margin.add_theme_constant_override("margin_bottom", 24)
	panel.add_child(margin)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 10)
	margin.add_child(col)
	return [cc, panel, col]


func _corner_button(text: String, target: Callable) -> Button:
	var b := UIKit.make_button(text, false)
	b.custom_minimum_size = Vector2(0, 28)
	UIKit.style_ghost_button(b)
	b.pressed.connect(target)
	b.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	b.position = Vector2(18, 16)
	b.size = Vector2(150, 28)
	screen.add_child(b)
	return b


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------

func _show_menu() -> void:
	mode = "menu"
	var s := _new_screen()
	var cc := CenterContainer.new()
	_full_rect(cc)
	s.add_child(cc)

	var v := VBoxContainer.new()
	v.custom_minimum_size = Vector2(1040, 0)
	v.add_theme_constant_override("separation", 10)
	cc.add_child(v)

	var overline := UIKit.label("A GAME ABOUT WHAT WE SHARE", 11, UIKit.GREEN, true)
	overline.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(overline)

	var title := UIKit.label("COMMON GROUND", 64, UIKit.INK, true)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(title)

	var subtitle := UIKit.wrapped_label(
		"A short game about listening, interests, and solutions that include everyone.",
		17, UIKit.INK_SOFT
	)
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle.custom_minimum_size = Vector2(0, 28)
	v.add_child(subtitle)

	var gap := UIKit.vsep(12)
	v.add_child(gap)

	var cards := HBoxContainer.new()
	cards.alignment = BoxContainer.ALIGNMENT_CENTER
	cards.add_theme_constant_override("separation", 14)
	v.add_child(cards)
	for i in range(scenarios.size()):
		cards.add_child(_scenario_card(i, scenarios[i]))

	var gap2 := UIKit.vsep(8)
	v.add_child(gap2)

	var actions := HBoxContainer.new()
	actions.alignment = BoxContainer.ALIGNMENT_CENTER
	actions.add_theme_constant_override("separation", 10)
	v.add_child(actions)
	var how := UIKit.make_button("How to Play", false)
	how.custom_minimum_size = Vector2(180, 38)
	how.pressed.connect(_show_howto)
	actions.add_child(how)
	var guide := UIKit.make_button("The Field Guide", false)
	guide.custom_minimum_size = Vector2(180, 38)
	guide.pressed.connect(func() -> void: _show_field_guide(false))
	actions.add_child(guide)

	var footer := UIKit.label("Three chapters · about 15 minutes · mouse or keyboard · sound on", 10, UIKit.MUTED)
	footer.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(footer)


func _scenario_card(index: int, sc: Dictionary) -> Button:
	var b := Button.new()
	b.custom_minimum_size = Vector2(332, 164)
	b.focus_mode = Control.FOCUS_ALL
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	b.add_theme_stylebox_override("normal", UIKit.box(UIKit.PAPER, 16, UIKit.LINE, 1, true))
	b.add_theme_stylebox_override("hover", UIKit.box(Color("#FFF8E8"), 16, UIKit.GREEN, 2, true))
	b.add_theme_stylebox_override("pressed", UIKit.box(Color("#F5EDDE"), 16, UIKit.GREEN, 2, true))
	b.add_theme_stylebox_override("focus", UIKit.box(UIKit.PAPER, 16, UIKit.GREEN, 2, true))
	b.add_theme_stylebox_override("disabled", UIKit.box(UIKit.PAPER, 16, UIKit.LINE, 1))
	b.pressed.connect(_on_scenario_card_pressed.bind(index))

	var m := MarginContainer.new()
	_full_rect(m)
	m.mouse_filter = Control.MOUSE_FILTER_IGNORE
	m.add_theme_constant_override("margin_left", 16)
	m.add_theme_constant_override("margin_right", 16)
	m.add_theme_constant_override("margin_top", 14)
	m.add_theme_constant_override("margin_bottom", 14)
	b.add_child(m)

	var v := VBoxContainer.new()
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_theme_constant_override("separation", 4)
	m.add_child(v)

	var chapter := UIKit.label(str(sc.get("chapter", "")).to_upper(), 9, UIKit.GOLD, true)
	v.add_child(chapter)

	var title := UIKit.wrapped_label(str(sc.get("title", "")), 21, UIKit.INK, true)
	title.max_lines_visible = 2
	v.add_child(title)

	var sub := UIKit.wrapped_label(str(sc.get("subtitle", "")), 12, UIKit.MUTED)
	sub.max_lines_visible = 2
	v.add_child(sub)

	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(spacer)

	var cta := UIKit.label("BEGIN  →", 10, UIKit.GREEN, true)
	v.add_child(cta)
	return b


func _on_scenario_card_pressed(index: int) -> void:
	audio.play("click")
	_start_scenario(index)


# ---------------------------------------------------------------------------
# Intro
# ---------------------------------------------------------------------------

func _start_scenario(index: int) -> void:
	scenario_index = index
	scenario = scenarios[index]
	party_a = scenario["a"]
	party_b = scenario["b"]
	trust = {"a": START_TRUST, "b": START_TRUST}
	turn = 0
	revealed = {}
	resolved = {}
	selected.clear()
	failed_pairs = {}
	log_entries.clear()
	last_result = ""
	_show_intro()


func _show_intro() -> void:
	mode = "intro"
	var s := _new_screen()
	_corner_button("← Menu", _show_menu)

	var page := _page(900)
	var col: VBoxContainer = page[2]

	var chapter := UIKit.label(str(scenario.get("chapter", "")).to_upper(), 10, UIKit.GOLD, true)
	col.add_child(chapter)
	var title := UIKit.wrapped_label(str(scenario.get("title", "")), 40, UIKit.INK, true)
	col.add_child(title)
	var sub := UIKit.wrapped_label(str(scenario.get("subtitle", "")), 15, UIKit.MUTED)
	col.add_child(sub)

	var setting := UIKit.wrapped_label(str(scenario.get("setting", "")), 14, UIKit.INK_SOFT)
	setting.custom_minimum_size = Vector2(0, 54)
	col.add_child(setting)

	var rule := ColorRect.new()
	rule.color = UIKit.LINE
	rule.custom_minimum_size = Vector2(0, 1)
	rule.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_child(rule)

	var parties := HBoxContainer.new()
	parties.add_theme_constant_override("separation", 12)
	col.add_child(parties)
	parties.add_child(_intro_party_box(party_a))
	parties.add_child(_intro_party_box(party_b))

	var tip := UIKit.label("A position is what they say they want. An interest is why. Listen for the why.", 11, UIKit.GREEN)
	tip.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	col.add_child(tip)

	var btn_row := HBoxContainer.new()
	btn_row.alignment = BoxContainer.ALIGNMENT_CENTER
	col.add_child(btn_row)
	var begin := UIKit.make_button("Take your seat  →", true)
	begin.custom_minimum_size = Vector2(250, 44)
	begin.pressed.connect(_show_game)
	btn_row.add_child(begin)


func _intro_party_box(party: Dictionary) -> PanelContainer:
	var accent := Color(str(party.get("color", "#2E5E46")))
	var p := PanelContainer.new()
	p.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	p.add_theme_stylebox_override("panel", UIKit.box(Color(accent, 0.055), 14, Color(accent, 0.24), 1))

	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 5)
	p.add_child(v)

	var name_row := HBoxContainer.new()
	name_row.add_theme_constant_override("separation", 8)
	v.add_child(name_row)
	var dot := PanelContainer.new()
	dot.custom_minimum_size = Vector2(26, 26)
	var dot_style := UIKit.box(accent, 13)
	dot_style.content_margin_left = 0
	dot_style.content_margin_right = 0
	dot_style.content_margin_top = 0
	dot_style.content_margin_bottom = 0
	dot.add_theme_stylebox_override("panel", dot_style)
	name_row.add_child(dot)
	var initial := UIKit.label(_initials(str(party.get("name", ""))), 9, Color("#FFFDF6"), true)
	initial.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	initial.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	dot.add_child(initial)

	var name := UIKit.label(str(party.get("name", "")), 14, UIKit.INK, true)
	name.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	name_row.add_child(name)

	var quote := UIKit.wrapped_label(str(party.get("quote", "")), 12, UIKit.INK_SOFT)
	quote.custom_minimum_size = Vector2(0, 32)
	v.add_child(quote)

	var role := UIKit.label(str(party.get("role", "")).to_upper(), 8, UIKit.MUTED, true)
	v.add_child(role)
	return p


# ---------------------------------------------------------------------------
# Game screen
# ---------------------------------------------------------------------------

func _show_game() -> void:
	mode = "play"
	audio.play("click")
	var s := _new_screen()

	var margin := MarginContainer.new()
	_full_rect(margin)
	margin.add_theme_constant_override("margin_left", 16)
	margin.add_theme_constant_override("margin_right", 16)
	margin.add_theme_constant_override("margin_top", 12)
	margin.add_theme_constant_override("margin_bottom", 12)
	s.add_child(margin)

	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 8)
	margin.add_child(root)

	# Top bar.
	var top := HBoxContainer.new()
	top.custom_minimum_size = Vector2(0, 40)
	top.add_theme_constant_override("separation", 10)
	root.add_child(top)

	var leave := UIKit.make_button("← Leave table", false)
	leave.custom_minimum_size = Vector2(120, 30)
	UIKit.style_ghost_button(leave)
	leave.pressed.connect(_confirm_leave)
	top.add_child(leave)

	var title_box := VBoxContainer.new()
	title_box.add_theme_constant_override("separation", -2)
	title_box.alignment = BoxContainer.ALIGNMENT_CENTER
	top.add_child(title_box)
	var chapter := UIKit.label(str(scenario.get("chapter", "")).to_upper(), 8, UIKit.GOLD, true)
	title_box.add_child(chapter)
	var title := UIKit.label(str(scenario.get("title", "")), 17, UIKit.INK, true)
	title_box.add_child(title)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top.add_child(spacer)

	sound_button = UIKit.make_button("Sound: On" if sound_on else "Sound: Off", false)
	sound_button.custom_minimum_size = Vector2(96, 30)
	UIKit.style_ghost_button(sound_button)
	sound_button.pressed.connect(_toggle_sound)
	top.add_child(sound_button)

	var guide := UIKit.make_button("How to play", false)
	guide.custom_minimum_size = Vector2(110, 30)
	guide.pressed.connect(_open_help_overlay)
	top.add_child(guide)

	# Main table.
	var main := HBoxContainer.new()
	main.size_flags_vertical = Control.SIZE_EXPAND_FILL
	main.add_theme_constant_override("separation", 12)
	root.add_child(main)

	panel_a = PartyPanel.new()
	panel_a.setup(party_a, "a")
	panel_a.listen_pressed.connect(_on_listen)
	panel_a.reassure_pressed.connect(_on_reassure)
	panel_a.card_pressed.connect(_on_card_pressed)
	main.add_child(panel_a)

	var center := _build_center()
	main.add_child(center)

	panel_b = PartyPanel.new()
	panel_b.setup(party_b, "b")
	panel_b.listen_pressed.connect(_on_listen)
	panel_b.reassure_pressed.connect(_on_reassure)
	panel_b.card_pressed.connect(_on_card_pressed)
	main.add_child(panel_b)

	# Conversation log.
	root.add_child(_build_log())

	_add_log("[color=#D9A441]THE TABLE[/color]  " + str(Data.opening_lines().pick_random()))
	_add_log("[color=#8A948B]ROUND 1[/color]  Both sides are seated. You have " + str(MAX_TURNS) + " rounds before the meeting ends.")
	_refresh_game()

	if audio != null:
		audio.play("settle")


func _build_center() -> VBoxContainer:
	var col := VBoxContainer.new()
	col.custom_minimum_size = Vector2(352, 0)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.size_flags_vertical = Control.SIZE_EXPAND_FILL
	col.size_flags_stretch_ratio = 1.08
	col.add_theme_constant_override("separation", 7)

	var heading := UIKit.label("THE TABLE", 9, UIKit.GREEN, true)
	heading.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	col.add_child(heading)

	var proposal := PanelContainer.new()
	proposal.add_theme_stylebox_override("panel", UIKit.box(UIKit.PAPER_WARM, 14, UIKit.LINE, 1))
	col.add_child(proposal)

	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", 5)
	proposal.add_child(pv)

	var plabel := UIKit.label("YOUR PROPOSAL", 8, UIKit.MUTED, true)
	pv.add_child(plabel)

	var chip_row := HBoxContainer.new()
	chip_row.add_theme_constant_override("separation", 6)
	pv.add_child(chip_row)

	chip_a = _make_chip("a")
	chip_row.add_child(chip_a["panel"])
	var plus := UIKit.label("+", 18, UIKit.GOLD, true)
	plus.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	chip_row.add_child(plus)
	chip_b = _make_chip("b")
	chip_row.add_child(chip_b["panel"])

	var hint := UIKit.label("Select one need from each side.", 10, UIKit.MUTED)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pv.add_child(hint)

	connect_button = UIKit.make_button("FIND COMMON GROUND", true)
	connect_button.custom_minimum_size = Vector2(0, 42)
	connect_button.pressed.connect(_on_connect_pressed)
	col.add_child(connect_button)

	var progress_panel := PanelContainer.new()
	progress_panel.add_theme_stylebox_override("panel", UIKit.box(Color("#EFE7D7"), 12, Color(0, 0, 0, 0), 0))
	col.add_child(progress_panel)

	var prog := VBoxContainer.new()
	prog.add_theme_constant_override("separation", 6)
	progress_panel.add_child(prog)

	var prow := HBoxContainer.new()
	prog.add_child(prow)
	var pl := UIKit.label("COMMON GROUND", 8, UIKit.MUTED, true)
	pl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	prow.add_child(pl)
	var pspacer := Control.new()
	pspacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pspacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	prow.add_child(pspacer)
	cg_count = UIKit.label("0 / 6", 11, UIKit.GREEN, true)
	cg_count.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	prow.add_child(cg_count)

	progress_bar = ProgressBar.new()
	progress_bar.min_value = 0
	progress_bar.max_value = TOTAL_NEEDS
	progress_bar.value = 0
	progress_bar.show_percentage = false
	progress_bar.custom_minimum_size = Vector2(0, 9)
	var bg_style := UIKit.box(Color(0.15, 0.2, 0.15, 0.10), 5)
	var fill_style := UIKit.box(UIKit.GREEN, 5)
	for st in [bg_style, fill_style]:
		st.content_margin_left = 0
		st.content_margin_right = 0
		st.content_margin_top = 0
		st.content_margin_bottom = 0
	progress_bar.add_theme_stylebox_override("background", bg_style)
	progress_bar.add_theme_stylebox_override("fill", fill_style)
	prog.add_child(progress_bar)

	var turn_row := HBoxContainer.new()
	turn_row.add_theme_constant_override("separation", 8)
	col.add_child(turn_row)
	turn_label = UIKit.label("ROUND 1 / 14", 13, UIKit.INK, true)
	turn_row.add_child(turn_label)
	var t_spacer := Control.new()
	t_spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	t_spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	turn_row.add_child(t_spacer)
	turn_sub = UIKit.label("14 actions left", 10, UIKit.MUTED)
	turn_sub.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	turn_row.add_child(turn_sub)

	var status_panel := PanelContainer.new()
	status_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	status_panel.add_theme_stylebox_override("panel", UIKit.box(Color(UIKit.GREEN, 0.045), 12, Color(UIKit.GREEN, 0.14), 1))
	col.add_child(status_panel)
	var status_box := VBoxContainer.new()
	status_box.add_theme_constant_override("separation", 6)
	status_panel.add_child(status_box)
	status_label = UIKit.wrapped_label(
		"Listen to both sides to reveal what they actually need. Then connect one need from each side.",
		11, UIKit.INK_SOFT
	)
	status_label.max_lines_visible = 4
	status_box.add_child(status_label)
	var status_fill := Control.new()
	status_fill.size_flags_vertical = Control.SIZE_EXPAND_FILL
	status_fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	status_box.add_child(status_fill)
	var mantra := UIKit.wrapped_label(
		"A good agreement does not split the loss. It meets both fears.",
		10, Color(UIKit.GREEN, 0.75)
	)
	mantra.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	status_box.add_child(mantra)

	var small_actions := HBoxContainer.new()
	small_actions.add_theme_constant_override("separation", 6)
	col.add_child(small_actions)
	var clear := UIKit.make_button("Clear", false)
	clear.custom_minimum_size = Vector2(0, 30)
	clear.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	clear.pressed.connect(_on_clear_pressed)
	small_actions.add_child(clear)
	var quick := UIKit.make_button("Quick guide", false)
	quick.custom_minimum_size = Vector2(0, 30)
	quick.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	quick.pressed.connect(_open_help_overlay)
	small_actions.add_child(quick)

	return col


func _make_chip(pid: String) -> Dictionary:
	var party := _party(pid)
	var accent := Color(str(party.get("color", "#2E5E46")))
	var panel := PanelContainer.new()
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	panel.add_theme_stylebox_override("panel", UIKit.box(Color(accent, 0.055), 10, Color(accent, 0.24), 1))

	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 1)
	panel.add_child(v)

	var who := UIKit.label(str(party.get("name", "")).to_upper(), 7, accent, true)
	who.max_lines_visible = 1
	who.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	v.add_child(who)

	var title := UIKit.wrapped_label("Choose a need", 12, UIKit.MUTED, true)
	title.max_lines_visible = 2
	title.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	v.add_child(title)
	return {"panel": panel, "label": title, "party": party, "accent": accent}


func _build_log() -> PanelContainer:
	var p := PanelContainer.new()
	p.custom_minimum_size = Vector2(0, 94)
	p.add_theme_stylebox_override("panel", UIKit.box(Color("#26352D"), 14))

	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 3)
	p.add_child(v)

	var head := HBoxContainer.new()
	v.add_child(head)
	var label := UIKit.label("THE CONVERSATION", 8, UIKit.GOLD, true)
	head.add_child(label)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	head.add_child(spacer)
	var side := UIKit.label("what was said, and what it meant", 8, Color(0.65, 0.68, 0.60))
	head.add_child(side)

	log_text = RichTextLabel.new()
	log_text.bbcode_enabled = true
	log_text.scroll_active = true
	log_text.scroll_following = true
	log_text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	log_text.custom_minimum_size = Vector2(0, 58)
	log_text.add_theme_font_size_override("normal_font_size", 11)
	log_text.add_theme_font_size_override("bold_font_size", 11)
	log_text.add_theme_font_size_override("italics_font_size", 11)
	log_text.add_theme_color_override("default_color", Color("#EDE7D8"))
	v.add_child(log_text)
	return p


# ---------------------------------------------------------------------------
# Game actions
# ---------------------------------------------------------------------------

func _party(pid: String) -> Dictionary:
	if pid == "a":
		return party_a
	return party_b


func _other(pid: String) -> String:
	return "b" if pid == "a" else "a"


func _party_name(pid: String) -> String:
	return str(_party(pid).get("name", "This side"))


func _interest_for(pid: String, iid: String) -> Dictionary:
	for it in _party(pid).get("interests", []):
		if str(it.get("id", "")) == iid:
			return it
	return {}


func _interest_title(iid: String) -> String:
	var pid := "a" if iid.begins_with("a") else "b"
	var it := _interest_for(pid, iid)
	return str(it.get("title", iid))


func _adjust_trust(pid: String, delta: int) -> void:
	trust[pid] = clampi(int(trust.get(pid, 0)) + delta, 0, MAX_TRUST)


func _on_listen(pid: String) -> void:
	if mode != "play":
		return
	var party := _party(pid)
	var hidden: Array = []
	for it in party.get("interests", []):
		var iid := str(it.get("id", ""))
		if not revealed.has(iid) and not resolved.has(iid):
			hidden.append(it)
	if hidden.is_empty():
		_add_log("[color=#C9B88E]LISTEN[/color]  " + _party_name(pid) + " has already told you everything they can.")
		audio.play("warn")
		return

	var pick: Dictionary = hidden[randi() % hidden.size()]
	var iid := str(pick.get("id", ""))
	revealed[iid] = true
	_adjust_trust(pid, 1)
	_adjust_trust(_other(pid), -1)
	turn += 1
	audio.play("listen")

	_add_log("[color=#D9A441]LISTEN[/color]  " + _party_name(pid) + " — \"" + str(pick.get("need", "")) + "\"")
	_add_log("[color=#8A948B]       Underneath:[/color] " + str(pick.get("fear", "")))
	if int(trust[_other(pid)]) <= 1:
		_add_log("[color=#C46B48]       " + _party_name(_other(pid)) + " notices the room turning away from them.[/color]")
	_after_action()


func _on_reassure(pid: String) -> void:
	if mode != "play":
		return
	_adjust_trust(pid, 1)
	_adjust_trust(_other(pid), -1)
	turn += 1
	audio.play("select")
	_add_log("[color=#8FB89A]REASSURE[/color]  You tell " + _party_name(pid) + " that you can see the pressure they are under. It helps — a little.")
	if int(trust[_other(pid)]) <= 1:
		_add_log("[color=#C46B48]       " + _party_name(_other(pid)) + " feels the attention move away.[/color]")
	_after_action()


func _on_card_pressed(iid: String) -> void:
	if mode != "play":
		return
	if resolved.has(iid):
		return
	if not revealed.has(iid):
		audio.play("warn")
		_add_log("[color=#C9B88E]NOT YET[/color]  You reach for a need that has not been spoken aloud. Listen first.")
		return

	if selected.has(iid):
		selected.erase(iid)
		audio.play("click")
	else:
		var pid := "a" if iid.begins_with("a") else "b"
		var keep: Array[String] = []
		for s in selected:
			if not s.begins_with(pid):
				keep.append(s)
		keep.append(iid)
		selected = keep
		audio.play("select")
	_refresh_game()


func _on_clear_pressed() -> void:
	selected.clear()
	audio.play("click")
	_refresh_game()


func _on_connect_pressed() -> void:
	if mode != "play":
		return
	if selected.size() != 2:
		return
	var a_id := ""
	var b_id := ""
	for iid in selected:
		if iid.begins_with("a"):
			a_id = iid
		else:
			b_id = iid
	if a_id == "" or b_id == "":
		return
	var key := a_id + "|" + b_id
	if failed_pairs.has(key):
		audio.play("warn")
		return

	var synergies: Dictionary = scenario.get("synergies", {})
	if synergies.has(key):
		var bridge: Dictionary = synergies[key]
		resolved[a_id] = true
		resolved[b_id] = true
		_adjust_trust("a", 1)
		_adjust_trust("b", 1)
		turn += 1
		selected.clear()
		audio.play("success")
		_add_log("[color=#8FB89A]CONNECT[/color]  " + str(bridge.get("title", "A bridge")) + ".")
		_add_log("[color=#D5CEBE]       " + str(bridge.get("text", "")) + "[/color]")
		_add_log("[color=#D9A441]       Both needs are now on common ground.[/color]")
		_celebrate()
		_refresh_game()
		_after_action()
	else:
		var decoys: Dictionary = scenario.get("decoys", {})
		var fail_text := "The two needs do not fit together as stated. One side's fear is still unprotected."
		if decoys.has(key):
			fail_text = str(decoys[key].get("text", fail_text))
		failed_pairs[key] = true
		_adjust_trust("a", -1)
		_adjust_trust("b", -1)
		turn += 1
		selected.clear()
		audio.play("fail")
		_add_log("[color=#C46B48]NOT A BRIDGE[/color]  " + _interest_title(a_id) + " + " + _interest_title(b_id) + ".")
		_add_log("[color=#D5CEBE]       " + fail_text + "[/color]")
		_refresh_game()
		_after_action()


func _after_action() -> void:
	if int(trust["a"]) <= 0 or int(trust["b"]) <= 0:
		_end_game("walkout")
		return
	if resolved.size() >= TOTAL_NEEDS:
		_win_sequence()
		return
	if turn >= MAX_TURNS:
		_end_game("timeout")
		return
	_refresh_game()


func _win_sequence() -> void:
	mode = "settling"
	_refresh_game()
	audio.play("settle")
	_add_log("[color=#D9A441]COMMON GROUND[/color]  Every need is met. The room is quiet in a different way now.")
	_celebrate()
	await get_tree().create_timer(1.35).timeout
	if mode == "settling":
		_end_game("win")


func _end_game(kind: String) -> void:
	last_result = kind
	mode = "result"
	_show_result(kind)


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------

func _refresh_game() -> void:
	if panel_a == null or panel_b == null:
		return
	panel_a.set_trust(int(trust["a"]), MAX_TRUST)
	panel_b.set_trust(int(trust["b"]), MAX_TRUST)
	panel_a.set_interests(revealed, resolved, selected)
	panel_b.set_interests(revealed, resolved, selected)

	var a_id := ""
	var b_id := ""
	for iid in selected:
		if iid.begins_with("a"):
			a_id = iid
		else:
			b_id = iid

	_update_chip(chip_a, a_id, "a")
	_update_chip(chip_b, b_id, "b")

	var both := a_id != "" and b_id != ""
	var key := a_id + "|" + b_id
	connect_button.disabled = not both
	if both and failed_pairs.has(key):
		connect_button.disabled = true
		connect_button.text = "ALREADY TRIED — TRY ANOTHER PAIR"
		status_label.text = "These two needs have already shown where they break. Look for a pairing that protects both fears."
	elif both:
		connect_button.text = "FIND COMMON GROUND"
		status_label.text = "Two needs, one proposal. If the solution meets both fears, it will hold."
	elif a_id != "" or b_id != "":
		connect_button.text = "FIND COMMON GROUND"
		status_label.text = "Now choose one need from the other side."
	else:
		connect_button.text = "FIND COMMON GROUND"
		if panel_a.hidden_count == 0 and panel_b.hidden_count == 0:
			status_label.text = "Every need is on the table. Connect them with proposals that meet both sides' fears."
		else:
			status_label.text = "Listen to reveal needs. Then select one need from each side and find a solution that meets both."

	var count := resolved.size()
	progress_bar.value = count
	cg_count.text = str(count) + " / " + str(TOTAL_NEEDS)
	cg_count.add_theme_color_override("font_color", UIKit.GREEN if count < TOTAL_NEEDS else UIKit.GOLD)
	if count >= TOTAL_NEEDS:
		connect_button.disabled = true
		connect_button.text = "ALL NEEDS SETTLED"
		status_label.text = "Every need is on common ground. The room is quiet in a different way now."

	turn_label.text = "ROUND " + str(mini(turn + 1, MAX_TURNS)) + " / " + str(MAX_TURNS)
	var left := maxi(0, MAX_TURNS - turn)
	turn_sub.text = str(left) + (" action left" if left == 1 else " actions left")
	turn_sub.add_theme_color_override("font_color", UIKit.RED if left <= 3 else UIKit.MUTED)

	var all_revealed: bool = int(panel_a.hidden_count) == 0 and int(panel_b.hidden_count) == 0
	if all_revealed and count < TOTAL_NEEDS and not both:
		status_label.add_theme_color_override("font_color", UIKit.GREEN_DARK)
	else:
		status_label.add_theme_color_override("font_color", UIKit.INK_SOFT)

	_update_log()


func _update_chip(chip: Dictionary, iid: String, pid: String) -> void:
	if chip.is_empty():
		return
	var label: Label = chip["label"]
	var panel: PanelContainer = chip["panel"]
	var accent: Color = chip["accent"]
	var has := iid != ""
	if has:
		label.text = _interest_title(iid)
		label.add_theme_color_override("font_color", UIKit.INK)
	else:
		label.text = "Choose a need"
		label.add_theme_color_override("font_color", UIKit.MUTED)
	var bg_alpha := 0.10 if has else 0.045
	var border_alpha := 0.55 if has else 0.22
	panel.add_theme_stylebox_override(
		"panel",
		UIKit.box(Color(accent, bg_alpha), 10, Color(accent, border_alpha), 2 if has else 1)
	)


func _add_log(line: String) -> void:
	log_entries.append(line)
	while log_entries.size() > 26:
		log_entries.pop_front()
	_update_log()


func _update_log() -> void:
	if log_text != null:
		log_text.text = "\n".join(log_entries)


func _toggle_sound() -> void:
	sound_on = not sound_on
	audio.set_muted(not sound_on)
	sound_button.text = "Sound: On" if sound_on else "Sound: Off"
	audio.play("click")


# ---------------------------------------------------------------------------
# Celebration
# ---------------------------------------------------------------------------

func _celebrate() -> void:
	var palette := [UIKit.GOLD, UIKit.TERRA, UIKit.GREEN, UIKit.BLUE, Color("#C9A227"), Color("#7EA06A")]
	var center := Vector2(size.x * 0.5, size.y * 0.46)
	for i in range(24):
		var p := ColorRect.new()
		p.color = palette[i % palette.size()]
		p.size = Vector2(randf_range(4, 9), randf_range(4, 9))
		p.position = center + Vector2(randf_range(-46, 46), randf_range(-24, 24))
		p.mouse_filter = Control.MOUSE_FILTER_IGNORE
		p.z_index = 120
		add_child(p)
		var target := p.position + Vector2(randf_range(-210, 210), randf_range(-200, 80))
		var tw := create_tween()
		tw.set_parallel(true)
		tw.tween_property(p, "position", target, randf_range(0.7, 1.25)).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tw.tween_property(p, "modulate:a", 0.0, randf_range(0.85, 1.35))
		tw.finished.connect(p.queue_free)

	var toast := PanelContainer.new()
	toast.custom_minimum_size = Vector2(310, 54)
	toast.position = Vector2(size.x * 0.5 - 155.0, 76.0)
	toast.z_index = 121
	toast.mouse_filter = Control.MOUSE_FILTER_IGNORE
	toast.add_theme_stylebox_override("panel", UIKit.box(UIKit.PAPER, 18, UIKit.GREEN, 2, true))
	var lbl := UIKit.label("+  COMMON GROUND", 22, UIKit.GREEN, true)
	lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	toast.add_child(lbl)
	add_child(toast)
	var tw2 := create_tween()
	tw2.set_parallel(true)
	tw2.tween_property(toast, "position:y", toast.position.y - 54.0, 1.5).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tw2.tween_property(toast, "modulate:a", 0.0, 1.5).set_delay(0.45)
	tw2.finished.connect(toast.queue_free)


# ---------------------------------------------------------------------------
# Modals
# ---------------------------------------------------------------------------

func _open_modal(title: String, builder: Callable, default_close: bool = true) -> void:
	if overlay != null:
		return
	overlay = Control.new()
	overlay.z_index = 200
	_full_rect(overlay)
	overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(overlay)

	var dim := ColorRect.new()
	dim.color = Color(0.07, 0.09, 0.07, 0.55)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	_full_rect(dim)
	overlay.add_child(dim)

	var cc := CenterContainer.new()
	_full_rect(cc)
	cc.mouse_filter = Control.MOUSE_FILTER_IGNORE
	overlay.add_child(cc)

	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(590, 0)
	panel.add_theme_stylebox_override("panel", UIKit.box(UIKit.PAPER, 18, Color(UIKit.GREEN, 0.2), 1, true))
	cc.add_child(panel)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 24)
	margin.add_theme_constant_override("margin_right", 24)
	margin.add_theme_constant_override("margin_top", 20)
	margin.add_theme_constant_override("margin_bottom", 20)
	panel.add_child(margin)

	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 9)
	margin.add_child(v)

	var head := HBoxContainer.new()
	v.add_child(head)
	var heading := UIKit.label(title, 22, UIKit.INK, true)
	heading.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(heading)
	var close := UIKit.make_button("Close", false)
	close.custom_minimum_size = Vector2(88, 28)
	UIKit.style_ghost_button(close)
	close.pressed.connect(_close_modal)
	head.add_child(close)

	builder.call(v)

	if default_close:
		var got := UIKit.make_button("Got it", true)
		got.custom_minimum_size = Vector2(0, 36)
		got.pressed.connect(_close_modal)
		v.add_child(got)


func _close_modal() -> void:
	if overlay != null:
		remove_child(overlay)
		overlay.queue_free()
		overlay = null
	audio.play("click")


func _open_help_overlay() -> void:
	if mode == "menu":
		_show_howto()
		return
	audio.play("click")
	_open_modal("How to Play", func(v: VBoxContainer) -> void:
		var intro := UIKit.wrapped_label(
			"You are the mediator. Each side has a public position and three hidden interests. Bring every need onto common ground before the goodwill runs out.",
			13, UIKit.INK_SOFT
		)
		v.add_child(intro)
		_modal_rule(v, "LISTEN", "Reveal one hidden need on a side. Their goodwill rises; the other side feels the attention shift.")
		_modal_rule(v, "REASSURE", "Spend a turn restoring goodwill without revealing anything. Sometimes keeping someone at the table is the work.")
		_modal_rule(v, "CONNECT", "Select one revealed need from each side, then Find Common Ground. Genuine bridges protect both fears.")
		_modal_rule(v, "KEEP THE TABLE", "If either side's goodwill reaches zero, they walk out. A solution that ignores someone is only a delay.")
		var goal := UIKit.wrapped_label("Goal: all six needs settled by round 14. There is no single right answer — only better and worse ways to listen.", 11, UIKit.GREEN, true)
		v.add_child(goal)
	)


func _modal_rule(parent: VBoxContainer, tag: String, text: String) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	parent.add_child(row)
	var t := UIKit.label(tag, 9, UIKit.GREEN, true)
	t.custom_minimum_size = Vector2(78, 0)
	t.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	row.add_child(t)
	var body := UIKit.wrapped_label(text, 12, UIKit.INK_SOFT)
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(body)


func _confirm_leave() -> void:
	audio.play("click")
	_open_modal("Leave the table?", func(v: VBoxContainer) -> void:
		v.add_child(UIKit.wrapped_label(
			"The conversation will be lost, and both sides will be left where they started.",
			13, UIKit.INK_SOFT
		))
		var row := HBoxContainer.new()
		row.alignment = BoxContainer.ALIGNMENT_END
		row.add_theme_constant_override("separation", 8)
		v.add_child(row)
		var stay := UIKit.make_button("Stay", false)
		stay.custom_minimum_size = Vector2(110, 36)
		stay.pressed.connect(_close_modal)
		row.add_child(stay)
		var go := UIKit.make_button("Leave", true, UIKit.TERRA)
		go.custom_minimum_size = Vector2(110, 36)
		go.pressed.connect(_show_menu)
		row.add_child(go)
	, false)


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

func _show_result(kind: String) -> void:
	mode = "result"
	var s := _new_screen()
	var page := _page(880)
	var col: VBoxContainer = page[2]

	var won := kind == "win"
	var accent := UIKit.GREEN if won else UIKit.TERRA
	var kicker := str(scenario.get("chapter", "")).to_upper() + "  ·  " + str(scenario.get("title", "")).to_upper()
	col.add_child(UIKit.label(kicker, 9, UIKit.GOLD, true))

	var heading := "Common Ground"
	var body := str(scenario.get("epilogue", ""))
	if kind == "timeout":
		if resolved.size() >= 4:
			heading = "A Fragile Truce"
			body = "The meeting ends with " + str(resolved.size()) + " of 6 needs met. Nobody walks away, but the hardest fears are still unprotected. The agreement will hold only as long as nobody looks too closely."
		else:
			heading = "The Conversation Stalls"
			body = "The clock runs out with " + str(resolved.size()) + " of 6 needs met. Both sides leave with their positions intact and their fears untouched. The argument will be waiting at the next meeting."
	elif kind == "walkout":
		var who := "a"
		if int(trust["a"]) > 0:
			who = "b"
		heading = "One Side Walks Away"
		body = str(_party_name(who)) + " stands up and leaves. The other side is left at the table. A process that lets someone become invisible eventually loses them — and with them, any agreement that could have lasted."

	var title := UIKit.wrapped_label(heading, 38, accent, true)
	col.add_child(title)
	if won:
		col.add_child(UIKit.label("A settlement that includes everyone.", 13, UIKit.GREEN, true))
	var body_label := UIKit.wrapped_label(body, 14, UIKit.INK_SOFT)
	body_label.custom_minimum_size = Vector2(0, 46)
	col.add_child(body_label)

	var stats := HBoxContainer.new()
	stats.add_theme_constant_override("separation", 10)
	col.add_child(stats)
	var score_value := _score(kind)
	stats.add_child(_stat_box("NEEDS SETTLED", str(resolved.size()) + " / 6", UIKit.GREEN))
	stats.add_child(_stat_box("GOODWILL LEFT", str(maxi(0, int(trust["a"])) + maxi(0, int(trust["b"]))) + " / 12", UIKit.GOLD))
	stats.add_child(_stat_box("UNDERSTANDING", str(score_value), accent))

	var lesson_panel := PanelContainer.new()
	lesson_panel.add_theme_stylebox_override("panel", UIKit.box(Color(UIKit.GREEN, 0.06), 13, Color(UIKit.GREEN, 0.18), 1))
	col.add_child(lesson_panel)
	var lv := VBoxContainer.new()
	lv.add_theme_constant_override("separation", 4)
	lesson_panel.add_child(lv)
	lv.add_child(UIKit.label("WHAT THIS TEACHES", 8, UIKit.GREEN, true))
	var lesson := UIKit.wrapped_label(str(scenario.get("lesson", "")), 12, UIKit.INK_SOFT)
	lesson.max_lines_visible = 3
	lv.add_child(lesson)

	if not won:
		col.add_child(_missed_bridges())

	var buttons := HBoxContainer.new()
	buttons.alignment = BoxContainer.ALIGNMENT_CENTER
	buttons.add_theme_constant_override("separation", 9)
	col.add_child(buttons)

	if won:
		if scenario_index < scenarios.size() - 1:
			var nxt := UIKit.make_button("Next chapter  →", true)
			nxt.custom_minimum_size = Vector2(190, 40)
			nxt.pressed.connect(_on_scenario_card_pressed.bind(scenario_index + 1))
			buttons.add_child(nxt)
		else:
			var fg := UIKit.make_button("Read the Field Guide  →", true)
			fg.custom_minimum_size = Vector2(240, 40)
			fg.pressed.connect(func() -> void: _show_field_guide(true))
			buttons.add_child(fg)
	else:
		var retry := UIKit.make_button("Try again", true)
		retry.custom_minimum_size = Vector2(150, 40)
		retry.pressed.connect(_start_scenario.bind(scenario_index))
		buttons.add_child(retry)

	var menu := UIKit.make_button("Back to menu", false)
	menu.custom_minimum_size = Vector2(150, 40)
	menu.pressed.connect(_show_menu)
	buttons.add_child(menu)


func _score(kind: String) -> int:
	var base := resolved.size() * 50
	var trust_bonus := (maxi(0, int(trust["a"])) + maxi(0, int(trust["b"]))) * 12
	var win_bonus := 120 if kind == "win" else 0
	var time_bonus := 0
	if kind == "win":
		time_bonus = maxi(0, MAX_TURNS - turn) * 4
	return base + trust_bonus + win_bonus + time_bonus


func _stat_box(caption: String, value: String, accent: Color) -> PanelContainer:
	var p := PanelContainer.new()
	p.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	p.add_theme_stylebox_override("panel", UIKit.box(Color(accent, 0.065), 12, Color(accent, 0.18), 1))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", -2)
	p.add_child(v)
	var val := UIKit.label(value, 21, accent, true)
	val.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(val)
	var cap := UIKit.label(caption, 8, UIKit.MUTED, true)
	cap.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(cap)
	return p


func _missed_bridges() -> PanelContainer:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", UIKit.box(Color(UIKit.GOLD, 0.07), 13, Color(UIKit.GOLD, 0.22), 1))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 3)
	p.add_child(v)
	v.add_child(UIKit.label("BRIDGES THAT WERE AVAILABLE", 8, UIKit.GOLD, true))
	var synergies: Dictionary = scenario.get("synergies", {})
	for key in synergies:
		var parts: PackedStringArray = str(key).split("|")
		if parts.size() != 2:
			continue
		var bridge: Dictionary = synergies[key]
		var row := UIKit.wrapped_label(
			"•  " + _interest_title(parts[0]) + "  +  " + _interest_title(parts[1]) + "  →  " + str(bridge.get("title", "")),
			11, UIKit.INK_SOFT
		)
		row.max_lines_visible = 1
		row.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		v.add_child(row)
	return p


# ---------------------------------------------------------------------------
# How to play + Field Guide
# ---------------------------------------------------------------------------

func _show_howto() -> void:
	mode = "howto"
	var s := _new_screen()
	_corner_button("← Menu", _show_menu)
	var page := _page(820)
	var col: VBoxContainer = page[2]

	col.add_child(UIKit.label("HOW TO PLAY", 9, UIKit.GREEN, true))
	col.add_child(UIKit.label("The work is in the listening.", 34, UIKit.INK, true))

	var intro := UIKit.wrapped_label(
		"You are chairing a conversation between two groups that have stopped hearing each other. Each side has a public position — and three hidden interests: the needs and fears underneath. Your job is not to split the difference. It is to find solutions that let both sides keep what they actually need.",
		14, UIKit.INK_SOFT
	)
	col.add_child(intro)

	var rules := [
		["01  LISTEN", "Click Listen on either side. It reveals one hidden need and raises that side's goodwill. The other side loses a little goodwill — attention is finite. Listen to both, not just the side you agree with."],
		["02  READ THE FEAR", "Every card shows a need and a fear. The fear is the engine. A real bridge protects both fears at once; it does not ask one side to be brave about the thing that keeps them up at night."],
		["03  CONNECT", "Select one revealed need from each side, then press Find Common Ground. Some pairings are genuine synergies. Others look fair but leave one need unmet. Failed attempts cost goodwill."],
		["04  KEEP THE TABLE", "If either side's goodwill reaches zero, they walk out. Use Reassure to restore goodwill at the cost of a turn. Neglect is not neutral: it is a choice with a cost."]
	]
	for r in rules:
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 12)
		col.add_child(row)
		var tag := UIKit.label(str(r[0]), 9, UIKit.GREEN, true)
		tag.custom_minimum_size = Vector2(108, 0)
		tag.vertical_alignment = VERTICAL_ALIGNMENT_TOP
		row.add_child(tag)
		var text := UIKit.wrapped_label(str(r[1]), 12, UIKit.INK_SOFT)
		text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(text)

	var goal := UIKit.wrapped_label("Win by bringing all six needs onto common ground before round 14 ends. There is no timer on the conversation itself — only on this meeting.", 11, UIKit.GREEN, true)
	col.add_child(goal)

	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 10)
	col.add_child(row)
	var begin := UIKit.make_button("Begin Chapter I  →", true)
	begin.custom_minimum_size = Vector2(210, 40)
	begin.pressed.connect(_start_scenario.bind(0))
	row.add_child(begin)
	var back := UIKit.make_button("Back", false)
	back.custom_minimum_size = Vector2(110, 40)
	back.pressed.connect(_show_menu)
	row.add_child(back)


func _show_field_guide(campaign_complete: bool) -> void:
	mode = "guide"
	var s := _new_screen()
	_corner_button("← Menu", _show_menu)
	var page := _page(860)
	var col: VBoxContainer = page[2]

	col.add_child(UIKit.label("THE COMMON GROUND FIELD GUIDE", 9, UIKit.GOLD, true))
	col.add_child(UIKit.label("Five habits that travel well.", 32, UIKit.INK, true))
	if campaign_complete:
		col.add_child(UIKit.label("You finished all three chapters. Take these with you.", 13, UIKit.GREEN, true))
	else:
		col.add_child(UIKit.label("The game is a rehearsal. These are the things worth practicing.", 13, UIKit.MUTED))

	var principles := Data.field_guide()
	for p in principles:
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 12)
		col.add_child(row)

		var num_panel := PanelContainer.new()
		num_panel.custom_minimum_size = Vector2(38, 38)
		num_panel.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		var ns := UIKit.box(Color(UIKit.GOLD, 0.12), 19, Color(UIKit.GOLD, 0.28), 1)
		ns.content_margin_left = 0
		ns.content_margin_right = 0
		ns.content_margin_top = 0
		ns.content_margin_bottom = 0
		num_panel.add_theme_stylebox_override("panel", ns)
		row.add_child(num_panel)
		var num := UIKit.label(str(p.get("number", "")), 11, UIKit.GOLD, true)
		num.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		num.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		num_panel.add_child(num)

		var body := VBoxContainer.new()
		body.add_theme_constant_override("separation", 1)
		body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(body)
		body.add_child(UIKit.label(str(p.get("title", "")), 14, UIKit.INK, true))
		var text := UIKit.wrapped_label(str(p.get("text", "")), 11, UIKit.INK_SOFT)
		text.max_lines_visible = 2
		body.add_child(text)

	var closing := PanelContainer.new()
	closing.add_theme_stylebox_override("panel", UIKit.box(Color(UIKit.GREEN, 0.07), 13, Color(UIKit.GREEN, 0.2), 1))
	col.add_child(closing)
	var cv := VBoxContainer.new()
	cv.add_theme_constant_override("separation", 3)
	closing.add_child(cv)
	cv.add_child(UIKit.label("IF EVERYONE PLAYED THIS", 8, UIKit.GREEN, true))
	var close_text := UIKit.wrapped_label(
		"The world does not need everyone to agree. It needs enough people who can hear what is underneath a demand — and who look for the solution that lets both sides keep what they need. That is a skill. It can be practiced.",
		12, UIKit.INK_SOFT
	)
	close_text.max_lines_visible = 3
	cv.add_child(close_text)
	var next_step := UIKit.wrapped_label(
		"One small next step: in your next disagreement, ask \"What are you afraid of losing?\" before you answer.",
		11, UIKit.GREEN, true
	)
	cv.add_child(next_step)

	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 10)
	col.add_child(row)
	var again := UIKit.make_button("Play from the beginning", true)
	again.custom_minimum_size = Vector2(220, 40)
	again.pressed.connect(_start_scenario.bind(0))
	row.add_child(again)
	var menu := UIKit.make_button("Back to menu", false)
	menu.custom_minimum_size = Vector2(140, 40)
	menu.pressed.connect(_show_menu)
	row.add_child(menu)


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if overlay != null:
			_close_modal()
			get_viewport().set_input_as_handled()
			return
		if mode == "play":
			_confirm_leave()
			get_viewport().set_input_as_handled()
		elif mode == "intro" or mode == "howto" or mode == "guide" or mode == "result":
			_show_menu()
			get_viewport().set_input_as_handled()


func _initials(full_name: String) -> String:
	var skip := ["the", "of", "and", "a", "an"]
	var result := ""
	for word in full_name.split(" ", false):
		if str(word).to_lower() in skip:
			continue
		result += str(word).substr(0, 1).to_upper()
		if result.length() >= 2:
			break
	return result
