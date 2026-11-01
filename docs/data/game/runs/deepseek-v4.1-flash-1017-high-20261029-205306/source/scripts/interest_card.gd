extends Button
## A single revealed or hidden interest. States: hidden, revealed, selected, resolved.

signal card_pressed(interest_id: String)

const UIKit = preload("res://scripts/ui_kit.gd")

var interest_id := ""
var interest_data: Dictionary = {}
var accent := UIKit.GREEN
var is_revealed := false
var is_selected := false
var is_resolved := false

var title_label: Label
var tag_label: Label
var need_label: Label
var fear_label: Label
var _body: VBoxContainer


func setup(data: Dictionary, party_color: Color) -> void:
	interest_data = data
	interest_id = data.get("id", "")
	accent = party_color
	text = ""
	focus_mode = Control.FOCUS_ALL
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	custom_minimum_size = Vector2(0, 104)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	clip_text = false

	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_theme_constant_override("margin_left", 11)
	margin.add_theme_constant_override("margin_right", 11)
	margin.add_theme_constant_override("margin_top", 8)
	margin.add_theme_constant_override("margin_bottom", 8)
	add_child(margin)

	_body = VBoxContainer.new()
	_body.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_body.add_theme_constant_override("separation", 2)
	margin.add_child(_body)

	var top := HBoxContainer.new()
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top.add_theme_constant_override("separation", 6)
	_body.add_child(top)

	title_label = UIKit.label("", 14, UIKit.INK, true)
	title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_label.max_lines_visible = 1
	title_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	top.add_child(title_label)

	tag_label = UIKit.label("", 8, UIKit.MUTED, true)
	tag_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	tag_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	top.add_child(tag_label)

	need_label = UIKit.wrapped_label("", 11, UIKit.INK_SOFT)
	need_label.max_lines_visible = 2
	need_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_body.add_child(need_label)

	fear_label = UIKit.wrapped_label("", 11, UIKit.MUTED)
	fear_label.max_lines_visible = 2
	fear_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_body.add_child(fear_label)

	pressed.connect(_on_pressed)
	refresh()


func _on_pressed() -> void:
	card_pressed.emit(interest_id)


func refresh() -> void:
	var bg := UIKit.PAPER
	var border := Color(accent, 0.30)
	var border_w := 1
	var title_col := UIKit.INK
	var body_col := UIKit.INK_SOFT
	var tag_col := accent

	if is_resolved:
		bg = Color("#EDF4EA")
		border = Color(UIKit.GREEN, 0.55)
		border_w = 1
		tag_col = UIKit.GREEN
		title_col = UIKit.GREEN_DARK
		body_col = Color("#4B5F50")
	elif is_selected:
		bg = Color("#FFF7E2")
		border = accent
		border_w = 2
		tag_col = accent
	elif not is_revealed:
		bg = Color("#F4EDE1")
		border = Color(0.4, 0.4, 0.35, 0.16)
		border_w = 1
		title_col = UIKit.MUTED
		body_col = Color(0.48, 0.48, 0.42)
		tag_col = UIKit.FAINT

	title_label.add_theme_color_override("font_color", title_col)
	need_label.add_theme_color_override("font_color", body_col)
	fear_label.add_theme_color_override("font_color", Color(body_col, 0.78))
	tag_label.add_theme_color_override("font_color", tag_col)

	if is_resolved:
		title_label.text = "✓ " + str(interest_data.get("title", ""))
		need_label.text = "Need met: " + str(interest_data.get("need", ""))
		fear_label.text = "Common ground found."
		tag_label.text = "SETTLED"
	elif not is_revealed:
		title_label.text = "A need not yet heard"
		need_label.text = "Listen to this side to reveal what is underneath."
		fear_label.text = "Every hard demand is protecting something."
		tag_label.text = "HIDDEN"
	else:
		title_label.text = str(interest_data.get("title", ""))
		need_label.text = "Needs: " + str(interest_data.get("need", ""))
		fear_label.text = "Fears: " + str(interest_data.get("fear", ""))
		tag_label.text = str(interest_data.get("tag", ""))

	disabled = is_resolved
	mouse_default_cursor_shape = Control.CURSOR_ARROW if is_resolved else Control.CURSOR_POINTING_HAND

	var normal := UIKit.box(bg, 12, border, border_w)
	var hover := UIKit.box(bg.lightened(0.018), 12, accent if is_revealed and not is_resolved else border, max(border_w, 2 if is_selected else 1))
	var pressed_style := UIKit.box(bg.darkened(0.025), 12, accent, max(border_w, 2))
	var focus := UIKit.box(bg, 12, accent, 2)
	var disabled_style := UIKit.box(bg, 12, border, border_w)
	for s in [normal, hover, pressed_style, focus, disabled_style]:
		s.content_margin_left = 0
		s.content_margin_right = 0
		s.content_margin_top = 0
		s.content_margin_bottom = 0
	add_theme_stylebox_override("normal", normal)
	add_theme_stylebox_override("hover", hover)
	add_theme_stylebox_override("pressed", pressed_style)
	add_theme_stylebox_override("focus", focus)
	add_theme_stylebox_override("disabled", disabled_style)
