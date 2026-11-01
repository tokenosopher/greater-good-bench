extends Control
## Ripple: learn to spot the six common manipulation tricks (and to trust
## honest information) while your choices ripple through a small town.

const Content = preload("res://scripts/content.gd")
const TownView = preload("res://scripts/town.gd")

const BG_COLOR := Color("#151b2b")
const PANEL_COLOR := Color("#212a40")
const CARD_COLOR := Color("#f4f1ea")
const TEXT_COLOR := Color("#e9ecf3")
const MUTED_COLOR := Color("#9aa5bd")
const INK_COLOR := Color("#1f2430")
const HONEST_COLOR := Color("#69db7c")
const ALERT_COLOR := Color("#ffa94d")
const BAD_COLOR := Color("#ff8787")
const CARD_HOME := Vector2(640, 56)
const ACTION_POS := Vector2(640, 366)
const ACTION_SIZE := Vector2(620, 340)

var town: Control
var chapter_idx := 0
var post_idx := 0
var unlocked: Array = []
var streak := 0
var best_streak := 0
var total_correct := 0
var total_seen := 0
var chapter_correct := 0
var chapter_seen := 0
var stats := {}
var state := "title"
var current: Dictionary = {}
var overlay_action: Callable

var lbl_chapter: Label
var lbl_clear: Label
var lbl_streak: Label
var card: PanelContainer
var card_style: StyleBoxFlat
var card_avatar: Label
var card_avatar_style: StyleBoxFlat
var card_name: Label
var card_handle: Label
var card_text: Label
var card_attach: Label
var card_attach_panel: PanelContainer
var card_counter: Label
var stamp: Label
var stamp_style: StyleBoxFlat
var choose_box: VBoxContainer
var pick_box: VBoxContainer
var pick_grid: GridContainer
var fb_panel: PanelContainer
var fb_style: StyleBoxFlat
var fb_title: Label
var fb_text: Label
var fb_ask: Label
var fb_impact: Label
var guide_text: RichTextLabel
var overlay: ColorRect
var overlay_panel: PanelContainer
var overlay_box: VBoxContainer


func _ready() -> void:
	var t := Theme.new()
	t.default_font_size = 18
	theme = t
	var bg := ColorRect.new()
	bg.color = BG_COLOR
	bg.set_anchors_preset(PRESET_FULL_RECT)
	bg.mouse_filter = MOUSE_FILTER_IGNORE
	add_child(bg)
	_build_top_bar()
	_build_town()
	_build_guide()
	_build_card()
	_build_actions()
	_build_overlay()
	show_title()


# ---------------------------------------------------------------- UI helpers

func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	return l


func _wrap(l: Label) -> Label:
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.size_flags_horizontal = SIZE_EXPAND_FILL
	return l


func _style(color: Color, radius := 12, margin := 14) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = color
	s.set_corner_radius_all(radius)
	s.set_content_margin_all(margin)
	return s


func _button(text: String, color: Color, font_color := INK_COLOR, font_size := 18) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = FOCUS_NONE
	b.mouse_default_cursor_shape = CURSOR_POINTING_HAND
	b.add_theme_font_size_override("font_size", font_size)
	b.add_theme_stylebox_override("normal", _style(color, 10, 10))
	b.add_theme_stylebox_override("hover", _style(color.lightened(0.18), 10, 10))
	b.add_theme_stylebox_override("pressed", _style(color.darkened(0.15), 10, 10))
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	for k in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color", "font_hover_pressed_color"]:
		b.add_theme_color_override(k, font_color)
	b.custom_minimum_size = Vector2(0, 50)
	return b


func _clear(node: Node) -> void:
	for c in node.get_children():
		node.remove_child(c)
		c.queue_free()


# ------------------------------------------------------------------ building

func _build_top_bar() -> void:
	var title := _label("RIPPLE", 28, TEXT_COLOR)
	title.position = Vector2(24, 10)
	add_child(title)
	lbl_clear = _label("", 18, Color("#ffd97a"))
	lbl_clear.position = Vector2(180, 17)
	lbl_clear.size = Vector2(430, 30)
	lbl_clear.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	add_child(lbl_clear)
	lbl_chapter = _label("", 18, MUTED_COLOR)
	lbl_chapter.position = Vector2(642, 17)
	add_child(lbl_chapter)
	lbl_streak = _label("", 18, ALERT_COLOR)
	lbl_streak.position = Vector2(960, 17)
	lbl_streak.size = Vector2(300, 30)
	lbl_streak.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	add_child(lbl_streak)


func _build_town() -> void:
	town = TownView.new()
	town.position = Vector2(20, 56)
	add_child(town)
	town.setup(Vector2(590, 340))
	town.clarity_changed.connect(_update_top)


func _build_guide() -> void:
	var panel := PanelContainer.new()
	panel.position = Vector2(20, 406)
	panel.custom_minimum_size = Vector2(590, 300)
	panel.size = panel.custom_minimum_size
	panel.add_theme_stylebox_override("panel", _style(PANEL_COLOR, 14, 16))
	add_child(panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 6)
	panel.add_child(box)
	box.add_child(_label("FIELD GUIDE", 16, MUTED_COLOR))
	guide_text = RichTextLabel.new()
	guide_text.bbcode_enabled = true
	guide_text.fit_content = true
	guide_text.scroll_active = false
	guide_text.mouse_filter = MOUSE_FILTER_IGNORE
	guide_text.size_flags_horizontal = SIZE_EXPAND_FILL
	guide_text.add_theme_font_size_override("normal_font_size", 15)
	guide_text.add_theme_color_override("default_color", Color("#c9d1e3"))
	guide_text.add_theme_constant_override("line_separation", 3)
	box.add_child(guide_text)


func _build_card() -> void:
	card = PanelContainer.new()
	card.position = CARD_HOME
	card.custom_minimum_size = Vector2(620, 290)
	card_style = _style(CARD_COLOR, 16, 22)
	card_style.set_border_width_all(4)
	card_style.border_color = CARD_COLOR
	card.add_theme_stylebox_override("panel", card_style)
	add_child(card)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 14)
	card.add_child(box)

	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 12)
	box.add_child(head)
	card_avatar = _label("", 24, Color.WHITE)
	card_avatar.custom_minimum_size = Vector2(52, 52)
	card_avatar.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	card_avatar.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	card_avatar_style = _style(Color.GRAY, 26, 0)
	card_avatar.add_theme_stylebox_override("normal", card_avatar_style)
	head.add_child(card_avatar)
	var names := VBoxContainer.new()
	names.add_theme_constant_override("separation", 0)
	names.size_flags_horizontal = SIZE_EXPAND_FILL
	head.add_child(names)
	card_name = _label("", 20, INK_COLOR)
	names.add_child(card_name)
	card_handle = _label("", 16, Color("#6b7385"))
	names.add_child(card_handle)
	card_counter = _label("", 15, Color("#8a91a1"))
	card_counter.size_flags_vertical = SIZE_SHRINK_BEGIN
	head.add_child(card_counter)

	card_text = _wrap(_label("", 22, INK_COLOR))
	box.add_child(card_text)
	card_attach_panel = PanelContainer.new()
	card_attach_panel.add_theme_stylebox_override("panel", _style(Color("#e2ddd2"), 8, 10))
	box.add_child(card_attach_panel)
	card_attach = _wrap(_label("", 16, Color("#5a6070")))
	card_attach_panel.add_child(card_attach)

	stamp = _label("", 20, Color.WHITE)
	stamp_style = _style(Color.GRAY, 6, 8)
	stamp.add_theme_stylebox_override("normal", stamp_style)
	stamp.visible = false
	add_child(stamp)


func _build_actions() -> void:
	choose_box = VBoxContainer.new()
	choose_box.position = ACTION_POS
	choose_box.custom_minimum_size = Vector2(ACTION_SIZE.x, 0)
	choose_box.add_theme_constant_override("separation", 14)
	add_child(choose_box)
	choose_box.add_child(_label("Would you share this with your neighbours?", 18, MUTED_COLOR))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 14)
	choose_box.add_child(row)
	var share := _button("Share it   [S]", HONEST_COLOR, INK_COLOR, 20)
	share.custom_minimum_size.y = 70
	share.size_flags_horizontal = SIZE_EXPAND_FILL
	share.pressed.connect(func(): evaluate("honest"))
	row.add_child(share)
	var flag := _button("Something's off   [F]", ALERT_COLOR, INK_COLOR, 20)
	flag.custom_minimum_size.y = 70
	flag.size_flags_horizontal = SIZE_EXPAND_FILL
	flag.pressed.connect(_on_flag)
	row.add_child(flag)
	choose_box.add_child(_wrap(_label("Take your time. Pausing before you share is the whole point.", 15, Color("#6f7a93"))))

	pick_box = VBoxContainer.new()
	pick_box.position = ACTION_POS
	pick_box.custom_minimum_size = Vector2(ACTION_SIZE.x, 0)
	pick_box.add_theme_constant_override("separation", 12)
	add_child(pick_box)
	pick_box.add_child(_label("Which trick is it using?", 18, MUTED_COLOR))
	pick_grid = GridContainer.new()
	pick_grid.columns = 2
	pick_grid.add_theme_constant_override("h_separation", 12)
	pick_grid.add_theme_constant_override("v_separation", 10)
	pick_box.add_child(pick_grid)
	var back := _button("Back   [Esc]", Color("#3a4560"), TEXT_COLOR, 16)
	back.custom_minimum_size = Vector2(160, 40)
	back.size_flags_horizontal = SIZE_SHRINK_BEGIN
	back.pressed.connect(func(): _show_actions("choose"))
	pick_box.add_child(back)

	fb_panel = PanelContainer.new()
	fb_panel.position = ACTION_POS
	fb_panel.custom_minimum_size = Vector2(ACTION_SIZE.x, 0)
	fb_style = _style(PANEL_COLOR, 14, 16)
	fb_style.border_width_left = 6
	fb_panel.add_theme_stylebox_override("panel", fb_style)
	add_child(fb_panel)
	var fb := VBoxContainer.new()
	fb.add_theme_constant_override("separation", 8)
	fb_panel.add_child(fb)
	fb_title = _wrap(_label("", 23, TEXT_COLOR))
	fb.add_child(fb_title)
	fb_text = _wrap(_label("", 16, TEXT_COLOR))
	fb.add_child(fb_text)
	fb_ask = _wrap(_label("", 15, Color("#ffd97a")))
	fb.add_child(fb_ask)
	fb_impact = _wrap(_label("", 14, MUTED_COLOR))
	fb.add_child(fb_impact)
	var cont := _button("Continue   [Enter]", Color("#4c6ef5"), Color.WHITE, 17)
	cont.custom_minimum_size = Vector2(220, 42)
	cont.size_flags_horizontal = SIZE_SHRINK_END
	cont.pressed.connect(_on_continue)
	fb.add_child(cont)


func _build_overlay() -> void:
	overlay = ColorRect.new()
	overlay.color = Color(0.03, 0.04, 0.08, 0.82)
	overlay.set_anchors_preset(PRESET_FULL_RECT)
	overlay.mouse_filter = MOUSE_FILTER_STOP
	add_child(overlay)
	var center := CenterContainer.new()
	center.set_anchors_preset(PRESET_FULL_RECT)
	overlay.add_child(center)
	overlay_panel = PanelContainer.new()
	overlay_panel.add_theme_stylebox_override("panel", _style(PANEL_COLOR, 18, 30))
	center.add_child(overlay_panel)
	overlay_box = VBoxContainer.new()
	overlay_box.add_theme_constant_override("separation", 12)
	overlay_panel.add_child(overlay_box)


func _open_overlay(width: float) -> void:
	_clear(overlay_box)
	overlay_panel.custom_minimum_size = Vector2(width, 0)
	overlay_panel.reset_size()
	overlay.visible = true
	overlay.modulate.a = 0.0
	create_tween().tween_property(overlay, "modulate:a", 1.0, 0.25)


func _o(node: Control) -> Control:
	overlay_box.add_child(node)
	return node


func _o_button(text: String, action: Callable) -> void:
	overlay_action = action
	var b := _button(text, Color("#4c6ef5"), Color.WHITE, 20)
	b.custom_minimum_size = Vector2(300, 54)
	b.size_flags_horizontal = SIZE_SHRINK_CENTER
	b.pressed.connect(action)
	var spacer := Control.new()
	spacer.custom_minimum_size.y = 4
	_o(spacer)
	_o(b)


# ------------------------------------------------------------------- screens

func show_title() -> void:
	state = "title"
	card.visible = false
	stamp.visible = false
	_show_actions("none")
	_refresh_guide()
	_update_top()
	_open_overlay(820)
	var t := _label("RIPPLE", 60, TEXT_COLOR)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_o(t)
	var sub := _label("A game about what we share, and why it matters", 20, Color("#ffd97a"))
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_o(sub)
	_o(_wrap(_label("Brindlewick is a small town with a busy feed. Everything you share ripples out to your neighbours, for better or for worse.\n\nIn this game you'll learn the six most common tricks used to mislead people online. Just as important, you'll learn to recognise honest information that deserves to be shared. The same tricks show up in real feeds every day, about real things.", 18, TEXT_COLOR)))
	_o(_wrap(_label("Why this game? Research on \"psychological inoculation\" (Roozenbeek, van der Linden and others) has found that practising how to spot manipulation techniques in a safe setting helps people resist them in real life. If everyone paused before sharing, the world would be calmer, kinder and better informed.", 15, MUTED_COLOR)))
	_o_button("Begin   [Enter]", start_game)


func start_game() -> void:
	chapter_idx = 0
	unlocked.clear()
	streak = 0
	best_streak = 0
	total_correct = 0
	total_seen = 0
	chapter_correct = 0
	chapter_seen = 0
	stats.clear()
	for id in Content.TECH_ORDER:
		stats[id] = [0, 0]
	stats["honest"] = [0, 0]
	town.reset()
	show_intro()


func show_intro() -> void:
	state = "intro"
	var ch: Dictionary = Content.CHAPTERS[chapter_idx]
	var tech: String = ch.tech
	if tech != "" and not unlocked.has(tech):
		unlocked.append(tech)
	_refresh_guide()
	_update_top()
	_show_actions("none")
	card.visible = false
	stamp.visible = false
	_open_overlay(800)
	if chapter_idx > 0:
		var prev := _label("Chapter complete: you judged %d of %d posts well.  Clear-minded neighbours: %d of %d" % [chapter_correct, chapter_seen, town.count_clear(), town.total()], 15, HONEST_COLOR)
		_o(_wrap(prev))
	_o(_label("CHAPTER %d OF %d" % [chapter_idx + 1, Content.CHAPTERS.size()], 15, MUTED_COLOR))
	_o(_label(ch.title, 42, TEXT_COLOR))
	if tech != "":
		var info: Dictionary = Content.TECHNIQUES[tech]
		_o(_label("New trick: " + info.name, 24, Color(info.color)))
		_o(_wrap(_label(info.explain, 18, TEXT_COLOR)))
		var ex := PanelContainer.new()
		ex.add_theme_stylebox_override("panel", _style(Color("#1a2133"), 10, 14))
		ex.add_child(_wrap(_label("Example:  " + info.example, 17, Color("#c9d1e3"))))
		_o(ex)
		_o(_wrap(_label("Ask yourself:  " + info.question, 19, Color("#ffd97a"))))
	else:
		_o(_wrap(_label(ch.intro, 18, TEXT_COLOR)))
	if chapter_idx == 0:
		_o(_wrap(_label("How to play: if a post is honest, share it. If something's off, flag it and name the trick. Not every post is a trick, and honest information deserves to reach people.", 16, MUTED_COLOR)))
	chapter_correct = 0
	chapter_seen = 0
	_o_button("Open the feed   [Enter]", _begin_chapter)


func _begin_chapter() -> void:
	overlay.visible = false
	post_idx = 0
	show_post()


func show_post() -> void:
	state = "choose"
	var ch: Dictionary = Content.CHAPTERS[chapter_idx]
	current = ch.posts[post_idx]
	card.visible = true
	stamp.visible = false
	card_style.border_color = CARD_COLOR
	card_name.text = current.author
	card_handle.text = current.handle
	card_text.text = current.text
	var attach: String = current.get("attach", "")
	card_attach.text = attach
	card_attach_panel.visible = attach != ""
	card_avatar.text = String(current.author).substr(0, 1).to_upper()
	card_avatar_style.bg_color = Color.from_hsv(float(absi(String(current.handle).hash()) % 360) / 360.0, 0.45, 0.72)
	card_counter.text = "%d / %d" % [post_idx + 1, ch.posts.size()]
	_fit_panels()
	_show_actions("choose")
	_update_top()
	card.position = CARD_HOME + Vector2(70, 0)
	card.modulate.a = 0.0
	var tw := create_tween().set_parallel(true)
	tw.tween_property(card, "position", CARD_HOME, 0.35).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tw.tween_property(card, "modulate:a", 1.0, 0.25)


func _fit_panels() -> void:
	card.reset_size()
	fb_panel.reset_size()


func _process(_delta: float) -> void:
	# Wrapped labels only know their height after layout, so shrink-wrap
	# the panels whenever their size drifts from the minimum.
	if card.size != card.get_combined_minimum_size():
		card.reset_size()
	if fb_panel.size != fb_panel.get_combined_minimum_size():
		fb_panel.reset_size()


func _show_actions(which: String) -> void:
	if which != "none" and which != "feedback":
		state = which
	choose_box.visible = which == "choose"
	pick_box.visible = which == "pick"
	fb_panel.visible = which == "feedback"


func _on_flag() -> void:
	if state != "choose":
		return
	_clear(pick_grid)
	for i in unlocked.size():
		var info: Dictionary = Content.TECHNIQUES[unlocked[i]]
		var b := _button("%d   %s" % [i + 1, info.name], Color(info.color), INK_COLOR, 18)
		b.custom_minimum_size = Vector2(299, 50)
		var id: String = unlocked[i]
		b.pressed.connect(func(): evaluate(id))
		pick_grid.add_child(b)
	_show_actions("pick")


func evaluate(choice: String) -> void:
	if state != "choose" and state != "pick":
		return
	state = "feedback"
	var answer: String = current.a
	var also: Array = current.get("also", [])
	var outcome := ""
	if answer == "honest":
		outcome = "honest_shared" if choice == "honest" else "honest_flagged"
	elif choice == "honest":
		outcome = "trick_shared"
	elif choice == answer or also.has(choice):
		outcome = "trick_named"
	else:
		outcome = "trick_caught"

	var correct := outcome == "honest_shared" or outcome == "trick_named"
	total_seen += 1
	chapter_seen += 1
	stats[answer][1] += 1
	if correct:
		total_correct += 1
		chapter_correct += 1
		stats[answer][0] += 1
		streak += 1
		best_streak = maxi(best_streak, streak)
	elif outcome != "trick_caught":
		streak = 0

	var info: Dictionary = Content.TECHNIQUES.get(answer, {})
	var why: String = current.why
	var title := ""
	var color := HONEST_COLOR
	var impact := ""
	match outcome:
		"honest_shared":
			title = "Good share! This one was honest."
			impact = "You passed on useful information, and your neighbours are better informed."
			town.send_wave(0.11)
		"trick_named":
			title = "Spotted it: " + info.name
			color = Color(info.color)
			impact = "You stopped it spreading and helped your neighbours learn the trick too."
			if choice != answer:
				title = "Spotted it: " + Content.TECHNIQUES[choice].name
				why = "Its main trick is %s. %s" % [info.name, why]
			town.send_wave(0.13)
		"trick_caught":
			title = "You caught it, but the main trick is " + info.name
			color = ALERT_COLOR
			impact = "You stopped it spreading. Naming the right trick helps people recognise it next time."
			town.send_wave(0.05)
		"trick_shared":
			title = "Oops! That was a trick: " + info.name
			color = BAD_COLOR
			impact = "It spread fast. Misleading posts often travel further and faster than the truth."
			town.send_wave(-0.2)
		"honest_flagged":
			title = "Actually, this one was honest."
			color = BAD_COLOR
			impact = "Useful information didn't reach the people who needed it. Too much suspicion does harm too."
			town.send_wave(-0.12)
	fb_title.text = title
	fb_title.add_theme_color_override("font_color", color)
	fb_style.border_color = color
	fb_text.text = why
	if answer == "honest":
		fb_ask.text = Content.HONEST_SIGNS
	else:
		fb_ask.text = "Ask yourself:  " + info.question
	fb_impact.text = impact
	_fit_panels()
	_show_actions("feedback")
	_update_top()

	card_style.border_color = color
	stamp.text = "SHARED" if choice == "honest" else "FLAGGED"
	stamp_style.bg_color = Color(color, 0.95)
	stamp.add_theme_color_override("font_color", INK_COLOR)
	stamp.visible = true
	stamp.reset_size()
	stamp.pivot_offset = stamp.size * 0.5
	stamp.position = CARD_HOME + Vector2(430, 22)
	stamp.rotation = -0.12
	stamp.scale = Vector2(1.8, 1.8)
	stamp.modulate.a = 0.0
	var tw := create_tween().set_parallel(true)
	tw.tween_property(stamp, "scale", Vector2.ONE, 0.22).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(stamp, "modulate:a", 1.0, 0.15)


func _on_continue() -> void:
	if state != "feedback":
		return
	post_idx += 1
	var ch: Dictionary = Content.CHAPTERS[chapter_idx]
	if post_idx < ch.posts.size():
		show_post()
		return
	chapter_idx += 1
	if chapter_idx < Content.CHAPTERS.size():
		show_intro()
	else:
		show_end()


func show_end() -> void:
	state = "end"
	card.visible = false
	stamp.visible = false
	_show_actions("none")
	_update_top()
	_open_overlay(1120)
	var clear: int = town.count_clear()
	var n: int = town.total()
	var ratio := float(clear) / float(n)
	var verdict := ""
	if ratio >= 0.9:
		verdict = "Brindlewick is thriving. Your neighbours trust each other, share good information and spot tricks on their own."
	elif ratio >= 0.7:
		verdict = "Brindlewick is in good shape. A few neighbours are still lost in the fog, but the town is learning."
	elif ratio >= 0.45:
		verdict = "Brindlewick is divided. Some neighbours see clearly; others are caught up in rumours."
	else:
		verdict = "Fog has settled over Brindlewick. Every trick you learn to spot makes the next one easier, so try again!"
	_o(_label("The feed is quiet. Here's how Brindlewick is doing.", 30, TEXT_COLOR))
	_o(_wrap(_label("Clear-minded neighbours: %d of %d.  %s" % [clear, n, verdict], 17, Color("#ffd97a"))))

	var cols := HBoxContainer.new()
	cols.add_theme_constant_override("separation", 30)
	_o(cols)
	var left := RichTextLabel.new()
	left.bbcode_enabled = true
	left.fit_content = true
	left.scroll_active = false
	left.custom_minimum_size = Vector2(400, 0)
	left.add_theme_font_size_override("normal_font_size", 16)
	left.add_theme_color_override("default_color", TEXT_COLOR)
	var s := "[color=#9aa5bd]YOUR RESULTS[/color]\n"
	s += "Posts judged well: [b]%d / %d[/b]\nBest streak: [b]%d[/b]\n\n" % [total_correct, total_seen, best_streak]
	s += "[color=#69db7c]Honest posts shared[/color]   %d / %d\n" % [stats["honest"][0], stats["honest"][1]]
	for id in Content.TECH_ORDER:
		var info: Dictionary = Content.TECHNIQUES[id]
		s += "[color=%s]%s[/color]   %d / %d\n" % [info.color, info.name, stats[id][0], stats[id][1]]
	left.text = s
	cols.add_child(left)

	var right := RichTextLabel.new()
	right.bbcode_enabled = true
	right.fit_content = true
	right.scroll_active = false
	right.size_flags_horizontal = SIZE_EXPAND_FILL
	right.add_theme_font_size_override("normal_font_size", 16)
	right.add_theme_color_override("default_color", TEXT_COLOR)
	var g := "[color=#9aa5bd]YOUR POCKET GUIDE: BEFORE YOU SHARE, ASK...[/color]\n"
	for id in Content.TECH_ORDER:
		var info: Dictionary = Content.TECHNIQUES[id]
		g += "[color=%s]>[/color] %s\n" % [info.color, info.question]
	g += "[color=#69db7c]>[/color] Does it name a source I can check? Is it honest about what it doesn't know?\n"
	right.text = g
	cols.add_child(right)

	_o(_wrap(_label("These tricks work on everyone, no matter how smart they are, and they work best when we're in a hurry. So: pause. Ask the question. Check the source. Then share what's true, and be generous with people who got fooled. Your real neighbours are waiting.", 16, MUTED_COLOR)))
	_o_button("Play again   [Enter]", start_game)


# ------------------------------------------------------------------ HUD/input

func _refresh_guide() -> void:
	var s := "[color=#69db7c]Honest[/color]  Named sources, calm tone, admits uncertainty, corrects mistakes.\n"
	for i in Content.TECH_ORDER.size():
		var id: String = Content.TECH_ORDER[i]
		var info: Dictionary = Content.TECHNIQUES[id]
		if unlocked.has(id):
			s += "[color=%s]%d  %s[/color]  %s\n" % [info.color, unlocked.find(id) + 1, info.name, info.question]
		else:
			s += "[color=#4a5570]?  Unlocks in chapter %d[/color]\n" % (i + 1)
	guide_text.text = s


func _update_top() -> void:
	lbl_clear.text = "Clear-minded neighbours: %d / %d" % [town.count_clear(), town.total()]
	if state == "title":
		lbl_chapter.text = ""
		lbl_streak.text = ""
		return
	var idx := mini(chapter_idx, Content.CHAPTERS.size() - 1)
	lbl_chapter.text = "Chapter %d: %s" % [idx + 1, Content.CHAPTERS[idx].title]
	lbl_streak.text = "Streak: %d" % streak if streak > 1 else ""


func _unhandled_input(event: InputEvent) -> void:
	var ke := event as InputEventKey
	if ke == null or not ke.pressed or ke.echo:
		return
	var k: Key = ke.keycode
	var confirm := k == KEY_ENTER or k == KEY_KP_ENTER or k == KEY_SPACE
	match state:
		"title", "intro", "end":
			if confirm and overlay_action.is_valid():
				overlay_action.call()
		"choose", "pick":
			if state == "choose" and k == KEY_S:
				evaluate("honest")
			elif state == "choose" and k == KEY_F:
				_on_flag()
			elif state == "pick" and (k == KEY_ESCAPE or k == KEY_BACKSPACE):
				_show_actions("choose")
			elif k >= KEY_1 and k <= KEY_6:
				var i: int = k - KEY_1
				if i < unlocked.size():
					evaluate(unlocked[i])
		"feedback":
			if confirm:
				_on_continue()
	get_viewport().set_input_as_handled()
